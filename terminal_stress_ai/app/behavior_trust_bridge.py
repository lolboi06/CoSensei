from __future__ import annotations

from typing import Dict, List

from .trust_engine import InteractionSignals, TrustEngine


class BehaviorTrustBridge:
    """Maps behavior-event history into TrustEngine signals."""

    def __init__(self) -> None:
        self.engine = TrustEngine()

    @staticmethod
    def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))

    def build_signals(self, events: List[dict], features: Dict[str, float]) -> InteractionSignals:
        total_events = max(len(events), 1)
        correction_rate = self._clamp(float(features.get("backspace_ratio", 0.0)))
        pause_1500 = self._clamp(float(features.get("pause_1500ms_count", 0.0)) / 5.0)
        content_intensity = self._clamp(float(features.get("content_intensity_mean", 0.0)))
        profanity_rate = self._clamp(float(features.get("profanity_event_rate", 0.0)))
        insult_rate = self._clamp(float(features.get("insult_event_rate", 0.0)))
        distrust_rate = self._clamp(float(features.get("distrust_event_rate", 0.0)))
        distrust_recent = self._clamp(float(features.get("distrust_recent", 0.0)))
        intensity_recent = self._clamp(float(features.get("content_intensity_recent", 0.0)))

        # Treat each Enter key as one suggestion decision point for this terminal flow.
        decision_events = [e for e in events if e.get("key") == "Enter"]
        decisions = [str(e.get("suggestion_action", "none")) for e in decision_events]
        total_decisions = max(len(decisions), 1)

        accepts = sum(1 for d in decisions if d == "accept")
        overrides = sum(1 for d in decisions if d == "override")
        neutrals = sum(1 for d in decisions if d == "none")

        explicit = accepts + overrides
        if explicit > 0:
            accept_rate = accepts / explicit
            override_rate = overrides / explicit
        else:
            # If explicit user decision isn't present, infer conservative trust from behavior quality.
            inferred = self._clamp(0.45 + 0.20 * (1.0 - correction_rate) - 0.18 * pause_1500 - 0.40 * content_intensity)
            accept_rate = inferred
            override_rate = 1.0 - inferred

        if profanity_rate > 0.0:
            # Hostile/profane interactions should suppress inferred trust.
            accept_rate = self._clamp(accept_rate - 0.35 * profanity_rate)
            override_rate = self._clamp(max(override_rate, 0.4 + 0.4 * profanity_rate))
        if insult_rate > 0.0:
            accept_rate = self._clamp(accept_rate - 0.30 * insult_rate)
            override_rate = self._clamp(max(override_rate, 0.45 + 0.35 * insult_rate))
        if distrust_rate > 0.0:
            accept_rate = self._clamp(accept_rate - 0.45 * distrust_rate)
            override_rate = self._clamp(max(override_rate, 0.5 + 0.4 * distrust_rate))
        if distrust_recent > 0.0:
            accept_rate = self._clamp(accept_rate - 0.55 * distrust_recent)
            override_rate = self._clamp(max(override_rate, 0.6 + 0.35 * distrust_recent))

        # Usage frequency = fraction of decision points with an explicit AI action.
        usage_frequency = explicit / total_decisions
        if neutrals > 0 and explicit == 0:
            # In this terminal flow many interactions are neutral; keep a conservative usage floor.
            usage_frequency = 0.25
        if distrust_recent > 0.0 or profanity_rate > 0.0:
            usage_frequency = min(usage_frequency, 0.35)

        # Session success proxy: combines acceptance and quality signals.
        session_success = self._clamp(
            accept_rate * 0.5
            + (1.0 - correction_rate) * 0.25
            + (1.0 - override_rate) * 0.15
            + (1.0 - pause_1500) * 0.10
            - 0.20 * content_intensity
            - 0.25 * profanity_rate
            - 0.20 * insult_rate
            - 0.35 * distrust_rate
            - 0.30 * distrust_recent
            - 0.10 * intensity_recent
        )

        return InteractionSignals(
            accept_rate=self._clamp(accept_rate),
            usage_frequency=self._clamp(usage_frequency),
            correction_rate=correction_rate,
            override_rate=self._clamp(override_rate),
            session_success=self._clamp(session_success),
        )

    def analyze(self, events: List[dict], features: Dict[str, float]) -> Dict[str, object]:
        signals = self.build_signals(events, features)
        trust_result = self.engine.calculate_trust(signals)
        return {
            "trust": trust_result,
            "signals": {
                "accept_rate": round(signals.accept_rate, 3),
                "usage_frequency": round(signals.usage_frequency, 3),
                "correction_rate": round(signals.correction_rate, 3),
                "override_rate": round(signals.override_rate, 3),
                "session_success": round(signals.session_success, 3),
            },
        }
