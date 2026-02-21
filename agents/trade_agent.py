import random
from typing import Dict, Any, List
from models.trade import Trade

class TradeAgent:
    def __init__(self, slippage_bps: float = 5.0, commission_pct: float = 0.001):
        """
        slippage_bps: simulated slippage in basis points (e.g. 5.0 bps = 0.05%)
        commission_pct: simulated commission + fees as a percentage of trade value (e.g. 0.001 = 0.1%)
        """
        self.slippage_bps = slippage_bps
        self.commission_pct = commission_pct
        self.open_trades: List[Trade] = []
        self.trade_history: List[Trade] = []

    def execute_trade(self, decision_data: Dict[str, Any], current_price: float, symbol: str) -> Trade:
        """
        Executes a paper trade based on Fusion Agent's decision.
        """
        decision = decision_data.get("decision", "NO_TRADE")
        if decision == "NO_TRADE":
            return None
            
        position_size = decision_data.get("position_size", 0.0)
        
        # Calculate simulated slippage
        # simple model: +/- N bps randomly skewed against the trader
        slip_pct = (self.slippage_bps / 10000.0) * random.uniform(0.5, 1.5)
        
        if decision == "BUY":
            fill_price = current_price * (1 + slip_pct)
            sl = fill_price * 0.98 # default 2% stop loss
            tg = fill_price * 1.04 # default 4% target (1:2 RR)
        else: # SELL
            fill_price = current_price * (1 - slip_pct)
            sl = fill_price * 1.02 # default 2% stop loss
            tg = fill_price * 0.96 # default 4% target (1:2 RR)

        trade = Trade(
            symbol=symbol,
            action=decision,
            position_size=position_size,
            desired_entry=current_price,
            fill_price=fill_price,
            commission_fee=self.commission_pct,
            stop_loss=sl,
            target=tg
        )
        
        self.open_trades.append(trade)
        return trade

    def monitor_trades(self, current_price: float):
        """
        Checks all open trades against the current price to trigger SL or target.
        """
        for t in self.open_trades[:]:
            if t.action == "BUY":
                if current_price <= t.stop_loss:
                    t.close_trade(current_price, "Stop Loss Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
                elif current_price >= t.target:
                    t.close_trade(current_price, "Target Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
            elif t.action == "SELL":
                if current_price >= t.stop_loss:
                    t.close_trade(current_price, "Stop Loss Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
                elif current_price <= t.target:
                    t.close_trade(current_price, "Target Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
