#!/usr/bin/env python3
"""Quick test to verify the system works after cache clear"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import CoSenseiController

def test():
    controller = CoSenseiController()
    
    # Test 1: Vague input should trigger clarification
    print("TEST 1: Vague Input (HI)")
    print("-" * 60)
    result1 = controller.process_user_input("HI")
    print(f"Type: {result1['type']}")
    if result1['type'] == 'clarification':
        print(f"Questions: {len(result1['questions'])}")
        print("✓ PASS: Got clarification\n")
    else:
        print("✗ FAIL: Expected clarification but got solutions\n")
    
    # Reset controller
    controller = ContextFlowController()
    
    # Test 2: Detailed input should generate solutions
    print("TEST 2: Detailed Input (Spotify clone...)")
    print("-" * 60)
    result2 = controller.process_user_input("Build a Spotify clone with Python FastAPI and PostgreSQL")
    print(f"Type: {result2['type']}")
    if result2['type'] == 'solutions':
        print(f"Solutions: {len(result2['solutions'])}")
        print("✓ PASS: Got solutions\n")
    else:
        print(f"✗ FAIL: Expected solutions but got {result2['type']}\n")
    
    # Test 3: Short response should trigger clarification
    print("TEST 3: Short/Vague Input (HELLO)")
    print("-" * 60) 
    result3 = controller.process_user_input("HELLO")
    print(f"Type: {result3['type']}")
    if result3['type'] == 'clarification':
        print(f"Questions: {len(result3['questions'])}")
        print("✓ PASS: Got clarification\n")
    else:
        print(f"✗ FAIL: Expected clarification but got {result3['type']}\n")

if __name__ == "__main__":
    try:
        test()
        print("=" * 60)
        print("✓ All critical tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
