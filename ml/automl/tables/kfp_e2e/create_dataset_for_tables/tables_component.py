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


def automl_create_dataset_for_tables(
  gcp_project_id: str,
  gcp_region: str,
  dataset_display_name: str,
  api_endpoint: str = None,
  tables_dataset_metadata: dict = {},
) -> NamedTuple('Outputs', [('dataset_path', str), ('create_time', str), ('dataset_id', str)]):

  import sys
  import subprocess
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'googleapis-common-protos==1.6.0',
      '--no-warn-script-location'],
      env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-cloud-automl==0.9.0',
      '--quiet', '--no-warn-script-location'],
      env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)

  import google
  import logging
  from google.api_core.client_options import ClientOptions
  from google.cloud import automl_v1beta1 as automl

  logging.getLogger().setLevel(logging.INFO)  # TODO: make level configurable
  # TODO: we could instead check for region 'eu' and use 'eu-automl.googleapis.com:443'endpoint
  # in that case, instead of requiring endpoint to be specified.
  if api_endpoint:
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region,
        client_options=client_options)
  else:
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region)

  try:
    # Create a dataset with the given display name
    dataset = client.create_dataset(dataset_display_name, metadata=tables_dataset_metadata)
    # Log info about the created dataset
    logging.info("Dataset name: {}".format(dataset.name))
    logging.info("Dataset id: {}".format(dataset.name.split("/")[-1]))
    logging.info("Dataset display name: {}".format(dataset.display_name))
    logging.info("Dataset metadata:")
    logging.info("\t{}".format(dataset.tables_dataset_metadata))
    logging.info("Dataset example count: {}".format(dataset.example_count))
    logging.info("Dataset create time:")
    logging.info("\tseconds: {}".format(dataset.create_time.seconds))
    logging.info("\tnanos: {}".format(dataset.create_time.nanos))
    print(str(dataset))
    dataset_id = dataset.name.rsplit('/', 1)[-1]
    return (dataset.name, str(dataset.create_time), dataset_id)
  except google.api_core.exceptions.GoogleAPICallError as e:
    logging.warning(e)
    raise e


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(automl_create_dataset_for_tables,
      output_component_file='tables_component.yaml', base_image='python:3.7')
