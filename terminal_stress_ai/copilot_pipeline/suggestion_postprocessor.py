from __future__ import annotations

import re
from typing import Dict


class SuggestionPostProcessor:
    """Normalizes raw LLM output into a structured suggestion object."""

    CODE_BLOCK_PATTERN = re.compile(r"```(?P<lang>[a-zA-Z0-9_+-]*)\n(?P<code>.*?)```", re.DOTALL)

    def process(self, llm_output: Dict[str, object]) -> Dict[str, object]:
        raw_content = str(llm_output.get("content", "") or "")
        extracted = self._extract_code(raw_content)
        language = str(llm_output.get("language") or extracted["language"] or self._detect_language(raw_content))
        content = extracted["code"] or raw_content
        suggestion_type = str(llm_output.get("type", "code"))
        confidence = self._confidence(llm_output, content)
        safe_to_execute = suggestion_type in {"code", "code_modification"} and confidence >= 0.8

        return {
            "suggestion_type": suggestion_type,
            "language": language,
            "content": content.strip(),
            "confidence": confidence,
            "explanation": str(llm_output.get("explanation", "") or "No explanation provided."),
            "safe_to_execute": safe_to_execute,
            "provider": str(llm_output.get("provider", "template")),
        }

    def _extract_code(self, raw_content: str) -> Dict[str, str]:
        match = self.CODE_BLOCK_PATTERN.search(raw_content)
        if not match:
            return {"language": "", "code": ""}
        return {
            "language": match.group("lang").strip(),
            "code": match.group("code").strip(),
        }

    def _detect_language(self, raw_content: str) -> str:
        lowered = raw_content.lower()
        if "#include" in lowered or "std::cout" in lowered:
            return "cpp"
        if "def " in lowered or "print(" in lowered:
            return "python"
        if "function " in lowered or "console.log" in lowered:
            return "javascript"
        return "plain_text"

    def _confidence(self, llm_output: Dict[str, object], content: str) -> float:
        base = 0.82 if str(llm_output.get("provider", "")) in {"openai", "local_llm"} else 0.7
        if not content.strip():
            return 0.2
        if len(content.splitlines()) >= 3:
            base += 0.08
        return round(min(0.99, base), 3)
