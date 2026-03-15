from __future__ import annotations

from typing import Dict, Optional


class ContextBuilder:
    """Builds structured context for an LLM or template suggestion generator."""

    def build_context(
        self,
        task_info: Dict[str, object],
        memory: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        memory = memory or {}
        conversation_history = list(memory.get("conversation_history", []))
        current_code = str(memory.get("current_code", "") or memory.get("working_code", ""))
        user_preferences = dict(memory.get("user_preferences", {}))

        return {
            "language": task_info.get("language", "plain_text"),
            "task": task_info.get("task", "general_query"),
            "objective": task_info.get("objective", ""),
            "requires_context": bool(task_info.get("requires_context", False)),
            "is_continuation": bool(task_info.get("is_continuation", False)),
            "framework": task_info.get("framework"),
            "storage": task_info.get("storage"),
            "clarification_state": dict(task_info.get("clarification_state", {})),
            "previous_code": current_code,
            "conversation_history": conversation_history[-8:],
            "user_preferences": user_preferences,
            "prompt_context": self._prompt_context(task_info, current_code, user_preferences),
        }

    def _prompt_context(self, task_info: Dict[str, object], current_code: str, user_preferences: Dict[str, object]) -> str:
        tone = str(user_preferences.get("preferred_ai_behavior", "balanced_guidance"))
        context_clause = "Use and preserve the existing code." if current_code else "Produce a fresh suggestion."
        framework = task_info.get("framework") or "none"
        storage = task_info.get("storage") or "none"
        return (
            "You are a lightweight coding copilot. "
            f"Task={task_info.get('task', 'general_query')}. "
            f"Language={task_info.get('language', 'plain_text')}. "
            f"Objective={task_info.get('objective', '')}. "
            f"Framework={framework}. "
            f"Storage={storage}. "
            f"Preference={tone}. "
            f"{context_clause}"
        )
