# Entity and Sentiment Analysis with the Natural Language API

## Overview

The [Cloud Natural Language API](https://cloud.google.com/natural-language/) lets you extract entities from text, perform sentiment and syntactic analysis, and classify text into categories.
In this lab, we'll learn how to use the Natural Language API to analyze entities, sentiment, and syntax.

What you'll learn:

* Creating a Natural Language API request and calling the API with curl
* Extracting entities and running sentiment analysis on text with the Natural Language API
* Performing linguistic analysis on text with the Natural Language API
* Creating a Natural Language API request in a different language

![Natural Language API logo](https://storage.googleapis.com/aju-dev-demos-codelabs/images/NaturalLanguage_Retina_sm.png)

**Time to complete**: About 30 minutes

Click the **Continue** button to move to the next step.

## Create a Google Cloud Platform (GCP) project if you don't have one

**If you already have a Google Cloud Platform project, you can skip this step**.

If you don't have a Google Cloud Platform (GCP) project yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.
**Note the name of your new project** — you'll use that in the next step.

Return to this tab once you're done.

## Set your project in the Cloud Shell and create an API Key

First, run the following command to ensure that the Cloud Shell is using the correct GCP project— whether new or existing— as follows (replacing `<project-name>` with the name of your project):

```bash
  gcloud config set project <project-name>
```

Next, since we'll be using curl to send a request to the Natural Language API, we'll need to generate an API key to pass in our request URL.

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

Next, you'll enable the Natural Language API for your project, if you've not already done so.

## Enable the Natural Langage API

Click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=language.googleapis.com) to enable the Natural Language API for your project. (After you've enabled it, you don't need to do any further setup, as you've already set up an API key above.)

Next, you'll use the Natural Language API to analyze *entities* in text.

## Make an Entity Analysis Request

First, change to this directory in the cloud shell:

```bash
cd ~/code-snippets/ml/cloud_shell_tutorials/cloud-nl-intro
```

You'll remain in this directory for the rest of the tutorial.

The first Natural Language API method we'll use is `analyzeEntities`. With this method, the API can extract entities
(like people, places, and events) from text. To try out the API's entity analysis, we'll use the following sentence:

> *Joanne Rowling, who writes under the pen names J. K. Rowling and Robert Galbraith, is a British novelist and screenwriter who wrote the Harry Potter fantasy series.*

Bring up the `request.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-intro/request.json" "in the text editor"`.

It should look like this:

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"Joanne Rowling, who writes under the pen names J. K. Rowling and Robert Galbraith, is a British novelist and screenwriter who wrote the Harry Potter fantasy series."
  },
  "encodingType":"UTF8"
}
```


In the request, you're telling the Natural Language API about the text being sent. Supported type values
are `PLAIN_TEXT` or `HTML`. In content, we pass the text to send to the Natural Language API for analysis. The Natural Language API also supports sending files stored in Cloud Storage for text processing. If you wanted to send a file from Cloud Storage, you would replace `content` with `gcsContentUri` and give it a value of the text file's uri in Cloud Storage. `encodingType` tells the API which type of text encoding to use when processing our text. The API will use this to calculate where specific entities appear in our text.

Next, you'll call the Natural Language API with that request.

## Call the Natural Language API


You can now pass your request body, along with the API key environment variable you saved earlier, to the Natural Language API with the following `curl` command (all in one single command line):

```bash
curl "https://language.googleapis.com/v1/documents:analyzeEntities?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request.json
```

Notice that the curl command used the API key that you generated.

The beginning of your response should look like this:

```json
{
  "entities": [
     {
      "name": "Robert Galbraith",
      "type": "PERSON",
      "metadata": {
        "mid": "/m/042xh",
        "wikipedia_url": "https://en.wikipedia.org/wiki/J._K._Rowling"
      },
      "salience": 0.78821284,
      "mentions": [
        {
          "text": {
            "content": "Joanne Rowling",
            "beginOffset": 0
          },
          "type": "PROPER"
        },
        {
          "text": {
            "content": "Rowling",
            "beginOffset": 53
          },
          "type": "PROPER"
        },
        {
          "text": {
            "content": "novelist",
            "beginOffset": 96
          },
          "type": "COMMON"
        },
        {
          "text": {
            "content": "Robert Galbraith",
            "beginOffset": 65
          },
          "type": "PROPER"
        }
      ]
    },
    ...
  ]}
```

For each entity in the response, we get the entity `type`, the associated Wikipedia URL if there is one, the
`salience`, and the indices of where this entity appeared in the text. Salience is a number in the [0,1] range that refers to the centrality of the entity to the text as a whole. The Natural Language API can also recognize the same entity mentioned in different ways. Take a look at the `mentions` list in the response: ​the API is able to tell that "Joanne Rowling", "Rowling", "novelist" and "Robert Galbraith" all point to the same thing.​

Next, we'll use the Natural Language API to perform sentiment analysis.

## Sentiment analysis with the Natural Language API

In addition to extracting entities, the Natural Language API also lets you perform sentiment analysis on a block of text. This JSON request will include the same parameters as the request above, but this time change the text to include something with a stronger sentiment.

Bring up the `request2.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-intro/request2.json" "in the text editor"`.

