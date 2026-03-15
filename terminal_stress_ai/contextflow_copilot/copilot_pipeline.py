from __future__ import annotations

from typing import Dict, List, Optional

from .contextflow_controller import ContextFlowController


class CopilotPipeline:
    """Public wrapper for the reusable ContextFlow copilot frontend."""

    def __init__(self, controller: Optional[ContextFlowController] = None) -> None:
        self.controller = controller or ContextFlowController()

    def process_input(
        self,
        user_input: str,
        *,
        session_id: str = "default-session",
        user_id: str = "default-user",
        memory: Optional[Dict[str, object]] = None,
        behavioral_signals: Optional[List[dict]] = None,
        clarification_state: Optional[Dict[str, str]] = None,
        user_settings: Optional[Dict[str, object]] = None,
        feedback: Optional[str] = None,
    ) -> Dict[str, object]:
        return self.controller.process(
            user_input,
            session_id=session_id,
            user_id=user_id,
            memory=memory,
            behavioral_signals=behavioral_signals,
            clarification_state=clarification_state,
            user_settings=user_settings,
            feedback=feedback,
        )

    def refine_until_satisfied(
        self,
        user_input: str,
        *,
        session_id: str = "default-session",
        user_id: str = "default-user",
        memory: Optional[Dict[str, object]] = None,
        behavioral_signals: Optional[List[dict]] = None,
        clarification_state: Optional[Dict[str, str]] = None,
        user_settings: Optional[Dict[str, object]] = None,
        feedback_sequence: Optional[List[str]] = None,
        max_rounds: int = 3,
    ) -> Dict[str, object]:
        feedback_sequence = list(feedback_sequence or [])
        result: Dict[str, object] = {}
        for round_index in range(max_rounds):
            feedback = feedback_sequence[round_index] if round_index < len(feedback_sequence) else None
            result = self.process_input(
                user_input,
                session_id=session_id,
                user_id=user_id,
                memory=memory,
                behavioral_signals=behavioral_signals,
                clarification_state=clarification_state,
                user_settings=user_settings,
                feedback=feedback,
            )
            if result.get("clarification_required"):
                return result
            if not feedback or feedback.lower() in {"satisfied", "accepted", "done"}:
                return result
            memory = dict(memory or {})
            memory.setdefault("feedback_history", []).append(feedback)
        return result
