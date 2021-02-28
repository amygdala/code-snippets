# Copyright 2021 Google Inc. All Rights Reserved.
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

from typing import NamedTuple


def generate_tfdv_stats(input_data: str, output_path: str, job_name: str, use_dataflow: str,
                        project_id: str, region:str, gcs_temp_location: str, gcs_staging_location: str,
                        whl_location: str = '', requirements_file: str = 'requirements.txt'
) -> NamedTuple('Outputs', [('stats_path', str)]):

  import logging
  import time

  import tensorflow_data_validation as tfdv
  import tensorflow_data_validation.statistics.stats_impl
  from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions

  # pip download tensorflow_data_validation --no-deps --platform manylinux2010_x86_64 --only-binary=:all:
  # CHANGE this if your download resulted in a different filename.

  logging.getLogger().setLevel(logging.INFO)
  logging.info("output path: %s", output_path)
  logging.info("Building pipeline options")
  # Create and set your PipelineOptions.
  options = PipelineOptions()

  if use_dataflow == 'true':
    logging.info("using Dataflow")
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

  return (output_path, )


if __name__ == '__main__':
  import kfp
  kfp.components.func_to_container_op(generate_tfdv_stats,
      output_component_file='../tfdv_component.yaml',
      base_image='gcr.io/google-samples/tfdv-tests:v1')
