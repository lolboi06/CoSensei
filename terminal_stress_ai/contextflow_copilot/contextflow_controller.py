from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from app.autonomy_decision_engine import AutonomyDecisionEngine
from app.autonomy_explanation_module import AutonomyExplanationModule
from app.behavior_trust_bridge import BehaviorTrustBridge
from app.cognitive_state_model import CognitiveStateModel
from app.features import extract_features
from app.model import StateModel
from app.risk_analyzer import RiskAnalyzer
from app.shared_autonomy_controller import SharedAutonomyController
from app.trust_fusion_module import TrustFusionModule
from app.user_preference_engine import UserPreferenceEngine
from contextflow.execution.action_manager import ActionManager

from .context_builder import ContextBuilder
from .clarification_engine import ClarificationEngine
from .execution_ai import ExecutionAI
from .llm_suggestion_engine import LLMSuggestionEngine
from .planner_ai import PlannerAI
from .solution_generator_ai import SolutionGeneratorAI
from .suggestion_normalizer import SuggestionNormalizer
from .suggestion_quality import SuggestionQualityEvaluator
from .solution_verification import SolutionVerificationEngine
from .task_input_router import TaskInputRouter
from .task_understanding import TaskUnderstandingEngine
from .user_control import UserControlLayer


@dataclass
class ContextFlowMiddlewareAdapter:
    state_model: StateModel
    behavior_bridge: BehaviorTrustBridge
    risk_analyzer: RiskAnalyzer
    preference_engine: UserPreferenceEngine
    trust_fusion: TrustFusionModule
    autonomy_engine: AutonomyDecisionEngine
    shared_autonomy_controller: SharedAutonomyController
    autonomy_explainer: AutonomyExplanationModule
    cognitive_state_model: CognitiveStateModel
    action_manager: ActionManager

    def analyze_interaction(
        self,
        user_input: str,
        *,
        user_id: str,
        session_id: str,
        behavioral_signals: List[dict],
        suggestion: Dict[str, object],
        current_code: str,
    ) -> Dict[str, object]:
        feature_vector = extract_features(behavioral_signals)
        scores = self.state_model.predict(feature_vector)
        trust_analysis = self.behavior_bridge.analyze(behavioral_signals, feature_vector.values)
        fused_trust = self.trust_fusion.fuse(scores["trust_in_ai"], trust_analysis["trust"])
        quality = round(min(1.0, max(1, len(behavioral_signals)) / 80.0), 3)
        risk_analysis = self.risk_analyzer.analyze(
            scores=scores,
            features=feature_vector.values,
            quality=quality,
            trust_engine_score=float(trust_analysis["trust"]["trust_score"]),
        )
        preference_data = self.preference_engine.update_user_profile(
            user_id=user_id,
            session_id=session_id,
            features=feature_vector.values,
            trust_signals=trust_analysis["signals"],
            scores=scores,
        )
        return {
            "user_input": user_input,
            "session_id": session_id,
            "user_id": user_id,
            "behavior_features": feature_vector.values,
            "scores": scores,
            "trust_engine": trust_analysis["trust"],
            "trust_signals": trust_analysis["signals"],
            "fused_trust": fused_trust,
            "risk_analysis": risk_analysis,
            "user_preferences": preference_data["user_preferences"],
            "user_profile": preference_data["profile"],
            "suggestion": suggestion,
            "current_code": current_code,
        }

    def compute_autonomy(self, analysis: Dict[str, object]) -> Dict[str, object]:
        suggestion = dict(analysis["suggestion"])
        code_context = {
            "language": suggestion.get("language", "plain_text"),
            "file_type": suggestion.get("language", "plain_text"),
            "function_length": len([line for line in str(suggestion.get("content", "")).splitlines() if line.strip()]),
            "syntax_errors": 0,
            "compilation_failures": 0,
            "recent_edits": 1 if analysis.get("current_code") and analysis.get("current_code") != suggestion.get("content") else 0,
        }
        suggestion_quality = {
            "suggestions_shown": 1,
            "suggestions_accepted": 0,
            "suggestions_modified": 0,
            "suggestions_rejected": 0,
            "suggestion_quality_score": float(suggestion.get("quality_score", 0.6)),
        }
        autonomy = self.autonomy_engine.decide(
            user_id=str(analysis["user_id"]),
            scores=dict(analysis["scores"]),
            risk_severity=dict(analysis["risk_analysis"]["risk_severity_scores"]),
            trust_signals=dict(analysis["trust_signals"]),
            user_preferences=dict(analysis["user_preferences"]),
            code_context=code_context,
            suggestion_quality=suggestion_quality,
            trust_trend="stable",
            fused_trust=dict(analysis["fused_trust"]),
        )
        shared = self.shared_autonomy_controller.decide(
            user_id=str(analysis["user_id"]),
            fused_trust=dict(analysis["fused_trust"]),
            scores=dict(analysis["scores"]),
            suggestion_quality=suggestion_quality,
            risk_severity=dict(analysis["risk_analysis"]["risk_severity_scores"]),
            user_preferences=dict(analysis["user_preferences"]),
            trust_trend="stable",
            task_understanding={"active_task": "writing_new_code", "task_continuity": "new_task"},
        )
        explanation = self.autonomy_explainer.explain(
            shared_autonomy=shared,
            fused_trust=dict(analysis["fused_trust"]),
            scores=dict(analysis["scores"]),
            risk_severity=dict(analysis["risk_analysis"]["risk_severity_scores"]),
        )
        cognitive_state = self.cognitive_state_model.build(
            scores=dict(analysis["scores"]),
            fused_trust=dict(analysis["fused_trust"]),
            risk_severity=dict(analysis["risk_analysis"]["risk_severity_scores"]),
            suggestion_quality=suggestion_quality,
        )
        return {
            "autonomy_decision": autonomy,
            "shared_autonomy": shared,
            "shared_autonomy_explanation": explanation,
            "cognitive_state": cognitive_state,
        }

    def generate_action(self, decision: Dict[str, object], suggestion: Dict[str, object]) -> Dict[str, object]:
        risk_level = max(float(v) for v in decision["risk_analysis"]["risk_severity_scores"].values())
        return {
            "autonomy_mode": decision["shared_autonomy"]["autonomy_mode"],
            "suggestion": suggestion,
            "current_code": str(decision.get("current_code", "")),
            "risk_level": risk_level,
            "user_preferences": dict(decision["user_preferences"]),
        }

    def execute_action(self, action: Dict[str, object]) -> Dict[str, object]:
        return self.action_manager.handle_action(
            autonomy_decision={"autonomy_mode": action["autonomy_mode"]},
            suggestion=action["suggestion"],
            current_code=action["current_code"],
            risk_level=float(action["risk_level"]),
            user_preferences=action["user_preferences"],
        )


