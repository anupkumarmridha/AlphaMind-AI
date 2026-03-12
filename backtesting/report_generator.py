"""
Report Generator for Backtesting Engine

Generates comprehensive backtest reports with metrics, charts, and trade details.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
import pandas as pd

from backtesting.models import BacktestResult


class ReportGenerator:
    """Generates backtest reports in various formats."""
    
    @staticmethod
    def generate_summary_report(result: BacktestResult) -> Dict[str, Any]:
        """
        Generate summary report with key metrics.
        
        Args:
            result: BacktestResult object
            
        Returns:
            Dictionary containing report data
        """
        report = {
            "backtest_id": result.id,
            "created_at": result.created_at.isoformat(),
            "symbol": result.symbol,
            "period": {
                "start_date": result.start_date.isoformat(),
                "end_date": result.end_date.isoformat(),
                "interval": result.interval
            },
            "strategy": {
                "name": result.strategy_config.name,
                "technical_weight": result.strategy_config.technical_weight,
                "event_weight": result.strategy_config.event_weight,
                "risk_weight": result.strategy_config.risk_weight,
                "max_position_size": result.strategy_config.max_position_size,
                "max_open_positions": result.strategy_config.max_open_positions
            },
            "performance": {
                "total_trades": result.metrics.total_trades,
                "closed_trades": result.metrics.closed_trades,
                "win_rate": f"{result.metrics.win_rate * 100:.2f}%",
                "profit_factor": f"{result.metrics.profit_factor:.2f}",
                "total_return": f"{result.metrics.total_return_pct:.2f}%",
                "max_drawdown": f"{result.metrics.max_drawdown_pct:.2f}%",
                "sharpe_ratio": f"{result.metrics.sharpe_ratio:.2f}",
                "avg_trade_duration_hours": f"{result.metrics.avg_trade_duration_hours:.1f}",
                "trades_per_day": f"{result.metrics.trades_per_day:.2f}",
                "longest_win_streak": result.metrics.longest_win_streak,
                "longest_loss_streak": result.metrics.longest_loss_streak,
                "final_equity": f"${result.metrics.final_equity:,.2f}"
            },
            "baseline": {
                "buy_hold_return": f"{result.buy_hold_return_pct:.2f}%",
                "alpha": f"{result.metrics.alpha_vs_buy_hold:.2f}%"
            },
            "equity_curve": [
                {"timestamp": ts.isoformat(), "equity": eq}
                for ts, eq in result.equity_curve
            ],
            "trade_distribution": ReportGenerator._generate_trade_distribution(result),
            "drawdown_data": ReportGenerator._generate_drawdown_data(result)
        }
        
        return report
    
    @staticmethod
    def _generate_trade_distribution(result: BacktestResult) -> Dict[str, Any]:
        """Generate trade distribution data (wins vs losses histogram)."""
        closed_trades = [t for t in result.trades if t.status == "CLOSED"]
        
        if not closed_trades:
            return {"wins": 0, "losses": 0, "pnl_distribution": []}
        
        wins = [t for t in closed_trades if t.get_pnl_percentage() > 0]
        losses = [t for t in closed_trades if t.get_pnl_percentage() <= 0]
        
        # PnL distribution buckets
        pnl_values = [t.get_pnl_percentage() * 100 for t in closed_trades]
        
        return {
            "wins": len(wins),
            "losses": len(losses),
            "pnl_distribution": pnl_values
        }
    
    @staticmethod
    def _generate_drawdown_data(result: BacktestResult) -> List[Dict[str, Any]]:
        """Generate drawdown chart data over time."""
        if not result.equity_curve:
            return []
        
        equities = [eq for _, eq in result.equity_curve]
        timestamps = [ts for ts, _ in result.equity_curve]
        
        peak = equities[0]
        drawdown_data = []
        
        for i, equity in enumerate(equities):
            if equity > peak:
                peak = equity
            dd_pct = ((peak - equity) / peak) * 100 if peak > 0 else 0.0
            
            drawdown_data.append({
                "timestamp": timestamps[i].isoformat(),
                "drawdown_pct": dd_pct
            })
        
        return drawdown_data
    
    @staticmethod
    def export_json(result: BacktestResult, output_path: str):
        """
        Export report to JSON format.
        
        Args:
            result: BacktestResult object
            output_path: Path for JSON output file
        """
        report = ReportGenerator.generate_summary_report(result)
        
        # Add complete trade table
        report["trades"] = [
            {
                "trade_id": t.id,
                "symbol": t.symbol,
                "action": t.action,
                "position_size": t.position_size,
                "desired_entry": t.desired_entry,
                "fill_price": t.fill_price,
                "commission_fee": t.commission_fee,
                "stop_loss": t.stop_loss,
                "target": t.target,
                "status": t.status,
                "timestamp": t.timestamp.isoformat(),
                "exit_price": t.exit_price,
                "exit_reason": t.exit_reason,
                "exit_timestamp": t.exit_timestamp.isoformat() if t.exit_timestamp else None,
                "pnl_pct": f"{t.get_pnl_percentage() * 100:.2f}%" if t.status == "CLOSED" else None
            }
            for t in result.trades
        ]
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    @staticmethod
    def export_csv(result: BacktestResult, output_path: str):
        """
        Export trades to CSV format.
        
        Args:
            result: BacktestResult object
            output_path: Path for CSV output file
        """
        trades_data = []
        for trade in result.trades:
            trades_data.append({
                'trade_id': trade.id,
                'symbol': trade.symbol,
                'action': trade.action,
                'position_size': trade.position_size,
                'desired_entry': trade.desired_entry,
                'fill_price': trade.fill_price,
                'commission_fee': trade.commission_fee,
                'stop_loss': trade.stop_loss,
                'target': trade.target,
                'status': trade.status,
                'timestamp': trade.timestamp,
                'exit_price': trade.exit_price,
                'exit_reason': trade.exit_reason,
                'exit_timestamp': trade.exit_timestamp,
                'pnl_pct': trade.get_pnl_percentage() * 100 if trade.status == "CLOSED" else None
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(output_path, index=False)
