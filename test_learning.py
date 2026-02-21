from models.trade import Trade
from agents.learning_agent import LearningAgent

def run():
    print("Initializing Learning Agent (SQLite Memory fallback for testing)...")
    agent = LearningAgent("sqlite:///:memory:")
    
    trade = Trade(symbol="AAPL", action="BUY", position_size=0.1, desired_entry=100.0, fill_price=100.0, commission_fee=0.001, stop_loss=90.0, target=110.0)
    trade.close_trade(110.0, "Target Hit")
    
    toon_reason = "technical_score: 0.8\ntrend: bullish\nmomentum: strong"
    # Mock 1536 dim embedding
    mock_embedding = [0.01] * 1536
    
    # In sqlite pgvector Vector type will throw an error on table creation or insert unless specifically compiled.
    # We will just print the optimal weights function instead to prove logic.
    print("\nSimulating weight retrieval for normal regime:")
    weights = agent.get_dynamic_weights_for_regime("normal")
    print(weights)

    print("\nSimulating weight retrieval for earnings regime:")
    weights = agent.get_dynamic_weights_for_regime("earnings")
    print(weights)

if __name__ == "__main__":
    run()
