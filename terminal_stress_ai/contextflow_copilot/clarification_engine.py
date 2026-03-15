from __future__ import annotations

import re
from typing import Dict, List, Optional


class ClarificationEngine:
    """Asks clarifying questions when the task lacks enough implementation detail."""

    FRAMEWORK_CATALOG = {
        "python": {
            "options": ["Flask", "FastAPI", "Django", "plain Python"],
            "recommended": "Flask",
        },
        "java": {
            "options": ["Spring Boot", "Jakarta EE", "Micronaut", "plain Java"],
            "recommended": "Spring Boot",
        },
        "javascript": {
            "options": ["Express", "Next.js", "NestJS", "plain Node.js"],
            "recommended": "Express",
        },
        "typescript": {
            "options": ["NestJS", "Express", "Next.js", "plain TypeScript"],
            "recommended": "NestJS",
        },
        "cpp": {
            "options": ["Qt", "Poco", "Crow", "plain C++"],
            "recommended": "plain C++",
        },
        "go": {
            "options": ["Gin", "Fiber", "Echo", "plain Go"],
            "recommended": "Gin",
        },
        "csharp": {
            "options": ["ASP.NET Core", ".NET Minimal API", "plain C#"],
            "recommended": "ASP.NET Core",
        },
        "rust": {
            "options": ["Axum", "Actix Web", "Rocket", "plain Rust"],
            "recommended": "Axum",
        },
    }
    STORAGE_RECOMMENDATION = "If you're unsure, I can choose the most practical database for this task and continue."
    LANGUAGE_RECOMMENDATION = "If you're unsure, I can choose the most practical language for this task and continue."
    LANGUAGE_DEFAULT = "python"
    DOMAIN_KEYWORDS = {
        "game": ("game", "gameplay", "multiplayer", "shooter", "rpg", "strategy", "puzzle"),
        "website": ("website", "web site", "landing page", "portfolio", "blog"),
        "api": ("api", "backend", "service", "microservice", "endpoint"),
        "mobile_app": ("mobile app", "android", "ios", "phone app"),
        "dashboard": ("dashboard", "analytics", "reporting", "admin panel"),
        "agent": ("bot", "chatbot", "assistant", "agent"),
        "tool": ("tool", "automation", "script", "cli", "calculator", "program"),
    }

    def analyze(self, task: Dict[str, str], clarification_state: Optional[Dict[str, str]] = None) -> Dict[str, object]:
        clarification_state = clarification_state or {}
        task_type = task.get("task_type", "general_query")
        questions: List[str] = []
        language = str(clarification_state.get("language") or task.get("language") or "plain_text")
        raw_input = str(task.get("raw_input", "")).lower()
        topic = self._topic_phrase(task)
        domain = self._infer_domain(raw_input)

        if task_type == "software_development":
            domain_questions = self._domain_questions(domain, topic, clarification_state)
            if domain_questions:
                return {
                    "clarification_required": True,
                    "questions": [domain_questions[0]],
                    "known_answers": clarification_state,
                }

        if task_type in {"code_generation", "software_development"} and not clarification_state.get("language") and task.get("language") == "plain_text":
            if clarification_state.get("language_unsure"):
                recommended_language = self.recommended_language(clarification_state)
                questions.append(f"For {topic}, if you're unsure, I recommend {recommended_language} as the most practical default. I can continue with {recommended_language}.")
            else:
                questions.append(f"For {topic}, which programming language should be used?")
        if task_type == "software_development" and not clarification_state.get("framework"):
            if clarification_state.get("framework_unsure"):
                questions.append(self._framework_recommendation(language, topic, clarification_state))
            else:
                questions.append(f"For {topic}, which framework or library should I use? {self._framework_hint(language)}")
        if task_type == "software_development" and not clarification_state.get("storage"):
            if clarification_state.get("storage_unsure"):
                recommended_storage = self.recommended_storage(clarification_state)
                questions.append(f"For {topic}, if you're unsure, I recommend {recommended_storage} as the most practical default. I can continue with {recommended_storage}.")
            else:
                questions.append(f"For {topic}, should I use persistent storage? Options: SQLite, PostgreSQL, MySQL, MongoDB, or none.")
        if task_type == "debugging" and not clarification_state.get("error_details"):
            questions.append(f"For {topic}, what error message, failing behavior, or stack trace are you seeing?")
        next_questions = questions[:1]

        return {
            "clarification_required": bool(next_questions),
            "questions": next_questions,
            "known_answers": clarification_state,
        }

    def _infer_domain(self, raw_input: str) -> str:
        raw_input = self._normalize_text(raw_input)
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(token in raw_input for token in keywords):
                return domain
        return "generic"

    def _domain_questions(self, domain: str, topic: str, state: Dict[str, object]) -> List[str]:
        if domain == "game":
            if not state.get("platform"):
                return [f"For {topic}, should it target PC, mobile, web, or console?"]
            if not state.get("game_scope"):
                return [f"For {topic}, do you want a concept/design only result, or an actual playable implementation?"]
            if not state.get("player_mode"):
                return [f"For {topic}, should it be single-player, local multiplayer, or online multiplayer?"]
            return []
        if domain == "website":
            if not state.get("site_type"):
                return [f"For {topic}, is this a landing page, web app, e-commerce site, dashboard, or content site?"]
            if not state.get("platform"):
                return [f"For {topic}, should it target desktop, mobile-first, or fully responsive web?"]
            return []
        if domain == "api":
            if not state.get("api_style"):
                return [f"For {topic}, should I design it as REST, GraphQL, WebSocket, or something else?"]
            if not state.get("storage"):
                return [f"For {topic}, should I use persistent storage? Options: SQLite, PostgreSQL, MySQL, MongoDB, or none."]
            return []
        if domain == "mobile_app":
            if not state.get("platform"):
                return [f"For {topic}, should it target Android, iOS, or both?"]
            if not state.get("app_scope"):
                return [f"For {topic}, do you want a concept/design only result, or an actual app implementation?"]
            return []
        if domain == "dashboard":
            if not state.get("dashboard_focus"):
                return [f"For {topic}, what is the main purpose: analytics, admin control, reporting, or monitoring?"]
            if not state.get("storage"):
                return [f"For {topic}, should I use persistent storage? Options: SQLite, PostgreSQL, MySQL, MongoDB, or none."]
            return []
        if domain == "agent":
            if not state.get("agent_goal"):
                return [f"For {topic}, should it answer questions, automate tasks, assist with coding, or do something else?"]
            if not state.get("platform"):
                return [f"For {topic}, should it run on web, desktop, terminal, or messaging platforms?"]
            return []
        if domain == "tool":
            if not state.get("tool_type"):
                return [f"For {topic}, is this a CLI tool, automation script, desktop tool, or web tool?"]
            if not state.get("app_scope"):
                return [f"For {topic}, do you want a quick prototype, a production-ready implementation, or just a design?"]
            return []
        if not any(state.get(key) for key in ("language", "framework", "storage", "non_implementation")) and not state.get("app_scope"):
            return [f"For {topic}, do you want a concept/design, a quick prototype, or a full working implementation?"]
        if state.get("app_scope") and not state.get("target_surface") and not state.get("non_implementation"):
            return [f"For {topic}, should it run on web, desktop, mobile, terminal, backend, or somewhere else?"]
        return []

    def _framework_hint(self, language: str) -> str:
        entry = self.FRAMEWORK_CATALOG.get(language)
        if not entry:
            return "Examples: a framework, a lightweight library, or no framework."
        return "Examples: " + ", ".join(entry["options"]) + "."

    def _framework_recommendation(self, language: str, topic: str, state: Optional[Dict[str, object]] = None) -> str:
        recommended = self.recommended_framework(language, state)
        entry = self.FRAMEWORK_CATALOG.get(language)
        if not entry:
            return f"For {topic}, if you're unsure, I recommend no framework here. I can continue with that unless you want a specific library."
        options = ", ".join(entry["options"])
        language_label = language if language != "plain_text" else "this stack"
        return f"For {topic}, if you're unsure, I recommend {recommended} for {language_label}. I can continue with {recommended}, or you can choose from {options}."

    def _topic_phrase(self, task: Dict[str, str]) -> str:
        goal = self._normalize_text(str(task.get("goal", "")).strip()) or "this task"
        raw_input = self._normalize_text(str(task.get("raw_input", "")).strip())
        lowered_goal = goal.lower()
        prefixes = (
            "ok we need to build ",
            "ok we need to make ",
            "we need to build ",
            "we need to make ",
            "i think i wanna build ",
            "i think i wanna make ",
            "i want to make ",
            "i want to build ",
            "i need to build ",
            "i need to make ",
            "make ",
            "build ",
            "create ",
            "generate ",
            "write ",
        )
        for prefix in prefixes:
            if lowered_goal.startswith(prefix):
                goal = goal[len(prefix):].strip()
                break
        cleaned = goal or raw_input or "this task"
        for article in ("a ", "an ", "the "):
            if cleaned.lower().startswith(article):
                cleaned = cleaned[len(article):].strip()
                break
        return f"this {cleaned}"

    def _normalize_text(self, text: str) -> str:
        normalized = f" {text.lower()} "
        replacements = {
            " e-commerece ": " e-commerce ",
            " e-commerence ": " e-commerce ",
            " ecommerece ": " ecommerce ",
            " aroung ": " around ",
            " dashbaord ": " dashboard ",
            " physicis ": " physics ",
        }
        for wrong, right in replacements.items():
            normalized = normalized.replace(wrong, right)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def recommended_language(self, state: Optional[Dict[str, object]] = None) -> str:
        state = state or {}
        if state.get("site_type") in {"landing_page", "web_app", "ecommerce", "dashboard", "content_site"}:
            return "typescript"
        if state.get("player_mode") or state.get("game_scope"):
            return "csharp"
        if state.get("api_style"):
            return "typescript"
        return self.LANGUAGE_DEFAULT

    def recommended_framework(self, language: str, state: Optional[Dict[str, object]] = None) -> str:
        state = state or {}
        if state.get("site_type") in {"landing_page", "web_app", "ecommerce", "content_site"}:
            if language in {"typescript", "javascript"}:
                return "Next.js"
        if state.get("site_type") == "dashboard":
            if language in {"typescript", "javascript"}:
                return "Next.js"
        entry = self.FRAMEWORK_CATALOG.get(language)
        return str(entry["recommended"]) if entry else "none"

    def recommended_storage(self, state: Optional[Dict[str, object]] = None) -> str:
        state = state or {}
        if state.get("site_type") in {"ecommerce", "dashboard"} or state.get("api_style"):
            return "postgresql"
        return "sqlite"
