
# "Bikes & Weather" training + serving pipeline

## Introduction

This Kubeflow pipeline trains a TF2 model on a dataset of bike rental information.
It predicts duration of bike rental for given trip configuration (starting rental station, end station, day of week, time of start, weather details, etc.)

Then, the model is served on the KF cluster using TF-serving.

### About the data

The default dataset used in this example is derived from two public datasets available on BigQuery: NOAA weather information and London bike rentals logs.  The datasets were joined based on date + weather that day for a London weather station.  Then some processing was done to add additional GIS-related fields and do some cleanup. 

The data, exported to GCS in CSV format, is here: `gs://aju-dev-demos-codelabs/bikes_weather/`. 
It has no particular sort, and has been arbitrarily divided into 'train' and 'test' files. You can copy these files and split the data differently if you like.

## Kubeflow Installation

This example assumes a Kubeflow installation onto GKE, though with some work it could be adapted for other cloud providers, as it only needs to access Google Cloud Storage (GCS).
It requires a GPU node pool.  
Probably the most straightforward way to do the installation is to follow the instructions in the first sections of this codelab: [https://g.co/codelabs/kfp-gis](https://g.co/codelabs/kfp-gis).

## Running the pipeline

This is the pipeline specification: [example_pipelines/bw.py](./example_pipelines/bw.py).

To run it, find detailed info at [kubeflow.org/docs/pipelines](https://www.kubeflow.org/docs/pipelines/)
The quick overview:

- Install the KFP SDK (this requires py3) as follows: `pip install -U kfp`. 
- Upload the compiled pipeline to the dashboard of your Kubeflow installation.  The codelab ([https://g.co/codelabs/kfp-gis](https://g.co/codelabs/kfp-gis)) gives more detail.
- Once uploaded, run the pipeline.  You'll need to provide some parameter(s), depending upon the how you want to run it, as described below.


### Training from scratch

You'll probably require about ~10 training epochs to build a model that's fairly accurate.  That will take a long time.  To do that, set the `epochs` parameter to 10, leave the `steps-per-epoch` parameter as the default `-1` (which indicates that the pipeline will calculate a value based on the dataset size), and leave the `load-checkpoint` field blank.

### Training from a checkpoint

Particularly for demos and workshops, you may want to load an existing checkpoint and train for just a few more steps from that starting point.
To train from an existing checkpoint, enter the GCS path to the checkpoint in the `load-checkpoint` field.  
The checkpoint should have the form `gs://path/to/checkpoint/bikes_weather.cpt`.  **Amy TODO: create a public such checkpoint**.

You may additionally want to override the `steps-per-epoch` default, to provide a specific number.

## Accessing the TF-serving service

The trained model is served using TF-Serving. 
Currently, the TF-serving service is deployed to an external IP endpoint. (**This may change**).  
After it's deployed, find the endpoint by running:

```sh
kubectl get services -n kubeflow
```

You'll see a service with a name of this form: `bikesw<timestamp>` and an external IP.

To test the endpoint, run the following, **replacing `<IP_ADDRESS>` with your actual external IP** for that service:

```sh
curl -d '{"instances": [{"end_station_id": "333", "ts": 1435774380.0, "day_of_week": "4", "start_station_id": "160", "euclidean": 4295.88, "loc_cross": "POINT(-0.13 51.51)POINT(-0.19 51.51)", "prcp": 0.0, "max": 94.5, "min": 58.9, "temp": 81.8, "dewp": 59.5 }]}' \
  -X POST http://<IP_ADDRESS>:8500/v1/models/bikesw:predict
```    

If you want to send a prediction request for multiple instances, you can edit the json above to include multiple data instances in the `"instances"` list.

### Scaling the TF-serving service

One nice feature of running on Kubernetes is that it makes it easy to scale out.  If you want to increase the number of replicas in the tf-serving deployment, this is easy to do. 

```sh
kubectl get deployments -n kubeflow
```
...

```sh
kubectl scale --replicas=1 deployment <deployment_name> -n kubeflow
```
...





