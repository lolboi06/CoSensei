from __future__ import annotations

from typing import Dict

from .action_execution_engine import ActionExecutionEngine
from .autonomy_explanation_module import AutonomyExplanationModule
from .cognitive_state_model import CognitiveStateModel
from .conversation_memory_manager import ConversationMemoryManager
from .policy_learning_system import PolicyLearningSystem
from .shared_autonomy_controller import SharedAutonomyController
from .suggestion_engine import SuggestionEngine
from .task_memory_manager import TaskMemoryManager
from .task_understanding_module import TaskUnderstandingModule
from .user_profile_memory_manager import UserProfileMemoryManager


class AdaptiveCopilotPipeline:
    """Coordinates the adaptive copilot stack on top of the existing analyzers."""

    def __init__(
        self,
        conversation_memory: ConversationMemoryManager,
        task_memory: TaskMemoryManager,
        user_profile_memory: UserProfileMemoryManager,
        cognitive_state_model: CognitiveStateModel,
        task_understanding: TaskUnderstandingModule,
        autonomy_controller: SharedAutonomyController,
        explanation_module: AutonomyExplanationModule,
        suggestion_engine: SuggestionEngine,
        action_engine: ActionExecutionEngine,
        policy_learning: PolicyLearningSystem,
    ) -> None:
        self.conversation_memory = conversation_memory
        self.task_memory = task_memory
        self.user_profile_memory = user_profile_memory
        self.cognitive_state_model = cognitive_state_model
        self.task_understanding = task_understanding
        self.autonomy_controller = autonomy_controller
        self.explanation_module = explanation_module
        self.suggestion_engine = suggestion_engine
        self.action_engine = action_engine
        self.policy_learning = policy_learning

    @staticmethod
    def _is_code_suggestion(suggestion: Dict[str, object]) -> bool:
        return str(suggestion.get("type", "")) in {"code", "code_modification"}

    def run(
        self,
        *,
        session_id: str,
        user_id: str,
        current_message: str,
        code_context: Dict[str, object],
        detected_intent: Dict[str, object],
        scores: Dict[str, dict],
        fused_trust: Dict[str, object],
        suggestion_quality: Dict[str, object],
        risk_severity: Dict[str, float],
        user_preferences: Dict[str, object],
        validation: Dict[str, object] | None,
        trust_signals: Dict[str, float],
        trust_trend: str,
    ) -> Dict[str, object]:
        conversation_memory = self.conversation_memory.get_recent_context(session_id, limit=12)
        working_memory = self.task_memory.get(session_id)
        long_term_memory = self.user_profile_memory.get(user_id)

        task_understanding = self.task_understanding.understand(
            memory=conversation_memory,
            current_message=current_message,
            detected_intent=detected_intent,
            working_memory=working_memory,
            long_term_memory=long_term_memory,
            code_context=code_context,
        )
        suggestion = self.suggestion_engine.generate(
            task_understanding=task_understanding,
            memory=conversation_memory,
            task_context=code_context,
            user_preferences=user_preferences,
            working_memory=working_memory,
        )
        shared_autonomy = self.autonomy_controller.decide(
            user_id=user_id,
            fused_trust=fused_trust,
            scores=scores,
            suggestion_quality=suggestion_quality,
            risk_severity=risk_severity,
            user_preferences=user_preferences,
            trust_trend=trust_trend,
            task_understanding=task_understanding,
        )
        autonomy_explanation = self.explanation_module.explain(
            shared_autonomy=shared_autonomy,
            fused_trust=fused_trust,
            scores=scores,
            risk_severity=risk_severity,
        )
        cognitive_state = self.cognitive_state_model.build(
            scores=scores,
            fused_trust=fused_trust,
            risk_severity=risk_severity,
            suggestion_quality=suggestion_quality,
        )
        generated_code = str(suggestion.get("content", "")) if self._is_code_suggestion(suggestion) else ""
        task_memory = self.task_memory.update(
            session_id=session_id,
            active_task=str(task_understanding.get("active_task", "")),
            language=str(suggestion.get("language") or code_context.get("language", "")),
            generated_code=generated_code,
            suggestion=suggestion,
            reasoning_state=str(autonomy_explanation.get("explanation", "")),
            reasoning_trace={
                "task_understanding": task_understanding,
                "autonomy": shared_autonomy,
                "cognitive_state": cognitive_state,
            },
        )
        action_result = self.action_engine.execute(
            session_id=session_id,
            shared_autonomy=shared_autonomy,
            suggestion=suggestion,
            risk_severity=risk_severity,
            explanation=autonomy_explanation,
            task_understanding=task_understanding,
        )
        policy_learning = self.policy_learning.update(
            user_id=user_id,
            session_id=session_id,
            suggestion_quality=suggestion_quality,
            trust_signals=trust_signals,
            trust_score=float(scores["trust_in_ai"]["score"]),
            validation=validation,
            autonomy_mode=str(shared_autonomy.get("autonomy_mode", "SHARED_CONTROL")),
            action_result=action_result,
        )

        return {
            "conversation_memory": self.conversation_memory.get_full_memory_snapshot(session_id),
            "working_memory": task_memory,
            "long_term_memory": long_term_memory,
            "task_understanding": task_understanding,
            "suggestion": suggestion,
            "shared_autonomy": shared_autonomy,
            "shared_autonomy_explanation": autonomy_explanation,
            "cognitive_state": cognitive_state,
            "action_manager": action_result,
            "policy_learning": policy_learning,
        }
