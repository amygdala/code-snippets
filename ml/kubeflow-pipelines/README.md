
# Kubeflow Pipelines examples

[Kubeflow](https://www.kubeflow.org/) is an OSS project to support a machine learning stack on Kubernetes, to make deployments of ML workflows on Kubernetes simple, portable and scalable.

[**Kubeflow Pipelines**](https://github.com/kubeflow/pipelines) is a new component of Kubeflow that makes it easy to compose, deploy and manage end-to-end machine learning workflows. The Kubeflow Pipelines documentation is [here](https://www.kubeflow.org/docs/guides/pipelines/).

This directory tree contains code for several different groups of Kubeflow Pipelines examples.

The examples highlight how Kubeflow and Kubeflow Pipelines can help support portability, composability and reproducibility, scalability, and visualization and collaboration in your ML lifecycle; and make it easier to support hybrid ML solutions.

The first set of pipelines uses some data on Chicago taxi trips.
Its README is here: [README_taxidata_examples.md](./README_taxidata_examples.md).
These examples include use of [TensorFlow Transform](https://github.com/tensorflow/transform) (TFT) for preprocessing and to avoid training/serving skew; Kubeflow's tf-jobs CRD for supporting distributed training; and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis.
The workflows also include deployment of the trained models to both
[Cloud ML Engine Online Prediction](https://cloud.google.com/ml-engine/docs/tensorflow/prediction-overview);
and to [TensorFlow Serving](https://github.com/tensorflow/serving) via Kubeflow.

The second Pipelines example shows how to build a web app that summarizes GitHub issues using Kubeflow Pipelines to train and serve a model.
The pipeline trains a Tensor2Tensor model on GitHub issue data, learning to predict issue titles from issue bodies. It then exports the trained model and deploys the exported model using Tensorflow Serving. The final step in the pipeline launches a web app, which interacts with the TF-Serving instance in order to get model predictions.
Its README is here: [README_github_summ.md](README_github_summ.md).
**Update**: going forward, the current version of this example lives here: https://github.com/kubeflow/examples/tree/master/github_issue_summarization/pipelines. The one in this repo may become outdated.

A third example shows how you can make calls to the AutoML Vision API to build a pipeline that creates an AutoML *dataset* and then trains a model on that dataset. Its README is here: [samples/automl/README.md](./samples/automl/README.md).
