from data.price_service import PriceService
from agents.risk_agent import RiskAgent

def run():
    print("Fetching 50 days of price data for TSLA...")
    prices = PriceService.fetch_price_history("TSLA", period="50d")
    
    print("\nRunning Risk Agent...")
    toon_output = RiskAgent.analyze_risk(prices)
    print("--- TOON OUTPUT ---")
    print(toon_output)
    print("-------------------")

if __name__ == "__main__":
    run()
