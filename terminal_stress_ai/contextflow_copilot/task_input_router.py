from __future__ import annotations

import re
from typing import Dict


class TaskInputRouter:
    """Parses raw input into a normalized copilot task description."""

    LANGUAGE_MAP = {
        "c++": "cpp",
        "cpp": "cpp",
        "python": "python",
        "javascript": "javascript",
        "js": "javascript",
        "typescript": "typescript",
        "ts": "typescript",
        "java": "java",
        "rust": "rust",
        "go": "go",
        "c#": "csharp",
        "csharp": "csharp",
    }

    def parse_input(self, user_input: str) -> Dict[str, str]:
        raw_input = self._normalize_input(user_input.strip().strip("`").strip("\\/"))
        lowered = f" {raw_input.lower()} "
        language = self._detect_language(lowered)
        task_type = self._detect_task_type(lowered)
        goal = self._extract_goal(raw_input, language)
        return {
            "task_type": task_type,
            "language": language,
            "goal": goal,
            "raw_input": raw_input,
        }

    def _normalize_input(self, user_input: str) -> str:
        normalized = f" {user_input.lower()} "
        replacements = {
            " e-commerece ": " e-commerce ",
            " e-commerence ": " e-commerce ",
            " ecommerece ": " ecommerce ",
            " ecommercee ": " ecommerce ",
            " aroung ": " around ",
            " physicis ": " physics ",
            " gam theroy ": " game theory ",
            " dashbaord ": " dashboard ",
            " c sharp ": " c# ",
            " c sharp. ": " c# ",
        }
        for wrong, right in replacements.items():
            normalized = normalized.replace(wrong, right)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _detect_language(self, lowered: str) -> str:
        for hint, language in self.LANGUAGE_MAP.items():
            if hint in lowered:
                return language
        if " c " in lowered:
            return "c"
        return "plain_text"

    def _detect_task_type(self, lowered: str) -> str:
        casual_greetings = {"hi", "hello", "hey", "hello there", "hey there"}
        normalized = lowered.strip()
        build_tokens = [
            " build ",
            " make ",
            " code ",
            " program ",
            " website ",
            " app ",
            " system ",
            " tool ",
            " game ",
        ]
        has_code_intent = any(token in lowered for token in build_tokens)
        if (normalized in casual_greetings or " how are " in lowered or " what's up " in lowered or " whats up " in lowered) and not has_code_intent:
            return "casual_conversation"
        if any(token in lowered for token in [" write ", " create ", " generate ", " snippet "]):
            return "code_generation"
        if any(token in lowered for token in [" game ", " gameplay ", " multiplayer ", " shooter ", " rpg ", " puzzle game ", " strategy game "]):
            return "software_development"
        if any(token in lowered for token in [" build ", " make ", " system ", " app ", " service ", " backend ", " frontend ", " website ", " tool ", " program "]):
            return "software_development"
        if any(token in lowered for token in [" debug ", " fix ", " bug ", " error ", " traceback "]):
            return "debugging"
        if any(token in lowered for token in [" explain ", " how does ", " why does ", " what does "]):
            return "explanation"
        if any(token in lowered for token in [" docs ", " documentation ", " api ", " reference "]):
            return "documentation"
        if any(token in lowered for token in [" write ", " create ", " generate ", " build ", " code ", " program ", " snippet "]):
            return "code_generation"
        return "general_query"

    def _extract_goal(self, raw_input: str, language: str) -> str:
        goal = raw_input.strip()
        prefixes = ("write ", "create ", "generate ", "build ", "debug ", "fix ", "explain ")
        lowered = goal.lower()
        for prefix in prefixes:
            if lowered.startswith(prefix):
                goal = goal[len(prefix) :].strip()
                break
        if language != "plain_text":
            goal = goal.replace(language, "", 1).strip()
            if language == "cpp":
                goal = goal.replace("c++", "", 1).strip()
        return goal or raw_input.strip()
