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


train_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/amygdala/code-snippets/master/ml/kubeflow-pipelines/keras_tuner/components/train_component.yaml'
  )
serve_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/amygdala/code-snippets/master/ml/kubeflow-pipelines/keras_tuner/components/serve_component.yaml'
  )

tb_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/kubeflow/pipelines/master/components/tensorflow/tensorboard/prepare_tensorboard/component.yaml'
  )

# tfdv_op = comp.load_component_from_url(
#   'https://raw.githubusercontent.com/amygdala/code-snippets/keras_tuner3/ml/kubeflow-pipelines/keras_tuner/components/tfdv_component.yaml'
#   )

eval_metrics_op = comp.load_component_from_url(
  'https://raw.githubusercontent.com/amygdala/code-snippets/master/ml/kubeflow-pipelines/keras_tuner/components/eval_metrics_component.yaml'
)

tfdv_op = comp.load_component_from_file(
  '../components/tfdv_component.yaml'
  )
tfdv_drift_op = comp.load_component_from_file(
  '../components/tfdv_drift_component.yaml'
)


@dsl.pipeline(
  name='bikes_weather',
  description='Model bike rental duration given weather'
)
def bikes_weather_tfdv( 
  train_epochs: int = 3,
  working_dir: str = 'gs://YOUR/GCS/PATH',  # for the full training jobs
  data_dir: str = 'gs://aju-dev-demos-codelabs/bikes_weather/', # currently, requires trailing slash
  steps_per_epoch: int = -1 ,  # if -1, don't override normal calcs based on dataset size
  # num_best_hps_list: list = [0],
  hptune_params: str = '[{"num_hidden_layers": %s, "learning_rate": %s, "hidden_size": %s}]' % (3, 1e-2, 64),
  # tfdv-related
  project_id: str = 'aju-vtests2',
  region: str = 'us-central1',
  requirements_file: str = 'requirements.txt',
  job_name: str = 'testx',
  gcs_staging_location: str = 'gs://aju-pipelines/tfdv_expers',
  gcs_temp_location:str = 'gs://aju-pipelines/tfdv_expers/tmp',
  # input_data: str = 'gs://aju-dev-demos-codelabs/bikes_weather',
  output_path: str = 'gs://aju-pipelines/tfdv_expers',
  whl_location: str = 'tensorflow_data_validation-0.26.0-cp37-cp37m-manylinux2010_x86_64.whl',
  use_dataflow: str = '',
  thresholds: str = '{"root_mean_squared_error": 2000}',
  stats_older_path: str = 'gs://aju-pipelines/tfdv_expers/ea85fbed-b617-423f-8b4e-46bbd6276312/eval/evaltrain.pb'
  ):


  # create TensorBoard viz for the parent directory of all training runs, so that we can
  # compare them.
  tb_viz = tb_op(
    log_dir_uri='%s/%s' % (working_dir, dsl.RUN_ID_PLACEHOLDER)
  )

  tfdv1 = tfdv_op(
    input_data='%stest-*.csv' % (data_dir,),
    output_path='%s/%s/eval/evaltest.pb' % (output_path, dsl.RUN_ID_PLACEHOLDER),
    job_name='%s-1' % (job_name,),
    use_dataflow=use_dataflow,
    project_id=project_id, region=region,
    gcs_temp_location=gcs_temp_location, gcs_staging_location=gcs_staging_location,
    whl_location=whl_location, requirements_file=requirements_file
    )
  tfdv2 = tfdv_op(
    input_data='%strain-*.csv' % (data_dir,),
    output_path='%s/%s/eval/evaltrain.pb' % (output_path, dsl.RUN_ID_PLACEHOLDER),
    job_name='%s-2' % (job_name,),
    use_dataflow=use_dataflow,
    project_id=project_id, region=region,
    gcs_temp_location=gcs_temp_location, gcs_staging_location=gcs_staging_location,
    whl_location=whl_location, requirements_file=requirements_file
    )

  tfdv_drift = tfdv_drift_op(stats_older_path, tfdv2.outputs['stats_path'])
  
  # with dsl.ParallelFor(num_best_hps_list) as idx:  # start the full training runs in parallel
  with dsl.Condition(tfdv_drift.outputs['train'] == 'true'):

    train = train_op(
      data_dir=data_dir,
      workdir='%s/%s' % (tb_viz.outputs['log_dir_uri'], 0),
      tb_dir=tb_viz.outputs['log_dir_uri'],
      epochs=train_epochs, steps_per_epoch=steps_per_epoch,
      hp_idx=0,
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
  compiler.Compiler().compile(bikes_weather_tfdv, __file__ + '.tar.gz')
