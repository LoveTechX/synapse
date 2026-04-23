"""Workspace analyzer for fast file-event context detection.

This module intentionally keeps logic deterministic and lightweight for Phase 1.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, TypedDict

ProjectType = Literal["git", "python", "node", "java", "generic"]
EventType = Literal["created", "modified", "deleted", "moved"]
FileRole = Literal[
    "source_code",
    "config",
    "dependency",
    "build_output",
    "log",
    "binary",
    "temp",
    "unknown",
]


class WorkspaceContext(TypedDict):
    """Context envelope returned for each file path analysis."""

    is_project: bool
    project_root: str | None
    project_type: str | None
    is_nested_project: bool
    is_safe_zone: bool
    file_role: str
    is_critical_file: bool
    project_confidence: float
    role_confidence: float
    location_confidence: float
    overall_confidence: float
    context_confidence: float
    recommended_action: str
    reason: str


PROJECT_MARKER_RULES: tuple[tuple[str, ProjectType, int], ...] = (
    (".git", "git", 100),
    ("pyproject.toml", "python", 90),
    ("requirements.txt", "python", 85),
    ("setup.py", "python", 80),
    (".venv", "python", 70),
    ("venv", "python", 65),
    ("package.json", "node", 75),
    ("node_modules", "node", 60),
    ("pom.xml", "java", 70),
    ("Makefile", "generic", 40),
)

DEFAULT_SAFE_ZONE_NAMES: set[str] = {
    "src",
    "tests",
    "node_modules",
    ".git",
    "build",
    "dist",
    "venv",
    ".venv",
    "__pycache__",
    "pycache",
}

SOURCE_CODE_EXTENSIONS: set[str] = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".kts",
    ".scala",
    ".sh",
    ".bat",
    ".ps1",
}

CONFIG_NAMES: set[str] = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pipfile",
    "pipfile.lock",
    "poetry.lock",
    "setup.py",
    "setup.cfg",
    "pom.xml",
    "gradle.properties",
    "settings.gradle",
    "build.gradle",
    "tsconfig.json",
    "next.config.js",
    "webpack.config.js",
    "vite.config.ts",
    "dockerfile",
    "makefile",
    ".gitignore",
    ".editorconfig",
}

CONFIG_EXTENSIONS: set[str] = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
    ".xml",
}

DEPENDENCY_FILENAMES: set[str] = {
    "requirements.txt",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yml",
    "cargo.lock",
    "go.sum",
    "composer.lock",
    "pom.xml",
}

DEPENDENCY_DIRECTORIES: set[str] = {
    "node_modules",
    "venv",
    ".venv",
    "site-packages",
}

BUILD_OUTPUT_DIRECTORIES: set[str] = {
    "build",
    "dist",
    "target",
    "out",
    ".next",
    "coverage",
}

BUILD_OUTPUT_EXTENSIONS: set[str] = {
    ".class",
    ".pyc",
    ".pyo",
    ".o",
    ".obj",
    ".a",
    ".lib",
}

LOG_EXTENSIONS: set[str] = {".log"}
LOG_FILENAMES: set[str] = {"debug.log", "error.log", "access.log", "application.log"}

BINARY_EXTENSIONS: set[str] = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pyd",
    ".whl",
}

TEMP_EXTENSIONS: set[str] = {
    ".tmp",
    ".temp",
    ".swp",
    ".swo",
    ".bak",
    ".cache",
}

TEMP_PREFIXES: tuple[str, ...] = (".~", "tmp", "temp")
TEMP_SUFFIXES: tuple[str, ...] = ("~", ".tmp", ".temp", ".bak")

CRITICAL_FILENAMES: set[str] = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "dockerfile",
    "makefile",
}

ROLE_CONFIDENCE_BY_ROLE: dict[str, float] = {
    "source_code": 0.85,
    "config": 0.9,
    "dependency": 0.93,
    "build_output": 0.88,
    "log": 0.92,
    "binary": 0.87,
    "temp": 0.86,
    "unknown": 0.4,
}

EVENT_CONFIDENCE_BIAS: dict[str, float] = {
    "created": 0.03,
    "modified": 0.02,
    "deleted": -0.04,
    "moved": -0.01,
}

PROJECT_CONFIDENCE_WEIGHT = 0.4
ROLE_CONFIDENCE_WEIGHT = 0.3
LOCATION_CONFIDENCE_WEIGHT = 0.3


@dataclass(slots=True)
class _ProjectDetection:
    project_root: Path | None
    project_type: str | None
    marker_count: int
    marker_priority: int
    root_distance: int


@dataclass(slots=True)
class WorkspaceAnalyzer:
    """Analyze file paths to infer project and file context."""

    workspace_root: str | None = None
    safe_zones: Iterable[str] | None = None
    cache_size: int = 1024

    @classmethod
    def from_config(cls, config: object, cache_size: int = 1024) -> "WorkspaceAnalyzer":
        """Build an analyzer from a workspace config-like object."""

        workspace_root = getattr(config, "workspace_root", None)
        rules = getattr(config, "rules", None)
        safe_zones = getattr(rules, "safe_zones", None)
        return cls(workspace_root=workspace_root, safe_zones=safe_zones, cache_size=cache_size)

    def __post_init__(self) -> None:
        self._workspace_root_path = self._normalize(self.workspace_root) if self.workspace_root else None
        self._safe_zone_names = set(DEFAULT_SAFE_ZONE_NAMES)
        self._safe_zone_paths: set[Path] = set()
        self._project_cache: OrderedDict[tuple[str, str, str], _ProjectDetection] = OrderedDict()

        for zone in self.safe_zones or ():
            raw_zone = str(zone).strip()
            if not raw_zone:
                continue

            looks_like_path = (
                "/" in raw_zone
                or "\\" in raw_zone
                or Path(raw_zone).is_absolute()
            )
            if looks_like_path:
                zone_path = Path(raw_zone).expanduser()
                if not zone_path.is_absolute() and self._workspace_root_path is not None:
                    zone_path = self._workspace_root_path / zone_path
                self._safe_zone_paths.add(zone_path.resolve())
            else:
                self._safe_zone_names.add(raw_zone)

    def analyze(self, file_path: str | Path, event_type: EventType | str = "modified") -> WorkspaceContext:
        """Return a deterministic workspace context for the given file path."""

        candidate = self._normalize(file_path)
        normalized_event = self._normalize_event_type(event_type)
        detection = self._detect_project(candidate, normalized_event)
        is_nested_project = self._is_nested_project(detection.project_root)
        is_safe_zone = self._is_safe_zone(candidate, detection.project_root)
        file_role = self._detect_file_role(candidate)
        is_critical_file = self._is_critical_file(candidate)

        project_confidence = self._project_confidence(detection, is_nested_project)
        role_confidence = self._role_confidence(file_role, is_critical_file)
        location_confidence = self._location_confidence(is_safe_zone, detection.root_distance, normalized_event)
        overall_confidence = self._overall_confidence(
            project_confidence=project_confidence,
            role_confidence=role_confidence,
            location_confidence=location_confidence,
            is_critical_file=is_critical_file,
        )
        recommended_action = self._recommended_action(
            is_critical_file=is_critical_file,
            is_safe_zone=is_safe_zone,
            overall_confidence=overall_confidence,
        )
        reason = self._build_reason(
            detection=detection,
            file_path=candidate,
            is_safe_zone=is_safe_zone,
            is_critical_file=is_critical_file,
            recommended_action=recommended_action,
        )

        return {
            "is_project": detection.project_root is not None,
            "project_root": str(detection.project_root) if detection.project_root else None,
            "project_type": detection.project_type,
            "is_nested_project": is_nested_project,
            "is_safe_zone": is_safe_zone,
            "file_role": file_role,
            "is_critical_file": is_critical_file,
            "project_confidence": project_confidence,
            "role_confidence": role_confidence,
            "location_confidence": location_confidence,
            "overall_confidence": overall_confidence,
            "context_confidence": overall_confidence,
            "recommended_action": recommended_action,
            "reason": reason,
        }

    @staticmethod
    def _normalize(path_value: str | Path) -> Path:
        return Path(path_value).expanduser().resolve()

    def _iter_candidate_roots(self, file_path: Path) -> list[Path]:
        parents = [file_path.parent, *file_path.parents]
        if self._workspace_root_path is None:
            return parents

        candidates: list[Path] = []
        for parent in parents:
            candidates.append(parent)
            if parent == self._workspace_root_path:
                break
        return candidates

    def _detect_project(self, file_path: Path, event_type: str) -> _ProjectDetection:
        cache_key = (str(file_path.parent), file_path.suffix.lower(), event_type)
        cached = self._project_cache.get(cache_key)
        if cached is not None:
            # OrderedDict + move_to_end gives true LRU behavior.
            self._project_cache.move_to_end(cache_key)
            return cached

        result = self._detect_project_uncached(file_path)
        self._project_cache[cache_key] = result
        if len(self._project_cache) > max(1, self.cache_size):
            # Drop least-recently-used entry.
            self._project_cache.popitem(last=False)
        return result

    def _detect_project_uncached(self, file_path: Path) -> _ProjectDetection:
        candidates = self._iter_candidate_roots(file_path)
        for distance, parent in enumerate(candidates):
            marker_type, marker_count, marker_priority = self._project_type_from_markers(parent)
            if marker_type is not None:
                return _ProjectDetection(
                    project_root=parent,
                    project_type=marker_type,
                    marker_count=marker_count,
                    marker_priority=marker_priority,
                    root_distance=distance,
                )

        return _ProjectDetection(
            project_root=None,
            project_type=None,
            marker_count=0,
            marker_priority=0,
            root_distance=0,
        )

    @staticmethod
    def _project_type_from_markers(directory: Path) -> tuple[str | None, int, int]:
        matches: list[tuple[int, str]] = []
        for marker, project_type, priority in PROJECT_MARKER_RULES:
            if (directory / marker).exists():
                matches.append((priority, project_type))

        if not matches:
            return None, 0, 0

        best_priority, best_type = max(matches, key=lambda item: item[0])
        return best_type, len(matches), best_priority

    def _is_nested_project(self, project_root: Path | None) -> bool:
        if project_root is None:
            return False

        for parent in project_root.parents:
            marker_type, _, _ = self._project_type_from_markers(parent)
            if marker_type is not None:
                return True
            if self._workspace_root_path is not None and parent == self._workspace_root_path:
                break

        return False

    def _is_safe_zone(self, file_path: Path, project_root: Path | None) -> bool:
        if project_root is not None:
            try:
                relative_parts = file_path.relative_to(project_root).parts
            except ValueError:
                relative_parts = file_path.parts
        else:
            relative_parts = file_path.parts

        if any(part in self._safe_zone_names for part in relative_parts):
            return True

        for zone_path in self._safe_zone_paths:
            try:
                file_path.relative_to(zone_path)
                return True
            except ValueError:
                continue

        return False

    @staticmethod
    def _detect_file_role(file_path: Path) -> str:
        name = file_path.name
        lower_name = name.lower()
        suffix = file_path.suffix.lower()
        parts_lower = {part.lower() for part in file_path.parts}

        if parts_lower.intersection(DEPENDENCY_DIRECTORIES) or lower_name in DEPENDENCY_FILENAMES:
            return "dependency"

        if parts_lower.intersection(BUILD_OUTPUT_DIRECTORIES) or suffix in BUILD_OUTPUT_EXTENSIONS:
            return "build_output"

        if suffix in LOG_EXTENSIONS or lower_name in LOG_FILENAMES:
            return "log"

        if suffix in BINARY_EXTENSIONS:
            return "binary"

        if lower_name in CONFIG_NAMES or suffix in CONFIG_EXTENSIONS:
            return "config"

        if suffix in SOURCE_CODE_EXTENSIONS:
            return "source_code"

        if suffix in TEMP_EXTENSIONS:
            return "temp"
        if lower_name.startswith(TEMP_PREFIXES) or lower_name.endswith(TEMP_SUFFIXES):
            return "temp"

        return "unknown"

    @staticmethod
    def _is_critical_file(file_path: Path) -> bool:
        return file_path.name.lower() in CRITICAL_FILENAMES

    @staticmethod
    def _normalize_event_type(event_type: EventType | str) -> str:
        return str(event_type).strip().lower()

    @staticmethod
    def _project_confidence(detection: _ProjectDetection, is_nested_project: bool) -> float:
        confidence = 0.1

        if detection.project_root is not None:
            confidence += 0.5
            confidence += min(0.2, detection.marker_count * 0.05)
            confidence += min(0.15, detection.marker_priority / 700)
            confidence += max(0.0, 0.08 - (detection.root_distance * 0.015))

        if is_nested_project:
            confidence -= 0.05

        return round(max(0.0, min(1.0, confidence)), 3)

    @staticmethod
    def _role_confidence(file_role: str, is_critical_file: bool) -> float:
        confidence = ROLE_CONFIDENCE_BY_ROLE.get(file_role, 0.4)
        if is_critical_file:
            confidence = min(1.0, confidence + 0.05)
        return round(confidence, 3)

    @staticmethod
    def _location_confidence(is_safe_zone: bool, root_distance: int, event_type: str) -> float:
        confidence = 0.45

        if is_safe_zone:
            confidence += 0.35

        confidence += max(0.0, 0.15 - (root_distance * 0.02))
        confidence += EVENT_CONFIDENCE_BIAS.get(event_type, 0.0)

        return round(max(0.0, min(1.0, confidence)), 3)

    @staticmethod
    def _overall_confidence(
        *,
        project_confidence: float,
        role_confidence: float,
        location_confidence: float,
        is_critical_file: bool,
    ) -> float:
        overall = (
            (project_confidence * PROJECT_CONFIDENCE_WEIGHT)
            + (role_confidence * ROLE_CONFIDENCE_WEIGHT)
            + (location_confidence * LOCATION_CONFIDENCE_WEIGHT)
        )

        if is_critical_file:
            overall = min(overall, 0.4)

        return round(max(0.0, min(1.0, overall)), 3)

    @staticmethod
    def _recommended_action(*, is_critical_file: bool, is_safe_zone: bool, overall_confidence: float) -> str:
        if is_critical_file:
            return "review"
        if is_safe_zone and overall_confidence >= 0.75:
            return "ignore"
        if overall_confidence >= 0.45:
            return "suggest"
        return "review"

    @staticmethod
    def _primary_marker_for_project_type(project_type: str | None) -> str | None:
        if project_type is None:
            return None

        for marker, marker_project_type, _priority in PROJECT_MARKER_RULES:
            if marker_project_type == project_type:
                return marker
        return None

    def _build_reason(
        self,
        *,
        detection: _ProjectDetection,
        file_path: Path,
        is_safe_zone: bool,
        is_critical_file: bool,
        recommended_action: str,
    ) -> str:
        reasons: list[str] = []

        if detection.project_type is not None:
            marker = self._primary_marker_for_project_type(detection.project_type)
            if marker is not None:
                reasons.append(f"Detected {detection.project_type} project via {marker}")
            else:
                reasons.append(f"Detected {detection.project_type} project")
        else:
            reasons.append("No project markers detected")

        if is_safe_zone:
            safe_part = self._matched_safe_zone_name(file_path, detection.project_root)
            if safe_part is not None:
                reasons.append(f"File inside safe zone: {safe_part}/")
            else:
                reasons.append("File inside configured safe zone")

        if is_critical_file:
            reasons.append("Critical config file")

        reasons.append(f"Recommended action: {recommended_action}")
        return "; ".join(reasons)

    def _matched_safe_zone_name(self, file_path: Path, project_root: Path | None) -> str | None:
        if project_root is not None:
            try:
                relative_parts = file_path.relative_to(project_root).parts
            except ValueError:
                relative_parts = file_path.parts
        else:
            relative_parts = file_path.parts

        for part in relative_parts:
            if part in self._safe_zone_names:
                return part
        return None
