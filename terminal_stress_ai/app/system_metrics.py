from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Optional


class SystemMetricsTracker:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "contextflow_metrics.sqlite3")
        self.json_path = root / "data" / "contextflow_metrics.json"
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
                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    prediction_accuracy REAL NOT NULL,
                    suggestion_accept_rate REAL NOT NULL,
                    trust_score REAL NOT NULL
                )
                """
            )
            conn.commit()

    def _init_json(self) -> None:
        if not self.json_path.exists():
            self.json_path.write_text(json.dumps({"session_metrics": {}}), encoding="utf-8")

    def _load_json(self) -> dict:
        self._init_json()
        return json.loads(self.json_path.read_text(encoding="utf-8"))

    def _save_json(self, payload: dict) -> None:
        self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def record_and_summarize(
        self,
        session_id: str,
        validation: dict | None,
        suggestion_quality: dict,
        trust_score: float,
    ) -> Dict[str, object]:
        prediction_accuracy = float(validation["model_accuracy"]) if validation else 0.0
        suggestion_accept_rate = 0.0
        shown = int(suggestion_quality.get("suggestions_shown", 0))
        if shown > 0:
            suggestion_accept_rate = float(suggestion_quality.get("suggestions_accepted", 0)) / shown

        self._store(session_id, prediction_accuracy, suggestion_accept_rate, trust_score)
        return self._summary()

    def _store(self, session_id: str, prediction_accuracy: float, suggestion_accept_rate: float, trust_score: float) -> None:
        if self.storage_mode == "json":
            payload = self._load_json()
            payload["session_metrics"][session_id] = {
                "prediction_accuracy": prediction_accuracy,
                "suggestion_accept_rate": suggestion_accept_rate,
                "trust_score": trust_score,
            }
            self._save_json(payload)
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO session_metrics(session_id, prediction_accuracy, suggestion_accept_rate, trust_score)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    prediction_accuracy=excluded.prediction_accuracy,
                    suggestion_accept_rate=excluded.suggestion_accept_rate,
                    trust_score=excluded.trust_score
                """,
                (session_id, prediction_accuracy, suggestion_accept_rate, trust_score),
            )
            conn.commit()

    def _summary(self) -> Dict[str, object]:
        rows: list[tuple[float, float, float]] = []
        if self.storage_mode == "json":
            payload = self._load_json()
            rows = [
                (
                    float(item.get("prediction_accuracy", 0.0)),
                    float(item.get("suggestion_accept_rate", 0.0)),
                    float(item.get("trust_score", 0.0)),
                )
                for item in payload.get("session_metrics", {}).values()
            ]
        else:
            with self._connect() as conn:
                rows = [(float(a), float(b), float(c)) for a, b, c in conn.execute(
                    "SELECT prediction_accuracy, suggestion_accept_rate, trust_score FROM session_metrics ORDER BY rowid ASC"
                ).fetchall()]
        if not rows:
            return {
                "prediction_accuracy": 0.0,
                "suggestion_accept_rate": 0.0,
                "user_trust_trend": "stable",
                "latest_trust_score": 0.0,
            }
        prediction_accuracy = sum(row[0] for row in rows) / len(rows)
        accept_rate = sum(row[1] for row in rows) / len(rows)
        trust_trend = "stable"
        if len(rows) >= 2:
            if rows[-1][2] - rows[0][2] > 0.08:
                trust_trend = "increasing"
            elif rows[-1][2] - rows[0][2] < -0.08:
                trust_trend = "decreasing"
        return {
            "prediction_accuracy": round(prediction_accuracy, 3),
            "suggestion_accept_rate": round(accept_rate, 3),
            "user_trust_trend": trust_trend,
            "latest_trust_score": round(rows[-1][2], 3),
        }
