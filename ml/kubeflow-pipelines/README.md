
# Kubeflow Pipelines examples

[Kubeflow](https://www.kubeflow.org/) is an OSS project to support a machine learning stack on Kubernetes, to make deployments of ML workflows on Kubernetes simple, portable and scalable.

[**Kubeflow Pipelines**](https://github.com/kubeflow/pipelines) is a new component of Kubeflow that makes it easy to compose, deploy and manage end-to-end machine learning workflows. The Kubeflow Pipelines documentation is [here]().

This directory tree contains code for two different groups of Kubeflow Pipelines examples. 

The examples highlight how Kubeflow and Kubeflow Pipelines can help support portability, composability and reproducibility, scalability, and visualization and collaboration in your ML lifecycle; and make it easier to support hybrid ML solutions.

The first set of pipelines uses some data on Chicago taxi trips, and shows 
Its README is here: [README_taxidata_examples.md](./README_taxidata_examples.md).
These examples include use of [TensorFlow Transform](https://github.com/tensorflow/transform) (TFT) for preprocessing and to avoid training/serving skew; Kubeflow's tf-jobs CRD for supporting distributed training; and [TFMA](https://github.com/tensorflow/model-analysis/) for model analysis.
The workflows also include deployment of the trained models to both
[Cloud ML Engine Online Prediction](https://cloud.google.com/ml-engine/docs/tensorflow/prediction-overview);
and to [TensorFlow Serving](https://github.com/tensorflow/serving) via Kubeflow.

The second set of 
Its README is here: [README_github_summ.md](README_github_summ.md).


