from __future__ import annotations

from typing import Dict
from app.solution_strategy_generator import SolutionStrategyGenerator


class SuggestionGenerator:
    def generate(
        self,
        user_intent: Dict[str, object],
        memory: Dict[str, object],
        task_context: Dict[str, object],
        user_preferences: Dict[str, object],
        task_understanding: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        history = memory.get("conversation_history", [])
        last_user = ""
        for item in reversed(history):
            if item.get("role") == "user":
                last_user = str(item.get("content", ""))
                break

        language = self._detect_language(last_user, task_context, memory)
        last_code = str((task_understanding or {}).get("retrieved_code", "") or memory.get("code_memory", {}).get("last_generated_code", ""))
        task = str(user_intent.get("task", "writing_new_code"))
        concise = str(user_preferences.get("preferred_ai_behavior", "")) == "concise_suggestions"

        if ((task_understanding or {}).get("active_task") == "asking_for_explanation") and last_code:
            code = last_code
            explanation = "This explanation focuses on the current code in working memory so the conversation stays continuous."
        elif ((task_understanding or {}).get("active_task") in {"editing_previous_code", "refactoring_code"}) and last_code:
            code = self._rewrite_with_function(last_code, language)
            explanation = "This revision updates the existing code instead of starting over, preserving task continuity."
        elif "modify" in last_user.lower() and "function" in last_user.lower() and last_code:
            code = self._rewrite_with_function(last_code, language)
            explanation = "This version extracts the earlier logic into a function so the code is easier to reuse."
        elif task == "debugging":
            code = self._debug_template(language)
            explanation = "This suggestion adds a simple, testable structure so you can isolate the failing path quickly."
        elif task == "exploring_api":
            code = self._api_template(language)
            explanation = "This suggestion shows a small usage example so you can explore the API with minimal setup."
        else:
            code = self._coding_template(language, last_user)
            explanation = "This suggestion gives you a minimal working implementation that matches the detected task."

        if concise:
            explanation = explanation.split(".")[0] + "."

        return {
            "language": language,
            "code": code,
            "explanation": explanation,
            "source": "template",
        }

    def _detect_language(self, prompt: str, task_context: Dict[str, object], memory: Dict[str, object]) -> str:
        prompt_l = prompt.lower()
        if "c++" in prompt_l or "cpp" in prompt_l:
            return "cpp"
        if "python" in prompt_l:
            return "python"
        if "javascript" in prompt_l or "node" in prompt_l:
            return "javascript"
        code_lang = str(memory.get("code_memory", {}).get("language", "")).strip()
        if code_lang:
            return code_lang
        context_lang = str(task_context.get("language", "")).strip()
        return context_lang or "python"

    def _coding_template(self, language: str, prompt: str) -> str:
        prompt_l = prompt.lower()
        if language == "cpp" and "hello world" in prompt_l:
            return "\n".join(
                [
                    "#include <iostream>",
                    "",
                    "int main() {",
                    '    std::cout << "Hello, World!" << std::endl;',
                    "    return 0;",
                    "}",
                ]
            )
        if language == "cpp" and "add" in prompt.lower():
            return "\n".join(
                [
                    "#include <iostream>",
                    "",
                    "int add(int a, int b) {",
                    "    return a + b;",
                    "}",
                    "",
                    "int main() {",
                    "    int a = 0, b = 0;",
                    '    std::cout << "Enter two integers: ";',
                    "    std::cin >> a >> b;",
                    '    std::cout << "Sum: " << add(a, b) << std::endl;',
                    "    return 0;",
                    "}",
                ]
            )
        if language == "cpp":
            return "\n".join(
                [
                    "#include <iostream>",
                    "",
                    "int main() {",
                    '    std::cout << "Hello from ContextFlow!" << std::endl;',
                    "    return 0;",
                    "}",
                ]
            )
        if language == "javascript":
            return "\n".join(
                [
                    "function main() {",
                    "  const values = [1, 2];",
                    "  const total = values.reduce((sum, value) => sum + value, 0);",
                    "  console.log(`Sum: ${total}`);",
                    "}",
                    "",
                    "main();",
                ]
            )
        return "\n".join(
            [
                "def add(a: int, b: int) -> int:",
                "    return a + b",
                "",
                "def main() -> None:",
                "    a = int(input('Enter first integer: '))",
                "    b = int(input('Enter second integer: '))",
                "    print(f'Sum: {add(a, b)}')",
                "",
                "if __name__ == '__main__':",
                "    main()",
            ]
        )

    def _rewrite_with_function(self, last_code: str, language: str) -> str:
        if language == "cpp":
            if "int add(" in last_code:
                return last_code
            return self._coding_template("cpp", "add with function")
        if language == "python":
            if "def add(" in last_code:
                return last_code
            return self._coding_template("python", "add with function")
        return last_code

    def _debug_template(self, language: str) -> str:
        if language == "cpp":
            return "\n".join(
                [
                    "#include <cassert>",
                    "#include <iostream>",
                    "",
                    "int add(int a, int b) { return a + b; }",
                    "",
                    "int main() {",
                    "    assert(add(2, 3) == 5);",
                    '    std::cout << "Basic test passed." << std::endl;',
                    "    return 0;",
                    "}",
                ]
            )
        return "\n".join(
            [
                "def add(a: int, b: int) -> int:",
                "    return a + b",
                "",
                "def test_add() -> None:",
                "    assert add(2, 3) == 5",
                "",
                "if __name__ == '__main__':",
                "    test_add()",
                "    print('Basic test passed.')",
            ]
        )

    def _api_template(self, language: str) -> str:
        if language == "javascript":
            return "\n".join(
                [
                    "async function fetchExample() {",
                    "  const response = await fetch('https://api.example.com/items');",
                    "  const data = await response.json();",
                    "  console.log(data);",
                    "}",
                    "",
                    "fetchExample();",
                ]
            )
        return "\n".join(
            [
                "import requests",
                "",
                "def fetch_items() -> None:",
                "    response = requests.get('https://api.example.com/items', timeout=10)",
                "    response.raise_for_status()",
                "    print(response.json())",
                "",
                "if __name__ == '__main__':",
                "    fetch_items()",
            ]
        )
