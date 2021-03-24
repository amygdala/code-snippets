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

def deploy_model(
    project: str,
    endpoint_disp_name: str,
    model_name: str,
    deployed_model_display_name: str,
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
    timeout: int = 7200,
    ):

  import logging
  from google.cloud import aiplatform

  logging.getLogger().setLevel(logging.INFO)

  def create_endpoint(
      project: str,
      display_name: str,
      client,
      location: str = "us-central1",
      api_endpoint: str = "us-central1-aiplatform.googleapis.com",
      timeout: int = 300,
      ):

    endpoint = {"display_name": display_name}
    parent = f"projects/{project}/locations/{location}"
    response = client.create_endpoint(parent=parent, endpoint=endpoint)
    print("Long running operation:", response.operation.name)
    create_endpoint_response = response.result(timeout=timeout)
    print("create_endpoint_response:", create_endpoint_response)
    endpoint_name = create_endpoint_response.name
    logging.info('endpoint name: %s', endpoint_name)
    return endpoint_name

  # The AI Platform services require regional API endpoints.
  client_options = {"api_endpoint": api_endpoint}
  # Initialize client that will be used to create and send requests.
  # This client only needs to be created once, and can be reused for multiple requests.
  client = aiplatform.gapic.EndpointServiceClient(client_options=client_options)

  # create endpoint
  logging.info('creating endpoint %s', endpoint_disp_name)
  endpoint_path = create_endpoint(project, endpoint_disp_name, client)
  logging.info("using endpoint path ID %s", endpoint_path)

  deployed_model = {
      # format: 'projects/{project}/locations/{location}/models/{model}'
      "model": model_name,
      "display_name": deployed_model_display_name,
      # `dedicated_resources` must be used for non-AutoML models
      "dedicated_resources": {
          "min_replica_count": 1,
          "machine_spec": {
              "machine_type": "n1-standard-2",
              # Accelerators can be used only if the model specifies a GPU image.
              # 'accelerator_type': aiplatform.gapic.AcceleratorType.NVIDIA_TESLA_K80,
              # 'accelerator_count': 1,
          },
      },
  }
  # key '0' assigns traffic for the newly deployed model
  # Traffic percentage values must add up to 100
  # Leave dictionary empty if endpoint should not accept any traffic
  traffic_split = {"0": 100}
#   endpoint = client.endpoint_path(
#       project=project, location=location, endpoint=endpoint_id
#   )
  response = client.deploy_model(
      endpoint=endpoint_path, deployed_model=deployed_model, traffic_split=traffic_split
  )
  logging.info("Long running operation: %s", response.operation.name)
  deploy_model_response = response.result(timeout=timeout)
  logging.info("deploy_model_response: %s", deploy_model_response)
  # TODO: output status info in some form


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(deploy_model,
      output_component_file='../model_deploy_component.yaml',
      base_image='gcr.io/google-samples/bw-aiplatform:v1')
