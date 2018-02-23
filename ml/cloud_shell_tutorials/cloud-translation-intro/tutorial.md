# Translate Text with the Translation API


## Overview

The [[Cloud Translation API](https://cloud.google.com/translate/) lets you translate an arbitrary string into any supported language using state-of-the-art Neural Machine Translation. 

In this lab, we'll use the Cloud Translation API from the command line to translate text and detect the language of text if the language is unknown.

![Translate API logo](https://storage.googleapis.com/aju-dev-demos-codelabs/images/Translate_API_sm.png)

**Time to complete**: About 15 minutes

Click the **Continue** button to move to the next step.

## Create a Google Cloud Platform (GCP) project if you don't have one

If you already have a Google Cloud Platform project, you can skip this step.

If you don't have a Google Cloud Platform (GCP) project yet, you can click this button to set one up. Be sure to sign up for the free trial when you do so. (You can also set up your project via [this link](https://cloud.google.com/free/)). 

`walkthrough project-billing-setup`

Once you have a GCP project created, note its name— you'll use that in the next step.

## Set your project in the Cloud Shell and create an API Key

Set the cloud shell to use your GCP project— whether new or existing— as follows (replacing `<project-name>` with the name of your project:

```bash
  gcloud config set project <project-name>
```


Next, since we'll be using curl to send a request to the Translation API, we'll need to generate an API key to pass in our request URL.

> **Note**: If you've already created an API key in this project during one of the other Cloud Shell tutorials, you can just use the existing key⸺you don't need to create another one.

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

Next, you'll enable the Translation API for your project, if you've not already done so.

## Enable the Translation API

Click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=translate.googleapis.com) to enable the Translation API for your project. (After you've enabled it, you don't need to do any further setup, as you've already set up an API key above.)

Next, you'll translate some text from English to Spanish.

## Translate Text

In this example you will translate the string "My name is Steve" into Spanish. Pass the text to be translated, along with the API key environment variable you saved earlier, to the Translation API with the following curl command:

```bash
TEXT="My%20name%20is%20Steve"
curl "https://translation.googleapis.com/language/translate/v2?target=es&key=${API_KEY}&q=${TEXT}"
```

Your response should look like the following:

```json
{
  "data": {
    "translations": [
      {
        "translatedText": "Mi nombre es Steve",
        "detectedSourceLanguage": "en"
      }
    ]
  }
}
```

In the response, you can see that the translated text as well as the source language that the API detected.​


## Detect Language

In addition to translating text, the Translation API also lets you detect the language of text. In this example you will detect the language of two strings. Pass the text to be examined, along with the API key environment variable you saved earlier, to the Translation API with the following curl command: 

```bash
TEXT_ONE="Meu%20nome%20é%20Steven"
TEXT_TWO="日本のグーグルのオフィスは、東京の六本木ヒルズにあります"
curl "https://translation.googleapis.com/language/translate/v2/detect?key=${API_KEY}&q=${TEXT_ONE}&q=${TEXT_TWO}"
```

Your response should look like this:

```json
{
  "data": {
    "detections": [
      [
        {
          "confidence": 0.84644311666488647,
          "isReliable": false,
          "language": "pt"
        }
      ],
      [
        {
          "confidence": 1,
          "isReliable": false,
          "language": "ja"
        }
      ]
    ]
  }
}
```

The languages returned by this sample are "pt" and "ja". These are the  [ISO-639-1](https://en.wikipedia.org/wiki/ISO_639-1) identifiers for Portuguese and Japanese. This  [list of languages supported by the Translation API](https://cloud.google.com/translate/docs/languages) lists all the possible language codes which can be returned.


## Congratulations!

`walkthrough conclusion-trophy`

You've learned how to translate text with the Cloud Translation API! 

#### What we've covered

* Creating a Cloud Translation API request and calling the API with curl
* Translating Text
* Using the Premium Edition
* Detecting Language

#### Next Steps

* Check out the  [Translation API sample applications ](https://cloud.google.com/translate/docs/samples)built using client libraries using a variety of popular programming languages.
* Try out the  [Vision API](https://cloud.google.com/vision/) and  [Speech API](https://cloud.google.com/speech/)!

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
