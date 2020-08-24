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

import argparse
import logging
import json
import time

import tensorflow as tf
from google.cloud import storage
from kerastuner.tuners import RandomSearch # , Hyperband

import bwmodel.model as bwmodel


DEVELOP_MODE = False
NBUCKETS = 5 # for embeddings
NUM_EXAMPLES = 1000*1000 * 20 # assume 20 million examples

STRATEGY = tf.distribute.MirroredStrategy()
TRAIN_BATCH_SIZE = 256 * STRATEGY.num_replicas_in_sync


def create_model(hp):

  inputs, sparse, real = bwmodel.get_layers()

  logging.info('sparse keys: %s', sparse.keys())
  logging.info('real keys: %s', real.keys())

  model = None
  print('num replicas...')
  print(STRATEGY.num_replicas_in_sync)

  model = bwmodel.wide_and_deep_classifier(
      inputs,
      linear_feature_columns=sparse.values(),
      dnn_feature_columns=real.values(),
      num_hidden_layers=hp.Int('num_hidden_layers', 2, 5),
      dnn_hidden_units1=hp.Int('hidden_size', 32, 256, step=32),
      learning_rate=hp.Choice('learning_rate',
                    values=[1e-1, 1e-2, 1e-3, 1e-4])
    )

  model.summary()
  return model


def main():
  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser(description='Keras Tuner HP search')
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
      '--bucket-name', required=True)
  parser.add_argument(
      '--tuner-dir',
      required=True)
  parser.add_argument(
      '--tuner-num',
      required=True)
  parser.add_argument(
      '--respath',
      required=True)
  parser.add_argument(
      '--executions-per-trial', type=int,
      default=2)
  parser.add_argument(
      '--max-trials', type=int,
      default=20)
  parser.add_argument(
      '--num-best-hps', type=int,
      default=2)
  parser.add_argument(
      '--data-dir',
      default='gs://aju-dev-demos-codelabs/bikes_weather/')

  args = parser.parse_args()
  logging.info('Tensorflow version %s', tf.__version__)

  TRAIN_DATA_PATTERN = args.data_dir + "train*"
  EVAL_DATA_PATTERN = args.data_dir + "test*"


  train_batch_size = TRAIN_BATCH_SIZE
  eval_batch_size = 1000
  if args.steps_per_epoch == -1:  # calc based on dataset size
    steps_per_epoch = NUM_EXAMPLES // train_batch_size
  else:
    steps_per_epoch = args.steps_per_epoch
  logging.info('using %s steps per epoch', steps_per_epoch)

  logging.info('using train batch size %s', train_batch_size)
  train_dataset = bwmodel.read_dataset(TRAIN_DATA_PATTERN, train_batch_size)
  eval_dataset = bwmodel.read_dataset(EVAL_DATA_PATTERN, eval_batch_size,
      tf.estimator.ModeKeys.EVAL,
      eval_batch_size * 100 * STRATEGY.num_replicas_in_sync
  )

  logging.info('executions per trial: %s', args.executions_per_trial)

  # TODO: parameterize
  retries = 0
  num_retries = 5
  sleep_time = 5
  while retries < num_retries:
    try:
      tuner = RandomSearch(
      # tuner = Hyperband(
          create_model,
          objective='val_mae',
          # max_epochs=10,
          # hyperband_iterations=2,
          max_trials=args.max_trials,
          distribution_strategy=STRATEGY,
          executions_per_trial=args.executions_per_trial,
          directory=args.tuner_dir,
          project_name=args.tuner_proj
        )
      break
    except Exception as e:
      logging.warning(e)
      logging.info('sleeping %s seconds...', sleep_time)
      time.sleep(sleep_time)
      retries += 1
      sleep_time *= 2

  logging.info("search space summary:")
  logging.info(tuner.search_space_summary())

  logging.info("hp tuning model....")
  tuner.search(train_dataset,
      validation_data=eval_dataset,
      validation_steps=eval_batch_size,
      epochs=args.epochs,
      steps_per_epoch=steps_per_epoch,
      )
  best_hps = tuner.get_best_hyperparameters(args.num_best_hps)
  best_hps_list = [best_hps[i].values for i in range(args.num_best_hps)]
  logging.info('best_hps_list: %s', best_hps_list)
  best_hp_values = json.dumps(best_hps_list)
  logging.info('best hyperparameters: %s', best_hp_values)

  storage_client = storage.Client()
  logging.info('writing best results to %s', args.respath)
  bucket = storage_client.get_bucket(args.bucket_name)
  logging.info('using bucket %s: %s, path %s', args.bucket_name, bucket, args.respath)
  blob = bucket.blob(args.respath)
  blob.upload_from_string(best_hp_values)

  # uncomment to also save best model from hp search
  # OUTPUT_DIR = '{}/{}/{}/bwmodel/trained_model'.format(args.tuner_dir,
  #     args.tuner_proj, args.tuner_num)
  # logging.info('Writing trained model to %s', OUTPUT_DIR)

  # best_model = tuner.get_best_models(1)[0]
  # logging.info('best model: %s', best_model)

  # ts = str(int(time.time()))
  # export_dir = '{}/export/bikesw/{}'.format(OUTPUT_DIR, ts)
  # logging.info('Exporting to %s', export_dir)

  # try:
  #   logging.info("exporting model....")
  #   tf.saved_model.save(best_model, export_dir)
  # except Exception as e:  # retry once if error
  #   logging.warning(e)
  #   logging.info("retrying...")
  #   time.sleep(10)
  #   logging.info("again ... exporting model....")
  #   tf.saved_model.save(best_model, export_dir)


if __name__ == "__main__":
  main()
