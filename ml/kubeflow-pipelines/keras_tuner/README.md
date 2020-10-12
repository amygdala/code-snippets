# Kubeflow Pipelines Distributed Keras Tuner example

> **Note**: this example may take a long time to run, and **incur significant charges** in its use of GPUs, depending upon how its parameters are configured.

## Introduction

The performance of a machine learning model is often crucially dependent on the choice of good [hyperparameters][1]. For models of any complexity, relying on trial and error to find good values for these parameters does not scale. This tutorial shows how to use [Cloud AI Platform Pipelines][2]  in conjunction with [Keras Tuner][3] to build a hyperparameter-tuning workflow that uses distributed HP search.

[Cloud AI Platform Pipelines][4], currently in Beta, provides a way to deploy robust, repeatable machine learning pipelines along with monitoring, auditing, version tracking, and reproducibility, and gives you an easy-to-install, secure execution environment for your ML workflows. AI Platform Pipelines is based on [Kubeflow Pipelines][5] (KFP) installed on a [Google Kubernetes Engine (GKE)][6] cluster, and can run pipelines specified via both the KFP and TFX SDKs. See [this blog post][7] for more detail on the Pipelines tech stack.
You can create an AI Platform Pipelines installation with just a few clicks. After installing, you access AI Platform Pipelines by visiting the AI Platform Panel in the [Cloud Console][8].

[Keras Tuner][9] is an easy-to-use, distributable hyperparameter optimization framework. Keras Tuner makes it easy to define a search space and leverage included algorithms to find the best hyperparameter values. Keras Tuner comes with several search  algorithms built-in, and is also designed to be easy for researchers to extend in order to experiment with new search algorithms.  It is straightforward to run the tuner in [distributed search mode][10], which we’ll leverage for this example.

The intent of a HP tuning search is typically not to do full training for each parameter combination, but to find the best starting points.  The number of epochs run in the HP search trials are typically smaller than that used in the full training. So, an HP tuning-based workflow could include:

- perform a distributed HP tuning search, and obtain the results
- do concurrent model training runs for each of the best N parameter configurations, and export the model for each
- serve the results (often after model evaluation).

As mentioned above, a Cloud AI Platform (KFP) Pipeline runs under the hood on a GKE cluster.  This makes it straightforward to implement this workflow— including the distributed HP search and model serving— so that you just need to launch a pipeline job to kick it off.  This tutorial shows how to do that.  It also shows how to use **preemptible** GPU-enabled VMS for the HP search, to reduce costs; and how to use [TF-serving][11] to deploy the trained model(s) on the same cluster for serving.
As part of the process, we’ll see how GKE provides a scalable, resilient platform with easily-configured use of accelerators.

## About the dataset and modeling task

### The dataset

The [Cloud Public Datasets Program][12] makes available public datasets that are useful for experimenting with machine learning. Just as we did in our “[Explaining model predictions on structured data][13]” post, we’ll use data that is essentially a join of two public datasets stored in [BigQuery][14]: [London Bike rentals][15] and [NOAA weather data][16], with some additional processing to clean up outliers and derive additional GIS and day-of-week fields.

### The modeling task and Keras model

We’ll use this dataset to build a [Keras][17] _regression model_ to predict the **duration** of a bike rental based on information about the start and end stations, the day of the week, the weather on that day, and other data. If we were running a bike rental company, for example, these predictions—and their explanations—could help us anticipate demand and even plan how to stock each location.

We’ll then use the Keras Tuner package to do an HP search using this model.

## Keras tuner in distributed mode on GKE with preemptible VMs

With the Keras Tuner, you set up a HP tuning search along these lines (the code is from this example; other search algorithms are supported in addition to 'random'):

```python
tuner = RandomSearch(
    create_model,
    objective='val_mae',
    max_trials=args.max_trials,
    distribution_strategy=STRATEGY,
    executions_per_trial=args.executions_per_trial,
    directory=args.tuner_dir,
    project_name=args.tuner_proj
)
```

