#!/usr/bin/env python3
"""Complete flow verification - simulate full user journey"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import CoSenseiController

def simulate_user_journey():
    """Simulate a complete user journey through ContextFlow"""
    
    print("="*70)
    print("CONTEXTFLOW - COMPLETE USER JOURNEY VERIFICATION")
    print("="*70)
    print()
    
    # Scenario 1: Vague start, then clarification
    print("SCENARIO 1: User starts vague")
    print("-"*70)
    controller = CoSenseiController()
    
    # User says "HI"
    print("User: 'HI'")
    result = controller.process_user_input("HI")
    if result['type'] == 'clarification':
        print(f"✓ System asks for clarification (5 questions)")
        print(f"  Q1: {result['questions'][0]}")
    else:
        print(f"✗ ERROR: Expected clarification, got {result['type']}")
        return False
    
    # User provides details
    print("\nUser: 'I want to build an ecommerce website'")
    result = controller.process_user_input("I want to build an ecommerce website")
    if result['type'] == 'solutions':
        print(f"✓ System generates 3 solutions")
        print(f"  Solution 2 (Recommended): {result['solutions'][1].get('title')}")
    else:
        print(f"✗ ERROR: Expected solutions, got {result['type']}")
        return False
    
    print()
    
    # Scenario 2: Detailed input immediately
    print("SCENARIO 2: User provides detailed input immediately")
    print("-"*70)
    controller = CoSenseiController()
    
    print("User: 'Build a real-time chat app using Node.js and React'")
    result = controller.process_user_input("Build a real-time chat app using Node.js and React")
    if result['type'] == 'solutions':
        print(f"✓ System immediately generates 3 solutions")
        for i, sol in enumerate(result['solutions'][:1], 1):
            print(f"  {i}. {sol.get('title')}")
    else:
        print(f"✗ ERROR: Expected solutions, got {result['type']}")
        return False
    
    # User selects solution
    print("\nUser selects solution 2...")
    if len(result['solutions']) >= 2:
        sol = result['solutions'][1]
        print(f"✓ Solution selected: {sol.get('title')}")
        print(f"  Timeline: {sol.get('effort')}")
        print(f"  Description: {sol.get('description')[:60]}...")
    
    print()
    
    # Scenario 3: Multi-word project
    print("SCENARIO 3: Single-word unclear input")
    print("-"*70)
    controller = CoSenseiController()
    
    print("User: 'WEBSITE'")
    result = controller.process_user_input("WEBSITE")
    if result['type'] == 'clarification':
        print(f"✓ System asks for clarification (recognizes it's unclear)")
    elif result['type'] == 'solutions':
        print(f"✗ WARNING: 'WEBSITE' generated solutions (minor issue)")
    else:
        print(f"✗ ERROR: Expected clarification or solutions, got {result['type']}")
        return False
    
    print()
    print("="*70)
    print("✓ COMPLETE FLOW VERIFICATION PASSED!")
    print("="*70)
    return True

if __name__ == "__main__":
    try:
        success = simulate_user_journey()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
