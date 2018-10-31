# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Preprocessor applying tf.transform to the chicago_taxi data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import datetime
import uuid
import os

import apache_beam as beam

import tensorflow as tf
import tensorflow_transform as transform
from tensorflow.python.lib.io import file_io

from tensorflow_transform.beam import impl as beam_impl
from tensorflow_transform.beam.tft_beam_io import transform_fn_io
from tensorflow_transform.coders import example_proto_coder
from tensorflow_transform.tf_metadata import dataset_metadata
from tensorflow_transform.tf_metadata import dataset_schema

from tensorflow_transform import coders as tft_coders

import taxi_schema.taxi_schema as ts


def make_sql(table_name, ts1, ts2, stage, max_rows=None, for_eval=False):
  """Creates the sql command for pulling data from BigQuery.

  Args:
    table_name: BigQuery table name
    max_rows: if set, limits the number of rows pulled from BigQuery
    for_eval: True if this is for evaluation, false otherwise

  Returns:
    sql command as string
  """
  if ts1 and ts2:
    if stage == 'eval':
      # 1/3 of the dataset used for eval
      where_clause = ('WHERE pickup_latitude is not NULL and MOD(FARM_FINGERPRINT(unique_key), 3) = 0' +
       " AND UNIX_SECONDS(trip_start_timestamp) > UNIX_SECONDS('%s') AND UNIX_SECONDS(trip_start_timestamp) < UNIX_SECONDS('%s')" % (ts1, ts2))
    else:
      # 2/3 of the dataset used for training
      where_clause = ('WHERE pickup_latitude is not NULL and MOD(FARM_FINGERPRINT(unique_key), 3) > 0 ' +
        " AND UNIX_SECONDS(trip_start_timestamp) > UNIX_SECONDS('%s') AND UNIX_SECONDS(trip_start_timestamp) < UNIX_SECONDS('%s')" % (ts1, ts2))
  else:
    if stage == 'eval':
      # 1/3 of the dataset used for eval
      where_clause = ('WHERE pickup_latitude is not NULL and MOD(FARM_FINGERPRINT(unique_key), 3) = 0')
    else:
      # 2/3 of the dataset used for training
      where_clause = ('WHERE pickup_latitude is not NULL and MOD(FARM_FINGERPRINT(unique_key), 3) > 0 ')

  limit_clause = ''
  if max_rows:
    limit_clause = 'LIMIT {max_rows}'.format(max_rows=max_rows)
  return """
  SELECT
      CAST(pickup_community_area AS string) AS pickup_community_area,
      CAST(dropoff_community_area AS string) AS dropoff_community_area,
      CAST(pickup_census_tract AS string) AS pickup_census_tract,
      CAST(dropoff_census_tract AS string) AS dropoff_census_tract,
      fare,
      EXTRACT(MONTH FROM trip_start_timestamp) AS trip_start_month,
      EXTRACT(HOUR FROM trip_start_timestamp) AS trip_start_hour,
      EXTRACT(DAYOFWEEK FROM trip_start_timestamp) AS trip_start_day,
      UNIX_SECONDS(trip_start_timestamp) AS trip_start_timestamp,
      pickup_latitude,
      pickup_longitude,
      dropoff_latitude,
      dropoff_longitude,
      trip_miles,
      payment_type,
      company,
      trip_seconds,
      tips
  FROM `{table_name}`
  {where_clause}
  {limit_clause}
""".format(table_name=table_name,
           where_clause=where_clause,
           limit_clause=limit_clause)


