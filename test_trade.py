from agents.trade_agent import TradeAgent

def run():
    agent = TradeAgent()
    
    fusion_output = {
        "decision": "BUY",
        "confidence": 0.8,
        "position_size": 0.08,
        "reason": "Strong technicals"
    }
    
    print("Executing Trade at 100.0...")
    trade = agent.execute_trade(fusion_output, current_price=100.0, symbol="AAPL")
    
    print(f"Trade details:\n  Action: {trade.action}\n  Desired: {trade.desired_entry}\n  Filled: {trade.fill_price:.4f}\n  SL: {trade.stop_loss:.4f}\n  Target: {trade.target:.4f}")
    
    print("\nSimulating market movement...")
    # Simulate price going up to hit target
    agent.monitor_trades(102.0)
    print(f"Open trades: {len(agent.open_trades)}") # Still open, tgt is ~104
    
    agent.monitor_trades(105.0)
    print(f"Open trades: {len(agent.open_trades)}") # Closed
    
    completed = agent.trade_history[0]
    print(f"\nCompleted Trade: {completed.exit_reason} at {completed.exit_price}")
    print(f"Net PnL (including slippage & fees): {completed.get_pnl_percentage() * 100:.2f}%")

if __name__ == "__main__":
    run()
