from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional


class TaskMemoryManager:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "task_memory.sqlite3")
        self.json_path = root / "data" / "task_memory.json"
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
                CREATE TABLE IF NOT EXISTS task_memory (
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
            "active_task": "",
            "generated_code": "",
            "language": "",
            "recent_suggestions": [],
            "reasoning_state": "",
            "reasoning_trace": {},
            "task_history": [],
        }

    def get(self, session_id: str) -> dict:
        if self.storage_mode == "json":
            payload = self._load_json()
            return payload.get("sessions", {}).get(session_id, self._default_payload(session_id))
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM task_memory WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return self._default_payload(session_id)
        try:
            return json.loads(str(row[0]))
        except Exception:
            return self._default_payload(session_id)

    def save(self, session_id: str, payload: dict) -> dict:
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("sessions", {})[session_id] = payload
            self._save_json(root)
            return payload
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO task_memory(session_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload_json=excluded.payload_json
                """,
                (session_id, json.dumps(payload)),
            )
            conn.commit()
        return payload

    def update(
        self,
        session_id: str,
        active_task: str,
        language: str,
        generated_code: str,
        suggestion: dict,
        reasoning_state: str,
        reasoning_trace: Optional[Dict[str, object]] = None,
    ) -> dict:
        payload = self.get(session_id)
        previous_task = str(payload.get("active_task", ""))
        payload["active_task"] = active_task
        payload["language"] = language or payload.get("language", "")
        if generated_code:
            payload["generated_code"] = generated_code
        payload["reasoning_state"] = reasoning_state
        if reasoning_trace:
            payload["reasoning_trace"] = dict(reasoning_trace)
        recent = list(payload.get("recent_suggestions", []))
        if suggestion:
            recent.append(suggestion)
        payload["recent_suggestions"] = recent[-5:]
        history = list(payload.get("task_history", []))
        if active_task and active_task != previous_task:
            history.append({"previous_task": previous_task, "active_task": active_task})
        payload["task_history"] = history[-10:]
        return self.save(session_id, payload)

    def reset(self, session_id: str) -> None:
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("sessions", {}).pop(session_id, None)
            self._save_json(root)
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM task_memory WHERE session_id = ?", (session_id,))
            conn.commit()
