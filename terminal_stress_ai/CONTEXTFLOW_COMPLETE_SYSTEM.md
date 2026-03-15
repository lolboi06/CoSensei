# CoSensei Dual-AI System - Complete Implementation

## 📋 Overview

CoSensei is a **behavior-aware dual-AI copilot system** that dynamically adapts its autonomy level based on user cognitive state and interaction patterns.

The system demonstrates how two AI models can collaborate:
- **AI #1 (Planner AI)**: Clarifies requirements, builds context, verifies solutions
- **AI #2 (Generator AI)**: Creates three distinct solution strategies

The system uses behavioral analysis to maintain human control while enabling safe AI automation.

---

## 🏗️ System Architecture

### Two-AI Pipeline

```
User Input
    ↓
Behavioral Analysis (stress, engagement, trust tracking)
    ↓
AI #1: Planner
├─ Analyzes clarity level
├─ Generates clarification questions (if needed)
└─ Builds structured task context
    ↓
AI #2: Generator
├─ Creates Solution 1: Simple Implementation
├─ Creates Solution 2: Optimized Architecture  
└─ Creates Solution 3: Scalable Enterprise Architecture
    ↓
AI #1: Verifier
└─ Scores and ranks solutions
    ↓
ContextFlow Controller
├─ Estimates user stress/engagement/trust
├─ Decides autonomy mode
└─ Applies safety constraints
    ↓
Autonomy Modes:
• AUTO_EXECUTE: Run without asking
• SHARED_CONTROL: Show options, ask for selection
• SUGGEST_ONLY: Generate suggestions only
• HUMAN_CONTROL: Require explicit approval
    ↓
User Selection & Implementation
```

---

## 📁 Key Components

### 1. **Planner AI** (`planner_ai.py`)
- **Purpose**: Requirements analysis and context building
- **Key Methods**:
  - `analyze_user_input()`: Detects clarity level and categories
  - `generate_clarification_questions()`: Creates smart questions based on missing info
  - `build_task_context()`: Structures answers into task JSON
  - `verify_solutions()`: Scores solutions against requirements

### 2. **Generator AI** (`generator_ai.py`)
- **Purpose**: Solution strategy generation
- **Key Methods**:
  - `generate_solutions()`: Creates three structurally different approaches
  - Strategy 1: **Simple Implementation** (monolithic, fast, low cost)
  - Strategy 2: **Optimized Architecture** (layered, cached, production-ready)
  - Strategy 3: **Scalable Architecture** (microservices, enterprise-grade)

### 3. **CoSensei Coordinator** (`contextflow_coordinator.py`)
- **Purpose**: Orchestrates the full pipeline
- **Key Classes**:
  - `CoSenseiController`: Main system logic
  - `CoSenseiSession`: Interactive terminal interface

### 4. **Autonomy Decision Engine** (`autonomy_decision_engine_v2.py`)
- **Purpose**: Determines AI autonomy level
- **Factors**:
  - Task clarity (0-1)
  - User stress (0-1)
  - Engagement level (0-1)
  - Trust level (0-1)
  - Risk classification (LOW/MEDIUM/HIGH)

### 5. **Dynamic Clarification Generator** (`dynamic_clarification_generator.py`)
- **Purpose**: Semantic analysis without LLM (pure Python)
- **Features**:
  - 10 semantic categories
  - Keywords extraction
  - Dynamic question generation
  - Answer parsing and context building

---

## 🚀 Running the System

### Installation

```bash
cd "C:\Users\Sam Roger\OneDrive\Documents\ContextFlow\terminal_stress_ai"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies (if needed)
pip install requests
```

### Start Interactive Session

```bash
python app/contextflow_coordinator.py
```

### Example Interaction

```
================================================================================
COSENSEI COPILOT - Behavior-Aware AI System
================================================================================

Hello. I'm CoSensei Copilot, a behavior-aware AI assistant.
I analyze your interaction patterns to adapt my autonomy level.

Tell me what you want to build, fix, or understand.

Status: 
  Trust: 🟢 50.0%
  Stress: 🟢 0.0%
  Autonomy: SUGGEST_ONLY
  Mode: SHARED_CONTROL

================================================================================

You: I want to build an ecommerce website

I need a bit more information to generate the best solution.

  1. What type of site? (ecommerce/saas/blog/landing page)
  2. What platform? (mobile-first/desktop/responsive)
  3. What programming language? (python/java/javascript)
  4. What database? (postgresql/mysql/mongodb/sqlite)
  5. Any specific integrations needed? (payment/email/analytics)

You: mobile-first, python, fastapi, postgresql, payment integration

======================================================================
SOLUTION STRATEGIES
======================================================================

1. SIMPLE IMPLEMENTATION
   Monolithic FastAPI application with PostgreSQL database and basic REST endpoints.
   • Effort: Low (1-2 weeks)
   • Scalability: Low

2. OPTIMIZED ARCHITECTURE ⭐ RECOMMENDED
   Layered FastAPI backend with service layer, caching, and responsive frontend.
   • Effort: Medium (3-4 weeks)
   • Scalability: Medium

3. SCALABLE ARCHITECTURE
   Microservice-ready FastAPI backend with API gateway, PostgreSQL, and container deployment.
   • Effort: High (6-8 weeks)
   • Scalability: Enterprise

Select a solution (1/simple, 2/optimized, 3/scalable):

You: 2

======================================================================
IMPLEMENTATION: OPTIMIZED ARCHITECTURE
======================================================================

## SYSTEM ARCHITECTURE

[Load Balancer]
        |
        v
[FASTAPI API Server] <--> [Redis Cache]
        |
        v
[Service Layer]
        |
        v
[PostgreSQL Database]

Features: Caching, Services, Error Handling, Logging

## TECH STACK

• Backend: fastapi
• Database: postgresql
• Cache: redis
• Frontend: react
• Deployment: docker
```

