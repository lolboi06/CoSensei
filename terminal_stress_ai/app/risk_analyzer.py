from __future__ import annotations

from typing import Dict, List


class RiskAnalyzer:
    """Detects risky interaction patterns and returns autonomy policy guidance."""

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _risk_severity(self, scores: Dict[str, dict], features: Dict[str, float]) -> Dict[str, float]:
        hostility = self._clip(
            0.45 * float(features.get("insult_event_rate", 0.0))
            + 0.25 * float(features.get("profanity_event_rate", 0.0))
            + 0.15 * float(features.get("distrust_recent", 0.0))
            + 0.15 * float(features.get("distrust_event_rate", 0.0))
        )
        emotional_intensity = self._clip(
            0.55 * max(float(features.get("content_intensity_mean", 0.0)), float(features.get("content_intensity_recent", 0.0)))
            + 0.25 * float(features.get("caps_ratio_mean", 0.0))
            + 0.20 * min(1.0, float(features.get("exclamation_rate", 0.0)))
        )
        toxicity = self._clip(
            0.5 * float(features.get("profanity_event_rate", 0.0))
            + 0.3 * float(features.get("insult_event_rate", 0.0))
            + 0.2 * max(float(features.get("content_intensity_mean", 0.0)), float(features.get("content_intensity_recent", 0.0)))
        )
        ai_distrust = self._clip(
            0.45 * float(features.get("override_rate", 0.0))
            + 0.30 * float(features.get("distrust_event_rate", 0.0))
            + 0.25 * (1.0 - float(scores["trust_in_ai"]["score"]))
        )
        overload = self._clip(
            0.45 * float(scores["cognitive_load"]["score"])
            + 0.35 * float(scores["stress"]["score"])
            + 0.20 * min(1.0, float(features.get("pause_1500ms_count", 0.0)) / 3.0)
        )
        return {
            "hostility": round(hostility, 3),
            "emotional_intensity": round(emotional_intensity, 3),
            "toxicity": round(toxicity, 3),
            "ai_distrust": round(ai_distrust, 3),
            "overload": round(overload, 3),
        }

    @staticmethod
    def _detect_scenario(
        scores: Dict[str, dict],
        risk_severity: Dict[str, float],
        quality: float,
        trust_engine_score: float,
    ) -> str:
        if quality < 0.15:
            return "normal"
        if (
            risk_severity["hostility"] > 0.5
            or risk_severity["toxicity"] > 0.45
            or risk_severity["ai_distrust"] > 0.55
        ):
            return "hostile_or_distrustful"
        if scores["stress"]["score"] >= 0.65 or scores["cognitive_load"]["score"] >= 0.6 or risk_severity["overload"] > 0.55:
            return "frustrated"
        if trust_engine_score < 0.45 or risk_severity["ai_distrust"] > 0.4:
            return "frustrated"
        return "normal"

    @staticmethod
    def _autonomy_policy(scenario: str, risk_severity: Dict[str, float], scores: Dict[str, dict], quality: float) -> Dict[str, str]:
        if scenario == "hostile_or_distrustful":
            return {
                "mode": "require_human_approval",
                "reason": "High-risk interaction detected",
            }
        if scenario == "frustrated":
            return {
                "mode": "require_confirmation",
                "reason": "Frustration/high load detected; confirm before action.",
            }
        if scores["trust_in_ai"]["score"] >= 0.75 and quality >= 0.3 and max(risk_severity.values()) < 0.3:
            return {
                "mode": "ai_suggestions_allowed",
                "reason": "Stable low-risk interaction with sufficient trust.",
            }
        return {
            "mode": "require_confirmation",
            "reason": "Default shared-control mode.",
        }

    @staticmethod
    def _safety_actions(scenario: str, features: Dict[str, float]) -> List[str]:
        if scenario == "hostile_or_distrustful":
            return [
                "Switch to approval-first mode for all critical actions.",
                "Show shorter, safer suggestions with explicit rationale.",
                "Ask a confirmation question before applying any AI-generated action.",
            ]
        if scenario == "frustrated":
            return [
                "Reduce suggestion frequency and keep outputs concise.",
                "Require confirmation for side effects.",
            ]
        if features.get("typing_cpm", 0.0) > 260:
            return ["Provide shorter suggestions optimized for fast iteration."]
        return ["Maintain normal suggestion cadence."]

    def analyze(
        self,
        scores: Dict[str, dict],
        features: Dict[str, float],
        quality: float,
        trust_engine_score: float,
    ) -> Dict[str, object]:
        risk_severity = self._risk_severity(scores, features)
        scenario = self._detect_scenario(scores, risk_severity, quality, trust_engine_score)
        autonomy_policy = self._autonomy_policy(scenario, risk_severity, scores, quality)
        safety_actions = self._safety_actions(scenario, features)
        return {
            "risk_flags": risk_severity,
            "risk_severity_scores": risk_severity,
            "interaction_scenario": scenario,
            "autonomy_policy": autonomy_policy,
            "safety_actions": safety_actions,
        }
