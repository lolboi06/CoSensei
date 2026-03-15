from __future__ import annotations

from typing import Dict


class ExecutionAI:
    """AI #2 execution-side role: prepares the selected suggestion for execution."""

    def prepare(self, suggestion: Dict[str, object], autonomy_mode: str, current_code: str) -> Dict[str, object]:
        return {
            **suggestion,
            "execution_ready": autonomy_mode in {"AUTO_EXECUTE", "SUGGEST_ONLY", "REQUIRE_APPROVAL"},
            "current_code": current_code,
            "execution_mode": autonomy_mode,
        }
