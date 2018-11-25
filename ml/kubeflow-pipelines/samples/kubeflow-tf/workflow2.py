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
  name='Workflow 2',
  description='Demonstrate TFT-based feature processing, TFMA, TFJob, BQ ingestion, and CMLE OP'
)
def workflow2(
  input_handle_eval: dsl.PipelineParam=dsl.PipelineParam(name='input-handle-eval', value='bigquery-public-data.chicago_taxi_trips.taxi_trips'),
  input_handle_train: dsl.PipelineParam=dsl.PipelineParam(name='input-handle-train', value='bigquery-public-data.chicago_taxi_trips.taxi_trips'),
  outfile_prefix_eval: dsl.PipelineParam=dsl.PipelineParam(name='outfile-prefix-eval', value='eval_transformed'),
  outfile_prefix_train: dsl.PipelineParam=dsl.PipelineParam(name='outfile-prefix-train', value='train_transformed'),
  train_steps: dsl.PipelineParam=dsl.PipelineParam(name='train-steps', value=10000),
  project: dsl.PipelineParam=dsl.PipelineParam(name='project', value='YOUR_PROJECT_HERE'),
  working_dir: dsl.PipelineParam=dsl.PipelineParam(name='working-dir', value='YOUR_GCS_DIR_HERE'),
  tft_setup_file: dsl.PipelineParam=dsl.PipelineParam(name='tft-setup-file', value='/ml/transform/setup.py'),
  tfma_setup_file: dsl.PipelineParam=dsl.PipelineParam(name='tfma-setup-file', value='/ml/analysis/setup.py'),
  workers: dsl.PipelineParam=dsl.PipelineParam(name='workers', value=2),
  pss: dsl.PipelineParam=dsl.PipelineParam(name='pss', value=1),
  max_rows: dsl.PipelineParam=dsl.PipelineParam(name='max-rows', value=10000),
  ts1_1: dsl.PipelineParam=dsl.PipelineParam(name='ts1-1', value='2016-02-01 00:00:00'),
  ts2_1: dsl.PipelineParam=dsl.PipelineParam(name='ts2-1', value='2016-03-01 00:00:00'),
  ts1_2: dsl.PipelineParam=dsl.PipelineParam(name='ts1-2', value='2013-01-01 00:00:00'),
  ts2_2: dsl.PipelineParam=dsl.PipelineParam(name='ts2-2', value='2016-03-01 00:00:00'),
  preprocessing_module: dsl.PipelineParam=dsl.PipelineParam(name='preprocessing-module1', value='gs://aju-dev-demos-codelabs/KF/taxi-preproc/preprocessing.py'),
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
          "--max_rows", max_rows,
          "--ts1", ts1_1,
          "--ts2", ts2_1,
          "--stage", "eval",
          "--preprocessing_module", preprocessing_module]
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
          "--ts1", ts1_1,
          "--ts2", ts2_1,
          "--stage", "train",
          "--preprocessing_module", preprocessing_module]
      )
  tfteval2 = dsl.ContainerOp(
      name = 'tft-eval2',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tftbq-taxi',
      arguments = [ "--input_handle", input_handle_eval, "--outfile_prefix", outfile_prefix_eval,
          "--working_dir", '%s/%s/tft-eval2' % (working_dir, '{{workflow.name}}'),
          "--project", project,
          "--mode", preprocess_mode,
          "--setup_file", tft_setup_file,
          "--max_rows", max_rows,
          "--ts1", ts1_2,
          "--ts2", ts2_2,
          "--stage", "eval",
          "--preprocessing_module", preprocessing_module]
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
          "--ts1", ts1_2,
          "--ts2", ts2_2,
          "--stage", "train",
          "--preprocessing_module", preprocessing_module]
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
      arguments = ["--input_csv", '%s/%s/tft-eval/eval.csv-00000-of-00001' % (working_dir, '{{workflow.name}}'),
          "--tfma_run_dir", '%s/%s/tfma/output' % (working_dir, '{{workflow.name}}'),
          "--eval_model_dir", '%s/%s/tf/eval_model_dir' % (working_dir, '{{workflow.name}}'),
          "--mode", tfma_mode,
          "--setup_file", tfma_setup_file,
          "--project", project]
      )
  analyze2 = dsl.ContainerOp(
      name = 'analyze2',
      image = 'gcr.io/google-samples/ml-pipeline-dataflow-tfma-taxi',
      arguments = ["--input_csv", '%s/%s/tft-eval/eval.csv-00000-of-00001' % (working_dir, '{{workflow.name}}'),
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
          "--version-name", '{{workflow.name}}_2',
          "--project", project]
      )


  analyze.after(train)
  analyze.after(tfteval)
  analyze2.after(tfteval)
  analyze2.after(train2)
  cmleop.after(train)
  cmleop2.after(train2)

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(workflow2, __file__ + '.tar.gz')
