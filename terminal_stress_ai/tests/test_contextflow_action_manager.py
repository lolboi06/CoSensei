import unittest

from contextflow.execution.action_manager import Action, ActionManager


class ActionManagerTests(unittest.TestCase):
    def test_ai_full_executes_code(self) -> None:
        manager = ActionManager()
        result = manager.handle_action(
            autonomy_decision="AI_FULL",
            suggestion={
                "type": "code",
                "language": "cpp",
                "content": "#include <iostream>\nint main(){return 0;}",
                "explanation": "Insert hello world program",
            },
            current_code="",
            risk_level=0.1,
            user_preferences={},
        )
        self.assertEqual(result["action_manager"]["status"], "executed_automatically")
        self.assertIn("rollback_token", result["action_manager"]["payload"])

    def test_shared_control_requests_approval(self) -> None:
        manager = ActionManager()
        result = manager.handle_action(
            autonomy_decision={"autonomy_mode": "SHARED_CONTROL"},
            suggestion={
                "type": "code",
                "language": "python",
                "content": "print('hello')",
                "explanation": "Print hello",
            },
            current_code="",
            risk_level=0.7,
            user_preferences={},
        )
        self.assertEqual(result["action_manager"]["status"], "approval_required")
        self.assertTrue(result["action_manager"]["human_required"])

    def test_human_control_returns_hint_only(self) -> None:
        manager = ActionManager()
        result = manager.handle_action(
            autonomy_decision="HUMAN_CONTROL",
            suggestion={
                "type": "explanation",
                "content": "Use std::cout for output.",
                "explanation": "Prefer manual edits in this mode.",
            },
            current_code="",
            risk_level=0.1,
            user_preferences={},
        )
        self.assertEqual(result["action_manager"]["status"], "hint_only")
        self.assertIn("hint", result["action_manager"]["payload"])

    def test_dangerous_payload_is_blocked(self) -> None:
        manager = ActionManager()
        result = manager.handle_action(
            autonomy_decision="AI_FULL",
            suggestion={
                "type": "code",
                "content": "rm -rf /",
                "explanation": "danger",
            },
            current_code="safe",
            risk_level=0.1,
            user_preferences={},
        )
        self.assertEqual(result["action_manager"]["status"], "blocked")

    def test_rollback_restores_previous_code(self) -> None:
        manager = ActionManager()
        exec_result = manager.execute_action(
            Action(type="insert_code_snippet", payload={"code": "print('new')"}, explanation="apply"),
            current_code="print('old')",
            risk_level=0.1,
            execution_mode="AI_FULL",
        )
        rollback_token = exec_result["action_manager"]["payload"]["rollback_token"]
        rollback = manager.rollback_action(rollback_token)
        self.assertTrue(rollback["rolled_back"])
        self.assertEqual(rollback["restored_code"], "print('old')")


if __name__ == "__main__":
    unittest.main()
