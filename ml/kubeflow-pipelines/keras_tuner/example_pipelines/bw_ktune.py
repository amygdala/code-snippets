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


train_op = comp.load_component_from_file(
  '../components/train_component.yaml' # pylint: disable=line-too-long
  )
serve_op = comp.load_component_from_file(
  '../components/serve_component.yaml' # pylint: disable=line-too-long
  )


@dsl.pipeline(
  name='bikes_weather_keras_tuner',
  description='Model bike rental duration given weather, use Keras Tuner'
)
def bikes_weather_hptune(  #pylint: disable=unused-argument
  tune_epochs: int = 2,
  train_epochs: int = 7,
  num_tuners: int = 8,
  bucket_name: str = 'YOUR_BUCKET_NAME',  # used for the HP dirs; don't include the 'gs://'
  tuner_dir_prefix: str = 'hptest',
  tuner_proj: str = 'p1',
  max_trials: int = 128,
  working_dir: str = 'gs://YOUR/GCS/PATH',  # for the full training jobs
  data_dir: str = 'gs://aju-dev-demos-codelabs/bikes_weather/',
  steps_per_epoch: int = -1 ,  # if -1, don't override normal calcs based on dataset size
  num_best_hps: int = 2,  # the N best parameter sets for full training
  # the indices to the best param sets; necessary in addition to the above param because of
  # how KFP loops work currently.  Must be consistent with the above param.
  num_best_hps_list: list = [0, 1]
  ):

  hptune = dsl.ContainerOp(
      name='ktune',
      image='gcr.io/google-samples/ml-pipeline-bikes-dep:v1',
      arguments=['--epochs', tune_epochs, '--num-tuners', num_tuners,
          '--tuner-dir', '%s/%s' % (tuner_dir_prefix, dsl.RUN_ID_PLACEHOLDER),
          '--tuner-proj', tuner_proj, '--bucket-name', bucket_name, '--max-trials', max_trials,
          '--namespace', 'default', '--num-best-hps', num_best_hps, '--executions-per-trial', 2,
          '--deploy'
          ],
      file_outputs={'hps': '/tmp/hps.json'},
      )

  with dsl.ParallelFor(num_best_hps_list) as idx:
    train = train_op(
      data_dir=data_dir,
      workdir='%s/%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER, idx),
      tb_dir='%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER),
      epochs=train_epochs, steps_per_epoch=steps_per_epoch,
      hp_idx=idx, hptune_results=hptune.outputs['hps']
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

