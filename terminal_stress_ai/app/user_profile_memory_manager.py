from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional


class UserProfileMemoryManager:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "user_profile_memory.sqlite3")
        self.json_path = root / "data" / "user_profile_memory.json"
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
                CREATE TABLE IF NOT EXISTS user_profile_memory (
                    user_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _init_json(self) -> None:
        if not self.json_path.exists():
            self.json_path.write_text(json.dumps({"users": {}}), encoding="utf-8")

    def _load_json(self) -> dict:
        self._init_json()
        try:
            return json.loads(self.json_path.read_text(encoding="utf-8"))
        except Exception:
            return {"users": {}}

    def _save_json(self, payload: dict) -> None:
        self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _default_payload(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "trust_history": [],
            "interaction_patterns": [],
            "success_metrics": [],
            "user_preferences": {},
            "behavioral_baseline": {},
            "policy_learning_history": [],
        }

    def get(self, user_id: str) -> dict:
        if self.storage_mode == "json":
            root = self._load_json()
            return root.get("users", {}).get(user_id, self._default_payload(user_id))
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM user_profile_memory WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return self._default_payload(user_id)
        try:
            return json.loads(str(row[0]))
        except Exception:
            return self._default_payload(user_id)

    def save(self, user_id: str, payload: dict) -> dict:
        if self.storage_mode == "json":
            root = self._load_json()
            root.setdefault("users", {})[user_id] = payload
            self._save_json(root)
            return payload
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_profile_memory(user_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    payload_json=excluded.payload_json
                """,
                (user_id, json.dumps(payload)),
            )
            conn.commit()
        return payload

    def update(
        self,
        user_id: str,
        trust_score: float,
        success_metric: float,
        preferences: Dict[str, object],
        baseline: Dict[str, object],
        interaction_pattern: Dict[str, object],
        policy_signal: Optional[Dict[str, object]] = None,
    ) -> dict:
        payload = self.get(user_id)
        trust_history = list(payload.get("trust_history", []))
        trust_history.append(round(float(trust_score), 3))
        payload["trust_history"] = trust_history[-20:]
        success_metrics = list(payload.get("success_metrics", []))
        success_metrics.append(round(float(success_metric), 3))
        payload["success_metrics"] = success_metrics[-20:]
        patterns = list(payload.get("interaction_patterns", []))
        patterns.append(interaction_pattern)
        payload["interaction_patterns"] = patterns[-20:]
        if policy_signal:
            learning_history = list(payload.get("policy_learning_history", []))
            learning_history.append(policy_signal)
            payload["policy_learning_history"] = learning_history[-20:]
        payload["user_preferences"] = dict(preferences)
        payload["behavioral_baseline"] = dict(baseline)
        return self.save(user_id, payload)

    def trust_trend(self, user_id: str) -> str:
        payload = self.get(user_id)
        trust_history = [float(v) for v in payload.get("trust_history", [])]
        if len(trust_history) < 2:
            return "stable"
        if trust_history[-1] - trust_history[0] > 0.08:
            return "increasing"
        if trust_history[-1] - trust_history[0] < -0.08:
            return "decreasing"
        return "stable"
