# Classify Text into Categories with the Natural Language API

## Overview

The Cloud Natural Language API lets you extract entities from text, perform sentiment and syntactic analysis, and classify text into categories. In this lab, we'll focus on text classification. Using a database of 700+ categories, this API feature makes it easy to classify a large dataset of text.

What you'll learn:

* Creating a Natural Language API request and calling the API with curl
* Use the NL API's text classification feature
* Use text classification to understand a dataset of news articles

![Natural Language API logo](https://storage.googleapis.com/aju-dev-demos-codelabs/images/NaturalLanguage_Retina_sm.png)

**Time to complete**: About 30 minutes

Click the **Continue** button to move to the next step.


## Create an API Key

Since we'll be using curl to send a request to the Natural Language API, we'll need to generate an API key to pass in our request URL.

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

Next, you'll enable the Natural Language API for your project, if you've not already done so.

## Enable the Natural Langage API

Click on [this link](https://console.cloud.google.com/flows/enableapi?apiid=language.googleapis.com) to enable the Natural Language API for your project.

Next, you'll use the Natural Language API's `classifyText` method to classify a news article.

## Classify a news article

First, change to this directory in the cloud shell:

```bash
cd ~/code-snippets/ml/cloud_shell_tutorials/cloud-nl-text-classification
```

You'll remain in this directory for the rest of the tutorial.

Using the Natural Language API's `classifyText` method, we can sort our text data into categories with a single API call. This method returns a list of content categories that apply to a text document. These categories range in specificity, from broad categories like __/Computers & Electronics__ to highly specific categories such as __/Computers & Electronics/Programming/Java (Programming Language)__. A full list of the 700+ possible categories can be found  [here](https://cloud.google.com/natural-language/docs/categories).

We'll start by classifying a single article, and then we'll see how we can use this method to make sense of a large news corpus. To start, let's take this headline and description from a New York Times article in the food section:

> *A Smoky Lobster Salad With a Tapa Twist. This spin on the Spanish pulpo a la gallega skips the octopus, but keeps the sea salt, olive oil, pimentón and boiled potatoes.* 

Bring up the `request.json` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-text-classification/request.json" "in the text editor"`.

It should look like this:


```json
{
  "document":{
    "type":"PLAIN_TEXT",
    "content":"A Smoky Lobster Salad With a Tapa Twist. This spin on the Spanish pulpo a la gallega skips the octopus, but keeps the sea salt, olive oil, pimentón and boiled potatoes."
  }
}
```

We can send this text to the NL API's `classifyText` method with the following curl command:

```
curl "https://language.googleapis.com/v1/documents:classifyText?key=${API_KEY}" \
  -s -X POST -H "Content-Type: application/json" --data-binary @request.json
```

Notice that the curl command used the API key that you generated.

Let's take a look at the response:

```json
{ categories: 
  [ 
    { 
      name: '/Food & Drink/Cooking & Recipes',
       confidence: 0.85 
    },
    { 
       name: '/Food & Drink/Food/Meat & Seafood',
       confidence: 0.63 
     }
  ] 
}
```

The API returned 2 categories for this text: **/Food & Drink/Cooking & Recipes** and **/Food & Drink/Food/Meat & Seafood**. The text doesn't explicitly mention that this is a recipe or even that it includes seafood, but the API is able to categorize it for us!

Classifying a single article is cool, but to really see the power of this feature we should classify lots of text data. We'll do that next.

## Classifying a large text dataset


To see how the `classifyText` method can help us understand a dataset with lots of text, we'll use this  [public dataset](http://mlg.ucd.ie/datasets/bbc.html) of BBC news articles. The dataset consists of 2,225 articles in five topic areas (business, entertainment, politics, sport, tech) from 2004 - 2005. We've put a subset of these articles into a public [Google Cloud Storage](https://cloud.google.com/storage/) (GCS) bucket. Each of the articles is in a `.txt` file. 

To examine the data and send it to the NL API, we'll write a Python script to read each text file from GCS, send it to the `classifyText` endpoint, and store the results in a [BigQuery](https://cloud.google.com/bigquery/) table. BigQuery is Google Cloud's big data warehouse tool - it lets us easily store and analyze large datasets. 

To see the type of text we'll be working with, run the following command to view one article (`gsutil` provides a command line interface for GCS):

```bash
gsutil cat gs://text-classification-codelab/bbc_dataset/entertainment/001.txt
```

Next we'll create a BigQuery table for our data.


## Creating a BigQuery table for our categorized text data


Before we send the text to the Natural Language API, we need a place to store the text and category for each article - enter BigQuery! Navigate to the BigQuery web UI in your console:

![Navigate to the BigQuery web UI](https://storage.googleapis.com/aju-dev-demos-codelabs/images/bigquery1.png)

Then click on the dropdown arrow next to your project name and select __Create new dataset__: 

![Create a new BigQuery dataset](https://storage.googleapis.com/aju-dev-demos-codelabs/images/bigquery2.png)

Name your dataset `news_classification`. You can leave the defaults in the **Data location** and **Data expiration** fields:

![Name your new dataset](https://storage.googleapis.com/aju-dev-demos-codelabs/images/bigquery3.png)

Click on the dropdown arrow next to your dataset name and select __Create new table__. Under Source Data, select "Create empty table". Then name your table __article_data__ and give it the following 3 fields in the schema:

![Create a new table](https://storage.googleapis.com/aju-dev-demos-codelabs/images/bigquery4.png)

After creating the table you should see the following:

![New table details](https://storage.googleapis.com/aju-dev-demos-codelabs/images/bigquery5.png)

Our table is empty right now. In the next step we'll read the articles from Google Cloud Storage, send them to the NL API for classification, and store the result in BigQuery.


## Classifying news data and storing the result in BigQuery


Before we write a script to send the news data to the NL API, we need to create a service account. We'll use this to authenticate to the NL API and BigQuery from our Python script. First, export the name of your Cloud project as an environment variable:

```bash
export PROJECT=<your_project_name>
```

Then run the following commands from Cloud Shell to create a service account:

```bash
gcloud iam service-accounts create my-account --display-name my-account
gcloud projects add-iam-policy-binding $PROJECT --member=serviceAccount:my-account@$PROJECT.iam.gserviceaccount.com --role=roles/bigquery.admin
gcloud iam service-accounts keys create key.json --iam-account=my-account@$PROJECT.iam.gserviceaccount.com
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

Now we're ready to send the text data to the NL API. To do that we'll use a Python script using the Python module for Google Cloud (note that you could accomplish the same thing from many other languages; there are many different cloud  [client libraries](https://cloud.google.com/apis/docs/cloud-client-libraries)). 

Bring up the `classify-text.py` file
`walkthrough editor-open-file "code-snippets/ml/cloud_shell_tutorials/cloud-nl-text-classification/classify-text.py" "in the text editor"`, and in the code, **replace `YOUR_PROJECT`** with the name of your project.

The file looks like this:

```python
from google.cloud import storage, language, bigquery

# Set up our GCS, NL, and BigQuery clients
storage_client = storage.Client()
nl_client = language.LanguageServiceClient()
# TODO: replace YOUR_PROJECT with your project name below
bq_client = bigquery.Client(project='YOUR_PROJECT')

dataset_ref = bq_client.dataset('news_classification')
dataset = bigquery.Dataset(dataset_ref)
table_ref = dataset.table('article_data')
table = bq_client.get_table(table_ref)

# Send article text to the NL API's classifyText method
def classify_text(article):
        response = nl_client.classify_text(
                document=language.types.Document(
                        content=article,
                        type=language.enums.Document.Type.PLAIN_TEXT
                )
        )
        return response


rows_for_bq = []
files = storage_client.bucket('text-classification-codelab').list_blobs()
print("Got article files from GCS, sending them to the NL API (this will take ~2 minutes)...")

# Send files to the NL API and save the result to send to BigQuery
for file in files:
        if file.name.endswith('txt'):
                article_text = file.download_as_string()
                nl_response = classify_text(article_text)
                if len(nl_response.categories) > 0:
                        rows_for_bq.append((article_text, nl_response.categories[0].name, nl_response.categories[0].confidence))

print("Writing NL API article data to BigQuery...")
# Write article text + category data to BQ
errors = bq_client.create_rows(table, rows_for_bq)
assert errors == []
```

We're ready to start classifying articles and importing them to BigQuery. Run the `classify-text.py` script like this:

```bash
python classify-text.py
```

The script takes about two minutes to complete, so while it's running we'll discuss what's happening. 

We're using the `google-cloud` [Python client library](https://googlecloudplatform.github.io/google-cloud-python/) to access Google Cloud Storage, the NL API, and BigQuery. First we create a client for each service we'll be using, and then we create references to our BigQuery table. 

`files` is a reference to each of the BBC dataset files in the public bucket. We iterate through these files, download the articles as strings, and send each one to the NL API's in our `classify_text` function. For all articles where the NL API returns a category, we save the article and its category data to a `rows_for_bq` list. When we're done classifying each article, we insert our data into BigQuery using `create_rows()`.

When your script has finished running, it's time to verify that the article data was saved to BigQuery. Navigate to your `article_data` table in the BigQuery web UI and click __Query Table__:

![Query your new BigQuery table](https://storage.googleapis.com/aju-dev-demos-codelabs/images/bigquery6.png)

Enter the following query in the **Compose Query** box, **first replacing `YOUR_PROJECT`** with your project name:

```sql
#standardSQL
SELECT * FROM `YOUR_PROJECT.news_classification.article_data`
```

You should see your data when the query completes. The `category` column has the name of the first category the NL API returned for our article, and `confidence` is a value between 0 and 1 indicating how confident the API is that it categorized the article correctly. 

We'll learn how to perform more complex queries on the data in the next step.


## Analyzing categorized news data in BigQuery


First, let's see which categories were most common in our dataset. Enter the following query in the **Compose Query** box, **replacing `YOUR_PROJECT`** with your project name:

```sql
#standardSQL
SELECT 
  category, 
  COUNT(*) c 
FROM 
  `YOUR_PROJECT.news_classification.article_data` 
GROUP BY 
  category 
ORDER BY 
  c DESC
```

You should see something like this in the query results:

![Query results](https://storage.googleapis.com/aju-dev-demos-codelabs/images/query_results.png)

Let's say we wanted to find the article returned for a more obscure category like **/Arts & Entertainment/Music & Audio/Classical Music**. We could write the following query (again, replace `YOUR_PROJECT` first):

```sql
#standardSQL
SELECT * FROM `YOUR_PROJECT.news_classification.article_data`
WHERE category = "/Arts & Entertainment/Music & Audio/Classical Music"
```

Or, we could get only the articles where the NL API returned a confidence score greater than 90% (again, replace `YOUR_PROJECT` first):

```sql
#standardSQL
SELECT 
  article_text, 
  category 
FROM `YOUR_PROJECT.news_classification.article_data` 
WHERE cast(confidence as float64) > 0.9
```

To perform more queries on your data, explore the [BigQuery documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-and-operators). BigQuery also integrates with a number of visualization tools. To create visualizations of your categorized news data, check out the  [Data Studio quickstart](https://cloud.google.com/bigquery/docs/visualize-data-studio) for BigQuery. Here's an example of a Data Studio chart we could create for the query above:

![Example Data Studio chart](https://storage.googleapis.com/aju-dev-demos-codelabs/images/data_studio.png)


## Congratulations!

`walkthrough conclusion-trophy`

You've learned how to use the Natural Language API's text classification method to classify news articles. You started by classifying one article, and then learned how to classify and analyze a large news dataset using the NL API with BigQuery.

#### What we've covered

* Creating a NL API `classifyText` request and calling the API with curl
* Using the google-cloud Python module to analyze a large news dataset
* Importing and analyzing data in BigQuery

#### Some next steps

* Try the  [NL API intro lab](https://google.qwiklabs.com/focuses/6890) to learn about other NL API methods
* Check out the  [docs for classifying content](https://cloud.google.com/natural-language/docs/classifying-text) with the NL API
* Learn more about BigQuery in the  [documentation](https://cloud.google.com/bigquery/quickstart-web-ui)

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
