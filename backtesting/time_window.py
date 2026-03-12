"""
Time Window Manager for Backtesting Engine

Manages temporal boundaries, generates time steps, and prevents look-ahead bias
by slicing historical data appropriately.
"""

from typing import List, Tuple
from datetime import datetime, timedelta
from data.schema import PriceData, NewsData
import pandas as pd


class TimeWindowManager:
    """Manages time windows and temporal slicing for backtesting."""
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
        lookback_window: int = 50
    ):
        """
        Initialize time window with backtest parameters.
        
        Args:
            start_date: Start date of backtest period
            end_date: End date of backtest period
            interval: Time interval (1d, 1h, 15m, etc.)
            lookback_window: Number of historical bars agents see (e.g., 50 days for EMA)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.interval = interval
        self.lookback_window = lookback_window
    
    def generate_time_steps(self) -> List[datetime]:
        """
        Generate chronological list of time steps for iteration.
        
        Returns:
            List of datetime objects representing each time step
        """
        # Parse interval to determine frequency
        if self.interval == "1d":
            freq = "D"
        elif self.interval == "1h":
            freq = "H"
        elif self.interval == "15m":
            freq = "15min"
        elif self.interval == "5m":
            freq = "5min"
        else:
            freq = "D"  # Default to daily
        
        # Generate date range using pandas
        time_steps = pd.date_range(
            start=self.start_date,
            end=self.end_date,
            freq=freq
        )
        
        return [ts.to_pydatetime() for ts in time_steps]
    
    def get_historical_slice(
        self,
        current_time: datetime,
        all_prices: List[PriceData],
        all_news: List[NewsData]
    ) -> Tuple[List[PriceData], List[NewsData]]:
        """
        Return data slice up to current_time (prevents look-ahead bias).
        
        This is critical for preventing look-ahead bias - only data with
        timestamp <= current_time is visible to agents.
        
        Args:
            current_time: Current time step in backtest
            all_prices: Complete price history
            all_news: Complete news history
            
        Returns:
            Tuple of (price_slice, news_slice) up to current_time
        """
        # Filter prices up to current time
        price_slice = [
            price for price in all_prices
            if price.timestamp <= current_time
        ]
        
        # Apply lookback window to prices (agents only see recent history)
        if len(price_slice) > self.lookback_window:
            price_slice = price_slice[-self.lookback_window:]
        
        # Filter news up to current time
        news_slice = [
            news for news in all_news
            if news.date <= current_time
        ]
        
        # Limit news to recent window (e.g., last 30 days)
        news_window_days = 30
        news_cutoff = current_time - timedelta(days=news_window_days)
        news_slice = [
            news for news in news_slice
            if news.date >= news_cutoff
        ]
        
        return price_slice, news_slice
    
    def split_walk_forward(
        self,
        train_ratio: float = 0.7
    ) -> List[Tuple[datetime, datetime]]:
        """
        Split time window into training/testing periods for walk-forward analysis.
        
        Args:
            train_ratio: Ratio of training period to total period (0.0 to 1.0)
            
        Returns:
            List of (train_start, train_end, test_start, test_end) tuples
        """
        total_days = (self.end_date - self.start_date).days
        train_days = int(total_days * train_ratio)
        test_days = total_days - train_days
        
        periods = []
        
        # Single walk-forward split for MVP
        train_start = self.start_date
        train_end = self.start_date + timedelta(days=train_days)
        test_start = train_end
        test_end = self.end_date
        
        periods.append((train_start, train_end, test_start, test_end))
        
        return periods
