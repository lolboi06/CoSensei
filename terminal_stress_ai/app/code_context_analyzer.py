from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional


class CodeContextAnalyzer:
    def analyze(self, events: List[dict], file_path: str | None = None) -> Dict[str, object]:
        line_events = [e for e in events if e.get("key") == "Enter" and e.get("line_text") is not None]
        recent_lines = [str(e.get("line_text", "")) for e in line_events[-10:]]
        recent_text = "\n".join(line for line in recent_lines if line.strip())
        language = self._detect_language(file_path, recent_lines)
        syntax_errors = self._syntax_errors(language, recent_text)
        function_length = self._function_length(language, recent_lines)
        recent_edits = sum(1 for e in line_events[-10:] if int(e.get("backspace_count", 0)) > 0)
        return {
            "language": language,
            "file_type": self._file_type(file_path, language),
            "function_length": function_length,
            "syntax_errors": syntax_errors,
            "compilation_failures": 1 if syntax_errors > 0 else 0,
            "recent_edits": recent_edits,
        }

    def _detect_language(self, file_path: str | None, lines: List[str]) -> str:
        if file_path:
            suffix = Path(file_path).suffix.lower()
            mapping = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".jsx": "javascript",
                ".java": "java",
                ".go": "go",
                ".rs": "rust",
                ".cpp": "cpp",
                ".c": "c",
                ".cs": "csharp",
            }
            if suffix in mapping:
                return mapping[suffix]

        joined = "\n".join(lines).lower()
        if "c++" in joined or "cpp" in joined or "#include" in joined or "std::cout" in joined:
            return "cpp"
        if "hello world" in joined and (" c " in f" {joined} " or "language c" in joined):
            return "c"
        if "def " in joined or "import " in joined or "print(" in joined:
            return "python"
        if "function " in joined or "console.log" in joined or "=>" in joined:
            return "javascript"
        if "public class" in joined or "system.out.println" in joined:
            return "java"
        if "fn " in joined or "println!" in joined:
            return "rust"
        return "plain_text"

    def _file_type(self, file_path: str | None, language: str) -> str:
        if file_path:
            return Path(file_path).suffix.lstrip(".") or language
        return language

    def _syntax_errors(self, language: str, text: str) -> int:
        if not text.strip():
            return 0
        if language == "python":
            try:
                ast.parse(text)
                return 0
            except SyntaxError:
                return 1
        # Lightweight delimiter balance check for non-Python snippets.
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack: list[str] = []
        for ch in text:
            if ch in pairs:
                stack.append(ch)
            elif ch in pairs.values():
                if not stack:
                    return 1
                opening = stack.pop()
                if pairs[opening] != ch:
                    return 1
        return 1 if stack else 0

    def _function_length(self, language: str, lines: List[str]) -> int:
        if not lines:
            return 0
        if language == "python":
            for idx, line in enumerate(lines):
                if line.strip().startswith("def "):
                    indent = len(line) - len(line.lstrip(" "))
                    length = 1
                    for follow in lines[idx + 1 :]:
                        stripped = follow.strip()
                        if not stripped:
                            length += 1
                            continue
                        current_indent = len(follow) - len(follow.lstrip(" "))
                        if current_indent <= indent and not follow.lstrip().startswith("#"):
                            break
                        length += 1
                    return length
        return len([line for line in lines if line.strip()])
