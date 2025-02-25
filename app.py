import os

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.inference.prompts import PromptTemplate
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.core.settings import settings
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

settings.tracing_implementation = "opentelemetry"
AIInferenceInstrumentor().instrument(enable_content_recording=True)

from services.quote import quote_agent, quote
from services.attestation import attestation_agent, attestation
from services.advice import advice_agent, advice


project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

# Enable instrumentation of AI packages (inference, agents, openai, langchain)
project.telemetry.enable()

# Log traces to the project's application insights resource
application_insights_connection_string = project.telemetry.get_connection_string()
if application_insights_connection_string:
    configure_azure_monitor(connection_string=application_insights_connection_string)


ai_chat_client = project.inference.get_azure_openai_client(
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

orchestrator_tools = [
    quote_agent,
    attestation_agent,
    advice_agent
]

answer_system_prompt = PromptTemplate.from_string(prompt_template="""
    assistant:
        You are an AI assistant that can provide a response to the user's query.
        Use the user query and the assistant responses to generate the response.
        If you are not able to generate a response, aswer that your current capabilities do not allow you to response the user intent.
        Use only the contextual data to answer the user query.
    
    history:
        {{messages}}

    assistant:
        {{assistant_answers}}

    user:
        {{user_query}}
    """)


@tracer.start_as_current_span(name="orchestrator")
# Fonction pour traiter la requête
def process_query(user_id, user_query):
    messages = orchestrator_system_prompt.create_messages(user_query=user_query)
    
    orchestrator_client_response = ai_chat_client.chat.completions.create(
        messages=messages,
        tools=orchestrator_tools,
        model=os.environ.get('AZURE_CHAT_DEPLOYMENT')
    )

    orchestrator_response_message = orchestrator_client_response.choices[0].message

    if not orchestrator_response_message.tool_calls:
        return orchestrator_response_message

    assistants_answers = []
    
    for tool in orchestrator_response_message.tool_calls:
        function_name = tool.function.name

        match function_name:
            case 'quote':
                assistants_answers.append(quote(user_id, messages))
            case 'attestation':
                assistants_answers.append(attestation(messages))
            case 'advice':
                assistants_answers.append(advice(messages))
    
    answer_messages = answer_system_prompt.create_messages(
        messages=messages,
        assistant_answers=assistants_answers,
        user_query=user_query
    )

    answer_client_response = ai_chat_client.chat.completions.create(
        messages=answer_messages,
        model=os.environ.get('AZURE_CHAT_DEPLOYMENT')
    )

    answer_client_message = answer_client_response.choices[0].message.content

    return answer_client_message


user_query = "je cherche à faire assurer ma nouvelle maison pour y héberger mes 6 chiens, quelles sont les garanties possibles et combien cela me couterait-il ?"
result = process_query('matthieu', user_query)
print(result)

# user_query = "je veux une attestation d'assurance"
# result = process_query('matthieu', user_query)
# print(result)

# user_query = "je fais du parapente, avez-vous des conseils ?"
# result = process_query('matthieu', user_query)
# print(result)