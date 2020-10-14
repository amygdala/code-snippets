# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import NamedTuple
# from kfp.components import InputPath, OutputPath


# An example of how the model eval info could be used to make decisions about whether or not
# to deploy the model.
def eval_metrics(
  metrics: str,
  thresholds: str
) -> NamedTuple('Outputs', [('deploy', str)]):

  import json
  import logging

  def regression_threshold_check(metrics_info):
    # ...
    for k, v in thresholds_dict.items():
      logging.info('k {}, v {}'.format(k, v))
      if k in ['root_mean_squared_error', 'mae']:
        if metrics_info[k][-1] > v:
          logging.info('{} > {}; returning False'.format(metrics_info[k][0], v))
          return ('False', )
    return ('deploy', )

  logging.getLogger().setLevel(logging.INFO)  # TODO: make level configurable

  thresholds_dict = json.loads(thresholds)
  logging.info('thresholds dict: {}'.format(thresholds_dict))
  logging.info('metrics: %s', metrics)
  metrics_dict = json.loads(metrics)

  logging.info("got metrics info: %s", metrics_dict)
  res = regression_threshold_check(metrics_dict)
  logging.info('deploy decision: %s', res)
  return res


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(eval_metrics,
      output_component_file='../../eval_metrics_component.yaml', base_image='gcr.io/deeplearning-platform-release/tf2-cpu.2-3:latest')
