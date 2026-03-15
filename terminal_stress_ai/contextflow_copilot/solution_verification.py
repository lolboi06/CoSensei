from __future__ import annotations

from typing import Dict, List

from .suggestion_quality import SuggestionQualityEvaluator


class SolutionVerificationEngine:
    """Scores and ranks candidate suggestions before ContextFlow receives them."""

    def __init__(self, evaluator: SuggestionQualityEvaluator | None = None) -> None:
        self.evaluator = evaluator or SuggestionQualityEvaluator()

    def verify(self, suggestions: List[Dict[str, object]], verification_level: str = "balanced") -> Dict[str, object]:
        verification: List[Dict[str, object]] = []
        best_id = 0
        best_score = -1.0
        level_bias = {"balanced": 1.0, "strict": 0.9}.get(verification_level, 1.0)

        for suggestion in suggestions:
            quality = self.evaluator.evaluate(
                {
                    "suggestion_type": suggestion.get("type", "code"),
                    "language": suggestion.get("language", "plain_text"),
                    "content": suggestion.get("content", ""),
                    "confidence": 0.82,
                }
            )
            score = round(float(quality["quality_score"]) * level_bias, 3)
            item = {
                "suggestion_id": suggestion["id"],
                "score": score,
                "valid_code": quality["valid_code"],
                "safe_to_execute": quality["safe_to_execute"],
            }
            verification.append(item)
            if score > best_score:
                best_score = score
                best_id = int(suggestion["id"])

        return {
            "verification": verification,
            "recommended": best_id,
        }
