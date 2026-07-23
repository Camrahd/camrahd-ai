import os
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models


from camrahd_ai.config import config
from camrahd_ai.context.indexers.code_parser import parse_file, get_source_files
from camrahd_ai.context.indexers.manifest import plan_reindex, save_manifest
from camrahd_ai.llm.factory import get_embedder
from camrahd_ai.observability.logger import get_logger


logger = get_logger(__name__)


def delete_file_points(client: QdrantClient, collection_name: str, filepaths: list[str]) -> None:
   """Remove all points whose metadata.source matches one of filepaths."""
   for filepath in filepaths:
       client.delete(
           collection_name=collection_name,
           points_selector=models.FilterSelector(filter=models.Filter(must=[
               models.FieldCondition(key="metadata.source", match=models.MatchValue(value=filepath))
           ])),
       )


def build_documents(filepaths: list[str]) -> list[Document]:
   """Parse files into LangChain Documents ready for embedding."""
   docs = []
   for filepath in filepaths:
       try:
           chunks = parse_file(filepath)
       except (SyntaxError, ValueError) as e:
           logger.error(f"Skipping {filepath}: {e}")
           continue
       for chunk in chunks:
           docs.append(Document(
               page_content=chunk.content,
               metadata={
                   "source": chunk.source,
                   "name": chunk.name,
                   "type": chunk.type,
                   "start_line": chunk.start_line,
                   "end_line": chunk.end_line,
               }
           ))
           logger.debug(f"  Indexed {chunk.type} '{chunk.name}' from {filepath}")
   return docs




def index_codebase(repo_path: str) -> QdrantVectorStore:
   """
   Parse source files in repo_path, embed each chunk and store in Qdrant.
   Incremental: only files whose content hash changed since the last run
   are re-embedded; chunks of deleted files are removed.
   """
   embedder = get_embedder()
   collection_name = config["qdrant"]["collection_name"]
   url = os.getenv("QDRANT_URL")
   api_key = os.getenv("QDRANT_API_KEY")


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


   logger.info(f"Starting semantic indexing of {repo_path}")
   docs = build_documents(files)


   vector_store = QdrantVectorStore.from_documents(
       docs, embedder,
       url=url,
       api_key=api_key,
       collection_name=collection_name,
       batch_size=50,
   )


   save_manifest(repo_path, new_manifest)
   logger.info(f"Semantic indexing complete. Total chunks: {len(docs)}")
   return vector_store




def show_index(vector_store: QdrantVectorStore) -> None:
   """Display all documents stored in the Qdrant collection."""
   from rich.console import Console
   console = Console()
   client = vector_store.client
   collection_name = config["qdrant"]["collection_name"]
   results = client.scroll(collection_name=collection_name, with_payload=True, with_vectors=True, limit=1000)
   points = results[0]
   console.print(f"\n[bold]Semantic Index — {len(points)} chunks[/bold]\n")


   for i, point in enumerate(points):
       payload = point.payload
       emb = point.vector
       console.print(f"[bold cyan]── Chunk {i+1} ──────────────────────────[/bold cyan]")
       console.print(f"  File     : {payload['source']}")
       console.print(f"  Name     : {payload['name']} ({payload['type']})")
       console.print(f"  Lines    : {payload['start_line']} - {payload['end_line']}")
       console.print(f"  Embedding: [{', '.join(f'{v:.4f}' for v in emb[:5])}...] ({len(emb)} dims)")
       console.print(f"  Code     :\n[dim]{payload.get('page_content', '')[:300]}[/dim]\n")
