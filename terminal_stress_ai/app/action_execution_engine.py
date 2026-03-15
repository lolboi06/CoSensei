from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from .action_manager import ActionManager


class ActionExecutionEngine:
    def __init__(self, log_path: Path | None = None) -> None:
        self.manager = ActionManager()
        root = Path(__file__).resolve().parent.parent
        self.log_path = log_path or (root / "data" / "action_execution_log.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.undo_stack: dict[str, list[dict]] = {}

    @staticmethod
    def _risk_level(risk_severity: Dict[str, float]) -> float:
        return max((float(v) for v in risk_severity.values()), default=0.0)

    def _log(self, payload: Dict[str, object]) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    def execute(
        self,
        session_id: str,
        shared_autonomy: Dict[str, object],
        suggestion: Dict[str, object],
        risk_severity: Dict[str, float] | None = None,
        explanation: Dict[str, object] | None = None,
        task_understanding: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        mode = str(shared_autonomy.get("autonomy_mode", "SHARED_CONTROL"))
        risk_severity = risk_severity or {}
        action = {
            "code": "insert_code_snippet",
            "code_modification": "modify_existing_code",
            "debug_strategy": "show_debug_strategy",
            "explanation": "show_explanation",
            "response": "show_response",
        }.get(str(suggestion.get("type", "code")), "display_suggestion")
        manager_result = self.manager.manage(
            autonomy_decision={"autonomy_mode": mode},
            proposed_action=action,
            command_preview=str(suggestion.get("content", ""))[:200],
        )
        risk_level = self._risk_level(risk_severity)
        confirmation_required = bool(
            manager_result.get("human_required")
            or risk_level >= 0.6
            or str(suggestion.get("type", "")) == "code_modification"
        )
        execution_result = {
            **manager_result,
            "session_id": session_id,
            "confirmation_required": confirmation_required,
            "risk_level": round(risk_level, 3),
            "explanation": explanation or {},
            "task_understanding": task_understanding or {},
            "audit_logged": True,
        }
        if manager_result.get("status") == "executed_automatically":
            self.undo_stack.setdefault(session_id, []).append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": action,
                    "content": suggestion.get("content", ""),
                }
            )
            execution_result["undo_token"] = f"{session_id}:{len(self.undo_stack[session_id])}"
        self._log(execution_result)
        return execution_result

    def rollback(self, session_id: str) -> Dict[str, object]:
        stack = self.undo_stack.get(session_id, [])
        if not stack:
            result = {"session_id": session_id, "rolled_back": False, "reason": "No executed actions available to undo."}
            self._log(result)
            return result
        previous = stack.pop()
        result = {
            "session_id": session_id,
            "rolled_back": True,
            "restored_action": previous.get("action"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._log(result)
        return result
