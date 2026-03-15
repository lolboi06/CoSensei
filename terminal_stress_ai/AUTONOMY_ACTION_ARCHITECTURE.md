# ContextFlow Autonomy Decision And Action Manager

## New runtime stages

The live pipeline now extends from behavioral analysis into execution control:

1. User Interaction
2. Behavior Capture
3. Feature Extraction
4. Trust Engine
5. Risk Analyzer
6. User Preference Engine
7. Autonomy Decision Engine
8. Action Manager
9. Structured Output

## `app/autonomy_decision_engine.py`

Inputs:

- stress score
- cognitive load score
- trust score
- engagement score
- risk flags
- override rate
- user preference profile
- code/task context

Outputs:

- `mode`
  - `auto_execute`
  - `require_confirmation`
  - `suggest_only`
  - `approval_required`
- `reason`
- `suggestion_frequency`
- `explanation_mode`
- `priority`
- `task_complexity`

Policy behavior:

- low trust or hostile interaction -> `approval_required`
- high load or high complexity -> `suggest_only`
- high override or confirmation-oriented profile -> `require_confirmation`
- high trust + low risk + stable state -> `auto_execute`

An optional `joblib` model can be dropped in later for ML policy selection. If absent, the runtime uses the rule-based engine.

## `app/action_manager.py`

Inputs:

- autonomy decision
- proposed assistant action
- optional command preview

Outputs:

- `status`
- `action`
- `execution_mode`
- `undo_available`
- `rollback_supported`
- `human_in_loop`
- `reason`

Guardrails:

- blocks destructive command patterns
- never auto-executes unsafe command previews
- logs every action decision to `data/action_manager.log`
- keeps rollback/human oversight fields explicit

## Example output

```json
{
  "autonomy_decision": {
    "mode": "require_confirmation",
    "reason": "User preference or override behavior indicates manual checkpointing.",
    "suggestion_frequency": "low",
    "explanation_mode": true,
    "priority": "high",
    "policy_backend": "rule_based",
    "task_complexity": 0.68
  },
  "action_manager": {
    "status": "awaiting_user_confirmation",
    "action": "insert_code_snippet",
    "execution_mode": "require_confirmation",
    "undo_available": false,
    "rollback_supported": true,
    "human_in_loop": true,
    "reason": "User confirmation required before execution."
  }
}
```
