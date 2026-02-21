from data.price_service import PriceService
from agents.technical_agent import TechnicalAgent

def run():
    print("Fetching 100 days of price data for AAPL...")
    prices = PriceService.fetch_price_history("AAPL", period="100d")
    
    print("\nRunning Technical Agent...")
    toon_output = TechnicalAgent.calculate_technical_score(prices)
    print("--- TOON OUTPUT ---")
    print(toon_output)
    print("-------------------")

if __name__ == "__main__":
    run()
