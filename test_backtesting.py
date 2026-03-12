"""
Test file for Backtesting Engine

Tests the core backtesting functionality with a simple example.
"""

from datetime import datetime
from backtesting.simulator import BacktestSimulator
from backtesting.models import StrategyConfig
from backtesting.storage import BacktestStorage
from backtesting.validation import validate_backtest_config


def run():
    """Run backtesting engine test."""
    print("=" * 60)
    print("Testing Backtesting Engine")
    print("=" * 60)
    
    # Test 1: Validation
    print("\n[Test 1] Configuration Validation")
    strategy_config = StrategyConfig(
        name="test_strategy",
        technical_weight=0.5,
        event_weight=0.2,
        risk_weight=0.3,
        max_position_size=0.10,
        max_open_positions=3
    )
    
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 3, 31)
    symbol = "AAPL"
    
    errors = validate_backtest_config(symbol, start_date, end_date, strategy_config)
    if errors:
        print(f"❌ Validation failed: {errors}")
        return
    else:
        print("✓ Configuration validation passed")
    
    # Test 2: Run Backtest
    print("\n[Test 2] Running Backtest")
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Strategy: {strategy_config.name}")
    
    try:
        simulator = BacktestSimulator(
            strategy_config=strategy_config,
            initial_capital=100000.0
        )
        
        result = simulator.run_backtest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="1d"
        )
        
        print(f"✓ Backtest completed successfully")
        print(f"  Result ID: {result.id}")
        print(f"  Total Trades: {result.metrics.total_trades}")
        print(f"  Closed Trades: {result.metrics.closed_trades}")
        print(f"  Win Rate: {result.metrics.win_rate * 100:.2f}%")
        print(f"  Total Return: {result.metrics.total_return_pct:.2f}%")
        print(f"  Max Drawdown: {result.metrics.max_drawdown_pct:.2f}%")
        print(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
        print(f"  Final Equity: ${result.metrics.final_equity:,.2f}")
        print(f"  Buy & Hold Return: {result.buy_hold_return_pct:.2f}%")
        print(f"  Alpha: {result.metrics.alpha_vs_buy_hold:.2f}%")
        
        # Test 3: Storage
        print("\n[Test 3] Result Storage")
        storage = BacktestStorage()
        result_id = storage.save_result(result)
        print(f"✓ Result saved with ID: {result_id}")
        
        # Load result back
        loaded_result = storage.load_result(result_id)
        print(f"✓ Result loaded successfully")
        print(f"  Loaded {len(loaded_result.trades)} trades")
        print(f"  Loaded {len(loaded_result.equity_curve)} equity points")
        
        # Test 4: Query Results
        print("\n[Test 4] Query Results")
        results = storage.query_results(symbol=symbol)
        print(f"✓ Found {len(results)} backtest(s) for {symbol}")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run()
