import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


# User configs, first match wins: project-local file, then global config,
# then the packaged default.
_CONFIG_PATHS = (
   Path.cwd() / "mcp_servers.json",
   Path.home() / ".config" / "camrahd" / "mcp_servers.json",
   Path(__file__).parent.parent / "mcp_servers.json",
)


def _config_path() -> Path:
   for path in _CONFIG_PATHS:
       if path.exists():
           return path
   return _CONFIG_PATHS[-1]


def load_mcp_configs() -> dict:
   """Return mcp_servers dict from mcp_servers.json with env vars resolved.

   CWD is injected at load time so ${CWD} in the config always resolves to the
   directory where camrahd was launched — not the package install location.
   """
   os.environ.setdefault("CWD", str(Path.cwd()))
   raw = json.loads(_config_path().read_text())
   # Replace ${VAR} placeholders in the config with actual env var values
   resolved = re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), ""), json.dumps(raw))
   return json.loads(resolved).get("mcp_servers", {})
