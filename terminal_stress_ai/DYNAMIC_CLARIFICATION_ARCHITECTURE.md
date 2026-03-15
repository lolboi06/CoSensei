# Dynamic Clarification in AI Architecture

## System Overview

```
User Input
    ↓
[Dynamic Clarification Generator] ← NEW: Semantic analysis of user prompt
    ↓
[Middle AI - Decision Router] ← Decides: routes to handler or asks clarification
    ↓
[Generator AI - Task Handler] ← Gets rich context, no hardcoding needed
```

## Data Flow

### Before (Static Approach)
```
User: "Build a web app"
     ↓
Router: "This is probably web/UI domain, ask template questions 1-5"
     ↓
Same 5 questions for: web, mobile, desktop, api, game projects
     ↓
Generator: "I got these answers... I guess this is a web project?"
```

### After (Dynamic Approach)
```
User: "Build a web app"
     ↓
[Analyze] Detect: interface, scope, technology
[Generate] Questions: "Platforms?" "MVP or full?" "Tech stack?"
     ↓
Middle AI: "Request is clear enough on these 3 categories"
     ↓
Generator AI gets context: {
    "relevant_categories": ["interface", "scope", "technology"],
    "target_platform": "web",
    "project_scale": "medium",
    "preferred_technology": "python",
    "needs_persistence": true
}
```

## Integration with Middle AI

Middle AI is the decision router - it should use DCG like this:

```python
# middle_ai/decision_router.py

from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR

class MiddleAIRouter:
    def route_request(self, user_prompt):
        # Step 1: Analyze what clarity is needed
        analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(user_prompt)
        
        # Step 2: Decide: clarify or proceed?
        if len(analysis['relevant_categories']) < 2:
            # Too vague - ask for clarification
            clarification_prompt = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(
                user_prompt, analysis
            )
            return {
                "action": "clarify",
                "prompt": clarification_prompt,
                "analysis_id": id(analysis)
            }
        
        # Step 3: User provided (or implied) answers - extract context
        context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
            user_prompt, analysis, self.extract_user_answers(user_prompt)
        )
        
        # Step 4: Route to appropriate generator service
        return {
            "action": "route",
            "service": self.select_service(context),
            "context": context
        }
    
    def select_service(self, context):
        """Select which Generator AI service handles this."""
        categories = context.get('relevant_categories', [])
        
        if 'interface' in categories:
            if context.get('target_platform') == 'web':
                return "generator_web"
            elif context.get('target_platform') == 'mobile':
                return "generator_mobile"
            else:
                return "generator_ui"
        
        if 'data' in categories:
            return "generator_data_analysis"
        
        if 'integration' in categories:
            return "generator_api"
        
        if 'security' in categories:
            return "generator_security"
        
        return "generator_general"
```

## Integration with Generator AI

Generator AI services receive rich semantic context:

```python
# generator_ai/web_service.py

class WebProjectGenerator:
    def generate(self, context):
        """
        context = {
            "original_request": "Build a web app for task tracking",
            "relevant_categories": ["interface", "scope", "data"],
            "target_platform": "web",
            "project_scale": "medium",
            "needs_persistence": True,
            "preferred_technology": "python",
            "timeline": "short",
            ... (more extracted facts)
        }
        """
        
        # No need to guess - we have real information
        framework = self.select_framework(context)  # Not hardcoded
        storage = self.select_storage(context)      # Based on data needs
        deployment = self.select_deployment(context) # Based on scale
        
        return self.generate_full_project(framework, storage, deployment)
    
    def select_framework(self, context):
        """Select tech based on actual detected preference, not template."""
        tech = context.get('preferred_technology')
        scale = context.get('project_scale')
        
        if tech == 'python':
            return 'fastapi' if scale == 'large' else 'flask'
        elif tech == 'javascript':
            return 'nextjs' if scale == 'large' else 'express'
        # ... etc
```

## Context Structure

### Semantic Context
```python
{
    # Global
    "original_request": str,
    "relevant_categories": List[str],  # e.g., ["interface", "data", "security"]
    "_task_type": "dynamic",
    "_clarification_dynamic": True,
    
    # Extracted from analysis & answers
    "preferred_technology": str,  # "python", "javascript", etc
    "target_platform": str,       # "web", "mobile", "desktop", "api"
    "project_scale": str,         # "small", "medium", "large", "enterprise"
    "timeline": str,              # "urgent", "short", "medium", "flexible"
    "needs_persistence": bool,
    "needs_authentication": bool,
    
    # Raw answers
    "answers": Dict[str, str]     # Answer 1, 2, 3, ...
}
```

### Benefits of This Structure
- **No Hardcoding**: Generator AI doesn't have domain-specific conditionals
- **Extensible**: New fields can be added without breaking existing code
- **Semantic**: Contains actual meaning (not just raw answers)
- **Traceable**: Can see which questions led to which conclusions

## Usage Patterns

### Pattern 1: Quick Routing
```python
def route_user_request(prompt):
    analysis = analyze(prompt)
    
    if len(analysis['relevant_categories']) >= 2:
        context = build_context(prompt, analysis)
        return route_to_service(context)
    else:
        return ask_clarification(analysis)
```

### Pattern 2: Progressive Clarification
```python
user_input = "Build an app"
analysis = analyze(user_input)  # Detects: nothing specific

# Ask about: technology, interface, scope
clarifications = generate_questions(analysis)
user_answers = ask_user(clarifications)

analysis2 = enhance_analysis(analysis, user_answers)  # Evolves analysis
context = build_context_from_answers(user_input, analysis2, user_answers)

# Now route with better information
return route_to_service(context)
```

### Pattern 3: Multi-AI Pipeline
```
User: "Build a web app"
    ↓
Middle AI: Analyzes, decides not enough info, asks questions
    ↓
User: "React frontend, Node backend, PostgreSQL"
    ↓
Middle AI: Builds context with detected: ["interface", "data", "integration"]
    ↓
Generator AI (UI): "I see React + web + modern scale"
    ↓
Generator AI (Backend): "I see Node + API + moderate data"
    ↓
Generator AI (Data): "I see PostgreSQL + relational + persistence"
```

## Comparison: Template vs Dynamic

| Aspect | Template Approach | Dynamic Approach |
|--------|-------------------|-----------------|
| Questions | 5 fixed per domain | 3-5 based on content |
| Domains | 6 predefined | Unlimited |
| New AI? | Must add domain | Works automatically |
| Context | Generic | Semantic + extracted |
| Extensibility | Hard (hardcoded) | Easy (add keywords) |
| User Experience | Repetitive | Personalized |

## When Dynamic Clarification Should Be Used

✅ **USE**: Multi-AI systems where clarification varies by domain
✅ **USE**: Services that handle diverse task types
✅ **USE**: Systems where you want progressive refinement
✅ **USE**: AI routers that need to make intelligent decisions

❌ **SKIP**: Single-domain specialized services
❌ **SKIP**: Real-time systems with strict latency (overhead: ~1ms)
❌ **SKIP**: When clarifications are always the same (template is fine)

## Summary

The Dynamic Clarification Generator enables **semantic-aware AI workflows** where:

1. Each request is understood contextually (not pattern-matched)
2. Clarifications are targeted (not template-based)
3. Multiple AI services receive rich context (not generic templates)
4. The system scales to new domains (not hardcoded)
5. User experience is personalized (not repetitive)

This makes it ideal for complex, multi-AI systems that need to adapt intelligently to diverse task types.
