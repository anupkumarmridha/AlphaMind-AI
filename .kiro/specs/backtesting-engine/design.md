# Design Document: Backtesting Engine

## Overview

The Backtesting Engine extends AlphaMind AI with the capability to evaluate trading strategies on historical market data. This feature enables strategy validation, performance measurement, and continuous improvement by simulating the complete multi-agent decision pipeline over past time periods.

The design integrates seamlessly with the existing LangGraph orchestration, stateless agent architecture, and TOON communication format. The backtesting system operates as a time-series simulator that replays historical market conditions while preventing look-ahead bias and applying realistic trading constraints.

### Key Design Goals

- Reuse existing agent pipeline without modification
- Maintain temporal integrity (no look-ahead bias)
- Support multiple backtesting modes (single symbol, multi-symbol, walk-forward)
- Provide comprehensive performance analytics
- Enable strategy comparison and optimization
- Store results for historical analysis

### Integration Points

- **LangGraph Pipeline**: Reuses `alphamind_graph` from `agents/graph.py`
- **Data Services**: Extends `PriceService` and `NewsService` for historical data
- **Analytics Module**: Extends `EvaluationEngine` with additional metrics
- **Trade Model**: Leverages existing `Trade` model with slippage/commission
- **FastAPI Backend**: Adds backtesting endpoints for UI integration

## Architecture

### High-Level Component Structure


```
┌─────────────────────────────────────────────────────────────┐
│                    Backtesting Engine                        │
│                                                              │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │   Historical   │  │   Simulation     │  │ Performance │ │
│  │ Data Provider  │→ │     Runner       │→ │   Tracker   │ │
│  └────────────────┘  └──────────────────┘  └─────────────┘ │
│          ↓                    ↓                     ↓        │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │  Time Window   │  │  LangGraph       │  │   Result    │ │
│  │   Manager      │  │  Orchestrator    │  │   Storage   │ │
│  └────────────────┘  └──────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
              ┌─────────────────────────────┐
              │   Existing Agent Pipeline   │
              │  (technical, event, risk,   │
              │   fusion, trade)            │
              └─────────────────────────────┘
```

### Component Responsibilities

**Historical Data Provider**
- Fetches price and news data for specified time ranges
- Caches data to minimize API calls
- Returns data in existing Pydantic schema format
- Handles data gaps and missing periods

**Time Window Manager**
- Defines backtest periods (start, end, interval)
- Generates chronological time steps
- Manages sliding windows for agent context
- Supports walk-forward period splitting

**Simulation Runner**
- Orchestrates time-series execution
- Maintains temporal isolation (prevents look-ahead bias)
- Executes LangGraph pipeline at each time step
- Applies slippage and commission models
- Monitors open positions for stop loss/target exits

**Performance Tracker**
- Calculates comprehensive metrics (win rate, profit factor, Sharpe, drawdown)
- Tracks equity curve progression
- Performs regime-specific analysis
- Compares against buy-and-hold baseline

**Result Storage**
- Persists backtest results with unique identifiers
- Stores trades, metrics, and configuration
- Enables querying and comparison
- Supports export to JSON/CSV



### Execution Flow

```
1. Initialize Backtest
   ├─> Load Strategy Configuration
   ├─> Validate Time Window
   └─> Fetch Historical Data (with caching)

2. For Each Time Step (chronological):
   ├─> Slice Historical Data (up to current time only)
   ├─> Build TradingState with historical context
   ├─> Execute LangGraph Pipeline
   │   ├─> Technical Agent (on historical prices)
   │   ├─> Event Agent (on historical news)
   │   ├─> Risk Agent (on historical volatility)
   │   ├─> Fusion Agent (synthesize signals)
   │   └─> Trade Agent (execute with slippage)
   ├─> Monitor Open Positions (check SL/target)
   ├─> Update Equity Curve
   └─> Log Agent Decisions (TOON outputs)

3. Finalize Results
   ├─> Calculate Performance Metrics
   ├─> Generate Equity Curve
   ├─> Compare vs Buy-and-Hold
   ├─> Perform Regime Analysis
   └─> Store Backtest Result
```

### Temporal Isolation Strategy

To prevent look-ahead bias, the Simulation Runner implements strict temporal boundaries:

- **Data Slicing**: At time step T, only data with timestamp ≤ T is visible to agents
- **State Isolation**: Each time step receives a fresh TradingState instance
- **No Future Peeking**: News and price data are filtered by timestamp before agent execution
- **Realistic Delays**: Optional simulation of data availability delays (e.g., news published at T may not be available until T+1)

## Components and Interfaces

### 1. Historical Data Provider

**Module**: `backtesting/historical_data.py`

