# CoSensei - Dual-AI Architecture

## Overview

**CoSensei** is a three-tier AI system with dynamic shared control for risk management.

```
┌─────────────────────────────────────────────────────────┐
│         USER (Interactive Terminal)                     │
└──────────────────┬──────────────────────────────────────┘
                   │
     ┌─────────────┴──────────────┐
     │                            │
     v                            v
┌──────────────┐          ┌──────────────────┐
│ Planner AI   │          │ ContextFlow      │
│ (Middle)     │◄────────►│ Controller       │
└──────┬───────┘          └──────────────────┘
       │
       ├─ Clarification Engine
       ├─ Task Context Manager
       ├─ Middle AI (Risk Evaluator)
       │
       v
   ┌──────────────────────────────┐
   │   Risk Assessment + Prompt   │
   │   (Survey + Behavior Data)   │
   └──────────┬───────────────────┘
              │
              v
      ┌──────────────────┐
      │ Generator AI     │
      │ (Solution Gen.)  │
      └────────┬─────────┘
               │
               ├─ 3 Distinct Solutions
               ├─ Risk-Weighted
               ├─ User Selects (SHARED_CONTROL)
               │
               v
         IMPLEMENTATION
```

---

## Three-Tier Architecture

### Layer 1: Planner AI (MIDDLE)
**Job**: Collect requirements, analyze behavior, evaluate risk

**Components**:
- `EnhancedClarificationEngine` - Explains options, provides defaults
- `TaskContextManager` - Persistent context storage (no repeated questions)
- `MiddleAIPlannerEngine` - Risk evaluation + prompt creation

**Output**: Structured prompt with risk assessment for Generator AI

**Code Flow**:
```python
user_behavior = extract_behavioral_signals(events)
survey_data = extract_survey_responses(nasa_tlx, trust_survey)
task_context = load_from_persistent_memory(session_id)

risk_assessment = MIDDLE_AI.calculate_risk_factors(
    task_context,
    user_behavior,
    survey_data
)

prompt = MIDDLE_AI.create_prompt_for_generator(
    task_context,
    risk_assessment,
    user_behavior,
    user_risk_inputs  # User adjusts some risks dynamically
)
```

### Layer 2: Generator AI
**Job**: Generate three distinct solution strategies based on Middle AI prompt

**Input**: Prompt from Middle AI (includes risk level, constraints)

**Output**: Three solutions that respect risk assessment

**Code Flow**:
```python
solutions = GENERATOR_AI.generate_solutions(prompt_from_middle_ai)

# Solutions always differ structurally:
# 1. Simple (MVP, minimal code)
# 2. Optimized (best practices, balanced)
# 3. Scalable (enterprise, distributed)
```

### Layer 3: ContextFlow Controller
**Job**: Respect autonomy restrictions and manage risk

**Controls**:
- `SUGGEST_ONLY` - Show three solutions, wait for user selection
- `HUMAN_CONTROL` - Require user approval for each risk factor
- `SHARED_CONTROL` - User adjusts contextual risk factors dynamically
- `AUTO_EXECUTE` - Generate implementation without confirmation

**Dynamic Shared Control Example**:
```
Middle AI calculates risk factors:

SYSTEM-CALCULATED (non-negotiable):
  - stress_level: 0.75
  - distrust_signals: 0.2
  - technical_complexity: 0.6

USER-ADJUSTABLE (SHARED_CONTROL):
  - project_complexity: ??? (user knows best)
  - time_pressure: ??? (only user has deadline)
  - team_capacity: ??? (only user knows team)

System asks user:
  "How complex is your project? (1=simple, 10=massive)"
  User: "5"
  
  "Any time pressure? (1=relaxed, 10=urgent)"
  User: "8"
  
  "Team experience level? (1=new, 10=expert)"
  User: "3"

Middle AI recalculates overall risk with user inputs.
Generator AI adjusts solution recommendations.
```

---

## Data Flow Example

### Scenario: "I need to build a web app"

#### Step 1: Planner Collects & Clarifies
```
User: "i want to build a web app"
Planner asks (with explanations):
  "What platform? (responsive works on all devices)"
  User: "responsive"
  ✓ Saved to TaskContextManager
  
  "Programming language?"
  User: "python"
  ✓ Saved to TaskContextManager
  
  "Framework?"
  User: "flask"
  ✓ Saved
```

#### Step 2: Middle AI Analyzes Risk
```
Behavioral Analysis:
  - User stress: 0.6 (medium)
  - Corrections: 0.08 (minimal), suggesting confidence
  - Hesitation: low
  - Overall behavioral flags: NONE

Survey Data:
  - Mental demand: 60/100
  - Frustration: 25/100
  - Trust in AI: 4/5
  
Technical Context:
  - Site type: "web app" → moderate complexity
  - Platform: "responsive" → medium performance demand
  - Language: "python" → rich ecosystem
  
Risk Factors Calculated:
  - Behavioral risk: 0.35 (low-medium)
  - Technical risk: 0.45 (medium)
  - Overall: 0.40 (MEDIUM)
```

#### Step 3: Middle AI Asks for User Risk Input (SHARED_CONTROL)
```
System: "Quick risk calibration before solutions:"
  1. How complex is this project? (1-10) _____
  2. Time pressure? (1=relaxed, 10=urgent) _____
  3. Team experience? (1=new, 10=expert) _____

User answers:
  1. 4 (simple project)
  2. 6 (moderate deadline)
  3. 2 (small team, new)
  
Recalculated Overall Risk: 0.48 (MEDIUM-HIGH)
```

