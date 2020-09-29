
# (Deprecated) Kubeflow Pipelines examples

**These examples are not currently maintained and are probably no longer working properly.**

- [Installation and setup](#installation-and-setup)
  - [Create a GCP project and enable the necessary APIs](#create-a-gcp-project-and-enable-the-necessary-apis)
  - [Install the gcloud sdk (or use the Cloud Shell)](#install-the-gcloud-sdk-or-use-the-cloud-shell)
  - [Create a Kubernetes Engine (GKE) cluster with Kubeflow installed](#create-a-kubernetes-engine-gke-cluster-with-kubeflow-installed)
  - [Create a Google Cloud Storage (GCS) bucket](#create-a-google-cloud-storage-gcs-bucket)
- [Running the examples](#running-the-examples)
  - [Example workflow 1](#example-workflow-1)
    - [View the results of model analysis in a Jupyter notebook](#view-the-results-of-model-analysis-in-a-jupyter-notebook)
    - [Use your models for prediction](#use-your-models-for-prediction)
    - [Use the Cloud ML Engine Online Prediction service](#use-the-cloud-ml-engine-online-prediction-service)
    - [Access the TF-serving endpoints for your learned model](#access-the-tf-serving-endpoints-for-your-learned-model)
  - [Example workflow 2](#example-workflow-2)
    - [View the results of model analysis in a Jupyter notebook](#view-the-results-of-model-analysis-in-a-jupyter-notebook-1)
    - [Use your models for prediction with Cloud ML Engine Online Prediction](#use-your-models-for-prediction-with-cloud-ml-engine-online-prediction)
- [Navigating the example code](#navigating-the-example-code)
- [Cleanup](#cleanup)
  - [Take down the TF-serving endpoints](#take-down-the-tf-serving-endpoints)

[Kubeflow](https://www.kubeflow.org/) is an OSS project to support a machine learning stack on Kubernetes, to make deployments of ML workflows on Kubernetes simple, portable and scalable.

[**Kubeflow Pipelines**](https://github.com/kubeflow/pipelines) is a new component of Kubeflow that makes it easy to compose, deploy and manage end-to-end machine learning workflows. The Kubeflow Pipelines documentation is [here]().

This directory contains some Kubeflow Pipelines examples.
The examples highlight how Kubeflow and Kubeflow Pipelines can help support portability, composability and reproducibility, scalability, and visualization and collaboration in your ML lifecycle; and make it easier to support hybrid ML solutions.

The examples include use of [TensorFlow Transform](https://github.com/tensorflow/transform) (TFT) for preprocessing and to avoid training/serving skew; Kubeflow's tf-jobs CRD for supporting distributed training; and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis.
The workflows also include deployment of the trained models to both
[Cloud ML Engine Online Prediction](https://cloud.google.com/ml-engine/docs/tensorflow/prediction-overview);
and to [TensorFlow Serving](https://github.com/tensorflow/serving) via Kubeflow.

## Installation and setup

The examples require a Google Cloud Platform (GCP) account and project.

You'll also either need [gcloud](https://cloud.google.com/sdk/) installed on your laptop; or alternately you can run gcloud in the [Cloud Shell](https://cloud.google.com/shell/docs/) via the GCP [Cloud Console](https://console.cloud.google.com).

### Create a GCP project and enable the necessary APIs

If you don't have a Google Cloud Platform (GCP) account yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.

Then, [create a GCP Project](https://console.cloud.google.com/) if you don't have one.

Then, __[enable](https://support.google.com/cloud/answer/6158841?hl=en) the following APIs__ for your project: Dataflow, BigQuery, Cloud Machine Learning Engine, and Kubernetes Engine. (You don't need to create any credentials for these APIs, as we'll set up a Kubernetes Engine (GKE) cluster with sufficient access).

### Install the gcloud sdk (or use the Cloud Shell)

Install the GCP [gcloud command-line sdk](https://cloud.google.com/sdk/install) on your laptop.

Or, if you don't want to install `gcloud` locally, you can bring up the [Cloud Shell](https://cloud.google.com/shell/docs/quickstart) from the Cloud Console and run `kubectl` and `gcloud` from there.  When you start the cloud shell, confirm from the initial output that it's set to use the GCP project in which your GKE cluster is running.


### Create a Kubernetes Engine (GKE) cluster with Kubeflow installed

Install Kubeflow as described [here](https://www.kubeflow.org/docs/started/getting-started-gke/).
**Kubeflow version >=0.4 is required for these examples**, as they use the TFJob v1beta1 API.

It is probably the most straightforward to use the [launcher UI](https://www.kubeflow.org/docs/started/getting-started-gke/#deploy-kubeflow-on-gke-using-the-ui) for installation, and to check "Skip IAP" for quicker setup
(you will then need to port-forward to connect to the Kubeflow dashboard, as described below).


### Create a Google Cloud Storage (GCS) bucket

Your ML workflow will need access to a GCS bucket. Create one as [described here](https://cloud.google.com/storage/docs/creating-buckets).  Make it *regional*, not multi-regional.

## Running the examples

There are two examples. Both revolve around a TensorFlow 'taxi fare tip prediction' model, with data pulled from a [public BigqQery dataset of Chicago taxi trips](https://cloud.google.com/bigquery/public-data/chicago-taxi).

Both examples use [TFT](https://github.com/tensorflow/transform) for data preprocessing and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis (either can be run via local [Apache Beam](https://beam.apache.org/), or via [Dataflow](https://cloud.google.com/dataflow)); do distributed training via the Kubeflow tf-jobs [custom resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/); and deploy to the Cloud ML Engine Online Prediction service.
The first example also includes use of [TF-Serving](https://github.com/tensorflow/serving) via Kubeflow, and the second includes use of [BigQuery](cloud.google.com/bigquery) as a data source.

Change to the [`samples/kubeflow-tf/older`](samples/kubeflow-tf/older) directory, and see that [README](samples/kubeflow-tf/older/README.md) for details on runing the examples. To bring up the Pipelines UI, set up a port-forward to the Kubeflow dashboard:

```
export NAMESPACE=kubeflow
kubectl port-forward -n ${NAMESPACE}  `kubectl get pods -n ${NAMESPACE} --selector=service=ambassador -o jsonpath='{.items[0].metadata.name}'` 8080:80
```

and then visit the Pipelines page: `http://localhost:8080/pipeline`

Once you've uploaded a pipeline, you can then create *Experiments* based on that pipeline.  When you initiate an experiment *run*, fill in the `<YOUR_BUCKET>` and `<YOUR_PROJECT>` parameter values with your information. You can then monitor the run in the Pipelines UI, as well as view information about each step: its logs, configuration, and inputs and outputs.

You can also use `kubectl` to watch the pods created in the various stages of the workflows:

```sh
kubectl get pods -o wide --all-namespaces=true --watch=true
```

In particular, this lets you monitor creation and status of the pods used for Kubeflow `TF-job` distributed training.

### Example workflow 1

Run the first example [as described here](samples/kubeflow-tf/older/README.md#example-workflow-1).
This example illustrates how you can use a Kubeflow pipeline to experiment with
[TFT](https://github.com/tensorflow/transform)-based feature engineering, and how you can serve your trained model from both on-prem and cloud endpoints.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-pls/workflow1_graph_ds.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-pls/workflow1_graph_ds.png" width="90%"/></a>
<figcaption><br/><i>A workflow for TFT-based feature engineering experimentation</i></figcaption>
</figure>

<p></p>

The pipeline runs two paths concurrently, passing a different TFT preprocessing function to each ([`preprocessing.py`](components/older/dataflow/tft/preprocessing.py) vs [`preprocessing2.py`](components/older/dataflow/tft/preprocessing.py)).

Then each model is trained, using Kubeflow's tf-jobs [CRD](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/).  For example purposes, distributed training is used for one path, and single-node training is used for the other.  This is done by specifying the number of *workers* and *parameter servers* to use for the training job.

For this workflow, one processing path used two workers and one parameter server as well as a 'master' (for distributed training), and the other is hardwired to use just one of each.  While the training parts of the workflow are running, you'll see something like the following in your list of pods:

```
trainer-b64ef136-953d-4b57-b4e1-604aabff-master-huex-0-szz88   1/1       Running     0          1m        10.20.0.10   gke-pipelines-default-pool-2a81a07a-ptmq
trainer-b64ef136-953d-4b57-b4e1-604aabff-ps-huex-0-x983w       1/1       Running     0          1m        10.20.2.9    gke-pipelines-default-pool-2a81a07a-26k2
trainer-b64ef136-953d-4b57-b4e1-604aabff-worker-huex-0-ki35n   1/1       Running     0          1m        10.20.2.10   gke-pipelines-default-pool-2a81a07a-26k2
trainer-b64ef136-953d-4b57-b4e1-604aabff-worker-huex-1-imzg0   1/1       Running     0          1m        10.20.0.11   gke-pipelines-default-pool-2a81a07a-ptmq
```

When the training is finished, both models are deployed to both Cloud ML Engine and TF-Serving.  Additionally, the the models are analyzed using [TFMA](https://github.com/tensorflow/model-analysis/), as described below.

#### View the results of model analysis in a Jupyter notebook

One of the workflow steps runs TensorFlow Model Analysis (TFMA) on the trained model, using a given [specification of how to slice the data](components/older/dataflow/tfma/model_analysis-taxi.py#L45).  You can visualize the results via a Jupyter notebook.
You can do this in a local notebook (see the TFMA docs for installation).

Or, kubeflow's JupyterHub installation makes this easy to do, via a `port-forward` to your GKE cluster. The necessary libraries and visualization widgets are already installed.
See the *"To connect to your Jupyter Notebook locally"* section in this [Kubeflow guide](https://www.kubeflow.org/docs/guides/components/jupyter/) for more info.

Load and run the [`tfma_expers.ipynb`](components/older/dataflow/tfma/tfma_expers.ipynb) notebook to explore the results of the TFMA analysis.

#### Use your models for prediction

Change to the [`components/older/kubeflow/tf-serving`](components/older/kubeflow/tf-serving) directory, and copy the `trainer` module from the `taxi_model` directory into this directory:

```sh
cp -pr ../taxi_model/trainer .
```

#### Use the Cloud ML Engine Online Prediction service

As part of the workflow, your models were deployed to the Cloud ML Engine online prediction service. The model name is `taxifare`, and the version names are derived from the workflow name.

You can view the deployed versions of the `taxifare` model in the Cloud Console:
[https://console.cloud.google.com/mlengine/models](https://console.cloud.google.com/mlengine/models).

Make a prediction using one of the deployed model versions as follows.
In the [`components/older/kubeflow/tf-serving`](components/older/kubeflow/tf-serving) directory, run the following client script, replacing `<MODEL_VERSION_NAME>` with one of your deployed versions. (Note that this script assumes that you have gcloud configured to point to the correct project.  If it is not, first run `gcloud config set project <YOUR_PROJECT_NAME>`). You'll need to use Python 2.7 and have `tensorflow_serving-api` installed to run the script.

```sh
python chicago_taxi_client.py \
  --num_examples=1 \
  --examples_file='../taxi_model/data/eval/data.csv' \
  --server=mlengine:taxifare --model_name=<CMLE_MODEL_VERSION_NAME>
```

#### Access the TF-serving endpoints for your learned model

This workflow deploys your learned models not only to Cloud ML Engine, but also to [TensorFlow Serving](https://github.com/tensorflow/serving), which is part  of the Kubeflow installation.

View the TF-serving endpoint services by:

```sh
kubectl get services -n kubeflow
```

Look for the services with prefix `workflow-1`, and note their names. You should see two.

Port-forward to one of the services as follows:

```
kubectl port-forward --namespace kubeflow svc/<SERVICE NAME> 9000:9000
```

Then, run the client script as follows, replacing the following with your service name. You'll need to use Python 2.7 and have `tensorflow_serving-api` and `tensorflow-transform` installed to run the script.


```sh
python chicago_taxi_client.py \
  --num_examples=1 \
  --examples_file='../taxi_model/data/eval/data.csv' \
  --server=localhost:9000 --model_name=<SERVICE NAME>
```

### Example workflow 2

This workflow shows how you might use TFMA to investigate relative accuracies of models trained on different datasets, evaluating against fresh data. As part of the preprocessing step, it pulls data directly from the source [BigQuery Chicago taxi dataset](https://cloud.google.com/bigquery/public-data/chicago-taxi), with differing min and max time boundaries, effectively training on 'recent' data vs a batch that includes older data.  Then, it runs TFMA analysis on both learned models, using 'recent' data for evaluation. As with Workflow 1 above, it also deploys the trained models to Cloud ML Engine.

Run the second example [as described here](samples/kubeflow-tf/older/README.md#example-workflow-2).

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-pls/wkflw2_graph_ds.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-pls/wkflw2_graph_ds.png" width="90%"/></a>

<figcaption><br/><i>Comparing models trained on datasets that cover differing time intervals</i></figcaption>
</figure>

<p></p>

#### View the results of model analysis in a Jupyter notebook

As for Workflow 1, you can view the results of the TFMA analysis in a Jupyter notebook.
See [above](#view-the-results-of-model-analysis-in-a-jupyter-notebook) for details.


#### Use your models for prediction with Cloud ML Engine Online Prediction

As part of the workflow, your trained models were deployed to Cloud ML Engine Online Prediction. As with Workflow 1, you can use these models for prediction.
See [above](#use-your-models-for-prediction-with-cloud-ml-engine-online-prediction) for details.


## Navigating the example code

The code is organized into two subdirectories.

- [`components`](components) holds the implementation of the various Pipeline steps used in the workflows. These steps are container-based, so for each such step, we need to provide both the source code used in the container, and the specification of how to build the container.

- [`samples`](samples) holds the Pipeline definitions.
They use prebuilt containers so that the examples are easy to run, but if you want to do any customization, you can build your own component containers and use those instead.

## Cleanup

When you're done, __delete your GKE cluster so that you don't incur extra charges__. An easy way to do this is via the
[Cloud Console](https://console.cloud.google.com/kubernetes).

If you're not ready to take down the whole GKE cluster, you might want to do some finer-grained cleanup:

<!-- ### Delete the completed pods for a workflow

The completed Argo pods aren't deleted by default -- this allows easier debugging, since you can view their logs via
`kubectl logs <podname> main`.
To delete the completed Kubernetes pods for a given Argo workflow, run the following, replacing `<WORKFLOW_NAME>` with the name of the workflow:

```sh
argo delete <WORKFLOW_NAME>
``` -->

### Take down the TF-serving endpoints

When you're done running the examples, you can take down your TF-serving endpoints by deleting their Kubernetes services & deployments. The default quota of external IP addresses for a project is quite small, so you'll probably want to do this.

Run:

```sh
kubectl get services
```

Look for the services with prefix `preproc-train-deploy2-analyze` and delete those via:

```sh
kubectl delete services <service names>
```

Then look for the related deployments (`kubectl get deployments`) and delete those as well (`kubectl delete deployments <deployment names>`).

<!-- ## Summary

[TBD..] -->


