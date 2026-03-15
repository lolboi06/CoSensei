# ContextFlow Adaptive Copilot Controller

## Runtime pipeline

ContextFlow now supports a Copilot-style adaptive controller with these stages:

1. User Interaction
2. Behavior Capture
3. Code Context Analyzer
4. Feature Extraction
5. Trust Engine
6. Risk Analyzer
7. User Preference Engine
8. Intent Predictor
9. Adaptive AI Policy Engine
10. Survey Validation
11. Structured Output

## Modules

- `app/code_context_analyzer.py`
  - detects language and file type
  - estimates function length
  - checks lightweight syntax failures
  - tracks recent edit frequency

- `app/suggestion_quality_tracker.py`
  - counts shown / accepted / modified / rejected suggestions
  - computes `suggestion_quality_score`

- `app/intent_predictor.py`
  - predicts:
    - `writing_new_code`
    - `debugging`
    - `refactoring`
    - `exploring_api`

- `app/user_preference_engine.py`
  - stores persistent user baselines
  - updates baseline metrics with moving averages
  - infers stable preference profiles

- `app/adaptive_policy_engine.py`
  - converts trust + state + intent + preferences into:
    - suggestion frequency
    - explanation mode
    - confirmation requirement
    - suggestion length

- `app/ml_stress_model.py`
  - optional ML stress scorer wrapper
  - uses a saved model artifact if present
  - falls back cleanly to heuristic scoring

- `app/system_metrics.py`
  - tracks cross-session controller performance
  - outputs accuracy, acceptance rate, and trust trend

## Output extension

The structured response now includes:

```json
{
  "code_context": {
    "language": "python",
    "file_type": "py",
    "function_length": 42,
    "syntax_errors": 1,
    "compilation_failures": 1,
    "recent_edits": 5
  },
  "suggestion_quality": {
    "suggestions_shown": 8,
    "suggestions_accepted": 5,
    "suggestions_modified": 2,
    "suggestions_rejected": 1,
    "suggestion_quality_score": 0.71
  },
  "user_intent": {
    "task": "debugging",
    "confidence": 0.82
  },
  "adaptive_ai_policy": {
    "suggestion_frequency": "low",
    "explanation_mode": true,
    "confirmation_required": true,
    "suggestion_length": "concise"
  },
  "system_metrics": {
    "prediction_accuracy": 0.81,
    "suggestion_accept_rate": 0.64,
    "user_trust_trend": "increasing"
  }
}
```

## ML stress model note

The runtime wrapper is implemented in `app/ml_stress_model.py`.

Current behavior:

- if a saved model artifact exists at `data/stress_model.json`, it is used
- otherwise the heuristic stress model remains active

This keeps the system deployable in restricted environments while still giving a clear slot for a trained `scikit-learn` model later.
