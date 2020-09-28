# Kubeflow Pipelines Distributed Keras Tuner example

This example shows how to run a Kubeflow Pipelines-based hyperparameter tuning example using the Keras Tuner, leveraging GKE to support concurrent search through the HP space.

It's currently under development, so may have some rough edges.

## Introduction

The performance of a machine learning model is often crucially dependent on the choice of good [hyperparameters][1]. For models of any complexity, relying on trial and error to find good values for these parameters does not scale. This tutorial shows how to use [Cloud AI Platform Pipelines][2]  in conjunction with [Keras Tuner][3] to build a hyperparameter-tuning workflow that uses distributed HP search.

[Cloud AI Platform Pipelines][4], currently in Beta, provides a way to deploy robust, repeatable machine learning pipelines along with monitoring, auditing, version tracking, and reproducibility, and gives you an easy-to-install, secure execution environment for your ML workflows. AI Platform Pipelines is based on [Kubeflow Pipelines][5] (KFP) installed on a [Google Kubernetes Engine (GKE)][6] cluster, and can run pipelines specified via both the KFP and TFX SDKs. See [this blog post][7] for more detail on the Pipelines tech stack.
You can create an AI Platform Pipelines installation with just a few clicks. After installing, you access AI Platform Pipelines by visiting the AI Platform Panel in the [Cloud Console][8].

[Keras Tuner][9] is an easy-to-use, distributable hyperparameter optimization framework. Keras Tuner makes it easy to define a search space and leverage included algorithms to find the best hyperparameter values. Keras Tuner comes with several search  algorithms built-in, and is also designed to be easy for researchers to extend in order to experiment with new search algorithms.  It is straightforward to run the tuner in [distributed search mode][10], which we’ll leverage for this example.

The intent of using the Keras Tuner is [not to do full training, but to find the best starting points][11]. Typically, the number of epochs run in the trials would be quite a bit smaller than that used in the full training. So, a useful HP tuning-based workflow could be:

- perform a distributed HP tuning search, and obtain the results
- do concurrent model training runs for each of the best N parameter configurations, and export the model for each
- serve the results (perhaps after model evaluation).

As mentioned above, a [Cloud AI Platform Pipeline][12] runs under the hood on a GKE cluster.  This makes it straightforward to implement this workflow— including the distributed HP search— so that you just need to launch a pipeline job to kick it off.  This tutorial shows how to do that.  It also shows how to use preemptible GPU-enabled VMS for the HP search, to reduce costs; and how to use [TF-serving][13] to deploy the trained model(s) on the same cluster for serving.
As part of the process, we’ll see how GKE provides a scalable, resilient platform with easily-configured use of accelerators.

## About the dataset and modeling task

### The dataset

The [Cloud Public Datasets Program][14] makes available public datasets that are useful for experimenting with machine learning. Just as we did in our “[Explaining model predictions on structured data][15]” post, we’ll use data that is essentially a join of two public datasets stored in [BigQuery][16]: [London Bike rentals][17] and [NOAA weather data][18], with some additional processing to clean up outliers and derive additional GIS and day-of-week fields.

### The modeling task and Keras model

We’ll use this dataset to build a [Keras][19] _regression model_ to predict the **duration** of a bike rental based on information about the start and end stations, the day of the week, the weather on that day, and other data. If we were running a bike rental company, for example, these predictions—and their explanations—could help us anticipate demand and even plan how to stock each location.

We’ll then use the Keras Tuner package to do an HP search using this model.

## Keras tuner in distributed mode on GKE

The [Keras Tuner][20] supports running a hyperparameter search  in [distributed mode][21].
[Google Kubernetes Engine (GKE)][22] makes it straightforward to configure and run a distributed HP tuning search.  GKE is  a good fit not only because it lets you easily distribute the HP tuning workload, but because you can leverage autoscaling to boost node pools for a large job, then scale down when the resources are no longer needed.  It’s also easy to deploy trained models for serving onto the same GKE cluster, using [TF-serving][23].  In addition, the Keras Tuner works well with [preemptible VMs][24], making it even cheaper to run your workloads.

With the Keras Tuner’s distributed config, you specify one node as the ‘chief’, which coordinates the search, and ‘tuner’ nodes that do the actual work of running model training jobs using a given param set (the _trials_).  When you set up an HP search, you indicate the max number of trials to run, and how many ‘executions’ to run per trial. The Kubeflow pipeline allows dynamic specification of the number of tuners to use for a given HP search— this determines how many trials you can run concurrently— as well as the max number of trials and number of executions.

