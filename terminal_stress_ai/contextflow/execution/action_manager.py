from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Action:
    type: str
    payload: Dict[str, Any]
    explanation: Optional[str] = None


class ActionManager:
    """Converts autonomy decisions into safe executable actions."""

    BLOCKED_COMMAND_PATTERNS = (
        "rm ",
        "del ",
        "format ",
        "shutdown",
        "reboot",
        "mkfs",
        "rmdir /s",
        "powershell -encodedcommand",
        "curl http",
        "wget http",
    )

    CODE_ACTION_TYPES = {
        "code",
        "code_modification",
        "insert_code_snippet",
        "modify_existing_code",
        "replace_code",
    }

    def __init__(self, log_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_path or (data_dir / "contextflow_action_manager.jsonl")
        self._rollback_stack: List[Dict[str, Any]] = []

    def handle_action(
        self,
        autonomy_decision: str | Dict[str, Any],
        suggestion: Dict[str, Any],
        current_code: str = "",
        risk_level: float = 0.0,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        mode = self._normalize_mode(autonomy_decision)
        user_preferences = user_preferences or {}
        action = self._build_action(suggestion)

        validation_error = self._validate_action(action, risk_level)
        if validation_error:
            result = self._result(
                status="blocked",
                execution_mode=mode,
                human_required=True,
                payload={"error": validation_error, "suggestion": suggestion},
                action=action,
                reason="Safety validation failed.",
            )
            self._log_event("handle_action", result)
            return result

        if mode == "AI_FULL":
            result = self.execute_action(action, current_code=current_code, risk_level=risk_level, execution_mode=mode)
        elif mode == "AI_ASSIST":
            auto_apply = bool(user_preferences.get("auto_apply_low_risk")) and risk_level < 0.35
            result = (
                self.execute_action(action, current_code=current_code, risk_level=risk_level, execution_mode=mode)
                if auto_apply
                else self.suggest_action(action, execution_mode=mode, allow_auto_apply=True)
            )
        elif mode == "SHARED_CONTROL":
            result = self.request_approval(action, execution_mode=mode, risk_level=risk_level)
        elif mode == "HUMAN_CONTROL":
            result = self.suggest_action(action, execution_mode=mode, hint_only=True)
        else:
            result = self.request_approval(action, execution_mode="SHARED_CONTROL", risk_level=risk_level)

        self._log_event("handle_action", result)
        return result

    def execute_action(
        self,
        action: Action,
        current_code: str = "",
        risk_level: float = 0.0,
        execution_mode: str = "AI_FULL",
    ) -> Dict[str, Any]:
        if risk_level >= 0.85:
            result = self.request_approval(action, execution_mode=execution_mode, risk_level=risk_level)
            self._log_event("execute_action", result)
            return result

        rollback_token = self._create_rollback_point(current_code=current_code, action=action)

        try:
            if action.type in self.CODE_ACTION_TYPES:
                updated_code = self.apply_code_change(current_code=current_code, action=action)
                result = self._result(
                    status="executed_automatically",
                    execution_mode=execution_mode,
                    human_required=False,
                    payload={"code": updated_code, "rollback_token": rollback_token},
                    action=action,
                    reason="Action executed successfully.",
                )
            else:
                result = self._result(
                    status="executed_automatically",
                    execution_mode=execution_mode,
                    human_required=False,
                    payload=action.payload,
                    action=action,
                    reason="Non-code action executed successfully.",
                )
        except Exception as exc:
            rollback_result = self.rollback_action(rollback_token)
            result = self._result(
                status="execution_failed",
                execution_mode=execution_mode,
                human_required=True,
                payload={"error": str(exc), "rollback": rollback_result},
                action=action,
                reason="Execution failed and rollback was attempted.",
            )

        self._log_event("execute_action", result)
        return result

    def suggest_action(
        self,
        action: Action,
        execution_mode: str = "AI_ASSIST",
        allow_auto_apply: bool = False,
        hint_only: bool = False,
    ) -> Dict[str, Any]:
        status = "hint_only" if hint_only else "suggestion_displayed"
        payload = dict(action.payload)
        if hint_only:
            payload = {
                "hint": action.explanation or payload.get("explanation") or "Review the suggestion before making a manual change.",
                "suggestion": payload,
            }

        result = self._result(
            status=status,
            execution_mode=execution_mode,
            human_required=not allow_auto_apply or hint_only,
            payload=payload,
            action=action,
            reason="Suggestion prepared for user review." if not hint_only else "Human control mode returns hints only.",
            additional_fields={"auto_apply_available": allow_auto_apply and not hint_only},
        )
        self._log_event("suggest_action", result)
        return result

    def request_approval(
        self,
        action: Action,
        execution_mode: str = "SHARED_CONTROL",
        risk_level: float = 0.0,
    ) -> Dict[str, Any]:
        result = self._result(
            status="approval_required",
            execution_mode=execution_mode,
            human_required=True,
            payload=action.payload,
            action=action,
            reason="Human approval is required before execution.",
            additional_fields={
                "approval_prompt": action.explanation or "Approve this AI-generated action before it is applied.",
                "risk_level": round(float(risk_level), 3),
            },
        )
        self._log_event("request_approval", result)
        return result

    def apply_code_change(self, current_code: str, action: Action) -> str:
        code = str(action.payload.get("code", "")).strip()
        if not code:
            raise ValueError("Code action is missing a code payload.")

        strategy = str(action.payload.get("strategy", "replace"))
        if strategy == "append":
            if not current_code:
                return code
            return f"{current_code.rstrip()}\n\n{code}"
        if strategy == "prepend":
            if not current_code:
                return code
            return f"{code}\n\n{current_code.lstrip()}"
        return code

    def rollback_action(self, rollback_token: Optional[str] = None) -> Dict[str, Any]:
        if not self._rollback_stack:
            result = {"rolled_back": False, "reason": "No rollback state available."}
            self._log_event("rollback_action", {"action_manager": result})
            return result

        if rollback_token:
            for index in range(len(self._rollback_stack) - 1, -1, -1):
                item = self._rollback_stack[index]
                if item["token"] == rollback_token:
                    state = self._rollback_stack.pop(index)
                    result = {
                        "rolled_back": True,
                        "rollback_token": state["token"],
                        "restored_code": state["current_code"],
                    }
                    self._log_event("rollback_action", {"action_manager": result})
                    return result

            result = {"rolled_back": False, "reason": "Rollback token not found."}
            self._log_event("rollback_action", {"action_manager": result})
            return result

        state = self._rollback_stack.pop()
        result = {
            "rolled_back": True,
            "rollback_token": state["token"],
            "restored_code": state["current_code"],
        }
        self._log_event("rollback_action", {"action_manager": result})
        return result

    def _build_action(self, suggestion: Dict[str, Any]) -> Action:
        suggestion_type = str(suggestion.get("type", "code"))
        explanation = suggestion.get("explanation")
        content = suggestion.get("content")
        language = suggestion.get("language")

        action_type = {
            "code": "insert_code_snippet",
            "code_modification": "modify_existing_code",
            "debug_strategy": "display_debug_strategy",
            "explanation": "display_explanation",
        }.get(suggestion_type, suggestion_type)

        payload: Dict[str, Any] = dict(suggestion.get("payload", {}))
        if content is not None and "code" not in payload:
            payload["code"] = content
        if language and "language" not in payload:
            payload["language"] = language
        if explanation and "explanation" not in payload:
            payload["explanation"] = explanation
        return Action(type=action_type, payload=payload, explanation=explanation)

    def _validate_action(self, action: Action, risk_level: float) -> Optional[str]:
        if risk_level < 0.0 or risk_level > 1.0:
            return "Risk level must be between 0.0 and 1.0."
        if action.type in self.CODE_ACTION_TYPES and not str(action.payload.get("code", "")).strip():
            return "Code action payload is empty."

        serialized_payload = json.dumps(action.payload, ensure_ascii=True).lower()
        if any(pattern in serialized_payload for pattern in self.BLOCKED_COMMAND_PATTERNS):
            return "Dangerous command pattern detected in payload."

        return None

    def _create_rollback_point(self, current_code: str, action: Action) -> str:
        token = f"rollback-{len(self._rollback_stack) + 1}-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self._rollback_stack.append(
            {
                "token": token,
                "current_code": current_code,
                "action_type": action.type,
            }
        )
        return token

    @staticmethod
    def _normalize_mode(autonomy_decision: str | Dict[str, Any]) -> str:
        if isinstance(autonomy_decision, dict):
            return str(autonomy_decision.get("autonomy_mode") or autonomy_decision.get("mode") or "SHARED_CONTROL")
        return str(autonomy_decision or "SHARED_CONTROL")

    def _result(
        self,
        *,
        status: str,
        execution_mode: str,
        human_required: bool,
        payload: Dict[str, Any],
        action: Action,
        reason: str,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = {
            "action_manager": {
                "status": status,
                "execution_mode": execution_mode,
                "human_required": human_required,
                "payload": payload,
                "action": {
                    "type": action.type,
                    "payload": action.payload,
                    "explanation": action.explanation,
                },
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_bus_topic": "contextflow.action_manager",
            }
        }
        if additional_fields:
            result["action_manager"].update(additional_fields)
        return result

    def _log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        entry = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
