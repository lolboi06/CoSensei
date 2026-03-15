"""
Generates three distinct solution strategies based on task context.
Ensures each solution is structurally different and has unique characteristics.
"""
from __future__ import annotations

from typing import Dict, List


class SolutionStrategyGenerator:
    """Generates three distinct solution strategies for a task."""

    def generate_solutions(
        self,
        task_input: str,
        language: str,
        framework: str,
        database: str,
        context: Dict[str, str] | None = None,
    ) -> List[Dict[str, str]]:
        """Generate three distinct solutions for the task."""
        
        context = context or {}
        site_type = context.get("site_type", "general")
        
        solutions = [
            self._simple_solution(task_input, language, framework, database, site_type),
            self._optimized_solution(task_input, language, framework, database, site_type),
            self._scalable_solution(task_input, language, framework, database, site_type),
        ]
        
        return solutions

    def _simple_solution(
        self,
        task: str,
        language: str,
        framework: str,
        database: str,
        site_type: str,
    ) -> Dict[str, str]:
        """Generate a minimal, quick-start solution."""
        return {
            "id": "1",
            "strategy": "simple",
            "title": "Simple Implementation",
            "description": "A minimal, quick-start solution with basic functionality.",
            "characteristics": [
                "Minimal code and dependencies",
                "Quick to implement (1-2 hours)",
                "Single-file or flat structure",
                "No advanced patterns",
                "Best for: prototypes, learning, small projects",
            ],
            "architecture": self._simple_architecture(language, framework, database, site_type),
            "effort": "Low (1-2 hours)",
            "scalability": "Low",
            "maintenance_burden": "Low",
        }

    def _optimized_solution(
        self,
        task: str,
        language: str,
        framework: str,
        database: str,
        site_type: str,
    ) -> Dict[str, str]:
        """Generate a performance-focused, production-ready solution."""
        return {
            "id": "2",
            "strategy": "optimized",
            "title": "Optimized Implementation",
            "description": "A production-ready solution optimized for performance and reliability.",
            "characteristics": [
                "Clean, modular architecture",
                "Performance optimization",
                "Proper error handling",
                "Logging and monitoring",
                "Best for: production systems, performance-critical apps",
            ],
            "architecture": self._optimized_architecture(language, framework, database, site_type),
            "effort": "Medium (4-8 hours)",
            "scalability": "Medium",
            "maintenance_burden": "Medium",
        }

    def _scalable_solution(
        self,
        task: str,
        language: str,
        framework: str,
        database: str,
        site_type: str,
    ) -> Dict[str, str]:
        """Generate an enterprise-grade, scalable solution."""
        return {
            "id": "3",
            "strategy": "scalable",
            "title": "Scalable Architecture",
            "description": "An enterprise-grade architecture designed for growth and high load.",
            "characteristics": [
                "Microservices-ready structure",
                "Advanced design patterns",
                "Distributed caching",
                "Async/concurrent processing",
                "API-first design",
                "Best for: large teams, high-traffic systems, enterprises",
            ],
            "architecture": self._scalable_architecture(language, framework, database, site_type),
            "effort": "High (16-40 hours)",
            "scalability": "High",
            "maintenance_burden": "High",
        }

    def _simple_architecture(self, language: str, framework: str, database: str, site_type: str) -> str:
        """Simple project structure."""
        if language == "python":
            if framework == "flask":
                return """
app.py              # Single entry point
templates/          # HTML templates
static/            # CSS, JS
requirements.txt   # Dependencies
"""
            elif framework == "django":
                return """
manage.py
project/
  settings.py
  urls.py
app/
  models.py
  views.py
  templates/
"""
        elif language == "javascript":
            return """
index.js            # Entry point
components/         # Simple components
styles.css         # Basic styling
package.json
"""
        return "Single main file with inline logic"

    def _optimized_architecture(self, language: str, framework: str, database: str, site_type: str) -> str:
        """Production-ready project structure."""
        if language == "python":
            if framework == "fastapi":
                return """
src/
  main.py                 # Application entry
  config.py              # Configuration
  models/                # Data models
  services/              # Business logic
  api/                   # Route handlers
  middleware/            # Custom middleware
  utils/                 # Utilities
  database.py            # DB connection
tests/                   # Unit tests
requirements.txt        # Dependencies
.env                    # Environment config
"""
            elif framework == "django":
                return """
config/
  settings/
    base.py
    production.py
  urls.py
apps/
  users/
    models.py
    views.py
    serializers.py
  core/
    models.py
    services.py
templates/
static/
tests/
requirements.txt
"""
        elif language == "javascript":
            if framework == "react":
                return """
src/
  components/
    Common/
    Features/
  pages/
  services/
  hooks/
  utils/
  styles/
public/
tests/
package.json
"""
        return "Organized module structure with separation of concerns"

    def _scalable_architecture(self, language: str, framework: str, database: str, site_type: str) -> str:
        """Enterprise-grade project structure."""
        if language == "python":
            return """
services/
  api/
    __init__.py
    main.py
    routes/
    middleware/
    auth/
  workers/              # Background jobs
  scheduler/            # Task scheduling
  cache/               # Caching layer
  logging/             # Centralized logging
shared/
  models/
  schemas/
  utils/
  exceptions/
tests/
  unit/
  integration/
  e2e/
deployment/
  docker/
  kubernetes/
infrastructure/
  monitoring/
  alerting/
requirements.txt
pyproject.toml
"""
        elif language == "javascript":
            return """
packages/
  api/
    src/
      graphql/
      rest/
      middleware/
      services/
  web/                 # Frontend
  shared/             # Shared utilities
  monitoring/
  logging/
  cache/
tests/
  unit/
  integration/
  e2e/
infrastructure/
  docker/
  helm/
monorepo.json
"""
        return "Microservices-ready architecture with multiple layers"

    def format_for_display(self, solutions: List[Dict[str, str]]) -> str:
        """Format solutions for user display."""
        lines = ["Here are three possible solutions:\n"]
        
        for sol in solutions:
            lines.append(f"{sol['id']}. {sol['title']}")
            lines.append(f"   {sol['description']}")
            lines.append(f"   Effort: {sol['effort']} | Scalability: {sol['scalability']}")
            lines.append("")
        
        lines.append("Recommended solution: 2 (Optimized Implementation)")
        lines.append("\nWhich solution would you like? (1, 2, or 3)")
        
        return "\n".join(lines)

    def get_solution_details(self, solution_id: str, solutions: List[Dict[str, str]]) -> Dict[str, str] | None:
        """Get detailed information about a specific solution."""
        for sol in solutions:
            if sol["id"] == solution_id or sol["strategy"].lower() == solution_id.lower():
                return sol
        return None
