from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Support running both as `py -m app.main` and `py app\main.py`.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.features import extract_features
from app.features import FeatureVector
from app.behavior_trust_bridge import BehaviorTrustBridge
from app.risk_analyzer import RiskAnalyzer
from app.survey_validation import NasaTlxSurvey, SurveyValidationEngine, TrustSurvey
from app.code_context_analyzer import CodeContextAnalyzer
from app.suggestion_quality_tracker import SuggestionQualityTracker
from app.intent_predictor import IntentPredictor
from app.adaptive_policy_engine import AdaptivePolicyEngine
from app.system_metrics import SystemMetricsTracker
from app.autonomy_decision_engine import AutonomyDecisionEngine
from app.action_manager import ActionManager
from app.trust_fusion_module import TrustFusionModule
from app.shared_autonomy_allocator import SharedAutonomyAllocator
from app.autonomy_explanation_module import AutonomyExplanationModule
from app.conversation_memory_manager import ConversationMemoryManager
from app.suggestion_generator import SuggestionGenerator
from app.task_memory_manager import TaskMemoryManager
from app.user_profile_memory_manager import UserProfileMemoryManager
from app.cognitive_state_model import CognitiveStateModel
from app.task_understanding_module import TaskUnderstandingModule
from app.shared_autonomy_controller import SharedAutonomyController
from app.suggestion_engine import SuggestionEngine
from app.action_execution_engine import ActionExecutionEngine
from app.policy_learning_system import PolicyLearningSystem
from app.user_preference_engine import UserPreferenceEngine
from app.adaptive_copilot_pipeline import AdaptiveCopilotPipeline
from app.model import StateModel, model_version
from app.task_context_manager import TaskContextManager
from app.solution_strategy_generator import SolutionStrategyGenerator
from app.solution_selector import SolutionSelector
from app.status_formatter import StatusFormatter
from app.enhanced_clarification_engine import EnhancedClarificationEngine
from app.middle_ai_planner_engine import MiddleAIPlannerEngine
from app.generator_ai import GeneratorAI
from contextflow.controller import ContextFlowController, ControllerModules
from contextflow.execution.action_manager import ActionManager as ContextFlowActionManager
from contextflow_copilot import CopilotPipeline as FrontendCopilotPipeline
from contextflow_copilot import ClarificationEngine as FrontendClarificationEngine
from contextflow_copilot import LLMSuggestionEngine as FrontendLLMSuggestionEngine

SESSIONS: dict[str, list[dict]] = {}
SESSION_ANALYSIS: dict[str, list[dict]] = {}
MODEL = StateModel()
TRUST_BRIDGE = BehaviorTrustBridge()
RISK_ANALYZER = RiskAnalyzer()
VALIDATION_ENGINE = SurveyValidationEngine()
PREFERENCE_ENGINE = UserPreferenceEngine()
CODE_CONTEXT_ANALYZER = CodeContextAnalyzer()
SUGGESTION_TRACKER = SuggestionQualityTracker()
INTENT_PREDICTOR = IntentPredictor()
POLICY_ENGINE = AdaptivePolicyEngine()
SYSTEM_METRICS = SystemMetricsTracker()
AUTONOMY_ENGINE = AutonomyDecisionEngine()
ACTION_MANAGER = ActionManager()
TRUST_FUSION = TrustFusionModule()
SHARED_AUTONOMY_ALLOCATOR = SharedAutonomyAllocator()
AUTONOMY_EXPLAINER = AutonomyExplanationModule()
MEMORY_MANAGER = ConversationMemoryManager()
SUGGESTION_GENERATOR = SuggestionGenerator()
TASK_MEMORY = TaskMemoryManager()
USER_PROFILE_MEMORY = UserProfileMemoryManager()
COGNITIVE_STATE_MODEL = CognitiveStateModel()
TASK_UNDERSTANDING = TaskUnderstandingModule()
SHARED_AUTONOMY_CONTROLLER = SharedAutonomyController()
SUGGESTION_ENGINE = SuggestionEngine()
ACTION_EXECUTION_ENGINE = ActionExecutionEngine()
POLICY_LEARNING = PolicyLearningSystem()
ADAPTIVE_COPILOT = AdaptiveCopilotPipeline(
    conversation_memory=MEMORY_MANAGER,
    task_memory=TASK_MEMORY,
    user_profile_memory=USER_PROFILE_MEMORY,
    cognitive_state_model=COGNITIVE_STATE_MODEL,
    task_understanding=TASK_UNDERSTANDING,
    autonomy_controller=SHARED_AUTONOMY_CONTROLLER,
    explanation_module=AUTONOMY_EXPLAINER,
    suggestion_engine=SUGGESTION_ENGINE,
    action_engine=ACTION_EXECUTION_ENGINE,
    policy_learning=POLICY_LEARNING,
)
CONTEXTFLOW_CONTROLLER = ContextFlowController(
    modules=ControllerModules(
        state_model=MODEL,
        behavior_bridge=TRUST_BRIDGE,
        risk_analyzer=RISK_ANALYZER,
        preference_engine=PREFERENCE_ENGINE,
        trust_fusion=TRUST_FUSION,
        autonomy_engine=AUTONOMY_ENGINE,
        shared_autonomy_controller=SHARED_AUTONOMY_CONTROLLER,
        cognitive_state_model=COGNITIVE_STATE_MODEL,
        task_understanding_module=TASK_UNDERSTANDING,
        autonomy_explainer=AUTONOMY_EXPLAINER,
        suggestion_engine=SUGGESTION_ENGINE,
        action_manager=ContextFlowActionManager(),
    )
)
FRONTEND_COPILOT = FrontendCopilotPipeline()
FRONTEND_CLARIFIER = FrontendClarificationEngine()
FRONTEND_LLM = FrontendLLMSuggestionEngine()
TASK_CONTEXT_MANAGER = TaskContextManager()
SOLUTION_STRATEGY_GENERATOR = SolutionStrategyGenerator()
SOLUTION_SELECTOR = SolutionSelector()
STATUS_FORMATTER = StatusFormatter()
MIDDLE_AI = MiddleAIPlannerEngine()
GENERATOR_AI = GeneratorAI()
MIN_EVENTS_FOR_TREND = int(os.getenv("MIN_EVENTS_FOR_TREND", "20"))
MIN_EVENTS_FOR_INDICATORS = int(os.getenv("MIN_EVENTS_FOR_INDICATORS", "5"))


def _detect_task_type(user_input: str) -> dict:
    """Detect task type from user input and return task classification with suggested clarification fields."""
    lowered = f" {user_input.lower()} "
    
    # Task type patterns
    patterns = {
        "web_development": (["website", "web app", "web application", "responsive", "frontend", "html", "react", "vue", "angular", "next", "nuxt"], 
                           ["site_type", "target_platform", "language", "framework", "database"]),
        "mobile_development": (["mobile app", "ios", "android", "flutter", "react native", "mobile-first", "smartphone"], 
                             ["app_type", "target_platform", "language", "framework", "database"]),
        "game_development": (["game", "unity", "godot", "graphics", "2d", "3d", "game engine", "multiplayer", "player"], 
                            ["game_type", "target_platform", "graphics_style", "framework", "multiplayer"]),
        "api_backend": (["api", "rest", "graphql", "backend", "server", "microservice", "endpoints", "database"], 
                       ["api_type", "authentication", "language", "framework", "database"]),
        "data_analysis": (["data", "analysis", "analytics", "dataset", "pandas", "excel", "csv", "visualization", "dashboard", "report"],
                         ["data_source", "data_format", "analysis_type", "language", "output_format"]),
        "machine_learning": (["ml", "machine learning", "model", "training", "prediction", "neural", "tensorflow", "pytorch", "classification"],
                            ["problem_type", "dataset_size", "model_type", "framework", "deployment"]),
        "desktop_app": (["desktop", "windows", "electron", "wxpython", "tkinter", "gui", "application"],
                       ["app_purpose", "target_os", "language", "framework", "database"]),
    }
    
    # Score each task type
    scores = {}
    for task_type, (keywords, fields) in patterns.items():
        score = sum(1 for keyword in keywords if f" {keyword} " in lowered)
        scores[task_type] = score
    
    # Get highest scoring task type (default to generic if no match)
    detected_type = max(scores, key=scores.get) if max(scores.values()) > 0 else "generic"
    
    if detected_type == "generic":
        fields = ["task_scope", "target_audience", "language", "framework", "deployment"]
    else:
        fields = patterns[detected_type][1]
    
    return {
        "task_type": detected_type,
        "clarification_fields": fields,
        "keywords_matched": scores[detected_type] if detected_type != "generic" else 0
    }


