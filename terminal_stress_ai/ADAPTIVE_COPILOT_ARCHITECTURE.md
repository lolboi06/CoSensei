# ContextFlow Multi-Layer Adaptive Copilot

## Memory layers

Short-term memory:

- `ConversationMemoryManager`
- stores recent user and assistant turns per session

Working memory:

- `TaskMemoryManager`
- stores:
  - active task
  - generated code
  - language
  - recent suggestions
  - reasoning state

Long-term memory:

- `UserProfileMemoryManager`
- stores:
  - user preferences
  - behavioral baseline
  - trust history
  - interaction patterns
  - success metrics

## Cognitive state

Module:

- `CognitiveStateModel`

Outputs:

- stress
- cognitive load
- engagement
- trust level
- frustration index
- autonomy readiness score

## Task continuity

Module:

- `TaskUnderstandingModule`

Tracks task continuity across turns, including:

- `writing_new_code`
- `debugging_code`
- `refactoring_code`
- `asking_for_explanation`
- `editing_previous_code`

If previous code exists and the user asks to modify or update it, the system keeps the task in edit mode instead of resetting to a fresh code-generation task.

## Shared autonomy

Module:

- `SharedAutonomyController`

Wraps the allocator and returns the shared-autonomy level:

- `AI_FULL`
- `AI_ASSIST`
- `SHARED_CONTROL`
- `HUMAN_CONTROL`

## Suggestion engine

Module:

- `SuggestionEngine`

Capabilities:

- generate code snippets
- modify existing code
- suggest debugging strategies
- explain algorithms

Current runtime path:

- template-based generation
- context-aware follow-up using conversation/code memory

## Action execution

Module:

- `ActionExecutionEngine`

Responsibilities:

- map shared-autonomy level to execution behavior
- enforce safety checks
- preserve undo / rollback metadata
- log actions

## Policy learning

Module:

- `PolicyLearningSystem`

Collects:

- suggestion acceptance rate
- override rate
- trust score
- completion success

Returns a coarse policy adjustment signal:

- `increase_autonomy`
- `reduce_autonomy`
- `stable_policy`

## Output additions

The response now includes:

```json
{
  "conversation_memory": {...},
  "task_memory": {...},
  "cognitive_state": {...},
  "task_understanding": {...},
  "shared_autonomy": {...},
  "shared_autonomy_explanation": {...},
  "suggestion": {...},
  "action_manager": {...},
  "policy_learning": {...},
  "user_profile_memory": {...}
}
```
