# ContextFlow User Preference Modeling Architecture

## Pipeline position

The persistent preference layer now sits after trust/risk inference and before survey validation:

1. `capture_terminal.py`
2. `app/features.py`
3. `app/behavior_trust_bridge.py`
4. `app/trust_engine.py`
5. `app/risk_analyzer.py`
6. `app/user_preference_engine.py`
7. `app/model.py`
8. `app/survey_validation.py`
9. `app/main.py`

## Module design

New module:

- `app/user_preference_engine.py`

Responsibilities:

- persist one session summary per `session_id`
- aggregate summaries across sessions for a `user_id`
- learn a behavioral baseline after the first few sessions
- infer stable user preferences
- compute per-session deviations from baseline
- recommend adaptive AI behavior

Current terminal integration uses `session_id` as `user_id`. If a separate user identity is introduced later, the engine is already designed around a dedicated `user_id` field.

## SQLite storage

Database:

- `data/contextflow_profiles.sqlite3`

Tables:

```sql
CREATE TABLE session_summaries (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    typing_cpm REAL NOT NULL,
    pause_mean REAL NOT NULL,
    backspace_ratio REAL NOT NULL,
    hesitation_rate REAL NOT NULL,
    accept_rate REAL NOT NULL,
    override_rate REAL NOT NULL,
    trust_score REAL NOT NULL,
    stress_score REAL NOT NULL,
    engagement_score REAL NOT NULL,
    load_score REAL NOT NULL,
    content_intensity REAL NOT NULL,
    summary_json TEXT NOT NULL
);

CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    session_count INTEGER NOT NULL,
    baseline_typing_cpm REAL NOT NULL,
    baseline_pause_mean REAL NOT NULL,
    baseline_backspace_ratio REAL NOT NULL,
    baseline_hesitation_rate REAL NOT NULL,
    ai_accept_rate REAL NOT NULL,
    override_rate REAL NOT NULL,
    trust_baseline_score REAL NOT NULL,
    trust_baseline TEXT NOT NULL,
    typical_stress_level REAL NOT NULL,
    interaction_style TEXT NOT NULL,
    preferred_ai_behavior TEXT NOT NULL,
    profile_json TEXT NOT NULL
);
```

## Baseline learning logic

The first `3` sessions are treated as the baseline learning phase.

Baseline metrics are the mean across stored session summaries:

- `baseline_typing_cpm`
- `baseline_pause_mean`
- `baseline_backspace_ratio`
- `baseline_hesitation_rate`
- `ai_accept_rate`
- `override_rate`
- `trust_baseline_score`
- `typical_stress_level`

Trust baseline level:

- `low` if score `< 0.33`
- `medium` if score `< 0.66`
- `high` otherwise

## Preference inference rules

Interaction style:

- `fast_typist` if `baseline_typing_cpm >= 300`
- `reflective_typist` if `baseline_typing_cpm <= 170` or `baseline_pause_mean >= 380`
- `balanced_typist` otherwise

AI usage pattern:

- `high_acceptance` if `ai_accept_rate >= 0.75`
- `high_override` if `override_rate >= 0.4`
- `mixed_acceptance` otherwise

Editing behavior:

- `heavy_editor` if `baseline_backspace_ratio >= 0.12`
- `low_editing` if `baseline_backspace_ratio <= 0.05`
- `moderate_editing` otherwise

Trust profile:

- `high_trust_user` if `trust_baseline_score >= 0.7`
- `low_trust_user` if `trust_baseline_score <= 0.45`
- `calibrated_trust_user` otherwise

Automation preference:

- `require_confirmation` for high-override or low-trust users
- `auto_accept_suggestions` for high-trust, high-acceptance users
- `suggestion_review_mode` otherwise

Preferred AI behavior:

- `concise_suggestions` for fast typists
- `explanation_first` for low-trust users
- `draft_then_refine` for heavy editors
- `balanced_guidance` otherwise

## Baseline deviation analysis

For each session, the engine compares current behavior against the stored profile:

- `typing_cpm_delta`
- `pause_mean_delta`
- `backspace_ratio_delta`
- `hesitation_rate_delta`
- `trust_score_delta`
- `stress_score_delta`

Derived deviation flags:

- `abnormal_stress`
- `increased_cognitive_load`
- `increased_distrust`
- `unusual_typing_behavior`

## Integration in `app/main.py`

After the trust and risk stages:

```python
preference_data = PREFERENCE_ENGINE.update_user_profile(
    user_id=session_id,
    session_id=session_id,
    features=vec.values,
    trust_signals=trust_data["signals"],
    scores=scores,
)
```

The response is extended with:

- `user_profile`
- `user_preferences`
- `baseline_delta_analysis`
- `baseline_learning`

## Example output

```json
{
  "user_profile": {
    "user_id": "user1",
    "session_count": 4,
    "baseline_typing_cpm": 241.2,
    "baseline_pause_mean": 318.7,
    "baseline_backspace_ratio": 0.047,
    "baseline_hesitation_rate": 0.9,
    "ai_accept_rate": 0.79,
    "override_rate": 0.14,
    "trust_baseline_score": 0.72,
    "trust_baseline": "high",
    "typical_stress_level": 0.41,
    "interaction_style": "fast_typist",
    "preferred_ai_behavior": "concise_suggestions"
  },
  "user_preferences": {
    "interaction_style": "fast_typist",
    "ai_usage_pattern": "high_acceptance",
    "editing_behavior": "low_editing",
    "trust_profile": "high_trust_user",
    "automation_preference": "auto_accept_suggestions",
    "preferred_ai_behavior": "concise_suggestions"
  },
  "baseline_delta_analysis": {
    "typing_cpm_delta": 0.12,
    "pause_mean_delta": 0.05,
    "backspace_ratio_delta": -0.11,
    "hesitation_rate_delta": 0.02,
    "trust_score_delta": -0.18,
    "stress_score_delta": 0.24,
    "deviations": ["abnormal_stress"]
  },
  "baseline_learning": {
    "in_learning_phase": false,
    "sessions_observed": 4,
    "minimum_sessions": 3
  }
}
```

## Adaptive AI behavior

The preference engine contributes additional system actions:

- reduce suggestion frequency for cautious users
- shorten responses for fast typists
- show explanations for low-trust users
- switch to review-first mode when distrust rises above baseline
- lower autonomy when stress rises above the learned norm
