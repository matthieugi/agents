import os
from datetime import datetime

from opentelemetry.trace import get_tracer

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

tracer = get_tracer(__name__)

_project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())


_agent_client = _project.inference.get_azure_openai_client(
  api_version=os.environ.get('AZURE_OPENAI_API_VERSION'),

)

advice_agent = {
    "type": "function",
    "function": {
        "name": "advice",
        "description": "Propose des conseils supplémentaires pour le client dans le cas de la pratique de sports ou d'activités à risque, de voyages à l'étranger ou de la possession d'animaux de compagnie.",
    }
}

@tracer.start_as_current_span(name="conseil")
def advice(messages):
    f"""
    Devis pour un plan d'assurance habitation ou voiture

    Args:
        userId (str): L'identifiant de l'utilisateur
        type (str): Le type d'assurance, les valeurs peuvent être "voiture" ou "habitation"

    Returns:
        dict: 
    """

    return "Keep the smile"
