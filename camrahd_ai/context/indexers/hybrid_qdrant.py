import os
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient


from camrahd_ai.config import config
from camrahd_ai.context.indexers.code_parser import get_source_files
from camrahd_ai.context.indexers.manifest import plan_reindex, save_manifest
from camrahd_ai.context.indexers.semantic_qdrant import build_documents, delete_file_points
from camrahd_ai.llm.factory import get_embedder
from camrahd_ai.observability.logger import get_logger


logger = get_logger(__name__)


RETRIEVAL_MODE_MAP = {
   "dense": RetrievalMode.DENSE,
   "sparse": RetrievalMode.SPARSE,
   "hybrid": RetrievalMode.HYBRID,
}




def _get_retrieval_mode() -> RetrievalMode:
   mode = config["vector_store"].get("retrieval_mode", "hybrid")
   return RETRIEVAL_MODE_MAP.get(mode, RetrievalMode.HYBRID)




def index_codebase(repo_path: str) -> QdrantVectorStore:
   """
   Parse all source files, embed with dense + sparse vectors and store in Qdrant.
   Supports dense, sparse, and hybrid retrieval modes via config.
   Incremental: only files whose content hash changed since the last run
   are re-embedded; chunks of deleted files are removed.
   """
   embedder = get_embedder()
   collection_name = config["qdrant"]["collection_name"]
   url = os.getenv("QDRANT_URL")
   api_key = os.getenv("QDRANT_API_KEY")
   retrieval_mode = _get_retrieval_mode()


   # Check if collection already has data
   client = QdrantClient(url=url, api_key=api_key)
   try:
       existing = [c.name for c in client.get_collections().collections]
   except Exception as e:
       raise SystemExit(
           f"Could not reach a Qdrant server at {url or 'http://localhost:6333'} ({e.__class__.__name__}).\n"
           "Either start one:  docker run -d -p 6333:6333 qdrant/qdrant\n"
           "or point QDRANT_URL at your instance in .env,\n"
           "or switch vector_store.provider to 'chromadb' in camrahd.yaml."
       ) from e
   files = get_source_files(repo_path)
   to_index, deleted, new_manifest = plan_reindex(repo_path, files)


   if collection_name in existing:
       info = client.get_collection(collection_name)
       if info.points_count > 0:
           vector_store = QdrantVectorStore.from_existing_collection(
               embedding=embedder,
               sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
               retrieval_mode=retrieval_mode,
               url=url,
               api_key=api_key,
               collection_name=collection_name,
           )
           if not to_index and not deleted:
               logger.info(f"Index up to date with {info.points_count} chunks")
               return vector_store
           logger.info(f"Incremental reindex: {len(to_index)} changed, {len(deleted)} deleted")
           delete_file_points(client, collection_name, deleted + to_index)
           docs = build_documents(to_index)
           if docs:
               vector_store.add_documents(docs, batch_size=50)
           save_manifest(repo_path, new_manifest)
           return vector_store


   logger.info(f"Starting hybrid indexing of {repo_path}")
   docs = build_documents(files)


   vector_store = QdrantVectorStore.from_documents(
       docs, embedder,
       sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
       retrieval_mode=retrieval_mode,
       url=url,
       api_key=api_key,
       collection_name=collection_name,
       batch_size=50,
   )


   logger.info(f"Hybrid indexing complete. Total chunks: {len(docs)}")
   return vector_store


def show_index(vector_store: QdrantVectorStore) -> None:
   from rich.console import Console
   console = Console()
   client = vector_store.client
   collection_name = config["qdrant"]["collection_name"]
   results = client.scroll(collection_name=collection_name, with_payload=True, with_vectors=False, limit=1000)
   points = results[0]
   console.print(f"\n[bold]Hybrid Index — {len(points)} chunks[/bold]\n")


   for i, point in enumerate(points):
       content = point.payload.get("page_content", "")
       meta = point.payload.get("metadata", {})
       console.print(f"[bold cyan]── Chunk {i+1} ──────────────────────────[/bold cyan]")
       console.print(f"  File     : {meta.get('source', 'unknown')}")
       console.print(f"  Name     : {meta.get('name', 'unknown')} ({meta.get('type', 'unknown')})")
       console.print(f"  Lines    : {meta.get('start_line')} - {meta.get('end_line')}")
       console.print(f"  Code     :\n[dim]{content[:300]}[/dim]\n")
