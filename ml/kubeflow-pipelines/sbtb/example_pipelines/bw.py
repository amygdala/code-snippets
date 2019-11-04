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

# copydata_op = comp.load_component_from_url(
#   'https://raw.githubusercontent.com/kubeflow/examples/master/github_issue_summarization/pipelines/components/t2t/datacopy_component.yaml'  # pylint: disable=line-too-long
#   )

# train_op = comp.load_component_from_url(
#   'https://raw.githubusercontent.com/kubeflow/examples/master/github_issue_summarization/pipelines/components/t2t/train_component.yaml' # pylint: disable=line-too-long
#   )

# metadata_log_op = comp.load_component_from_url(
#   'https://raw.githubusercontent.com/kubeflow/examples/master/github_issue_summarization/pipelines/components/t2t/metadata_log_component.yaml' # pylint: disable=line-too-long
#   )

@dsl.pipeline(
  name='bikes_weather',
  description='Model bike rental duration given weather'
)
def bikes_weather(  #pylint: disable=unused-argument
  export_dir: GCSPath = 'gs://aju-vtests2-pipelines/bwmodel/trained_model/export/bikesw',
  working_dir: GCSPath = 'gs://YOUR_GCS_DIR_HERE',
  data_dir: GCSPath = 'gs://aju-dev-demos-codelabs/bikes_weather/',
  epochs: 'Integer' = 1,
  load_checkpoint: String = ''
  ):


  train = dsl.ContainerOp(
      name='train',
      image='gcr.io/aju-vtests2/ml-pipeline-bikes-train',
      arguments=["--data-dir", data_dir, "--workdir", '%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
          "--load-checkpoint", load_checkpoint, "--epochs", epochs
          ]
      ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  serve = dsl.ContainerOp(
      name='serve',
      image='gcr.io/aju-vtests2/ml-pipeline-tfserve',
      arguments=["--model_name", 'bikesw',
          # "--model_path", export_dir
          "--model_path", '%s/%s/bwmodel/trained_model/export/bikesw' % (working_dir, dsl.RUN_ID_PLACEHOLDER)
          ]
      ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  serve.after(train)
  train.set_gpu_limit(1)

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(bikes_weather, __file__ + '.tar.gz')
