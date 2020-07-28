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

import time 

import kfp.dsl as dsl
import kfp.gcp as gcp
import kfp.components as comp
from kfp.dsl.types import GCSPath, String

# train_op = comp.load_component_from_url(
#   'https://raw.githubusercontent.com/amygdala/code-snippets/master/ml/kubeflow-pipelines/sbtb/components/train_component.yaml' # pylint: disable=line-too-long
#   )
serve_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/amygdala/code-snippets/master/ml/kubeflow-pipelines/sbtb/components/serve_component.yaml' # pylint: disable=line-too-long
  )


@dsl.pipeline(
  name='bikes_weather_keras_tuner',
  description='Model bike rental duration given weather, use Keras Tuner'
)
def bikes_weather_hptune(  #pylint: disable=unused-argument
  tune_epochs: int = 2,
  train_epochs: int = 3,
  num_tuners: int = 3,
  bucket_name: str = 'aju-pipelines',
  tuner_dir_prefix: str = 'hptest',
  tuner_proj: str = 'p1',
  max_trials: int = 32,
  working_dir: str = 'gs://YOUR_GCS_DIR_HERE',
  data_dir: str = 'gs://aju-dev-demos-codelabs/bikes_weather/',
  steps_per_epoch: int = -1 ,  # if -1, don't override normal calcs based on dataset size
  # load_checkpoint: str = ''
  ):

  hptune = dsl.ContainerOp(
      name='ktune',
      image='gcr.io/aju-vtests2/ml-pipeline-bikes-dep:v5',
      arguments=['--epochs', tune_epochs, '--num-tuners', num_tuners, 
          '--tuner-dir', '{}_{}'.format(tuner_dir_prefix, int(time.time())),
          '--tuner-proj', tuner_proj, '--bucket-name', bucket_name, '--max-trials', max_trials,
          '--deploy'
          ],
      file_outputs={'hps': '/tmp/hps.json'},
      )
  train = dsl.ContainerOp(
      name='train',
      image='gcr.io/aju-vtests2/ml-pl-bikes-train:v1',
      arguments=[
          '--data-dir', data_dir, '--steps-per-epoch', steps_per_epoch,
          '--workdir', '%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
          # '--load-checkpoint', load_checkpoint,
          '--epochs', train_epochs, '--hptune-results', hptune.outputs['hps']
          ],
      file_outputs={'train_output_path': '/tmp/train_output_path.txt'},
    )

  # train = train_op(
  #   data_dir=data_dir,
  #   workdir='%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
  #   epochs=epochs, steps_per_epoch=steps_per_epoch,
  #   load_checkpoint=load_checkpoint
  #   ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  serve = serve_op(
    model_path=train.outputs['train_output_path'],
    model_name='bikesw'
    )

  train.set_gpu_limit(2)

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(bikes_weather_hptune, __file__ + '.tar.gz')
