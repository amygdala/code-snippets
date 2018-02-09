# Copyright 2018 Google Inc. All Rights Reserved. Licensed under the Apache
# License, Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

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
