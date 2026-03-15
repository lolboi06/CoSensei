from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


BASELINE_MIN_SESSIONS = 3
EMA_ALPHA = 0.3


@dataclass
class SessionPreferenceSummary:
    user_id: str
    session_id: str
    typing_cpm: float
    pause_mean: float
    backspace_ratio: float
    hesitation_rate: float
    accept_rate: float
    override_rate: float
    trust_score: float
    stress_score: float
    engagement_score: float
    load_score: float
    content_intensity: float


class UserPreferenceEngine:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (root / "data" / "contextflow_profiles.sqlite3")
        self.json_path = root / "data" / "contextflow_profiles.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_mode = "sqlite"
        try:
            self._init_db()
        except sqlite3.Error:
            self.storage_mode = "json"
            self._init_json_store()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    typing_cpm REAL NOT NULL,
                    pause_mean REAL NOT NULL,
                    backspace_ratio REAL NOT NULL,
                    hesitation_rate REAL NOT NULL,
                    accept_rate REAL NOT NULL,
                    override_rate REAL NOT NULL,
                    trust_score REAL NOT NULL,
                    stress_score REAL NOT NULL,
                    engagement_score REAL NOT NULL,
                    load_score REAL NOT NULL,
                    content_intensity REAL NOT NULL,
                    summary_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    session_count INTEGER NOT NULL,
                    baseline_typing_cpm REAL NOT NULL,
                    baseline_pause_mean REAL NOT NULL,
                    baseline_backspace_ratio REAL NOT NULL,
                    baseline_hesitation_rate REAL NOT NULL,
                    ai_accept_rate REAL NOT NULL,
                    override_rate REAL NOT NULL,
                    trust_baseline_score REAL NOT NULL,
                    trust_baseline TEXT NOT NULL,
                    typical_stress_level REAL NOT NULL,
                    interaction_style TEXT NOT NULL,
                    preferred_ai_behavior TEXT NOT NULL,
                    profile_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _init_json_store(self) -> None:
        if not self.json_path.exists():
            self.json_path.write_text(json.dumps({"profiles": {}, "sessions": {}}), encoding="utf-8")

    def _load_json_store(self) -> dict:
        self._init_json_store()
        try:
            return json.loads(self.json_path.read_text(encoding="utf-8"))
        except Exception:
            return {"profiles": {}, "sessions": {}}

    def _save_json_store(self, payload: dict) -> None:
        self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _round3(value: float) -> float:
        return round(float(value), 3)

    @staticmethod
    def _level(score: float) -> str:
        if score < 0.33:
            return "low"
        if score < 0.66:
            return "medium"
        return "high"

    def _upsert_session_summary(self, summary: SessionPreferenceSummary) -> None:
        payload = {
            "typing_cpm": summary.typing_cpm,
            "pause_mean": summary.pause_mean,
            "backspace_ratio": summary.backspace_ratio,
            "hesitation_rate": summary.hesitation_rate,
            "accept_rate": summary.accept_rate,
            "override_rate": summary.override_rate,
            "trust_score": summary.trust_score,
            "stress_score": summary.stress_score,
            "engagement_score": summary.engagement_score,
            "load_score": summary.load_score,
            "content_intensity": summary.content_intensity,
        }
        if self.storage_mode == "json":
            store = self._load_json_store()
            store["sessions"][summary.session_id] = {"user_id": summary.user_id, **payload}
            self._save_json_store(store)
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO session_summaries (
                    session_id, user_id, typing_cpm, pause_mean, backspace_ratio,
                    hesitation_rate, accept_rate, override_rate, trust_score,
                    stress_score, engagement_score, load_score, content_intensity, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_id=excluded.user_id,
                    typing_cpm=excluded.typing_cpm,
                    pause_mean=excluded.pause_mean,
                    backspace_ratio=excluded.backspace_ratio,
                    hesitation_rate=excluded.hesitation_rate,
                    accept_rate=excluded.accept_rate,
                    override_rate=excluded.override_rate,
                    trust_score=excluded.trust_score,
                    stress_score=excluded.stress_score,
                    engagement_score=excluded.engagement_score,
                    load_score=excluded.load_score,
                    content_intensity=excluded.content_intensity,
                    summary_json=excluded.summary_json
                """,
                (
                    summary.session_id,
                    summary.user_id,
                    summary.typing_cpm,
                    summary.pause_mean,
                    summary.backspace_ratio,
                    summary.hesitation_rate,
                    summary.accept_rate,
                    summary.override_rate,
                    summary.trust_score,
                    summary.stress_score,
                    summary.engagement_score,
                    summary.load_score,
                    summary.content_intensity,
                    json.dumps(payload),
                ),
            )
            conn.commit()

    def _load_user_sessions(self, user_id: str) -> list[dict]:
        if self.storage_mode == "json":
            store = self._load_json_store()
            sessions: list[dict] = []
            for session_id, item in store.get("sessions", {}).items():
                if item.get("user_id") != user_id:
                    continue
                sessions.append({"session_id": session_id, **item})
            sessions.sort(key=lambda item: item["session_id"])
            return sessions
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, typing_cpm, pause_mean, backspace_ratio, hesitation_rate,
                       accept_rate, override_rate, trust_score, stress_score,
                       engagement_score, load_score, content_intensity
                FROM session_summaries
                WHERE user_id = ?
                ORDER BY rowid ASC
                """,
                (user_id,),
            ).fetchall()
        sessions: list[dict] = []
        for row in rows:
            sessions.append(
                {
                    "session_id": row[0],
                    "typing_cpm": float(row[1]),
                    "pause_mean": float(row[2]),
                    "backspace_ratio": float(row[3]),
                    "hesitation_rate": float(row[4]),
                    "accept_rate": float(row[5]),
                    "override_rate": float(row[6]),
                    "trust_score": float(row[7]),
                    "stress_score": float(row[8]),
                    "engagement_score": float(row[9]),
                    "load_score": float(row[10]),
                    "content_intensity": float(row[11]),
                }
            )
        return sessions

    def _mean(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return self._round3(sum(values) / len(values))

    def _infer_preferences(self, profile: dict) -> dict:
        typing_cpm = float(profile["baseline_typing_cpm"])
        accept_rate = float(profile["ai_accept_rate"])
        override_rate = float(profile["override_rate"])
        trust_score = float(profile["trust_baseline_score"])
        backspace_ratio = float(profile["baseline_backspace_ratio"])
        pause_mean = float(profile["baseline_pause_mean"])

        if typing_cpm >= 300:
            interaction_style = "fast_typist"
        elif typing_cpm <= 170 or pause_mean >= 380:
            interaction_style = "reflective_typist"
        else:
            interaction_style = "balanced_typist"

        if accept_rate >= 0.75:
            ai_usage_pattern = "high_acceptance"
        elif override_rate >= 0.4:
            ai_usage_pattern = "high_override"
        else:
            ai_usage_pattern = "mixed_acceptance"

        if backspace_ratio >= 0.12:
            editing_behavior = "heavy_editor"
        elif backspace_ratio <= 0.05:
            editing_behavior = "low_editing"
        else:
            editing_behavior = "moderate_editing"

        if trust_score >= 0.7:
            trust_profile = "high_trust_user"
        elif trust_score <= 0.45:
            trust_profile = "low_trust_user"
        else:
            trust_profile = "calibrated_trust_user"

        if override_rate >= 0.4 or trust_score <= 0.45:
            automation_preference = "require_confirmation"
        elif accept_rate >= 0.8 and trust_score >= 0.7:
            automation_preference = "auto_accept_suggestions"
        else:
            automation_preference = "suggestion_review_mode"

        if trust_profile == "low_trust_user":
            preferred_ai_behavior = "explanation_first"
        elif interaction_style == "fast_typist":
            preferred_ai_behavior = "concise_suggestions"
        elif editing_behavior == "heavy_editor":
            preferred_ai_behavior = "draft_then_refine"
        else:
            preferred_ai_behavior = "balanced_guidance"

        return {
            "interaction_style": interaction_style,
            "ai_usage_pattern": ai_usage_pattern,
            "editing_behavior": editing_behavior,
            "trust_profile": trust_profile,
            "automation_preference": automation_preference,
            "preferred_ai_behavior": preferred_ai_behavior,
        }

    def _build_profile(self, user_id: str, sessions: list[dict]) -> dict:
        profile = {
            "user_id": user_id,
            "session_count": len(sessions),
            "baseline_typing_cpm": self._mean([s["typing_cpm"] for s in sessions]),
            "baseline_pause_mean": self._mean([s["pause_mean"] for s in sessions]),
            "baseline_backspace_ratio": self._mean([s["backspace_ratio"] for s in sessions]),
            "baseline_hesitation_rate": self._mean([s["hesitation_rate"] for s in sessions]),
            "ai_accept_rate": self._mean([s["accept_rate"] for s in sessions]),
            "override_rate": self._mean([s["override_rate"] for s in sessions]),
            "trust_baseline_score": self._mean([s["trust_score"] for s in sessions]),
            "trust_baseline": self._level(self._mean([s["trust_score"] for s in sessions])),
            "typical_stress_level": self._mean([s["stress_score"] for s in sessions]),
        }
        prefs = self._infer_preferences(profile)
        profile.update(
            {
                "interaction_style": prefs["interaction_style"],
                "preferred_ai_behavior": prefs["preferred_ai_behavior"],
            }
        )
        return profile

    def _ema(self, previous: float, current: float, alpha: float = EMA_ALPHA) -> float:
        return self._round3((1.0 - alpha) * previous + alpha * current)

    def _apply_moving_average(self, previous_profile: dict | None, summary: SessionPreferenceSummary, profile: dict) -> dict:
        if not previous_profile:
            return profile
        profile["baseline_typing_cpm"] = self._ema(float(previous_profile["baseline_typing_cpm"]), summary.typing_cpm)
        profile["baseline_pause_mean"] = self._ema(float(previous_profile["baseline_pause_mean"]), summary.pause_mean)
        profile["baseline_backspace_ratio"] = self._ema(float(previous_profile["baseline_backspace_ratio"]), summary.backspace_ratio)
        profile["baseline_hesitation_rate"] = self._ema(float(previous_profile["baseline_hesitation_rate"]), summary.hesitation_rate)
        profile["ai_accept_rate"] = self._ema(float(previous_profile["ai_accept_rate"]), summary.accept_rate)
        profile["override_rate"] = self._ema(float(previous_profile["override_rate"]), summary.override_rate)
        profile["trust_baseline_score"] = self._ema(float(previous_profile["trust_baseline_score"]), summary.trust_score)
        profile["trust_baseline"] = self._level(profile["trust_baseline_score"])
        profile["typical_stress_level"] = self._ema(float(previous_profile["typical_stress_level"]), summary.stress_score)
        prefs = self._infer_preferences(profile)
        profile["interaction_style"] = prefs["interaction_style"]
        profile["preferred_ai_behavior"] = prefs["preferred_ai_behavior"]
        return profile

    def _save_profile(self, profile: dict) -> None:
        if self.storage_mode == "json":
            store = self._load_json_store()
            store["profiles"][profile["user_id"]] = profile
            self._save_json_store(store)
            return
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_profiles (
                    user_id, session_count, baseline_typing_cpm, baseline_pause_mean,
                    baseline_backspace_ratio, baseline_hesitation_rate, ai_accept_rate,
                    override_rate, trust_baseline_score, trust_baseline, typical_stress_level,
                    interaction_style, preferred_ai_behavior, profile_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    session_count=excluded.session_count,
                    baseline_typing_cpm=excluded.baseline_typing_cpm,
                    baseline_pause_mean=excluded.baseline_pause_mean,
                    baseline_backspace_ratio=excluded.baseline_backspace_ratio,
                    baseline_hesitation_rate=excluded.baseline_hesitation_rate,
                    ai_accept_rate=excluded.ai_accept_rate,
                    override_rate=excluded.override_rate,
                    trust_baseline_score=excluded.trust_baseline_score,
                    trust_baseline=excluded.trust_baseline,
                    typical_stress_level=excluded.typical_stress_level,
                    interaction_style=excluded.interaction_style,
                    preferred_ai_behavior=excluded.preferred_ai_behavior,
                    profile_json=excluded.profile_json
                """,
                (
                    profile["user_id"],
                    profile["session_count"],
                    profile["baseline_typing_cpm"],
                    profile["baseline_pause_mean"],
                    profile["baseline_backspace_ratio"],
                    profile["baseline_hesitation_rate"],
                    profile["ai_accept_rate"],
                    profile["override_rate"],
                    profile["trust_baseline_score"],
                    profile["trust_baseline"],
                    profile["typical_stress_level"],
                    profile["interaction_style"],
                    profile["preferred_ai_behavior"],
                    json.dumps(profile),
                ),
            )
            conn.commit()

    def get_profile(self, user_id: str) -> Optional[dict]:
        if self.storage_mode == "json":
            store = self._load_json_store()
            profile = store.get("profiles", {}).get(user_id)
            return dict(profile) if isinstance(profile, dict) else None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT profile_json FROM user_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(str(row[0]))

    def _safe_relative_delta(self, current: float, baseline: float) -> float:
        if abs(baseline) < 1e-6:
            return 0.0
        return self._round3((current - baseline) / abs(baseline))

    def _deviation_label(self, delta: float, positive_is_risk: bool = True) -> str:
        signed = delta if positive_is_risk else -delta
        if signed >= 0.25:
            return "significantly_above_baseline"
        if signed >= 0.1:
            return "above_baseline"
        if signed <= -0.25:
            return "significantly_below_baseline"
        if signed <= -0.1:
            return "below_baseline"
        return "within_baseline_range"

    def _baseline_analysis(self, summary: SessionPreferenceSummary, profile: dict) -> dict:
        typing_delta = self._safe_relative_delta(summary.typing_cpm, float(profile["baseline_typing_cpm"]))
        pause_delta = self._safe_relative_delta(summary.pause_mean, float(profile["baseline_pause_mean"]))
        backspace_delta = self._safe_relative_delta(summary.backspace_ratio, float(profile["baseline_backspace_ratio"]))
        hesitation_delta = self._safe_relative_delta(summary.hesitation_rate, float(profile["baseline_hesitation_rate"]))
        trust_delta = self._safe_relative_delta(summary.trust_score, float(profile["trust_baseline_score"]))
        stress_delta = self._safe_relative_delta(summary.stress_score, float(profile["typical_stress_level"]))

        deviations: list[str] = []
        if stress_delta >= 0.2:
            deviations.append("abnormal_stress")
        if pause_delta >= 0.2 or hesitation_delta >= 0.2:
            deviations.append("increased_cognitive_load")
        if trust_delta <= -0.2 or summary.override_rate > float(profile["override_rate"]) + 0.15:
            deviations.append("increased_distrust")
        if abs(typing_delta) >= 0.2 or backspace_delta >= 0.25:
            deviations.append("unusual_typing_behavior")

        return {
            "typing_cpm_delta": typing_delta,
            "pause_mean_delta": pause_delta,
            "backspace_ratio_delta": backspace_delta,
            "hesitation_rate_delta": hesitation_delta,
            "trust_score_delta": trust_delta,
            "stress_score_delta": stress_delta,
            "typing_behavior_status": self._deviation_label(abs(typing_delta), positive_is_risk=True),
            "cognitive_load_status": self._deviation_label(max(pause_delta, hesitation_delta), positive_is_risk=True),
            "trust_status": self._deviation_label(-trust_delta, positive_is_risk=True),
            "stress_status": self._deviation_label(stress_delta, positive_is_risk=True),
            "deviations": deviations,
        }

    def _adaptive_behavior(self, preferences: dict, baseline_analysis: dict) -> list[str]:
        actions: list[str] = []
        if preferences["automation_preference"] == "require_confirmation":
            actions.append("Reduce suggestion frequency and require confirmation before applying actions.")
        if preferences["preferred_ai_behavior"] == "concise_suggestions":
            actions.append("Prefer shorter suggestions optimized for fast iteration.")
        if preferences["preferred_ai_behavior"] == "explanation_first":
            actions.append("Show rationale and source-backed explanations before proposing actions.")
        if preferences["editing_behavior"] == "heavy_editor":
            actions.append("Provide editable drafts instead of longer auto-complete blocks.")
        if "increased_distrust" in baseline_analysis["deviations"]:
            actions.append("Switch to review-first mode until trust returns to baseline.")
        if "abnormal_stress" in baseline_analysis["deviations"]:
            actions.append("Lower autonomy and break actions into smaller steps.")
        if not actions:
            actions.append("Keep current suggestion style; behavior matches the learned profile.")
        return actions

    def update_user_profile(
        self,
        user_id: str,
        session_id: str,
        features: dict,
        trust_signals: dict,
        scores: dict,
    ) -> dict:
        summary = SessionPreferenceSummary(
            user_id=user_id,
            session_id=session_id,
            typing_cpm=float(features.get("typing_cpm", 0.0)),
            pause_mean=float(features.get("iki_mean", 0.0)),
            backspace_ratio=float(features.get("backspace_ratio", 0.0)),
            hesitation_rate=float(features.get("hesitation_count", 0.0)),
            accept_rate=float(trust_signals.get("accept_rate", 0.0)),
            override_rate=float(trust_signals.get("override_rate", 0.0)),
            trust_score=float(scores["trust_in_ai"]["score"]),
            stress_score=float(scores["stress"]["score"]),
            engagement_score=float(scores["engagement"]["score"]),
            load_score=float(scores["cognitive_load"]["score"]),
            content_intensity=max(float(features.get("content_intensity_mean", 0.0)), float(features.get("content_intensity_recent", 0.0))),
        )
        self._upsert_session_summary(summary)
        sessions = self._load_user_sessions(user_id)
        previous_profile = self.get_profile(user_id)
        profile = self._build_profile(user_id, sessions)
        profile = self._apply_moving_average(previous_profile, summary, profile)
        self._save_profile(profile)
        preferences = self._infer_preferences(profile)
        baseline_analysis = self._baseline_analysis(summary, profile)

        return {
            "profile": profile,
            "baseline_learning_phase": len(sessions) < BASELINE_MIN_SESSIONS,
            "baseline_learning_sessions": len(sessions),
            "user_preferences": preferences,
            "baseline_delta_analysis": baseline_analysis,
            "adaptive_ai_behavior": self._adaptive_behavior(preferences, baseline_analysis),
        }
