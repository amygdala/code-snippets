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
import datetime


@dsl.pipeline(
  name='Workflow 1',
  description='Demonstrate TFT-based feature processing, TFMA, TFJob, CMLE OP, and TF-Serving'
)
def workflow1(
  input_handle_eval: dsl.PipelineParam=dsl.PipelineParam(name='input-handle-eval', value='gs://aju-dev-demos-codelabs/KF/taxidata/eval/data.csv'),
  input_handle_train: dsl.PipelineParam=dsl.PipelineParam(name='input-handle-train', value='gs://aju-dev-demos-codelabs/KF/taxidata/train/data.csv'),
  outfile_prefix_eval: dsl.PipelineParam=dsl.PipelineParam(name='outfile-prefix-eval', value='eval_transformed'),
  outfile_prefix_train: dsl.PipelineParam=dsl.PipelineParam(name='outfile-prefix-train', value='train_transformed'),
  train_steps: dsl.PipelineParam=dsl.PipelineParam(name='train-steps', value=10000),
  project: dsl.PipelineParam=dsl.PipelineParam(name='project', value='YOUR_PROJECT_HERE'),
  working_dir: dsl.PipelineParam=dsl.PipelineParam(name='working-dir', value='YOUR_GCS_DIR_HERE'),
  tft_setup_file: dsl.PipelineParam=dsl.PipelineParam(name='tft-setup-file', value='/ml/transform/setup.py'),
  tfma_setup_file: dsl.PipelineParam=dsl.PipelineParam(name='tfma-setup-file', value='/ml/analysis/setup.py'),
  workers: dsl.PipelineParam=dsl.PipelineParam(name='workers', value=0),
  pss: dsl.PipelineParam=dsl.PipelineParam(name='pss', value=0),
  max_rows: dsl.PipelineParam=dsl.PipelineParam(name='max-rows', value=10000),
  ts1: dsl.PipelineParam=dsl.PipelineParam(name='ts1', value=''),
  ts2: dsl.PipelineParam=dsl.PipelineParam(name='ts2', value=''),
  preprocessing_module1: dsl.PipelineParam=dsl.PipelineParam(name='preprocessing-module1', value='gs://aju-dev-demos-codelabs/KF/taxi-preproc/preprocessing.py'),
  preprocessing_module2: dsl.PipelineParam=dsl.PipelineParam(name='preprocessing-module2', value='gs://aju-dev-demos-codelabs/KF/taxi-preproc/preprocessing2.py'),
  preprocess_mode: dsl.PipelineParam=dsl.PipelineParam(name='preprocess-mode', value='local'),
  tfma_mode: dsl.PipelineParam=dsl.PipelineParam(name='tfma-mode', value='local')):

  tfteval = dsl.ContainerOp(
      name = 'tft-eval',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tftbq-taxi',
      arguments = [ "--input_handle", input_handle_eval, "--outfile_prefix", outfile_prefix_eval,
          "--working_dir", '%s/%s/tft-eval' % (working_dir, '{{workflow.name}}'),
          "--project", project,
          "--mode", preprocess_mode,
          "--setup_file", tft_setup_file,
          "--max-rows", 5000,
          "--ts1", ts1,
          "--ts2", ts2,
          "--stage", "eval",
          "--preprocessing-module", preprocessing_module1]
      # file_outputs = {'transformed': '/output.txt'}
      )
  tfttrain = dsl.ContainerOp(
      name = 'tft-train',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tftbq-taxi',
      arguments = [ "--input_handle", input_handle_train, "--outfile_prefix", outfile_prefix_train,
          "--working_dir", '%s/%s/tft-train' % (working_dir, '{{workflow.name}}'),
          "--project", project,
          "--mode", preprocess_mode,
          "--setup_file", tft_setup_file,
          "--max_rows", max_rows,
          "--ts1", ts1,
          "--ts2", ts2,
          "--stage", "train",
          "--preprocessing_module", preprocessing_module1]
      # file_outputs = {'transformed': '/output.txt'}
      )
  tfteval2 = dsl.ContainerOp(
      name = 'tft-eval2',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tftbq-taxi',
      arguments = [ "--input_handle", input_handle_eval, "--outfile_prefix", outfile_prefix_eval,
          "--working_dir", '%s/%s/tft-eval2' % (working_dir, '{{workflow.name}}'),
          "--project", project,
          "--mode", preprocess_mode,
          "--setup_file", tft_setup_file,
          "--max_rows", 5000,
          "--ts1", ts1,
          "--ts2", ts2,
          "--stage", "eval",
          "--preprocessing_module", preprocessing_module2]
      )
  tfttrain2 = dsl.ContainerOp(
      name = 'tft-train2',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tftbq-taxi',
      arguments = [ "--input_handle", input_handle_train, "--outfile_prefix", outfile_prefix_train,
          "--working_dir", '%s/%s/tft-train2' % (working_dir, '{{workflow.name}}'),
          "--project", project,
          "--mode", preprocess_mode,
          "--setup_file", tft_setup_file,
          "--max_rows", max_rows,
          "--ts1", ts1,
          "--ts2", ts2,
          "--stage", "train",
          "--preprocessing_module", preprocessing_module2]
      )

  train = dsl.ContainerOp(
      name = 'train',
      image = 'gcr.io/google-samples/ml-pipeline-kubeflow-tf-taxi',
      arguments = [ "--tf-transform-dir", '%s/%s/tft-train' % (working_dir, '{{workflow.name}}'),
          "--output-dir", '%s/%s/tf' % (working_dir, '{{workflow.name}}'),
          "--working-dir", '%s/%s/tf/serving_model_dir' % (working_dir, '{{workflow.name}}'),
          "--job-dir", '%s/%s/tf' % (working_dir, '{{workflow.name}}'),
          "--train-files-dir", '%s/%s/tft-train' % (working_dir, '{{workflow.name}}'),
          "--eval-files-dir", '%s/%s/tft-eval' % (working_dir, '{{workflow.name}}'),
          "--train-files-prefix", outfile_prefix_train,
          "--eval-files-prefix", outfile_prefix_eval,
          "--train-steps", train_steps,
          "--workers", workers,
          "--pss", pss]
      )
  train.after(tfteval)
  train.after(tfttrain)

  train2 = dsl.ContainerOp(
      name = 'train2',
      image = 'gcr.io/google-samples/ml-pipeline-kubeflow-tf-taxi',
      arguments = [ "--tf-transform-dir", '%s/%s/tft-train2' % (working_dir, '{{workflow.name}}'),
          "--output-dir", '%s/%s/tf2' % (working_dir, '{{workflow.name}}'),
          "--working-dir", '%s/%s/tf2/serving_model_dir' % (working_dir, '{{workflow.name}}'),
          "--job-dir", '%s/%s/tf2' % (working_dir, '{{workflow.name}}'),
          "--train-files-dir", '%s/%s/tft-train2' % (working_dir, '{{workflow.name}}'),
          "--eval-files-dir", '%s/%s/tft-eval2' % (working_dir, '{{workflow.name}}'),
          "--train-files-prefix", outfile_prefix_train,
          "--eval-files-prefix", outfile_prefix_eval,
          "--train-steps", train_steps,
          "--workers", workers,
          "--pss", pss]
      )
  train2.after(tfteval2)
  train2.after(tfttrain2)

  analyze = dsl.ContainerOp(
      name = 'analyze',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tfma-taxi',
      arguments = ["--input_csv", input_handle_eval,
          "--tfma_run_dir", '%s/%s/tfma/output' % (working_dir, '{{workflow.name}}'),
          "--eval_model_dir", '%s/%s/tf/eval_model_dir' % (working_dir, '{{workflow.name}}'),
          "--mode", tfma_mode,
          "--setup_file", tfma_setup_file,
          "--project", project]
      )
  analyze2 = dsl.ContainerOp(
      name = 'analyze2',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tfma-taxi',
      arguments = ["--input_csv", input_handle_eval,
          "--tfma_run_dir", '%s/%s/tfma2/output' % (working_dir, '{{workflow.name}}'),
          "--eval_model_dir", '%s/%s/tf2/eval_model_dir' % (working_dir, '{{workflow.name}}'),
          "--mode", tfma_mode,
          "--setup_file", tfma_setup_file,
          "--project", project]
      )

  cmleop = dsl.ContainerOp(
      name = 'cmleop',
      image = 'gcr.io/google-samples/ml-pipeline-cmle-op',
      arguments = ["--gcs-path", '%s/%s/tf/serving_model_dir/export/chicago-taxi' % (working_dir, '{{workflow.name}}'),
          "--version-name", '{{workflow.name}}',
          "--project", project]
      )
  cmleop2 = dsl.ContainerOp(
      name = 'cmleop2',
      image = 'gcr.io/google-samples/ml-pipeline-cmle-op',
      arguments = ["--gcs-path", '%s/%s/tf2/serving_model_dir/export/chicago-taxi' % (working_dir, '{{workflow.name}}'),
          "--version-name", '{{workflow.name}}',
          "--project", project]
      )

  tfserving = dsl.ContainerOp(
      name = 'tfserving',
      image = 'gcr.io/google-samples/ml-pipeline-kubeflow-tfserve-taxi',
      arguments = ["--model_name", '{{workflow.name}}',
          "--model_path", '%s/%s/tf/serving_model_dir/export/chicago-taxi' % (working_dir, '{{workflow.name}}')]
      )
  tfserving2 = dsl.ContainerOp(
      name = 'tfserving2',
      image = 'gcr.io/google-samples/ml-pipeline-kubeflow-tfserve-taxi',
      arguments = ["--model_name", '{{workflow.name}}',
          "--model_path", '%s/%s/tf2/serving_model_dir/export/chicago-taxi' % (working_dir, '{{workflow.name}}')]
      )

  analyze.after(train)
  analyze2.after(train2)
  cmleop.after(train)
  cmleop2.after(train2)
  tfserving.after(train)
  tfserving2.after(train2)

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(workflow1, __file__ + '.tar.gz')