class ContextFlowController:
    """Coordinates the pre-ContextFlow copilot pipeline and calls ContextFlow."""

    def __init__(
        self,
        *,
        task_router: Optional[TaskInputRouter] = None,
        task_engine: Optional[TaskUnderstandingEngine] = None,
        context_builder: Optional[ContextBuilder] = None,
        clarification_engine: Optional[ClarificationEngine] = None,
        planner_ai: Optional[PlannerAI] = None,
        llm_engine: Optional[LLMSuggestionEngine] = None,
        solution_generator: Optional[SolutionGeneratorAI] = None,
        normalizer: Optional[SuggestionNormalizer] = None,
        evaluator: Optional[SuggestionQualityEvaluator] = None,
        verifier: Optional[SolutionVerificationEngine] = None,
        execution_ai: Optional[ExecutionAI] = None,
        user_control: Optional[UserControlLayer] = None,
        contextflow: Optional[ContextFlowMiddlewareAdapter] = None,
    ) -> None:
        self.task_router = task_router or TaskInputRouter()
        self.task_engine = task_engine or TaskUnderstandingEngine()
        self.context_builder = context_builder or ContextBuilder()
        self.clarification_engine = clarification_engine or ClarificationEngine()
        self.llm_engine = llm_engine or LLMSuggestionEngine()
        self.solution_generator = solution_generator or SolutionGeneratorAI(self.llm_engine)
        self.normalizer = normalizer or SuggestionNormalizer()
        self.evaluator = evaluator or SuggestionQualityEvaluator()
        self.verifier = verifier or SolutionVerificationEngine(self.evaluator)
        self.planner_ai = planner_ai or PlannerAI(
            task_understanding=self.task_engine,
            clarification_engine=self.clarification_engine,
            verification_engine=self.verifier,
        )
        self.execution_ai = execution_ai or ExecutionAI()
        self.user_control = user_control or UserControlLayer()
        self.contextflow = contextflow or self._default_contextflow()

    def process(
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
        task = self.task_router.parse_input(user_input)
        plan = self.planner_ai.plan(task, clarification_state)
        task_info = dict(plan["task_info"])
        clarification = dict(plan["clarification"])
        settings = self.user_control.resolve(user_settings)
        memory = dict(memory or {})
        if feedback:
            memory.setdefault("feedback_history", []).append(feedback)
        if clarification["clarification_required"]:
            return {
                "task": task,
                "task_info": task_info,
                "planner": plan,
                "clarification_required": True,
                "questions": clarification["questions"],
                "user_settings": settings,
            }

        context = self.context_builder.build_context(task_info, memory)
        if task_info.get("task") in {"general_query", "casual_conversation"}:
            response = self.llm_engine.generate(context)
            normalized = self.normalizer.normalize(response)
            quality = self.evaluator.evaluate(normalized)
            normalized["quality_score"] = quality["quality_score"]
            normalized["safe_to_execute"] = quality["safe_to_execute"]
            analysis = self.contextflow.analyze_interaction(
                user_input,
                user_id=user_id,
                session_id=session_id,
                behavioral_signals=behavioral_signals or self._default_behavioral_signals(user_input),
                suggestion=normalized,
                current_code=str((memory or {}).get("current_code", "") or (memory or {}).get("working_code", "")),
            )
            autonomy_bundle = self.contextflow.compute_autonomy(analysis)
            decision = {**analysis, **autonomy_bundle}
            return {
                "task": task,
                "task_info": task_info,
                "planner": plan,
                "context": context,
                "clarification_required": False,
                "suggestions": [],
                "suggestion": normalized,
                "suggestion_quality": quality,
                "analysis": analysis,
                "autonomy_mode": self._map_mode_for_user_control(decision["shared_autonomy"]["autonomy_mode"]),
                "action_manager": {
                    "status": "response_displayed",
                    "human_required": False,
                    "payload": {"message": normalized["content"]},
                },
                "contextflow_decision": decision,
                "execution_ai": {"execution_ready": False, "mode": "chat_response"},
                "user_settings": settings,
                "feedback_state": {
                    "feedback": feedback,
                    "refinement_applied": False,
                },
            }
        solution_set = self.solution_generator.generate_solutions(context, suggestion_count=int(settings["suggestion_count"]))
        normalized_suggestions: List[Dict[str, object]] = []
        for suggestion in solution_set["suggestions"]:
            normalized = self.normalizer.normalize(suggestion)
            quality = self.evaluator.evaluate(normalized)
            normalized["quality_score"] = quality["quality_score"]
            normalized["safe_to_execute"] = quality["safe_to_execute"]
            normalized["id"] = suggestion["id"]
            normalized["strategy"] = suggestion["strategy"]
            normalized_suggestions.append(normalized)

        verification = self.planner_ai.verify(normalized_suggestions, verification_level=str(settings["verification_level"]))
        recommended_id = int(verification["recommended"])
        recommended = next(item for item in normalized_suggestions if int(item["id"]) == recommended_id)

        analysis = self.contextflow.analyze_interaction(
            user_input,
            user_id=user_id,
            session_id=session_id,
            behavioral_signals=behavioral_signals or self._default_behavioral_signals(user_input),
            suggestion=recommended,
            current_code=str((memory or {}).get("current_code", "") or (memory or {}).get("working_code", "")),
        )
        autonomy_bundle = self.contextflow.compute_autonomy(analysis)
        decision = {**analysis, **autonomy_bundle}
        computed_mode = self._map_mode_for_user_control(decision["shared_autonomy"]["autonomy_mode"])
        overridden_mode = self.user_control.override_autonomy(computed_mode, settings)
        decision["shared_autonomy"]["autonomy_mode"] = self._map_mode_to_contextflow(overridden_mode)
        prepared_execution = self.execution_ai.prepare(
            recommended,
            autonomy_mode=overridden_mode,
            current_code=str((memory or {}).get("current_code", "") or (memory or {}).get("working_code", "")),
        )
        action = self.contextflow.generate_action(decision, prepared_execution)
        result = self.contextflow.execute_action(action)

        return {
            "task": task,
            "task_info": task_info,
            "planner": plan,
            "context": context,
            "clarification_required": False,
            "suggestions": normalized_suggestions,
            "suggestion": recommended,
            "suggestion_quality": verification,
            "analysis": analysis,
            "autonomy_mode": overridden_mode,
            "action_manager": result["action_manager"],
            "contextflow_decision": decision,
            "execution_ai": prepared_execution,
            "user_settings": settings,
            "feedback_state": {
                "feedback": feedback,
                "refinement_applied": bool(feedback and feedback.lower() not in {"satisfied", "accepted", "done"}),
            },
        }

    @staticmethod
    def _map_mode_for_user_control(mode: str) -> str:
        mapping = {
            "AI_FULL": "AUTO_EXECUTE",
            "AI_ASSIST": "SUGGEST_ONLY",
            "SHARED_CONTROL": "REQUIRE_APPROVAL",
            "HUMAN_CONTROL": "REQUIRE_APPROVAL",
        }
        return mapping.get(mode, "SUGGEST_ONLY")

    @staticmethod
    def _map_mode_to_contextflow(mode: str) -> str:
        mapping = {
            "AUTO_EXECUTE": "AI_FULL",
            "SUGGEST_ONLY": "AI_ASSIST",
            "REQUIRE_APPROVAL": "SHARED_CONTROL",
        }
        return mapping.get(mode, "SHARED_CONTROL")

    def _default_contextflow(self) -> ContextFlowMiddlewareAdapter:
        preference_engine = UserPreferenceEngine(db_path=Path("data") / f"contextflow_copilot_profiles_{uuid4().hex}.sqlite3")
        autonomy_engine = AutonomyDecisionEngine()
        autonomy_engine.smoother._get_state = lambda user_id: {"last_mode": "suggest_only", "pending_mode": "", "safe_streak": 0}
        autonomy_engine.smoother._save_state = lambda user_id, state: None
        shared_autonomy = SharedAutonomyController()
        shared_autonomy.allocator.smoother._get_state = lambda user_id: {"last_mode": "SHARED_CONTROL", "pending_mode": "", "safe_streak": 0}
        shared_autonomy.allocator.smoother._save_state = lambda user_id, state: None
        return ContextFlowMiddlewareAdapter(
            state_model=StateModel(),
            behavior_bridge=BehaviorTrustBridge(),
            risk_analyzer=RiskAnalyzer(),
            preference_engine=preference_engine,
            trust_fusion=TrustFusionModule(),
            autonomy_engine=autonomy_engine,
            shared_autonomy_controller=shared_autonomy,
            autonomy_explainer=AutonomyExplanationModule(),
            cognitive_state_model=CognitiveStateModel(),
            action_manager=ActionManager(log_path=Path("data") / f"contextflow_copilot_actions_{uuid4().hex}.jsonl"),
        )

    @staticmethod
    def _default_behavioral_signals(user_input: str) -> List[dict]:
        return [
            {"event_type": "keydown", "key": "a", "gap_ms": 120},
            {"event_type": "keydown", "key": "Enter", "gap_ms": 180, "line_text": user_input, "suggestion_action": "none"},
        ]
