from opentelemetry.trace import get_tracer

tracer = get_tracer(__name__)

@tracer.start_as_current_span(name="search_index")
def search_index(query):
    """
    Searches the index for the given query and returns the results.

    Args:
        query (str): The search query.

    Returns:
        dict: A dictionary containing the search results.
    """

    return {"results": f"Search results for query: {query}"}

search_tool = {
    "type": "function",
    "function": {
        "name": "search_index",
        "description": "Search for information in the index.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
}