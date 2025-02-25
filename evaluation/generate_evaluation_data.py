import sys
import os
import pandas as pd

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, chat

dataset = pd.read_json("./data/dataset.jsonl", lines=True).to_dict(orient="records")
results = []

with app.app_context():
    for element in dataset:
        response, status = chat(query=element['query'])
        results.append({
            "query": element['query'],
            "response": response.json[len(response.json) - 1]['content'],
            "ground_truth": element['ground_truth'],
            "context": element['context']
        })

df = pd.DataFrame(results)
with open("evaluation/eval_results/generatedDataset.jsonl", "w") as f:
    f.write(df.to_json(orient="records", lines=True, force_ascii=False))

