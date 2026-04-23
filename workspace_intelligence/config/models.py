"""Typed configuration models for the workspace intelligence engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class ConfigValidationError(ValueError):
    """Raised when a configuration file contains invalid data."""


@dataclass(slots=True)
class WatcherConfig:
    """Configuration for filesystem observation."""

    roots: list[str] = field(default_factory=list)
    recursive: bool = True
    debounce_seconds: float = 0.5
    include_hidden: bool = False


@dataclass(slots=True)
class RoutingRule:
    """Pattern-based routing rule used by the future rule engine."""

    pattern: str
    destination: str
    reason: str | None = None
    priority: int = 100


@dataclass(slots=True)
class RuleConfig:
    """Deterministic rules that protect user workspaces."""

    ignore_folders: list[str] = field(default_factory=list)
    safe_zones: list[str] = field(default_factory=list)
    file_routing: dict[str, str] = field(default_factory=dict)
    routing_rules: list[RoutingRule] = field(default_factory=list)
    case_sensitive: bool = False


@dataclass(slots=True)
class DecisionConfig:
    """Decision policy for future routing and AI fallback."""

    use_ai_fallback: bool = False
    min_confidence: float = 0.8
    dry_run: bool = True
    log_decisions: bool = True


@dataclass(slots=True)
class WorkspaceIntelligenceConfig:
    """Root configuration object for the V2 engine."""

    version: int = 1
    workspace_root: str = "."
    watcher: WatcherConfig = field(default_factory=WatcherConfig)
    rules: RuleConfig = field(default_factory=RuleConfig)
    decision: DecisionConfig = field(default_factory=DecisionConfig)

    def __post_init__(self) -> None:
        self.workspace_root = str(Path(self.workspace_root).expanduser())

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "WorkspaceIntelligenceConfig":
        if not isinstance(raw, dict):
            raise ConfigValidationError("Configuration root must be an object.")

        watcher_raw = raw.get("watcher", {})
        rules_raw = raw.get("rules", {})
        decision_raw = raw.get("decision", {})

        if not isinstance(watcher_raw, dict):
            raise ConfigValidationError("watcher must be an object.")
        if not isinstance(rules_raw, dict):
            raise ConfigValidationError("rules must be an object.")
        if not isinstance(decision_raw, dict):
            raise ConfigValidationError("decision must be an object.")

        routing_rules: list[RoutingRule] = []
        for item in rules_raw.get("routing_rules", []):
            if not isinstance(item, dict):
                raise ConfigValidationError("routing_rules entries must be objects.")
            routing_rules.append(
                RoutingRule(
                    pattern=str(item.get("pattern", "")).strip(),
                    destination=str(item.get("destination", "")).strip(),
                    reason=item.get("reason"),
                    priority=int(item.get("priority", 100)),
                )
            )

        return cls(
            version=int(raw.get("version", 1)),
            workspace_root=str(raw.get("workspace_root", ".")),
            watcher=WatcherConfig(
                roots=[str(value) for value in watcher_raw.get("roots", [])],
                recursive=bool(watcher_raw.get("recursive", True)),
                debounce_seconds=float(watcher_raw.get("debounce_seconds", 0.5)),
                include_hidden=bool(watcher_raw.get("include_hidden", False)),
            ),
            rules=RuleConfig(
                ignore_folders=[str(value) for value in rules_raw.get("ignore_folders", [])],
                safe_zones=[str(value) for value in rules_raw.get("safe_zones", [])],
                file_routing={str(key): str(value) for key, value in rules_raw.get("file_routing", {}).items()},
                routing_rules=routing_rules,
                case_sensitive=bool(rules_raw.get("case_sensitive", False)),
            ),
            decision=DecisionConfig(
                use_ai_fallback=bool(decision_raw.get("use_ai_fallback", False)),
                min_confidence=float(decision_raw.get("min_confidence", 0.8)),
                dry_run=bool(decision_raw.get("dry_run", True)),
                log_decisions=bool(decision_raw.get("log_decisions", True)),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
