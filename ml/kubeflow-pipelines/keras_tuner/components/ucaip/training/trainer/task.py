# Copyright 2021 Google Inc. All Rights Reserved.
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
import os
import time

import tensorflow as tf

import bwmodel.model as bwmodel

DEVELOP_MODE = False
NBUCKETS = 5 # for embeddings
NUM_EXAMPLES = 1000*1000 * 20 # assume 20 million examples

STRATEGY = tf.distribute.MirroredStrategy()
TRAIN_BATCH_SIZE = 64 * STRATEGY.num_replicas_in_sync


def create_model(learning_rate, hidden_size, num_hidden_layers):

  inputs, sparse, real = bwmodel.get_layers()

  logging.info('sparse keys: %s', sparse.keys())
  logging.info('real keys: %s', real.keys())

  model = None
  print('num replicas...')
  print(STRATEGY.num_replicas_in_sync)

  with STRATEGY.scope():  # hmmm
    model = bwmodel.wide_and_deep_classifier(
        inputs,
        linear_feature_columns=sparse.values(),
        dnn_feature_columns=real.values(),
        num_hidden_layers=num_hidden_layers,
        dnn_hidden_units1=hidden_size,
        learning_rate=learning_rate)


  model.summary()
  return model

def run_training(
    # epochs: int,
    data_dir: str,
    # steps_per_epoch: int,
    hptune_dict: str
    ):

  if 'AIP_MODEL_DIR' not in os.environ:
      raise KeyError(
          'The `AIP_MODEL_DIR` environment variable has not been' +
          'set. See https://cloud.google.com/ai-platform-unified/docs/tutorials/image-recognition-custom/training'
      )

  logging.getLogger().setLevel(logging.INFO)

  # data_dir = 'gs://aju-dev-demos-codelabs/bikes_weather/'

  hptune_info = json.loads(str(args.hptune_dict))
  logging.info('hptune_info: %s', hptune_info)
  learning_rate = hptune_info['learning_rate']
  hidden_size = hptune_info['hidden_size']
  num_hidden_layers = hptune_info['num_hidden_layers']
  epochs = hptune_info['epochs']
  steps_per_epoch = hptune_info['steps_per_epoch']
  logging.info('using: learning rate %s, hidden size %s, first hidden layer %s',
      learning_rate, hidden_size, num_hidden_layers)
  logging.info('epochs: %s', epochs)
  logging.info('Tensorflow version %s', tf.__version__)

  TRAIN_DATA_PATTERN = data_dir + "train*"
  EVAL_DATA_PATTERN = data_dir + "test*"

  # OUTPUT_DIR = '{}/bwmodel/trained_model'.format(args.workdir)
  OUTPUT_DIR = os.environ['AIP_MODEL_DIR']
  logging.info('Writing trained model to %s', OUTPUT_DIR)

  train_batch_size = TRAIN_BATCH_SIZE
  eval_batch_size = 1000
  if steps_per_epoch == -1:  # calc based on dataset size
    steps_per_epoch = NUM_EXAMPLES // train_batch_size
  else:
    steps_per_epoch = steps_per_epoch
  logging.info('using %s steps per epoch', steps_per_epoch)

  train_dataset = bwmodel.read_dataset(TRAIN_DATA_PATTERN, train_batch_size)
  eval_dataset = bwmodel.read_dataset(EVAL_DATA_PATTERN, eval_batch_size,
      tf.estimator.ModeKeys.EVAL, eval_batch_size * 100 * STRATEGY.num_replicas_in_sync
  )

  model = create_model(learning_rate, hidden_size, num_hidden_layers)

  checkpoint_path = '{}checkpoints/bikes_weather.cpt'.format(OUTPUT_DIR)
  logging.info("checkpoint path: %s", checkpoint_path)
  cp_callback = tf.keras.callbacks.ModelCheckpoint(checkpoint_path,
                                                    save_weights_only=True,
                                                    verbose=1)
  tb_callback = tf.keras.callbacks.TensorBoard(log_dir='{}/logs'.format(OUTPUT_DIR),
                                                update_freq=20000)

  logging.info("training model....")
  history = model.fit(train_dataset,
                      validation_data=eval_dataset,
                      validation_steps=eval_batch_size,
                      epochs=epochs,
                      steps_per_epoch=steps_per_epoch,
                      callbacks=[cp_callback, tb_callback]
                      )

  tf.saved_model.save(model, OUTPUT_DIR)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Input Arguments
  # parser.add_argument(
  #     '--epochs', type=int, default=5)
  parser.add_argument(
      # e.g. {"num_hidden_layers": 3, "hidden_size": 96, "learning_rate": 0.01}
      '--hptune-dict', required=True)
  # parser.add_argument(
  #     '--steps-per-epoch', type=int,
  #     default=-1)  # if set to -1, don't override the normal calcs for this
  parser.add_argument(
      '--data-dir', default='gs://aju-dev-demos-codelabs/bikes_weather/')
  args = parser.parse_args()

  run_training(
      # args.epochs,
      args.data_dir,
      # args.steps_per_epoch,
      args.hptune_dict)
