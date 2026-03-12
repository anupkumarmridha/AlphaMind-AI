# Bugfix Requirements Document

## Introduction

The AlphaMind AI multi-agent trading system contains multiple critical bugs across all agents that can cause system crashes, incorrect calculations, silent failures, and poor trading decisions. These bugs affect the TechnicalAgent (indicator calculations), RiskAgent (risk assessment), FusionAgent (signal synthesis), TradeAgent (trade execution), LearningAgent (database operations), and Graph orchestration (workflow resilience). The issues range from division by zero errors and NaN handling to missing validation, unbounded database growth, and lack of error recovery mechanisms. These bugs compromise system reliability, trading accuracy, and operational stability.

## Bug Analysis

### Current Behavior (Defect)

#### TechnicalAgent Calculation Errors

1.1 WHEN calculating RSI and gain or loss rolling mean equals zero THEN the system performs division by zero (rs = gain / loss) causing a crash with ZeroDivisionError

1.2 WHEN RSI calculation produces NaN or inf values due to insufficient price variation THEN the system propagates these invalid values to downstream agents without validation or handling

1.3 WHEN price_history contains all zeros, missing values, or invalid data THEN the system attempts calculations without validation causing incorrect indicator values or crashes

1.4 WHEN volume indicators are calculated with zero volume data THEN the system may produce NaN or inf values that are not caught before use

1.5 WHEN calculated indicators (EMA, RSI, volume ratios) are used in comparisons THEN the system does not perform bounds checking leading to invalid logic branches

#### RiskAgent Assessment Failures

1.6 WHEN price_history has fewer than 14 data points THEN the system returns "insufficient data" without specifying the minimum required count making debugging difficult

1.7 WHEN extreme market conditions occur (flash crashes, circuit breakers, trading halts) THEN the system has no special handling and may produce inappropriate risk assessments

1.8 WHEN risk thresholds are evaluated THEN the system uses hardcoded values without regime-specific adjustments leading to inappropriate risk levels in different market conditions

1.9 WHEN calculating risk scores THEN the system does not consider gap risk or overnight risk which can cause significant losses

1.10 WHEN RSI or volatility calculations produce NaN values THEN the system checks for NaN but returns early without logging the issue for debugging

#### FusionAgent Parsing and Validation Issues

1.11 WHEN parsing TOON format scores and ValueError exceptions occur THEN the system silently defaults to 0 without logging the parsing error making debugging impossible

1.12 WHEN confidence adjustments are applied to weights THEN the system does not validate that weights sum correctly after adjustment potentially causing incorrect signal calculations

1.13 WHEN context agent weight is redistributed to technical weight THEN the system performs this without documentation or validation of the redistribution logic

1.14 WHEN parsing TOON fields that are missing or malformed THEN the system defaults to 0 beyond the try-except blocks without comprehensive validation

1.15 WHEN final_signal is calculated THEN the system does not perform bounds checking before using it in decision logic

#### TradeAgent Execution Risks

1.16 WHEN multiple trades are opened THEN the system does not enforce maximum position limits across all open trades allowing over-exposure

1.17 WHEN opening new trades THEN the system does not check capital availability before execution potentially causing negative account balances

1.18 WHEN calculating stop loss and target prices THEN the system does not account for market hours, gaps, or after-hours price movements

1.19 WHEN orders are submitted THEN the system has no handling for partial fills or order rejection scenarios

1.20 WHEN position_size is calculated THEN the system does not validate that the size is within acceptable bounds (e.g., not negative, not exceeding limits)

#### LearningAgent Database Issues

1.21 WHEN using SQLite as database fallback THEN the system will fail silently on pgvector operations since SQLite does not support vector extensions

1.22 WHEN database operations are performed THEN the system has no connection pooling or retry logic causing failures on transient connection issues

1.23 WHEN storing embeddings THEN the system has embedding dimension hardcoded to 1536 making it inflexible for different embedding models

1.24 WHEN validation records accumulate over time THEN the system has no cleanup mechanism causing the database to grow indefinitely

1.25 WHEN database connection failures occur THEN the system has no error handling or graceful degradation causing agent failures

#### Graph Orchestration Failures

1.26 WHEN agent operations take too long to complete THEN the system has no timeout handling causing the workflow to hang indefinitely

1.27 WHEN agents repeatedly fail THEN the system has no circuit breaker mechanism to prevent continuous retry attempts

