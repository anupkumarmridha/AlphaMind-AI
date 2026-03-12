# Implementation Plan: Backtesting Engine

## Overview

This implementation plan follows a 5-phase approach to build the Backtesting Engine for AlphaMind AI. The engine will enable strategy validation on historical market data by simulating the complete multi-agent decision pipeline over past time periods while maintaining strict temporal isolation to prevent look-ahead bias.

The implementation reuses the existing LangGraph orchestration (`agents/graph.py`), stateless agent architecture, and TOON communication format. Each phase builds incrementally on the previous phase, with comprehensive property-based testing to ensure correctness.

## Tasks

- [x] 1. Phase 1: Core Infrastructure - Set up foundation components
  - [x] 1.1 Create backtesting module structure and data models
    - Create `backtesting/__init__.py` module
    - Implement `StrategyConfig` Pydantic model with agent weights, risk parameters, execution costs
    - Implement `SlippageModel` Pydantic model with `calculate_slippage()` method supporting fixed, volume-based, and volatility-based models
    - Implement `PerformanceMetrics` Pydantic model with all required metric fields
    - Implement `DecisionLog` Pydantic model for agent decision tracking
    - Implement `BacktestResult` Pydantic model with complete result structure
    - _Requirements: 3.1, 3.2, 4.1-4.9, 6.2-6.5_

  - [ ]* 1.2 Write property test for StrategyConfig validation
    - **Property 11: Configuration Validation Rejection**
    - **Validates: Requirements 3.6, 10.2**

  - [x] 1.3 Implement Historical Data Provider with caching
    - Create `backtesting/historical_data.py` module
    - Implement `HistoricalDataProvider.fetch_historical_prices()` using yfinance with start/end dates
    - Implement `HistoricalDataProvider.fetch_historical_news()` for historical news data
    - Implement in-memory caching with `get_cached_data()` and `cache_data()` methods
    - Handle API rate limits and data gaps gracefully
    - Return data in existing `PriceData` and `NewsData` Pydantic schemas
    - _Requirements: 1.1, 1.2, 1.3, 1.6_

  - [ ]* 1.4 Write property tests for Historical Data Provider
    - **Property 1: Historical Data Temporal Bounds**
    - **Validates: Requirements 1.1, 1.2**
    - **Property 2: Historical Data Schema Consistency**
    - **Validates: Requirements 1.3**
    - **Property 3: Historical Data Caching Idempotence**
    - **Validates: Requirements 1.6**

  - [x] 1.5 Implement Time Window Manager
    - Create `backtesting/time_window.py` module
    - Implement `TimeWindowManager.__init__()` with start_date, end_date, interval, lookback_window parameters
    - Implement `generate_time_steps()` to create chronological list of time steps
    - Implement `get_historical_slice()` to return data up to current_time (prevents look-ahead bias)
    - Implement `split_walk_forward()` for training/testing period splitting
    - _Requirements: 2.1, 2.2, 2.4, 8.1_

  - [ ]* 1.6 Write property tests for Time Window Manager
    - **Property 4: Chronological Time Step Ordering**
    - **Validates: Requirements 2.1**
    - **Property 5: Temporal Isolation (No Look-Ahead Bias)**
    - **Validates: Requirements 2.2, 2.4**
    - **Property 23: Walk-Forward Period Splitting**
    - **Validates: Requirements 8.1**

  - [x] 1.7 Implement file-based storage system
    - Create `backtesting/storage.py` module
    - Implement `BacktestStorage.__init__()` with configurable storage path
    - Implement `save_result()` to save BacktestResult as JSON file with unique ID
    - Implement `load_result()` to load BacktestResult by ID
    - Implement `query_results()` with filtering by symbol, date range, strategy name
    - Implement `compare_results()` to generate comparison DataFrame
    - Implement `export_to_csv()` for CSV export
    - Create `backtests/` directory for result storage
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [ ]* 1.8 Write property tests for storage system
    - **Property 9: Strategy Configuration Round Trip**
    - **Validates: Requirements 3.3, 3.4**
    - **Property 17: Backtest Result Unique Identification**
    - **Validates: Requirements 6.1**
    - **Property 18: Backtest Result Completeness**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
    - **Property 19: Backtest Result Query Filtering**
    - **Validates: Requirements 6.6**

