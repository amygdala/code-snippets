
# Examples of Kubeflow + Argo for ML workflow

[Kubeflow](https://www.kubeflow.org/) is an OSS project to support a machine learning stack on Kubernetes, towards making deployments of ML workflows on Kubernetes simple, portable and scalable.

This directory contains some ML workflow examples that run on Kubeflow plus [Argo](https://github.com/argoproj/argo).

The examples highlight how Kubeflow can help support portability, composability and reproducibility, scalability, and visualization and collaboration in your ML lifecycle; and make it easier to support hybrid ML solutions.

The examples include use of [TensorFlow Transform](https://github.com/tensorflow/transform) for preprocessing and to avoid training/serving skew; Kubeflow's tf-jobs CRD for supporting distributed training; and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis.
The workflows also include deployment of the trained models to both
[Cloud ML Engine Online Prediction](https://cloud.google.com/ml-engine/docs/tensorflow/prediction-overview);
and to [TensorFlow Serving](https://github.com/tensorflow/serving) via Kubeflow.

## Installation and setup

The examples require a Google Cloud Platform (GCP) account and project, a Google Kubernetes Engine (GKE) cluster running Kubeflow and Argo.
(It's not necessary that Kubeflow be run on GKE, but it would require some additional credentials setup to run these examples elsewhere).

You'll also either need [gcloud](https://cloud.google.com/sdk/) installed on your laptop; or alternately you can run gcloud in the [Cloud Shell](https://cloud.google.com/shell/docs/) via the GCP [Cloud Console](https://console.cloud.google.com).

### Create a GCP project and enable the necessary APIs

If you don't have a Google Cloud Platform (GCP) account yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.

Then, [create a GCP Project](https://console.cloud.google.com/) if you don't have one.

Then, __[enable](https://support.google.com/cloud/answer/6158841?hl=en) the following APIs__ for your project: Dataflow, BigQuery, Cloud Machine Learning Engine, and Kubernetes Engine. (You don't need to create any credentials for these examples, as we'll set up a Kubernetes Engine (GKE) cluster with sufficient access).

### Install the gcloud sdk (or use the Cloud Shell)

Install the GCP [gcloud command-line sdk](https://cloud.google.com/sdk/install) on your laptop.

Or, if you don't want to install `gcloud` locally, you can bring up the [Cloud Shell](https://cloud.google.com/shell/docs/quickstart) from the Cloud Console and run `kubectl` and `gcloud` from there.  When you start the cloud shell, confirm from the initial output that it's set to use the GCP project in which your GKE cluster is running.

### Set up a Kubernetes Engine (GKE) cluster

Visit the [cloud console](https://console.cloud.google.com/kubernetes) for your project and create a GKE cluster. Give it at least 3 nodes.

<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup1.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup1.png" width=600/></a>

Click The '__Advanced edit__' button, and under **Access scopes**, click 'Allow full access to all Cloud APIs'. (You can also enable autoscaling in this panel).

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup2.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/gke_setup2.png" /></a>
<figcaption>_Set up your GKE cluster to allow full access to all Cloud APIs._</figcaption>
</figure>

After your GKE cluster is up and running, click the "Connect" button
[to the right of the cluster](https://console.cloud.google.com/kubernetes) to set your `kubectl` context to the new cluster.  The gcloud command will look like the following, replacing `<your cluster zone>`, `<your cluster name>`,
and `<your project>` with the correct zone, cluster name, and project name.

```
gcloud container clusters get-credentials <your cluster name> --zone <your cluster zone> --project
```

Then run the following command, replacing `<your gcp account email>` with the email associated with your GCP project.

```
kubectl create clusterrolebinding default-admin --clusterrole=cluster-admin --user=<your gcp account email>
```

### Install ksonnet

You'll first need to [install ksonnet](https://github.com/ksonnet/ksonnet#install) version 0.11.0 or greater. It is used for the Kubeflow install. Follow the instructions for your OS.

To install on Cloud Shell or a local Linux machine, set this environment variable:

```
export KS_VER=ks_0.11.0_linux_amd64
```

Then download and unpack the appropriate binary, and add it to your $PATH:

```
wget -O /tmp/$KS_VER.tar.gz https://github.com/ksonnet/ksonnet/releases/download/v0.11.0/$KS_VER.tar.gz

mkdir -p ${HOME}/bin
tar -xvf /tmp/$KS_VER.tar.gz -C ${HOME}/bin

export PATH=$PATH:${HOME}/bin/$KS_VER
```

### Install Kubeflow + Argo on the GKE cluster

Now you're ready to install Kubeflow and Argo. The order doesn't matter.

Install Argo as described [here](https://github.com/argoproj/argo/blob/master/demo.md).

Then install Kubeflow. These instructions are for version 0.2.2.
We're following nearly the same process as described in the [quick start](https://www.kubeflow.org/docs/started/getting-started#quick-start), but we need to do an extra step.
The example code uses the tf-jobs API `v1alpha1`, which is not the 0.2.2 default.
So we'll build but not deploy the ksonnet app, edit the tf-jobs API info, then deploy.

First build the ks app:

```
export KUBEFLOW_VERSION=0.2.2; export KUBEFLOW_DEPLOY=false
curl https://raw.githubusercontent.com/kubeflow/kubeflow/v${KUBEFLOW_VERSION}/scripts/deploy.sh | bash
```

Then do the actual deployment as follows.  If you built into a different directory than `kubeflow_ks_app`, change to that subdir instead.

```
cd kubeflow_ks_app
ks param set kubeflow-core tfJobVersion v1alpha1
ks apply default
```

### Create a Google Cloud Storage (GCS) bucket

Your ML workflow will need access to a GCS bucket. Create one as [described here](https://cloud.google.com/storage/docs/creating-buckets).  Make it *regional*, not multi-regional.

## Running the examples

There are two examples. Both revolve around a TensorFlow 'taxi fare tip prediction' model, with data pulled from a [public BigqQery dataset of Chicago taxi trips](https://cloud.google.com/bigquery/public-data/chicago-taxi).

Both examples use [TFT](https://github.com/tensorflow/transform) for data preprocessing and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis (either can be run via local [Apache Beam](https://beam.apache.org/), or via [Dataflow](https://cloud.google.com/dataflow)); do distributed training via the Kubeflow tf-jobs CRD; and deploy to the Cloud ML Engine Online Prediction service.
The first example also includes use of [TF-Serving](https://github.com/tensorflow/serving) via Kubeflow, and the second includes use of [BigQuery](cloud.google.com/bigquery) as a data source.

Change to the [`samples/kubeflow-tf`](samples/kubeflow-tf) directory to run the examples.

For both workflows, you can use the Argo UI to track the progress of a workflow over time, e.g.:

```
kubectl port-forward $(kubectl get pods -n default -l app=argo-ui -o jsonpath='{.items[0].metadata.name}') -n default 8001:8001
```
See the Argo documentation for more.

You can also use `kubectl` to watch the pods created in the various stages of the workflows.

```
kubectl get pods -o wide --watch=true
```

In particular, this lets you monitor creation and status of the pods used for Kubeflow tf-job distributed training.

### Example workflow 1

Run the first example [as described here](samples/kubeflow-tf/README.md).

<2 paths, feature experimentation via passing in the preprocessing function.... deployment to CMLE as well as TF-serving..>

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow1.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow1.png" width="90%"/></a>
<figcaption>_..._</figcaption>
</figure>


#### View the results of model analysis in a Jupyter notebook

One of the workflow steps runs TensorFlow Model Analysis (TFMA) on the trained model, using a given [specification of how to slice the data](xxx).  You can visualize the results via a Jupyter notebook. Kubeflow's JupyterHub installation makes this easy to do, via a `port-forward` to your GKE cluster. The necessary libraries and visualization widgets are already installed.
See the "To connect to your Jupyter Notebook locally:" section in this [Kubeflow guide](https://www.kubeflow.org/docs/guides/components/jupyter/) for more info.

<point to notebook in the repo...>
<this notebook also... CMLE OP..>

#### Access the TF-serving endpoints for your learned model

This workflow deploys your learned models not only to Cloud ML Engine, but also to [TensorFlow Serving](https://github.com/tensorflow/serving), which is part  of the Kubeflow installation.

To make it easy to demo, the TF-serving deployments use a Kubernetes service of type `LoadBalancer`, which creates an endpoint with an external IP. (For a production system, you'd probably want to use something like [Cloud Identity-Aware Proxy](https://cloud.google.com/iap/) instead).

View the TF-serving endpoint services by:

```
kubectl get services
```

Look for the services with prefix `preproc-train-deploy2-analyze`, and note their names and external IP addresses.

You can make requests against these endpoints using this script: [`chicago_taxi_client.py`](components/kubeflow/tf-serving/chicago_taxi_client.py).
Change to the `components/kubeflow/tf-serving` directory and run the script as follows, replacing the following with your external IP address and service name. You'll need to have `tensorflow_serving` installed to do this.

```
python chicago_taxi_client.py \
  --num_examples=1 \
  --examples_file='../taxi_model/data/eval/data.csv' \
  --server=<EXTERNAL IP>:9000 --model_name=<SERVICE NAME>
```


When you're done experimenting, you'll probably want to take down the tf-serving endpoints.  See the "Cleanup" section below.

### Example workflow 2

<...option to grab data from bigquery as part of preprocessing.. evaluate 2 models (built with diff input datasets) against three different eval files...>

Run the second example [as described here](samples/kubeflow-tf/README.md).

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow2.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-argo/argo_workflow2.png" width="90%"/></a>
<figcaption>_...._</figcaption>
</figure>

#### View the results of model analysis in a Jupyter notebook

As above for Example 1, you can view the


### Using Cloud Dataflow for TFT and/or TFMA

... <slow to start up, so for our small datasets is slower, but this will be amortized for larger jobs that benefit from dataflows ability to scale out automatically...>

## Navigating the example code

The code is organized into two subdirectories.

- [`components`](components) holds the implementation of the various Argo steps used in the workflows. These steps are container-based, so for each such step, we need to provide both the source code used in the container, and the specification of how to build the container.


- [`samples`](samples) holds the Argo workflow definitions.
We link to prebuilt containers so that the examples are easy to run, but if you want to do any customization, you can build your own component containers and use those instead.

## Cleanup

...

### Delete the completed argo pods

### Take down the TF-serving endpoints

### Delete your GKE cluster

## Summary

[add some of the points from the slide deck?...]


