from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .decision_smoother import DecisionSmoother


class AutonomyDecisionEngine:
    """Decides autonomy mode from behavioral state, trust, risk, and context."""

    def __init__(self, model_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.model_path = model_path or (root / "data" / "autonomy_policy.joblib")
        self.model = None
        self.backend = "rule_based"
        self.smoother = DecisionSmoother()
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            return
        try:
            import joblib  # type: ignore

            self.model = joblib.load(self.model_path)
            self.backend = "sklearn_joblib"
        except Exception:
            self.model = None
            self.backend = "rule_based"

    @staticmethod
    def _complexity_score(code_context: Dict[str, object]) -> float:
        syntax_errors = float(code_context.get("syntax_errors", 0))
        function_length = float(code_context.get("function_length", 0))
        recent_edits = float(code_context.get("recent_edits", 0))
        compilation_failures = float(code_context.get("compilation_failures", 0))
        complexity = (
            min(1.0, syntax_errors / 2.0) * 0.35
            + min(1.0, function_length / 80.0) * 0.25
            + min(1.0, recent_edits / 8.0) * 0.2
            + min(1.0, compilation_failures / 2.0) * 0.2
        )
        return round(min(1.0, complexity), 3)

    def _rule_policy(
        self,
        scores: Dict[str, dict],
        risk_severity: Dict[str, float],
        trust_signals: Dict[str, float],
        user_preferences: Dict[str, object],
        code_context: Dict[str, object],
        suggestion_quality: Dict[str, object],
        trust_trend: str,
        fused_trust: Dict[str, object],
    ) -> Dict[str, object]:
        stress = float(scores["stress"]["score"])
        stress_conf = float(scores["stress"]["probability"])
        load = float(scores["cognitive_load"]["score"])
        load_conf = float(scores["cognitive_load"]["probability"])
        trust = float(fused_trust["score"])
        trust_conf = float(fused_trust["probability"])
        engagement = float(scores["engagement"]["score"])
        override_rate = float(trust_signals.get("override_rate", 0.0))
        complexity = self._complexity_score(code_context)
        automation_preference = str(user_preferences.get("automation_preference", "suggestion_review_mode"))
        trust_profile = str(user_preferences.get("trust_profile", "calibrated_trust_user"))
        suggestion_quality_score = float(suggestion_quality.get("suggestion_quality_score", 0.5))

        hostility = float(risk_severity.get("hostility", 0.0))
        emotional = float(risk_severity.get("emotional_intensity", 0.0))
        ai_distrust = float(risk_severity.get("ai_distrust", 0.0))
        high_risk = max(hostility, emotional, ai_distrust) >= 0.75
        high_stress = stress >= 0.7 and stress_conf > 0.6
        high_load = load >= 0.7 and load_conf > 0.6
        uncertain = min(stress_conf, load_conf, trust_conf) < 0.6

        if hostility > 0.75:
            mode = "approval_required"
            reason = "Severe hostility detected."
        elif emotional > 0.5 or ai_distrust > 0.7:
            mode = "require_confirmation"
            reason = "Emotional intensity or distrust exceeds safe threshold."
        elif uncertain:
            mode = "suggest_only"
            reason = "Prediction confidence is low; falling back to safer suggestion-only mode."
        elif fused_trust["score"] < 0.3 and high_stress:
            mode = "require_confirmation"
            reason = "Low fused trust and elevated stress detected."
        elif high_load or complexity >= 0.7:
            mode = "suggest_only"
            reason = "High cognitive load or coding complexity detected."
        elif automation_preference == "require_confirmation" or override_rate >= 0.45:
            mode = "require_confirmation"
            reason = "User preference or override behavior indicates manual checkpointing."
        elif trust_trend == "decreasing":
            mode = "require_confirmation"
            reason = "User trust trend is decreasing."
        elif trust >= 0.7 and hostility < 0.3 and ai_distrust < 0.4 and stress < 0.55 and engagement >= 0.55:
            mode = "auto_execute"
            reason = "High fused trust, low risk, and stable engagement detected."
        else:
            mode = "suggest_only"
            reason = "Mixed signals; maintaining suggestion-only mode."

        suggestion_frequency = "medium"
        if suggestion_quality_score < 0.35:
            suggestion_frequency = "low"
        elif suggestion_quality_score > 0.7 and trust >= 0.7:
            suggestion_frequency = "high"
        elif mode in {"approval_required", "suggest_only"} or stress >= 0.7:
            suggestion_frequency = "low"
        elif trust >= 0.8 and engagement >= 0.7 and complexity < 0.45:
            suggestion_frequency = "high"

        explanation_mode = (
            mode in {"require_confirmation", "approval_required"}
            or trust_profile == "low_trust_user"
            or complexity >= 0.55
            or suggestion_quality_score < 0.35
        )

        priority = "normal"
        if high_risk:
            priority = "critical"
        elif complexity >= 0.65 or load >= 0.65:
            priority = "high"
        elif trust >= 0.8 and max(risk_severity.values()) < 0.3:
            priority = "low"

        risk_score = max(hostility, emotional, ai_distrust, float(risk_severity.get("toxicity", 0.0)))
        confidence = max(0.0, min(1.0, (trust_conf + stress_conf + risk_score) / 3.0))

        return {
            "mode": mode,
            "reason": reason,
            "suggestion_frequency": suggestion_frequency,
            "explanation_mode": explanation_mode,
            "priority": priority,
            "policy_backend": self.backend,
            "task_complexity": complexity,
            "confidence": round(confidence, 3),
        }

    def _ml_policy(
        self,
        scores: Dict[str, dict],
        risk_severity: Dict[str, float],
        trust_signals: Dict[str, float],
        code_context: Dict[str, object],
    ) -> Optional[Dict[str, object]]:
        if self.model is None:
            return None
        try:
            row = [[
                float(scores["stress"]["score"]),
                float(scores["cognitive_load"]["score"]),
                float(scores["trust_in_ai"]["score"]),
                float(scores["engagement"]["score"]),
                float(trust_signals.get("override_rate", 0.0)),
                float(self._complexity_score(code_context)),
                max(float(v) for v in risk_severity.values()) if risk_severity else 0.0,
            ]]
            mode = str(self.model.predict(row)[0])
        except Exception:
            return None

        reason_map = {
            "auto_execute": "ML policy selected autonomous execution.",
            "require_confirmation": "ML policy selected confirmation checkpoint.",
            "suggest_only": "ML policy reduced autonomy because of current session state.",
            "approval_required": "ML policy detected elevated execution risk.",
        }
        return {
            "mode": mode,
            "reason": reason_map.get(mode, "ML policy selected the autonomy mode."),
            "policy_backend": self.backend,
        }

    def decide(
        self,
        user_id: str,
        scores: Dict[str, dict],
        risk_severity: Dict[str, float],
        trust_signals: Dict[str, float],
        user_preferences: Dict[str, object],
        code_context: Dict[str, object],
        suggestion_quality: Dict[str, object],
        trust_trend: str,
        fused_trust: Dict[str, object],
    ) -> Dict[str, object]:
        decision = self._rule_policy(
            scores,
            risk_severity,
            trust_signals,
            user_preferences,
            code_context,
            suggestion_quality,
            trust_trend,
            fused_trust,
        )
        ml = self._ml_policy(scores, risk_severity, trust_signals, code_context)
        if ml is not None:
            decision["mode"] = ml["mode"]
            decision["reason"] = ml["reason"]
            decision["policy_backend"] = ml["policy_backend"]

        safe_state = (
            max(float(v) for v in risk_severity.values()) < 0.3
            and float(fused_trust["score"]) >= 0.6
            and float(scores["stress"]["score"]) < 0.6
        )
        smooth = self.smoother.smooth(user_id=user_id, proposed_mode=str(decision["mode"]), safe_state=safe_state)
        if smooth["mode"] != decision["mode"]:
            decision["reason"] = f"{decision['reason']} Smoothed from {decision['mode']} to {smooth['mode']}."
        decision["mode"] = smooth["mode"]
        decision["decision_smoothing_state"] = smooth["state"]
        decision["smoothing_applied"] = bool(smooth["smoothed"])
        return decision
