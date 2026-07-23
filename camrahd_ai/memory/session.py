import uuid
from pathlib import Path


from camrahd_ai.config import config
from camrahd_ai.observability.logger import get_logger


logger = get_logger(__name__)


def _session_file() -> Path:
   return Path(config["memory"]["db_path"]).parent / "current_session"


def get_current_session() -> str:
   session_file = _session_file()
   if session_file.exists():
       session_id = session_file.read_text().strip()
       logger.info(f"Resuming session: {session_id}")
       return session_id
   return new_session()


def new_session() -> str:
   session_id = str(uuid.uuid4())
   session_file = _session_file()
   session_file.parent.mkdir(exist_ok=True)
   session_file.write_text(session_id)
   logger.info(f"Started new session: {session_id}")
   return session_id


def list_sessions() -> list[str]:
   """Return all session ids that have checkpoints in the memory database."""
   import sqlite3

   db_path = Path(config["memory"]["db_path"])
   if not db_path.exists():
       return []
   try:
       with sqlite3.connect(db_path) as conn:
           rows = conn.execute("SELECT DISTINCT thread_id FROM checkpoints").fetchall()
       return [row[0] for row in rows]
   except sqlite3.Error as e:
       logger.warning(f"Could not list sessions: {e}")
       return []


def switch_session(session_id: str) -> str:
   session_file = _session_file()
   session_file.write_text(session_id)
   logger.info(f"Switched to session: {session_id}")
   return session_id
