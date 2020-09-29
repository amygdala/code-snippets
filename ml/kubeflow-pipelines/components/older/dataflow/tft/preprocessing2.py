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

"""Preprocessing function, for applying tf.transform to the chicago_taxi data."""

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

import taxi_schema.taxi_schema as taxi


# Number of buckets used by tf.transform for encoding each feature.
FEATURE_BUCKET_COUNT = 2
# Number of vocabulary terms used for encoding VOCAB_FEATURES by tf.transform
VOCAB_SIZE = 10
# Count of out-of-vocab buckets in which unrecognized VOCAB_FEATURES are hashed.
OOV_SIZE = 1

def _fill_in_missing(x):
  """Replace missing values in a SparseTensor.

  Fills in missing values of `x` with '' or 0, and converts to a dense tensor.

  Args:
    x: A `SparseTensor` of rank 2.  Its dense shape should have size at most 1
      in the second dimension.

  Returns:
    A rank 1 tensor where missing values of `x` have been filled in.
  """
  default_value = '' if x.dtype == tf.string else 0
  return tf.squeeze(
      tf.sparse_to_dense(x.indices, [x.dense_shape[0], 1], x.values,
                         default_value),
      axis=1)


def preprocessing_fn(inputs):
  """tf.transform's callback function for preprocessing inputs.

  Args:
    inputs: map from feature keys to raw not-yet-transformed features.

  Returns:
    Map from string feature key to transformed feature operations.
  """
  outputs = {}
  for key in taxi.DENSE_FLOAT_FEATURE_KEYS:
    # Preserve this feature as a dense float, setting nan's to the mean.
    outputs[taxi.transformed_name(key)] = transform.scale_to_z_score(
        _fill_in_missing(inputs[key]))

  for key in taxi.VOCAB_FEATURE_KEYS:
    # Build a vocabulary for this feature.
    outputs[
        taxi.transformed_name(key)] = transform.compute_and_apply_vocabulary(
            _fill_in_missing(inputs[key]),
            top_k=taxi.VOCAB_SIZE,
            num_oov_buckets=taxi.OOV_SIZE)

  for key in taxi.BUCKET_FEATURE_KEYS:
    outputs[taxi.transformed_name(key)] = transform.bucketize(
        _fill_in_missing(inputs[key]), taxi.FEATURE_BUCKET_COUNT)

  for key in taxi.CATEGORICAL_FEATURE_KEYS:
    outputs[taxi.transformed_name(key)] = _fill_in_missing(inputs[key])

  # Was this passenger a big tipper?
  taxi_fare = _fill_in_missing(inputs[taxi.FARE_KEY])
  tips = _fill_in_missing(inputs[taxi.LABEL_KEY])
  outputs[taxi.transformed_name(taxi.LABEL_KEY)] = tf.where(
      tf.is_nan(taxi_fare),
      tf.cast(tf.zeros_like(taxi_fare), tf.int64),
      # Test if the tip was > 5% of the fare.
      tf.cast(
          tf.greater(tips, tf.multiply(taxi_fare, tf.constant(0.05))),
          tf.int64))

  return outputs
