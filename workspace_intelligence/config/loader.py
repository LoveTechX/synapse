"""Load JSON or YAML configuration for the workspace intelligence engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import RoutingRule, WorkspaceIntelligenceConfig

DEFAULT_CONFIG_FILENAME = "default_config.json"
DEFAULT_CONFIG_PATH = Path(__file__).with_name(DEFAULT_CONFIG_FILENAME)


class ConfigLoadError(RuntimeError):
    """Raised when a configuration file cannot be loaded or validated."""


def _resolve_path(base_dir: Path, raw_value: str) -> str:
    candidate = Path(raw_value).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve())
    return str((base_dir / candidate).resolve())


def _read_raw_config(config_path: Path) -> dict[str, Any]:
    suffix = config_path.suffix.lower()
    raw_text = config_path.read_text(encoding="utf-8")

    if suffix in {".json", ""}:
        loaded = json.loads(raw_text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised only with YAML input
            raise ConfigLoadError(
                "YAML configuration requires PyYAML. Install it or use a JSON config file."
            ) from exc

        loaded = yaml.safe_load(raw_text)
    else:
        raise ConfigLoadError(f"Unsupported config format: {config_path.suffix}")

    if loaded is None:
        return {}

    if not isinstance(loaded, dict):
        raise ConfigLoadError("Configuration file must contain a top-level object.")

    return loaded


def _resolve_config_paths(config: WorkspaceIntelligenceConfig, base_dir: Path) -> WorkspaceIntelligenceConfig:
    config.workspace_root = _resolve_path(base_dir, config.workspace_root)
    config.watcher.roots = [_resolve_path(base_dir, value) for value in config.watcher.roots]
    config.rules.safe_zones = [_resolve_path(base_dir, value) for value in config.rules.safe_zones]
    config.rules.file_routing = {
        key: _resolve_path(base_dir, value) for key, value in config.rules.file_routing.items()
    }
    config.rules.routing_rules = [
        RoutingRule(
            pattern=rule.pattern,
            destination=_resolve_path(base_dir, rule.destination),
            reason=rule.reason,
            priority=rule.priority,
        )
        for rule in config.rules.routing_rules
    ]
    return config


def load_config(config_path: str | Path | None = None) -> WorkspaceIntelligenceConfig:
    """Load and validate a workspace intelligence config file.

    Relative paths inside the config are resolved relative to the config file location.
    """

    resolved_path = Path(config_path or DEFAULT_CONFIG_PATH).expanduser()
    if not resolved_path.is_absolute():
        resolved_path = (Path.cwd() / resolved_path).resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")

    raw_config = _read_raw_config(resolved_path)
    config = WorkspaceIntelligenceConfig.from_dict(raw_config)
    return _resolve_config_paths(config, resolved_path.parent)


def load_default_config() -> WorkspaceIntelligenceConfig:
    """Load the packaged default JSON configuration."""

    return load_config(DEFAULT_CONFIG_PATH)
