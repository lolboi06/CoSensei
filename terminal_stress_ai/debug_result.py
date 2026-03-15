#!/usr/bin/env python3
"""Debug - check what result structure is returned"""

import sys
import json
sys.path.insert(0, 'app')

from contextflow_coordinator import ContextFlowController

controller = ContextFlowController()

# Test with project details
result = controller.process_user_input(
    "I want to build a real-time chat application for gamers with voice integration"
)

print("Result type:", result.get('type'))
print("\nResult keys:")
for key in result.keys():
    print(f"  - {key}")

# Show structure of first solution
if result.get('solutions'):
    print("\nFirst solution keys:")
    for key in result['solutions'][0].keys():
        print(f"  - {key}")
