#!/usr/bin/env python3
"""
ContextFlow Live Demo - Shows how to run the interactive system
"""

import sys
sys.path.insert(0, 'app')

from contextflow_coordinator import ContextFlowController

def demo():
    """Run a live demonstration of the conversation flow"""
    
    controller = ContextFlowController()
    
    print("\n" + "=" * 80)
    print("CONTEXTFLOW COPILOT - LIVE DEMONSTRATION")
    print("=" * 80)
    print("\nThis demonstrates how ContextFlow creates engaging conversations.\n")
    
    # Display the system greeting
    print("SYSTEM GREETING:")
    print("-" * 80)
    print("Hello! I'm ContextFlow, your AI assistant.")
    print("\nI work by:")
    print("  1. Asking you clarifying questions (feel free to be verbose)")
    print("  2. Understanding your project needs")
    print("  3. Generating 3 distinct solution approaches")
    print("  4. Adapting to your work style and stress level")
    print("  5. Never asking the same question twice\n")
    
    # Simulate first user interaction
    print("USER INPUT #1: 'Hi'")
    print("-" * 80)
    result = controller.process_user_input("Hi")
    
    if result['type'] == 'clarification':
        print("\nSYSTEM RESPONSE:")
        print(result['message'])
        print()
        for i, q in enumerate(result['questions'], 1):
            print(f"{i}. {q}")
        print("\n(You can answer all at once or one at a time)\n")
    
    # Simulate second user interaction with more details
    print("\nUSER INPUT #2: 'I want to build a real-time chat application for gamers'")
    print("-" * 80)
    result = controller.process_user_input(
        "I want to build a real-time chat application for gamers with voice integration, " +
        "using Node.js backend and React frontend"
    )
    
    if result['type'] == 'solutions':
        print("\nSYSTEM RESPONSE:")
        print("=" * 70)
        print("SOLUTION STRATEGIES FOR YOUR PROJECT")
        print("=" * 70 + "\n")
        
        for i, sol in enumerate(result['solutions'], 1):
            rec = " [RECOMMENDED START HERE]" if sol.get('recommended', False) else ""
            title = sol.get('title') or sol.get('name') or f"Solution {i}"
            print(f"{i}. {title.upper()}{rec}")
            print(f"   {sol.get('description', '')}")
            print(f"   • Timeline: {sol.get('effort', 'Unknown')}")
            print(f"   • Scalability: {sol.get('scalability', 'Unknown')}")
            print()
    
    print("\nWould you like to run the full interactive session?")
    print("-" * 80)
    print("\nTo start a fully interactive session, run:")
    print("  cd terminal_stress_ai")
    print("  python app/contextflow_coordinator.py")
    print("\nThen type your project description and follow the prompts!\n")
    
    print("=" * 80)
    print("AVAILABLE COMMANDS IN INTERACTIVE MODE:")
    print("=" * 80)
    print("  • Type numbers 1, 2, or 3 to select a solution")
    print("  • Type 'new' to start a fresh project")
    print("  • Type 'exit' or 'quit' to end the session")
    print("  • Type 'bye' to say goodbye")
    print()

if __name__ == "__main__":
    demo()
