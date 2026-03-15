from __future__ import annotations

import re
from typing import Dict


class SuggestionNormalizer:
    """Normalizes raw LLM output into a structured suggestion payload."""

    CODE_BLOCK = re.compile(r"```(?P<lang>[a-zA-Z0-9_+-]*)\n(?P<code>.*?)```", re.DOTALL)

    def normalize(self, llm_output: Dict[str, object]) -> Dict[str, object]:
        content = str(llm_output.get("content", "") or "")
        code_match = self.CODE_BLOCK.search(content)
        extracted_language = code_match.group("lang").strip() if code_match else ""
        extracted_code = code_match.group("code").strip() if code_match else content.strip()
        language = str(llm_output.get("language") or extracted_language or self._detect_language(extracted_code))

        return {
            "suggestion_type": str(llm_output.get("type", "code")),
            "language": language,
            "content": extracted_code,
            "explanation": str(llm_output.get("explanation", "") or "No explanation provided."),
            "confidence": self._confidence(llm_output, extracted_code),
            "provider": str(llm_output.get("provider", "template")),
        }

    def _detect_language(self, content: str) -> str:
        lowered = content.lower()
        if "#include" in lowered or "std::cout" in lowered:
            return "cpp"
        if "def " in lowered or "print(" in lowered:
            return "python"
        if "function " in lowered or "console.log" in lowered:
            return "javascript"
        return "plain_text"

    def _confidence(self, llm_output: Dict[str, object], content: str) -> float:
        provider = str(llm_output.get("provider", "template"))
        base = 0.78 if provider in {"openai", "local_llm"} else 0.7
        if len(content.splitlines()) >= 3:
            base += 0.08
        if not content.strip():
            base = 0.2
        return round(min(0.99, base), 3)
