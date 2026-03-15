from __future__ import annotations

"""
Lightweight placeholder trainer for environments where compiled ML deps are unavailable.

This script generates synthetic behavioral data and prints baseline statistics.
For real ML training, collect labeled data and train with scikit-learn/XGBoost offline.
"""

import random
from statistics import mean


def make_synthetic_scores(n: int = 1000, seed: int = 42) -> list[dict]:
    random.seed(seed)
    rows = []
    for _ in range(n):
        iki_mean = max(40.0, min(1200.0, random.gauss(260, 90)))
        pause_1500 = min(20, max(0, int(random.expovariate(1 / 2))))
        backspace_ratio = random.random() * 0.35
        override_rate = random.random()

        stress = max(0.0, min(1.0, 0.002 * iki_mean + 0.015 * pause_1500 + 0.8 * backspace_ratio + 0.2 * override_rate))
        rows.append({"stress": stress})
    return rows


def main() -> None:
    rows = make_synthetic_scores()
    avg_stress = mean(r["stress"] for r in rows)
    print("Synthetic baseline generated.")
    print("Rows:", len(rows))
    print("Average synthetic stress:", round(avg_stress, 4))
    print("No model file is required; API uses heuristic_v2 scoring.")


if __name__ == "__main__":
    main()