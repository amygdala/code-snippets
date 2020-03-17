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

def automl_import_data_for_tables(
  # dataset_path,
  path: str,
  gcp_project_id: str,
  gcp_region: str,
  dataset_display_name: str,
  api_endpoint: str = None,
) -> NamedTuple('Outputs', [('dataset_display_name', str)]):
  import sys
  import subprocess
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'googleapis-common-protos==1.6.0',  '--no-warn-script-location'], env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-cloud-automl==0.9.0', '--quiet', '--no-warn-script-location'], env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)

  import google
  import logging
  from google.api_core.client_options import ClientOptions
  from google.cloud import automl_v1beta1 as automl

  def list_column_specs(client,
                        dataset_display_name,
                        filter_=None):
      """List all column specs."""
      result = []

      # List all the table specs in the dataset
      response = client.list_column_specs(
          dataset_display_name=dataset_display_name, filter_=filter_)
      logging.info("List of column specs:")
      for column_spec in response:
          # Display the column_spec information.
          logging.info("Column spec name: {}".format(column_spec.name))
          logging.info("Column spec id: {}".format(column_spec.name.split("/")[-1]))
          logging.info("Column spec display name: {}".format(column_spec.display_name))
          logging.info("Column spec data type: {}".format(column_spec.data_type))

          result.append(column_spec)
      return result

  logging.getLogger().setLevel(logging.INFO)  # TODO: make level configurable

  # TODO: we could instead check for region 'eu' and use 'eu-automl.googleapis.com:443'endpoint
  # in that case, instead of requiring endpoint to be specified.
  if api_endpoint:
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region,
      client_options=client_options)
  else:
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region)

  response = None
  if path.startswith('bq'):
    response = client.import_data(
      dataset_display_name=dataset_display_name, bigquery_input_uri=path
    )
  else:
    # Get the multiple Google Cloud Storage URIs.
    input_uris = path.split(",")
    response = client.import_data(
      dataset_display_name=dataset_display_name,
      gcs_input_uris=input_uris
      )
  logging.info("Processing import... This can take a while.")
  # synchronous check of operation status.
  logging.info("Data imported. {}".format(response.result()))
  logging.info("Response metadata: {}".format(response.metadata))
  logging.info("Operation name: {}".format(response.operation.name))

  # now list the inferred col schema
  list_column_specs(client, dataset_display_name)
  return (dataset_display_name)



# if __name__ == "__main__":
#     automl_import_data_for_tables('bq://aju-dev-demos.london_bikes_weather.bikes_weather',
#         'aju-vtests2', 'us-central1', 'comp_test1')


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(automl_import_data_for_tables,
      output_component_file='tables_component.yaml', base_image='python:3.7')
