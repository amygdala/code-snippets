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

import tensorflow as tf


CSV_COLUMNS  = ('duration,end_station_id,bike_id,ts,day_of_week,start_station_id' +
                ',start_latitude,start_longitude,end_latitude,end_longitude' +
                ',euclidean,loc_cross,prcp,max,min,temp,dewp').split(',')
LABEL_COLUMN = 'duration'
DEFAULTS     = [[0.0],['na'],['na'],[0.0],['na'],['na'],
               [0.0],[0.0],[0.0],[0.0],
               [0.0],['na'],[0.0],[0.0],[0.0],[0.0], [0.0]]

def load_dataset(pattern, batch_size=1):
  return tf.data.experimental.make_csv_dataset(pattern, batch_size, CSV_COLUMNS, DEFAULTS)

def features_and_labels(features):
  label = features.pop('duration') # this is what we will train for
  features.pop('bike_id')
  return features, label

def read_dataset(pattern, batch_size, mode=tf.estimator.ModeKeys.TRAIN, truncate=None):
  dataset = load_dataset(pattern, batch_size)
  dataset = dataset.map(features_and_labels, num_parallel_calls=tf.data.experimental.AUTOTUNE)
  if mode == tf.estimator.ModeKeys.TRAIN:
    dataset = dataset.repeat().shuffle(batch_size*10)
    # dataset = dataset.repeat()
  dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
  # dataset = dataset.prefetch(1)
  if truncate is not None:
    dataset = dataset.take(truncate)
  return dataset

def get_layers():

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
        'end_station_id' : tf.feature_column.categorical_column_with_hash_bucket(
            'end_station_id', hash_bucket_size=800),
        'start_station_id' : tf.feature_column.categorical_column_with_hash_bucket(
            'start_station_id', hash_bucket_size=800),
        'loc_cross' : tf.feature_column.categorical_column_with_hash_bucket(
            'loc_cross', hash_bucket_size=21000),
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
  return inputs, sparse, real

# Build a wide-and-deep model.
def wide_and_deep_classifier(inputs, linear_feature_columns, dnn_feature_columns,
    num_hidden_layers, dnn_hidden_units1, learning_rate):
    deep = tf.keras.layers.DenseFeatures(dnn_feature_columns, name='deep_inputs')(inputs)
    layers = [dnn_hidden_units1]
    if num_hidden_layers > 1:
      layers += [int(dnn_hidden_units1/(x*2)) for x in range(1, num_hidden_layers)]
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
