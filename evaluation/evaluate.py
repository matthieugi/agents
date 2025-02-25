import json
import pathlib
import os
# set environment variables before importing any other code
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from pprint import pprint

from azure.core.settings import settings
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.evaluation import evaluate, RelevanceEvaluator, FluencyEvaluator, GroundednessEvaluator, CoherenceEvaluator, ViolenceEvaluator, SexualEvaluator, SelfHarmEvaluator, IndirectAttackEvaluator

settings.tracing_implementation = "opentelemetry"

project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

openai_client = project.inference.get_azure_openai_client(
  api_version=os.environ.get('AZURE_OPENAI_API_VERSION')
)

# Define helper methods
def load_jsonl(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f.readlines()]

def run_evaluation(eval_name, dataset_path):

    azure_ai_project = {
        "subscription_id": project.scope.get("subscription_id"),
        "resource_group_name": project.scope.get("resource_group_name"),
        "project_name": project.scope.get("project_name"),
    }

    model_config= {
        "azure_endpoint": f'https://{openai_client.base_url.host}',
        "azure_deployment": os.environ.get('AZURE_CHAT_DEPLOYMENT'),
        "api_key": openai_client.api_key,
    }

    # Initializing Evaluators
    groundedness_eval = GroundednessEvaluator(model_config)
    relevance_eval = RelevanceEvaluator(model_config)
    fluency_eval = FluencyEvaluator(model_config)
    coherence_eval = CoherenceEvaluator(model_config)
    
    violence_eval = ViolenceEvaluator(azure_ai_project=azure_ai_project, credential=DefaultAzureCredential())
    sexual_eval = SexualEvaluator(azure_ai_project=azure_ai_project, credential=DefaultAzureCredential())
    self_harm_eval = SelfHarmEvaluator(azure_ai_project=azure_ai_project, credential=DefaultAzureCredential())
    indirect_attack_eval = IndirectAttackEvaluator(azure_ai_project=azure_ai_project, credential=DefaultAzureCredential())


    # #custom eval
    # friendliness_eval = FriendlinessEvaluator()
    # #completeness_eval = CompletenessEvaluator(model_config)
    
    # Evaluate the default vs the improved system prompt to see if the improved prompt
    # performs consistently better across a larger set of inputs
    path = str(pathlib.Path.cwd() / dataset_path)

    output_path = str(pathlib.Path.cwd() / "evaluation/generated_datasets/insurance_global_evaluation_results_fr.jsonl")

    result = evaluate(
        evaluation_name=eval_name,
        data=path,
        evaluators={
            "groundedness": groundedness_eval,
            "relevance": relevance_eval,
            "fluency": fluency_eval,
            "coherence": coherence_eval,
            "violence": violence_eval,
            "sexual": sexual_eval,
            "self_harm": self_harm_eval,
            "indirect_attack": indirect_attack_eval,
        },
        evaluator_config={
            "groundedness": {
                "column_mapping": {
                    "query": "${data.query}",
                    "context": "${data.ground_truth}",
                    "response": "${data.response}"
                }
            },
            "relevance": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "fluency": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "coherence": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "violence": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "sexual": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "self_harm": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}"
                }
            },
            "indirect_attack": {
                "column_mapping": {
                    "query": "${data.query}",
                    "response": "${data.response}",
                    "context": "${data.ground_truth}"
                }
            },
        },
        azure_ai_project=azure_ai_project
    )
    
    tabular_result = pd.DataFrame(result.get("rows"))
    tabular_result.to_json(output_path, orient="records", lines=True) 

    return result, tabular_result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-name", help="evaluation name used to log the evaluation to AI Studio", type=str)
    parser.add_argument("--dataset-path", help="Test dataset to use with evaluation", type=str)
    args = parser.parse_args()

    evaluation_name = args.evaluation_name if args.evaluation_name else "test-sdk-copilot"
    dataset_path = args.dataset_path if args.dataset_path else "./evaluation/evaluation_dataset_small.jsonl"

    result, tabular_result = run_evaluation(eval_name=evaluation_name,
                              dataset_path=dataset_path)

    pprint("-----Summarized Metrics-----")
    pprint(result["metrics"])
    pprint("-------Tabular Result-------")
    pprint(tabular_result)
    pprint(f"View evaluation results in AI Studio: {result['studio_url']}")