- [x] 2. Checkpoint - Verify Phase 1 foundation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Phase 2: Simulation Engine - Implement core backtesting logic
  - [x] 3.1 Implement BacktestSimulator core structure
    - Create `backtesting/simulator.py` module
    - Implement `BacktestSimulator.__init__()` with strategy_config, slippage_model, initial_capital
    - Initialize TradeAgent instance for position tracking
    - Initialize PerformanceTracker for metrics
    - Set up equity curve tracking list
    - _Requirements: 3.2, 5.3_

  - [x] 3.2 Implement single-symbol backtest execution
    - Implement `run_backtest()` method for single symbol
    - Fetch historical data using HistoricalDataProvider
    - Create TimeWindowManager for the specified period
    - Generate time steps and iterate chronologically
    - Call `_execute_time_step()` for each time step
    - Handle errors with graceful degradation (continue on individual failures, abort if >10% fail)
    - Return complete BacktestResult
    - _Requirements: 2.1, 2.2, 10.3, 10.4_

  - [ ]* 3.3 Write property tests for backtest execution flow
    - **Property 4: Chronological Time Step Ordering**
    - **Validates: Requirements 2.1**
    - **Property 29: Time Step Failure Resilience**
    - **Validates: Requirements 10.3**

  - [x] 3.4 Implement time step execution with LangGraph integration
    - Implement `_execute_time_step()` method
    - Build TradingState with historical data slice (up to current time only)
    - Execute existing `alphamind_graph` from `agents/graph.py`
    - Extract trade decision from graph output
    - Apply slippage using SlippageModel
    - Apply commission fees
    - Record trade if executed
    - Log agent decisions (technical_toon, event_toon, risk_toon, fusion_decision)
    - _Requirements: 2.2, 2.3, 2.4, 2.6, 5.1, 5.2, 13.1, 13.2_

  - [ ]* 3.5 Write property tests for time step execution
    - **Property 5: Temporal Isolation (No Look-Ahead Bias)**
    - **Validates: Requirements 2.2, 2.4**
    - **Property 6: Complete Agent Pipeline Execution**
    - **Validates: Requirements 2.3**
    - **Property 7: State Isolation Between Time Steps**
    - **Validates: Requirements 2.5**
    - **Property 8: Trade Execution Cost Application**
    - **Validates: Requirements 2.6, 5.1, 5.2**

  - [x] 3.6 Implement position monitoring and exit logic
    - Implement `_monitor_positions()` method
    - Check each open position for stop loss trigger
    - Check each open position for target trigger
    - Handle gap-through scenarios (execute at gap price, not stop price)
    - Close positions when triggered
    - Update equity curve after position changes
    - _Requirements: 5.4, 5.5, 5.7_

  - [ ]* 3.7 Write property tests for position monitoring
    - **Property 15: Stop Loss and Target Monitoring**
    - **Validates: Requirements 5.4, 5.5**

  - [x] 3.8 Implement equity curve tracking and capital constraints
    - Implement `_update_equity_curve()` method
    - Calculate current portfolio equity at each time step
    - Record timestamp and equity value
    - Enforce position sizing limits based on available capital
    - Prevent opening positions when capital insufficient
    - Enforce max_open_positions limit
    - _Requirements: 4.8, 5.3, 5.6_

  - [ ]* 3.9 Write property tests for capital constraints
    - **Property 10: Strategy Configuration Consistency**
    - **Validates: Requirements 3.2**
    - **Property 14: Position Sizing Capital Constraint**
    - **Validates: Requirements 5.3**
    - **Property 16: Maximum Position Limit Enforcement**
    - **Validates: Requirements 5.6**

