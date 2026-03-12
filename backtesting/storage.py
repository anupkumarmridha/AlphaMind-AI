"""
Storage system for Backtesting Engine

File-based storage for backtest results with querying and comparison capabilities.
"""

import json
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

from backtesting.models import BacktestResult


class BacktestStorage:
    """File-based storage for backtest results."""
    
    def __init__(self, storage_path: str = "backtests/"):
        """
        Initialize storage with file system path.
        
        Args:
            storage_path: Directory path for storing backtest results
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_result(self, result: BacktestResult) -> str:
        """
        Save backtest result to JSON file, return result ID.
        
        Args:
            result: BacktestResult object to save
            
        Returns:
            Result ID (unique identifier)
        """
        file_path = self.storage_path / f"{result.id}.json"
        
        # Convert to dict and handle datetime serialization
        result_dict = result.model_dump()
        
        # Convert datetime objects to ISO format strings
        result_dict['created_at'] = result.created_at.isoformat()
        result_dict['start_date'] = result.start_date.isoformat()
        result_dict['end_date'] = result.end_date.isoformat()
        
        # Convert equity curve tuples to serializable format
        result_dict['equity_curve'] = [
            [dt.isoformat(), equity] for dt, equity in result.equity_curve
        ]
        
        # Save to JSON file
        with open(file_path, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        return result.id
    
    def load_result(self, result_id: str) -> BacktestResult:
        """
        Load backtest result by ID.
        
        Args:
            result_id: Unique identifier of the backtest result
            
        Returns:
            BacktestResult object
            
        Raises:
            FileNotFoundError: If result ID does not exist
        """
        file_path = self.storage_path / f"{result_id}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Backtest result {result_id} not found")
        
        with open(file_path, 'r') as f:
            result_dict = json.load(f)
        
        # Convert ISO format strings back to datetime
        result_dict['created_at'] = datetime.fromisoformat(result_dict['created_at'])
        result_dict['start_date'] = datetime.fromisoformat(result_dict['start_date'])
        result_dict['end_date'] = datetime.fromisoformat(result_dict['end_date'])
        
        # Convert equity curve back to tuples
        result_dict['equity_curve'] = [
            (datetime.fromisoformat(dt), equity)
            for dt, equity in result_dict['equity_curve']
        ]
        
        return BacktestResult(**result_dict)
    
    def query_results(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_name: Optional[str] = None
    ) -> List[BacktestResult]:
        """
        Query results with filters.
        
        Args:
            symbol: Filter by symbol
            start_date: Filter by start date (results starting after this date)
            end_date: Filter by end date (results ending before this date)
            strategy_name: Filter by strategy configuration name
            
        Returns:
            List of BacktestResult objects matching filters
        """
        results = []
        
        # Iterate through all JSON files in storage directory
        for file_path in self.storage_path.glob("*.json"):
            try:
                result = self.load_result(file_path.stem)
                
                # Apply filters
                if symbol and result.symbol != symbol:
                    continue
                
                if start_date and result.start_date < start_date:
                    continue
                
                if end_date and result.end_date > end_date:
                    continue
                
                if strategy_name and result.strategy_config.name != strategy_name:
                    continue
                
                results.append(result)
            except Exception as e:
                print(f"Warning: Failed to load result {file_path.stem}: {e}")
        
        # Sort by created_at descending (most recent first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        return results
    
    def compare_results(
        self,
        result_ids: List[str]
    ) -> pd.DataFrame:
        """
        Generate comparison table of multiple backtest results.
        
        Args:
            result_ids: List of result IDs to compare
            
        Returns:
            DataFrame with comparison metrics
        """
        comparison_data = []
        
        for result_id in result_ids:
            try:
                result = self.load_result(result_id)
                
                comparison_data.append({
                    'result_id': result.id,
                    'symbol': result.symbol,
                    'strategy': result.strategy_config.name,
                    'start_date': result.start_date,
                    'end_date': result.end_date,
                    'total_trades': result.metrics.total_trades,
                    'win_rate': result.metrics.win_rate,
                    'total_return_pct': result.metrics.total_return_pct,
                    'max_drawdown_pct': result.metrics.max_drawdown_pct,
                    'sharpe_ratio': result.metrics.sharpe_ratio,
                    'profit_factor': result.metrics.profit_factor,
                    'alpha_vs_buy_hold': result.metrics.alpha_vs_buy_hold,
                    'final_equity': result.metrics.final_equity
                })
            except Exception as e:
                print(f"Warning: Failed to load result {result_id}: {e}")
        
        return pd.DataFrame(comparison_data)
    
    def export_to_csv(self, result_id: str, output_path: str):
        """
        Export backtest trades and metrics to CSV.
        
        Args:
            result_id: Unique identifier of the backtest result
            output_path: Path for CSV output file
        """
        result = self.load_result(result_id)
        
        # Export trades to CSV
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
                'pnl_pct': trade.get_pnl_percentage() if trade.status == "CLOSED" else None
            })
        
        df = pd.DataFrame(trades_data)
        df.to_csv(output_path, index=False)
