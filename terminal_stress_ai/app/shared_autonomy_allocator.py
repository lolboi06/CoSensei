from __future__ import annotations

from typing import Dict

from .decision_smoother import DecisionSmoother


class SharedAutonomyAllocator:
    LEVELS = ["HUMAN_CONTROL", "SHARED_CONTROL", "AI_ASSIST", "AI_FULL"]
    ORDER = {level: idx for idx, level in enumerate(LEVELS)}

    def __init__(self) -> None:
        self.smoother = DecisionSmoother()

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _score(
        self,
        fused_trust: Dict[str, object],
        scores: Dict[str, dict],
        suggestion_quality: Dict[str, object],
        risk_severity: Dict[str, float],
    ) -> tuple[float, float]:
        trust = float(fused_trust.get("score", 0.0))
        engagement = float(scores["engagement"]["score"])
        stress = float(scores["stress"]["score"])
        load = float(scores["cognitive_load"]["score"])
        suggestion_quality_score = float(suggestion_quality.get("suggestion_quality_score", 0.5))
        risk_score = max(float(v) for v in risk_severity.values()) if risk_severity else 0.0

        autonomy_score = (
            0.35 * trust
            + 0.2 * engagement
            + 0.15 * suggestion_quality_score
            - 0.2 * stress
            - 0.1 * risk_score
        )
        confidence = (
            float(fused_trust.get("probability", 0.5))
            + float(scores["stress"].get("probability", 0.5))
            + float(scores["engagement"].get("probability", 0.5))
            + (1.0 - min(1.0, load))
        ) / 4.0
        return self._clip(autonomy_score), self._clip(confidence)

    def _allocate_level(
        self,
        autonomy_score: float,
        confidence: float,
        risk_severity: Dict[str, float],
        trust_trend: str,
    ) -> tuple[str, str]:
        hostility = float(risk_severity.get("hostility", 0.0))
        ai_distrust = float(risk_severity.get("ai_distrust", 0.0))
        emotional = float(risk_severity.get("emotional_intensity", 0.0))

        if hostility > 0.75 or ai_distrust > 0.8:
            return "HUMAN_CONTROL", "High hostility or distrust detected."
        if hostility > 0.5 or trust_trend == "decreasing":
            return "SHARED_CONTROL", "Moderate hostility or decreasing trust trend detected."
        if confidence < 0.6:
            return "SHARED_CONTROL", "Prediction confidence is low; keeping human in the loop."
        if emotional > 0.6:
            return "SHARED_CONTROL", "Emotional intensity is elevated."
        if autonomy_score >= 0.75:
            return "AI_FULL", "High trust, engagement, and suggestion quality support full AI control."
        if autonomy_score >= 0.55:
            return "AI_ASSIST", "Signals support assisted autonomy with optional AI completion."
        if autonomy_score >= 0.35:
            return "SHARED_CONTROL", "Mixed signals support shared control."
        return "HUMAN_CONTROL", "Low autonomy score requires human control."

    def _policy_shape(self, level: str, scores: Dict[str, dict], suggestion_quality: Dict[str, object]) -> Dict[str, object]:
        suggestion_quality_score = float(suggestion_quality.get("suggestion_quality_score", 0.5))
        stress = float(scores["stress"]["score"])
        suggestion_frequency = "medium"
        if level in {"HUMAN_CONTROL", "SHARED_CONTROL"} or stress > 0.7:
            suggestion_frequency = "low"
        elif level == "AI_FULL" and suggestion_quality_score > 0.7:
            suggestion_frequency = "high"

        explanation_mode = level in {"SHARED_CONTROL", "HUMAN_CONTROL"} or suggestion_quality_score < 0.35
        priority = "normal"
        if level == "HUMAN_CONTROL":
            priority = "critical"
        elif level == "SHARED_CONTROL":
            priority = "high"
        elif level == "AI_FULL":
            priority = "low"

        return {
            "suggestion_frequency": suggestion_frequency,
            "explanation_mode": explanation_mode,
            "priority": priority,
        }

    def allocate(
        self,
        user_id: str,
        fused_trust: Dict[str, object],
        scores: Dict[str, dict],
        suggestion_quality: Dict[str, object],
        risk_severity: Dict[str, float],
        user_preferences: Dict[str, object],
        trust_trend: str,
    ) -> Dict[str, object]:
        autonomy_score, confidence = self._score(fused_trust, scores, suggestion_quality, risk_severity)
        level, reason = self._allocate_level(autonomy_score, confidence, risk_severity, trust_trend)

        safe_state = (
            max(float(v) for v in risk_severity.values()) < 0.3
            and float(fused_trust.get("score", 0.0)) >= 0.65
            and float(scores["stress"]["score"]) < 0.55
        )
        smooth = self.smoother.smooth(user_id=user_id, proposed_mode=level, safe_state=safe_state)
        final_level = str(smooth["mode"])
        if final_level != level:
            reason = f"{reason} Smoothed from {level} to {final_level}."

        policy = self._policy_shape(final_level, scores, suggestion_quality)
        automation_preference = str(user_preferences.get("automation_preference", "suggestion_review_mode"))
        if automation_preference == "require_confirmation" and final_level == "AI_FULL":
            final_level = "AI_ASSIST"
            reason = f"{reason} User preference reduced full autonomy."
            policy = self._policy_shape(final_level, scores, suggestion_quality)

        return {
            "autonomy_mode": final_level,
            "autonomy_score": round(autonomy_score, 3),
            "confidence": round(confidence, 3),
            "reason": reason,
            "decision_smoothing_state": smooth["state"],
            "smoothing_applied": bool(smooth["smoothed"]),
            **policy,
        }
