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

import argparse
import os
import logging
import subprocess


def main():
  parser = argparse.ArgumentParser(description='Serving webapp')
  parser.add_argument(
      '--model_name',
      required=True)
  parser.add_argument(
      '--image_name',
      required=True)
  parser.add_argument(
      '--namespace',
      default='default')

  args = parser.parse_args()

  NAMESPACE = 'default'

  logging.getLogger().setLevel(logging.INFO)
  args_dict = vars(args)


  logging.info('Generating training template.')

  template_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'model_serve_template.yaml')
  target_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'model_serve.yaml')
  mname = args.model_name.replace('_', '-')
  logging.info("using model name: {}, image {}, and namespace: {}".format(
      mname, args.image_name, NAMESPACE))


  with open(template_file, 'r') as f:
    with open(target_file, "w") as target:
      data = f.read()
      changed = data.replace('MODEL_NAME', mname).replace(
      		'IMAGE_NAME', args.image_name).replace('NAMESPACE', NAMESPACE)
      target.write(changed)


  logging.info('deploying...')
  subprocess.call(['kubectl', 'create', '-f', '/ml/model_serve.yaml'])

  # kubectl -n default  port-forward svc/<mname>  8080:80
  # curl -X POST --data @./instances.json http://localhost:8080/predict

if __name__ == "__main__":
  main()
