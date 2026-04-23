"""Rule engine placeholder for Phase 2 of the workspace intelligence engine.

The first phase wires configuration and filesystem observation first. This module
exists now so future rule evaluation can plug into a stable package boundary.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleOutcome:
    """Result of rule evaluation."""

    action: str
    reason: str
    destination: str | None = None


class RuleEngine:
    """Deterministic rule engine shell for future decisioning."""

    def evaluate(self, path: str) -> RuleOutcome:
        raise NotImplementedError("RuleEngine will be implemented in the next phase.")