It should look like the following. (Feel free to replace the `content` below with your own text).

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"Harry Potter is the best book. I think everyone should read it."
  },
  "encodingType": "UTF8"
}
```

Next we'll send the request to the API's `analyzeSentiment` endpoint:

```bash
curl "https://language.googleapis.com/v1/documents:analyzeSentiment?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request2.json
```

Your response should look like this:

```json
{
  "documentSentiment": {
    "magnitude": 0.8,
    "score": 0.4
  },
  "language": "en",
  "sentences": [
    {
      "text": {
        "content": "Harry Potter is the best book.",
        "beginOffset": 0
      },
      "sentiment": {
        "magnitude": 0.7,
        "score": 0.7
      }
    },
    {
      "text": {
        "content": "I think everyone should read it.",
        "beginOffset": 31
      },
      "sentiment": {
        "magnitude": 0.1,
        "score": 0.1
      }
    }
  ]
}
```

Notice that you get two types of sentiment values: sentiment for the document as a whole, and sentiment broken down by sentence. The sentiment method returns two values:

* `score` - a number from -1.0 to 1.0 indicating how positive or negative the statement is.
* `magnitude` - a number ranging from 0 to infinity that represents the weight of sentiment expressed in the statement, regardless of being positive or negative.

Longer blocks of text with heavily weighted statements have higher magnitude values. The score for the first sentence is positive (0.7), whereas the score for the second sentence is neutral (0.1).

In addition to providing sentiment details on the entire text document, the Natural Language API can also break down sentiment by the entities in the text. We'll look at that next.

## Analyzing entity sentiment

In addition to providing sentiment details on the entire text document, the Natural Language API can also break down sentiment by the entities in the text. Use this sentence as an example:

> *I liked the sushi but the service was terrible*.

In this case, getting a sentiment score for the entire sentence as you did above might not be so useful. If this was a restaurant review and there were hundreds of reviews for the same restaurant, you'd want to know exactly which things people liked and didn't like in their reviews. Fortunately, the Natural Language API has a method that lets you get the sentiment for each entity in the text, called `analyzeEntitySentiment`. Let's see how it works!

Bring up the `request3.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-intro/request3.json" "in the text editor"`.

It should look like this:

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"I liked the sushi but the service was terrible."
  },
  "encodingType": "UTF8"
}
```


Then call the `analyzeEntitySentiment` endpoint with the following curl command:

```bash
curl "https://language.googleapis.com/v1/documents:analyzeEntitySentiment?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request3.json
```

In the response, you get back two entity objects: one for "sushi" and one for "service." Here's the full JSON response:

```json
{
  "entities": [
    {
      "name": "service",
      "type": "OTHER",
      "metadata": {},
      "salience": 0.5136989,
      "mentions": [
        {
          "text": {
            "content": "service",
            "beginOffset": 26
          },
          "type": "COMMON",
          "sentiment": {
            "magnitude": 0.9,
            "score": -0.9
          }
        }
      ],
      "sentiment": {
        "magnitude": 0.9,
        "score": -0.9
      }
    },
    {
      "name": "sushi",
      "type": "CONSUMER_GOOD",
      "metadata": {},
      "salience": 0.4863011,
      "mentions": [
        {
          "text": {
            "content": "sushi",
            "beginOffset": 12
          },
          "type": "COMMON",
          "sentiment": {
            "magnitude": 0.9,
            "score": 0.9
          }
        }
      ],
      "sentiment": {
        "magnitude": 0.9,
        "score": 0.9
      }
    }
  ],
  "language": "en"
}
```

You can see that the score returned for "sushi" was 0.9, whereas "service" got a score of -0.9. Cool! You also may notice that there are two sentiment objects returned for each entity. If either of these terms were mentioned more than once, the API would return a different sentiment score and magnitude for each mention, along with an aggregate sentiment for the entity.

The Natural Language API can also be used for analyzing syntax and parts of speech.  We'll do that next.

## Analyzing syntax and parts of speech

Looking at the Natural Language API's third method - text annotation - you'll dive deeper into the the linguistic details of the text. `annotateText` is an advanced method that provides a full set of details on the semantic and syntactic elements of the text. For each word in the text, the API will tell us the word's part of speech (noun, verb, adjective, etc.) and how it relates to other words in the sentence (Is it the root verb? A modifier?).

Try it out with a simple sentence. This JSON request will be similar to the ones above, with the addition of a features key. This will tell the API that we'd like to perform syntax annotation.

Bring up the `request4.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-intro/request4.json" "in the text editor"`.

