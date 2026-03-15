"""
Generator AI - Generates three distinct solution strategies.
Receives prompts from Middle AI and produces solutions respecting risk levels.
Fully dynamic generation driven by parsed user request context.
"""
from __future__ import annotations

from typing import Dict, List, Any, Optional


class GeneratorAI:
    """
    Generates three distinct solution strategies for a given task.
    Respects risk assessments and constraints from Middle AI.
    All generation is driven by parsed user request context — no static templates.
    """

    def __init__(self):
        self.solutions_cache = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_solutions(
        self,
        prompt_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate three solutions based on Middle AI prompt.
        Always produces structurally different solutions with detailed phases.
        """
        task_context = prompt_data.get("task_context", {})
        user_request = prompt_data.get("user_request", "")
        risk_level = prompt_data.get("risk_level", "MEDIUM")
        recommended_strategy = prompt_data.get("recommended_strategy", "optimized")
        constraints = prompt_data.get("solution_constraints", {})

        # Parse the user request into rich detected_info
        detected_info = self._parse_user_request(user_request, task_context)

        solutions = [
            self._generate_simple_solution(task_context, constraints, prompt_data, user_request, detected_info),
            self._generate_optimized_solution(task_context, constraints, prompt_data, user_request, detected_info),
            self._generate_scalable_solution(task_context, constraints, prompt_data, user_request, detected_info),
        ]

        # Mark recommended solution
        strategy_map = {"simple": 0, "optimized": 1, "scalable": 2}
        recommended_idx = strategy_map.get(recommended_strategy, 1)
        solutions[recommended_idx]["recommended"] = True

        return solutions

    # ------------------------------------------------------------------
    # Request parsing
    # ------------------------------------------------------------------

    def _parse_user_request(
        self, user_request: str, task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract rich metadata from the raw user request and any existing task_context.
        Returns a dict with language, framework, database, project_type, feature flags,
        scale_hint, and famous_app_match.
        Falls back to sensible defaults when nothing is detected.
        """
        text = user_request.lower()

        # ---- language detection ----
        lang_map = {
            "python": ["python", "flask", "fastapi", "django", "pytorch", "pandas"],
            "javascript": ["javascript", "node", "nodejs", "express", "react", "vue", "nextjs", "next.js"],
            "typescript": ["typescript", "nestjs", "nest.js", "angular"],
            "java": ["java", "spring", "springboot", "spring boot"],
            "go": ["golang", " go ", "gin framework", "echo framework"],
            "rust": ["rust", "actix", "axum", "rocket"],
            "php": ["php", "laravel", "symfony"],
        }
        language = task_context.get("language") or self._first_match(text, lang_map) or "python"

        # ---- framework detection ----
        fw_map = {
            "fastapi": ["fastapi", "fast api"],
            "flask": ["flask"],
            "django": ["django"],
            "express": ["express", "expressjs", "express.js"],
            "nestjs": ["nestjs", "nest.js", "nestframework"],
            "spring": ["spring", "spring boot", "springboot"],
            "rails": ["rails", "ruby on rails", "ror"],
            "laravel": ["laravel"],
            "nextjs": ["next.js", "nextjs"],
        }
        framework = task_context.get("framework") or self._first_match(text, fw_map)
        if not framework:
            # smart language-based defaults
            lang_fw_defaults = {
                "python": "fastapi",
                "javascript": "express",
                "typescript": "nestjs",
                "java": "spring",
                "go": "gin",
                "rust": "actix",
                "php": "laravel",
            }
            framework = lang_fw_defaults.get(language, "fastapi")

        # ---- database detection ----
        db_map = {
            "postgresql": ["postgresql", "postgres", "pg "],
            "mongodb": ["mongodb", "mongo"],
            "mysql": ["mysql"],
            "redis": ["redis"],
            "sqlite": ["sqlite"],
            "dynamodb": ["dynamodb", "dynamo"],
        }
        database = task_context.get("database") or self._first_match(text, db_map)
        if not database:
            # smart project-type aware default chosen after project_type detection below
            database = None  # resolved after project_type is known

        # ---- project type detection ----
        famous_apps = {
            "spotify": "streaming",
            "netflix": "streaming",
            "youtube": "streaming",
            "twitter": "social",
            "instagram": "social",
            "facebook": "social",
            "airbnb": "marketplace",
            "uber": "marketplace",
            "amazon": "ecommerce",
            "shopify": "ecommerce",
            "slack": "chat",
            "discord": "chat",
            "whatsapp": "chat",
            "reddit": "social",
            "medium": "blog",
            "wordpress": "blog",
            "stripe": "fintech",
            "robinhood": "fintech",
            "duolingo": "education",
            "coursera": "education",
            "github": "saas",
            "jira": "saas",
            "trello": "saas",
            "tableau": "dashboard",
            "grafana": "dashboard",
        }
        famous_app_match: Optional[str] = None
        project_type_override: Optional[str] = None
        for app_name, app_type in famous_apps.items():
            if app_name in text:
                famous_app_match = app_name
                project_type_override = app_type
                break

        type_map = {
            "ecommerce": ["ecommerce", "e-commerce", "shop", "store", "cart", "checkout", "product"],
            "social": ["social", "social network", "feed", "follow", "like", "post", "profile"],
            "blog": ["blog", "cms", "content management", "article", "post"],
            "dashboard": ["dashboard", "analytics", "metrics", "reporting", "admin panel"],
            "streaming": ["streaming", "video", "audio", "media", "player", "podcast"],
            "chat": ["chat", "messaging", "instant message", "realtime chat", "dm"],
            "fintech": ["fintech", "finance", "banking", "payment", "wallet", "trading", "crypto"],
            "healthcare": ["healthcare", "health", "medical", "hospital", "patient", "clinic"],
            "education": ["education", "learning", "course", "quiz", "lms", "school"],
            "marketplace": ["marketplace", "two-sided", "freelance", "gig", "booking"],
            "saas": ["saas", "software as a service", "subscription", "tenant", "workspace"],
            "ai_ml": ["ai", "machine learning", "ml model", "neural", "nlp", "computer vision", "llm"],
            "iot": ["iot", "sensor", "device", "embedded", "mqtt"],
            "api": ["api", "rest api", "graphql", "backend only", "microservice"],
        }
        project_type = project_type_override or self._first_match(text, type_map) or "general"

        # Resolve database default now that project_type is known
        if database is None:
            db_defaults = {
                "streaming": "postgresql",
                "social": "postgresql",
                "ecommerce": "postgresql",
                "fintech": "postgresql",
                "healthcare": "postgresql",
                "chat": "mongodb",
                "iot": "mongodb",
                "ai_ml": "postgresql",
                "saas": "postgresql",
                "marketplace": "postgresql",
                "dashboard": "postgresql",
                "blog": "postgresql",
                "education": "postgresql",
                "api": "postgresql",
                "general": "postgresql",
            }
            database = db_defaults.get(project_type, "postgresql")

        # ---- feature flags ----
        has_auth = any(kw in text for kw in [
            "auth", "login", "register", "signup", "sign up", "jwt", "oauth", "user account",
            "authentication", "authorization", "password",
        ])
        has_payments = any(kw in text for kw in [
            "payment", "stripe", "checkout", "billing", "subscription", "monetize",
            "purchase", "buy", "sell", "invoice",
        ])
        has_realtime = any(kw in text for kw in [
            "realtime", "real-time", "websocket", "socket.io", "live", "push notification",
            "instant", "streaming data", "chat",
        ])
        has_ml = any(kw in text for kw in [
            "machine learning", "ml", "ai model", "predict", "neural network", "nlp",
            "recommendation", "classification", "deep learning", "llm", "gpt", "transformers",
        ])
        has_file_upload = any(kw in text for kw in [
            "upload", "file", "image", "photo", "video upload", "s3", "storage",
            "attachment", "media upload",
        ])
        has_search = any(kw in text for kw in [
            "search", "elasticsearch", "algolia", "full-text", "fulltext", "filter",
        ])

        # project_type overrides for chat/streaming
        if project_type == "chat":
            has_realtime = True
        if project_type == "streaming":
            has_file_upload = True

        # ---- scale hint ----
        scale_hints_large = [
            "million users", "millions of users", "enterprise", "high traffic",
            "large scale", "billion", "global", "distributed", "100k", "1 million",
        ]
        scale_hints_small = [
            "mvp", "prototype", "small", "personal", "side project", "hobby",
            "poc", "proof of concept", "solo", "indie",
        ]
        if any(kw in text for kw in scale_hints_large):
            scale_hint = "large"
        elif any(kw in text for kw in scale_hints_small):
            scale_hint = "small"
        else:
            scale_hint = "medium"

        return {
            "language": language,
            "framework": framework,
            "database": database,
            "project_type": project_type,
            "has_auth": has_auth,
            "has_payments": has_payments,
            "has_realtime": has_realtime,
            "has_ml": has_ml,
            "has_file_upload": has_file_upload,
            "has_search": has_search,
            "scale_hint": scale_hint,
            "famous_app_match": famous_app_match,
        }

    # ------------------------------------------------------------------
    # Solution generators
    # ------------------------------------------------------------------

    def _generate_simple_solution(
        self,
        task_context: Dict[str, str],
        constraints: Dict[str, str],
        prompt_data: Dict[str, Any],
        user_request: str = "",
        detected_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate minimal viable product solution with implementation phases."""
        if detected_info is None:
            detected_info = self._parse_user_request(user_request, task_context)

        framework = detected_info["framework"]
        database = detected_info["database"]
        project_type = detected_info["project_type"]

        # Dynamic naming
        pt_label = project_type.replace("_", " ").title()
        fw_label = framework.title()
        name = f"Quick {pt_label} MVP"
        if project_type == "general":
            name = f"Minimal {fw_label} Starter"

        title = name
        description = (
            f"Minimal {pt_label} app with {fw_label} — core features only, "
            f"single server, {database.upper()}, no scaling overhead."
        )

        # Risk score
        base_risk = 0.2
        if detected_info["has_payments"]:
            base_risk += 0.06
        if detected_info["has_ml"]:
            base_risk += 0.05
        risk_score = round(min(base_risk, 0.38), 2)

        # Phases
        phases = self._build_phases_simple(detected_info, framework, database)

        # Tech stack string using detected values
        extras = []
        if detected_info["has_auth"]:
            extras.append("JWT")
        if detected_info["has_payments"]:
            extras.append("Stripe")
        tech_stack = f"{fw_label} + {database.upper()} + HTML/CSS/JS"
        if extras:
            tech_stack += " + " + " + ".join(extras)

        # Architecture
        architecture = self._architecture_simple(framework, database, detected_info)

        return {
            "id": "1",
            "strategy": "simple",
            "name": name,
            "title": title,
            "description": description,
            "characteristics": self._characteristics_simple(detected_info),
            "architecture": architecture,
            "effort": "Low",
            "timeline": "1-2 weeks",
            "scalability": "Low",
            "maintenance": "Low",
            "risk_score": risk_score,
            "risk_mitigation": "Reduces complexity-related stress and technical risk",
            "constraints_applied": constraints,
            "tech_stack": tech_stack,
            "phases": phases,
            "detected_info": detected_info,
        }

    def _generate_optimized_solution(
        self,
        task_context: Dict[str, str],
        constraints: Dict[str, str],
        prompt_data: Dict[str, Any],
        user_request: str = "",
        detected_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate production-ready solution with best practices and contextual phases."""
        if detected_info is None:
            detected_info = self._parse_user_request(user_request, task_context)

        framework = detected_info["framework"]
        database = detected_info["database"]
        project_type = detected_info["project_type"]

        # Dynamic naming
        pt_label = project_type.replace("_", " ").title()
        fw_label = framework.title()
        name = f"Production-Ready {fw_label} App"
        if project_type not in ("general", "api"):
            name = f"{pt_label} Platform"
        title = name

        description = (
            f"Production-grade {pt_label} solution — best practices, "
            f"performance optimization, proper error handling, and CI/CD."
        )

        # Risk score
        base_risk = 0.35
        if detected_info["has_payments"]:
            base_risk += 0.08
        if detected_info["has_ml"]:
            base_risk += 0.07
        if detected_info["has_realtime"]:
            base_risk += 0.04
        risk_score = round(min(base_risk, 0.58), 2)

        # Phases
        phases = self._build_phases_optimized(detected_info, framework, database, pt_label)

        # Tech stack
        cache_tech = "Redis"
        fe_tech = "React"
        tech_stack = f"{fw_label} + {database.upper()} + {fe_tech} + {cache_tech}"
        if detected_info["has_payments"]:
            tech_stack += " + Stripe"
        if detected_info["has_search"]:
            tech_stack += " + Elasticsearch"

        architecture = self._architecture_optimized(framework, database, detected_info)

        return {
            "id": "2",
            "strategy": "optimized",
            "name": name,
            "title": title,
            "description": description,
            "characteristics": self._characteristics_optimized(detected_info),
            "architecture": architecture,
            "effort": "Medium",
            "timeline": "4-8 weeks",
            "scalability": "Medium",
            "maintenance": "Medium",
            "risk_score": risk_score,
            "risk_mitigation": "Balances complexity and reliability with proven patterns",
            "constraints_applied": constraints,
            "tech_stack": tech_stack,
            "phases": phases,
            "detected_info": detected_info,
        }

    def _generate_scalable_solution(
        self,
        task_context: Dict[str, str],
        constraints: Dict[str, str],
        prompt_data: Dict[str, Any],
        user_request: str = "",
        detected_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate enterprise-grade scalable solution with contextual phases."""
        if detected_info is None:
            detected_info = self._parse_user_request(user_request, task_context)

        database = detected_info["database"]
        project_type = detected_info["project_type"]
        scale_hint = detected_info["scale_hint"]

        # Dynamic naming
        pt_label = project_type.replace("_", " ").title()
        if scale_hint == "large":
            name = f"Distributed {pt_label} Architecture"
        else:
            name = f"Enterprise {pt_label} System"
        title = name

        description = (
            f"Enterprise-grade {pt_label} — distributed microservices, "
            f"Kubernetes orchestration, event-driven design, and full observability."
        )

        # Risk score
        base_risk = 0.55
        if detected_info["has_payments"]:
            base_risk += 0.07
        if detected_info["has_ml"]:
            base_risk += 0.08
        if detected_info["has_realtime"]:
            base_risk += 0.03
        if detected_info["has_file_upload"]:
            base_risk += 0.02
        risk_score = round(min(base_risk, 0.85), 2)

        # Phases
        phases = self._build_phases_scalable(detected_info, database, pt_label)

        # Tech stack
        tech_stack = f"Microservices + Kubernetes + {database.upper()} Cluster + Kafka"
        if detected_info["has_realtime"]:
            tech_stack += " + WebSocket Gateway"
        if detected_info["has_ml"]:
            tech_stack += " + ML Serving (TorchServe/TF Serving)"
        if detected_info["has_search"]:
            tech_stack += " + Elasticsearch"

        architecture = self._architecture_scalable(database, detected_info)

        return {
            "id": "3",
            "strategy": "scalable",
            "name": name,
            "title": title,
            "description": description,
            "characteristics": self._characteristics_scalable(detected_info),
            "architecture": architecture,
            "effort": "High",
            "timeline": "12-16 weeks",
            "scalability": "High",
            "maintenance": "High",
            "risk_score": risk_score,
            "risk_mitigation": "Handles future growth, team scaling, and fault tolerance",
            "constraints_applied": constraints,
            "tech_stack": tech_stack,
            "phases": phases,
            "detected_info": detected_info,
        }

    # ------------------------------------------------------------------
    # Phase builders
    # ------------------------------------------------------------------

    def _build_phases_simple(
        self, di: Dict, framework: str, database: str
    ) -> List[Dict[str, Any]]:
        fw = framework.title()
        db = database.upper()
        phases = [
            {
                "name": "Phase 1: Foundation Setup",
                "tasks": [
                    "Create project directory and virtual environment",
                    f"Install {fw} and core dependencies",
                    f"Configure {db} connection",
                    "Define base project structure",
                ],
            }
        ]

        feature_tasks: List[str] = []
        if di["has_auth"]:
            feature_tasks += [
                "Implement user model (email, password_hash)",
                "Add JWT login/register endpoints",
                "Protect routes with auth middleware",
            ]
        if di["has_payments"]:
            feature_tasks += [
                "Integrate Stripe Checkout",
                "Add webhook endpoint for payment events",
            ]
        if di["has_realtime"]:
            feature_tasks += [
                "Add basic WebSocket support",
                "Implement simple pub/sub for live updates",
            ]
        if di["has_file_upload"]:
            feature_tasks += [
                "Add file upload endpoint",
                "Store uploads locally (or S3 bucket)",
            ]

        # Project-type specific core tasks
        core_tasks = self._core_tasks_by_type(di["project_type"], "simple")
        feature_tasks = core_tasks + feature_tasks

        if feature_tasks:
            phases.append({"name": "Phase 2: Core Features", "tasks": feature_tasks})

        phases.append(
            {
                "name": f"Phase {'3' if feature_tasks else '2'}: Testing & Deploy",
                "tasks": [
                    "Write basic unit tests",
                    "Manual QA on all endpoints",
                    "Deploy to Heroku / Fly.io",
                    "Set up basic error logging",
                ],
            }
        )
        return phases

    def _build_phases_optimized(
        self, di: Dict, framework: str, database: str, pt_label: str
    ) -> List[Dict[str, Any]]:
        fw = framework.title()
        db = database.upper()
        phases = [
            {
                "name": "Phase 1: Design & Architecture",
                "tasks": [
                    f"Define {pt_label} domain models",
                    "Design RESTful API contract (OpenAPI spec)",
                    f"Design {db} schema with indexes",
                    "Plan caching strategy (Redis)",
                    "Define security requirements",
                ],
            },
            {
                "name": "Phase 2: Backend Implementation",
                "tasks": [
                    f"Build {fw} API with layered architecture",
                    "Implement repository/service pattern",
                    "Add Alembic migrations",
                    "Input validation and error handling",
                    "Structured logging with request IDs",
                    "Redis caching layer",
                ],
            },
        ]

        # Feature-driven phase
        feature_tasks: List[str] = []
        if di["has_auth"]:
            feature_tasks += [
                "JWT authentication with refresh tokens",
                "Role-based access control (RBAC)",
                "Password reset flow",
            ]
        if di["has_payments"]:
            feature_tasks += [
                "Stripe subscription / one-time payment integration",
                "Webhook handler for payment lifecycle events",
                "Payment status stored in DB",
            ]
        if di["has_realtime"]:
            feature_tasks += [
                "WebSocket / Socket.io server setup",
                "Redis pub/sub for room broadcasting",
                "Connection lifecycle management",
            ]
        if di["has_file_upload"]:
            feature_tasks += [
                "Multipart file upload endpoint",
                "S3 pre-signed URL generation",
                "File metadata stored in DB",
            ]
        if di["has_search"]:
            feature_tasks += [
                "Elasticsearch index setup",
                "Full-text search endpoint",
                "Search result pagination",
            ]
        if di["has_ml"]:
            feature_tasks += [
                "ML model loading (scikit-learn / lightweight)",
                "Prediction endpoint with input validation",
                "Async inference with Celery",
            ]

        core_tasks = self._core_tasks_by_type(di["project_type"], "optimized")
        all_feature_tasks = core_tasks + feature_tasks

        if all_feature_tasks:
            phases.append({"name": "Phase 3: Feature Integration", "tasks": all_feature_tasks})

        phases += [
            {
                "name": "Phase 4: Frontend",
                "tasks": [
                    "React / Next.js UI components",
                    "API integration with proper loading states",
                    "Responsive layout",
                    "Error boundary and toast notifications",
                ],
            },
            {
                "name": "Phase 5: DevOps & QA",
                "tasks": [
                    "Unit tests (80%+ coverage)",
                    "Docker multi-stage build",
                    "docker-compose for local stack",
                    "GitHub Actions CI/CD",
                    "Sentry error tracking",
                ],
            },
        ]
        return phases

    def _build_phases_scalable(
        self, di: Dict, database: str, pt_label: str
    ) -> List[Dict[str, Any]]:
        db = database.upper()
        phases = [
            {
                "name": "Phase 1: Distributed Architecture",
                "tasks": [
                    "Design microservice boundaries (DDD)",
                    "Set up Kubernetes cluster (EKS / GKE)",
                    f"Design {db} sharding / replication strategy",
                    "API Gateway (Kong / AWS API GW)",
                    "Service mesh planning (Istio)",
                    "Kafka topic design for event streaming",
                ],
            },
            {
                "name": "Phase 2: Core Services",
                "tasks": [
                    "Auth service (OAuth2 + JWT + MFA)",
                    f"{pt_label} business logic service",
                    "Event publishing with Kafka producers",
                    "Kafka consumer workers",
                    "Redis Cluster for distributed caching",
                    "gRPC inter-service communication",
                ],
            },
        ]

        # Feature-driven phases
        feature_tasks: List[str] = []
        if di["has_auth"]:
            feature_tasks += [
                "OAuth2 social login (Google, GitHub)",
                "Multi-factor authentication (TOTP)",
                "Session revocation and audit log",
            ]
        if di["has_payments"]:
            feature_tasks += [
                "Dedicated payment microservice",
                "Idempotent Stripe charge processing",
                "Billing event sourcing",
                "Invoice PDF generation",
            ]
        if di["has_realtime"]:
            feature_tasks += [
                "Dedicated WebSocket gateway service",
                "Redis pub/sub cluster for message fanout",
                "Connection draining for zero-downtime deploys",
            ]
        if di["has_file_upload"]:
            feature_tasks += [
                "Media ingestion service with S3 multipart upload",
                "Image/video transcoding pipeline (FFmpeg workers)",
                "CDN (CloudFront) invalidation on updates",
            ]
        if di["has_search"]:
            feature_tasks += [
                "Elasticsearch cluster setup",
                "Index sync via Kafka consumers",
                "Autocomplete and relevance tuning",
            ]
        if di["has_ml"]:
            feature_tasks += [
                "ML model training service (distributed, GPU)",
                "Model registry (MLflow)",
                "TorchServe / TF Serving inference microservice",
                "A/B model rollout with feature flags",
                "Online feature store (Feast)",
            ]

        core_tasks = self._core_tasks_by_type(di["project_type"], "scalable")
        all_feature_tasks = core_tasks + feature_tasks

        if all_feature_tasks:
            phases.append({"name": "Phase 3: Advanced Features", "tasks": all_feature_tasks})

        phases += [
            {
                "name": "Phase 4: Frontend & Client SDKs",
                "tasks": [
                    "React / Next.js with SSR",
                    "Real-time UI updates via WebSocket",
                    "CDN static asset delivery",
                    "Mobile app (React Native / Flutter)",
                ],
            },
            {
                "name": "Phase 5: Observability & Production",
                "tasks": [
                    "Prometheus + Grafana monitoring dashboards",
                    "ELK stack for centralized logging",
                    "OpenTelemetry distributed tracing (Jaeger)",
                    "Auto-scaling policies (HPA)",
                    "Canary and blue/green deployments",
                    "Disaster recovery: cross-region replication",
                    "Security audit and penetration testing",
                ],
            },
        ]
        return phases

    def _core_tasks_by_type(self, project_type: str, tier: str) -> List[str]:
        """Return project-type-specific core implementation tasks."""
        tasks_map: Dict[str, Dict[str, List[str]]] = {
            "ecommerce": {
                "simple": ["Product listing CRUD", "Shopping cart (session-based)", "Basic order creation"],
                "optimized": ["Product catalog with variants", "Persistent cart (DB)", "Order management system", "Inventory tracking"],
                "scalable": ["Product service + Inventory service", "Cart service with Redis TTL", "Order saga pattern (distributed transactions)", "Fulfillment workflow"],
            },
            "social": {
                "simple": ["User profiles", "Create/read posts", "Follow system"],
                "optimized": ["News feed (fan-out on read)", "Likes and comments", "Follow graph queries", "Notification system"],
                "scalable": ["Fan-out on write for hot users", "Graph DB for social connections", "Activity stream service", "Recommendation engine"],
            },
            "blog": {
                "simple": ["Post CRUD with markdown", "Tags and categories", "RSS feed"],
                "optimized": ["Draft / published workflow", "SEO metadata", "Comment system", "Search by tag"],
                "scalable": ["Multi-author / multi-tenant CMS", "CDN-cached static generation", "Personalised recommendation feed"],
            },
            "streaming": {
                "simple": ["Media file upload", "Basic video/audio player", "Playlist management"],
                "optimized": ["HLS adaptive streaming", "CDN delivery", "Watch history tracking", "Recommendations"],
                "scalable": ["Transcoding pipeline (FFmpeg workers)", "Multi-CDN failover", "Live streaming (RTMP ingest)", "Content delivery analytics"],
            },
            "chat": {
                "simple": ["Send/receive messages", "Basic room creation", "Message history"],
                "optimized": ["Typing indicators", "Message read receipts", "File attachments", "Push notifications"],
                "scalable": ["Presence service", "Offline message queue", "End-to-end encryption", "Message search"],
            },
            "dashboard": {
                "simple": ["Data tables and charts", "Date range filters", "CSV export"],
                "optimized": ["Real-time metric updates", "Custom widget builder", "Role-based views", "Scheduled reports"],
                "scalable": ["ClickHouse / BigQuery OLAP backend", "Streaming aggregations (Kafka Streams)", "Embedded analytics SDK", "Multi-tenant isolation"],
            },
            "fintech": {
                "simple": ["Account balance display", "Transaction history", "Basic transfer"],
                "optimized": ["Double-entry bookkeeping", "Fraud detection rules", "Multi-currency support", "Audit trail"],
                "scalable": ["Ledger service (event sourcing)", "Compliance reporting", "Real-time risk scoring", "Reconciliation batch jobs"],
            },
            "ai_ml": {
                "simple": ["Dataset ingestion", "Simple model training script", "Prediction REST endpoint"],
                "optimized": ["Experiment tracking (MLflow)", "Model versioning", "Batch and online inference", "Model performance dashboard"],
                "scalable": ["Distributed training (Horovod / DeepSpeed)", "Feature store", "Model A/B testing", "Drift detection and retraining triggers"],
            },
        }
        project_tasks = tasks_map.get(project_type, {})
        return project_tasks.get(tier, [])

    # ------------------------------------------------------------------
    # Characteristics builders
    # ------------------------------------------------------------------

    def _characteristics_simple(self, di: Dict) -> List[str]:
        chars = ["Monolithic architecture", "Single database", "Basic UI", "Single deployment unit"]
        if di["has_auth"]:
            chars.append("Session or JWT auth")
        if di["has_realtime"]:
            chars.append("Basic WebSocket support")
        return chars

    def _characteristics_optimized(self, di: Dict) -> List[str]:
        chars = [
            "Layered architecture (API, Service, Data layers)",
            "Redis caching layer",
            "Comprehensive logging",
            "Error handling & recovery",
            "API versioning",
        ]
        if di["has_auth"]:
            chars.append("JWT with RBAC")
        if di["has_realtime"]:
            chars.append("WebSocket server with Redis pub/sub")
        if di["has_payments"]:
            chars.append("PCI-aware payment handling")
        if di["has_search"]:
            chars.append("Full-text search (Elasticsearch)")
        return chars

    def _characteristics_scalable(self, di: Dict) -> List[str]:
        chars = [
            "Microservices architecture",
            "Event-driven with Kafka",
            "Distributed caching (Redis Cluster)",
            "API Gateway",
            "Horizontal auto-scaling",
            "Full observability (tracing, metrics, logs)",
        ]
        if di["has_realtime"]:
            chars.append("Dedicated WebSocket gateway")
        if di["has_ml"]:
            chars.append("ML serving infrastructure")
        if di["has_payments"]:
            chars.append("Dedicated payment microservice")
        if di["has_search"]:
            chars.append("Elasticsearch cluster")
        return chars

    # ------------------------------------------------------------------
    # Architecture diagram builders (use detected tech)
    # ------------------------------------------------------------------

    def _architecture_simple(
        self, framework: str, database: str, di: Dict
    ) -> str:
        fw = (framework or "Backend").upper()
        db = (database or "Database").upper()
        lines = [
            "Frontend (HTML/CSS/JS)",
            "    |",
            "    v",
            f"[{fw} Backend]",
        ]
        if di.get("has_auth"):
            lines += ["    |  (JWT Auth middleware)", "    v"]
        else:
            lines += ["    |", "    v"]
        if di.get("has_payments"):
            lines += [f"[{db} Database] <--> [Stripe Payment Gateway]"]
        else:
            lines += [f"[{db} Database]"]
        if di.get("has_file_upload"):
            lines += ["    |", "    v", "[S3 / Object Storage]"]
        if di.get("has_realtime"):
            lines += ["    |", "    v", "[WebSocket Server (same process)]"]
        lines.append("\nSingle deployed unit — straightforward REST API.")
        return "\n".join(lines)

    def _architecture_optimized(
        self, framework: str, database: str, di: Dict
    ) -> str:
        fw = (framework or "API").upper()
        db = (database or "Database").upper()
        lines = [
            "[Client / Web UI]",
            "        |",
            "        v",
            "[Load Balancer]",
            "        |",
            "        v",
            f"[{fw} API Server] <--> [Redis Cache]",
            "        |",
            "        v",
            "[Service Layer]",
            "        |",
            "        v",
            f"    [{db} Database]",
        ]
        optional = []
        if di.get("has_payments"):
            optional.append("        |")
            optional.append("        v")
            optional.append("[Stripe Payment Gateway]")
        if di.get("has_file_upload"):
            optional.append("        |")
            optional.append("        v")
            optional.append("[S3 Bucket / CDN]")
        if di.get("has_search"):
            optional.append("        |")
            optional.append("        v")
            optional.append("[Elasticsearch]")
        if di.get("has_realtime"):
            optional.append("        |")
            optional.append("        v")
            optional.append("[WebSocket Server + Redis Pub/Sub]")
        if di.get("has_ml"):
            optional.append("        |")
            optional.append("        v")
            optional.append("[ML Inference Service (Celery + scikit-learn)]")
        lines += optional
        lines.append("\nFeatures: Caching, Services, Error Handling, Logging, CI/CD")
        return "\n".join(lines)

    def _architecture_scalable(
        self, database: str, di: Dict
    ) -> str:
        db = (database or "Database").upper()
        lines = [
            "[Clients: Web / Mobile / IoT]",
            "        |",
            "        v",
            "[API Gateway / Load Balancer]",
            "        |",
            "    ____|_______________________________",
            "   |        |          |          |    |",
            "   v        v          v          v    v",
            "[Auth]  [Business]  [Worker]  [Admin] [Notify]",
            " Svc      Service    Service   Panel   Service",
            "   |        |          |          |",
            "   |________v__________|__________|",
            "        |",
            "   [Kafka Event Bus]",
            "        |",
            "   _____|_______________________________________",
            "  |       |          |         |        |      |",
            "  v       v          v         v        v      v",
            f"[Redis] [Search] [Analytics] [{db}] [CDN] [Blob]",
            "                              [Cluster]",
        ]
        if di.get("has_realtime"):
            lines += [
                "        |",
                "        v",
                "[WebSocket Gateway + Redis Cluster Pub/Sub]",
            ]
        if di.get("has_ml"):
            lines += [
                "        |",
                "        v",
                "[ML Serving (TorchServe / TF Serving) + GPU Nodes]",
                "[Feature Store (Feast)] <--> [Model Registry (MLflow)]",
            ]
        if di.get("has_payments"):
            lines += [
                "        |",
                "        v",
                "[Payment Microservice] <--> [Stripe API]",
            ]
        lines.append("\nKubernetes orchestration — Prometheus/Grafana/ELK observability stack")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def format_for_display(self, solutions: List[Dict[str, Any]]) -> str:
        """Format solutions for terminal display."""
        lines = [
            "\n" + "=" * 70,
            "SOLUTION OPTIONS",
            "=" * 70,
        ]

        for sol in solutions:
            marker = "✓ RECOMMENDED" if sol.get("recommended") else ""
            lines.append(f"\n{sol['id']}. {sol['title']} {marker}")
            lines.append(f"   {sol['description']}")
            lines.append(f"   Effort: {sol['effort']} | Scalability: {sol['scalability']}")
            tech = sol.get("tech_stack", "N/A")
            lines.append(f"   Tech: {tech if isinstance(tech, str) else tech.get('backend', 'N/A')}")

        lines.append("\n" + "=" * 70)
        lines.append("Select a solution: type 1, 2, 3 (or 'simple', 'optimized', 'scalable')")
        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    def get_solution_by_strategy(
        self, strategy: str, solutions: List[Dict[str, Any]]
    ) -> Dict[str, Any] | None:
        """Get a specific solution by strategy name."""
        for sol in solutions:
            if sol.get("strategy", "").lower() == strategy.lower() or sol.get("id") == strategy:
                return sol
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _first_match(text: str, mapping: Dict[str, List[str]]) -> Optional[str]:
        """Return the first key in mapping whose any keyword appears in text."""
        for key, keywords in mapping.items():
            for kw in keywords:
                if kw in text:
                    return key
        return None
