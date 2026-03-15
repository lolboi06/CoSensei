from __future__ import annotations

from typing import Dict, List, Optional


class ContextBuilder:
    """Builds an LLM-ready context object from task and memory state."""

    def build_context(
        self,
        task: Dict[str, str],
        memory: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        memory = memory or {}
        conversation_history = list(memory.get("conversation_history", []))
        previous_code = str(memory.get("working_code", "") or memory.get("previous_code", ""))
        user_preferences = dict(memory.get("user_preferences", {}))

        return {
            "task": task,
            "language": task.get("language", "plain_text"),
            "goal": task.get("goal", ""),
            "previous_code": previous_code,
            "conversation_context": conversation_history[-8:],
            "user_preferences": user_preferences,
            "system_prompt": self._system_prompt(task, previous_code, user_preferences),
        }

    def _system_prompt(self, task: Dict[str, str], previous_code: str, user_preferences: Dict[str, object]) -> str:
        tone = str(user_preferences.get("preferred_ai_behavior", "balanced_guidance"))
        continuity = "Modify the existing code if relevant." if previous_code else "Generate a fresh suggestion."
        return (
            "You are a coding copilot. "
            f"Task type: {task.get('task_type', 'general_query')}. "
            f"Language: {task.get('language', 'plain_text')}. "
            f"Interaction preference: {tone}. "
            f"{continuity}"
        )
