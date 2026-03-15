from __future__ import annotations

import ast
from typing import Dict


class SuggestionQualityEvaluator:
    """Evaluates suggestion quality before ContextFlow autonomy checks."""

    def evaluate(self, suggestion: Dict[str, object]) -> Dict[str, object]:
        content = str(suggestion.get("content", "") or "")
        language = str(suggestion.get("language", "plain_text"))
        confidence = float(suggestion.get("confidence", 0.0))

        valid_code = self._valid_code(content, language, str(suggestion.get("suggestion_type", "")))
        completeness = self._completeness(content)
        quality_score = round(min(1.0, 0.45 * confidence + 0.35 * completeness + 0.20 * (1.0 if valid_code else 0.0)), 3)
        safe_to_execute = valid_code and quality_score >= 0.8 and str(suggestion.get("suggestion_type", "")) in {"code", "code_modification"}

        return {
            "quality_score": quality_score,
            "valid_code": valid_code,
            "safe_to_execute": safe_to_execute,
            "completeness_score": completeness,
            "language_detected": language,
        }

    def _valid_code(self, content: str, language: str, suggestion_type: str) -> bool:
        if suggestion_type not in {"code", "code_modification"}:
            return bool(content.strip())
        if not content.strip():
            return False
        if language == "python":
            try:
                ast.parse(content)
                return True
            except SyntaxError:
                return False
        if language in {"cpp", "c", "javascript", "typescript", "java", "rust", "go"}:
            return self._balanced_delimiters(content)
        return len(content.strip()) > 0

    def _balanced_delimiters(self, content: str) -> bool:
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack: list[str] = []
        for char in content:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                opening = stack.pop()
                if pairs[opening] != char:
                    return False
        return not stack

    def _completeness(self, content: str) -> float:
        stripped = [line for line in content.splitlines() if line.strip()]
        if not stripped:
            return 0.0
        if len(stripped) >= 5:
            return 0.95
        if len(stripped) >= 2:
            return 0.75
        return 0.55
