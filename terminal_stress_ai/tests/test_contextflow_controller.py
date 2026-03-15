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
from contextflow.controller import ContextFlowController, ControllerModules
from contextflow.execution.action_manager import ActionManager


class ContextFlowControllerTests(unittest.TestCase):
    def _controller(self) -> ContextFlowController:
        preference_engine = UserPreferenceEngine(db_path=Path("data") / f"test_profiles_{uuid4().hex}.sqlite3")
        autonomy_engine = AutonomyDecisionEngine()
        autonomy_engine.smoother._get_state = lambda user_id: {"last_mode": "suggest_only", "pending_mode": "", "safe_streak": 0}
        autonomy_engine.smoother._save_state = lambda user_id, state: None
        shared_autonomy_controller = SharedAutonomyController()
        shared_autonomy_controller.allocator.smoother._get_state = lambda user_id: {
            "last_mode": "SHARED_CONTROL",
            "pending_mode": "",
            "safe_streak": 0,
        }
        shared_autonomy_controller.allocator.smoother._save_state = lambda user_id, state: None
        return ContextFlowController(
            modules=ControllerModules(
                state_model=StateModel(),
                behavior_bridge=BehaviorTrustBridge(),
                risk_analyzer=RiskAnalyzer(),
                preference_engine=preference_engine,
                trust_fusion=TrustFusionModule(),
                autonomy_engine=autonomy_engine,
                shared_autonomy_controller=shared_autonomy_controller,
                cognitive_state_model=CognitiveStateModel(),
                task_understanding_module=TaskUnderstandingModule(),
                autonomy_explainer=AutonomyExplanationModule(),
                suggestion_engine=SuggestionEngine(),
                action_manager=ActionManager(log_path=Path("data") / f"test_action_manager_{uuid4().hex}.jsonl"),
            )
        )
        
    @staticmethod
    def _behavioral_signals() -> list[dict]:
        return [
            {"event_type": "keydown", "key": "a", "gap_ms": 120},
            {"event_type": "keydown", "key": "Enter", "gap_ms": 180, "line_text": "write python hello world", "suggestion_action": "accept"},
        ]

    def test_controller_returns_autonomy_decision(self) -> None:
        controller = self._controller()
        result = controller.evaluate_suggestion(
            session_id="s1",
            user_id="u1",
            llm_suggestion={
                "type": "code",
                "language": "cpp",
                "content": "#include <iostream>\nint main() { return 0; }",
                "explanation": "Minimal C++ program.",
            },
            current_code="",
            behavioral_signals=self._behavioral_signals(),
            task_input="write c++ code",
        )
        self.assertIn("autonomy_decision", result)
        self.assertIn(result["autonomy_decision"]["autonomy_mode"], {"AI_FULL", "AI_ASSIST", "SHARED_CONTROL", "HUMAN_CONTROL"})
        self.assertIn("shared_autonomy", result)
        self.assertIn("cognitive_state", result)

    def test_controller_process_invokes_action_manager(self) -> None:
        controller = self._controller()
        result = controller.process(
            session_id="s2",
            user_id="u2",
            llm_suggestion={
                "type": "code",
                "language": "python",
                "content": "print('hello')",
                "explanation": "Print hello.",
            },
            current_code="",
            behavioral_signals=self._behavioral_signals(),
            task_input="write python hello world",
        )
        self.assertIn("action_manager", result)
        self.assertIn(result["action_manager"]["status"], {"executed_automatically", "suggestion_displayed", "approval_required", "hint_only"})

    def test_controller_can_generate_suggestion_from_task_input(self) -> None:
        controller = self._controller()

        def llm_engine(task_input: str, current_code: str) -> dict:
            return {
                "type": "code",
                "language": "python",
                "content": "print('hello world')",
                "explanation": f"Generated for: {task_input}",
            }

        result = controller.handle_task_input(
            session_id="s3",
            user_id="u3",
            task_input="write python hello world",
            current_code="",
            behavioral_signals=self._behavioral_signals(),
            llm_suggestion_engine=llm_engine,
        )
        self.assertEqual(result["llm_suggestion"]["content"], "print('hello world')")
        self.assertIn("shared_autonomy_explanation", result)


if __name__ == "__main__":
    unittest.main()
