#!/usr/bin/env python
# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import os
import logging

from flask import Flask, request

from googleapiclient import discovery
from googleapiclient import errors
from oauth2client.client import GoogleCredentials
import requests
import twilio.twiml
from twilio.twiml.messaging_response import MessagingResponse

logging.getLogger().setLevel(logging.INFO)


DISCOVERY_URL = 'https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'  # noqa
ACCEPTABLE_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
DEFAULT_PRETEXT = ("Your message has been passed to the Google Cloud "
                   "Vision API for processing.\n Images are not stored in "
                   "Google Cloud Platform, and will periodically need to be "
                   "deleted from Twilio.")
PRETEXT = os.environ.get('MESSAGE_BLURB', DEFAULT_PRETEXT)


app = Flask(__name__)
app.debug = True


@app.route("/", methods=['GET', 'POST'])
def receive_message():
    """Run a label request on an image received from Twilio"""

    resp = MessagingResponse()

    attachments = int(request.values.get('NumMedia', 0))
    if not attachments:
        response_text = "No media attachments found."
        resp.message(response_text)
        return str(resp)

    # Process media attachments
    for i in range(attachments):

        media_content_type = request.values.get('MediaContentType%i' % i, None)

        # First, check to see if we can use the attachment
        if media_content_type in ACCEPTABLE_FILE_TYPES:

            # get the image
            media_url = request.values.get('MediaUrl%i' % i, None)
            image = requests.get(media_url).content

            # Query the API
            labels, face_annotations, logos = get_labels(image)
            logging.info("got labels %s", str(labels))
            # We're only looking at the first image
            break
        else:
            response_text = "We are not able to process this type of attachment."
            resp.message(response_text)
            return str(resp)

    # Construct the response
    resp = construct_message(labels, face_annotations, logos)
    return str(resp)


def construct_message(labels, face_annotations, logos):
    """Build up the response from the labels found"""

    # We'll use this to construct our response
    response_text = PRETEXT
    label_desc = ""
    pos_labels = ['very likely', 'likely', 'possibly']

    # Go through labels and turn them into text of the response
    for i in range(len(labels)):

        # We've got an answer! Let's tell them about it
        label_desc += '\nScore is %s for %s' % (labels[i]['score'],
                                                labels[i]['description'])

    for i in range(len(logos)):
        label_desc += '\nLogo score is %s for %s' % (logos[i]['score'],
                                                logos[i]['description'])

    joy, anger, sorrow, surprise = extract_sentiment(face_annotations)

    for i in range(len(pos_labels)):
        if joy[i] > 0:
            label_desc += '\nWe found %s people who are ' \
                '%s experiencing joy' % (joy[i], pos_labels[i])
        if anger[i] > 0:
            label_desc += '\nWe found %s people who are ' \
                '%s experiencing anger' % (anger[i], pos_labels[i])
        if sorrow[i] > 0:
            label_desc += '\nWe found %s people who are ' \
                '%s experiencing sorrow' \
                % (sorrow[i], pos_labels[i])
        if surprise[i] > 0:
            label_desc += '\nWe found %s people who are ' \
                '%s experiencing surprise' \
                % (surprise[i], pos_labels[i])

    # Add the prefix
    if not label_desc:
        label_desc = " No labels found."
    response_text += label_desc
    resp = MessagingResponse()
    resp.message(response_text)
    return resp


def extract_sentiment(emotions):
    """Extract the sentiment from the facial annotations"""
    joy = [0, 0, 0]
    sorrow = [0, 0, 0]
    anger = [0, 0, 0]
    surprise = [0, 0, 0]
    odds = ['VERY_LIKELY', 'LIKELY', 'POSSIBLE']

    # Loop through the emotions we're pulling and get the count
    for i in range(len(odds)):
        joy[i] = sum(f['joyLikelihood'] == odds[i] for f in emotions)
        anger[i] = sum(f['angerLikelihood'] == odds[i] for f in emotions)
        sorrow[i] = sum(f['sorrowLikelihood'] == odds[i] for f in emotions)
        surprise[i] = sum(f['surpriseLikelihood'] == odds[i] for f in emotions)

    return joy, anger, sorrow, surprise


def get_labels(image, num_retries=3, max_labels=3, max_faces=10, max_logos=1):
    """Given an image, execute the label request"""

    labels = ""
    face_annotations = ""
    logos = ""

    # Set up the service that can access the API
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('vision', 'v1', credentials=credentials,
                              discoveryServiceUrl=DISCOVERY_URL)

    # Prepare the image for the API
    image_content = base64.b64encode(image).decode('UTF-8')

    # Construct the request
    service_request = service.images().annotate(
        body={
            'requests': [{
                'image': {
                    'content': image_content
                },
                'features': [{
                    'type': 'LABEL_DETECTION',
                    'maxResults': max_labels,
                },
                    {
                    'type': 'FACE_DETECTION',
                    'maxResults': max_faces,
                },
                {
                    'type': 'LOGO_DETECTION',
                    'maxResults': max_logos,
                }]
            }]
        })

    # Send it off to the API
    try:
        response = service_request.execute(num_retries=num_retries)
        logging.info("got response: %s", str(response))

        if('responses' in response):
            if('labelAnnotations' in response['responses'][0]):
                labels = response['responses'][0]['labelAnnotations']
            if('logoAnnotations' in response['responses'][0]):
                logos = response['responses'][0]['logoAnnotations']
            if('faceAnnotations' in response['responses'][0]):
                face_annotations = response['responses'][0]['faceAnnotations']
    except KeyError as e2:
        logging.warn("Key error: %s", e2)
    except Exception as e:
        logging.warn(e)
    return labels, face_annotations, logos



if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