def transform_data(input_handle,
                   outfile_prefix,
                   working_dir,
                   setup_file, ts1, ts2,
                   project=None,
                   max_rows=None,
                   mode=None,
                   stage=None,
                   preprocessing_fn=None):
  """The main tf.transform method which analyzes and transforms data.

  Args:
    input_handle: BigQuery table name to process specified as
      DATASET.TABLE or path to csv file with input data.
    outfile_prefix: Filename prefix for emitted transformed examples
    working_dir: Directory in which transformed examples and transform
      function will be emitted.
    max_rows: Number of rows to query from BigQuery
    pipeline_args: additional DataflowRunner or DirectRunner args passed to the
      beam pipeline.
  """

  def def_preprocessing_fn(inputs):
    """tf.transform's callback function for preprocessing inputs.

    Args:
      inputs: map from feature keys to raw not-yet-transformed features.

    Returns:
      Map from string feature key to transformed feature operations.
    """
    outputs = {}
    for key in ts.DENSE_FLOAT_FEATURE_KEYS:
      # Preserve this feature as a dense float, setting nan's to the mean.
      outputs[key] = transform.scale_to_z_score(inputs[key])

    for key in ts.VOCAB_FEATURE_KEYS:
      # Build a vocabulary for this feature.
      outputs[key] = transform.string_to_int(
          inputs[key], top_k=ts.VOCAB_SIZE, num_oov_buckets=ts.OOV_SIZE)

    for key in ts.BUCKET_FEATURE_KEYS:
      outputs[key] = transform.bucketize(inputs[key], ts.FEATURE_BUCKET_COUNT)

    for key in ts.CATEGORICAL_FEATURE_KEYS:
      outputs[key] = inputs[key]

    # Was this passenger a big tipper?
    def convert_label(label):
      taxi_fare = inputs[ts.FARE_KEY]
      return tf.where(
          tf.is_nan(taxi_fare),
          tf.cast(tf.zeros_like(taxi_fare), tf.int64),
          # Test if the tip was > 20% of the fare.
          tf.cast(
              tf.greater(label, tf.multiply(taxi_fare, tf.constant(0.2))),
              tf.int64))

    outputs[ts.LABEL_KEY] = transform.apply_function(convert_label,
                                                       inputs[ts.LABEL_KEY])

    return outputs

  preprocessing_fn = preprocessing_fn or def_preprocessing_fn

  print('ts1 %s, ts2 %s' % (ts1,ts2))
  raw_feature_spec = ts.get_raw_feature_spec()
  raw_schema = dataset_schema.from_feature_spec(raw_feature_spec)
  raw_data_metadata = dataset_metadata.DatasetMetadata(raw_schema)
  temp_dir = os.path.join(working_dir, 'tmp')
  if stage is None:
    stage = 'train'

  if mode == 'local':
    options = {
      'project': project}
    pipeline_options = beam.pipeline.PipelineOptions(flags=[], **options)
    runner = 'DirectRunner'
  elif mode == 'cloud':
    options = {
      'job_name': 'tft-' + stage + '-' + str(uuid.uuid4()),
      'temp_location': temp_dir,
      'project': project,
      'save_main_session': True,
      'setup_file': setup_file
    }
    pipeline_options = beam.pipeline.PipelineOptions(flags=[], **options)
    runner = 'DataFlowRunner'
  else:
    raise ValueError("Invalid mode %s." % mode)

  with beam.Pipeline(runner, options=pipeline_options) as pipeline:
    with beam_impl.Context(temp_dir=temp_dir):
      csv_coder = ts.make_csv_coder()
      if 'csv' in input_handle.lower():
        raw_data = (
            pipeline
            | 'ReadFromText' >> beam.io.ReadFromText(
                input_handle, skip_header_lines=1)
            | 'ParseCSV' >> beam.Map(csv_coder.decode))
      else:
        query = make_sql(input_handle, ts1, ts2, stage, max_rows=max_rows, for_eval=False)
        raw_data = (
            pipeline
            | 'ReadBigQuery' >> beam.io.Read(
                beam.io.BigQuerySource(query=query, use_standard_sql=True)))

      raw_data |= 'CleanData' >> beam.Map(ts.clean_raw_data_dict)

      transform_fn = ((raw_data, raw_data_metadata)
                      | 'Analyze' >> beam_impl.AnalyzeDataset(preprocessing_fn))

      _ = (
          transform_fn
          | 'WriteTransformFn' >> transform_fn_io.WriteTransformFn(working_dir))

      # Shuffling the data before materialization will improve training
      # effectiveness downstream.
      shuffled_data = raw_data | 'RandomizeData' >> beam.transforms.Reshuffle()

      (transformed_data, transformed_metadata) = (
          ((shuffled_data, raw_data_metadata), transform_fn)
          | 'Transform' >> beam_impl.TransformDataset())

      if 'csv' not in input_handle.lower():  # if querying BQ
        _ = (
            raw_data
            | beam.Map(csv_coder.encode)
            | beam.io.WriteToText(os.path.join(working_dir, '{}.csv'.format(stage)), num_shards=1)
            )

      coder = example_proto_coder.ExampleProtoCoder(transformed_metadata.schema)
      _ = (
          transformed_data
          | 'SerializeExamples' >> beam.Map(coder.encode)
          | 'WriteExamples' >> beam.io.WriteToTFRecord(
              os.path.join(working_dir, outfile_prefix),
              compression_type=beam.io.filesystem.CompressionTypes.GZIP)
          )


