from __future__ import annotations

from typing import Dict


class UserControlLayer:
    """Applies explicit user controls on suggestion count, verification, and autonomy."""

    DEFAULTS = {
        "autonomy_mode": None,
        "suggestion_count": 3,
        "verification_level": "balanced",
    }

    def resolve(self, user_settings: Dict[str, object] | None = None) -> Dict[str, object]:
        resolved = dict(self.DEFAULTS)
        if user_settings:
            resolved.update({k: v for k, v in user_settings.items() if v is not None})
        resolved["suggestion_count"] = max(1, min(int(resolved["suggestion_count"]), 5))
        return resolved

    def override_autonomy(self, computed_mode: str, user_settings: Dict[str, object]) -> str:
        requested = user_settings.get("autonomy_mode")
        if requested in {"AUTO_EXECUTE", "SUGGEST_ONLY", "REQUIRE_APPROVAL"}:
            return str(requested)
        return computed_mode
