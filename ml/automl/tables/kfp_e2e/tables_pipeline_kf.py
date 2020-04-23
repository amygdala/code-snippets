# Copyright 2020 Google LLC
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
import kfp.gcp as gcp
import kfp.components as comp
import json
import time

DEFAULT_SCHEMA = json.dumps({"end_station_id": ["CATEGORY", True], "start_station_id": ["CATEGORY", True],
  "loc_cross": ["CATEGORY", True], "bike_id": ["CATEGORY", True]})
# DEFAULT_SCHEMA = json.dumps({"accepted_answer_id": ["CATEGORY", True], "id": ["CATEGORY", True],
    # "last_editor_display_name": ["CATEGORY", True], "last_editor_user_id": ["CATEGORY", True],
    # "owner_display_name": ["CATEGORY", True], "owner_user_id": ["CATEGORY", True],
    # "parent_id": ["CATEGORY", True], "post_type_id": ["CATEGORY", True], "tags": ["CATEGORY", True]})


create_dataset_op = comp.load_component_from_file(
  './create_dataset_for_tables/tables_component.yaml'
  )
import_data_op = comp.load_component_from_file(
  './import_data_from_bigquery/tables_component.yaml'
  )
set_schema_op = comp.load_component_from_file(
  './import_data_from_bigquery/tables_schema_component.yaml'
  )
train_model_op = comp.load_component_from_file(
    './create_model_for_tables/tables_component.yaml')
eval_model_op = comp.load_component_from_file(
    './create_model_for_tables/tables_eval_component.yaml')
eval_metrics_op = comp.load_component_from_file(
    './create_model_for_tables/tables_eval_metrics_component.yaml')
deploy_model_op = comp.load_component_from_file(
    './deploy_model_for_tables/tables_deploy_component.yaml'
    )

@dsl.pipeline(
  name='AutoML Tables',
  description='Demonstrate an AutoML Tables workflow'
)
def automl_tables(  #pylint: disable=unused-argument
  gcp_project_id: str = 'YOUR_PROJECT_HERE',
  gcp_region: str = 'us-central1',
  dataset_display_name: str = 'YOUR_DATASET_NAME',
  api_endpoint: str = '',
  path: str = 'bq://aju-dev-demos.london_bikes_weather.bikes_weather',
  target_col_name: str = 'duration',
  time_col_name: str = '',
  # test_train_col_name: str = '',
 # schema dict with col name as key, type as value
  schema_info: str = DEFAULT_SCHEMA,
  train_budget_milli_node_hours: 'Integer' = 1000,
  model_prefix: str = 'bwmodel',
  # one of strings: [MAXIMIZE_AU_ROC, MAXIMIZE_AU_PRC, MINIMIZE_LOG_LOSS, MAXIMIZE_RECALL_AT_PRECISION, MAXIMIZE_PRECISION_AT_RECALL, MINIMIZE_RMSE, MINIMIZE_MAE, MINIMIZE_RMSLE]
  optimization_objective: str = '',  # if not set, will use default
  # ["title", "body", "answer_count", "comment_count", "creation_date", "favorite_count", "owner_user_id", "score", "view_count"]
  include_column_spec_names: str = '',
  exclude_column_spec_names: str = '',
  bucket_name: str = 'YOUR_BUCKET_NAME',
  # thresholds: str = '{"au_prc": 0.9}',
  thresholds: str = '{"mean_absolute_error": 480}',
  ):

  create_dataset = create_dataset_op(
    gcp_project_id=gcp_project_id,
    gcp_region=gcp_region,
    dataset_display_name=dataset_display_name,
    api_endpoint=api_endpoint,
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  import_data = import_data_op(
    gcp_project_id=gcp_project_id,
    gcp_region=gcp_region,
    dataset_display_name=dataset_display_name,
    api_endpoint=api_endpoint,
    path=path
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  set_schema = set_schema_op(
    gcp_project_id=gcp_project_id,
    gcp_region=gcp_region,
    display_name=dataset_display_name,
    api_endpoint=api_endpoint,
    target_col_name=target_col_name,
    schema_info=schema_info,
    time_col_name=time_col_name
    # test_train_col_name=test_train_col_name
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))


  import_data.after(create_dataset)
  set_schema.after(import_data)

  train_model = train_model_op(
    gcp_project_id=gcp_project_id,
    gcp_region=gcp_region,
    dataset_display_name=dataset_display_name,
    api_endpoint=api_endpoint,
    model_prefix=model_prefix,
    train_budget_milli_node_hours=train_budget_milli_node_hours,
    optimization_objective=optimization_objective
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  train_model.after(set_schema)

  eval_model = eval_model_op(
    gcp_project_id=gcp_project_id,
    gcp_region=gcp_region,
    bucket_name=bucket_name,
    gcs_path='automl_evals/{}'.format(dsl.RUN_ID_PLACEHOLDER),
    api_endpoint=api_endpoint,
    model_display_name=train_model.outputs['model_display_name']
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  eval_metrics = eval_metrics_op(
    thresholds=thresholds,
    eval_data=eval_model.outputs['eval_data'],
    ).apply(gcp.use_gcp_secret('user-gcp-sa'))

  with dsl.Condition(eval_metrics.outputs['deploy'] == 'd'):
    deploy_model = deploy_model_op(
      gcp_project_id=gcp_project_id,
      gcp_region=gcp_region,
      api_endpoint=api_endpoint,
      model_display_name=train_model.outputs['model_display_name'],
      ).apply(gcp.use_gcp_secret('user-gcp-sa'))


if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(automl_tables, __file__ + '.tar.gz')
