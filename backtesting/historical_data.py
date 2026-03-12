"""
Historical Data Provider for Backtesting Engine

Fetches historical price and news data for specified time ranges,
with caching to minimize API calls.
"""

import yfinance as yf
from typing import List, Optional, Dict
from datetime import datetime
from data.schema import PriceData, NewsData


class HistoricalDataProvider:
    """Provides historical market data with caching support."""
    
    # In-memory cache for historical data
    _cache: Dict[str, Dict] = {}
    
    @staticmethod
    def fetch_historical_prices(
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[PriceData]:
        """
        Fetch historical price data using yfinance.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Time interval (1d, 1h, 15m, etc.)
            
        Returns:
            List of PriceData objects in chronological order
        """
        # Check cache first
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}_{interval}_prices"
        cached_data = HistoricalDataProvider.get_cached_data(cache_key)
        
        if cached_data is not None:
            return [PriceData(**item) for item in cached_data]
        
        # Fetch from yfinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if hist.empty:
            return []
        
        # Convert to PriceData objects
        price_data = []
        for timestamp, row in hist.iterrows():
            price_data.append(PriceData(
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                timestamp=timestamp.to_pydatetime()
            ))
        
        # Cache the results
        cache_data = [item.model_dump() for item in price_data]
        HistoricalDataProvider.cache_data(cache_key, cache_data)
        
        return price_data
    
    @staticmethod
    def fetch_historical_news(
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[NewsData]:
        """
        Fetch historical news data (limited by yfinance availability).
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for historical news
            end_date: End date for historical news
            
        Returns:
            List of NewsData objects in chronological order
        """
        # Check cache first
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}_news"
        cached_data = HistoricalDataProvider.get_cached_data(cache_key)
        
        if cached_data is not None:
            return [NewsData(**item) for item in cached_data]
        
        # Fetch from yfinance (limited historical news availability)
        ticker = yf.Ticker(symbol)
        news_data = []
        
        try:
            news = ticker.news
            if news:
                for article in news:
                    # Parse yfinance news format
                    pub_date = datetime.fromtimestamp(article.get('providerPublishTime', 0))
                    
                    # Filter by date range
                    if start_date <= pub_date <= end_date:
                        news_data.append(NewsData(
                            title=article.get('title', ''),
                            content=article.get('summary', ''),
                            date=pub_date,
                            url=article.get('link', ''),
                            publisher=article.get('publisher', None)
                        ))
        except Exception as e:
            # yfinance news API can be unreliable, return empty list on failure
            print(f"Warning: Failed to fetch news for {symbol}: {e}")
        
        # Sort by date
        news_data.sort(key=lambda x: x.date)
        
        # Cache the results
        cache_data = [item.model_dump() for item in news_data]
        HistoricalDataProvider.cache_data(cache_key, cache_data)
        
        return news_data
    
    @staticmethod
    def get_cached_data(cache_key: str) -> Optional[Dict]:
        """
        Retrieve cached historical data to avoid redundant API calls.
        
        Args:
            cache_key: Unique key for cached data
            
        Returns:
            Cached data if available, None otherwise
        """
        return HistoricalDataProvider._cache.get(cache_key)
    
    @staticmethod
    def cache_data(cache_key: str, data: Dict, ttl: int = 3600):
        """
        Cache historical data with time-to-live.
        
        Args:
            cache_key: Unique key for cached data
            data: Data to cache
            ttl: Time-to-live in seconds (not enforced in MVP)
        """
        HistoricalDataProvider._cache[cache_key] = data
    
    @staticmethod
    def clear_cache():
        """Clear all cached data."""
        HistoricalDataProvider._cache.clear()
