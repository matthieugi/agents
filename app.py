import os

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.inference.prompts import PromptTemplate

from services.quote import quote_agent, quote
from services.attestation import attestation_agent, attestation
from services.advice import advice_agent, advice


project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())


orchestrator_client = project.inference.get_azure_openai_client(
  api_version=os.environ.get('AZURE_OPENAI_API_VERSION'),

)

orchestrator_system_prompt = PromptTemplate.from_string(prompt_template="""
    assistant:
        You are an AI assistant that helps classify user requests 
        If you are able to classify the user request, levereage the appropriate tool.
        If you are unable to classify the user request or do not have the necessary information, respond with "None".
        

    user:                                                        
    {{user_query}}
    """)

tools = [
    quote_agent,
    attestation_agent,
    advice_agent
]

# Fonction pour traiter la requête
def process_query(user_id, user_query):
    messages = orchestrator_system_prompt.create_messages(user_query=user_query)
    
    client_response = orchestrator_client.chat.completions.create(
        messages=messages,
        tools=tools,
        model=os.environ.get('AZURE_CHAT_DEPLOYMENT')
    )

    assistant_message = client_response.choices[0].message

    if not assistant_message.tool_calls:
        return assistant_message

    
    for tool in assistant_message.tool_calls:
        function_name = tool.function.name
        result = None

        match function_name:
            case 'quote':
                result = quote(user_id, messages)
                messages.append({"role": "assistant", "content": result})
            case 'attestation':
                result = attestation(user_id, messages)
                messages.append({"role": "assistant", "content": result})
            case 'advice':
                result = advice(messages)
                messages.append({"role": "assistant", "content": result})

    return result


user_query = "je cherche à faire assurer ma nouvelle maison"
result = process_query('matthieu', user_query)
print(result)

user_query = "je veux une attestation d'assurance"
result = process_query('matthieu', user_query)
print(result)

user_query = "je fais du parapente, avez-vous des conseils ?"
result = process_query('matthieu', user_query)
print(result)