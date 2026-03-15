# ContextFlow Trust And Risk Architecture

## System architecture

ContextFlow processes each terminal interaction through these stages:

1. `capture_terminal.py`
   - Captures keystroke timing, pauses, corrections, suggestion interaction, and content cues.
   - Emits event batches to the local analysis server.

2. `app/features.py`
   - Extracts behavioral features from raw events.
   - Produces a `FeatureVector` containing timing, correction, hesitation, and content-intensity features.

3. `app/model.py`
   - Computes heuristic state estimates:
     - stress
     - cognitive_load
     - engagement
     - trust_in_ai
   - Optionally merges Grok/xAI or Groq enrichment when available.

4. `app/behavior_trust_bridge.py`
   - Converts session events + extracted features into trust-oriented signals:
     - accept_rate
     - usage_frequency
     - correction_rate
     - override_rate
     - session_success

5. `app/trust_engine.py`
   - Computes `trust_score`, `trust_level`, and trust reasoning.

6. `app/risk_analyzer.py`
   - Computes `risk_flags`
   - Determines `interaction_scenario`
   - Returns `autonomy_policy`
   - Generates safety actions

7. `app/survey_validation.py`
   - Stores NASA-TLX and trust survey responses per session
   - Computes validation error against predicted stress/load/trust
   - Returns a model accuracy summary

8. `app/main.py`
   - Orchestrates the full pipeline
   - Extends the structured JSON response
   - Preserves compatibility with the existing session analysis flow

## Python module structure

- `app/features.py`
- `app/model.py`
- `app/trust_engine.py`
- `app/behavior_trust_bridge.py`
- `app/risk_analyzer.py`
- `app/survey_validation.py`
- `app/main.py`
- `capture_terminal.py`
- `run_all.py`

## Trust Engine implementation

`app/trust_engine.py` provides:

- `calculate_trust(signals)`
- `update_trust(event, intensity=1.0)`
- `get_trust_level(score=None)`

Trust formula:

```python
score = (
    accept_rate * 0.5
    + usage_frequency * 0.2
    - correction_rate * 0.2
    - override_rate * 0.2
    + session_success * 0.1
)
score = clamp(score, 0.0, 1.0)
```

Trust levels:

- `HIGH` if score `> 0.75`
- `MEDIUM` if score `>= 0.5`
- `LOW` otherwise

Example:

```python
from app.trust_engine import TrustEngine, InteractionSignals

engine = TrustEngine()
result = engine.calculate_trust(
    InteractionSignals(
        accept_rate=0.82,
        usage_frequency=0.74,
        correction_rate=0.12,
        override_rate=0.08,
        session_success=0.77,
    )
)
print(result)
```

## Risk Analyzer implementation

`app/risk_analyzer.py` provides one main integration method:

```python
analyze(scores, features, quality, trust_engine_score)
```

It evaluates:

- hostile language
- profanity / insults
- excessive capitalization
- emotional intensity
- high stress
- high cognitive load
- distrust toward AI

Example returned structure:

```python
{
    "risk_flags": ["hostile_language_detected", "high_emotional_intensity"],
    "interaction_scenario": "hostile_or_distrustful",
    "autonomy_policy": {
        "mode": "require_human_approval",
        "reason": "High-risk interaction detected",
    },
    "safety_actions": [
        "Switch to approval-first mode for all critical actions.",
        "Show shorter, safer suggestions with explicit rationale.",
    ],
}
```

## Existing pipeline integration

`app/main.py` integrates the modules per user comment:

1. Extracts `FeatureVector` from the current session event buffer.
2. Computes state scores through `StateModel`.
3. Computes trust through `BehaviorTrustBridge` -> `TrustEngine`.
4. Computes risk and autonomy through `RiskAnalyzer`.
5. Optionally loads stored survey ratings and validates predictions through `SurveyValidationEngine`.
6. Merges everything into the structured output.

Core integration points already active in the current server:

- `trust_engine`
- `trust_engine_signals`
- `risk_flags`
- `interaction_scenario`
- `autonomy_policy`
- `adaptive_recommendations`
- `validation`

## Survey validation module

`app/survey_validation.py` provides:

- `NasaTlxSurvey`
- `TrustSurvey`
- `SurveyValidationEngine`

Storage:

- SQLite database at `data/contextflow_validation.sqlite3`

Schema:

```sql
CREATE TABLE session_surveys (
    session_id TEXT PRIMARY KEY,
    nasa_tlx_json TEXT NOT NULL,
    trust_json TEXT NOT NULL,
    nasa_tlx_score REAL NOT NULL,
    trust_rating REAL NOT NULL
);
```

NASA-TLX:

- mental_demand
- physical_demand
- temporal_demand
- performance
- effort
- frustration

Each is stored on a 0-100 scale and averaged into `nasa_tlx`.

Trust survey:

- trust_ai_suggestions
- ai_reliable
- comfortable_relying_on_ai

Each is stored on a 1-5 Likert scale and averaged into `trust_rating`.

Validation algorithm:

```python
nasa_norm = nasa_tlx_score / 100.0
trust_norm = (trust_rating - 1.0) / 4.0

stress_error = abs(predicted_stress - nasa_norm)
load_error = abs(predicted_load - nasa_norm)
trust_error = abs(predicted_trust - trust_norm)

model_accuracy = 1.0 - ((stress_error + load_error + trust_error) / 3.0)
```

Example survey submission payload:

```json
{
  "nasa_tlx": {
    "mental_demand": 70,
    "physical_demand": 10,
    "temporal_demand": 60,
    "performance": 55,
    "effort": 75,
    "frustration": 65
  },
  "trust": {
    "trust_ai_suggestions": 4,
    "ai_reliable": 3,
    "comfortable_relying_on_ai": 4
  }
}
```

Example validation output:

```json
{
  "validation": {
    "survey_scores": {
      "nasa_tlx": 55.833,
      "trust_rating": 3.667
    },
    "model_comparison": {
      "stress_error": 0.042,
      "cognitive_load_error": 0.055,
      "trust_error": 0.031
    },
    "model_accuracy": 0.957
  }
}
```

## Structured output extension

Current extended response shape includes:

```json
{
  "stress": {"level": "medium", "score": 0.57, "probability": 0.61},
  "cognitive_load": {"level": "low", "score": 0.28, "probability": 0.53},
  "engagement": {"level": "high", "score": 0.73, "probability": 0.55},
  "trust_in_ai": {"level": "medium", "score": 0.53, "probability": 0.64},
  "trust_engine": {
    "trust_score": 0.37,
    "trust_level": "LOW",
    "reason": "low correction rate and high session success"
  },
  "risk_flags": ["hostile_language_detected"],
  "interaction_scenario": "hostile_or_distrustful",
  "autonomy_policy": {
    "mode": "require_human_approval",
    "reason": "High-risk interaction detected"
  }
}
```

## Integration strategy

- Keep `FeatureVector` as the shared contract across behavioral, trust, and risk modules.
- Keep `TrustEngine` independent from UI/runtime concerns.
- Keep `RiskAnalyzer` policy-focused and stateless.
- Let `main.py` remain the single orchestration point for session analysis.
- Continue using the existing event capture and JSON output pipeline without breaking compatibility.
