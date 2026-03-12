"""
Validation and Error Handling for Backtesting Engine

Validates backtest configurations and provides descriptive error messages.
"""

from typing import List
from datetime import datetime
import yfinance as yf

from backtesting.models import StrategyConfig


class BacktestValidationError(Exception):
    """Custom exception for backtest validation errors."""
    pass


def validate_backtest_config(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    strategy_config: StrategyConfig
) -> List[str]:
    """
    Validate configuration before starting backtest.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date for backtest
        end_date: End date for backtest
        strategy_config: Strategy configuration
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Validate date range
    if end_date <= start_date:
        errors.append(f"End date {end_date.date()} must be after start date {start_date.date()}")
    
    if start_date > datetime.now():
        errors.append(f"Start date {start_date.date()} cannot be in the future")
    
    if end_date > datetime.now():
        errors.append(f"End date {end_date.date()} cannot be in the future")
    
    # Validate strategy config parameters
    if strategy_config.max_position_size <= 0 or strategy_config.max_position_size > 1:
        errors.append(
            f"Invalid max_position_size: {strategy_config.max_position_size} "
            "(must be between 0 and 1)"
        )
    
    if strategy_config.max_open_positions <= 0:
        errors.append(
            f"Invalid max_open_positions: {strategy_config.max_open_positions} "
            "(must be greater than 0)"
        )
    
    if strategy_config.slippage_bps < 0:
        errors.append(
            f"Invalid slippage_bps: {strategy_config.slippage_bps} "
            "(must be non-negative)"
        )
    
    if strategy_config.commission_pct < 0:
        errors.append(
            f"Invalid commission_pct: {strategy_config.commission_pct} "
            "(must be non-negative)"
        )
    
    # Validate fusion weights sum to reasonable value
    weight_sum = (
        strategy_config.technical_weight +
        strategy_config.event_weight +
        strategy_config.risk_weight
    )
    if abs(weight_sum - 1.0) > 0.01:  # Allow small floating point error
        errors.append(
            f"Fusion weights should sum to 1.0, got {weight_sum:.3f}"
        )
    
    # Validate symbol exists
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or 'symbol' not in info:
            errors.append(f"Invalid or unknown symbol: {symbol}")
    except Exception as e:
        errors.append(f"Cannot validate symbol {symbol}: {str(e)}")
    
    return errors


def validate_and_raise(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    strategy_config: StrategyConfig
):
    """
    Validate configuration and raise exception if invalid.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date for backtest
        end_date: End date for backtest
        strategy_config: Strategy configuration
        
    Raises:
        BacktestValidationError: If configuration is invalid
    """
    errors = validate_backtest_config(symbol, start_date, end_date, strategy_config)
    
    if errors:
        error_msg = "BacktestValidationError: Invalid backtest configuration\n"
        for error in errors:
            error_msg += f"  - {error}\n"
        error_msg += "\nSuggestion: Check your time window and strategy configuration parameters."
        
        raise BacktestValidationError(error_msg)
