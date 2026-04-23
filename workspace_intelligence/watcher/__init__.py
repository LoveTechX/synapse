"""Filesystem watcher package for the workspace intelligence engine."""

from .service import WorkspaceWatcher, print_file_event

__all__ = ["WorkspaceWatcher", "print_file_event"]
