# Copyright 2021 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from kfp.v2 import dsl
from kfp.v2 import compiler
from kfp import components

model_train_op = components.load_component_from_file(
  './model_train_component.yaml'
  )

model_deploy_op = components.load_component_from_file(
  './model_deploy_component.yaml'
  )


@dsl.pipeline(
  name='ucaip-model-train',
  description='ucaip model train'
)
def model_train_pipeline(
    prediction_image_uri: str = 'us-docker.pkg.dev/cloud-aiplatform/prediction/tf2-cpu.2-3:latest',
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
    # project: str = 'aju-vtests2',
    project: str = 'CHANGE THIS',
    training_display_name: str = 'CHANGE THIS',
    model_display_name: str = 'CHANGE THIS',
    endpoint_disp_name: str = 'CHANGE THIS',
    train_container_type: str = 'prebuilt',
    executor_image_uri: str = 'us-docker.pkg.dev/cloud-aiplatform/training/tf-gpu.2-3:latest',
    # package_uri: str = 'gs://aju-pipelines/ucaip/training1/bw-trainer-0.1.tar.gz',
    package_uri: str = 'CHANGE THIS',  # TODO: upload publicly readable version
    python_module: str = 'trainer.task',
    container_image_uri: str = '',
    # base_output_directory_prefix: str = 'gs://aju-pipelines/ucaip/training2/',
    base_output_directory_prefix: str = 'CHANGE THIS',
    timeout: int = 7200,
    hptune_dict: str = '{"num_hidden_layers": 3, "hidden_size": 32, "learning_rate": 0.01, "epochs": 3, "steps_per_epoch": -1}',
    data_dir: str = 'gs://aju-dev-demos-codelabs/bikes_weather/'
    ):

  model_train = model_train_op(
    project, training_display_name, model_display_name,
    train_container_type,
    executor_image_uri, package_uri, python_module,
    container_image_uri,
    base_output_directory_prefix,
    prediction_image_uri,
    location, api_endpoint,
    data_dir,
    hptune_dict
  )

  model_deploy = model_deploy_op(
    project, endpoint_disp_name,
    model_train.outputs['model_id'],
    model_display_name,
    location, api_endpoint, timeout
  )



if __name__ == '__main__':
  PIPELINE_ROOT = 'gs://aju-pipelines/pipeline_root/ucaiptests'
  compiler.Compiler().compile(pipeline_func=model_train_pipeline,
                              pipeline_root=PIPELINE_ROOT,
                              output_path='ucaip_train_pipeline_spec.json')
