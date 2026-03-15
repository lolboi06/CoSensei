"""
CoSensei API Service — Fully conversational AI pipeline (Grok-powered)
No numbered menus. No static templates. Pure chat.

Stages:
  clarification  → grok-3-mini asks contextual questions
  solutions      → grok-3 proposes tailored approaches, user picks by saying anything
  code_gen       → grok-3 generates real file tree + code, asks for feedback
  risk_review    → grok-3 analyzes risks on rejection
  risk_control   → HIGH risk: user guides, grok-3 regenerates
  complete       → delivered
"""

import sys
import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from implementation_generator import ImplementationGenerator

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
_CFG_PATH = os.path.join(os.path.dirname(__file__), '..', '.terminal_stress_ai_config.json')
try:
    with open(_CFG_PATH) as _f:
        _CFG = json.load(_f)
except Exception:
    _CFG = {}

_KEY      = _CFG.get('generator_ai', {}).get('api_key') or _CFG.get('grok_api_key', '')
_MDL_FAST = _CFG.get('generator_ai', {}).get('model', 'grok-3-mini')
_MDL_BEST = _CFG.get('second_ai',    {}).get('model', 'grok-3')


# --------------------------------------------------------------------------- #
# Grok client
# --------------------------------------------------------------------------- #
class GrokClient:
    ENDPOINT = "https://api.x.ai/v1/chat/completions"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model   = model

    def chat(self, system: str, user: str,
             max_tokens: int = 2000, temperature: float = 0.65) -> str:
        if not self.api_key:
            return ""
        try:
            import requests
            r = requests.post(
                self.ENDPOINT,
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"},
                json={"model": self.model,
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user",   "content": user}],
                      "max_tokens": max_tokens, "temperature": temperature},
                timeout=45,
            )
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content'].strip()
            print(f"[Grok {self.model}] HTTP {r.status_code}: {r.text[:200]}")
            return ""
        except Exception as exc:
            print(f"[Grok {self.model}] error: {exc}")
            return ""

    def json_chat(self, system: str, user: str, max_tokens: int = 3500) -> Optional[Dict]:
        raw = self.chat(system, user, max_tokens, temperature=0.2)
        if not raw:
            return None
        for extract in [
            lambda t: json.loads(t),
            lambda t: json.loads(re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', t).group(1)),
            lambda t: json.loads(re.search(r'\{[\s\S]+\}', t, re.DOTALL).group(0)),
        ]:
            try:
                return extract(raw)
            except Exception:
                pass
        print(f"[Grok] JSON parse failed. Raw: {raw[:300]}")
        return None


# --------------------------------------------------------------------------- #
# Service
# --------------------------------------------------------------------------- #
class CoSenseiAPIService:

    def __init__(self):
        self.fast  = GrokClient(_KEY, _MDL_FAST)
        self.best  = GrokClient(_KEY, _MDL_BEST)
        self.impl  = ImplementationGenerator()
        self.sessions: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    # Session management
    # ------------------------------------------------------------------ #
    def create_session(self, user_id: str, chat_id: str) -> Dict[str, Any]:
        s = {
            "chat_id": chat_id, "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "messages": [], "history": [],
            "task_context": {}, "solutions": None,
            "selected_solution": None, "generated_code": None,
            "risks": None, "stage": "clarification",
        }
        self.sessions[chat_id] = s
        return s

    def process_message(self, message: str, chat_id: str, user_id: str) -> Dict[str, Any]:
        if chat_id not in self.sessions:
            self.create_session(user_id, chat_id)

        s = self.sessions[chat_id]
        s["messages"].append({"role": "user", "content": message,
                               "timestamp": datetime.now().isoformat()})
        s["history"].append({"role": "user", "content": message})

        stage = s["stage"]
        try:
            if   stage == "clarification": resp = self._clarify(message, s)
            elif stage == "solutions":     resp = self._route_solutions(message, s)
            elif stage == "code_gen":      resp = self._route_code_gen(message, s)
            elif stage == "risk_review":   resp = self._route_risk(message, s)
            elif stage == "risk_control":  resp = self._risk_control(message, s)
            elif stage == "complete":      resp = self._route_complete(message, s)
            else:                          resp = "Something went wrong. Say 'new' to start fresh."
        except Exception as exc:
            print(f"[CoSensei] stage={stage} error: {exc}")
            resp = "I hit an unexpected error. Please try again or say 'new' to start fresh."

        s["messages"].append({"role": "assistant", "content": resp,
                               "timestamp": datetime.now().isoformat()})
        s["history"].append({"role": "assistant", "content": resp})

        return {"message": resp, "chat_id": chat_id,
                "stage": s["stage"], "timestamp": datetime.now().isoformat()}

    # ================================================================== #
    # INTENT DETECTION — understands natural language at every stage
    # ================================================================== #
    _SYS_INTENT = """You are an intent classifier for CoSensei, a software architecture AI.

Given the current stage and user message, classify the intent.

Return ONLY valid JSON:
{
  "intent": "one of the valid intents listed below",
  "solution_index": null or 0 | 1 | 2  (0-based, only when intent is select_solution),
  "sentiment": "positive | negative | neutral",
  "key_info": "brief summary of what the user said / wants"
}

Valid intents per stage:
- clarification stage: "provide_info" | "question" | "greeting" | "new_project"
- solutions stage:     "select_solution" | "question" | "new_project" | "more_info"
- code_gen stage:      "accept" | "reject" | "question" | "new_project"
- risk_review stage:   "apply_fixes" | "accept_anyway" | "more_direction" | "new_project"
- risk_control stage:  "direction_given" | "question" | "new_project"
- complete stage:      "new_project" | "question" | "exit"

For select_solution: match "first/simple/1/one" -> 0, "second/middle/optimized/2/two" -> 1, "third/scalable/enterprise/3" -> 2
For accept: "yes/good/great/looks good/perfect/ok/sure/accept/approved/go with it/do it" -> accept
For reject: "no/nope/bad/wrong/change/not right/don't like/redo/different/refactor" -> reject"""

    def _detect_intent(self, stage: str, message: str, s: Dict) -> Dict:
        """Use grok-3-mini to understand what the user means."""
        history_snippet = self._hist(s["history"][-6:])
        prompt = f"Stage: {stage}\nRecent conversation:\n{history_snippet}\n\nUser message: \"{message}\"\n\nClassify intent. Return JSON."
        result = self.fast.json_chat(self._SYS_INTENT, prompt, 300)
        if result:
            return result
        # Fallback: simple keyword matching
        return self._keyword_intent(stage, message)

    def _keyword_intent(self, stage: str, message: str) -> Dict:
        m = message.lower().strip()
        if any(w in m for w in ("new", "start over", "restart", "fresh")):
            return {"intent": "new_project", "solution_index": None, "key_info": m}
        if stage == "solutions":
            for patterns, idx in [
                (["1", "first", "simple", "one", "easy", "quick"], 0),
                (["2", "second", "middle", "optimized", "medium"], 1),
                (["3", "third", "enterprise", "scalable", "last"], 2),
            ]:
                if any(p in m for p in patterns):
                    return {"intent": "select_solution", "solution_index": idx, "key_info": m}
        if stage == "code_gen":
            if any(w in m for w in ("yes", "ok", "good", "great", "perfect", "accept", "sure", "do it")):
                return {"intent": "accept", "key_info": m}
            if any(w in m for w in ("no", "bad", "wrong", "change", "reject", "redo", "different")):
                return {"intent": "reject", "key_info": m}
        return {"intent": "question", "solution_index": None, "key_info": m}

    # ================================================================== #
    # STAGE 1 — CLARIFICATION
    # ================================================================== #
    _SYS_CLARIFY = """You are CoSensei — a senior software architect with strong opinions and genuine curiosity. You talk like a brilliant, direct teammate who actually cares about getting the architecture RIGHT — not a form-filler.

Your job: understand the user's project DEEPLY before generating anything. Generic questions = generic architecture. Curiosity = great architecture.

=== CURIOSITY PROTOCOL — follow this order STRICTLY ===

LEVEL 1 — Vision (must know before anything else):
  • What SPECIFICALLY does it do? (not "predict things" — "predict blood glucose 30 min ahead from CGM readings")
  • WHO uses it daily? (diabetics self-monitoring? doctors reviewing patient panels? nurses in a ward?)
  • What PROBLEM does it solve RIGHT NOW for those users?

LEVEL 2 — Domain depth (ask these for specific domains before touching tech):
  • Health/Medical: Where does the data come from? (wearable, manual entry, lab results, EHR?)
                    Is there an existing ML model or do they want to build one from scratch?
                    Who makes decisions based on the predictions? (patient, doctor, automated alert?)
  • AI/ML apps:     What's the input data and where does it live? (CSV? live stream? user-uploaded?)
                    Existing model or need to train? If existing — what format? (pickle? ONNX? API?)
                    What does "good prediction" look like — what's the acceptable error margin?
  • Ecommerce:      What are you selling? Physical products, digital, subscriptions, or marketplace?
                    Single vendor or multi-vendor? Do you already have products/inventory?
  • Wildlife:       What sensors/data sources? (GPS collar, camera trap, satellite, ranger reports?)
                    Real-time alerts or periodic analysis? Who acts on the data?
  • SaaS/Platform:  What does the user DO in the app every day? Walk me through one session.
                    Freemium or paid from day 1? Any existing competitors you're benchmarked against?

LEVEL 3 — Scope signals (ask only after Level 1+2 are clear):
  • Scale: is this for 10 users (internal tool), 1000 (community), or 100k+ (consumer)?
  • MVP or full product? What's the ONE feature you ship first?
  • Any hard constraints: deadline, budget, existing tech they're locked into?

LEVEL 4 — Tech (ask LAST, only if not obvious from the above):
  • Platform: only ask if the domain doesn't make it obvious
  • Language: only ask if Level 1-3 didn't make Python/JS/etc. the clear choice
  • Stack: suggest strongly based on what you've learned, don't just ask

=== WHEN TO SET needs_clarification=false ===
You need ALL of these before proceeding:
  1. You can write a SPECIFIC one-sentence summary (not "a health app" — "a blood glucose prediction web app for Type 2 diabetics using CGM data")
  2. You know WHO the primary users are and what they're trying to accomplish
  3. You have at least one domain-depth answer (data source, scale, MVP scope, or existing model)
  If any of these is missing or vague → needs_clarification=true

Return ONLY valid JSON:
{
  "needs_clarification": true | false,
  "response": "Your reply — warm, curious, direct. React to what they said (show you understood), then ask ONE sharp follow-up that uncovers the most important missing piece. Never ask two questions at once. If false: get genuinely excited about the specific vision, confirm what you understood, then say you're spinning up options.",
  "detected": {
    "project_name": "exact brand/product name if mentioned — empty string if none",
    "project_type": "",
    "platform": "",
    "language": "",
    "framework": "",
    "database": "",
    "features": [],
    "audience": "",
    "scale": "small | medium | large | enterprise",
    "summary": "one SPECIFIC sentence: what this is, what it does exactly, who it's for"
  }
}

Personality rules:
- Sound like a brilliant senior dev who's genuinely curious, not a chatbot running through a form.
- React to what the user said before asking. "Sugar level prediction — oh interesting, this is a health AI project." then ask the specific follow-up.
- When something is vague, call it out warmly but be SPECIFIC about what's missing: "Love it, but 'predict sugar levels' could mean 10 different things — are you predicting from blood test results, from a CGM wearable stream, from food intake logs, or something else?"
- NEVER ask "What platform?" or "What language?" until you understand the domain deeply.
- NEVER ask "What is X?" for animals, species, nature terms, food, medical terms, or geography — these are the domain.
- DO ask "What is [Name]?" for unknown software products, startups, or brands you've never heard of.
- Ask ONE question at a time. Always. No bullet lists of questions.
- When the user answers a question, acknowledge it specifically before asking the next one.
- Your questions should NARROW the design space, not just collect fields.

Tone examples:
  User: "I want to predict sugar levels"
  → "Blood glucose prediction — nice, this is a health AI project. Who's the main user here? Are diabetics tracking their own levels day-to-day, or is this more like a clinical tool for doctors monitoring a patient panel?"

  User: "build me an ecommerce website"
  → "Ecommerce — love it! What are we selling and who's buying? A single-brand store for one seller is very different from a multi-vendor marketplace. Give me the pitch."

  User: "I want to track tigers in a national park"
  → "Wildlife conservation tech — great problem space! Who's actually using this on the ground: rangers getting real-time alerts, or researchers doing post-hoc movement analysis? That changes the architecture significantly."

  User: "I need a platform for HARO"
  → "HARO — tell me more? Is this a brand/product you're building, cloning, or integrating with? Quick description and I'll have everything I need."

  User: "we are building a deadly ass website to predict sugar level ukwim"
  → "Blood glucose prediction — yeah I'm with you, this is a health AI project. Couple of things I need to know to design this right: are users entering their readings manually (like logging after a finger prick), or is this pulling from a CGM device automatically? And who's the main user — patients tracking themselves, or doctors monitoring multiple patients?"\""""

    # Pure-greeting / small-talk word sets — word-boundary safe
    _GREETING_EXACT = {
        "hi", "hello", "hey", "yo", "sup", "hiya", "howdy", "greetings",
        "hi there", "hello there", "good morning", "good afternoon",
        "good evening", "what's up", "whats up", "hey there",
    }
    _GREETING_WORDS = {"hi", "hello", "hey", "yo", "sup", "hiya", "howdy"}
    _YOU_WORDS      = {"you", "u", "ur", "are"}

    def _is_small_talk(self, message: str) -> bool:
        """Word-boundary safe small-talk detector."""
        cleaned = message.lower().strip().rstrip("!?., ")
        if cleaned in self._GREETING_EXACT:
            return True
        words = set(cleaned.split())
        n = len(words)
        # Short greeting words
        if n <= 5 and words & self._GREETING_WORDS:
            return True
        # "who/what are you", "what is cosensei"
        if n <= 7 and words & {"who", "what"} and words & self._YOU_WORDS | {"cosensei", "sensei"}:
            return True
        # "how are you", "how r u"
        if n <= 5 and {"how"} & words and words & self._YOU_WORDS:
            return True
        # Personal / affectionate questions about CoSensei (not project-related)
        # e.g. "can i call you sensei", "are you an ai", "nice to meet you"
        personal_indicators = {"call", "name", "nickname", "sensei", "nice", "meet",
                                "pleasure", "thanks", "thank", "cool", "awesome", "love"}
        project_indicators  = {"build", "create", "make", "app", "api", "website", "system",
                                "need", "want", "develop", "code", "project"}
        if n <= 10 and words & personal_indicators and not words & project_indicators:
            return True
        return False

    _INTRO = (
        "Yo! I'm CoSensei — part senior architect, part code sherpa, full-time obsessed with building things right.\n\n"
        "Tell me about your project — the idea, the problem you're solving, who it's for. "
        "Don't worry about the tech yet, just talk to me like you'd pitch it to a teammate.\n\n"
        "What are we building?"
    )

    _PERSONAL_RESPONSES = {
        "sensei":  (
            "Ha — yeah, Sensei works. I've been called worse.\n\n"
            "I'm your AI architect. You bring the idea, I figure out the stack, "
            "design the system, and hand you working starter code. No fluff.\n\n"
            "So — what are we shipping today?"
        ),
        "name": (
            "CoSensei. Think of me as the senior dev you wished was on your team — "
            "the one who's actually excited about your project and won't gatekeep the architecture decisions.\n\n"
            "What are you building?"
        ),
        "who": (
            "I'm CoSensei — an AI software architect.\n\n"
            "Here's my deal: you describe an idea (messy is fine, I'm used to it), "
            "I ask a few sharp questions, then I hand you 3 tailored architecture options, "
            "pick your favorite, and generate real working code for it — not pseudocode, not templates, actual files.\n\n"
            "I also flag risks, show you what to watch out for, and stay in the conversation "
            "if you want to iterate. Built-in autonomy engine too — I adjust how much I drive vs. "
            "how much I defer to you based on how the session goes.\n\n"
            "Now — what's the project?"
        ),
        "nice": (
            "Good to meet you! I don't do small talk well but I'm genuinely great at system design.\n\n"
            "What are we building?"
        ),
        "thanks": (
            "Always. That's what I'm here for.\n\n"
            "Got another project knocking around in your head? Let's go."
        ),
        "cool": (
            "Appreciate that! I do try.\n\n"
            "Alright — what's next? Got a project idea you've been sitting on?"
        ),
        "default": (
            "Let's build something. What's the idea?"
        ),
    }

    def _small_talk_response(self, message: str) -> str:
        words = set(message.lower().split())
        if words & {"sensei", "call"}:           return self._PERSONAL_RESPONSES["sensei"]
        if words & {"who", "what", "cosensei"}:  return self._PERSONAL_RESPONSES["who"]
        if words & {"name", "nickname"}:         return self._PERSONAL_RESPONSES["name"]
        if words & {"nice", "meet", "pleasure"}:  return self._PERSONAL_RESPONSES["nice"]
        if words & {"thanks", "thank"}:           return self._PERSONAL_RESPONSES["thanks"]
        if words & {"cool", "awesome", "love", "great"}:  return self._PERSONAL_RESPONSES["cool"]
        return self._PERSONAL_RESPONSES["default"] if words & {"sensei"} else self._INTRO

    def _clarify(self, message: str, s: Dict) -> str:
        # Handle greetings / small talk — word-boundary safe, no API call needed
        if self._is_small_talk(message):
            return self._small_talk_response(message)

        history = self._hist(s["history"][:-1])
        prompt  = f"Conversation so far:\n{history or '(first message)'}\n\nUser: {message}"

        data = self.fast.json_chat(self._SYS_CLARIFY, prompt, 900)
        if data is None:
            return self._smart_fallback(message, s)

        detected = data.get("detected", {})
        s["task_context"].update({k: v for k, v in detected.items() if v})
        s["task_context"]["raw_input"] = message

        response = data.get("response", "")
        if not response:
            response = "Interesting — tell me more. What's the core problem this solves, and who's using it?"

        if not data.get("needs_clarification", True):
            s["stage"] = "solutions"
            solutions_text = self._gen_solutions(message, s)
            return response.rstrip(".!") + ".\n\n" + solutions_text

        return response

    # ================================================================== #
    # STAGE 2 — SOLUTION GENERATION + SELECTION
    # ================================================================== #
    _SYS_SOLUTIONS = """You are CoSensei, a senior software architect.

Generate exactly 3 solution tiers for the user's project. Return ONLY valid JSON:
{
  "intro": "One natural sentence introducing the options, referencing the project by name if known",
  "solutions": [
    {
      "name": "Project-and-domain-specific title that references what the user is building",
      "tier": "simple",
      "description": "2-3 sentences about THIS specific project — what it does, who uses it, why this approach fits",
      "tech_stack": "Specific tech for this project, comma-separated",
      "timeline": "X-Y weeks",
      "effort": "Low",
      "risk_score": 0.20,
      "phases": [
        { "name": "Phase 1: Name", "tasks": ["task specific to this project", "task", "task"] }
      ]
    },
    { "tier": "optimized", "effort": "Medium", "risk_score": 0.38, ... },
    { "tier": "scalable",  "effort": "High",   "risk_score": 0.55, ... }
  ],
  "closing": "Conversational closing sentence — reference the project domain specifically"
}

Rules:
- If the user mentioned a product/brand name (e.g. HARO, Trello clone, Notion), include it in EVERY solution name.
  Good: "HARO Reporter Platform MVP", "HARO Production Platform", "Enterprise HARO Network"
  Bad:  "Live Tracking MVP", "Simple Implementation", "Web App MVP"
- If no brand name: use the domain + key feature. E.g. "Reporter Query Marketplace MVP" not "Web App MVP"
- tech_stack must match the user's stated language/platform preference
- phases and tasks must be specific to THIS project's domain — not generic web app steps
- description must mention what the app specifically does (not just "production-ready with caching")
- risk_score: float 0.0-1.0
- closing must NOT say 'type 1, 2 or 3' — reference the actual options by what they do
- Tone: enthusiastic senior dev, not a sales brochure. "Option 1 gets you live fast with minimal drama. Option 3 is for if you're serious about scale from day one." That kind of energy."""

    def _gen_solutions(self, message: str, s: Dict) -> str:
        ctx = s.get("task_context", {})
        ctx.setdefault("raw_input", message)

        data = self.best.json_chat(
            self._SYS_SOLUTIONS,
            f"Project context:\n{json.dumps(ctx, indent=2)}\n\nConversation:\n{self._hist(s['history'])}",
            4000,
        )

        if data and isinstance(data.get("solutions"), list) and len(data["solutions"]) >= 2:
            solutions = data["solutions"]
            intro   = data.get("intro",   "Here are three approaches for your project:")
            closing = data.get("closing", "Which direction feels right for you?")
        else:
            print("[CoSensei] Solutions JSON failed — fallback")
            solutions = self._fallback_solutions(ctx)
            intro   = "Here are three approaches I'd recommend:"
            closing = "Which direction feels right for you?"

        for i, sol in enumerate(solutions):
            sol.setdefault("risk_score", [0.2, 0.38, 0.55][i] if i < 3 else 0.4)
            sol.setdefault("phases", [])
            if "name" not in sol and "title" in sol:
                sol["name"] = sol["title"]

        s["solutions"] = solutions

        risk_label = lambda r: "LOW risk" if r < 0.4 else "MEDIUM risk" if r < 0.7 else "HIGH risk"

        lines = [intro, ""]
        for i, sol in enumerate(solutions, 1):
            name = sol.get("name") or sol.get("title", f"Option {i}")
            tech = sol.get("tech_stack", "")
            risk = sol.get("risk_score", 0.3)
            t    = (tech[:80] + "...") if len(tech) > 83 else tech
            lines.append(f"Option {i} — {name}")
            lines.append(f"  {sol.get('description', '')}")
            if t: lines.append(f"  Stack: {t}")
            lines.append(f"  Timeline: {sol.get('timeline','TBD')} | Effort: {sol.get('effort','Medium')} | {risk_label(risk)}")
            lines.append("")

        lines.append(closing)
        return "\n".join(lines)

    def _route_solutions(self, message: str, s: Dict) -> str:
        solutions = s.get("solutions", [])
        intent    = self._detect_intent("solutions", message, s)
        action    = intent.get("intent", "question")

        if action == "new_project":
            return self._reset(s)

        if action == "select_solution":
            idx = intent.get("solution_index")
            if idx is not None and 0 <= idx < len(solutions):
                s["selected_solution"] = solutions[idx]
                s["stage"] = "code_gen"
                return self._generate_code(s)
            # Couldn't determine which — ask naturally
            return "Which option are you leaning towards? Feel free to describe what appeals to you."

        if action == "more_info":
            # User wants to know more about options before deciding
            return self._explain_solutions(message, s)

        # It's a question or unclear — answer conversationally using AI
        return self._conversational_answer("solutions", message, s)

    def _explain_solutions(self, message: str, s: Dict) -> str:
        solutions = s.get("solutions", [])
        sol_text  = json.dumps([{"name": sol.get("name"), "tech": sol.get("tech_stack"),
                                  "phases": sol.get("phases")} for sol in solutions], indent=2)
        prompt    = (f"The user asked: \"{message}\"\n\nSolutions presented:\n{sol_text}\n\n"
                     f"Answer their question naturally and helpfully. End by asking which option they prefer.")
        answer = self.fast.chat(
            "You are CoSensei, a helpful software architect. Answer the user's question about the proposed solutions. Be concise and conversational.",
            prompt, 800
        )
        return answer if answer else "Happy to explain! Which option would you like more details on?"

    # ================================================================== #
    # CODE GENERATION — real files + directory tree
    # ================================================================== #
    _SYS_CODEGEN = """You are CoSensei's code generation AI (grok-3).

Generate complete, runnable starter code for the selected project.

Return ONLY valid JSON:
{
  "intro": "One sentence: 'Here's your [project name] starter — [key highlight]'",
  "directory_tree": "ASCII tree of the complete project structure",
  "files": [
    {
      "path": "relative/path/file.ext",
      "language": "python | javascript | typescript | sql | dockerfile | yaml | toml | ...",
      "content": "COMPLETE file content — real, runnable code. No placeholders like 'add your logic here'.",
      "description": "what this file does"
    }
  ],
  "run_commands": ["step-by-step shell commands to install and run"],
  "env_setup": "environment setup instructions",
  "closing": "Conversational question like 'Does this match what you had in mind, or would you like me to change anything?'"
}

Rules:
- Generate 5-8 key files with REAL, complete code
- Entry point, core logic, models/schemas, routes/controllers, config, tests (at least one)
- Language and framework must match the selected tech stack exactly
- No pseudocode. No '# TODO'. No '...' placeholders.
- run_commands must be real commands that actually work"""

    def _generate_code(self, s: Dict) -> str:
        sol = s["selected_solution"]
        ctx = s.get("task_context", {})

        data = self.best.json_chat(
            self._SYS_CODEGEN,
            f"Project: {ctx.get('summary', ctx.get('raw_input', ''))}\n"
            f"Solution: {sol.get('name','')}\nDescription: {sol.get('description','')}\n"
            f"Tech stack: {sol.get('tech_stack','')}\nTimeline: {sol.get('timeline','')}\n"
            f"Context:\n{json.dumps(ctx, indent=2)}",
            5000,
        )

        # If Grok unavailable, generate real code offline
        if data is None:
            data = self._offline_codegen(sol, ctx)

        artifacts = self.impl.generate_implementation(sol, ctx)
        s["generated_code"] = data

        name  = sol.get("name") or "your project"
        tech  = sol.get("tech_stack", "")
        phases = sol.get("phases", [])

        # ---- Assemble step-by-step response ----
        # Step 1: Show roadmap + project structure only, then prompt
        framework = next((v for v in ["FastAPI", "Django", "Flask", "Express", "NestJS", "Spring", "Rails", "Gin"]
                          if v.lower() in tech.lower()), "Flask")
        db_name   = next((v for v in ["MongoDB", "PostgreSQL", "MySQL", "SQLite", "Redis"]
                          if v.lower() in tech.lower()), "PostgreSQL")
        tree      = data.get("directory_tree", "").strip() if data else ""

        # Build files dict for on-demand delivery
        files = {}
        if data:
            for f in data.get("files", []):
                path    = f.get("path", "file")
                content = f.get("content", "").strip()
                if content:
                    files[path] = content
        # Also include artifact files
        for label, key, _ in [
            ("requirements.txt",  "requirements_txt",    ""),
            (".env.example",      "env_template",        ""),
            ("schema.sql",        "database_schema_sql", ""),
            ("Dockerfile",        "dockerfile",          ""),
        ]:
            content = artifacts.get(key, "")
            if content and label not in files:
                files[label] = content.strip()

        # run_cmd and env_content for full delivery
        run_cmd = ""
        if data and data.get("run_commands"):
            run_cmd = "\n".join(f"  $ {cmd}" for cmd in data["run_commands"])
        env_content = artifacts.get("env_template", data.get("env_setup", "") if data else "")

        risk_score  = sol.get("risk_score", 0.4)
        risk_label  = "LOW" if risk_score < 0.4 else "MED" if risk_score < 0.7 else "HIGH"
        risk_badge  = f"[{risk_label}]"
        autonomy    = "[AUTO_EXECUTE]" if risk_score < 0.3 else "[SHARED_CONTROL]" if risk_score < 0.6 else "[SUGGEST_ONLY]"

        # ── Overview table ──────────────────────────────────────────────
        r  = f"**{name}** — implementation ready.\n\n"
        r += "OVERVIEW\n" + "-" * 50 + "\n"
        r += "| Property | Value |\n"
        r += "|---|---|\n"
        r += f"| **Solution** | {name} |\n"
        r += f"| **Tech Stack** | {sol.get('tech_stack', tech)} |\n"
        r += f"| **Framework** | {framework} |\n"
        r += f"| **Database** | {db_name} |\n"
        r += f"| **Timeline** | {sol.get('timeline','TBD')} |\n"
        r += f"| **Effort** | {sol.get('effort','Medium')} |\n"
        r += f"| **Risk** | {risk_badge} {risk_score:.0%} |\n"
        r += f"| **Autonomy Mode** | {autonomy} |\n"
        r += f"| **Files Generated** | {len(files)} files |\n"

        # ── Roadmap table ───────────────────────────────────────────────
        if phases:
            r += "\nROADMAP\n" + "-" * 50 + "\n"
            r += "| Phase | Key Tasks |\n"
            r += "|---|---|\n"
            for ph in phases:
                tasks_str = ", ".join(ph.get("tasks", [])[:3])
                r += f"| **{ph.get('name','Phase')}** | {tasks_str} |\n"

        # ── Files table ─────────────────────────────────────────────────
        if files:
            r += "\nFILES\n" + "-" * 50 + "\n"
            r += "| File | Purpose |\n"
            r += "|---|---|\n"
            desc_map = {}
            if data:
                for f in data.get("files", []):
                    desc_map[f.get("path","")] = f.get("description", "")
            for path in files:
                desc = desc_map.get(path, path.split("/")[-1].replace("_"," ").replace(".py",""))
                r += f"| `{path}` | {desc} |\n"

        # ── Project structure ───────────────────────────────────────────
        if tree:
            r += "\nPROJECT STRUCTURE\n" + "-" * 50 + "\n```\n" + tree + "\n```\n"

        # ── Autonomy status ─────────────────────────────────────────────
        r += "\nAUTONOMY ENGINE\n" + "-" * 50 + "\n"
        r += "| Mode | Trust | Stress | Action |\n"
        r += "|---|---|---|---|\n"
        r += f"| {autonomy} | High | Low | AI generates full implementation |\n"
        r += "\n`autonomy_engine.py` is included in the generated files.\n"

        # Store full file contents in session for on-demand delivery
        s["_pending_files"]    = files
        s["_pending_run"]      = run_cmd
        s["_pending_env"]      = env_content
        s["_pending_risk"]     = self._static_risk_scan(sol, ctx, data)
        s["_pending_manual"]   = self._manual_tasks_required(ctx)
        s["_pending_shown"]    = False

        r += "\n" + "-" * 50
        r += "\nAll implementation files are ready. Say **yes** to see the full code,\n"
        r += "or ask about any file, phase, or component above."

        return r

    def _route_code_gen(self, message: str, s: Dict) -> str:
        intent = self._detect_intent("code_gen", message, s)
        action = intent.get("intent", "question")

        if action == "new_project":
            return self._reset(s)

        # Deliver pending files if user says yes / show me / ready
        if s.get("_pending_files") and not s.get("_pending_shown"):
            m_low = message.lower()
            wants_files = (action == "accept" or
                           any(kw in m_low for kw in ["yes", "show", "code", "ready", "all", "file", "give", "see"]))
            # Check for specific file request
            specific = next((f for f in s["_pending_files"] if f.split("/")[-1].lower() in m_low), None)
            if specific or wants_files:
                files_to_show = {specific: s["_pending_files"][specific]} if specific else s["_pending_files"]
                out = ""
                for path, content in files_to_show.items():
                    lang = "python" if path.endswith(".py") else "dockerfile" if "Dockerfile" in path else "text"
                    out += f"\nFILE: {path}\n```{lang}\n{content}\n```\n"
                if not specific:
                    # Full delivery — also show run, env, risk, manual
                    out += "\nHOW TO RUN\n" + "-"*50 + "\n" + s["_pending_run"] + "\n"
                    out += "\nENV TEMPLATE\n" + "-"*50 + "\n```\n" + s["_pending_env"] + "\n```\n"
                    out += "\n" + s["_pending_risk"]
                    out += "\n\n" + s["_pending_manual"]
                    s["_pending_shown"] = True
                return out.strip() or "Here are the files above."

        if action == "accept":
            s["stage"] = "complete"
            return ("Great! Your starter code is ready above.\n\n"
                    "Copy the files into your project directory, follow the run commands, and you're off.\n\n"
                    "Feel free to ask me anything else about the code, or say 'new project' to build something else.")

        if action == "reject":
            s["stage"] = "risk_review"
            return self._run_risk_analysis(message, s)

        # Detect framework / library swap requests before falling back to AI
        m_low = message.lower()
        is_change = any(kw in m_low for kw in ["instead", "change", "switch", "use ", "want ", "prefer", "replace"])
        fw_map = {
            "django":   "Django",  "flask":   "Flask",  "fastapi": "FastAPI",
            "express":  "Express", "nestjs":  "NestJS", "spring":  "Spring",
            "gin":      "Gin",     "rails":   "Rails",
        }
        db_map = {
            "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
            "mongodb":    "MongoDB",    "mongo":    "MongoDB",
            "mysql":      "MySQL",      "sqlite":   "SQLite",
            "redis":      "Redis",
        }
        new_fw = next((v for k, v in fw_map.items() if k in m_low), None)
        new_db = next((v for k, v in db_map.items() if k in m_low), None)

        if is_change and (new_fw or new_db):
            sol = dict(s.get("selected_solution", {}))
            tech = sol.get("tech_stack", "")
            changes = []
            if new_fw:
                old_fw = next((v for k, v in fw_map.items() if k in tech.lower()), "")
                tech = re.sub(r"(?i)" + re.escape(old_fw), new_fw, tech) if old_fw else new_fw + " + " + tech
                s["task_context"]["framework"] = new_fw.lower()
                changes.append(f"framework → {new_fw}")
            if new_db:
                old_db = next((v for k, v in db_map.items() if k in tech.lower()), "")
                tech = re.sub(r"(?i)" + re.escape(old_db), new_db, tech) if old_db else tech + " + " + new_db
                s["task_context"]["database"] = new_db.lower()
                changes.append(f"database → {new_db}")
            sol["tech_stack"] = tech
            s["selected_solution"] = sol
            s["stage"] = "code_gen"
            change_summary = " and ".join(changes)
            return f"Sure — updating {change_summary}. Here's the revised implementation:\n\n" + self._generate_code(s)

        # It's a question or feedback — answer with AI
        return self._conversational_answer("code_gen", message, s)

    # ================================================================== #
    # RISK ANALYSIS
    # ================================================================== #
    _SYS_RISK = """You are CoSensei's risk analysis AI.

Analyze the architecture, generated code, and the user's feedback. Return ONLY valid JSON:
{
  "overall_risk": "LOW | MEDIUM | HIGH | CRITICAL",
  "overall_score": 0.0,
  "summary": "2-3 sentence natural assessment",
  "risks": [
    {
      "category": "Security | Performance | Scalability | Maintainability | Architecture | Data | Deployment",
      "level": "LOW | MEDIUM | HIGH | CRITICAL",
      "title": "Short risk title",
      "issue": "What the specific problem is",
      "impact": "What happens if unaddressed",
      "fix": "Concrete recommended fix"
    }
  ],
  "user_concern": "What the user seems to dislike or worry about",
  "suggested_changes": ["Specific change 1", "Specific change 2"],
  "requires_user_control": true | false,
  "response": "Natural conversational reply that presents these findings — no numbered lists, just clear prose with the key risks and what you'd suggest. End with a question asking what they want to do."
}

requires_user_control = true when overall_risk is HIGH or CRITICAL, or when significant architectural decisions need the user's input."""

    def _run_risk_analysis(self, user_feedback: str, s: Dict) -> str:
        sol  = s.get("selected_solution", {})
        ctx  = s.get("task_context", {})
        code = s.get("generated_code", {}) or {}

        prompt = (f"Solution: {sol.get('name','')} | Tech: {sol.get('tech_stack','')}\n"
                  f"Context: {json.dumps(ctx, indent=2)}\n\n"
                  f"User feedback: \"{user_feedback}\"\n\n"
                  f"Files generated: {[f.get('path','') for f in code.get('files',[])]}\n"
                  f"Directory: {code.get('directory_tree','(none)')[:300]}")

        data = self.best.json_chat(self._SYS_RISK, prompt, 3000)

        if data is None:
            s["stage"] = "risk_control"
            return ("I couldn't run a full analysis right now, but I hear your concern. "
                    "Tell me specifically what you'd like to change and I'll regenerate accordingly.")

        s["risks"]   = data
        overall      = data.get("overall_risk", "MEDIUM")
        needs_uc     = data.get("requires_user_control", False)
        response_txt = data.get("response", "")

        # Build full risk breakdown
        risks  = data.get("risks", [])
        r      = response_txt + "\n\n" if response_txt else ""

        if risks:
            r += "RISK BREAKDOWN\n" + "-" * 50 + "\n"
            level_tag = {"LOW": "[LOW]", "MEDIUM": "[MED]", "HIGH": "[HIGH]", "CRITICAL": "[!!!]"}
            for risk in risks:
                lv = risk.get("level", "MEDIUM")
                r += f"\n  {level_tag.get(lv,'[?]')} {risk.get('title','')}\n"
                r += f"    Issue:  {risk.get('issue','')}\n"
                r += f"    Impact: {risk.get('impact','')}\n"
                r += f"    Fix:    {risk.get('fix','')}\n"
            r += "\n"

        suggested = data.get("suggested_changes", [])
        if suggested:
            r += "SUGGESTED CHANGES\n" + "-" * 50 + "\n"
            for ch in suggested:
                r += f"  - {ch}\n"
            r += "\n"

        if needs_uc or overall in ("HIGH", "CRITICAL"):
            s["stage"] = "risk_control"
            r += f"[{overall} RISK — YOU'RE IN CONTROL]\n\n"
            r += "This needs your direction before I proceed. Tell me:\n"
            r += "  - What aspects matter most to you (security, speed, cost, simplicity)?\n"
            r += "  - What trade-offs are you comfortable making?\n"
            r += "  - Any constraints I should know about?\n\n"
            r += "I'll regenerate the solution around your decisions."
        else:
            s["stage"] = "risk_review"
            r += "The risk level is manageable. I can apply these fixes and regenerate, "
            r += "or you can tell me exactly what you want changed. What would you like to do?"

        return r

    def _route_risk(self, message: str, s: Dict) -> str:
        intent = self._detect_intent("risk_review", message, s)
        action = intent.get("intent", "more_direction")

        if action == "new_project": return self._reset(s)

        if action == "accept_anyway":
            s["stage"] = "complete"
            return ("Understood — the code is yours as-is. "
                    "The risks noted above are worth revisiting as you grow. "
                    "Say 'new project' anytime to start something else.")

        # apply_fixes or more_direction or anything else → regenerate
        s["stage"] = "risk_control"
        return self._risk_control(
            message if action != "apply_fixes" else "Apply all suggested changes and fixes", s)

    # ================================================================== #
    # RISK CONTROL — user directs, AI regenerates
    # ================================================================== #
    _SYS_RISK_CONTROL = """You are CoSensei's redesign AI.

The user's architecture had HIGH or CRITICAL risk. Incorporate the user's direction, constraints and priorities, then regenerate improved, real code.

Return ONLY valid JSON:
{
  "intro": "Brief natural sentence on what you improved and why",
  "improvements": ["What changed and why"],
  "risks_addressed": ["Risk X addressed by Y"],
  "remaining_risks": ["Risk that stays and why it's acceptable"],
  "directory_tree": "Updated ASCII project structure",
  "files": [
    {
      "path": "path/to/file",
      "language": "...",
      "content": "COMPLETE updated file — real, runnable code",
      "description": "what changed in this file"
    }
  ],
  "run_commands": ["command"],
  "closing": "Conversational: does this address your concerns?"
}"""

    def _risk_control(self, user_direction: str, s: Dict) -> str:
        sol   = s.get("selected_solution", {})
        ctx   = s.get("task_context", {})
        risks = s.get("risks", {})
        code  = s.get("generated_code", {}) or {}

        data = self.best.json_chat(
            self._SYS_RISK_CONTROL,
            f"Project: {ctx.get('summary', ctx.get('raw_input',''))}\n"
            f"Solution: {sol.get('name','')} | Tech: {sol.get('tech_stack','')}\n\n"
            f"Risks identified:\n{json.dumps(risks.get('risks',[]), indent=2)}\n\n"
            f"User's direction: \"{user_direction}\"\n\n"
            f"Previous structure:\n{code.get('directory_tree','(none)')[:400]}",
            5000,
        )

        if data is None:
            return ("I couldn't reach the AI to regenerate. "
                    "Please try describing what you want again, or say 'new project' to restart.")

        s["generated_code"] = data
        s["stage"]          = "code_gen"

        intro   = data.get("intro",   "Here's the improved implementation based on your direction.")
        closing = data.get("closing", "Does this address your concerns?")

        r = intro + "\n\n"

        if data.get("improvements"):
            r += "IMPROVEMENTS MADE\n" + "-" * 50 + "\n"
            for imp in data["improvements"]:
                r += f"  + {imp}\n"
            r += "\n"

        if data.get("risks_addressed"):
            r += "RISKS ADDRESSED\n" + "-" * 50 + "\n"
            for ra in data["risks_addressed"]:
                r += f"  [FIXED] {ra}\n"
            r += "\n"

        if data.get("remaining_risks"):
            r += "REMAINING (ACCEPTABLE) RISKS\n" + "-" * 50 + "\n"
            for rr in data["remaining_risks"]:
                r += f"  [NOTE] {rr}\n"
            r += "\n"

        if data.get("directory_tree"):
            r += "UPDATED PROJECT STRUCTURE\n" + "-" * 50 + "\n"
            r += "```\n" + data["directory_tree"].strip() + "\n```\n\n"

        for f in data.get("files", []):
            lang    = f.get("language", "")
            path    = f.get("path", "file")
            content = f.get("content", "").strip()
            desc_f  = f.get("description", "")
            if content:
                r += f"FILE: {path}"
                if desc_f: r += f"  — {desc_f}"
                r += f"\n```{lang}\n{content}\n```\n\n"

        if data.get("run_commands"):
            r += "HOW TO RUN\n" + "-" * 50 + "\n"
            for cmd in data["run_commands"]:
                r += f"  $ {cmd}\n"
            r += "\n"

        r += "-" * 70 + "\n"
        r += closing
        return r

    # ================================================================== #
    # COMPLETE stage — follow-up questions allowed
    # ================================================================== #
    _CASUAL_THANKS = {"thx", "thanks", "thank you", "ty", "appreciate", "nice", "cool",
                      "awesome", "great", "perfect", "excellent", "got it", "noted",
                      "cheers", "ok cool", "ok great", "ok nice"}
    _CASUAL_FAREWELL = {"bye", "goodbye", "later", "cya", "see ya", "see you", "peace",
                        "done", "that's all", "thats all", "all good", "i'm good", "im good"}

    def _route_complete(self, message: str, s: Dict) -> str:
        intent = self._detect_intent("complete", message, s)
        if intent.get("intent") in ("new_project",) or "new" in message.lower():
            return self._reset(s)
        if intent.get("intent") == "exit":
            return "Goodbye! Come back anytime you have a new project in mind."

        m = message.lower().strip().rstrip("!.,")
        sol_name = s.get("selected_solution", {}).get("name", "your project")

        # ── Casual thanks / positive reaction ───────────────────────────────
        if m in self._CASUAL_THANKS or any(m.startswith(t) for t in ("thx", "thank", "ty ", "great job", "good job", "well done")):
            return (f"Anytime! You've got a solid foundation with **{sol_name}** — "
                    f"go build something awesome. 🚀\n\n"
                    f"If you hit a wall or want to add a feature, just come back. "
                    f"Or say **'new'** to start a different project.")

        # ── Farewell / done ──────────────────────────────────────────────────
        if m in self._CASUAL_FAREWELL:
            return (f"Good luck with **{sol_name}**! You've got the architecture, the code, "
                    f"and the roadmap — time to ship it. 💪\n\n"
                    f"Come back anytime. Say **'new'** to start fresh.")

        # ── Bare negative / vague rejection ─────────────────────────────────
        if m in ("no", "nah", "nope", "not really", "no thanks", "no thank you",
                 "n", "nvm", "nevermind", "never mind", "ok", "okay", "k", "alright"):
            return (f"No worries! Is there something specific about **{sol_name}** "
                    f"you'd like to change or know more about?\n\n"
                    f"  - Say **'change the stack'** to swap a technology\n"
                    f"  - Say **'explain the architecture'** for a full breakdown\n"
                    f"  - Say **'show me the code'** to see all generated files\n"
                    f"  - Say **'new'** to start a different project")

        # ── Reference to project contents / files / "read this" ─────────────
        if any(w in m for w in ("read", "content", "this project", "our project",
                                 "the project", "project content", "files", "what's in",
                                 "whats in", "what is in")):
            ctx  = s.get("task_context", {})
            desc = s.get("selected_solution", {}).get("description", "")
            summary = ctx.get("summary", ctx.get("raw_input", ""))
            tech = s.get("selected_solution", {}).get("tech_stack", "")
            pending = s.get("_pending_files", {})
            r  = f"Here's what we built for **{sol_name}**:\n\n"
            if summary:
                r += f"**Project:** {summary[:200]}\n\n"
            if desc:
                r += f"**Architecture:** {desc[:300]}\n\n"
            if tech:
                r += f"**Tech Stack:** {tech}\n\n"
            if pending:
                r += f"**Generated files ({len(pending)}):**\n"
                for path in list(pending.keys())[:10]:
                    r += f"  📄 {path}\n"
                r += "\nSay **'show me [filename]'** to see any file, or **'show all'** for the full implementation."
            else:
                r += "The full code was already delivered above. What part would you like to explore?"
            return r

        # ── Prevent repeating the generic menu twice in a row ────────────────
        history = s.get("history", [])
        if history:
            last_assistant = next(
                (h["content"] for h in reversed(history) if h["role"] == "assistant"),
                ""
            )
            if "Here's what you can ask me" in last_assistant or "I'm here to help with" in last_assistant:
                # Already showed the menu — ask something direct instead
                return (f"What specifically would you like to know about **{sol_name}**? "
                        f"Architecture, deployment, security, cost, or something else?")

        return self._conversational_answer("complete", message, s)

    # ================================================================== #
    # CONVERSATIONAL ANSWER — any free-form question at any stage
    # ================================================================== #
    _SYS_CONVERSE = """You are CoSensei, a senior software architect and genuinely curious technical advisor.

The user has selected an architecture and may have questions, doubts, or requests at any point.
Answer like a knowledgeable teammate — warm, direct, specific, and curious. Reference the ACTUAL project details
(solution name, tech stack, phases, domain) in every answer. Never give generic textbook answers.

Rules:
- Always reference the specific project: use its name, tech stack, domain in your answer
- **Be curious to reduce hallucinations**: when you're about to make an assumption, SAY it and ask to confirm.
  Example: "I'm assuming you'll deploy this on a managed cloud — is that right, or are you working with on-prem hardware?"
  Example: "Before I answer that — are you using the CGM data in real-time, or batch processing at intervals?"
- If the user has a vague doubt ("I have a doubt"), ask ONE focused follow-up: "Doubt about which part — the tech stack, a specific phase, deployment, or something else?"
- If they ask "why X", explain the actual architectural reasoning for THIS project's requirements, then ask: "Does that match what you had in mind, or were you thinking of a different approach?"
- If they ask about security/auth/payments — give specific advice for the domain, then ask: "Any compliance requirements I should factor in? (HIPAA, GDPR, PCI-DSS etc.)"
- If they ask about scaling — reference actual numbers for the chosen infra, then ask: "What's your expected user volume at launch vs 6 months in?"
- If the user's message is ambiguous, ask ONE clarifying question before answering — don't guess and hallucinate
- End every answer with one helpful follow-up question or offer that moves the project forward
- Tone: enthusiastic, curious senior dev who wants to get the details RIGHT, not just answer and move on"""

    def _conversational_answer(self, stage: str, message: str, s: Dict) -> str:
        sol  = s.get("selected_solution", {})
        ctx  = s.get("task_context", {})
        hist = self._hist(s["history"])

        prompt = (f"Stage: {stage}\n"
                  f"Project: {ctx.get('summary', ctx.get('raw_input',''))}\n"
                  f"Solution selected: {sol.get('name','')} | Tech: {sol.get('tech_stack','')}\n"
                  f"Timeline: {sol.get('timeline','')} | Effort: {sol.get('effort','')}\n"
                  f"Risk score: {sol.get('risk_score', '')}\n"
                  f"Description: {sol.get('description','')}\n"
                  f"Domain: {ctx.get('domain','')} | Language: {ctx.get('language','')} | "
                  f"Platform: {ctx.get('platform','')}\n\n"
                  f"Conversation:\n{hist}\n\n"
                  f"User: \"{message}\"\n\n"
                  f"Answer in context of THIS specific project. Be specific, warm, helpful.")

        answer = self.best.chat(self._SYS_CONVERSE, prompt, 1500, temperature=0.65)
        return answer if answer else self._local_answer(message, stage, s)

    def _local_answer(self, message: str, stage: str, s: Dict) -> str:
        """Rich, context-aware chatbot fallback when Grok is unavailable."""
        m    = message.lower().strip()
        sol  = s.get("selected_solution", {})
        ctx  = s.get("task_context", {})

        sol_name  = sol.get("name",       "your project")
        tech      = sol.get("tech_stack", "")
        tier      = sol.get("tier",       "scalable")
        timeline  = sol.get("timeline",   "TBD")
        risk      = sol.get("risk_score", 0.4)
        desc      = sol.get("description","")
        phases    = sol.get("phases",     [])
        domain    = ctx.get("domain",     ctx.get("project_type", ""))
        lang      = ctx.get("language",   "")
        platform  = ctx.get("platform",   "web")
        features  = ctx.get("features",   [])

        is_ecommerce  = any(w in domain for w in ("ecommerce", "shop", "store"))
        is_wildlife   = any(w in domain for w in ("wildlife", "tracking", "animal"))
        is_fintech    = any(w in domain for w in ("fintech", "banking", "payment"))
        is_healthtech = "healthtech" in domain
        is_realtime   = "realtime" in features
        has_phases    = bool(phases)
        phase_names   = [p.get("name", "") for p in phases]
        pending_files = s.get("_pending_files", {})

        # ── Vague doubt / I have a question ──────────────────────────────
        if any(w in m for w in ("doubt", "have a question", "query", "unclear", "confused",
                                 "don't understand", "not sure", "idk", "lost", "help me understand")):
            r  = f"Of course! Let me help you clear that up. Which part of **{sol_name}** are you unsure about?\n\n"
            r += "Here's what you can ask me about:\n\n"
            if tech:
                r += f"  📦 **Tech Stack** — {tech[:100]}\n"
                r += f"       Ask: 'Why {tech.split(',')[0].strip()}?', 'Can I use X instead?'\n\n"
            if has_phases:
                r += f"  🗺  **Roadmap** — {len(phases)} phases\n"
                for ph in phases[:4]:
                    r += f"       • {ph.get('name','')}\n"
                r += "\n"
            r += f"  💰 **Cost & Timeline** — {timeline}, {tier} effort\n"
            r += f"       Ask: 'How much will this cost?', 'Can I cut scope?'\n\n"
            r += f"  🔒 **Security & Auth** — {'payments + user accounts' if is_ecommerce else 'API security'}\n"
            r += f"       Ask: 'How do I handle auth?', 'Is this secure?'\n\n"
            r += f"  🚀 **Deployment** — how to get it live\n"
            r += f"       Ask: 'How do I deploy this?', 'Which cloud?'\n\n"
            r += "Just tell me which part and I'll go deep on it!"
            return r

        # ── Explain / tell me more ────────────────────────────────────────
        if any(w in m for w in ("explain", "tell me more", "elaborate", "what does", "what is",
                                  "how does", "describe", "break down", "walk me through")):
            r  = f"Happy to break it down! Here's **{sol_name}** explained:\n\n"
            if desc:
                r += f"**What it is:** {desc}\n\n"
            if tech:
                r += f"**Tech Stack:** {tech}\n\n"
                # Domain-specific component explanations
                if is_ecommerce:
                    r += ("**How the pieces work together:**\n"
                          "  - **Frontend (React/JS):** Product catalog, cart, checkout UI\n"
                          "  - **Backend API:** Handles orders, inventory, user accounts\n"
                          "  - **Database:** Stores products, orders, customers\n"
                          "  - **Payment (Stripe):** Processes transactions securely\n"
                          "  - **Auth (JWT):** Keeps customer sessions secure\n\n")
                elif is_wildlife:
                    r += ("**How the pieces work together:**\n"
                          "  - **API Layer:** Receives GPS/satellite data from field devices\n"
                          "  - **Database:** Stores sightings, trails, animal records\n"
                          "  - **Processing:** Haversine distance, home-range estimation\n"
                          "  - **Dashboard:** Map view of animal movements in real time\n\n")
                elif is_fintech:
                    r += ("**How the pieces work together:**\n"
                          "  - **Auth:** Multi-factor authentication, session tokens\n"
                          "  - **Core API:** Transaction processing, ledger entries\n"
                          "  - **Database:** Immutable audit log + main tables\n"
                          "  - **Compliance layer:** PCI-DSS data handling rules\n\n")
                else:
                    r += ("**How the pieces work together:**\n"
                          "  - **Backend:** Handles business logic and data\n"
                          "  - **Database:** Stores and retrieves your data\n"
                          "  - **API layer:** Exposes endpoints for the frontend\n"
                          "  - **Frontend:** User interface and interactions\n\n")
            if has_phases:
                r += f"**Phases ({timeline}):**\n"
                for ph in phases:
                    tasks = ph.get("tasks", [])
                    r += f"  {ph.get('name','')} — {', '.join(tasks[:3])}\n"
                r += "\n"
            r += "What specific part would you like me to go deeper on?"
            return r

        # ── Why this tech / reasoning ─────────────────────────────────────
        if any(w in m for w in ("why", "reason", "why not", "advantage", "benefit",
                                  "pros", "cons", "compare", "vs", "versus", "better than")):
            r  = f"Great question — here's why I chose this stack for **{sol_name}**:\n\n"
            tech_lower = tech.lower()
            if "kafka" in tech_lower:
                r += "  **Kafka** — handles high-throughput event streaming; perfect for order events, inventory updates, real-time feeds. Alternative: RabbitMQ (simpler, lower throughput).\n\n"
            if "kubernetes" in tech_lower or "k8s" in tech_lower:
                r += "  **Kubernetes** — auto-scales your services under load; handles rolling deploys with zero downtime. For smaller teams: Docker Compose is simpler.\n\n"
            if "redis" in tech_lower:
                r += "  **Redis** — in-memory cache cuts DB load by 70-90% for repeated reads (product pages, session data). Also used for rate limiting and job queues.\n\n"
            if "postgresql" in tech_lower or "postgres" in tech_lower:
                r += "  **PostgreSQL** — ACID transactions are critical for" + (" orders and payments." if is_ecommerce else " data integrity.") + " Battle-tested, excellent for relational data.\n\n"
            if "react" in tech_lower:
                r += "  **React** — component-driven UI makes" + (" product pages, cart, checkout reusable." if is_ecommerce else " building interactive UIs faster.") + " Huge ecosystem, easy to hire for.\n\n"
            if "fastapi" in tech_lower:
                r += "  **FastAPI** — async Python framework with automatic OpenAPI docs. 2-3x faster than Flask for I/O bound workloads.\n\n"
            if "microservices" in tech_lower:
                r += "  **Microservices** — lets you scale individual services (e.g., checkout service) independently. Trade-off: more infrastructure complexity vs monolith.\n\n"
            r += f"Risk score for this tier: **{risk:.0%}** — {'well within acceptable range' if risk < 0.5 else 'higher complexity, manageable with good team practices'}.\n\n"
            r += "Want me to compare against a simpler option, or are you happy with this stack?"
            return r

        # ── Security / auth questions ─────────────────────────────────────
        if any(w in m for w in ("security", "secure", "auth", "authentication", "login",
                                  "password", "jwt", "oauth", "permission", "access", "hack",
                                  "safe", "protect", "encrypt", "ssl", "https")):
            r = f"Security for **{sol_name}** — here's what matters most:\n\n"
            if is_ecommerce:
                r += ("  🔐 **Authentication:** JWT tokens with refresh rotation. Never store passwords in plain text — use bcrypt.\n"
                      "  💳 **Payments:** Always use Stripe (never roll your own payment processing). Stripe handles PCI-DSS compliance.\n"
                      "  🛡 **API Security:** Rate limiting on all endpoints. CORS locked to your domain only.\n"
                      "  🔒 **Data:** HTTPS everywhere. Sensitive customer data encrypted at rest.\n"
                      "  📋 **Common attacks to defend:** SQL injection (use ORM), XSS (sanitize inputs), CSRF tokens on forms.\n\n"
                      "  Critical: Never log credit card numbers or passwords. Add a security audit before going live.\n")
            elif is_fintech:
                r += ("  🔐 **Auth:** MFA is mandatory for financial apps. Use TOTP (Google Authenticator) or SMS codes.\n"
                      "  🏦 **Compliance:** PCI-DSS if handling card data. Immutable audit logs for all transactions.\n"
                      "  🔒 **Encryption:** AES-256 for data at rest. TLS 1.3 for transit. No exceptions.\n"
                      "  🚨 **Fraud detection:** Rate limit all transaction endpoints. Flag anomalous patterns.\n")
            elif is_healthtech:
                r += ("  🏥 **HIPAA compliance is mandatory.** All PHI must be encrypted at rest and in transit.\n"
                      "  🔐 **Auth:** Role-based access (doctor vs patient vs admin). Session timeouts.\n"
                      "  📋 **Audit logs:** Every data access must be logged with timestamp and user.\n"
                      "  🔒 **Data isolation:** Patient records must never be accessible cross-tenant.\n")
            else:
                r += ("  🔐 **JWT Auth:** Access token (15min) + Refresh token (7 days). Store refresh in httpOnly cookie.\n"
                      "  🛡 **API:** Rate limiting (100 req/min default). Input validation on every endpoint.\n"
                      "  🔒 **Database:** Never expose DB directly. Use parameterized queries / ORM only.\n"
                      "  🌐 **Transport:** HTTPS only. HSTS headers. Restrict CORS origins.\n"
                      "  📦 **Secrets:** All keys in .env, never in code. Rotate keys regularly.\n")
            r += "\nWant me to add an auth module to the generated code?"
            return r

        # ── Payments / Stripe / billing ───────────────────────────────────
        if any(w in m for w in ("payment", "stripe", "billing", "invoice", "checkout",
                                  "card", "subscription", "refund", "transaction")):
            r = f"Payment integration for **{sol_name}**:\n\n"
            if is_ecommerce:
                r += ("  **Recommended: Stripe** — the industry standard. Handles PCI-DSS compliance so you don't have to.\n\n"
                      "  Setup:\n"
                      "  1. Install stripe: `pip install stripe` or `npm install stripe`\n"
                      "  2. Create a payment intent on your backend when checkout starts\n"
                      "  3. Use Stripe.js on the frontend to collect card details (never hits your server)\n"
                      "  4. Confirm payment on backend, then fulfill the order\n\n"
                      "  Costs: 2.9% + $0.30 per successful transaction. No monthly fee.\n\n"
                      "  For subscriptions: Use Stripe Billing. For marketplaces: Stripe Connect.\n")
            else:
                r += ("  Use **Stripe** for any payment processing — it's the safest, most reliable option.\n"
                      "  Never store card numbers yourself — always tokenize through Stripe.\n"
                      "  Webhook validation is critical: verify Stripe signatures on all webhook events.\n")
            r += "\nShould I add Stripe integration to the generated code?"
            return r

        # ── Database questions ────────────────────────────────────────────
        if any(w in m for w in ("database", "db", "sql", "schema", "table", "model",
                                  "migration", "postgres", "mongo", "mysql", "query", "orm")):
            db = next((v for v in ["MongoDB", "PostgreSQL", "MySQL", "SQLite", "Redis"]
                       if v.lower() in tech.lower()), "PostgreSQL")
            r  = f"Database design for **{sol_name}** using {db}:\n\n"
            if is_ecommerce:
                r += ("  **Core tables/collections:**\n"
                      "  - `users` — id, email, password_hash, created_at, role\n"
                      "  - `products` — id, name, description, price, stock, category, images\n"
                      "  - `orders` — id, user_id, status, total, created_at\n"
                      "  - `order_items` — id, order_id, product_id, qty, price_at_purchase\n"
                      "  - `addresses` — id, user_id, street, city, country, is_default\n"
                      "  - `payments` — id, order_id, stripe_id, status, amount\n\n"
                      "  Key indexes: `products.category`, `orders.user_id`, `orders.status`\n")
            elif is_wildlife:
                r += ("  **Core tables:**\n"
                      "  - `animals` — id, name, species, sex, age, tag_id\n"
                      "  - `sightings` — id, animal_id, latitude, longitude, source, observed_at\n"
                      "  - `satellite_passes` — id, satellite_id, captured_at, image_url, processed\n"
                      "  - `zones` — id, name, boundary_polygon, park_id\n\n"
                      "  Spatial index on `sightings(latitude, longitude)` for fast trail queries.\n")
            else:
                r += (f"  {db} is the right choice for your project. "
                      f"Use an ORM (SQLAlchemy for Python, Prisma for JS) — never raw SQL with user input.\n"
                      f"  Always use migrations (Alembic / Prisma Migrate) to version your schema.\n")
            r += "\nWant me to generate the full DB schema SQL file?"
            return r

        # ── Scaling / performance ─────────────────────────────────────────
        if any(w in m for w in ("scale", "scaling", "performance", "load", "traffic",
                                  "slow", "fast", "optimize", "cache", "speed", "latency",
                                  "concurrent", "users", "requests per second")):
            r  = f"Scaling strategy for **{sol_name}** ({tier} tier):\n\n"
            tech_lower = tech.lower()
            if "kubernetes" in tech_lower:
                r += ("  **Kubernetes auto-scaling:** HPA (Horizontal Pod Autoscaler) scales pods based on CPU/memory.\n"
                      "  Target: keep CPU below 70%. Scale at 100 concurrent users per pod.\n\n")
            if "redis" in tech_lower:
                r += ("  **Redis caching:** Cache product listings, search results, user sessions.\n"
                      "  TTL: 5 min for catalog, 15 min for static content, 24h for user prefs.\n\n")
            if "kafka" in tech_lower:
                r += ("  **Kafka:** Async processing of orders/events prevents blocking the API.\n"
                      "  Consumer groups scale horizontally — add more consumers as load grows.\n\n")
            if "postgresql" in tech_lower:
                r += ("  **PostgreSQL:** Add read replicas for heavy read workloads. "
                      "Connection pooling via PgBouncer (max 100 connections per instance).\n\n")
            r += (f"  **Realistic numbers for {tier} tier:**\n"
                  f"  - MVP: handles ~50 concurrent users on a $20/mo VPS\n"
                  f"  - Production: 500-2000 concurrent with proper caching + CDN\n"
                  f"  - Enterprise ({tech[:40]}...): 10k+ concurrent with K8s scaling\n\n"
                  f"  First bottleneck is almost always the database — add indexes and caching before scaling horizontally.\n")
            r += "\nWant a performance checklist specific to your stack?"
            return r

        # ── Deployment / hosting ──────────────────────────────────────────
        if any(w in m for w in ("deploy", "hosting", "host", "cloud", "aws", "gcp", "azure",
                                  "heroku", "railway", "vercel", "vps", "server", "docker",
                                  "container", "kubernetes", "production", "live", "launch")):
            r  = f"Deployment options for **{sol_name}** ({tier} tier):\n\n"
            pending_run = s.get("_pending_run", "")
            tech_lower = tech.lower()
            if tier in ("scalable", "enterprise") or "kubernetes" in tech_lower:
                r += ("  **Recommended: AWS EKS or GCP GKE** (managed Kubernetes)\n"
                      "  - Cost: ~$150-500/mo for a production cluster\n"
                      "  - AWS EKS: best for enterprise, huge ecosystem\n"
                      "  - GCP GKE: slightly cheaper, excellent auto-pilot mode\n\n"
                      "  **Cheaper alternative for getting started:**\n"
                      "  - Railway.app or Render.com — deploy Docker containers easily, ~$20-50/mo\n\n")
            else:
                r += ("  **Quick options by budget:**\n"
                      "  - 🆓 Free tier: Railway, Render, Fly.io (limited but great for MVP)\n"
                      "  - 💵 $5-20/mo: DigitalOcean Droplet or Hetzner VPS (best value)\n"
                      "  - 💰 $50+/mo: AWS EC2 / GCP Compute (most features, most complex)\n\n"
                      "  **Frontend:** Vercel or Netlify (free for React/Next.js)\n"
                      "  **Database:** Supabase (free PostgreSQL) or Railway DB ($5/mo)\n\n")
            if pending_run:
                r += f"  **Local run commands (already generated):**\n{pending_run}\n\n"
            r += "  First step: get it running locally → Docker Compose → deploy to Railway → then scale up.\n"
            r += "\nReady to see the Dockerfile and deployment config? Say 'yes' for the full code."
            return r

        # ── Testing questions ─────────────────────────────────────────────
        if any(w in m for w in ("test", "testing", "unit test", "integration", "pytest",
                                  "jest", "coverage", "tdd", "mock", "ci", "cd", "pipeline")):
            r  = f"Testing strategy for **{sol_name}**:\n\n"
            lang_lower = lang.lower()
            is_python = "python" in lang_lower or "fastapi" in tech.lower() or "flask" in tech.lower() or "django" in tech.lower()
            is_js = "javascript" in lang_lower or "node" in tech.lower() or "react" in tech.lower()
            if is_python:
                r += ("  **Python testing stack:**\n"
                      "  - `pytest` — test runner (already in requirements.txt)\n"
                      "  - `pytest-asyncio` — for async FastAPI endpoints\n"
                      "  - `httpx` or `TestClient` — hit real endpoints in tests\n"
                      "  - `factory_boy` — generate test data\n\n")
            elif is_js:
                r += ("  **JS testing stack:**\n"
                      "  - `Jest` — unit + integration tests\n"
                      "  - `Supertest` — HTTP endpoint testing\n"
                      "  - `React Testing Library` — component tests\n"
                      "  - `Playwright` or `Cypress` — end-to-end tests\n\n")
            if is_ecommerce:
                r += ("  **Critical paths to test first:**\n"
                      "  1. Add to cart → checkout → payment (happy path)\n"
                      "  2. Payment failure handling\n"
                      "  3. Inventory decrement on order\n"
                      "  4. Auth: unauthenticated access to protected routes\n\n")
            else:
                r += ("  **Priority test cases:**\n"
                      "  1. Core API endpoints (GET/POST/PUT/DELETE)\n"
                      "  2. Auth flows (login, token refresh, logout)\n"
                      "  3. Error cases (400, 401, 404, 500)\n"
                      "  4. Data validation (invalid inputs)\n\n")
            r += ("  **CI/CD:** GitHub Actions is free and easy. Push → run tests → deploy on green.\n"
                  "  Aim for 70%+ coverage on core business logic before going live.\n")
            r += "\nTests are already included in the generated code. Say 'yes' to see them."
            return r

        # ── Frontend questions ────────────────────────────────────────────
        if any(w in m for w in ("frontend", "ui", "ux", "react", "interface", "component",
                                  "css", "design", "responsive", "mobile", "page", "view")):
            r  = f"Frontend approach for **{sol_name}**:\n\n"
            tech_lower = tech.lower()
            if "react" in tech_lower:
                r += ("  **React** is your UI framework. Key structure:\n"
                      "  - `src/components/` — reusable UI pieces\n"
                      "  - `src/pages/` — route-level components\n"
                      "  - `src/hooks/` — data fetching (useQuery from TanStack Query)\n"
                      "  - `src/store/` — global state (Zustand or Redux Toolkit)\n\n")
                if is_ecommerce:
                    r += ("  **Key pages:**\n"
                          "  - `/` — Home / product listing\n"
                          "  - `/products/:id` — Product detail + add to cart\n"
                          "  - `/cart` — Cart review\n"
                          "  - `/checkout` — Stripe payment form\n"
                          "  - `/orders` — Order history (auth required)\n\n"
                          "  **Styling:** Tailwind CSS is the fastest to work with. Shadcn/ui for ready-made components.\n")
            elif "vanilla js" in tech_lower:
                r += ("  **Vanilla JS** — lightweight, no build step. Good for getting started fast.\n"
                      "  Fetch API for data, localStorage for cart state.\n"
                      "  Consider upgrading to React/Vue once the backend is solid.\n")
            r += "\nWant me to add specific frontend components to the generated code?"
            return r

        # ── API / REST / endpoints ────────────────────────────────────────
        if any(w in m for w in ("api", "endpoint", "rest", "route", "http", "request",
                                  "response", "get", "post", "put", "delete", "graphql",
                                  "websocket", "webhook")):
            r  = f"API design for **{sol_name}**:\n\n"
            if is_ecommerce:
                r += ("  **Core REST endpoints:**\n"
                      "  GET  /api/v1/products          — list products (paginated)\n"
                      "  GET  /api/v1/products/:id      — product detail\n"
                      "  POST /api/v1/cart              — add to cart\n"
                      "  GET  /api/v1/cart              — view cart\n"
                      "  POST /api/v1/orders            — place order\n"
                      "  GET  /api/v1/orders            — order history (auth)\n"
                      "  POST /api/v1/auth/register     — create account\n"
                      "  POST /api/v1/auth/login        — get JWT token\n"
                      "  POST /api/v1/payments/intent   — create Stripe payment intent\n\n")
            elif is_wildlife:
                r += ("  **Core REST endpoints:**\n"
                      "  GET  /api/v1/animals           — list tracked animals\n"
                      "  POST /api/v1/animals           — register new animal\n"
                      "  POST /api/v1/animals/:id/sightings — record GPS sighting\n"
                      "  GET  /api/v1/animals/:id/trail — movement trail + home range\n"
                      "  POST /api/v1/satellite/process — submit satellite image batch\n\n")
            else:
                r += (f"  Standard REST pattern:\n"
                      f"  GET  /api/v1/resources        — list\n"
                      f"  POST /api/v1/resources        — create\n"
                      f"  GET  /api/v1/resources/:id    — detail\n"
                      f"  PUT  /api/v1/resources/:id    — update\n"
                      f"  DELETE /api/v1/resources/:id  — delete\n\n")
            if is_realtime:
                r += "  **WebSocket:** /ws — real-time updates (order status, live tracking).\n\n"
            r += "  All endpoints return JSON. Use `/health` for uptime monitoring.\n"
            r += "\nAPI routes are included in the generated files. Say 'yes' to see them."
            return r

        # ── Files / code / show me ────────────────────────────────────────
        if any(w in m for w in ("file", "show", "code", "give", "see", "implementation",
                                  "models.py", "routes", "services", "main.py", "config")):
            if pending_files:
                file_list = "\n".join(f"  📄 {p}" for p in pending_files.keys())
                return (f"Here are the files I've prepared for **{sol_name}**:\n\n{file_list}\n\n"
                        f"Say **yes** to see all of them, or name a specific one "
                        f"(e.g. 'show models.py' or 'show api.py').")
            return f"Say **yes** to generate and see the full implementation code for {sol_name}."

        # ── Cost / budget ─────────────────────────────────────────────────
        if any(w in m for w in ("cost", "price", "budget", "expensive", "cheap",
                                  "how much", "money", "dollar", "pricing", "afford")):
            r  = f"Cost breakdown for **{sol_name}** ({tier} tier, {timeline}):\n\n"
            r += ("  **Development cost (main cost):**\n"
                  "  - Solo dev: your own time\n"
                  "  - Freelancer: $30-150/hr depending on market\n"
                  f"  - Agency: usually 2-5x freelancer rate for {timeline}\n\n"
                  "  **Infrastructure (monthly recurring):**\n")
            if tier in ("simple", "mvp"):
                r += ("  - Hosting: $0-20/mo (Railway, Render free tier)\n"
                      "  - Database: $0-10/mo (Supabase, Railway DB)\n"
                      "  - Total: $0-30/mo to start\n\n")
            elif tier == "optimized":
                r += ("  - Server: $20-50/mo (DigitalOcean, Hetzner)\n"
                      "  - Database: $15-30/mo managed PostgreSQL\n"
                      "  - Redis: $10-20/mo\n"
                      "  - Total: ~$50-100/mo\n\n")
            else:
                r += ("  - Kubernetes cluster: $150-500/mo (EKS/GKE)\n"
                      "  - Managed DB: $50-200/mo\n"
                      "  - CDN + monitoring: $50-150/mo\n"
                      "  - Total: $300-800+/mo at scale\n\n")
            if is_ecommerce:
                r += "  **Per-transaction:** Stripe takes 2.9% + $0.30. No monthly fee.\n\n"
            r += "  Tip: Start cheap (Railway free tier) and scale only when you need to.\n"
            r += "\nWant me to suggest ways to reduce costs or scope?"
            return r

        # ── Change / modify stack ─────────────────────────────────────────
        if any(w in m for w in ("change", "switch", "replace", "modify", "use ",
                                  "want ", "prefer", "instead", "different")):
            return (f"Sure! Tell me exactly what you want to change in **{sol_name}**:\n\n"
                    f"  - **Framework:** e.g. 'use Django instead', 'switch to Express'\n"
                    f"  - **Database:** e.g. 'use MongoDB', 'switch to MySQL'\n"
                    f"  - **Feature:** e.g. 'add real-time updates', 'remove Kafka'\n"
                    f"  - **Stack:** e.g. 'make it TypeScript', 'use GraphQL instead of REST'\n\n"
                    f"Current stack: {tech}\n\n"
                    f"Just say what to swap and I'll regenerate the implementation immediately.")

        # ── Doubt about a specific phase ──────────────────────────────────
        if has_phases:
            for ph in phases:
                ph_name = ph.get("name", "").lower()
                if ph_name and any(word in m for word in ph_name.split()):
                    tasks = ph.get("tasks", [])
                    r  = f"**{ph.get('name','')}** — here's what happens in this phase:\n\n"
                    for t in tasks:
                        r += f"  ✓ {t}\n"
                    r += f"\nThis phase is part of the {timeline} timeline for {sol_name}.\n"
                    r += "Want me to go deeper on any of these tasks, or skip to a specific one?"
                    return r

        # ── Generic — check if we already showed this menu recently ─────────
        history = s.get("history", [])
        already_showed_menu = any(
            "Here's what you can ask me" in h.get("content", "") or "I'm here to help with" in h.get("content", "")
            for h in history[-4:]
            if h.get("role") == "assistant"
        )

        if already_showed_menu:
            # Already showed the menu — be direct and ask specifically
            topics = []
            if tech:        topics.append("the tech stack")
            if has_phases:  topics.append("a specific phase")
            topics.extend(["deployment", "security", "cost"])
            topic_list = ", ".join(topics[:4])
            return (f"I'm not sure what you're after — could you be a bit more specific?\n\n"
                    f"For **{sol_name}**, I can go deep on: {topic_list}.\n\n"
                    f"Or say **'explain everything'** for a full architecture walkthrough, "
                    f"or **'new'** to start a different project.")

        # ── Generic menu (first time) ─────────────────────────────────────
        r  = f"I'm here to help with **{sol_name}**! Here's what you can ask me:\n\n"
        r += "  💬 'Explain the architecture' — full breakdown of how it works\n"
        r += "  🔒 'How do I handle security/auth?' — security best practices\n"
        r += "  🚀 'How do I deploy this?' — hosting options and steps\n"
        r += "  💰 'How much will this cost?' — infra and dev cost estimates\n"
        r += "  📊 'How does it scale?' — performance and scaling strategy\n"
        r += "  🧪 'How do I test this?' — testing approach and tools\n"
        r += "  🔄 'Change the database/framework' — swap any component\n"
        r += "  📄 'Show me the code' — see all generated files\n"
        if is_ecommerce:
            r += "  💳 'How do I add payments?' — Stripe integration guide\n"
        if has_phases:
            r += f"\n  Or ask about any phase: {', '.join(phase_names[:3])}\n"
        r += "\nWhat would you like to know?"
        return r

    # ================================================================== #
    # Helpers
    # ================================================================== #
    def _reset(self, s: Dict) -> str:
        s.update({"stage": "clarification", "task_context": {},
                   "solutions": None, "selected_solution": None,
                   "generated_code": None, "risks": None, "history": [],
                   "_pending_files": {}, "_pending_shown": False})
        return (
            "Clean slate. What are we building this time?\n\n"
            "Tell me the idea — messy is fine, we'll sharpen it together."
        )

    @staticmethod
    def _hist(history: List[Dict], n: int = 14) -> str:
        lines = []
        for msg in history[-n:]:
            role    = "User" if msg["role"] == "user" else "CoSensei"
            content = msg.get("content", "")[:700]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _static_risk_scan(self, sol: Dict, ctx: Dict, code_data: Optional[Dict]) -> str:
        """Automatically scan generated code for common risks."""
        risks = []
        domain  = ctx.get("domain", "")
        features = ctx.get("features", [])
        tech    = str(sol.get("tech_stack", "")).lower()
        files   = code_data.get("files", []) if code_data else []

        # Scan file contents for risk patterns
        all_code = " ".join(f.get("content", "") for f in files).lower()

        if "hardcoded" in all_code or 'password = "' in all_code or "secret = '" in all_code:
            risks.append(("CRITICAL", "Hardcoded secrets detected",
                          "Move all credentials to .env — never commit secrets to git"))

        if "debug=true" in all_code or "debug = true" in all_code:
            risks.append(("HIGH", "Debug mode enabled",
                          "Set DEBUG=False in production — exposes stack traces"))

        if "select *" in all_code and "%" in all_code and "parameterized" not in all_code:
            risks.append(("HIGH", "Potential SQL injection",
                          "Use parameterized queries / ORM — never format SQL with user input"))

        if "cors" not in all_code and ("flask" in tech or "fastapi" in tech):
            risks.append(("MEDIUM", "CORS not configured",
                          "Add CORS middleware and restrict allowed origins in production"))

        if "jwt" not in all_code and "auth" not in all_code and "token" not in all_code:
            risks.append(("MEDIUM", "No authentication visible",
                          "Add JWT or session auth before exposing any endpoint publicly"))

        if "https" not in all_code and "tls" not in all_code:
            risks.append(("MEDIUM", "No HTTPS / TLS enforced",
                          "Use HTTPS in production — configure TLS at the reverse proxy level"))

        if "realtime" in features and "rate limit" not in all_code and "limiter" not in all_code:
            risks.append(("MEDIUM", "No rate limiting on real-time endpoints",
                          "Add rate limiting (e.g. flask-limiter / slowapi) to prevent abuse"))

        # Domain-specific risks
        if "fintech" in domain or "ai_fintech" in domain:
            risks.append(("HIGH", "Financial data handling — compliance required",
                          "Review PCI-DSS requirements. Encrypt all financial data at rest and in transit"))
        if "healthtech" in domain:
            risks.append(("HIGH", "Medical data — HIPAA compliance required",
                          "PHI must be encrypted. Implement audit logging for all data access"))
        if "ai" in domain:
            risks.append(("MEDIUM", "AI model outputs not validated",
                          "Add output validation and human oversight for high-stakes AI decisions"))

        if not risks:
            risks.append(("LOW", "No obvious critical risks in starter code",
                          "Review security before deploying to production"))

        level_tag = {"CRITICAL": "[CRITICAL]", "HIGH": "[HIGH]", "MEDIUM": "[MED]", "LOW": "[LOW]"}
        r  = "CODE RISK SCAN\n" + "-" * 50 + "\n"
        r += "| Severity | Issue | Fix |\n"
        r += "|---|---|---|\n"
        for level, title, fix in risks:
            tag = level_tag.get(level, "[MED]")
            r += f"| {tag} | {title} | {fix} |\n"
        return r.rstrip()

    def _manual_tasks_required(self, ctx: Dict) -> str:
        """List critical tasks that CANNOT be done by AI — user must handle them."""
        domain   = ctx.get("domain", "")
        features = ctx.get("features", [])

        tasks = [
            ("Environment setup",
             "Copy .env.example → .env and fill in your real API keys, DB credentials, and secrets. "
             "Never commit .env to git."),
            ("Database provisioning",
             "Create your database, run migrations, and seed initial data. "
             "The code assumes the DB exists and is reachable."),
            ("API key registration",
             "Register accounts and get API keys for any external services used "
             "(OpenAI, Stripe, AWS, etc.) and add them to .env."),
            ("Domain & SSL",
             "Register your domain, point DNS, and set up SSL/TLS certificates "
             "(use Let's Encrypt or your cloud provider's certificate manager)."),
            ("Production server",
             "Deploy to a real server or cloud (AWS, GCP, Azure, Heroku, Railway, etc.). "
             "The dev server (Flask run / uvicorn --reload) is NOT safe for production."),
            ("Security review",
             "Review all endpoints for authentication and authorization before going live. "
             "Consider a penetration test or security audit for anything customer-facing."),
            ("Monitoring & alerts",
             "Set up error tracking (Sentry), uptime monitoring, and log aggregation "
             "before going live. You need to know when things break."),
            ("Backups",
             "Configure automated database backups. Test the restore process before you need it."),
        ]

        # Domain-specific mandatory tasks
        if "fintech" in domain or "ai_fintech" in domain:
            tasks.insert(2, ("Compliance — PCI-DSS / Financial regulations",
                             "MANDATORY: Get legal/compliance review before processing any real financial data. "
                             "This cannot be skipped — violations carry heavy penalties."))
        if "healthtech" in domain:
            tasks.insert(2, ("Compliance — HIPAA",
                             "MANDATORY: Any app handling patient data must comply with HIPAA. "
                             "Get a compliance officer or legal review before launch."))
        if "ai_prediction" in domain or "ai" in domain:
            tasks.insert(3, ("AI model testing with real data",
                             "The starter code uses mock/placeholder AI calls. "
                             "You must test with your actual data, validate outputs, and tune thresholds."))
        if "realtime" in features:
            tasks.append(("WebSocket / real-time infrastructure",
                          "Real-time features require proper infrastructure (Redis pub/sub, WebSocket server). "
                          "Validate WebSocket connections under load before production."))

        r  = "WHAT YOU MUST DO MANUALLY\n" + "-" * 50 + "\n"
        r += "These are CRITICAL steps the AI cannot complete for you:\n\n"
        for i, (title, detail) in enumerate(tasks, 1):
            r += f"  {i}. {title}\n     {detail}\n\n"
        r += "Complete these before considering your project production-ready."
        return r

    def _offline_codegen(self, sol: Dict, ctx: Dict) -> Dict:
        """Generate real starter code locally when Grok API is unavailable."""
        tech  = str(sol.get("tech_stack", "")).lower()
        name  = sol.get("name", "project")

        use_fastapi = "fastapi" in tech or "django" in tech
        use_django  = "django"  in tech
        use_mongo   = "mongo"   in tech or "nosql" in str(ctx).lower()
        use_redis   = "redis"   in tech
        raw_ctx     = (str(ctx.get("raw_input","")) + " " + str(ctx.get("summary","")) + " " + str(ctx.get("domain",""))).lower()
        # Domain flags from project context (more specific than generic "is_ai")
        is_tracking  = any(w in raw_ctx for w in ["track", "tracking", "gps", "location", "route", "routing", "sensor", "telemetry"])
        is_wildlife  = any(w in raw_ctx for w in ["tiger", "lion", "animal", "wildlife", "species", "forest", "national park", "satellite image"])
        is_ecommerce = any(w in raw_ctx for w in ["shop", "store", "product", "cart", "ecommerce", "e-commerce", "inventory", "order"])
        is_social    = any(w in raw_ctx for w in ["social", "feed", "post", "follow", "profile", "community"])
        is_chatbot   = any(w in raw_ctx for w in ["chatbot", "chat bot", "llm assistant", "ai assistant", "gpt wrapper", "openai"])
        # is_ai only true for actual AI assistant/chatbot projects
        is_ai        = is_chatbot or any(w in tech for w in ("openai", "gpt", "llm"))
        # Compose a human-readable project label for use in generated code
        project_label = name.title() if name and name.lower() not in ("project", "app") else "App"

        framework = "FastAPI" if use_fastapi else "Flask"
        db_name   = "MongoDB" if use_mongo else "PostgreSQL"
        tree = f"""{name.lower().replace(' ', '_')}/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── autonomy_engine.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py
│   └── services/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_api.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md"""

        # ── Shared Autonomy Engine (embedded in every generated project) ──
        autonomy_code = f'''"""autonomy_engine.py — Shared Autonomy Engine
Tracks API usage patterns and decides how much autonomy the AI/system takes.

Autonomy Modes:
  AUTO_EXECUTE   — system acts fully autonomously, no confirmation needed
  SHARED_CONTROL — system suggests actions, user approves key decisions
  SUGGEST_ONLY   — system proposes, user executes everything
  HUMAN_CONTROL  — user controls all actions, system advises only
"""
import time
import math
from typing import Dict, Optional
from functools import wraps


class AutonomyMode:
    AUTO_EXECUTE   = "AUTO_EXECUTE"
    SHARED_CONTROL = "SHARED_CONTROL"
    SUGGEST_ONLY   = "SUGGEST_ONLY"
    HUMAN_CONTROL  = "HUMAN_CONTROL"


class AutonomyEngine:
    """Tracks session behavior and computes the current autonomy mode."""

    def __init__(self, auto_threshold: float = 0.75, human_threshold: float = 0.25):
        self._sessions: Dict[str, Dict] = {{}}
        self.auto_threshold  = auto_threshold
        self.human_threshold = human_threshold

    # ------------------------------------------------------------------ #
    def get_or_create(self, session_id: str) -> Dict:
        if session_id not in self._sessions:
            self._sessions[session_id] = {{
                "session_id":     session_id,
                "request_count":  0,
                "error_count":    0,
                "success_count":  0,
                "response_times": [],
                "last_active":    time.time(),
                "trust_score":    0.5,    # 0 = no trust  → 1 = full trust
                "stress_level":   0.3,    # 0 = calm       → 1 = high stress
                "engagement":     0.5,    # 0 = passive    → 1 = fully engaged
                "autonomy_mode":  AutonomyMode.SHARED_CONTROL,
            }}
        return self._sessions[session_id]

    # ------------------------------------------------------------------ #
    def record_request(self, session_id: str, success: bool, latency_ms: float = 0.0):
        """Call this on every API request to update behavioral metrics."""
        s = self.get_or_create(session_id)
        s["request_count"] += 1
        s["last_active"]    = time.time()
        if success:
            s["success_count"] += 1
        else:
            s["error_count"] += 1
        s["response_times"].append(latency_ms)
        if len(s["response_times"]) > 20:
            s["response_times"] = s["response_times"][-20:]
        self._recompute(s)

    # ------------------------------------------------------------------ #
    def _recompute(self, s: Dict):
        total = max(s["request_count"], 1)
        # Trust: proportion of successful requests (exponential moving avg)
        raw_trust = s["success_count"] / total
        s["trust_score"] = 0.8 * s["trust_score"] + 0.2 * raw_trust

        # Stress: driven by error rate + high latency
        error_rate      = s["error_count"] / total
        avg_latency     = (sum(s["response_times"]) / len(s["response_times"])
                           if s["response_times"] else 0)
        latency_stress  = min(1.0, avg_latency / 5000)   # 5 s = full stress
        raw_stress      = error_rate * 0.6 + latency_stress * 0.4
        s["stress_level"] = 0.7 * s["stress_level"] + 0.3 * raw_stress

        # Engagement: saturates at ~50 requests
        s["engagement"] = 1 - math.exp(-s["request_count"] / 50)

        s["autonomy_mode"] = self._decide(s)

    # ------------------------------------------------------------------ #
    def _decide(self, s: Dict) -> str:
        score = (s["trust_score"] * 0.5
                 + s["engagement"] * 0.3
                 - s["stress_level"] * 0.2)
        if score >= self.auto_threshold:   return AutonomyMode.AUTO_EXECUTE
        if score >= 0.50:                  return AutonomyMode.SHARED_CONTROL
        if score >= self.human_threshold:  return AutonomyMode.SUGGEST_ONLY
        return AutonomyMode.HUMAN_CONTROL

    # ------------------------------------------------------------------ #
    def get_status(self, session_id: str) -> Dict:
        s = self.get_or_create(session_id)
        score = (s["trust_score"] * 0.5
                 + s["engagement"] * 0.3
                 - s["stress_level"] * 0.2)
        return {{
            "autonomy_mode": s["autonomy_mode"],
            "trust_score":   round(s["trust_score"],   2),
            "stress_level":  round(s["stress_level"],  2),
            "engagement":    round(s["engagement"],    2),
            "composite_score": round(score, 2),
            "request_count": s["request_count"],
        }}

    def should_auto_execute(self, session_id: str) -> bool:
        return self.get_or_create(session_id)["autonomy_mode"] == AutonomyMode.AUTO_EXECUTE

    def should_ask_confirmation(self, session_id: str) -> bool:
        mode = self.get_or_create(session_id)["autonomy_mode"]
        return mode in (AutonomyMode.SHARED_CONTROL, AutonomyMode.SUGGEST_ONLY)


# Singleton — import and use anywhere in the app
autonomy_engine = AutonomyEngine()


# ── Flask / FastAPI middleware helpers ─────────────────────────────────────
{"def autonomy_middleware(f):" if not use_fastapi else "# FastAPI: use as a dependency"}
{"    '''Decorator: wraps any Flask route with autonomy tracking.'''" if not use_fastapi else ""}
{"    @wraps(f)" if not use_fastapi else ""}
{"    def wrapper(*args, **kwargs):" if not use_fastapi else ""}
{"        from flask import request, g" if not use_fastapi else ""}
{"        session_id = request.headers.get('X-Session-ID', 'default')" if not use_fastapi else ""}
{"        start = time.time()" if not use_fastapi else ""}
{"        try:" if not use_fastapi else ""}
{"            result = f(*args, **kwargs)" if not use_fastapi else ""}
{"            autonomy_engine.record_request(session_id, success=True, latency_ms=(time.time()-start)*1000)" if not use_fastapi else ""}
{"            return result" if not use_fastapi else ""}
{"        except Exception as exc:" if not use_fastapi else ""}
{"            autonomy_engine.record_request(session_id, success=False, latency_ms=(time.time()-start)*1000)" if not use_fastapi else ""}
{"            raise exc" if not use_fastapi else ""}
{"    return wrapper" if not use_fastapi else ""}


def get_autonomy_status(session_id: str = "default") -> Dict:
    """Return current autonomy status for a session. Use in any endpoint."""
    return autonomy_engine.get_status(session_id)
'''

        if use_fastapi:
            main_code = '''"""main.py — FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.routes.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.APP_NAME}")
    yield
    print("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
'''
        else:
            main_code = '''"""main.py — Flask application entry point"""
from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.routes.api import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}})
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.route("/health")
    def health():
        return {"status": "healthy", "service": Config.APP_NAME}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
'''

        config_code = f'''"""config.py — Application configuration"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str        = os.getenv("APP_NAME", "{name}")
    APP_DESCRIPTION: str = os.getenv("APP_DESCRIPTION", "AI-powered application")
    SECRET_KEY: str      = os.getenv("SECRET_KEY", "change-me-in-production")
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

    # Database
    DATABASE_URL: str  = os.getenv("DATABASE_URL", "{"mongodb://localhost:27017/app" if use_mongo else "postgresql://user:pass@localhost:5432/app"}")

    # AI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL: str       = os.getenv("AI_MODEL", "gpt-4o-mini")
    MAX_TOKENS: int     = int(os.getenv("MAX_TOKENS", "1000"))

    {"# Redis" + chr(10) + "    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')" if use_redis else ""}

settings = Settings()
Config   = Settings  # Flask compat alias
'''

        # ---- Domain-specific service, models, routes ----

        if is_wildlife and is_tracking:
            # ── Wildlife / GPS / Satellite tracking ──
            service_code = f'''"""services/core.py — {project_label} core logic: location processing & satellite imagery"""
from datetime import datetime
from typing import Optional, List, Tuple
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def process_satellite_image(image_path: str, timestamp: datetime) -> dict:
    """Stub: process a satellite image frame and detect animal signatures."""
    # TODO: integrate actual image-processing model (e.g. OpenCV, YOLOv8)
    return {{
        "image_path":  image_path,
        "timestamp":   timestamp.isoformat(),
        "detections":  [],          # list of {{label, confidence, bbox}}
        "processed":   False,       # set True after real model runs
    }}


def get_animal_trail(sightings: List[dict]) -> List[Tuple[float, float]]:
    """Return ordered GPS path from a list of sighting dicts."""
    sorted_s = sorted(sightings, key=lambda s: s.get("observed_at", ""))
    return [(s["latitude"], s["longitude"]) for s in sorted_s if "latitude" in s]


def estimate_home_range(trail: List[Tuple[float, float]]) -> dict:
    """Bounding-box home-range estimate from a GPS trail."""
    if not trail:
        return {{}}
    lats = [p[0] for p in trail]
    lons = [p[1] for p in trail]
    return {{
        "min_lat": min(lats), "max_lat": max(lats),
        "min_lon": min(lons), "max_lon": max(lons),
        "area_km2": round(
            haversine_distance(min(lats), min(lons), max(lats), max(lons)), 2
        ),
    }}
'''

            models_code = f'''"""models.py — {project_label} data models"""
{"from pydantic import BaseModel, Field" if use_fastapi else "from dataclasses import dataclass, field"}
from typing import Optional, List
from datetime import datetime
import uuid


{"class Animal(BaseModel):" if use_fastapi else "@dataclass\\nclass Animal:"}
    id:          str      {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    name:        str                  # e.g. "Tiger-01", "M-Simba"
    species:     str      = "Tiger"
    sex:         Optional[str] = None
    age_years:   Optional[int] = None
    tag_id:      Optional[str] = None
    notes:       str      = ""
    created_at:  datetime {"= Field(default_factory=datetime.utcnow)" if use_fastapi else "= field(default_factory=datetime.utcnow)"}


{"class Sighting(BaseModel):" if use_fastapi else "@dataclass\\nclass Sighting:"}
    id:           str     {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    animal_id:    str
    latitude:     float
    longitude:    float
    altitude_m:   Optional[float] = None
    source:       str     = "satellite"     # "satellite" | "camera_trap" | "ranger"
    image_url:    Optional[str] = None
    observed_at:  datetime {"= Field(default_factory=datetime.utcnow)" if use_fastapi else "= field(default_factory=datetime.utcnow)"}
    notes:        str     = ""


{"class SatellitePass(BaseModel):" if use_fastapi else "@dataclass\\nclass SatellitePass:"}
    id:           str     {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    satellite_id: str
    image_url:    str
    captured_at:  datetime
    processed:    bool    = False
    detections:   {"List[dict]" if use_fastapi else "list"} = {"Field(default_factory=list)" if use_fastapi else "field(default_factory=list)"}
    zone:         Optional[str] = None      # forest zone / grid cell
'''

            routes_code = f'''"""routes/api.py — {project_label} API endpoints"""
{"from fastapi import APIRouter, HTTPException" if use_fastapi else "from flask import Blueprint, request, jsonify"}
from app.services.core import get_animal_trail, estimate_home_range, process_satellite_image
from datetime import datetime

{"router = APIRouter()" if use_fastapi else 'api_bp = Blueprint("api", __name__)'}

# In-memory store (replace with DB in production)
_animals:   dict = {{}}
_sightings: list = []


{"@router.get('/animals')" if use_fastapi else "@api_bp.route('/animals', methods=['GET'])"}
{"async def list_animals():" if use_fastapi else "def list_animals():"}
    {"return list(_animals.values())" if use_fastapi else "return jsonify(list(_animals.values()))"}


{"@router.post('/animals/{animal_id}/sightings')" if use_fastapi else "@api_bp.route('/animals/<animal_id>/sightings', methods=['POST'])"}
{"async def add_sighting(animal_id: str, lat: float, lon: float, source: str = 'satellite'):" if use_fastapi else "def add_sighting(animal_id):"}
    {"" if use_fastapi else "    data = request.get_json()"}
    sighting = {{
        "id":          str(datetime.utcnow().timestamp()),
        "animal_id":   animal_id,
        "latitude":    {"lat" if use_fastapi else "data['latitude']"},
        "longitude":   {"lon" if use_fastapi else "data['longitude']"},
        "source":      {"source" if use_fastapi else "data.get('source','satellite')"},
        "observed_at": datetime.utcnow().isoformat(),
    }}
    _sightings.append(sighting)
    {"return sighting" if use_fastapi else "return jsonify(sighting), 201"}


{"@router.get('/animals/{animal_id}/trail')" if use_fastapi else "@api_bp.route('/animals/<animal_id>/trail', methods=['GET'])"}
{"async def get_trail(animal_id: str):" if use_fastapi else "def get_trail(animal_id):"}
    animal_sightings = [s for s in _sightings if s["animal_id"] == animal_id]
    trail = get_animal_trail(animal_sightings)
    home_range = estimate_home_range(trail)
    result = {{"animal_id": animal_id, "trail": trail, "home_range": home_range, "total_points": len(trail)}}
    {"return result" if use_fastapi else "return jsonify(result)"}
'''

        elif is_ecommerce:
            service_code = f'''"""services/core.py — {project_label} e-commerce logic"""
from typing import List, Optional


def calculate_order_total(items: List[dict], discount_pct: float = 0.0) -> float:
    subtotal = sum(i.get("price", 0) * i.get("qty", 1) for i in items)
    return round(subtotal * (1 - discount_pct / 100), 2)


def check_inventory(product_id: str, inventory: dict, qty_requested: int = 1) -> bool:
    return inventory.get(product_id, 0) >= qty_requested


def apply_coupon(code: str, coupons: dict) -> Optional[float]:
    """Return discount percentage or None if invalid."""
    return coupons.get(code.upper())
'''
            models_code = f'''"""models.py — {project_label} models"""
{"from pydantic import BaseModel, Field" if use_fastapi else "from dataclasses import dataclass, field"}
from typing import Optional, List
from datetime import datetime
import uuid


{"class Product(BaseModel):" if use_fastapi else "@dataclass\\nclass Product:"}
    id:          str      {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    name:        str
    description: str      = ""
    price:       float    = 0.0
    stock:       int      = 0
    category:    str      = "general"
    image_url:   Optional[str] = None


{"class Order(BaseModel):" if use_fastapi else "@dataclass\\nclass Order:"}
    id:          str      {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    user_id:     str
    items:       {"List[dict]" if use_fastapi else "list"} {"= Field(default_factory=list)" if use_fastapi else "= field(default_factory=list)"}
    total:       float    = 0.0
    status:      str      = "pending"
    created_at:  datetime {"= Field(default_factory=datetime.utcnow)" if use_fastapi else "= field(default_factory=datetime.utcnow)"}
'''
            routes_code = f'''"""routes/api.py — {project_label} endpoints"""
{"from fastapi import APIRouter, HTTPException" if use_fastapi else "from flask import Blueprint, request, jsonify"}
from app.services.core import calculate_order_total, check_inventory

{"router = APIRouter()" if use_fastapi else 'api_bp = Blueprint("api", __name__)'}
_products: dict = {{}}
_orders:   list = []


{"@router.get('/products')" if use_fastapi else "@api_bp.route('/products', methods=['GET'])"}
{"async def list_products():" if use_fastapi else "def list_products():"}
    {"return list(_products.values())" if use_fastapi else "return jsonify(list(_products.values()))"}


{"@router.post('/orders')" if use_fastapi else "@api_bp.route('/orders', methods=['POST'])"}
{"async def create_order(user_id: str, items: list):" if use_fastapi else "def create_order():"}
    {"" if use_fastapi else "    data = request.get_json()"}
    total = calculate_order_total({"items" if use_fastapi else "data['items']"})
    order = {{"id": "o1", "user_id": {"user_id" if use_fastapi else "data['user_id']"}, "items": {"items" if use_fastapi else "data['items']"}, "total": total, "status": "pending"}}
    _orders.append(order)
    {"return order" if use_fastapi else "return jsonify(order), 201"}
'''

        elif is_chatbot or is_ai:
            service_code = '''"""services/core.py — AI chatbot service layer"""
import os
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a helpful AI assistant with shared autonomy capabilities.
You collaborate with the user, adapting your level of autonomy based on their preferences and confidence.
Always explain your reasoning and ask for confirmation on high-stakes decisions."""


def get_ai_response(user_message: str, history: list) -> dict:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model=settings.AI_MODEL, messages=messages, max_tokens=settings.MAX_TOKENS, temperature=0.7,
    )
    content = response.choices[0].message.content
    return {"response": content, "model": settings.AI_MODEL, "tokens": response.usage.total_tokens}
'''
            models_code = f'''"""models.py — {project_label} models"""
{"from pydantic import BaseModel, Field" if use_fastapi else "from dataclasses import dataclass, field"}
from typing import Optional, List
from datetime import datetime
import uuid


{"class Message(BaseModel):" if use_fastapi else "@dataclass\\nclass Message:"}
    id:         str      {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    session_id: str
    role:       str      # 'user' | 'assistant' | 'system'
    content:    str
    timestamp:  datetime {"= Field(default_factory=datetime.utcnow)" if use_fastapi else "= field(default_factory=datetime.utcnow)"}
    tokens:     Optional[int] = None
'''
            routes_code = f'''"""routes/api.py — {project_label} endpoints"""
{"from fastapi import APIRouter, HTTPException" if use_fastapi else "from flask import Blueprint, request, jsonify"}
from app.services.core import get_ai_response

{"router = APIRouter()" if use_fastapi else 'api_bp = Blueprint("api", __name__)'}


{"@router.post('/chat')" if use_fastapi else "@api_bp.route('/chat', methods=['POST'])"}
{"async def chat(message: str, session_id: str = 'default', history: list = []):" if use_fastapi else "def chat():"}
    {"" if use_fastapi else "    data = request.get_json()"}
    result = get_ai_response({"message" if use_fastapi else "data['message']"}, {"history" if use_fastapi else "data.get('history',[])"})
    {"return result" if use_fastapi else "return jsonify(result)"}
'''

        else:
            # Generic CRUD app
            service_code = f'''"""services/core.py — {project_label} core logic"""
from app.config import settings


def process_request(data: dict) -> dict:
    return {{"status": "success", "data": data, "message": "Processed successfully"}}


def validate_input(data: dict, required_fields: list) -> tuple:
    for f in required_fields:
        if f not in data or not data[f]:
            return False, f"Missing required field: {{f}}"
    return True, ""
'''
            models_code = f'''"""models.py — {project_label} models"""
{"from pydantic import BaseModel, Field" if use_fastapi else "from dataclasses import dataclass, field"}
from typing import Optional
from datetime import datetime
import uuid


{"class Item(BaseModel):" if use_fastapi else "@dataclass\\nclass Item:"}
    id:         str      {"= Field(default_factory=lambda: str(uuid.uuid4()))" if use_fastapi else "= field(default_factory=lambda: str(uuid.uuid4()))"}
    title:      str
    description: str     = ""
    created_at: datetime {"= Field(default_factory=datetime.utcnow)" if use_fastapi else "= field(default_factory=datetime.utcnow)"}
    active:     bool     = True
'''
            routes_code = f'''"""routes/api.py — {project_label} endpoints"""
{"from fastapi import APIRouter, HTTPException" if use_fastapi else "from flask import Blueprint, request, jsonify"}
from app.services.core import process_request, validate_input

{"router = APIRouter()" if use_fastapi else 'api_bp = Blueprint("api", __name__)'}
_items: dict = {{}}


{"@router.get('/items')" if use_fastapi else "@api_bp.route('/items', methods=['GET'])"}
{"async def list_items():" if use_fastapi else "def list_items():"}
    {"return list(_items.values())" if use_fastapi else "return jsonify(list(_items.values()))"}


{"@router.post('/items')" if use_fastapi else "@api_bp.route('/items', methods=['POST'])"}
{"async def create_item(title: str, description: str = ''):" if use_fastapi else "def create_item():"}
    {"" if use_fastapi else "    data = request.get_json()"}
    item = {{"id": "i1", "title": {"title" if use_fastapi else "data['title']"}, "active": True}}
    _items[item["id"]] = item
    {"return item" if use_fastapi else "return jsonify(item), 201"}
'''

        test_code = f'''"""tests/test_api.py — API tests"""
import pytest
{"from fastapi.testclient import TestClient" if use_fastapi else ""}
{"from flask.testing import FlaskClient" if not use_fastapi else ""}
from app.main import app


{"client = TestClient(app)" if use_fastapi else ""}

{"@pytest.fixture" if not use_fastapi else ""}
{"def client():" if not use_fastapi else ""}
{"    app.config['TESTING'] = True" if not use_fastapi else ""}
{"    with app.test_client() as c:" if not use_fastapi else ""}
{"        yield c" if not use_fastapi else ""}


def test_health{"()" if use_fastapi else "(client)"}:
    r = client.get("/health")
    assert r.status_code == 200
    {"assert r.json()['status'] == 'healthy'" if use_fastapi else "assert r.get_json()['status'] == 'ok'"}


def test_chat{"()" if use_fastapi else "(client)"}:
    payload = {{"message": "Hello, what can you do?"}}
    r = client.post("/api/v1/chat", json=payload)
    # Without AI key this may 500, but endpoint must exist
    assert r.status_code in (200, 500)
'''

        reqs = f"""{"fastapi" if use_fastapi else "flask"}
{"uvicorn[standard]" if use_fastapi else ""}
{"flask-cors" if not use_fastapi else ""}
{"pydantic" if use_fastapi else ""}
openai
python-dotenv
{"motor" if use_mongo else "psycopg2-binary"}
{"pymongo" if use_mongo else "sqlalchemy"}
{"redis" if use_redis else ""}
pytest
httpx
""".strip()

        env = f"""APP_NAME={name}
APP_DESCRIPTION=AI-powered application
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000

# AI
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
MAX_TOKENS=1000

# Database
DATABASE_URL={"mongodb://localhost:27017/app" if use_mongo else "postgresql://user:password@localhost:5432/app"}
{"REDIS_URL=redis://localhost:6379/0" if use_redis else ""}
"""

        dockerfile = f"""FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

{"CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]" if use_fastapi else 'CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]'}
"""

        run_cmds = [
            "python -m venv venv",
            "source venv/bin/activate  # Windows: venv\\Scripts\\activate",
            "pip install -r requirements.txt",
            "cp .env.example .env  # then edit .env with your keys",
            f"{'uvicorn app.main:app --reload' if use_fastapi else 'python app/main.py'}",
        ]

        return {
            "intro": f"Here's your {name} starter — {framework} backend, {db_name} database, real AI integration.",
            "directory_tree": tree,
            "files": [
                {"path": "app/main.py",             "language": "python",    "content": main_code,      "description": "entry point"},
                {"path": "app/config.py",            "language": "python",    "content": config_code,    "description": "configuration"},
                {"path": "app/models.py",            "language": "python",    "content": models_code,    "description": "data models"},
                {"path": "app/autonomy_engine.py",   "language": "python",    "content": autonomy_code,  "description": "shared autonomy engine — tracks trust/stress/engagement, decides AUTO_EXECUTE vs SHARED_CONTROL"},
                {"path": "app/routes/api.py",        "language": "python",    "content": routes_code,    "description": "API endpoints"},
                {"path": "app/services/core.py",     "language": "python",    "content": service_code,   "description": "core business logic"},
                {"path": "tests/test_api.py",        "language": "python",    "content": test_code,      "description": "API tests"},
                {"path": "requirements.txt",         "language": "text",      "content": reqs,           "description": "dependencies"},
                {"path": ".env.example",             "language": "text",      "content": env,            "description": "environment variables template"},
                {"path": "Dockerfile",               "language": "dockerfile", "content": dockerfile,    "description": "container config"},
            ],
            "run_commands": run_cmds,
            "closing": "Here's your complete starter code. Does this match what you had in mind, or would you like me to adjust the stack or add any features?",
        }

    # Domain keyword map → (keywords, domain_label, human_name)
    # ORDER MATTERS: more specific entries first so they take priority
    _DOMAIN_MAP = [
        # AI / Prediction — must come before fintech/health so "predict petroleum in a bank" = AI FinTech
        (["predict", "prediction", "forecast", "ml model", "machine learning", "deep learning",
          "neural network", "pytorch", "tensorflow", "sklearn", "train a model", "regression",
          "classification", "nlp", "computer vision", "llm", "openai", "claude", "gemini",
          "gpt", "autonomy", "shared autonomy", "ai agent", "autonomous"],
         "ai_prediction", "AI Prediction System"),
        # Petroleum / Energy — before generic "monitoring"
        (["petroleum", "petrol", "crude oil", "oil", "gas", "fuel reserve", "propellant",
          "energy reserve", "barrel", "refinery", "pipeline", "fossil"],
         "energy",        "Petroleum / Energy"),
        # Aerospace
        (["rocket", "spacecraft", "satellite", "orbit", "nasa", "space", "launch", "aerospace",
          "reentry", "mission", "thrust", "payload"],
         "aerospace",     "Space / Aerospace"),
        # Tracking / Monitoring
        (["track", "tracker", "tracking", "monitor", "live update", "real-time", "realtime",
          "dashboard", "telemetry", "surveillance", "gps", "location", "fleet"],
         "tracking",      "Live Tracking"),
        # E-Commerce
        (["ecommerce", "e-commerce", "shop", "store", "product catalog", "cart", "checkout",
          "inventory", "stripe", "payment gateway"],
         "ecommerce",     "E-Commerce"),
        # Chat / Assistant
        (["chatbot", "chat app", "messaging", "conversation", "virtual assistant", "bot",
          "slack bot", "discord bot", "whatsapp"],
         "chatbot",       "Chat / Assistant"),
        # Social
        (["social network", "social media", "feed", "post", "like", "follow", "community",
          "user profile", "newsfeed"],
         "social",        "Social Platform"),
        # FinTech — lower priority than AI prediction
        (["fintech", "banking", "bank account", "transaction", "wallet", "crypto", "defi",
          "invoice", "billing", "ledger", "financial model", "stock", "trading"],
         "fintech",       "FinTech"),
        # HealthTech
        (["health", "medical", "patient", "doctor", "clinic", "appointment", "hospital",
          "ehr", "emr", "telemedicine", "diagnosis"],
         "healthtech",    "HealthTech"),
        # Analytics
        (["analytics", "report", "chart", "graph", "metrics", "visuali", "bi ", "business intelligence",
          "kpi", "data pipeline", "etl"],
         "analytics",     "Analytics"),
        # IoT
        (["iot", "sensor", "hardware", "raspberry", "arduino", "embedded", "firmware"],
         "iot",           "IoT Platform"),
        # EdTech
        (["education", "e-learning", "course", "learn", "student", "teacher", "quiz", "lesson", "lms"],
         "edtech",        "EdTech"),
        # Gaming
        (["game", "gaming", "player", "score", "leaderboard", "multiplayer", "unity", "unreal"],
         "gaming",        "Game"),
        # Generic AI (catch-all, after specific AI types)
        (["ai", "ml", "model", "neural", "llm", "autonomous", "intelligence"],
         "ai_app",        "AI System"),
    ]

    def _extract_context(self, message: str, ctx: Dict) -> None:
        """Extract all detectable context from a message into ctx (in-place)."""
        w = message.lower()
        word_list = w.split()

        # Platform
        if any(x in w for x in ("web app", "website", "browser", "web-based")):
            ctx.setdefault("platform", "web")
        elif any(x in w for x in ("mobile app", "ios", "android", "phone app", "flutter", "react native")):
            ctx.setdefault("platform", "mobile")
        elif any(x in w for x in ("api ", "backend", "rest api", "graphql", "microservice")):
            ctx.setdefault("platform", "api")
        elif any(x in w for x in ("desktop", "electron", "windows app", "mac app")):
            ctx.setdefault("platform", "desktop")
        elif "mobile" in word_list:
            ctx.setdefault("platform", "mobile")
        elif "web" in word_list:
            ctx.setdefault("platform", "web")
        elif "api" in word_list:
            ctx.setdefault("platform", "api")

        # Language
        for lang, kws in [
            ("Python",     ["python", "flask", "fastapi", "django", "py"]),
            ("JavaScript", ["javascript", "node", "nodejs", "express", "vue", "next"]),
            ("TypeScript", ["typescript"]),
            ("Kotlin",     ["kotlin", "android native"]),
            ("Swift",      ["swift", "ios native"]),
            ("Java",       ["java", "spring"]),
            ("Go",         ["golang"]),
            ("Rust",       ["rust"]),
            ("C#",         ["c#", "dotnet", ".net", "csharp"]),
        ]:
            if any(k in w for k in kws):
                ctx.setdefault("language", lang)

        # Database
        if any(x in w for x in ("postgres", "postgresql", "mysql", "sqlite", " sql ")):
            ctx.setdefault("database", "PostgreSQL")
        elif any(x in w for x in ("mongodb", "mongo", "nosql", "document db", "firebase", "dynamo")):
            ctx.setdefault("database", "MongoDB")
        elif any(x in w for x in ("redis",)):
            ctx.setdefault("database", "Redis")

        # Domain detection — collect ALL matches, then build a combined name
        matched = []
        for keywords, domain, human in self._DOMAIN_MAP:
            if any(k in w for k in keywords):
                matched.append((domain, human))

        if matched:
            # If AI/prediction + another domain → combine them: "AI-Powered FinTech"
            ai_domains = {"ai_prediction", "ai_app"}
            ai_match   = next((m for m in matched if m[0] in ai_domains), None)
            non_ai     = [m for m in matched if m[0] not in ai_domains]

            if ai_match and non_ai:
                # AI + subject domain: "AI-Powered Petroleum / Energy"
                combined_human = f"AI-Powered {non_ai[0][1]}"
                ctx.setdefault("domain",       f"ai_{non_ai[0][0]}")
                ctx.setdefault("project_type", "ai_app")
                ctx.setdefault("summary",      combined_human)
                ctx.setdefault("human_name",   combined_human)
            else:
                # Single domain
                domain, human = matched[0]
                ctx.setdefault("domain",       domain)
                ctx.setdefault("project_type", domain)
                ctx.setdefault("human_name",   human)

        # Features
        features = ctx.get("features", [])
        if any(x in w for x in ("real-time", "realtime", "live", "websocket", "streaming")):
            if "realtime" not in features: features.append("realtime")
        if any(x in w for x in ("global", "worldwide", "international", "multi-region")):
            if "global" not in features: features.append("global")
            ctx.setdefault("scale", "large")
        if features:
            ctx["features"] = features

        # Build summary if not already set
        parts = []
        if ctx.get("human_name"):
            parts.append(ctx["human_name"])
        elif ctx.get("domain"):
            for _, d, h in self._DOMAIN_MAP:
                if d == ctx["domain"]:
                    parts.append(h)
                    break
        if ctx.get("platform") and ctx["platform"] not in str(parts):
            parts.append(ctx["platform"].title() + " app")
        if ctx.get("features"):
            parts.append("(" + ", ".join(ctx["features"]) + ")")
        if parts:
            ctx.setdefault("summary", " ".join(parts))

    def _smart_fallback(self, message: str, s: Dict) -> str:
        """Conversation-aware fallback when Grok API is unavailable."""
        ctx = s.get("task_context", {})
        w   = message.lower()

        # Extract everything from the current message
        self._extract_context(message, ctx)
        s["task_context"] = ctx

        # ---- Confusion / explanation request ----
        if any(x in w for x in ("don't know", "dont know", "explain", "not sure", "idk",
                                  "help me", "i don't understand", "what do you mean")):
            if ctx.get("domain") == "ai_app" or ctx.get("ai_type"):
                return (
                    "Totally fine — AI projects have two very different paths and it's worth picking the right one early:\n\n"
                    "  **Path A — Call an existing AI API** (OpenAI, Claude, Gemini)\n"
                    "  You write backend code that sends prompts and gets responses back. "
                    "Fast to build, no ML knowledge needed, costs per API call.\n\n"
                    "  **Path B — Train or fine-tune your own model** (PyTorch / TensorFlow / HuggingFace)\n"
                    "  Full control over behavior, runs on your own hardware or GPU cloud, "
                    "way more complex to set up and maintain.\n\n"
                    "Most products start with Path A and never need Path B. What sounds closer to your situation?"
                )
            return (
                "No worries — let's back up. I just need to understand the idea itself before we touch tech.\n\n"
                "Tell me: **what problem does this thing solve, and who has that problem?**\n\n"
                "Even one sentence like 'helps freelancers track which clients owe them money' "
                "is enough for me to start designing something real."
            )

        # ---- Count how much we know now ----
        known = sum(1 for k in ("platform", "language", "database", "project_type", "domain") if ctx.get(k))

        # Count short assistant turns (each = one question asked)
        asked = sum(1 for m in s.get("history", [])
                    if m.get("role") == "assistant" and len(m.get("content", "")) < 500)

        # Push to solutions only when we have specific, non-vague context
        # Require: platform + domain/project_type + at least one more field
        has_specific_domain = bool(ctx.get("domain") or ctx.get("project_type")) and \
                              ctx.get("summary", "your project") not in ("your project", "app", "website", "")
        has_language_or_features = bool(ctx.get("language") or ctx.get("features") or ctx.get("database"))

        if known >= 4 or (asked >= 6) or (known >= 3 and has_specific_domain and has_language_or_features):
            ctx.setdefault("project_type", "app")
            ctx.setdefault("platform",     "web")
            ctx.setdefault("language",     "Python")
            ctx.setdefault("summary",      "your project")
            s["task_context"] = ctx
            s["stage"] = "solutions"
            return "Got it! Here's what I'd suggest:\n\n" + self._gen_solutions(message, s)

        # ---- Ask the ONE most important missing piece ----
        # Check for unrecognized proper nouns — skip when user is typing in ALL-CAPS
        raw = ctx.get("raw_input", message)
        words_in_raw = raw.split()
        pct_upper = sum(1 for w in words_in_raw if w.isupper() and len(w) > 1) / max(len(words_in_raw), 1)
        _COMMON_WORDS = {
            # Animals & nature
            "tiger", "lion", "bear", "wolf", "elephant", "deer", "fox", "rabbit",
            "eagle", "shark", "whale", "dolphin", "monkey", "gorilla", "leopard",
            "cheetah", "jaguar", "panther", "panda", "buffalo", "rhino", "giraffe",
            "zebra", "crocodile", "snake", "bird", "fish", "horse", "cow", "pig",
            # Geography
            "forest", "park", "lake", "river", "mountain", "ocean", "sea", "valley",
            "jungle", "desert", "island", "beach", "city", "town", "village", "zone",
            "national", "international", "global", "local", "regional",
            # Common project words
            "system", "app", "application", "platform", "tool", "service", "website",
            "portal", "dashboard", "tracker", "monitor", "manager", "builder",
            # Common verbs/nouns
            "track", "tracking", "route", "routing", "manage", "monitor", "build",
            "create", "course", "project", "team", "user", "admin", "data",
        }
        if pct_upper <= 0.6:    # Only scan mixed-case text for brand names
            proper_nouns = [
                w for w in words_in_raw
                if w and w[0].isupper() and len(w) > 2
                and not all(c.isupper() or not c.isalpha() for c in w)  # skip ALL-CAPS words
                and w.lower() not in _COMMON_WORDS
                and w.lower() not in {
                    "i", "the", "a", "an", "in", "on", "at", "to", "for", "of", "and",
                    "my", "we", "our", "create", "build", "make", "want", "need",
                    "web", "app", "api", "website", "system", "platform", "tool",
                    "python", "javascript", "react", "node", "django", "flask",
                }
            ]
            unknown_nouns = [w for w in proper_nouns if w.lower() not in {
                "saas", "mvp", "crud", "rest", "graphql", "sql", "aws", "gcp", "azure",
                "docker", "kubernetes", "postgres", "mongodb", "mysql", "redis",
                "stripe", "github", "slack", "notion", "trello", "jira",
            }]
            if unknown_nouns and not ctx.get("project_name"):
                noun = unknown_nouns[0]
                return (f"Quick one — what's **{noun}**? "
                        f"Is it a product you're building, cloning, or integrating with? "
                        f"Just a sentence or two and I'll have everything I need.")

        # First: if we don't know the WHAT or WHO yet, ask that — not platform/language
        if not ctx.get("project_type") and not ctx.get("domain"):
            return (
                "Love that you want to build something — but I need to understand the idea before we touch tech.\n\n"
                "**What does it do, and who's it for?** Even rough is fine: "
                "'helps small restaurant owners manage staff schedules' or "
                "'lets students find study partners at their university'. "
                "The more specific, the better I can design it."
            )

        if not has_specific_domain:
            domain_hint = ctx.get("domain") or ctx.get("project_type", "")
            return (
                f"I've got the general vibe but need a sharper picture — "
                f"right now I could build you almost anything in the {domain_hint or 'general'} space. "
                f"**What specifically does it {domain_hint or 'do'}, and who's the main user?** "
                f"The more concrete you are, the less generic my architecture will be."
            )

        # ── Domain-depth curiosity: ask critical domain questions BEFORE platform/language ──
        domain = ctx.get("domain", ctx.get("project_type", ""))
        audience = ctx.get("audience", "")

        # Health / medical / glucose / prediction projects
        is_health = any(w in domain for w in ("health", "medical", "clinical", "glucose", "sugar",
                                               "diabetes", "patient", "doctor", "hospital"))
        is_ai = any(w in domain for w in ("ai", "ml", "predict", "model", "learn", "recommend"))

        if (is_health or is_ai) and not ctx.get("_asked_data_source"):
            ctx["_asked_data_source"] = True
            s["task_context"] = ctx
            if is_health:
                return (
                    f"Got it — a health prediction project. Super important question before I design anything: "
                    f"**where does the data come from?** Is the user entering readings manually (typing in numbers), "
                    f"does it pull automatically from a wearable/CGM device, or are you working with lab/EHR data? "
                    f"The entire architecture changes based on this."
                )
            else:
                return (
                    f"AI project — nice. One thing that'll shape the whole design: "
                    f"**do you have an existing trained model, or do we need to train one from scratch?** "
                    f"And what does the input data look like — CSV files, a live stream, user-uploaded images, something else?"
                )

        if (is_health or is_ai) and not audience and not ctx.get("_asked_audience"):
            ctx["_asked_audience"] = True
            s["task_context"] = ctx
            if is_health:
                return (
                    f"And who's actually making decisions based on the predictions? "
                    f"Is this **patients monitoring themselves** day-to-day, or **doctors reviewing a patient panel**, "
                    f"or something more automated (like triggering alerts)? "
                    f"This tells me how critical the accuracy requirements are."
                )
            else:
                return (
                    f"Who's the main user and what do they DO with the prediction result? "
                    f"Like — do they just see a number, get an alert, or does something happen automatically? "
                    f"Helps me figure out the right UI and reliability requirements."
                )

        # Ecommerce — need to know what's being sold before touching stack
        is_ecom = any(w in domain for w in ("ecommerce", "shop", "store", "marketplace"))
        if is_ecom and not ctx.get("_asked_product_type"):
            ctx["_asked_product_type"] = True
            s["task_context"] = ctx
            return (
                f"Before I pick the stack — **what are you selling, and is it single-vendor or multi-vendor?** "
                f"Physical products, digital downloads, subscriptions, or a marketplace where multiple sellers list? "
                f"These are all very different architectures."
            )

        # SaaS / platform — need core workflow
        is_saas = any(w in domain for w in ("saas", "platform", "tool", "dashboard"))
        if is_saas and not ctx.get("summary") and not ctx.get("_asked_workflow"):
            ctx["_asked_workflow"] = True
            s["task_context"] = ctx
            return (
                f"Walk me through one typical user session — what does a user actually **do** in this thing day-to-day? "
                f"Like 'they log in, see X, click Y, get Z result'. The more specific you are, the tighter the architecture."
            )

        if not ctx.get("platform"):
            sum_text = ctx.get("summary", ctx.get("domain", "this"))
            return (
                f"Got the concept. Where does {sum_text} live — "
                f"**web app, mobile, backend API, or something else?** "
                f"Not sure? Tell me who the users are and I'll recommend."
            )

        if not ctx.get("language"):
            plat = ctx.get("platform", "")
            if "mobile" in plat:
                return (
                    "For mobile, the two main options are:\n\n"
                    "  **React Native** — JavaScript, one codebase for iOS + Android, huge community\n"
                    "  **Flutter** — Dart, excellent performance, Google-backed\n\n"
                    "Any preference, or should I pick what fits your project best?"
                )
            if is_health or is_ai:
                return (
                    "For the backend, Python is the obvious call here — best ML/data ecosystem by far "
                    "(scikit-learn, pandas, FastAPI). Unless you're locked into something else, I'd default to that. "
                    "Any reason to go a different direction, or should I run with Python?"
                )
            return (
                "Any language preference? "
                "If you know JavaScript, I'd lean that way — same language front and back. "
                "If Python, also great — best ecosystem for anything data/AI related. "
                "No preference? Just say so and I'll pick the right tool for the job."
            )

        # If we get here we have enough
        s["stage"] = "solutions"
        return "Alright, I've got what I need. Spinning up your options now:\n\n" + self._gen_solutions(message, s)

    def _fallback_solutions(self, ctx: Dict) -> List[Dict]:
        platform = ctx.get("platform", "web")
        domain   = ctx.get("domain",   ctx.get("project_type", "app"))
        lang     = ctx.get("language", "")
        db       = ctx.get("database", "PostgreSQL")
        is_mob   = "mobile" in platform.lower()
        is_api   = "api" in platform.lower()
        features = ctx.get("features", [])
        has_rt   = "realtime" in features

        # Human-readable project name — prefer explicit project_name, then human_name, then domain map
        human_name = ctx.get("project_name") or ctx.get("human_name", "App")
        if human_name in ("App", "", None):
            for _, d, h in self._DOMAIN_MAP:
                if d == domain:
                    human_name = h
                    break

        # Tech stacks per tier
        if is_mob:
            t1 = f"React Native + Expo + {db} + AsyncStorage"
            t2 = f"React Native + FastAPI backend + {db} + Redux Toolkit" + (" + WebSockets" if has_rt else "")
            t3 = f"React Native + Microservices + {db} Cluster + Kafka" + (" + WebSockets" if has_rt else "")
        elif is_api:
            t1 = f"{'FastAPI' if not lang else lang + ' FastAPI'} + {db}"
            t2 = f"FastAPI + {db} + Redis + Celery"
            t3 = f"Microservices + Kubernetes + {db} Cluster + Kafka + Redis"
        else:
            t1 = f"{'Python Flask' if not lang else lang} + {db} + Vanilla JS"
            t2 = f"FastAPI + {db} + React" + (" + WebSockets" if has_rt else "") + " + Redis"
            t3 = f"Microservices + Kubernetes + {db} Cluster + Kafka + React"

        n = human_name   # short alias — used in all names/descriptions below

        return [
            {"name": f"{n} MVP",
             "description": f"Get your {n} {'mobile app' if is_mob else 'app'} running fast. Minimal complexity, perfect for validation.",
             "tech_stack": t1, "timeline": "1-2 weeks", "effort": "Low", "risk_score": 0.20,
             "phases": [
                 {"name": "Phase 1: Setup",    "tasks": ["Project scaffold", "Core models", "Basic endpoints", "Local DB"]},
                 {"name": "Phase 2: Features", "tasks": ["Main business logic", "Auth", "API integration", "Basic UI"]},
                 {"name": "Phase 3: Ship",     "tasks": ["Tests", "Docker", "Deploy", "Monitoring"]},
             ]},
            {"name": f"Production {n}",
             "description": f"Production-ready {n} with proper auth, caching, tests, and full observability.",
             "tech_stack": t2, "timeline": "4-8 weeks", "effort": "Medium", "risk_score": 0.38,
             "phases": [
                 {"name": "Phase 1: Design",   "tasks": ["Architecture", "DB schema", "API design", "Auth strategy"]},
                 {"name": "Phase 2: Backend",  "tasks": ["REST API", "JWT auth", "Caching", "Validation", "Tests"]},
                 {"name": "Phase 3: Frontend", "tasks": ["UI components", "State management", "API hooks", "Responsive"]},
                 {"name": "Phase 4: DevOps",   "tasks": ["Docker Compose", "CI/CD", "Monitoring", "Load testing"]},
             ]},
            {"name": f"Enterprise {n} Platform",
             "description": f"Enterprise-grade {n} built for high load, distributed teams, and long-term scale.",
             "tech_stack": t3, "timeline": "12-16 weeks", "effort": "High", "risk_score": 0.55,
             "phases": [
                 {"name": "Phase 1: Infra",    "tasks": ["Microservices design", "K8s cluster", f"{db} sharding", "Kafka", "API Gateway"]},
                 {"name": "Phase 2: Services", "tasks": ["Auth service", "Core services", "Event streaming", "Service mesh", "gRPC"]},
                 {"name": "Phase 3: Frontend", "tasks": ["App shell", "Real-time updates", "Offline support", "CDN", "A11y"]},
                 {"name": "Phase 4: Ops",      "tasks": ["Prometheus/Grafana", "ELK stack", "Auto-scaling", "DR plan", "Pen test"]},
             ]},
        ]

    # ================================================================== #
    # History API
    # ================================================================== #
    def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        out = []
        for chat_id, s in self.sessions.items():
            if s.get("user_id") == user_id:
                msgs = s.get("messages", [])
                out.append({
                    "chat_id":       chat_id,
                    "title":         self._extract_title(s),
                    "created_at":    s.get("created_at"),
                    "updated_at":    msgs[-1].get("timestamp") if msgs else s.get("created_at"),
                    "message_count": len(msgs),
                })
        return sorted(out, key=lambda x: x.get("updated_at", ""), reverse=True)

    def get_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        s = self.sessions.get(chat_id)
        return s.get("messages", []) if s else []

    def _extract_title(self, s: Dict) -> str:
        for msg in s.get("messages", []):
            if msg.get("role") == "user":
                c = msg.get("content", "")
                return (c[:50] + "...") if len(c) > 50 else c
        return "New Chat"


# Singleton
cosensei_service = CoSenseiAPIService()
