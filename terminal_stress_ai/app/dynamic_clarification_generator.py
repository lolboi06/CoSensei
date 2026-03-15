"""
Dynamic Clarification Generator - Intelligently generates clarification questions for ANY task.
Uses semantic analysis to determine what clarifications are actually needed, not predefined templates.
"""
from __future__ import annotations
from typing import Dict, List, Any
import re


class DynamicClarificationGenerator:
    """
    Analyzes user prompts and generates only the clarifications that are actually needed.
    Works for any task type - not domain-specific templates.
    """
    
    def __init__(self):
        self.clarification_categories = {
            "scope": {
                "keywords": ["build", "create", "make", "design", "implement", "write", "develop"],
                "questions": [
                    "What exactly do you want to accomplish? (Describe the end result)",
                    "How big/complex should this be? (MVP, full-featured, enterprise-scale?)"
                ]
            },
            "audience": {
                "keywords": ["user", "customer", "audience", "who", "whom"],
                "questions": [
                    "Who is the primary user or audience?",
                    "What's their technical level? (beginner, intermediate, advanced?)"
                ]
            },
            "technology": {
                "keywords": ["tech", "stack", "language", "framework", "library", "tool", "using"],
                "questions": [
                    "Do you have a preferred technology or language?",
                    "Any constraints or requirements for the tech stack?"
                ]
            },
            "data": {
                "keywords": ["data", "database", "storage", "persist", "save", "load"],
                "questions": [
                    "Do you need persistent data storage? (database, files, memory?)",
                    "How much data? (small, medium, large?)"
                ]
            },
            "interface": {
                "keywords": ["ui", "interface", "frontend", "display", "visual", "web", "mobile", "desktop"],
                "questions": [
                    "What platforms? (web, mobile, desktop, CLI, API?)",
                    "Any UI framework or design preferences?"
                ]
            },
            "performance": {
                "keywords": ["fast", "slow", "performance", "speed", "scale", "load", "concurrent", "real-time"],
                "questions": [
                    "Performance requirements? (how fast, how many concurrent users?)",
                    "Any specific latency or throughput targets?"
                ]
            },
            "security": {
                "keywords": ["secure", "security", "auth", "encryption", "permission", "private", "sensitive"],
                "questions": [
                    "Are there security or privacy requirements?",
                    "Do you need authentication or access control?"
                ]
            },
            "integration": {
                "keywords": ["integrate", "api", "connect", "third-party", "service", "external"],
                "questions": [
                    "Does this need to integrate with other systems?",
                    "Any external APIs or services involved?"
                ]
            },
            "timeline": {
                "keywords": ["deadline", "asap", "urgent", "when", "soon", "later", "timeline"],
                "questions": [
                    "What's your timeline? (today, this week, this month?)",
                    "Is this blocking other work?"
                ]
            },
            "constraints": {
                "keywords": ["must", "should", "cannot", "avoid", "restriction", "limitation", "requirement"],
                "questions": [
                    "Any hard constraints or must-have requirements?",
                    "What should be avoided or excluded?"
                ]
            }
        }
    
    def analyze_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Analyze user prompt and determine which clarifications are actually needed.
        Returns only relevant questions, not a fixed set.
        """
        lowered = f" {user_prompt.lower()} "
        
        # Score each category based on keyword presence
        scores = {}
        for category, data in self.clarification_categories.items():
            keywords = data["keywords"]
            score = sum(1 for keyword in keywords if f" {keyword} " in lowered)
            scores[category] = score
        
        # Get categories that have at least some match
        relevant_categories = [cat for cat, score in scores.items() if score > 0]
        real_matches_found = len(relevant_categories) > 0
        
        # If nothing matched, default for asking clarification (but DON'T set categories yet)
        if not relevant_categories:
            # Return a special flag indicating clarification is NEEDED
            return {
                "relevant_categories": [],
                "questions": [],
                "num_questions": 0,
                "category_scores": scores,
                "needs_clarification": True,
                "real_matches_found": False
            }
        
        # Generate dynamic questions based on what's actually needed
        generated_questions = []
        for category in sorted(relevant_categories, key=lambda x: scores[x], reverse=True)[:4]:  # Top 4 categories
            questions = self.clarification_categories[category]["questions"]
            # Pick the first question for this category
            generated_questions.append(questions[0])
        
        # Ensure we have 3-5 questions
        while len(generated_questions) < 3 and relevant_categories:
            # Add more specific follow-ups if needed
            for category in relevant_categories:
                if len(generated_questions) >= 5:
                    break
                questions = self.clarification_categories[category]["questions"]
                if len(questions) > 1:
                    generated_questions.append(questions[1])
        
        generated_questions = generated_questions[:5]  # Cap at 5
        
        return {
            "relevant_categories": relevant_categories,
            "questions": generated_questions,
            "num_questions": len(generated_questions),
            "category_scores": scores,
            "needs_clarification": not real_matches_found,
            "real_matches_found": real_matches_found
        }
    
    def generate_clarification_prompt(self, user_prompt: str, analysis: Dict[str, Any]) -> str:
        """
        Generate a conversational clarification prompt with all questions.
        """
        questions = analysis["questions"]
        
        prompt = f"""Based on your request: "{user_prompt}"
        