#### Step 4: Generator AI Creates Solutions
```
Middle AI Prompt to Generator:
{
  "task_context": {
    "site_type": "web_app",
    "language": "python",
    "framework": "flask",
    "database": "sqlite"
  },
  "overall_risk_score": 0.48,
  "risk_level": "MEDIUM-HIGH",
  "recommended_strategy": "optimized",
  "strategy_reasoning": "Medium-high risk: new team + moderate deadline. 
                         Avoid complexity but ensure reliability.",
  "solution_constraints": {
    "implementation_scope": "MODERATE - core features + polish",
    "technology_stack": "BALANCED - proven frameworks",
    "team_structure": "SMALL - 2-3 developers"
  }
}

Generator produces:

1. Simple Implementation
   MVP with core features only. 1-2 weeks.
   
2. Optimized Architecture ✓ RECOMMENDED
   Production-ready with best practices. 4-8 weeks.
   
3. Scalable Architecture
   Enterprise-grade. 12-16 weeks.
   (Not recommended due to team size + deadline)
```

#### Step 5: User Selects Solution
```
User: "2" (Optimized)

System:
✓ Confirmed: Optimized Architecture selected
  
Generating implementation package...
  - System architecture diagram
  - Folder structure
  - Starter code
  - Technology stack summary
```

---

## Risk Factor Categories

### Behavioral Risks (System-Calculated)
These are **detected by ContextFlow**, not negotiable:
- **User stress level** - From behavioral signals
- **Cognitive overload** - From pauses, hesitation
- **Distrust indicators** - From correction frequency
- **Uncertainty** - From backspace ratio

### Contextual Risks (User-Adjusted via SHARED_CONTROL)
These require **user knowledge**, adjustable:
- **Project complexity** - "How big is this really?"
- **Time pressure** - "What's the deadline?"
- **Scope clarity** - "How clear is the goal?"
- **Team capacity** - "What's our team like?"

### Technical Risks (System-Calculated)
These are **inferred from task context**, non-negotiable:
- **Scalability required** - From site type (e-commerce needs scale)
- **Security criticality** - From site type (shopping = high security)
- **Performance criticality** - From platform (mobile needs optimization)

---

## Autonomy Modes & Shared Control

### SUGGEST_ONLY (Default)
- Show three solutions
- User selects strategy
- Proceed to implementation
- ✓ Respects user expertise

### HUMAN_CONTROL  
- Show risk assessment
- User approves/adjusts each factor
- Show solutions
- User selects strategy
- ✓ Maximum transparency

### SHARED_CONTROL ← **Recommended**
- System calculates derived risks
- User adjusts contextual risks (project complexity, deadline, team)
- System recalculates overall risk
- Show solutions with adjusted risk level
- User selects strategy
- ✓ Balances automation + user control

### AUTO_EXECUTE
- Generate implementation automatically
- No user selection needed
- ✓ Fastest, but requires high trust

---

## Benefits

✓ **No Repeated Questions** - TaskContextManager persists answers
✓ **Smart Clarification** - Enhanced explanations + defaults  
✓ **Risk-Aware Solutions** - Adjusted for behavioral + contextual + technical risk
✓ **User Control** - Adjust risk factors that only you know
✓ **Conversational AI** - Explains reasoning, never condescending
✓ **ContextFlow Safe** - Respects autonomy restrictions
✓ **Three Distinct Options** - Always generates structurally different solutions

---

## Implementation Status

✓ **Planner AI**:
  - EnhancedClarificationEngine (conversational questions)
  - TaskContextManager (persistent memory)
  - MiddleAIPlannerEngine (risk evaluation)

✓ **Generator AI**:
  - GeneratorAI (three solutions)
  - Risk-weighted recommendations
  - Architecture templates

✓ **ContextFlow Integration**:
  - Respects autonomy modes
  - Inline status display
  - Shared control for risk factors

✓ **Status Display**:
  - Real-time trust/risk/autonomy
  - Behavioral guidance
  - Risk assessment report

---

## User Experience Flow

```
1. User: "I want to build X"
   ↓
2. System (Planner): Explains options briefly, asks questions
   "Is this a web app? (interactive with user accounts)"
   ↓
3. System: Suggests defaults if answer is vague
   User: "web"
   System: "I'll use responsive design - works on all devices"
   ↓
4. System (Middle AI): Analyzes behavior + risk factors
   ↓
5. System: Asks user about contextual risks they know best
   "How complex? (1=simple, 10=massive)"
   ↓
6. System (Generator): Creates 3 solutions, risk-weighted
   ✓ Recommended: Solution 2 (Optimized)
   ↓
7. User: "2"
   ↓
8. System: Generates full implementation package
   - Architecture
   - Folder structure
   - Starter code
   - Stack summary
```

---

## Next Steps

1. **Restart server** to load new modules
2. **Test conversation** with full clarification flow
3. **Select solution** and see implementation
4. **Monitor trust/risk/autonomy** status in real-time

```bash
cd terminal_stress_ai
py run_all.py --session user_demo --reset
```

---

**System Ready**: All dual-AI components integrated
**Status**: Production Ready
**Autonomy Control**: SHARED_CONTROL (Recommended)
