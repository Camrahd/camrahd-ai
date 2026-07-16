# Dharma's Claude

A Claude Code–style AI coding agent that lives in your terminal. Built from scratch in Python to understand how agentic coding assistants actually work under the hood: code-aware retrieval, tool orchestration, persistent memory, and MCP integration.

```
Dharmas Claude — RAG-powered code assistant
LLM: openai / gpt-5.5
Embedder: openai / text-embedding-3-small
Session: 2a1f...
✓ Ready

> /ask how does the indexing pipeline work?
```

## Features

- **Code-aware chunking** — Uses [tree-sitter](https://tree-sitter.github.io/) to parse source files into semantic chunks (classes, functions) instead of naive text splitting, so retrieval respects code structure.
- **Hybrid RAG** — Dense + sparse retrieval over Qdrant (via FastEmbed), with a pluggable indexer/retriever layer that also supports ChromaDB and pure semantic mode.
- **Agentic tool use** — The agent can read/write files and run terminal commands through a LangGraph-orchestrated agent loop.
- **Persistent sessions** — Short-term memory checkpointed to SQLite; create, switch, and resume conversations across runs.
- **Automatic summarization** — Long conversations are summarized past a token threshold (`summarize_at_tokens`) so the agent stays coherent in long sessions.
- **MCP integration** — Connects to Model Context Protocol servers (e.g. filesystem MCP) to consume external tools without hardcoding them.
- **Skills system** — A registry of reusable skills loaded from `.Dharma/skills/` that extend the agent's behavior without touching core code.
- **Multi-provider** — Swap between OpenAI and Anthropic models (and embedders) via config.

## Architecture

```
Dharmas_claude/
├── main.py                 # REPL entry point
├── config.py / config.yaml # Provider, RAG mode, memory settings
├── agent/                  # Agent factory, orchestrator, tool bindings
├── context/
│   ├── indexers/           # tree-sitter code parser, Qdrant/Chroma indexers
│   └── retrievers/         # semantic + hybrid retrievers
├── llm/                    # LLM & embedder factories (OpenAI / Anthropic)
├── memory/                 # Session management, SQLite checkpointing
├── mcp/                    # MCP client & server config
├── skills/                 # Skill registry & tools
├── tools/                  # Filesystem & terminal tools
└── observability/          # Logging
```

**Query flow:** user query → hybrid retrieval over the indexed codebase → context assembled into the agent's prompt → LangGraph agent loop with tool calls (filesystem, terminal, MCP, skills) → response, checkpointed to the session.

## Getting started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- A running [Qdrant](https://qdrant.tech/) instance (or switch to ChromaDB in `config.yaml`)
- An OpenAI and/or Anthropic API key

### Install & run

```bash
git clone https://github.com/Camrahd/claud_code.git
cd claud_code
poetry install

# Add your API keys
echo "OPENAI_API_KEY=sk-..." > .env

# Run from the repo you want to index (defaults to cwd)
poetry run Dharmas_claude
```

On first run, the agent indexes the current working directory and drops you into a REPL.

### Commands

| Command | Description |
|---|---|
| `/ask <question>` | Ask a question about the codebase |
| `/show_index` | Show all chunks in the index |
| `/new_session` | Start a fresh conversation |
| `/switch <session_id>` | Resume a past session |
| `/session` | Show the current session id |
| `/exit` | Quit |

## Configuration

Everything lives in `Dharmas_claude/config.yaml`:

```yaml
llm:
  provider: openai        # openai | anthropic
  model: gpt-5.5

vector_store:
  provider: qdrant        # qdrant | chromadb
  retrieval_mode: hybrid  # dense | sparse | hybrid

memory:
  summarize_at_tokens: 4000
  keep_last_messages: 20
```

## Why I built this

Tools like Claude Code feel like magic, but the magic isn't the LLM — it's the engineering around it. Building this taught me that context management, retrieval quality, and tool orchestration are where coding agents are won or lost.

## Tech stack

Python · LangChain / LangGraph · Qdrant · ChromaDB · tree-sitter · FastEmbed · MCP · SQLite · Rich
