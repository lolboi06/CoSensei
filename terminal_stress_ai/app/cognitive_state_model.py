from __future__ import annotations

from typing import Dict


class CognitiveStateModel:
    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _level(score: float) -> str:
        if score < 0.33:
            return "low"
        if score < 0.66:
            return "medium"
        return "high"

    def build(
        self,
        scores: Dict[str, dict],
        fused_trust: Dict[str, object],
        risk_severity: Dict[str, float],
        suggestion_quality: Dict[str, object],
    ) -> Dict[str, object]:
        stress = float(scores["stress"]["score"])
        load = float(scores["cognitive_load"]["score"])
        engagement = float(scores["engagement"]["score"])
        trust = float(fused_trust["score"])
        frustration = self._clip(
            0.45 * stress
            + 0.25 * load
            + 0.20 * float(risk_severity.get("emotional_intensity", 0.0))
            + 0.10 * float(risk_severity.get("hostility", 0.0))
        )
        autonomy_readiness = self._clip(
            0.35 * trust
            + 0.20 * engagement
            + 0.15 * float(suggestion_quality.get("suggestion_quality_score", 0.5))
            - 0.20 * stress
            - 0.10 * float(risk_severity.get("ai_distrust", 0.0))
        )
        state_summary = "stable"
        if frustration >= 0.66:
            state_summary = "frustrated"
        elif load >= 0.66 and engagement < 0.45:
            state_summary = "overloaded"
        elif engagement >= 0.7 and trust >= 0.6:
            state_summary = "ready_for_collaboration"
        return {
            "human_cognitive_state": state_summary,
            "stress": scores["stress"],
            "cognitive_load": scores["cognitive_load"],
            "engagement": scores["engagement"],
            "trust_level": {
                "score": round(trust, 3),
                "probability": round(float(fused_trust.get("probability", 0.5)), 3),
                "level": self._level(trust),
            },
            "frustration_index": {
                "score": round(frustration, 3),
                "level": self._level(frustration),
            },
            "autonomy_readiness_score": {
                "score": round(autonomy_readiness, 3),
                "level": self._level(autonomy_readiness),
            },
        }
