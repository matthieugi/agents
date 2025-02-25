import sys
import os
import pandas as pd

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, process

dataset = pd.read_json("./evaluation/generated_datasets/insurance_simulated_dataset_fr.jsonl", lines=True).to_dict(orient="records")
results = []

with app.app_context():
    for element in dataset:
        response = process(user_query=element['query'], user_id="matthieu")
        results.append({
            "query": element['query'],
            "response": response['content'],
            "ground_truth": element['ground_truth']
        })

df = pd.DataFrame(results)
with open("evaluation/generated_datasets/insurance_evaluation_dataset.jsonl", "w") as f:
    f.write(df.to_json(orient="records", lines=True, force_ascii=False))

