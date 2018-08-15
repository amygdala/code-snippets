# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Deploy a TF model to CMLE."""

import argparse
import os
import subprocess
import time

from tensorflow.python.lib.io import file_io

def main(argv=None):
  parser = argparse.ArgumentParser(description='ML Trainer')
  parser.add_argument(
      '--project',
      help='The GCS project to use',
      required=True)
  parser.add_argument(
      '--gcs-path',
      help='The GCS path to the trained model. The path should end with "../export/<model-name>".',
      required=True)
  parser.add_argument(
      '--version-name',
      help='The model version name.',
      required=True)

  parser.add_argument(
      '--model-name',
      help='The model name.',
      default='taxifare')

  parser.add_argument(
      '--region',
      help='The model region.',
      default='us-central1'
      )

  args = parser.parse_args()

  # Make sure the model dir exists before proceeding, as sometimes it takes a few seconds to become
  # available after training completes.
  retries = 0
  sleeptime = 5
  while retries < 20:
    try:
      model_location = os.path.join(args.gcs_path, file_io.list_directory(args.gcs_path)[-1])
      print("model location: %s" % model_location)
      break
    except Exception as e:
      print(e)
      print("Sleeping %s seconds to wait for GCS files..." % sleeptime)
      time.sleep(sleeptime)
      retries += 1
      sleeptime *= 2
  if retries >=20:
    print("could not get model location subdir from %s, exiting" % args.gcs_path)
    exit(1)


  model_create_command = ['gcloud', 'ml-engine', 'models', 'create', args.model_name, '--regions',
      args.region, '--project', args.project]
  print(model_create_command)
  result = subprocess.call(model_create_command)
  print(result)

  proper_version_name = args.version_name.replace('_', '-')
  print("using version name: %s" % proper_version_name)

  model_deploy_command = ['gcloud', 'ml-engine', 'versions', 'create', proper_version_name,
    '--model', args.model_name, '--runtime-version', '1.6', '--project', args.project,
    '--origin', model_location
      ]
  print(model_deploy_command)
  result2 = subprocess.call(model_deploy_command)
  print(result2)




if __name__== "__main__":
  main()