...where in the above, the `create_model` call takes takes an argument `hp` from which you can sample hyperparameters.  For this example, we're varying number of hidden layers, number of nodes per hidden layer, and learning rate in the HP search. There are many other hyperparameters that you might also want to vary in your search.
```python
def create_model(hp):
  inputs, sparse, real = bwmodel.get_layers()
  ...
  model = bwmodel.wide_and_deep_classifier(
      inputs,
      linear_feature_columns=sparse.values(),
      dnn_feature_columns=real.values(),
      num_hidden_layers=hp.Int('num_hidden_layers', 2, 5),
      dnn_hidden_units1=hp.Int('hidden_size', 32, 256, step=32),
      learning_rate=hp.Choice('learning_rate',
                    values=[1e-1, 1e-2, 1e-3, 1e-4])
    )
```

Then, call `tuner.search(...)`.  See the Keras Tuner docs for more.


The [Keras Tuner][18] supports running a hyperparameter search in [distributed mode][19].
[Google Kubernetes Engine (GKE)][20] makes it straightforward to configure and run a distributed HP tuning search.  GKE is  a good fit not only because it lets you easily distribute the HP tuning workload, but because you can leverage autoscaling to boost node pools for a large job, then scale down when the resources are no longer needed.  It’s also easy to deploy trained models for serving onto the same GKE cluster, using [TF-serving][21].  In addition, the Keras Tuner works well with [preemptible VMs][22], making it even cheaper to run your workloads.

With the Keras Tuner’s distributed config, you specify one node as the ‘chief’, which coordinates the search, and ‘tuner’ nodes that do the actual work of running model training jobs using a given param set (the _trials_).  When you set up an HP search, you indicate the max number of trials to run, and how many ‘executions’ to run per trial. The Kubeflow pipeline allows dynamic specification of the number of tuners to use for a given HP search— this determines how many trials you can run concurrently— as well as the max number of trials and number of executions.

We’ll define the tuner components as Kubernetes [_jobs_][23], each specified to have  1 _replica_.   This means that if a tuner job pod is terminated for some reason prior to job completion, Kubernetes will start up another replica.
Thus, the Keras Tuner’s HP search is a good fit for use of [preemptible VMs][24].  Because the HP search bookkeeping— orchestrated by the tuner ‘chief’, via an ‘oracle’ file— tracks the state of the trials,  the configuration is robust to a tuner pod terminating unexpectedly— say, due to a preemption— and a new one being restarted.  The new job pod will get its instructions from the ‘oracle’ and continue running _trials_.
The example uses GCS for the tuners’ shared file system.

Once the HP search has finished, any of the tuners can obtain information on the N best parameter sets (as well as export the best model(s)).

## Defining the HP Tuning + training workflow as a pipeline

The definition of the pipeline itself is [here][25], specified using the KFP SDK.  It’s then compiled to an archive file and uploaded to AI Platforms Pipelines. (To compile it yourself, you’ll need to have the [KFP SDK installed][26]).  Pipeline steps are container-based, and you can find the Dockerfiles and underlying code for the steps under the [`components`][27] directory.

The example pipeline first runs a distributed HP tuning search using a specified number of tuner workers,  then obtains the best `N` parameter combinations—by default, two.  The pipeline step itself does not do the heavy lifting, but rather launches all the tuner [*jobs*][28] on GKE, which run concurrently, and monitors for their completion. (Unsurprisingly, this stage of the pipeline may run for quite a long time, depending upon how many HP search trials were specified and how many tuners you’re using).

