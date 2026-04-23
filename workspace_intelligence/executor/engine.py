"""Safe action executor and end-to-end workspace pipeline."""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from workspace_intelligence.decision import Decision, DecisionEngine
from workspace_intelligence.workspace import WorkspaceAnalyzer, WorkspaceContext


class ExecutionResult(TypedDict):
    """Execution response returned by the action executor."""

    executed: bool
    success: bool
    action: str
    execution_type: str
    message: str
    operation_id: str
    source_path: str | None
    target_path: str | None


class PipelineResult(TypedDict):
    """Full pipeline result for an incoming file event."""

    context: WorkspaceContext
    decision: Decision
    execution_result: ExecutionResult
    pipeline_steps: list[str]


SYSTEM_HIDDEN_FILENAMES: set[str] = {
    "thumbs.db",
    "desktop.ini",
    ".ds_store",
}

FILTERED_TEMP_EXTENSIONS: set[str] = {".tmp", ".swp"}
DEFAULT_COLLISION_POLICY = "BLOCK"


@dataclass(slots=True)
class ActionExecutor:
    """Execute or simulate decisions with strict safety guards."""

    dry_run: bool = True
    allow_real_execution: bool = False
    collision_policy: str = DEFAULT_COLLISION_POLICY

    def execute(
        self,
        decision: Decision,
        project_root: str | None = None,
        source_path: str | None = None,
    ) -> ExecutionResult:
        """Execute a decision safely, defaulting to simulation mode."""

        action = str(decision.get("action", "IGNORE"))
        target_path = decision.get("target_path")
        requires_confirmation = bool(decision.get("requires_confirmation", False))
        operation_id = str(uuid.uuid4())

        if requires_confirmation:
            return {
                "executed": False,
                "success": True,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "Execution blocked: requires manual confirmation.",
                "operation_id": operation_id,
                "source_path": source_path,
                "target_path": self._as_optional_str(target_path),
            }

        if action == "IGNORE":
            return {
                "executed": False,
                "success": True,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "No operation performed (IGNORE).",
                "operation_id": operation_id,
                "source_path": source_path,
                "target_path": self._as_optional_str(target_path),
            }

        if action == "SUGGEST":
            return {
                "executed": False,
                "success": True,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "Suggestion logged; no filesystem change performed.",
                "operation_id": operation_id,
                "source_path": source_path,
                "target_path": self._as_optional_str(target_path),
            }

        if action != "MOVE":
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": f"Unknown action: {action}",
                "operation_id": operation_id,
                "source_path": source_path,
                "target_path": self._as_optional_str(target_path),
            }

        if not isinstance(target_path, str) or not target_path.strip():
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "MOVE requested but target_path is missing.",
                "operation_id": operation_id,
                "source_path": source_path,
                "target_path": None,
            }

        if project_root is None:
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "MOVE blocked: project_root is required for safety checks.",
                "operation_id": operation_id,
                "source_path": source_path,
                "target_path": self._as_optional_str(target_path),
            }

        if not isinstance(source_path, str) or not source_path.strip():
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "MOVE blocked: source_path is required.",
                "operation_id": operation_id,
                "source_path": None,
                "target_path": self._as_optional_str(target_path),
            }

        root = Path(project_root).expanduser().resolve()
        source = Path(source_path).expanduser().resolve()
        target = Path(target_path).expanduser().resolve()

        try:
            source.relative_to(root)
            target.relative_to(root)
        except ValueError:
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "MOVE blocked: source or target is outside project_root.",
                "operation_id": operation_id,
                "source_path": str(source),
                "target_path": str(target),
            }

        if not source.exists():
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "MOVE blocked: source file does not exist.",
                "operation_id": operation_id,
                "source_path": str(source),
                "target_path": str(target),
            }

        if target.exists() and self.collision_policy == "BLOCK":
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": "Target file already exists",
                "operation_id": operation_id,
                "source_path": str(source),
                "target_path": str(target),
            }

        if self.dry_run:
            return {
                "executed": False,
                "success": True,
                "action": action,
                "execution_type": "SIMULATION",
                "message": f"[DRY RUN] Would move file from {source} to {target}.",
                "operation_id": operation_id,
                "source_path": str(source),
                "target_path": str(target),
            }

        if not self.allow_real_execution:
            return {
                "executed": False,
                "success": True,
                "action": action,
                "execution_type": "SIMULATION",
                "message": "[BLOCKED] Real execution disabled",
                "operation_id": operation_id,
                "source_path": str(source),
                "target_path": str(target),
            }

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
        except OSError as exc:
            return {
                "executed": False,
                "success": False,
                "action": action,
                "execution_type": "BLOCKED",
                "message": f"MOVE failed: {exc}",
                "operation_id": operation_id,
                "source_path": str(source),
                "target_path": str(target),
            }

        return {
            "executed": True,
            "success": True,
            "action": action,
            "execution_type": "REAL",
            "message": "File moved successfully",
            "operation_id": operation_id,
            "source_path": str(source),
            "target_path": str(target),
        }


