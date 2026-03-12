"""
Data models for the Backtesting Engine

All models use Pydantic v2 for validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
from models.trade import Trade


class StrategyConfig(BaseModel):
    """Configuration for backtesting strategy parameters."""
    name: str = "default"
    
    # Fusion weights
    technical_weight: float = 0.5
    event_weight: float = 0.2
    risk_weight: float = 0.3
    
    # Position sizing
    max_position_size: float = 0.10  # 10% of equity
    max_open_positions: int = 3
    
    # Execution costs
    slippage_bps: float = 5.0
    commission_pct: float = 0.001
    
    # Risk management
    stop_loss_pct: float = 0.02  # 2%
    target_pct: float = 0.04     # 4%
    
    # Market regime override
    market_regime: Optional[str] = None  # "normal", "volatile", "earnings"


class SlippageModel(BaseModel):
    """Model for calculating realistic slippage."""
    model_type: str = "fixed"  # "fixed", "volume_based", "volatility_based"
    base_slippage_bps: float = 5.0
    
    def calculate_slippage(
        self,
        action: str,
        price: float,
        volume: int = 0,
        volatility: float = 0.0
    ) -> float:
        """Calculate slippage percentage based on model type."""
        if self.model_type == "fixed":
            return self.base_slippage_bps / 10000.0
        elif self.model_type == "volume_based":
            # Lower volume = higher slippage
            volume_factor = max(1.0, 1000000 / max(volume, 1))
            return (self.base_slippage_bps * volume_factor) / 10000.0
        elif self.model_type == "volatility_based":
            # Higher volatility = higher slippage
            vol_factor = 1.0 + (volatility * 10)
            return (self.base_slippage_bps * vol_factor) / 10000.0
        return self.base_slippage_bps / 10000.0


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics for a backtest."""
    total_trades: int
    closed_trades: int
    win_rate: float
    profit_factor: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_trade_duration_hours: float
    trades_per_day: float
    longest_win_streak: int
    longest_loss_streak: int
    alpha_vs_buy_hold: float
    final_equity: float


class DecisionLog(BaseModel):
    """Log of agent decisions at a specific time step."""
    timestamp: datetime
    symbol: str
    technical_toon: str
    event_toon: str
    risk_toon: str
    fusion_decision: Dict[str, Any]
    trade_executed: Optional[Trade] = None


class BacktestResult(BaseModel):
    """Complete result of a backtest execution."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Configuration
    symbol: str
    symbols: Optional[List[str]] = None
    start_date: datetime
    end_date: datetime
    interval: str
    strategy_config: StrategyConfig
    initial_capital: float
    
    # Results
    trades: List[Trade]
    metrics: PerformanceMetrics
    equity_curve: List[Tuple[datetime, float]]
    
    # Optional detailed logs
    decision_logs: Optional[List[DecisionLog]] = None
    regime_metrics: Optional[Dict[str, PerformanceMetrics]] = None
    
    # Baseline comparison
    buy_hold_return_pct: float