- [x] 4. Checkpoint - Verify Phase 2 simulation engine
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Phase 3: Performance Analytics - Implement comprehensive metrics
  - [x] 5.1 Implement PerformanceTracker core functionality
    - Create `backtesting/performance.py` module
    - Implement `PerformanceTracker.__init__()` with empty state
    - Implement `record_trade()` to add closed trades to history
    - Implement `record_equity_point()` to track equity over time
    - _Requirements: 4.1-4.9_

  - [x] 5.2 Implement comprehensive metrics calculation
    - Implement `calculate_metrics()` method
    - Calculate win_rate from closed trades
    - Calculate profit_factor (gross profit / gross loss)
    - Calculate total_return_pct
    - Calculate max_drawdown_pct from equity curve
    - Calculate sharpe_ratio from trade returns
    - Calculate avg_trade_duration_hours
    - Calculate trades_per_day
    - Calculate longest_win_streak and longest_loss_streak
    - Return PerformanceMetrics model
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.9_

  - [ ]* 5.3 Write property test for metrics calculation
    - **Property 12: Performance Metrics Calculation Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.9**

  - [x] 5.4 Implement equity curve generation
    - Implement `generate_equity_curve()` method
    - Return list of (timestamp, equity) tuples in chronological order
    - _Requirements: 4.8_

  - [ ]* 5.5 Write property test for equity curve
    - **Property 13: Equity Curve Monotonic Recording**
    - **Validates: Requirements 4.8**

  - [x] 5.6 Implement buy-and-hold baseline calculation
    - Implement `calculate_buy_and_hold_baseline()` method
    - Calculate simple buy-and-hold return: (end_price - start_price) / start_price
    - Calculate alpha: strategy_return - buy_hold_return
    - Calculate risk-adjusted alpha using Sharpe ratio comparison
    - _Requirements: 12.1, 12.2, 12.3_

  - [ ]* 5.7 Write property tests for baseline comparison
    - **Property 36: Buy-and-Hold Baseline Calculation**
    - **Validates: Requirements 12.1, 12.2**
    - **Property 37: Risk-Adjusted Alpha Calculation**
    - **Validates: Requirements 12.3**
    - **Property 38: Baseline Metrics Inclusion**
    - **Validates: Requirements 12.4**

  - [x] 5.8 Implement regime classification and analysis
    - Create `backtesting/regime_classifier.py` module
    - Implement `classify_regime()` function to classify time periods into regimes (normal, volatile, trending, earnings)
    - Implement `calculate_regime_metrics()` in PerformanceTracker
    - Calculate metrics separately for each regime
    - Identify best and worst performing regimes
    - Calculate regime transition impact
    - _Requirements: 11.1, 11.2, 11.3, 11.5_

  - [ ]* 5.9 Write property tests for regime analysis
    - **Property 32: Regime Classification Completeness**
    - **Validates: Requirements 11.1**
    - **Property 33: Regime-Specific Metrics Segmentation**
    - **Validates: Requirements 11.2**
    - **Property 34: Regime Performance Ranking**
    - **Validates: Requirements 11.3**

  - [x] 5.10 Implement report generation
    - Create `backtesting/report_generator.py` module
    - Implement `generate_summary_report()` to create report with key metrics
    - Include equity curve data for visualization
    - Include trade distribution data (wins vs losses histogram)
    - Include drawdown chart data
    - Include complete trade table with entry/exit details
    - Support JSON and CSV export formats
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [ ]* 5.11 Write property test for report completeness
    - **Property 41: Backtest Report Completeness**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**

- [x] 6. Checkpoint - Verify Phase 3 analytics
  - Ensure all tests pass, ask the user if questions arise.

- [-] 7. Phase 4: Advanced Features - Multi-symbol, walk-forward, monitoring
  - [ ] 7.1 Implement multi-symbol backtesting
    - Implement `run_multi_symbol_backtest()` in BacktestSimulator
    - Run simulations for each symbol independently
    - Track separate open positions per symbol
    - Track separate equity per symbol
    - Enforce portfolio-level position limits across all symbols
    - _Requirements: 7.1, 7.2, 7.6_

  - [ ]* 7.2 Write property tests for multi-symbol backtesting
    - **Property 20: Multi-Symbol Simulation Isolation**
    - **Validates: Requirements 7.2**
    - **Property 22: Portfolio Position Limit Enforcement**
    - **Validates: Requirements 7.6**

  - [ ] 7.3 Implement portfolio-level metrics aggregation
    - Extend PerformanceTracker to handle multi-symbol results
    - Calculate aggregate portfolio metrics (total return, portfolio drawdown)
    - Calculate correlation matrix between symbol performances
    - Support parallel execution of multi-symbol backtests (optional optimization)
    - _Requirements: 7.3, 7.4, 7.5_

  - [ ]* 7.4 Write property test for portfolio metrics
    - **Property 21: Portfolio-Level Metrics Aggregation**
    - **Validates: Requirements 7.3, 7.4**

  - [ ] 7.5 Implement walk-forward analysis
    - Implement walk-forward execution logic in BacktestSimulator
    - Use TimeWindowManager.split_walk_forward() to create periods
    - Run sequential in-sample and out-of-sample tests
    - Calculate performance degradation between periods
    - Calculate consistency metrics across periods (variance, stability score)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 7.6 Write property tests for walk-forward analysis
    - **Property 24: Walk-Forward Sequential Execution**
    - **Validates: Requirements 8.2**
    - **Property 25: Walk-Forward Performance Degradation Calculation**
    - **Validates: Requirements 8.3**
    - **Property 26: Walk-Forward Consistency Metrics**
    - **Validates: Requirements 8.5**

  - [ ] 7.7 Implement progress monitoring and cancellation
    - Add progress tracking to BacktestSimulator
    - Report progress percentage during execution
    - Report current time step being processed
    - Report number of trades executed so far
    - Implement cancellation support with signal handling
    - Implement `handle_cancellation()` to save partial results
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 7.8 Write property tests for progress monitoring
    - **Property 27: Progress Reporting Monotonicity**
    - **Validates: Requirements 9.1, 9.2, 9.3**
    - **Property 28: Cancellation Partial Result Preservation**
    - **Validates: Requirements 9.5**

  - [ ] 7.9 Implement agent decision logging
    - Add decision logging to BacktestSimulator
    - Create DecisionLog entries at each time step
    - Include all agent TOON outputs (technical_toon, event_toon, risk_toon)
    - Include fusion_decision and trade_executed
    - Support filtering decision logs by confidence level or decision type
    - Support exporting decision logs for external analysis
    - Make decision logging optional (can be disabled for large backtests)
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

  - [ ]* 7.10 Write property tests for decision logging
    - **Property 39: Agent Decision Logging Completeness**
    - **Validates: Requirements 13.1, 13.2**
    - **Property 40: Decision Log Filtering**
    - **Validates: Requirements 13.3**

  - [x] 7.11 Implement validation and error handling
    - Implement `validate_backtest_config()` function
    - Validate date range (end_date > start_date, no future dates)
    - Validate symbol existence using yfinance
    - Validate StrategyConfig parameters (ranges, weights)
    - Implement error handling for insufficient historical data
    - Implement data gap handling with forward fill
    - Return descriptive error messages with remediation suggestions
    - _Requirements: 10.1, 10.2, 10.5, 10.6_

  - [ ]* 7.12 Write property tests for validation
    - **Property 30: Date Range Validation**
    - **Validates: Requirements 10.5**
    - **Property 31: Symbol Validation**
    - **Validates: Requirements 10.6**

  - [ ] 7.13 Implement regime filtering
    - Add regime filtering support to BacktestSimulator
    - Accept list of regimes to include in backtest
    - Filter time steps to only include specified regimes
    - Calculate metrics only for filtered periods
    - _Requirements: 11.4_

  - [ ]* 7.14 Write property test for regime filtering
    - **Property 35: Regime Filtering Correctness**
    - **Validates: Requirements 11.4**

