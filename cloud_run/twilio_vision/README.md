
# Cloud Run example: 'Twilio-vision'

This directory contains a simple [Cloud Run](https://cloud.google.com/run/docs/) example that lets you text images to a [Twilio](https://www.twilio.com) phone number (once set up), and get back information about how the
[Cloud Vision API](https://cloud.google.com/vision/docs/) labeled the image.

<a href="https://storage.googleapis.com/amy-jo/images/doofball_doghouse.jpg" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/doofball_doghouse.jpg" width=300/></a>

## Prerequisites

1. Create a project in the [Google Cloud Platform Console](https://console.cloud.google.com).

2. Enable the Cloud Vision API. See the
   ["Getting Started"](https://cloud.google.com/vision/docs/quickstart) page
   for more information.

3. Install the [Google Cloud SDK](https://cloud.google.com/sdk):

        $ curl https://sdk.cloud.google.com | bash
        $ gcloud init
    Alternately, you can use the [Cloud Shell](https://cloud.google.com/shell/docs/), where `gcloud` is already installed.

4. Optional: Install and start up [Docker](https://www.docker.com/).
   This is only necessary if you want to build your container image locally.
   You can run the example without doing this.


## Build and push the Docker image for your Cloud Run app

You can do this via either a local Docker installation, or via [Cloud Build](https://cloud.google.com/cloud-build/).

### Using a local Docker install

(If you're using the Cloud Shell, no installation or config should be necessary). 
Install docker, then run the following `gcloud` commands to add the gcloud Docker credential helper:

```sh
gcloud auth configure-docker
```

Then, run the following from this directory (the one that contains the `Dockerfile`) to build and push your container. Replace the following with your GCP project ID.

```sh
docker build -t gcr.io/<your_project>/twilio-vision:v1 .
docker push gcr.io/<your_project>/twilio-vision:v1
```

### Using Cloud Build

Alternately, build your container image using Cloud Build.  Run the following from this directory, again editing to use your project ID:

```sh
gcloud builds submit --tag gcr.io/<your_project>/twilio-vision:v1
```

## Deploy the Cloud Run app

Once you've built the container image, deploy the app as follows (edit to use your project id).  Replace the
`MESSAGE_BLURB` string with whatever you prefer — this string will be returned as part of the app response, along with information from the Cloud Vision API.

```sh
gcloud beta run deploy \
    --image gcr.io/<your_project>/twilio-vision:v1 \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars MESSAGE_BLURB="Courtesy of the Google Cloud Vision API..."
```

Make note of the endpoint the app is running on. You'll need it for the next step.

## Set up a Twilio number 

Create and set up a [Twilio account](https://www.twilio.com/try-twilio) and number capable of  sending and receiving MMS.

### Create a Twilio "TwilML app" using the your new Cloud Run service's URL

Visit [this page](https://www.twilio.com/console/sms/runtime/twiml-apps) on the Twilio
site, and create a "TwilML" app that points to the Cloud Run endpoint from the previous step.

Then, configure your Twilio phone number to use that TwiML app for Messaging.

## Test your app!

Text an image to the Twilio number.  You should receive a response with some information about the image from the Cloud Vision API.

<a href="https://storage.googleapis.com/amy-jo/images/doofball_doghouse.jpg" target="_blank"><img src="https://storage.googleapis.com/amy-jo/images/doofball_doghouse.jpg" width=300/></a>

