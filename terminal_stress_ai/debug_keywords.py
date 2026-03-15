#!/usr/bin/env python3
"""Debug: Check what the clarification generator is actually matching"""

import sys
sys.path.insert(0, 'app')

from dynamic_clarification_generator import DynamicClarificationGenerator

gen = DynamicClarificationGenerator()

test_inputs = [
    "HI",
    "HELLO",
    "Build a Spotify clone with Python FastAPI and PostgreSQL",
    "website",
    "WEBSITE",
]

for test_input in test_inputs:
    result = gen.analyze_prompt(test_input)
    print(f"Input: '{test_input}'")
    print(f"  real_matches_found: {result.get('real_matches_found')}")
    print(f"  relevant_categories: {result.get('relevant_categories', [])}")
    print(f"  category_scores: {result.get('category_scores', {})}")
    print(f"  needs_clarification: {result.get('needs_clarification')}")
    print()
