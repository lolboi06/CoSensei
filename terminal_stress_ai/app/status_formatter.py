"""
Formats CoSensei status information for terminal display.
Shows trust, risk, and autonomy mode at every response.
"""
from __future__ import annotations

from typing import Dict, Any, Optional


class StatusFormatter:
    """Formats CoSensei metrics for display."""

    @staticmethod
    def format_status_line(
        trust_score: float,
        risk_level: float,
        autonomy_mode: str,
        timestamp: Optional[str] = None,
    ) -> str:
        """Format single-line status summary."""
        trust_level = StatusFormatter.score_to_level(trust_score)
        risk_indicator = StatusFormatter.get_risk_indicator(risk_level)
        
        return (
            f"Status: "
            f"trust={trust_level}({trust_score:.2f}) "
            f"risk={risk_indicator}({risk_level:.2f}) "
            f"mode={autonomy_mode}"
        )

    @staticmethod
    def format_status_block(
        scores: Dict[str, Any],
        fused_trust: Dict[str, Any],
        risk_severity_scores: Dict[str, float],
        autonomy_mode: str,
        shared_autonomy: Dict[str, Any],
    ) -> str:
        """Format detailed status block."""
        lines = [
            "=" * 60,
            "COSENSEI STATUS",
            "=" * 60,
        ]
        
        # Trust metrics
        trust_score = float(fused_trust.get("score", 0.0))
        trust_level = StatusFormatter.score_to_level(trust_score)
        lines.append(f"Trust:       {trust_level:<8} ({trust_score:.3f})")
        
        # Stress and cognitive load
        stress_score = float(scores.get("stress", {}).get("score", 0.0))
        stress_level = StatusFormatter.score_to_level(stress_score)
        load_score = float(scores.get("cognitive_load", {}).get("score", 0.0))
        load_level = StatusFormatter.score_to_level(load_score)
        
        lines.append(f"Stress:      {stress_level:<8} ({stress_score:.3f})")
        lines.append(f"Cognitive:   {load_level:<8} ({load_score:.3f})")
        
        # Risk summary
        max_risk = max(risk_severity_scores.values()) if risk_severity_scores else 0.0
        risk_indicator = StatusFormatter.get_risk_indicator(max_risk)
        lines.append(f"Risk:        {risk_indicator:<8} ({max_risk:.3f})")
        
        # Autonomy mode
        lines.append(f"Autonomy:    {autonomy_mode:<8}")
        
        # Shared autonomy score
        autonomy_score = float(shared_autonomy.get("autonomy_score", 0.0))
        lines.append(f"Autonomy Score: {autonomy_score:.3f}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)

    @staticmethod
    def score_to_level(score: float) -> str:
        """Convert numeric score to text level."""
        if score < 0.33:
            return "LOW"
        elif score < 0.66:
            return "MED"
        else:
            return "HIGH"

    @staticmethod
    def get_risk_indicator(risk_level: float) -> str:
        """Get risk indicator symbol and level."""
        if risk_level < 0.3:
            return "✓ SAFE"
        elif risk_level < 0.6:
            return "⚠ WARN"
        else:
            return "✗ CRIT"

    @staticmethod
    def format_inline_status(trust_score: float, risk_level: float, autonomy_mode: str) -> str:
        """Format status for inline display in responses."""
        return f"\n[Status: trust={trust_score:.2f} | risk={risk_level:.2f} | mode={autonomy_mode}]"

    @staticmethod
    def format_action_recommendation(shared_autonomy: Dict[str, Any], action_manager: Dict[str, Any]) -> str:
        """Format action recommendation based on autonomy decision."""
        mode = shared_autonomy.get("autonomy_mode", "SHARED_CONTROL")
        reason = shared_autonomy.get("reason", "Standard operation")
        
        recommendations = {
            "AI_FULL": "✓ AI can execute the suggestion automatically.",
            "AI_ASSIST": "◆ AI will assist; you review and approve.",
            "SHARED_CONTROL": "◇ Shared control mode; high interaction expected.",
            "HUMAN_CONTROL": "⊗ Human approval required before execution.",
        }
        
        return recommendations.get(mode, f"Mode: {mode}")

    @staticmethod
    def format_trust_explanation(fused_trust: Dict[str, Any], trust_signals: Dict[str, Any]) -> str:
        """Explain trust score in human-readable terms."""
        trust_score = float(fused_trust.get("score", 0.0))
        
        if trust_score >= 0.8:
            return "Trust is high. System is confident in current recommendations."
        elif trust_score >= 0.6:
            return "Trust is moderate. System will verify recommendations before action."
        elif trust_score >= 0.4:
            return "Trust is low. Increased oversight required."
        else:
            return "Trust is very low. Human approval required for all actions."

    @staticmethod
    def format_session_summary(
        session_id: str,
        event_count: int,
        trust_score: float,
        conversation_turns: int,
        clarifications_asked: int,
    ) -> str:
        """Format session summary for display."""
        lines = [
            f"\nSession: {session_id}",
            f"Events: {event_count} | Turns: {conversation_turns}",
            f"Trust: {trust_score:.3f} | Clarifications: {clarifications_asked}",
        ]
        return " | ".join(lines)
