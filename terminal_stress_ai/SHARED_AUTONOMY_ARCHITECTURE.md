# ContextFlow Shared Autonomy Control Layer

## Control levels

The system now supports these shared-autonomy levels:

- `AI_FULL`
  - AI executes safe actions automatically
- `AI_ASSIST`
  - AI suggests and may auto-complete low-risk actions
- `SHARED_CONTROL`
  - AI suggests actions, explains reasoning, and waits for the human
- `HUMAN_CONTROL`
  - AI only offers minimal hints and keeps control with the human

## SharedAutonomyAllocator

Module:

- `app/shared_autonomy_allocator.py`

Inputs:

- fused trust score
- stress score
- engagement score
- cognitive load
- suggestion quality
- risk severity
- user preferences
- trust trend

Autonomy score:

```python
autonomy_score = (
    0.4 * trust
    + 0.2 * engagement
    + 0.2 * suggestion_quality
    - 0.2 * stress
    - 0.1 * risk_severity
    - 0.05 * cognitive_load
)
```

Thresholds:

- `> 0.75` -> `AI_FULL`
- `> 0.50` -> `AI_ASSIST`
- `> 0.30` -> `SHARED_CONTROL`
- otherwise -> `HUMAN_CONTROL`

The allocator also:

- computes confidence
- applies smoothing through `DecisionSmoother`
- respects strong user preference constraints

## AutonomyExplanationModule

Module:

- `app/autonomy_explanation_module.py`

Outputs:

- natural-language explanation
- compact signal summary

Example:

```json
{
  "explanation": "Trust is moderate or stress/risk is elevated, so the system will explain suggestions and let the human decide execution.",
  "signal_summary": "trust=0.46, stress=0.62, load=0.48, hostility=0.10, emotional_intensity=0.33"
}
```

## Action manager behavior

Module:

- `app/action_manager.py`

Behavior by shared-autonomy level:

- `AI_FULL`
  - `executed_automatically`
- `AI_ASSIST`
  - `suggestion_displayed`
  - human available, but not always required
- `SHARED_CONTROL`
  - `suggestion_displayed`
  - explanation included
  - human approval required
- `HUMAN_CONTROL`
  - `human_control_only`
  - only hints are allowed

Safety guardrails remain active:

- destructive command blocking
- undo / rollback flags
- logging to `data/action_manager.log`
- human-in-the-loop metadata

## Output extension

Current output now includes:

```json
{
  "shared_autonomy": {
    "autonomy_mode": "SHARED_CONTROL",
    "autonomy_score": 0.44,
    "confidence": 0.72,
    "reason": "Mixed signals support shared control.",
    "decision_smoothing_state": {
      "last_mode": "SHARED_CONTROL",
      "pending_mode": "",
      "safe_streak": 1
    },
    "smoothing_applied": false,
    "suggestion_frequency": "low",
    "explanation_mode": true,
    "priority": "high"
  },
  "shared_autonomy_explanation": {
    "explanation": "Trust is moderate or stress/risk is elevated, so the system will explain suggestions and let the human decide execution.",
    "signal_summary": "trust=0.44, stress=0.63, load=0.51, hostility=0.09, emotional_intensity=0.31"
  },
  "action_manager": {
    "mode": "SHARED_CONTROL",
    "status": "suggestion_displayed",
    "human_required": true
  }
}
```
