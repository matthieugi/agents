import json
import os
import logging
import asyncio

from flask import Flask, request, jsonify
from openai import AzureOpenAI
from azure.ai.inference.tracing import AIInferenceInstrumentor
from azure.ai.projects.aio import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor

from opentelemetry import trace
from opentelemetry.trace import get_tracer

from services.booking import book_flight, book_flight_tool
from services.search import search_index, search_tool

# Flask app definition and logger
app = Flask(__name__)
log = app.logger
log.setLevel(logging.DEBUG)

tracer = get_tracer(__name__)

async def initialize_monitoring():
    project = AIProjectClient.from_connection_string(
        conn_str=os.environ.get('AZURE_PROJECT_CONNECTION_STRING'),
        credential=DefaultAzureCredential()
    )

    # Enable instrumentation of AI packages (inference, agents, openai, langchain)
    project.telemetry.enable()

    # Log traces to the project's application insights resource
    application_insights_connection_string = await project.telemetry.get_connection_string()
    if application_insights_connection_string:
        configure_azure_monitor(
            connection_string=application_insights_connection_string,
            enable_live_metrics=True)

# Initialize the project client
asyncio.run(initialize_monitoring())

openai_client = AzureOpenAI(
    azure_deployment=os.environ.get('AZURE_OPENAI_DEPLOYMENT'),
    azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
    api_key=os.environ.get('AZURE_OPENAI_KEY'),
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION')
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
                search_result = search_index(query)
                messages.append({"role": "assistant", "content": search_result['results']})

                log.debug("Received %s results, calling LLM to generate final answer ", len(messages))
                response = openai_client.chat.completions.create(
                    messages=messages,
                    model=os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                )
                messages.append({"role": "assistant", "content": response.choices[0].message.content})
                result = messages

            else:
                result = {"message": "Function not recognized"}
    else:
        log.debug("Message Content: %s", assistant_message.content)
        result = {"message": assistant_message.content}

    return jsonify(result), 200



if __name__ == '__main__':
    # Initialisation de l'instrumentation OpenTelemetry
    AIInferenceInstrumentor().instrument(enable_content_recording=True)
    
    app.run(debug=True)