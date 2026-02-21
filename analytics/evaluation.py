from typing import List, Dict, Any
import math
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
                "max_drawdown": 0.0,
                "final_equity_multiple": 1.0,
                "sharpe_ratio": 0.0,
                "alpha": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "win_streak": 0,
                "expected_value": 0.0,
                "calmar_ratio": 0.0,
            }

        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0
        total_return = 0.0
        pnl_returns: List[float] = []
        win_returns: List[float] = []
        loss_returns: List[float] = []
        max_win_streak = 0
        current_win_streak = 0
        
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
            pnl_returns.append(trade_return)
            current_equity *= (1 + trade_return)
            
            if current_equity > peak_equity:
                peak_equity = current_equity
            
            drawdown = (peak_equity - current_equity) / peak_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            if pnl_pct > 0:
                wins += 1
                gross_profit += pnl_pct
                win_returns.append(pnl_pct)
                current_win_streak += 1
                max_win_streak = max(max_win_streak, current_win_streak)
            else:
                losses += 1
                gross_loss += abs(pnl_pct)
                loss_returns.append(abs(pnl_pct))
                current_win_streak = 0

        win_rate = wins / len(closed_trades) if closed_trades else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        avg_return = total_return / len(closed_trades) if closed_trades else 0.0
        avg_win = sum(win_returns) / len(win_returns) if win_returns else 0.0
        avg_loss = sum(loss_returns) / len(loss_returns) if loss_returns else 0.0
        expected_value = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss)
        calmar_ratio = (avg_return / max_drawdown) if max_drawdown > 0 else 0.0

        if len(pnl_returns) > 1:
            mean_ret = sum(pnl_returns) / len(pnl_returns)
            variance = sum((r - mean_ret) ** 2 for r in pnl_returns) / (len(pnl_returns) - 1)
            std_dev = math.sqrt(max(variance, 0.0))
            sharpe_ratio = (mean_ret / std_dev) * math.sqrt(len(pnl_returns)) if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        benchmark_avg = 0.001  # 0.1% per-trade baseline for lightweight alpha estimate
        alpha = avg_return - benchmark_avg

        return {
            "total_trades": len(closed_trades),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4),
            "avg_return": round(avg_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "final_equity_multiple": round(current_equity, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "alpha": round(alpha, 4),
            "avg_win": round(avg_win, 4),
            "avg_loss": round(avg_loss, 4),
            "win_streak": max_win_streak,
            "expected_value": round(expected_value, 4),
            "calmar_ratio": round(calmar_ratio, 4),
        }
