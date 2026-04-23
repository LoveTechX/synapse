"""Real-time filesystem watcher built on watchdog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from workspace_intelligence.config.models import WorkspaceIntelligenceConfig

logger = logging.getLogger(__name__)

EventCallback = Callable[[str, Path, WorkspaceIntelligenceConfig], None]


def _looks_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _is_ignored(path: Path, config: WorkspaceIntelligenceConfig) -> bool:
    if not config.watcher.include_hidden and _looks_hidden(path):
        return True

    ignore_names = {Path(folder).name for folder in config.rules.ignore_folders}
    if any(part in ignore_names for part in path.parts):
        return True

    return False


def print_file_event(event_type: str, path: Path, config: WorkspaceIntelligenceConfig) -> None:
    """Default event printer used by the watcher."""

    del config
    print(f"[{event_type.upper()}] {path}")


class WorkspaceFileEventHandler(FileSystemEventHandler):
    """Translate watchdog events into a small, safe callback surface."""

    def __init__(self, config: WorkspaceIntelligenceConfig, on_event: EventCallback | None = None) -> None:
        self.config = config
        self.on_event = on_event or print_file_event

    def on_created(self, event: FileSystemEvent) -> None:
        self._emit("created", event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._emit("moved", event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._emit("modified", event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._emit("deleted", event)

    def _emit(self, event_type: str, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        path = Path(getattr(event, "dest_path", None) or event.src_path)
        if _is_ignored(path, self.config):
            return

        self.on_event(event_type, path, self.config)


class WorkspaceWatcher:
    """Manage observer lifecycle for the workspace intelligence engine."""

    def __init__(
        self,
        config: WorkspaceIntelligenceConfig,
        on_event: EventCallback | None = None,
    ) -> None:
        self.config = config
        self._observer = Observer()
        self._handler = WorkspaceFileEventHandler(config, on_event=on_event)
        self._scheduled_roots: list[Path] = []

    def _iter_roots(self) -> list[Path]:
        roots = self.config.watcher.roots or [self.config.workspace_root]
        return [Path(root).expanduser() for root in roots]

    def start(self) -> None:
        roots = self._iter_roots()
        if not roots:
            raise ValueError("At least one watcher root must be configured.")

        for root in roots:
            if not root.exists():
                logger.warning("Skipping missing watcher root: %s", root)
                continue

            self._observer.schedule(
                self._handler,
                str(root),
                recursive=self.config.watcher.recursive,
            )
            self._scheduled_roots.append(root)

        if not self._scheduled_roots:
            raise FileNotFoundError("No valid watcher roots exist on disk.")

        self._observer.start()
        logger.info("Watching %d root(s) for workspace changes.", len(self._scheduled_roots))

    def stop(self) -> None:
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)

    def wait(self) -> None:
        self._observer.join()

    def __enter__(self) -> "WorkspaceWatcher":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb
        self.stop()
