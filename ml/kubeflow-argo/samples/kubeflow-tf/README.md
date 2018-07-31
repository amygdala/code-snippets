
# ....

(TBD -- just raw notes now).

## Setup and installation

The requirements:

* requires a GKE cluster with [argo](https://github.com/argoproj/argo) and
  [kubeflow](https://github.com/kubeflow/kubeflow) installed.
  The GKE cluster needs cloud-platform scope. For example:

  ```
  gcloud container clusters create [your-gke-cluster-name] --zone us-central1-a --scopes cloud-platform
  ```

* if running locally -- do they need service account credentials files set up?

* BQ, CMLE, and DataFlow APIs need to be enabled for your project to run the full extent of the examples.



## Running the example pipelines

....

argo submit taxi-preproc2bq-train-analyze-cmleop.yaml \
     -p input-handle-eval='bigquery-public-data.chicago_taxi_trips.taxi_trips' \
     -p input-handle-train='bigquery-public-data.chicago_taxi_trips.taxi_trips' \
     -p outfile-prefix-eval=eval_transformed \
     -p outfile-prefix-train=train_transformed \
     -p working-dir=gs://<YOUR_BUCKET>/taxifare \
     -p project=<YOUR_PROJECT> \
     -p preprocess-mode=local \
     -p tfma-mode=local \
     -p ts1-1="2016-02-01 00:00:00" \
     -p ts2-1="2016-03-01 00:00:00" \
     -p ts1-2="2013-01-01 00:00:00" \
     -p ts2-2="2016-03-01 00:00:00" \
     -p max-rows=50000 \
     -p train-steps=20000 \
     -p workers=3 \
     -p pss=1 \
     -p preprocessing-module=gs://aju-dev-demos-pipelines/taxi-preproc/preprocessing.py \
     -p old-eval-model-dir="gs://aju-dev-demos-pipelines/taxidata/prev/eval_model_dir" \
     --entrypoint preproc-train-analyze-deploy

(gs://aju-dev-demos-pipelines/argotaxibq/preproc-train-analyze-mcklv/tf2/eval_model_dir is from 2015-08-01 to 2015-09-01)
(gs://aju-dev-demos-pipelines/argotaxibq/preproc-train-analyze-s2lzc/tf2/eval_model_dir is from 2014-01-01 to 2014-03-01)

argo submit taxi-preproc2-train-analyze-cmleop-tfserve.yaml \
     -p input-handle-eval=gs://aju-dev-demos-pipelines/taxidata/eval/data.csv \
     -p input-handle-train=gs://aju-dev-demos-pipelines/taxidata/train/data.csv \
     -p outfile-prefix-eval=eval_transformed \
     -p outfile-prefix-train=train_transformed \
     -p working-dir=gs://<YOUR_BUCKET>/taxifare \
     -p project=<YOUR_PROJECT> \
     -p preprocess-mode=local \
     -p tfma-mode=local \
     -p workers=2 \
     -p pss=1 \
     -p preprocessing-module1=gs://aju-dev-demos-pipelines/taxi-preproc/preprocessing.py \
     -p preprocessing-module2=gs://aju-dev-demos-pipelines/taxi-preproc/preprocessing2.py \
     --entrypoint preproc-train-deploy2-analyze

