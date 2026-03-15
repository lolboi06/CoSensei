import unittest
from pathlib import Path
from uuid import uuid4

from app.autonomy_decision_engine import AutonomyDecisionEngine
from app.autonomy_explanation_module import AutonomyExplanationModule
from app.behavior_trust_bridge import BehaviorTrustBridge
from app.cognitive_state_model import CognitiveStateModel
from app.risk_analyzer import RiskAnalyzer
from app.shared_autonomy_controller import SharedAutonomyController
from app.suggestion_engine import SuggestionEngine
from app.task_understanding_module import TaskUnderstandingModule
from app.trust_fusion_module import TrustFusionModule
from app.user_preference_engine import UserPreferenceEngine
from app.model import StateModel
from contextflow.controller import ControllerModules
from contextflow.execution.action_manager import ActionManager

from copilot_pipeline import CopilotPipeline, ContextFlowController as FrontContextFlowController
from contextflow import ContextFlowController as MiddlewareController


class CopilotPipelineTests(unittest.TestCase):
    def _middleware(self) -> MiddlewareController:
        preference_engine = UserPreferenceEngine(db_path=Path("data") / f"test_profiles_{uuid4().hex}.sqlite3")
        autonomy_engine = AutonomyDecisionEngine()
        autonomy_engine.smoother._get_state = lambda user_id: {"last_mode": "suggest_only", "pending_mode": "", "safe_streak": 0}
        autonomy_engine.smoother._save_state = lambda user_id, state: None
        shared_autonomy = SharedAutonomyController()
        shared_autonomy.allocator.smoother._get_state = lambda user_id: {"last_mode": "SHARED_CONTROL", "pending_mode": "", "safe_streak": 0}
        shared_autonomy.allocator.smoother._save_state = lambda user_id, state: None
        return MiddlewareController(
            modules=ControllerModules(
                state_model=StateModel(),
                behavior_bridge=BehaviorTrustBridge(),
                risk_analyzer=RiskAnalyzer(),
                preference_engine=preference_engine,
                trust_fusion=TrustFusionModule(),
                autonomy_engine=autonomy_engine,
                shared_autonomy_controller=shared_autonomy,
                cognitive_state_model=CognitiveStateModel(),
                task_understanding_module=TaskUnderstandingModule(),
                autonomy_explainer=AutonomyExplanationModule(),
                suggestion_engine=SuggestionEngine(),
                action_manager=ActionManager(log_path=Path("data") / f"test_action_manager_{uuid4().hex}.jsonl"),
            )
        )

    def test_task_router_detects_code_generation(self) -> None:
        from copilot_pipeline import TaskInputRouter

        task = TaskInputRouter().parse_input("write a c++ hello world program")
        self.assertEqual(task["task_type"], "code_generation")
        self.assertEqual(task["language"], "cpp")

    def test_postprocessor_normalizes_suggestion(self) -> None:
        from copilot_pipeline import SuggestionPostProcessor

        processed = SuggestionPostProcessor().process(
            {
                "type": "code",
                "content": "```python\nprint('hello')\n```",
                "explanation": "Print hello.",
                "provider": "template",
            }
        )
        self.assertEqual(processed["language"], "python")
        self.assertGreaterEqual(processed["confidence"], 0.7)

    def test_front_controller_processes_into_contextflow(self) -> None:
        controller = FrontContextFlowController(contextflow=self._middleware())
        result = controller.process(
            "write a python hello world program",
            session_id="s1",
            user_id="u1",
            memory={"working_code": "", "conversation_history": []},
        )
        self.assertIn("suggestion", result)
        self.assertIn("autonomy_mode", result)
        self.assertIn("action_manager", result)

    def test_pipeline_wrapper_exposes_simple_interface(self) -> None:
        pipeline = CopilotPipeline(controller=FrontContextFlowController(contextflow=self._middleware()))
        result = pipeline.process_input(
            "explain how a binary search works",
            session_id="s2",
            user_id="u2",
            memory={"working_code": "", "conversation_history": []},
        )
        self.assertIn("task", result)
        self.assertIn("contextflow", result)


if __name__ == "__main__":
    unittest.main()
