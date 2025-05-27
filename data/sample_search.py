import uuid
import json
import logging
import os

from openai import AzureOpenAI

from azure.core.settings import settings
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, VectorizedQuery
from azure.ai.projects import AIProjectClient

settings.tracing_implementation = "opentelemetry"

project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

openai_client = project.inference.get_azure_openai_client(
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION')
)

seach_connection = project.connections.get(
    connection_name=os.environ.get('AZURE_SEARCH_CONNECTION_NAME_2'),
    include_credentials=True
)

index_name = os.environ.get('AZURE_SEARCH_INDEX_HACK')

search_index_client = SearchClient(
    endpoint=seach_connection.endpoint_url, 
    credential=AzureKeyCredential(seach_connection.key),
    index_name=index_name)

query = "I need to a payment solution, what company would you recommend ?"

# search_results = search_index_client.search(
#     search_text=query,
#     top=1,
#     select="company",
#     query_type=QueryType.SIMPLE,
#     query_language="en-us",
# )

def generate_embeddings(query):
    response = openai_client.embeddings.create(
        input=query,
        model=os.environ.get('AZURE_OPENAI_EMBEDDING_DEPLOYMENT'),
    )
    return response.data[0].embedding

query_vector = VectorizedQuery(
    vector=generate_embeddings(query),
    fields="description_vector"
)

# search_results = search_index_client.search(
#     vector_queries=[query_vector],
#     top=1
# )

# search_results = search_index_client.search(
#     search_text=query,
#     vector_queries=[query_vector],
#     top=1,
#     query_language="en-us",
# )

search_results = search_index_client.search(
    search_text=query,
    vector_queries=[query_vector],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name="default",
    query_caption="extractive",
    query_answer="extractive",
    top=2,
    query_language="en-us",
)

# for result in search_results:
#     print(f"Company: {result['company']}")

#     # Semantic Ranker Caption results (not used in simple or vector queries)
#     if result.get("@search.captions"):
#         caption = result["@search.captions"][0]
#         print(f"Caption: { caption.highlights }")

from azure.ai.inference.prompts import PromptTemplate

prompt_template = PromptTemplate.from_string(prompt_template="""
    system:
        You are an AI assistant that helps customer fiding the best company for their use case.
        Provide answers only based to the documents provided
                                                   
        Here are the documents provided:
        {{documents}}
    user:
        {{user_query}}
    """)

documents = [
    (f"Company : { result['company'] } Description : { result['description'] }") 
    for result in search_results
]

prompt = prompt_template.create_messages(
    documents=documents,
    user_query=query
)

# print(prompt)

answer = openai_client.chat.completions.create(
    messages=prompt,
    model=os.environ.get('AZURE_CHAT_DEPLOYMENT')
)

print(answer.choices[0].message.content)