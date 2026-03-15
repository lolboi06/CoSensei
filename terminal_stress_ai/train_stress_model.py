from __future__ import annotations

import json
from pathlib import Path


FEATURE_ORDER = [
    "typing_cpm",
    "iki_mean",
    "pause_500ms_count",
    "backspace_ratio",
    "override_rate",
    "emotional_intensity",
    "caps_ratio",
    "hesitation_count",
]


def _synthetic_rows() -> tuple[list[list[float]], list[float]]:
    rows = [
        [420, 140, 0, 0.01, 0.00, 0.05, 0.02, 0],
        [360, 180, 1, 0.02, 0.05, 0.10, 0.05, 0],
        [280, 240, 2, 0.05, 0.10, 0.15, 0.10, 1],
        [220, 320, 4, 0.08, 0.20, 0.25, 0.20, 2],
        [180, 420, 6, 0.12, 0.35, 0.40, 0.35, 3],
        [140, 520, 8, 0.18, 0.50, 0.60, 0.55, 4],
        [120, 610, 10, 0.22, 0.70, 0.80, 0.75, 5],
    ]
    labels = [0, 0, 0, 0, 1, 1, 1]
    return rows, labels


def train() -> None:
    root = Path(__file__).resolve().parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    rows, labels = _synthetic_rows()

    try:
        import joblib  # type: ignore
        from sklearn.ensemble import GradientBoostingClassifier  # type: ignore

        model = GradientBoostingClassifier(random_state=42)
        model.fit(rows, labels)
        joblib.dump(model, data_dir / "stress_model.joblib")
        metadata = {
            "backend": "sklearn_joblib_gradient_boosting_classifier",
            "feature_order": FEATURE_ORDER,
            "samples": len(rows),
        }
        (data_dir / "stress_model_meta.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"Saved sklearn model to {data_dir / 'stress_model.joblib'}")
        return
    except Exception as exc:
        print(f"scikit-learn training unavailable ({exc}); writing linear fallback artifact.")

    fallback = {
        "type": "linear_weights",
        "weights": {
            "typing_cpm": -0.0005,
            "iki_mean": 0.0012,
            "pause_500ms_count": 0.025,
            "backspace_ratio": 0.35,
            "override_rate": 0.30,
            "content_intensity_mean": 0.25,
            "content_intensity_recent": 0.25,
            "caps_ratio_mean": 0.12,
            "hesitation_count": 0.04,
        },
        "bias": 0.05,
        "feature_order": FEATURE_ORDER,
    }
    (data_dir / "stress_model.json").write_text(json.dumps(fallback, indent=2), encoding="utf-8")
    print(f"Saved fallback model to {data_dir / 'stress_model.json'}")


if __name__ == "__main__":
    train()
