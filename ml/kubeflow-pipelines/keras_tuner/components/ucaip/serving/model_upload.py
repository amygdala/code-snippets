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

from kfp.components import OutputPath


def upload_model(
    project: str,
    display_name: str,
    image_uri: str,
    artifact_uri: str,
    location: str, # "us-central1",
    api_endpoint: str, #"us-central1-aiplatform.googleapis.com",
    timeout: int, # 1800,
    model_id: OutputPath('String')
    ):
  import logging
  import subprocess
  from google.cloud import aiplatform

  logging.getLogger().setLevel(logging.INFO)
  metadata_schema_uri = ""

  # The AI Platform services require regional API endpoints.
  client_options = {"api_endpoint": api_endpoint}
  # Initialize client that will be used to create and send requests.
  # This client only needs to be created once, and can be reused for multiple requests.
  client = aiplatform.gapic.ModelServiceClient(client_options=client_options)
  model = {
      "display_name": display_name,
      "metadata_schema_uri": metadata_schema_uri,
      # The artifact_uri should be the path to a GCS directory containing
      # saved model artifacts.  The bucket must be accessible for the
      # project's AI Platform service account and in the same region as
      # the api endpoint.
      "artifact_uri": artifact_uri,
      "container_spec": {
          "image_uri": image_uri,
          "command": [],
          "args": [],
          "env": [],
          "ports": [],
          "predict_route": "",
          "health_route": "",
      },
  }
  parent = f"projects/{project}/locations/{location}"
  response = client.upload_model(parent=parent, model=model)
  logging.info("Long running operation: %s", response.operation.name)
  upload_model_response = response.result(timeout=timeout)
  logging.info("upload_model_response: %s", upload_model_response)
  model_path = upload_model_response.model
  logging.info('got model path: %s', model_path)
  with open('temp.txt', "w") as outfile:
    outfile.write(model_path)
  subprocess.run(['gsutil', 'cp', 'temp.txt', model_id])



if __name__ == '__main__':
  # upload_model('aju-vtests2', display_name='sdk_test1', metadata_schema_uri="",
  #     image_uri='us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-3:latest',
  #     artifact_uri='gs://aju-pipelines/v64/077ae97e-9c6d-4c1c-b5a1-fc2e95fb7dbb/0/bwmodel/trained_model/export/bikesw/1615937808')
  import kfp
  kfp.components.func_to_container_op(upload_model,
      output_component_file='../model_upload_component.yaml',
      base_image='gcr.io/aju-vtests2/bw-aiplatform:v1')


# gcloud beta ai models upload --region=us-central1 --display-name=bw2 --container-image-uri=us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-3:latest --artifact-uri=gs://aju-pipelines/ktune13/f8515c75-32b7-47a4-af70-5ff24362eccc/0/bwmodel/trained_model/export/bikesw/1603733739