import sys
import os
import pandas as pd
from azure.core.settings import settings

settings.tracing_implementation = "opentelemetry"

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.advice import advice

dataset = pd.read_json("./evaluation/generated_datasets/insurance_simulated_dataset_fr.jsonl", lines=True).to_dict(orient="records")
results = []

for element in dataset:
    messages = [
        { "role": "system", "content": "empty" },
        { "role": "user", "content": element['query'] }
    ]

    response = advice(messages)

    results.append({
        "query": element['query'],
        "response": response['advices'],
        "ground_truth": element['ground_truth']
    })

df = pd.DataFrame(results)
with open("evaluation/generated_datasets/insurance_advice_evaluation_dataset.jsonl", "w") as f:
    f.write(df.to_json(orient="records", lines=True, force_ascii=False))

