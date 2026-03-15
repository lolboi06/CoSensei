from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List


@dataclass
class FeatureVector:
    values: Dict[str, float]


FEATURE_ORDER = [
    "iki_mean",
    "iki_std",
    "pause_500ms_count",
    "pause_1500ms_count",
    "typing_cpm",
    "backspace_ratio",
    "override_rate",
    "hesitation_count",
    "content_intensity_mean",
    "profanity_event_rate",
    "insult_event_rate",
    "exclamation_rate",
    "caps_ratio_mean",
    "distrust_event_rate",
    "distrust_recent",
    "content_intensity_recent",
]


def _safe_mean(arr: List[float]) -> float:
    if not arr:
        return 0.0
    return float(sum(arr) / len(arr))


def _safe_std(arr: List[float]) -> float:
    if not arr:
        return 0.0
    mean = _safe_mean(arr)
    variance = sum((x - mean) ** 2 for x in arr) / len(arr)
    return float(math.sqrt(variance))


def extract_features(events: List[dict]) -> FeatureVector:
    if not events:
        return FeatureVector({k: 0.0 for k in FEATURE_ORDER})

    gaps = [float(e.get("gap_ms", 0.0)) for e in events if e.get("gap_ms") is not None]
    backspaces = sum(1 for e in events if e.get("key") == "Backspace")
    char_keys = sum(1 for e in events if e.get("event_type") == "keydown" and isinstance(e.get("key"), str) and len(e.get("key")) == 1)

    overrides = sum(1 for e in events if e.get("suggestion_action") == "override")
    accepts = sum(1 for e in events if e.get("suggestion_action") == "accept")
    total_suggestions = overrides + accepts

    hesitation_count = 0
    for g in gaps:
        if g > 1200:
            hesitation_count += 1

    total_duration_min = max((sum(gaps) / 1000.0) / 60.0, 1e-6)
    typing_cpm = char_keys / total_duration_min
    line_events = [e for e in events if e.get("key") == "Enter" and e.get("line_text") is not None]
    line_count = max(len(line_events), 1)
    intensity_values = [float(e.get("content_intensity", 0.0)) for e in line_events]
    profanity_values = [1.0 if float(e.get("profanity_count", 0)) > 0 else 0.0 for e in line_events]
    insult_values = [1.0 if float(e.get("insult_count", 0)) > 0 else 0.0 for e in line_events]
    exclamation_values = [float(e.get("exclamation_count", 0)) for e in line_events]
    caps_values = [float(e.get("caps_ratio", 0.0)) for e in line_events]
    distrust_values = [float(e.get("distrust_intent", 0.0)) for e in line_events]
    distrust_recent = float(line_events[-1].get("distrust_intent", 0.0)) if line_events else 0.0
    intensity_recent = float(line_events[-1].get("content_intensity", 0.0)) if line_events else 0.0

    feats = {
        "iki_mean": _safe_mean(gaps),
        "iki_std": _safe_std(gaps),
        "pause_500ms_count": float(sum(1 for g in gaps if g > 500)),
        "pause_1500ms_count": float(sum(1 for g in gaps if g > 1500)),
        "typing_cpm": float(typing_cpm),
        "backspace_ratio": float(backspaces / max(char_keys, 1)),
        "override_rate": float(overrides / max(total_suggestions, 1)),
        "hesitation_count": float(hesitation_count),
        "content_intensity_mean": _safe_mean(intensity_values),
        "profanity_event_rate": float(sum(profanity_values) / line_count),
        "insult_event_rate": float(sum(insult_values) / line_count),
        "exclamation_rate": float(sum(exclamation_values) / line_count),
        "caps_ratio_mean": _safe_mean(caps_values),
        "distrust_event_rate": float(sum(distrust_values) / line_count),
        "distrust_recent": distrust_recent,
        "content_intensity_recent": intensity_recent,
    }
    return FeatureVector(feats)


def feature_list(vector: FeatureVector) -> List[float]:
    return [vector.values[k] for k in FEATURE_ORDER]
