# Detect Labels, Faces, and Landmarks in Images with the Cloud Vision API


## Overview


The [Cloud Vision API](https://cloud.google.com/vision/) lets you understand the content of an image by encapsulating powerful machine learning models in a simple REST API.

In this lab, we will send images to the Vision API and see it detect objects, faces, and landmarks.

What you'll learn:

* Creating a Vision API request and calling the API with curl
* Using the label, web, face, and landmark detection methods of the vision API

![Vision API logo](https://storage.googleapis.com/aju-dev-demos-codelabs/images/Vision_logo_sm.png)

**Time to complete**: About 30 minutes

Click the **Continue** button to move to the next step.

## Create a Google Cloud Platform (GCP) project if you don't have one

**If you already have a Google Cloud Platform project, you can skip this step**.

If you don't have a Google Cloud Platform (GCP) project yet, create one [here](https://cloud.google.com/free/). Be sure to sign up for free trial credits.
**Note the name of your new project** — you'll use that in the next step.

Return to this window once you're done.

## Set your project in the Cloud Shell and create an API Key

First, run the following command to ensure that the Cloud Shell is using the correct GCP project
(replacing `<project-name>` with the name of your project):

```bash
  gcloud config set project <project-name>
```

Next, since we'll be using curl to send a request to the Vision API, we'll need to generate an API key to pass in our request URL.

> **Note**: If you've already created an API key in this project during one of the other Cloud Shell tutorials, you can just use the existing key— you don't need to create another one.  Just be sure to set the `API_KEY` environment variable with your existing key as described below.

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

Next, you'll enable the Vision API for your project, if you've not already done so.

## Enable the Vision API

Click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com) to enable the Vision API for your project, if you haven't already done so.

After you've enabled it, you don't need to do any further setup, as you've already set up an API key. Just return to this window.

Next, you'll send a request to the Vision API.


## Create your Vision API request

First, change to this directory in the cloud shell:

```bash
cd ~/code-snippets/ml/cloud_shell_tutorials/cloud-vision-intro
```

We'll send a larger version of this image (of donuts) to the Vision API:

![donuts](https://storage.googleapis.com/aju-dev-demos-codelabs/images/vision_donuts_sm.jpeg)

Bring up the `request.json` file
<walkthrough-editor-open-file filePath="code-snippets/ml/cloud_shell_tutorials/cloud-vision-intro/request.json">in the text editor</walkthrough-editor-open-file>

It should look like this:

```json
{
  "requests": [
      {
        "image": {
          "source": {
              "imageUri": "https://storage.googleapis.com/aju-dev-demos-codelabs/images/vision_donuts.png"
          }
        },
        "features": [
          {
            "type": "LABEL_DETECTION",
            "maxResults": 10
          }
        ]
      }
  ]
}
```

The first Cloud Vision API feature we'll explore is label detection. This method will return a list of labels (words) of what's in your image.


## Call the Vision API's label detection method


We're now ready to call the Vision API with curl:

```bash
curl -s -X POST -H "Content-Type: application/json" --data-binary @request.json  https://vision.googleapis.com/v1/images:annotate?key=${API_KEY}
```

Notice that the curl command used the API key that you generated.

Your response should look something like the following:

```json
{
  "responses": [
    {
      "labelAnnotations": [
        {
          "mid": "/m/01dk8s",
          "description": "powdered sugar",
          "score": 0.94369215,
          "topicality": 0.94369215
        },
        {
          "mid": "/m/01wydv",
          "description": "beignet",
          "score": 0.7160288,
          "topicality": 0.7160288
        },
        {
          "mid": "/m/06_dn",
          "description": "snow",
          "score": 0.7121925,
          "topicality": 0.7121925
        },
        {
          "mid": "/m/0bp3f6m",
          "description": "fried food",
          "score": 0.7075313,
          "topicality": 0.7075313
        },
        {
          "mid": "/m/02wvn_6",
          "description": "ricciarelli",
          "score": 0.5625,
          "topicality": 0.5625
        },
        {
          "mid": "/m/052lwg6",
          "description": "baked goods",
          "score": 0.53270745,
          "topicality": 0.53270745
        }
      ]
    }
  ]
}
```

The API was able to identify the specific type of donuts these are (beignets), cool!

For each label the Vision API found, it returns a `description` with the name of the item. It also returns a `score`, a number from 0 - 100 indicating how confident it is that the description matches what's in the image, and a `topicality`, which is the relevancy label to the image. (For example, the relevancy of "tower" is likely higher to an image containing the detected "Eiffel Tower" than to an image containing a detected distant towering building, even though the confidence that there is a tower in each image may be the same).

The `mid` value maps to the item's mid in Google's  [Knowledge Graph](https://www.google.com/intl/bn/insidesearch/features/search/knowledge.html). You can use the `mid` when calling the  [Knowledge Graph API](https://developers.google.com/knowledge-graph/) to get more information on the item.

## Web Detection with the Vision API


In addition to getting labels on what's in our image, the Vision API can also search the Internet for additional details on our image. Through the API's [webDetection method](https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate#WebDetection), we get a lot of interesting data back:

* A list of entities found in our image, based on content from pages with similar images
* URLs of exact and partial matching images found across the web, along with the URLs of those pages
* URLs of similar images, like doing a reverse image search

To try out web detection, we'll use the same image of beignets from above so all we need to change is one line in our request file (you can also venture out into the unknown and use an entirely different image). Under the features list, we'll just change "type" from `LABEL_DETECTION` to `WEB_DETECTION`.

Bring up the `request2.json` file
<walkthrough-editor-open-file filePath="code-snippets/ml/cloud_shell_tutorials/cloud-vision-intro/request2.json">in the text editor</walkthrough-editor-open-file>

The request should look like this, with just the "type" different from the previous request:

```json
{
  "requests": [
      {
        "image": {
          "source": {
              "imageUri": "https://storage.googleapis.com/aju-dev-demos-codelabs/images/vision_donuts.png"
          }
        },
        "features": [
          {
            "type": "WEB_DETECTION",
            "maxResults": 10
          }
        ]
      }
  ]
}
```

To send this request to the Vision API, you can use curl as before:

```bash
curl -s -X POST -H "Content-Type: application/json" --data-binary @request2.json  https://vision.googleapis.com/v1/images:annotate?key=${API_KEY}
```

Let's dive into the response, starting with `webEntities`. Here are some of the entities this image returned:

```json
 "webEntities": [
          {
            "entityId": "/m/01hyh_",
            "score": 0.7119,
            "description": "Machine learning"
          },
          ...
          {
            "entityId": "/m/0105pbj4",
            "score": 0.6036,
            "description": "Google Cloud Platform"
          },
          ...
          {
            "entityId": "/m/045c7b",
            "score": 0.244,
            "description": "Google"
          },
          ...
        ]
```

This image has been reused in many presentations on our Cloud ML APIs, which is why the API found the entities "Machine learning," "Google Cloud Platform," and "Google".

If we inpsect the URLs under `fullMatchingImages`, `partialMatchingImages`, and `pagesWithMatchingImages`, we'll notice that many of the URLs point to a Google codelab site where a similar version of this lab exists.

Let's say we want to find other images of beignets, but not the exact same images. That's where the
`visuallySimilarImages` part of the API response comes in handy. Here are a few of the visually similar images it found (you might see some different URLs, but with similar content):

```json
"visuallySimilarImages": [
          {
            "url": "https://igx.4sqi.net/img/general/558x200/21646809_fe8K-bZGnLLqWQeWruymGEhDGfyl-6HSouI2BFPGh8o.jpg"
          },
          {
            "url": "https://spoilednyc.com//2016/02/16/beignetszzzzzz-852.jpg"
          },
          {
            "url": "https://img-global.cpcdn.com/001_recipes/a66a9a6fc2696648/1200x630cq70/photo.jpg"
          },
          ...
]
```

We can navigate to those URLs to see the similar images:

![a beignet](https://storage.googleapis.com/aju-dev-demos-codelabs/images/b1.jpeg) ![a beignet](https://storage.googleapis.com/aju-dev-demos-codelabs/images/b2.jpeg)

![a beignet](https://storage.googleapis.com/aju-dev-demos-codelabs/images/b3.jpeg) ![a beignet](https://storage.googleapis.com/aju-dev-demos-codelabs/images/b4.jpeg)

Cool! And now you probably really want a beignet (sorry). This is similar to searching by an image on
[Google Images](https://images.google.com/).
But with Cloud Vision, we can access this functionality with an easy-to-use REST API and integrate it into our applications.


## Face and Landmark Detection with the Vision API

Next we'll explore the face and landmark detection methods of the Vision API. The face detection method returns data on faces found in an image, including the emotions of the faces and their location in the image. Landmark detection can identify common (and obscure) landmarks - it returns the name of the landmark, its latitude longitude coordinates, and the location of where the landmark was identified in an image.

To use these two new methods, let's use a new image with faces and landmarks:

![selfie](https://storage.googleapis.com/aju-dev-demos-codelabs/images/selfie.jpeg)

Next, we'll update our json request to include the URL of the new image, and to use face and landmark detection instead of label detection.

Bring up the `request3.json` file
<walkthrough-editor-open-file filePath="code-snippets/ml/cloud_shell_tutorials/cloud-vision-intro/request3.json">in the text editor</walkthrough-editor-open-file>

It contains the following request. Note the 'types' specified:

```json
{
  "requests": [
      {
        "image": {
          "source": {
              "imageUri": "https://storage.googleapis.com/aju-dev-demos-codelabs/images/selfie.png"
          }
        },
        "features": [
          {
            "type": "FACE_DETECTION"
          },
          {
            "type": "LANDMARK_DETECTION"
          }
        ]
      }
  ]
}
```

Next, we'll call the Vision API with this request.

## Call the Vision API and parse the response

Now you're ready to call the Vision API using curl as before:

```bash
curl -s -X POST -H "Content-Type: application/json" --data-binary @request3.json  https://vision.googleapis.com/v1/images:annotate?key=${API_KEY}
```

Let's take a look at the `faceAnnotations` object in our response first. You'll notice the API returns an object for each face found in the image - in this case, three. Here's a clipped version of our response:

```json
{
      "faceAnnotations": [
        {
          "boundingPoly": {
            "vertices": [
              {
                "x": 669,
                "y": 324
              },
              ...
            ]
          },
          "fdBoundingPoly": {
            ...
          },
          "landmarks": [
            {
              "type": "LEFT_EYE",
              "position": {
                "x": 692.05646,
                "y": 372.95868,
                "z": -0.00025268539
              }
            },
            ...
          ],
          "rollAngle": 0.21619819,
          "panAngle": -23.027969,
          "tiltAngle": -1.5531756,
          "detectionConfidence": 0.72354823,
          "landmarkingConfidence": 0.20047489,
          "joyLikelihood": "POSSIBLE",
          "sorrowLikelihood": "VERY_UNLIKELY",
          "angerLikelihood": "VERY_UNLIKELY",
          "surpriseLikelihood": "VERY_UNLIKELY",
          "underExposedLikelihood": "VERY_UNLIKELY",
          "blurredLikelihood": "VERY_UNLIKELY",
          "headwearLikelihood": "VERY_LIKELY"
        }
        ...
     }
}
```

The `boundingPoly` gives us the x,y coordinates around the face in the image. `fdBoundingPoly` is a smaller box than `boundingPoly`, encodling on the skin part of the face. `landmarks` is an array of objects for each facial feature (some you may not have even known about!). This tells us the type of landmark, along with the 3D position of that feature (x,y,z coordinates) where the z coordinate is the depth. The remaining values gives us more details on the face, including the likelihood of joy, sorrow, anger, and surprise. The object above is for the person furthest back in the image - you can see he's making kind of a silly face which explains the `joyLikelihood` of `POSSIBLE`.

Next let's look at the `landmarkAnnotations` part of our response:

```json
"landmarkAnnotations": [
        {
          "mid": "/m/0c7zy",
          "description": "Petra",
          "score": 0.5689378,
          "boundingPoly": {
            "vertices": [
              {
                "x": 169,
                "y": 46
              },
              ...
            ]
          },
          "locations": [
            {
              "latLng": {
                "latitude": 30.323975,
                "longitude": 35.449361
              }
            }
          ]
```

Here, __the Vision API was able to tell that this picture was taken in Petra__ - this is pretty impressive given the visual clues in this image are minimal. The values in this response should look similar to the `labelAnnotations` response above.

We get the `mid` of the landmark, its name (`description`), along with a confidence `score`. `boundingPoly` shows the region in the image where the landmark was identified. The `locations` key tells us the latitude longitude coordinates of  [this landmark](https://www.google.com/?ion=1&espv=2#q=30.323975%2C%2035.449361).


## Explore other Vision API methods

We've looked at the Vision API's label, face, and landmark detection methods, but there are others we haven't explored. Dive into [the docs](https://cloud.google.com/vision/reference/rest/v1/images/annotate#Feature) to learn more, including:

* __Logo detection__: identify common logos and their location in an image.
* __Safe search detection__: determine whether or not an image contains explicit content. This is useful for any application with user-generated content. You can filter images based on four factors: adult, medical, violent, and spoof content.
* __Text detection__: run OCR to extract text from images. This method can even identify the language of text present in an image.


## Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You've learned how to analyze images with the Vision API. In this example you passed the API the URLs of your images. Alternatively, you can pass a base64 encoded string of your image.

#### What we've covered

* Calling the Vision API with curl by passing it the URL of an image in a Cloud Storage bucket
* Using the Vision API's __label__, __web__, __face__, and __landmark__ detection methods

#### Next Steps

* Check out the Vision API  [tutorials](https://cloud.google.com/vision/docs/tutorials) in the documentation
* Find a  [Vision API sample](https://github.com/googlecloudplatform/cloud-vision) in your favorite language on GitHub
* Try out the  [Speech API](https://codelabs.developers.google.com/codelabs/cloud-speech-intro/index.html?index=..%2F..%2Findex#0) and  [Natural Language API](https://codelabs.developers.google.com/codelabs/cloud-nl-intro) codelabs!


