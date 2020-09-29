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
# import uuid
import yaml
from py import tf_job_client
from kubernetes import client as k8s_client
from kubernetes import config


def _generate_train_yaml(src_filename, tfjob_ns, workers, pss, args_list):
  """_generate_train_yaml  generates train yaml files based on train.template.yaml"""
  with open(src_filename, 'r') as f:
    content = yaml.load(f)

  content['metadata']['generateName'] = 'trainer-'
  content['metadata']['namespace'] = tfjob_ns

  if workers and pss:
    content['spec']['tfReplicaSpecs']['PS']['replicas'] = pss
    content['spec']['tfReplicaSpecs']['PS']['template']['spec']['containers'][0]['command'].extend(args_list)
    content['spec']['tfReplicaSpecs']['Worker']['replicas'] = workers
    content['spec']['tfReplicaSpecs']['Worker']['template']['spec']['containers'][0]['command'].extend(args_list)
    content['spec']['tfReplicaSpecs']['Master']['template']['spec']['containers'][0]['command'].extend(args_list)
  else:
    # If no workers and pss set, default is 1.
    master_spec = content['spec']['tfReplicaSpecs']['Master']
    worker_spec = content['spec']['tfReplicaSpecs']['Worker']
    ps_spec = content['spec']['tfReplicaSpecs']['PS']
    master_spec['template']['spec']['containers'][0]['command'].extend(args_list)
    worker_spec['template']['spec']['containers'][0]['command'].extend(args_list)
    ps_spec['template']['spec']['containers'][0]['command'].extend(args_list)

  return content


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
  parser.add_argument('--kfversion', type=str,
                      default='v1beta1',
                      help='The version of the deployed kubeflow. ' +
                           'If not set, the default version is v1beta1')
  parser.add_argument('--tfjob-ns', type=str,
                      default='kubeflow',
                      help='The namespace where the tfjob is submitted' +
                           'If not set, the namespace is kubeflow')
  parser.add_argument('--tfjob-timeout-minutes', type=int,
                      default=20,
                      help='Time in minutes to wait for the TFJob to complete')
  args = parser.parse_args()

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

  # logging.info('Getting credentials for GKE cluster %s.' % cluster)
  # subprocess.call(['gcloud', 'container', 'clusters', 'get-credentials', cluster,
                   # '--zone', zone])

  # Create metadata.json file for visualization.
  tb_dir = args_dict.pop('working_dir') # don't pass this arg to the training module
  metadata = {
    'outputs' : [{
      'type': 'tensorboard',
      'source': tb_dir,
    }]
  }
  with file_io.FileIO('/mlpipeline-ui-metadata.json', 'w') as f:
    json.dump(metadata, f)

  workers = args_dict.pop('workers')
  pss = args_dict.pop('pss')
  kf_version = args_dict.pop('kfversion')
  tfjob_ns = args_dict.pop('tfjob_ns')
  tfjob_timeout_minutes = args_dict.pop('tfjob_timeout_minutes')
  args_list = ['--%s=%s' % (k.replace('_', '-'),v)
               for k,v in six.iteritems(args_dict) if v is not None]
  logging.info('Generating training template.')
  template_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'train.template.yaml')
  content_yaml = _generate_train_yaml(template_file, tfjob_ns, workers, pss, args_list)

  logging.info('Start training.')
  # Set up handler for k8s clients
  config.load_incluster_config()
  api_client = k8s_client.ApiClient()
  create_response = tf_job_client.create_tf_job(api_client, content_yaml, version=kf_version)
  job_name = create_response['metadata']['name']

  wait_response = tf_job_client.wait_for_job(
      api_client, tfjob_ns, job_name, kf_version,
      timeout=datetime.timedelta(minutes=tfjob_timeout_minutes))
  succ = True

  # TODO: update this failure checking after tf-operator has the condition checking function.
  if 'Worker' in wait_response['status']['replicaStatuses']:
    if 'Failed' in wait_response['status']['replicaStatuses']['Worker']:
      logging.error('Training failed since workers failed.')
      succ = False
  if 'PS' in wait_response['status']['replicaStatuses']:
    if 'Failed' in wait_response['status']['replicaStatuses']['PS']:
      logging.error('Training failed since PSs failed.')
      succ = False
  if 'Master' in wait_response['status']['replicaStatuses']:
    if 'Failed' in wait_response['status']['replicaStatuses']['Master']:
      logging.error('Training failed since Master failed.')
      succ = False

  # #TODO: remove this after kubeflow fixes the wait_for_job issue
  # # because the wait_for_job returns when the worker finishes but the master might not be complete yet.
  # if 'Master' in wait_response['status']['replicaStatuses'] and 'active' in wait_response['status']['replicaStatuses']['Master']:
  #   master_active = True
  #   while master_active:
  #     # Wait for master to finish
  #     time.sleep(2)
  #     wait_response = tf_job_client.wait_for_job(api_client, tfjob_ns, job_name, kf_version,
  #                                            timeout=datetime.timedelta(minutes=tfjob_timeout_minutes))
  #     if 'active' not in wait_response['status']['tfReplicaStatuses']['Master']:
  #       master_active = False

  if succ:
    logging.info('Training success.')

  tf_job_client.delete_tf_job(api_client, tfjob_ns, job_name, version=kf_version)
  with open('/output.txt', 'w') as f:
    f.write(args.job_dir)

if __name__== "__main__":
  main()
