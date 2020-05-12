import logging
import datetime
import logging
import time
 
import kfp
import kfp.compiler as compiler
import kfp.dsl as dsl
 
import requests
 
# TODO: replace yours
# HOST = 'https://<yours>.pipelines.googleusercontent.com'
HOST = 'https://7c7f7f3e3d11e1d4-dot-us-central2.pipelines.googleusercontent.com'
 
@dsl.pipeline(
    name='Sequential',
    description='A pipeline with two sequential steps.'
)
def sequential_pipeline(filename='gs://ml-pipeline-playground/shakespeare1.txt'):
  """A pipeline with two sequential steps."""
  op1 = dsl.ContainerOp(
      name='filechange',
      image='library/bash:4.4.23',
      command=['sh', '-c'],
      arguments=['echo "%s" > /tmp/results.txt' % filename],
      file_outputs={'newfile': '/tmp/results.txt'})
  op2 = dsl.ContainerOp(
      name='echo',
      image='library/bash:4.4.23',
      command=['sh', '-c'],
      arguments=['echo "%s"' % op1.outputs['newfile']]
      )
 
def get_access_token():
  url = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token'
  r = requests.get(url, headers={'Metadata-Flavor': 'Google'})
  r.raise_for_status()
  access_token = r.json()['access_token']
  return access_token
 
def hosted_kfp_test(data, context):
  logging.info('Event ID: {}'.format(context.event_id))
  logging.info('Event type: {}'.format(context.event_type))
  logging.info('Data: {}'.format(data))
  logging.info('Bucket: {}'.format(data['bucket']))
  logging.info('File: {}'.format(data['name']))
  file_uri = 'gs://%s/%s' % (data['bucket'], data['name'])
  logging.info('Using file uri: %s', file_uri)
  
  logging.info('Metageneration: {}'.format(data['metageneration']))
  logging.info('Created: {}'.format(data['timeCreated']))
  logging.info('Updated: {}'.format(data['updated']))
  
  token = get_access_token() 
  logging.info('attempting to launch pipeline run.')
  ts = int(datetime.datetime.utcnow().timestamp() * 100000)
  client = kfp.Client(host=HOST, existing_token=token)
  compiler.Compiler().compile(sequential_pipeline, '/tmp/sequential.tar.gz')
  exp = client.create_experiment(name='gcstriggered')  # this is a 'get or create' op
  res = client.run_pipeline(exp.id, 'sequential_' + str(ts), '/tmp/sequential.tar.gz',
                              params={'filename': file_uri})
  logging.info(res)
