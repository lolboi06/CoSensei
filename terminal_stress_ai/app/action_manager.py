from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


class ActionManager:
    """Applies autonomy decisions to assistant actions with guardrails."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.log_path = log_path or (root / "data" / "action_manager.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _command_is_unsafe(command: str) -> bool:
        lowered = command.lower().strip()
        blocked = [
            "rm ",
            "del ",
            "format ",
            "shutdown",
            "reboot",
            "mkfs",
            "rmdir /s",
            "powershell -encodedcommand",
        ]
        return any(token in lowered for token in blocked)

    def _log(self, payload: Dict[str, object]) -> None:
        line = json.dumps(payload, ensure_ascii=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def manage(
        self,
        autonomy_decision: Dict[str, object],
        proposed_action: str = "display_suggestion",
        command_preview: str = "",
    ) -> Dict[str, object]:
        mode = str(autonomy_decision.get("autonomy_mode", autonomy_decision.get("mode", "SHARED_CONTROL")))
        unsafe = self._command_is_unsafe(command_preview) if command_preview else False
        timestamp = datetime.now(timezone.utc).isoformat()

        if unsafe:
            result = {
                "status": "blocked_unsafe_action",
                "action": proposed_action,
                "execution_mode": "blocked",
                "mode": mode,
                "undo_available": False,
                "rollback_supported": True,
                "human_in_loop": True,
                "human_required": True,
                "reason": "Unsafe command pattern detected; action blocked.",
            }
        elif mode == "AI_FULL":
            result = {
                "status": "executed_automatically",
                "action": proposed_action,
                "execution_mode": "AI_FULL",
                "mode": mode,
                "undo_available": True,
                "rollback_supported": True,
                "human_in_loop": False,
                "human_required": False,
                "reason": "Shared autonomy level allows safe automatic execution.",
            }
        elif mode == "AI_ASSIST":
            result = {
                "status": "suggestion_displayed",
                "action": proposed_action,
                "execution_mode": "AI_ASSIST",
                "mode": mode,
                "undo_available": True,
                "rollback_supported": True,
                "human_in_loop": True,
                "human_required": False,
                "reason": "AI assist mode shows or auto-completes low-risk suggestions.",
            }
        elif mode == "HUMAN_CONTROL":
            result = {
                "status": "human_control_only",
                "action": proposed_action,
                "execution_mode": "HUMAN_CONTROL",
                "mode": mode,
                "undo_available": False,
                "rollback_supported": True,
                "human_in_loop": True,
                "human_required": True,
                "reason": "Human control mode disables automation and provides only minimal hints.",
            }
        else:
            result = {
                "status": "suggestion_displayed",
                "action": proposed_action,
                "execution_mode": "SHARED_CONTROL",
                "mode": mode,
                "undo_available": False,
                "rollback_supported": True,
                "human_in_loop": True,
                "human_required": True,
                "reason": "Shared control mode shows a suggestion, explanation, and waits for user approval.",
            }

        self._log(
            {
                "timestamp": timestamp,
                "autonomy_decision": autonomy_decision,
                "action_manager": result,
                "command_preview": command_preview,
            }
        )
        return result
