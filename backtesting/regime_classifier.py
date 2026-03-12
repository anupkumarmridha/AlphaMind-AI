"""
Regime Classifier for Backtesting Engine

Classifies market periods into different regimes (normal, volatile, trending, earnings)
for regime-specific performance analysis.
"""

from typing import List
from datetime import datetime, timedelta
import numpy as np

from data.schema import PriceData


class RegimeClassifier:
    """Classifies market periods into different regimes."""
    
    @staticmethod
    def classify_regime(
        prices: List[PriceData],
        timestamp: datetime,
        lookback_days: int = 20
    ) -> str:
        """
        Classify time period into market regime.
        
        Args:
            prices: Historical price data
            timestamp: Current timestamp to classify
            lookback_days: Number of days to look back for classification
            
        Returns:
            Regime name: "normal", "volatile", "trending", or "earnings"
        """
        # Filter prices within lookback window
        cutoff = timestamp - timedelta(days=lookback_days)
        recent_prices = [p for p in prices if cutoff <= p.timestamp <= timestamp]
        
        if len(recent_prices) < 5:
            return "normal"
        
        # Calculate volatility (standard deviation of returns)
        closes = [p.close for p in recent_prices]
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns)
        
        # Calculate trend strength (linear regression slope)
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        trend_strength = abs(slope / closes[0])  # Normalized slope
        
        # Check for earnings (volume spike)
        volumes = [p.volume for p in recent_prices]
        avg_volume = np.mean(volumes[:-1]) if len(volumes) > 1 else volumes[0]
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Classification logic
        if volume_ratio > 3.0:
            return "earnings"
        elif volatility > 0.03:  # 3% daily volatility threshold
            return "volatile"
        elif trend_strength > 0.02:  # 2% trend strength threshold
            return "trending"
        else:
            return "normal"
