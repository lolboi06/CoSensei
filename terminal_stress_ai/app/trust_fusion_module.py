from __future__ import annotations

from typing import Dict


class TrustFusionModule:
    def __init__(self, engine_weight: float = 0.6, model_weight: float = 0.4) -> None:
        self.engine_weight = engine_weight
        self.model_weight = model_weight

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

    def fuse(self, trust_model: Dict[str, object], trust_engine: Dict[str, object]) -> Dict[str, object]:
        model_score = float(trust_model.get("score", 0.0))
        model_probability = float(trust_model.get("probability", 0.5))
        engine_score = float(trust_engine.get("trust_score", 0.0))

        fused_score = self._clip(self.engine_weight * engine_score + self.model_weight * model_score)
        divergence = abs(engine_score - model_score)
        fusion_confidence = self._clip(0.5 + 0.5 * (1.0 - divergence))
        fused_probability = self._clip(0.5 + (model_probability - 0.5) * fusion_confidence)

        return {
            "score": round(fused_score, 3),
            "probability": round(fused_probability, 3),
            "level": self._level(fused_score),
            "model_score": round(model_score, 3),
            "engine_score": round(engine_score, 3),
            "divergence": round(divergence, 3),
            "fusion_confidence": round(fusion_confidence, 3),
        }
