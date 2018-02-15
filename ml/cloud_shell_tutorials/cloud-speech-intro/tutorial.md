# Speech to Text Transcription with the Cloud Speech API

[Codelab Feedback](https://github.com/googlecodelabs/feedback/issues/new?title=[cloud-speech-intro]:&labels[]=content-platform&labels[]=cloud)


## Overview

*Duration is 1 min*


The Cloud Speech API lets you do speech to text transcription from audio files in over 80 languages.

In this lab, we will record an audio file and send it to the Cloud Speech API for transcription.

#### What you'll learn

* Creating a Speech API request and calling the API with curl
* Calling the Speech API with audio files in different languages

#### What you'll need

* A Google Cloud Platform Project
* A Browser, such  [Chrome](https://www.google.com/chrome/browser/desktop/) or  [Firefox](https://www.mozilla.org/firefox/)


## Create an API Key

*Duration is 2 min*


Since we'll be using curl to send a request to the Speech API, we'll need to generate an API key to pass in our request URL. To create an API key, navigate to the API Manager section of your project dashboard:

![8cbae8dc9ba56e1e.png](img/8cbae8dc9ba56e1e.png)

Then, navigate to the __Credentials__ tab and click __Create credentials__:

![fc9b83db953a127a.png](img/fc9b83db953a127a.png)

In the drop down menu, select __API key__:

![bc4940935c1bef7f.png](img/bc4940935c1bef7f.png)

Next, copy the key you just generated.

Now that you have an API key, save it to an environment variable to avoid having to insert the value of your API key in each request. You can do this in Cloud Shell. Be sure to replace `<your_api_key>` with the key you just copied.

```
export API_KEY=<YOUR_API_KEY>
```


## Create your Speech API request

*Duration is 2 min*


You can build your request to the speech API in a `request.json` file. First create this file in Cloud Shell:

```
touch request.json
```

Open it using your preferred command line editor (`nano`, `vim`, `emacs`). Add the following to your `request.json` file, replacing the `uri` value with the uri of your raw audio file:

#### __request.json__

```
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

In the `audio` object, you pass the API the uri of our audio file in Cloud Storage. Now you're ready to call the Speech API!


## Call the Speech API

*Duration is 1 min*


You can now pass your request body, along with the API key environment variable you saved earlier, to the Speech API with the following `curl` command (all in one single command line):

```
curl -s -X POST -H "Content-Type: application/json" --data-binary @request.json \
"https://speech.googleapis.com/v1beta1/speech:syncrecognize?key=${API_KEY}"
```

Your response should look something like the following:

```
{
  "results": [
    {
      "alternatives": [
        {
          "transcript": "how old is the Brooklyn Bridge",
          "confidence": 0.98267895
        }
      ]
    }
  ]
}
```

The `transcript` value will return the Speech API's text transcription of your audio file, and the `confidence` value indicates how sure the API is that it has accurately transcribed your audio.

You'll notice that we called the `syncrecognize` method in our request above. The Speech API supports both synchronous and asynchronous speech to text transcription. In this example we sent it a complete audio file, but you can also use the `syncrecognize` method to perform streaming speech to text transcription while the user is still speaking.


## Speech to text transcription in different languages

*Duration is 2 min*


Are you multilingual? The Speech API supports speech to text transcription in over 80 languages! You can change the `language_code` parameter in `request.json`. You can find a list of supported languages  [here](https://cloud.google.com/speech/docs/languages).

For example, if you had a Spanish audio file, you can set the `language_code` attributes in the `request.json` file like this:

#### __request.json__

```
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




You've learned how to perform speech to text transcription with the Speech API. In this example you passed the API the Google Cloud Storage URI of your audio file. Alternatively, you can pass a base64 encoded string of your audio content.

#### __What we've covered__

* Passing the Speech API a Google Cloud Storage URI of an audio file
* Creating a Speech API request and calling the API with curl
* Calling the Speech API with audio files in different languages

#### Next Steps

* Check out the Speech API  [tutorials](https://cloud.google.com/speech/docs/tutorials) in the documentations.
* Try out the  [Vision API](https://cloud.google.com/vision/) and  [Natural Language API](https://cloud.google.com/natural-language/)!


