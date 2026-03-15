#!/usr/bin/env python3
"""Final comprehensive validation of ContextFlow system"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import CoSenseiController

def run_comprehensive_tests():
    """Run comprehensive test suite"""
    
    tests = []
    
    # Test Matrix
    test_cases = [
        # (input, expected_type, description)
        ("HI", "clarification", "Single word vague"),
        ("HELLO", "clarification", "Greeting"),
        ("Hey", "clarification", "Informal greeting"),
        ("Tell me something", "clarification", "Vague request"),
        ("Build a website", "solutions", "Project with keyword"),
        ("Build a Spotify clone", "solutions", "Project name"),
        ("Create an ecommerce app", "solutions", "Type specified"),
        ("I want to design a database", "solutions", "Design keyword"),
        ("Implement a dashboard", "solutions", "Scope keyword"),
        ("Make a mobile app", "solutions", "Platform keyword"),
        ("Write an API", "solutions", "Scope keyword"),
        ("Develop a ChatBot", "solutions", "Scope keyword"),
        ("Design a system", "solutions", "Design keyword"),
        ("WEBSITE", "clarification", "Single tech word (ambiguous)"),
        ("Python", "clarification", "Language only (ambiguous)"),
        ("react website", "solutions", "Tech + scope"),
        ("Build app with Node.js", "solutions", "Project + tech"),
    ]
    
    print("="*80)
    print("COSENSEI - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print()
    
    passed = 0
    failed = 0
    
    for user_input, expected, description in test_cases:
        controller = CoSenseiController()
        result = controller.process_user_input(user_input)
        actual = result['type']
        
        # Check result
        is_pass = actual == expected
        status = "✓ PASS" if is_pass else "✗ FAIL"
        
        if is_pass:
            passed += 1
        else:
            failed += 1
        
        # Get extra info
        if actual == 'clarification':
            num_items = len(result.get('questions', []))
            detail = f"({num_items} questions)"
        elif actual == 'solutions':
            num_items = len(result.get('solutions', []))
            detail = f"({num_items} solutions)"
        else:
            detail = ""
        
        print(f"{status} | '{user_input}'".ljust(40))
        print(f"     Expected: {expected}, Got: {actual} {detail}".ljust(40))
        print(f"     '{description}'")
        print()
        
        tests.append({
            'input': user_input,
            'description': description,
            'expected': expected,
            'actual': actual,
            'passed': is_pass
        })
    
    # Summary
    print("="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*80)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED - SYSTEM IS FULLY FUNCTIONAL!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed - review above")
        print("\nFailed tests:")
        for test in tests:
            if not test['passed']:
                print(f"  • '{test['input']}' - expected {test['expected']}, got {test['actual']}")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