1.28 WHEN state flows between nodes THEN the system does not validate state structure or required fields between transitions

1.29 WHEN a node fails mid-execution THEN the system has no rollback mechanism to restore previous state or clean up partial changes

1.30 WHEN state transitions occur THEN the system does not log transitions making debugging workflow issues extremely difficult

### Expected Behavior (Correct)

#### TechnicalAgent Calculation Fixes

2.1 WHEN calculating RSI and loss rolling mean equals zero THEN the system SHALL handle the division by zero case by setting RSI to 100 (maximum bullish) or using a small epsilon value to avoid division by zero

2.2 WHEN RSI calculation produces NaN or inf values THEN the system SHALL detect these invalid values and either use fallback calculations or return an error state with appropriate reason

2.3 WHEN price_history is received THEN the system SHALL validate that data contains valid numeric values, sufficient variation, and no all-zero sequences before performing calculations

2.4 WHEN volume indicators are calculated THEN the system SHALL check for zero volume conditions and handle them gracefully by returning neutral indicators or skipping volume-based signals

2.5 WHEN using calculated indicators in logic THEN the system SHALL perform bounds checking to ensure values are within expected ranges before comparisons

#### RiskAgent Assessment Improvements

2.6 WHEN price_history has insufficient data THEN the system SHALL return a detailed error message specifying the minimum required data points (e.g., "insufficient data: need at least 14 points, got 10")

2.7 WHEN extreme market conditions are detected (volatility > 10%, price gaps > 5%) THEN the system SHALL apply special risk handling with elevated risk scores and appropriate warnings

2.8 WHEN evaluating risk thresholds THEN the system SHALL use regime-specific adjustments (e.g., higher thresholds during earnings, lower during volatile periods)

2.9 WHEN calculating risk scores THEN the system SHALL incorporate gap risk analysis by checking for overnight price changes and market hour transitions

2.10 WHEN RSI or volatility calculations produce NaN values THEN the system SHALL log the issue with context (data points, values) before returning the error state

#### FusionAgent Parsing and Validation Fixes

2.11 WHEN parsing TOON format scores and ValueError exceptions occur THEN the system SHALL log the parsing error with the problematic value and field name before defaulting to 0

2.12 WHEN confidence adjustments are applied to weights THEN the system SHALL validate that all weights sum to approximately 1.0 (within tolerance) and normalize if needed

2.13 WHEN context agent weight is redistributed THEN the system SHALL document the redistribution logic and validate that total weight allocation remains correct

2.14 WHEN parsing TOON fields THEN the system SHALL implement comprehensive validation for all expected fields and log warnings for missing or malformed fields

2.15 WHEN final_signal is calculated THEN the system SHALL perform bounds checking to ensure the value is within [-1, 1] range and clamp if necessary

#### TradeAgent Execution Safeguards

2.16 WHEN opening new trades THEN the system SHALL enforce maximum position limits by checking total exposure across all open trades before execution

2.17 WHEN opening new trades THEN the system SHALL check available capital and reject trades that would exceed account balance or margin requirements

2.18 WHEN calculating stop loss and target prices THEN the system SHALL account for market hours and apply wider stops for overnight positions to handle gap risk

2.19 WHEN orders are submitted THEN the system SHALL implement handling for partial fills (update position size) and order rejections (log and notify)

2.20 WHEN position_size is calculated THEN the system SHALL validate that size is positive, non-zero for trades, and does not exceed maximum allocation limits

#### LearningAgent Database Improvements

2.21 WHEN SQLite is used as database THEN the system SHALL detect the lack of pgvector support and either disable vector operations or provide a fallback implementation with warnings

2.22 WHEN database operations are performed THEN the system SHALL implement connection pooling and retry logic with exponential backoff for transient failures

2.23 WHEN storing embeddings THEN the system SHALL make embedding dimension configurable through environment variables or initialization parameters

2.24 WHEN validation records accumulate THEN the system SHALL implement automatic cleanup of records older than a configurable retention period (e.g., 90 days)

2.25 WHEN database connection failures occur THEN the system SHALL implement error handling with graceful degradation (e.g., skip learning updates but continue trading)

#### Graph Orchestration Resilience

2.26 WHEN agent operations are executed THEN the system SHALL implement timeout handling with configurable timeout values per agent type

2.27 WHEN agents fail repeatedly THEN the system SHALL implement circuit breaker pattern to stop retries after N failures and require manual reset

