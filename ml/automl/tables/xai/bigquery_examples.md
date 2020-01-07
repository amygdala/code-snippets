
# Examples of inspecting the "bikes and weather" test dataset in BigQuery


AutoML Tables allows you to [export a model's test dataset to BigQuery](https://cloud.google.com/automl-tables/docs/evaluate#downloading_your_test_dataset_to) after training.  This makes it easy to do some additional poking around in a sample of the dataset— even if it didn't originally reside in BigQuery. This can be helpful, for example, if your model's explanations of predictions suggest some interesting characteristics of the data.
(See the "Use your trained model to make predictions and see explanations of the results" section of [automl_tables_xai.ipynb](automl_tables_xai.ipynb).

Here are a few examples queries.
In the following, replace `your-project` and `your-dataset` with the appropriate values. (The exported table should be named `evaluated_examples`, but if not, edit that value as well.)

1. Find the average predicted and actual ride durations for the day of the week (in this dataset, 1 & 7 are weekends).

```sql
SELECT day_of_week, avg(predicted_duration[offset(0)].tables.value) as ad, avg(duration) as adur
FROM `your-project.your-dataset.evaluated_examples`
where euclidean > 0 group by day_of_week
order by adur desc
limit 10000
```

2. Find the average predicted and actual ride durations for those rides where the max temperature was > 70F or < 40F.

```sql
SELECT max, avg(predicted_duration[offset(0)].tables.value) as ad, avg(duration) as adur
FROM `your-project.your-dataset.evaluated_examples`
where euclidean > 0 and (max > 70 or max < 40) group by max
order by adur desc
limit 10000
```

3. Show the starting stations for rides as ordered by greatest standard deviation in prediction accuracy. 

```sql
SELECT start_station_id, stddev(predicted_duration[offset(0)].tables.value - duration) as sd, avg(predicted_duration[offset(0)].tables.value - duration) as ad
FROM `your-project.your-dataset.evaluated_examples`
where euclidean > 0 group by start_station_id
order by sd desc
limit 1000
```