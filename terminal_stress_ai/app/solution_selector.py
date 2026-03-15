"""
Solution selection detector and validator.
Identifies when user has selected a solution and validates the choice.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional


class SolutionSelector:
    """Detects and processes user solution selections."""

    # Maps various user inputs to solution strategies
    SELECTION_MAPPING = {
        # Simple solution
        "1": "simple",
        "one": "simple",
        "simple": "simple",
        "minimal": "simple",
        "basic": "simple",
        "quick": "simple",
        "lightweight": "simple",
        
        # Optimized solution
        "2": "optimized",
        "two": "optimized",
        "optimized": "optimized",
        "optimised": "optimized",
        "production": "optimized",
        "efficient": "optimized",
        "medium": "optimized",
        "recommended": "optimized",
        
        # Scalable solution
        "3": "scalable",
        "three": "scalable",
        "scalable": "scalable",
        "enterprise": "scalable",
        "large": "scalable",
        "distributed": "scalable",
        "advanced": "scalable",
        "full": "scalable",
    }

    def detect_selection(self, user_input: str) -> Optional[str]:
        """
        Detect if user is selecting a solution.
        Returns strategy name ('simple', 'optimized', 'scalable') or None.
        """
        if not user_input or not isinstance(user_input, str):
            return None
        
        lowered = user_input.strip().lower()
        
        # Remove common words
        lowered = re.sub(r'\b(solution|option|choice|please|thanks|i want|i prefer|use|go with|select|choose)\b', '', lowered)
        lowered = lowered.strip()
        
        # Direct match
        if lowered in self.SELECTION_MAPPING:
            return self.SELECTION_MAPPING[lowered]
        
        # Check if input contains a selection token
        tokens = lowered.split()
        for token in tokens:
            clean = token.rstrip('.,!?;:')
            if clean in self.SELECTION_MAPPING:
                return self.SELECTION_MAPPING[clean]
        
        # Pattern matching for things like "option 2" or "solution 1"
        patterns = [
            r'(?:solution|option|choice|strategy|approach)\s*[\W_]*\s*([1-3]|simple|optimized|scalable)',
            r'([1-3]|simple|optimized|scalable)\s*(?:solution|option|choice|strategy)',
            r'^([1-3])[\s\.]*$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, lowered, re.IGNORECASE)
            if match:
                token = match.group(1).lower()
                if token in self.SELECTION_MAPPING:
                    return self.SELECTION_MAPPING[token]
        
        return None

    def validate_selection(self, selected_strategy: str, available_solutions: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """
        Validate that the selected strategy exists in available solutions.
        Returns the full solution dict or None if invalid.
        """
        if not selected_strategy:
            return None
        
        for solution in available_solutions:
            if (solution.get("strategy", "").lower() == selected_strategy.lower() or
                solution.get("id") == selected_strategy):
                return solution
        
        return None

    def is_selection_input(self, user_input: str) -> bool:
        """Check if user input is likely a solution selection (not a question)."""
        if not user_input or len(user_input) > 100:
            return False
        
        selection = self.detect_selection(user_input)
        return selection is not None

    def extract_solution_choice(self, user_input: str, available_solutions: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """
        Extract and validate solution choice from user input.
        Returns full solution dict if valid, None otherwise.
        """
        strategy = self.detect_selection(user_input)
        if not strategy:
            return None
        
        return self.validate_selection(strategy, available_solutions)

    def get_selection_confirmation_message(self, selected_solution: Dict[str, str]) -> str:
        """Generate a confirmation message for the selected solution."""
        return (
            f"\n✓ You selected: {selected_solution.get('title', 'Solution')}\n"
            f"Description: {selected_solution.get('description', '')}\n"
            f"Effort: {selected_solution.get('effort', 'Unknown')}\n"
            f"\nGenerating implementation package...\n"
        )

    def get_invalid_selection_message(self, user_input: str) -> Optional[str]:
        """Generate helpful message if selection was invalid."""
        if len(user_input) > 50:
            return "Your input was too long to be a solution selection. Please respond with just the number (1, 2, or 3) or strategy name (simple, optimized, scalable)."
        
        # Check if they're trying to select but failed
        if any(word in user_input.lower() for word in ["option", "solution", "number", "choose"]):
            return "I didn't recognize that as a valid solution selection. Please choose: 1 (Simple), 2 (Optimized), or 3 (Scalable)."
        
        return None
