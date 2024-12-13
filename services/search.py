import os

from opentelemetry.trace import get_tracer
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery


search_client = SearchClient(
    endpoint=os.environ.get('AZURE_SEARCH_ENDPOINT'),
    credential=AzureKeyCredential(os.environ.get('AZURE_SEARCH_KEY')),
    index_name=os.environ.get('AZURE_SEARCH_INDEX')
)

tracer = get_tracer(__name__)

@tracer.start_as_current_span(name="search_index")
def search_index(query):
    search_results = search_client.search(
        search_text=query, 
        query_type="semantic",
        semantic_configuration_name="default",
        top=5,
        vector_queries=[VectorizableTextQuery(
            text=query, k_nearest_neighbors=50, fields="text_vector"
        )],
    )

    result = ""
    for r in search_results:
        result += f"[{r['title']}]: {r['chunk']}\n-----\n"

    return {"results": result}

search_tool = {
    "type": "function",
    "function": {
        "name": "search_index",
        "description": """Search for information in the index for questions related to :
            Family and Children
            Authorized Baggage
            Special Baggage
            Authorized Products
            Pregnant Women
            Seniors
            Pets
            SkyPriority""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
}