**Class**: `HistoricalDataProvider`

**Methods**:


```python
@staticmethod
def fetch_historical_prices(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d"
) -> List[PriceData]:
    """Fetch historical price data using yfinance."""
    
@staticmethod
def fetch_historical_news(
    symbol: str,
    start_date: datetime,
    end_date: datetime
) -> List[NewsData]:
    """Fetch historical news data (limited by yfinance availability)."""
    
@staticmethod
def get_cached_data(cache_key: str) -> Optional[Dict]:
    """Retrieve cached historical data to avoid redundant API calls."""
    
@staticmethod
def cache_data(cache_key: str, data: Dict, ttl: int = 3600):
    """Cache historical data with time-to-live."""
```

**Design Notes**:
- Extends existing `PriceService` and `NewsService` patterns
- Uses yfinance's `history()` method with start/end dates
- Implements simple in-memory caching (dict-based) for MVP
- Returns data in existing `PriceData` and `NewsData` Pydantic models
- Handles API rate limits and data gaps gracefully

### 2. Time Window Manager

**Module**: `backtesting/time_window.py`

**Class**: `TimeWindowManager`

**Methods**:

```python
def __init__(
    self,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d",
    lookback_window: int = 50
):
    """Initialize time window with backtest parameters."""
    
def generate_time_steps(self) -> List[datetime]:
    """Generate chronological list of time steps for iteration."""
    
def get_historical_slice(
    self,
    current_time: datetime,
    all_prices: List[PriceData],
    all_news: List[NewsData]
) -> Tuple[List[PriceData], List[NewsData]]:
    """Return data slice up to current_time (prevents look-ahead bias)."""
    
def split_walk_forward(
    self,
    train_ratio: float = 0.7
) -> List[Tuple[datetime, datetime]]:
    """Split time window into training/testing periods for walk-forward analysis."""
```

**Design Notes**:
- Manages temporal boundaries for backtesting
- `lookback_window` defines how many historical bars agents see (e.g., 50 days for EMA calculation)
- `get_historical_slice()` is critical for preventing look-ahead bias
- Supports walk-forward analysis by splitting periods

### 3. Simulation Runner

**Module**: `backtesting/simulator.py`

**Class**: `BacktestSimulator`

**Methods**:

```python
def __init__(
    self,
    strategy_config: StrategyConfig,
    slippage_model: SlippageModel = None,
    initial_capital: float = 100000.0
):
    """Initialize simulator with strategy configuration."""
    
def run_backtest(
    self,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d"
) -> BacktestResult:
    """Execute complete backtest for a single symbol."""
    
def run_multi_symbol_backtest(
    self,
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d"
) -> BacktestResult:
    """Execute backtest across multiple symbols with portfolio-level tracking."""
    
def _execute_time_step(
    self,
    current_time: datetime,
    price_slice: List[PriceData],
    news_slice: List[NewsData],
    symbol: str
) -> Optional[Trade]:
    """Execute LangGraph pipeline for a single time step."""
    
def _monitor_positions(
    self,
    current_price: float,
    current_time: datetime
):
    """Check open positions for stop loss or target exits."""
    
def _update_equity_curve(self, current_time: datetime):
    """Calculate and record current portfolio equity."""
```

**Design Notes**:
- Core orchestration component that drives the backtest
- Reuses existing `alphamind_graph` from `agents/graph.py`
- Maintains a `TradeAgent` instance to track open positions
- Applies slippage and commission through existing `Trade` model
- Tracks equity curve at each time step for drawdown calculation

### 4. Strategy Configuration

**Module**: `backtesting/config.py`

**Class**: `StrategyConfig` (Pydantic Model)

```python
class StrategyConfig(BaseModel):
    name: str = "default"
    
    # Agent weights (for fusion)
    technical_weight: float = 0.5
    event_weight: float = 0.2
    risk_weight: float = 0.3
    
    # Risk parameters
    max_position_size: float = 0.10  # 10% of equity
    max_open_positions: int = 3
    
    # Execution parameters
    slippage_bps: float = 5.0
    commission_pct: float = 0.001
    
    # Stop loss and target defaults
    stop_loss_pct: float = 0.02  # 2%
    target_pct: float = 0.04     # 4%
    
    # Market regime (if fixed for backtest)
    market_regime: Optional[str] = None  # "normal", "volatile", "earnings"
```

**Class**: `SlippageModel` (Pydantic Model)

```python
class SlippageModel(BaseModel):
    model_type: str = "fixed"  # "fixed", "volume_based", "volatility_based"
    base_slippage_bps: float = 5.0
    
    def calculate_slippage(
        self,
        action: str,
        price: float,
        volume: int,
        volatility: float
    ) -> float:
        """Calculate slippage based on model type."""
```

