# Dharmas Claude: RAG-Powered Code Assistant

Welcome to Dharmas Claude, a sophisticated code assistant designed to help you interact with and navigate large codebases efficiently. It uses Retrieval-Augmented Generation (RAG) to provide smart code querying and indexing capabilities, thanks to its integration with a range of specialized retrievers and indexers.

## Key Features

### Retrievers
Retrievers are the components that fetch relevant pieces of code based on your queries:
- **Hybrid Qdrant Retriever**: Combines dense and sparse embeddings to enhance retrieval performance from Qdrant.
- **Semantic Qdrant Retriever**: Utilizes semantic embeddings to find similar code chunks in Qdrant.
- **Semantic Chroma Retriever**: Leverages ChromaDB for returning code segments aligned with your search context.

### Indexers
Indexers process and store code data for efficient retrieval:
- **Semantic Chroma Indexer**: Processes code files into embeddings stored within ChromaDB.
- **Semantic Qdrant Indexer**: Converts code files into embeddings, managed via QdrantVectorStore.

## MCP Integration
Dharmas Claude connects to multiple configured MCP (Multilingual Code Processing) servers to extend its capabilities by loading additional tools.

### MCP Client
- **Functionality**: Connects to all MCP servers configured and retrieves the tools they offer.
- **Implementation**: Uses `MultiServerMCPClient` to handle server connections and tool retrieval.

### MCP Configuration
- **Functionality**: Loads server configurations from `mcp_servers.json`, resolving any environment variable placeholders.
- **Purpose**: Ensures configurations are dynamically adapted based on the environment and working directory.

## Configuration

Configurations are central to tailoring the behavior of Dharmas Claude. The `config.yaml` file allows you to define:
- Which retriever and indexer to use.
- Model and embedding preferences.
- Any additional settings required for customizing your search and retrieval needs.

## Getting Started

To get up and running with Dharmas Claude:

1. **Launch the Assistant**
   Open your terminal and run the assistant using:
   ```sh
   python main.py
   ```
   Interact using commands like `/ask <question>` to query the codebase or `/show_semantic_index` to inspect indexed contents.

2. **Tweak Configurations**
   Modify `config.yaml` to update retriever/indexer selections, and adjust model or provider settings to optimize for your specific requirements.

## Directory Overview

A quick guide to the project's structure:

- **`agent/`**: Holds the components for the agent's operations.
- **`context/`**: Contains the logic for indexers and retrievers.
- **`llm/`**: Manages Large Language Model settings.
- **`main.py`**: The main script to start the assistant.
- **`tools/`**: Utility scripts and additional tools to extend functionality.
- **`mcp/`**: Manages MCP server interactions and configurations.

## Prerequisites

Prior to usage, ensure:
- Appropriate environment variables are set for services like Qdrant.
- Dependencies are up to date, as indicated in dependencies files (e.g., `requirements.txt`).

This project is designed for developers looking to enhance their productivity when exploring and understanding complex codebases. Enjoy making your development experience smoother with Dharmas Claude!
