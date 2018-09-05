

# Examples of Kubeflow + Argo for ML workflow


  - [Installation and setup](#installation-and-setup)
    - [Create a GCP project and enable the necessary APIs](#create-a-gcp-project-and-enable-the-necessary-apis)
    - [Install the gcloud sdk (or use the Cloud Shell)](#install-the-gcloud-sdk-or-use-the-cloud-shell)
    - [Set up a Kubernetes Engine (GKE) cluster](#set-up-a-kubernetes-engine-gke-cluster)
    - [Install ksonnet](#install-ksonnet)
    - [Install Kubeflow + Argo on the GKE cluster](#install-kubeflow--argo-on-the-gke-cluster)
    - [Create a Google Cloud Storage (GCS) bucket](#create-a-google-cloud-storage-gcs-bucket)
  - [Running the examples](#running-the-examples)
    - [Example workflow 1](#example-workflow-1)
      - [View the results of model analysis in a Jupyter notebook](#view-the-results-of-model-analysis-in-a-jupyter-notebook)
      - [Use your models for prediction with Cloud ML Engine Online Prediction](#use-your-models-for-prediction-with-cloud-ml-engine-online-prediction)
      - [Access the TF-serving endpoints for your learned model](#access-the-tf-serving-endpoints-for-your-learned-model)
    - [Example workflow 2](#example-workflow-2)
      - [View the results of model analysis in a Jupyter notebook](#view-the-results-of-model-analysis-in-a-jupyter-notebook-1)
      - [Use your models for prediction with Cloud ML Engine Online Prediction](#use-your-models-for-prediction-with-cloud-ml-engine-online-prediction-1)
  - [Navigating the example code](#navigating-the-example-code)
  - [Cleanup](#cleanup)
    - [Delete the completed pods for a workflow](#delete-the-completed-pods-for-a-workflow)
    - [Take down the TF-serving endpoints](#take-down-the-tf-serving-endpoints)
  - [Summary](#summary)

[Kubeflow](https://www.kubeflow.org/) is an OSS project to support a machine learning stack on Kubernetes, to make deployments of ML workflows on Kubernetes simple, portable and scalable.

This directory contains some ML workflow examples that run on Kubeflow plus
[Argo](https://github.com/argoproj/argo) (a container-native workflow framework for Kubernetes).

The examples highlight how Kubeflow can help support portability, composability and reproducibility, scalability, and visualization and collaboration in your ML lifecycle; and make it easier to support hybrid ML solutions.

The examples include use of [TensorFlow Transform](https://github.com/tensorflow/transform) (TFT) for preprocessing and to avoid training/serving skew; Kubeflow's tf-jobs CRD for supporting distributed training; and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis.
The workflows also include deployment of the trained models to both
[Cloud ML Engine Online Prediction](https://cloud.google.com/ml-engine/docs/tensorflow/prediction-overview);
and to [TensorFlow Serving](https://github.com/tensorflow/serving) via Kubeflow.

## Installation and setup

The examples require a Google Cloud Platform (GCP) account and project, and a Google Kubernetes Engine (GKE) cluster running Kubeflow and Argo.
(It's not necessary that Kubeflow be run on GKE, but it would require some additional credentials setup to run these examples elsewhere).

You'll also either need [gcloud](https://cloud.google.com/sdk/) installed on your laptop; or alternately you can run gcloud in the [Cloud Shell](https://cloud.google.com/shell/docs/) via the GCP [Cloud Console](https://console.cloud.google.com).

### Create a GCP project and enable the necessary APIs

If you don't have a Google Cloud Platform (GCP) account yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.

Then, [create a GCP Project](https://console.cloud.google.com/) if you don't have one.

Then, __[enable](https://support.google.com/cloud/answer/6158841?hl=en) the following APIs__ for your project: Dataflow, BigQuery, Cloud Machine Learning Engine, and Kubernetes Engine. (You don't need to create any credentials for these APIs, as we'll set up a Kubernetes Engine (GKE) cluster with sufficient access).

### Install the gcloud sdk (or use the Cloud Shell)

Install the GCP [gcloud command-line sdk](https://cloud.google.com/sdk/install) on your laptop.

Or, if you don't want to install `gcloud` locally, you can bring up the [Cloud Shell](https://cloud.google.com/shell/docs/quickstart) from the Cloud Console and run `kubectl` and `gcloud` from there.  When you start the cloud shell, confirm from the initial output that it's set to use the GCP project in which your GKE cluster is running.

### Set up a Kubernetes Engine (GKE) cluster

Visit the [Cloud Console](https://console.cloud.google.com/kubernetes) for your project and create a GKE cluster.
So that you don't have any Kubernetes pods stuck in "Pending" for lack of resources while you run the examples, consider giving it 4 4-core nodes. You may need to [increase your Compute Engine API CPUs quota](https://console.cloud.google.com/iam-admin/quotas) before you do this.
(See the 'Cleanup' section below so that you don't get further charged for the cluster after you're done experimenting).

<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup_start.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup_start.png" width="600"/></a>

Click The '__Advanced edit__' button, and under **Access scopes**, click 'Allow full access to all Cloud APIs'. (You can also enable autoscaling in this panel if you want).

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup_adv.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup_adv.png" /></a>
<figcaption><br/><i>Set up your GKE cluster to allow full access to all Cloud APIs.</i></figcaption>
</figure>

<p></p>

After your GKE cluster is up and running, click the "Connect" button
[to the right of the cluster](https://console.cloud.google.com/kubernetes) in the Console, to set your `kubectl` context to the new cluster.  The gcloud command will look like the following, replacing `<your cluster zone>`, `<your cluster name>`,
and `<your project>` with the correct zone, cluster name, and project name.

```sh
gcloud container clusters get-credentials <your cluster name> --zone <your cluster zone> --project
```

Then run the following command, replacing `<your gcp account email>` with the email associated with your GCP project.

```sh
kubectl create clusterrolebinding default-admin --clusterrole=cluster-admin --user=<your gcp account email>
```
(You need to be a project *owner* to run this command).

### Install ksonnet

You'll first need to [install ksonnet](https://github.com/ksonnet/ksonnet#install) version 0.11.0 or greater. It is used for the Kubeflow install. Follow the instructions for your OS.

To install on Cloud Shell or a local Linux machine, set this environment variable:

```sh
export KS_VER=ks_0.11.0_linux_amd64
```

Then download and unpack the appropriate binary, and add it to your $PATH:

```sh
wget -O /tmp/$KS_VER.tar.gz https://github.com/ksonnet/ksonnet/releases/download/v0.11.0/$KS_VER.tar.gz

mkdir -p ${HOME}/bin
tar -xvf /tmp/$KS_VER.tar.gz -C ${HOME}/bin

export PATH=$PATH:${HOME}/bin/$KS_VER
```

### Install Kubeflow + Argo on the GKE cluster

Now you're ready to install Kubeflow and Argo.

Install Argo as described [here](https://github.com/argoproj/argo/blob/master/demo.md).

Then install Kubeflow. These instructions are for version 0.2.2.
We're following nearly the same process as described in the [quick start](https://www.kubeflow.org/docs/started/getting-started#quick-start), but we need to do an extra step.
The example code uses the tf-jobs API `v1alpha1`, which is not the 0.2.2 default.
So we'll build but not deploy the ksonnet app, edit the tf-jobs API info, _then_ deploy.

First build the ksonnet app:

```sh
export KUBEFLOW_VERSION=0.2.2; export KUBEFLOW_DEPLOY=false
curl https://raw.githubusercontent.com/kubeflow/kubeflow/v${KUBEFLOW_VERSION}/scripts/deploy.sh | bash
```

Then do the actual deployment as follows.  If you generated your build into a different directory than
`kubeflow_ks_app`, change to that subdir instead.

```sh
cd kubeflow_ks_app
ks param set kubeflow-core tfJobVersion v1alpha1
ks apply default
```

(If you see errors, double check that you've installed ksonnet).

### Create a Google Cloud Storage (GCS) bucket

Your ML workflow will need access to a GCS bucket. Create one as [described here](https://cloud.google.com/storage/docs/creating-buckets).  Make it *regional*, not multi-regional.

## Running the examples

There are two examples. Both revolve around a TensorFlow 'taxi fare tip prediction' model, with data pulled from a [public BigqQery dataset of Chicago taxi trips](https://cloud.google.com/bigquery/public-data/chicago-taxi).

Both examples use [TFT](https://github.com/tensorflow/transform) for data preprocessing and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis (either can be run via local [Apache Beam](https://beam.apache.org/), or via [Dataflow](https://cloud.google.com/dataflow)); do distributed training via the Kubeflow tf-jobs [custom resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/); and deploy to the Cloud ML Engine Online Prediction service.
The first example also includes use of [TF-Serving](https://github.com/tensorflow/serving) via Kubeflow, and the second includes use of [BigQuery](cloud.google.com/bigquery) as a data source.

Change to the [`samples/kubeflow-tf`](samples/kubeflow-tf) directory to run the examples.

For both workflows, you can use the Argo UI to track the progress of a workflow over time, e.g.:

```sh
kubectl port-forward $(kubectl get pods -n default -l app=argo-ui -o jsonpath='{.items[0].metadata.name}') -n default 8001:8001
```
See the Argo documentation for more.

You can also use `kubectl` to watch the pods created in the various stages of the workflows.

```sh
kubectl get pods -o wide --watch=true
```

In particular, this lets you monitor creation and status of the pods used for Kubeflow tf-job distributed training.

### Example workflow 1

Run the first example [as described here](samples/kubeflow-tf/README.md#example-workflow-1).
This example illustrates how you can use a ML workflow to experiment with
[TFT](https://github.com/tensorflow/transform)-based feature engineering, and how you can serve your trained model from both on-prem and cloud endpoints.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow1.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow1.png" width="90%"/></a>
<figcaption><br><i>A workflow for TFT-based feature engineering experimentation</i></figcaption>
</figure>

<p></p>

The workflow runs two paths concurrently, passing a different TFT preprocessing function to each ([`preprocessing.py`](components/dataflow/tft/preprocessing.py) vs [`preprocessing2.py`](components/dataflow/tft/preprocessing.py)).

Then each model is trained, using Kubeflow's tf-jobs [CRD](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/).  For example purposes, distributed training is used for one path, and single-node training is used for the other.  This is done by specifying the number of *workers* and *parameter servers* to use for the training job.

For this workflow, one processing path used two workers and one parameter server as well as a 'master' (for distributed training), and the other is hardwired to use just one 'master' (single-node training).  While the training parts of the workflow are running, you'll see something like the following in your list of pods:

```
trainer-4d449038-afa7-4906-98ad-4e32b811-master-qm3y-0-qp1b0   1/1       Running     0          1m        10.20.0.12   gke-pipelines-default-pool-2a81a07a-ptmq
trainer-b64ef136-953d-4b57-b4e1-604aabff-master-huex-0-szz88   1/1       Running     0          1m        10.20.0.10   gke-pipelines-default-pool-2a81a07a-ptmq
trainer-b64ef136-953d-4b57-b4e1-604aabff-ps-huex-0-x983w       1/1       Running     0          1m        10.20.2.9    gke-pipelines-default-pool-2a81a07a-26k2
trainer-b64ef136-953d-4b57-b4e1-604aabff-worker-huex-0-ki35n   1/1       Running     0          1m        10.20.2.10   gke-pipelines-default-pool-2a81a07a-26k2
trainer-b64ef136-953d-4b57-b4e1-604aabff-worker-huex-1-imzg0   1/1       Running     0          1m        10.20.0.11   gke-pipelines-default-pool-2a81a07a-ptmq
```

When the training is finished, both models are deployed to both Cloud ML Engine and TF-Serving.  Additionally, the the models are analyzed using [TFMA](https://github.com/tensorflow/model-analysis/), as described below.

#### View the results of model analysis in a Jupyter notebook

One of the workflow steps runs TensorFlow Model Analysis (TFMA) on the trained model, using a given [specification of how to slice the data](components/dataflow/tfma/model_analysis-taxi.py#L45).  You can visualize the results via a Jupyter notebook.
You can do this in a local notebook (see the TFMA docs for installation).

Or, kubeflow's JupyterHub installation makes this easy to do, via a `port-forward` to your GKE cluster. The necessary libraries and visualization widgets are already installed.
See the *"To connect to your Jupyter Notebook locally"* section in this [Kubeflow guide](https://www.kubeflow.org/docs/guides/components/jupyter/) for more info.

Load and run the [`tfma_expers.ipynb`](components/dataflow/tfma/tfma_expers.ipynb) notebook to explore the results of the TFMA analysis.

#### Use your models for prediction with Cloud ML Engine Online Prediction

As part of the workflow, your models were deployed to Cloud ML Engine Online Prediction. The model name is `taxifare`, and the version names are derived from the workflow name.

You can view the deployed versions of the `taxifare` model in the Cloud Console:
[https://console.cloud.google.com/mlengine/models](https://console.cloud.google.com/mlengine/models).

Make a prediction using one of the deployed model versions as follows.  Change to the [`components/cmle`](components/cmle) directory, and run the following command, replacing `<YOUR_PROJECT_NAME>` and `<MODEL_VERSION_NAME>`.

```sh
gcloud ml-engine predict --model=taxifare --json-instances=temp_input2.json --project=<YOUR_PROJECT_NAME> \
 --version=<MODEL_VERSION_NAME>
```
You can set any of these model versions to be the default. For the default model, the request does not need to include the `--version` arg.

#### Access the TF-serving endpoints for your learned model

This workflow deploys your learned models not only to Cloud ML Engine, but also to [TensorFlow Serving](https://github.com/tensorflow/serving), which is part  of the Kubeflow installation.

To make it easy to demo, the TF-serving deployments use a Kubernetes service of type `LoadBalancer`, which creates an endpoint with an external IP. (For a production system, you'd probably want to use something like [Cloud Identity-Aware Proxy](https://cloud.google.com/iap/) instead).

View the TF-serving endpoint services by:

```sh
kubectl get services
```

Look for the services with prefix `preproc-train-deploy2-analyze`, and note their names and external IP addresses.

You can make requests against these endpoints using this script: [`chicago_taxi_client.py`](components/kubeflow/tf-serving/chicago_taxi_client.py).
Change to the `components/kubeflow/tf-serving` directory and run the script as follows, replacing the following with your external IP address and service name. You'll need to have `tensorflow_serving` installed to do this.

```sh
python chicago_taxi_client.py \
  --num_examples=1 \
  --examples_file='../taxi_model/data/eval/data.csv' \
  --server=<EXTERNAL IP>:9000 --model_name=<SERVICE NAME>
```


When you're done experimenting, you'll probably want to take down the tf-serving endpoints.  See the "Cleanup" section below.

### Example workflow 2

This workflow shows how you might use TFMA to investigate relative accuracies of models trained on different datasets, evaluating against fresh data. As part of the preprocessing step, it pulls data directly from the source [BigQuery Chicago taxi dataset](https://cloud.google.com/bigquery/public-data/chicago-taxi), with differing min and max time boundaries, effectively training on 'recent' data vs a batch that includes older data.  Then, it runs TFMA analysis on both learned models, using 'recent' data for evaluation.  (It also evaluates the 'recent' data against an older model trained on older data). As with Workflow 1 above, it also deploys the trained models to Cloud ML Engine.

Run the second example [as described here](samples/kubeflow-tf/README.md#example-workflow-2).

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow2.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow2.png" width="90%"/></a>
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

- [`components`](components) holds the implementation of the various Argo steps used in the workflows. These steps are container-based, so for each such step, we need to provide both the source code used in the container, and the specification of how to build the container.

- [`samples`](samples) holds the Argo workflow definitions.
The definitions use prebuilt containers so that the examples are easy to run, but if you want to do any customization, you can build your own component containers and use those instead.

## Cleanup

When you're done, __delete your GKE cluster so that you don't incur extra charges__. An easy way to do this is via the
[Cloud Console](https://console.cloud.google.com/kubernetes).

If you're not ready to take down the whole GKE cluster, you might want to do some finer-grained cleanup, as follows:

### Delete the completed pods for a workflow

The completed Argo pods aren't deleted by default -- this allows easier debugging, since you can view their logs via
`kubectl logs <podname> main`.
To delete the completed Kubernetes pods for a given Argo workflow, run the following, replacing `<WORKFLOW_NAME>` with the name of the workflow:

```sh
argo delete <WORKFLOW_NAME>
```

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


