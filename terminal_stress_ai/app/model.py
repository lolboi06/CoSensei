from __future__ import annotations

import json
import os
from typing import Dict, List
from urllib import request, error

from .features import FeatureVector
from .ml_stress_model import MLStressModel

TARGETS = ["stress", "cognitive_load", "engagement", "trust_in_ai"]


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _to_level(score: float) -> str:
    if score < 0.33:
        return "low"
    if score < 0.66:
        return "medium"
    return "high"


def _probability_for_level(score: float) -> float:
    boundaries = [0.33, 0.66]
    margin = min(abs(score - boundaries[0]), abs(score - boundaries[1]))
    prob = 0.5 + 0.5 * min(margin / 0.33, 1.0)
    return float(round(prob, 3))


def _heuristic_scores(vec: FeatureVector) -> List[float]:
    f = vec.values
    distrust_signal = max(f.get("distrust_event_rate", 0.0), f.get("distrust_recent", 0.0))
    intensity_signal = max(f.get("content_intensity_mean", 0.0), f.get("content_intensity_recent", 0.0))
    stress = _clip(
        0.0014 * f["iki_mean"]
        + 0.004 * f["pause_1500ms_count"]
        + 0.35 * f["backspace_ratio"]
        + 0.3 * f["override_rate"]
        + 0.0008 * f["iki_std"]
        + 0.35 * intensity_signal
        + 0.12 * f.get("profanity_event_rate", 0.0)
        + 0.10 * f.get("insult_event_rate", 0.0)
        + 0.22 * distrust_signal
    )
    cognitive = _clip(
        0.0013 * f["iki_std"]
        + 0.0025 * f["pause_500ms_count"]
        + 0.04 * f["hesitation_count"]
        + 0.12 * f["backspace_ratio"]
        + 0.08 * intensity_signal
    )
    engagement = _clip(
        0.9
        - (0.0012 * f["iki_mean"] + 0.01 * f["pause_1500ms_count"])
        + 0.0005 * f["typing_cpm"]
        - 0.10 * intensity_signal
    )
    trust = _clip(
        0.9
        - (0.55 * f["override_rate"] + 0.15 * f["backspace_ratio"] + 0.001 * f["pause_500ms_count"])
        - 0.15 * intensity_signal
        - 0.15 * f.get("insult_event_rate", 0.0)
        - 0.40 * distrust_signal
    )
    return [stress, cognitive, engagement, trust]


class StateModel:
    def __init__(self) -> None:
        self.name = "heuristic_v4_grok_optional"
        self.stress_model = MLStressModel()
        self.grok_api_key = os.getenv("GROK_API_KEY", "").strip()
        self.grok_model = os.getenv("GROK_MODEL", "grok-3-mini").strip()
        self.provider = "xai"
        if self.grok_api_key.startswith("gsk_"):
            # gsk_* is a Groq key, not xAI Grok.
            self.provider = "groq"
            self.grok_base_url = os.getenv("GROK_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
            if self.grok_model.startswith("grok-"):
                # Auto-fallback to a Groq-supported default unless explicitly overridden.
                self.grok_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        else:
            self.grok_base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1").strip().rstrip("/")

    def predict(self, vec: FeatureVector) -> Dict[str, dict]:
        scores = _heuristic_scores(vec)
        scores[0] = self.stress_model.predict(vec.values, scores[0])
        out: Dict[str, dict] = {}
        for idx, target in enumerate(TARGETS):
            score = float(scores[idx])
            out[target] = {
                "level": _to_level(score),
                "score": round(score, 3),
                "probability": _probability_for_level(score),
            }
        return out

    def llm_enrichment(self, vec: FeatureVector, base_scores: Dict[str, dict]) -> Dict[str, object]:
        if not self.grok_api_key:
            return {
                "enabled": False,
                "used": False,
                "reason": "GROK_API_KEY not set; using local heuristic only.",
            }

        payload = {
            "model": self.grok_model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a behavioral-state scorer. Return ONLY valid JSON with keys: "
                        "stress, cognitive_load, engagement, trust_in_ai, confidence_adjustment, llm_explanation. "
                        "Each state key must contain: level(low/medium/high), score(0..1), probability(0..1). "
                        "Use provided feature signal and baseline scores. Do not output markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "features": vec.values,
                            "baseline_scores": base_scores,
                            "task": "Refine estimates and explain strongest indicators.",
                        }
                    ),
                },
            ],
        }

        req = request.Request(
            f"{self.grok_base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "terminal_stress_ai/1.0",
            },
        )
        try:
            with request.urlopen(req, timeout=12) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8")
            except Exception:
                detail = str(exc)
            return {
                "enabled": True,
                "used": False,
                "reason": f"{self.provider.upper()} HTTP {exc.code}: {detail[:240]}",
            }
        except (error.URLError, TimeoutError, ValueError) as exc:
            return {
                "enabled": True,
                "used": False,
                "reason": f"{self.provider.upper()} call failed: {exc}",
            }

        try:
            content = raw["choices"][0]["message"]["content"]
            llm = json.loads(content)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            return {
                "enabled": True,
                "used": False,
                "reason": f"Grok response parse failed: {exc}",
            }

        return {
            "enabled": True,
            "used": True,
            "reason": f"{self.provider.upper()} enrichment applied.",
            "result": llm,
        }

    @staticmethod
    def explain_indicators(vec: FeatureVector) -> List[str]:
        f = vec.values
        indicators: List[str] = []
        if f["pause_1500ms_count"] > 3:
            indicators.append("Frequent long pauses (>1500 ms)")
        if f["backspace_ratio"] > 0.15:
            indicators.append("High correction behavior (backspace ratio)")
        if f["override_rate"] > 0.5:
            indicators.append("High AI suggestion override rate")
        if f["typing_cpm"] < 120:
            indicators.append("Lower typing speed than typical active editing")
        if f["hesitation_count"] > 4:
            indicators.append("Repeated hesitation pattern in inter-key gaps")
        if f.get("content_intensity_mean", 0.0) > 0.6:
            indicators.append("High emotional intensity detected in typed content")
        if f.get("profanity_event_rate", 0.0) > 0.3:
            indicators.append("Frequent profanity/hostile wording patterns observed")
        if f.get("insult_event_rate", 0.0) > 0.3:
            indicators.append("Direct insulting language detected in recent interaction")
        if max(f.get("distrust_event_rate", 0.0), f.get("distrust_recent", 0.0)) > 0.3:
            indicators.append("Explicit distrust language detected toward AI output")
        if not indicators:
            indicators.append("Behavioral indicators are within stable range")
        return indicators


def model_version() -> str:
    return "heuristic_v4_grok_optional_with_ml_stress"
