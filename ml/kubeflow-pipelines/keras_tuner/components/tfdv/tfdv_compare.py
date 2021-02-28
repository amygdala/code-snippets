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

from typing import NamedTuple


def tfdv_detect_drift(
    stats_older_path: str, stats_new_path: str
) -> NamedTuple('Outputs', [('drift', str)]):

  import logging
  import time

  import tensorflow_data_validation as tfdv
  import tensorflow_data_validation.statistics.stats_impl

  logging.getLogger().setLevel(logging.INFO)
  logging.info('stats_older_path: %s', stats_older_path)
  logging.info('stats_new_path: %s', stats_new_path)

  if stats_older_path == 'none':
    return ('true', )

  stats1 = tfdv.load_statistics(stats_older_path)
  stats2 = tfdv.load_statistics(stats_new_path)

  schema1 = tfdv.infer_schema(statistics=stats1)
  tfdv.get_feature(schema1, 'duration').drift_comparator.jensen_shannon_divergence.threshold = 0.01
  drift_anomalies = tfdv.validate_statistics(
      statistics=stats2, schema=schema1, previous_statistics=stats1)
  logging.info('drift analysis results: %s', drift_anomalies.drift_skew_info)

  from google.protobuf.json_format import MessageToDict
  d = MessageToDict(drift_anomalies)
  val = d['driftSkewInfo'][0]['driftMeasurements'][0]['value']
  thresh = d['driftSkewInfo'][0]['driftMeasurements'][0]['threshold']
  logging.info('value %s and threshold %s', val, thresh)
  res = 'true'
  if val < thresh:
    res = 'false'
  logging.info('train decision: %s', res)
  return (res, )


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(tfdv_detect_drift,
      output_component_file='../tfdv_drift_component.yaml',
      base_image='gcr.io/google-samples/tfdv-tests:v1')
