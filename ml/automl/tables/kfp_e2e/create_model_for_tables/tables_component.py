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


def automl_create_model_for_tables(
  gcp_project_id: str,
  gcp_region: str,
  dataset_display_name: str,
  api_endpoint: str = None,
  model_display_name: str = None,
  model_prefix: str = 'bwmodel',
  optimization_objective: str = None,
  include_column_spec_names: list = None,
  exclude_column_spec_names: list = None,
  train_budget_milli_node_hours: int = 1000,
) -> NamedTuple('Outputs', [('model_display_name', str), ('model_name', str), ('model_id', str)]):

  import subprocess
  import sys
  # we could build a base image that includes these libraries if we don't want to do
  # the dynamic installation when the step runs.
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'googleapis-common-protos==1.6.0', '--no-warn-script-location'],
      env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-cloud-automl==0.9.0', '--quiet', '--no-warn-script-location'],
      env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)

  import google
  import logging
  from google.api_core.client_options import ClientOptions
  from google.cloud import automl_v1beta1 as automl
  import time

  logging.getLogger().setLevel(logging.INFO)  # TODO: make level configurable
  # TODO: we could instead check for region 'eu' and use 'eu-automl.googleapis.com:443'endpoint
  # in that case, instead of requiring endpoint to be specified.
  if api_endpoint:
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region,
        client_options=client_options)
  else:
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region)

  if not model_display_name:
    model_display_name = '{}_{}'.format(model_prefix, str(int(time.time())))

  logging.info('Training model {}...'.format(model_display_name))
  response = client.create_model(
    model_display_name,
    train_budget_milli_node_hours=train_budget_milli_node_hours,
    dataset_display_name=dataset_display_name,
    optimization_objective=optimization_objective,
    include_column_spec_names=include_column_spec_names,
    exclude_column_spec_names=exclude_column_spec_names,
  )

  logging.info("Training operation: {}".format(response.operation))
  logging.info("Training operation name: {}".format(response.operation.name))
  logging.info("Training in progress. This operation may take multiple hours to complete.")
  # block termination of the op until training is finished.
  result = response.result()
  logging.info("Training completed: {}".format(result))
  model_name = result.name
  model_id = model_name.rsplit('/', 1)[-1]
  print('model name: {}, model id: {}'.format(model_name, model_id))
  return (model_display_name, model_name, model_id)



if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(automl_create_model_for_tables,
      output_component_file='tables_component.yaml',
      base_image='python:3.7')
