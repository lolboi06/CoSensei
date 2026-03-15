import unittest
from pathlib import Path
from uuid import uuid4

from app.action_execution_engine import ActionExecutionEngine
from app.adaptive_copilot_pipeline import AdaptiveCopilotPipeline
from app.autonomy_explanation_module import AutonomyExplanationModule
from app.cognitive_state_model import CognitiveStateModel
from app.conversation_memory_manager import ConversationMemoryManager
from app.intent_predictor import IntentPredictor
from app.policy_learning_system import PolicyLearningSystem
from app.shared_autonomy_controller import SharedAutonomyController
from app.suggestion_engine import SuggestionEngine
from app.task_memory_manager import TaskMemoryManager
from app.task_understanding_module import TaskUnderstandingModule
from app.user_profile_memory_manager import UserProfileMemoryManager


class AdaptiveCopilotTests(unittest.TestCase):
    def test_task_understanding_reuses_previous_code(self) -> None:
        module = TaskUnderstandingModule()
        memory = {
            "conversation_history": [{"role": "user", "content": "write a C++ program that adds numbers"}],
            "code_memory": {"language": "cpp", "last_generated_code": "int main() { return 0; }"},
            "task_context": {"active_task": "writing_new_code"},
        }
        working_memory = {"active_task": "writing_new_code", "generated_code": "int main() { return 0; }"}

        result = module.understand(
            memory=memory,
            current_message="now modify it to use functions",
            detected_intent={"task": "writing_new_code"},
            working_memory=working_memory,
            code_context={"language": "cpp"},
        )

        self.assertEqual(result["active_task"], "editing_previous_code")
        self.assertTrue(result["uses_previous_code"])
        self.assertEqual(result["task_continuity"], "continued_task")

    def test_shared_autonomy_uses_formula_and_returns_mode(self) -> None:
        controller = SharedAutonomyController()
        controller.allocator.smoother._get_state = lambda user_id: {"last_mode": "SHARED_CONTROL", "pending_mode": "", "safe_streak": 0}
        controller.allocator.smoother._save_state = lambda user_id, state: None
        decision = controller.decide(
            user_id="u1",
            fused_trust={"score": 0.9, "probability": 0.9},
            scores={
                "stress": {"score": 0.1, "probability": 0.9},
                "cognitive_load": {"score": 0.2, "probability": 0.8},
                "engagement": {"score": 0.8, "probability": 0.9},
            },
            suggestion_quality={"suggestion_quality_score": 0.9},
            risk_severity={"hostility": 0.1, "ai_distrust": 0.1, "emotional_intensity": 0.1},
            user_preferences={},
            trust_trend="stable",
            task_understanding={"active_task": "writing_new_code", "task_continuity": "continued_task"},
        )

        self.assertIn(decision["autonomy_mode"], {"AI_ASSIST", "AI_FULL"})
        self.assertGreater(decision["autonomy_score"], 0.55)

    def test_action_engine_requires_confirmation_for_modification(self) -> None:
        engine = ActionExecutionEngine()
        result = engine.execute(
            session_id="s1",
            shared_autonomy={"autonomy_mode": "SHARED_CONTROL"},
            suggestion={"type": "code_modification", "content": "print('x')"},
            risk_severity={"hostility": 0.1, "ai_distrust": 0.1, "emotional_intensity": 0.2},
            explanation={"explanation": "Need approval."},
            task_understanding={"active_task": "editing_previous_code"},
        )
        self.assertTrue(result["confirmation_required"])
        self.assertEqual(result["mode"], "SHARED_CONTROL")

    def test_policy_learning_persists_metrics(self) -> None:
        db_path = Path("data") / f"test_policy_learning_{uuid4().hex}.sqlite3"
        system = PolicyLearningSystem(db_path=db_path)
        result = system.update(
            user_id="u1",
            session_id="s1",
            suggestion_quality={"suggestions_shown": 4, "suggestions_accepted": 3},
            trust_signals={"override_rate": 0.1, "trust_delta": 0.2},
            trust_score=0.8,
            validation={"model_accuracy": 0.9},
            autonomy_mode="AI_ASSIST",
            action_result={"status": "executed_automatically"},
        )
        self.assertEqual(result["policy_adjustment"], "increase_autonomy")
        self.assertTrue(db_path.exists())

    def test_casual_conversation_does_not_generate_code(self) -> None:
        predictor = IntentPredictor()
        intent = predictor.predict(
            events=[{"key": "Enter", "line_text": "how are u"}],
            features={"override_rate": 1.0, "backspace_ratio": 0.2},
            code_context={"language": "plain_text", "syntax_errors": 0, "function_length": 1},
        )
        self.assertEqual(intent["task"], "casual_conversation")

        suggestion = SuggestionEngine().generate(
            task_understanding={
                "active_task": "casual_conversation",
                "retrieved_code": "",
                "language": "plain_text",
            },
            memory={"conversation_history": [{"role": "user", "content": "how are u"}], "code_memory": {}, "task_context": {}},
            task_context={"language": "plain_text"},
            user_preferences={},
            working_memory={},
        )
        self.assertEqual(suggestion["type"], "response")

    def test_casual_response_does_not_pollute_code_memory(self) -> None:
        session_id = "chat-session"
        user_id = "chat-user"
        conversation_memory = ConversationMemoryManager()
        conversation_memory.storage_mode = "json"
        conversation_memory.json_path = Path("data") / f"test_conversation_memory_{uuid4().hex}.json"
        task_memory = TaskMemoryManager()
        task_memory.storage_mode = "json"
        task_memory.json_path = Path("data") / f"test_task_memory_{uuid4().hex}.json"
        user_profile_memory = UserProfileMemoryManager()
        user_profile_memory.storage_mode = "json"
        user_profile_memory.json_path = Path("data") / f"test_user_profile_memory_{uuid4().hex}.json"
        pipeline = AdaptiveCopilotPipeline(
            conversation_memory=conversation_memory,
            task_memory=task_memory,
            user_profile_memory=user_profile_memory,
            cognitive_state_model=CognitiveStateModel(),
            task_understanding=TaskUnderstandingModule(),
            autonomy_controller=SharedAutonomyController(),
            explanation_module=AutonomyExplanationModule(),
            suggestion_engine=SuggestionEngine(),
            action_engine=ActionExecutionEngine(),
            policy_learning=PolicyLearningSystem(db_path=Path("data") / f"test_policy_learning_{uuid4().hex}.sqlite3"),
        )
        pipeline.autonomy_controller.allocator.smoother._get_state = lambda user_id: {
            "last_mode": "SHARED_CONTROL",
            "pending_mode": "",
            "safe_streak": 0,
        }
        pipeline.autonomy_controller.allocator.smoother._save_state = lambda user_id, state: None

        conversation_memory.add_user_message(session_id, "how are u")
        output = pipeline.run(
            session_id=session_id,
            user_id=user_id,
            current_message="how are u",
            code_context={"language": "plain_text", "file_type": "plain_text"},
            detected_intent={"task": "casual_conversation", "confidence": 0.9},
            scores={
                "stress": {"score": 0.2, "probability": 0.8, "level": "low"},
                "cognitive_load": {"score": 0.2, "probability": 0.8, "level": "low"},
                "engagement": {"score": 0.5, "probability": 0.8, "level": "medium"},
                "trust_in_ai": {"score": 0.5, "probability": 0.8, "level": "medium"},
            },
            fused_trust={"score": 0.5, "probability": 0.8, "level": "medium"},
            suggestion_quality={"suggestion_quality_score": 0.5, "suggestions_shown": 1, "suggestions_accepted": 0},
            risk_severity={"hostility": 0.0, "ai_distrust": 0.0, "emotional_intensity": 0.0},
            user_preferences={},
            validation={"model_accuracy": 0.8},
            trust_signals={"override_rate": 0.0, "trust_delta": 0.0},
            trust_trend="stable",
        )

        self.assertEqual(output["suggestion"]["type"], "response")
        self.assertEqual(output["working_memory"]["generated_code"], "")


if __name__ == "__main__":
    unittest.main()
