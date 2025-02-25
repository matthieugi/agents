import os

from opentelemetry.trace import get_tracer

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.ai.projects import AIProjectClient
from azure.ai.inference.prompts import PromptTemplate
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery

tracer = get_tracer(__name__)

_project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

_agent_client = _project.inference.get_azure_openai_client(
  api_version=os.environ.get('AZURE_OPENAI_API_VERSION'))

_search_connection = _project.connections.get(
    connection_name=os.environ.get('AZURE_SEARCH_CONNECTION_NAME'),
    include_credentials=True)

_search_client = SearchClient(
    endpoint=_search_connection.endpoint_url, 
    credential=AzureKeyCredential(_search_connection.key), 
    index_name=os.environ.get('AZURE_SEARCH_INDEX_NAME', 'insurance'))

advice_agent = {
    "type": "function",
    "function": {
        "name": "advice",
        "description": "Propose des conseils supplémentaires pour le client dans le cas de la pratique de sports ou d'activités à risque, de voyages à l'étranger ou de la possession d'animaux de compagnie.",
    }
}

advice_system_prompt = PromptTemplate.from_string(prompt_template="""
    system:
        You are an AI assistant that synthesizes advice for the user based on their query.
        Provide answers only based to the documents provided, if not clear advice is stated, respond with "None".
                                                  
        Here are the documents provided:
        {{documents}}

    user:
        {{user_query}}
    """)

@tracer.start_as_current_span(name="advice")
def advice(messages):
    user_query = messages[-1]['content']

    search_results = _search_client.search(
        search_text=user_query, 
        top=2,
        vector_queries=[VectorizableTextQuery(
            text=user_query, k_nearest_neighbors=5, fields="text_vector"
        )]
    )

    result = ""
    for r in search_results:
        result += f"[{r['title']}]: {r['chunk']}\n-----\n"

    query = advice_system_prompt.create_messages(messages=messages, documents=result, user_query=user_query)

    agent_answer = _agent_client.chat.completions.create(
        messages=query,
        model=os.environ.get('AZURE_CHAT_DEPLOYMENT'))

    return {
        "advices": agent_answer.choices[0].message.content
    }
