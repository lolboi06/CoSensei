from __future__ import annotations

from typing import Dict, List


class IntentPredictor:
    def predict(self, events: List[dict], features: Dict[str, float], code_context: Dict[str, object]) -> Dict[str, object]:
        text = " ".join(
            str(e.get("line_text", "")).lower()
            for e in events[-20:]
            if e.get("key") == "Enter" and e.get("line_text") is not None
        )
        last_line = next(
            (
                str(e.get("line_text", "")).lower().strip()
                for e in reversed(events[-20:])
                if e.get("key") == "Enter" and e.get("line_text") is not None
            ),
            "",
        )
        syntax_errors = int(code_context.get("syntax_errors", 0))
        function_length = int(code_context.get("function_length", 0))
        override_rate = float(features.get("override_rate", 0.0))
        backspace_ratio = float(features.get("backspace_ratio", 0.0))
        language = str(code_context.get("language", ""))

        explicit_new_code = any(
            term in text
            for term in [
                "write",
                "create",
                "make",
                "generate",
                "program",
                "hello world",
                "print ",
                "c++",
                "cpp",
                "python",
                "javascript",
            ]
        )
        casual_conversation = any(
            phrase in last_line
            for phrase in [
                "how are you",
                "how are u",
                "hello",
                "hi",
                "hey",
                "what's up",
                "whats up",
            ]
        )
        if casual_conversation and not explicit_new_code and "code" not in text and "program" not in text:
            return {"task": "casual_conversation", "confidence": 0.93}

        if any(term in text for term in ["error", "bug", "fix", "traceback", "wrong"]):
            return {"task": "debugging", "confidence": 0.82}
        if explicit_new_code:
            return {"task": "writing_new_code", "confidence": 0.86}
        if syntax_errors > 0 and language != "plain_text":
            return {"task": "debugging", "confidence": 0.72}
        if any(term in text for term in ["refactor", "cleanup", "rename", "optimize"]) or function_length >= 40:
            return {"task": "refactoring", "confidence": 0.76}
        if any(term in text for term in ["api", "docs", "library", "package", "how to use"]) or override_rate > 0.45:
            return {"task": "exploring_api", "confidence": 0.71}
        if backspace_ratio < 0.08 and syntax_errors == 0:
            return {"task": "writing_new_code", "confidence": 0.74}
        return {"task": "writing_new_code", "confidence": 0.58}
