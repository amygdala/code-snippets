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
  '../components/train_component.yaml'
  )
serve_op = comp.load_component_from_file(
  '../components/serve_component.yaml'
  )

eval_metrics_op = comp.load_component_from_file(
    '../components/eval_metrics_component.yaml')

tb_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/kubeflow/pipelines/master/components/tensorflow/tensorboard/prepare_tensorboard/component.yaml' # pylint: disable=line-too-long
  )


@dsl.pipeline(
  name='bikes_weather',
  description='Model bike rental duration given weather'
)
def bikes_weather_metrics(  #pylint: disable=unused-argument
  train_epochs: int = 5,
  working_dir: str = 'gs://YOUR/GCS/PATH',  # for the full training jobs
  data_dir: str = 'gs://aju-dev-demos-codelabs/bikes_weather/',
  steps_per_epoch: int = -1 ,  # if -1, don't override normal calcs based on dataset size
  num_best_hps_list: list = [0],
  hptune_params: str = '[{"num_hidden_layers": %s, "learning_rate": %s, "hidden_size": %s}]' % (3, 1e-2, 64),
  thresholds: str = '{"root_mean_squared_error": 2000}'
  ):


  # create TensorBoard viz for the parent directory of all training runs, so that we can
  # compare them.
  tb_viz = tb_op(
    log_dir_uri='%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER)
  )

  with dsl.ParallelFor(num_best_hps_list) as idx:  # start the full training runs in parallel

    train = train_op(
      data_dir=data_dir,
      workdir='%s/%s' % (tb_viz.outputs['log_dir_uri'], idx),
      tb_dir=tb_viz.outputs['log_dir_uri'],
      epochs=train_epochs, steps_per_epoch=steps_per_epoch,
      hp_idx=idx,
      hptune_results=hptune_params
      )

    eval_metrics = eval_metrics_op(
      thresholds=thresholds,
      metrics=train.outputs['metrics_output_path'],
      )

    with dsl.Condition(eval_metrics.outputs['deploy'] == 'deploy'):
      serve = serve_op(
        model_path=train.outputs['train_output_path'],
        model_name='bikesw',
        namespace='default'
        )
    train.set_gpu_limit(2)


if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(bikes_weather_metrics, __file__ + '.tar.gz')

