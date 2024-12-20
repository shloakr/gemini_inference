# Happenstance Message Classification 

## flask_app
This is a Flask-based application that uses the Gemini 1.5 flash to generate responses to user messages. It includes a Redis cache layer to improve performance and avoid redundant API calls.

## classification_results
This directory contains the results of the classification process, on the test dataset. 
We achive super low inference times and high accuracy—around 96/7% after adjusting for inncorect ground truth labels.

## Research_Dump
This directory contains has a finetunes DistilBERT model for the classification task. My initial approach was to fine-tune a pretrained DistilBERT model, but I later switched to Gemini 1.5. DistilBERT did poorly on edge cases. 

To train DistilBERT, I used GPT o1 to generate syntheic data and achived ~80% accuracy on the test dataset.