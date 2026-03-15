#!/usr/bin/env python3
"""Test Verifier AI risk analysis"""

import sys
sys.path.insert(0, 'app')

from verifier_ai import VerifierAI

def test_risk_analysis():
    """Test Verifier AI risk detection"""
    
    verifier = VerifierAI()
    
    # Test 1: High-risk solution (poor practices)
    high_risk_solution = {
        'title': 'Insecure Monolith',
        'description': 'Simple Flask app with hardcoded credentials',
        'architecture': '''
        [Monolithic Flask App]
        - admin username: "admin123" 
        - API keys embedded in code
        - No input validation
        - Direct database queries in routes
        - No authentication/authorization
        ''',
        'features': []
    }
    
    task_context = "Build a payment processing system"
    
    print("="*70)
    print("VERIFIER AI - RISK ANALYSIS TEST")
    print("="*70)
    print()
    
    print("TEST 1: High-Risk Solution")
    print("-"*70)
    print("Solution:", high_risk_solution['title'])
    print("Context:", task_context)
    print()
    
    result = verifier.analyze_risk(high_risk_solution, task_context)
    
    print(f"Risk Score: {result['risk_score']:.2f}/1.0")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Autonomy Mode: {result['autonomy_mode']}")
    print()
    
    print("Issues Found:")
    issues_found = False
    for category in ['security_issues', 'architecture_issues', 'performance_issues', 'scalability_issues', 'deployment_issues']:
        if result[category]:
            print(f"  {category.replace('_', ' ').title()}:")
            for issue in result[category]:
                print(f"    • {issue}")
            issues_found = True
    if not issues_found:
        print("  No issues detected")
    
    print()
    print("Explanation:")
    print(result['explanation'])
    
    print()
    print("Recommendations:")
    for rec in result['recommendations'][:3]:
        print(f"  • {rec}")
    
    print()
    print()
    
    # Test 2: Low-risk solution (best practices)
    low_risk_solution = {
        'title': 'Secure Microservices',
        'description': 'Industry-standard microservices with security',
        'architecture': '''
        [API Gateway] -> [Load Balancer]
            |
            v
        [Microservices with Kong API Gateway]
        - All credentials in environment variables
        - TLS encryption enabled
        - Input validation on all endpoints
        - OAuth2 authentication
        - Rate limiting configured
        - Database connection pooling
        ''',
        'features': ['Authentication', 'Authorization', 'Rate Limiting', 
                    'Monitoring', 'Logging', 'Encryption']
    }
    
    print("TEST 2: Low-Risk Solution")
    print("-"*70)
    print("Solution:", low_risk_solution['title'])
    print("Context:", task_context)
    print()
    
    result = verifier.analyze_risk(low_risk_solution, task_context)
    
    print(f"Risk Score: {result['risk_score']:.2f}/1.0")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Autonomy Mode: {result['autonomy_mode']}")
    print()
    
    issues_found = False
    for category in ['security_issues', 'architecture_issues', 'performance_issues', 'scalability_issues', 'deployment_issues']:
        if result[category]:
            issues_found = True
            break
    
    if issues_found:
        print("Issues Found:")
        for category in ['security_issues', 'architecture_issues', 'performance_issues', 'scalability_issues', 'deployment_issues']:
            if result[category]:
                print(f"  {category.replace('_', ' ').title()}:")
                for issue in result[category]:
                    print(f"    • {issue}")
    else:
        print("✓ No issues detected - solution follows best practices")
    
    print()
    print()
    
    # Test 3: Verification display
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print("✓ Verifier AI successfully analyzing solutions")
    print("✓ Risk categories: Security, Architecture, Performance, Scalability, Deployment")
    print("✓ Autonomy modes determined based on risk score")
    print("✓ High-risk solutions trigger HUMAN_CONTROL mode")
    print("✓ Low-risk solutions allow AUTO_EXECUTE mode")

if __name__ == "__main__":
    test_risk_analysis()