**Design Notes**:
- Pydantic models ensure type safety and validation
- Configuration can be saved/loaded as JSON
- Supports different slippage models for realism
- Defaults match existing production parameters

### 5. Performance Tracker

**Module**: `backtesting/performance.py`

**Class**: `PerformanceTracker`

**Methods**:

```python
def __init__(self):
    """Initialize tracker with empty state."""
    
def record_trade(self, trade: Trade):
    """Add a closed trade to the tracking history."""
    
def record_equity_point(self, timestamp: datetime, equity: float):
    """Record equity value at a specific time."""
    
def calculate_metrics(self) -> PerformanceMetrics:
    """Calculate comprehensive performance metrics."""
    
def calculate_regime_metrics(
    self,
    regime_classifier: Callable
) -> Dict[str, PerformanceMetrics]:
    """Calculate metrics separately for each market regime."""
    
def calculate_buy_and_hold_baseline(
    self,
    start_price: float,
    end_price: float
) -> float:
    """Calculate buy-and-hold return for comparison."""
    
def generate_equity_curve(self) -> List[Tuple[datetime, float]]:
    """Return time-series equity curve data."""
```

**Class**: `PerformanceMetrics` (Pydantic Model)

```python
class PerformanceMetrics(BaseModel):
    total_trades: int
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
```

**Design Notes**:
- Extends existing `EvaluationEngine` with additional metrics
- Tracks equity curve for drawdown and Sharpe calculation
- Supports regime-specific analysis
- Calculates alpha (excess return over buy-and-hold)

### 6. Result Storage

**Module**: `backtesting/storage.py`

**Class**: `BacktestResult` (Pydantic Model)

```python
class BacktestResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Configuration
    symbol: str
    symbols: Optional[List[str]] = None  # for multi-symbol
    start_date: datetime
    end_date: datetime
    interval: str
    strategy_config: StrategyConfig
    
    # Results
    trades: List[Trade]
    metrics: PerformanceMetrics
    equity_curve: List[Tuple[datetime, float]]
    
    # Agent decision logs (optional, can be large)
    decision_logs: Optional[List[Dict]] = None
    
    # Regime analysis
    regime_metrics: Optional[Dict[str, PerformanceMetrics]] = None
```

**Class**: `BacktestStorage`

```python
class BacktestStorage:
    def __init__(self, storage_path: str = "backtests/"):
        """Initialize storage with file system path."""
        
    def save_result(self, result: BacktestResult) -> str:
        """Save backtest result to JSON file, return result ID."""
        
    def load_result(self, result_id: str) -> BacktestResult:
        """Load backtest result by ID."""
        
    def query_results(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_name: Optional[str] = None
    ) -> List[BacktestResult]:
        """Query results with filters."""
        
    def compare_results(
        self,
        result_ids: List[str]
    ) -> pd.DataFrame:
        """Generate comparison table of multiple backtest results."""
        
    def export_to_csv(self, result_id: str, output_path: str):
        """Export backtest trades and metrics to CSV."""
```

**Design Notes**:
- File-based storage for MVP (JSON files in `backtests/` directory)
- Each result saved as `{result_id}.json`
- Pydantic models enable easy serialization/deserialization
- Query functionality for filtering and comparison
- Future enhancement: migrate to PostgreSQL for scalability



## Data Models

### Core Data Models

All data models use Pydantic v2 for validation and serialization.

**Existing Models (Reused)**:
- `PriceData` - OHLCV data with timestamp (from `data/schema.py`)
- `NewsData` - News article with title, content, date, URL (from `data/schema.py`)
- `Trade` - Trade execution with slippage, commission, SL/target (from `models/trade.py`)
- `TradingState` - LangGraph state dictionary (from `agents/graph.py`)

**New Models**:

```python
# backtesting/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid

class StrategyConfig(BaseModel):
    """Configuration for backtesting strategy parameters."""
    name: str = "default"
    
    # Fusion weights
    technical_weight: float = 0.5
    event_weight: float = 0.2
    risk_weight: float = 0.3
    
    # Position sizing
    max_position_size: float = 0.10
    max_open_positions: int = 3
    
    # Execution costs
    slippage_bps: float = 5.0
    commission_pct: float = 0.001
    
    # Risk management
    stop_loss_pct: float = 0.02
    target_pct: float = 0.04
    
    # Market regime override
    market_regime: Optional[str] = None

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
```

### Data Flow Through System

