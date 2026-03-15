from __future__ import annotations

from typing import Dict, Optional

from .clarification_engine import ClarificationEngine
from .grok_client import GrokClient
from .solution_verification import SolutionVerificationEngine
from .task_understanding import TaskUnderstandingEngine


class PlannerAI:
    """AI #1 role: plans tasks, requests clarification, and verifies solution sets."""

    def __init__(
        self,
        *,
        task_understanding: Optional[TaskUnderstandingEngine] = None,
        clarification_engine: Optional[ClarificationEngine] = None,
        verification_engine: Optional[SolutionVerificationEngine] = None,
    ) -> None:
        self.task_understanding = task_understanding or TaskUnderstandingEngine()
        self.clarification_engine = clarification_engine or ClarificationEngine()
        self.verification_engine = verification_engine or SolutionVerificationEngine()
        self.grok_client = GrokClient(api_key_env="PLANNER_GROK_API_KEY", model_env="PLANNER_GROK_MODEL")

    def plan(self, task: Dict[str, str], clarification_state: Optional[Dict[str, str]] = None) -> Dict[str, object]:
        task_info = self.task_understanding.understand(task, clarification_state)
        clarification = self.clarification_engine.analyze(task, clarification_state)
        complexity = "high" if task_info["requires_context"] and task["task_type"] in {"software_development", "debugging"} else "medium"
        result = {
            "task_info": task_info,
            "clarification": clarification,
            "complexity": complexity,
        }
        grok_result = self._plan_with_grok(task, clarification_state)
        if grok_result is not None:
            result["planner_ai"] = grok_result
        return result

    def verify(self, suggestions: list[Dict[str, object]], verification_level: str = "balanced") -> Dict[str, object]:
        verified = self.verification_engine.verify(suggestions, verification_level=verification_level)
        grok_result = self._verify_with_grok(suggestions, verification_level)
        if grok_result is not None:
            verified["planner_ai"] = grok_result
        return verified

    def _plan_with_grok(self, task: Dict[str, str], clarification_state: Optional[Dict[str, str]]) -> Dict[str, object] | None:
        return self.grok_client.complete_json(
            system_prompt=(
                "You are AI #1 Planner. Return JSON with keys: missing_information, technologies, complexity, notes. "
                "Be concise and structured."
            ),
            user_prompt=str(
                {
                    "task": task,
                    "clarification_state": clarification_state or {},
                }
            ),
        )

    def _verify_with_grok(self, suggestions: list[Dict[str, object]], verification_level: str) -> Dict[str, object] | None:
        return self.grok_client.complete_json(
            system_prompt=(
                "You are AI #1 Verifier. Return JSON with keys: evaluation and recommended_solution. "
                "evaluation must be a list of objects with solution, score, notes."
            ),
            user_prompt=str(
                {
                    "verification_level": verification_level,
                    "suggestions": suggestions,
                }
            ),
        )
