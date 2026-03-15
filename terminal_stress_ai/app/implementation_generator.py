"""
CoSensei Implementation Generator (AI #4)
Generates concrete implementation details, code structure, and deployment steps
for selected architecture solutions.  Enriched with requirements.txt, .env template,
sample API code, database schema SQL, and Dockerfile generation.
"""

import sys
import os
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ImplementationGenerator:
    """AI #4: Concrete implementation guide generator"""

    def __init__(self):
        self.implementation_templates = {
            "simple": {
                "title": "Simple MVP Implementation",
                "duration": "1-2 weeks",
                "complexity": "Low",
            },
            "optimized": {
                "title": "Optimized Production Implementation",
                "duration": "4-8 weeks",
                "complexity": "Medium",
            },
            "scalable": {
                "title": "Enterprise Scalable Implementation",
                "duration": "12-16 weeks",
                "complexity": "High",
            },
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_implementation(
        self,
        solution: Dict[str, Any],
        task_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate concrete implementation plan for selected solution"""

        title = solution.get("title", "Unknown Solution")
        template_type = self._get_template_type(title)

        # Pull detected_info carried by the solution dict (set by GeneratorAI)
        detected_info: Dict[str, Any] = (
            solution.get("detected_info")
            or (task_context or {}).get("detected_info")
            or {}
        )

        implementation_plan = {
            "solution_title": title,
            "implementation_type": template_type,
            "project_structure": self._generate_project_structure(template_type, task_context),
            "setup_instructions": self._generate_setup_instructions(template_type),
            "core_files_to_create": self._generate_core_files(template_type, solution),
            "configuration": self._generate_configuration(template_type, solution),
            "database_setup": self._generate_database_setup(template_type, solution),
            "deployment_steps": self._generate_deployment_steps(template_type, solution),
            "development_checklist": self._generate_dev_checklist(template_type),
            "estimated_hours": self._estimate_effort(template_type),
            "success_criteria": self._generate_success_criteria(solution),
            "next_steps": self._generate_next_steps(template_type),
            # --- new rich sections ---
            "requirements_txt": self._generate_requirements_txt(template_type, detected_info),
            "env_template": self._generate_env_template(template_type, detected_info),
            "sample_api_code": self._generate_sample_api_code(template_type, detected_info),
            "database_schema_sql": self._generate_database_schema_sql(template_type, detected_info),
            "dockerfile": self._generate_dockerfile(template_type),
        }

        return implementation_plan

    # ------------------------------------------------------------------
    # New generation methods
    # ------------------------------------------------------------------

    def _generate_requirements_txt(
        self, template_type: str, detected_info: Dict[str, Any]
    ) -> str:
        """Return pip requirements file content based on template and detected features."""
        framework = detected_info.get("framework", "fastapi")

        pkgs: List[str] = []

        # Core web framework
        if framework == "flask":
            pkgs += ["flask>=3.0.0", "flask-cors>=4.0.0"]
        else:
            pkgs += [
                "fastapi>=0.110.0",
                "uvicorn[standard]>=0.29.0",
                "pydantic>=2.6.0",
            ]

        # Always-on
        pkgs += [
            "sqlalchemy>=2.0.0",
            "alembic>=1.13.0",
            "python-dotenv>=1.0.0",
            "httpx>=0.27.0",
        ]

        # Feature-driven
        if detected_info.get("has_auth"):
            pkgs += ["python-jose[cryptography]>=3.3.0", "passlib[bcrypt]>=1.7.4", "bcrypt>=4.1.0"]

        if detected_info.get("has_payments"):
            pkgs += ["stripe>=8.0.0"]

        if detected_info.get("has_file_upload"):
            pkgs += ["boto3>=1.34.0", "Pillow>=10.3.0"]

        if detected_info.get("has_realtime"):
            pkgs += ["websockets>=12.0", "python-socketio>=5.11.0"]

        if detected_info.get("has_ml"):
            if template_type == "scalable":
                pkgs += [
                    "torch>=2.2.0",
                    "transformers>=4.39.0",
                    "scikit-learn>=1.4.0",
                    "pandas>=2.2.0",
                    "numpy>=1.26.0",
                ]
            else:
                pkgs += [
                    "scikit-learn>=1.4.0",
                    "pandas>=2.2.0",
                    "numpy>=1.26.0",
                ]

        if detected_info.get("has_search"):
            pkgs += ["elasticsearch>=8.13.0"]

        # Tier-specific additions
        if template_type == "optimized":
            pkgs += ["redis>=5.0.0", "celery>=5.3.0"]

        if template_type == "scalable":
            pkgs += [
                "redis>=5.0.0",
                "celery>=5.3.0",
                "kafka-python>=2.0.2",
                "prometheus-client>=0.20.0",
                "opentelemetry-api>=1.24.0",
                "opentelemetry-sdk>=1.24.0",
                "sentry-sdk>=1.44.0",
            ]

        return "\n".join(pkgs) + "\n"

    def _generate_env_template(
        self, template_type: str, detected_info: Dict[str, Any]
    ) -> str:
        """Return .env file content based on template and detected features."""
        framework = detected_info.get("framework", "fastapi")
        database = detected_info.get("database", "postgresql")

        if database == "sqlite":
            db_url = "sqlite:///./app.db"
        elif database == "mongodb":
            db_url = "mongodb://localhost:27017/myapp"
        else:
            db_url = f"{database}://user:password@localhost:5432/myapp"

        lines: List[str] = [
            "# Application",
            f"DATABASE_URL={db_url}",
            "SECRET_KEY=change-me-to-a-long-random-string",
            "DEBUG=False",
            f"APP_PORT={'5000' if framework == 'flask' else '8000'}",
            "",
        ]

        if detected_info.get("has_auth"):
            lines += [
                "# Authentication",
                "JWT_SECRET=change-me-jwt-secret",
                "JWT_EXPIRY_MINUTES=30",
                "JWT_REFRESH_EXPIRY_DAYS=7",
                "",
            ]

        if detected_info.get("has_payments"):
            lines += [
                "# Stripe",
                "STRIPE_SECRET_KEY=sk_test_...",
                "STRIPE_PUBLISHABLE_KEY=pk_test_...",
                "STRIPE_WEBHOOK_SECRET=whsec_...",
                "",
            ]

        if detected_info.get("has_file_upload"):
            lines += [
                "# AWS / S3",
                "AWS_ACCESS_KEY_ID=your-access-key",
                "AWS_SECRET_ACCESS_KEY=your-secret-key",
                "AWS_REGION=us-east-1",
                "S3_BUCKET=my-app-bucket",
                "",
            ]

        if detected_info.get("has_realtime") or template_type in ("optimized", "scalable"):
            lines += [
                "# Redis",
                "REDIS_URL=redis://localhost:6379/0",
                "",
            ]

        if template_type in ("optimized", "scalable"):
            lines += [
                "# Cache",
                "CACHE_TTL=300",
                "",
            ]

        if template_type == "scalable":
            lines += [
                "# Kafka",
                "KAFKA_BROKERS=localhost:9092",
                "",
                "# Elasticsearch",
                "ELASTICSEARCH_URL=http://localhost:9200",
                "",
                "# Observability",
                "SENTRY_DSN=https://...@sentry.io/...",
                "OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317",
                "",
            ]

        return "\n".join(lines)

    def _generate_sample_api_code(
        self, template_type: str, detected_info: Dict[str, Any]
    ) -> str:
        """Return 2-3 sample endpoint snippets relevant to the project type."""
        framework = detected_info.get("framework", "fastapi")
        project_type = detected_info.get("project_type", "general")
        use_fastapi = framework != "flask"

        if use_fastapi:
            return self._sample_fastapi_code(project_type, detected_info)
        return self._sample_flask_code(project_type, detected_info)

    def _sample_fastapi_code(self, project_type: str, di: Dict) -> str:
        snippets: List[str] = [
            "from fastapi import FastAPI, Depends, HTTPException, status",
            "from pydantic import BaseModel",
            "from typing import Optional, List",
            "",
            "app = FastAPI(title='My App')",
            "",
        ]

        if di.get("has_auth"):
            snippets += [
                "# --- Auth ---",
                "class LoginRequest(BaseModel):",
                "    email: str",
                "    password: str",
                "",
                "class TokenResponse(BaseModel):",
                "    access_token: str",
                "    token_type: str = 'bearer'",
                "",
                "@app.post('/auth/login', response_model=TokenResponse)",
                "async def login(body: LoginRequest):",
                "    user = await authenticate_user(body.email, body.password)",
                "    if not user:",
                "        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)",
                "    token = create_access_token(user.id)",
                "    return TokenResponse(access_token=token)",
                "",
                "@app.post('/auth/register', status_code=201)",
                "async def register(body: LoginRequest):",
                "    user = await create_user(body.email, body.password)",
                "    return {'id': user.id, 'email': user.email}",
                "",
            ]

        if project_type == "ecommerce":
            snippets += [
                "# --- Products ---",
                "class Product(BaseModel):",
                "    id: int",
                "    name: str",
                "    price: float",
                "    stock: int",
                "",
                "@app.get('/products', response_model=List[Product])",
                "async def list_products(skip: int = 0, limit: int = 20):",
                "    return await db.products.find_all(skip=skip, limit=limit)",
                "",
                "# --- Cart ---",
                "class CartItem(BaseModel):",
                "    product_id: int",
                "    quantity: int",
                "",
                "@app.post('/cart/items', status_code=201)",
                "async def add_to_cart(item: CartItem, user_id: int = Depends(get_current_user)):",
                "    return await cart_service.add_item(user_id, item.product_id, item.quantity)",
                "",
            ]
        elif project_type in ("chat", "social"):
            snippets += [
                "# --- Messages ---",
                "class MessageRequest(BaseModel):",
                "    room_id: str",
                "    content: str",
                "",
                "class MessageResponse(BaseModel):",
                "    id: str",
                "    sender_id: int",
                "    content: str",
                "    created_at: str",
                "",
                "@app.post('/messages', response_model=MessageResponse, status_code=201)",
                "async def send_message(body: MessageRequest, user_id: int = Depends(get_current_user)):",
                "    msg = await message_service.send(user_id, body.room_id, body.content)",
                "    await ws_manager.broadcast(body.room_id, msg)",
                "    return msg",
                "",
                "@app.get('/rooms/{room_id}/messages', response_model=List[MessageResponse])",
                "async def get_messages(room_id: str, limit: int = 50):",
                "    return await message_service.get_recent(room_id, limit)",
                "",
            ]
        elif project_type == "streaming":
            snippets += [
                "# --- Media ---",
                "from fastapi import UploadFile, File",
                "",
                "@app.post('/media/upload', status_code=201)",
                "async def upload_media(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):",
                "    url = await storage.upload(file)",
                "    record = await media_service.create(user_id, file.filename, url)",
                "    return {'id': record.id, 'url': url}",
                "",
                "@app.get('/media/{media_id}/stream')",
                "async def stream_media(media_id: int):",
                "    media = await media_service.get(media_id)",
                "    return {'stream_url': cdn.sign_url(media.s3_key)}",
                "",
            ]
        else:
            snippets += [
                "# --- Health & generic resource ---",
                "@app.get('/health')",
                "async def health_check():",
                "    return {'status': 'ok'}",
                "",
                "class Item(BaseModel):",
                "    name: str",
                "    description: Optional[str] = None",
                "",
                "@app.get('/items')",
                "async def list_items(skip: int = 0, limit: int = 20):",
                "    return await db.items.find_all(skip=skip, limit=limit)",
                "",
                "@app.post('/items', status_code=201)",
                "async def create_item(item: Item):",
                "    return await db.items.create(item.model_dump())",
                "",
            ]

        return "\n".join(snippets)

    def _sample_flask_code(self, project_type: str, di: Dict) -> str:
        snippets: List[str] = [
            "from flask import Flask, request, jsonify",
            "from dataclasses import dataclass",
            "",
            "app = Flask(__name__)",
            "",
        ]

        if di.get("has_auth"):
            snippets += [
                "# --- Auth ---",
                "@dataclass",
                "class LoginRequest:",
                "    email: str",
                "    password: str",
                "",
                "@app.post('/auth/login')",
                "def login():",
                "    data = request.get_json()",
                "    user = authenticate_user(data['email'], data['password'])",
                "    if not user:",
                "        return jsonify(error='Unauthorized'), 401",
                "    return jsonify(access_token=create_token(user.id))",
                "",
            ]

        if project_type == "ecommerce":
            snippets += [
                "@app.get('/products')",
                "def list_products():",
                "    page = int(request.args.get('page', 1))",
                "    products = Product.query.paginate(page=page, per_page=20)",
                "    return jsonify([p.to_dict() for p in products.items])",
                "",
                "@app.post('/cart/items')",
                "def add_to_cart():",
                "    data = request.get_json()",
                "    item = cart_service.add(data['product_id'], data['quantity'])",
                "    return jsonify(item.to_dict()), 201",
                "",
            ]
        else:
            snippets += [
                "@app.get('/health')",
                "def health():",
                "    return jsonify(status='ok')",
                "",
                "@app.get('/items')",
                "def list_items():",
                "    items = Item.query.limit(20).all()",
                "    return jsonify([i.to_dict() for i in items])",
                "",
            ]

        return "\n".join(snippets)

    def _generate_database_schema_sql(
        self, template_type: str, detected_info: Dict[str, Any]
    ) -> str:
        """Return actual SQL CREATE TABLE statements for the detected project type."""
        project_type = detected_info.get("project_type", "general")

        tables: List[str] = []

        # Always: users table
        tables.append(
            "CREATE TABLE IF NOT EXISTS users (\n"
            "    id          SERIAL PRIMARY KEY,\n"
            "    email       VARCHAR(255) NOT NULL UNIQUE,\n"
            "    password_hash VARCHAR(255) NOT NULL,\n"
            "    is_active   BOOLEAN NOT NULL DEFAULT TRUE,\n"
            "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n"
            "    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
            ");\n"
            "CREATE INDEX idx_users_email ON users (email);"
        )

        if detected_info.get("has_auth"):
            tables.append(
                "CREATE TABLE IF NOT EXISTS refresh_tokens (\n"
                "    id          SERIAL PRIMARY KEY,\n"
                "    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n"
                "    token       VARCHAR(512) NOT NULL UNIQUE,\n"
                "    expires_at  TIMESTAMPTZ NOT NULL,\n"
                "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                ");\n"
                "CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens (user_id);"
            )

        if project_type == "ecommerce":
            tables += [
                (
                    "CREATE TABLE IF NOT EXISTS products (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    name        VARCHAR(255) NOT NULL,\n"
                    "    description TEXT,\n"
                    "    price       NUMERIC(10,2) NOT NULL,\n"
                    "    stock       INTEGER NOT NULL DEFAULT 0,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS orders (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    user_id     INTEGER NOT NULL REFERENCES users(id),\n"
                    "    status      VARCHAR(50) NOT NULL DEFAULT 'pending',\n"
                    "    total       NUMERIC(10,2) NOT NULL,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");\n"
                    "CREATE INDEX idx_orders_user_id ON orders (user_id);"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS order_items (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,\n"
                    "    product_id  INTEGER NOT NULL REFERENCES products(id),\n"
                    "    quantity    INTEGER NOT NULL,\n"
                    "    unit_price  NUMERIC(10,2) NOT NULL\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS cart_items (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n"
                    "    product_id  INTEGER NOT NULL REFERENCES products(id),\n"
                    "    quantity    INTEGER NOT NULL DEFAULT 1,\n"
                    "    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n"
                    "    UNIQUE (user_id, product_id)\n"
                    ");"
                ),
            ]

        elif project_type in ("social", "chat"):
            tables += [
                (
                    "CREATE TABLE IF NOT EXISTS posts (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    user_id     INTEGER NOT NULL REFERENCES users(id),\n"
                    "    content     TEXT NOT NULL,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");\n"
                    "CREATE INDEX idx_posts_user_id ON posts (user_id);"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS messages (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    sender_id   INTEGER NOT NULL REFERENCES users(id),\n"
                    "    room_id     VARCHAR(255) NOT NULL,\n"
                    "    content     TEXT NOT NULL,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");\n"
                    "CREATE INDEX idx_messages_room_id ON messages (room_id);\n"
                    "CREATE INDEX idx_messages_sender_id ON messages (sender_id);"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS follows (\n"
                    "    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n"
                    "    followee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n"
                    "    PRIMARY KEY (follower_id, followee_id)\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS likes (\n"
                    "    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n"
                    "    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n"
                    "    PRIMARY KEY (user_id, post_id)\n"
                    ");"
                ),
            ]

        elif project_type == "streaming":
            tables += [
                (
                    "CREATE TABLE IF NOT EXISTS media_files (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    user_id     INTEGER NOT NULL REFERENCES users(id),\n"
                    "    title       VARCHAR(255) NOT NULL,\n"
                    "    s3_key      VARCHAR(512) NOT NULL,\n"
                    "    duration_s  INTEGER,\n"
                    "    status      VARCHAR(50) NOT NULL DEFAULT 'processing',\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS playlists (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    user_id     INTEGER NOT NULL REFERENCES users(id),\n"
                    "    name        VARCHAR(255) NOT NULL,\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS playlist_items (\n"
                    "    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,\n"
                    "    media_id    INTEGER NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,\n"
                    "    position    INTEGER NOT NULL DEFAULT 0,\n"
                    "    PRIMARY KEY (playlist_id, media_id)\n"
                    ");"
                ),
            ]

        elif project_type in ("saas", "general", "api", "dashboard"):
            tables += [
                (
                    "CREATE TABLE IF NOT EXISTS workspaces (\n"
                    "    id          SERIAL PRIMARY KEY,\n"
                    "    name        VARCHAR(255) NOT NULL,\n"
                    "    owner_id    INTEGER NOT NULL REFERENCES users(id),\n"
                    "    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS workspace_members (\n"
                    "    workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,\n"
                    "    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n"
                    "    role         VARCHAR(50) NOT NULL DEFAULT 'member',\n"
                    "    joined_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n"
                    "    PRIMARY KEY (workspace_id, user_id)\n"
                    ");"
                ),
                (
                    "CREATE TABLE IF NOT EXISTS subscriptions (\n"
                    "    id              SERIAL PRIMARY KEY,\n"
                    "    workspace_id    INTEGER NOT NULL REFERENCES workspaces(id),\n"
                    "    plan            VARCHAR(50) NOT NULL DEFAULT 'free',\n"
                    "    stripe_sub_id   VARCHAR(255),\n"
                    "    current_period_end TIMESTAMPTZ,\n"
                    "    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()\n"
                    ");"
                ),
            ]

        return "\n\n".join(tables) + "\n"

    def _generate_dockerfile(self, template_type: str) -> str:
        """Return a Dockerfile appropriate for the implementation tier."""
        if template_type == "simple":
            return (
                "FROM python:3.11-slim\n"
                "\n"
                "WORKDIR /app\n"
                "\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "\n"
                "COPY . .\n"
                "\n"
                "EXPOSE 8000\n"
                "\n"
                'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
            )

        if template_type == "optimized":
            return (
                "# ---- builder ----\n"
                "FROM python:3.11-slim AS builder\n"
                "WORKDIR /build\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir --prefix=/install -r requirements.txt\n"
                "\n"
                "# ---- production ----\n"
                "FROM python:3.11-slim\n"
                "WORKDIR /app\n"
                "\n"
                "# Non-root user for security\n"
                "RUN addgroup --system app && adduser --system --ingroup app app\n"
                "\n"
                "COPY --from=builder /install /usr/local\n"
                "COPY . .\n"
                "\n"
                "RUN chown -R app:app /app\n"
                "USER app\n"
                "\n"
                "EXPOSE 8000\n"
                "\n"
                'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]\n'
            )

        # scalable
        return (
            "# ---- builder ----\n"
            "FROM python:3.11-slim AS builder\n"
            "WORKDIR /build\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir --prefix=/install -r requirements.txt\n"
            "\n"
            "# ---- production ----\n"
            "FROM python:3.11-slim\n"
            "\n"
            "LABEL maintainer='team@example.com'\n"
            "LABEL version='1.0.0'\n"
            "\n"
            "WORKDIR /app\n"
            "\n"
            "# Non-root user\n"
            "RUN addgroup --system app && adduser --system --ingroup app app\n"
            "\n"
            "COPY --from=builder /install /usr/local\n"
            "COPY . .\n"
            "\n"
            "RUN chown -R app:app /app\n"
            "USER app\n"
            "\n"
            "EXPOSE 8000\n"
            "\n"
            "HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\\n"
            '    CMD python -c "import httpx; httpx.get(\'http://localhost:8000/health\').raise_for_status()"\n'
            "\n"
            'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]\n'
        )

    # ------------------------------------------------------------------
    # Existing generation methods (unchanged signatures)
    # ------------------------------------------------------------------

    def _get_template_type(self, title: str) -> str:
        """Determine implementation type from solution title"""
        title_lower = title.lower()
        if "simple" in title_lower or "mvp" in title_lower or "minimal" in title_lower or "prototype" in title_lower:
            return "simple"
        elif "scalable" in title_lower or "enterprise" in title_lower or "distributed" in title_lower:
            return "scalable"
        else:
            return "optimized"

    def _generate_project_structure(
        self, template_type: str, context: Dict = None
    ) -> Dict[str, List[str]]:
        """Generate folder and file structure"""

        base_structure = {
            "root": [
                "README.md",
                "requirements.txt",
                ".gitignore",
                ".env.example",
                "docker-compose.yml",
                "Dockerfile",
            ],
            "app": [
                "__init__.py",
                "main.py",
                "config.py",
                "models.py",
                "routes.py",
                "services.py",
                "utils.py",
            ],
            "tests": [
                "__init__.py",
                "test_models.py",
                "test_routes.py",
                "test_services.py",
            ],
            "migrations": ["alembic.ini", "versions/"],
            "static": ["css/", "js/", "images/"],
            "templates": ["base.html", "index.html", "404.html", "500.html"],
        }

        if template_type == "simple":
            return {
                "root": base_structure["root"],
                "app": base_structure["app"][:5],
                "static": ["css/", "js/"],
                "templates": ["base.html", "index.html"],
            }
        elif template_type == "scalable":
            base_structure.update(
                {
                    "services": [
                        "__init__.py",
                        "auth_service.py",
                        "data_service.py",
                        "cache_service.py",
                        "queue_service.py",
                    ],
                    "middleware": [
                        "__init__.py",
                        "auth.py",
                        "logging.py",
                        "error_handler.py",
                        "rate_limit.py",
                    ],
                    "scripts": ["setup.sh", "deploy.sh", "backup.sh", "migrate.sh"],
                    "docker": [
                        "Dockerfile.prod",
                        "docker-compose.prod.yml",
                        "nginx.conf",
                    ],
                }
            )
            return base_structure
        else:
            return base_structure

    def _generate_setup_instructions(self, template_type: str) -> List[str]:
        """Generate step-by-step setup instructions"""

        base_steps = [
            "1. Create project directory: mkdir my_project && cd my_project",
            "2. Initialize git repository: git init",
            "3. Create Python virtual environment: python -m venv venv",
            "4. Activate virtual environment (Windows): .\\venv\\Scripts\\activate",
            "5. Activate virtual environment (Mac/Linux): source venv/bin/activate",
            "6. Install dependencies: pip install -r requirements.txt",
            "7. Copy environment file: cp .env.example .env",
            "8. Configure .env with your settings",
            "9. Initialize database: python app/models.py",
            "10. Run development server: python app/main.py",
        ]

        if template_type == "simple":
            return base_steps[:10]
        elif template_type == "scalable":
            return base_steps + [
                "11. Setup Redis: docker run -d -p 6379:6379 redis:latest",
                "12. Setup PostgreSQL: docker run -d -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:latest",
                "13. Run database migrations: alembic upgrade head",
                "14. Start message queue: docker run -d -p 5672:5672 rabbitmq:latest",
                "15. Initialize services: python scripts/setup.sh",
            ]
        else:
            return base_steps + [
                "11. Setup Redis: pip install redis",
                "12. Setup Docker containers: docker-compose up -d",
                "13. Run migrations: python migrations.py",
                "14. Create admin user: python app/create_admin.py",
            ]

    def _generate_core_files(
        self, template_type: str, solution: Dict
    ) -> Dict[str, str]:
        """Generate core file templates and their purposes"""

        tech_stack = solution.get("tech_stack", "")
        if isinstance(tech_stack, dict):
            backend = tech_stack.get("backend", "flask")
            database = tech_stack.get("database", "sqlite")
        else:
            tech_str = str(tech_stack).lower()
            backend = "fastapi" if "fastapi" in tech_str else "flask"
            database = "postgresql" if "postgresql" in tech_str else "sqlite"

        core_files = {
            "main.py": f"Entry point - Initialize {backend} app and start server",
            "config.py": "Configuration management - Database, cache, API keys",
            "models.py": f"Data models - Define {database} schema and relationships",
            "routes.py": "API endpoints - Define all HTTP routes and handlers",
            "services.py": "Business logic - Core application logic",
            "utils.py": "Helper functions - Common utilities and decorators",
        }

        if template_type == "scalable":
            core_files.update(
                {
                    "auth_service.py": "Authentication and authorization service",
                    "cache_service.py": "Redis cache management",
                    "queue_service.py": "Message queue service (RabbitMQ/Kafka)",
                    "middleware/auth.py": "JWT/OAuth authentication middleware",
                    "middleware/logging.py": "Request/response logging",
                    "middleware/rate_limit.py": "Rate limiting middleware",
                }
            )
        elif template_type == "optimized":
            core_files.update(
                {
                    "cache.py": "Redis caching layer",
                    "middleware.py": "Custom middleware (logging, error handling)",
                }
            )

        return core_files

    def _generate_configuration(
        self, template_type: str, solution: Dict
    ) -> Dict[str, str]:
        """Generate configuration requirements"""

        base_config = {
            "DATABASE_URL": "Database connection string",
            "SECRET_KEY": "Flask/Django secret key for session management",
            "DEBUG": "Debug mode (True for dev, False for production)",
            "ALLOWED_HOSTS": "List of allowed hostnames",
            "API_PORT": "API server port (default: 5000 or 8000)",
        }

        if template_type == "optimized":
            base_config.update(
                {
                    "REDIS_URL": "Redis connection string for caching",
                    "CACHE_TTL": "Cache time-to-live in seconds",
                    "LOG_LEVEL": "Logging level (DEBUG, INFO, WARNING, ERROR)",
                }
            )
        elif template_type == "scalable":
            base_config.update(
                {
                    "REDIS_CLUSTER": "Redis cluster endpoints",
                    "KAFKA_BROKERS": "Kafka broker addresses",
                    "ELASTICSEARCH_URL": "Elasticsearch connection for logging",
                    "PROMETHEUS_PORT": "Prometheus metrics port",
                    "JAEGER_AGENT_HOST": "Jaeger tracing host",
                    "AUTH_PROVIDER": "OAuth2 provider URL",
                    "JWT_SECRET": "JWT signing secret",
                    "RATE_LIMIT": "Requests per minute limits",
                }
            )

        return base_config

    def _generate_database_setup(
        self, template_type: str, solution: Dict
    ) -> Dict[str, Any]:
        """Generate database schema information"""

        database = solution.get("tech_stack", {})
        if isinstance(database, dict):
            database = database.get("database", "sqlite")
        else:
            database = "sqlite"

        setup = {
            "database_type": database,
            "initial_tables": [
                "users (id, username, email, password_hash, created_at)",
                "sessions (id, user_id, token, expires_at)",
                "logs (id, level, message, created_at)",
            ],
            "indexes": [
                "users.email - For fast user lookups",
                "sessions.user_id - For user session queries",
            ],
        }

        if template_type == "optimized":
            setup["initial_tables"].extend(
                [
                    "cache_keys (key, value, ttl)",
                    "api_calls (id, endpoint, user_id, response_time, timestamp)",
                ]
            )
        elif template_type == "scalable":
            setup["initial_tables"].extend(
                [
                    "audit_logs (id, user_id, action, resource, timestamp)",
                    "api_keys (id, user_id, key, permissions, created_at)",
                    "rate_limits (id, user_id, endpoint, count, window_start)",
                    "feature_flags (name, enabled, rollout_percentage)",
                    "shards (shard_id, database_url, status)",
                ]
            )
            setup["replication"] = "Primary-Replica replication setup recommended"
            setup["sharding"] = "Prepare sharding strategy by user_id or time"

        return setup

    def _generate_deployment_steps(
        self, template_type: str, solution: Dict
    ) -> List[str]:
        """Generate deployment instructions"""

        if template_type == "simple":
            return [
                "1. Build Docker image: docker build -t myapp:latest .",
                "2. Run container: docker run -p 8000:8000 myapp:latest",
                "3. Or deploy to Heroku: git push heroku main",
                "4. Verify deployment: curl http://localhost:8000/health",
            ]
        elif template_type == "optimized":
            return [
                "1. Build Docker image: docker build -t myapp:latest .",
                "2. Start docker-compose stack: docker-compose up -d",
                "3. Verify services running: docker-compose ps",
                "4. Run migrations: docker-compose exec web alembic upgrade head",
                "5. Deploy to cloud (AWS/GCP): Use container registry and load balancer",
                "6. Setup SSL certificate: Let's Encrypt or AWS Certificate Manager",
                "7. Configure auto-scaling rules: Based on CPU/Memory metrics",
                "8. Enable monitoring: Setup CloudWatch/Datadog",
            ]
        else:  # scalable
            return [
                "1. Setup Kubernetes cluster: kubectl create cluster",
                "2. Build Docker images for each service",
                "3. Push to container registry: docker push myregistry/service:latest",
                "4. Deploy Kubernetes manifests: kubectl apply -f k8s/",
                "5. Setup Ingress controller for routing",
                "6. Configure Service Mesh (Istio/Linkerd)",
                "7. Setup persistent volumes for databases",
                "8. Configure auto-scaling policies: HPA for pods",
                "9. Setup monitoring stack: Prometheus + Grafana",
                "10. Configure centralized logging: ELK Stack",
                "11. Setup CI/CD pipeline: GitHub Actions or GitLab CI",
                "12. Configure disaster recovery: Cross-region replication",
            ]

    def _generate_dev_checklist(self, template_type: str) -> List[str]:
        """Generate development checklist"""

        checklist = [
            "☐ Setup development environment locally",
            "☐ Create initial project structure",
            "☐ Setup database with sample data",
            "☐ Implement core API endpoints",
            "☐ Add request/response validation",
            "☐ Implement error handling and logging",
            "☐ Write unit tests (aim for 80%+ coverage)",
            "☐ Setup API documentation (Swagger/OpenAPI)",
            "☐ Configure environment variables",
            "☐ Setup version control (.gitignore, commits)",
        ]

        if template_type == "optimized":
            checklist.extend(
                [
                    "☐ Implement Redis caching layer",
                    "☐ Add input sanitization and validation",
                    "☐ Setup HTTPS/TLS certificates",
                    "☐ Implement rate limiting",
                    "☐ Add structured logging",
                    "☐ Performance testing and optimization",
                    "☐ Security audit and fixes",
                ]
            )
        elif template_type == "scalable":
            checklist.extend(
                [
                    "☐ Design microservices architecture",
                    "☐ Setup API Gateway",
                    "☐ Implement service-to-service authentication",
                    "☐ Setup distributed tracing",
                    "☐ Implement circuit breakers",
                    "☐ Setup multi-region deployment",
                    "☐ Implement feature flags",
                    "☐ Security penetration testing",
                    "☐ Load testing and capacity planning",
                    "☐ Disaster recovery drills",
                ]
            )

        return checklist

    def _estimate_effort(self, template_type: str) -> Dict[str, Any]:
        """Estimate development effort in hours"""

        base_estimates = {
            "Setup and Configuration": 8,
            "Core Backend Development": 40,
            "Database Design and Implementation": 16,
            "API Development": 32,
            "Testing": 24,
            "Frontend Integration": 20,
            "Documentation": 8,
        }

        if template_type == "simple":
            factors: Dict[str, Any] = {k: int(v * 0.5) for k, v in base_estimates.items()}
        elif template_type == "optimized":
            factors = base_estimates.copy()
            factors.update(
                {
                    "Caching Layer": 16,
                    "Performance Optimization": 20,
                    "Security Hardening": 16,
                }
            )
        else:  # scalable
            factors = base_estimates.copy()
            factors.update(
                {
                    "Microservices Design": 40,
                    "Service Communication": 32,
                    "Distributed Tracing": 16,
                    "Load Balancing": 16,
                    "Security & Authentication": 24,
                    "Monitoring & Observability": 24,
                    "Deployment Infrastructure": 40,
                }
            )

        total = sum(v for v in factors.values() if isinstance(v, (int, float)))
        factors["TOTAL_HOURS"] = total
        factors["TOTAL_WEEKS"] = round(total / 40, 1)

        return factors

    def _generate_success_criteria(self, solution: Dict) -> List[str]:
        """Generate success criteria for the implementation"""

        return [
            "✓ Application runs without errors on local machine",
            "✓ All API endpoints respond with correct status codes",
            "✓ Database operations execute without data loss",
            "✓ User authentication/authorization working correctly",
            "✓ Error handling provides meaningful error messages",
            "✓ Application logs all important events",
            "✓ Code passes all unit and integration tests",
            "✓ API documentation is complete and accurate",
            "✓ Application responds within acceptable latency (< 200ms for 95th percentile)",
            "✓ No obvious security vulnerabilities detected",
            "✓ Code follows style guide and is maintainable",
            "✓ Docker image builds successfully",
            "✓ Deployment process is documented and repeatable",
        ]

    def _generate_next_steps(self, template_type: str) -> List[str]:
        """Generate recommended next steps after implementation"""

        base_steps = [
            "1. Deploy to staging environment",
            "2. Conduct user acceptance testing (UAT)",
            "3. Performance load testing",
            "4. Security audit and penetration testing",
            "5. Set up monitoring and alerting",
        ]

        if template_type == "simple":
            return base_steps + [
                "6. Deploy to production (single server)",
                "7. Monitor performance and user feedback",
                "8. Plan scaling strategy for future growth",
            ]
        elif template_type == "optimized":
            return base_steps + [
                "6. Setup continuous deployment pipeline",
                "7. Configure auto-scaling policies",
                "8. Plan for database optimization",
                "9. Evaluate migration to microservices",
            ]
        else:  # scalable
            return base_steps + [
                "6. Multi-region deployment",
                "7. Setup disaster recovery procedures",
                "8. Implement feature flagging and canary deployments",
                "9. Continuous optimization based on metrics",
                "10. Plan for team expansion and handoff",
            ]

    # ------------------------------------------------------------------
    # Display formatting
    # ------------------------------------------------------------------

    def format_implementation_for_display(self, plan: Dict[str, Any]) -> str:
        """Format implementation plan for terminal display — includes all new sections."""

        output: List[str] = []
        output.append("=" * 70)
        output.append("IMPLEMENTATION DETAILS")
        output.append("=" * 70)
        output.append("")

        # Summary
        output.append(f"Solution: {plan['solution_title']}")
        output.append(f"Type: {plan['implementation_type'].title()}")
        output.append(f"Estimated Effort: {plan['estimated_hours']['TOTAL_WEEKS']} weeks")
        output.append("")

        # Project Structure
        output.append("PROJECT STRUCTURE")
        output.append("-" * 70)
        for folder, items in plan["project_structure"].items():
            output.append(f"{folder}/")
            for item in items:
                output.append(f"  ├── {item}")
        output.append("")

        # Setup Instructions
        output.append("SETUP INSTRUCTIONS")
        output.append("-" * 70)
        for step in plan["setup_instructions"][:5]:
            output.append(f"  {step}")
        if len(plan["setup_instructions"]) > 5:
            output.append(f"  ... and {len(plan['setup_instructions']) - 5} more steps")
        output.append("")

        # Requirements.txt
        output.append("REQUIREMENTS.TXT")
        output.append("-" * 70)
        output.append("```")
        output.append(plan.get("requirements_txt", "").rstrip())
        output.append("```")
        output.append("")

        # .env Template
        output.append("ENV TEMPLATE (.env)")
        output.append("-" * 70)
        output.append("```")
        output.append(plan.get("env_template", "").rstrip())
        output.append("```")
        output.append("")

        # Sample API Code
        output.append("SAMPLE API CODE")
        output.append("-" * 70)
        output.append("```python")
        output.append(plan.get("sample_api_code", "").rstrip())
        output.append("```")
        output.append("")

        # Database Schema
        output.append("DATABASE SCHEMA")
        output.append("-" * 70)
        output.append("```sql")
        output.append(plan.get("database_schema_sql", "").rstrip())
        output.append("```")
        output.append("")

        # Dockerfile
        output.append("DOCKERFILE")
        output.append("-" * 70)
        output.append("```dockerfile")
        output.append(plan.get("dockerfile", "").rstrip())
        output.append("```")
        output.append("")

        # Development Timeline
        output.append("DEVELOPMENT TIMELINE")
        output.append("-" * 70)
        timeline_items = [
            (k, v)
            for k, v in plan["estimated_hours"].items()
            if k not in ("TOTAL_HOURS", "TOTAL_WEEKS")
        ]
        for task, hours in timeline_items:
            output.append(f"  {task}: {hours} hours")
        output.append("")

        # Success Criteria
        output.append("SUCCESS CRITERIA")
        output.append("-" * 70)
        for criterion in plan["success_criteria"][:5]:
            output.append(f"  {criterion}")
        if len(plan["success_criteria"]) > 5:
            output.append(f"  ... and {len(plan['success_criteria']) - 5} more criteria")
        output.append("")

        output.append("For detailed implementation guide, check project documentation.")
        output.append("")

        return "\n".join(output)
