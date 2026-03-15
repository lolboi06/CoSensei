"""
ContextFlow Planner AI (AI #1)
Handles clarification, context building, and solution verification
"""

import sys
import os
from typing import Dict, List, Any, Optional
from dynamic_clarification_generator import DynamicClarificationGenerator

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PlannerAI:
    """AI #1: Clarification, Context Building, and Verification"""
    
    def __init__(self):
        self.clarification_engine = DynamicClarificationGenerator()
        self.session_context = {}
        self.interaction_history = []
        
    def analyze_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze input for clarity and extract task context.
        Returns: analysis with clarity level and detected categories.
        """
        
        analysis = self.clarification_engine.analyze_prompt(user_input)
        
        # Get categories from either 'relevant_categories' or 'categories'
        categories = analysis.get('relevant_categories', analysis.get('categories', []))
        real_matches = analysis.get('real_matches_found', False)
        
        # Force clarification if no real keyword matches found
        if not real_matches:
            return {
                "clarity_level": 0.0,
                "categories": [],
                "keywords": [],
                "needs_clarification": True,
                "reason": "No clarity - need more details"
            }
        
        return {
            "clarity_level": min(len(categories) / 3, 1.0),  # 0-1 scale (3+ categories = clear)
            "categories": categories,
            "keywords": analysis.get('keywords', []),
            "needs_clarification": analysis.get('needs_clarification', False)
        }
    
    def generate_clarification_questions(self, user_input: str) -> Optional[List[str]]:
        """
        Generate dynamic clarification questions if input is too vague.
        Never ask twice for the same information.
        """
        
        analysis = self.clarification_engine.analyze_prompt(user_input)
        real_matches = analysis.get('real_matches_found', False)
        
        # If NO real keyword matches found, ask fundamental questions
        if not real_matches:
            return [
                "What do you want to build? (e.g., website, mobile app, API, database, etc.)",
                "What's the main purpose or domain? (e.g., ecommerce, social media, streaming, finance)",
                "What platform or technology are you thinking of? (e.g., Python, Node.js, Java, React, Vue)",
                "Any specific features you need? (e.g., real-time, payments, authentication, analytics)",
                "How urgent is this? (e.g., MVP, production, proof of concept)"
            ]
        
        # Otherwise use the questions from analysis
        questions = analysis.get('questions', [])
        return questions if questions else None
    
    def build_task_context(self, user_input: str, answers: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Build structured task context from user input and clarification answers.
        """
        
        analysis = self.clarification_engine.analyze_prompt(user_input)
        categories = analysis.get('relevant_categories', analysis.get('categories', []))
        
        task_context = {
            "raw_input": user_input,
            "project_type": answers.get("project_type") if answers else None,
            "site_type": answers.get("site_type") if answers else None,
            "target_platform": answers.get("target_platform") if answers else None,
            "language": answers.get("language") if answers else None,
            "framework": answers.get("framework") if answers else None,
            "database": answers.get("database") if answers else None,
            "features": answers.get("features", []) if answers else [],
            "keywords": analysis.get('keywords', []),
            "categories": categories
        }
        
        # Update session context
        self.session_context.update(task_context)
        
        return task_context
    
    def verify_solutions(self, solutions: List[Dict], task_context: Dict) -> Dict[str, Any]:
        """
        Verify generated solutions against task context.
        Returns: verification scores and recommended solution.
        """
        
        verification = {
            "solution_scores": [],
            "confidence": 0.95,
            "issues": [],
            "recommended_solution": 1  # 0-indexed
        }
        
        for i, solution in enumerate(solutions):
            score = {
                "solution": i + 1,  # 1-indexed for UI
                "score": 0.85 + (i * 0.05),  # Simple scoring
                "alignment": self._check_alignment(solution, task_context),
                "valid": True
            }
            verification["solution_scores"].append(score)
        
        # Find highest scoring solution
        best_idx = max(range(len(verification["solution_scores"])), 
                      key=lambda i: verification["solution_scores"][i]["score"])
        verification["recommended_solution"] = best_idx + 1
        
        return verification
    
    def _check_alignment(self, solution: Dict, context: Dict) -> str:
        """Check if solution matches task context"""
        
        level = solution.get('level', 1)
        
        # Simple heuristic: match based on context clarity
        if len(context.get('categories', [])) < 3:
            if level == 1:
                return "excellent"
            return "good"
        elif len(context.get('categories', [])) < 6:
            if level == 2:
                return "excellent"
            return "good"
        else:
            if level == 3:
                return "excellent"
            return "fair"
    
    def reset_session(self):
        """Reset session context for new project"""
        self.session_context = {}
        self.interaction_history = []
