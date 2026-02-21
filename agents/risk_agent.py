import pandas as pd
from typing import List
from data.schema import PriceData

class RiskAgent:
    @staticmethod
    def analyze_risk(price_history: List[PriceData]) -> str:
        """
        Calculates risk conditions.
        Outputs TOON format and checks for hard risk veto.
        """
        if len(price_history) < 14:
            return "risk_score: 0.0\nrisk_level: low\nreason: insufficient data for risk analysis\n"

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
        
        risk_score = 0.3 # Base risk
        risk_level = "LOW"
        reasons = []
        is_critical = False

        rsi = latest['RSI_14']
        vol = latest['Volatility_14']
        
        if pd.isna(rsi) or pd.isna(vol):
             return "risk_score: 0.0\nrisk_level: low\nreason: not enough data to compute indicators\n"

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

        risk_score = min(1.0, risk_score)
        
        if is_critical or risk_score >= 0.8:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"

        # Output in TOON format
        result = f"""risk_score: {risk_score:.2f}
risk_level: {risk_level}
reason: {', '.join(reasons) if reasons else 'Normal conditions'}
"""
        return result
