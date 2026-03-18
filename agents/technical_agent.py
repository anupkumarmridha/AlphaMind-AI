import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple
from data.schema import PriceData

logger = logging.getLogger(__name__)


class TechnicalAgent:

    @staticmethod
    def _validate_price_history(price_history: List[PriceData]) -> Tuple[bool, str]:
        """Validate price history before calculations."""
        if len(price_history) < 50:
            return False, f"insufficient data: need at least 50 points, got {len(price_history)}"

        closes = [p.close for p in price_history]

        # Check for all-zero close prices
        if all(c == 0.0 for c in closes):
            return False, "invalid data: all close prices are zero"

        # Check for NaN or inf in any field
        for i, p in enumerate(price_history):
            for field, val in [("close", p.close), ("open", p.open),
                                ("high", p.high), ("low", p.low)]:
                if pd.isna(val) or np.isinf(val):
                    return False, f"invalid data: {field} at index {i} is NaN/inf"

        return True, ""

    @staticmethod
    def _safe_divide(num: float, denom: float, default: float = 0.0) -> float:
        """Divide safely, returning default if denominator is near zero."""
        if abs(denom) < 1e-10:
            return default
        result = num / denom
        if pd.isna(result) or np.isinf(result):
            return default
        return result

    @staticmethod
    def _is_valid_number(value) -> bool:
        """Return True if value is a finite, non-NaN number."""
        try:
            return not (pd.isna(value) or np.isinf(value))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def analyze(price_history: List[PriceData]) -> Dict[str, Any]:
        # --- Input validation ---
        is_valid, error_msg = TechnicalAgent._validate_price_history(price_history)
        if not is_valid:
            return {
                "technical_score": 0.0,
                "trend": "neutral",
                "momentum": "unknown",
                "reason": error_msg,
            }

        df = pd.DataFrame([p.model_dump() for p in price_history])
        df.set_index('timestamp', inplace=True)

        # Calculate EMA 20 and 50
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()

        # Calculate RSI 14 with safe division
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

        # Check if the latest gain and loss are both effectively zero (flat prices → RSI undefined)
        latest_gain = gain.iloc[-1]
        latest_loss = loss.iloc[-1]
        gain_is_nan = pd.isna(latest_gain)
        loss_is_nan = pd.isna(latest_loss)
        gain_is_zero = gain_is_nan or abs(float(latest_gain)) < 1e-10
        loss_is_zero = loss_is_nan or abs(float(latest_loss)) < 1e-10

        if gain_is_zero and loss_is_zero:
            # Both gain and loss are zero/NaN → RSI is undefined (NaN in raw formula)
            logger.warning(
                "TechnicalAgent: RSI is NaN/undefined (flat price history, gain=0, loss=0)"
            )
            return {
                "technical_score": 0.0,
                "trend": "neutral",
                "momentum": "unknown",
                "reason": "invalid indicator: RSI is nan (flat price history, no price variation)",
            }

        def safe_rsi(g, l):
            # Handle NaN inputs from rolling window (insufficient data)
            if pd.isna(g) or pd.isna(l):
                return 50.0
            if abs(l) < 1e-10:
                # loss=0: if gain>0 → RSI=100 (max bullish), else RSI=50 (neutral)
                return 100.0 if g > 1e-10 else 50.0
            rs = g / l
            rsi = 100 - (100 / (1 + rs))
            if pd.isna(rsi) or np.isinf(rsi):
                return 50.0
            return rsi

        df['RSI_14'] = [safe_rsi(g, l) for g, l in zip(gain, loss)]

        # Calculate Volume Trend (simple 5-day avg vs 20-day avg)
        df['Vol_5'] = df['volume'].rolling(window=5).mean()
        df['Vol_20'] = df['volume'].rolling(window=20).mean()

        latest = df.iloc[-1]

        # --- Post-calculation validation ---
        for indicator in ('EMA_20', 'EMA_50', 'RSI_14'):
            val = latest[indicator]
            if not TechnicalAgent._is_valid_number(val):
                logger.warning(
                    "TechnicalAgent: indicator %s is invalid (%s) for last row",
                    indicator, val
                )
                return {
                    "technical_score": 0.0,
                    "trend": "neutral",
                    "momentum": "unknown",
                    "reason": f"invalid indicator: {indicator} is NaN/inf",
                }

        # Validate RSI is in [0, 100]
        rsi_val = float(latest['RSI_14'])
        rsi_val = max(0.0, min(100.0, rsi_val))

        # --- Scoring logic ---
        score = 0.5
        trend = "neutral"
        momentum = "neutral"
        reasons = []

        ema20 = latest['EMA_20']
        ema50 = latest['EMA_50']

        if TechnicalAgent._is_valid_number(ema20) and TechnicalAgent._is_valid_number(ema50):
            if ema20 > ema50:
                score += 0.2
                trend = "bullish"
                reasons.append("EMA20 > EMA50")
            else:
                score -= 0.2
                trend = "bearish"
                reasons.append("EMA20 < EMA50")
        else:
            reasons.append("EMA indicators invalid")

        if rsi_val > 60:
            score += 0.1
            momentum = "strong"
            reasons.append(f"RSI={rsi_val:.1f} (Bullish)")
        elif rsi_val < 40:
            score -= 0.1
            momentum = "weak"
            reasons.append(f"RSI={rsi_val:.1f} (Bearish)")
        else:
            reasons.append(f"RSI={rsi_val:.1f} (Neutral)")

        # --- Volume validation ---
        all_zero_volume = all(p.volume == 0 for p in price_history)
        if all_zero_volume:
            logger.warning("TechnicalAgent: all volume values are zero, skipping volume scoring")
            reasons.append("volume data unavailable")
        else:
            vol5 = latest['Vol_5']
            vol20 = latest['Vol_20']
            if TechnicalAgent._is_valid_number(vol5) and TechnicalAgent._is_valid_number(vol20):
                if vol5 > vol20:
                    score += 0.1
                    reasons.append("Volume rising")
                else:
                    score -= 0.1
                    reasons.append("Volume falling")
            else:
                reasons.append("volume data unavailable")

        # Clamp score to [0.0, 1.0]
        score = max(0.0, min(1.0, score))

        # Final bounds assertion
        assert TechnicalAgent._is_valid_number(score), f"Final score is invalid: {score}"

        return {
            "technical_score": round(score, 2),
            "trend": trend,
            "momentum": momentum,
            "reason": ", ".join(reasons),
        }

    @staticmethod
    def to_toon(payload: Dict[str, Any]) -> str:
        return (
            f"technical_score: {payload.get('technical_score', 0.0)}\n"
            f"trend: {payload.get('trend', 'neutral')}\n"
            f"momentum: {payload.get('momentum', 'unknown')}\n"
            f"reason: {payload.get('reason', '')}\n"
        )

    @staticmethod
    def calculate_technical_score(price_history: List[PriceData]) -> str:
        """Backward-compatible TOON output helper."""
        return TechnicalAgent.to_toon(TechnicalAgent.analyze(price_history))
