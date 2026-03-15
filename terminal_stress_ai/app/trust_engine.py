from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Literal, Optional


TrustLevel = Literal["HIGH", "MEDIUM", "LOW"]
TrustEvent = Literal["accept", "reject", "heavy_edit", "task_success", "task_failure"]


@dataclass
class InteractionSignals:
    accept_rate: float
    usage_frequency: float
    correction_rate: float
    override_rate: float
    session_success: float


@dataclass
class EngineAdapters:
    behavior_analysis: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None
    risk_evaluation: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None
    autonomy_decision: Optional[Callable[[Dict[str, float]], Dict[str, str]]] = None


class TrustEngine:
    """Trust estimation module for ContextFlow shared autonomy."""

    def __init__(self, adapters: Optional[EngineAdapters] = None) -> None:
        self.adapters = adapters or EngineAdapters()
        self._trust_score: float = 0.5

    @staticmethod
    def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))

    def get_trust_level(self, score: Optional[float] = None) -> TrustLevel:
        value = self._trust_score if score is None else score
        if value > 0.75:
            return "HIGH"
        if value >= 0.5:
            return "MEDIUM"
        return "LOW"

    def calculate_trust(self, signals: InteractionSignals) -> Dict[str, object]:
        # Weighted trust formula using user interaction signals.
        score = (
            signals.accept_rate * 0.5
            + signals.usage_frequency * 0.2
            - signals.correction_rate * 0.2
            - signals.override_rate * 0.2
            + signals.session_success * 0.1
        )
        score = self._clamp(score)
        self._trust_score = score

        reasons: List[str] = []
        if signals.accept_rate < 0.4:
            reasons.append("low acceptance rate")
        if signals.accept_rate >= 0.7:
            reasons.append("high acceptance rate")
        if signals.usage_frequency >= 0.6:
            reasons.append("frequent AI usage")
        if signals.override_rate >= 0.5:
            reasons.append("high override rate")
        if signals.correction_rate <= 0.25:
            reasons.append("low correction rate")
        if signals.override_rate <= 0.2:
            reasons.append("low override rate")
        if signals.session_success >= 0.7:
            reasons.append("high session success")
        if not reasons:
            reasons.append("mixed interaction signals")

        return {
            "trust_score": round(score, 3),
            "trust_level": self.get_trust_level(score),
            "reason": " and ".join(reasons),
        }

    def update_trust(self, event: TrustEvent, intensity: float = 1.0) -> Dict[str, object]:
        intensity = self._clamp(intensity)
        delta_map = {
            "accept": 0.03,
            "reject": -0.05,
            "heavy_edit": -0.04,
            "task_success": 0.04,
            "task_failure": -0.06,
        }
        delta = delta_map[event] * intensity
        self._trust_score = self._clamp(self._trust_score + delta)

        reason_map = {
            "accept": "user accepted an AI suggestion",
            "reject": "user rejected an AI suggestion",
            "heavy_edit": "user heavily edited AI output",
            "task_success": "AI-assisted task completed successfully",
            "task_failure": "AI-assisted task failed",
        }

        return {
            "trust_score": round(self._trust_score, 3),
            "trust_level": self.get_trust_level(),
            "reason": reason_map[event],
        }

    @property
    def trust_score(self) -> float:
        return self._trust_score


if __name__ == "__main__":
    engine = TrustEngine()

    signals = InteractionSignals(
        accept_rate=0.82,
        usage_frequency=0.74,
        correction_rate=0.12,
        override_rate=0.08,
        session_success=0.77,
    )

    baseline = engine.calculate_trust(signals)
    print("Baseline:", baseline)

    after_accept = engine.update_trust("accept")
    print("After accept:", after_accept)

    after_heavy_edit = engine.update_trust("heavy_edit", intensity=0.8)
    print("After heavy edit:", after_heavy_edit)
