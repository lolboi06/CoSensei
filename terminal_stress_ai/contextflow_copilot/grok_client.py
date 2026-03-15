from __future__ import annotations

import json
import os
from typing import Dict, Optional
from urllib import error, request


class GrokClient:
    """Minimal Grok/xAI chat client using stdlib only."""

    def __init__(self, *, api_key_env: str, model_env: str, default_model: str = "grok-3-mini") -> None:
        self.api_key_env = api_key_env
        self.model_env = model_env
        self.default_model = default_model

    def enabled(self) -> bool:
        return bool(self._api_key())

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> Optional[Dict[str, object]]:
        api_key = self._api_key()
        if not api_key:
            return None

        payload = {
            "model": os.getenv(self.model_env, self.default_model).strip(),
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = request.Request(
            f"{self._base_url()}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "contextflow_copilot/1.0",
            },
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            content = raw["choices"][0]["message"]["content"]
            return json.loads(content)
        except (error.HTTPError, error.URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
            return None

    def complete_text(self, *, system_prompt: str, user_prompt: str) -> Optional[str]:
        api_key = self._api_key()
        if not api_key:
            return None

        payload = {
            "model": os.getenv(self.model_env, self.default_model).strip(),
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = request.Request(
            f"{self._base_url()}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "contextflow_copilot/1.0",
            },
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            return str(raw["choices"][0]["message"]["content"]).strip()
        except (error.HTTPError, error.URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
            return None

    def _api_key(self) -> str:
        return os.getenv(self.api_key_env, "").strip() or os.getenv("GROK_API_KEY", "").strip()

    @staticmethod
    def _base_url() -> str:
        return os.getenv("GROK_BASE_URL", "https://api.x.ai/v1").strip().rstrip("/")
