from __future__ import annotations

from typing import Dict


class TaskInputRouter:
    """Parses raw user input into a normalized copilot task."""

    LANGUAGE_HINTS = {
        "c++": "cpp",
        "cpp": "cpp",
        "python": "python",
        "py": "python",
        "javascript": "javascript",
        "js": "javascript",
        "typescript": "typescript",
        "ts": "typescript",
        "java": "java",
        "rust": "rust",
        "go": "go",
        "c#": "csharp",
        "csharp": "csharp",
        "c ": "c",
    }

    def parse_input(self, user_input: str) -> Dict[str, str]:
        text = user_input.strip()
        lowered = f" {text.lower()} "
        language = self._detect_language(lowered)
        task_type = self._task_type(lowered)
        goal = self._goal(text, task_type, language)

        return {
            "task_type": task_type,
            "language": language,
            "goal": goal,
            "raw_input": text,
        }

    def _detect_language(self, lowered: str) -> str:
        for hint, language in self.LANGUAGE_HINTS.items():
            if hint in lowered:
                return language
        return "plain_text"

    def _task_type(self, lowered: str) -> str:
        if any(token in lowered for token in [" debug ", " fix ", " error ", " traceback ", " bug "]):
            return "debugging"
        if any(token in lowered for token in [" explain ", " what does ", " how does ", " why does "]):
            return "explanation"
        if any(token in lowered for token in [" write ", " create ", " generate ", " build ", " program ", " snippet ", " code "]):
            return "code_generation"
        return "general_query"

    def _goal(self, user_input: str, task_type: str, language: str) -> str:
        if task_type == "general_query":
            return user_input.strip()

        goal = user_input.strip()
        for prefix in ["write", "create", "generate", "build", "debug", "fix", "explain"]:
            if goal.lower().startswith(prefix + " "):
                goal = goal[len(prefix) + 1 :]
                break
        if language != "plain_text":
            goal = goal.replace(language, "", 1).strip()
            if language == "cpp":
                goal = goal.replace("c++", "", 1).strip()
        return goal or user_input.strip()
