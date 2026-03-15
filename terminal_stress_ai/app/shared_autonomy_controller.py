from __future__ import annotations

from typing import Dict

from .shared_autonomy_allocator import SharedAutonomyAllocator


class SharedAutonomyController:
    def __init__(self) -> None:
        self.allocator = SharedAutonomyAllocator()

    def decide(
        self,
        user_id: str,
        fused_trust: Dict[str, object],
        scores: Dict[str, dict],
        suggestion_quality: Dict[str, object],
        risk_severity: Dict[str, float],
        user_preferences: Dict[str, object],
        trust_trend: str,
        task_understanding: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        decision = self.allocator.allocate(
            user_id=user_id,
            fused_trust=fused_trust,
            scores=scores,
            suggestion_quality=suggestion_quality,
            risk_severity=risk_severity,
            user_preferences=user_preferences,
            trust_trend=trust_trend,
        )
        decision["task_alignment"] = {
            "active_task": str((task_understanding or {}).get("active_task", "")),
            "continuity": str((task_understanding or {}).get("task_continuity", "")),
        }
        return decision
