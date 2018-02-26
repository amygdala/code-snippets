
# Shot Change Detection with the Cloud Video Intelligence API

## Overview

The [Cloud Video Intelligence API](https://cloud.google.com/video-intelligence/) Google Cloud Video Intelligence makes videos searchable and discoverable, by extracting metadata with an easy-to-use REST API.

This lab walks you through a basic Video Intelligence API Python application, using a `SHOT_CHANGE_DETECTION` request, which identifies all of the shot changes that occur within a given video, and the start and end times of each shot.

What you'll learn:

* How to programmatically access the Video Intelligence API in Python.
* How to authenticate with the Video Intelligence API.
* How to parse results returned from a request.

![Video Intelligence API logo](https://storage.googleapis.com/aju-dev-demos-codelabs/images/video_intell_api_sm.png)

**Time to complete**: About 20 minutes

Click the **Continue** button to move to the next step.

## Create a Google Cloud Platform (GCP) project if you don't have one

**If you already have a Google Cloud Platform project, you can skip this step**.

If you don't have a Google Cloud Platform (GCP) project yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.
**Note the name of your new project** — you'll use that in the next step.

Return to this window once you're done.

## Set your project in the Cloud Shell and Enable the Video Intelligence API

### Ensure the Cloud Shell is set to use your project

First, export the name of your Cloud project as an environment variable (replacing `<project-name>` with the name of your project).

```bash
export PROJECT=<your_project_name>
```

Then, run the following command to ensure that the Cloud Shell is using the correct GCP project:

```bash
  gcloud config set project $PROJECT
```

### Enable the Video Intelligence API

Next, click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=videointelligence.googleapis.com) to **enable the Video Intelligence API** for your project, if you haven't already done so.

After you've enabled it, just return to this window.

Next, you'll create a service account, in order to allow our Python script to authenticate with the Video Intelligence API.

## Create a service account

First, change to this directory in the cloud shell:

```bash
cd ~/code-snippets/ml/cloud_shell_tutorials/cloud-video-shotchange
```

You'll remain in this directory for the rest of the tutorial.

Before we can run the script, we need to create a [service account](https://cloud.google.com/iam/docs/understanding-service-accounts). This will allow our Python script to authenticate with the Video Intelligence API using [application default credentials](https://developers.google.com/identity/protocols/application-default-credentials).

Here, we'll create the service account from the command line, though it's also possible to [manage service accounts](https://cloud.google.com/video-intelligence/docs/common/auth#set_up_a_service_account) via the [Cloud Console](https://console.cloud.google.com).

Run the following commands from Cloud Shell to create a service account and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the downloaded service account key file. Note that the `PROJECT` environment variable must be set, as done in the previous section.

```bash
gcloud iam service-accounts create my-account --display-name my-account
gcloud iam service-accounts keys create key.json --iam-account=my-account@$PROJECT.iam.gserviceaccount.com
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

(If you've already created a service account in that project with the same name, e.g. in a previous tutorial, you will see an ignorable error with the 'create' command).

You can take a look at the `key.json` file that was downloaded via:

```bash
cat key.json
```

## Run a Python script to analyze video shot changes

We'll run a script that uses the Video Intelligence API to analyze shot changes in a video.
Install the python library requirements for the example:

```bash
pip install --upgrade -r requirements.txt
```

Bring up the `shotchange.py` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-video-shotchange/shotchange.py" "in the text editor"`.

It should look like this (a few comments have been removed for conciseness):


```python
import argparse

from google.cloud import videointelligence


def analyze_shots(path):
    """ Detects camera shot changes. """
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.enums.Feature.SHOT_CHANGE_DETECTION]
    operation = video_client.annotate_video(path, features=features)
    print('\nProcessing video for shot change annotations:')

    result = operation.result(timeout=90)
    print('\nFinished processing.')

    for i, shot in enumerate(result.annotation_results[0].shot_annotations):
        start_time = (shot.start_time_offset.seconds +
                      shot.start_time_offset.nanos / 1e9)
        end_time = (shot.end_time_offset.seconds +
                    shot.end_time_offset.nanos / 1e9)
        print('\tShot {}: {} to {}'.format(i, start_time, end_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('path', help='GCS path for shot change detection.')
    args = parser.parse_args()

    analyze_shots(args.path)
```

Let's run it first, then take a closer look at what it's doing. To run the script, simply pass it the Google Cloud Storage URI of a video:

```bash
python shotchange.py gs://demomaker/gbikes_dinosaur.mp4
```

While we're passing a Google Cloud Storage URI to the script, you can also take a look at the video [here](https://storage.googleapis.com/demomaker/gbikes_dinosaur.mp4) to see what's in it.

You'll see output like this:

```
Processing video for shot change annotations:
Finished processing.
        Shot 0: 0.0 to 5.166666
        Shot 1: 5.233333 to 10.066666
        Shot 2: 10.1 to 28.133333
        Shot 3: 28.166666 to 42.766666
```


This simple application performs the following tasks:

- Imports the libraries necessary to run the application
- Gets credentials to run the Video Intelligence API service
- Creates a video annotation request to send to the video service
- Sends the request and waits for the response
- Parses the response for the service and displays it to the user

We'll look at some of these steps in more detail next.

## A closer look at the code

### Importing libraries

```python
import argparse
from google.cloud import videointelligence
```

To use the Cloud Video Intelligence API, we'll import the `google.cloud.videointelligence` library.
We also import a standard library, `argparse`, to allow the application to accept input filenames as arguments.

Next, let's look at how we send a request to the Video Intelligence API to do shot detection.

## Constructing a request to the Video Intelligence API

Before communicating with the Video Intelligence API service, you need to authenticate your service using previously acquired credentials. Within an application, it's simplest to use Application Default Credentials (ADC). By default, ADC will attempt to obtain credentials from the `GOOGLE_APPLICATION_CREDENTIALS` environment file, which we set above to point to your service account's `key.json` file. So, with that environment variable set, we can just run the script.

In the script, we first create a client object:

```python
video_client = videointelligence.VideoIntelligenceServiceClient()
```

Then, we construct a request to the service, by building a JSON object that indicates we'd like to do shot change detection:

```python
features = [videointelligence.enums.Feature.SHOT_CHANGE_DETECTION]
```

Then, we call the client with our request, and wait for the result. In the request, `path` is the [Google Cloud Storage](https://cloud.google.com/storage/) path to the video we want to analyze (when we ran the script above, we passed in `gs://demomaker/gbikes_dinosaur.mp4`).

```python
operation = video_client.annotate_video(path, features=features)
print('\nProcessing video for shot change annotations:')
result = operation.result(timeout=90)
print('\nFinished processing.')
```

Next, we'll parse the result.

## Parsing the response from the Video Intelligence API

We can grab information about the shot changes from the result object as follows, then enumerate the shots to extract the start and end times of the segements.

```python
for i, shot in enumerate(result.annotation_results[0].shot_annotations):
    start_time = (shot.start_time_offset.seconds +
                  shot.start_time_offset.nanos / 1e9)
    end_time = (shot.end_time_offset.seconds +
                shot.end_time_offset.nanos / 1e9)
    print('\tShot {}: {} to {}'.format(i, start_time, end_time))
```


## Congratulations!

`walkthrough conclusion-trophy`


You've learned how to make a request to the Video Intelligence API and parse the results.

#### What we've covered

* How to programmatically access the Video Intelligence API in Python to request shot change annotations for a video.
* How to authenticate with the Video Intelligence API using a service account.
* How to parse results returned from a request.

#### Next Steps

* Take a look at the [documentation](https://cloud.google.com/video-intelligence/docs) for the Video Intelligence API, including the API reference, other tutorials, and information on accessing the API in other languages.
* Watch the [Next 2017 keynote demo, which introduces](https://www.youtube.com/watch?v=mDAoLO4G4CQ) the Video Intelligence API.
