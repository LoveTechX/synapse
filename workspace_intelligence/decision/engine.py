"""Safe-first decision engine for Phase 2 of the workspace intelligence engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

Action = Literal["IGNORE", "SUGGEST", "MOVE"]


class Decision(TypedDict):
    """Decision payload returned by the decision engine."""

    action: Action
    target_path: str | None
    requires_confirmation: bool
    reason: str
    decision_confidence: float


ROLE_TARGETS: dict[str, str] = {
    "source_code": "src",
    "config": "config",
    "log": "logs",
    "build_output": "build",
}

AUTO_MOVE_ROLES: set[str] = {"log", "temp", "build_output"}


@dataclass(slots=True)
class DecisionEngine:
    """Convert workspace context into deterministic, safe decisions."""

    move_confidence_threshold: float = 0.85

    def decide(self, workspace_context: dict[str, object]) -> Decision:
        """Return the next action without executing any filesystem change."""

        recommended_action = str(workspace_context.get("recommended_action", "review")).strip().lower()
        is_critical_file = bool(workspace_context.get("is_critical_file", False))
        is_safe_zone = bool(workspace_context.get("is_safe_zone", False))
        analyzer_confidence = self._as_float(workspace_context.get("overall_confidence", 0.0))
        file_role = str(workspace_context.get("file_role", "unknown")).strip().lower()
        project_root = self._as_optional_str(workspace_context.get("project_root"))
        source_file = self._extract_source_path(workspace_context)

        target_path = self._resolve_target_path(project_root=project_root, file_role=file_role)

        if source_file is not None and target_path is not None and self._is_already_in_target(source_file, target_path):
            confidence = self._decision_confidence(
                analyzer_confidence=analyzer_confidence,
                rule_clarity=0.98,
            )
            return self._decision(
                action="IGNORE",
                target_path=None,
                requires_confirmation=False,
                reason="File already in correct location.",
                decision_confidence=confidence,
            )

        if is_safe_zone:
            confidence = self._decision_confidence(
                analyzer_confidence=analyzer_confidence,
                rule_clarity=0.95,
            )
            return self._decision(
                action="IGNORE",
                target_path=None,
                requires_confirmation=False,
                reason="File is inside a safe zone, so move actions are blocked.",
                decision_confidence=confidence,
            )

        if is_critical_file:
            confidence = self._decision_confidence(
                analyzer_confidence=analyzer_confidence,
                rule_clarity=0.96,
            )
            return self._decision(
                action="SUGGEST",
                target_path=target_path,
                requires_confirmation=True,
                reason="Critical file detected; automatic move is disabled.",
                decision_confidence=confidence,
            )

        if target_path is None:
            confidence = self._decision_confidence(
                analyzer_confidence=analyzer_confidence,
                rule_clarity=0.85,
            )
            return self._decision(
                action="IGNORE",
                target_path=None,
                requires_confirmation=False,
                reason="No target mapping exists for this file role, so no action is taken.",
                decision_confidence=confidence,
            )

        can_auto_move = (
            analyzer_confidence >= self.move_confidence_threshold
            and not is_critical_file
            and not is_safe_zone
            and file_role in AUTO_MOVE_ROLES
        )
        if can_auto_move:
            confidence = self._decision_confidence(
                analyzer_confidence=analyzer_confidence,
                rule_clarity=0.97,
            )
            return self._decision(
                action="MOVE",
                target_path=target_path,
                requires_confirmation=False,
                reason="High-confidence, low-risk file role allows automatic move.",
                decision_confidence=confidence,
            )

        if recommended_action == "ignore":
            confidence = self._decision_confidence(
                analyzer_confidence=analyzer_confidence,
                rule_clarity=0.86,
            )
            return self._decision(
                action="IGNORE",
                target_path=None,
                requires_confirmation=False,
                reason="Analyzer hint is ignore and auto-move conditions are not met.",
                decision_confidence=confidence,
            )

        requires_confirmation = recommended_action == "review"
        confidence = self._decision_confidence(
            analyzer_confidence=analyzer_confidence,
            rule_clarity=0.88,
        )
        return self._decision(
            action="SUGGEST",
            target_path=target_path,
            requires_confirmation=requires_confirmation,
            reason="Manual suggestion is safer because auto-move constraints are not fully satisfied.",
            decision_confidence=confidence,
        )

    @staticmethod
    def _decision(
        *,
        action: Action,
        target_path: str | None,
        requires_confirmation: bool,
        reason: str,
        decision_confidence: float,
    ) -> Decision:
        return {
            "action": action,
            "target_path": target_path,
            "requires_confirmation": requires_confirmation,
            "reason": reason,
            "decision_confidence": decision_confidence,
        }

    @staticmethod
    def _resolve_target_path(project_root: str | None, file_role: str) -> str | None:
        target_folder = ROLE_TARGETS.get(file_role)
        if target_folder is None:
            return None

        if project_root is None:
            return None

        root = Path(project_root).expanduser().resolve()
        candidate = (root / target_folder).resolve()

        try:
            candidate.relative_to(root)
        except ValueError:
            return None

        return str(candidate)

    @staticmethod
    def _is_already_in_target(source_file: Path, target_path: str) -> bool:
        try:
            source_parent = source_file.parent.resolve()
            target_parent = Path(target_path).expanduser().resolve()
            return source_parent == target_parent
        except OSError:
            return False

    @staticmethod
    def _extract_source_path(workspace_context: dict[str, object]) -> Path | None:
        for key in ("file_path", "path", "source_path"):
            value = workspace_context.get(key)
            if value:
                return Path(str(value)).expanduser()
        return None

    @staticmethod
    def _as_optional_str(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _as_float(value: object) -> float:
        try:
            parsed = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, parsed))

    @staticmethod
    def _decision_confidence(*, analyzer_confidence: float, rule_clarity: float) -> float:
        combined = (analyzer_confidence * 0.7) + (rule_clarity * 0.3)
        return round(max(0.0, min(1.0, combined)), 3)
