from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional


class DecisionSmoother:
    ORDER = {
        "auto_execute": 0,
        "suggest_only": 1,
        "require_confirmation": 2,
        "approval_required": 3,
    }

    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "contextflow_decisions.sqlite3")
        self.json_path = root / "data" / "contextflow_decisions.json"
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
                CREATE TABLE IF NOT EXISTS decision_state (
                    user_id TEXT PRIMARY KEY,
                    last_mode TEXT NOT NULL,
                    pending_mode TEXT NOT NULL,
                    safe_streak INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def _init_json(self) -> None:
        if not self.json_path.exists():
            self.json_path.write_text(json.dumps({"decision_state": {}}), encoding="utf-8")

    def _load_json(self) -> dict:
        self._init_json()
        return json.loads(self.json_path.read_text(encoding="utf-8"))

    def _save_json(self, payload: dict) -> None:
        self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _get_state(self, user_id: str) -> Dict[str, object]:
        if self.storage_mode == "json":
            payload = self._load_json()
            return payload.get("decision_state", {}).get(
                user_id,
                {"last_mode": "suggest_only", "pending_mode": "", "safe_streak": 0},
            )
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_mode, pending_mode, safe_streak FROM decision_state WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return {"last_mode": "suggest_only", "pending_mode": "", "safe_streak": 0}
        return {"last_mode": str(row[0]), "pending_mode": str(row[1]), "safe_streak": int(row[2])}

    def _save_state(self, user_id: str, state: Dict[str, object]) -> None:
        if self.storage_mode == "json":
            payload = self._load_json()
            payload.setdefault("decision_state", {})[user_id] = state
            self._save_json(payload)
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decision_state(user_id, last_mode, pending_mode, safe_streak)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_mode=excluded.last_mode,
                    pending_mode=excluded.pending_mode,
                    safe_streak=excluded.safe_streak
                """,
                (user_id, str(state["last_mode"]), str(state["pending_mode"]), int(state["safe_streak"])),
            )
            conn.commit()

    def smooth(self, user_id: str, proposed_mode: str, safe_state: bool) -> Dict[str, object]:
        state = self._get_state(user_id)
        last_mode = str(state["last_mode"])
        pending_mode = str(state["pending_mode"])
        safe_streak = int(state["safe_streak"])

        if proposed_mode == last_mode:
            next_state = {"last_mode": last_mode, "pending_mode": "", "safe_streak": safe_streak + (1 if safe_state else 0)}
            self._save_state(user_id, next_state)
            return {"mode": proposed_mode, "state": next_state, "smoothed": False}

        relaxing = self.ORDER.get(proposed_mode, 1) < self.ORDER.get(last_mode, 1)
        if relaxing and safe_state:
            if pending_mode == proposed_mode:
                safe_streak += 1
            else:
                pending_mode = proposed_mode
                safe_streak = 1
            if safe_streak < 2:
                next_state = {"last_mode": last_mode, "pending_mode": pending_mode, "safe_streak": safe_streak}
                self._save_state(user_id, next_state)
                return {"mode": last_mode, "state": next_state, "smoothed": True}

        next_state = {"last_mode": proposed_mode, "pending_mode": "", "safe_streak": 1 if safe_state else 0}
        self._save_state(user_id, next_state)
        return {"mode": proposed_mode, "state": next_state, "smoothed": proposed_mode != last_mode}
