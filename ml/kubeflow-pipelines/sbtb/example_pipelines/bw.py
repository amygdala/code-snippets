# Copyright 2019 Google LLC
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


import kfp.dsl as dsl
import kfp.gcp as gcp
import kfp.components as comp
from kfp.dsl.types import GCSPath, String


COPY_ACTION = 'copy_data'
TRAIN_ACTION = 'train'
WORKSPACE_NAME = 'ws_gh_summ'
DATASET = 'dataset'
MODEL = 'model'

train_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/amygdala/code-snippets/sbtb/ml/kubeflow-pipelines/sbtb/components/train_component.yaml' # pylint: disable=line-too-long
  )
serve_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/amygdala/code-snippets/sbtb/ml/kubeflow-pipelines/sbtb/components/serve_component.yaml' # pylint: disable=line-too-long
  )


@dsl.pipeline(
  name='bikes_weather',
  description='Model bike rental duration given weather'
)
def bikes_weather(  #pylint: disable=unused-argument
  export_dir: GCSPath = 'gs://aju-vtests2-pipelines/bwmodel/trained_model/export/bikesw',
  working_dir: GCSPath = 'gs://YOUR_GCS_DIR_HERE',
  data_dir: GCSPath = 'gs://aju-dev-demos-codelabs/bikes_weather/',
  epochs: 'Integer' = 1,
  steps_per_epoch: 'Integer' = -1 ,  # if -1, don't override normal calcs based on dataset size
  load_checkpoint: String = ''
  ):


  train = train_op(
    data_dir=data_dir,
    workdir='%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
    epochs=epochs, steps_per_epoch=steps_per_epoch,
    load_checkpoint=load_checkpoint
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  serve = serve_op(
    model_path=train.outputs['train_output_path'],
    model_name='bikesw'
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  train.set_gpu_limit(1)

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(bikes_weather, __file__ + '.tar.gz')
