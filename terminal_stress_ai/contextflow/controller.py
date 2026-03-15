from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from app.autonomy_decision_engine import AutonomyDecisionEngine
from app.autonomy_explanation_module import AutonomyExplanationModule
from app.behavior_trust_bridge import BehaviorTrustBridge
from app.cognitive_state_model import CognitiveStateModel
from app.features import extract_features
from app.model import StateModel
from app.risk_analyzer import RiskAnalyzer
from app.shared_autonomy_controller import SharedAutonomyController
from app.suggestion_engine import SuggestionEngine
from app.task_understanding_module import TaskUnderstandingModule
from app.trust_fusion_module import TrustFusionModule
from app.user_preference_engine import UserPreferenceEngine

from .execution.action_manager import ActionManager


@dataclass
class ControllerModules:
    state_model: StateModel
    behavior_bridge: BehaviorTrustBridge
    risk_analyzer: RiskAnalyzer
    preference_engine: UserPreferenceEngine
    trust_fusion: TrustFusionModule
    autonomy_engine: AutonomyDecisionEngine
    shared_autonomy_controller: SharedAutonomyController
    cognitive_state_model: CognitiveStateModel
    task_understanding_module: TaskUnderstandingModule
    autonomy_explainer: AutonomyExplanationModule
    suggestion_engine: SuggestionEngine
    action_manager: ActionManager


