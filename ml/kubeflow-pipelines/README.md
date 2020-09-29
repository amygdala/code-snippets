
# Kubeflow Pipelines examples

[Kubeflow](https://www.kubeflow.org/) is an OSS project to support a machine learning stack on Kubernetes, to make deployments of ML workflows on Kubernetes simple, portable and scalable.

[**Kubeflow Pipelines**](https://github.com/kubeflow/pipelines) is a new component of Kubeflow that makes it easy to compose, deploy and manage end-to-end machine learning workflows. The Kubeflow Pipelines documentation is [here](https://www.kubeflow.org/docs/guides/pipelines/).

This directory tree contains code for several different groups of Kubeflow Pipelines examples.
The examples highlight how Kubeflow and Kubeflow Pipelines can help support portability, composability and reproducibility, scalability, and visualization and collaboration in your ML lifecycle; and make it easier to support hybrid ML solutions.

- A pipeline that [implements an AutoML Tables end-to-end workflow](https://github.com/amygdala/code-snippets/tree/master/ml/automl/tables/kfp_e2e).
- [Distributed Keras Tuner + KFP example](./keras_tuner)
- A pipeline that shows how you can make calls to the AutoML Vision API to build a pipeline that creates an AutoML *dataset* and then trains a model on that dataset: [samples/automl/README.md](./samples/automl/README.md).
- [Example pipeline](./sbtb) for Scale by the Bay workshop (2019)

## Deprecated examples

These examples are not currently maintained and most likely don't work properly.

- [README_taxidata_examples.md](./README_taxidata_examples.md)
- [README_github_summ.md](README_github_summ.md): going forward, the current version of this example lives here: https://github.com/kubeflow/examples/tree/master/github_issue_summarization/pipelines.

The first set of pipelines uses some data on Chicago taxi trips.
Its README is here: [README_taxidata_examples.md](./README_taxidata_examples.md).
These examples include use of [TensorFlow Transform](https://github.com/tensorflow/transform) (TFT) for preprocessing and to avoid training/serving skew; Kubeflow's tf-jobs CRD for supporting distributed training; and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis.
The workflows also include deployment of the trained models to both
[Cloud ML Engine Online Prediction](https://cloud.google.com/ml-engine/docs/tensorflow/prediction-overview);
and to [TensorFlow Serving](https://github.com/tensorflow/serving) via Kubeflow.
