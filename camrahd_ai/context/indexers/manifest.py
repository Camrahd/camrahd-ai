import hashlib
import json
from pathlib import Path


from camrahd_ai.observability.logger import get_logger


logger = get_logger(__name__)


MANIFEST_NAME = "index_manifest.json"


def _manifest_path(repo_path: str) -> Path:
   return Path(repo_path) / ".camrahd" / MANIFEST_NAME


def _hash_file(filepath: str) -> str:
   return hashlib.sha256(Path(filepath).read_bytes()).hexdigest()


def load_manifest(repo_path: str) -> dict[str, str]:
   """Return the {filepath: sha256} map from the last indexing run, or {}."""
   path = _manifest_path(repo_path)
   if not path.exists():
       return {}
   try:
       return json.loads(path.read_text())
   except (json.JSONDecodeError, OSError) as e:
       logger.warning(f"Ignoring unreadable index manifest {path}: {e}")
       return {}


def save_manifest(repo_path: str, manifest: dict[str, str]) -> None:
   path = _manifest_path(repo_path)
   path.parent.mkdir(parents=True, exist_ok=True)
   path.write_text(json.dumps(manifest, indent=2))
   logger.info(f"Saved index manifest with {len(manifest)} files to {path}")


def plan_reindex(repo_path: str, files: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
   """
   Compare current file hashes against the last indexing run.
   Returns (files_to_reindex, deleted_files, new_manifest). Files whose
   content hash is unchanged are excluded from files_to_reindex.
   """
   old = load_manifest(repo_path)
   new: dict[str, str] = {}
   for filepath in files:
       try:
           new[filepath] = _hash_file(filepath)
       except OSError as e:
           logger.warning(f"Could not hash {filepath}: {e}")

   to_index = [f for f, digest in new.items() if old.get(f) != digest]
   deleted = [f for f in old if f not in new]
   logger.info(
       f"Reindex plan: {len(to_index)} changed/new, {len(deleted)} deleted, "
       f"{len(new) - len(to_index)} unchanged"
   )
   return to_index, deleted, new
