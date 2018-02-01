
# Easy distributed training with TensorFlow using `tf.estimator.train_and_evaluate` and Cloud ML Engine

## Introduction

TensorFlow release 1.4 introduced the function [**`tf.estimator.train_and_evaluate`**](https://www.tensorflow.org/api_docs/python/tf/estimator/train_and_evaluate), which simplifies training, evaluation, and exporting of [`Estimator`](https://www.tensorflow.org/get_started/estimator) models. It abstracts away the details of [distributed execution](https://www.google.com/url?q=https://www.tensorflow.org/deploy/distributed) for training and evaluation, while also supporting local execution, and provides consistent behavior across both local/non-distributed and distributed configurations.

This means that with **`tf.estimator.train_and_evaluate`**, you can run the same code on both locally and distributed in the cloud, on different devices and using different cluster configurations, and get consistent results, **without making any code changes**. When you're done training (or at intermediate stages), the trained model is automatically exported in a [form suitable for serving](https://www.tensorflow.org/programmers_guide/saved_model) (e.g. for [Cloud ML Engine online prediction](https://cloud.google.com/ml-engine/docs/prediction-overview) or [TensorFlow serving](https://www.tensorflow.org/serving/)).

In this example, we'll walk through how to use `tf.estimator.train_and_evaluate` with an `Estimator` model, and then show how easy it is to do **distributed training of the model on [Cloud ML Engine](https://cloud.google.com/ml-engine)**, moving between different cluster configurations with just a config tweak.
(The TensorFlow code itself supports distribution on any infrastructure (GCE, GKE, etc.) when properly configured, but we will focus on Cloud ML Engine, which makes the experience seamless).

The primary steps necessary to do this are:

- build your `Estimator` model;
- define how data is fed into the model for both training and test datasets (often these definitions are essentially the same); and
- define training and eval specifications ([`TrainSpec`](https://www.tensorflow.org/api_docs/python/tf/estimator/TrainSpec) and [`EvalSpec`](https://www.tensorflow.org/api_docs/python/tf/estimator/EvalSpec)) to be passed to `tf.estimator.train_and_evaluate`.  The `EvalSpec` can include information on how to export your trained model for prediction (serving), and we'll look at how to do that as well.

Then we'll look at how to **use your trained model to make predictions**.

The example also includes the use of [**Datasets**](https://www.tensorflow.org/api_docs/python/tf/data/Dataset) to manage our input data. This API is part of TensorFlow 1.4, and is an [easier and more performant way](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/docs_src/performance/datasets_performance.md) to create input pipelines to TensorFlow models; this is particularly important with large datasets and when using accelerators.
 (See [this article](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/docs_src/performance/datasets_performance.md) for more on why input pipelining is so important, particularly when using accelerators).

For our example, we'll use the The [Census Income Data
Set](https://archive.ics.uci.edu/ml/datasets/Census+Income) hosted by the [UC Irvine Machine Learning
Repository](https://archive.ics.uci.edu/ml/datasets/). We have hosted the data
on [Google Cloud Storage](https://cloud.google.com/storage/) (GCS) in a slightly cleaned form. We'll use this dataset to predict income category based on various information about a person.

This README omits some of the details of the example.
To see the specifics and work through the code yourself, visit the [Jupyter](http://jupyter.org/) notebook [in this directory](using_tf.estimator.train_and_evaluate.ipynb).
(The example in the [notebook](using_tf.estimator.train_and_evaluate.ipynb) is a slightly modified version of [this other example](https://github.com/GoogleCloudPlatform/cloudml-samples/tree/master/census/estimator/trainer)).


## Step 1: Create an Estimator

The TensorFlow [Estimator](https://www.tensorflow.org/api_docs/python/tf/estimator/Estimator) class wraps a model, and provides built-in support for distributed training and evaluation. You should nearly always use Estimators to create your TensorFlow models. ‘Pre-made’ Estimator subclasses are an effective way to quickly create standard models, and you can build a [Custom Estimator](https://www.tensorflow.org/extend/estimators) if none of the pre-made Estimators suit your purpose.

For this example, we’ll create an [Estimator](https://www.tensorflow.org/get_started/estimator) object using a pre-made subclass, [`DNNLinearCombinedClassifier`](https://www.tensorflow.org/api_docs/python/tf/estimator/DNNLinearCombinedClassifier), which implements a ["wide and deep"](https://research.googleblog.com/2016/06/wide-deep-learning-better-together-with.html) model. Wide and deep models use a deep neural net (DNN) to learn high level abstractions about complex features or interactions between such features. These models then combine the outputs from the DNN with a [linear regression](https://en.wikipedia.org/wiki/Linear_regression) performed on simpler features. This provides a balance between power and speed that is effective on many structured data problems.

See the accompanying [notebook](https://nbviewer.jupyter.org/github/amygdala/code-snippets/blob/master/ml/census_train_and_eval/using_tf.estimator.train_and_evaluate.ipynb#First-step:-create-an-Estimator) for the details of defining our Estimator, including specification of the expected format of the input data.
The data is in csv format, and looks like this:

```
39, State-gov, 77516, Bachelors, 13, Never-married, Adm-clerical, Not-in-family, White, Male, 2174, 0, 40, United-States, <=50K
50, Self-emp-not-inc, 83311, Bachelors, 13, Married-civ-spouse, Exec-managerial, Husband, White, Male, 0, 0, 13, United-States, <=50K
38, Private, 215646, HS-grad, 9, Divorced, Handlers-cleaners, Not-in-family, White, Male, 0, 0, 40, United-States, <=50K
...
```

We'll use the last field, which indicates income bracket, as our label, meaning that this is the value we'll predict based on the values of the other fields.

In the [notebook](using_tf.estimator.train_and_evaluate.ipynb), we define a `build_estimator` function, which takes as input config info, and returns a `tf.estimator.DNNLinearCombinedClassifier` object.
We'll call it like this:

```python
run_config = tf.estimator.RunConfig()
run_config = run_config.replace(model_dir=output_dir)

FIRST_LAYER_SIZE = 100  # Number of nodes in the first layer of the DNN
NUM_LAYERS = 4  # Number of layers in the DNN
SCALE_FACTOR = 0.7  # How quickly should the size of the layers in the DNN decay
EMBEDDING_SIZE = 8  # Number of embedding dimensions for categorical columns

estimator = build_estimator(
    embedding_size=EMBEDDING_SIZE,
    # Construct layers sizes with exponential decay
    hidden_units=[
        max(2, int(FIRST_LAYER_SIZE *
                   SCALE_FACTOR**i))
        for i in range(NUM_LAYERS)
    ],
    config=run_config
)
```


## Step 2: Define input functions using Datasets

Now that we have defined our model structure, the next step is to use it for training and evaluation.
As with any `Estimator`, we'll need to tell the `DNNLinearCombinedClassifier` object how to get its training and eval data. We'll define a function (`input_fn`) that knows how to generate features and labels for training or evaluation, then use that definition to create the actual train and eval input functions.

We'll use [Datasets](https://www.tensorflow.org/api_docs/python/tf/data/Dataset) to access our data.
This API is a new way to create [input pipelines to TensorFlow models](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/docs_src/performance/datasets_performance.md).
The `Dataset` API is much more performant than using `feed_dict` or the queue-based pipelines, and it's [cleaner and easier](https://developers.googleblog.com/2017/09/introducing-tensorflow-datasets.html) to use.

In this simple example, our datasets are too small for the use of the Dataset API to make a large difference, but with larger datasets it becomes much more important.

The `input_fn` definition is below. It uses a couple of helper functions that are defined in the accompanying [notebook](https://nbviewer.jupyter.org/github/amygdala/code-snippets/blob/master/ml/census_train_and_eval/using_tf.estimator.train_and_evaluate.ipynb#Define-input-functions-(using-Datasets)). One of these,
`parse_label_column`, is used to convert the label strings (in our case, ' <=50K' and ' >50K') into [one-hot](https://www.kaggle.com/dansbecker/using-categorical-data-with-one-hot-encoding) encodings, which map categorical features into a format that works better with most ML classification models.


```python
# This function returns a (features, indices) tuple, where features is a dictionary of
# Tensors, and indices is a single Tensor of label indices.
def input_fn(filenames,
                      num_epochs=None,
                      shuffle=True,
                      skip_header_lines=0,
                      batch_size=200):

  dataset = tf.data.TextLineDataset(filenames).skip(skip_header_lines).map(parse_csv)

  if shuffle:
    dataset = dataset.shuffle(buffer_size=batch_size * 10)
  dataset = dataset.repeat(num_epochs)
  dataset = dataset.batch(batch_size)
  iterator = dataset.make_one_shot_iterator()
  features = iterator.get_next()
  return features, parse_label_column(features.pop(LABEL_COLUMN))
```

Then, we'll use `input_fn` to define both the `train_input` and `eval_input` functions.  We just need to pass `input_fn` the different source files to use for training versus evaluation.
As we'll see below, these two functions will be used to define a `TrainSpec` and `EvalSpec` used by `train_and_evaluate`.


```python
train_input = lambda: input_fn(
    TRAIN_FILES,
    batch_size=40
)

# Don't shuffle evaluation data
eval_input = lambda: input_fn(
    EVAL_FILES,
    batch_size=40,
    shuffle=False
)
```

## Step 3: Define training and eval specs

Now we're nearly set.  We just need to define the the `TrainSpec` and `EvalSpec` used by `tf.estimator.train_and_evaluate`. These specify not only the input functions, but how to export our trained model; that is, how to save it in the standard [SavedModel](https://www.tensorflow.org/programmers_guide/saved_model) format, so that we can later use it for serving.

First, we'll define the [`TrainSpec`](https://www.tensorflow.org/api_docs/python/tf/estimator/TrainSpec), which takes as an arg `train_input`:


```python
train_spec = tf.estimator.TrainSpec(train_input,
                                  max_steps=1000
                                  )
```

For our [`EvalSpec`](https://www.tensorflow.org/api_docs/python/tf/estimator/EvalSpec), we’ll instantiate it with something additional – a list of _exporters_, that specify how to export (save) the trained model so that it can be used for serving with respect to a particular data input format. Here we’ll just define one such exporter.

To specify our exporter, we must first define a
[*serving input function*](https://www.tensorflow.org/programmers_guide/saved_model#preparing_serving_inputs).
This is what determines the input format that the exporter will accept.
As we saw above, during training, an `input_fn()` ingests data and prepares it for use by the model.
At serving time, similarly, a `serving_input_receiver_fn()` accepts inference requests and prepares them for the model. This function has the following purposes:

- To add placeholders to the model graph that the serving system will feed with inference requests.
- To add any additional ops needed to convert data from the input format into the feature Tensors expected by the model.

The serving input function should return a [`tf.estimator.export.ServingInputReceiver`](https://www.tensorflow.org/api_docs/python/tf/estimator/export/ServingInputReceiver) object, which packages the placeholders and the resulting feature `Tensors` together.

A `ServingInputReceiver` is instantiated with two arguments — `features` and `receiver_tensors`. The `features` represent the inputs to our Estimator when it is being served for prediction. The `receiver_tensor` represents inputs to the server.

These two arguments will not necessarily always be the same — in some cases we may want to perform some transformation(s) before feeding the data to the model. [Here's](https://github.com/GoogleCloudPlatform/cloudml-samples/blob/master/census/estimator/trainer/model.py#L197) one example of that, where the inputs to the server (csv-formatted rows) include a field to be removed.

However, in our case, the inputs to the server are the same as the features input to the model. Here's what our serving input function looks like:


```python
def json_serving_input_fn():
  """Build the serving inputs."""
  inputs = {}
  for feat in INPUT_COLUMNS:
    inputs[feat.name] = tf.placeholder(shape=[None], dtype=feat.dtype)

  return tf.estimator.export.ServingInputReceiver(inputs, inputs)
```

Then, we define an [Exporter](https://www.tensorflow.org/api_docs/python/tf/estimator/Exporter) in terms of that serving input function. It will export the model in SavedModel format. We pass the `EvalSpec` constructor a list of exporters (here, just one).

Here, we're using
the [`FinalExporter`](https://www.tensorflow.org/api_docs/python/tf/estimator/FinalExporter) class.  This class performs a single export at the end of training. This is in contrast to
[`LatestExporter`](https://www.tensorflow.org/api_docs/python/tf/estimator/LatestExporter), which does regular exports and retains the last `N`. (We're just using one exporter here, but if you define multiple exporters, training will result in multiple saved models).


```python
exporter = tf.estimator.FinalExporter('census',
      json_serving_input_fn)
eval_spec = tf.estimator.EvalSpec(eval_input,
                                steps=100,
                                exporters=[exporter],
                                name='census-eval'
                                )
```

## Step 4: Train your model using `train_and_evaluate`


Now we have defined everything we need to train and evaluate our model, and to export the trained model for serving, via a call to **`train_and_evaluate`**:


```python
tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
```

This call will train the model and export the result in a format that is easy to use for prediction!

With `train_and_evaluate`, the training behavior will be consistent whether you run this function in a local/non-distributed context or in a distributed configuration.

The exported trained model can be served on many platforms. You may particularly want to consider ways to scalably serve your model, in order to handle many prediction requests at once— say if you're using your model in an app you're building, and you expect it to become popular. [Cloud ML Engine online prediction](https://cloud.google.com/ml-engine/docs/prediction-overview) and [TensorFlow serving](https://www.tensorflow.org/serving/)) are two options for doing this.

In this example, we'll look at using **Cloud ML Engine Online Prediction**. But first, let's take a closer look at our exported model.

### Examine the signature of the exported model.

TensorFlow ships with a CLI that allows you to inspect the *signature* of exported binary files. This can be useful as a sanity check.
It's run as follows, by passing it the path to directory containing the [saved model](https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/saved_model/README.md), which will be called `saved_model.pb`.
For our model, it will be found under `$output_dir/export/census`.  This is because we passed the `census` name to our `FinalExporter` above.  (`$output_dir` was specified when we constructed our Estimator).

```sh
saved_model_cli show --dir $output_dir/export/census/<timestamp> --tag serve --signature_def predict
```

The `saved_model_cli` command shows us this info (abbreviated for conciseness):

```
The given SavedModel SignatureDef contains the following input(s):
inputs['age'] tensor_info:
    dtype: DT_FLOAT
    shape: (-1)
    name: Placeholder_8:0
inputs['capital_gain'] tensor_info:
    dtype: DT_FLOAT
    shape: (-1)
    name: Placeholder_10:0
inputs['capital_loss'] tensor_info:
    dtype: DT_FLOAT
    shape: (-1)
    name: Placeholder_11:0
inputs['education'] tensor_info:
    dtype: DT_STRING
    shape: (-1)
    name: Placeholder_2:0
<... more input fields here ...>
The given SavedModel SignatureDef contains the following output(s):
outputs['class_ids'] tensor_info:
    dtype: DT_INT64
    shape: (-1, 1)
    name: head/predictions/classes:0
outputs['classes'] tensor_info:
    dtype: DT_STRING
    shape: (-1, 1)
    name: head/predictions/str_classes:0
outputs['logistic'] tensor_info:
    dtype: DT_FLOAT
    shape: (-1, 1)
    name: head/predictions/logistic:0
outputs['logits'] tensor_info:
    dtype: DT_FLOAT
    shape: (-1, 1)
    name: head/predictions/logits:0
outputs['probabilities'] tensor_info:
    dtype: DT_FLOAT
    shape: (-1, 2)
    name: head/predictions/probabilities:0
Method name is: tensorflow/serving/predict
```
Based on our knowledge of `DNNLinearCombinedClassifier`, and the input fields we defined, this looks as we expect. (Notice that the model generates multiple outputs).

### Check local prediction with gcloud

Another useful sanity check is running local prediction with your trained model. We'll use the [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/downloads) command-line tool for that.

We'll use the example input in [`test.json`](test.json) to predict a person's income bracket based on the features encoded in the `test.json` instance. Again, we point to the directory containing the saved model.


```sh
gcloud ml-engine local predict --model-dir $output_dir/export/census/<timestamp> --json-instances test.json
```

```
CLASS_IDS  CLASSES  LOGISTIC               LOGITS                 PROBABILITIES
[0]        [u'0']   [0.06585630029439926]  [-2.6521551609039307]  [0.9341437220573425, 0.06585630774497986]
```

You can see how the input fields in `test.json` correspond to the inputs listed by the `saved_model_cli` command above, and how the prediction outputs correspond to the outputs listed by `saved_model_cli`.
In this model, Class 0 indicates income <= 50k and Class 1 indicates income >50k.

## Using Cloud ML Engine for easy distributed training and scalable online prediction

In the previous section, we looked at how to use `tf.estimator.train_and_evaluate` first to train and export a model, and then to make predictions using the trained model.

In this section, you'll see how easy it is to use the same code — without any changes — to do **distributed training on [Cloud ML Engine](https://cloud.google.com/ml-engine/)**, thanks to the **`Estimator`** class and **`train_and_evaluate`**.  Then we'll use [**Cloud ML Engine Online Prediction**](https://cloud.google.com/ml-engine/docs/online-predict) to scalably serve the trained model.

One advantage of Cloud ML Engine is that there’s no lock-in. You could potentially train your TensorFlow model elsewhere, then deploy to Cloud ML Engine for serving (prediction); or alternately use Cloud ML Engine for distributed training and then serve elsewhere (e.g. with [TensorFlow serving](https://github.com/tensorflow/serving)).  Here, we’ll show how to use Cloud ML Engine for both stages.

To launch a training job on Cloud ML Engine, we can again use `gcloud`.  We'll need to package our code so that it can be deployed, and specify the Python file to run to start the training (`--module-name`).

The `trainer` module code is [here](trainer).
`trainer.task` is the entry point, and when that file is run, it calls `tf.estimator.train_and_evaluate`.
(You can read more about how to package your code [here](https://cloud.google.com/ml-engine/docs/packaging-trainer)).

If we want to, we could test (distributed) training via `gcloud` locally first, to make sure that we have everything packaged up correctly. See the accompanying [notebook](using_tf.estimator.train_and_evaluate.ipynb) for details.

But here, we'll jump right in to using Cloud ML Engine to do cloud-based distributed training.

We'll set the training job to use the `SCALE_TIER_STANDARD_1` scale spec.  This [gives us](https://cloud.google.com/ml-engine/docs/training-overview#job_configuration_parameters) one 'master' instance, plus four _workers_ and three _parameter servers_.


```sh
gcloud ml-engine jobs submit training $JOB_NAME --scale-tier `SCALE_TIER_STANDARD_1` \
    --runtime-version 1.4 --job-dir $GCS_JOB_DIR \
    --module-name trainer.task --package-path trainer/ \
    --region us-central1 \
    -- --train-steps 5000 --train-files $GCS_TRAIN_FILE --eval-files $GCS_EVAL_FILE --eval-steps 100
```

The cool thing about this is that **we don't need to change our code at all to use this distributed config**.  Our use of the Estimator class in conjunction with the Cloud ML Engine scale specification makes the distributed training config transparent to us — it just works.
Further, we could swap in any of the other predefined scale tiers (say `BASIC_GPU`), or define our own custom cluster, again without any code changes.
For example, we could alternatively configure our job to [use a GPU cluster](https://cloud.google.com/ml-engine/docs/using-gpus).

Once our training job is running, we can stream its logs to the terminal, and/or monitor it in the [Cloud Console](https://console.cloud.google.com/mlengine/jobs).


<a href="https://amy-jo.storage.googleapis.com/images/census_train_eval/ml_jobs.png" target="_blank"><img src="https://amy-jo.storage.googleapis.com/images/census_train_eval/ml_jobs.png" width="500"/></a>


In the logs, you'll see output from the multiple worker replicas and parameter servers that we utilized by specifying a `SCALE_TIER_STANDARD_1 ` cluster.  In the logs viewers, you can filter on the output of a particular node (e.g. a given worker) if you like.

Once your job is finished, you'll find the exported model under the specified GCS directory, in addition to other data such as model checkpoints.
That exported model has exactly the same signature as the locally-generated model we looked at above, and can be used in just the same ways.

### Scalably serve your trained model with Cloud ML Engine online prediction

You can deploy an exported model to Cloud ML Engine and scalably serve it for **prediction**, using the [Cloud ML Engine prediction service](https://cloud.google.com/ml-engine/docs/prediction-overview) to generate a prediction on new data with an easy-to-use REST API. Here we'll look at Cloud ML Engine online prediction, which [recently moved to general availability (GA) status](https://cloud.google.com/blog/big-data/2017/12/bringing-cloud-ml-engine-to-more-developers-with-online-prediction-features-and-reduced-prices); but [batch prediction](https://cloud.google.com/ml-engine/docs/batch-predict) is supported as well.

The online prediction service scales the number of nodes it uses to maximize the number of requests it can handle without introducing too much latency. To do that, the service:

- Allocates some nodes the first time you request predictions after a long pause in requests.
- Scales the number of nodes in response to request traffic, adding nodes when traffic increases, and removing them when there are fewer requests.
- Keeps at least one node ready to handle requests even when there are none to handle. It then scales down to zero by default when your model version goes several minutes without a prediction request (but if you like, you can specify a minimum number of nodes to keep ready for a given model).

See the accompanying [notebook](using_tf.estimator.train_and_evaluate.ipynb) for details on how to deploy your model so that you can use it to make predictions.

Once your model is serving with Cloud ML Engine Online Prediction, you can access it via a REST API.  It's [easy](https://cloud.google.com/ml-engine/docs/online-predict#requesting_predictions) to do this programmatically via the [Google Cloud Client libraries](https://cloud.google.com/apis/docs/cloud-client-libraries) or via `gcloud`.    
`gcloud` is great for testing your deployed model, and the command looks almost the same as it did for the local version of the model:

```sh
gcloud ml-engine predict --model census --version v1 --json-instances test.json
```

The Cloud Console makes it easy to inspect the different versions of a model, as well as set the default version: [console.cloud.google.com/mlengine/models](https://console.cloud.google.com/mlengine/models).
You can list your model information using `gcloud` too.

<a href="https://amy-jo.storage.googleapis.com/images/census_train_eval/ml_model_details.png" target="_blank"><img src="https://amy-jo.storage.googleapis.com/images/census_train_eval/ml_model_details.png" width="500"/></a>


## Summary -- and what's next?

In this example, we've walked through how to configure and use the TensorFlow `Estimator` class, and
`tf.estimator.train_and_evaluate`.  They enable distributed execution for training and evaluation, while also supporting local execution, and provides consistent behavior across both local/non-distributed and distributed configurations.

For more, see the accompanying [notebook](using_tf.estimator.train_and_evaluate.ipynb).  The notebook includes examples of how to run your training job on a Cloud ML Engine GPU cluster, and how to use Cloud ML Engine to do [hyperparameter tuning](https://cloud.google.com/ml-engine/docs/hyperparameter-tuning-overview).