def _generate_dynamic_clarification_questions(task_type: str, field: str) -> str:
    """Generate clarification question based on task type and field."""
    questions = {
        "web_development": {
            "site_type": "What kind of website? (landing page, web app, e-commerce site, dashboard, or content site?)",
            "target_platform": "Should it target desktop, mobile-first, or fully responsive web?",
            "language": "Which programming language? (Python, JavaScript, PHP, Java, C#, Go, Rust?)",
            "framework": "Which framework or library? (React, Vue, Angular, Django, Flask, Spring Boot?)",
            "database": "Should I use persistent storage? (SQLite, PostgreSQL, MySQL, MongoDB, or none?)",
        },
        "mobile_development": {
            "app_type": "What kind of mobile app? (productivity, games, social, utility, e-commerce?)",
            "target_platform": "iOS, Android, or both?",
            "language": "Which language? (Swift, Kotlin, JavaScript/React Native, Dart/Flutter?)",
            "framework": "Which framework? (React Native, Flutter, Native, Xamarin?)",
            "database": "Should I use persistent storage? (SQLite, Realm, Firebase, or none?)",
        },
        "game_development": {
            "game_type": "What genre? (2D, 3D, puzzle, action, strategy, RPG, simulation?)",
            "target_platform": "PC, Console, Web, or Mobile?",
            "graphics_style": "Art style? (pixel art, realistic, stylized, minimalist?)",
            "framework": "Which engine? (Unity, Unreal Engine, Godot, custom?)",
            "multiplayer": "Single-player or multiplayer?",
        },
        "api_backend": {
            "api_type": "REST API, GraphQL, or something else?",
            "authentication": "Authentication needed? (OAuth, JWT, API keys, none?)",
            "language": "Which language? (Python, Node.js, Go, Java, C#?)",
            "framework": "Which framework? (FastAPI, Express, Gin, Spring Boot?)",
            "database": "Which database? (PostgreSQL, MySQL, MongoDB, Redis?)",
        },
        "data_analysis": {
            "data_source": "Where's the data from? (CSV, Excel, API, Database, Web scraping?)",
            "data_format": "Data format? (CSV, JSON, Parquet, Raw text?)",
            "analysis_type": "What analysis? (Exploratory, Statistical, Predictive, Visualization?)",
            "language": "Which language? (Python, R, SQL, JavaScript?)",
            "output_format": "Output format? (Jupyter notebook, Dashboard, Report, HTML, PDF?)",
        },
        "machine_learning": {
            "problem_type": "Problem type? (Classification, Regression, Clustering, NLP, Computer Vision?)",
            "dataset_size": "Dataset size? (Small <1MB, Medium 1-100MB, Large >100MB?)",
            "model_type": "Preferred model? (Neural Network, Decision Tree, SVM, Random Forest, Transformer?)",
            "framework": "Which framework? (TensorFlow, PyTorch, Scikit-learn, XGBoost?)",
            "deployment": "How to deploy? (Cloud, On-premise, Mobile, Edge device?)",
        },
        "desktop_app": {
            "app_purpose": "What does the app do? (Productivity, Entertainment, Utility, System tool?)",
            "target_os": "Target OS? (Windows, Mac, Linux, All?)",
            "language": "Which language? (Python, C#, Java, C++, JavaScript?)",
            "framework": "Which framework? (Electron, PyQt, WinForms, GTK?)",
            "database": "Local storage needed? (SQLite, JSON files, none?)",
        },
    }
    
    # Get question or use generic fallback
    if task_type in questions and field in questions[task_type]:
        return questions[task_type][field]
    
    # Generic fallbacks
    generic_questions = {
        "task_scope": "What exactly do you want to build?",
        "target_audience": "Who is this for?",
        "language": "Which programming language?",
        "framework": "Which framework or library?",
        "deployment": "Where will this run?",
    }
    
    return generic_questions.get(field, f"Can you clarify the {field} details?")


def _suggestion_code_payload(suggestion: dict) -> tuple[str, str]:
    suggestion_type = str(suggestion.get("type") or suggestion.get("suggestion_type") or "")
    if suggestion_type in {"code", "code_modification"}:
        return str(suggestion.get("content", "")), str(suggestion.get("language", ""))
    return "", ""


def _legacy_suggestion_shape(suggestion: dict | None) -> dict:
    suggestion = dict(suggestion or {})
    return {
        "type": str(suggestion.get("type") or suggestion.get("suggestion_type") or "response"),
        "language": str(suggestion.get("language", "plain_text")),
        "content": str(suggestion.get("content", "")),
        "explanation": str(suggestion.get("explanation", "")),
        "provider": str(suggestion.get("provider", "template")),
        "confidence": suggestion.get("confidence"),
        "quality_score": suggestion.get("quality_score"),
        "safe_to_execute": suggestion.get("safe_to_execute"),
        "id": suggestion.get("id"),
        "strategy": suggestion.get("strategy"),
    }