Concurrently to the Keras Tuner runs, the pipeline sets up a [TensorBoard visualization component](https://github.com/kubeflow/pipelines/blob/master/components/tensorflow/tensorboard/prepare_tensorboard/component.yaml), its log directory set to the GCS path under which we’ll run the full training jobs.  The output of this step—the log dir info— is consumed by the training step.

The pipeline then runs full training jobs, concurrently, for each of the `N` best parameter sets (by default, 2).  It does this via the KFP [loop][29] construct, allowing the pipeline to support dynamic specification of `N`.
We’ll be able to compare the training jobs to each other using TensorBoard, both while they’re running and after they’ve completed.

Then, the trained models are deployed for serving for serving on the GKE cluster, using [TF-serving][30].  Each deployed model has its own cluster service endpoint.
(While not shown in this example, one could insert a step for model evaluation before deploying to TF-serving.)

For example, here is the [DAG][31] for a pipeline execution that did training and then deployed prediction services for the two best parameter configurations.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-pls/pl_dag.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-pls/pl_dag.png" width="60%"/></a>
<figcaption><br/><i>The DAG for keras tuner pipeline execution.  Here the two best parameter configurations were used for full training.</i></figcaption>
</figure>

## Running the example pipeline

> **Note**: this example may take a long time to run, and **incur significant charges** in its use of GPUs, depending upon how its parameters are configured.

### 1. Create a Cloud AI Platform Pipelines installation

To run the example, first create a Cloud AI Platform Pipelines installation, as described in the Pipelines [documentation][32].  **Be sure to tick the box that sets up the GKE cluster with full access to GCP APIs**.  It’s necessary to additionally configure the installation’s underlying GKE cluster as described below, before running the pipeline.

### 2. Do some cluster config and create GPU node pools

Once the Pipelines installation has finished, grab the credentials for the underlying GKE cluster as follows:

```bash
gcloud container clusters get-credentials <cluster-name> --zone <cluster-zone> --project <your-project>
```

Note that you can reconstruct this command via the “Connect” button in the GKE cluster listing [in the Cloud Console][33].  If you don’t have `gcloud` [installed][34] locally, you can run the commands in this section via the [Cloud Shell][35].

Next, give the `pipeline-runner` service account permissions to launch new Kubernetes resources:

```bash
kubectl create clusterrolebinding sa-admin --clusterrole=cluster-admin --serviceaccount=kubeflow:pipeline-runner
```

Then,  apply a Nvidia `daemonset`, that will install Nvidia drivers on any GPU-enabled cluster nodes.

```bash
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

Next, create GPU node pools. Just for the purposes of this example, we’ll create two: one a pool of preemptible nodes with one GPU each (the lighter-weight Keras tuner jobs can select this pool), and another of nodes with two GPUs each, which we’ll use for full training.  (The pipeline is defined so that the full training steps are placed on nodes with at least 2 GPUs, though you can change this value and recompile the pipeline if you like.)

We’ll configure both node pools to use autoscaling and to scale down to zero when not in use. This means that when you run the example, you may see pauses while a node pool scales up.

> Note: Before you run these commands, you may need to [**increase the GPU quota**][36] for your project.

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

> Note: There is no reason we couldn’t make all our GPU-enabled node pools preemptible, and run the full training steps on preemptible nodes as well.  While for simplicity we’re not doing that as part of this example, see [this blog post][37] for information on how to define a KFP pipeline that supports step retries on interruption.

### 3. Launch a Keras Tuner pipeline job

Upload the compiled ‘Keras Tuner’ pipeline to the Kubeflow Pipelines dashboard.  You can use this URL: [`https://storage.googleapis.com/aju-dev-demos-codelabs/KF/compiled_pipelines/bw_ktune.py.tar.gz`][38], or if you’ve checked out or downloaded the [repo][39], you can upload the [compiled archive file][40] directly. (To compile the [`bw_ktune.py`][41] pipeline file yourself, you’ll need to have the [KFP SDK installed][42]).

For the pipeline parameters, fill in the name of a bucket (under which the HP tuning bookkeeping will be written) as well as a `working_dir` path (under which the info for the model full training will be written).   These don’t need to be the same bucket, but of course both must be accessible to the pipelines installation.
You can adjust the other params if you like.  E.g., you may want to lower the `max_trials` number.

The `num_best_hps` and `num_best_hps_list` params specify the N top param sets to use for full training, and _must be consistent with each other_, with the latter the list of the N first indices.  (This redundancy is a bit hacky, but a loop in the pipeline spec makes use of this latter param). If you change these values, recall that the full training jobs are configured to each run on nodes with at least two GPUs, and so your node pool config must reflect this. You can edit this line in the pipeline spec: `train.set_gpu_limit(2)` and then recompile to change that constraint.

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/keras_tuner/ktuner_pl_params.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/keras_tuner/ktuner_pl_params.png" width="50%"/></a>
<figcaption><br/><i>The 'keras tuner' pipeline parameters.</i></figcaption>
</figure>

> Note: The pipeline specification hardwires the number of executions per trial to 2 (the `--executions-per-trial` arg)— to change that, edit the pipeline definition and recompile it.

Once you launch this pipeline, it may run for quite a long time, depending upon how many trials you’re doing.  The first pipeline step (`ktune`) launches the Keras Tuner workers and chief as Kubernetes `jobs`, and so the pipeline step logs just show that the tuners have been deployed, then waits for them all to finish before proceeding.
You can track the pods via `kubectl`, e.g.:
```bash
kubectl get pods -A --watch=true -o wide
```
(or via the Cloud Console).  You can view the output for each of the tuner pods in their Stackdriver logs (or via `kubectl` until the node pool is scaled back down).

You may notice GPU preemptions in the pod listing while the tuners are running, since we set up that node pool to be preemptible. The pod status will look like this: `OutOfnvidia.com/gpu`; then you’ll see a replacement pod start up in its place, since we defined the tuner jobs to require 1 replica each.  The new pod will communicate with the HP search `oracle` to get its instructions, and continue running trials.

After the HP search has completed, the first (`ktune`) step will obtain the N best parameter sets, and start full training jobs using those parameters.
After a full training step has finished, the exported model will be deployed to the cluster for serving, using [TF-serving][43].  (For simplicity, we’re not including model eval in the workflow, but typically you’d want to do that as well.  For TF/Keras models, the [TFMA][44] library can be useful with such analyses.)

### 4. Use TensorBoard to view information on the training runs

The full training runs use the `tf.keras.callbacks.TensorBoard` _callback_, so you can view and compare training info in TensorBoard during or after training.

To do this, we’re using a [prebuilt KFP component][45] for TensorBoard visualization. In the [pipeline specification][46], we run this step before we launch the full training job(s), pointing the TB log dir to the parent directory of the training runs.  By including this component, we can view the logs _during_ training.  (The training component also generates metadata to create a TB visualization—pointing to the same directory— but this viz will not be available until the training step completes.  Because it points to the same directory, the visualization generated by the training step is redundant to the TB viz pipeline step in this pipeline).

<figure>
<a href="https://storage.googleapis.com/amy-jo/images/kf-pls/tb_viz.png" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/kf-pls/tb_viz.png" width="40%"/></a>
<figcaption><br/><i>Start up TensorBoard from the pipeline's <b>Run Output</b> panel.</i></figcaption>
</figure>


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

You can find the KFP component code in the ￼[`components`][47]￼ subdirectory, and the component Dockerfile definitions are under the ￼[`components/kubeflow-resources/containers`][48]￼ subdirectory.

In the [`bikesw_training`][49] directory, [`deploy_tuner.py`][50] implements the KFP component that launches the tuner ‘workers’ and ‘chief’ [`jobs`][51], using the `yaml` templates in the same directory.
[`bw_hptune_standalone.py`][52] is executed in the tuner pod containers.  This is where the tuner search is set up and run.  For this example, we’re using the Keras Tuner’s `RandomSearch` , but other options are supported as well.   Then, the best `N` results are written to a given GCS path, and this info is used to kick off the full training runs.

The [`bikes_weather_limited.py`][53] is used for full training with the given HP tuning parameters. The [`bwmodel`][54] module contains core model code used by both.

> Note: With Keras Tuner, you can do both data-parallel and trial-parallel distribution. That is, you can use tf.distribute.Strategy to run each Model on multiple GPUs, and you can also search over multiple different hyperparameter combinations in parallel on different workers.  The template yamls specify just one GPU, but it would be easy to modify the code to support the former.

The TF-Serving component is in the [`tf-serving`][55] directory, which contains both the code that launches the TF-serving service, and the `yaml` template used to do so.

## Cleanup

After you’re done running the example, you probably want to do some cleanup.
(If you set up the GPU node pools using autoscaling, they should scale down to zero on their own after a period of inactivity).

You can delete the ‘chief’ _job_ when you’re done with it via this command:
```bash
kubectl delete jobs -l apptype=ktuner-chief
```
Then delete the chief _service_ as well:
```bash
kubectl delete services -l apptype=ktuner-chief
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


[1]:	https://en.wikipedia.org/wiki/Hyperparameter_(machine_learning)
[2]:	https://cloud.google.com/blog/products/ai-machine-learning/introducing-cloud-ai-platform-pipelines
[3]:	https://blog.tensorflow.org/2020/01/hyperparameter-tuning-with-keras-tuner.html
[4]:	https://cloud.google.com/ai-platform/pipelines/docs
[5]:	https://www.kubeflow.org/docs/pipelines/
[6]:	https://cloud.google.com/kubernetes-engine
[7]:	https://cloud.google.com/blog/products/ai-machine-learning/introducing-cloud-ai-platform-pipelines
[8]:	https://console.cloud.google.com/
[9]:	https://blog.tensorflow.org/2020/01/hyperparameter-tuning-with-keras-tuner.html
[10]:	https://keras-team.github.io/keras-tuner/tutorials/distributed-tuning/
[11]:	https://www.tensorflow.org/tfx/guide/serving
[12]:	https://cloud.google.com/bigquery/public-data/
[13]:	https://cloud.google.com/blog/products/ai-machine-learning/explaining-model-predictions-structured-data
[14]:	https://cloud.google.com/bigquery/
[15]:	https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=london_bicycles&page=dataset
[16]:	https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=noaa_gsod&page=dataset
[17]:	https://keras.io/
[18]:	https://keras-team.github.io/keras-tuner/
[19]:	https://keras-team.github.io/keras-tuner/tutorials/distributed-tuning/
[20]:	https://cloud.google.com/kubernetes-engine
[21]:	https://www.tensorflow.org/tfx/guide/serving
[22]:	https://cloud.google.com/kubernetes-engine/docs/how-to/preemptible-vms
[23]:	https://kubernetes.io/docs/concepts/workloads/controllers/job/
[24]:	https://cloud.google.com/preemptible-vms
[25]:	./example_pipelines/bw_ktune.py
[26]:	https://www.kubeflow.org/docs/pipelines/sdk/install-sdk/#install-the-kubeflow-pipelines-sdk
[27]:	./components
[28]:	https://cloud.google.com/kubernetes-engine/docs/how-to/jobs
[29]:	https://github.com/kubeflow/pipelines/tree/master/samples/core/loop_parameter
[30]:	https://www.tensorflow.org/tfx/guide/serving
[31]:	https://en.wikipedia.org/wiki/Directed_acyclic_graph
[32]:	https://cloud.google.com/ai-platform/pipelines/docs
[33]:	https://console.cloud.google.com/kubernetes/list
[34]:	https://cloud.google.com/sdk/install
[35]:	https://cloud.google.com/shell
[36]:	https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#request_quota
[37]:	https://cloud.google.com/blog/products/ai-machine-learning/reduce-the-costs-of-ml-workflows-with-preemptible-vms-and-gpus
[38]:	https://storage.googleapis.com/aju-dev-demos-codelabs/KF/compiled_pipelines/bw_ktune.py.tar.gz
[39]:	https://github.com/amygdala/code-snippets
[40]:	./example_pipelines/bw_ktune.py.tar.gz
[41]:	./example_pipelines/bw_ktune.py
[42]:	https://www.kubeflow.org/docs/pipelines/sdk/install-sdk/#install-the-kubeflow-pipelines-sdk
[43]:	https://www.tensorflow.org/tfx/guide/serving
[44]:	https://www.tensorflow.org/tfx/model_analysis/get_started
[45]:	https://github.com/kubeflow/pipelines/blob/master/components/tensorflow/tensorboard/prepare_tensorboard/component.yaml
[46]:	./example_pipelines/bw_ktune.py
[47]:	./components
[48]:	./components/kubeflow-resources/containers
[49]:	./components/kubeflow-resources/bikesw_training
[50]:	./components/kubeflow-resources/bikesw_training/deploy_tuner.py
[51]:	https://kubernetes.io/docs/concepts/workloads/controllers/job/
[52]:	./components/kubeflow-resources/bikesw_training/bw_hptune_standalone.py
[53]:	./components/kubeflow-resources/bikesw_training/bikes_weather_limited.py
[54]:	./components/kubeflow-resources/bikesw_training/bwmodel
[55]:	./components/kubeflow-resources/tf-serving

