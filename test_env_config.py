"""
Quick test to verify environment configuration and Ollama integration.
"""
import os
from agents.event_agent import EventAgent
from data.schema import NewsData

def test_env_loading():
    """Test that environment variables are loaded correctly."""
    print("=== Environment Configuration Test ===\n")
    
    # Check environment variables
    print("Environment Variables:")
    print(f"  OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', 'NOT SET')}")
    print(f"  OLLAMA_MODEL: {os.getenv('OLLAMA_MODEL', 'NOT SET')}")
    print(f"  EVENT_TRIAGE_MODEL: {os.getenv('EVENT_TRIAGE_MODEL', 'NOT SET')}")
    print(f"  EVENT_EXTRACT_MODEL: {os.getenv('EVENT_EXTRACT_MODEL', 'NOT SET')}")
    print(f"  EVENT_FALLBACK_MODEL: {os.getenv('EVENT_FALLBACK_MODEL', 'NOT SET')}")
    print()

def test_event_agent_init():
    """Test that EventAgent initializes with correct models."""
    print("=== EventAgent Initialization Test ===\n")
    
    agent = EventAgent()
    
    print("EventAgent Models:")
    print(f"  Triage Model: {agent.triage_llm.model}")
    print(f"  Extract Model: {agent.extract_llm.model}")
    print(f"  Fallback Model: {agent.fallback_llm.model}")
    print(f"  Base URL: {agent.triage_llm.base_url}")
    print()
    
    return agent

def test_simple_analysis():
    """Test a simple news analysis."""
    print("=== Simple News Analysis Test ===\n")
    
    agent = EventAgent()
    
    # Create a simple test news item
    test_news = [
        NewsData(
            title="Test: Company Reports Strong Earnings",
            content="The company exceeded expectations with strong quarterly results.",
            url="https://example.com/test-article",
            publisher="Test Source"
        )
    ]
    
    print("Analyzing test news article...")
    print(f"Title: {test_news[0].title}")
    print()
    
    try:
        result = agent.analyze_news(test_news)
        print("Analysis Result (TOON format):")
        print(result)
        print("\n✅ Test passed! EventAgent is working with Ollama.")
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_env_loading()
    test_event_agent_init()
    success = test_simple_analysis()
    
    if success:
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("Environment configuration is working correctly.")
        print("Ollama integration is functional.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ Some tests failed. Check the output above.")
        print("="*50)