- [x] 8. Checkpoint - Verify Phase 4 advanced features
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Phase 5: API and UI Integration - User-facing interfaces
  - [x] 9.1 Implement FastAPI endpoints for backtesting
    - Add `/api/backtest/run` POST endpoint to `backend/app.py`
    - Accept BacktestRequest with symbol, date range, strategy config
    - Execute backtest asynchronously (return job ID immediately)
    - Add `/api/backtest/status/{job_id}` GET endpoint for progress monitoring
    - Add `/api/backtest/results/{result_id}` GET endpoint to retrieve results
    - Add `/api/backtest/results` GET endpoint to query results with filters
    - Add `/api/backtest/compare` POST endpoint to compare multiple results
    - Add `/api/backtest/cancel/{job_id}` POST endpoint to cancel running backtest
    - Enable CORS for frontend access
    - _Requirements: 6.6, 6.7, 9.1, 9.2, 9.3, 9.4_

  - [ ]* 9.2 Write integration tests for API endpoints
    - Test backtest execution via API
    - Test progress monitoring
    - Test result retrieval and querying
    - Test cancellation

  - [x] 9.3 Create backtest configuration UI component
    - Create `frontend/src/components/BacktestConfig.jsx`
    - Add form inputs for symbol, date range, interval
    - Add strategy configuration inputs (weights, risk parameters)
    - Add validation for form inputs
    - Add "Run Backtest" button to trigger API call
    - Display loading state and progress during execution
    - Use Tailwind CSS for styling
    - _Requirements: 3.1, 3.2, 9.1_

  - [x] 9.4 Create backtest results visualization component
    - Create `frontend/src/components/BacktestResults.jsx`
    - Display performance metrics in card layout
    - Implement equity curve chart using Chart.js
    - Implement drawdown chart using Chart.js
    - Implement trade distribution histogram using Chart.js
    - Display trade table with entry/exit details, sortable columns
    - Add export buttons for JSON and CSV
    - Use Tailwind CSS for styling
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [x] 9.5 Create backtest comparison UI component
    - Create `frontend/src/components/BacktestComparison.jsx`
    - Allow selecting multiple backtest results for comparison
    - Display side-by-side metrics comparison table
    - Display overlaid equity curves for visual comparison
    - Highlight best/worst performers
    - Use Tailwind CSS for styling
    - _Requirements: 6.7_

  - [x] 9.6 Integrate backtesting UI into main application
    - Add "Backtesting" navigation item to `frontend/src/App.jsx`
    - Create routing for backtest pages
    - Wire up components with API endpoints
    - Test end-to-end user flow

- [x] 10. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at phase boundaries
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- The implementation reuses existing components: `agents/graph.py`, `data/schema.py`, `models/trade.py`, `analytics/evaluation.py`
- All code follows Python type hints, Pydantic v2 models, and stateless patterns
- TOON format is used for agent communication, JSON for API responses
