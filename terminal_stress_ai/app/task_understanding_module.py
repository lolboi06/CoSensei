from __future__ import annotations

import re
from typing import Dict


class TaskUnderstandingModule:
    def _recent_user_messages(self, history: list[dict]) -> list[str]:
        return [str(item.get("content", "")) for item in history if item.get("role") == "user" and item.get("content")]

    def understand(
        self,
        memory: Dict[str, object],
        current_message: str,
        detected_intent: Dict[str, object],
        working_memory: Dict[str, object] | None = None,
        long_term_memory: Dict[str, object] | None = None,
        code_context: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        message = current_message.lower()
        previous_code = str((working_memory or {}).get("generated_code") or memory.get("code_memory", {}).get("last_generated_code", ""))
        active_task = str(detected_intent.get("task", "writing_new_code"))
        history = memory.get("conversation_history", [])
        recent_user_messages = self._recent_user_messages(history)
        previous_task = str((working_memory or {}).get("active_task", "") or memory.get("task_context", {}).get("active_task", ""))

        if any(token in message for token in ["modify", "change", "update", "rewrite", "convert"]) and previous_code:
            active_task = "editing_previous_code"
        elif active_task == "casual_conversation":
            active_task = "casual_conversation"
        elif any(token in message for token in ["explain", "how does this work", "why", "what is happening"]):
            active_task = "asking_for_explanation"
        elif "debug" in message or "fix" in message or "error" in message:
            active_task = "debugging_code"
        elif "refactor" in message:
            active_task = "refactoring_code"
        elif any(token in message for token in ["write", "make", "create", "program"]):
            active_task = "writing_new_code"

        continuity = 1.0 if previous_code and active_task == "editing_previous_code" else 0.6
        if active_task == previous_task:
            continuity = max(continuity, 0.8)
        if previous_code and re.search(r"\b(now|instead|also|same|that|it)\b", message):
            continuity = max(continuity, 0.9)

        explicit_language = ""
        if "c++" in message or "cpp" in message:
            explicit_language = "cpp"
        elif "python" in message:
            explicit_language = "python"
        elif "javascript" in message or "node" in message:
            explicit_language = "javascript"

        if explicit_language and previous_code:
            previous_language = str(memory.get("code_memory", {}).get("language", "") or (working_memory or {}).get("language", ""))
            if previous_language and previous_language != explicit_language:
                previous_code = ""

        objective = current_message.strip() or (recent_user_messages[-1] if recent_user_messages else "")
        language = explicit_language or str((code_context or {}).get("language") or memory.get("code_memory", {}).get("language", "python"))
        if language == "plain_text":
            language = explicit_language or ("plain_text" if active_task == "casual_conversation" else "python")
        task_continuity = "continued_task" if continuity >= 0.8 else "new_task"

        return {
            "active_task": active_task,
            "confidence": round(continuity, 3),
            "uses_previous_code": bool(previous_code and active_task in {"editing_previous_code", "refactoring_code", "debugging_code"}),
            "task_continuity": task_continuity,
            "task_objective": objective,
            "retrieved_code": previous_code,
            "language": language,
            "reasoning_state": f"Detected {active_task} with {task_continuity}.",
            "user_profile_hints": (long_term_memory or {}).get("user_preferences", {}),
        }
