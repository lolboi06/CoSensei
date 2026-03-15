"""
ContextFlow Autonomy Decision Engine
Determines AI autonomy mode based on user state and system signals
"""

from typing import Dict, Any


class AutonomyDecisionEngine:
    """
    Evaluates whether the AI should operate in:
    - AUTO_EXECUTE: Run without asking
    - SHARED_CONTROL: Show options, ask for selection
    - SUGGEST_ONLY: Generate suggestions only
    - HUMAN_CONTROL: Require explicit approval
    """
    
    def decide_autonomy(
        self,
        task_clarity: float,  # 0-1, how clear is the task
        user_stress: float,   # 0-1, estimated stress
        engagement_level: float,  # 0-1, interaction engagement
        trust_level: float,   # 0-1, accumulated system trust
        risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    ) -> Dict[str, Any]:
        """
        Decide autonomy mode based on multiple signals.
        
        Args:
            task_clarity: How clear the task requirements are
            user_stress: Estimated user stress level
            engagement_level: How engaged the user is
            trust_level: How much user trusts the system
            risk_level: Overall risk classification
            
        Returns:
            Decision context including mode selection
        """
        
        # Decision weights
        weights = {
            "clarity": 0.25,
            "stress": 0.25,
            "engagement": 0.25,
            "trust": 0.25,
            "risk": 0.30  # Risk has extra weight
        }
        
        # Normalize inputs
        clarity_score = task_clarity
        stress_score = 1 - user_stress  # Invert: lower stress = better
        engagement_score = engagement_level
        trust_score = trust_level
        
        # Calculate composite score
        autonomy_score = (
            clarity_score * weights["clarity"] +
            stress_score * weights["stress"] +
            engagement_score * weights["engagement"] +
            trust_score * weights["trust"]
        )
        
        # Apply risk modifier
        risk_modifier = self._get_risk_modifier(risk_level)
        autonomy_score = autonomy_score * (1 - risk_modifier)
        
        # Select mode
        if risk_level == "HIGH":
            mode = "HUMAN_CONTROL"
            reasoning = "High risk detected - requiring human approval"
        elif user_stress > 0.7:
            mode = "SUGGEST_ONLY"
            reasoning = "High user stress detected - reducing autonomy"
        elif task_clarity < 0.3:
            mode = "SUGGEST_ONLY"
            reasoning = "Task clarity too low - need more information"
        elif trust_level < 0.3:
            mode = "SUGGEST_ONLY"
            reasoning = "Trust level low - operating in suggestion mode"
        elif autonomy_score > 0.8:
            mode = "AUTO_EXECUTE"
            reasoning = "Conditions optimal - operating in auto mode"
        elif autonomy_score > 0.6:
            mode = "SHARED_CONTROL"
            reasoning = "Moderate autonomy - shared control mode"
        else:
            mode = "SUGGEST_ONLY"
            reasoning = "Conservative autonomy - suggestion mode"
        
        return {
            "mode": mode,
            "score": autonomy_score,
            "reasoning": reasoning,
            "factors": {
                "clarity": clarity_score,
                "stress": stress_score,
                "engagement": engagement_score,
                "trust": trust_score
            },
            "risk_level": risk_level
        }
    
    def _get_risk_modifier(self, risk_level: str) -> float:
        """Get autonomy reduction based on risk"""
        
        modifiers = {
            "LOW": 0.05,
            "MEDIUM": 0.20,
            "HIGH": 0.50
        }
        
        return modifiers.get(risk_level, 0.20)
    
    def should_auto_execute(self, mode: str) -> bool:
        """Check if mode allows automatic execution"""
        return mode == "AUTO_EXECUTE"
    
    def should_ask_for_selection(self, mode: str) -> bool:
        """Check if mode should show options and ask for selection"""
        return mode in ["SHARED_CONTROL", "SUGGEST_ONLY"]
    
    def should_require_approval(self, mode: str) -> bool:
        """Check if mode requires explicit human approval"""
        return mode == "HUMAN_CONTROL"
    
    def get_mode_description(self, mode: str) -> str:
        """Get user-friendly description of mode"""
        
        descriptions = {
            "AUTO_EXECUTE": "Automatic execution - I'll implement solutions without asking",
            "SHARED_CONTROL": "Shared control - I'll show options for your selection",
            "SUGGEST_ONLY": "Suggestion mode - I'll generate suggestions only",
            "HUMAN_CONTROL": "Manual control - I'll request approval for each step"
        }
        
        return descriptions.get(mode, "Unknown mode")


class RiskAnalyzer:
    """Analyze task risk"""
    
    @staticmethod
    def assess_task_risk(task_context: Dict[str, Any]) -> str:
        """
        Assess risk level for a task.
        
        Returns: LOW, MEDIUM, or HIGH
        """
        
        risk_factors = 0
        
        # Check for high-impact factors
        if task_context.get('database') == 'production':
            risk_factors += 2
        
        if 'payment' in str(task_context.get('features', '')).lower():
            risk_factors += 2
        
        if 'security' in str(task_context.get('features', '')).lower():
            risk_factors += 2
        
        # Task complexity factor
        categories = task_context.get('categories', [])
        if len(categories) > 7:
            risk_factors += 1
        
        if risk_factors >= 4:
            return "HIGH"
        elif risk_factors >= 2:
            return "MEDIUM"
        else:
            return "LOW"
