"""
CoSensei Verifier AI (AI #3)
Performs comprehensive risk analysis on generated architectures and code
Determines autonomy control level based on detected risks
"""

import sys
import os
from typing import Dict, List, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class VerifierAI:
    """AI #3: Risk Analysis and Architecture Verification"""
    
    def __init__(self):
        self.risk_factors = {
            "security": [],
            "architecture": [],
            "performance": [],
            "scalability": [],
            "deployment": []
        }
        self.risk_score = 0.0
        self.risk_level = "MEDIUM"
        
    def analyze_risk(self, solution: Dict[str, Any], task_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive risk analysis of generated solution architecture.
        Returns structured risk report with score, level, and recommendations.
        """
        
        # Extract solution text
        architecture_text = f"{solution.get('architecture', '')} {solution.get('description', '')}"
        tech_stack = solution.get('tech_stack', {})
        
        # Analyze different risk categories
        self._analyze_security(architecture_text, tech_stack)
        self._analyze_architecture(architecture_text, tech_stack)
        self._analyze_performance(architecture_text, tech_stack)
        self._analyze_scalability(architecture_text, tech_stack)
        self._analyze_deployment(architecture_text, tech_stack)
        
        # Calculate risk score
        self._calculate_risk_score()
        
        # Determine risk level
        self._determine_risk_level()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Build risk report
        risk_report = {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "security_issues": self.risk_factors["security"],
            "architecture_issues": self.risk_factors["architecture"],
            "performance_issues": self.risk_factors["performance"],
            "scalability_issues": self.risk_factors["scalability"],
            "deployment_issues": self.risk_factors["deployment"],
            "all_issues": self._flatten_issues(),
            "explanation": self._generate_explanation(),
            "recommendations": recommendations,
            "autonomy_mode": self.determine_autonomy_mode(),
            "requires_human_approval": self.risk_score >= 0.7
        }
        
        # Reset for next analysis
        self.risk_factors = {
            "security": [],
            "architecture": [],
            "performance": [],
            "scalability": [],
            "deployment": []
        }
        
        return risk_report
    
    def _analyze_security(self, architecture_text: str, tech_stack: Dict) -> None:
        """Analyze security-related risks"""
        
        text_lower = architecture_text.lower()
        
        # Check for hardcoded credentials
        if any(term in text_lower for term in ["hardcoded", "password", "secret", "api_key", "token"]):
            if "hardcoded" in text_lower or ("password" in text_lower and "plain" in text_lower):
                self.risk_factors["security"].append("Hardcoded credentials detected")
        
        # Check for missing authentication
        if not any(term in text_lower for term in ["auth", "oauth", "jwt", "authentication", "login"]):
            self.risk_factors["security"].append("No authentication mechanism specified")
        
        # Check for missing input validation
        if not any(term in text_lower for term in ["validation", "sanitize", "input check", "verify input"]):
            self.risk_factors["security"].append("Missing input validation layer")
        
        # Check for insecure API design
        if "rest" in text_lower or "api" in text_lower:
            if not any(term in text_lower for term in ["https", "encryption", "tls", "ssl"]):
                self.risk_factors["security"].append("API lacks encryption (no HTTPS/TLS)")
        
        # Check for missing rate limiting
        if not any(term in text_lower for term in ["rate limit", "throttle", "ratelimit"]):
            self.risk_factors["security"].append("No rate limiting implemented")
        
        # Check for missing CORS security
        if "web" in text_lower or "frontend" in text_lower:
            if not any(term in text_lower for term in ["cors", "cross-origin"]):
                self.risk_factors["security"].append("CORS policy not specified")
    
    def _analyze_architecture(self, architecture_text: str, tech_stack: Dict) -> None:
        """Analyze architecture-related risks"""
        
        text_lower = architecture_text.lower()
        
        # Check for single point of failure
        if not any(term in text_lower for term in ["redundant", "failover", "replication", "backup"]):
            self.risk_factors["architecture"].append("Potential single point of failure")
        
        # Check for load balancing
        if not any(term in text_lower for term in ["load balancer", "nginx", "route", "distribute"]):
            self.risk_factors["architecture"].append("No load balancing mentioned")
        
        # Check for caching layer
        if not any(term in text_lower for term in ["cache", "redis", "memcached"]):
            self.risk_factors["architecture"].append("Missing caching layer")
        
        # Check for proper service separation
        count_services = sum(1 for term in ["microservice", "service", "api", "worker"] if term in text_lower)
        if count_services < 2:
            self.risk_factors["architecture"].append("Limited service separation (consider microservices)")
        
        # Check for queue/messaging system
        if not any(term in text_lower for term in ["queue", "kafka", "rabbitmq", "message"]):
            self.risk_factors["architecture"].append("No message queue for async processing")
        
        # Check for database scaling
        if "database" in text_lower or "postgresql" in text_lower or "mysql" in text_lower:
            if not any(term in text_lower for term in ["shard", "replica", "cluster", "partition"]):
                self.risk_factors["architecture"].append("Database lacks scaling strategy")
    
    def _analyze_performance(self, architecture_text: str, tech_stack: Dict) -> None:
        """Analyze performance-related risks"""
        
        text_lower = architecture_text.lower()
        
        # Check for async architecture
        if not any(term in text_lower for term in ["async", "asynchronous", "non-blocking", "event-driven"]):
            self.risk_factors["performance"].append("No async/non-blocking architecture mentioned")
        
        # Check for database query optimization
        if not any(term in text_lower for term in ["index", "optimize", "query", "efficient"]):
            self.risk_factors["performance"].append("Database query optimization not specified")
        
        # Check for connection pooling
        if not any(term in text_lower for term in ["connection pool", "pool", "pooling"]):
            self.risk_factors["performance"].append("No connection pooling mentioned")
        
        # Check for CDN/static content delivery
        if "frontend" in text_lower or "web" in text_lower:
            if not any(term in text_lower for term in ["cdn", "static", "cloudfront", "edge"]):
                self.risk_factors["performance"].append("No CDN for static content delivery")
    
    def _analyze_scalability(self, architecture_text: str, tech_stack: Dict) -> None:
        """Analyze scalability-related risks"""
        
        text_lower = architecture_text.lower()
        
        # Check for horizontal scaling
        if not any(term in text_lower for term in ["horizontal", "scale out", "scalable", "multiple instances"]):
            self.risk_factors["scalability"].append("Limited horizontal scaling capability")
        
        # Check for containerization
        if not any(term in text_lower for term in ["docker", "container", "kubernetes", "k8s"]):
            self.risk_factors["scalability"].append("No containerization mentioned")
        
        # Check for stateless design
        if not any(term in text_lower for term in ["stateless", "session", "distributed"]):
            self.risk_factors["scalability"].append("Architecture may not be stateless")
        
        # Check for monolithic vs distributed
        if text_lower.count("monolithic") > text_lower.count("microservice"):
            self.risk_factors["scalability"].append("Monolithic architecture limits scaling")
    
    def _analyze_deployment(self, architecture_text: str, tech_stack: Dict) -> None:
        """Analyze deployment-related risks"""
        
        text_lower = architecture_text.lower()
        
        # Check for monitoring
        if not any(term in text_lower for term in ["monitor", "prometheus", "datadog", "newrelic"]):
            self.risk_factors["deployment"].append("No monitoring system specified")
        
        # Check for logging
        if not any(term in text_lower for term in ["log", "logging", "elk", "splunk"]):
            self.risk_factors["deployment"].append("No centralized logging")
        
        # Check for health checks
        if not any(term in text_lower for term in ["health", "healthcheck", "readiness", "liveness"]):
            self.risk_factors["deployment"].append("No health checks defined")
        
        # Check for CI/CD
        if not any(term in text_lower for term in ["ci/cd", "pipeline", "deploy", "automation"]):
            self.risk_factors["deployment"].append("No CI/CD pipeline mentioned")
        
        # Check for disaster recovery
        if not any(term in text_lower for term in ["backup", "recovery", "restore", "disaster"]):
            self.risk_factors["deployment"].append("No disaster recovery plan")
    
    def _calculate_risk_score(self) -> None:
        """Calculate overall risk score 0.0-1.0"""
        
        total_issues = sum(len(issues) for issues in self.risk_factors.values())
        
        # Weight different categories
        weights = {
            "security": 1.5,      # Security issues are critical
            "architecture": 1.2,   # Architecture issues are important
            "deployment": 1.0,     # Deployment issues are moderate
            "scalability": 0.9,    # Scalability can be addressed later
            "performance": 0.8     # Performance can be optimized later
        }
        
        weighted_score = 0.0
        for category, issues in self.risk_factors.items():
            weighted_score += len(issues) * weights.get(category, 1.0)
        
        # Normalize to 0-1 scale (max 20 weighted issues = score of 1.0)
        max_possible_score = 20.0
        self.risk_score = min(weighted_score / max_possible_score, 1.0)
    
    def _determine_risk_level(self) -> None:
        """Determine risk level based on score"""
        
        if self.risk_score < 0.3:
            self.risk_level = "LOW"
        elif self.risk_score < 0.7:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "HIGH"
    
    def _flatten_issues(self) -> List[str]:
        """Flatten all issues into single list"""
        
        all_issues = []
        for category, issues in self.risk_factors.items():
            all_issues.extend(issues)
        return all_issues
    
    def _generate_explanation(self) -> str:
        """Generate human-readable explanation of risks"""
        
        if self.risk_level == "LOW":
            return "The generated architecture follows best practices with minimal risk factors."
        elif self.risk_level == "MEDIUM":
            return "The architecture has moderate risk factors that should be addressed before production deployment."
        else:  # HIGH
            return "The architecture contains significant risk factors that make it unsuitable for production without major improvements."
    
    def _generate_recommendations(self) -> List[str]:
        """Generate specific recommendations"""
        
        recommendations = []
        
        # Security recommendations
        if self.risk_factors["security"]:
            recommendations.append("Implement comprehensive authentication and authorization system")
            recommendations.append("Add input validation and sanitization throughout the application")
            recommendations.append("Enable HTTPS/TLS encryption for all network communication")
            recommendations.append("Implement rate limiting and CORS policies")
        
        # Architecture recommendations
        if self.risk_factors["architecture"]:
            recommendations.append("Add load balancing and redundancy to prevent single points of failure")
            recommendations.append("Implement caching layer (Redis/Memcached) for performance")
            recommendations.append("Consider microservices architecture for better scalability")
            recommendations.append("Add message queue for asynchronous processing")
            recommendations.append("Implement database replication and sharding strategy")
        
        # Performance recommendations
        if self.risk_factors["performance"]:
            recommendations.append("Implement async/non-blocking processing patterns")
            recommendations.append("Optimize database queries and add proper indexing")
            recommendations.append("Implement connection pooling for database connections")
            recommendations.append("Use CDN for static content delivery")
        
        # Scalability recommendations
        if self.risk_factors["scalability"]:
            recommendations.append("Containerize application using Docker")
            recommendations.append("Implement orchestration using Kubernetes")
            recommendations.append("Design application to be stateless for horizontal scaling")
        
        # Deployment recommendations
        if self.risk_factors["deployment"]:
            recommendations.append("Implement comprehensive monitoring and alerting")
            recommendations.append("Set up centralized logging system")
            recommendations.append("Define health checks and readiness probes")
            recommendations.append("Establish automated CI/CD pipeline")
            recommendations.append("Create disaster recovery and backup plan")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def determine_autonomy_mode(self) -> str:
        """Determine autonomy mode based on risk score"""
        
        if self.risk_score < 0.3:
            return "AUTO_EXECUTE"
        elif self.risk_score < 0.7:
            return "SUGGEST_ONLY"
        else:
            return "HUMAN_CONTROL"
    
    def get_risk_report_display(self, risk_report: Dict[str, Any]) -> str:
        """Format risk report for terminal display"""
        
        output = "\n" + "="*70 + "\n"
        output += "RISK ANALYSIS\n"
        output += "="*70 + "\n\n"
        
        # Risk score and level
        score_pct = int(risk_report["risk_score"] * 100)
        output += f"Risk Score: {risk_report['risk_score']:.2f} ({score_pct}%)\n"
        output += f"Risk Level: {self._format_risk_level(risk_report['risk_level'])}\n\n"
        
        # Detected issues
        if risk_report["all_issues"]:
            output += "Detected Issues:\n"
            for issue in risk_report["all_issues"]:
                output += f"  • {issue}\n"
            output += "\n"
        
        # Explanation
        output += "Explanation:\n"
        output += f"{risk_report['explanation']}\n\n"
        
        # Recommendations
        if risk_report["recommendations"]:
            output += "Recommendations:\n"
            for i, rec in enumerate(risk_report["recommendations"], 1):
                output += f"  {i}. {rec}\n"
            output += "\n"
        
        return output
    
    def _format_risk_level(self, level: str) -> str:
        """Format risk level with visual indicator"""
        
        if level == "LOW":
            return "[LOW] Low risk - Safe to proceed"
        elif level == "MEDIUM":
            return "[MEDIUM] Moderate risk - Review recommended"
        else:  # HIGH
            return "[HIGH] High risk - Human approval required"