---

## 🎯 Autonomy Modes Explained

### 1. **AUTO_EXECUTE**
- AI makes decisions and executes automatically
- **Activated When**: High clarity + low stress + high trust + low risk
- **Use Case**: Repeated, well-understood tasks

### 2. **SHARED_CONTROL**
- AI shows multiple options; user selects
- **Activated When**: Medium conditions across all factors
- **Use Case**: Most common development scenarios

### 3. **SUGGEST_ONLY**
- AI generates suggestions; requires user decision
- **Activated When**: High stress OR low clarity OR low trust
- **Use Case**: Complex decisions, stressed users

### 4. **HUMAN_CONTROL**
- AI requests approval before each action
- **Activated When**: HIGH risk detected
- **Use Case**: Production systems, payment processing, critical data

---

## 🧠 Behavioral Analysis

The system tracks:
- **Typing patterns**: Keystroke timing
- **Pauses**: Duration > 1 second
- **Backspace usage**: Indicates indecision/stress
- **Engagement**: Number of interactions
- **Trust**: Solution acceptance rate

These signals inform autonomy decisions.

---

## 🔧 Solution Generation Strategy

### Solution 1: Simple Implementation
- Single deployed unit
- Basic REST API
- Embedded database or simple hosted DB
- Perfect for: MVPs, prototypes, learning

### Solution 2: Optimized Architecture (RECOMMENDED)
- Layered design
- Caching layer
- Service pattern
- Professional structure
- Perfect for: Production applications, small teams

### Solution 3: Scalable Architecture
- Microservices ready
- API Gateway
- Distributed systems
- Enterprise deployment
- Perfect for: Large-scale systems, many teams

---

## 📊 Verification Logic

After generating solutions, **Planner AI verifies**:
1. **Correctness**: Solutions match requirements
2. **Alignment**: Tech stack fits constraints
3. **Risk**: Potential issues identified
4. **Completeness**: All requirements covered

Each solution gets a score (0-1), and the highest-scoring solution is marked as recommended.

---

## 🔐 Safety & Control

All AI actions are controlled by the CoSensei autonomy layer:
- ✅ User stress monitored → autonomy reduced
- ✅ Task clarity checked → clarifications generated
- ✅ Trust tracked → autonomy increases over time
- ✅ Risk assessed → human approval required for high-risk tasks
- ✅ All decisions logged for audit trail

---

## 📝 Session Memory

The system maintains session context to avoid repeated questions:

```python
session_context = {
    "project_type": "ecommerce",
    "site_type": "ecommerce",
    "target_platform": "mobile-first",
    "language": "python",
    "framework": "fastapi",
    "database": "postgresql",
    "features": ["product catalog", "shopping cart", "checkout"],
    "categories": ["web", "ecommerce", "mobile"],
    "keywords": ["build", "website", "shopping", "mobile"]
}
```

If user is asked a question they've already answered, the system uses the cached answer.

---

## 🎓 Learning Outcomes

This system demonstrates:
1. **Dual-AI Architecture**: Two models working together
2. **Behavior Analysis**: HSHow to track and use behavioral signals
3. **Dynamic Autonomy**: Adapting control based on context
4. **Safe Automation**: Maintaining human control while enabling AI
5. **Session State**: Managing context across interactions
6. **Solution Verification**: Ranking options for users

---

## 🚦 Example Scenarios

### Scenario 1: Stressed User
- High backspace count + many pauses
- CoSensei → switches to SUGGEST_ONLY
- Shows one recommendation instead of three options
- Reduces cognitive load

### Scenario 2: Clear Requirements
- High task clarity (all categories covered)
- Low risk level
- CoSensei → can use SHARED_CONTROL or AUTO_EXECUTE
- Faster feedback loop

### Scenario 3: High-Risk Task
- Payment processing detected
- Production database flagged
- CoSensei → forces HUMAN_CONTROL
- All actions await explicit approval

---

## 📈 Extending the System

To add new capabilities:

1. **Add Semantic Category**: Update `dynamic_clarification_generator.py`
2. **Add New Solution Type**: Extend `generator_ai.py`
3. **Modify Autonomy Logic**: Update `autonomy_decision_engine_v2.py`
4. **Add Behavioral Signals**: Extend `CoSenseiController._track_input_behavior()`

---

## ✅ Design Principles

- **User-Centric**: Respects user's cognitive capacity
- **Transparent**: Status shown in every response
- **Safe**: High-risk actions require approval
- **Efficient**: Never asks for information twice
- **Intelligent**: Adapts to user patterns
- **Auditable**: All decisions can be reviewed

---

## 🤝 The CoSensei Advantage

Unlike systems that always show three solutions (template-based), ContextFlow:
- ✅ Shows ONE option if user is stressed
- ✅ Skips clarification if context exists
- ✅ Adapts recommendations based on risk
- ✅ Tracks user patterns across sessions
- ✅ Respects autonomy constraints

This creates a genuinely Behavior-Aware AI Copilot.

---

## Commands Reference

| Command | Effect |
|---------|--------|
| `1` or `simple` | Select Simple Implementation |
| `2` or `optimized` | Select Optimized Architecture |
| `3` or `scalable` | Select Scalable Architecture |
| `exit` | End session |
| `quit` | End session |

---

## Status Indicators

```
🟢 Green:   Optimal (0-33%)
🟡 Yellow:  Caution (33-66%)
🔴 Red:     Alert (66-100%)
```

---

**ContextFlow v1.0 - Behavior-Aware AI Copilot**
