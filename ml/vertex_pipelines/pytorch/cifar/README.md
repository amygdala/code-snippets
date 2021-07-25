
# Vertex Pipelines PyTorch end-to-end CIFAR10 example

The [notebook](./pytorch_cifar10_vertex_pipelines.ipynb) in this directory shows two variants of a PyTorch CIFAR10 end-to-end example using [Vertex Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines).

Thanks to the PyTorch team at Facebook for some of the underlying code and much helpful advice.

## Running the pipelines examples on an OSS KFP installation


It also is possible to run the examples pipelines on an open-source Kubeflow Pipelines installation via [v2 compatibility mode](https://www.kubeflow.org/docs/components/pipelines/sdk/v2/v2-compatibility/#compiling-and-running-pipelines-in-v2-compatibility-mode).  This requires a KFP 1.7x installation or greater.  At time of writing, this requires a [KFP 'standalone' installation](https://www.kubeflow.org/docs/components/pipelines/installation/standalone-deployment/) as described below.
You will need to set up your GKE cluster to support a GPU node pool, and— to run the examples without modification— create the cluster with the `cloud-platform` scope.

### Create a GKE cluster

(To run the commands below, you will need to have the [gcloud sdk installed](https://cloud.google.com/sdk/docs/install) and configured to use for your GCP project).

For example, you can create the cluster via:

```sh
gcloud container clusters create kfp-test  --zone=us-central1-c --machine-type=n1-standard-8  --enable-autoscaling --enable-autorepair --scopes=cloud-platform --min-nodes=2 --max-nodes=10
```
Then create the node pool similarly to the following:

```sh
gcloud container node-pools create gpu-pool  --cluster=kfp-test --zone us-central1-c --enable-autoscaling --max-nodes=8 --min-nodes=0  --machine-type n1-highmem-8  --scopes cloud-platform --verbosity error  --accelerator=type=nvidia-tesla-v100,count=1
```
**Note**: Your project will need to have quota for the accelerator type that you specify.  Then, in the [notebook example](./pytorch_cifar10_vertex_pipelines.ipynb), when defining the first version of the pipeline, you must make sure to specify the same accelerator type:

```python
 cifar_train_task.add_node_selector_constraint(
     # You can change this to use a different accelerator. Ensure you have quota for it.
     "cloud.google.com/gke-accelerator", "nvidia-tesla-v100"
 )
```
After the cluster has been created, get its credentials:

```sh
gcloud container clusters get-credentials kfp-test2 --zone us-central1-c --project <your-project-id>
```

Then, apply the Nvidia driver daemonset to your cluster:

```sh
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

### Deploy KFP on the GKE cluster

Follow the instructions [here](https://www.kubeflow.org/docs/components/pipelines/installation/standalone-deployment/) to deploy KFP on your cluster.
An installation >= 1.7.0 is required to use the *v2 compatibility mode* successfully with these pipelines. At time of writing, this requires setting `export PIPELINE_VERSION=1.7.0-rc.2` before fetching the installation manifests. (You can find the releases [here](https://github.com/kubeflow/pipelines/releases)).

### Find the host URL for your installation

After installation has completed, navigate to `https://console.cloud.google.com/ai-platform/pipelines/clusters`, where you should see your installation listed. Click on **SETTINGS**, which opens a dialog with a "Connect Guide".  You should see a panel something like the following.  Copy this information, as it will be required when you run the 'v2 compatibility mode' sections in the example notebook.

```
import kfp
client = kfp.Client(host='https://xxxxxxx-dot-us-central1.pipelines.googleusercontent.com')
```

You should now be set up to run the `v2 compatibility mode` sections in the example notebook.

Note: the example pipelines will not run as is on non-GKE clusters, since many of the steps require that they are authenticated to GCP services.
