from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class ConversationMemoryManager:
    def __init__(self, db_path: Optional[Path] = None, short_term_limit: int = 12) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "conversation_memory.sqlite3")
        self.json_path = root / "data" / "conversation_memory.json"
        self.short_term_limit = max(2, int(short_term_limit))
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
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    session_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
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

    def _default_payload(self, session_id: str) -> dict:
        return {
            "session_id": session_id,
            "conversation_history": [],
            "code_memory": {
                "language": "",
                "last_generated_code": "",
            },
            "task_context": {
                "active_task": "",
                "task_continuity": "new_task",
                "reasoning_state": "",
            },
        }

    def _load_session(self, session_id: str) -> dict:
        if self.storage_mode == "json":
            payload = self._load_json()
            return payload.get("sessions", {}).get(session_id, self._default_payload(session_id))
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM conversation_memory WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return self._default_payload(session_id)
        try:
            return json.loads(str(row[0]))
        except Exception:
            return self._default_payload(session_id)

    def _save_session(self, session_id: str, payload: dict) -> None:
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("sessions", {})[session_id] = payload
            self._save_json(root)
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversation_memory(session_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload_json=excluded.payload_json
                """,
                (session_id, json.dumps(payload)),
            )
            conn.commit()

    def _append_message(
        self,
        session_id: str,
        role: str,
        content: str = "",
        code: str = "",
        language: str = "",
        metadata: Optional[Dict[str, object]] = None,
    ) -> dict:
        payload = self._load_session(session_id)
        history = payload.setdefault("conversation_history", [])
        message: dict = {
            "role": role,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if content:
            message["content"] = content
        if code:
            message["code"] = code
        if language:
            message["language"] = language
        if metadata:
            message["metadata"] = dict(metadata)

        if role == "user":
            if not history or history[-1].get("role") != "user" or history[-1].get("content") != content:
                history.append(message)
        else:
            history.append(message)

        if code:
            payload.setdefault("code_memory", {})["last_generated_code"] = code
        if language:
            payload.setdefault("code_memory", {})["language"] = language
        payload["conversation_history"] = history[-100:]
        self._save_session(session_id, payload)
        return payload

    def add_user_message(self, session_id: str, content: str, metadata: Optional[Dict[str, object]] = None) -> dict:
        return self._append_message(session_id=session_id, role="user", content=content, metadata=metadata)

    def add_ai_response(self, session_id: str, content: str = "", code: str = "", language: str = "") -> dict:
        return self._append_message(
            session_id=session_id,
            role="assistant",
            content=content,
            code=code,
            language=language,
        )

    def update_task_context(self, session_id: str, task_context: Dict[str, object]) -> dict:
        payload = self._load_session(session_id)
        current = dict(payload.get("task_context", {}))
        current.update(task_context)
        payload["task_context"] = current
        self._save_session(session_id, payload)
        return payload

    def get_recent_context(self, session_id: str, limit: int = 6) -> dict:
        payload = self._load_session(session_id)
        short_term_limit = max(1, min(int(limit), self.short_term_limit))
        history = payload.get("conversation_history", [])
        return {
            "session_id": session_id,
            "conversation_history": history[-short_term_limit:],
            "code_memory": payload.get("code_memory", {}),
            "task_context": payload.get("task_context", {}),
            "short_term_memory": history[-short_term_limit:],
        }

    def get_last_generated_code(self, session_id: str) -> str:
        payload = self._load_session(session_id)
        return str(payload.get("code_memory", {}).get("last_generated_code", ""))

    def get_full_memory_snapshot(self, session_id: str, short_term_limit: Optional[int] = None) -> dict:
        payload = self._load_session(session_id)
        limit = short_term_limit or self.short_term_limit
        history = payload.get("conversation_history", [])
        return {
            "session_id": session_id,
            "short_term_memory": history[-limit:],
            "working_memory": {
                "code_memory": payload.get("code_memory", {}),
                "task_context": payload.get("task_context", {}),
            },
            "conversation_turns": len(history),
        }

    def reset(self, session_id: str) -> None:
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("sessions", {}).pop(session_id, None)
            self._save_json(root)
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM conversation_memory WHERE session_id = ?", (session_id,))
            conn.commit()
