# Dynamic Clarification Generator - Integration Guide

## Overview

The **Dynamic Clarification Generator** replaces static, hardcoded question templates with a semantic analysis approach that generates unique clarification questions based on the actual user prompt.

### Problem Solved
- ❌ OLD: Always ask the same 5 questions, slightly tweaked per domain
- ✅ NEW: Ask only the questions that are actually relevant to this specific task

## How It Works

### 1. **Semantic Analysis**
The generator analyzes keywords in the user's prompt to identify which categories of clarification are needed:

```
User: "Build a web app for tracking tasks"
       ↓
Detected: interface ([web], platform), scope (build), data (tasks=persistence)
       ↓
Questions: "What platforms?" "How big?" "Do you need storage?"
```

### 2. **Dynamic Question Generation**
Instead of templates, questions are selected based on what's actually relevant:

| User Input | Detected | Questions Generated |
|---|---|---|
| "Build a web app" | interface, scope | Platform? Tech stack? |
| "Analyze customer data" | data, scope, audience | Data format? Scale? Who uses it? |
| "Write a bash script" | timeline, constraints | Timeline? OS? Error handling? |
| "Help me" | (nothing) | Scope? Tech? Platform? |

### 3. **Context Extraction**
Once user provides answers, the system extracts key information:

```python
answers = ["Python", "AWS", "PostgreSQL", "<100ms latency"]
         ↓
context = {
    "preferred_technology": "python",
    "target_platform": "aws",
    "needs_persistence": True,
    "performance_requirement": "high"
}
```

## Integration Points

### For Middle AI (Decision Router)

```python
from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR

# Step 1: Analyze incoming user prompt
analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(user_prompt)

# Step 2: If ambiguous, ask for clarification
if len(analysis['relevant_categories']) < 2:  # Too vague
    clarification = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(
        user_prompt, analysis
    )
    return {"status": "needs_clarification", "prompt": clarification}

# Step 3: If clear, extract answers and build context
else:
    context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
        user_prompt, analysis, user_answers
    )
    return {"status": "ready", "context": context}
```

### For Generator AI (Decision Making)

```python
from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR

# Extract the dynamically-generated context
context = request.context
categories_detected = context.get('relevant_categories', [])

# Use detected categories to inform routing
if 'interface' in categories_detected:
    route_to_ui_service()
elif 'data' in categories_detected:
    route_to_data_service()
elif 'integration' in categories_detected:
    route_to_api_service()
else:
    route_to_general_service()
```

## Clarification Categories

The system uses 10 semantic categories:

| Category | Keywords | Example Questions |
|----------|----------|-------------------|
| **scope** | build, create, make, design | What exactly? MVP or full? |
| **audience** | user, customer, who | Who's using this? Tech level? |
| **technology** | tech, language, framework | Preferred tech? Stack constraints? |
| **data** | database, storage, persist | Need data storage? How much? |
| **interface** | UI, web, mobile, desktop | Platforms? UI framework? |
| **performance** | fast, scale, concurrent | Performance targets? Latency? |
| **security** | secure, auth, encrypt | Security needs? Authentication? |
| **integration** | API, third-party, connect | External integrations? Services? |
| **timeline** | deadline, asap, when | Timeline? Blocking other work? |
| **constraints** | must, should, cannot | Hard requirements? Avoid what? |

## API Reference

### `analyze_prompt(user_prompt: str) → Dict`
Analyzes user prompt and returns detected categories and questions.

```python
result = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt("Build a web app")
# {
#   "relevant_categories": ["scope", "interface", "technology"],
#   "questions": ["What exactly do you want...?", "What platforms...?", ...],
#   "num_questions": 3,
#   "category_scores": {"interface": 1, "scope": 1, "technology": 0, ...}
# }
```

### `generate_clarification_prompt(user_prompt: str, analysis: Dict) → str`
Generates a conversational clarification prompt with numbered questions.

```python
prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(
    "Build a web app", analysis
)
# Returns formatted prompt with questions
```

### `extract_answers_from_response(response_text: str, num_questions: int) → Dict`
Extracts answers from user's freeform response (numbered or paragraph).

```python
answers = DYNAMIC_CLARIFICATION_GENERATOR.extract_answers_from_response(
    "1. Python\n2. React\n3. PostgreSQL",
    num_questions=3
)
# {"answer_1": "Python", "answer_2": "React", "answer_3": "PostgreSQL"}
```

### `build_context_from_answers(user_prompt: str, analysis: Dict, answers: Dict) → Dict`
Builds a context dictionary suitable for downstream AI services.

```python
context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
    user_prompt="Build a web app",
    analysis=analysis,
    answers=answers
)
# {
#   "original_request": "Build a web app",
#   "relevant_categories": [...],
#   "preferred_technology": "python",
#   "target_platform": "web",
#   ...
# }
```

## Usage Examples

See `example_dynamic_clarification.py` for:
- Web applications
- Data analysis projects
- API backends
- Bash scripts
- Mobile apps
- Vague requests
- Answer extraction workflow

Run with:
```bash
python -m app.example_dynamic_clarification
```

## Benefits for Multiple AIs

### For Codex/Claude (Generator AI)
- **Richer Context**: Gets semantic information about what matters for this task
- **Better Routing**: Knows which domain service to use based on detected categories
- **Adaptable**: Works for any task type, not just predefined domains

### For Middle AI (Router/Decision Engine)
- **Smart Decisions**: Can decide whether to ask for clarification based on detected ambiguity
- **Progressive Disclosure**: Asks only relevant follow-ups, not a fixed list
- **Extract Intent**: Understands user intent from minimal input

### For External AI Services
- **Structured Context**: Receives well-formed context with extracted metadata
- **No Hardcoding**: Service doesn't need domain-specific logic
- **Extensible**: New categories can be added without touching downstream services

## Extending the System

### Add New Category

```python
# In DynamicClarificationGenerator.__init__()
"ml_model": {
    "keywords": ["model", "train", "ai", "neural", "algorithm"],
    "questions": [
        "What's your data size and quality?",
        "Do you need real-time predictions?",
    ]
}
```

### Customize Questions

```python
# Modify specific questions
generator = DYNAMIC_CLARIFICATION_GENERATOR
generator.clarification_categories["data"]["questions"][0] = "Your custom question?"
```

### Add Context Extraction Logic

```python
# In build_context_from_answers()
if "gpu" in response_text.lower():
    context["requires_gpu"] = True
```

## Testing

```bash
cd terminal_stress_ai
python -m app.example_dynamic_clarification  # See all examples

# Or programmatically:
from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR

analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt("Your prompt")
print(analysis)
```

## Configuration

No external configuration needed. The generator is self-contained and works out-of-the-box for any domain.

To adjust behavior:
- **More questions**: Increase limit in `analyze_prompt()` from 4 to 5
- **Fewer questions**: Decrease from 4 to 3
- **Different scoring**: Modify keyword matching logic in `analyze_prompt()`
- **Custom follow-ups**: Change which questions are selected per category
