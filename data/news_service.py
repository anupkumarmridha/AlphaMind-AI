import yfinance as yf
from datetime import datetime
from typing import List
from data.schema import NewsData

class NewsService:
    @staticmethod
    def fetch_news(symbol: str, max_items: int = 10) -> List[NewsData]:
        """
        Fetch recent news articles for a symbol using yfinance.
        """
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
        except Exception:
            return []
        
        news_data_list = []
        for item in raw_news[:max_items]:
            # yfinance news format can vary, gracefully extracting fields
            title = item.get('title', '')
            content = item.get('summary', '') or title # Fallback to title if summary is missing
            url = item.get('link', '')
            publisher = item.get('publisher', '')
            
            # Convert timestamp to datetime; keep missing values as None.
            pub_date = item.get('providerPublishTime')
            if pub_date:
                date_obj = datetime.fromtimestamp(pub_date)
            else:
                date_obj = None
                
            news_data_list.append(NewsData(
                title=title,
                content=content,
                date=date_obj,
                url=url,
                publisher=publisher
            ))
            
        return news_data_list
