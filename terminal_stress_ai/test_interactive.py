#!/usr/bin/env python3
"""
Interactive test of ContextFlow system
This demonstrates the complete conversation flow
"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import ContextFlowController

def test_interactive_flow():
    """Test the full interactive flow"""
    
    controller = ContextFlowController()
    
    print("=" * 80)
    print("CONTEXTFLOW SYSTEM - INTERACTIVE CONVERSATION FLOW TEST")
    print("=" * 80)
    print()
    
    # Simulate vague user input
    print("SCENARIO 1: User enters vague input")
    print("-" * 80)
    print("User input: 'Hi'")
    print()
    
    result1 = controller.process_user_input("Hi")
    
    print(f"Result type: {result1['type']}")
    print(f"Needs clarification: {result1.get('needs_clarification', False)}")
    
    if result1['type'] == 'clarification':
        print(f"Number of questions: {len(result1.get('questions', []))}")
        print("Sample questions:")
        for i, q in enumerate(result1.get('questions', [])[:3], 1):
            print(f"  {i}. {q}")
        print()
    
    # Simulate detailed user input
    print("\nSCENARIO 2: User provides project details")
    print("-" * 80)
    project_desc = "Build a Spotify clone with real-time music streaming, user playlists, and recommendations using Python/Django backend and React frontend"
    print(f"User input: '{project_desc[:60]}...'")
    print()
    
    result2 = controller.process_user_input(project_desc)
    
    print(f"Result type: {result2['type']}")
    
    if result2['type'] == 'solutions':
        solutions = result2.get('solutions', [])
        print(f"Number of solutions generated: {len(solutions)}")
        print("\nSolutions proposed:")
        for i, sol in enumerate(solutions, 1):
            title = sol.get('title') or sol.get('name') or f'Solution {i}'
            effort = sol.get('effort') or sol.get('timeline') or 'Unknown'
            print(f"  {i}. {title.upper()}")
            print(f"     Timeline: {effort}")
        
        # Show what happens when user selects solution 2
        print("\n\nSCENARIO 3: User selects solution #2 (Optimized)")
        print("-" * 80)
        controller.solutions = solutions
        
        if len(solutions) >= 2:
            selected = solutions[1]
            print(f"\nSelected: {selected.get('title') or selected.get('name')}")
            print(f"Description: {selected.get('description', '')[:100]}...")
            if 'timeline' in selected or 'effort' in selected:
                print(f"Timeline: {selected.get('timeline') or selected.get('effort')}")
            if 'phases' in selected:
                print(f"Implementation phases: {len(selected.get('phases', []))}")
                if selected.get('phases'):
                    print(f"  Phase 1: {selected['phases'][0] if selected['phases'] else 'N/A'}")
    
    print("\n" + "=" * 80)
    print("✓ Interactive flow test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_interactive_flow()
