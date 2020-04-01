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


def automl_set_dataset_schema(
  gcp_project_id: str,
  gcp_region: str,
  display_name: str,
  target_col_name: str,
  schema_info: str = '{}',  # dict with key of col name, value an array with [type, nullable]
  time_col_name: str = None,
  test_train_col_name: str = None,
  api_endpoint: str = None,
) -> NamedTuple('Outputs', [('display_name', str)]):
  import sys
  import subprocess
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'googleapis-common-protos==1.6.0',
      '--no-warn-script-location'], env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-cloud-automl==0.9.0',
      '--quiet', '--no-warn-script-location'],
      env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)

  import json
  import google
  import logging
  from google.api_core.client_options import ClientOptions
  from google.cloud import automl_v1beta1 as automl

  def update_column_spec(client,
                         dataset_display_name,
                         column_spec_display_name,
                         type_code,
                         nullable=None
                         ):

    logging.info("Setting {} to type {} and nullable {}".format(
        column_spec_display_name, type_code, nullable))
    response = client.update_column_spec(
        dataset_display_name=dataset_display_name,
        column_spec_display_name=column_spec_display_name,
        type_code=type_code,
        nullable=nullable
    )

    # synchronous check of operation status.
    print("Table spec updated. {}".format(response))

  def update_dataset(client,
                     dataset_display_name,
                     target_column_spec_name=None,
                     time_column_spec_name=None,
                     test_train_column_spec_name=None):

    if target_column_spec_name:
      response = client.set_target_column(
          dataset_display_name=dataset_display_name,
          column_spec_display_name=target_column_spec_name
      )
      print("Target column updated. {}".format(response))
    if time_column_spec_name:
      response = client.set_time_column(
          dataset_display_name=dataset_display_name,
          column_spec_display_name=time_column_spec_name
      )
      print("Time column updated. {}".format(response))

  logging.getLogger().setLevel(logging.INFO)  # TODO: make level configurable


  # TODO: we could instead check for region 'eu' and use 'eu-automl.googleapis.com:443'endpoint
  # in that case, instead of requiring endpoint to be specified.
  if api_endpoint:
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region,
      client_options=client_options)
  else:
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region)

  schema_dict = json.loads(schema_info)
  # Update cols for which the desired schema was not inferred.
  if schema_dict:
    for k, v in schema_dict.items():
      update_column_spec(client, display_name, k, v[0], nullable=v[1])

  # Update the dataset with info about the target col, plus optionally info on how to split on
  # a time col or a test/train col.
  update_dataset(client, display_name,
                 target_column_spec_name=target_col_name,
                 time_column_spec_name=time_col_name,
                 test_train_column_spec_name=test_train_col_name)

  return display_name


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(automl_set_dataset_schema,
      output_component_file='tables_schema_component.yaml', base_image='python:3.7')