```
Historical Data (yfinance)
    ↓
[PriceData, NewsData] (Pydantic models)
    ↓
Time Window Manager (slicing by timestamp)
    ↓
TradingState (LangGraph state dict)
    ↓
Agent Pipeline (TOON outputs)
    ↓
Trade (execution with slippage/commission)
    ↓
PerformanceMetrics (calculated from trades)
    ↓
BacktestResult (complete result package)
    ↓
JSON Storage (file system)
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Historical Data Temporal Bounds

*For any* historical data fetch with start_date and end_date, all returned PriceData and NewsData timestamps should fall within the range [start_date, end_date].

**Validates: Requirements 1.1, 1.2**

### Property 2: Historical Data Schema Consistency

*For any* historical data fetch, all returned objects should be valid PriceData and NewsData Pydantic model instances that match the schema used by live data services.

**Validates: Requirements 1.3**

### Property 3: Historical Data Caching Idempotence

*For any* identical historical data request made twice, the second request should return cached data without making an additional API call, and both results should be equivalent.

**Validates: Requirements 1.6**

### Property 4: Chronological Time Step Ordering

*For any* backtest execution, the sequence of time steps should be strictly monotonically increasing (each timestamp > previous timestamp).

**Validates: Requirements 2.1**

### Property 5: Temporal Isolation (No Look-Ahead Bias)

*For any* time step T in a backtest, all data provided to the agent pipeline (price_history and news_list) should have timestamps ≤ T, ensuring no future information is accessible.

**Validates: Requirements 2.2, 2.4**

### Property 6: Complete Agent Pipeline Execution

*For any* time step in a backtest, the execution should produce outputs from all required agents (technical_toon, event_toon, risk_toon, fusion decision) before proceeding to the next step.

**Validates: Requirements 2.3**

### Property 7: State Isolation Between Time Steps

*For any* two consecutive time steps T and T+1, modifications to TradingState at time T should not affect the initial state at time T+1 (each step receives a fresh state instance).

**Validates: Requirements 2.5**

### Property 8: Trade Execution Cost Application

*For any* trade executed in simulation, the fill_price should differ from desired_entry by the calculated slippage amount, and the commission_fee should be recorded according to the configured commission percentage.

**Validates: Requirements 2.6, 5.1, 5.2**

### Property 9: Strategy Configuration Round Trip

*For any* valid StrategyConfig, saving it to storage and then loading it back should produce an equivalent configuration object (all fields match).

**Validates: Requirements 3.3, 3.4**

### Property 10: Strategy Configuration Consistency

*For any* backtest executed with a specific StrategyConfig, all trades should respect the configured parameters (max_position_size, stop_loss_pct, target_pct, slippage_bps, commission_pct).

**Validates: Requirements 3.2**

### Property 11: Configuration Validation Rejection

*For any* invalid StrategyConfig (e.g., negative position size, invalid weights), validation should fail before backtest execution begins, returning specific error messages.

**Validates: Requirements 3.6, 10.2**

### Property 12: Performance Metrics Calculation Correctness

*For any* list of closed trades, the calculated metrics (win_rate, profit_factor, total_return_pct, max_drawdown_pct, sharpe_ratio, avg_trade_duration, trades_per_day, streaks) should be mathematically correct according to standard financial formulas.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.9**

### Property 13: Equity Curve Monotonic Recording

*For any* backtest execution, the equity curve should have an entry recorded at each time step, with timestamps in chronological order.

**Validates: Requirements 4.8**

### Property 14: Position Sizing Capital Constraint

*For any* trade execution attempt, the position size should not exceed the available simulated capital, and trades that would violate this constraint should be rejected or reduced.

**Validates: Requirements 5.3**

### Property 15: Stop Loss and Target Monitoring

*For any* open trade with defined stop_loss and target levels, each subsequent time step should check if the current price has crossed these levels, and if so, close the trade at the appropriate price.

**Validates: Requirements 5.4, 5.5**

### Property 16: Maximum Position Limit Enforcement

*For any* state where the number of open positions equals max_open_positions, attempts to open new positions should be blocked until an existing position closes.

**Validates: Requirements 5.6**

### Property 17: Backtest Result Unique Identification

*For any* completed backtest, saving the result should generate a unique identifier, and no two backtest results should share the same ID.

**Validates: Requirements 6.1**

### Property 18: Backtest Result Completeness

*For any* saved BacktestResult, it should contain all required fields: trades list, performance metrics, strategy configuration, time window parameters, and equity curve data.

**Validates: Requirements 6.2, 6.3, 6.4, 6.5**

### Property 19: Backtest Result Query Filtering

*For any* query with filter criteria (symbol, date range, strategy name), only BacktestResult objects matching all specified filters should be returned.

**Validates: Requirements 6.6**

### Property 20: Multi-Symbol Simulation Isolation

*For any* multi-symbol backtest, each symbol should have independent simulation state (separate open positions, separate equity tracking), and trades for one symbol should not affect another symbol's state.

**Validates: Requirements 7.2**

### Property 21: Portfolio-Level Metrics Aggregation

*For any* multi-symbol backtest, the aggregate portfolio metrics should correctly combine results from all symbols (total return, portfolio drawdown, correlation matrix).

**Validates: Requirements 7.3, 7.4**

### Property 22: Portfolio Position Limit Enforcement

*For any* multi-symbol backtest, the total number of open positions across all symbols should not exceed the configured portfolio-level position limit.

**Validates: Requirements 7.6**

### Property 23: Walk-Forward Period Splitting

*For any* time window and training/testing ratio, the walk-forward split should produce non-overlapping sequential periods where training period ends before testing period begins, and all periods cover the full time window.

**Validates: Requirements 8.1**

### Property 24: Walk-Forward Sequential Execution

*For any* walk-forward analysis, the execution should run in-sample tests on training periods followed by out-of-sample tests on testing periods in chronological order.

**Validates: Requirements 8.2**

### Property 25: Walk-Forward Performance Degradation Calculation

*For any* walk-forward analysis result, the performance degradation metric should correctly calculate the difference between in-sample and out-of-sample performance.

**Validates: Requirements 8.3**

### Property 26: Walk-Forward Consistency Metrics

*For any* walk-forward analysis with multiple periods, consistency metrics (variance of returns across periods, stability score) should be calculated and included in the result.

**Validates: Requirements 8.5**

### Property 27: Progress Reporting Monotonicity

*For any* running backtest, progress percentage should be monotonically non-decreasing (never goes backward), and trade count should be monotonically non-decreasing.

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 28: Cancellation Partial Result Preservation

*For any* backtest that is cancelled mid-execution, the partial result should contain all trades executed up to the cancellation point and valid metrics calculated from those trades.

**Validates: Requirements 9.5**

### Property 29: Time Step Failure Resilience

*For any* backtest where individual time steps fail, the simulation should continue processing subsequent time steps and log the failures, unless the failure rate exceeds 10%.

**Validates: Requirements 10.3**

### Property 30: Date Range Validation

*For any* backtest configuration where end_date ≤ start_date, validation should fail before execution with a descriptive error message.

**Validates: Requirements 10.5**

### Property 31: Symbol Validation

*For any* backtest configuration with invalid ticker symbols, validation should fail before execution with a descriptive error message identifying the invalid symbols.

**Validates: Requirements 10.6**

### Property 32: Regime Classification Completeness

*For any* backtest time period, each time step should be classified into exactly one market regime (normal, volatile, trending, earnings).

**Validates: Requirements 11.1**

### Property 33: Regime-Specific Metrics Segmentation

*For any* backtest with multiple market regimes, performance metrics should be calculated separately for each regime, and the union of regime-specific trades should equal all trades.

**Validates: Requirements 11.2**

### Property 34: Regime Performance Ranking

*For any* set of regime-specific metrics, the best and worst performing regimes should be correctly identified based on total return or Sharpe ratio.

**Validates: Requirements 11.3**

### Property 35: Regime Filtering Correctness

*For any* backtest filtered to specific regimes, only time steps classified as those regimes should be included in the simulation.

**Validates: Requirements 11.4**

### Property 36: Buy-and-Hold Baseline Calculation

*For any* backtest, the buy-and-hold return should be calculated as (end_price - start_price) / start_price, and alpha should be calculated as strategy_return - buy_hold_return.

**Validates: Requirements 12.1, 12.2**

### Property 37: Risk-Adjusted Alpha Calculation

*For any* backtest, risk-adjusted alpha should correctly incorporate both return difference and Sharpe ratio comparison between strategy and buy-and-hold.

**Validates: Requirements 12.3**

### Property 38: Baseline Metrics Inclusion

*For any* saved BacktestResult, both strategy metrics and buy-and-hold baseline metrics should be present for comparison.

**Validates: Requirements 12.4**

### Property 39: Agent Decision Logging Completeness

*For any* backtest with decision logging enabled, each time step should have a DecisionLog entry containing technical_toon, event_toon, risk_toon, and fusion_decision.

**Validates: Requirements 13.1, 13.2**

### Property 40: Decision Log Filtering

*For any* decision log query with filters (confidence level, decision type), only DecisionLog entries matching the filter criteria should be returned.

**Validates: Requirements 13.3**

### Property 41: Backtest Report Completeness

*For any* generated backtest report, it should contain all required sections: summary metrics, equity curve data, trade distribution data, drawdown data, and complete trade table.

**Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**



## Error Handling

### Error Categories

**Data Availability Errors**
- Insufficient historical data for requested period
- API rate limits exceeded
- Network failures during data fetch
- Missing data for specific dates (market holidays, gaps)

**Configuration Errors**
- Invalid StrategyConfig parameters (negative values, invalid weights)
- Invalid time window (end before start, future dates)
- Invalid symbols (non-existent tickers)
- Incompatible configuration combinations

**Execution Errors**
- Agent pipeline failures at specific time steps
- LangGraph execution errors
- State corruption or data leakage
- Memory exhaustion on large backtests

**Storage Errors**
- File system write failures
- Disk space exhaustion
- Corrupted result files
- Permission errors

### Error Handling Strategies

**Graceful Degradation**
```python
# Example: Continue backtest despite individual time step failures
try:
    result = self._execute_time_step(current_time, price_slice, news_slice, symbol)
