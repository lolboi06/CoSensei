from __future__ import annotations

from typing import Dict, List


class SuggestionQualityTracker:
    def analyze(self, events: List[dict], features: Dict[str, float]) -> Dict[str, float]:
        line_events = [e for e in events if e.get("key") == "Enter" and e.get("line_text") is not None]
        shown = len(line_events)
        accepted = sum(1 for e in line_events if e.get("suggestion_action") == "accept")
        rejected = sum(1 for e in line_events if e.get("suggestion_action") == "override")
        modified = sum(1 for e in line_events if int(e.get("backspace_count", 0)) > 0)
        if shown == 0:
            shown = 1
        quality = (
            (accepted / shown) * 0.5
            + (1.0 - min(1.0, modified / shown)) * 0.2
            + (1.0 - min(1.0, rejected / shown)) * 0.2
            + (1.0 - min(1.0, float(features.get("backspace_ratio", 0.0)))) * 0.1
        )
        return {
            "suggestions_shown": max(0, len(line_events)),
            "suggestions_accepted": accepted,
            "suggestions_modified": modified,
            "suggestions_rejected": rejected,
            "suggestion_quality_score": round(max(0.0, min(1.0, quality)), 3),
        }