class ContextFlowController:
    """Middleware controller that evaluates an LLM suggestion before execution."""

    def __init__(self, modules: Optional[ControllerModules] = None) -> None:
        self.modules = modules or ControllerModules(
            state_model=StateModel(),
            behavior_bridge=BehaviorTrustBridge(),
            risk_analyzer=RiskAnalyzer(),
            preference_engine=UserPreferenceEngine(),
            trust_fusion=TrustFusionModule(),
            autonomy_engine=AutonomyDecisionEngine(),
            shared_autonomy_controller=SharedAutonomyController(),
            cognitive_state_model=CognitiveStateModel(),
            task_understanding_module=TaskUnderstandingModule(),
            autonomy_explainer=AutonomyExplanationModule(),
            suggestion_engine=SuggestionEngine(),
            action_manager=ActionManager(),
        )

    def handle_task_input(
        self,
        *,
        session_id: str,
        user_id: str,
        task_input: str,
        current_code: str,
        behavioral_signals: List[Dict[str, Any]],
        llm_suggestion_engine: Optional[Callable[[str, str], Dict[str, Any]]] = None,
        llm_suggestion: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        suggestion = llm_suggestion or self._generate_llm_suggestion(
            task_input=task_input,
            current_code=current_code,
            llm_suggestion_engine=llm_suggestion_engine,
        )
        result = self.process(
            session_id=session_id,
            user_id=user_id,
            llm_suggestion=suggestion,
            current_code=current_code,
            behavioral_signals=behavioral_signals,
            task_input=task_input,
        )
        result["task_input"] = task_input
        return result

    def evaluate_suggestion(
        self,
        *,
        session_id: str,
        user_id: str,
        llm_suggestion: Dict[str, Any],
        current_code: str,
        behavioral_signals: List[Dict[str, Any]],
        task_input: str = "",
    ) -> Dict[str, Any]:
        feature_vector = extract_features(behavioral_signals)
        scores = self.modules.state_model.predict(feature_vector)
        trust_analysis = self.modules.behavior_bridge.analyze(behavioral_signals, feature_vector.values)
        fused_trust = self.modules.trust_fusion.fuse(scores["trust_in_ai"], trust_analysis["trust"])

        quality = self._quality_score(len(behavioral_signals))
        risk_analysis = self.modules.risk_analyzer.analyze(
            scores=scores,
            features=feature_vector.values,
            quality=quality,
            trust_engine_score=float(trust_analysis["trust"]["trust_score"]),
        )
        preference_data = self.modules.preference_engine.update_user_profile(
            user_id=user_id,
            session_id=session_id,
            features=feature_vector.values,
            trust_signals=trust_analysis["signals"],
            scores=scores,
        )
        task_understanding = self.modules.task_understanding_module.understand(
            memory={
                "conversation_history": [{"role": "user", "content": task_input}],
                "code_memory": {
                    "language": llm_suggestion.get("language", "plain_text"),
                    "last_generated_code": current_code,
                },
                "task_context": {},
            },
            current_message=task_input,
            detected_intent={"task": "writing_new_code"},
            working_memory={
                "active_task": "",
                "generated_code": current_code,
                "language": llm_suggestion.get("language", "plain_text"),
            },
            long_term_memory={"user_preferences": preference_data["user_preferences"]},
            code_context=self._code_context(llm_suggestion, current_code),
        )
        suggestion_quality = self._suggestion_quality(llm_suggestion)
        autonomy_decision = self.modules.autonomy_engine.decide(
            user_id=user_id,
            scores=scores,
            risk_severity=risk_analysis["risk_severity_scores"],
            trust_signals=trust_analysis["signals"],
            user_preferences=preference_data["user_preferences"],
            code_context=self._code_context(llm_suggestion, current_code),
            suggestion_quality=suggestion_quality,
            trust_trend="stable",
            fused_trust=fused_trust,
        )
        mapped_mode = self._map_autonomy_mode(autonomy_decision.get("mode", "suggest_only"))
        shared_autonomy = self.modules.shared_autonomy_controller.decide(
            user_id=user_id,
            fused_trust=fused_trust,
            scores=scores,
            suggestion_quality=suggestion_quality,
            risk_severity=risk_analysis["risk_severity_scores"],
            user_preferences=preference_data["user_preferences"],
            trust_trend="stable",
            task_understanding=task_understanding,
        )
        cognitive_state = self.modules.cognitive_state_model.build(
            scores=scores,
            fused_trust=fused_trust,
            risk_severity=risk_analysis["risk_severity_scores"],
            suggestion_quality=suggestion_quality,
        )
        autonomy_explanation = self.modules.autonomy_explainer.explain(
            shared_autonomy=shared_autonomy,
            fused_trust=fused_trust,
            scores=scores,
            risk_severity=risk_analysis["risk_severity_scores"],
        )

        return {
            "task_input": task_input,
            "llm_suggestion": llm_suggestion,
            "current_code": current_code,
            "behavior_features": feature_vector.values,
            "scores": scores,
            "trust_engine": trust_analysis["trust"],
            "trust_signals": trust_analysis["signals"],
            "fused_trust": fused_trust,
            "risk_analysis": risk_analysis,
            "user_preferences": preference_data["user_preferences"],
            "user_profile": preference_data["profile"],
            "task_understanding": task_understanding,
            "suggestion_quality": suggestion_quality,
            "cognitive_state": cognitive_state,
            "autonomy_decision": {
                **autonomy_decision,
                "autonomy_mode": mapped_mode,
            },
            "shared_autonomy": shared_autonomy,
            "shared_autonomy_explanation": autonomy_explanation,
        }

    def process(
        self,
        *,
        session_id: str,
        user_id: str,
        llm_suggestion: Dict[str, Any],
        current_code: str,
        behavioral_signals: List[Dict[str, Any]],
        task_input: str = "",
    ) -> Dict[str, Any]:
        evaluation = self.evaluate_suggestion(
            session_id=session_id,
            user_id=user_id,
            llm_suggestion=llm_suggestion,
            current_code=current_code,
            behavioral_signals=behavioral_signals,
            task_input=task_input,
        )
        autonomy = evaluation["shared_autonomy"]
        risk_level = max(float(v) for v in evaluation["risk_analysis"]["risk_severity_scores"].values())
        action_result = self.modules.action_manager.handle_action(
            autonomy_decision={"autonomy_mode": autonomy["autonomy_mode"]},
            suggestion=llm_suggestion,
            current_code=current_code,
            risk_level=risk_level,
            user_preferences=evaluation["user_preferences"],
        )
        return {
            **evaluation,
            "action_manager": action_result["action_manager"],
        }

    def _generate_llm_suggestion(
        self,
        *,
        task_input: str,
        current_code: str,
        llm_suggestion_engine: Optional[Callable[[str, str], Dict[str, Any]]],
    ) -> Dict[str, Any]:
        if llm_suggestion_engine is not None:
            return llm_suggestion_engine(task_input, current_code)
        return self.modules.suggestion_engine.generate(
            task_understanding={
                "active_task": "editing_previous_code" if current_code.strip() else "writing_new_code",
                "retrieved_code": current_code,
                "language": "python",
            },
            memory={
                "conversation_history": [{"role": "user", "content": task_input}],
                "code_memory": {"language": "python", "last_generated_code": current_code},
                "task_context": {},
            },
            task_context={"language": "python"},
            user_preferences={},
            working_memory={"generated_code": current_code, "language": "python"},
        )

    @staticmethod
    def _map_autonomy_mode(mode: str) -> str:
        mapping = {
            "auto_execute": "AI_FULL",
            "suggest_only": "AI_ASSIST",
            "require_confirmation": "SHARED_CONTROL",
            "approval_required": "HUMAN_CONTROL",
        }
        return mapping.get(str(mode), "SHARED_CONTROL")

    @staticmethod
    def _quality_score(event_count: int) -> float:
        return round(min(1.0, max(1, event_count) / 80.0), 3)

    @staticmethod
    def _code_context(llm_suggestion: Dict[str, Any], current_code: str) -> Dict[str, Any]:
        suggestion_code = str(llm_suggestion.get("content", "") or "")
        language = str(llm_suggestion.get("language", "") or "plain_text")
        code_blob = suggestion_code or current_code
        function_length = len([line for line in code_blob.splitlines() if line.strip()])
        syntax_errors = 1 if (language in {"python", "cpp", "c", "javascript"} and not code_blob.strip()) else 0
        return {
            "language": language,
            "file_type": language,
            "function_length": function_length,
            "syntax_errors": syntax_errors,
            "compilation_failures": syntax_errors,
            "recent_edits": 1 if current_code and suggestion_code and current_code != suggestion_code else 0,
        }

    @staticmethod
    def _suggestion_quality(llm_suggestion: Dict[str, Any]) -> Dict[str, Any]:
        content = str(llm_suggestion.get("content", "") or "")
        suggestion_type = str(llm_suggestion.get("type", "code"))
        quality = 0.6
        if not content.strip():
            quality = 0.2
        elif suggestion_type in {"code", "code_modification"} and len(content.splitlines()) >= 3:
            quality = 0.75
        return {
            "suggestions_shown": 1,
            "suggestions_accepted": 0,
            "suggestions_modified": 0,
            "suggestions_rejected": 0,
            "suggestion_quality_score": quality,
        }
