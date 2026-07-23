import yaml
from pathlib import Path


_DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"

# User overrides, first match wins: project-local file, then global config.
_USER_CONFIG_PATHS = (
   Path.cwd() / "camrahd.yaml",
   Path.home() / ".config" / "camrahd" / "config.yaml",
)


def _deep_merge(base: dict, override: dict) -> dict:
   merged = dict(base)
   for key, value in override.items():
       if isinstance(value, dict) and isinstance(merged.get(key), dict):
           merged[key] = _deep_merge(merged[key], value)
       else:
           merged[key] = value
   return merged


def load_config() -> dict:
   """Load packaged defaults, then merge overrides from camrahd.yaml in the
   current directory or ~/.config/camrahd/config.yaml (first one found)."""
   settings = yaml.safe_load(_DEFAULT_CONFIG.read_text())
   for path in _USER_CONFIG_PATHS:
       if path.exists():
           settings = _deep_merge(settings, yaml.safe_load(path.read_text()) or {})
           break
   return settings


config = load_config()
