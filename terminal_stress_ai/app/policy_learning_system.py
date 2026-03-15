from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict


class PolicyLearningSystem:
    def __init__(self, db_path: Path | None = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "contextflow_policy_learning.sqlite3")
        self.json_path = root / "data" / "contextflow_policy_learning.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_mode = "sqlite"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS policy_learning (
                        user_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except sqlite3.Error:
            self.storage_mode = "json"
            if not self.json_path.exists():
                self.json_path.write_text(json.dumps({"events": []}, indent=2), encoding="utf-8")

    def _save(self, payload: Dict[str, object]) -> None:
        if self.storage_mode == "json":
            try:
                root = json.loads(self.json_path.read_text(encoding="utf-8"))
            except Exception:
                root = {"events": []}
            root.setdefault("events", []).append(payload)
            self.json_path.write_text(json.dumps(root, indent=2), encoding="utf-8")
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO policy_learning(user_id, session_id, payload_json) VALUES (?, ?, ?)",
                (str(payload.get("user_id", "")), str(payload.get("session_id", "")), json.dumps(payload)),
            )
            conn.commit()

    def update(
        self,
        user_id: str,
        session_id: str,
        suggestion_quality: Dict[str, object],
        trust_signals: Dict[str, float],
        trust_score: float,
        validation: dict | None,
        autonomy_mode: str,
        action_result: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        shown = max(int(suggestion_quality.get("suggestions_shown", 0)), 1)
        accepted = int(suggestion_quality.get("suggestions_accepted", 0))
        acceptance_rate = accepted / shown
        override_rate = float(trust_signals.get("override_rate", 0.0))
        completion_success = float(validation.get("model_accuracy", 0.0)) if validation else 0.0
        trust_delta = float(trust_signals.get("trust_delta", 0.0))
        auto_executed = 1.0 if str((action_result or {}).get("status", "")) == "executed_automatically" else 0.0

        policy_adjustment = "stable_policy"
        if override_rate > 0.45 or trust_score < 0.4:
            policy_adjustment = "reduce_autonomy"
        elif acceptance_rate > 0.7 and trust_score > 0.7:
            policy_adjustment = "increase_autonomy"

        result = {
            "user_id": user_id,
            "session_id": session_id,
            "suggestion_acceptance_rate": round(acceptance_rate, 3),
            "override_rate": round(override_rate, 3),
            "trust_score": round(trust_score, 3),
            "trust_change": round(trust_delta, 3),
            "completion_success": round(completion_success, 3),
            "task_completion_success": round(completion_success, 3),
            "autonomy_mode": autonomy_mode,
            "automatic_execution_rate": round(auto_executed, 3),
            "policy_adjustment": policy_adjustment,
        }
        self._save(result)
        return result
