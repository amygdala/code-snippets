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
import time
import logging
import subprocess
# import requests


def main():
  parser = argparse.ArgumentParser(description='Keras distributed tuner')
  parser.add_argument(
      '--epochs', type=int, required=True)
  parser.add_argument(
      '--num-tuners', type=int, required=True)
  parser.add_argument(
      '--tuner-dir', required=True)
  parser.add_argument(
      '--tuner-proj', required=True)
  parser.add_argument(
      '--max-trials', type=int, required=True)
  parser.add_argument(
      '--namespace', default='default')
      
  args = parser.parse_args()

  logging.getLogger().setLevel(logging.INFO)
  args_dict = vars(args)
  # # Get cluster name and zone from metadata
  # metadata_server = "http://metadata/computeMetadata/v1/instance/"
  # metadata_flavor = {'Metadata-Flavor' : 'Google'}
  # cluster = requests.get(metadata_server + "attributes/cluster-name",
  #                         headers=metadata_flavor).text
  # zone = requests.get(metadata_server + "zone",
  #                     headers=metadata_flavor).text.split('/')[-1]

  logging.info('Generating tuner deployment templates.')
  ts = int(time.time())
  KTUNER_CHIEF = 'ktuner{}-chief'.format(ts)
  logging.info('KTUNER_CHIEF: {}'.format(KTUNER_CHIEF))
  KTUNER_DEP_PREFIX = 'ktuner{}-dep'.format(ts)
  logging.info('KTUNER_DEP_PREFIX: {}'.format(KTUNER_DEP_PREFIX))

  template_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)), 'kchief_deployment_templ.yaml')
  chief_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'kchief_dep.yaml')

  with open(template_file, 'r') as f:
    with open(chief_file_path, "w") as target:
      data = f.read()
      changed = data.replace('EPOCHS', str(args.epochs)).replace(
          'TUNER_DIR', args.tuner_dir).replace('NAMESPACE', args.namespace).replace(
          'TUNER_PROJ', args.tuner_proj).replace('MAX_TRIALS', str(args.max_trials)).replace(
          'KTUNER_CHIEF', KTUNER_CHIEF)
      target.write(changed)

  tuner_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ktuners_dep.yaml')
  logging.info("tuner file path: %s", tuner_file_path)
  if os.path.exists(tuner_file_path):
    os.remove(tuner_file_path)
  template_file = os.path.join(
      os.path.dirname(os.path.realpath(__file__)), 'ktuners_deployment_templ.yaml')
  logging.info("num tuners: %s", args.num_tuners)
  with open(template_file, 'r') as f:
    with open(tuner_file_path, "a") as target:
      data = f.read()
      for i in range(args.num_tuners):
        changed = data.replace('EPOCHS', str(args.epochs)).replace(
            'TUNER_DIR', args.tuner_dir).replace('NAMESPACE', args.namespace).replace(
            'TUNER_PROJ', args.tuner_proj).replace('KTUNER_CHIEF', KTUNER_CHIEF).replace(
            'MAX_TRIALS', str(args.max_trials))      
        changed = changed.replace(
            'KTUNER_DEP_NAME', KTUNER_DEP_PREFIX +'{}'.format(i)).replace(
            'KTUNER_ID', 'tuner{}'.format(i))
        target.write(changed)

  logging.info('deploying chief...')
  subprocess.call(['kubectl', 'apply', '-f', chief_file_path])
  logging.info('pausing before tuner worker deployment...')
  time.sleep(120)
  logging.info('deploying tuners...')
  subprocess.call(['kubectl', 'apply', '-f', tuner_file_path])
  logging.info('finished deployments.')

  logging.info('pausing before start the wait for job completion...')
  time.sleep(180)
  # wait for all the tuner workers to complete
  for i in range(args.num_tuners):  # hmm...
    logging.info('waiting for completion of tuner %s...', i)
    # negative timeout value --> one week
    subprocess.call(['kubectl', 'wait', '--for=condition=complete', '--timeout=-1m', 'job/{}{}'.format(KTUNER_DEP_PREFIX, i)])  
  

if __name__ == "__main__":
  main()

# python deploy_tuner.py --epochs 2 --num-tuners 3 --tuner-dir gs://aju-pipelines/hptest1 --tuner-proj p2 --max-trials 8
# kubectl create clusterrolebinding sa-admin --clusterrole=cluster-admin --serviceaccount=kubeflow:pipeline-runner
