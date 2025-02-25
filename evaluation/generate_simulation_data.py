import os
import asyncio
import json
from typing import List, Dict, Any, Optional

from azure.core.settings import settings
from azure.identity import DefaultAzureCredential
from azure.ai.evaluation.simulator import Simulator
from azure.ai.inference.tracing import AIInferenceInstrumentor 
from azure.ai.projects import AIProjectClient

import pandas as pd

settings.tracing_implementation = "opentelemetry"
AIInferenceInstrumentor().uninstrument()

project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

openai_client = project.inference.get_azure_openai_client(
  api_version=os.environ.get('AZURE_OPENAI_API_VERSION')
)

knwoledge_dataset = pd.read_json("./data/insurance/faq.json").to_dict(orient="records")

async def callback(
    messages: List[Dict],
    stream: bool = False,
    session_state: Any = None,  # noqa: ANN401
    context: Optional[Dict[str, Any]] = None,
) -> dict:
    return {
        "messages": messages["messages"],
        "stream": stream,
        "session_state": session_state,
        "context": context
    }

simulator = Simulator(
    model_config= {
        "azure_endpoint": f'https://{openai_client.base_url.host}',
        "azure_deployment": os.environ.get('AZURE_CHAT_DEPLOYMENT'),
        "api_key": openai_client.api_key,
    })

simulated_dataset = []

for element in knwoledge_dataset:
    knwoledge_data = element['chunk']

    simulator_questions = asyncio.run(
        simulator(
            target=callback,
            text=knwoledge_data,
            num_queries=3,
            max_conversation_turns=1,
            query_response_generating_prompty="evaluation/custom_simulation_prompt.prompty"
        )
    )

    for conversation in simulator_questions:
        context = conversation.get('context')

        query= context.get('query')
        expected_response = context.get('expected_response')
        original_text = context.get('original_text')

        simulated_dataset.append({
            "query": query,
            "ground_truth": original_text
        })

df = pd.DataFrame(simulated_dataset)
with open("evaluation/generated_datasets/insurance_simulated_dataset_fr.jsonl", "w") as f:
    f.write(df.to_json(orient="records", lines=True, force_ascii=False))