# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def generate_tfdv_stats(input_data: str, output_path: str, job_name: str, use_dataflow: bool,
                        project_id: str, region:str, gcs_temp_location: str, gcs_staging_location: str,
                        whl_location: str = '', requirements_file: str = 'requirements.txt'):
  import tensorflow_data_validation as tfdv
  import logging
  import time

  import tensorflow_data_validation.statistics.stats_impl
  import tensorflow_data_validation as tfdv
  from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions

  # pip download tensorflow_data_validation --no-deps --platform manylinux2010_x86_64 --only-binary=:all:
  # CHANGE this if your download resulted in a different filename.

  # Create and set your PipelineOptions.
  options = PipelineOptions()

  if use_dataflow:
    if not whl_location:
      logging.warning('tfdv whl file required with dataflow runner.')
      exit(1)
    # For Cloud execution, set the Cloud Platform project, job_name,
    # staging location, temp_location and specify DataflowRunner.
    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.project = project_id
    google_cloud_options.job_name = '{}-{}'.format(job_name, str(int(time.time())))
    google_cloud_options.staging_location = gcs_staging_location
    google_cloud_options.temp_location = gcs_temp_location
    google_cloud_options.region = region
    options.view_as(StandardOptions).runner = 'DataflowRunner'

    setup_options = options.view_as(SetupOptions)
    # PATH_TO_WHL_FILE should point to the downloaded tfdv wheel file.
    setup_options.extra_packages = [whl_location]
    setup_options.requirements_file = 'requirements.txt'

  tfdv.generate_statistics_from_csv(
    data_location=input_data, output_path=output_path,
    pipeline_options=options)


def main():

  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser(description='TVDV')

  parser.add_argument(
      '--project_id', default='aju-vtests2')
  parser.add_argument(
      '--region', default='us-central1')
  parser.add_argument(
      '--job_name', required=True)
  parser.add_argument(
      '--gcs-staging-location', required=True)
  parser.add_argument(
      '--gcs-temp-location', required=True)
  parser.add_argument(
      '--output-path', required=True)
  parser.add_argument(
      '--data-path', required=True)
  # TFDV whl required for Dataflow runner. Download whl file with this command:
  # pip download tensorflow_data_validation --no-deps --platform manylinux2010_x86_64 --only-binary=:all:
  parser.add_argument('--whl-location')
  parser.add_argument('--requirements_file', default='requirements.txt')
  parser.add_argument('--use-dataflow', default=False, help='Run on Dataflow', action='store_true')
  parser.add_argument('--local', dest='use-dataflow', help='Run locally', action='store_false')
  args = parser.parse_args()

  use_dataflow = False
  if args.use_dataflow:
    use_dataflow = True

  generate_tfdv_stats(args.data_path, args.output_path, args.job_name, use_dataflow,
      args.project_id, args.region, args.gcs_temp_location, args.gcs_staging_location,
      args.whl_location, args.requirements_file)



if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(generate_tfdv_stats,
      output_component_file='../tfdv_component.yaml', base_image='gcr.io/aju-vtests2/tfdv-tests:v6')
  # main()