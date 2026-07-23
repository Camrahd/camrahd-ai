import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from camrahd_ai.config import config


_configured = False


def _configure() -> None:
   """Send all logs to one rotating file; only warnings+ reach the console.

   Configured via camrahd.yaml:
     logging:
       file: .camrahd/camrahd.log
       level: DEBUG        # level written to the file for camrahd loggers
   """
   global _configured
   if _configured:
       return

   log_config = config.get("logging", {})
   log_path = Path(log_config.get("file", ".camrahd/camrahd.log"))
   log_path.parent.mkdir(parents=True, exist_ok=True)

   handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
   handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

   # Root at WARNING keeps third-party libraries (openai, httpcore…) quiet;
   # without a console handler, warnings+ still surface via logging's
   # last-resort stderr handler.
   root = logging.getLogger()
   root.setLevel(logging.WARNING)
   root.addHandler(handler)

   level_name = str(log_config.get("level", "DEBUG")).upper()
   logging.getLogger("camrahd_ai").setLevel(getattr(logging, level_name, logging.DEBUG))
   _configured = True


def get_logger(name: str) -> logging.Logger:
   _configure()
   return logging.getLogger(name)
