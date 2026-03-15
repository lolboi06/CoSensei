from __future__ import annotations

from typing import Dict, Optional


class TaskUnderstandingEngine:
    """Interprets routed tasks into copilot execution intent."""

    def understand(self, task: Dict[str, str], clarification_state: Optional[Dict[str, str]] = None) -> Dict[str, object]:
        clarification_state = clarification_state or {}
        task_type = task.get("task_type", "general_query")
        language = clarification_state.get("language") or task.get("language", "plain_text")
        objective = task.get("goal", "")
        raw_input = task.get("raw_input", "").lower()
        framework = clarification_state.get("framework")
        storage = clarification_state.get("storage")

        requires_context = task_type in {"debugging", "documentation", "software_development"} or any(
            token in raw_input for token in ["continue", "modify", "refactor", "update", "previous", "existing"]
        )
        is_continuation = any(token in raw_input for token in ["continue", "modify", "refactor", "update", "previous", "existing"])

        return {
            "task": task_type,
            "language": language,
            "objective": objective,
            "requires_context": requires_context,
            "is_continuation": is_continuation,
            "framework": framework,
            "storage": storage,
            "clarification_state": clarification_state,
        }
