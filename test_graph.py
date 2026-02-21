from agents.graph import alphamind_graph

def run():
    print("Initializing AlphaMind AI LangGraph Pipeline...\n")
    
    initial_state = {
        "symbol": "NVDA",
        "market_regime": "volatile"
    }

    # Run the compiled LangGraph app.
    # If Ollama/models are unavailable, EventAgent degrades gracefully in the pipeline.
    result = alphamind_graph.invoke(initial_state)
    
    print("\n--- LangGraph Pipeline Completed ---")
    print(f"Final Decision: {result['decision_data']['decision']}")
    print(f"Confidence: {result['decision_data']['confidence']}")
    print(f"Reason: {result['decision_data']['reason']}")
    
    trade = result.get('trade_executed')
    if trade:
        print(f"\nTrade Executed: {trade.action} @ {trade.fill_price:.2f} (SL: {trade.stop_loss:.2f}, TG: {trade.target:.2f})")

if __name__ == "__main__":
    run()
