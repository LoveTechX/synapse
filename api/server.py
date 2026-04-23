"""
🧠 SYNAPSE API Server

FastAPI backend for Synapse Dashboard.
Provides analytics, decision logs, and system configuration endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services import analytics_service
from storage import database
from storage.decision_log import get_decision_log, get_decisions_by_file

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app with CORS for dashboard integration
app = FastAPI(
    title="🧠 Synapse API",
    description="AI Workspace Engine - Analytics and Intelligence API",
    version="1.0.0",
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "🧠 Synapse API",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/info")
async def system_info() -> Dict[str, Any]:
    """Get system information."""
    return {
        "name": "🧠 SYNAPSE — AI Workspace Engine",
        "version": "1.0.0",
        "description": "AI-powered developer workspace intelligence",
        "api_version": "1.0.0",
    }


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get system statistics.

    Returns:
        Dictionary with total files, today's count, and system health metrics.
    """
    try:
        total_files = database.get_total_files()
        today_count = database.get_today_count()

        return {
            "total_files": total_files,
            "today_files": today_count,
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@app.get("/categories")
async def get_categories() -> Dict[str, Any]:
    """
    Get file distribution by category.

    Returns:
        Dictionary with category counts and total files.
    """
    try:
        stats = database.get_category_stats()

        return {
            "categories": stats,
            "total": sum(item["count"] for item in stats),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve category statistics"
        )


@app.get("/confidence")
async def get_confidence_distribution() -> Dict[str, Any]:
    """
    Get confidence score distribution.

    Returns:
        Dictionary with confidence buckets and counts.
    """
    try:
        distribution = database.get_confidence_distribution()

        return {
            "distribution": distribution,
            "total": sum(item["count"] for item in distribution),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get confidence distribution: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve confidence distribution"
        )


# ============================================================================
# ACTIVITY ENDPOINTS
# ============================================================================


@app.get("/activity")
async def get_activity(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent file activity/decisions.

    Args:
        limit: Maximum number of records to return (default 50)

    Returns:
        List of recent file decisions with metadata.
    """
    try:
        if limit > 500:
            limit = 500  # Safety cap

        log_entries = get_decision_log()

        # Sort by timestamp descending and limit
        recent = sorted(
            log_entries, key=lambda x: x.get("timestamp", ""), reverse=True
        )[:limit]

        return {
            "activity": recent,
            "count": len(recent),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity log")


@app.get("/activity/today")
async def get_today_activity() -> Dict[str, Any]:
    """
    Get today's file activity.

    Returns:
        List of file decisions from today.
    """
    try:
        log_entries = get_decision_log()

        # Filter entries from today
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_entries = [
            entry
            for entry in log_entries
            if entry.get("timestamp")
            and datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            >= today_start
        ]

        return {
            "activity": today_entries,
            "count": len(today_entries),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get today's activity: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve today's activity"
        )


@app.get("/activity/file/{file_name}")
async def get_file_activity(file_name: str) -> Dict[str, Any]:
    """
    Get activity for a specific file.

    Args:
        file_name: Name of the file to look up

    Returns:
        List of decisions/activities for the specified file.
    """
    try:
        decisions = get_decisions_by_file(file_name)

        return {
            "file_name": file_name,
            "activity": decisions if decisions else [],
            "count": len(decisions) if decisions else 0,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get file activity for {file_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file activity")


# ============================================================================
# SUMMARY ENDPOINTS
# ============================================================================


@app.get("/summary")
async def get_summary() -> Dict[str, Any]:
    """
    Get comprehensive system summary.

    Returns:
        Combined statistics for dashboard overview.
    """
    try:
        return analytics_service.get_summary()
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary")


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================


@app.get("/settings")
async def get_settings() -> Dict[str, Any]:
    """
    Get system settings and configuration.

    Returns:
        Current system configuration.
    """
    return {
        "confidence_thresholds": {
            "high": 0.80,
            "medium": 0.60,
            "low": 0.40,
        },
        "preview_mode": False,
        "auto_mode": True,
        "monitoring_enabled": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/settings")
async def update_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update system settings.

    Args:
        settings: Configuration dictionary to update

    Returns:
        Updated settings confirmation.
    """
    # This would update system configuration
    # For now, just return confirmation
    return {
        "status": "settings_updated",
        "settings": settings,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root API endpoint with available endpoints."""
    return {
        "message": "🧠 SYNAPSE API - AI Workspace Engine",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "stats": "/stats",
            "categories": "/categories",
            "confidence": "/confidence",
            "activity": "/activity",
            "activity/today": "/activity/today",
            "activity/file/{file_name}": "/activity/file/{file_name}",
            "summary": "/summary",
            "settings": "/settings",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
