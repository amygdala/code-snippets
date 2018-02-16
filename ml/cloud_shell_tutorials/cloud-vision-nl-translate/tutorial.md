# Extract, Analyze, and Translate Text from Images with the Cloud ML APIs


## Overview

In this lab, we'll explore the power of machine learning by using multiple machine learning APIs together. We'll start with the [Cloud Vision API's](https://cloud.google.com/vision/) text detection method to make use of Optical Character Recognition (OCR) to extract text from images. Then we'll learn how to translate that text with the [Translation API](https://cloud.google.com/translate/) and analyze it with the [Natural Language API](https://cloud.google.com/natural-language/).

What you'll learn:

* Creating a Vision API request and calling the API with curl
* Using the text detection (OCR) method of the Vision API
* Using the Translation API to translate text from your image
* Using the Natural Language API to analyze the text

![Some of the ML APIs](https://storage.googleapis.com/aju-dev-demos-codelabs/images/tutorial_mlapi_initial_image_sm.png)

**Time to complete**: About 30 minutes

Click the **Continue** button to move to the next step.

## Create an API Key

Since we'll be using curl to send a request to the Vision API, we'll need to generate an API key to pass in our request URL.

> **Note**: If you've already created an API key in this project during one of the other Cloud Shell tutorials, you can just use the existing key⸺you don't need to create another one.

To create an API key, navigate to:

**APIs & services > Credentials**:

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

Next, you'll enable the Vision, Translate, and Natural Language APIs for your project, if you've not already done so.

## Enable the Vision, Translate, and Natural Language APIs

Click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com,translate.googleapis.com,language.googleapis.com) to enable the Vision, Translate, and Natural Language APIs for your project.
(After you've enabled them, you don't need to do any further setup, as you've already set up an API key above.)

Next, you'll send a request to the Cloud Vision API.

## Create your Vision API request

First, change to this directory in the cloud shell:

```bash
cd ~/code-snippets/ml/cloud_shell_tutorials/cloud-vision-nl-translate
```

You'll remain in this directory for the rest of the tutorial.

We've uploaded a picture of a French sign to this Google Cloud Storage 
URL, and made it public: `gs://aju-dev-demos-codelabs/images/french_sign.png`.
The sign looks like this:

![french_sign](https://storage.googleapis.com/aju-dev-demos-codelabs/images/french_sign.png)


You'll use that URL to form a JSON request to analyze the photo. In particular, you're going to use
the  [`TEXT_DETECTION`](https://cloud.google.com/vision/docs/ocr) feature of the Vision API. This will run optical character recognition (OCR) on the image to extract text.

Bring up the `ocr-request.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-vision-nl-translate/ocr-request.json" "in the text editor"`.

It contains the following request:


```json
{
  "requests": [
      {
        "image": {
          "source": {
              "gcsImageUri": "gs://aju-dev-demos-codelabs/images/french_sign.png"
          } 
        },
        "features": [
          {
            "type": "TEXT_DETECTION",
            "maxResults": 10
          }
        ]
      }
  ]
}
```

Next, you'll call the Vision API using this JSON request file.

## Call the Vision API's text detection method


In Cloud Shell, call the Vision API with `curl`:

```bash
curl -s -X POST -H "Content-Type: application/json" --data-binary @ocr-request.json  https://vision.googleapis.com/v1/images:annotate?key=${API_KEY}
```

Notice that the curl command used the API key that you generated.

The first part of your response should look like the following:

```json
{
  "responses": [
    {
      "textAnnotations": [
        {
          "locale": "fr",
          "description": "LE BIEN PUBLIC\nles dépeches\nPour Obama,\nla moutarde\nest\nde Dijon\n",
          "boundingPoly": {
            "vertices": [
              {
                "x": 146,
                "y": 48
              },
              {
                "x": 621,
                "y": 48
              },
              {
                "x": 621,
                "y": 795
              },
              {
                "x": 146,
                "y": 795
              }
            ]
          }
        },
        {
          "description": "LE",
          "boundingPoly": {
            "vertices": [
              {
                "x": 146,
                "y": 99
              },
              {
                "x": 274,
                "y": 85
              },
              {
                "x": 284,
                "y": 175
              },
              {
                "x": 156,
                "y": 189
              }
            ]
          }
        },
        {
          "description": "BIEN",
          "boundingPoly": {
            "vertices": [
              {
                "x": 292,
                "y": 83
              },
              {
                "x": 412,
                "y": 70
              },
            }
            ...
      ]
}]
}
```


The OCR method is able to extract lots of text from our image, cool! Let's break down the response. The first piece of data you get back from `textAnnotations` is the entire block of text the API found in the image. This includes the language code (in this case fr for French), a string of the text, and a bounding box indicating where the text was found in our image. Then you get an object for each word found in the text with a bounding box for that specific word.

> **Note**: The Vision API also has a `DOCUMENT_TEXT_DETECTION` feature optimized for images with more text. This response includes additional information and breaks text down into page, blocks, paragraphs, and words.

Unless you speak French you probably don't know what this says. The next step is translation. 

Run the following `curl` command to save the response to an `ocr-response.json` file so it can be referenced later:

```
curl -s -X POST -H "Content-Type: application/json" --data-binary @ocr-request.json  https://vision.googleapis.com/v1/images:annotate?key=${API_KEY} -o ocr-response.json
```
Next, we'll send the extracted text to the Translation API.

## Sending the extracted text from the image to the Translation API


The [Translation API](https://cloud.google.com/translate/docs/reference/translate) can translate text into 100+ languages. It can also detect the language of the input text. To translate the French text into English, all you need to do is pass the text and the language code for the target language (en-US) to the Translation API.

Bring up the `translation-request.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-vision-nl-translate/translation-request.json" "in the text editor"`.

It should look like this:

```json
{
  "q": "your_text_here",
  "target": "en"
}
```

`q` is where you'll pass the string to translate. 


Run the following command in Cloud Shell to extract the image text from the previous step and update `translation-request.json`, in one command:

```bash
STR=$(jq .responses[0].textAnnotations[0].description ocr-response.json) && STR="${STR//\"}" && sed -i "s|your_text_here|$STR|g" translation-request.json
```

Now you're ready to call the Translation API. This command will also copy the response into a translation-response.json file:

```bash
curl -s -X POST -H "Content-Type: application/json" --data-binary @translation-request.json https://translation.googleapis.com/language/translate/v2?key=${API_KEY} -o translation-response.json
```

Run this command to inspect the file with the Translation API response:

```bash
cat translation-response.json
```

Awesome, you can understand what the sign said!  The result should look like this:

```json
{
  "data": {
    "translations": [
      {
        "translatedText": "THE PUBLIC GOOD the despatches For Obama, the mustard is from Dijon",
        "detectedSourceLanguage": "fr"
      }
    ]
  }
}
```

In the response, `translatedText` contains the resulting translation, and `detectedSourceLanguage` is `fr`, the ISO language code for French. The Translation API supports 100+ languages, all of which are listed  [here](https://cloud.google.com/translate/docs/languages).

In addition to translating the text from our image, you might want to do more analysis on it. That's where the Natural Language API comes in handy. 

Onward to the next step, where we'll analyze the translated text using the Natural Language API.

## Analyzing our image's text with the Natural Language API


The Natural Language API helps us understand text by extracting entities, analyzing sentiment and syntax, and classifying text into categories. You can use the `analyzeEntities` method to see what entities the Natural Language API can find in the text from your image. 

Bring up the `nl-request.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-vision-nl-translate/nl-request.json" "in the text editor"`.

It should look like this:

```javascript
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"your_text_here"
  },
  "encodingType":"UTF8"
}
```

In the request, you're telling the Natural Language API about the text you're sending:

__`type`:__ Supported type values are `PLAIN_TEXT` or `HTML`.

__`content`:__ pass the text to send to the Natural Language API for analysis. The Natural Language API also supports sending files stored in Cloud Storage for text processing. To send a file from Cloud Storage, you would replace `content` with `gcsContentUri` and use the value of the text file's uri in Cloud Storage.

__`encodingType`:__ tells the API which type of text encoding to use when processing the text. The API will use this to calculate where specific entities appear in the text.

Run the following bash command in Cloud Shell to copy the translated text into the content block of the `nl-request.json` Natural Language API request:

```bash
STR=$(jq .data.translations[0].translatedText  translation-response.json) && STR="${STR//\"}" && sed -i "s|your_text_here|$STR|g" nl-request.json
```

The `nl-request.json` file now contains the translated English text from the original image. Time to analyze it! 

Call the `analyzeEntities` endpoint of the Natural Language API with this `curl` request:

```bash
curl "https://language.googleapis.com/v1/documents:analyzeEntities?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @nl-request.json
```

In the response you can see the entities the Natural Language API found:

```json
{
  "entities": [
    {
      "name": "despatches",
      "type": "OTHER",
      "metadata": {},
      "salience": 0.31271625,
      "mentions": [
        {
          "text": {
            "content": "despatches",
            "beginOffset": 20
          },
          "type": "COMMON"
        }
      ]
    },
    {
      "name": "PUBLIC GOOD",
      "type": "OTHER",
      "metadata": {
        "mid": "/m/017bkk",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Public_good"
      },
      "salience": 0.28040817,
      "mentions": [
        {
          "text": {
            "content": "PUBLIC GOOD",
            "beginOffset": 4
          },
        {
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "Obama",
      "type": "PERSON",
      "metadata": {
        "wikipedia_url": "https://en.wikipedia.org/wiki/Barack_Obama",
        "mid": "/m/02mjmr"
      },
      "salience": 0.19405179,
      "mentions": [
        {
          "text": {
            "content": "Obama",
            "beginOffset": 35
          },
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "mustard",
      "type": "OTHER",
      "metadata": {},
      "salience": 0.11838918,
      "mentions": [
        {
          "text": {
            "content": "mustard",
            "beginOffset": 46
          },
          "type": "COMMON"
        }
      ]
    },
    {
      "name": "Dijon",
      "type": "LOCATION",
      "metadata": {
        "mid": "/m/0pbhz",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Dijon"
      },
      "salience": 0.09443461,
      "mentions": [
        {
          "text": {
            "content": "Dijon",
            "beginOffset": 62
          },
          "type": "PROPER"
        }
      ]
    }
  ],
  "language": "en"
}
```

For entities that have a wikipedia page, the API provides metadata including the URL of that page along with the entity's `mid`. The `mid` is an ID that maps to this entity in Google's Knowledge Graph. To get more information on it, you could call the  [Knowledge Graph API](https://developers.google.com/knowledge-graph/), passing it this ID. For all entities, the Natural Language API tells us the places it appeared in the text `(mentions`), the `type` of entity, and `salience` (a [0,1] range indicating how important the entity is to the text as a whole). In addition to English, the Natural Language API also supports the languages listed  [here](https://cloud.google.com/natural-language/docs/languages).

Looking at this image it's relatively easy for us to pick out the important entities, but if we had a library of thousands of images this would be much more difficult. OCR, translation, and natural language processing can help to extract meaning from large datasets of images.


## Congratulations!

`walkthrough conclusion-trophy`

You've learned how to combine 3 different machine learning APIs: the Vision API's OCR method extracted text from an image, then the Translation API translated that text to English, and then the Natural Language API to found entities in that text.

#### What we've covered

* Use cases for combining multiple machine learning APIs
* Creating a Vision API OCR request and calling the API with curl
* Translating text with the Translation API
* Extract entities from text with the Natural Language API


#### Some next steps

* Sign up for the full  [Coursera Course on Machine Learning](https://www.coursera.org/learn/serverless-machine-learning-gcp/)
* Check out the tutorials and docs for  [Vision](https://cloud.google.com/vision/docs/detecting-text),  [Translation](https://cloud.google.com/translate/docs/samples), and  [Natural Language](https://cloud.google.com/natural-language/docs/samples)


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


