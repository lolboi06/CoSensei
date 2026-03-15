"""
Enhanced clarification engine with explanations, defaults, and better UX.
"""
from __future__ import annotations

from typing import Dict, Optional


class EnhancedClarificationEngine:
    """Provides intelligent clarification with explanations and defaults."""

    QUESTION_EXPLANATIONS = {
        "site_type": {
            "question": "What type of site do you want to build?",
            "options": {
                "landing_page": "Landing page - single page promoting a product/service",
                "web_app": "Web app - interactive application with user accounts and features",
                "ecommerce": "E-commerce - online store with products and shopping",
                "dashboard": "Dashboard - data visualization and real-time monitoring",
                "content_site": "Content site - blog, news, documentation",
            },
            "default": "web_app",
            "explanation": "This determines the overall architecture and complexity.",
        },
        "platform": {
            "question": "What devices should it work on?",
            "options": {
                "desktop": "Desktop - optimized for computers (1920x1080+)",
                "mobile_first": "Mobile-first - phones primary, then tablets/desktop",
                "responsive_web": "Responsive - works equally well on all devices",
            },
            "default": "responsive_web",
            "explanation": "This affects layout, performance, and user experience.",
        },
        "language": {
            "question": "What programming language?",
            "options": {
                "python": "Python - easy to learn, great for web backends",
                "javascript": "JavaScript - web standard, runs everywhere",
                "typescript": "TypeScript - JavaScript with type safety",
                "java": "Java - enterprise, scalable applications",
                "csharp": "C# - Windows/.NET ecosystem development",
            },
            "default": "python",
            "explanation": "Language choice affects available frameworks and deployment options.",
        },
        "framework": {
            "question": "What framework or library?",
            "options": {
                "flask": "Flask - lightweight Python web framework",
                "django": "Django - full-featured Python framework",
                "fastapi": "FastAPI - modern Python async framework",
                "react": "React - JavaScript UI library (frontend)",
                "vue": "Vue - lightweight JavaScript framework",
                "angular": "Angular - comprehensive web framework",
                "spring": "Spring - Java enterprise framework",
                "express": "Express - minimal Node.js framework",
            },
            "default": "flask",
            "explanation": "Framework provides structure and tools for development.",
        },
        "database": {
            "question": "What database for storing data?",
            "options": {
                "sqlite": "SQLite - simple embedded database (good for learning)",
                "postgresql": "PostgreSQL - powerful open-source database",
                "mysql": "MySQL - popular relational database",
                "mongodb": "MongoDB - document-based NoSQL database",
                "none": "None - no database (stateless app)",
            },
            "default": "sqlite",
            "explanation": "Database stores user data, posts, products, etc.",
        },
    }

    @staticmethod
    def format_question_with_explanation(field: str) -> str:
        """Format a question with options and explanation."""
        if field not in EnhancedClarificationEngine.QUESTION_EXPLANATIONS:
            return ""

        spec = EnhancedClarificationEngine.QUESTION_EXPLANATIONS[field]
        lines = [
            f"\n{spec['question']}",
            f"({spec['explanation']})\n",
        ]

        for key, description in spec["options"].items():
            lines.append(f"  • {description}")

        return "\n".join(lines)

    @staticmethod
    def suggest_default(field: str) -> str:
        """Suggest sensible default for a field."""
        if field not in EnhancedClarificationEngine.QUESTION_EXPLANATIONS:
            return ""

        spec = EnhancedClarificationEngine.QUESTION_EXPLANATIONS[field]
        default_key = spec.get("default", "")

        # Find default description
        for key, desc in spec["options"].items():
            if key == default_key:
                return desc.split(" - ")[0]  # Return just the name

        return ""

    @staticmethod
    def handle_unclear_answer(field: str, user_input: str) -> Optional[str]:
        """
        Detect unclear answers and suggest clarification.
        Returns suggestion message or None if answer is clear.
        """
        lowered = user_input.strip().lower()

        # Vague answers
        if lowered in ["web", "yes", "ok", "good", "sure", "any", "whatever"]:
            default = EnhancedClarificationEngine.suggest_default(field)
            if default:
                return (
                    f"That's a bit vague. Let me suggest the most practical option: "
                    f"**{default}**. Sound good? Or did you want something different?"
                )

        # Confused/unsure answers
        if any(
            word in lowered
            for word in ["not sure", "don't know", "unclear", "confused", "help", "explain"]
        ):
            spec = EnhancedClarificationEngine.QUESTION_EXPLANATIONS.get(field, {})
            default = spec.get("default", "")
            return f"No problem! I'd recommend **{default}** for your situation. That work for you?"

        return None

    @staticmethod
    def explain_field(field: str) -> str:
        """Provide detailed explanation of a field."""
        spec = EnhancedClarificationEngine.QUESTION_EXPLANATIONS.get(field, {})
        if not spec:
            return "I need that detail to build the right solution."

        lines = [
            f"\n**{field.replace('_', ' ').title()}**\n",
            spec.get("explanation", ""),
            "\nOptions:",
        ]

        for key, desc in spec.get("options", {}).items():
            lines.append(f"  • {desc}")

        default = spec.get("default", "")
        if default:
            for key, desc in spec.get("options", {}).items():
                if key == default:
                    lines.append(f"\nI'd suggest: **{desc.split(' - ')[0]}**")
                    break

        return "\n".join(lines)

    @staticmethod
    def format_progress(answered: Dict[str, str], required_fields: list[str]) -> str:
        """Show progress in a friendly way."""
        count = sum(1 for f in required_fields if answered.get(f))
        total = len(required_fields)

        if count == total:
            return "\n✓ Got all the details! Generating solutions...\n"

        remaining = [f for f in required_fields if not answered.get(f)]
        lines = [f"\nGot {count}/{total}. Still need:"]
        for field in remaining:
            spec = EnhancedClarificationEngine.QUESTION_EXPLANATIONS.get(field, {})
            lines.append(f"  • {spec.get('question', field)}")

        return "\n".join(lines) + "\n"
