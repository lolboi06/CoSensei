from __future__ import annotations

from typing import Dict, List

from .llm_suggestion_engine import LLMSuggestionEngine


class SolutionGeneratorAI:
    """Generates a set of candidate solutions using strategy-oriented prompting."""

    STRATEGIES = [
        ("simple", "Provide the most direct implementation."),
        ("optimized", "Provide an implementation optimized for performance and maintainability."),
        ("scalable", "Provide an implementation designed for extensibility and larger systems."),
    ]

    def __init__(self, llm_engine: LLMSuggestionEngine | None = None) -> None:
        self.llm_engine = llm_engine or LLMSuggestionEngine()

    def generate_solutions(self, context: Dict[str, object], suggestion_count: int = 3) -> Dict[str, object]:
        suggestions: List[Dict[str, object]] = []
        for idx, (label, instruction) in enumerate(self.STRATEGIES[:suggestion_count], start=1):
            strategy_context = dict(context)
            strategy_context["prompt_context"] = (
                f"{context.get('prompt_context', '')} "
                "Generate one solution only. "
                "It must be structurally different from the other strategies. "
                "State the architecture shape, implementation approach, and why this strategy fits. "
                f"{instruction}"
            ).strip()
            strategy_context["strategy"] = label
            generated = self.llm_engine.generate(strategy_context)
            suggestions.append(
                {
                    "id": idx,
                    "strategy": label,
                    "type": generated.get("type", "code"),
                    "language": generated.get("language", context.get("language", "plain_text")),
                    "content": generated.get("content", ""),
                    "explanation": generated.get("explanation", f"{label.title()} solution."),
                    "provider": generated.get("provider", "template"),
                }
            )
        return {"suggestions": suggestions}