def _extract_clarification_state(text: str, existing: dict | None = None, current_question: str = "") -> dict:
    existing = dict(existing or {})
    lowered = f" {text.lower()} "
    question = current_question.lower()
    normalized = lowered
    replacements = {
        " dashbaord ": " dashboard ",
        " e-commerece ": " e-commerce ",
        " e-commerence ": " e-commerce ",
        " ecommerece ": " ecommerce ",
        " c sharp ": " c# ",
        " c sharp. ": " c# ",
        " fullyresponsive ": " fully responsive ",
        " physicis ": " physics ",
        " aroung ": " around ",
    }
    for wrong, right in replacements.items():
        normalized = normalized.replace(wrong, right)
    normalized = re.sub(r"\s+", " ", normalized)
    choose_for_me = any(
        token in normalized
        for token in (
            " your choice ",
            " ur choice ",
            " you choose ",
            " choose for me ",
            " decide for me ",
            " pick for me ",
        )
    )
    unsure = any(
        token in normalized
        for token in (
            " i don't know ",
            " dont know ",
            " not sure ",
            " unsure ",
            " recommend ",
            " whatever ",
        )
    )
    if any(token in normalized for token in (" non programmable ", " non-programmable ", " no code ", " without code ", " just design ", " conceptual only ")):
        existing["language"] = "plain_text"
        existing["framework"] = "none"
        existing["storage"] = "none"
        existing["non_implementation"] = True
        existing["game_scope"] = "design_only"
        existing.pop("language_unsure", None)
        existing.pop("framework_unsure", None)
        existing.pop("storage_unsure", None)
        return existing
    if "platform" in question:
        for option in ("pc", "mobile", "web", "console"):
            if f" {option} " in normalized:
                existing["platform"] = option
                break
    if "should it run on web, desktop, mobile, terminal, backend" in question:
        for option in ("web", "desktop", "mobile", "terminal", "backend"):
            if f" {option} " in normalized:
                existing["target_surface"] = option
                break
        if " somewhere else " in normalized or " other " in normalized:
            existing["target_surface"] = "other"
    if "landing page, web app, e-commerce site, dashboard, or content site" in question:
        if " landing page " in normalized:
            existing["site_type"] = "landing_page"
        elif " web app " in normalized or " app " in normalized:
            existing["site_type"] = "web_app"
        elif " e-commerce " in normalized or " ecommerce " in normalized or " store " in normalized:
            existing["site_type"] = "ecommerce"
        elif " dashboard " in normalized:
            existing["site_type"] = "dashboard"
        elif " content site " in normalized or " blog " in normalized or " content " in normalized:
            existing["site_type"] = "content_site"
    if "target desktop, mobile-first, or fully responsive web" in question:
        if " desktop " in normalized:
            existing["platform"] = "desktop"
        elif " mobile-first " in normalized or " mobile first " in normalized:
            existing["platform"] = "mobile_first"
        elif " responsive " in normalized or " fully responsive web " in normalized or " fully responsive " in normalized:
            existing["platform"] = "responsive_web"
        elif " web " in normalized and " responsive" not in normalized:
            # User said "web" but didn't specify which type - offer default
            existing["platform"] = "responsive_web"
            existing["_assistant_message"] = (
                "Good! I'll use **responsive design** (works on all devices) - "
                "that's the most effective choice for modern web apps. Let's continue."
            )
    if "concept/design only" in question or "playable implementation" in question:
        if any(token in normalized for token in (" design ", " concept ", " conceptual ", " non programmable ", " no code ")):
            existing["game_scope"] = "design_only"
        elif any(token in normalized for token in (" playable ", " implementation ", " code ", " build it ")):
            existing["game_scope"] = "implementation"
    if "concept/design, a quick prototype, or a full working implementation" in question:
        if any(token in normalized for token in (" design ", " concept ", " conceptual ", " idea only ", " no code ")):
            existing["app_scope"] = "design_only"
            existing["non_implementation"] = True
        elif any(token in normalized for token in (" prototype ", " mvp ", " quick version ")):
            existing["app_scope"] = "prototype"
        elif any(token in normalized for token in (" implementation ", " full ", " working ", " build it ", " code ")):
            existing["app_scope"] = "implementation"
    if "single-player" in question or "multiplayer" in question:
        if " online multiplayer " in normalized or " online " in normalized:
            existing["player_mode"] = "online_multiplayer"
        elif " local multiplayer " in normalized or " local " in normalized:
            existing["player_mode"] = "local_multiplayer"
        elif " single player " in normalized or " single-player " in normalized:
            existing["player_mode"] = "single_player"
    if "language" in question and unsure:
        existing["language_unsure"] = True
        recommended_language = FRONTEND_CLARIFIER.recommended_language(existing)
        existing["language"] = recommended_language
        existing["auto_selected_field"] = "language"
        existing["_assistant_message"] = f"You said you do not know, so I will use {recommended_language} as the most practical default and continue."
        existing.pop("language_unsure", None)
    elif "language" in question and choose_for_me:
        recommended_language = FRONTEND_CLARIFIER.recommended_language(existing)
        existing["language"] = recommended_language
        existing["auto_selected_field"] = "language"
        existing["_assistant_message"] = f"I will use {recommended_language} and continue."
    if "framework" in question or "library" in question:
        existing.pop("language_unsure", None)
        if unsure:
            recommended_framework = FRONTEND_CLARIFIER.recommended_framework(str(existing.get("language", "plain_text")), existing)
            existing["framework"] = recommended_framework
            existing["auto_selected_field"] = "framework"
            existing["_assistant_message"] = f"You said you do not know, so I will use {recommended_framework} as the most effective default here and continue."
            existing.pop("framework_unsure", None)
        elif choose_for_me:
            recommended_framework = FRONTEND_CLARIFIER.recommended_framework(str(existing.get("language", "plain_text")), existing)
            existing["framework"] = recommended_framework
            existing["auto_selected_field"] = "framework"
            existing["_assistant_message"] = f"I will use {recommended_framework} and continue."
    if "storage" in question or "database" in question:
        existing.pop("framework_unsure", None)
        if unsure:
            recommended_storage = FRONTEND_CLARIFIER.recommended_storage(existing)
            existing["storage"] = recommended_storage
            existing["auto_selected_field"] = "storage"
            existing["_assistant_message"] = f"You said you do not know, so I will use {recommended_storage} as the most practical default and continue."
            existing.pop("storage_unsure", None)
        elif choose_for_me:
            recommended_storage = FRONTEND_CLARIFIER.recommended_storage(existing)
            existing["storage"] = recommended_storage
            existing["auto_selected_field"] = "storage"
            existing["_assistant_message"] = f"I will use {recommended_storage} and continue."

    language_map = {
        " python ": "python",
        " flask ": None,
        " django ": None,
        " fastapi ": None,
        " c# ": "csharp",
        " csharp ": "csharp",
        " c++ ": "cpp",
        " cpp ": "cpp",
        " javascript ": "javascript",
        " typescript ": "typescript",
        " java ": "java",
        " rust ": "rust",
        " go ": "go",
    }
    for token, value in language_map.items():
        if token in normalized and value is not None:
            existing["language"] = value
            existing.pop("language_unsure", None)
            break

    for framework in ("flask", "django", "fastapi", "react", "vue", "angular", "spring", "express"):
        if f" {framework} " in normalized:
            existing["framework"] = framework
            existing.pop("framework_unsure", None)
            break
    if any(token in normalized for token in (" plain java ", " plain python ", " plain javascript ", " plain typescript ", " no framework ", " without framework ")):
        existing["framework"] = "none"
        existing.pop("framework_unsure", None)

    if any(token in normalized for token in (" sqlite ", " mysql ", " postgres ", " postgresql ", " mongodb ", " database ", " db ")):
        if "sqlite" in normalized:
            existing["storage"] = "sqlite"
        elif "postgres" in normalized:
            existing["storage"] = "postgresql"
        elif "mysql" in normalized:
            existing["storage"] = "mysql"
        elif "mongodb" in normalized:
            existing["storage"] = "mongodb"
        else:
            existing["storage"] = "database"
        existing.pop("storage_unsure", None)
    if any(token in normalized for token in (" no database ", " without database ", " no db ", " in memory ")):
        existing["storage"] = "none"
        existing.pop("storage_unsure", None)
    return existing


def _is_clarification_help_request(text: str) -> bool:
    lowered = text.strip().lower()
    return any(
        phrase in lowered
        for phrase in (
            "what is",
            "what's",
            "whats",
            "what do you mean",
            "which one",
            "why",
            "explain",
            "help me choose",
            "tell me more",
            "define",
        )
    )


def _clarification_help_response(question: str) -> str:
    lowered = question.lower()
    if "framework" in lowered or "library" in lowered:
        return (
            "A framework or library is the toolkit I should build with. "
            "It affects project structure, dependencies, and how much code is already provided. "
            "If you do not care, I can recommend a sensible default for your language."
        )
    if "language" in lowered:
        return (
            "The programming language determines the syntax, ecosystem, and available frameworks. "
            "If you do not have a preference, I can recommend one based on the kind of system you want."
        )
    if "storage" in lowered or "database" in lowered:
        return (
            "Persistent storage means saving user data such as accounts and passwords. "
            "If this is just a prototype, SQLite is a simple default. If not, I can suggest another database."
        )
    return "I need that detail so I can generate a solution that matches your actual setup instead of guessing."


def _is_task_continuation_request(text: str) -> bool:
    lowered = text.strip().lower()
    return any(
        phrase in lowered
        for phrase in (
            "go ahead",
            "start",
            "give the code",
            "show the code",
            "do it",
            "continue",
            "proceed",
            "generate it",
            "build it",
        )
    )


def _detect_solution_choice(text: str, solution_options: list[dict] | None) -> dict | None:
    """Detect solution choice using new selector."""
    selector = SolutionSelector()
    selected = selector.extract_solution_choice(text, solution_options or [])
    return selected


def _build_session_task_context(
    original_input: str,
    task_info: dict | None,
    clarification_state: dict,
    solution_options: list[dict] | None = None,
    selected_solution: dict | None = None,
) -> dict:
    task_info = dict(task_info or {})
    return {
        "original_input": original_input,
        "task_type": task_info.get("task", ""),
        "objective": task_info.get("objective", original_input),
        "site_type": clarification_state.get("site_type"),
        "target_platform": clarification_state.get("platform") or clarification_state.get("target_surface"),
        "language": clarification_state.get("language") or task_info.get("language"),
        "framework": clarification_state.get("framework") or task_info.get("framework"),
        "database": clarification_state.get("storage") or task_info.get("storage"),
        "tool_type": clarification_state.get("tool_type"),
        "app_scope": clarification_state.get("app_scope") or clarification_state.get("game_scope"),
        "solution_options": list(solution_options or []),
        "solution_choice": dict(selected_solution or {}),
    }


def _implementation_context(session_task_context: dict, selected_solution: dict, memory: dict) -> dict:
    objective = str(session_task_context.get("objective") or session_task_context.get("original_input") or "the requested system")
    language = str(session_task_context.get("language") or "plain_text")
    framework = session_task_context.get("framework")
    storage = session_task_context.get("database")
    return {
        "task": "implementation_package",
        "language": language,
        "objective": objective,
        "framework": framework,
        "storage": storage,
        "strategy": selected_solution.get("strategy", "recommended"),
        "clarification_state": session_task_context,
        "conversation_history": list(memory.get("conversation_history", [])),
        "user_preferences": dict(memory.get("user_preferences", {})),
        "previous_code": str(memory.get("current_code", "")),
        "prompt_context": (
            "You are a coding copilot. "
            "Generate the full implementation package for the selected solution. "
            "Include system architecture, project structure, and starter code. "
            "Be concrete and continue the current task without asking the same questions again."
        ),
    }


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _merged_scores(base_scores: dict, llm_result: dict | None) -> tuple[dict, dict]:
    if not llm_result:
        return base_scores, {
            "enabled": False,
            "used": False,
            "reason": "No LLM result provided.",
        }

    merged = dict(base_scores)
    for key in ("stress", "cognitive_load", "engagement", "trust_in_ai"):
        candidate = llm_result.get(key)
        if not isinstance(candidate, dict):
            continue
        try:
            score = float(candidate.get("score"))
            prob = float(candidate.get("probability"))
            level = str(candidate.get("level"))
        except (TypeError, ValueError):
            continue
        merged[key] = {
            "level": level if level in {"low", "medium", "high"} else base_scores[key]["level"],
            "score": max(0.0, min(1.0, round(score, 3))),
            "probability": max(0.0, min(1.0, round(prob, 3))),
        }

    meta = {
        "enabled": True,
        "used": True,
        "reason": "Grok enrichment merged.",
        "confidence_adjustment": llm_result.get("confidence_adjustment"),
        "llm_explanation": llm_result.get("llm_explanation"),
    }
    return merged, meta


