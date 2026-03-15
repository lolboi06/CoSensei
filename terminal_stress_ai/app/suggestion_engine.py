from __future__ import annotations

import os
from typing import Dict

from .suggestion_generator import SuggestionGenerator


class SuggestionEngine:
    def __init__(self) -> None:
        self.generator = SuggestionGenerator()

    def generate(
        self,
        task_understanding: Dict[str, object],
        memory: Dict[str, object],
        task_context: Dict[str, object],
        user_preferences: Dict[str, object],
        working_memory: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        active_task = str(task_understanding.get("active_task", "writing_new_code"))
        previous_code = str(task_understanding.get("retrieved_code", "") or (working_memory or {}).get("generated_code", ""))
        generator_intent = {
            "task": {
                "casual_conversation": "casual_conversation",
                "editing_previous_code": "writing_new_code",
                "asking_for_explanation": "exploring_api",
                "debugging_code": "debugging",
                "refactoring_code": "refactoring",
                "writing_new_code": "writing_new_code",
            }.get(active_task, "writing_new_code")
        }
        if active_task == "casual_conversation":
            content = "I am functioning normally. If you want code, tell me the language and the task."
            return {
                "type": "response",
                "language": "plain_text",
                "content": content,
                "explanation": "Casual conversation detected; returning a plain-language response instead of code.",
                "source": "template",
                "provider": "template",
                "continuation": False,
                "structured_output": {
                    "suggestion": {
                        "type": "response",
                        "language": "plain_text",
                        "content": content,
                        "explanation": "Casual conversation detected; returning a plain-language response instead of code.",
                    }
                },
            }
        suggestion = self.generator.generate(
            user_intent=generator_intent,
            memory=memory,
            task_context=task_context,
            user_preferences=user_preferences,
            task_understanding=task_understanding,
        )
        suggestion_type = "code"
        if active_task == "asking_for_explanation":
            suggestion_type = "explanation"
        elif active_task == "debugging_code":
            suggestion_type = "debug_strategy"
        elif active_task == "editing_previous_code":
            suggestion_type = "code_modification"
        elif active_task == "refactoring_code":
            suggestion_type = "code_modification"
        provider = "template"
        if os.getenv("CONTEXTFLOW_LLM_ENABLED", "").lower() in {"1", "true", "yes"}:
            provider = "llm"
        return {
            "type": suggestion_type,
            "language": suggestion.get("language", task_context.get("language", "")),
            "content": suggestion.get("code", ""),
            "explanation": suggestion.get("explanation", ""),
            "source": suggestion.get("source", provider),
            "provider": provider,
            "continuation": bool(previous_code),
            "structured_output": {
                "suggestion": {
                    "type": suggestion_type,
                    "language": suggestion.get("language", task_context.get("language", "")),
                    "content": suggestion.get("code", ""),
                    "explanation": suggestion.get("explanation", ""),
                }
            },
        }
