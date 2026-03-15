"""
Middle AI / Planner Engine - Evaluates risk, creates prompts, enables dynamic shared control.
Bridges user behavior + survey data with solution generation.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any


class MiddleAIPlannerEngine:
    """
    Evaluates user behavior and risk factors.
    Creates detailed prompts for Generator AI.
    Enables dynamic shared control for risk assessment.
    """

    # Risk factor categories
    RISK_CATEGORIES = {
        "behavioral": ["stress", "cognitive_load", "distrust", "frustration"],
        "contextual": ["complexity", "time_pressure", "scope_creep", "ambiguity"],
        "technical": ["compatibility", "performance_risk", "security", "scalability"],
        "human": ["experience_level", "team_capacity", "deadline_feasibility"],
    }

    @staticmethod
    def analyze_user_behavior(
        behavioral_signals: List[Dict[str, Any]],
        feature_snapshot: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Analyze user behavior signals and extract risk indicators.
        Returns detailed behavior analysis with flagged risks.
        """
        analysis = {
            "stress_level": feature_snapshot.get("stress", 0.5),
            "cognitive_load": feature_snapshot.get("cognitive_load", 0.5),
            "engagement": feature_snapshot.get("engagement", 0.5),
            "distrust_signals": feature_snapshot.get("distrust_event_rate", 0.0),
            "corrections_made": feature_snapshot.get("backspace_ratio", 0.0),
            "typing_confidence": feature_snapshot.get("typing_cpm", 200.0),
            "hesitation_count": feature_snapshot.get("hesitation_count", 0.0),
            "override_rate": feature_snapshot.get("override_rate", 0.0),
        }

        # Identify behavior flags
        flags = []
        if analysis["stress_level"] > 0.7:
            flags.append(("HIGH_STRESS", "User is stressed - simpler solution recommended"))
        if analysis["cognitive_load"] > 0.7:
            flags.append(("HIGH_LOAD", "High cognitive demand - break into smaller steps"))
        if analysis["distrust_signals"] > 0.3:
            flags.append(("DISTRUST", "User shows distrust - explain reasoning"))
        if analysis["override_rate"] > 0.5:
            flags.append(("FREQUENT_EDITS", "User edits frequently - provide scaffolding"))
        if analysis["corrections_made"] > 0.15:
            flags.append(("UNCERTAINTY", "User shows uncertainty - offer defaults"))

        analysis["behavioral_flags"] = flags
        return analysis

    @staticmethod
    def extract_survey_data(
        nasa_tlx: Optional[Dict[str, float]] = None,
        trust_survey: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Extract and normalize survey data into actionable insights.
        """
        survey_data = {
            "mental_demand": nasa_tlx.get("mental_demand", 50) if nasa_tlx else 50,
            "physical_demand": nasa_tlx.get("physical_demand", 0) if nasa_tlx else 0,
            "temporal_demand": nasa_tlx.get("temporal_demand", 50) if nasa_tlx else 50,
            "performance": nasa_tlx.get("performance", 50) if nasa_tlx else 50,
            "effort": nasa_tlx.get("effort", 50) if nasa_tlx else 50,
            "frustration": nasa_tlx.get("frustration", 20) if nasa_tlx else 20,
            "trust_ai_suggestions": trust_survey.get("trust_ai_suggestions", 3) if trust_survey else 3,
            "ai_reliability": trust_survey.get("ai_reliable", 3) if trust_survey else 3,
            "comfort_with_autonomy": trust_survey.get("comfort_autonomy", 3) if trust_survey else 3,
        }

        # Normalize to 0-1 scale
        for key in survey_data:
            if "demand" in key or key in ["performance", "effort", "frustration"]:
                survey_data[key] = survey_data[key] / 100.0
            else:  # Trust ratings 1-5
                survey_data[key] = survey_data[key] / 5.0

        return survey_data

    @staticmethod
    def calculate_risk_factors(
        task_context: Dict[str, str],
        behavior_analysis: Dict[str, Any],
        survey_data: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Calculate risk factors across multiple dimensions.
        Returns risk matrix with some factors marked for user approval (SHARED_CONTROL).
        """

        # Behavioral risks (system-calculated)
        behavioral_risks = {
            "user_stress": min(1.0, behavior_analysis.get("stress_level", 0.5)),
            "cognitive_overload": min(1.0, behavior_analysis.get("cognitive_load", 0.5)),
            "distrust": min(1.0, behavior_analysis.get("distrust_signals", 0.0)),
            "uncertainty": min(1.0, behavior_analysis.get("corrections_made", 0.0)),
        }

        # Contextual risks - some need user input
        contextual_risks = {
            "project_complexity": {
                "value": MiddleAIPlannerEngine._estimate_complexity(task_context),
                "requires_user_input": True,  # User knows their project best
                "description": "How complex is this project? (1=simple, 10=massive)",
            },
            "time_pressure": {
                "value": survey_data.get("temporal_demand", 0.5),
                "requires_user_input": True,  # Only user knows deadline
                "description": "Any time pressure? (1=relaxed, 10=urgent)",
            },
            "scope_clarity": {
                "value": 1.0 - behavior_analysis.get("hesitation_count", 0.0) * 0.1,
                "requires_user_input": True,  # User confirms scope clarity
                "description": "How clear is your project scope? (1=vague, 10=crystal clear)",
            },
            "team_capacity": {
                "value": 0.5,  # Default - user should adjust
                "requires_user_input": True,  # Users know their team
                "description": "Team experience level? (1=new, 10=expert)",
            },
        }

        # Technical risks (system-calculated)
        technical_risks = {
            "scalability_required": MiddleAIPlannerEngine._needs_scalability(task_context),
            "security_criticality": MiddleAIPlannerEngine._security_level(task_context),
            "performance_criticality": MiddleAIPlannerEngine._performance_level(task_context),
        }

        return {
            "behavioral_risks": behavioral_risks,
            "contextual_risks": contextual_risks,
            "technical_risks": technical_risks,
            "overall_risk_score": MiddleAIPlannerEngine._calculate_overall_risk(
                behavioral_risks, contextual_risks, technical_risks, survey_data
            ),
        }

    @staticmethod
    def _estimate_complexity(task_context: Dict[str, str]) -> float:
        """Estimate project complexity from task context."""
        complexity_map = {
            "landing_page": 0.2,
            "web_app": 0.5,
            "ecommerce": 0.6,
            "dashboard": 0.4,
            "content_site": 0.3,
        }
        return complexity_map.get(task_context.get("site_type", "web_app"), 0.5)

    @staticmethod
    def _needs_scalability(task_context: Dict[str, str]) -> float:
        """Determine if scalability is critical."""
        site_type = task_context.get("site_type", "web_app")
        if site_type in ["ecommerce", "dashboard"]:
            return 0.8
        elif site_type == "web_app":
            return 0.5
        else:
            return 0.2

    @staticmethod
    def _security_level(task_context: Dict[str, str]) -> float:
        """Determine security requirements."""
        site_type = task_context.get("site_type", "web_app")
        if site_type in ["ecommerce", "dashboard"]:
            return 0.9
        elif site_type == "web_app":
            return 0.6
        else:
            return 0.3

    @staticmethod
    def _performance_level(task_context: Dict[str, str]) -> float:
        """Determine performance criticality."""
        platform = task_context.get("target_platform", "responsive_web")
        if platform == "mobile_first":
            return 0.8
        else:
            return 0.5

    @staticmethod
    def _calculate_overall_risk(
        behavioral: Dict[str, float],
        contextual: Dict[str, Any],
        technical: Dict[str, float],
        survey_data: Dict[str, float],
    ) -> float:
        """Calculate overall risk score (0-1)."""
        behavioral_avg = sum(behavioral.values()) / len(behavioral)

        contextual_values = [
            v.get("value", 0.5) if isinstance(v, dict) else v
            for v in contextual.values()
        ]
        contextual_avg = sum(contextual_values) / len(contextual_values) if contextual_values else 0.5

        technical_avg = sum(technical.values()) / len(technical) if technical else 0.5

        # Weight the components
        overall = (behavioral_avg * 0.3) + (contextual_avg * 0.3) + (technical_avg * 0.4)
        return min(1.0, overall)

    @staticmethod
    def create_prompt_for_generator(
        task_context: Dict[str, str],
        risk_assessment: Dict[str, Any],
        behavior_analysis: Dict[str, Any],
        user_risk_inputs: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Create a detailed prompt for the Generator AI based on all analysis.
        Incorporates user corrections to risk factors (SHARED_CONTROL).
        """

        # Apply user inputs to contextual risks
        if user_risk_inputs:
            for key, value in user_risk_inputs.items():
                if key in risk_assessment["contextual_risks"]:
                    risk_assessment["contextual_risks"][key]["value"] = value / 10.0

        overall_risk = risk_assessment.get("overall_risk_score", 0.5)
        behavioral_flags = behavior_analysis.get("behavioral_flags", [])

        # Determine solution strategy recommendation based on risk
        if overall_risk > 0.7:
            recommended_strategy = "simple"
            reasoning = "High-risk situation. Start with minimal viable product."
        elif overall_risk > 0.4:
            recommended_strategy = "optimized"
            reasoning = "Medium risk. Balanced approach with good practices."
        else:
            recommended_strategy = "scalable"
            reasoning = "Low risk. Can implement full enterprise architecture."

        # Build behavioral guidance
        behavioral_guidance = []
        for flag_code, flag_msg in behavioral_flags:
            behavioral_guidance.append(flag_msg)

        prompt_data = {
            "task_context": task_context,
            "overall_risk_score": overall_risk,
            "risk_level": "HIGH" if overall_risk > 0.7 else "MEDIUM" if overall_risk > 0.4 else "LOW",
            "recommended_strategy": recommended_strategy,
            "strategy_reasoning": reasoning,
            "behavioral_guidance": behavioral_guidance,
            "risk_factors": {
                "behavioral": risk_assessment["behavioral_risks"],
                "contextual": {
                    k: v.get("value", v) if isinstance(v, dict) else v
                    for k, v in risk_assessment["contextual_risks"].items()
                },
                "technical": risk_assessment["technical_risks"],
            },
            "solution_constraints": MiddleAIPlannerEngine._build_constraints(
                overall_risk, task_context
            ),
        }

        return prompt_data

    @staticmethod
    def _build_constraints(risk_level: float, task_context: Dict[str, str]) -> Dict[str, str]:
        """Build solution constraints based on risk level."""
        constraints = {}

        if risk_level > 0.7:
            constraints["implementation_scope"] = "MINIMAL - MVP only"
            constraints["technology_stack"] = "SIMPLE - avoid complex frameworks"
            constraints["timeline"] = "EXTENDED - allow buffer for issues"
            constraints["team_structure"] = "MINIMAL - single developer or small team"

        elif risk_level > 0.4:
            constraints["implementation_scope"] = "MODERATE - core features + polish"
            constraints["technology_stack"] = "BALANCED - proven frameworks"
            constraints["timeline"] = "REALISTIC - standard estimation"
            constraints["team_structure"] = "SMALL - 2-3 developers"

        else:
            constraints["implementation_scope"] = "FULL - complete feature set"
            constraints["technology_stack"] = "ADVANCED - cutting-edge acceptable"
            constraints["timeline"] = "AGGRESSIVE - fast delivery"
            constraints["team_structure"] = "SCALABLE - multiple teams possible"

        return constraints

    @staticmethod
    def get_user_input_requests(risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify which risk factors need user input for SHARED_CONTROL.
        Returns list of questions for user to refine risk assessment.
        """
        questions = []

        for factor_name, factor_data in risk_assessment.get("contextual_risks", {}).items():
            if isinstance(factor_data, dict) and factor_data.get("requires_user_input"):
                questions.append(
                    {
                        "factor": factor_name,
                        "question": factor_data.get("description", ""),
                        "default_value": factor_data.get("value", 0.5),
                        "scale": "1-10",
                        "importance": "HIGH",
                    }
                )

        return questions

    @staticmethod
    def format_risk_report(
        risk_assessment: Dict[str, Any],
        behavior_analysis: Dict[str, Any],
    ) -> str:
        """Format a human-readable risk assessment report."""
        lines = [
            "\n=== RISK ASSESSMENT REPORT ===\n",
            "Behavioral Analysis:",
        ]

        # Behavioral flags
        for flag_code, flag_msg in behavior_analysis.get("behavioral_flags", []):
            lines.append(f"  ⚠ {flag_code}: {flag_msg}")

        lines.append("\nCalculated Risk Factors:")

        # Overall score
        overall = risk_assessment.get("overall_risk_score", 0.5)
        risk_level = "HIGH (>70%)" if overall > 0.7 else "MEDIUM (40-70%)" if overall > 0.4 else "LOW (<40%)"
        lines.append(f"  Overall Risk: {risk_level}")

        return "\n".join(lines)
