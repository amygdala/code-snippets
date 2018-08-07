#!/bin/env python

# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import datetime
import os
import time
import uuid

import apache_beam as beam

import tensorflow as tf
from tensorflow.python.lib.io import file_io

import tensorflow_model_analysis as tfma
from tensorflow_model_analysis.eval_saved_model.post_export_metrics import post_export_metrics
from tensorflow_model_analysis.slicer import slicer

from tensorflow_transform import coders as tft_coders
from tensorflow_transform.tf_metadata import dataset_schema

from tensorflow_transform.beam import impl as beam_impl
from tensorflow_transform.coders import example_proto_coder

import taxi_schema.taxi_schema as ts


# An empty slice spec means the overall slice, that is, the whole dataset.
OVERALL_SLICE_SPEC = tfma.SingleSliceSpec()

# Data can be sliced along a feature column
# In this case, data is sliced along feature column trip_start_hour.
FEATURE_COLUMN_SLICE_SPEC = tfma.SingleSliceSpec(columns=['trip_start_hour'])
FEATURE_COLUMN_SLICE_SPEC2 = tfma.SingleSliceSpec(columns=['company'])


# Data can be sliced by crossing feature columns
# In this case, slices are computed for trip_start_day x trip_start_month.
FEATURE_COLUMN_CROSS_SPEC = tfma.SingleSliceSpec(columns=['trip_start_day', 'trip_start_month'])

# Metrics can be computed for a particular feature value.
# In this case, metrics are computed for all data where trip_start_hour is 12.
FEATURE_VALUE_SPEC = tfma.SingleSliceSpec(features=[('trip_start_hour', 12)])

# It is also possible to mix column cross and feature value cross.
# In this case, data where trip_start_hour is 12 will be sliced by trip_start_day.
COLUMN_CROSS_VALUE_SPEC = tfma.SingleSliceSpec(columns=['trip_start_day'],
    features=[('trip_start_hour', 12)])

ALL_SPECS = [
    OVERALL_SLICE_SPEC,
    FEATURE_COLUMN_SLICE_SPEC,
    FEATURE_COLUMN_SLICE_SPEC2,
    FEATURE_COLUMN_CROSS_SPEC,
    FEATURE_VALUE_SPEC,
    COLUMN_CROSS_VALUE_SPEC
]

def run_tfma(slice_spec, eval_model_base_dir, tfma_run_dir, input_csv,
             working_dir, mode, project, setup_file, add_metrics_callbacks=None):
    """Does model analysis, using the given spec of how to 'slice', and returns an
    EvalResult that can be used with TFMA visualization functions.
    """

    print("eval model base dir: %s" % eval_model_base_dir)
    # Make sure the model dir exists before proceeding, as sometimes it takes a few seconds to become
    # available after training completes.
    retries = 0
    sleeptime = 5
    while retries < 20:
      try:
        eval_model_dir = os.path.join(
            eval_model_base_dir, file_io.list_directory(eval_model_base_dir)[-1])
        print("eval model dir: %s" % eval_model_dir)
        if 'temp' not in eval_model_dir:
          break
        else:
          print("Sleeping %s seconds to sync with GCS..." % sleeptime)
          time.sleep(sleeptime)
          retries += 1
          sleeptime *= 2
      except Exception as e:
        print(e)
        print("Sleeping %s seconds to sync with GCS..." % sleeptime)
        time.sleep(sleeptime)
        retries += 1
        sleeptime *= 2

    raw_feature_spec = ts.get_raw_feature_spec()
    raw_schema = dataset_schema.from_feature_spec(raw_feature_spec)
    coder = example_proto_coder.ExampleProtoCoder(raw_schema)

    temp_dir = os.path.join(working_dir, 'tmp')

    if mode == 'local':
      print("mode == local")
      options = {
        'project': project}
      pipeline_options = beam.pipeline.PipelineOptions(flags=[], **options)
      runner = 'DirectRunner'
    elif mode == 'cloud':
      print("mode == cloud")
      options = {
        'job_name': 'tfma-' + str(uuid.uuid4()),
        'temp_location': temp_dir,
        'project': project,
        'save_main_session': True,
        'setup_file': setup_file
      }
      pipeline_options = beam.pipeline.PipelineOptions(flags=[], **options)
      runner = 'DataFlowRunner'
    else:
      raise ValueError("Invalid mode %s." % mode)

    display_only_data_location = input_csv

    with beam.Pipeline(runner, options=pipeline_options) as pipeline:
      with beam_impl.Context(temp_dir=temp_dir):
        csv_coder = ts.make_csv_coder()
        raw_data = (
            pipeline
            | 'ReadFromText' >> beam.io.ReadFromText(
                input_csv,
                coder=beam.coders.BytesCoder(),
                skip_header_lines=True)
            | 'ParseCSV' >> beam.Map(csv_coder.decode))

        raw_data = (
            raw_data
            | 'CleanData' >> beam.Map(ts.clean_raw_data_dict)
            | 'ToSerializedTFExample' >> beam.Map(coder.encode))

        _ = raw_data | 'EvaluateAndWriteResults' >> tfma.EvaluateAndWriteResults(
            eval_saved_model_path=eval_model_dir,
            slice_spec=slice_spec,
            output_path=tfma_run_dir,
            add_metrics_callbacks=add_metrics_callbacks,
            display_only_data_location=input_csv)

    return tfma.load_eval_result(output_path=tfma_run_dir)

def parse_arguments():
  """Parse command line arguments."""

  parser = argparse.ArgumentParser()
  parser.add_argument('--input_csv',
                      type=str,
                      required=True,
                      help='Path to the CSV file to use for eval.')
  parser.add_argument('--tfma_run_dir',
                      type=str,
                      required=True,
                      help='Directory for TFMA output')
  parser.add_argument('--eval_model_dir',
                      type=str,
                      required=True,
                      help='Path to the model exported for TFMA eval.')
  parser.add_argument('--mode',
                      choices=['local', 'cloud'],
                      required=True,
                      help='whether to run the job locally or in Cloud Dataflow.')
  parser.add_argument('--setup_file',
                      type=str,
                      required=True,
                      help='Path to setup.py file.')
  parser.add_argument('--project',
                      type=str,
                      help='The GCP project to run the dataflow job, if running in the `cloud` mode.')
  return parser.parse_args()


def main():
  tf.logging.set_verbosity(tf.logging.INFO)
  args = parse_arguments()

  tfma_result = run_tfma(input_csv=args.input_csv,
                         tfma_run_dir=args.tfma_run_dir,
                         eval_model_base_dir=args.eval_model_dir,
                         slice_spec=ALL_SPECS,
                         working_dir=args.tfma_run_dir,
                         mode=args.mode, project=args.project,
                         setup_file=args.setup_file
                         )


if __name__== "__main__":
  main()
