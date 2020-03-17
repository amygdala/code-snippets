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
from kfp.components import InputPath, OutputPath


def automl_eval_tables_model(
	gcp_project_id: str,
	gcp_region: str,
  model_display_name: str,
  bucket_name: str,
  gcs_path: str,
  eval_data_path: OutputPath('evals'),
  mlpipeline_ui_metadata_path: OutputPath('UI_metadata'),
  api_endpoint: str = None,

) -> NamedTuple('Outputs', [
    # ('evals_gcs_path', str),
    ('feat_list', str)]):
  import subprocess
  import sys
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'googleapis-common-protos==1.6.0',
     '--no-warn-script-location'], env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)
  subprocess.run([sys.executable, '-m', 'pip', 'install', 'google-cloud-automl==0.9.0',
     '--no-warn-script-location'], env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)
  subprocess.run([sys.executable, '-m', 'pip', 'install',
     'matplotlib', 'pathlib2', 'google-cloud-storage',
     '--no-warn-script-location'], env={'PIP_DISABLE_PIP_VERSION_CHECK': '1'}, check=True)


  import google
  import json
  import logging
  import pickle
  import pathlib2


  from google.api_core.client_options import ClientOptions
  from google.api_core import exceptions
  from google.cloud import automl_v1beta1 as automl
  from google.cloud.automl_v1beta1 import enums
  from google.cloud import storage


  def upload_blob(bucket_name, source_file_name, destination_blob_name,
      public_url=False):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logging.info("File {} uploaded to {}.".format(
            source_file_name, destination_blob_name))
    if public_url:
      blob.make_public()
      logging.info("Blob {} is publicly accessible at {}".format(
              blob.name, blob.public_url))
    return blob.public_url


  def get_model_details(client, model_display_name):
    try:
        model = client.get_model(model_display_name=model_display_name)
    except exceptions.NotFound:
        logging.info("Model %s not found." % model_display_name)
        return (None, None)

    model = client.get_model(model_display_name=model_display_name)
    # Retrieve deployment state.
    if model.deployment_state == enums.Model.DeploymentState.DEPLOYED:
        deployment_state = "deployed"
    else:
        deployment_state = "undeployed"
    # get features of top global importance
    feat_list = [
        (column.feature_importance, column.column_display_name)
        for column in model.tables_model_metadata.tables_model_column_info
    ]
    feat_list.sort(reverse=True)
    if len(feat_list) < 10:
        feat_to_show = len(feat_list)
    else:
        feat_to_show = 10

    # Display the model information.
    # TODO: skip this?
    logging.info("Model name: {}".format(model.name))
    logging.info("Model id: {}".format(model.name.split("/")[-1]))
    logging.info("Model display name: {}".format(model.display_name))
    logging.info("Features of top importance:")
    for feat in feat_list[:feat_to_show]:
        logging.info(feat)
    logging.info("Model create time:")
    logging.info("\tseconds: {}".format(model.create_time.seconds))
    logging.info("\tnanos: {}".format(model.create_time.nanos))
    logging.info("Model deployment state: {}".format(deployment_state))

    generate_fi_ui(feat_list)
    return (model, feat_list)


  def generate_fi_ui(feat_list):
    import matplotlib.pyplot as plt

    image_suffix = '{}/gfi.png'.format(gcs_path)
    res = list(zip(*feat_list))
    x = list(res[0])
    y = list(res[1])
    y_pos = list(range(len(y)))
    plt.barh(y_pos, x, alpha=0.5)
    plt.yticks(y_pos, y)
    plt.savefig('/gfi.png')
    public_url = upload_blob(bucket_name, '/gfi.png', image_suffix, public_url=True)
    logging.info('using image url {}'.format(public_url))

    html_suffix = '{}/gfi.html'.format(gcs_path)
    with open('/gfi.html', 'w') as f:
      f.write('<html><head></head><body><h1>Global Feature Importance</h1>\n<img src="{}" width="97%"/></body></html>'.format(public_url))
    upload_blob(bucket_name, '/gfi.html', html_suffix)
    html_source = 'gs://{}/{}'.format(bucket_name, html_suffix)
    logging.info('metadata html source: {}'.format(html_source))

    metadata = {
      'outputs' : [
      {
        'type': 'web-app',
        'storage': 'gcs',
        'source': html_source
      }]}
    logging.info('using metadata dict {}'.format(json.dumps(metadata)))
    # with open('/mlpipeline-ui-metadata.json', 'w') as f:
      # json.dump(metadata, f)
    logging.info('using metadata ui path: {}'.format(mlpipeline_ui_metadata_path))
    with open(mlpipeline_ui_metadata_path, 'w') as mlpipeline_ui_metadata_file:
      mlpipeline_ui_metadata_file.write(json.dumps(metadata))


  logging.getLogger().setLevel(logging.INFO)  # TODO: make level configurable
  # TODO: we could instead check for region 'eu' and use 'eu-automl.googleapis.com:443'endpoint
  # in that case, instead of requiring endpoint to be specified.
  if api_endpoint:
    client_options = ClientOptions(api_endpoint=api_endpoint)
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region,
        client_options=client_options)
  else:
    client = automl.TablesClient(project=gcp_project_id, region=gcp_region)

  (model, feat_list) = get_model_details(client, model_display_name)


  evals = list(client.list_model_evaluations(model_display_name=model_display_name))
  with open('temp_oput_regression', "w") as f:
    f.write('Model evals:\n{}'.format(evals))
  pstring = pickle.dumps(evals)

  # write to eval_data_path
  if eval_data_path:
    logging.info("eval_data_path: %s", eval_data_path)
    try:
      pathlib2.Path(eval_data_path).parent.mkdir(parents=True)
    except FileExistsError:
      pass
    pathlib2.Path(eval_data_path).write_bytes(pstring)

  feat_list_string = json.dumps(feat_list)
  # return(gcs_path, feat_list_string)
  return(feat_list_string)


if __name__ == '__main__':
	import kfp
	kfp.components.func_to_container_op(automl_eval_tables_model,
      output_component_file='tables_eval_component.yaml', base_image='python:3.7')

# if __name__ == '__main__':

# #   (eval_hex, features) = automl_eval_tables_model('aju-vtests2', 'us-central1', model_display_name='somodel_1579284627')
#   (eval_hex, features) = automl_eval_tables_model('aju-vtests2', 'us-central1',
#       bucket_name='aju-pipelines', model_display_name='bwmodel_1579017140',
#       # gcs_path='automl_evals/testing/somodel_1579284627',
#       eval_data_path=None)
# #   with open('temp_oput', "w") as f:
# #     f.write(eval_hex)

