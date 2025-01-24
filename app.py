import os
import json
import streamlit as st
from openai import AzureOpenAI
from services.booking import book_flight_tool, book_flight
from services.search import search_tool, search_index

# Initialiser le client OpenAI
openai_client = AzureOpenAI(
    azure_endpoint=os.environ.get('AZURE_OPENAI_ENDPOINT'),
    api_key=os.environ.get('AZURE_OPENAI_KEY'),
    api_version=os.environ.get('AZURE_OPENAI_API_VERSION')
)

tools = [
    book_flight_tool,
    search_tool
]

# Fonction pour traiter la requête
def process_query(query):
    client_response = openai_client.chat.completions.create(
        messages=st.session_state.messages,
        tools=tools,
        model=os.environ.get('AZURE_OPENAI_DEPLOYMENT')
    )

    assistant_message = client_response.choices[0].message

    if assistant_message.tool_calls:
        for tool in assistant_message.tool_calls:
            st.write(f"Tool call: {tool.function.name}")
            function_name = tool.function.name
            arguments = json.loads(tool.function.arguments)

            if function_name == 'book_flight':
                result = book_flight(arguments['destination'], arguments['date'])
                st.write(result)
            elif function_name == 'search_index':
                search_result = search_index(query)
                st.session_state.messages.append({"role": "assistant", "content": search_result['results']})

                st.write(f"Received {len(st.session_state.messages)} results, calling LLM to generate final answer")
                client_response = openai_client.chat.completions.create(
                    messages=st.session_state.messages,
                    model=os.environ.get('AZURE_OPENAI_DEPLOYMENT')
                )
                assistant_message = client_response.choices[0].message

    return assistant_message

# Interface utilisateur Streamlit
st.title("Chat with your airline assistant ✈️")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    msg = process_query(prompt).content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)