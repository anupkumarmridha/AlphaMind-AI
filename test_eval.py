from models.trade import Trade
from analytics.evaluation import EvaluationEngine

def run():
    # Mock some trades
    t1 = Trade(symbol="AAPL", action="BUY", position_size=0.1, desired_entry=100.0, fill_price=100.0, commission_fee=0.001, stop_loss=90.0, target=110.0)
    t1.close_trade(110.0, "Target Hit") # ~9.9% win
    
    t2 = Trade(symbol="TSLA", action="BUY", position_size=0.1, desired_entry=200.0, fill_price=200.0, commission_fee=0.001, stop_loss=190.0, target=220.0)
    t2.close_trade(190.0, "Stop Loss Hit") # ~-5.1% loss
    
    t3 = Trade(symbol="MSFT", action="SELL", position_size=0.1, desired_entry=300.0, fill_price=300.0, commission_fee=0.001, stop_loss=330.0, target=270.0)
    t3.close_trade(270.0, "Target Hit") # ~9.9% win

    metrics = EvaluationEngine.evaluate_performance([t1, t2, t3])
    
    print("Performance Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    run()
