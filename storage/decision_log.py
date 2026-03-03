"""
PHASE 1: Decision Logger
Comprehensive logging of all file processing decisions with full transparency.
Every file decision is logged to JSON for audit, analysis, and debugging.
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any


DECISION_LOG_FILE = "D:/AUTOMATION/decision_log.json"


def _load_decision_log() -> list:
    """Load existing decision log from JSON file."""
    if not os.path.exists(DECISION_LOG_FILE):
        return []
    try:
        with open(DECISION_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"⚠️  Decision log load failed: {e}")
        return []


def _save_decision_log(log_entries: list) -> None:
    """Save decision log to JSON file."""
    try:
        with open(DECISION_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_entries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Decision log save failed: {e}")


def log_decision(
    file_path: str,
    action: str,
    reason: str,
    category: Optional[str] = None,
    subject: Optional[str] = None,
    destination: Optional[str] = None,
    confidence: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a file processing decision with full details.

    Args:
        file_path: Full path to the file
        action: "moved" | "skipped" | "duplicate" | "error"
        reason: Human-readable explanation (e.g., "keyword 'assignment' detected")
        category: Detected category (COLLEGE, PROGRAMMING, etc.)
        subject: Detected subject (Operating Systems, etc.)
        destination: Final destination path
        confidence: Semantic confidence score (0-1)
        details: Additional metadata
    """

    file_name = os.path.basename(file_path)
    file_size = 0
    if os.path.exists(file_path):
        try:
            file_size = os.path.getsize(file_path)
        except:
            pass

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": file_name,
        "file_path": file_path,
        "file_size_bytes": file_size,
        "action": action,
        "reason": reason,
        "category": category,
        "subject": subject,
        "destination": destination,
        "confidence": confidence,
        "details": details or {},
    }

    log_entries = _load_decision_log()
    log_entries.append(log_entry)
    _save_decision_log(log_entries)


def get_decision_log() -> list:
    """Retrieve the full decision log."""
    return _load_decision_log()


def get_decisions_by_action(action: str) -> list:
    """Get all decisions of a specific action type."""
    log = _load_decision_log()
    return [entry for entry in log if entry.get("action") == action]


def get_decisions_by_file(file_name: str) -> list:
    """Get all decisions related to a specific file."""
    log = _load_decision_log()
    return [
        entry for entry in log if file_name.lower() in entry.get("file", "").lower()
    ]


def clear_decision_log() -> None:
    """Clear the decision log (for testing/reset)."""
    _save_decision_log([])


def print_log_summary() -> None:
    """Print a summary of the decision log."""
    log = _load_decision_log()
    if not log:
        print("📋 Decision log is empty.")
        return

    moved = len([e for e in log if e.get("action") == "moved"])
    skipped = len([e for e in log if e.get("action") == "skipped"])
    duplicates = len([e for e in log if e.get("action") == "duplicate"])
    errors = len([e for e in log if e.get("action") == "error"])

    print("\n" + "=" * 60)
    print("📊 DECISION LOG SUMMARY")
    print("=" * 60)
    print(f"Files Moved:      {moved}")
    print(f"Files Skipped:    {skipped}")
    print(f"Duplicates Found: {duplicates}")
    print(f"Processing Errors: {errors}")
    print(f"Total Entries:    {len(log)}")
    print(f"Log File:         {DECISION_LOG_FILE}")
    print("=" * 60 + "\n")