def _round3(value: float) -> float:
    return round(float(value), 3)


def _level_from_score(score: float) -> str:
    if score < 0.33:
        return "low"
    if score < 0.66:
        return "medium"
    return "high"


def _quality_score(event_count: int) -> float:
    return _round3(min(1.0, event_count / 80.0))


def _apply_quality(scores: dict, quality: float) -> dict:
    adjusted: dict = {}
    for key, item in scores.items():
        base_prob = float(item.get("probability", 0.5))
        damped_prob = 0.5 + (base_prob - 0.5) * quality
        adjusted[key] = {
            "level": item.get("level"),
            "score": _round3(float(item.get("score", 0.0))),
            "probability": _round3(max(0.0, min(1.0, damped_prob))),
        }
    return adjusted


def _feature_delta(current: float, baseline: float) -> float:
    if abs(baseline) < 1e-6:
        return 0.0
    return _round3((current - baseline) / abs(baseline))


def _trend_label(prev: float, current: float) -> str:
    delta = current - prev
    if delta > 0.08:
        return "increasing"
    if delta < -0.08:
        return "decreasing"
    return "stable"


def _recommendations(scores: dict, features: dict, trend: dict) -> list[str]:
    recs: list[str] = []
    if scores["stress"]["score"] >= 0.75:
        recs.append("Take a 60-90 second break and resume with a smaller sub-task.")
    if scores["cognitive_load"]["score"] >= 0.7:
        recs.append("Reduce simultaneous goals; process one prompt/edit cycle at a time.")
    if features.get("override_rate", 0.0) > 0.6:
        recs.append("Lower AI verbosity and request structured bullet outputs to reduce edits.")
    if features.get("backspace_ratio", 0.0) > 0.12:
        recs.append("Draft first, then edit in one pass to lower correction overhead.")
    if max(features.get("content_intensity_mean", 0.0), features.get("content_intensity_recent", 0.0)) >= 0.3:
        recs.append("Pause before sending and rewrite in neutral language for safer execution.")
    if features.get("insult_event_rate", 0.0) >= 0.2:
        recs.append("Enable approval-first mode and avoid auto-execution for this session.")
    if features.get("distrust_event_rate", 0.0) >= 0.4:
        recs.append("Trust is low; switch to human-approval mode for critical actions.")
    if trend.get("stress_trend") == "increasing":
        recs.append("Stress trend is rising; switch to checklist mode for the next 5 minutes.")
    if not recs:
        recs.append("Current interaction pattern is stable; continue with the same workflow.")
    return recs


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            _json_response(
                self,
                200,
                {
                    "name": "terminal_stress_ai",
                    "ok": True,
                    "model": model_version(),
                    "routes": [
                        "GET /health",
                        "GET /llm-test",
                        "POST /events",
                        "POST /survey/{session_id}",
                        "GET /profile/{user_id}",
                        "GET /memory/{session_id}",
                        "GET /task-memory/{session_id}",
                        "GET /autonomy-debug/{session_id}",
                        "GET /analysis/{session_id}",
                        "GET /session/{session_id}/timeline",
                        "POST /session/{session_id}/reset",
                    ],
                },
            )
            return

        if parsed.path == "/health":
            _json_response(self, 200, {"ok": True, "model": model_version()})
            return

        if parsed.path == "/llm-test":
            dummy_features = FeatureVector(
                {
                    "iki_mean": 260.0,
                    "iki_std": 120.0,
                    "pause_500ms_count": 3.0,
                    "pause_1500ms_count": 0.0,
                    "typing_cpm": 220.0,
                    "backspace_ratio": 0.05,
                    "override_rate": 0.2,
                    "hesitation_count": 1.0,
                }
            )
            base = MODEL.predict(dummy_features)
            llm = MODEL.llm_enrichment(dummy_features, base)
            _json_response(self, 200, {"ok": True, "model": model_version(), "llm_enrichment": llm})
            return

        if parsed.path.startswith("/profile/"):
            user_id = parsed.path.split("/profile/", 1)[1]
            profile = PREFERENCE_ENGINE.get_profile(user_id)
            if profile is None:
                _json_response(self, 404, {"error": "profile_not_found", "user_id": user_id})
            else:
                _json_response(self, 200, profile)
            return

        if parsed.path.startswith("/memory/"):
            session_id = parsed.path.split("/memory/", 1)[1]
            _json_response(self, 200, MEMORY_MANAGER.get_recent_context(session_id, limit=12))
            return

        if parsed.path.startswith("/task-memory/"):
            session_id = parsed.path.split("/task-memory/", 1)[1]
            _json_response(self, 200, TASK_MEMORY.get(session_id))
            return

        if parsed.path.startswith("/autonomy-debug/"):
            session_id = parsed.path.split("/autonomy-debug/", 1)[1]
            timeline = SESSION_ANALYSIS.get(session_id, [])
            if not timeline:
                _json_response(self, 404, {"error": "autonomy_debug_not_found", "session_id": session_id})
                return
            latest = timeline[-1]
            _json_response(
                self,
                200,
                {
                    "session_id": session_id,
                    "timestamp": latest.get("timestamp"),
                    "fused_trust_score": latest.get("fused_trust_score"),
                    "risk_severity_scores": latest.get("risk_severity_scores"),
                    "autonomy_decision": latest.get("autonomy_decision"),
                    "shared_autonomy": latest.get("shared_autonomy"),
                    "shared_autonomy_explanation": latest.get("shared_autonomy_explanation"),
                    "action_manager": latest.get("action_manager"),
                },
            )
            return

        if parsed.path.startswith("/session/") and parsed.path.endswith("/timeline"):
            session_id = parsed.path.split("/session/", 1)[1].rsplit("/timeline", 1)[0]
            timeline = SESSION_ANALYSIS.get(session_id, [])
            _json_response(
                self,
                200,
                {
                    "session_id": session_id,
                    "points": len(timeline),
                    "timeline": timeline[-50:],
                },
            )
            return

        if parsed.path.startswith("/analysis/"):
            session_id = parsed.path.split("/analysis/", 1)[1]
            events = SESSIONS.get(session_id, [])
            vec = extract_features(events)
            base_scores = MODEL.predict(vec)
            llm_info = MODEL.llm_enrichment(vec, base_scores)
            if llm_info.get("used"):
                scores, llm_meta = _merged_scores(base_scores, llm_info.get("result"))
            else:
                scores = base_scores
                llm_meta = llm_info
            quality = _quality_score(len(events))
            scores = _apply_quality(scores, quality)
            enough_for_indicators = len(events) >= MIN_EVENTS_FOR_INDICATORS
            if enough_for_indicators:
                indicators = MODEL.explain_indicators(vec)
            else:
                indicators = [f"Insufficient data for stable behavioral indicators ({len(events)}/{MIN_EVENTS_FOR_INDICATORS} events)."]
            history = SESSION_ANALYSIS.get(session_id, [])
            enough_for_trend = len(events) >= MIN_EVENTS_FOR_TREND
            if history and enough_for_trend:
                first = history[0]
                prev = history[-1]
                baseline_features = first.get("feature_snapshot", {})
                baseline = {
                    "iki_mean_delta": _feature_delta(vec.values.get("iki_mean", 0.0), float(baseline_features.get("iki_mean", 0.0))),
                    "typing_cpm_delta": _feature_delta(vec.values.get("typing_cpm", 0.0), float(baseline_features.get("typing_cpm", 0.0))),
                    "backspace_ratio_delta": _feature_delta(
                        vec.values.get("backspace_ratio", 0.0), float(baseline_features.get("backspace_ratio", 0.0))
                    ),
                }
                trend = {
                    "stress_trend": _trend_label(float(prev["stress"]["score"]), float(scores["stress"]["score"])),
                    "load_trend": _trend_label(float(prev["cognitive_load"]["score"]), float(scores["cognitive_load"]["score"])),
                }
            else:
                baseline = {
                    "iki_mean_delta": 0.0,
                    "typing_cpm_delta": 0.0,
                    "backspace_ratio_delta": 0.0,
                }
                trend = {
                    "stress_trend": "stable",
                    "load_trend": "stable",
                }

            recommendations = _recommendations(scores, vec.values, trend)
            if not enough_for_trend:
                recommendations = [f"Collect more interaction data before trend actions ({len(events)}/{MIN_EVENTS_FOR_TREND} events)."]
            trust_data = TRUST_BRIDGE.analyze(events, vec.values)
            trust_engine_score = float(trust_data["trust"]["trust_score"])
            code_context = CODE_CONTEXT_ANALYZER.analyze(events)
            suggestion_quality = SUGGESTION_TRACKER.analyze(events, vec.values)
            fused_trust = TRUST_FUSION.fuse(scores["trust_in_ai"], trust_data["trust"])
            # Use stabilized fused trust everywhere downstream.
            aligned_trust = float(fused_trust["score"])
            distrust_recent = float(vec.values.get("distrust_recent", 0.0))
            distrust_rate = float(vec.values.get("distrust_event_rate", 0.0))
            profanity_rate = float(vec.values.get("profanity_event_rate", 0.0))
            intensity_recent = float(vec.values.get("content_intensity_recent", 0.0))
            # Hard cap trust under explicit distrust/hostile context.
            if distrust_recent >= 1.0:
                aligned_trust = min(aligned_trust, 0.45)
            elif distrust_rate >= 0.4:
                aligned_trust = min(aligned_trust, 0.55)
            elif profanity_rate > 0.3 or intensity_recent >= 0.6:
                aligned_trust = min(aligned_trust, 0.6)
            scores["trust_in_ai"]["score"] = _round3(max(0.0, min(1.0, aligned_trust)))
            scores["trust_in_ai"]["level"] = _level_from_score(scores["trust_in_ai"]["score"])
            scores["trust_in_ai"]["probability"] = _round3(
                max(0.0, min(1.0, min(float(fused_trust["probability"]), quality + 0.5)))
            )
            risk_data = RISK_ANALYZER.analyze(scores, vec.values, quality, trust_engine_score)
            risk_flags = risk_data["risk_flags"]
            risk_severity_scores = risk_data["risk_severity_scores"]
            scenario = risk_data["interaction_scenario"]
            autonomy_policy = risk_data["autonomy_policy"]
            adaptive_recs = risk_data["safety_actions"]
            user_id = session_id
            preference_data = PREFERENCE_ENGINE.update_user_profile(
                user_id=user_id,
                session_id=session_id,
                features=vec.values,
                trust_signals=trust_data["signals"],
                scores=scores,
            )
            user_intent = INTENT_PREDICTOR.predict(events, vec.values, code_context)
            line_events = [e for e in events if e.get("key") == "Enter" and e.get("line_text") is not None]
            if line_events:
                MEMORY_MANAGER.add_user_message(session_id, str(line_events[-1].get("line_text", "")))
            existing_user_memory = USER_PROFILE_MEMORY.get(user_id)
            previous_trust_history = existing_user_memory.get("trust_history", [])
            previous_trust_score = float(previous_trust_history[-1]) if previous_trust_history else float(scores["trust_in_ai"]["score"])
            MEMORY_MANAGER.update_task_context(
                session_id,
                {
                    "language": code_context.get("language"),
                    "file_type": code_context.get("file_type"),
                    "intent": user_intent,
                    "active_task": str(user_intent.get("task", "")),
                },
            )
            current_message = str(line_events[-1].get("line_text", "")) if line_events else ""
            recent_context = MEMORY_MANAGER.get_recent_context(session_id, limit=12)
            pending_clarification = dict(recent_context.get("task_context", {}).get("pending_clarification", {}))
            last_frontend_task = dict(recent_context.get("task_context", {}).get("last_frontend_task", {}))
            session_task_context = dict(recent_context.get("task_context", {}).get("frontend_session_context", {}))
            clarification_state = dict(pending_clarification.get("answers", {}))
            frontend_task_input = current_message
            clarification_help_message = ""
            selected_solution = None
            solution_set = []  # Initialize to empty - dual-AI pipeline will populate if needed
            
            # Detect task type on first user message
            if not clarification_state.get("_task_type") and current_message and not pending_clarification.get("required"):
                task_info = _detect_task_type(current_message)
                clarification_state["_task_type"] = task_info["task_type"]
                clarification_state["_clarification_fields"] = task_info["clarification_fields"]
                session_task_context["_task_type"] = task_info["task_type"]
            
            # Use task-specific required fields or fallback to stored ones
            task_type = clarification_state.get("_task_type", "generic")
            required_fields = clarification_state.get("_clarification_fields", ["site_type", "target_platform", "language", "framework", "storage"])
            
            # Check if all required clarification fields are already answered
            all_fields_answered = all(clarification_state.get(field) for field in required_fields)
            if all_fields_answered and pending_clarification.get("required"):
                # All questions already answered - mark clarification as complete
                pending_clarification["required"] = False
                pending_clarification["questions"] = []
            
            # Determine current phase
            clarification_required_phase = bool(pending_clarification.get("required", False))
            awaiting_risk_inputs_phase = bool(pending_clarification.get("_awaiting_risk_inputs", False))
            awaiting_solution_selection_phase = bool(session_task_context.get("_awaiting_solution_selection", False))
            
            if clarification_required_phase:
                current_question = str(next(iter(pending_clarification.get("questions", [])), ""))
                frontend_task_input = str(pending_clarification.get("original_input", current_message))
                parsed_state = _extract_clarification_state(current_message, clarification_state, current_question)
                if parsed_state != clarification_state:
                    clarification_help_message = str(parsed_state.pop("_assistant_message", "")).strip()
                    parsed_state.pop("auto_selected_field", None)
                    clarification_state = parsed_state
                    # Save answers to persistent task context
                    TASK_CONTEXT_MANAGER.update_multiple(session_id, clarification_state)
                elif _is_clarification_help_request(current_message):
                    clarification_help_message = _clarification_help_response(current_question)
                else:
                    clarification_state = parsed_state
            elif awaiting_risk_inputs_phase:
                # User is providing risk inputs (3 numbers for complexity, time_pressure, team_capacity)
                risk_values = re.findall(r'\d+', current_message)
                if len(risk_values) >= 3:
                    clarification_state["_risk_complexity"] = int(risk_values[0])
                    clarification_state["_risk_time_pressure"] = int(risk_values[1])
                    clarification_state["_risk_team_capacity"] = int(risk_values[2])
                    clarification_state["risk_inputs_collected"] = True
                    TASK_CONTEXT_MANAGER.update_multiple(session_id, clarification_state)
                    # Transition to solution selection phase
                    pending_clarification["_awaiting_risk_inputs"] = False
                else:
                    clarification_help_message = "Please provide 3 numbers (1-10 each) for:\n1. Complexity, 2. Time pressure, 3. Team experience\nExample: 5 7 3"
            elif awaiting_solution_selection_phase:
                selected_solution = _detect_solution_choice(current_message, list(session_task_context.get("_generated_solutions_list", [])))
                if selected_solution is None and _is_task_continuation_request(current_message):
                    selected_solution = dict(session_task_context.get("solution_choice") or {})
                    if not selected_solution:
                        selected_solution = dict(session_task_context.get("_generated_solutions_list", [])[0]) if session_task_context.get("_generated_solutions_list") else None
            elif session_task_context.get("solution_options"):
                selected_solution = _detect_solution_choice(current_message, list(session_task_context.get("solution_options", [])))
                if selected_solution is None and _is_task_continuation_request(current_message):
                    selected_solution = dict(session_task_context.get("solution_choice") or {})
                    if not selected_solution:
                        selected_solution = dict(session_task_context.get("solution_options", [])[0]) if session_task_context.get("solution_options") else None
            elif last_frontend_task and _is_task_continuation_request(current_message):
                frontend_task_input = str(last_frontend_task.get("original_input", current_message))
                clarification_state = dict(last_frontend_task.get("answers", {}))
            validation = VALIDATION_ENGINE.validate(
                session_id=session_id,
                predicted_stress=float(scores["stress"]["score"]),
                predicted_load=float(scores["cognitive_load"]["score"]),
                predicted_trust=float(scores["trust_in_ai"]["score"]),
            )
            system_metrics = SYSTEM_METRICS.record_and_summarize(
                session_id=session_id,
                validation=validation,
                suggestion_quality=suggestion_quality,
                trust_score=float(scores["trust_in_ai"]["score"]),
            )
            trust_signals = dict(trust_data["signals"])
            trust_signals["trust_delta"] = round(float(scores["trust_in_ai"]["score"]) - previous_trust_score, 3)
            frontend_memory = {
                "current_code": MEMORY_MANAGER.get_last_generated_code(session_id),
                "conversation_history": MEMORY_MANAGER.get_recent_context(session_id, limit=12).get("short_term_memory", []),
                "user_preferences": preference_data["user_preferences"],
            }
            if selected_solution is not None:
                implementation_context = _implementation_context(session_task_context, selected_solution, frontend_memory)
                implementation_result = FRONTEND_LLM.generate(implementation_context)
                frontend_result = {
                    "task_info": {
                        "task": str(session_task_context.get("task_type", "software_development")),
                        "language": str(session_task_context.get("language", "plain_text")),
                        "objective": str(session_task_context.get("objective", frontend_task_input)),
                        "framework": session_task_context.get("framework"),
                        "storage": session_task_context.get("database"),
                        "clarification_state": clarification_state,
                    },
                    "clarification_required": False,
                    "questions": [],
                    "suggestions": [],
                    "suggestion": implementation_result,
                }
                clarification_required = False
                clarification_questions = []
                solution_set = []
            else:
                # Only call FRONTEND_COPILOT if clarification is not already complete
                if not all_fields_answered:
                    frontend_result = FRONTEND_COPILOT.process_input(
                        frontend_task_input,
                        session_id=session_id,
                        user_id=user_id,
                        memory=frontend_memory,
                        behavioral_signals=events,
                        clarification_state=clarification_state,
                    )
                    clarification_required = bool(frontend_result.get("clarification_required"))
                    clarification_questions = list(frontend_result.get("questions", []))
                else:
                    # Clarification already complete - mark as such
                    frontend_result = {}
                    clarification_required = False
                    clarification_questions = []
                # Note: DO NOT generate suggestions here - let the dual-AI pipeline handle it below
                solution_set = []
            MEMORY_MANAGER.update_task_context(
                session_id,
                {
                    "pending_clarification": {
                        "required": clarification_required,
                        "questions": clarification_questions,
                        "answers": clarification_state,
                        "original_input": frontend_task_input,
                        # Preserve dual-AI pipeline flags even when clarification is done
                        "_awaiting_risk_inputs": pending_clarification.get("_awaiting_risk_inputs", False),
                        "_risk_inputs_provided": pending_clarification.get("_risk_inputs_provided", False),
                    },
                    "last_frontend_task": {
                        "original_input": frontend_task_input,
                        "answers": clarification_state,
                    }
                    if frontend_task_input and not clarification_required
                    else last_frontend_task,
                    "frontend_session_context": _build_session_task_context(
                        frontend_task_input,
                        frontend_result.get("task_info", {}),
                        clarification_state,
                        solution_options=solution_set if not clarification_required else session_task_context.get("solution_options", []),
                        selected_solution=selected_solution if selected_solution is not None else session_task_context.get("solution_choice", {}),
                    ),
                },
            )
            if clarification_required:
                # Use enhanced clarification engine for better explanations
                current_question = str(next(iter(clarification_questions or []), ""))
                
                # Map question text to field name
                question_to_field = {
                    "landing page": "site_type",
                    "web app": "site_type",
                    "e-commerce": "site_type",
                    "dashboard": "site_type",
                    "content site": "site_type",
                    "target": "platform",
                    "desktop": "platform",
                    "mobile": "platform",
                    "responsive": "platform",
                    "language": "language",
                    "framework": "framework",
                    "library": "framework",
                    "storage": "database",
                    "database": "database",
                }
                
                # Find matching field for current question
                current_field = None
                for keyword, field in question_to_field.items():
                    if keyword.lower() in current_question.lower():
                        current_field = field
                        break
                
                # Build enhanced clarification text
                if current_field and not clarification_help_message:
                    clarification_text = EnhancedClarificationEngine.format_question_with_explanation(current_field)
                elif clarification_help_message:
                    clarification_text = clarification_help_message
                else:
                    clarification_text = (
                        "I need a bit more detail:\n\n" + "\n".join(
                            f"{idx}. {question}" for idx, question in enumerate(clarification_questions, start=1)
                        )
                    )
                
                suggestion = {
                    "type": "clarification",
                    "language": "plain_text",
                    "content": "",
                    "explanation": clarification_text,
                    "provider": "planner_ai",
                }
                task_understanding = frontend_result.get("task_info", {})
                cognitive_state = COGNITIVE_STATE_MODEL.build(
                    scores=scores,
                    fused_trust=fused_trust,
                    risk_severity=risk_severity_scores,
                    suggestion_quality=suggestion_quality,
                )
                autonomy_decision = {
                    "mode": "suggest_only",
                    "reason": "Task details are incomplete; waiting for clarification before generating solutions.",
                    "confidence": 0.95,
                    "autonomy_mode": "AI_ASSIST",
                }
                autonomy_confidence = 0.95
                shared_autonomy = {
                    "autonomy_mode": "SHARED_CONTROL",
                    "autonomy_score": 0.0,
                    "confidence": 0.95,
                    "reason": "Clarification is required before any action can be taken.",
                }
                shared_autonomy_explanation = {
                    "explanation": clarification_text,
                    "signal_summary": "awaiting_clarification",
                }
                action_manager = {
                    "status": "awaiting_clarification",
                    "execution_mode": "SHARED_CONTROL",
                    "human_required": True,
                    "payload": {"questions": clarification_questions},
                    "reason": "The request is underspecified, so the system is asking clarification questions first.",
                }
                assistant_message = clarification_help_message
            # Check if initial clarification is done but risk inputs haven't been collected yet
            elif not clarification_required and not selected_solution and not clarification_state.get("risk_inputs_collected") and not pending_clarification.get("_awaiting_risk_inputs"):
                # STEP 1: Use Middle AI to analyze behavior and build risk assessment
                task_context_for_analysis = {
                    "site_type": clarification_state.get("site_type", "web_app"),
                    "target_platform": clarification_state.get("target_platform", "responsive_web"),
                    "language": clarification_state.get("language", "python"),
                    "framework": clarification_state.get("framework", "none"),
                    "database": clarification_state.get("storage", "none"),
                }
                
                # Analyze user behavior
                behavior_analysis = MIDDLE_AI.analyze_user_behavior(events, vec.values)
                
                # Extract survey data
                survey_data = MIDDLE_AI.extract_survey_data(
                    nasa_tlx=scores.get("nasa_tlx", {}),
                    trust_survey=scores.get("trust_survey", {}),
                )
                
                # Calculate risk factors
                risk_assessment = MIDDLE_AI.calculate_risk_factors(
                    task_context_for_analysis,
                    behavior_analysis,
                    survey_data,
                )
                
                # Build risk display for user
                risk_display = f"""
MIDDLE AI RISK ASSESSMENT
========================

Overall Risk Score: {risk_assessment.get('overall_risk_score', 0.5):.2f} / 1.0

Behavioral Risks (System-Calculated):
{json.dumps(risk_assessment.get('behavioral_risks', {}), indent=2)}

Technical Risks (System-Calculated):
{json.dumps(risk_assessment.get('technical_risks', {}), indent=2)}

Now I need your input on project factors to refine the recommendation.
Please respond with these values (1-10 scale):
1. Project complexity? (1=simple, 10=massive)
2. Time pressure? (1=relaxed, 10=urgent deadline)  
3. Team experience level? (1=new developers, 10=expert team)
"""
                
                # Store risk assessment in session for next step
                session_task_context["_middle_ai_analysis"] = {
                    "behavior_analysis": behavior_analysis,
                    "survey_data": survey_data,
                    "risk_assessment": risk_assessment,
                    "task_context": task_context_for_analysis,
                }
                
                # Mark that we're awaiting risk inputs
                pending_clarification["_awaiting_risk_inputs"] = True
                pending_clarification["required"] = False
                pending_clarification["answers"] = clarification_state
                
                suggestion = {
                    "type": "risk_assessment",
                    "language": "plain_text",
                    "content": "",
                    "explanation": risk_display,
                    "provider": "middle_ai",
                }
                task_understanding = frontend_result.get("task_info", {})
                cognitive_state = COGNITIVE_STATE_MODEL.build(
                    scores=scores,
                    fused_trust=fused_trust,
                    risk_severity=risk_severity_scores,
                    suggestion_quality=suggestion_quality,
                )
                autonomy_decision = {
                    "mode": "suggest_only",
                    "reason": "Risk assessment complete. Collecting user input for shared control.",
                    "confidence": 0.90,
                    "autonomy_mode": "SHARED_CONTROL",
                }
                autonomy_confidence = 0.90
                shared_autonomy = {
                    "autonomy_mode": "SHARED_CONTROL",
                    "autonomy_score": 0.5,
                    "confidence": 0.90,
                    "reason": "Waiting for user to provide project risk factors (complexity, time pressure, team capacity).",
                }
                shared_autonomy_explanation = {
                    "explanation": risk_display,
                    "signal_summary": "awaiting_user_risk_inputs",
                }
                action_manager = {
                    "status": "awaiting_risk_inputs",
                    "execution_mode": "SHARED_CONTROL",
                    "human_required": True,
                    "payload": {"risk_assessment": risk_assessment},
                    "reason": "Collecting user input for dynamic shared control.",
                }
                assistant_message = risk_display
                solution_set = []  # ENSURE no solutions are shown during Middle AI phase
            # Check if risk inputs are provided - extract them from user's response
            elif not clarification_required and not selected_solution and clarification_state.get("risk_inputs_collected"):
                # Extract risk values from clarification state
                user_risk_inputs = {
                    "project_complexity": clarification_state.get("_risk_complexity", 5),
                    "time_pressure": clarification_state.get("_risk_time_pressure", 5),
                    "team_capacity": clarification_state.get("_risk_team_capacity", 5),
                }
                
                # Get stored Middle AI analysis
                middle_ai_data = session_task_context.get("_middle_ai_analysis", {})
                
                # STEP 2: Create prompt for Generator AI
                generator_prompt = MIDDLE_AI.create_prompt_for_generator(
                    task_context=middle_ai_data.get("task_context", {}),
                    risk_assessment=middle_ai_data.get("risk_assessment", {}),
                    behavior_analysis=middle_ai_data.get("behavior_analysis", {}),
                    user_risk_inputs=user_risk_inputs,
                )
                
                # STEP 3: Generate solutions with Generator AI
                generated_solutions = GENERATOR_AI.generate_solutions(generator_prompt)
                
                # Build display for three solutions
                solution_display = f"""
GENERATOR AI: 3 SOLUTION OPTIONS
===============================

MIDDLE AI PROMPT (sent to Generator AI):
{json.dumps(generator_prompt, indent=2)}

---

Risk Analysis Summary:
- Overall Risk: {generator_prompt.get('overall_risk_score', 0.5):.2f}
- Risk Level: {generator_prompt.get('risk_level', 'MEDIUM')}
- Recommended: {generator_prompt.get('recommended_strategy', 'optimized').upper()}
- Reasoning: {generator_prompt.get('strategy_reasoning', '')}

Strategy Constraints Applied:
{json.dumps(generator_prompt.get('solution_constraints', {}), indent=2)}

---

"""
                
                for idx, sol in enumerate(generated_solutions, start=1):
                    recommended_mark = " ✓ RECOMMENDED" if sol.get("recommended") else ""
                    solution_display += f"""
{idx}. {sol.get('title', 'Solution')}{recommended_mark}
   Strategy: {sol.get('strategy', 'unknown')}
   Description: {sol.get('description', '')}
   
   Architecture:
{sol.get('architecture', 'N/A')}
   
   Effort: {sol.get('effort', 'Unknown')}
   Scalability: {sol.get('scalability', 'Unknown')}
   Maintenance: {sol.get('maintenance', 'Unknown')}
   
   Tech Stack:
{json.dumps(sol.get('tech_stack', {}), indent=2)}
   
   Risk Mitigation: {sol.get('risk_mitigation', 'N/A')}

---

"""
                
                solution_display += "\nWhich solution? (1=Simple, 2=Optimized, 3=Scalable)"
                
                # Store solutions for selection phase
                session_task_context["_generated_solutions"] = generated_solutions
                session_task_context["_generated_solutions_list"] = generated_solutions
                session_task_context["_generator_prompt"] = generator_prompt
                session_task_context["_awaiting_solution_selection"] = True
                
                solution_set = [_legacy_suggestion_shape({
                    "type": "solution",
                    "strategy": sol.get("strategy"),
                    "id": sol.get("id"),
                    "content": sol.get("architecture", ""),
                    "explanation": f"{sol.get('title')}\n{sol.get('description')}\nEffort: {sol.get('effort')}",
                }) for sol in generated_solutions]
                
                suggestion = {
                    "type": "solutions",
                    "language": "plain_text",
                    "content": "",
                    "explanation": solution_display,
                    "provider": "generator_ai",
                }
                task_understanding = frontend_result.get("task_info", {})
                cognitive_state = COGNITIVE_STATE_MODEL.build(
                    scores=scores,
                    fused_trust=fused_trust,
                    risk_severity=risk_severity_scores,
                    suggestion_quality=suggestion_quality,
                )
                autonomy_decision = {
                    "mode": "suggest_only",
                    "reason": "Three solution options generated. Waiting for user selection.",
                    "confidence": 0.95,
                    "autonomy_mode": "SHARED_CONTROL",
                }
                autonomy_confidence = 0.95
                shared_autonomy = {
                    "autonomy_mode": "SHARED_CONTROL",
                    "autonomy_score": 0.5,
                    "confidence": 0.95,
                    "reason": "Generator AI produced three solutions. User must select one.",
                }
                shared_autonomy_explanation = {
                    "explanation": solution_display,
                    "signal_summary": "awaiting_solution_selection",
                }
                action_manager = {
                    "status": "solution_selection_pending",
                    "execution_mode": "SHARED_CONTROL",
                    "human_required": True,
                    "payload": {"solutions": generated_solutions},
                    "reason": "Three solution options generated. Waiting for user to select one.",
                }
                assistant_message = solution_display
            else:
                controller_output = CONTEXTFLOW_CONTROLLER.handle_task_input(
                    session_id=session_id,
                    user_id=user_id,
                    task_input=frontend_task_input if selected_solution is None else str(session_task_context.get("original_input", frontend_task_input)),
                    current_code=MEMORY_MANAGER.get_last_generated_code(session_id),
                    behavioral_signals=events,
                )
                scores = controller_output["scores"]
                trust_data["trust"] = controller_output["trust_engine"]
                trust_data["signals"] = controller_output["trust_signals"]
                suggestion = _legacy_suggestion_shape(frontend_result.get("suggestion")) or controller_output["llm_suggestion"]
                task_understanding = frontend_result.get("task_info", {}) or controller_output["task_understanding"]
                cognitive_state = controller_output["cognitive_state"]
                autonomy_decision = frontend_result.get("contextflow_decision", {}).get("autonomy_decision", controller_output["autonomy_decision"])
                autonomy_confidence = float(autonomy_decision.get("confidence", 0.5))
                shared_autonomy = frontend_result.get("contextflow_decision", {}).get("shared_autonomy", controller_output["shared_autonomy"])
                shared_autonomy_explanation = frontend_result.get("contextflow_decision", {}).get(
                    "shared_autonomy_explanation",
                    controller_output["shared_autonomy_explanation"],
                )
                action_manager = frontend_result.get("action_manager", controller_output["action_manager"])
                suggestion_quality = controller_output["suggestion_quality"]
                fused_trust = controller_output["fused_trust"]
                risk_severity_scores = controller_output["risk_analysis"]["risk_severity_scores"]
                preference_data["user_preferences"] = controller_output["user_preferences"]
                preference_data["profile"] = controller_output["user_profile"]
                if selected_solution is not None:
                    assistant_message = str(suggestion.get("content", "")).strip() or str(suggestion.get("explanation", ""))
                else:
                    assistant_message = str(suggestion.get("explanation", ""))
            
            # Add ContextFlow status to assistant message
            status_line = STATUS_FORMATTER.format_inline_status(
                trust_score=float(fused_trust.get("score", 0.0)),
                risk_level=max(risk_severity_scores.values()) if risk_severity_scores else 0.0,
                autonomy_mode=shared_autonomy.get("autonomy_mode", "SHARED_CONTROL"),
            )
            assistant_message = assistant_message + status_line if assistant_message else status_line
            adaptive_ai_policy = POLICY_ENGINE.build(
                scores=scores,
                trust_engine=trust_data["trust"],
                intent=user_intent,
                user_preferences=preference_data["user_preferences"],
                autonomy_policy=autonomy_policy,
            )
            adaptive_recs = adaptive_recs + [
                item for item in preference_data["adaptive_ai_behavior"] if item not in adaptive_recs
            ]
            suggestion_code, suggestion_language = _suggestion_code_payload(suggestion)
            MEMORY_MANAGER.add_ai_response(
                session_id=session_id,
                content=str(suggestion.get("explanation", "")),
                code=suggestion_code,
                language=suggestion_language,
            )
            conversation_memory = MEMORY_MANAGER.get_full_memory_snapshot(session_id)
            task_memory = TASK_MEMORY.update(
                session_id=session_id,
                active_task=str(task_understanding.get("active_task", "")),
                language=str(suggestion.get("language") or code_context.get("language", "")),
                generated_code=suggestion_code,
                suggestion=suggestion,
                reasoning_state=str(shared_autonomy_explanation.get("explanation", "")),
                reasoning_trace={
                    "task_understanding": task_understanding,
                    "autonomy": shared_autonomy,
                    "cognitive_state": cognitive_state,
                },
            )
            policy_learning = POLICY_LEARNING.update(
                user_id=user_id,
                session_id=session_id,
                suggestion_quality=suggestion_quality,
                trust_signals=trust_signals,
                trust_score=float(scores["trust_in_ai"]["score"]),
                validation=validation,
                autonomy_mode=str(shared_autonomy.get("autonomy_mode", "SHARED_CONTROL")),
                action_result=action_manager,
            )
            user_profile_memory = USER_PROFILE_MEMORY.update(
                user_id=user_id,
                trust_score=float(scores["trust_in_ai"]["score"]),
                success_metric=float(validation.get("model_accuracy", 0.0)) if validation else 0.0,
                preferences=preference_data["user_preferences"],
                baseline=preference_data["profile"],
                interaction_pattern={
                    "task": task_understanding.get("active_task"),
                    "autonomy_mode": shared_autonomy.get("autonomy_mode"),
                    "suggestion_quality": suggestion_quality.get("suggestion_quality_score"),
                },
                policy_signal=policy_learning,
            )
            point = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stress": scores["stress"],
                "cognitive_load": scores["cognitive_load"],
                "engagement": scores["engagement"],
                "trust_in_ai": scores["trust_in_ai"],
                "trust_engine": trust_data["trust"],
                "fused_trust_score": fused_trust,
                "interaction_scenario": scenario,
                "risk_severity_scores": risk_severity_scores,
                "feature_snapshot": vec.values,
                "code_context": code_context,
                "conversation_memory": conversation_memory,
                "task_memory": task_memory,
                "suggestion": suggestion,
                "suggestions": solution_set,
                "clarification_required": clarification_required,
                "clarification_questions": clarification_questions,
                "assistant_message": assistant_message,
                "user_intent": user_intent,
                "task_understanding": task_understanding,
                "cognitive_state": cognitive_state,
                "user_preferences": preference_data["user_preferences"],
                "autonomy_decision": autonomy_decision,
                "shared_autonomy": shared_autonomy,
                "shared_autonomy_explanation": shared_autonomy_explanation,
                "action_manager": action_manager,
            }
            history.append(point)
            SESSION_ANALYSIS[session_id] = history[-200:]

            _json_response(
                self,
                200,
                {
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "model": model_version(),
                    "stress": scores["stress"],
                    "cognitive_load": scores["cognitive_load"],
                    "engagement": scores["engagement"],
                    "trust_in_ai": scores["trust_in_ai"],
                    "quality": {
                        "event_count": len(events),
                        "quality_score": quality,
                        "min_events_for_trend": MIN_EVENTS_FOR_TREND,
                        "trend_reliable": enough_for_trend,
                        "min_events_for_indicators": MIN_EVENTS_FOR_INDICATORS,
                        "indicators_reliable": enough_for_indicators,
                    },
                    "baseline_delta": baseline,
                    "trend": trend,
                    "risk_flags": risk_flags,
                    "risk_severity_scores": risk_severity_scores,
                    "code_context": code_context,
                    "conversation_memory": conversation_memory,
                    "task_memory": task_memory,
                    "feature_snapshot": vec.values,
                    "cognitive_state": cognitive_state,
                    "suggestion_quality": suggestion_quality,
                    "suggestion": suggestion,
                    "suggestions": solution_set,
                    "clarification_required": clarification_required,
                    "clarification_questions": clarification_questions,
                    "assistant_message": assistant_message,
                    "user_profile": preference_data["profile"],
                    "user_profile_memory": user_profile_memory,
                    "user_preferences": preference_data["user_preferences"],
                    "baseline_delta_analysis": preference_data["baseline_delta_analysis"],
                    "baseline_learning": {
                        "in_learning_phase": preference_data["baseline_learning_phase"],
                        "sessions_observed": preference_data["baseline_learning_sessions"],
                        "minimum_sessions": 3,
                    },
                    "trust_engine": trust_data["trust"],
                    "trust_engine_signals": trust_data["signals"],
                    "fused_trust_score": fused_trust,
                    "user_intent": user_intent,
                    "task_understanding": task_understanding,
                    "interaction_scenario": scenario,
                    "autonomy_policy": autonomy_policy,
                    "adaptive_ai_policy": adaptive_ai_policy,
                    "autonomy_decision": autonomy_decision,
                    "autonomy_confidence": autonomy_confidence,
                    "shared_autonomy": shared_autonomy,
                    "shared_autonomy_explanation": shared_autonomy_explanation,
                    "user_trust_trend": system_metrics.get("user_trust_trend", "stable"),
                    "decision_smoothing_state": shared_autonomy.get("decision_smoothing_state", {}),
                    "action_manager": action_manager,
                    "policy_learning": policy_learning,
                    "indicators": indicators,
                    "recommendations": recommendations,
                    "adaptive_recommendations": adaptive_recs,
                    "explanation": "Estimated from typing tempo, pauses, correction behavior, and AI override interaction.",
                    "llm_enrichment": llm_meta,
                    "validation": validation,
                    "system_metrics": system_metrics,
                },
            )
            return

        _json_response(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/survey/"):
            session_id = parsed.path.split("/survey/", 1)[1]
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(content_length)
                data = json.loads(raw.decode("utf-8"))
                nasa = NasaTlxSurvey(**data["nasa_tlx"])
                trust = TrustSurvey(**data["trust"])
            except Exception as exc:
                _json_response(self, 400, {"error": "invalid_survey_payload", "detail": str(exc)})
                return

            stored = VALIDATION_ENGINE.save_survey(session_id, nasa, trust)
            _json_response(self, 200, {"ok": True, "session_id": session_id, "survey_scores": stored})
            return

        if parsed.path.startswith("/session/") and parsed.path.endswith("/reset"):
            session_id = parsed.path.split("/session/", 1)[1].rsplit("/reset", 1)[0]
            SESSIONS[session_id] = []
            SESSION_ANALYSIS[session_id] = []
            MEMORY_MANAGER.reset(session_id)
            TASK_MEMORY.reset(session_id)
            TASK_CONTEXT_MANAGER.reset(session_id)
            _json_response(self, 200, {"ok": True, "session_id": session_id, "reset": True})
            return

        if parsed.path != "/events":
            _json_response(self, 404, {"error": "not_found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            _json_response(self, 400, {"error": "invalid_json", "detail": str(exc)})
            return

        session_id = str(data.get("session_id", "")).strip()
        events = data.get("events", [])

        if not session_id:
            _json_response(self, 400, {"error": "session_id_required"})
            return
        if not isinstance(events, list):
            _json_response(self, 400, {"error": "events_must_be_list"})
            return

        existing = SESSIONS.get(session_id, [])
        existing.extend(events)
        SESSIONS[session_id] = existing[-600:]

        _json_response(
            self,
            200,
            {"stored": len(events), "session_events": len(SESSIONS[session_id])},
        )


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Server running on http://{host}:{port}")
    print("Endpoints: GET /health, GET /llm-test, POST /events, POST /survey/{session_id}, GET /profile/{user_id}, GET /memory/{session_id}, GET /task-memory/{session_id}, GET /autonomy-debug/{session_id}, GET /analysis/{session_id}, GET /session/{session_id}/timeline, POST /session/{session_id}/reset")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run(host=args.host, port=args.port)
