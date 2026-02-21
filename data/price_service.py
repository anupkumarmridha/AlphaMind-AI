import yfinance as yf
from datetime import datetime
from typing import List
from data.schema import PriceData

class PriceService:
    @staticmethod
    def fetch_price_history(symbol: str, period: str = "1mo", interval: str = "1d") -> List[PriceData]:
        """
        Fetch historical price data for a symbol using yfinance.
        """
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        
        price_data_list = []
        for index, row in history.iterrows():
            price_data = PriceData(
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                timestamp=index.to_pydatetime()
            )
            price_data_list.append(price_data)
            
        return price_data_list
