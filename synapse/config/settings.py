"""Application settings for the Synapse AI MVP."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "organized_files"
DATABASE_PATH = BASE_DIR / "synapse.db"

# Folder names used for final file routing.
CATEGORY_FOLDERS = {
    "COLLEGE": "college",
    "PROGRAMMING": "programming",
    "PROJECTS": "projects",
    "CAREER": "career",
    "REFERENCE": "reference",
    "GENERAL": "general",
}

# Fallback category when no strong signal exists.
DEFAULT_CATEGORY = "GENERAL"
