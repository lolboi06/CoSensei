#!/usr/bin/env python3
"""Test implementation generation feature"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import CoSenseiController

def test_implementation_generation():
    """Test that implementation details are generated"""
    
    controller = CoSenseiController()
    
    print("="*70)
    print("TEST: Implementation Generation Feature")
    print("="*70)
    print()
    
    # Test 1: Process user input
    print("TEST 1: Generate solutions with risk analysis")
    print("-"*70)
    
    user_input = "Build a website for tiger prediction in national parks"
    result = controller.process_user_input(user_input)
    
    if result['type'] == 'solutions':
        print(f"✓ Generated {len(result['solutions'])} solutions")
        print(f"✓ Risk analyzed for each solution")
        
        for i, sol in enumerate(result['solutions'], 1):
            risk = result['risk_analyses'][i-1]
            print(f"  Solution {i}: {sol['title']} - Risk: {risk['risk_score']:.0%} ({risk['risk_level']})")
    else:
        print("✗ Failed to generate solutions")
        return False
    
    print()
    
    # Test 2: Process solution selection
    print("TEST 2: Generate implementation for selected solution")
    print("-"*70)
    
    # Select solution 2 (Optimized)
    task_context = result['task_context']
    implementation_output = controller.process_solution_selection(1, task_context)
    
    if "IMPLEMENTATION DETAILS" in implementation_output:
        print("✓ Implementation details generated successfully")
        print()
        print(implementation_output[:500] + "...\n")
        return True
    else:
        print("✗ Failed to generate implementation")
        print(implementation_output[:200])
        return False


if __name__ == "__main__":
    success = test_implementation_generation()
    if success:
        print("="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
    else:
        print("✗ TESTS FAILED")
        sys.exit(1)
