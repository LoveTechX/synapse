"""Analytics service layer for dashboard summary metrics."""

from datetime import datetime
from typing import Any, Dict

from storage import database


def get_summary() -> Dict[str, Any]:
    """Build comprehensive system summary for dashboard overview."""
    total_files = database.get_total_files()
    today_count = database.get_today_count()
    moved_count = database.get_moved_count()
    skipped_count = database.get_skipped_count()
    categories = database.get_category_stats()
    confidence = database.get_confidence_distribution()

    return {
        "overview": {
            "total_files": total_files,
            "today_files": today_count,
            "files_moved": moved_count,
            "files_skipped": skipped_count,
        },
        "categories": categories,
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat(),
    }