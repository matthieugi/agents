import os
import json
from datetime import datetime
from opentelemetry.trace import get_tracer
from azure.identity import DefaultAzureCredential
from azure.ai.inference.prompts import PromptTemplate
from azure.ai.projects import AIProjectClient


tracer = get_tracer(__name__)

quote_agent = {
    "type": "function",
    "function": {
        "name": "quote",
        "description": "Devis pour un plan d'assurance habitation ou voiture",
    }
}

_generate_quote_tool = {
    "type": "function",
    "function": {
        "name": "generate_quote",
        "description": "Genère un devis pour un plan d'assurance habitation ou voiture",
        "parameters": {
            "type": "object",
            "properties": {
                "userId": {"type": "string"},
                "type": {"type": "string"},
                "date_debut": {"type": "string"}
            },
            "required": ["userId", "type"]
        }
    }
}


quote_system_prompt = PromptTemplate.from_string(prompt_template="""
    assistant:
        You are an AI assistant that is able to generate a quote for a home or car insurance plan.
        If you are able to generate a quote for the user, provide the quote.
                                                 
        Quote type can only be "voiture" or "habitation".

        If you are unable to generate a quote for the user or do not have the necessary information, with the missing information.
        
    user:                                                        
    {{messages}}
    """)


project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

quote_client = project.inference.get_azure_openai_client(
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION'),
    )

tools = [
    _generate_quote_tool
]

@tracer.start_as_current_span(name="quote")
def quote(user_id, messages):

    messages = quote_system_prompt.create_messages(messages=messages)

    client_response = quote_client.chat.completions.create(
        messages=messages,
        tools=tools,
        model=os.environ.get('AZURE_CHAT_DEPLOYMENT')
    )

    assistant_message = client_response.choices[0].message

    if not assistant_message.tool_calls:
        return assistant_message
    
    for tool in assistant_message.tool_calls:
        function_name = tool.function.name

        params = json.loads(tool.function.arguments)
        user_id = params.get("userId")
        type =  params.get("type") if params.get("type") in ["voiture", "habitation"] else None
        date_debut = params.get("date") if params.get("date") else datetime.now().strftime("%d-%m-%Y")

        results = []

        match function_name :
            case"generate_quote":
                results.append(generate_quote(user_id, type, date_debut))

    return results


def generate_quote(user_id, type, date_debut):
    f"""
    Devis pour un plan d'assurance habitation ou voiture

    Args:
        userId (str): L'identifiant de l'utilisateur
        type (str): Le type d'assurance, les valeurs peuvent être "voiture" ou "habitation"
        date_debut (str): La date de début de l'assurance au format JJ-MM-AAAA. Spécifiez la date du jour ${ datetime.now().strftime("%d-%m-%Y") } pour un début immédiat.

    Returns:
        dict: 
    """
    
    if not date_debut:
        date_debut = datetime.now().strftime("%d-%m-%Y")
    
    return {
        "status": "Quote Generated",
        "type": type,
        "date_debut": date_debut
    }
