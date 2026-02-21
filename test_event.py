import os
from data.news_service import NewsService
from agents.event_agent import EventAgent

def run():
    print("Fetching news for AAPL...")
    news = NewsService.fetch_news("AAPL", max_items=3)
    
    if not os.getenv("OPENAI_API_KEY"):
         print("No OPENAI_API_KEY found in environment. The LLM calls will fail.")
         print("Export OPENAI_API_KEY='your_key' to test the actual LangChain inference.")
    
    agent = EventAgent()
    print("\nRunning Event Agent...")
    toon_output = agent.analyze_news(news)
    print("--- TOON OUTPUT ---")
    print(toon_output)
    print("-------------------")

if __name__ == "__main__":
    run()
