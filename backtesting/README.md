# Backtesting Engine

The Backtesting Engine enables AlphaMind AI to evaluate trading strategies on historical market data before deploying them in paper trading or live environments.

## Features

- **Historical Data Retrieval**: Fetch price and news data for any time period using yfinance
- **Time-Series Simulation**: Execute the complete multi-agent pipeline step-by-step through historical time
- **Temporal Isolation**: Strict prevention of look-ahead bias - only past data visible at each decision point
- **Realistic Execution**: Simulates slippage, commission, stop loss, and target exits
- **Comprehensive Metrics**: Win rate, profit factor, Sharpe ratio, max drawdown, and more
- **Performance Analytics**: Compare against buy-and-hold baseline, regime-specific analysis
- **Result Storage**: File-based storage with querying and comparison capabilities
- **API Integration**: FastAPI endpoints for UI integration

## Quick Start

### Run a Backtest

```python
from datetime import datetime
from backtesting.simulator import BacktestSimulator
from backtesting.models import StrategyConfig

# Configure strategy
strategy = StrategyConfig(
    name="my_strategy",
    technical_weight=0.5,
    event_weight=0.2,
    risk_weight=0.3,
    max_position_size=0.10,
    max_open_positions=3
)

# Create simulator
simulator = BacktestSimulator(
    strategy_config=strategy,
    initial_capital=100000.0
)

# Run backtest
result = simulator.run_backtest(
    symbol="AAPL",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    interval="1d"
)

# View results
print(f"Total Return: {result.metrics.total_return_pct:.2f}%")
print(f"Win Rate: {result.metrics.win_rate * 100:.2f}%")
print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
```

### Save and Load Results

```python
from backtesting.storage import BacktestStorage

storage = BacktestStorage()

# Save result
result_id = storage.save_result(result)

# Load result
loaded_result = storage.load_result(result_id)

# Query results
results = storage.query_results(symbol="AAPL")
```

### Generate Reports

```python
from backtesting.report_generator import ReportGenerator

# Generate summary report
report = ReportGenerator.generate_summary_report(result)

# Export to JSON
ReportGenerator.export_json(result, "backtest_report.json")

# Export to CSV
ReportGenerator.export_csv(result, "backtest_trades.csv")
```

## API Endpoints

### Run Backtest

```bash
POST /api/backtest/run
```

Request body:
```json
{
  "symbol": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "interval": "1d",
  "initial_capital": 100000,
  "strategy_config": {
    "name": "custom",
    "technical_weight": 0.5,
    "event_weight": 0.2,
    "risk_weight": 0.3,
    "max_position_size": 0.10,
    "max_open_positions": 3
  }
}
```

### Get Backtest Status

```bash
GET /api/backtest/status/{job_id}
```

### Get Backtest Results

```bash
GET /api/backtest/results/{result_id}
```

### Query Results

```bash
GET /api/backtest/results?symbol=AAPL&start_date=2023-01-01
```

### Compare Results

```bash
POST /api/backtest/compare
Body: ["result_id_1", "result_id_2"]
```

## Architecture

### Core Components

- **HistoricalDataProvider**: Fetches historical price and news data with caching
- **TimeWindowManager**: Manages temporal boundaries and prevents look-ahead bias
- **BacktestSimulator**: Orchestrates time-series execution of the trading pipeline
- **PerformanceTracker**: Calculates comprehensive performance metrics
- **BacktestStorage**: Persists and retrieves backtest results

### Data Flow

```
Historical Data (yfinance)
    ↓
Time Window Manager (temporal slicing)
    ↓
Backtest Simulator (executes agent pipeline at each time step)
    ↓
Performance Tracker (calculates metrics)
    ↓
Backtest Result (complete result package)
    ↓
Storage (file-based persistence)
```

## Testing

Run the backtesting engine test:

```bash
python test_backtesting.py
```

## Configuration

### Strategy Configuration

```python
StrategyConfig(
    name="strategy_name",
    technical_weight=0.5,      # Weight for technical analysis
    event_weight=0.2,          # Weight for event/news analysis
    risk_weight=0.3,           # Weight for risk assessment
    max_position_size=0.10,    # Max 10% of equity per position
    max_open_positions=3,      # Max 3 concurrent positions
    slippage_bps=5.0,          # 5 basis points slippage
    commission_pct=0.001,      # 0.1% commission
    stop_loss_pct=0.02,        # 2% stop loss
    target_pct=0.04,           # 4% target
    market_regime=None         # Optional regime override
)
```

### Slippage Models

```python
from backtesting.models import SlippageModel

# Fixed slippage
slippage = SlippageModel(model_type="fixed", base_slippage_bps=5.0)

# Volume-based slippage
slippage = SlippageModel(model_type="volume_based", base_slippage_bps=5.0)

# Volatility-based slippage
slippage = SlippageModel(model_type="volatility_based", base_slippage_bps=5.0)
```

## Performance Metrics

The engine calculates the following metrics:

- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Total Return**: Percentage return on initial capital
- **Max Drawdown**: Maximum peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return metric
- **Average Trade Duration**: Mean time in trades
- **Trades Per Day**: Trading frequency
- **Longest Win/Loss Streak**: Consecutive wins/losses
- **Alpha vs Buy & Hold**: Excess return over passive strategy

## Validation

The engine validates configurations before execution:

- Date range validation (end > start, no future dates)
- Symbol validation (ticker exists)
- Strategy parameter validation (weights, position sizes)
- Fusion weight sum validation

## Error Handling

The engine handles errors gracefully:

- Individual time step failures (continues with next step)
- Aborts if failure rate exceeds 10%
- Descriptive error messages with remediation suggestions
- Partial result preservation on cancellation

## Future Enhancements

- Multi-symbol portfolio backtesting
- Walk-forward analysis
- Regime-specific performance analysis
- Progress monitoring and cancellation
- Agent decision logging
- Database migration (PostgreSQL)
- Optimization engine (grid search, genetic algorithms)
- Monte Carlo simulation

## License

Part of AlphaMind AI - Agentic Trading Intelligence Platform
