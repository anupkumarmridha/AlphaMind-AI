import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


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
    def _validate_and_normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        """Validate and normalize weights so they sum to 1.0."""
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Weights sum to {total:.4f} (not 1.0), normalizing: {weights}"
            )
            weights = {k: v / total for k, v in weights.items()}
        return weights

    @staticmethod
    def _validate_toon_data(
        data: Dict, required_fields: List[str], source: str
    ) -> Dict:
        """Validate TOON data fields, log warnings for missing/malformed fields."""
        validated = dict(data)
        for field in required_fields:
            if field not in data or data[field] == '':
                default = 0 if field.endswith('_score') or field.endswith('_confidence') else 'unknown'
                logger.warning(
                    f"[{source}] Missing or empty field '{field}', defaulting to {default!r}"
                )
                validated[field] = default
        return validated

    @staticmethod
    def synthesize(
        technical_toon: str,
        event_toon: str,
        risk_toon: str,
        market_regime: str = "normal",
        context=None,
        dynamic_weights=None,
    ) -> Dict[str, Any]:
        """
        Fuses signals using Regime-Dependent Weights.
        Returns the final trade decision, confidence, and position size.
        """
        tech_data = FusionAgent._parse_toon(technical_toon)
        event_data = FusionAgent._parse_toon(event_toon)
        risk_data = FusionAgent._parse_toon(risk_toon)

        # Validate required fields in each TOON
        tech_data = FusionAgent._validate_toon_data(
            tech_data, ["technical_score"], "technical_toon"
        )
        event_data = FusionAgent._validate_toon_data(
            event_data, ["event_score", "confidence_score"], "event_toon"
        )
        risk_data = FusionAgent._validate_toon_data(
            risk_data, ["risk_score", "risk_level"], "risk_toon"
        )

        # 5.1 Parse scores with logging on error
        try:
            tech_score = float(tech_data.get('technical_score', 0))
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse technical_score: {tech_data.get('technical_score')} - {e}"
            )
            tech_score = 0

        try:
            event_score = float(event_data.get('event_score', 0))
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse event_score: {event_data.get('event_score')} - {e}"
            )
            event_score = 0

        try:
            risk_score = float(risk_data.get('risk_score', 0))
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse risk_score: {risk_data.get('risk_score')} - {e}"
            )
            risk_score = 0

        # Parse confidence_score from event_toon (new field from Task 3.4)
        try:
            event_confidence = float(event_data.get('confidence_score', 1.0))
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Failed to parse event_confidence: {event_data.get('confidence_score')} - {e}"
            )
            event_confidence = 1.0

        risk_level = risk_data.get('risk_level', 'LOW')
        if isinstance(risk_level, str):
            risk_level = risk_level.upper()
        else:
            risk_level = 'LOW'

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
        else:  # normal
            base_event_weight = 0.2
            weights = {"technical": 0.5, "event": base_event_weight, "context": 0.1, "risk": 0.3}

        # 5.3 Context agent not yet implemented in MVP, redistribute its weight to technical
        # This maintains total weight sum while giving technical agent more influence
        weights["technical"] += weights.get("context", 0)
        del weights["context"]
        weights = FusionAgent._validate_and_normalize_weights(weights)

        # Apply confidence-aware weighting to event signal
        # effective_event_weight = base_event_weight * confidence_score
        # If confidence is low (<0.5), reduce the event signal's influence
        effective_event_weight = weights["event"] * event_confidence
        weights["event"] = effective_event_weight

        # 5.6 Validate and normalize weights after confidence adjustment
        weights = FusionAgent._validate_and_normalize_weights(weights)

        # Map scores to unified scale [-1, 1] where 1 is strong BUY, -1 is strong SELL
        # tech_score is 0 to 1 (0.5 is neutral)
        # event_score is 0 to 1 (0.5 is neutral)
        tech_norm = (tech_score - 0.5) * 2   # maps [0, 1] to [-1, 1]
        event_norm = (event_score - 0.5) * 2

        # Risk always diminishes confidence in the direction of the trade
        base_signal = (tech_norm * weights["technical"]) + (event_norm * weights["event"])

        # Apply risk penalty
        if base_signal > 0:
            final_signal = max(0, base_signal - (risk_score * weights["risk"]))
        else:
            final_signal = min(0, base_signal + (risk_score * weights["risk"]))

        # 5.5 Bounds check final_signal to [-1, 1]
        if final_signal > 1.0 or final_signal < -1.0:
            logger.warning(f"final_signal {final_signal:.3f} out of [-1, 1], clamping")
        final_signal = max(-1.0, min(1.0, final_signal))

        confidence = abs(final_signal)

        # Decision Thresholds
        if final_signal >= 0.4:
            decision = "BUY"
        elif final_signal <= -0.4:
            decision = "SELL"
        else:
            decision = "NO_TRADE"

        # Position Sizing (fractional)
        # Max position is 10% of equity. We scale by confidence.
        MAX_ALLOCATION = 0.10
        if decision == "NO_TRADE":
            sz = 0.0
        else:
            sz = round(MAX_ALLOCATION * confidence, 3)

        explanation = (
            f"Regime: {market_regime}. "
            f"Tech Score: {tech_score:.2f}, Event Score: {event_score:.2f}, "
            f"Event confidence: {event_confidence:.2f}, Risk Penalty: {risk_score:.2f}. "
            f"Final Signal: {final_signal:.3f}. "
            f"Agent Reasons -> Tech: {tech_data.get('reason', '')}; "
            f"Event: {event_data.get('reason', '')}; Risk: {risk_data.get('reason', '')}"
        )

        return {
            "decision": decision,
            "confidence": round(confidence, 3),
            "position_size": sz,  # fraction of total equity
            "reason": explanation
        }
