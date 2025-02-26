import uuid
import json
import logging
import os

from openai import AzureOpenAI

from azure.core.settings import settings
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.identity import AzureDeveloperCliCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.ai.projects import AIProjectClient
from azure.search.documents.indexes.models import (
    AzureOpenAIParameters,
    AzureOpenAIVectorizer,
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)

settings.tracing_implementation = "opentelemetry"

project = AIProjectClient.from_connection_string(
  conn_str=os.environ.get('AZURE_AI_PROJECT_CONNECTION_STRING'),
  credential=DefaultAzureCredential())

openai_client = project.inference.get_azure_openai_client(
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION')
)

seach_connection = project.connections.get(
    connection_name=os.environ.get('AZURE_SEARCH_CONNECTION_NAME'),
    include_credentials=True
)

search_index_client = SearchIndexClient(endpoint=seach_connection.endpoint_url, credential=AzureKeyCredential(seach_connection.key))

def setup_index(index_name, azure_openai_embedding_deployment):
    index_names = [index.name for index in search_index_client.list_indexes()]
    if index_name in index_names:
        logger.info(f"Index {index_name} already exists, not re-creating")
    else:
        logger.info(f"Creating index: {index_name}")
        search_index_client.create_index(
            SearchIndex(
                name=index_name,
                fields=[
                    SearchableField(name="chunk_id", key=True, analyzer_name="keyword", sortable=True),
                    SimpleField(name="category", type=SearchFieldDataType.String, filterable=True),
                    SearchableField(name="title"),
                    SearchableField(name="chunk"),
                    SearchField(
                        name="text_vector", 
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        vector_search_dimensions=EMBEDDINGS_DIMENSIONS,
                        vector_search_profile_name="vp",
                        stored=True,
                        hidden=False)
                ],
                vector_search=VectorSearch(
                    algorithms=[
                        HnswAlgorithmConfiguration(name="algo", parameters=HnswParameters(metric=VectorSearchAlgorithmMetric.COSINE))
                    ],
                    vectorizers=[
                        AzureOpenAIVectorizer(
                            name="openai_vectorizer",
                            azure_open_ai_parameters=AzureOpenAIParameters(
                                resource_uri=f'https://{openai_client.base_url.host}',
                                deployment_id=azure_openai_embedding_deployment,
                                api_key=openai_client.api_key,
                            )
                        )
                    ],
                    profiles=[
                        VectorSearchProfile(name="vp", algorithm_configuration_name="algo", vectorizer="openai_vectorizer")
                    ]
                ),
                semantic_search=SemanticSearch(
                    configurations=[
                        SemanticConfiguration(
                            name="default",
                            prioritized_fields=SemanticPrioritizedFields(title_field=SemanticField(field_name="title"), content_fields=[SemanticField(field_name="chunk")])
                        )
                    ],
                    default_configuration_name="default"
                )
            )
        )

def upload_documents(index_name, azure_openai_embedding_deployment):
    search_client = SearchClient(endpoint=seach_connection.endpoint_url, index_name=index_name, credential=AzureKeyCredential(seach_connection.key))

    def generate_embeddings(text):
        response = openai_client.embeddings.create(
            input=text,
            model=azure_openai_embedding_deployment,
        )
        return response.data[0].embedding

    with open("data/insurance/faq.json", "r") as file:
        faq = json.load(file)
        faq_documents = []

        for i, item in enumerate(faq):
            faq_documents.append({
                "chunk_id": str(uuid.uuid4()),
                "category": item["category"],
                "title": item["title"],
                "chunk": item["chunk"],
                "text_vector": generate_embeddings(item["chunk"])
            })
        
        search_client.upload_documents(faq_documents)
        logger.info(f'Uploaded {len(faq_documents)} documents to Azure AI Search index {index_name}')



if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(message)s", datefmt="[%X]")
    logger = logging.getLogger("voicerag")
    logger.setLevel(logging.INFO)

    logger = logging.getLogger("voicerag")

    logger.info("Checking if we need to set up Azure AI Search index...")
    if os.environ.get("AZURE_SEARCH_REUSE_EXISTING") == "true":
        logger.info("Since an existing Azure AI Search index is being used, no changes will be made to the index.")
        exit()
    else:
        logger.info("Setting up Azure AI Search index and integrated vectorization...")

    # Used to name index, indexer, data source and skillset
    AZURE_SEARCH_INDEX = os.environ["AZURE_SEARCH_INDEX"]
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-3-large"
    EMBEDDINGS_DIMENSIONS = 3072

    setup_index(
        index_name=AZURE_SEARCH_INDEX, 
        azure_openai_embedding_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT)

    upload_documents(
        index_name=AZURE_SEARCH_INDEX,
        azure_openai_embedding_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT)