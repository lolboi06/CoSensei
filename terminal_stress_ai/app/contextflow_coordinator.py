"""
CoSensei - Main System Coordinator
Orchestrates Planner AI + Generator AI + Verifier AI with behavioral analysis and autonomy control
"""

import sys
import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planner_ai import PlannerAI
from generator_ai import GeneratorAI
from verifier_ai import VerifierAI
from implementation_generator import ImplementationGenerator
from cognitive_state_model import CognitiveStateModel
from autonomy_decision_engine_v2 import AutonomyDecisionEngine
from enhanced_clarification_engine import EnhancedClarificationEngine


class CoSenseiController:
    """Main coordinator for CoSensei system"""
    
    def __init__(self):
        self.planner_ai = PlannerAI()
        self.generator_ai = GeneratorAI()
        self.verifier_ai = VerifierAI()
        self.implementation_generator = ImplementationGenerator()
        self.cognitive_model = CognitiveStateModel()
        self.autonomy_engine = AutonomyDecisionEngine()
        
        self.session_start = time.time()
        self.interaction_count = 0
        self.user_selections = []
        self.current_autonomy_mode = "SUGGEST_ONLY"
        self.last_solutions = []
        
        # Behavioral tracking
        self.keystroke_times = []
        self.pause_durations = []
        self.backspace_count = 0
        self.edit_count = 0
        
    def start_session(self):
        """Initialize CoSensei session"""
        
        print("\n" + "=" * 70)
        print("COSENSEI - Behavior-Aware Dual-AI System")
        print("=" * 70)
        print("\nHello! I'm CoSensei, your AI assistant.")
        print("\nI work by:")
        print("  1. Asking you clarifying questions (feel free to be verbose)")
        print("  2. Understanding your requirements through conversation")
        print("  3. Generating 3 different solution architecture options")
        print("  4. Letting you choose the best approach for YOUR needs\n")
        print("I adapt my communication based on your patterns - when you're")
        print("stressed or unsure, I simplify the options. When you're clear,")
        print("I give you full details.\n")
        print(self._format_status_line())
        print("=" * 70)
        print("\nLet's start! Tell me about your project.")
        print("Example: 'I want to build a music streaming platform with real-time playback'\n")
    
    
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through the full pipeline.
        Returns: response with solutions or clarification questions.
        """
        
        self.interaction_count += 1
        
        # Track behavior
        self._track_input_behavior(user_input)
        
        # Minimum input check
        if len(user_input.strip()) < 2:
            return {
                "type": "prompt",
                "message": "Please tell me more about what you want to build or understand. Example: 'I want to build a website for...' or 'Help me design a...'"
            }
        
        try:
            # Step 1: Planner AI analyzes clarity
            analysis = self.planner_ai.analyze_user_input(user_input)
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                "type": "prompt",
                "message": f"Let me understand better - can you describe what you want to build in more detail?"
            }
        
        # Step 2: Never block on clarification — always proceed to solutions.
        # Autonomy engine + dynamic questions at implementation phase handle missing context.

        # Step 3: Build task context
        task_context = self.planner_ai.build_task_context(user_input)
        
        # Step 4: Generator AI creates solutions
        prompt_data = {
            "task_context": task_context,
            "risk_level": "MEDIUM",
            "recommended_strategy": "optimized",
            "solution_constraints": {}
        }
        solutions = self.generator_ai.generate_solutions(prompt_data)
        
        # Step 5: Planner AI verifies solutions
        verification = self.planner_ai.verify_solutions(solutions, task_context)
        
        # Step 5.5: Verifier AI analyzes risk
        # Analyze risk for each solution
        risk_analyses = []
        for solution in solutions:
            risk_report = self.verifier_ai.analyze_risk(solution, task_context)
            risk_analyses.append(risk_report)
        
        # Use risk of recommended solution (index 1)
        primary_risk = risk_analyses[1] if len(risk_analyses) > 1 else risk_analyses[0]
        
        # Step 6: CoSensei evaluates autonomy based on risk
        self._evaluate_autonomy(analysis, task_context)
        
        # Override autonomy mode if risk is high
        if primary_risk['autonomy_mode'] == 'HUMAN_CONTROL':
            self.current_autonomy_mode = 'HUMAN_CONTROL'
        
        # Store solutions for later selection
        self.last_solutions = solutions
        
        return {
            "type": "solutions",
            "solutions": solutions,
            "verification": verification,
            "risk_analyses": risk_analyses,
            "primary_risk": primary_risk,
            "task_context": task_context,
            "autonomy_mode": self.current_autonomy_mode
        }
    
    def process_with_confirmed_context(
        self, all_text: str, confirmed_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full pipeline using pre-confirmed survey context.
        confirmed_context overrides keyword inference in the generator.
        """
        self.interaction_count += 1
        self._track_input_behavior(all_text)

        analysis = self.planner_ai.analyze_user_input(all_text)

        # Build task context using confirmed answers
        task_context = self.planner_ai.build_task_context(all_text, confirmed_context)

        # Inject confirmed feature flags directly
        for flag in ("has_auth", "has_payments", "has_realtime", "has_ml",
                     "has_file_upload", "has_search", "scale_hint"):
            if flag in confirmed_context:
                task_context[flag] = confirmed_context[flag]

        prompt_data = {
            "task_context": task_context,
            "user_request": all_text,        # full survey text → better inference
            "risk_level": "MEDIUM",
            "recommended_strategy": "optimized",
            "solution_constraints": {},
        }
        solutions = self.generator_ai.generate_solutions(prompt_data)
        verification = self.planner_ai.verify_solutions(solutions, task_context)

        risk_analyses = []
        for solution in solutions:
            risk_report = self.verifier_ai.analyze_risk(solution, task_context)
            risk_analyses.append(risk_report)

        primary_risk = risk_analyses[1] if len(risk_analyses) > 1 else risk_analyses[0]

        self._evaluate_autonomy(analysis, task_context)
        if primary_risk["autonomy_mode"] == "HUMAN_CONTROL":
            self.current_autonomy_mode = "HUMAN_CONTROL"

        self.last_solutions = solutions

        return {
            "type": "solutions",
            "solutions": solutions,
            "verification": verification,
            "risk_analyses": risk_analyses,
            "primary_risk": primary_risk,
            "task_context": task_context,
            "autonomy_mode": self.current_autonomy_mode,
        }

    def process_clarification_answers(self, answers: Dict[str, str], original_input: str) -> Dict[str, Any]:
        """Process answers to clarification questions"""
        
        task_context = self.planner_ai.build_task_context(original_input, answers)
        
        prompt_data = {
            "task_context": task_context,
            "risk_level": "MEDIUM",
            "recommended_strategy": "optimized",
            "solution_constraints": {}
        }
        solutions = self.generator_ai.generate_solutions(prompt_data)
        verification = self.planner_ai.verify_solutions(solutions, task_context)
        
        return {
            "type": "solutions",
            "solutions": solutions,
            "verification": verification,
            "task_context": task_context,
            "autonomy_mode": self.current_autonomy_mode
        }
    
    def process_solution_selection(self, solution_index: int, task_context: Dict) -> str:
        """
        Generate implementation after user selects a solution.
        Respects autonomy mode.
        """
        
        # Use stored solutions instead of regenerating
        if not hasattr(self, 'last_solutions') or not self.last_solutions:
            prompt_data = {
                "task_context": task_context,
                "risk_level": "MEDIUM",
                "recommended_strategy": "optimized",
                "solution_constraints": {}
            }
            solutions = self.generator_ai.generate_solutions(prompt_data)
        else:
            solutions = self.last_solutions
        
        if solution_index < 0 or solution_index >= len(solutions):
            return "Invalid solution selected."
        
        selected = solutions[solution_index]
        
        self.user_selections.append({
            "solution": solution_index,
            "timestamp": datetime.now().isoformat(),
            "task": task_context.get('raw_input')
        })
        
        # Generate implementation using Implementation Generator AI
        implementation_plan = self.implementation_generator.generate_implementation(
            selected, 
            task_context
        )
        
        # Format for display
        implementation_output = self.implementation_generator.format_implementation_for_display(implementation_plan)
        
        # Add next steps
        output = implementation_output
        output += "\n" + "=" * 70 + "\n"
        output += "NEXT STEPS\n"
        output += "=" * 70 + "\n"
        for step in implementation_plan['next_steps']:
            output += f"{step}\n"
        
        return output
    
    def _format_implementation_output(self, solution: Dict, task_context: Dict) -> str:
        """Format implementation output"""
        
        output = "\n" + "=" * 70 + "\n"
        output += f"IMPLEMENTATION: {solution['title'].upper()}\n"
        output += "=" * 70 + "\n\n"
        
        output += "## SYSTEM ARCHITECTURE\n\n"
        output += solution['architecture']
        
        output += "\n## TECH STACK\n\n"
        for key, value in solution['tech_stack'].items():
            output += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        output += f"\n## EFFORT & TIMELINE\n"
        output += f"• Duration: {solution['effort']}\n"
        output += f"• Scalability: {solution['scalability']}\n"
        output += f"• Maintenance Level: {solution['maintenance']}\n"
        
        output += f"\n## RISK MITIGATION\n"
        output += f"• {solution['risk_mitigation']}\n"
        
        return output
    
    def request_human_approval(self, implementation: str) -> bool:
        """Request human approval before proceeding"""
        print("\n" + "=" * 70)
        print("AUTONOMY MODE: HUMAN_CONTROL")
        print("=" * 70)
        print("\nI've prepared the implementation. Approve it to proceed?")
        print(implementation)
        print("\n[approve/reject/modify]: ", end="")
        response = input().strip().lower()
        
        return response == "approve"
    
    def _track_input_behavior(self, user_input: str):
        """Track behavioral signals from user input"""
        
        current_time = time.time()
        
        # Track keystroke timing
        self.keystroke_times.append(current_time)
        
        # Track editing patterns
        if '\\b' in repr(user_input):  # Backspace indicator
            self.backspace_count += 1
        
        # Calculate pause duration if there's history
        if len(self.keystroke_times) > 1:
            pause = self.keystroke_times[-1] - self.keystroke_times[-2]
            if pause > 1.0:  # More than 1 second
                self.pause_durations.append(pause)
    
    def _evaluate_autonomy(self, analysis: Dict, task_context: Dict):
        """
        Evaluate CoSensei autonomy decision.
        Based on clarity, user demeanor, and system confidence.
        """
        
        # Calculate cognitive state
        stress = self._estimate_stress()
        engagement = self._estimate_engagement()
        trust = self._estimate_trust()
        
        # Autonomy decision
        decision = self.autonomy_engine.decide_autonomy(
            task_clarity=analysis['clarity_level'],
            user_stress=stress,
            engagement_level=engagement,
            trust_level=trust,
            risk_level="MEDIUM"
        )
        
        self.current_autonomy_mode = decision['mode']
    
    def _estimate_stress(self) -> float:
        """Estimate user stress from behavioral signals"""
        
        # High backspace count = high stress
        stress = min(self.backspace_count * 0.1, 1.0)
        
        # Many short pauses = stress
        if len(self.pause_durations) > 0:
            avg_pause = sum(self.pause_durations) / len(self.pause_durations)
            if avg_pause > 2.0:
                stress += 0.2
        
        return min(stress, 1.0)
    
    def _estimate_engagement(self) -> float:
        """Estimate user engagement level"""
        
        if self.interaction_count == 0:
            return 0.5
        
        # More interactions = higher engagement
        engagement = min(self.interaction_count * 0.15, 1.0)
        
        return engagement
    
    def _estimate_trust(self) -> float:
        """Estimate user trust in system"""
        
        if len(self.user_selections) == 0:
            return 0.5
        
        # User accepting solutions = building trust
        trust = min(len(self.user_selections) * 0.2, 1.0)
        
        return trust
    
    def _format_status_line(self) -> str:
        """Format CoSensei status display"""
        
        stress = self._estimate_stress()
        engagement = self._estimate_engagement()
        trust = self._estimate_trust()
        
        # Use text instead of emoji for better terminal compatibility
        stress_indicator = "[HIGH]" if stress > 0.7 else "[MED]" if stress > 0.4 else "[LOW]"
        trust_indicator = "[LOW]" if trust < 0.3 else "[MED]" if trust < 0.6 else "[HIGH]"
        
        return f"""
Status: 
  Trust: {trust_indicator} {trust:.1%}
  Stress: {stress_indicator} {stress:.1%}
  Autonomy: {self.current_autonomy_mode}
  Mode: {"AUTO_EXECUTE" if stress < 0.3 else "SHARED_CONTROL" if trust > 0.6 else "SUGGEST_ONLY"}
"""


# Survey question order — asked one at a time until user is satisfied
_SURVEY_QUESTIONS = [
    {
        "key": "project_type",
        "label": "Project type",
        "question": "What are you building?  (e.g., web app, REST API, mobile backend, CLI tool, data pipeline)",
        "required": True,
    },
    {
        "key": "domain",
        "label": "Domain / purpose",
        "question": "What is it for?  (e.g., ecommerce, social network, analytics, fintech, AI/ML, healthcare)",
        "required": True,
    },
    {
        "key": "features",
        "label": "Key features",
        "question": "What must it do?  (e.g., user auth, payments, real-time chat, file upload, search, notifications)",
        "required": True,
    },
    {
        "key": "language",
        "label": "Language / stack",
        "question": "Language or framework preference?  (e.g., Python/FastAPI, Node/Express, Java/Spring, Go/Gin)",
        "required": False,
    },
    {
        "key": "scale",
        "label": "Scale",
        "question": "Expected scale?  (e.g., MVP for 50 beta users, 10k/day, enterprise high-traffic)",
        "required": False,
    },
    {
        "key": "team",
        "label": "Team",
        "question": "Who is building this?  (solo dev, small team 2-5, larger engineering team)",
        "required": False,
    },
    {
        "key": "deploy",
        "label": "Deployment",
        "question": "Where will it run?  (AWS / GCP / Azure, DigitalOcean, self-hosted, Docker, Kubernetes)",
        "required": False,
    },
    {
        "key": "constraints",
        "label": "Constraints",
        "question": "Any hard constraints?  (must use X tech, avoid Y, budget, legacy system to integrate)",
        "required": False,
    },
]

class CoSenseiSession:
    """Interactive session management"""
    
    def __init__(self):
        self.controller = CoSenseiController()
        self.clarification_pending = False
        self.clarification_questions = []
        self.last_input = ""
        self.solutions = []
        self.current_task_context = {}
        self.human_control_pending = False
        self.current_risk_report = None
    
    
    def run(self):
        """Start interactive session"""
        
        self.controller.start_session()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nThank you for using CoSensei. Goodbye!")
                    break
                
                if user_input.lower() == 'new':
                    self.clarification_pending = False
                    self.human_control_pending = False
                    self.solutions = []
                    self.current_risk_report = None
                    self.controller.last_solutions = []
                    print("\nStarting fresh! Tell me about your new project:\n")
                    continue
                
                # Handle human control decisions for high-risk solutions
                if self.human_control_pending:
                    self._handle_risk_decision(user_input)
                    continue
                
                # Check if this is a solution selection (if solutions are waiting)
                if self.solutions and user_input.lower() in ['1', '2', '3', 'simple', 'optimized', 'scalable']:
                    self._handle_solution_selection_full(user_input)
                    continue
                
                # Handle clarification responses
                if self.clarification_pending:
                    result = self._handle_clarification_response(user_input)
                    self._display_result(result)
                elif not self.solutions:
                    # First query — run the survey loop (builds confirmed context)
                    self._run_survey_loop(user_input)
                else:
                    result = self.controller.process_user_input(user_input)
                    self.last_input = user_input
                    self._display_result(result)
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()
                print("Please try again.\n")
    
    # ------------------------------------------------------------------ #
    #  SURVEY LOOP                                                         #
    # ------------------------------------------------------------------ #

    def _run_survey_loop(self, initial_input: str) -> None:
        """
        Conversational survey — ask questions one at a time until the user
        is satisfied.  Tracks confirmed (explicit) vs inferred (detected)
        fields and passes the full confirmed context to the generator so
        implementation code is grounded in real answers, not guesses.
        """
        confirmed: Dict[str, Any] = {}
        inferred:  Dict[str, Any] = {}
        all_text = initial_input

        # Seed inferred from initial input
        inferred.update(self._parse_text_for_context(initial_input))

        self._show_survey_header()
        self._show_context_so_far(inferred, confirmed)

        round_num = 0

        while round_num < len(_SURVEY_QUESTIONS):
            # Find the next unanswered question
            next_q = None
            for q in _SURVEY_QUESTIONS:
                key = q["key"]
                if key in confirmed:
                    continue
                # For optional questions skip if already inferred
                if not q["required"] and inferred.get(key):
                    continue
                next_q = q
                break

            if next_q is None:
                break  # All gaps covered

            # Update autonomy dynamically based on confirmed count
            self._update_autonomy_from_survey(len(confirmed))
            autonomy = self.controller.current_autonomy_mode

            print(f"\n  // COSENSEI  [Round {round_num + 1}  |  Autonomy: {autonomy}]")
            print(f"  {next_q['question']}")
            print("  [Answer freely — Enter to skip — type 'ready' to proceed to solutions]")

            answer = input("\n  You: ").strip()

            if answer.lower() in ["ready", "go", "done", "proceed", "generate",
                                   "next", "yes", "y", "ok", "sure"]:
                break

            if answer:
                confirmed[next_q["key"]] = answer
                all_text += "  " + answer
                # Mine additional context clues from the answer
                more = self._parse_text_for_context(answer)
                inferred.update({k: v for k, v in more.items() if k not in confirmed})

            self._show_context_so_far(inferred, confirmed)
            round_num += 1

        # ---- Satisfaction confirmation loop ----
        while True:
            self._show_final_survey_summary(inferred, confirmed)
            self._update_autonomy_from_survey(len(confirmed))

            print(f"  // Current Autonomy Mode: {self.controller.current_autonomy_mode}")
            print("\n  Satisfied with this understanding?  Ready to generate solution strategies?")
            print("  [yes  /  tell me more about: ...]")

            ans = input("\n  You: ").strip()

            if ans.lower() in ["yes", "y", "go", "proceed", "ok",
                                "sure", "done", "generate", ""]:
                # User satisfied — grant full autonomy
                self.controller.current_autonomy_mode = "AUTO_EXECUTE"
                break
            elif ans:
                # User wants to refine — fold the answer in
                all_text += "  " + ans
                more = self._parse_text_for_context(ans)
                # Treat as explicit confirmation for any new field found
                for k, v in more.items():
                    if k not in confirmed:
                        confirmed[k] = v
                inferred.update({kk: vv for kk, vv in more.items() if kk not in confirmed})

        # ---- Build confirmed task context ----
        self.current_task_context = self._build_confirmed_task_context(
            initial_input, all_text, confirmed, inferred
        )
        self.last_input = all_text

        # ---- Generate solutions using confirmed context ----
        print("\n" + "=" * 70)
        print("  COSENSEI — Generating strategies from your confirmed requirements...")
        print("=" * 70 + "\n")

        result = self.controller.process_with_confirmed_context(
            all_text, self.current_task_context
        )
        self.solutions = result.get("solutions", [])
        self.current_task_context = result.get("task_context", self.current_task_context)
        self.current_risk_report = result.get("primary_risk")
        self._display_result(result)

    def _show_survey_header(self) -> None:
        print("\n" + "=" * 70)
        print("  COSENSEI — DISCOVERY PHASE")
        print("  I ask targeted questions to understand your project precisely.")
        print("  The more detail you give, the better the implementation.")
        print("  Type 'ready' at any point to skip ahead to solution generation.")
        print("=" * 70)

    def _show_context_so_far(self, inferred: Dict, confirmed: Dict) -> None:
        print("\n  " + "-" * 66)
        print("  CONTEXT SO FAR:")
        all_keys = list(dict.fromkeys(list(confirmed.keys()) + list(inferred.keys())))
        if not all_keys:
            print("    (nothing gathered yet)")
        else:
            for key in all_keys:
                if key in confirmed:
                    val = str(confirmed[key])[:55]
                    print(f"    {key:<22}  {val:<55}  [CONFIRMED]")
                elif inferred.get(key):
                    val = str(inferred[key])[:55]
                    print(f"    {key:<22}  {val:<55}  [inferred]")
        print("  " + "-" * 66)

    def _show_final_survey_summary(self, inferred: Dict, confirmed: Dict) -> None:
        print("\n" + "=" * 70)
        print("  COSENSEI — PROJECT UNDERSTANDING SUMMARY")
        print("=" * 70)

        confirmed_items = list(confirmed.items())
        inferred_items  = [(k, v) for k, v in inferred.items() if k not in confirmed]

        if confirmed_items:
            print("\n  CONFIRMED  (from your direct answers — used as-is):")
            for k, v in confirmed_items:
                print(f"    {k:<22}  {str(v)[:60]}")

        if inferred_items:
            print("\n  INFERRED  (detected from text — correct if wrong):")
            for k, v in inferred_items:
                print(f"    {k:<22}  {str(v)[:60]}")

        if not confirmed_items and not inferred_items:
            print("    (still gathering — answer a few more questions)")
        print()

    def _update_autonomy_from_survey(self, confirmed_count: int) -> None:
        """Raise autonomy mode as more fields are confirmed."""
        c = self.controller
        if confirmed_count >= 5:
            c.current_autonomy_mode = "AUTO_EXECUTE"
        elif confirmed_count >= 3:
            c.current_autonomy_mode = "SUGGEST_ONLY"
        elif confirmed_count >= 1:
            c.current_autonomy_mode = "SHARED_CONTROL"
        else:
            c.current_autonomy_mode = "HUMAN_CONTROL"

    def _parse_text_for_context(self, text: str) -> Dict[str, Any]:
        """Extract structured context clues from free-form text."""
        t = text.lower()
        ctx: Dict[str, Any] = {}

        # Language
        for lang, kws in {
            "python":     ["python", "fastapi", "flask", "django"],
            "javascript": ["javascript", "node", "nodejs", "express"],
            "typescript": ["typescript", "nestjs", "angular"],
            "java":       ["java", "spring", "springboot", "spring boot"],
            "go":         ["golang", " go ", "gin"],
            "rust":       ["rust", "actix"],
        }.items():
            if any(kw in t for kw in kws):
                ctx["language"] = lang
                break

        # Framework
        for fw, kws in {
            "fastapi": ["fastapi"],
            "flask":   ["flask"],
            "django":  ["django"],
            "express": ["express"],
            "nestjs":  ["nestjs", "nest.js"],
            "spring":  ["spring boot", "springboot"],
            "gin":     [" gin "],
        }.items():
            if any(kw in t for kw in kws):
                ctx["framework"] = fw
                break

        # Database
        for db, kws in {
            "postgresql": ["postgresql", "postgres"],
            "mongodb":    ["mongodb", "mongo"],
            "mysql":      ["mysql"],
            "sqlite":     ["sqlite"],
            "redis":      ["redis"],
        }.items():
            if any(kw in t for kw in kws):
                ctx["database"] = db
                break

        # Project type
        for ptype, kws in {
            "web app":        ["web app", "website", "web application"],
            "api":            ["rest api", "graphql", " api ", "backend only"],
            "mobile backend": ["mobile", "ios", "android", "flutter", "react native"],
            "data pipeline":  ["data pipeline", "etl", "batch processing"],
            "dashboard":      ["dashboard", "admin panel", "analytics"],
            "cli tool":       ["cli", "command line", "terminal tool"],
        }.items():
            if any(kw in t for kw in kws):
                ctx["project_type"] = ptype
                break

        # Domain
        for domain, kws in {
            "ecommerce":  ["ecommerce", "e-commerce", "shop", "store", "product", "cart"],
            "social":     ["social network", "social media", "feed", "follow"],
            "fintech":    ["fintech", "finance", "payment", "banking", "wallet", "trading"],
            "healthcare": ["healthcare", "health", "medical", "hospital", "patient"],
            "education":  ["education", "learning", "course", "quiz", "school", "lms"],
            "ai_ml":      [" ai ", "machine learning", " ml ", "neural", "llm", "gpt"],
            "chat":       ["chat app", "messaging", "instant message"],
            "streaming":  ["streaming", "video platform", "audio platform", "media"],
            "saas":       ["saas", "subscription", "multi-tenant", "workspace"],
        }.items():
            if any(kw in t for kw in kws):
                ctx["domain"] = domain
                break

        # Scale
        if any(kw in t for kw in ["enterprise", "million users", "high traffic", "kubernetes", "distributed"]):
            ctx["scale"] = "large"
        elif any(kw in t for kw in ["mvp", "prototype", "small", "solo", "personal", "side project", "poc"]):
            ctx["scale"] = "small"

        # Feature flags
        feature_parts = []
        if any(kw in t for kw in ["auth", "login", "register", "signup", "jwt", "oauth"]):
            ctx["has_auth"] = True
            feature_parts.append("auth")
        if any(kw in t for kw in ["payment", "stripe", "billing", "subscription", "checkout"]):
            ctx["has_payments"] = True
            feature_parts.append("payments")
        if any(kw in t for kw in ["realtime", "real-time", "websocket", "socket.io", "live update", "chat"]):
            ctx["has_realtime"] = True
            feature_parts.append("real-time")
        if any(kw in t for kw in ["upload", "file upload", "image upload", "s3", "media upload"]):
            ctx["has_file_upload"] = True
            feature_parts.append("file-upload")
        if any(kw in t for kw in ["search", "elasticsearch", "full-text", "fulltext"]):
            ctx["has_search"] = True
            feature_parts.append("search")
        if any(kw in t for kw in ["machine learning", " ml ", "ai model", "predict", "recommend", "neural network"]):
            ctx["has_ml"] = True
            feature_parts.append("ml")
        if feature_parts:
            ctx["features_detected"] = ", ".join(feature_parts)

        return ctx

    def _build_confirmed_task_context(
        self,
        initial_input: str,
        all_text: str,
        confirmed: Dict[str, Any],
        inferred: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge confirmed + inferred into a task_context.
        Confirmed always wins over inferred.
        Feature flags are derived from the full survey text.
        """
        merged = {**inferred, **confirmed}   # confirmed wins

        # Parse feature flags from combined text so confirmed answers contribute
        features_text = (
            confirmed.get("features", "")
            + " " + all_text
        ).lower()

        ctx: Dict[str, Any] = {
            "raw_input":       all_text,
            "language":        merged.get("language"),
            "framework":       merged.get("framework"),
            "database":        merged.get("database"),
            "site_type":       merged.get("domain") or merged.get("project_type"),
            "target_platform": merged.get("project_type"),
            "categories":      list(merged.keys()),
            "keywords":        all_text.lower().split(),
            # Feature flags — derived from full survey text
            "has_auth":        any(kw in features_text for kw in
                                   ["auth", "login", "register", "signup", "jwt", "oauth"]),
            "has_payments":    any(kw in features_text for kw in
                                   ["payment", "stripe", "billing", "subscription", "checkout"]),
            "has_realtime":    any(kw in features_text for kw in
                                   ["realtime", "real-time", "websocket", "socket", "live", "chat"]),
            "has_ml":          any(kw in features_text for kw in
                                   ["machine learning", " ml ", "ai model", "predict",
                                    "recommend", "neural", " llm ", "gpt"]),
            "has_file_upload": any(kw in features_text for kw in
                                   ["upload", "file", "image", "s3", "storage", "media upload"]),
            "has_search":      any(kw in features_text for kw in
                                   ["search", "elasticsearch", "fulltext", "full-text"]),
            "scale_hint":      merged.get("scale", "medium"),
            "confirmed_fields": list(confirmed.keys()),   # what the user explicitly said
        }

        return ctx

    def _handle_solution_selection(self, user_input: str) -> Optional[str]:
        """Handle solution selection"""
        
        if not self.solutions:
            return None
        
        # Map input to solution index
        mapping = {
            '1': 0, 'simple': 0,
            '2': 1, 'optimized': 1,
            '3': 2, 'scalable': 2
        }
        
        solution_idx = mapping.get(user_input.lower())
        if solution_idx is None:
            return None
        
        # Process selection
        implementation = self.controller.process_solution_selection(
            solution_idx,
            self.current_task_context
        )
        
        return implementation
    
    def _handle_clarification_response(self, user_input: str) -> Dict:
        """Handle answers to clarification questions"""
        
        # Parse answers from user input
        answers = self._parse_answers(user_input)
        
        result = self.controller.process_clarification_answers(
            answers, 
            self.last_input
        )
        
        self.clarification_pending = False
        self.solutions = result.get('solutions', [])
        self.current_task_context = result.get('task_context', {})
        
        return result
    
    def _parse_answers(self, user_input: str) -> Dict:
        """Parse user answers to clarification questions"""
        
        # Simple parsing - can be extended
        answers = {}
        
        lower_input = user_input.lower()
        
        # Detect answer patterns
        if 'ecommerce' in lower_input or 'shopping' in lower_input:
            answers['site_type'] = 'ecommerce'
        if 'dashboard' in lower_input or 'analytics' in lower_input:
            answers['site_type'] = 'dashboard'
        if 'blog' in lower_input:
            answers['site_type'] = 'blog'
        
        if 'mobile' in lower_input:
            answers['target_platform'] = 'mobile'
        if 'desktop' in lower_input:
            answers['target_platform'] = 'desktop'
        if 'both' in lower_input or 'responsive' in lower_input:
            answers['target_platform'] = 'responsive'
        
        if 'python' in lower_input:
            answers['language'] = 'python'
        if 'java' in lower_input:
            answers['language'] = 'java'
        if 'javascript' in lower_input or 'node' in lower_input:
            answers['language'] = 'javascript'
        
        return answers
    
    def _display_result(self, result: Dict):
        """Display result based on type"""
        
        if result['type'] == 'prompt':
            print("\n" + result['message'] + "\n")
        
        elif result['type'] == 'clarification':
            print("\n" + "="*70)
            print(result['message'])
            print("="*70 + "\n")
            for i, q in enumerate(result['questions'], 1):
                print(f"{i}. {q}")
            print("\n(You can answer all at once or one at a time)\n")
            self.clarification_pending = True
            self.clarification_questions = result['questions']
        
        elif result['type'] == 'solutions':
            self.solutions = result['solutions']
            self.current_task_context = result['task_context']
            self.current_risk_report = result.get('primary_risk')
            
            print("\n" + "=" * 70)
            print("SOLUTION STRATEGIES FOR YOUR PROJECT")
            print("=" * 70 + "\n")
            
            for i, sol in enumerate(result['solutions'], 1):
                rec = " [RECOMMENDED START HERE]" if sol.get('recommended', False) else ""
                title = sol.get('title') or sol.get('name') or f"Solution {i}"
                risk_info = ""
                if i <= len(result.get('risk_analyses', [])):
                    risk = result['risk_analyses'][i-1]
                    risk_level_short = "[LOW]" if risk['risk_level'] == 'LOW' else "[MED]" if risk['risk_level'] == 'MEDIUM' else "[HIGH]"
                    risk_info = f" {risk_level_short} (Risk: {risk['risk_score']:.0%})"
                print(f"{i}. {title.upper()}{rec}{risk_info}")
                print(f"   {sol.get('description', '')}")
                print(f"   • Timeline: {sol.get('effort', 'Unknown')}")
                print(f"   • Scalability: {sol.get('scalability', 'Unknown')}")
                print()
            
            # Display risk analysis for recommended solution
            if result.get('primary_risk'):
                risk_report = result['primary_risk']
                print(self.controller.verifier_ai.get_risk_report_display(risk_report))
            
            # Handle autonomy mode
            autonomy_mode = result.get('autonomy_mode', 'SUGGEST_ONLY')
            if autonomy_mode == 'HUMAN_CONTROL':
                self.human_control_pending = True
                print("=" * 70)
                print("AUTONOMY MODE: HUMAN_CONTROL")
                print("=" * 70)
                print("\nRisk level is HIGH. Please choose an action:\n")
                print("  1. Accept risk and proceed with solution")
                print("  2. Request safer alternative")
                print("  3. Request issue fixes")
                print("  4. Cancel\n")
            else:
                print("Which solution interests you? (enter 1, 2, or 3)\n")
    
    def _generate_and_display_implementation(self, solution_index: int) -> None:
        """Generate and display implementation details for selected solution"""
        
        if not self.solutions or solution_index < 1 or solution_index > len(self.solutions):
            print("Invalid solution selection.\n")
            return
        
        selected_solution = self.solutions[solution_index - 1]
        
        # Generate implementation plan
        implementation_plan = self.controller.implementation_generator.generate_implementation(
            selected_solution, 
            self.current_task_context
        )
        
        # Display formatted implementation
        display_text = self.controller.implementation_generator.format_implementation_for_display(implementation_plan)
        print(display_text)
        
        print("=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        for step in implementation_plan['next_steps']:
            print(f"  {step}")
        print()
    
    def _handle_solution_selection_full(self, user_input: str) -> None:
        """Full solution selection flow: questions → sections → scores."""
        mapping = {
            '1': 0, 'simple': 0,
            '2': 1, 'optimized': 1,
            '3': 2, 'scalable': 2
        }
        solution_idx = mapping.get(user_input.lower())
        if solution_idx is None:
            return

        self._ask_implementation_questions()

        implementation = self.controller.process_solution_selection(
            solution_idx,
            self.current_task_context
        )

        self._display_implementation_in_sections(implementation)
        self._display_final_scores()

        print("\nWould you like to ask about another project? (type 'new' or 'exit')\n")

    def _ask_implementation_questions(self) -> None:
        """Dynamically ask only about fields missing from task context, scaled to autonomy mode."""
        autonomy = self.controller.current_autonomy_mode

        # AUTO_EXECUTE: no questions at all — trust the context we have
        if autonomy == "AUTO_EXECUTE":
            return

        # How many gaps to ask about per autonomy level
        max_q = {"SHARED_CONTROL": 1, "SUGGEST_ONLY": 2, "HUMAN_CONTROL": 5}.get(autonomy, 2)

        # Map context fields to task_context keys
        ctx = self.current_task_context
        field_to_ctx_key = {
            "language":  "language",
            "framework": "framework",
            "database":  "database",
            "site_type": "site_type",
            "platform":  "target_platform",
        }

        # Collect fields that are genuinely unknown
        missing = [
            field for field, ctx_key in field_to_ctx_key.items()
            if not ctx.get(ctx_key)
            and field in EnhancedClarificationEngine.QUESTION_EXPLANATIONS
        ][:max_q]

        if not missing:
            return

        print("\n" + "=" * 70)
        print(f"QUICK SETUP  [Autonomy: {autonomy}]  (Enter = use default)")
        print("=" * 70)

        for field in missing:
            spec = EnhancedClarificationEngine.QUESTION_EXPLANATIONS[field]
            default = spec.get("default", "")
            opts    = " | ".join(spec["options"].keys())
            print(f"\n  {spec['question']}")
            print(f"  [{opts}]  default: {default}")
            answer = input("  > ").strip().lower()
            resolved = answer if answer in spec["options"] else default
            ctx_key  = field_to_ctx_key[field]
            self.current_task_context[ctx_key] = resolved
            print(f"  → {resolved}")

        print()

    def _display_implementation_in_sections(self, output: str) -> None:
        """Split implementation at section headers; prompting behaviour driven by autonomy mode."""
        autonomy = self.controller.current_autonomy_mode

        # AUTO_EXECUTE: dump everything without stopping
        prompt_between = autonomy != "AUTO_EXECUTE"

        sep   = "-" * 70
        lines = output.split("\n")

        sections: list = []
        current: list = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if i + 1 < len(lines) and lines[i + 1] == sep:
                if current:
                    sections.append(current)
                current = [line, sep]
                i += 2
            else:
                current.append(line)
                i += 1
        if current:
            sections.append(current)

        total = len(sections)
        for idx, section in enumerate(sections):
            print("\n".join(section))
            if prompt_between and idx < total - 1:
                label = f"  [ {idx + 1}/{total}  Press Enter for next section... ]\n"
                input(label)

    def _display_final_scores(self) -> None:
        """Display behavioral analysis scores at the end of implementation."""
        c = self.controller
        stress     = c._estimate_stress()
        trust      = c._estimate_trust()
        engagement = c._estimate_engagement()
        user_score = max(0.0, 1.0 - stress)  # higher is better

        def label(v, hi=0.7, lo=0.4):
            return "[HIGH]" if v > hi else "[MED]" if v > lo else "[LOW]"

        print("\n" + "=" * 70)
        print("SESSION BEHAVIORAL ANALYSIS")
        print("=" * 70)
        print(f"  User Score    : {user_score:>5.0%}  {label(user_score)}")
        print(f"  Trust Score   : {trust:>5.0%}  {label(trust, hi=0.6, lo=0.3)}")
        print(f"  Stress Level  : {stress:>5.0%}  {label(stress)}")
        print(f"  Engagement    : {engagement:>5.0%}  {label(engagement)}")
        print(f"  Autonomy Mode : {c.current_autonomy_mode}")
        print()

    def _handle_risk_decision(self, user_input: str) -> None:
        """Handle user decision on high-risk solution"""
        
        choice = user_input.lower().strip()
        
        if choice == '1' or choice.startswith('accept'):
            # Accept risk and proceed
            print("\n[OK] Risk accepted. Proceeding with solution.\n")
            self.human_control_pending = False
            print("Generating implementation details...\n")
            self._ask_implementation_questions()
            implementation = self.controller.process_solution_selection(1, self.current_task_context)
            self._display_implementation_in_sections(implementation)
            self._display_final_scores()
            print("\nWould you like to ask about another project? (type 'new' or 'exit')\n")
        
        elif choice == '2' or choice.startswith('safer'):
            # Request safer alternative (Simple solution with lower risk)
            print("\n[SAFE] Generating safer alternative (Simple MVP approach)...\n")
            if self.solutions:
                sol = self.solutions[0]  # Simple solution has lower risk
                print("=" * 70)
                print(f"SAFER ALTERNATIVE: {sol.get('title', 'Solution')}")
                print("=" * 70 + "\n")
                print(f"Description: {sol.get('description', '')}\n")
                print(f"Timeline: {sol.get('effort', '')}\n")
                print(f"This MVP approach has significantly lower risk.\n")
            self.human_control_pending = False
            print("Would you like to proceed with this solution? (enter 1 for yes, or 'new' for different project)\n")
        
        elif choice == '3' or choice.startswith('fix'):
            # Request issue fixes
            print("\n[FIX] Generating recommendations for fixing detected issues...\n")
            if self.current_risk_report:
                print("=" * 70)
                print("RECOMMENDED FIXES FOR HIGH-RISK ISSUES")
                print("=" * 70 + "\n")
                for i, rec in enumerate(self.current_risk_report.get('recommendations', [])[:5], 1):
                    print(f"{i}. {rec}\n")
            self.human_control_pending = False
            print("Apply these recommendations and regenerate the solution? (type 'new' to start fresh)\n")
        
        elif choice == '4' or choice.startswith('cancel'):
            # Cancel
            print("\n[X] Solution cancelled.\n")
            self.human_control_pending = False
            self.solutions = []
            self.current_risk_report = None
            print("Would you like to request a different type of solution? (type 'new' or describe another project)\n")
        
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.\n")


def main():
    """Start CoSensei"""
    
    session = CoSenseiSession()
    session.run()


if __name__ == "__main__":
    main()