I need a few more details to give you the best solution:

"""
        for idx, question in enumerate(questions, 1):
            prompt += f"{idx}. {question}\n"
        
        return prompt
    
    def extract_answers_from_response(self, response_text: str, num_questions: int) -> Dict[str, str]:
        """
        Extract answers from user's response (numbered or freeform).
        """
        lines = response_text.strip().split('\n')
        answers = {}
        
        for idx in range(1, num_questions + 1):
            # Look for numbered responses
            pattern = rf"^{idx}[.\)\\s]+"
            for line in lines:
                if re.match(pattern, line):
                    answer = re.sub(pattern, "", line).strip()
                    answers[f"answer_{idx}"] = answer
                    break
        
        # If not all found, treat entire response as answers
        if len(answers) < num_questions:
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            for idx, line in enumerate(non_empty_lines[:num_questions], 1):
                if f"answer_{idx}" not in answers:
                    answers[f"answer_{idx}"] = line
        
        return answers
    
    def build_context_from_answers(self, user_prompt: str, analysis: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Build a context dictionary from the user's prompt and answers.
        This context is used by Middle AI and Generator AI for decision making.
        """
        context = {
            "original_request": user_prompt,
            "relevant_categories": analysis["relevant_categories"],
            "num_clarifications": analysis["num_questions"],
            "answers": answers,
            "_task_type": "dynamic",
            "_clarification_dynamic": True,
        }
        
        # Extract key information from responses
        response_text = "\n".join(answers.values())
        
        # Look for tech mentions
        tech_keywords = ["python", "javascript", "java", "c#", "rust", "go", "react", "vue", "angular", "django", "flask", "spring", "nodejs", "node.js"]
        for tech in tech_keywords:
            if tech in response_text.lower():
                context["preferred_technology"] = tech
                break
        
        # Look for platform mentions
        platform_keywords = ["web", "mobile", "desktop", "cli", "api", "ios", "android", "windows", "linux", "mac"]
        for platform in platform_keywords:
            if platform in response_text.lower():
                context["target_platform"] = platform
                break
        
        # Look for scale/size mentions
        scale_keywords = {"small": "small", "medium": "medium", "large": "large", "enterprise": "enterprise", 
                         "mvp": "small", "prototype": "small", "full": "large", "complex": "large"}
        for keyword, scale in scale_keywords.items():
            if keyword in response_text.lower():
                context["project_scale"] = scale
                break
        
        # Look for timeline mentions
        timeline_keywords = {"today": "urgent", "asap": "urgent", "week": "short", "month": "medium", "later": "flexible"}
        for keyword, timeline in timeline_keywords.items():
            if keyword in response_text.lower():
                context["timeline"] = timeline
                break
        
        # Look for data/persistence mentions
        persistence_keywords = ["database", "storage", "persist", "save", "load", "postgresql", "mysql", "mongodb", "sqlite", "redis"]
        if any(word in response_text.lower() for word in persistence_keywords):
            context["needs_persistence"] = True
            # Try to extract specific database type
            db_keywords = {"postgresql": "PostgreSQL", "postgres": "PostgreSQL", "mysql": "MySQL", 
                          "mongodb": "MongoDB", "sqlite": "SQLite", "redis": "Redis"}
            for keyword, db_name in db_keywords.items():
                if keyword in response_text.lower():
                    context["database_preference"] = db_name
                    break
        else:
            context["needs_persistence"] = False
        
        return context


# Singleton instance
DYNAMIC_CLARIFICATION_GENERATOR = DynamicClarificationGenerator()