except Exception as e:
    self.logger.error(f"Time step {current_time} failed: {e}")
    self.failed_steps.append((current_time, str(e)))
    
    # Abort if failure rate exceeds threshold
    failure_rate = len(self.failed_steps) / self.total_steps
    if failure_rate > 0.10:
        raise BacktestAbortedError(f"Failure rate {failure_rate:.1%} exceeds 10% threshold")
    
    continue  # Skip this time step and continue
```

**Validation Before Execution**
```python
def validate_backtest_config(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    strategy_config: StrategyConfig
) -> List[str]:
    """Validate configuration before starting backtest."""
    errors = []
    
    if end_date <= start_date:
        errors.append(f"End date {end_date} must be after start date {start_date}")
    
    if start_date > datetime.now():
        errors.append(f"Start date {start_date} cannot be in the future")
    
    if strategy_config.max_position_size <= 0 or strategy_config.max_position_size > 1:
        errors.append(f"Invalid max_position_size: {strategy_config.max_position_size}")
    
    # Validate symbol exists
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            errors.append(f"Invalid symbol: {symbol}")
    except Exception:
        errors.append(f"Cannot validate symbol: {symbol}")
    
    return errors
```

**Partial Result Preservation**
```python
def handle_cancellation(self):
    """Save partial results when backtest is cancelled."""
    partial_result = BacktestResult(
        symbol=self.symbol,
        start_date=self.start_date,
        end_date=self.current_time,  # Actual end time
        interval=self.interval,
        strategy_config=self.strategy_config,
        initial_capital=self.initial_capital,
        trades=self.trade_agent.trade_history,
        metrics=self.performance_tracker.calculate_metrics(),
        equity_curve=self.performance_tracker.generate_equity_curve(),
        buy_hold_return_pct=self._calculate_buy_hold(self.current_time)
    )
    
    result_id = self.storage.save_result(partial_result)
    self.logger.info(f"Partial result saved: {result_id}")
    return partial_result
