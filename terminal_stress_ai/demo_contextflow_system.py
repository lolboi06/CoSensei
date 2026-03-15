"""
ContextFlow Demonstration Script
Shows the dual-AI system with behavioral analysis and autonomy control
"""

import json
from datetime import datetime


class DemoContextFlow:
    """Interactive demo of ContextFlow system"""
    
    def __init__(self):
        self.session_started = datetime.now()
        self.autonomy_mode = "SUGGEST_ONLY"
        self.user_stress = 0.0
        self.user_trust = 0.5
        self.interaction_count = 0
    
    def demo_scenario_1(self):
        """Scenario 1: Clear Requirements → Fast Track"""
        
        print("\n" + "="*70)
        print("SCENARIO 1: Clear Requirements → Fast Track")
        print("="*70 + "\n")
        
        user_input = "I want to build a mobile ecommerce app in Java with Spring Boot and PostgreSQL"
        print(f"User: {user_input}\n")
        
        # Step 1: Analyze clarity
        clarity = self._analyze_clarity(user_input)
        print(f"✓ Clarity Analysis: {clarity['level']:.0%}")
        print(f"  Found categories: {', '.join(clarity['categories'])}\n")
        
        # Step 2: No clarification needed
        if clarity['level'] > 0.7:
            print("✓ Clarity sufficient - skipping clarification questions\n")
        
        # Step 3: Generate solutions
        self._show_solutions()
        
        # Step 4: Autonomy decision
        self._evaluate_autonomy(clarity['level'], stress=0.2, trust=0.8)
        print(f"✓ Autonomy Mode: {self.autonomy_mode}\n")
    
    def demo_scenario_2(self):
        """Scenario 2: Vague Requirements → Clarification"""
        
        print("\n" + "="*70)
        print("SCENARIO 2: Vague Requirements → Clarification")
        print("="*70 + "\n")
        
        user_input = "I want to build something"
        print(f"User: {user_input}\n")
        
        # Step 1: Analyze clarity
        clarity = self._analyze_clarity(user_input)
        print(f"⚠ Clarity Analysis: {clarity['level']:.0%}")
        print(f"  Found categories: {len(clarity['categories'])} (need >3)\n")
        
        # Step 2: Generate clarification questions
        if clarity['level'] < 0.3:
            print("→ Generating clarification questions:\n")
            questions = [
                "1. What type of project? (website/mobile/desktop/API)",
                "2. What's the primary domain? (ecommerce/social/data/productivity)",
                "3. What platform/language do you prefer?",
                "4. Any specific integrations needed?",
                "5. What's your timeline?"
            ]
            for q in questions:
                print(f"  {q}")
        
        # Simulate user answers
        print("\nUser: ecommerce website, mobile-first, Python, FastAPI, PostgreSQL")
        answers = {
            "type": "ecommerce",
            "platform": "mobile-first",
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql"
        }
        print("(Answers captured)\n")
        
        # Step 3: Generate solutions
        self._show_solutions()
        
        # Step 4: Autonomy decision
        self._evaluate_autonomy(0.8, stress=0.3, trust=0.5)
        print(f"✓ Autonomy Mode: {self.autonomy_mode}\n")
    
    def demo_scenario_3(self):
        """Scenario 3: Stressed User → Simplified View"""
        
        print("\n" + "="*70)
        print("SCENARIO 3: Stressed User → Simplified Output")
        print("="*70 + "\n")
        
        print("User: (typing fast, multiple backspaces, pausing frequently)")
        print("      I want... no wait... build a web app with... hmm...\n")
        
        # Behavioral signals detected
        print("→ Behavioral Signals Detected:")
        print("  • Rapid keystroke/backspace ratio: High")
        print("  • Pause durations: >2 seconds (3 times)")
        print("  • Edit frequency: Multiple corrections")
        print(f"  → Estimated stress level: 0.75 (HIGH)\n")
        
        # Step 1: Despite clarity, respect user state
        print("✓ Task clarity: Moderate (65%)")
        print("✗ User stress: HIGH (75%)")
        print("→ Activating SUGGEST_ONLY mode\n")
        
        self.autonomy_mode = "SUGGEST_ONLY"
        self.user_stress = 0.75
        
        # Step 2: Show only recommended solution
        print("→ Showing SINGLE recommendation:")
        print("""
┌─────────────────────────────────────────────────────────┐
│ RECOMMENDED: Optimized Architecture                    │
│                                                         │
│ • Layered FastAPI backend                              │
│ • PostgreSQL database                                  │
│ • Redis caching                                        │
│ • React/Vue frontend                                   │
│ • Docker deployment                                    │
│                                                         │
│ Timeline: 4-6 weeks                                    │
│ Effort: Medium                                         │
│ Scalability: Medium                                    │
└─────────────────────────────────────────────────────────┘
""")
        
        print("→ Reduced to ONE option (instead of three) to reduce cognitive load")
        print("→ Status indicators hidden to avoid overwhelming user\n")
    
    def demo_scenario_4(self):
        """Scenario 4: High Risk → Human Approval Required"""
        
        print("\n" + "="*70)
        print("SCENARIO 4: Production Payment System → Human Control")
        print("="*70 + "\n")
        
        user_input = "Build a payment processing API with credit card handling"
        print(f"User: {user_input}\n")
        
        # Risk assessment
        print("→ Risk Assessment:")
        print("  ✗ Payment processing detected")
        print("  ✗ Credit card handling")
        print("  ✗ Regulatory compliance required (PCI-DSS)")
        print("  → Risk Level: HIGH\n")
        
        print("⚠ ACTIVATING: HUMAN_CONTROL MODE\n")
        print("All AI actions require explicit human approval\n")
        
        # Show solution with approval step
        print("→ Generated Solution: Microservices Architecture with...")
        print("  • PCI-DSS compliant payment service")
        print("  • Tokenized credit card handling")
        print("  • Encrypted data pipeline")
        print("  • Audit logging")
        print()
        print("⚠ REQUIRE APPROVAL: [approve/reject/modify]")
        print("(Awaiting user decision...)\n")
    
    def demo_scenario_5(self):
        """Scenario 5: Building Trust Over Time"""
        
        print("\n" + "="*70)
        print("SCENARIO 5: Trust Building Across Interactions")
        print("="*70 + "\n")
        
        print("Interaction #1:")
        print("User: Build a blog")
        print("→ Autonomy Mode: SUGGEST_ONLY (new user, unknown trust)")
        print("→ Show 3 solutions\n")
        
        print("User: *selects solution 2*")
        print("Trust +0.2 → Current trust: 0.7\n")
        
        print("Interaction #2:")
        print("User: Add ecommerce features")
        print("→ Autonomy Mode: SHARED_CONTROL (trust improved)")
        print("→ Show quick recommendations\n")
        
        print("User: *accepts recommendation*")
        print("Trust +0.2 → Current trust: 0.9\n")
        
        print("Interaction #3:")
        print("User: Optimize database")
        print("→ Autonomy Mode: AUTO_EXECUTE (high trust, clear request)")
        print("→ Automatically generate and suggest implementation\n")
        
        print("Note: Trust can decrease if:")
        print("  • User rejects multiple solutions")
        print("  • Stress levels spike")
        print("  • Risk situations detected\n")
    
    def _analyze_clarity(self, user_input: str) -> dict:
        """Analyze request clarity"""
        
        keywords = {
            "type": ["build", "create", "make", "develop"],
            "domain": ["ecommerce", "social", "blog", "api", "dashboard"],
            "platform": ["mobile", "web", "desktop", "responsive"],
            "language": ["python", "java", "javascript", "golang", "rust"],
            "framework": ["fastapi", "django", "spring boot", "react", "vue"],
            "database": ["postgresql", "mongodb", "mysql", "sqlite"]
        }
        
        found_categories = 0
        detected = []
        
        for category, words in keywords.items():
            for word in words:
                if word in user_input.lower():
                    found_categories += 1
                    detected.append(category)
                    break
        
        clarity_level = min(found_categories / 3, 1.0)
        
        return {
            "level": clarity_level,
            "categories": list(set(detected))
        }
    
    def _show_solutions(self):
        """Display three solution strategies"""
        
        print("→ Generator AI creating solution strategies:\n")
        
        solutions = [
            {
                "num": 1,
                "name": "Simple Implementation",
                "effort": "1-2 weeks",
                "stack": "Monolithic, basic DB, HTML/CSS/JS"
            },
            {
                "num": 2,
                "name": "Optimized Architecture",
                "effort": "4-6 weeks",
                "stack": "Layered, caching, React/Vue, Docker",
                "recommended": True
            },
            {
                "num": 3,
                "name": "Scalable Enterprise",
                "effort": "8-12 weeks",
                "stack": "Microservices, K8s, multi-region"
            }
        ]
        
        for sol in solutions:
            rec = " ⭐ RECOMMENDED" if sol.get("recommended") else ""
            print(f"{sol['num']}. {sol['name']}{rec}")
            print(f"   Timeline: {sol['effort']}")
            print(f"   Stack: {sol['stack']}\n")
    
    def _evaluate_autonomy(self, clarity: float, stress: float, trust: float):
        """Evaluate autonomy mode"""
        
        self.user_stress = stress
        self.user_trust = trust
        
        if stress > 0.7:
            self.autonomy_mode = "SUGGEST_ONLY"
            reason = "user_stress"
        elif clarity < 0.4:
            self.autonomy_mode = "SUGGEST_ONLY"
            reason = "low_clarity"
        elif trust < 0.3:
            self.autonomy_mode = "SUGGEST_ONLY"
            reason = "low_trust"
        elif clarity > 0.8 and trust > 0.7 and stress < 0.3:
            self.autonomy_mode = "SHARED_CONTROL"
            reason = "optimal_conditions"
        else:
            self.autonomy_mode = "SHARED_CONTROL"
            reason = "balanced"
        
        print(f"→ Autonomy Decision: {self.autonomy_mode}")
        print(f"  Factors: clarity={clarity:.0%}, stress={stress:.0%}, trust={trust:.0%}")
        print(f"  Reason: {reason}")


