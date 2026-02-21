import os
import time

from agents.graph import alphamind_graph
from models.trade import Trade

# Test symbols
SYMBOLS = ["AAPL", "TSLA", "MSFT"]

def main():
    print("====================================")
    print(" ALPHA MIND AI - SYSTEM TEST RUN OP")
    print("====================================")
    
    results = []
    
    for symbol in SYMBOLS:
        print(f"\n🚀 Initiating investigation for {symbol}")
        state = {
            "symbol": symbol,
            "market_regime": "earnings" if symbol == "AAPL" else "normal" # simulate regimes
        }
        
        # Run graph
        try:
            output = alphamind_graph.invoke(state)
            results.append(output)
            time.sleep(1) # simple delay
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            
    print("\n====================================")
    print(" SUMMARY OF DECISIONS")
    print("====================================")
    
    for r in results:
        symbol = r["symbol"]
        dec = r["decision_data"]["decision"]
        conf = r["decision_data"]["confidence"]
        sz = r["decision_data"].get("position_size", 0)
        reason = r["decision_data"]["reason"]
        
        print(f"\n[ {symbol} ] -> {dec}")
        print(f"  Confidence: {conf:.2f} | Size: {sz*100:.1f}%")
        print(f"  Narrative : {reason}")
        
    print("\n✅ System test complete.")

if __name__ == "__main__":
    main()
