This is a demo project for BERT based fake review classification on YELP Dataset

We released two version:

1. BERT based model with a classifier header.
2. BERT based model with a classifier header with rating input


I will upload the data source later, if there is no copy right issue, I will directly upload the data. I will also upload the following model checkpoint:
src\model.pkl: checkpoint for Model 2 above.

Following are the scores we achieved when we trained model on ZIP dataset

| Dataset | Recall | Precision | Accuracy | F1   |
|---------|--------|-----------|----------|------|
| YelpZIP | 0.74   | 0.74      | 0.74     | 0.74 |
| YelpNYC | 0.68   | 0.68      | 0.68     | 0.68 |
| YelpCHI | 0.64   | 0.64      | 0.64     | 0.64 |