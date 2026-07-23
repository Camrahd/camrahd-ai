"""
api.py — FastAPI server for Educosys Claude RAG assistant.

Replaces the CLI REPL with REST endpoints.
Start with: uvicorn api:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from Dharmas_claude.config import config
from Dharmas_claude.context.indexers.factory import get_indexer, get_index_inspector
from Dharmas_claude.llm.factory import get_llm, get_embedder
from Dharmas_claude.agent.orchestrator import handle_query
from Dharmas_claude.observability.logging import get_logger

# Load .env before anything else (same as main.py)
load_dotenv(Path(__file__).parent.parent / ".env")

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Shared application state (populated during startup)
# ---------------------------------------------------------------------------

app_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize LLM, embedder, and index once at server startup."""
    logger.info("Starting Educosys Claude API server")

    llm = get_llm()
    embedder = get_embedder()

    repo_path = str(Path.cwd())
    logger.info(f"Building/loading index for: {repo_path}")
    index = get_indexer()(repo_path)

    app_state["llm"] = llm
    app_state["embedder"] = embedder
    app_state["index"] = index

    logger.info(
        f"Ready — LLM: {config['llm']['provider']}/{config['llm']['model']} | "
        f"Embedder: {config['embeddings']['provider']}/{config['embeddings']['model']}"
    )

    yield  # Server is now running

    logger.info("Shutting down Educosys Claude API server")
    app_state.clear()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Educosys Claude",
    description="RAG-powered code assistant — ask questions about your codebase.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="The natural-language question to ask about the codebase.",
        examples=["How does the indexer factory decide which indexer to use?"],
    )


class QueryResponse(BaseModel):
    question: str = Field(..., description="Echo of the original question.")
    answer: str = Field(..., description="LLM-generated answer from the RAG pipeline.")


class IndexSummaryResponse(BaseModel):
    summary: str = Field(..., description="Human-readable dump of the current semantic index.")


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_model: str
    embedder_provider: str
    embedder_model: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    """Confirm the server is up and return the active model configuration."""
    if not app_state:
        raise HTTPException(status_code=503, detail="Server is still initializing.")
    return HealthResponse(
        status="ok",
        llm_provider=config["llm"]["provider"],
        llm_model=config["llm"]["model"],
        embedder_provider=config["embeddings"]["provider"],
        embedder_model=config["embeddings"]["model"],
    )


@app.post("/ask", response_model=QueryResponse, tags=["rag"])
def ask(body: QueryRequest):
    """
    Run a question through the RAG pipeline and return the LLM answer.

    Equivalent to the CLI command: `/ask <question>`
    """
    logger.info(f"Received question: {body.question}")
    try:
        answer = handle_query(body.question)
    except Exception as exc:
        logger.exception("handle_query raised an error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    
    

    return QueryResponse(question=body.question, answer=answer)


@app.get("/index/inspect", response_model=IndexSummaryResponse, tags=["index"])
def inspect_index():
    """
    Return a text summary of the current semantic index.

    Equivalent to the CLI command: `/show_semantic_index`
    """
    index = app_state.get("index")
    if index is None:
        raise HTTPException(status_code=503, detail="Index not yet available.")

    logger.info("Inspecting semantic index")

    # get_index_inspector() returns a callable that typically prints; capture it.
    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            get_index_inspector()(index)
        summary = buffer.getvalue() or "Index inspection returned no output."
    except Exception as exc:
        logger.exception("Index inspector raised an error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return IndexSummaryResponse(summary=summary)