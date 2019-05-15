
The pipeline in this directory shows how you can make calls to the AutoML Vision API to build a pipeline that creates an AutoML *dataset* and then trains a model on that dataset.

This pipeline requires a GKE installation of Kubeflow, e.g. via the
['click to deploy' web app](https://deploy.kubeflow.cloud/#/deploy).
Once Kubeflow is installed on your GKE cluster, to run this pipeline, you'll need to vist the [IAM panel in the GCP Cloud Console](https://pantheon.corp.google.com/iam-admin/iam), find the Kubeflow-created service account
`<deployment>-user@<project>.iam.gserviceaccount.com`, and add permissions to make that account an `AutoML Admin`. This will give the Kubeflow Pipeline steps permission to call the AutoML APIs.

[More detail TBD soon].