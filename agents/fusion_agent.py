import re
from typing import Dict, Any

class FusionAgent:
    @staticmethod
    def _parse_toon(toon_str: str) -> Dict[str, Any]:
        """Utility to parse TOON string output from agents into a python dictionary."""
        data = {}
        for line in toon_str.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return data

    @staticmethod
    def synthesize(technical_toon: str, event_toon: str, risk_toon: str, market_regime: str = "normal") -> Dict[str, Any]:
        """
        Fuses signals using Regime-Dependent Weights.
        Returns the final trade decision, confidence, and position size.
        """
        tech_data = FusionAgent._parse_toon(technical_toon)
        event_data = FusionAgent._parse_toon(event_toon)
        risk_data = FusionAgent._parse_toon(risk_toon)

        try:
            tech_score = float(tech_data.get('technical_score', 0))
        except ValueError:
            tech_score = 0
            
        try:
            event_score = float(event_data.get('event_score', 0))
        except ValueError:
            event_score = 0
            
        try:
            risk_score = float(risk_data.get('risk_score', 0))
        except ValueError:
            risk_score = 0
        
        # Parse confidence_score from event_toon (new field from Task 3.4)
        try:
            event_confidence = float(event_data.get('confidence_score', 1.0))
        except ValueError:
            event_confidence = 1.0  # Default to full confidence if not present or invalid

        risk_level = risk_data.get('risk_level', 'LOW').upper()

        # Hard Risk Veto
        if risk_level == "CRITICAL":
            return {
                "decision": "NO_TRADE",
                "confidence": 0.0,
                "position_size": 0.0,
                "reason": f"Risk Agent declared CRITICAL risk. Veto enforced. Reasons: {risk_data.get('reason', 'Unknown')}"
            }

        # Dynamic Regime-Dependent Weights
        if market_regime == "earnings":
            base_event_weight = 0.6
            weights = {"technical": 0.3, "event": base_event_weight, "context": 0.1, "risk": 0.4}
        elif market_regime == "volatile":
            base_event_weight = 0.2
            weights = {"technical": 0.4, "event": base_event_weight, "context": 0.1, "risk": 0.6}
        else: # normal
            base_event_weight = 0.2
            weights = {"technical": 0.5, "event": base_event_weight, "context": 0.1, "risk": 0.3}

        # For MVP we don't have context agent yet, we'll allocate its weight to technical
        weights["technical"] += weights.get("context", 0)
        
        # Apply confidence-aware weighting to event signal
        # effective_event_weight = base_event_weight * confidence_score
        # If confidence is low (<0.5), reduce the event signal's influence
        effective_event_weight = weights["event"] * event_confidence
        weights["event"] = effective_event_weight
        
        # We need to map scores to a unified scale [-1, 1] where 1 is strong BUY, -1 is strong SELL
        # Assume tech_score is 0 to 1 (0.5 is neutral)
        # event_score is 0 to 1 (0.5 is neutral)
        
        tech_norm = (tech_score - 0.5) * 2   # maps [0, 1] to [-1, 1]
        event_norm = (event_score - 0.5) * 2

        # Risk always diminishes confidence in the direction of the trade
        # e.g., if we are bullish, high risk reduces the bull score
        base_signal = (tech_norm * weights["technical"]) + (event_norm * weights["event"])
        
        # Apply risk penalty
        if base_signal > 0:
            final_signal = max(0, base_signal - (risk_score * weights["risk"]))
        else:
            final_signal = min(0, base_signal + (risk_score * weights["risk"]))

        confidence = abs(final_signal)

        # Decision Thresholds
        if final_signal >= 0.4:
            decision = "BUY"
        elif final_signal <= -0.4:
            decision = "SELL"
        else:
            decision = "NO_TRADE"
            
        # Position Sizing (fractional fractional)
        # e.g. Max position is 10% of equity. We scale by confidence.
        MAX_ALLOCATION = 0.10
        if decision == "NO_TRADE":
            sz = 0.0
        else:
            sz = round(MAX_ALLOCATION * confidence, 3)

        explanation = (
            f"Regime: {market_regime}. "
            f"Tech Score: {tech_score:.2f}, Event Score: {event_score:.2f}, Event confidence: {event_confidence:.2f}, Risk Penalty: {risk_score:.2f}. "
            f"Final Signal: {final_signal:.3f}. "
            f"Agent Reasons -> Tech: {tech_data.get('reason','')}; Event: {event_data.get('reason','')}; Risk: {risk_data.get('reason','')}"
        )

        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "position_size": sz, # fraction of total equity
            "reason": explanation
        }
