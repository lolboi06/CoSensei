from __future__ import annotations

from typing import Dict


class AdaptivePolicyEngine:
    def build(
        self,
        scores: Dict[str, dict],
        trust_engine: Dict[str, object],
        intent: Dict[str, object],
        user_preferences: Dict[str, object],
        autonomy_policy: Dict[str, str],
    ) -> Dict[str, object]:
        trust_score = float(trust_engine.get("trust_score", 0.5))
        stress = float(scores["stress"]["score"])
        load = float(scores["cognitive_load"]["score"])
        interaction_style = str(user_preferences.get("interaction_style", "balanced_typist"))
        trust_profile = str(user_preferences.get("trust_profile", "calibrated_trust_user"))
        automation_preference = str(user_preferences.get("automation_preference", "suggestion_review_mode"))
        task = str(intent.get("task", "writing_new_code"))

        suggestion_frequency = "medium"
        if automation_preference == "require_confirmation" or stress >= 0.7 or load >= 0.65:
            suggestion_frequency = "low"
        elif automation_preference == "auto_accept_suggestions" and trust_score >= 0.75:
            suggestion_frequency = "high"

        explanation_mode = trust_profile == "low_trust_user" or task in {"debugging", "exploring_api"}
        confirmation_required = autonomy_policy.get("mode") in {"require_confirmation", "require_human_approval"}

        suggestion_length = "balanced"
        if interaction_style == "fast_typist":
            suggestion_length = "concise"
        elif task in {"debugging", "exploring_api"} or explanation_mode:
            suggestion_length = "detailed"

        return {
            "suggestion_frequency": suggestion_frequency,
            "explanation_mode": explanation_mode,
            "confirmation_required": confirmation_required,
            "suggestion_length": suggestion_length,
        }
