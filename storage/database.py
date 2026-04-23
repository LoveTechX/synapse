"""SQLite persistence layer for Synapse decisions."""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).resolve().parent.parent / "organizer.db"


def get_connection() -> sqlite3.Connection:
    """Create a reusable SQLite connection with safe defaults."""
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_database() -> None:
    """Initialize database and schema if not already present."""
    conn = None
    try:
        conn = get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                file_name TEXT,
                category TEXT,
                subject TEXT,
                confidence REAL,
                action TEXT,
                destination TEXT,
                extraction_status TEXT,
                reason TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON decisions(timestamp)")
        conn.commit()
    except Exception:
        logger.exception("Failed to initialize Synapse database")
        raise
    finally:
        if conn is not None:
            conn.close()


def insert_decision(decision_dict: Dict[str, Any]) -> None:
    """Insert a single decision row."""
    conn = None
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO decisions (
                timestamp,
                file_name,
                category,
                subject,
                confidence,
                action,
                destination,
                extraction_status,
                reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_dict.get("timestamp"),
                decision_dict.get("file_name"),
                decision_dict.get("category"),
                decision_dict.get("subject"),
                decision_dict.get("confidence"),
                decision_dict.get("action"),
                decision_dict.get("destination"),
                decision_dict.get("extraction_status"),
                decision_dict.get("reason"),
            ),
        )
        conn.commit()
    finally:
        if conn is not None:
            conn.close()


def _run_scalar(query: str, params: tuple = ()) -> int:
    conn = None
    try:
        conn = get_connection()
        row = conn.execute(query, params).fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    finally:
        if conn is not None:
            conn.close()


def _run_rows(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        if conn is not None:
            conn.close()


def get_total_files() -> int:
    """Total logged decisions."""
    return _run_scalar("SELECT COUNT(*) FROM decisions")


def get_today_count() -> int:
    """Count of decisions logged today (UTC date)."""
    return _run_scalar(
        "SELECT COUNT(*) FROM decisions WHERE date(timestamp) = date('now')"
    )


def get_moved_count() -> int:
    """Count of decisions where action is moved."""
    return _run_scalar("SELECT COUNT(*) FROM decisions WHERE action = ?", ("moved",))


def get_skipped_count() -> int:
    """Count of decisions where action is skipped."""
    return _run_scalar(
        "SELECT COUNT(*) FROM decisions WHERE action = ?", ("skipped",)
    )


def get_category_stats() -> List[Dict[str, Any]]:
    """Grouped counts by category for analytics views."""
    return _run_rows(
        """
        SELECT COALESCE(category, 'UNKNOWN') AS category, COUNT(*) AS count
        FROM decisions
        GROUP BY COALESCE(category, 'UNKNOWN')
        ORDER BY count DESC
        """
    )


def get_confidence_distribution() -> List[Dict[str, Any]]:
    """Bucket confidence values for dashboard charts."""
    return _run_rows(
        """
        SELECT
            CASE
                WHEN confidence IS NULL THEN 'unknown'
                WHEN confidence < 0.4 THEN 'low'
                WHEN confidence < 0.8 THEN 'medium'
                ELSE 'high'
            END AS bucket,
            COUNT(*) AS count
        FROM decisions
        GROUP BY bucket
        ORDER BY bucket
        """
    )