```

**Data Gap Handling**
```python
def handle_missing_data(
    self,
    expected_dates: List[datetime],
    actual_data: List[PriceData]
) -> List[PriceData]:
    """Fill gaps in historical data."""
    actual_dates = {pd.timestamp for pd in actual_data}
    missing_dates = [d for d in expected_dates if d not in actual_dates]
    
    if missing_dates:
        self.logger.warning(f"Missing data for {len(missing_dates)} dates")
        
        # Forward fill missing dates
        filled_data = []
        last_price = None
        
        for date in expected_dates:
            if date in actual_dates:
                price_data = next(pd for pd in actual_data if pd.timestamp == date)
                filled_data.append(price_data)
                last_price = price_data
            elif last_price:
                # Forward fill with last known price
                filled_data.append(PriceData(
                    open=last_price.close,
                    high=last_price.close,
                    low=last_price.close,
                    close=last_price.close,
                    volume=0,
                    timestamp=date
                ))
        
        return filled_data
    
    return actual_data
```

### Error Reporting

All errors should include:
- Error type and category
- Timestamp of occurrence
- Context (symbol, time step, configuration)
- Suggested remediation steps
- Stack trace for debugging (in logs, not user-facing)

Example error message:
```
BacktestValidationError: Invalid backtest configuration
  - End date 2023-01-01 must be after start date 2023-06-01
  - Invalid max_position_size: 1.5 (must be between 0 and 1)
  
Suggestion: Check your time window and strategy configuration parameters.
```



## Testing Strategy

### Dual Testing Approach

The backtesting engine requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples and edge cases
- Integration between components
- Error conditions and validation
- Concrete scenarios (e.g., gap through stop loss, specific date ranges)

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Temporal integrity and no look-ahead bias
- Mathematical correctness of calculations

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs and validate specific behaviors, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

**Library Selection**: Use `hypothesis` for Python property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test references its design document property
- Tag format: `# Feature: backtesting-engine, Property {number}: {property_text}`

