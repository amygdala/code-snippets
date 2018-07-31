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

from tensorflow_transform.beam import impl as beam_impl
from tensorflow_transform.tf_metadata import dataset_metadata
from tensorflow_transform.tf_metadata import dataset_schema

from tensorflow_transform import coders as tft_coders

import taxi_schema.taxi_schema as ts

# Number of buckets used by tf.transform for encoding each feature.
FEATURE_BUCKET_COUNT = 10
# Number of vocabulary terms used for encoding VOCAB_FEATURES by tf.transform
VOCAB_SIZE = 1000
# Count of out-of-vocab buckets in which unrecognized VOCAB_FEATURES are hashed.
OOV_SIZE = 10


def preprocessing_fn(inputs):
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
        inputs[key], top_k=VOCAB_SIZE, num_oov_buckets=OOV_SIZE)

  for key in ts.BUCKET_FEATURE_KEYS:
    outputs[key] = transform.bucketize(inputs[key], FEATURE_BUCKET_COUNT)

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


