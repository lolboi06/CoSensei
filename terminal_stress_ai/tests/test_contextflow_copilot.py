import unittest
from app.main import _clarification_help_response, _detect_solution_choice, _extract_clarification_state, _is_clarification_help_request

from contextflow_copilot import (
    ClarificationEngine,
    ContextBuilder,
    ContextFlowController,
    CopilotPipeline,
    ExecutionAI,
    LLMSuggestionEngine,
    PlannerAI,
    SolutionGeneratorAI,
    SolutionVerificationEngine,
    SuggestionNormalizer,
    SuggestionQualityEvaluator,
    TaskInputRouter,
    TaskUnderstandingEngine,
    UserControlLayer,
)


class ContextFlowCopilotTests(unittest.TestCase):
    def test_router_detects_code_generation(self) -> None:
        task = TaskInputRouter().parse_input("write a c++ program to print hello world")
        self.assertEqual(task["task_type"], "code_generation")
        self.assertEqual(task["language"], "cpp")

    def test_router_detects_casual_conversation(self) -> None:
        task = TaskInputRouter().parse_input("hello")
        self.assertEqual(task["task_type"], "casual_conversation")

    def test_router_detects_game_build_as_software_development(self) -> None:
        task = TaskInputRouter().parse_input("i want to make a multiplayer shooting game")
        self.assertEqual(task["task_type"], "software_development")

    def test_router_detects_broad_program_build_request(self) -> None:
        task = TaskInputRouter().parse_input("i need to build a program for addition of two numbers")
        self.assertEqual(task["task_type"], "software_development")

    def test_router_normalizes_noisy_ecommerce_input(self) -> None:
        task = TaskInputRouter().parse_input("ok i want a website aroung e-commerence")
        self.assertIn("around e-commerce", task["goal"])

    def test_task_understanding_marks_context_requirement(self) -> None:
        task_info = TaskUnderstandingEngine().understand(
            {"task_type": "debugging", "language": "python", "goal": "fix failing test", "raw_input": "debug python test"}
        )
        self.assertTrue(task_info["requires_context"])

    def test_clarification_engine_requests_missing_details(self) -> None:
        clarification = ClarificationEngine().analyze(
            {"task_type": "software_development", "language": "plain_text", "goal": "login system", "raw_input": "build a login system"}
        )
        self.assertTrue(clarification["clarification_required"])
        self.assertEqual(len(clarification["questions"]), 1)

    def test_clarification_engine_asks_game_specific_question_first(self) -> None:
        clarification = ClarificationEngine().analyze(
            {"task_type": "software_development", "language": "plain_text", "goal": "multiplayer shooting game", "raw_input": "make a multiplayer shooting game"}
        )
        self.assertIn("this multiplayer shooting game", clarification["questions"][0].lower())
        self.assertIn("pc, mobile, web, or console", clarification["questions"][0].lower())

    def test_clarification_engine_asks_tool_specific_question_for_addition_program(self) -> None:
        clarification = ClarificationEngine().analyze(
            {"task_type": "software_development", "language": "plain_text", "goal": "program for addition of two numbers", "raw_input": "i need to build a program for addition of two numbers"}
        )
        self.assertIn("this program for addition of two numbers", clarification["questions"][0].lower())
        self.assertIn("cli tool, automation script, desktop tool, or web tool", clarification["questions"][0].lower())

    def test_clarification_engine_uses_generic_topic_specific_fallback(self) -> None:
        clarification = ClarificationEngine().analyze(
            {"task_type": "software_development", "language": "plain_text", "goal": "recommendation workflow for a hospital", "raw_input": "build a recommendation workflow for a hospital"}
        )
        self.assertIn("this recommendation workflow for a hospital", clarification["questions"][0].lower())
        self.assertIn("concept/design", clarification["questions"][0].lower())

    def test_clarification_engine_offers_language_specific_framework_recommendation_when_user_is_unsure(self) -> None:
        clarification = ClarificationEngine().analyze(
            {"task_type": "software_development", "language": "java", "goal": "login system", "raw_input": "build a login system"},
            {"language": "java", "framework_unsure": True},
        )
        self.assertIn("this login system", clarification["questions"][0].lower())
        self.assertIn("recommend", clarification["questions"][0].lower())
        self.assertIn("Spring Boot", clarification["questions"][0])

    def test_clarification_help_request_detection_and_response(self) -> None:
        self.assertTrue(_is_clarification_help_request("what is it"))
        self.assertFalse(_is_clarification_help_request("web app is it ok?"))
        self.assertIn("toolkit", _clarification_help_response("Which framework or library should I use?"))

    def test_extract_clarification_state_can_choose_default_framework(self) -> None:
        state = _extract_clarification_state("your choice", {"language": "java"}, "Which framework or library should I use?")
        self.assertEqual(state["framework"], "Spring Boot")

    def test_extract_clarification_state_auto_selects_effective_storage_when_user_does_not_know(self) -> None:
        state = _extract_clarification_state(
            "i don't know",
            {"site_type": "ecommerce", "language": "java", "framework": "Spring Boot"},
            "Should I use persistent storage? Options: SQLite, PostgreSQL, MySQL, MongoDB, or none.",
        )
        self.assertEqual(state["storage"], "postgresql")
        self.assertIn("most practical default", state["_assistant_message"])

    def test_extract_clarification_state_auto_selects_effective_language_for_website(self) -> None:
        state = _extract_clarification_state(
            "i don't know",
            {"site_type": "web_app"},
            "Which programming language should be used?",
        )
        self.assertEqual(state["language"], "typescript")

    def test_detect_solution_choice_by_label(self) -> None:
        selected = _detect_solution_choice(
            "Scalable",
            [
                {"id": 1, "strategy": "simple"},
                {"id": 2, "strategy": "optimized"},
                {"id": 3, "strategy": "scalable"},
            ],
        )
        self.assertEqual(selected["id"], 3)

    def test_extract_clarification_state_supports_non_implementation_mode(self) -> None:
        state = _extract_clarification_state("it is non-programmable", {}, "Which programming language should be used?")
        self.assertTrue(state["non_implementation"])
        self.assertEqual(state["language"], "plain_text")

    def test_extract_clarification_state_parses_website_site_type(self) -> None:
        state = _extract_clarification_state(
            "web app is it ok?",
            {},
            "For this website, is this a landing page, web app, e-commerce site, dashboard, or content site?",
        )
        self.assertEqual(state["site_type"], "web_app")

    def test_extract_clarification_state_parses_dashboard_typo(self) -> None:
        state = _extract_clarification_state(
            "dashbaord it is",
            {},
            "For this website, is this a landing page, web app, e-commerce site, dashboard, or content site?",
        )
        self.assertEqual(state["site_type"], "dashboard")

    def test_extract_clarification_state_parses_noisy_ecommerce_answer(self) -> None:
        state = _extract_clarification_state(
            "e-commerece",
            {},
            "For this website, is this a landing page, web app, e-commerce site, dashboard, or content site?",
        )
        self.assertEqual(state["site_type"], "ecommerce")

    def test_extract_clarification_state_parses_csharp_language(self) -> None:
        state = _extract_clarification_state("c#", {}, "Which programming language should be used?")
        self.assertEqual(state["language"], "csharp")

    def test_extract_clarification_state_parses_fully_responsive_variant(self) -> None:
        state = _extract_clarification_state(
            "fullyresponsive web",
            {},
            "For this website, should it target desktop, mobile-first, or fully responsive web?",
        )
        self.assertEqual(state["platform"], "responsive_web")

    def test_topic_phrase_strips_leading_ok_we_need_to(self) -> None:
        clarification = ClarificationEngine().analyze(
            {"task_type": "software_development", "language": "plain_text", "goal": "ok we need to build a website", "raw_input": "ok we need to build a website"}
        )
        self.assertIn("this website", clarification["questions"][0].lower())

    def test_context_builder_returns_llm_ready_context(self) -> None:
        context = ContextBuilder().build_context(
            {"task": "code_generation", "language": "python", "objective": "hello world", "requires_context": False, "is_continuation": False},
            {"conversation_history": [{"role": "user", "content": "hello"}], "current_code": "", "user_preferences": {}},
        )
        self.assertEqual(context["language"], "python")
        self.assertIn("prompt_context", context)

    def test_normalizer_and_quality(self) -> None:
        suggestion = SuggestionNormalizer().normalize(
            {"type": "code", "content": "```python\nprint('hello')\n```", "explanation": "Print hello.", "provider": "template"}
        )
        quality = SuggestionQualityEvaluator().evaluate(suggestion)
        self.assertEqual(suggestion["language"], "python")
        self.assertTrue(quality["valid_code"])

    def test_solution_verification_selects_recommended(self) -> None:
        verification = SolutionVerificationEngine().verify(
            [
                {"id": 1, "type": "code", "language": "python", "content": "print('a')"},
                {"id": 2, "type": "code", "language": "python", "content": "def main():\n    print('b')\n\nmain()"},
                {"id": 3, "type": "code", "language": "python", "content": ""},
            ]
        )
        self.assertEqual(verification["recommended"], 2)

    def test_user_control_overrides_autonomy(self) -> None:
        control = UserControlLayer()
        settings = control.resolve({"autonomy_mode": "REQUIRE_APPROVAL", "suggestion_count": 5, "verification_level": "strict"})
        self.assertEqual(control.override_autonomy("AUTO_EXECUTE", settings), "REQUIRE_APPROVAL")
        self.assertEqual(settings["suggestion_count"], 5)

    def test_planner_and_execution_roles_exist(self) -> None:
        planner = PlannerAI()
        plan = planner.plan(
            {"task_type": "software_development", "language": "plain_text", "goal": "login system", "raw_input": "build a login system"}
        )
        execution = ExecutionAI().prepare({"id": 2, "content": "print('hello')"}, "SUGGEST_ONLY", "")
        self.assertIn("clarification", plan)
        self.assertTrue(execution["execution_ready"])

    def test_controller_returns_structured_response(self) -> None:
        controller = ContextFlowController()
        result = controller.process(
            "write a python hello world program",
            session_id="s1",
            user_id="u1",
            memory={"current_code": "", "conversation_history": []},
        )
        self.assertIn("suggestions", result)
        self.assertEqual(len(result["suggestions"]), 3)
        self.assertIn("suggestion", result)
        self.assertIn("suggestion_quality", result)
        self.assertIn("autonomy_mode", result)
        self.assertIn("action_manager", result)
        self.assertIn("planner", result)
        self.assertIn("execution_ai", result)

    def test_controller_returns_clarification_when_needed(self) -> None:
        controller = ContextFlowController()
        result = controller.process(
            "build a login system",
            session_id="s3",
            user_id="u3",
            memory={"current_code": "", "conversation_history": []},
        )
        self.assertTrue(result["clarification_required"])
        self.assertIn("questions", result)

    def test_controller_uses_single_chat_response_for_casual_input(self) -> None:
        controller = ContextFlowController()
        result = controller.process(
            "hello",
            session_id="s5",
            user_id="u5",
            memory={"current_code": "", "conversation_history": []},
        )
        self.assertFalse(result["clarification_required"])
        self.assertEqual(result["suggestions"], [])
        self.assertEqual(result["suggestion"]["suggestion_type"], "response")

    def test_general_chat_response_handles_identity_question(self) -> None:
        response = LLMSuggestionEngine()._generate_template(
            {"task": "general_query", "objective": "who are u", "language": "plain_text", "conversation_history": []}
        )
        self.assertIn("assistant", response["content"].lower())

    def test_general_chat_response_handles_how_are_you(self) -> None:
        response = LLMSuggestionEngine()._generate_template(
            {"task": "general_query", "objective": "how r u", "language": "plain_text", "conversation_history": []}
        )
        self.assertIn("ready to help", response["content"].lower())

    def test_general_chat_response_can_give_requested_question(self) -> None:
        response = LLMSuggestionEngine()._generate_template(
            {"task": "general_query", "objective": "give me a physics question", "language": "plain_text", "conversation_history": []}
        )
        self.assertIn("2 kg object", response["content"])

    def test_solution_generator_creates_distinct_strategies(self) -> None:
        generator = SolutionGeneratorAI(LLMSuggestionEngine())
        result = generator.generate_solutions(
            {
                "task": "software_development",
                "language": "java",
                "objective": "website for supermarket",
                "framework": "Spring Boot",
                "storage": "sqlite",
                "conversation_history": [],
                "user_preferences": {},
                "prompt_context": "Generate implementation options.",
            }
        )
        contents = [item["content"] for item in result["suggestions"]]
        self.assertEqual(len(set(contents)), 3)

    def test_pipeline_wrapper(self) -> None:
        pipeline = CopilotPipeline()
        result = pipeline.process_input(
            "explain how binary search works",
            session_id="s2",
            user_id="u2",
            memory={"current_code": "", "conversation_history": []},
            user_settings={"autonomy_mode": "SUGGEST_ONLY", "suggestion_count": 3},
            feedback="refine",
        )
        self.assertIn("task", result)
        self.assertIn("contextflow_decision", result)
        self.assertIn("feedback_state", result)

    def test_refine_until_satisfied(self) -> None:
        pipeline = CopilotPipeline()
        result = pipeline.refine_until_satisfied(
            "write a python hello world program",
            session_id="s4",
            user_id="u4",
            memory={"current_code": "", "conversation_history": []},
            feedback_sequence=["refine", "satisfied"],
        )
        self.assertIn("suggestions", result)


if __name__ == "__main__":
    unittest.main()
