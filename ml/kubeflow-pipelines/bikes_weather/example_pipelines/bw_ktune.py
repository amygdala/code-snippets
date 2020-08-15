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
# from kfp.dsl.types import GCSPath, String

# train_op = comp.load_component_from_url(
#   'https://raw.githubusercontent.com/amygdala/code-snippets/master/ml/kubeflow-pipelines/sbtb/components/train_component.yaml' # pylint: disable=line-too-long
#   )
serve_op = comp.load_component_from_file(
  '/Users/amyu/devrel/code-snippets/ml/kubeflow-pipelines/bikes_weather/components/serve_component_a.yaml' # pylint: disable=line-too-long
  )


@dsl.pipeline(
  name='bikes_weather_keras_tuner',
  description='Model bike rental duration given weather, use Keras Tuner'
)
def bikes_weather_hptune(  #pylint: disable=unused-argument
  tune_epochs: int = 4,
  train_epochs: int = 10,
  num_tuners: int = 6,
  bucket_name: str = 'aju-pipelines',
  tuner_dir_prefix: str = 'hptest',
  tuner_proj: str = 'p1',
  max_trials: int = 128,
  working_dir: str = 'gs://aju-pipelines/ktune7',
  data_dir: str = 'gs://aju-dev-demos-codelabs/bikes_weather/',
  steps_per_epoch: int = -1 ,  # if -1, don't override normal calcs based on dataset size
  num_best_hps: int = 2,
  num_best_hps_list: list = [0, 1]
  ):

  hptune = dsl.ContainerOp(
      name='ktune',
      image='gcr.io/aju-vtests2/ml-pipeline-bikes-dep:xyz6',
      arguments=['--epochs', tune_epochs, '--num-tuners', num_tuners,
          '--tuner-dir', '%s/%s' % (tuner_dir_prefix, dsl.RUN_ID_PLACEHOLDER),
          '--tuner-proj', tuner_proj, '--bucket-name', bucket_name, '--max-trials', max_trials,
          '--namespace', 'default', '--num-best-hps', num_best_hps, '--executions-per-trial', 2,
          '--deploy'
          ],
      file_outputs={'hps': '/tmp/hps.json'},
      )

  with dsl.ParallelFor(num_best_hps_list) as idx:
    train = dsl.ContainerOp(
        name='train',
        image='gcr.io/aju-vtests2/ml-pl-bikes-train:v7',
        arguments=[
            '--data-dir', data_dir, '--steps-per-epoch', steps_per_epoch,
            '--workdir', '%s/%s0' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
            '--epochs', train_epochs, '--hptune-results', hptune.outputs['hps'],
            '--hp-idx', idx
            ],
        file_outputs={'train_output_path': '/tmp/train_output_path.txt'},
      )
    serve = serve_op(
      model_path=train.outputs['train_output_path'],
      model_name='bikesw',
      namespace='kubeflow'
      )
    train.set_gpu_limit(2)


if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(bikes_weather_hptune, __file__ + '.tar.gz')