def main():
    """Run all demo scenarios"""
    
    demo = DemoContextFlow()
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  CONTEXTFLOW DUAL-AI SYSTEM - DEMONSTRATION".center(68) + "█")
    print("█" + "  Behavior-Aware AI Copilot with Dynamic Autonomy Control".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # Run scenarios
    demo.demo_scenario_1()
    input("\nPress Enter to continue to Scenario 2...")
    
    demo.demo_scenario_2()
    input("\nPress Enter to continue to Scenario 3...")
    
    demo.demo_scenario_3()
    input("\nPress Enter to continue to Scenario 4...")
    
    demo.demo_scenario_4()
    input("\nPress Enter to continue to Scenario 5...")
    
    demo.demo_scenario_5()
    
    print("\n" + "="*70)
    print("SYSTEM ARCHITECTURE SUMMARY")
    print("="*70 + "\n")
    
    print("""
┌─────────────────────────────────────────────────────────────────┐
│                      CONTEXTFLOW PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input                                                    │
│      ↓                                                          │
│  Behavioral Tracking (stress, engagement, trust)              │
│      ↓                                                          │
│  AI #1: Planner                                                │
│  ├─ Analyze clarity                                            │
│  ├─ Generate questions (if needed)                             │
│  └─ Build task context                                         │
│      ↓                                                          │
│  AI #2: Generator                                              │
│  ├─ Solution 1: Simple                                         │
│  ├─ Solution 2: Optimized (RECOMMENDED)                        │
│  └─ Solution 3: Scalable                                       │
│      ↓                                                          │
│  AI #1: Verifier                                               │
│  └─ Score and rank solutions                                   │
│      ↓                                                          │
│  ContextFlow Autonomy Engine                                   │
│  ├─ Estimate user stress: 0-1                                  │
│  ├─ Estimate engagement: 0-1                                   │
│  ├─ Estimate trust: 0-1                                        │
│  └─ Decide mode: AUTO/SHARED/SUGGEST/HUMAN                    │
│      ↓                                                          │
│  User Selection & Implementation                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

KEY FEATURES:
✓ Dual-AI collaboration
✓ Behavioral analysis
✓ Dynamic autonomy control
✓ Trust accumulation
✓ Risk assessment
✓ Session memory
✓ Never asks twice
✓ Stress-aware

AUTONOMY MODES:
• AUTO_EXECUTE → Execute without asking (high trust, low stress)
• SHARED_CONTROL → Show options, user selects (balanced)
• SUGGEST_ONLY → Generate suggestions only (high stress OR low trust)
• HUMAN_CONTROL → Require approval for each action (HIGH RISK)
    """)
    
    print("\n" + "="*70)
    print("END OF DEMONSTRATION")
    print("="*70 + "\n")
    print("To run the full interactive system:")
    print("  python app/contextflow_coordinator.py\n")


if __name__ == "__main__":
    main()
