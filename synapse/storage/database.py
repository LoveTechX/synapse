"""SQLite persistence for Synapse AI metadata."""

import json
import sqlite3
from pathlib import Path

from synapse.models.file_model import FileModel


class FileDatabase:
    """Small SQLite wrapper focused on file metadata persistence."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = str(database_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        """Create the file metadata table when missing."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save_file(self, file_model: FileModel) -> int:
        """Insert one processed file and return its database id."""
        if not isinstance(file_model, FileModel):
            raise ValueError("file_model must be an instance of FileModel")

        # Basic pre-insert validation for required fields.
        required_text_fields = {
            "name": file_model.name,
            "path": file_model.path,
            "content": file_model.content,
            "category": file_model.category,
            "explanation": file_model.explanation,
            "created_at": file_model.created_at,
        }
        for field_name, value in required_text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        if not isinstance(file_model.tags, list) or not all(
            isinstance(tag, str) for tag in file_model.tags
        ):
            raise ValueError("tags must be a list of strings")

        try:
            tags_json = json.dumps(file_model.tags, ensure_ascii=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("tags must be JSON serializable") from exc

        insert_sql = """
            INSERT INTO files (name, path, content, category, tags, explanation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        insert_values = (
            file_model.name.strip(),
            file_model.path.strip(),
            file_model.content,
            file_model.category.strip(),
            tags_json,
            file_model.explanation,
            file_model.created_at.strip(),
        )

        connection = self._connect()
        try:
            cursor = connection.execute(insert_sql, insert_values)
            connection.commit()

            row_id = cursor.lastrowid
            if row_id is None:
                raise sqlite3.DatabaseError("insert did not return a row id")
            return int(row_id)
        except sqlite3.Error as exc:
            connection.rollback()
            raise sqlite3.DatabaseError(f"failed to insert file metadata: {exc}") from exc
        finally:
            connection.close()
