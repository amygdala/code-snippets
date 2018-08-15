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

"""Launch a potentially distributed TensorFlow training job using the Kubeflow tf-jobs API."""


import argparse
import datetime
import json
import os
import logging
import requests
import subprocess
import six
from tensorflow.python.lib.io import file_io
import time
import uuid
import yaml


def main(argv=None):
  parser = argparse.ArgumentParser(description='ML Trainer')
  parser.add_argument(
      '--working-dir',
      help='Training job working directory.',
      required=True)
  parser.add_argument(
      '--train-files-dir',
      help='Path to training data',
      required=True)
  parser.add_argument(
      '--train-files-prefix',
      help='The prefix of the training input files.',
      required=True)

  parser.add_argument(
      '--tf-transform-dir',
      help='Tf-transform directory with model from preprocessing step',
      required=True)

  parser.add_argument(
      '--output-dir',
      help="""\
      Directory under which which the serving model (under /serving_model_dir)\
      and the tf-mode-analysis model (under /eval_model_dir) will be written\
      """,
      required=True)

  parser.add_argument(
      '--eval-files-dir',
      help='Path to evaluation data',
      required=True
  )
  parser.add_argument(
      '--eval-files-prefix',
      help='The prefix of the eval input files.',
      required=True)

  # Training arguments
  parser.add_argument(
      '--job-dir',
      help='GCS location to write checkpoints and export models',
      required=True)

  # Argument to turn on all logging
  parser.add_argument(
      '--verbosity',
      choices=['DEBUG', 'ERROR', 'FATAL', 'INFO', 'WARN'],
      default='INFO',
  )
  # Experiment arguments
  parser.add_argument(
      '--train-steps',
      help='Count of steps to run the training job for',
      required=True,
      type=int)
  parser.add_argument(
      '--eval-steps',
      help='Number of steps to run evalution for at each checkpoint',
      default=100,
      type=int)
  parser.add_argument('--workers', type=int, default=0)
  parser.add_argument('--pss', type=int, default=0)
  parser.add_argument('--cluster', type=str,
                      help='GKE cluster set up for kubeflow. If set, zone must be provided. ' +
                           'If not set, assuming this runs in a GKE container and current ' +
                           'cluster is used.')
  parser.add_argument('--zone', type=str, help='zone of the kubeflow cluster.')
  args = parser.parse_args()

  KUBEFLOW_NAMESPACE = 'default'

  logging.getLogger().setLevel(logging.INFO)
  args_dict = vars(args)
  if args.cluster and args.zone:
    cluster = args_dict.pop('cluster')
    zone = args_dict.pop('zone')
  else:
    # Get cluster name and zone from metadata
    metadata_server = "http://metadata/computeMetadata/v1/instance/"
    metadata_flavor = {'Metadata-Flavor' : 'Google'}
    cluster = requests.get(metadata_server + "attributes/cluster-name",
                           headers = metadata_flavor).text
    zone = requests.get(metadata_server + "zone",
                        headers = metadata_flavor).text.split('/')[-1]

  logging.info('Getting credentials for GKE cluster %s.' % cluster)
  subprocess.call(['gcloud', 'container', 'clusters', 'get-credentials', cluster,
                   '--zone', zone])

  # Create metadata.json file for visualization.
  tb_dir = args_dict.pop('working_dir') # don't pass this arg to the training module
  metadata = {
    'outputs' : [{
      'type': 'tensorboard',
      'source': tb_dir,
    }]
  }
  with file_io.FileIO(os.path.join(tb_dir, 'metadata.json'), 'w') as f:
    json.dump(metadata, f)

  workers = args_dict.pop('workers')
  pss = args_dict.pop('pss')
  args_list = ['--%s=%s' % (k.replace('_', '-'),v)
               for k,v in six.iteritems(args_dict) if v is not None]
  logging.info('Generating training template.')
  template_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'train.template.yaml')
  with open(template_file, 'r') as f:
    content = yaml.load(f)

  job_name = 'trainer-' + str(uuid.uuid4())
  content['metadata']['name'] = job_name
  if workers and pss:
    for spec in content['spec']['replicaSpecs']:
      if spec['tfReplicaType'] == 'WORKER':
        spec['replicas'] = workers
      elif spec['tfReplicaType'] == 'PS':
        spec['replicas'] = pss
      # add the args to be passed to the training module.
      spec['template']['spec']['containers'][0]['command'].extend(args_list)
  else:
    # No workers and pss set. Remove the sections because setting replicas=0 doesn't work.
    replicas = content['spec']['replicaSpecs']
    content['spec']['replicaSpecs'] = [r for r in replicas
                                       if r['tfReplicaType'] not in ['WORKER', 'PS']]
    # Set master parameters. master is the only item in replicaSpecs in this case.
    master_spec = content['spec']['replicaSpecs'][0]
    # add the args to be passed to the training module.
    master_spec['template']['spec']['containers'][0]['command'].extend(args_list)

  with open('train.yaml', 'w') as f:
    yaml.dump(content, f, default_flow_style=False)

  logging.info('Start training.')
  subprocess.call(['kubectl', 'create', '-f', 'train.yaml', '--namespace', KUBEFLOW_NAMESPACE])


  # TODO: Replace polling with kubeflow API calls.
  while True:
    time.sleep(2)
    check_job_commands = ['kubectl', 'describe', 'tfjob', job_name, '--namespace', KUBEFLOW_NAMESPACE]
    kubectl_proc = subprocess.Popen(check_job_commands, stdout=subprocess.PIPE)
    grep_proc = subprocess.Popen(['grep', 'Phase:'], stdin=kubectl_proc.stdout,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    kubectl_proc.stdout.close()
    stdout, stderr = grep_proc.communicate()
    parts = stdout.rstrip().split(':')
    if len(parts) != 2:
      logging.error('Training failed.')
      logging.info(subprocess.check_output(check_job_commands))
      break

    status = parts[1].strip()
    if status == 'Done':
      # TODO: status == 'Done' may not always indicate success.
      # Switch to K8s API.
      logging.info('Training done.')
      break
    elif status == 'Failed':
      logging.error('Training failed.')
      logging.info(subprocess.check_output(check_job_commands))
      break

if __name__== "__main__":
  main()