It should look like this:

```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content": "Hermione often uses her quick wit, deft recall, and encyclopaedic knowledge to help Harry and Ron."
  },
  "encodingType": "UTF8"
}
```

Then call the API's `annotateText` method:

```bash
curl "https://language.googleapis.com/v1/documents:analyzeSyntax?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request4.json
```

The response should return an object like the one below for each token in the sentence:

```json
{
  "text": {
    "content": "uses",
    "beginOffset": 15
  },
  "partOfSpeech": {
    "tag": "VERB",
    "aspect": "ASPECT_UNKNOWN",
    "case": "CASE_UNKNOWN",
    "form": "FORM_UNKNOWN",
    "gender": "GENDER_UNKNOWN",
    "mood": "INDICATIVE",
    "number": "SINGULAR",
    "person": "THIRD",
    "proper": "PROPER_UNKNOWN",
    "reciprocity": "RECIPROCITY_UNKNOWN",
    "tense": "PRESENT",
    "voice": "VOICE_UNKNOWN"
  },
    "dependencyEdge": {
      "headTokenIndex": 2,
      "label": "ROOT"
    },
    "lemma": "use"
}
```

* `partOfSpeech` tells us that "uses" is a verb.
* `dependencyEdge` includes data that you can use to create a  [dependency parse tree](https://en.wikipedia.org/wiki/Parse_tree#Dependency-based_parse_trees) of the text. Essentially, this is a diagram showing how words in a sentence relate to each other. The (first part) of a dependency parse tree for the sentence above looks like this:

![parse tree](https://storage.googleapis.com/aju-dev-demos-codelabs/images/hermione.png)

* `lemma` is the canonical form of the word. The lemma value is useful for tracking occurrences of a word in a large piece of text over time.

The Natural Language API also supports languages other than English. Let's look at a Japanese example next.

## Multilingual natural language processing

The Natural Language API also supports languages other than English (full list  [here](https://cloud.google.com/natural-language/docs/languages)).


Bring up the `request5.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-intro/request5.json" "in the text editor"`.

It should look like this:


```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"Google lance un nouveau centre de recherche en Intelligence Artificielle en France."
  }
}
```

The text translates to: "Google is launching a new Artificial Intelligence research center in France".
Notice that you don't need to tell the API which language the text is — it can automatically detect it!

Next, you'll send this request to the `analyzeEntities` endpoint:

```bash
curl "https://language.googleapis.com/v1/documents:analyzeEntities?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request5.json
```

You should get the following response:

```json
{
  "entities": [
    {
      "name": "Google",
      "type": "ORGANIZATION",
      "metadata": {
        "mid": "/m/045c7b",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Google"
      },
      "salience": 0.3203956,
      "mentions": [
        {
          "text": {
            "content": "Google",
            "beginOffset": -1
          },
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "France",
      "type": "LOCATION",
      "metadata": {
        "mid": "/m/0f8l9c",
        "wikipedia_url": "https://en.wikipedia.org/wiki/France"
      },
      "salience": 0.24790826,
      "mentions": [
        {
          "text": {
            "content": "France",
            "beginOffset": -1
          },
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "Intelligence Artificielle",
      "type": "OTHER",
      "metadata": {},
      "salience": 0.19215278,
      "mentions": [
        {
          "text": {
            "content": "Intelligence Artificielle",
            "beginOffset": -1
          },
          "type": "COMMON"
        }
      ]
    },
    {
      "name": "centre",
      "type": "LOCATION",
      "metadata": {},
      "salience": 0.121489875,
      "mentions": [
        {
          "text": {
            "content": "centre",
            "beginOffset": -1
          },
          "type": "COMMON"
        }
      ]
    },
    {
      "name": "recherche",
      "type": "EVENT",
      "metadata": {},
      "salience": 0.11805349,
      "mentions": [
        {
          "text": {
            "content": "recherche",
            "beginOffset": -1
          },
          "type": "COMMON"
        }
      ]
    }
  ],
  "language": "fr"
}
```

Notice that in addition to the entity analysis, the language is correctly detected.

## Congratulations!

`walkthrough conclusion-trophy`

You've learned how to perform text analysis with the Cloud Natural Language API by extracting entities, analyzing sentiment, and doing syntax annotation.

#### What we've covered

* Creating a Natural Language API request and calling the API with curl
* Extracting entities and running sentiment analysis on text with the Natural Language API
* Performing linguistic analysis on text to create dependency parse trees
* Creating a Natural Language API request in Japanese

#### Some next steps

* Sign up for the full  [Coursera Course on Machine Learning](https://www.coursera.org/learn/serverless-machine-learning-gcp/)
* Check out the Natural Language API  [tutorials](https://cloud.google.com/natural-language/docs/tutorials) in the documentation.

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
