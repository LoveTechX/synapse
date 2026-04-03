"""Data model for processed files in Synapse AI."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FileModel:
    """Represents one processed file record in the MVP pipeline."""

    id: Optional[int]
    name: str
    path: str
    content: str
    category: str
    tags: List[str]
    explanation: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe representation of this model."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "explanation": self.explanation,
            "created_at": self.created_at,
        }