**Example Property Test Structure**:

```python
from hypothesis import given, strategies as st
from datetime import datetime, timedelta
import pytest

# Feature: backtesting-engine, Property 5: Temporal Isolation (No Look-Ahead Bias)
@given(
    time_steps=st.lists(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2023, 12, 31)), min_size=10, max_size=100),
    lookback_window=st.integers(min_value=10, max_value=50)
)
def test_temporal_isolation_property(time_steps, lookback_window):
    """For any time step T, all data provided should have timestamp <= T."""
    time_steps = sorted(time_steps)  # Ensure chronological order
    
    for i, current_time in enumerate(time_steps):
        # Generate mock historical data
        all_prices = generate_mock_prices(time_steps)
        all_news = generate_mock_news(time_steps)
        
        # Get slice for current time
        window_manager = TimeWindowManager(time_steps[0], time_steps[-1], lookback_window=lookback_window)
        price_slice, news_slice = window_manager.get_historical_slice(current_time, all_prices, all_news)
        
        # Property: All timestamps should be <= current_time
        for price in price_slice:
            assert price.timestamp <= current_time, f"Look-ahead bias detected: price at {price.timestamp} > current time {current_time}"
        
        for news in news_slice:
            assert news.date <= current_time, f"Look-ahead bias detected: news at {news.date} > current time {current_time}"
```

### Unit Test Coverage

**Component-Level Tests**:

1. **Historical Data Provider** (`test_historical_data.py`)
   - Test fetching data for valid date ranges
   - Test caching behavior
   - Test handling of invalid symbols
   - Test data gap handling

2. **Time Window Manager** (`test_time_window.py`)
   - Test time step generation
   - Test historical slicing
   - Test walk-forward splitting
   - Test edge cases (single day, very long periods)

3. **Simulation Runner** (`test_simulator.py`)
   - Test single-symbol backtest execution
   - Test multi-symbol backtest execution
   - Test position monitoring and exits
   - Test equity curve tracking
   - Test cancellation handling

4. **Performance Tracker** (`test_performance.py`)
   - Test metric calculations with known trade sequences
   - Test equity curve generation
   - Test regime-specific analysis
   - Test buy-and-hold baseline calculation

5. **Storage** (`test_storage.py`)
   - Test saving and loading results
   - Test querying with filters
   - Test result comparison
   - Test export to CSV/JSON

**Integration Tests**:

1. **End-to-End Backtest** (`test_backtest_integration.py`)
   - Run complete backtest on known historical period
   - Verify all components work together
   - Validate result completeness
   - Compare against expected metrics

2. **LangGraph Integration** (`test_graph_integration.py`)
   - Test that existing agent pipeline works in backtest mode
   - Verify TOON outputs are captured correctly
   - Test agent decision logging

### Test Data Strategy

**Synthetic Data**:
- Generate deterministic price sequences for reproducible tests
- Create known patterns (trends, reversals, gaps) for edge case testing
- Use property-based testing to generate random but valid data

**Historical Data**:
- Use small, cached historical datasets for integration tests
- Select periods with known market events (earnings, volatility spikes)
- Avoid relying on live API calls in unit tests

**Example Synthetic Data Generator**:

```python
def generate_synthetic_prices(
    start_date: datetime,
    num_days: int,
    initial_price: float = 100.0,
    trend: float = 0.001,  # Daily drift
    volatility: float = 0.02  # Daily volatility
) -> List[PriceData]:
    """Generate synthetic price data for testing."""
    prices = []
    current_price = initial_price
    
    for i in range(num_days):
        date = start_date + timedelta(days=i)
        
        # Random walk with drift
        daily_return = trend + (volatility * random.gauss(0, 1))
        current_price *= (1 + daily_return)
        
        # Generate OHLC
        high = current_price * (1 + abs(random.gauss(0, 0.01)))
        low = current_price * (1 - abs(random.gauss(0, 0.01)))
        open_price = current_price * (1 + random.gauss(0, 0.005))
        
        prices.append(PriceData(
            open=open_price,
            high=high,
            low=low,
            close=current_price,
            volume=random.randint(1000000, 10000000),
            timestamp=date
        ))
    
    return prices
```

### Continuous Testing

- Run unit tests on every commit (CI/CD integration)
- Run property tests nightly (longer execution time)
- Monitor test coverage (target: >80% for core components)
- Regression tests for bug fixes (add test case for each bug)



## Implementation Approach

### Phase 1: Core Infrastructure (Foundation)

