from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class NasaTlxSurvey:
    mental_demand: float
    physical_demand: float
    temporal_demand: float
    performance: float
    effort: float
    frustration: float

    def overall_score(self) -> float:
        values = [
            self.mental_demand,
            self.physical_demand,
            self.temporal_demand,
            self.performance,
            self.effort,
            self.frustration,
        ]
        return round(sum(values) / len(values), 3)


@dataclass
class TrustSurvey:
    trust_ai_suggestions: int
    ai_reliable: int
    comfortable_relying_on_ai: int

    def overall_score(self) -> float:
        values = [
            self.trust_ai_suggestions,
            self.ai_reliable,
            self.comfortable_relying_on_ai,
        ]
        return round(sum(values) / len(values), 3)


class SurveyValidationEngine:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "contextflow_validation.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_surveys (
                    session_id TEXT PRIMARY KEY,
                    nasa_tlx_json TEXT NOT NULL,
                    trust_json TEXT NOT NULL,
                    nasa_tlx_score REAL NOT NULL,
                    trust_rating REAL NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def normalize_nasa_tlx(score: float) -> float:
        return max(0.0, min(1.0, score / 100.0))

    @staticmethod
    def normalize_trust_rating(score: float) -> float:
        return max(0.0, min(1.0, (score - 1.0) / 4.0))

    def save_survey(self, session_id: str, nasa_tlx: NasaTlxSurvey, trust: TrustSurvey) -> Dict[str, float]:
        nasa_score = nasa_tlx.overall_score()
        trust_score = trust.overall_score()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO session_surveys(session_id, nasa_tlx_json, trust_json, nasa_tlx_score, trust_rating)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    nasa_tlx_json=excluded.nasa_tlx_json,
                    trust_json=excluded.trust_json,
                    nasa_tlx_score=excluded.nasa_tlx_score,
                    trust_rating=excluded.trust_rating
                """,
                (
                    session_id,
                    json.dumps(nasa_tlx.__dict__),
                    json.dumps(trust.__dict__),
                    nasa_score,
                    trust_score,
                ),
            )
            conn.commit()
        return {"nasa_tlx": nasa_score, "trust_rating": trust_score}

    def get_survey(self, session_id: str) -> Optional[Dict[str, float]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT nasa_tlx_score, trust_rating FROM session_surveys WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return {"nasa_tlx": float(row[0]), "trust_rating": float(row[1])}

    def validate(
        self,
        session_id: str,
        predicted_stress: float,
        predicted_load: float,
        predicted_trust: float,
    ) -> Optional[Dict[str, object]]:
        survey = self.get_survey(session_id)
        if survey is None:
            return None

        nasa_norm = self.normalize_nasa_tlx(survey["nasa_tlx"])
        trust_norm = self.normalize_trust_rating(survey["trust_rating"])

        stress_error = round(abs(predicted_stress - nasa_norm), 3)
        load_error = round(abs(predicted_load - nasa_norm), 3)
        trust_error = round(abs(predicted_trust - trust_norm), 3)
        avg_error = (stress_error + load_error + trust_error) / 3.0
        model_accuracy = round(max(0.0, 1.0 - avg_error), 3)

        return {
            "survey_scores": survey,
            "model_comparison": {
                "stress_error": stress_error,
                "cognitive_load_error": load_error,
                "trust_error": trust_error,
            },
            "model_accuracy": model_accuracy,
        }