2.28 WHEN state flows between nodes THEN the system SHALL validate that required fields are present and have correct types before proceeding to next node

2.29 WHEN a node fails mid-execution THEN the system SHALL implement rollback mechanism to restore state to last known good checkpoint

2.30 WHEN state transitions occur THEN the system SHALL log all transitions with timestamps, node names, and key state values for debugging

### Unchanged Behavior (Regression Prevention)

#### TechnicalAgent Preservation

3.1 WHEN price_history has 50 or more data points THEN the system SHALL CONTINUE TO calculate EMA_20, EMA_50, RSI_14, and volume trends as currently implemented

3.2 WHEN technical score is calculated THEN the system SHALL CONTINUE TO use the 0.0 to 1.0 scale with 0.5 as neutral baseline

3.3 WHEN trend and momentum are determined THEN the system SHALL CONTINUE TO use the current logic (EMA crossover for trend, RSI thresholds for momentum)

3.4 WHEN technical analysis is complete THEN the system SHALL CONTINUE TO return TOON format with technical_score, trend, momentum, and reason fields

#### RiskAgent Preservation

3.5 WHEN risk analysis is performed with valid data THEN the system SHALL CONTINUE TO calculate RSI_14 and 14-period volatility as primary risk indicators

3.6 WHEN risk levels are assigned THEN the system SHALL CONTINUE TO use the four-tier system (LOW, MEDIUM, HIGH, CRITICAL)

3.7 WHEN risk score thresholds are evaluated THEN the system SHALL CONTINUE TO use the current threshold values (0.3, 0.5, 0.8) as baseline before regime adjustments

3.8 WHEN risk analysis is complete THEN the system SHALL CONTINUE TO return TOON format with risk_score, risk_level, and reason fields

#### FusionAgent Preservation

3.9 WHEN synthesizing signals THEN the system SHALL CONTINUE TO use regime-dependent weights (earnings, volatile, normal regimes)

3.10 WHEN CRITICAL risk level is detected THEN the system SHALL CONTINUE TO enforce hard veto and return NO_TRADE decision

3.11 WHEN decision thresholds are evaluated THEN the system SHALL CONTINUE TO use ±0.4 thresholds for BUY/SELL decisions

3.12 WHEN position sizing is calculated THEN the system SHALL CONTINUE TO use MAX_ALLOCATION of 10% scaled by confidence

3.13 WHEN fusion is complete THEN the system SHALL CONTINUE TO return decision, confidence, position_size, and reason fields

#### TradeAgent Preservation

3.14 WHEN trades are executed THEN the system SHALL CONTINUE TO apply slippage simulation using the configured basis points

3.15 WHEN trades are executed THEN the system SHALL CONTINUE TO apply commission fees as percentage of trade value

3.16 WHEN stop loss and targets are set THEN the system SHALL CONTINUE TO use 2% stop loss and 4% target as defaults (1:2 risk-reward)

3.17 WHEN monitoring open trades THEN the system SHALL CONTINUE TO check current price against stop loss and target levels

3.18 WHEN trades are closed THEN the system SHALL CONTINUE TO move them from open_trades to trade_history

#### LearningAgent Preservation

3.19 WHEN trade patterns are stored THEN the system SHALL CONTINUE TO use the TradePattern model with symbol, action, reason_toon, market_regime, and embedding fields

3.20 WHEN sentiment validation is tracked THEN the system SHALL CONTINUE TO use the SentimentValidation model with all current fields

3.21 WHEN dynamic weights are requested THEN the system SHALL CONTINUE TO return regime-specific weight dictionaries

3.22 WHEN sentiment accuracy metrics are calculated THEN the system SHALL CONTINUE TO compute overall accuracy, confidence-weighted accuracy, and per-sentiment-type accuracy

#### Graph Orchestration Preservation

3.23 WHEN the trading workflow is executed THEN the system SHALL CONTINUE TO follow the sequence: fetch_data → [technical, event, risk, context] → fusion → trade

3.24 WHEN market data is fetched THEN the system SHALL CONTINUE TO use PriceService for price history and NewsService for news

3.25 WHEN agents run in parallel THEN the system SHALL CONTINUE TO execute technical, event, risk, and context agents concurrently after data fetch

3.26 WHEN fusion agent runs THEN the system SHALL CONTINUE TO wait for all upstream agents to complete before synthesizing signals

3.27 WHEN the workflow completes THEN the system SHALL CONTINUE TO return TradingState with all agent outputs and trade execution results
