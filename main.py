import json
import os
import logging

from flask import Flask, request, jsonify
from openai import AzureOpenAI
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential

from opentelemetry import trace
from opentelemetry.trace import get_tracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

from services.booking import book_flight, book_flight_tool
from services.search import search_index, search_tool

# Flask app definition and logger
app = Flask(__name__)
log = app.logger
log.setLevel(logging.DEBUG)

# Initialisation de l'instrumentation OpenTelemetry
AIInferenceInstrumentor().instrument()
span_exporter = ConsoleSpanExporter()
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
trace.set_tracer_provider(tracer_provider)
tracer = get_tracer(__name__)

project = AIProjectClient.from_connection_string(
    conn_str=os.environ.get('AZURE_PROJECT_CONNECTION_STRING'),
    credential=DefaultAzureCredential())

# Initialisez le client Azure OpenAI
openai_client = AzureOpenAI(
    azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
    api_key=os.environ.get('AZURE_OPENAI_KEY'),
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION'),
    azure_deployment=os.environ.get('AZURE_OPENAI_DEPLOYMENT')
)

tools = [
    book_flight_tool,
    search_tool
]

@tracer.start_as_current_span(name="chat")
@app.route('/chat', methods=['POST'])
def chat(query: str = None):

    if query is None:
        data = request.get_json()
        query = data.get('query', '')

    messages = [
        {"role": "user", "content": query}
    ]

    response = openai_client.chat.completions.create(
        messages=messages,
        tools=tools,
        model=os.environ.get('AZURE_OPENAI_DEPLOYMENT')
    )

    assistant_message = response.choices[0].message

    if assistant_message.tool_calls :
        for tool in assistant_message.tool_calls:
            log.debug("Tool call: %s", tool.function.name)
            function_name = tool.function.name
            arguments = json.loads(tool.function.arguments)

            if function_name == 'book_flight':
                result = book_flight(arguments['destination'], arguments['date'])
            elif function_name == 'search_index':
                result = search_index(arguments['query'])
            else:
                result = {"message": "Function not recognized"}
    else:
        log.debug("Message Content: %s", assistant_message.content)
        result = {"message": assistant_message.content}

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)