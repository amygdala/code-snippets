# Copyright 2018 Google LLC
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

@dsl.pipeline(
  name='Github issue summarization',
  description='Demonstrate TFT-based feature processing, TFMA, TFJob, CMLE OP, and TF-Serving'
)
def gh_summ(
  train_steps: dsl.PipelineParam=dsl.PipelineParam(name='train-steps', value=2020000),
  project: dsl.PipelineParam=dsl.PipelineParam(name='project', value='YOUR_PROJECT_HERE'),
  github_token: dsl.PipelineParam=dsl.PipelineParam(name='github-token', value='YOUR_GITHUB_TOKEN_HERE'),
  working_dir: dsl.PipelineParam=dsl.PipelineParam(name='working-dir', value='YOUR_GCS_DIR_HERE'),
  checkpoint_dir: dsl.PipelineParam=dsl.PipelineParam(name='checkpoint-dir', value='gs://aju-dev-demos-pipelines/temp/model_output_tbase.bak2019000'),
  # TODO: generalize web app setup s.t. the service name can be parameterized
  # model_name: dsl.PipelineParam=dsl.PipelineParam(name='model-name', value='ghsumm'),
  data_dir: dsl.PipelineParam=dsl.PipelineParam(name='data-dir', value='gs://aju-dev-demos-pipelines/temp/t2t_data_all')):


  train = dsl.ContainerOp(
      name = 'train',
      image = 'gcr.io/aju-dev-demos/ml-pipeline-t2ttrain',
      arguments = [ "--data-dir", data_dir,
          "--checkpoint-dir", checkpoint_dir,
          "--model-dir", '%s/%s/model_output' % (working_dir, '{{workflow.name}}'),
          "--train-steps", train_steps]
      )

  serve = dsl.ContainerOp(
      name = 'serve',
      image = 'gcr.io/aju-dev-demos/ml-pipeline-kubeflow-tfserve',
      arguments = ["--model_name", 'ghsumm-%s' % ('{{workflow.name}}',),
          "--model_path", '%s/%s/model_output/export' % (working_dir, '{{workflow.name}}')
          ]
      )
  serve.after(train)
  train.set_gpu_limit(8)

  webapp = dsl.ContainerOp(
      name = 'webapp',
      image = 'gcr.io/aju-dev-demos/ml-pipeline-webapp-launcher',
      arguments = ["--model_name", 'ghsumm-%s' % ('{{workflow.name}}',),
          "--github_token", github_token]

      )
  webapp.after(serve)

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(gh_summ, __file__ + '.tar.gz')