@dataclass(slots=True)
class WorkspacePipeline:
    """Minimal analyzer -> decision -> executor orchestration."""

    analyzer: WorkspaceAnalyzer = field(default_factory=WorkspaceAnalyzer)
    decision_engine: DecisionEngine = field(default_factory=DecisionEngine)
    executor: ActionExecutor = field(default_factory=ActionExecutor)

    def process_event(self, file_path: str, event_type: str) -> PipelineResult:
        """Process one file event through context, decision, and execution stages."""

        steps: list[str] = []
        try:
            source_path = Path(file_path).expanduser()
            if self._should_filter_event(source_path):
                context = self._fallback_context(file_path=file_path, event_type=event_type, reason="Event filtered.")
                decision: Decision = {
                    "action": "IGNORE",
                    "target_path": None,
                    "requires_confirmation": False,
                    "reason": "Event filtered (temporary or hidden system file).",
                    "decision_confidence": 0.99,
                }
                execution_result: ExecutionResult = {
                    "executed": False,
                    "success": True,
                    "action": "IGNORE",
                    "execution_type": "BLOCKED",
                    "message": "Event ignored by filter policy.",
                }
                steps.extend(["event_filtered", "decision_made", "execution_blocked"])
                return {
                    "context": context,
                    "decision": decision,
                    "execution_result": execution_result,
                    "pipeline_steps": steps,
                }

            context = self.analyzer.analyze(file_path=file_path, event_type=event_type)
            steps.append("analyzed")

            decision_input: dict[str, object] = dict(context)
            decision_input["source_path"] = file_path
            decision = self.decision_engine.decide(decision_input)
            steps.append("decision_made")

            execution_result = self.executor.execute(
                decision,
                project_root=context.get("project_root"),
                source_path=file_path,
            )
            steps.append(self._execution_step(execution_result))

            return {
                "context": context,
                "decision": decision,
                "execution_result": execution_result,
                "pipeline_steps": steps,
            }
        except Exception as exc:  # pragma: no cover - safety fallback path
            context = self._fallback_context(file_path=file_path, event_type=event_type, reason=str(exc))
            decision = {
                "action": "IGNORE",
                "target_path": None,
                "requires_confirmation": False,
                "reason": f"Pipeline fallback due to error: {exc}",
                "decision_confidence": 1.0,
            }
            execution_result = {
                "executed": False,
                "success": False,
                "action": "IGNORE",
                "execution_type": "BLOCKED",
                "message": f"Pipeline error handled safely: {exc}",
            }
            steps.extend(["error_fallback", "decision_made", "execution_blocked"])
            return {
                "context": context,
                "decision": decision,
                "execution_result": execution_result,
                "pipeline_steps": steps,
            }

    @staticmethod
    def _should_filter_event(file_path: Path) -> bool:
        lower_name = file_path.name.lower()
        if file_path.suffix.lower() in FILTERED_TEMP_EXTENSIONS:
            return True
        if lower_name in SYSTEM_HIDDEN_FILENAMES:
            return True
        if lower_name.startswith("."):
            return True
        return False

    @staticmethod
    def _execution_step(execution_result: ExecutionResult) -> str:
        execution_type = execution_result.get("execution_type", "BLOCKED")
        if execution_type == "SIMULATION":
            return "execution_simulated"
        if execution_type == "REAL":
            return "execution_completed"
        return "execution_blocked"

    @staticmethod
    def _as_optional_str(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _fallback_context(file_path: str, event_type: str, reason: str) -> WorkspaceContext:
        del event_type
        return {
            "is_project": False,
            "project_root": None,
            "project_type": None,
            "is_nested_project": False,
            "is_safe_zone": False,
            "file_role": "unknown",
            "is_critical_file": False,
            "project_confidence": 0.0,
            "role_confidence": 0.0,
            "location_confidence": 0.0,
            "overall_confidence": 0.0,
            "context_confidence": 0.0,
            "recommended_action": "review",
            "reason": f"Fallback context for {file_path}: {reason}",
        }