def main():
  tf.logging.set_verbosity(tf.logging.INFO)

  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--input_handle',
      help=('Input BigQuery table to process specified as: '
            'DATASET.TABLE or path to csv file with input data.'))

  # for preprocessing
  parser.add_argument(
      '--working_dir',
      help=('Directory in which transformed examples and function '
            'will be emitted.'))

  parser.add_argument(
      '--outfile_prefix',
      help='Filename prefix for emitted transformed examples')

  parser.add_argument('--project',
                      type=str,
                      required=True,
                      help='The GCP project in which to run the dataflow job.')
  parser.add_argument('--mode',
                      choices=['local', 'cloud'],
                      help='whether to run the job locally or in Cloud Dataflow.')
  parser.add_argument('--stage',
                      choices=['train', 'eval'],
                      required=True,
                      help='Whether this is training or eval data.')
  parser.add_argument('--setup_file',
                      type=str,
                      required=True,
                      help='Path to setup.py file.')
  parser.add_argument('--ts1',
                      type=str,
                      help="When generating data via a BigQuery query, the lower bound on 'trip_start_timestamp'")
  parser.add_argument('--ts2',
                      type=str,
                      help="When generating data via a BigQuery query, the upper bound on 'trip_start_timestamp'")
  parser.add_argument('--preprocessing_module',
                      type=str,
                      required=False,
                      help=('GCS path to a python file defining '
                            'a "preprocess" function.'))

  parser.add_argument(
      '--max_rows',
      help='Number of rows to query from BigQuery',
      default=None,
      type=int)

  known_args, pipeline_args = parser.parse_known_args()

  preprocessing_fcn = None
  if known_args.preprocessing_module:
    module_dir = os.path.abspath(os.path.dirname(__file__))
    preprocessing_module_path = os.path.join(module_dir, 'preprocessing.py')
    with open(preprocessing_module_path, 'w+') as preprocessing_file:
      preprocessing_file.write(
          file_io.read_file_to_string(known_args.preprocessing_module))
    import preprocessing

    def wrapped_preprocessing_fn(inputs):
      outputs = preprocessing.preprocessing_fn(inputs)
      for key in outputs:
        if outputs[key].dtype == tf.bool:
          outputs[key] = tft.string_to_int(tf.as_string(outputs[key]),
                                           vocab_filename='vocab_' + key)
      return outputs

    preprocessing_fcn = wrapped_preprocessing_fn

  transform_data(
      input_handle=known_args.input_handle,
      outfile_prefix=known_args.outfile_prefix,
      working_dir=known_args.working_dir,
      setup_file=known_args.setup_file,
      ts1=known_args.ts1, ts2=known_args.ts2,
      project=known_args.project,
      max_rows=known_args.max_rows,
      mode=known_args.mode,
      stage=known_args.stage,
      preprocessing_fn=preprocessing_fcn)


if __name__ == '__main__':
  main()
