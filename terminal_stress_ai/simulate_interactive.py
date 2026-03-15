#!/usr/bin/env python3
"""Simulate interactive session without user typing"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import CoSenseiSession

def simulate_interactive():
    """Simulate interactive session with predefined inputs"""
    
    session = CoSenseiSession()
    
    # Simulate the controller interactions directly
    controller = session.controller
    
    print("\n" + "="*70)
    print("SIMULATED INTERACTIVE SESSION")
    print("="*70 + "\n")
    
    # Simulate System greeting
    print("SYSTEM: Hello! I'm ContextFlow, your AI assistant.")
    print()
    
    # Simulate Test 1: User provides detailed project
    print("USER: Build a Spotify clone with Python FastAPI and React")
    result = controller.process_user_input("Build a Spotify clone with Python FastAPI and React")
    
    if result['type'] == 'solutions':
        print("\nSYSTEM RESPONSE:")
        print("-"*70)
        print("Here are 3 different solutions for your project:\n")
        for i, sol in enumerate(result['solutions'], 1):
            rec = " [RECOMMENDED]" if sol.get('recommended') else ""
            print(f"{i}. {sol.get('title')}{rec}")
            print(f"   {sol.get('description')}")
            print(f"   • Timeline: {sol.get('effort')}")
            print(f"   • Scalability: {sol.get('scalability')}")
            print()
    
    # Simulate Test 2: User selects a solution
    print("\nUSER: 2")
    print("\nSYSTEM RESPONSE:")
    print("-"*70)
    if len(result['solutions']) >= 2:
        sol = result['solutions'][1]
        print(f"IMPLEMENTATION: {sol.get('title')}")
        print(f"\nDescription: {sol.get('description')}")
        print(f"Architecture: {sol.get('architecture')}")
        print(f"Timeline: {sol.get('effort')}")
        print(f"Scalability: {sol.get('scalability')}")
        if 'tech_stack' in sol:
            print(f"\nTech Stack:")
            for key, val in sol['tech_stack'].items():
                print(f"  • {key}: {val}")
    
    # Simulate Test 3: New project
    print("\n\nUSER: new")
    print("\nSYSTEM: Starting new project analysis...")
    session.clarification_pending = False
    session.solutions = []
    
    print("\nUSER: Tell me about a simple website")
    result = controller.process_user_input("Tell me about a simple website")
    
    if result['type'] == 'solutions':
        print("\nSYSTEM RESPONSE: Here are 3 solutions for your simple website:\n")
        for i, sol in enumerate(result['solutions'], 1):
            print(f"{i}. {sol.get('title')}")
            print(f"   Timeline: {sol.get('effort')}")
            print()
    
    print("="*70)
    print("✓ SIMULATED INTERACTIVE SESSION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    simulate_interactive()
