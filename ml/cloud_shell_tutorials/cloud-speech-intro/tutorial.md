# Speech to Text Transcription with the Cloud Speech API

## Overview

The [Cloud Speech API](https://cloud.google.com/speech/) lets you do speech-to-text transcription from audio files in over 80 languages.

In this lab, you will see how to send an audio file to the Cloud Speech API for transcription.

#### What you'll learn

* Creating a Speech API request and calling the API with curl
* Calling the Speech API with audio files in different languages

![Speech API logo](https://storage.googleapis.com/aju-dev-demos-codelabs/images/speech_api_sm.png)

**Time to complete**: About 20 minutes

Click the **Continue** button to move to the next step.

## Create a Google Cloud Platform (GCP) project if you don't have one

**If you already have a Google Cloud Platform project, you can skip this step**.

If you don't have a Google Cloud Platform (GCP) project yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.
**Note the name of your new project** — you'll use that in the next step.

Return to this tab once you're done.

## Set your project in the Cloud Shell and create an API Key

First, run the following command to ensure that the Cloud Shell is using the correct GCP project
(replacing `<project-name>` with the name of your project):

```bash
  gcloud config set project <project-name>
```

Next, since we'll be using curl to send a request to the Speech API, we'll need to generate an API key to pass in our request URL.

> **Note**: If you've already created an API key in this project during one of the other Cloud Shell tutorials, you can just use the existing key— you don't need to create another one. Just be sure to set the `API_KEY` environment variable with your existing key as described below.

To create an API key, navigate to:

**APIs & services > Credentials** in the [Cloud Console](https://console.cloud.google.com/):

![apis_and_services](https://storage.googleapis.com/aju-dev-demos-codelabs/images/apis_and_services.png)

Then click __Create credentials__:

![create_credentials1](https://storage.googleapis.com/aju-dev-demos-codelabs/images/create_credentials1.png)

In the drop-down menu, select __API key__:

![create_credentials2](https://storage.googleapis.com/aju-dev-demos-codelabs/images/create_credentials2.png)

Next, copy the key you just generated. Click __Close__.

Now that you have an API key, save it to an environment variable to avoid having to insert the value of your API key in each request. You can do this in Cloud Shell. Be sure to replace `<your_api_key>` with the key you just copied.

```bash
export API_KEY=<YOUR_API_KEY>
```

Next, you'll enable the Speech API for your project, if you've not already done so.

## Enable the Speech API

Click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=speech.googleapis.com) to enable the Speech API for your project.

After you've enabled it, you don't need to do any further setup, as you've already set up an API key. Just return to this tab.

Next, you'll use the Speech API to make a transcription request.

## Create your Speech API request

First, change to this directory in the cloud shell:

```bash
cd ~/code-snippets/ml/cloud_shell_tutorials/cloud-speech-intro
```

You'll remain in this directory for the rest of the tutorial.

Bring up the `request.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-speech-intro/request.json" "in the text editor"`.

It should look like this:

```json
{
  "config": {
      "encoding":"FLAC",
      "sample_rate": 16000,
      "language_code": "en-US"
  },
  "audio": {
      "uri":"gs://cloud-samples-tests/speech/brooklyn.flac"
  }
}
```

The request body has a `config` and `audio` object. In `config`, we tell the Speech API how to process the request. The `encoding` parameter tells the API which type of audio encoding you're using for the audio file you're sending to the API. `FLAC` is the encoding type for .raw files (see the  [documentation](https://cloud.google.com/speech/reference/rest/v1/speech/recognize#audioencoding) for encoding type for more details). `sample_rate` is the rate in Hertz of the audio data you're sending to the API. There are other parameters you can add to your `config` object, but `encoding` and `sample_rate` are the only required ones.

In the `audio` object, you're passing the URI of an audio file in [Google Cloud Storage](https://cloud.google.com/storage/).

Now you're ready to call the Speech API!


## Call the Speech API


You can now pass your request body, along with the API key environment variable you saved earlier, to the Speech API with the following `curl` command:

```bash
curl -s -X POST -H "Content-Type: application/json" --data-binary @request.json \
"https://speech.googleapis.com/v1beta1/speech:syncrecognize?key=${API_KEY}"
```

Notice that the curl command used the API key that you generated.

Your response should look something like the following:

```json
{
  "results": [
    {
      "alternatives": [
        {
          "transcript": "how old is the Brooklyn Bridge",
          "confidence": 0.9840146
        }
      ]
    }
  ]
}
```

The `transcript` value will return the Speech API's text transcription of your audio file, and the `confidence` value indicates how sure the API is that it has accurately transcribed your audio.

You'll notice that we called the `syncrecognize` method in our request above. The Speech API supports both synchronous and asynchronous speech to text transcription. In this example we sent it a complete audio file, but you can also use the `syncrecognize` method to perform streaming speech to text transcription while the user is still speaking.


## Speech to text transcription in different languages

Are you multilingual? The Speech API supports speech to text transcription in over 80 languages! You can change the `language_code` parameter in your json request. You can find a list of supported languages  [here](https://cloud.google.com/speech/docs/languages).

For example, if you had a Spanish audio file, you could set the `language_code` attributes in the `request.json` file like this:


```json
 {
  "config": {
      "encoding":"FLAC",
      "sample_rate": 16000,
      "language_code": "es-ES"
  },
  "audio": {
      "uri":"gs://.../..."
  }
}
```


## Congratulations!

`walkthrough conclusion-trophy`


You've learned how to perform speech to text transcription with the Speech API. In this example you passed the API the Google Cloud Storage URI of your audio file. Alternatively, you can pass a base64 encoded string of your audio content.

#### What we've covered

* Passing the Speech API a Google Cloud Storage URI of an audio file
* Creating a Speech API request and calling the API with curl
* Calling the Speech API with audio files in different languages

#### Some next steps

* Check out the Speech API  [tutorials](https://cloud.google.com/speech/docs/tutorials) in the documentation.
* Try out the  [Vision API](https://cloud.google.com/vision/) and  [Natural Language API](https://cloud.google.com/natural-language/)!

---------------
Copyright 2018 Google Inc. All Rights Reserved. Licensed under the Apache
License, Version 2.0 (the "License"); you may not use this file except in
compliance with the License. You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License.
