from data.news_service import NewsService
from agents.event_agent import EventAgent

def run():
    print("Fetching news for AAPL...")
    news = NewsService.fetch_news("AAPL", max_items=3)
    
    print("Ensure your local Ollama is running and required models are available.")
    print("Optional env vars: OLLAMA_BASE_URL, OLLAMA_MODEL, EVENT_TRIAGE_MODEL, EVENT_EXTRACT_MODEL.")
    
    agent = EventAgent()
    print("\nRunning Event Agent...")
    toon_output = agent.analyze_news(news)
    print("--- TOON OUTPUT ---")
    print(toon_output)
    print("-------------------")

if __name__ == "__main__":
    run()
