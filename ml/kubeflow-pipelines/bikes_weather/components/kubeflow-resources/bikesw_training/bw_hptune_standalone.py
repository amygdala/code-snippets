# Copyright 2020 Google Inc. All Rights Reserved.
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

# Adapted in part from:
# https://github.com/GoogleCloudPlatform/data-science-on-gcp/blob/master/09_cloudml/flights_model_tf2.ipynb
# by Valliappa Lakshmanan.  (See that repo for more info about the accompanying book,
# "Data Science on the Google Cloud Platform", from O'Reilly.)


import argparse
import logging
import os, json, math, time, shutil
import numpy as np

# import pathlib2
import tensorflow as tf
from kerastuner.tuners import RandomSearch, Hyperband


DEVELOP_MODE = False
NBUCKETS = 5 # for embeddings
NUM_EXAMPLES = 1000*1000 * 20 # assume 20 million examples
# DNN_HIDDEN_UNITS = '128,64,32'

CSV_COLUMNS  = ('duration,end_station_id,bike_id,ts,day_of_week,start_station_id' +
                ',start_latitude,start_longitude,end_latitude,end_longitude' +
                ',euclidean,loc_cross,prcp,max,min,temp,dewp').split(',')
LABEL_COLUMN = 'duration'
DEFAULTS     = [[0.0],['na'],['na'],[0.0],['na'],['na'],
               [0.0],[0.0],[0.0],[0.0],
               [0.0],['na'],[0.0],[0.0],[0.0],[0.0], [0.0]]

STRATEGY = tf.distribute.MirroredStrategy()
# TRAIN_BATCH_SIZE = 256
TRAIN_BATCH_SIZE = 256 * STRATEGY.num_replicas_in_sync


def load_dataset(pattern, batch_size=1):
  return tf.data.experimental.make_csv_dataset(pattern, batch_size, CSV_COLUMNS, DEFAULTS)

def features_and_labels(features):
  label = features.pop('duration') # this is what we will train for
  features.pop('bike_id')
  return features, label

# def parse_fn(filename): 
#   return tf.data.Dataset.range(10) 


def read_dataset(pattern, batch_size, mode=tf.estimator.ModeKeys.TRAIN, truncate=None):
  dataset = load_dataset(pattern, batch_size)
  dataset = dataset.map(features_and_labels, num_parallel_calls=tf.data.experimental.AUTOTUNE)
  if mode == tf.estimator.ModeKeys.TRAIN:
    dataset = dataset.repeat().shuffle(batch_size*10)
    # dataset = dataset.repeat()
  dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
  if truncate is not None:
    dataset = dataset.take(truncate)
  return dataset


# Build a wide-and-deep model.
def wide_and_deep_classifier(inputs, linear_feature_columns, dnn_feature_columns,
    num_hidden_layers, dnn_hidden_units1, learning_rate):
    deep = tf.keras.layers.DenseFeatures(dnn_feature_columns, name='deep_inputs')(inputs)
    # layers = [int(x) for x in dnn_hidden_units.split(',')]
    layers = [dnn_hidden_units1]
    if num_hidden_layers > 1:
      layers += [int(dnn_hidden_units1/(x*2)) for x in range(1, num_hidden_layers)]
    # layers = [dnn_hidden_units1, dnn_hidden_units1/2, dnn_hidden_units1/4]  # using hp tuning val, but hardwired to 3 layers currently.
    for layerno, numnodes in enumerate(layers):
        deep = tf.keras.layers.Dense(numnodes, activation='relu', name='dnn_{}'.format(layerno+1))(deep)
    wide = tf.keras.layers.DenseFeatures(linear_feature_columns, name='wide_inputs')(inputs)
    both = tf.keras.layers.concatenate([deep, wide], name='both')
    output = tf.keras.layers.Dense(1, name='dur')(both)
    model = tf.keras.Model(inputs, output)
    optimizer = tf.keras.optimizers.RMSprop(learning_rate)
    model.compile(loss='mse', optimizer=optimizer,
                 metrics=['mse', 'mae', tf.keras.metrics.RootMeanSquaredError()])
    return model


