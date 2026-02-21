from typing import List, Dict, Any
from models.trade import Trade

class EvaluationEngine:
    @staticmethod
    def evaluate_performance(trades: List[Trade]) -> Dict[str, Any]:
        """
        Calculates Win Rate, Profit Factor, and average stats from a list of closed trades.
        """
        closed_trades = [t for t in trades if t.status == "CLOSED"]
        if not closed_trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_return": 0.0,
                "max_drawdown": 0.0
            }

        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0
        total_return = 0.0
        
        peak_equity = 1.0 # arbitrary relative starting point 100%
        current_equity = 1.0
        max_drawdown = 0.0

        for t in closed_trades:
            pnl_pct = t.get_pnl_percentage()
            total_return += pnl_pct
            
            # Simple compounded equity curve (assuming 10% risk per trade logic etc is separate, 
            # here we just track raw sequential pnl of trades scaled by their position size)
            # Actually, position_size is a fraction of equity.
            trade_return = pnl_pct * t.position_size
            current_equity *= (1 + trade_return)
            
            if current_equity > peak_equity:
                peak_equity = current_equity
            
            drawdown = (peak_equity - current_equity) / peak_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            if pnl_pct > 0:
                wins += 1
                gross_profit += pnl_pct
            else:
                losses += 1
                gross_loss += abs(pnl_pct)

        win_rate = wins / len(closed_trades) if closed_trades else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        avg_return = total_return / len(closed_trades) if closed_trades else 0.0

        return {
            "total_trades": len(closed_trades),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4),
            "avg_return": round(avg_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "final_equity_multiple": round(current_equity, 4)
        }
