from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PriceData(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime

class NewsData(BaseModel):
    title: str
    content: str
    date: datetime
    url: str
    publisher: Optional[str] = None

class NormalizedMarketData(BaseModel):
    symbol: str
    price_history: List[PriceData]
    news: List[NewsData]
