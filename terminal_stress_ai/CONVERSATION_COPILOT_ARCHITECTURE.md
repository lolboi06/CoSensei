# ContextFlow Conversation-Aware Copilot Layer

## New modules

- `app/conversation_memory_manager.py`
  - stores session-based conversation history
  - stores code memory and task context
  - methods:
    - `add_user_message()`
    - `add_ai_response()`
    - `get_recent_context()`
    - `get_last_generated_code()`

- `app/suggestion_generator.py`
  - produces context-aware code suggestions
  - uses:
    - detected user intent
    - recent conversation memory
    - code memory
    - task context
    - user preferences
  - supports:
    - template-based generation
    - follow-up modification using previous code memory

## Updated pipeline

1. User Input
2. Conversation Memory Manager
3. Behavior Monitoring
4. Feature Extraction
5. Trust Engine
6. Risk Analyzer
7. SharedAutonomyAllocator
8. AutonomyExplanationModule
9. SuggestionGenerator
10. Action Manager
11. Output / Execution

## Context-aware behavior

Example:

- first user input:
  - `make a C++ program to add numbers`
- later user input:
  - `now modify it to use a function`

The generator reads `code_memory.last_generated_code` and rewrites the previous code instead of starting from scratch.

## Output extension

The response now includes:

```json
{
  "conversation_memory": {
    "session_id": "user1",
    "conversation_history": [
      {"role": "user", "content": "make a C++ program to add numbers"},
      {"role": "assistant", "content": "This suggestion gives you a minimal working implementation that matches the detected task.", "code": "#include <iostream> ..."}
    ],
    "code_memory": {
      "language": "cpp",
      "last_generated_code": "#include <iostream> ..."
    },
    "task_context": {
      "language": "cpp",
      "file_type": "cpp",
      "intent": {"task": "writing_new_code", "confidence": 0.74}
    }
  },
  "suggestion": {
    "language": "cpp",
    "code": "#include <iostream> ...",
    "explanation": "This suggestion gives you a minimal working implementation that matches the detected task.",
    "source": "template"
  }
}
```

## New route

- `GET /memory/{session_id}`

Returns the latest structured conversation memory for the session.