We’ll define the tuner components as Kubernetes [_jobs_][25], each specified to have  1 _replica_.   This means that if a tuner job pod is terminated for some reason prior to job completion, Kubernetes will start up another replica.
Thus, the Keras Tuner’s HP search is a good fit for use of [preemptible VMs][26].  Because the HP search bookkeeping— orchestrated by the tuner ‘chief’, via an ‘oracle’ file— tracks the state of the trials,  the configuration is robust to a tuner pod terminating unexpectedly— say, due to a preemption— and a new one being restarted.  The new job pod will get its instructions from the ‘oracle’ and continue running _trials_.
The example uses GCS for the tuners’ shared file system.

Once the HP search has finished, any of the tuners can obtain information on the N best parameter sets (as well as export the best model(s)).

## Defining the HP Tuning + training workflow as a pipeline

The definition of the pipeline itself is [here][27], specified using the KFP SDK.  It’s then compiled to an archive file and uploaded to AI Platforms Pipelines. (To compile it yourself, you’ll need to have the [KFP SDK installed][28].  Pipeline steps are container-based, and you can find the Dockerfiles and underlying code for the steps under the [`components`][29] directory.

The example pipeline first runs a distributed HP tuning search using a specified number of tuner workers,  then obtains the best `N` parameter combinations—by default, 2.  The pipeline step itself does not do the heavy lifting, but rather launches all the tuner *jobs* on GKE, which run concurrently, and monitors for their completion. (Unsurprisingly, this stage of the pipeline may run for quite a long time, depending upon how many HP search trials were specified and how many tuners you’re using).

The pipeline then runs full training jobs, concurrently, for each of the `N` best parameter sets (by default, 2).  It does this via the KFP [loop][30] construct, allowing the pipeline to support dynamic specification of `N`.
We’ll be able to compare the training jobs to each other using TensorBoard, both while they’re running and after they’ve completed.

Then, the trained models are deployed for serving for serving on the GKE cluster, using [TF-serving][31].  Each deployed model has its own cluster service endpoint.
(While not shown in this example, one could insert a step for model evaluation before deploying to TF-serving.)

For example, here is the [DAG][32] for a pipeline execution that did training and then deployed prediction services for the three best parameter configurations.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/keras_tuner/Screen%20Shot%202020-08-27%20at%2011.33.06%20AM%202.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/keras_tuner/Screen%20Shot%202020-08-27%20at%2011.33.06%20AM%202.png" width="60%"/></a>
<figcaption><br/><i>The DAG for keras tuner pipeline execution.  Here the three best parameter configurations were used for full training.</i></figcaption>
</figure>

## Running the example pipeline

> **Note**: this example may take a long time to run, and **incur significant charges** in its use of GPUs, depending upon how its parameters are configured.

### 1. Create a Cloud AI Platform Pipelines installation

To run the example, first create a Cloud AI Platform Pipelines installation, as described in the Pipelines [documentation][33].  **Be sure to tick the box that sets up the GKE cluster with full access to GCP APIs**.  It’s necessary to additionally configure the installation’s underlying GKE cluster as described below, before running the pipeline.

### 2. Do some cluster config and create GPU node pools

Once the Pipelines installation has finished, grab the credentials for the underlying GKE cluster as follows:

```bash
gcloud container clusters get-credentials <cluster-name> --zone <cluster-zone> --project <your-project>
```

Note that you can reconstruct this command via the “Connect” button in the GKE cluster listing [in the Cloud Console][34].  If you don’t have `gcloud` [installed][35] locally, you can run the commands in this section via the [Cloud Shell][36].

Next, give the `pipeline-runner` service account permissions to launch new Kubernetes resources:

```bash
kubectl create clusterrolebinding sa-admin --clusterrole=cluster-admin --serviceaccount=kubeflow:pipeline-runner
```

Then,  apply a Nvidia `daemonset`, that will install Nvidia drivers on any GPU-enabled cluster nodes.

```bash
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

Next, create GPU node pools. Just for the purposes of this example, we’ll create two: one a pool of [preemptible][37] nodes with one GPU each (the lighter-weight Keras tuner jobs can select this pool), and another of nodes with two GPUs each, which we’ll use for full training.  (The pipeline is defined so that the full training steps are placed on nodes with at least 2 GPUs, though you can change this value and recompile the pipeline if you like.)

We’ll configure both node pools to use autoscaling and to scale down to zero when not in use. This means that when you run the example, you may see pauses while a node pool scales up.

> Note: Before you run these commands, you may need to [**increase the GPU quota**][38] for your project.

Create the pool with preemptible nodes (edit this command with your cluster’s config info first):

```bash
gcloud container node-pools create preempt-gpu-pool \
    --cluster=<your-cluster> \
    --zone <cluster-zone> \
    --enable-autoscaling --max-nodes=8 --min-nodes=0 \
    --machine-type n1-highmem-8 \
    --preemptible \
    --scopes cloud-platform --verbosity error \
    --accelerator=type=nvidia-tesla-k80,count=1
```

Create the non-preemptible pool (again, first edit with your info):

```bash
gcloud container node-pools create gpu-pool \
    --cluster=<your-cluster> \
    --zone <cluster-zone> \
    --enable-autoscaling --max-nodes=2 --min-nodes=0 \
    --machine-type n1-highmem-8 \
    --scopes cloud-platform --verbosity error \
    --accelerator=type=nvidia-tesla-k80,count=2
```

(If you have quota for more powerful accelerators, you can optionally specify them instead of the k80s, though of course that will increase the expense).

> Note: There is no reason we couldn’t make all our GPU-enabled node pools preemptible, and run the full training steps on preemptible nodes as well.  While for simplicity we’re not doing that as part of this example, see [this blog post][39] for information on how to define a KFP pipeline that supports step retries on interruption.

### 3. Launch a Keras Tuner pipeline job

Upload the compiled ‘Keras Tuner’ pipeline to the Kubeflow Pipelines dashboard.  You can use this URL: [https://storage.googleapis.com/aju-dev-demos-codelabs/KF/compiled\_pipelines/bw.py.tar.gz][40], or if you’ve checked out or downloaded the [repo][41], you can upload the [compiled archive file][42] directly.
(To compile the [`bw_ktune.py`][43] pipeline file yourself, you’ll need to have the KFP SDK installed).

For the pipeline parameters, fill in the name of a bucket (under which the HP tuning bookkeeping will be written) as well as a `working_dir` path (under which the info for the model full training will be written).   These don’t need to be the same bucket, but of course both must be accessible to the pipelines installation.
You can adjust the other params if you like.

The `num_best_hps` and `num_best_hps_list` params specify the N top param sets to use for full training, and _must be consistent with each other_, with the latter the list of the N first indices.  (This redundancy is a bit hacky, but a loop in the pipeline spec makes use of this latter param). If you change these values, recall that the full training jobs are configured to each run on nodes with at least two GPUs, and so your node pool config must reflect this. You can edit this line in the pipeline spec: `train.set_gpu_limit(2)` and then recompile to change that constraint.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/keras_tuner/ktuner_pl_params.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/keras_tuner/ktuner_pl_params.png" width="50%"/></a>
<figcaption><br/><i>The 'keras tuner' pipeline parameters.</i></figcaption>
</figure>

The pipeline specification…\< add info on changing the number of executions per trial… need to recompile the pipeline.. to do this, install the KFP SDK\>

Once you launch this pipeline, it may run for quite a long time, depending upon how many trials you’re doing.  The first pipeline step (`ktune`) launches the Keras Tuner workers and chief as Kubernetes `jobs`, and so the pipeline step logs just show that the tuners have been deployed, then waits for them all to finish before proceeding.
You can track the pods via `kubectl`, e.g.:
```bash
kubectl get pods -A --watch=true -o wide
```
(or via the Cloud Console).  You can view the output for each of the tuner pods in their Stackdriver logs (or via `kubectl` until the node pool is scaled back down).

You may notice GPU preemptions in the pod listing while the tuners are running, since we set up that node pool to be preemptible. The pod status will look like this: `OutOfnvidia.com/gpu`; then you’ll see a replacement pod start up in its place, since we defined the tuner jobs to require 1 replica each.  The new pod will communicate with the HP search `oracle` to get its instructions, and continue running trials.

After the HP search has completed, the first (`ktune`) step will obtain the N best parameter sets, and start full training jobs using those parameters.
After a full training step has finished, the exported model will be deployed to the cluster for serving, using [TF-serving][44].  (For simplicity, we’re not including model eval in the workflow, but typically you’d want to do that as well.  For TF/Keras models, the [TFMA][45] library can be useful with such analyses.)

### 4. Use TensorBoard to view information on the training runs

The full training runs use the `tf.keras.callbacks.TensorBoard` _callback_, so you can view and compare training info in TensorBoard during or after training.
(more detail TBD).

### 5. Make predictions against your trained model

After the full models have been trained and deployed for serving, you can request predictions from the TF-serving services.  For this example, we’re not putting the services behind external IP addresses, so we’ll port-forward to connect to them.

Find the `TF-serving` service names by running this command:
```bash
kubectl -n kubeflow get services  -l apptype=tf-serving
```

By default, you should see two such services per pipeline run.  The service names will look something like `bikeswxxxxxxxxxx`.  Port-forward to a service as follows, **first editing to use your service name**:

```bash
kubectl -n kubeflow port-forward svc/bikeswxxxxxxxxxx 8500:8500
```

Then, send the `TF-serving` service a prediction request, formatted as follows:

```bash
curl -d '{"instances": [{"end_station_id": "333", "ts": 1435774380.0, "day_of_week": "4", "start_station_id": "160", "euclidean": 4295.88, "loc_cross": "POINT(-0.13 51.51)POINT(-0.19 51.51)", "prcp": 0.0, "max": 94.5, "min": 58.9, "temp": 81.8, "dewp": 59.5 }]}' \
  -X POST http://localhost:8500/v1/models/bikesw:predict
```

You should get a response that looks something like this, where the prediction value is the rental `duration`:

```json
{
    "predictions": [[1493.55908]
    ]
}
```

## A closer look at the code
(TBD).


## Cleanup

After you’re done running the example, you probably want to do some cleanup.
(If you set up the GPU node pools using autoscaling, they should scale down to zero on their own after a period of inactivity).

You can delete the ‘chief’ _job_ when you’re done with it via this command:
```bash
kubectl delete jobs -l app=ktuner-chief
```
Then delete the chief _service_ as well:
```bash
kubectl delete services -l app=ktuner-chief
```
You can delete the tuner jobs as follows (if the jobs have completed, this will tear down their pods; if the jobs are still running, this will terminate them):
```bash
kubectl delete jobs -l app=ktuner-tuner
```

To take down the TF-serving _deployments_ and _services_:
```bash
kubectl delete deployment -n kubeflow -l apptype=tf-serving
kubectl delete services -n kubeflow -l apptype=tf-serving
```

You can also take down your Cloud AI Platform Pipelines installation— optionally deleting its GKE cluster too— via the Pipelines panel in the Cloud Console.

## What’s next?

(TBD).

[1]:	https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning)
[2]:	xxx
[3]:	https://blog.tensorflow.org/2020/01/hyperparameter-tuning-with-keras-tuner.html
[4]:	https://cloud.google.com/ai-platform/pipelines/docs
[5]:	https://www.kubeflow.org/docs/pipelines/
[6]:	https://cloud.google.com/kubernetes-engine
[7]:	https://cloud.google.com/blog/products/ai-machine-learning/introducing-cloud-ai-platform-pipelines
[8]:	https://console.cloud.google.com/
[9]:	https://blog.tensorflow.org/2020/01/hyperparameter-tuning-with-keras-tuner.html
[10]:	https://keras-team.github.io/keras-tuner/tutorials/distributed-tuning/
[11]:	xxx
[12]:	xxx
[13]:	https://www.tensorflow.org/tfx/guide/serving
[14]:	https://cloud.google.com/bigquery/public-data/
[15]:	https://cloud.google.com/blog/products/ai-machine-learning/explaining-model-predictions-structured-data
[16]:	https://cloud.google.com/bigquery/
[17]:	https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=london_bicycles&page=dataset
[18]:	https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=noaa_gsod&page=dataset
[19]:	xxx
[20]:	https://keras-team.github.io/keras-tuner/
[21]:	https://keras-team.github.io/keras-tuner/tutorials/distributed-tuning/
[22]:	https://cloud.google.com/kubernetes-engine
[23]:	https://www.tensorflow.org/tfx/guide/serving
[24]:	https://cloud.google.com/kubernetes-engine/docs/how-to/preemptible-vms
[25]:	https://kubernetes.io/docs/concepts/workloads/controllers/job/
[26]:	xxx
[27]:	./example_pipelines/bw_ktune.py
[28]:	xxx
[29]:	./components
[30]:	xxx
[31]:	xxx
[32]:	https://en.wikipedia.org/wiki/Directed_acyclic_graph
[33]:	xxx
[34]:	https://console.cloud.google.com/kubernetes/list
[35]:	https://cloud.google.com/sdk/install
[36]:	https://cloud.google.com/shell
[37]:	xxx
[38]:	https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#request_quota
[39]:	https://cloud.google.com/blog/products/ai-machine-learning/reduce-the-costs-of-ml-workflows-with-preemptible-vms-and-gpus
[40]:	https://storage.googleapis.com/aju-dev-demos-codelabs/KF/compiled_pipelines/bw.py.tar.gz
[41]:	xxx
[42]:	./example_pipelines/bw_ktune.py.tar.gz
[43]:	./example_pipelines/bw_ktune.py
[44]:	https://www.tensorflow.org/tfx/guide/serving
[45]:	https://www.tensorflow.org/tfx/model_analysis/get_started