def create_model(hp):

  # duration,end_station_id,bike_id,ts,day_of_week,start_station_id,start_latitude,start_longitude,end_latitude,end_longitude,
  # euclidean,loc_cross,prcp,max,min,temp,dewp

  real = {
      colname : tf.feature_column.numeric_column(colname)
            for colname in
  #            ('ts,start_latitude,start_longitude,end_latitude,end_longitude,euclidean,prcp,max,min,temp,dewp').split(',')
              ('ts,euclidean,prcp,max,min,temp,dewp').split(',')
  }
  sparse = {
        'day_of_week': tf.feature_column.categorical_column_with_vocabulary_list('day_of_week',
                    vocabulary_list='1,2,3,4,5,6,7'.split(',')),
        'end_station_id' : tf.feature_column.categorical_column_with_hash_bucket('end_station_id', hash_bucket_size=800),
        'start_station_id' : tf.feature_column.categorical_column_with_hash_bucket('start_station_id', hash_bucket_size=800),
        'loc_cross' : tf.feature_column.categorical_column_with_hash_bucket('loc_cross', hash_bucket_size=21000),
  #      'bike_id' : tf.feature_column.categorical_column_with_hash_bucket('bike_id', hash_bucket_size=14000)
  }

  inputs = {
      colname : tf.keras.layers.Input(name=colname, shape=(), dtype='float32')
            for colname in real.keys()
  }
  inputs.update({
      colname : tf.keras.layers.Input(name=colname, shape=(), dtype='string')
            for colname in sparse.keys()
  })

  # embed all the sparse columns
  embed = {
         'embed_{}'.format(colname) : tf.feature_column.embedding_column(col, 10)
            for colname, col in sparse.items()
  }
  real.update(embed)

  # one-hot encode the sparse columns
  sparse = {
      colname : tf.feature_column.indicator_column(col)
            for colname, col in sparse.items()
  }

  if DEVELOP_MODE:
      print(sparse.keys())
      print(real.keys())

  model = None
  print('num replicas...')
  print(STRATEGY.num_replicas_in_sync)

  # with STRATEGY.scope():  # hmmm
  model = wide_and_deep_classifier(
      inputs,
      linear_feature_columns = sparse.values(),
      dnn_feature_columns = real.values(),
      # dnn_hidden_units = DNN_HIDDEN_UNITS,
      num_hidden_layers = hp.Int('num_hidden_layers', 2,3, step=1, default=3),
      dnn_hidden_units1 = hp.Int('hidden_size', 32, 128, step=32, default=96),
      learning_rate=hp.Choice('learning_rate',
                    values=[1e-2, 1e-3, 1e-4])
    )

  model.summary()
  return model

def main():

  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser(description='ML Trainer')
  parser.add_argument(
      '--epochs', type=int,
      default=1)
  parser.add_argument(
      '--steps-per-epoch', type=int,
      default=-1)  # if set to -1, don't override the normal calcs for this
  parser.add_argument(
      '--tuner-proj',
      required=True) 
  parser.add_argument(
      '--tuner-dir',
      required=True)
  parser.add_argument(
      '--executions-per-trial', type=int,
      default=1)
  parser.add_argument(
      '--max-trials', type=int,
      default=20)              
  parser.add_argument(
      '--data-dir',
      default='gs://aju-dev-demos-codelabs/bikes_weather/')


  args = parser.parse_args()
  logging.info("Tensorflow version " + tf.__version__)

  TRAIN_DATA_PATTERN = args.data_dir + "train*"
  EVAL_DATA_PATTERN = args.data_dir + "test*"
  OUTPUT_DIR='{}/{}/bwmodel/trained_model'.format(args.tuner_dir, args.tuner_proj)
  logging.info('Writing trained model to {}'.format(OUTPUT_DIR))
  # learning_rate = 0.001

  train_batch_size = TRAIN_BATCH_SIZE
  eval_batch_size = 1000
  if args.steps_per_epoch == -1:  # calc based on dataset size
    steps_per_epoch = NUM_EXAMPLES // train_batch_size
  else:
    steps_per_epoch = args.steps_per_epoch
  logging.info('using {} steps per epoch'.format(steps_per_epoch))

  logging.info('using train batch size %s', train_batch_size)
  train_dataset = read_dataset(TRAIN_DATA_PATTERN, train_batch_size)
  eval_dataset = read_dataset(EVAL_DATA_PATTERN, eval_batch_size, tf.estimator.ModeKeys.EVAL,
      eval_batch_size * 100 * STRATEGY.num_replicas_in_sync
  )

  tuner = RandomSearch(
  # tuner = Hyperband(
      create_model,
      objective='val_mae',
      # max_epochs=10,
      # hyperband_iterations=2,
      max_trials=args.max_trials,
      # distribution_strategy=tf.distribute.MirroredStrategy(),
      executions_per_trial=args.executions_per_trial,
      directory=args.tuner_dir,
      project_name=args.tuner_proj
    )

  tuner.search_space_summary()

  checkpoint_path = '{}/checkpoints/bikes_weather.cpt'.format(OUTPUT_DIR)
  logging.info("checkpoint path: %s", checkpoint_path)
  cp_callback = tf.keras.callbacks.ModelCheckpoint(checkpoint_path,
                                                  save_weights_only=True,
                                                  verbose=1)
  tb_callback = tf.keras.callbacks.TensorBoard(log_dir='{}/logs'.format(OUTPUT_DIR),
                                              update_freq=10000)

  logging.info("hp tuning model....")
  tuner.search(train_dataset,
      validation_data=eval_dataset,
      validation_steps=eval_batch_size,
      epochs=args.epochs,
      steps_per_epoch=steps_per_epoch,
      # callbacks=[cp_callback  # , tb_callback
      # ]
      )
  best_hyperparameters = tuner.get_best_hyperparameters(1)[0]
  logging.info('best hyperparameters: {}, {}'.format(best_hyperparameters, 
      best_hyperparameters.values))
  best_model = tuner.get_best_models(1)[0]
  logging.info('best model: {}'.format(best_model))

  ts = str(int(time.time()))
  export_dir = '{}/export/bikesw/{}'.format(OUTPUT_DIR, ts)
  logging.info('Exporting to {}'.format(export_dir))

  try:
    logging.info("exporting model....")
    tf.saved_model.save(best_model, export_dir)
  except Exception as e:  # retry once if error
    logging.warning(e)
    logging.info("retrying...")
    time.sleep(10)
    logging.info("again ... exporting model....")
    tf.saved_model.save(best_model, export_dir)


if __name__ == "__main__":
  main()
