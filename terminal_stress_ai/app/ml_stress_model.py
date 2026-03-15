from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


class MLStressModel:
    """Optional ML stress scorer with heuristic fallback.

    If scikit-learn and a saved model are available, it uses them.
    Otherwise it falls back to deterministic weights so the runtime stays usable.
    """

    def __init__(self, model_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.model_path = model_path or (root / "data" / "stress_model.json")
        self.joblib_path = root / "data" / "stress_model.joblib"
        self.model = None
        self.backend = "heuristic"
        self._load()

    def _load(self) -> None:
        if self.joblib_path.exists():
            try:
                import joblib  # type: ignore

                self.model = joblib.load(self.joblib_path)
                self.backend = "sklearn_joblib"
                return
            except Exception:
                self.model = None
                self.backend = "heuristic"
        if not self.model_path.exists():
            return
        try:
            payload = json.loads(self.model_path.read_text(encoding="utf-8"))
        except Exception:
            return
        if payload.get("type") == "linear_weights":
            self.model = payload
            self.backend = "json_linear"

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def predict(self, features: Dict[str, float], heuristic_score: float) -> float:
        if self.backend == "sklearn_joblib" and self.model is not None:
            try:
                ordered = [
                    float(features.get("typing_cpm", 0.0)),
                    float(features.get("iki_mean", 0.0)),
                    float(features.get("pause_500ms_count", 0.0)),
                    float(features.get("backspace_ratio", 0.0)),
                    float(features.get("override_rate", 0.0)),
                    max(float(features.get("content_intensity_mean", 0.0)), float(features.get("content_intensity_recent", 0.0))),
                    float(features.get("caps_ratio_mean", 0.0)),
                    float(features.get("hesitation_count", 0.0)),
                ]
                if hasattr(self.model, "predict_proba"):
                    proba = self.model.predict_proba([ordered])[0]
                    if len(proba) >= 2:
                        return self._clip(float(proba[-1]))
                prediction = self.model.predict([ordered])[0]
                return self._clip(float(prediction))
            except Exception:
                return self._clip(heuristic_score)
        if self.backend == "json_linear" and self.model:
            weights = self.model.get("weights", {})
            bias = float(self.model.get("bias", 0.0))
            score = bias
            for key, weight in weights.items():
                score += float(weight) * float(features.get(key, 0.0))
            return self._clip(score)
        return self._clip(heuristic_score)

    def metadata(self) -> Dict[str, str]:
        return {"backend": self.backend}