**Deliverables**:
- Historical data provider with caching
- Time window manager with temporal slicing
- Basic data models (StrategyConfig, BacktestResult, PerformanceMetrics)
- File-based storage system

**Dependencies**: None (uses existing yfinance integration)

**Validation**: Unit tests for data fetching and time window management

### Phase 2: Simulation Engine (Core Logic)

**Deliverables**:
- BacktestSimulator class with single-symbol support
- Integration with existing LangGraph pipeline
- Trade execution with slippage and commission
- Position monitoring for stop loss and target exits
- Equity curve tracking

**Dependencies**: Phase 1 complete

**Validation**: Integration tests with synthetic data, verify temporal isolation

### Phase 3: Performance Analytics (Metrics)

**Deliverables**:
- PerformanceTracker with comprehensive metrics
- Buy-and-hold baseline calculation
- Regime classification and regime-specific analysis
- Report generation (JSON/CSV export)

**Dependencies**: Phase 2 complete

**Validation**: Unit tests with known trade sequences, verify metric calculations

### Phase 4: Advanced Features (Extensions)

**Deliverables**:
- Multi-symbol backtesting with portfolio-level tracking
- Walk-forward analysis
- Progress monitoring and cancellation support
- Agent decision logging
- Result querying and comparison

**Dependencies**: Phase 3 complete

**Validation**: End-to-end tests with multi-symbol scenarios

### Phase 5: API and UI Integration (User-Facing)

**Deliverables**:
- FastAPI endpoints for backtest execution and result retrieval
- Frontend components for backtest configuration and result visualization
- Equity curve charts, trade tables, metric dashboards

**Dependencies**: Phase 4 complete

**Validation**: Manual testing with UI, API integration tests

### Development Guidelines

**Code Organization**:
```
backtesting/
├── __init__.py
├── historical_data.py      # Phase 1
├── time_window.py          # Phase 1
├── models.py               # Phase 1
├── storage.py              # Phase 1
├── simulator.py            # Phase 2
├── performance.py          # Phase 3
├── regime_classifier.py    # Phase 3
└── report_generator.py     # Phase 3

test_backtesting/
├── test_historical_data.py
├── test_time_window.py
├── test_simulator.py
├── test_performance.py
├── test_storage.py
└── test_integration.py
```

**Integration Points**:
- Reuse `agents/graph.py` without modification
- Extend `analytics/evaluation.py` with additional metrics
- Add endpoints to `backend/app.py`
- Create new React components in `frontend/src/`

**Performance Considerations**:
- Cache historical data aggressively (avoid redundant API calls)
- Use pandas for efficient time-series operations
- Consider parallel execution for multi-symbol backtests (Phase 4)
- Limit decision logging to reduce memory usage on long backtests
- Implement progress callbacks for long-running backtests

**Security Considerations**:
- Validate all user inputs (symbols, dates, configuration)
- Sanitize file paths for result storage
- Rate limit backtest execution to prevent resource exhaustion
- Implement user-level result isolation (future: multi-user support)

## Future Enhancements

**Database Migration**:
- Move from file-based storage to PostgreSQL
- Enable complex queries and analytics
- Support concurrent access and multi-user scenarios

**Optimization Engine**:
- Grid search over strategy parameters
- Genetic algorithm for parameter optimization
- Bayesian optimization for efficient search

**Advanced Analytics**:
- Monte Carlo simulation for confidence intervals
- Sensitivity analysis for parameter robustness
- Factor attribution analysis

**Real-Time Backtesting**:
- Stream historical data in real-time simulation mode
- Test latency-sensitive strategies
- Simulate order book dynamics

**Machine Learning Integration**:
- Use backtest results to train learning agent
- Automated pattern recognition from historical trades
- Reinforcement learning for strategy optimization

## Conclusion

The Backtesting Engine design provides a comprehensive solution for evaluating AlphaMind AI trading strategies on historical data. By reusing the existing agent pipeline and maintaining strict temporal isolation, the system ensures realistic and unbiased performance evaluation.

The modular architecture enables incremental development, starting with core functionality and progressively adding advanced features. The dual testing approach (unit tests + property-based tests) ensures correctness and robustness across a wide range of scenarios.

Key design principles:
- **Temporal Integrity**: Strict prevention of look-ahead bias
- **Reusability**: Leverages existing agent pipeline without modification
- **Extensibility**: Modular design supports future enhancements
- **Testability**: Comprehensive property-based testing for correctness
- **Realism**: Accurate simulation of slippage, commission, and execution constraints

This design positions AlphaMind AI to validate strategies rigorously before deployment, enabling data-driven optimization and continuous improvement.

