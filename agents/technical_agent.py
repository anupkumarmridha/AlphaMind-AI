import pandas as pd
from typing import Any, Dict, List
from data.schema import PriceData

class TechnicalAgent:
    @staticmethod
    def analyze(price_history: List[PriceData]) -> Dict[str, Any]:
        if len(price_history) < 50:
            return {
                "technical_score": 0.0,
                "trend": "neutral",
                "momentum": "unknown",
                "reason": "insufficient data",
            }

        df = pd.DataFrame([p.model_dump() for p in price_history])
        df.set_index('timestamp', inplace=True)
        
        # Calculate EMA 20 and 50
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Calculate RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # Calculate Volume Trend (simple 5-day avg vs 20-day avg)
        df['Vol_5'] = df['volume'].rolling(window=5).mean()
        df['Vol_20'] = df['volume'].rolling(window=20).mean()

        latest = df.iloc[-1]
        
        # Logic
        score = 0.5
        trend = "neutral"
        momentum = "neutral"
        reasons = []

        if latest['EMA_20'] > latest['EMA_50']:
            score += 0.2
            trend = "bullish"
            reasons.append("EMA20 > EMA50")
        else:
            score -= 0.2
            trend = "bearish"
            reasons.append("EMA20 < EMA50")
            
        if latest['RSI_14'] > 60:
            score += 0.1
            momentum = "strong"
            reasons.append(f"RSI={latest['RSI_14']:.1f} (Bullish)")
        elif latest['RSI_14'] < 40:
            score -= 0.1
            momentum = "weak"
            reasons.append(f"RSI={latest['RSI_14']:.1f} (Bearish)")
        else:
            reasons.append(f"RSI={latest['RSI_14']:.1f} (Neutral)")

        if latest['Vol_5'] > latest['Vol_20']:
            score += 0.1
            reasons.append("Volume rising")
        else:
            score -= 0.1
            reasons.append("Volume falling")

        score = max(0.0, min(1.0, score)) # clamp between 0 and 1
        
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
        """
        Backward-compatible TOON output helper.
        """
        return TechnicalAgent.to_toon(TechnicalAgent.analyze(price_history))
