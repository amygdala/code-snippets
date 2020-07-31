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
import json
import logging
import os
import subprocess
import time

from google.cloud import storage


OUTPUT_PATH = '/tmp/hps.json'

def main():
  parser = argparse.ArgumentParser(description='Keras distributed tuner')
  parser.add_argument(
      '--epochs', type=int, required=True)
  parser.add_argument(
      '--num-tuners', type=int, required=True)
  parser.add_argument(
      '--bucket-name', required=True)
  parser.add_argument(
      '--tuner-dir', required=True)
  parser.add_argument(
      '--tuner-proj', required=True)
  parser.add_argument(
      '--max-trials', type=int, required=True)
  parser.add_argument(
      '--namespace', default='default')
  parser.add_argument('--deploy', default=False, action='store_true')
  parser.add_argument('--no-deploy', dest='deploy', action='store_false')

  args = parser.parse_args()
  logging.getLogger().setLevel(logging.INFO)
  args_dict = vars(args)
  tuner_path = 'gs://{}/{}'.format(args.bucket_name, args.tuner_dir)
  res_path = '{}/{}'.format(args.bucket_name, args.tuner_dir)  
  logging.info('tuner path: %s, res path %s', tuner_path, res_path)

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
          'TUNER_DIR', tuner_path).replace('NAMESPACE', args.namespace).replace(
          'TUNER_PROJ', args.tuner_proj).replace('MAX_TRIALS', str(args.max_trials)).replace(
          'KTUNER_CHIEF', KTUNER_CHIEF).replace('RES_PATH', res_path).replace(
          'BUCKET_NAME', args.bucket_name)
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
            'TUNER_DIR', tuner_path).replace('NAMESPACE', args.namespace).replace(
            'TUNER_PROJ', args.tuner_proj).replace('KTUNER_CHIEF', KTUNER_CHIEF).replace(
            'MAX_TRIALS', str(args.max_trials)).replace('RES_PATH', res_path).replace(
            'BUCKET_NAME', args.bucket_name)
        changed = changed.replace(
            'KTUNER_DEP_NAME', KTUNER_DEP_PREFIX +'{}'.format(i)).replace(
            'KTUNER_ID', 'tuner{}'.format(i))
        target.write(changed)

  if args.deploy:
    logging.info('deploying chief...')
    subprocess.call(['kubectl', 'apply', '-f', chief_file_path])
    logging.info('pausing before tuner worker deployment...')
    time.sleep(120)
    logging.info('deploying tuners...')
    subprocess.call(['kubectl', 'apply', '-f', tuner_file_path])
    logging.info('finished deployments.')

    # wait for the tuner pods to be ready... if we're autoscaling the GPU pool,
    # this might take a while.
    for i in range(args.num_tuners):  
      logging.info('waiting for tuner %s pod to be ready...', i)
      subprocess.call(['kubectl', '-n={}'.format(args.namespace), 'wait', 'pod',
              '--for=condition=ready', '--timeout=15m', '-l=job-name={}{}'.format(KTUNER_DEP_PREFIX, i)])    

    # wait for all the tuner workers to complete
    for i in range(args.num_tuners):
      logging.info('waiting for completion of tuner %s...', i)
      # negative timeout value --> one week
      subprocess.call(['kubectl', '-n={}'.format(args.namespace), 'wait',
              '--for=condition=complete', '--timeout=-1m', 'job/{}{}'.format(KTUNER_DEP_PREFIX, i)])

    # parse the results to get the best params
    # (is there a more preferred way to do this?)

    client = storage.Client()
    bucket = client.get_bucket(args.bucket_name)
    blob = bucket.get_blob(res_path)

    # oracle_json_str = blob.download_as_string()
    results_string = blob.download_as_string()
    logging.info('got results info: %s', results_string)
    # oracle_json = json.loads(oracle_json_str)
    # logging.info('oracle json: %s', oracle_json)
    # o_values = oracle_json['hyperparameters']['values']
    # hp_values_str = json.dumps(o_values)
    # logging.info('oracle values: %s', hp_values_str)

    with open(OUTPUT_PATH, 'w') as f:
      # f.write(hp_values_str)
      f.write(results_string)

if __name__ == "__main__":
  main()


# kubectl create clusterrolebinding sa-admin --clusterrole=cluster-admin --serviceaccount=kubeflow:pipeline-runner
# kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
