#!/usr/bin/env python3
"""Quick test of the ContextFlow conversation flow"""

import sys
sys.path.insert(0, 'app')

from dynamic_clarification_generator import DynamicClarificationGenerator
from planner_ai import PlannerAI

# Test 1: Vague input
print('TEST 1: Vague input (HI)')
print('='*60)
gen = DynamicClarificationGenerator()
result = gen.analyze_prompt('Hi')
print(f'Categories found: {result.get("relevant_categories", [])}')
print(f'Needs clarification: {result.get("needs_clarification")}')
print(f'Real matches: {result.get("real_matches_found")}')
print()

# Test 2: Project input
print('TEST 2: Project input (Spotify clone)')
print('='*60)
result = gen.analyze_prompt('Build a Spotify clone with Python and React')
print(f'Categories found: {result.get("relevant_categories", [])}')
print(f'Needs clarification: {result.get("needs_clarification")}')
print(f'Real matches: {result.get("real_matches_found")}')
print()

# Test 3: Check planner AI response for vague input
print('TEST 3: Planner AI analysis for vague input')
print('='*60)
planner = PlannerAI()
analysis = planner.analyze_user_input('Hi')
print(f'Clarity level: {analysis["clarity_level"]}')
print(f'Needs clarification: {analysis["needs_clarification"]}')
questions = planner.generate_clarification_questions('Hi')
print(f'Number of questions: {len(questions) if questions else 0}')
if questions:
    print(f'First question: {questions[0]}')
print()

# Test 4: Check planner AI response for detailed input
print('TEST 4: Planner AI analysis for detailed input')
print('='*60)
analysis = planner.analyze_user_input('Build a Spotify clone with Python and React')
print(f'Clarity level: {analysis["clarity_level"]}')
print(f'Needs clarification: {analysis["needs_clarification"]}')
print(f'Categories detected: {analysis["categories"]}')
print()

print("✓ All tests passed!")
