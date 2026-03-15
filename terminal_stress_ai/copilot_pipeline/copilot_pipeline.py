from __future__ import annotations

from typing import Any, Dict, List, Optional

from .contextflow_controller import ContextFlowController


class CopilotPipeline:
    """Public wrapper for reusable Copilot-style suggestion processing."""

    def __init__(self, controller: Optional[ContextFlowController] = None) -> None:
        self.controller = controller or ContextFlowController()

    def process_input(
        self,
        user_input: str,
        *,
        session_id: str = "default-session",
        user_id: str = "default-user",
        memory: Optional[Dict[str, object]] = None,
        behavioral_signals: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, object]:
        return self.controller.process(
            user_input,
            session_id=session_id,
            user_id=user_id,
            memory=memory,
            behavioral_signals=behavioral_signals,
        )
