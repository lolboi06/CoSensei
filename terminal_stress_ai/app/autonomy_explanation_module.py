from __future__ import annotations

from typing import Dict


class AutonomyExplanationModule:
    def explain(
        self,
        shared_autonomy: Dict[str, object],
        fused_trust: Dict[str, object],
        scores: Dict[str, dict],
        risk_severity: Dict[str, float],
    ) -> Dict[str, str]:
        mode = str(shared_autonomy.get("autonomy_mode", "SHARED_CONTROL"))
        trust = float(fused_trust.get("score", 0.0))
        stress = float(scores["stress"]["score"])
        load = float(scores["cognitive_load"]["score"])
        hostility = float(risk_severity.get("hostility", 0.0))
        emotional = float(risk_severity.get("emotional_intensity", 0.0))

        if mode == "AI_FULL":
            text = "Trust is high, risk is low, and the session appears stable, so the system can execute actions automatically."
        elif mode == "AI_ASSIST":
            text = "Trust and suggestion quality are strong enough for active AI assistance, but the human remains available for oversight."
        elif mode == "HUMAN_CONTROL":
            text = "Risk or distrust is elevated, so the system limits itself to minimal suggestions and keeps control with the human."
        else:
            text = "Stress levels are high or trust is moderate, so the system will provide suggestions, explain them, and require human approval."

        detail = (
            f" trust={trust:.2f}, stress={stress:.2f}, load={load:.2f}, "
            f"hostility={hostility:.2f}, emotional_intensity={emotional:.2f}"
        )
        return {"explanation": text.strip(), "signal_summary": detail.strip()}
