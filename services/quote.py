import os
import json
from datetime import datetime
from opentelemetry.trace import get_tracer, get_current_span
from azure.identity import DefaultAzureCredential
from azure.ai.inference.prompts import PromptTemplate
from azure.ai.projects import AIProjectClient


tracer = get_tracer(__name__)


quote_agent = {
    "type": "function",
    "function": {
        "name": "quote",
        "description": "Quote for a home or car insurance plan",
    }
}

_generate_quote_tool = {
    "type": "function",
    "function": {
        "name": "generate_quote",
        "description": "Generate a quote for a home or car insurance plan",	
        "parameters": {
            "type": "object",
            "properties": {
                "userId": {"type": "string"},
                "type": {"type": "string"},
                "start_date": {"type": "string"}
            },
            "required": ["userId", "type"]
        }
    }
}


quote_system_prompt = PromptTemplate.from_string(prompt_template="""
    assistant:
        You are an AI assistant that is able to generate a quote for a home or car insurance plan.
        If you are able to generate a quote for the user, provide the quote.
                                                 
        Quote type can only be "car" or "home".

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
        return assistant_message.content
    
    results = []

    for tool in assistant_message.tool_calls:
        function_name = tool.function.name

        params = json.loads(tool.function.arguments)
        user_id = params.get("userId")
        type =  params.get("type") if params.get("type") in ["car", "home"] else None
        start_date = params.get("date") if params.get("date") else datetime.now().strftime("%d-%m-%Y")

        match function_name :
            case"generate_quote":
                results.append(generate_quote(user_id, type, start_date))

    return results

def generate_quote(user_id, type, start_date):
    f"""
    Devis pour un plan d'assurance habitation ou voiture

    Args:
        userId (str): L'identifiant de l'utilisateur
        type (str): Le type d'assurance, les valeurs peuvent être "voiture" ou "habitation"
        start_date (str): La date de début de l'assurance au format JJ-MM-AAAA. Spécifiez la date du jour ${ datetime.now().strftime("%d-%m-%Y") } pour un début immédiat.

    Returns:
        dict: 
    """

    
    if not start_date:
        start_date = datetime.now().strftime("%d-%m-%Y")

    span = get_current_span()
    span.set_attribute("userId", user_id)
    span.set_attribute("type", type)
    span.set_attribute("start_date", start_date)
    
    return {
        "status": "Quote Generated",
        "type": type,
        "start_date": start_date
    }

if __name__ == "__main__":
    quote(
        user_id="12345",
        messages=[
            {
                "role": "user",
                "content": "I would like to get a insurance quote for my new car, my user Id is 12345"
            }
        ]
    )