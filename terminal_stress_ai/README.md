# Terminal Stress AI Estimator (Free/Open Source)

A research/hackathon-friendly system that estimates:
- Stress Level
- Cognitive Load
- Engagement Level
- Trust/Vigilance toward AI suggestions

from keyboard interaction behavior in terminal workflows.

## Free technologies
- Python 3.x standard library only

## Architecture
1. `capture_terminal.py` records keystroke timing (`gap_ms`), pauses, backspace behavior, and suggestion action (`accept/override/none`).
2. Server (`app/main.py`) stores event windows per session.
3. Feature extraction (`app/features.py`) computes behavioral features.
4. Model (`app/model.py`) estimates 4 continuous scores and maps them to low/medium/high + probability.
5. `app/adaptive_copilot_pipeline.py` runs the adaptive copilot flow:
   `Conversation Memory -> Cognitive State -> Task Understanding -> Shared Autonomy -> Explanation -> Suggestion -> Safe Action Execution -> Policy Learning`.
6. Server returns structured analysis, memory layers, autonomy decisions, action workflow state, and indicator explanations.

## Adaptive Copilot Output
`GET /analysis/{session_id}` now returns:
- `conversation_memory`: short-term conversation context plus working-memory task context
- `task_memory`: active task, generated code, reasoning trace, recent suggestions
- `user_profile_memory`: persistent trust history, interaction patterns, success metrics, preferences
- `cognitive_state`: stress, cognitive load, engagement, trust level, frustration index, autonomy readiness
- `task_understanding`: continuity-aware task classification and retrieved code context
- `shared_autonomy`: autonomy mode, score, confidence, smoothing state, policy shape
- `shared_autonomy_explanation`: natural-language explanation of the autonomy choice
- `suggestion`: structured suggestion payload for code, edits, debugging, or explanations
- `action_manager`: safe execution decision with confirmation and audit state
- `policy_learning`: acceptance, override, trust change, and policy adjustment metrics

## Run in terminal (PowerShell)
```powershell
cd "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\terminal_stress_ai"
py train_model.py
# Optional Grok integration:
$env:GROK_API_KEY="your_key_here"
$env:GROK_MODEL="grok-3-mini"
# Optional only if you need a non-default endpoint:
# $env:GROK_BASE_URL="https://api.x.ai/v1"
py app\main.py
```

In a second terminal:
```powershell
cd "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\terminal_stress_ai"
py capture_terminal.py --session user1
```

## One-command start (server + client)
```powershell
cd "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\terminal_stress_ai"
py run_all.py --session user1
```

With Grok key:
```powershell
py run_all.py --session user1 --grok-api-key "your_key_here" --grok-model "grok-3-mini"
```

Require LLM to be valid before interactive session starts:
```powershell
py run_all.py --session user1 --require-llm
```

After first run, key is saved locally and you can start with:
```powershell
py run_all.py --session user1
```

Tune reliability thresholds in same command (works in cmd.exe and PowerShell):
```powershell
py run_all.py --session user1 --min-events-indicators 1 --min-events-trend 5
```

## Use as module (single function)
```python
from run_all import run_session

run_session(
    session="user1",
    require_llm=True,
    min_events_indicators=5,
    min_events_trend=10,
)
```

## API endpoints
- `GET /health`
- `GET /llm-test`
- `POST /events`
- `POST /survey/{session_id}`
- `GET /profile/{user_id}`
- `GET /autonomy-debug/{session_id}`
- `GET /memory/{session_id}`
- `GET /analysis/{session_id}`
- `GET /session/{session_id}/timeline`
- `POST /session/{session_id}/reset`

## Post-session validation
- `run_all.py` can now collect the NASA-TLX and trust survey in the same terminal after the interaction ends.
- It also prints the latest autonomy debug snapshot before shutdown.

## Design Notes
- Trust and risk architecture: `TRUST_RISK_ARCHITECTURE.md`
- Persistent user preference modeling: `USER_PREFERENCE_ARCHITECTURE.md`
- Adaptive Copilot-style controller: `COPILOT_CONTROLLER_ARCHITECTURE.md`
- Autonomy decision and action control: `AUTONOMY_ACTION_ARCHITECTURE.md`
- Shared autonomy control layer: `SHARED_AUTONOMY_ARCHITECTURE.md`
- Conversation-aware copilot layer: `CONVERSATION_COPILOT_ARCHITECTURE.md`
- Full adaptive copilot architecture: `ADAPTIVE_COPILOT_ARCHITECTURE.md`
