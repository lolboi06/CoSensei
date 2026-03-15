"""
Integration Demo: How Middle AI and Generator AI work together with Dynamic Clarification
"""

import sys
import os

# Fix imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.dynamic_clarification_generator import DYNAMIC_CLARIFICATION_GENERATOR


class MiddleAIRouter:
    """Middle AI - Makes routing decisions based on semantic analysis"""
    
    def route_request(self, user_prompt: str, user_answers: dict = None) -> dict:
        """
        Analyze request and decide: clarify or route?
        """
        print(f"\n{'='*60}")
        print(f"MIDDLE AI: Processing '{user_prompt[:50]}...'")
        print(f"{'='*60}")
        
        # Step 1: Analyze what clarity is needed
        analysis = DYNAMIC_CLARIFICATION_GENERATOR.analyze_prompt(user_prompt)
        print(f"[OK] Detected categories: {analysis['relevant_categories']}")
        
        # Step 2: Decide: clarify or proceed?
        if len(analysis['relevant_categories']) < 2:
            print(f"[!] Too vague - {len(analysis['relevant_categories'])} category detected")
            clarification = DYNAMIC_CLARIFICATION_GENERATOR.generate_clarification_prompt(
                user_prompt, analysis
            )
            return {
                "action": "clarify",
                "prompt": clarification,
                "analysis": analysis
            }
        
        # Step 3: Build semantic context
        print(f"[OK] Clear enough - proceeding with {len(analysis['relevant_categories'])} categories")
        context = DYNAMIC_CLARIFICATION_GENERATOR.build_context_from_answers(
            user_prompt, analysis, user_answers or {}
        )
        
        # Step 4: Smart routing
        service = self.select_service(context)
        print(f"[OK] Routing to: {service}")
        
        return {
            "action": "route",
            "service": service,
            "context": context
        }
    
    def select_service(self, context: dict) -> str:
        """Select which Generator AI service handles this"""
        categories = context.get('relevant_categories', [])
        
        if 'interface' in categories:
            if context.get('target_platform') == 'web':
                return "GeneratorAI_Web"
            elif context.get('target_platform') == 'mobile':
                return "GeneratorAI_Mobile"
            else:
                return "GeneratorAI_UI"
        
        if 'data' in categories:
            return "GeneratorAI_DataAnalysis"
        
        if 'integration' in categories:
            return "GeneratorAI_API"
        
        if 'security' in categories:
            return "GeneratorAI_Security"
        
        return "GeneratorAI_General"


class GeneratorAI:
    """Generic Generator AI - Works with semantic context, no hardcoding"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def generate(self, context: dict) -> dict:
        """Generate solution based on semantic context"""
        print(f"\n{'='*60}")
        print(f"GENERATOR AI ({self.service_name}): Building solution")
        print(f"{'='*60}")
        print(f"Received context:")
        print(f"  > Categories: {context['relevant_categories']}")
        print(f"  > Tech: {context.get('preferred_technology', 'not specified')}")
        print(f"  > Platform: {context.get('target_platform', 'not specified')}")
        print(f"  > Scale: {context.get('project_scale', 'not specified')}")
        
        # Smart decisions based on actual context (no templates)
        decisions = self.make_decisions(context)
        
        print(f"\nGeneration decisions:")
        for key, value in decisions.items():
            print(f"  [*] {key}: {value}")
        
        return {
            "status": "generated",
            "service": self.service_name,
            "decisions": decisions,
            "context_used": context
        }
    
    def make_decisions(self, context: dict) -> dict:
        """Make technology decisions based on context"""
        decisions = {}
        
        # Decision 1: Framework
        tech = context.get('preferred_technology', 'general')
        scale = context.get('project_scale', 'medium')
        
        if tech == 'python':
            decisions['framework'] = 'FastAPI' if scale == 'large' else 'Flask'
        elif tech == 'javascript':
            decisions['framework'] = 'Next.js' if scale == 'large' else 'Express'
        else:
            decisions['framework'] = f"Standard {tech} framework"
        
        # Decision 2: Database
        if context.get('needs_persistence'):
            # Use detected database preference if available
            preferred_db = context.get('database_preference')
            if preferred_db:
                decisions['database'] = preferred_db
            else:
                # Fall back to scale-based selection
                decisions['database'] = 'PostgreSQL' if scale == 'large' else 'SQLite'
        else:
            decisions['database'] = 'In-memory (no persistence)'
        
        # Decision 3: Deployment
        platform = context.get('target_platform', 'web')
        scale = context.get('project_scale', 'medium')
        
        if platform == 'web':
            decisions['deployment'] = 'Docker + Kubernetes' if scale in ('large', 'enterprise') else 'Docker + local'
        elif platform == 'mobile':
            decisions['deployment'] = 'App Store / Play Store'
        elif platform == 'api':
            decisions['deployment'] = 'AWS Lambda' if scale in ('small', 'medium') else 'ECS Cluster'
        
        return decisions


# DEMO EXECUTION
if __name__ == "__main__":
    router = MiddleAIRouter()
    
    # Scenario 1: Web App Request (Clear)
    print("\n" + "="*70)
    print("SCENARIO 1: Clear Web App Request")
    print("="*70)
    
    result = router.route_request("Build a scalable web app for task management")
    if result['action'] == 'route':
        generator = GeneratorAI(result['service'])
        generator.generate(result['context'])
    
    # Scenario 2: Data Analysis Request (Clear)
    print("\n" + "="*70)
    print("SCENARIO 2: Clear Data Analysis Request")
    print("="*70)
    
    result = router.route_request("Analyze customer data for patterns and trends")
    if result['action'] == 'route':
        generator = GeneratorAI(result['service'])
        generator.generate(result['context'])
    
    # Scenario 3: Vague Request (Needs Clarification)
    print("\n" + "="*70)
    print("SCENARIO 3: Vague Request (Needs Clarification)")
    print("="*70)
    
    result = router.route_request("Help me build something")
    if result['action'] == 'clarify':
        print("\nMiddle AI asking for clarification:")
        print(result['prompt'])
    
    # Scenario 4: Multi-domain Project
    print("\n" + "="*70)
    print("SCENARIO 4: Multi-Domain Project (Web + API + Data)")
    print("="*70)
    
    user_answers = {
        'answer_1': 'React frontend with Node backend and PostgreSQL',
        'answer_2': 'Python and JavaScript',
        'answer_3': 'AWS deployment on web and mobile platforms',
        'answer_4': 'Enterprise scale with high availability'
    }
    
    result = router.route_request(
        "Build a full-stack app with API integration and data analytics",
        user_answers
    )
    if result['action'] == 'route':
        generator = GeneratorAI(result['service'])
        generator.generate(result['context'])
    
    print("\n" + "="*70)
    print("INTEGRATION DEMO COMPLETE")
    print("="*70)
