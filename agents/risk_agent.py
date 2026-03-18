import logging
import pandas as pd
from typing import Any, Dict, List
from data.schema import PriceData

logger = logging.getLogger(__name__)


class RiskAgent:
    @staticmethod
    def _detect_extreme_conditions(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect extreme market conditions: high volatility, price gaps, volume spikes."""
        conditions = []
        flags = {
            "extreme_volatility": False,
            "price_gap": False,
            "volume_spike": False,
        }

        # Check volatility > 10% daily swing
        returns = df['close'].pct_change().abs()
        if returns.max() > 0.10:
            flags["extreme_volatility"] = True
            conditions.append(f"extreme volatility detected ({returns.max():.1%} daily swing)")

        # Check price gaps > 5% between consecutive closes
        if 'open' in df.columns:
            gaps = ((df['open'] - df['close'].shift(1)) / df['close'].shift(1)).abs()
            max_gap = gaps.max()
            if max_gap > 0.05:
                flags["price_gap"] = True
                conditions.append(f"price gap detected ({max_gap:.1%})")

        # Check volume spikes > 3x average volume
        if 'volume' in df.columns and df['volume'].mean() > 0:
            avg_vol = df['volume'].mean()
            max_vol = df['volume'].max()
            if max_vol > 3 * avg_vol:
                flags["volume_spike"] = True
                conditions.append(f"volume spike detected ({max_vol / avg_vol:.1f}x average)")

        return {"flags": flags, "conditions": conditions}

    @staticmethod
    def _get_risk_thresholds(market_regime: str) -> Dict[str, float]:
        """Return risk level thresholds based on market regime."""
        regimes = {
            "normal":   {"LOW": 0.3, "MEDIUM": 0.5, "HIGH": 0.8},
            "earnings": {"LOW": 0.2, "MEDIUM": 0.4, "HIGH": 0.6},
            "volatile": {"LOW": 0.4, "MEDIUM": 0.6, "HIGH": 0.9},
        }
        return regimes.get(market_regime, regimes["normal"])

    @staticmethod
    def analyze(price_history: List[PriceData], market_regime: str = "normal") -> Dict[str, Any]:
        """
        Calculates risk conditions as structured data.
        """
        if len(price_history) < 14:
            return {
                "risk_score": 0.0,
                "risk_level": "LOW",
                "reason": f"insufficient data: need at least 14 points, got {len(price_history)}",
            }

        df = pd.DataFrame([p.model_dump() for p in price_history])
        df.set_index('timestamp', inplace=True)

        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # Calculate Volatility (Standard Deviation of returns)
        df['Returns'] = df['close'].pct_change()
        df['Volatility_14'] = df['Returns'].rolling(window=14).std()

        latest = df.iloc[-1]

        risk_score = 0.3  # Base risk
        risk_level = "LOW"
        reasons = []
        is_critical = False

        rsi = latest['RSI_14']
        vol = latest['Volatility_14']

        # Gap risk analysis (run before NaN check so gaps are always captured)
        if 'open' in df.columns:
            df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
            recent_gaps = df['gap'].tail(14).abs()
            max_gap = recent_gaps.max()
            if not pd.isna(max_gap) and max_gap > 0.03:
                risk_score += 0.2
                reasons.append(f"gap risk detected ({max_gap:.1%} max gap)")

        if pd.isna(rsi) or pd.isna(vol):
            logger.warning(
                f"Risk calculation produced NaN: RSI={rsi}, Vol={vol}, data_points={len(df)}"
            )
            # Still return gap/extreme info if we have it
            if reasons:
                risk_score = min(1.0, risk_score)
                thresholds = RiskAgent._get_risk_thresholds(market_regime)
                if risk_score >= thresholds["HIGH"]:
                    risk_level = "CRITICAL"
                elif risk_score >= thresholds["MEDIUM"]:
                    risk_level = "HIGH"
                elif risk_score >= thresholds["LOW"]:
                    risk_level = "MEDIUM"
                return {
                    "risk_score": round(risk_score, 2),
                    "risk_level": risk_level,
                    "reason": ", ".join(reasons),
                }
            return {
                "risk_score": 0.0,
                "risk_level": "LOW",
                "reason": "not enough data to compute indicators",
            }

        # Extreme RSI checks
        if rsi > 80:
            risk_score += 0.4
            reasons.append(f"RSI critically overbought ({rsi:.1f})")
            is_critical = True
        elif rsi > 70:
            risk_score += 0.2
            reasons.append(f"RSI overbought ({rsi:.1f})")

        if rsi < 20:
            risk_score += 0.4
            reasons.append(f"RSI critically oversold ({rsi:.1f})")
            is_critical = True
        elif rsi < 30:
            risk_score += 0.2
            reasons.append(f"RSI oversold ({rsi:.1f})")

        # Extreme Volatility (more than 5% daily swing standard deviation)
        if vol > 0.05:
            risk_score += 0.5
            reasons.append(f"Extreme volatility detected ({vol:.2%})")
            is_critical = True
        elif vol > 0.02:
            risk_score += 0.2
            reasons.append(f"High volatility ({vol:.2%})")

        # Detect extreme conditions (flash crashes, volume spikes, large gaps)
        extreme = RiskAgent._detect_extreme_conditions(df)
        for condition in extreme["conditions"]:
            if condition not in reasons:
                reasons.append(condition)

        risk_score = min(1.0, risk_score)

        # Apply regime-specific thresholds
        thresholds = RiskAgent._get_risk_thresholds(market_regime)
        if is_critical or risk_score >= thresholds["HIGH"]:
            risk_level = "CRITICAL"
        elif risk_score >= thresholds["MEDIUM"]:
            risk_level = "HIGH"
        elif risk_score >= thresholds["LOW"]:
            risk_level = "MEDIUM"

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "reason": ", ".join(reasons) if reasons else "Normal conditions",
        }

    @staticmethod
    def to_toon(payload: Dict[str, Any]) -> str:
        return (
            f"risk_score: {payload.get('risk_score', 0.0)}\n"
            f"risk_level: {payload.get('risk_level', 'LOW')}\n"
            f"reason: {payload.get('reason', '')}\n"
        )

    @staticmethod
    def analyze_risk(price_history: List[PriceData]) -> str:
        """
        Backward-compatible TOON output helper.
        """
        return RiskAgent.to_toon(RiskAgent.analyze(price_history))
