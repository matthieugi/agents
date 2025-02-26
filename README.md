# Agents

This project implements a multi-agent system designed to handle various user requests related to insurance services. The system leverages Azure AI services to provide intelligent responses and actions based on user queries. The main components of the system include the orchestrator and specialized agents for advice, attestation, and quotes.

## Overview

The application consists of the following key components:

1. **Orchestrator**: Manages the flow of user requests and delegates them to the appropriate agent based on the query.
2. **Advice Agent**: Provides additional advice to users, especially in cases involving sports, risky activities, travel, or pet ownership.
3. **Attestation Agent**: Generates insurance attestations for existing clients, including home, car, or liability insurance.
4. **Quote Agent**: Generates quotes for home or car insurance plans.

## Evaluation Tools

The project includes several tools to generate and evaluate datasets, ensuring the system's responses are accurate and reliable. These tools are implemented in the following scripts:

1. **generate_simulation_data.py**: This script generates simulated data by using a simulator to create various user queries and expected responses based on a knowledge dataset. The generated data is saved in a JSONL file for further evaluation.

2. **generate_evaluation_data.py**: This script processes the simulated dataset, sending user queries to the advice agent and collecting the responses. The results, including the original queries, agent responses, and ground truth, are saved in a JSONL file for evaluation.

3. **evaluate.py**: This script evaluates the performance of the system using various evaluators such as groundedness, relevance, fluency, coherence, and safety metrics (violence, sexual content, self-harm, and indirect attacks). The evaluation results are saved in a JSONL file and can be viewed in AI Studio.

More details on how to levereage evaluators here : https://learn.microsoft.com/en-us/azure/ai-studio/concepts/evaluation-metrics-built-in?tabs=warning

These tools help ensure that the agents provide accurate, coherent, and safe responses to user queries.

## Getting Started

# Create required infrastructure

TODO : add deployments scripts

To set up the required infrastructure for this project, follow these steps:

1. **Azure AI Foundry**: This service is used to manage and deploy AI models. Ensure you have the necessary connection string set in your `.env` file:
    ```sh
    export AZURE_AI_PROJECT_CONNECTION_STRING="your_connection_string_here"
    ```

2. **Azure OpenAI**: This service provides the AI models used for generating embeddings and responses. Set the deployment and API version in your `.env` file:
    ```sh
    export AZURE_CHAT_DEPLOYMENT="your_deployment_name_here"
    export AZURE_OPENAI_API_VERSION="your_api_version_here"
    ```

3. **Azure AI Search Service**: This service is used to index and search documents. Set the connection name and index in your `.env` file:
    ```sh
    export AZURE_SEARCH_CONNECTION_NAME="your_search_connection_name_here"
    export AZURE_SEARCH_INDEX="your_index_name_here"
    ```

4. **Environment Variables**: Ensure all necessary environment variables are set in your `.env` file:
    ```sh
    export AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED="true"
    export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="your_embedding_deployment_name_here"
    export AZURE_SDK_TRACING_IMPLEMENTATION="opentelemetry"
    ```

5. **Run the Setup Script**: Execute the `import_sample_data.py` script to set up the Azure AI Search index and upload sample documents:
    ```sh
    python3 data.import_sample_data
    ```

By following these steps, you will create the necessary services and infrastructure to run the solution effectively.

# Run the app

To run the app, follow these steps:

1. **Install Dependencies**: Ensure you have all the necessary dependencies installed. You can use `pip` to install them:
    ```sh
    pip install -r requirements.txt
    ```

2. **Set Environment Variables**: Make sure all required environment variables are set in your `.env` file as described in the "Getting Started" section. and import it into your current shell using : 

    ```sh
    source .env
    ```

3. **Run the Application**: Start the Flask application by executing the following command:
    ```sh
    python3 -m app
    ```

# Test it

4. **Test the /process Endpoint**: You can use the following `curl` command to send a POST request to the `/process` endpoint with a relevant query from the FAQ:

    ```sh
    curl -X POST http://localhost:5000/process -H "Content-Type: application/json" -d '{"user_id": "user123", "user_query": "Proposez-vous des assurances pour les animaux ?"}'
    ```
