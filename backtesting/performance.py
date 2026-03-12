"""
Performance Tracker for Backtesting Engine

Calculates comprehensive performance metrics from trade history and equity curve.
"""

from typing import List, Tuple, Dict, Callable, Optional
from datetime import datetime
import numpy as np

from models.trade import Trade
from backtesting.models import PerformanceMetrics


class PerformanceTracker:
    """Tracks and calculates performance metrics for backtests."""
    
    def __init__(self):
        """Initialize tracker with empty state."""
        self.trades: List[Trade] = []
        self.equity_points: List[Tuple[datetime, float]] = []
    
    def record_trade(self, trade: Trade):
        """
        Add a closed trade to the tracking history.
        
        Args:
            trade: Trade object to record
        """
        self.trades.append(trade)
    
    def record_equity_point(self, timestamp: datetime, equity: float):
        """
        Record equity value at a specific time.
        
        Args:
            timestamp: Time of equity measurement
            equity: Portfolio equity value
        """
        self.equity_points.append((timestamp, equity))
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.
        
        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        closed_trades = [t for t in self.trades if t.status == "CLOSED"]
        
        if not closed_trades:
            # Return zero metrics if no trades
            return PerformanceMetrics(
                total_trades=len(self.trades),
                closed_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                total_return_pct=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                avg_trade_duration_hours=0.0,
                trades_per_day=0.0,
                longest_win_streak=0,
                longest_loss_streak=0,
                alpha_vs_buy_hold=0.0,
                final_equity=self.equity_points[-1][1] if self.equity_points else 0.0
            )
        
        # Calculate win rate
        winning_trades = [t for t in closed_trades if t.get_pnl_percentage() > 0]
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0.0
        
        # Calculate profit factor
        gross_profit = sum(t.get_pnl_percentage() for t in closed_trades if t.get_pnl_percentage() > 0)
        gross_loss = abs(sum(t.get_pnl_percentage() for t in closed_trades if t.get_pnl_percentage() < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        # Calculate total return
        if self.equity_points:
            initial_equity = self.equity_points[0][1]
            final_equity = self.equity_points[-1][1]
            total_return_pct = ((final_equity - initial_equity) / initial_equity) * 100
        else:
            total_return_pct = 0.0
            final_equity = 0.0
        
        # Calculate max drawdown
        max_drawdown_pct = self._calculate_max_drawdown()
        
        # Calculate Sharpe ratio
        sharpe_ratio = self._calculate_sharpe_ratio(closed_trades)
        
        # Calculate average trade duration
        durations = []
        for trade in closed_trades:
            if trade.exit_timestamp:
                duration = (trade.exit_timestamp - trade.timestamp).total_seconds() / 3600  # hours
                durations.append(duration)
        avg_trade_duration_hours = np.mean(durations) if durations else 0.0
        
        # Calculate trades per day
        if self.equity_points and len(self.equity_points) > 1:
            total_days = (self.equity_points[-1][0] - self.equity_points[0][0]).days
            trades_per_day = len(closed_trades) / max(total_days, 1)
        else:
            trades_per_day = 0.0
        
        # Calculate streaks
        longest_win_streak, longest_loss_streak = self._calculate_streaks(closed_trades)
        
        return PerformanceMetrics(
            total_trades=len(self.trades),
            closed_trades=len(closed_trades),
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            avg_trade_duration_hours=avg_trade_duration_hours,
            trades_per_day=trades_per_day,
            longest_win_streak=longest_win_streak,
            longest_loss_streak=longest_loss_streak,
            alpha_vs_buy_hold=0.0,  # Calculated separately
            final_equity=final_equity
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage from equity curve."""
        if not self.equity_points:
            return 0.0
        
        equities = [eq for _, eq in self.equity_points]
        peak = equities[0]
        max_dd = 0.0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, closed_trades: List[Trade]) -> float:
        """Calculate Sharpe ratio from trade returns."""
        if not closed_trades:
            return 0.0
        
        returns = [t.get_pnl_percentage() for t in closed_trades]
        
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe (assuming ~252 trading days)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_streaks(self, closed_trades: List[Trade]) -> Tuple[int, int]:
        """Calculate longest winning and losing streaks."""
        if not closed_trades:
            return 0, 0
        
        current_win_streak = 0
        current_loss_streak = 0
        longest_win_streak = 0
        longest_loss_streak = 0
        
        for trade in closed_trades:
            pnl = trade.get_pnl_percentage()
            
            if pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                longest_win_streak = max(longest_win_streak, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                longest_loss_streak = max(longest_loss_streak, current_loss_streak)
        
        return longest_win_streak, longest_loss_streak
    
    def generate_equity_curve(self) -> List[Tuple[datetime, float]]:
        """
        Return time-series equity curve data.
        
        Returns:
            List of (timestamp, equity) tuples in chronological order
        """
        return self.equity_points
    
    def calculate_buy_and_hold_baseline(
        self,
        start_price: float,
        end_price: float
    ) -> float:
        """
        Calculate buy-and-hold return for comparison.
        
        Args:
            start_price: Starting price
            end_price: Ending price
            
        Returns:
            Buy-and-hold return percentage
        """
        return ((end_price - start_price) / start_price) * 100
    
    def calculate_regime_metrics(
        self,
        regime_classifier: Callable
    ) -> Dict[str, PerformanceMetrics]:
        """
        Calculate metrics separately for each market regime.
        
        Args:
            regime_classifier: Function to classify time periods into regimes
            
        Returns:
            Dictionary mapping regime names to PerformanceMetrics
        """
        # TODO: Implement in Phase 3 (task 5.8)
        raise NotImplementedError("Regime-specific metrics not yet implemented")
