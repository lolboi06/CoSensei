"""
Persistent task context manager to prevent repeated questions.
Stores clarification answers and tracks conversation state.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class TaskContextManager:
    """Manages persistent task context across conversation turns."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "task_context.sqlite3")
        self.json_path = root / "data" / "task_context.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_mode = "sqlite"
        try:
            self._init_db()
        except sqlite3.Error:
            self.storage_mode = "json"
            self._init_json()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_context (
                    session_id TEXT PRIMARY KEY,
                    context_json TEXT NOT NULL,
                    updated_at TEXT
                )
                """
            )
            conn.commit()

    def _init_json(self) -> None:
        if not self.json_path.exists():
            self.json_path.write_text(json.dumps({"sessions": {}}), encoding="utf-8")

    def _load_json(self) -> dict:
        self._init_json()
        try:
            return json.loads(self.json_path.read_text(encoding="utf-8"))
        except Exception:
            return {"sessions": {}}

    def _save_json(self, payload: dict) -> None:
        self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _default_context(self, session_id: str) -> dict:
        """Return default empty task context."""
        return {
            "session_id": session_id,
            "site_type": None,
            "target_platform": None,
            "language": None,
            "framework": None,
            "database": None,
            "tool_type": None,
            "app_scope": None,
            "player_mode": None,
            "non_implementation": False,
            "current_question": None,
            "asked_questions": [],  # Track which questions have been asked
            "creation_time": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def _load_context(self, session_id: str) -> dict:
        """Load task context from storage."""
        if self.storage_mode == "json":
            payload = self._load_json()
            return payload.get("sessions", {}).get(session_id, self._default_context(session_id))
        
        with self._connect() as conn:
            row = conn.execute(
                "SELECT context_json FROM task_context WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        
        if row is None:
            return self._default_context(session_id)
        try:
            return json.loads(str(row[0]))
        except Exception:
            return self._default_context(session_id)

    def _save_context(self, session_id: str, context: dict) -> None:
        """Save task context to storage."""
        context["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("sessions", {})[session_id] = context
            self._save_json(root)
            return
        
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO task_context(session_id, context_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    context_json=excluded.context_json,
                    updated_at=excluded.updated_at
                """,
                (session_id, json.dumps(context), context["last_updated"]),
            )
            conn.commit()

    def get_context(self, session_id: str) -> dict:
        """Get current task context."""
        return self._load_context(session_id)

    def update_answer(self, session_id: str, field: str, value: Optional[str]) -> dict:
        """Update a single clarification answer."""
        context = self._load_context(session_id)
        if value is not None:
            context[field] = value
        self._save_context(session_id, context)
        return context

    def update_multiple(self, session_id: str, updates: Dict[str, Optional[str]]) -> dict:
        """Update multiple fields at once."""
        context = self._load_context(session_id)
        for field, value in updates.items():
            if value is not None:
                context[field] = value
        self._save_context(session_id, context)
        return context

    def mark_question_asked(self, session_id: str, question: str) -> dict:
        """Mark a question as asked to avoid repetition."""
        context = self._load_context(session_id)
        if question not in context["asked_questions"]:
            context["asked_questions"].append(question)
        context["current_question"] = question
        self._save_context(session_id, context)
        return context

    def is_question_complete(self, session_id: str, field: str) -> bool:
        """Check if a field already has a value (answer provided)."""
        context = self._load_context(session_id)
        value = context.get(field)
        return value is not None and value != ""

    def has_all_required_fields(self, session_id: str, required_fields: List[str]) -> bool:
        """Check if all required fields have been answered."""
        context = self._load_context(session_id)
        for field in required_fields:
            if context.get(field) is None or context.get(field) == "":
                return False
        return True

    def get_missing_fields(self, session_id: str, required_fields: List[str]) -> List[str]:
        """Get list of fields that still need answers."""
        context = self._load_context(session_id)
        missing = []
        for field in required_fields:
            if context.get(field) is None or context.get(field) == "":
                missing.append(field)
        return missing

    def reset(self, session_id: str) -> None:
        """Reset task context for a session."""
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("sessions", {}).pop(session_id, None)
            self._save_json(root)
            return
        
        with self._connect() as conn:
            conn.execute("DELETE FROM task_context WHERE session_id = ?", (session_id,))
            conn.commit()

    def export_for_llm(self, session_id: str) -> str:
        """Export context as readable text for LLM processing."""
        context = self._load_context(session_id)
        lines = []
        
        fields_to_export = [
            ("site_type", "Site Type"),
            ("target_platform", "Target Platform"),
            ("language", "Programming Language"),
            ("framework", "Framework/Library"),
            ("database", "Database"),
            ("tool_type", "Tool Type"),
            ("app_scope", "Application Scope"),
        ]
        
        for field, label in fields_to_export:
            value = context.get(field)
            if value:
                lines.append(f"{label}: {value}")
        
        return "\n".join(lines) if lines else "No context collected yet."
