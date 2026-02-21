from data.price_service import PriceService
from data.news_service import NewsService

def run():
    print("Testing Price Service...")
    prices = PriceService.fetch_price_history("AAPL", period="5d")
    print(f"Fetched {len(prices)} price records. Latest: {prices[-1].close}")

    print("\nTesting News Service...")
    news = NewsService.fetch_news("AAPL", max_items=2)
    for n in news:
        print(f"- {n.title} ({n.date})")

if __name__ == "__main__":
    run()
