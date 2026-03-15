from __future__ import annotations

from typing import Any, Dict, List, Optional

from contextflow import ContextFlowController as MiddlewareController

from .context_builder import ContextBuilder
from .llm_suggestion_engine import LLMSuggestionEngine
from .suggestion_postprocessor import SuggestionPostProcessor
from .task_input_router import TaskInputRouter


class ContextFlowController:
    """Frontend copilot controller that feeds structured suggestions into ContextFlow."""

    def __init__(
        self,
        *,
        task_router: Optional[TaskInputRouter] = None,
        context_builder: Optional[ContextBuilder] = None,
        llm_engine: Optional[LLMSuggestionEngine] = None,
        postprocessor: Optional[SuggestionPostProcessor] = None,
        contextflow: Optional[MiddlewareController] = None,
    ) -> None:
        self.task_router = task_router or TaskInputRouter()
        self.context_builder = context_builder or ContextBuilder()
        self.llm_engine = llm_engine or LLMSuggestionEngine()
        self.postprocessor = postprocessor or SuggestionPostProcessor()
        self.contextflow = contextflow or MiddlewareController()

    def process(
        self,
        user_input: str,
        *,
        session_id: str = "default-session",
        user_id: str = "default-user",
        memory: Optional[Dict[str, object]] = None,
        behavioral_signals: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, object]:
        task = self.task_router.parse_input(user_input)
        context = self.context_builder.build_context(task, memory)
        raw_suggestion = self.llm_engine.generate_suggestion(context)
        structured = self.postprocessor.process(raw_suggestion)
        middleware_input = {
            "type": structured["suggestion_type"],
            "language": structured["language"],
            "content": structured["content"],
            "explanation": structured["explanation"],
            "confidence": structured["confidence"],
            "safe_to_execute": structured["safe_to_execute"],
            "provider": structured["provider"],
        }
        result = self.contextflow.handle_task_input(
            session_id=session_id,
            user_id=user_id,
            task_input=user_input,
            current_code=str((memory or {}).get("working_code", "")),
            behavioral_signals=behavioral_signals or self._default_behavioral_signals(user_input),
            llm_suggestion=middleware_input,
        )
        return {
            "task": task,
            "context": context,
            "suggestion": middleware_input,
            "autonomy_mode": result["shared_autonomy"]["autonomy_mode"],
            "action_manager": result["action_manager"],
            "contextflow": result,
        }

    @staticmethod
    def _default_behavioral_signals(user_input: str) -> List[Dict[str, Any]]:
        return [
            {"event_type": "keydown", "key": "a", "gap_ms": 120},
            {"event_type": "keydown", "key": "Enter", "gap_ms": 180, "line_text": user_input, "suggestion_action": "none"},
        ]
