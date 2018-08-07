
# Run the example workflows

See the top-level [README](../../README.md) for these examples for more context and demo setup instructions.

Run the following from the command line, after editing appropriately for your project and GCS bucket.

## Example workflow 1

<2 paths, feature experimentation..>

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow1.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow1.png" width="90%"/></a>
<figcaption>_..._</figcaption>
</figure>

Before running, replace `<YOUR_BUCKET>` and `<YOUR_PROJECT>` with your info.
You can set `preprocess-mode` and `tfma-mode` to either `local` or `cloud`, to run the [Apache Beam](https://beam.apache.org/) pipelines either locally (on your GKE cluster), or via [Dataflow](https://cloud.google.com/dataflow).

```
argo submit workflow1.yaml \
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
```


## Example workflow 2

<option to grab data from bigquery as part of preprocessing..>

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow2.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow2.png" width="90%"/></a>
<figcaption>_..._</figcaption>
</figure>

Before running, replace `<YOUR_BUCKET>` and `<YOUR_PROJECT>` with your info.
You can set `preprocess-mode` and `tfma-mode` to either `local` or `cloud`, to run the [Apache Beam](https://beam.apache.org/) pipelines either locally (on your GKE cluster), or via [Dataflow](https://cloud.google.com/dataflow).


```
argo submit workflow2.yaml \
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
```
