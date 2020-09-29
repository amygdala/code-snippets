
# Run the example pipelines

**These examples are not currently maintained and are probably out of date**.

See the top-level [`README_taxidata_examples.md`](../../../README_taxidata_examples.md) for installation instructions and more on what these examples do.

Then, if you have not already, install the [Kubeflow Pipelines SDK](https://github.com/kubeflow/pipelines/releases) according to the [instructions](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/).  It's most straightforward to install into a virtual environment such as Conda.

Then, a pipeline is run as follows. Compile the pipeline by running its Python script. E.g.,

```sh
python workflow1.py
```
This will generate a `*.tar.gz` archive for the pipeline. Upload that file to the Kubeflow Pipelines UI as a new pipeline.
To do this, set up a port-forward to the Kubeflow dashboard:

```
export NAMESPACE=kubeflow
kubectl port-forward -n ${NAMESPACE}  `kubectl get pods -n ${NAMESPACE} --selector=service=ambassador -o jsonpath='{.items[0].metadata.name}'` 8080:80
```

and then visit the Pipelines page: `http://localhost:8080/pipeline`

Once you've uploaded a pipeline, you can then create *Experiments* based on that pipeline.  When you initiate an experiment *run*, fill in the `<YOUR_BUCKET>` and `<YOUR_PROJECT>` parameter values with your information. You can then monitor the run in the Pipelines UI, as well as view information about each step: its logs, configuration, and inputs and outputs.


## Example workflow 1

This example illustrates how you can use a ML workflow to experiment with
[TFT](https://github.com/tensorflow/transform)-based feature engineering, and how you can serve your trained model from both on-prem and cloud endpoints.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-pls/workflow1_graph_ds.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-pls/workflow1_graph_ds.png" width="90%"/></a>
<figcaption><br/><i>A workflow for TFT-based feature engineering experimentation</i></figcaption>
</figure>

<p></p>


Compile the [`workflow1.py`](workflow1.py) pipeline:

```sh
python workflow1.py
```
and upload the resulting archive via the Kubeflow Pipelines UI.
Before running the pipeline, replace the `<YOUR_BUCKET>` and `<YOUR_PROJECT>` parameter values with your info.

You can also set the `preprocess-mode` and `tfma-mode` parameters to either `local` or `cloud`, to run the [Apache Beam](https://beam.apache.org/) pipelines either locally (on your GKE cluster), or via [Dataflow](https://cloud.google.com/dataflow).
(Running the pipelines on the Dataflow service will actually take a bit longer than running locally for these relatively small jobs, since since it includes time starting up the Dataflow workers.  If you were to scale out to large datasets, this would not be the case).

## Example workflow 2

Workflow 2 shows how you might use TFMA to investigate relative accuracies of models trained on different datasets, evaluating against ‘new’ data. As part of the preprocessing step, it pulls data directly from the source BigQuery Chicago taxi dataset, with differing min and max time boundaries, effectively training on ‘recent’ data vs a batch that includes older data. Then, it runs TFMA analysis on both learned models, using the newest data for evaluation.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-pls/wkflw2_graph_ds.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-pls/wkflw2_graph_ds.png" width="90%"/></a>

<figcaption><br/><i>Comparing models trained on datasets that cover differing time intervals</i></figcaption>
</figure>

<p></p>

Compile the [`workflow2.py`](workflow2.py) pipeline:

```sh
python workflow2.py
```
and upload the resulting archive via the Kubeflow Pipelines UI.

As above, when initiating a pipeline run, replace the `<YOUR_BUCKET>` and `<YOUR_PROJECT>` parameter values with your info; and you can also set the `preprocess-mode` and `tfma-mode` parameters to either `local` or `cloud`, to run the [Apache Beam](https://beam.apache.org/) pipelines either locally (on your GKE cluster), or via [Dataflow](https://cloud.google.com/dataflow).
