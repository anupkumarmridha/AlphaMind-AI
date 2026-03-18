# Implementation Plan

## Phase 1: Bug Condition Exploration Tests

- [x] 1. Write bug condition exploration tests for all 30 bugs
  - **Property 1: Bug Condition** - Multi-Agent System Bugs Exploration
  - **CRITICAL**: These tests MUST FAIL on unfixed code - failure confirms the bugs exist
  - **DO NOT attempt to fix the tests or the code when they fail**
  - **NOTE**: These tests encode the expected behavior - they will validate the fixes when they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate all 30 bugs exist
  - **Test Organization**: Create test files for each component with scoped test cases
  - Create `test_bugfix_technical_agent.py` for TechnicalAgent bugs 1.1-1.5
  - Create `test_bugfix_risk_agent.py` for RiskAgent bugs 1.6-1.10
  - Create `test_bugfix_fusion_agent.py` for FusionAgent bugs 1.11-1.15
  - Create `test_bugfix_trade_agent.py` for TradeAgent bugs 1.16-1.20
  - Create `test_bugfix_learning_agent.py` for LearningAgent bugs 1.21-1.25
  - Create `test_bugfix_graph_orchestration.py` for Graph bugs 1.26-1.30
  - Each test file should have a `run()` function that executes all tests for that component
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct - it proves the bugs exist)
  - Document counterexamples found (crashes, incorrect values, silent failures)
  - Mark task complete when tests are written, run, and failures are documented
  - _Requirements: 1.1-1.30 (all bug conditions from bugfix.md)_

## Phase 2: Preservation Property Tests

- [x] 2. Write preservation property tests (BEFORE implementing fixes)
  - **Property 2: Preservation** - Existing Functionality Preservation
  - **IMPORTANT**: Follow observation-first methodology
  - **Test Organization**: Add preservation tests to existing test files or create new ones
  - Create preservation tests for TechnicalAgent (valid price history, TOON format, calculations)
  - Create preservation tests for RiskAgent (valid risk calculations, thresholds, TOON format)
  - Create preservation tests for FusionAgent (valid synthesis, regime weights, decision thresholds)
  - Create preservation tests for TradeAgent (valid execution, slippage, commission, stops)
  - Create preservation tests for LearningAgent (valid storage, schema, dynamic weights)
  - Create preservation tests for Graph (valid workflow, state flow, parallel execution)
  - Observe behavior on UNFIXED code for non-buggy inputs (valid data, proper formatting)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1-3.27 (all preservation requirements from bugfix.md)_


## Phase 3: Implementation

- [x] 3. Fix TechnicalAgent calculation errors (Bugs 1.1-1.5)

  - [x] 3.1 Add input validation helper
    - Create `_validate_price_history()` static method
    - Check minimum length (50 points required)
    - Validate no all-zero sequences in close prices
    - Validate no NaN or inf values in input data
    - Return validation result with detailed error message
    - _Bug_Condition: isBugCondition(input) where input.type == "price_history" AND (hasZeroDivisionRisk OR hasInvalidData)_
    - _Expected_Behavior: Validate inputs before processing, return detailed error messages_
    - _Preservation: Maintain existing calculation logic for valid inputs (Requirements 3.1-3.4)_
    - _Requirements: 2.3_

  - [x] 3.2 Add safe division helper
    - Create `_safe_divide(numerator, denominator, default=0.0)` static method
    - Check for zero denominator before division
    - Use small epsilon (1e-10) instead of zero to avoid division errors
    - Return default value if division would produce NaN/inf
    - _Bug_Condition: isBugCondition(input) where loss rolling mean equals zero causing rs = gain / loss crash_
    - _Expected_Behavior: Handle division by zero with epsilon or default values_
    - _Preservation: Maintain RSI calculation formula for non-zero denominators (Requirements 3.1-3.4)_
    - _Requirements: 2.1_

  - [x] 3.3 Add NaN/Inf detection helper
    - Create `_is_valid_number(value)` static method
    - Check for NaN using `pd.isna(value)`
    - Check for inf using `np.isinf(value)`
    - Return boolean indicating validity
    - _Bug_Condition: isBugCondition(input) where calculations produce NaN or inf values_
    - _Expected_Behavior: Detect invalid values and handle gracefully_
    - _Preservation: Maintain existing indicator calculations for valid results (Requirements 3.1-3.4)_
    - _Requirements: 2.2_

  - [x] 3.4 Modify RSI calculation with safe division
    - Replace direct division with `_safe_divide(gain, loss, default=100.0)`
    - When loss=0 and gain>0, set RSI=100 (maximum bullish)
    - When both gain=0 and loss=0, set RSI=50 (neutral)
    - Validate RSI is in [0, 100] range after calculation
    - _Bug_Condition: isBugCondition(input) where gain or loss rolling mean equals zero_
    - _Expected_Behavior: Handle zero division cases with appropriate RSI values_
    - _Preservation: Maintain RSI formula for normal cases (Requirements 3.1-3.4)_
    - _Requirements: 2.1, 2.2_

  - [x] 3.5 Add post-calculation validation
    - After all indicator calculations, validate each indicator value
    - Check `latest['EMA_20']`, `latest['EMA_50']`, `latest['RSI_14']` for NaN/inf
    - If any indicator is invalid, return error state with reason
    - Log validation failures with data context for debugging
    - _Bug_Condition: isBugCondition(input) where calculations produce NaN/inf that propagate_
    - _Expected_Behavior: Detect and log invalid calculation results_
    - _Preservation: Maintain existing return format and values for valid calculations (Requirements 3.1-3.4)_
    - _Requirements: 2.2, 2.5_

  - [x] 3.6 Add volume validation
    - Before volume trend calculation, check if all volumes are zero
    - If zero volume detected, skip volume scoring and log warning
    - Set volume contribution to score as 0 (neutral) instead of NaN
    - Document in reason field: "volume data unavailable"
    - _Bug_Condition: isBugCondition(input) where volume indicators calculated with zero volume_
    - _Expected_Behavior: Handle zero volume gracefully with neutral indicators_
    - _Preservation: Maintain volume trend calculation for non-zero volumes (Requirements 3.1-3.4)_
    - _Requirements: 2.4_

  - [x] 3.7 Add bounds checking for indicators
    - Before using indicators in comparisons, validate they are valid numbers
    - Clamp technical_score to [0.0, 1.0] range (already done, but add validation)
    - Add assertion that final score is valid before returning
    - _Bug_Condition: isBugCondition(input) where calculated indicators used without bounds checking_
    - _Expected_Behavior: Validate indicator values before use in logic_
    - _Preservation: Maintain existing comparison logic and thresholds (Requirements 3.1-3.4)_
    - _Requirements: 2.5_

  - [x] 3.8 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - TechnicalAgent Calculation Fixes
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - Run `test_bugfix_technical_agent.py` on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms bugs 1.1-1.5 are fixed)
    - Verify no ZeroDivisionError on zero loss
    - Verify NaN/inf values detected and handled
    - Verify all-zero data validated before calculations
    - Verify zero volume handled gracefully
    - Verify bounds checking prevents invalid logic
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.9 Verify preservation tests still pass
    - **Property 2: Preservation** - TechnicalAgent Existing Functionality
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 - do NOT write new tests
    - Run preservation tests for TechnicalAgent on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify valid price history produces same results
    - Verify TOON format unchanged
    - Verify calculation logic unchanged for valid inputs
    - Verify thresholds and score clamping unchanged
    - _Requirements: 3.1, 3.2, 3.3, 3.4_


- [x] 4. Fix RiskAgent assessment failures (Bugs 1.6-1.10)

  - [x] 4.1 Improve insufficient data error message
    - Change error message to include actual and required counts
    - Format: f"insufficient data: need at least 14 points, got {len(price_history)}"
    - Update return dict with detailed message
    - _Bug_Condition: isBugCondition(input) where price_history has fewer than 14 points AND error message is vague_
    - _Expected_Behavior: Return detailed error message specifying minimum required data points_
    - _Preservation: Maintain existing risk calculation logic for sufficient data (Requirements 3.5-3.8)_
    - _Requirements: 2.6_

  - [x] 4.2 Add extreme condition detection
    - Create `_detect_extreme_conditions(df)` static method
    - Check for volatility > 0.10 (10% daily swing) as extreme
    - Check for price gaps > 5% between consecutive closes
    - Check for volume spikes > 3x average volume
    - Return dict with flags and detected conditions
    - _Bug_Condition: isBugCondition(input) where extreme market conditions occur AND no special handling_
    - _Expected_Behavior: Detect extreme conditions and apply special risk handling_
    - _Preservation: Maintain existing risk scoring for normal conditions (Requirements 3.5-3.8)_
    - _Requirements: 2.7_

  - [x] 4.3 Add regime-specific risk thresholds
    - Create `_get_risk_thresholds(market_regime: str)` static method
    - Return different thresholds based on regime:
      - Normal: {LOW: 0.3, MEDIUM: 0.5, HIGH: 0.8}
      - Earnings: {LOW: 0.2, MEDIUM: 0.4, HIGH: 0.6} (more cautious)
      - Volatile: {LOW: 0.4, MEDIUM: 0.6, HIGH: 0.9} (expect volatility)
    - Add `market_regime: str = "normal"` parameter to analyze() method
    - _Bug_Condition: isBugCondition(input) where risk thresholds use hardcoded values without regime adjustments_
    - _Expected_Behavior: Use regime-specific thresholds for risk level assignment_
    - _Preservation: Maintain baseline thresholds (0.3, 0.5, 0.8) for normal regime (Requirements 3.5-3.8)_
    - _Requirements: 2.8_

  - [x] 4.4 Add gap risk analysis
    - Calculate overnight gaps: `df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)`
    - Compute max gap in recent history (last 14 days)
    - If max gap > 3%, add 0.2 to risk_score
    - Document gap risk in reasons list
    - _Bug_Condition: isBugCondition(input) where risk calculation does not consider gap risk_
    - _Expected_Behavior: Incorporate gap risk analysis in risk score calculation_
    - _Preservation: Maintain existing RSI and volatility calculations (Requirements 3.5-3.8)_
    - _Requirements: 2.9_

  - [x] 4.5 Add logging for NaN detection
    - Import logging module at top of file
    - When NaN detected in RSI or volatility, log before returning
    - Log format: f"Risk calculation produced NaN: RSI={rsi}, Vol={vol}, data_points={len(df)}"
    - Include sample of recent close prices in log for debugging
    - Keep existing early return behavior but add logging
    - _Bug_Condition: isBugCondition(input) where RSI/volatility produce NaN AND no logging occurs_
    - _Expected_Behavior: Log NaN detection with context before returning error state_
    - _Preservation: Maintain existing early return behavior for NaN cases (Requirements 3.5-3.8)_
    - _Requirements: 2.10_

  - [x] 4.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - RiskAgent Assessment Improvements
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - Run `test_bugfix_risk_agent.py` on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms bugs 1.6-1.10 are fixed)
    - Verify detailed error messages for insufficient data
    - Verify extreme condition detection and handling
    - Verify regime-specific thresholds applied
    - Verify gap risk incorporated in risk score
    - Verify NaN detection logged with context
    - _Requirements: 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 4.7 Verify preservation tests still pass
    - **Property 2: Preservation** - RiskAgent Existing Functionality
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 - do NOT write new tests
    - Run preservation tests for RiskAgent on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify valid risk calculations produce same results
    - Verify TOON format unchanged
    - Verify RSI_14 and volatility calculations unchanged
    - Verify baseline thresholds used for normal regime
    - _Requirements: 3.5, 3.6, 3.7, 3.8_


- [x] 5. Fix FusionAgent parsing and validation issues (Bugs 1.11-1.15)

  - [x] 5.1 Add logging to parse errors
    - Import logging module at top of file
    - Wrap float conversions in try-except with logging
    - Log format: f"Failed to parse {field_name}: {value} - {error}"
    - Apply to tech_score, event_score, risk_score, event_confidence parsing
    - Log the problematic value and field name for debugging
    - _Bug_Condition: isBugCondition(input) where TOON parsing raises ValueError AND no logging occurs_
    - _Expected_Behavior: Log parsing errors with problematic value before defaulting_
    - _Preservation: Maintain existing parsing logic and default values (Requirements 3.9-3.13)_
    - _Requirements: 2.11_

  - [x] 5.2 Add weight validation and normalization
    - Create `_validate_and_normalize_weights(weights: Dict[str, float])` static method
    - Calculate total weight: `total = sum(weights.values())`
    - Check if total is within tolerance: `abs(total - 1.0) < 0.01`
    - If outside tolerance, normalize: `{k: v/total for k, v in weights.items()}`
    - Log warning if normalization was required
    - Return normalized weights
    - _Bug_Condition: isBugCondition(input) where confidence adjustments applied AND weights not validated_
    - _Expected_Behavior: Validate weights sum to 1.0 and normalize if needed_
    - _Preservation: Maintain existing weight calculation logic (Requirements 3.9-3.13)_
    - _Requirements: 2.12_

  - [x] 5.3 Document context weight redistribution
    - Add inline comment explaining redistribution logic
    - Comment: "Context agent not yet implemented in MVP, redistribute its weight to technical"
    - Comment: "This maintains total weight sum while giving technical agent more influence"
    - Validate weights after redistribution using helper method
    - _Bug_Condition: isBugCondition(input) where context weight redistributed without documentation_
    - _Expected_Behavior: Document redistribution logic and validate total weight_
    - _Preservation: Maintain existing redistribution behavior (Requirements 3.9-3.13)_
    - _Requirements: 2.13_

  - [x] 5.4 Add comprehensive TOON field validation
    - Create `_validate_toon_data(data: Dict, required_fields: List[str], source: str)` static method
    - Check that all required fields are present
    - Check that numeric fields can be parsed as floats
    - Log warnings for missing or malformed fields with source context
    - Return validated data dict with defaults for missing fields
    - _Bug_Condition: isBugCondition(input) where TOON fields missing or malformed AND no validation_
    - _Expected_Behavior: Validate all expected fields and log warnings for issues_
    - _Preservation: Maintain existing field parsing and default values (Requirements 3.9-3.13)_
    - _Requirements: 2.14_

  - [x] 5.5 Add final signal bounds checking
    - After calculating final_signal, validate it's in valid range
    - Add clamping: `final_signal = max(-1.0, min(1.0, final_signal))`
    - Log warning if clamping was required with original value
    - Ensures signal is always in [-1, 1] range before decision logic
    - _Bug_Condition: isBugCondition(input) where final_signal not bounds checked before use_
    - _Expected_Behavior: Clamp final_signal to [-1, 1] range before decision logic_
    - _Preservation: Maintain existing signal calculation and decision thresholds (Requirements 3.9-3.13)_
    - _Requirements: 2.15_

  - [x] 5.6 Apply weight validation after confidence adjustment
    - After applying confidence-aware weighting to event signal
    - Call `_validate_and_normalize_weights(weights)` to ensure sum is correct
    - Use normalized weights for signal calculation
    - _Bug_Condition: isBugCondition(input) where confidence adjustment causes weight sum != 1.0_
    - _Expected_Behavior: Normalize weights after confidence adjustment_
    - _Preservation: Maintain existing confidence adjustment logic (Requirements 3.9-3.13)_
    - _Requirements: 2.12_

  - [x] 5.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - FusionAgent Parsing and Validation Fixes
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - Run `test_bugfix_fusion_agent.py` on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms bugs 1.11-1.15 are fixed)
    - Verify parse errors logged with context
    - Verify weights validated and normalized
    - Verify context redistribution documented
    - Verify TOON field validation comprehensive
    - Verify final_signal clamped to valid range
    - _Requirements: 2.11, 2.12, 2.13, 2.14, 2.15_

  - [x] 5.8 Verify preservation tests still pass
    - **Property 2: Preservation** - FusionAgent Existing Functionality
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 - do NOT write new tests
    - Run preservation tests for FusionAgent on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify valid synthesis produces same results
    - Verify regime weights unchanged
    - Verify CRITICAL risk veto still enforced
    - Verify decision thresholds (±0.4) unchanged
    - Verify position sizing (MAX_ALLOCATION=0.10) unchanged
    - _Requirements: 3.9, 3.10, 3.11, 3.12, 3.13_


- [x] 6. Fix TradeAgent execution risks (Bugs 1.16-1.20)

  - [x] 6.1 Add position limit enforcement
    - Add `max_total_exposure: float = 0.50` parameter to __init__ (default 50% of equity)
    - Create `_calculate_total_exposure()` method to sum position_size of all open trades
    - In execute_trade(), check total exposure before opening new trade
    - If `current_exposure + new_position_size > max_total_exposure`, reject trade
    - Return None and log rejection reason
    - _Bug_Condition: isBugCondition(input) where multiple trades opened without position limit check_
    - _Expected_Behavior: Enforce maximum position limits across all open trades_
    - _Preservation: Maintain existing trade execution logic within limits (Requirements 3.14-3.18)_
    - _Requirements: 2.16_

  - [x] 6.2 Add capital availability check
    - Add `account_balance: float` parameter to __init__ (required for capital checks)
    - Create `_check_capital_available(position_size: float, price: float)` method
    - Calculate required capital: `required = position_size * account_balance * price`
    - Check if required capital is available (considering existing open trades)
    - Return boolean and reason string
    - _Bug_Condition: isBugCondition(input) where new trades opened without capital check_
    - _Expected_Behavior: Check capital availability before execution_
    - _Preservation: Maintain existing trade execution for sufficient capital (Requirements 3.14-3.18)_
    - _Requirements: 2.17_

  - [x] 6.3 Add market hours and gap risk handling
    - Create `_adjust_stops_for_overnight(action: str, fill_price: float, is_overnight: bool)` method
    - If is_overnight=True, widen stops by 50% to account for gap risk
    - For BUY: `sl = fill_price * 0.97` (3% instead of 2%)
    - For SELL: `sl = fill_price * 1.03` (3% instead of 2%)
    - Add `is_overnight: bool = False` parameter to execute_trade()
    - _Bug_Condition: isBugCondition(input) where stop loss calculated without market hours consideration_
    - _Expected_Behavior: Account for market hours and apply wider stops for overnight positions_
    - _Preservation: Maintain 2% stop loss for intraday trades (Requirements 3.14-3.18)_
    - _Requirements: 2.18_

  - [x] 6.4 Add partial fill handling
    - Add `actual_fill_size: float` parameter to Trade model (defaults to position_size)
    - In execute_trade(), simulate partial fills randomly (10% chance of 50-100% fill)
    - Update trade.actual_fill_size with filled amount
    - Log partial fills with warning level
    - Update position tracking to use actual_fill_size instead of position_size
    - _Bug_Condition: isBugCondition(input) where orders submitted without partial fill handling_
    - _Expected_Behavior: Handle partial fills and update position size accordingly_
    - _Preservation: Maintain existing trade execution for full fills (Requirements 3.14-3.18)_
    - _Requirements: 2.19_

  - [x] 6.5 Add position size validation
    - Create `_validate_position_size(position_size: float)` method
    - Check that position_size > 0 for actual trades
    - Check that position_size <= max_allocation (0.10)
    - Check that position_size is not NaN or inf
    - Return validation result and error message
    - Call before executing trade, reject if invalid
    - _Bug_Condition: isBugCondition(input) where position_size not validated before use_
    - _Expected_Behavior: Validate position size is within acceptable bounds_
    - _Preservation: Maintain existing position sizing logic for valid sizes (Requirements 3.14-3.18)_
    - _Requirements: 2.20_

  - [x] 6.6 Add order rejection handling
    - Add `rejection_rate: float = 0.05` parameter to __init__ (5% of orders rejected)
    - In execute_trade(), simulate random rejections
    - If rejected, log warning and return None
    - Include rejection reason in log
    - _Bug_Condition: isBugCondition(input) where orders submitted without rejection handling_
    - _Expected_Behavior: Handle order rejections gracefully with logging_
    - _Preservation: Maintain existing trade execution for accepted orders (Requirements 3.14-3.18)_
    - _Requirements: 2.19_

  - [x] 6.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - TradeAgent Execution Safeguards
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - Run `test_bugfix_trade_agent.py` on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms bugs 1.16-1.20 are fixed)
    - Verify position limits enforced across all trades
    - Verify capital availability checked before execution
    - Verify market hours considered for stop loss
    - Verify partial fills handled correctly
    - Verify position size validated before use
    - _Requirements: 2.16, 2.17, 2.18, 2.19, 2.20_

  - [x] 6.8 Verify preservation tests still pass
    - **Property 2: Preservation** - TradeAgent Existing Functionality
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 - do NOT write new tests
    - Run preservation tests for TradeAgent on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify valid trade execution produces same results
    - Verify slippage calculation unchanged
    - Verify commission application unchanged
    - Verify 2% stop loss and 4% target unchanged for normal trades
    - Verify trade monitoring logic unchanged
    - _Requirements: 3.14, 3.15, 3.16, 3.17, 3.18_


- [x] 7. Fix LearningAgent database issues (Bugs 1.21-1.25)

  - [x] 7.1 Add SQLite detection and pgvector compatibility check
    - In __init__, detect if db_url contains "sqlite"
    - Set `self.supports_pgvector = False` for SQLite
    - Log warning: "SQLite detected: pgvector operations disabled, using fallback storage"
    - In evaluate_and_store(), skip vector similarity search if not supports_pgvector
    - Store embeddings as JSON text field instead of Vector type for SQLite
    - _Bug_Condition: isBugCondition(input) where SQLite used AND pgvector operations attempted_
    - _Expected_Behavior: Detect SQLite and disable pgvector operations with warnings_
    - _Preservation: Maintain existing PostgreSQL pgvector functionality (Requirements 3.19-3.22)_
    - _Requirements: 2.21_

  - [x] 7.2 Add connection pooling
    - Import `pool` from sqlalchemy
    - Modify engine creation to use connection pooling:
      - poolclass=pool.QueuePool
      - pool_size=5
      - max_overflow=10
      - pool_pre_ping=True (verify connections before use)
    - Add pool_pre_ping to detect stale connections
    - _Bug_Condition: isBugCondition(input) where database operations performed without connection pooling_
    - _Expected_Behavior: Implement connection pooling for better reliability_
    - _Preservation: Maintain existing database operation behavior (Requirements 3.19-3.22)_
    - _Requirements: 2.22_

  - [x] 7.3 Add retry logic with exponential backoff
    - Create `_retry_db_operation(operation: Callable, max_retries: int = 3)` method
    - Implement exponential backoff: 1s, 2s, 4s delays
    - Catch SQLAlchemy connection errors and retry
    - Log each retry attempt with context
    - Raise exception after max retries exhausted
    - _Bug_Condition: isBugCondition(input) where database operations fail without retry logic_
    - _Expected_Behavior: Retry transient failures with exponential backoff_
    - _Preservation: Maintain existing database operation behavior for successful connections (Requirements 3.19-3.22)_
    - _Requirements: 2.22_

  - [x] 7.4 Make embedding dimension configurable
    - Add `embedding_dim: int` parameter to __init__
    - Default to `int(os.getenv("EMBEDDING_DIMENSION", "1536"))`
    - Store as instance variable: `self.embedding_dim = embedding_dim`
    - Document that table schema must match configured dimension
    - Note: Full dynamic schema requires table recreation, document limitation
    - _Bug_Condition: isBugCondition(input) where embedding dimension hardcoded to 1536_
    - _Expected_Behavior: Make embedding dimension configurable via environment variable_
    - _Preservation: Maintain default 1536 dimension for existing deployments (Requirements 3.19-3.22)_
    - _Requirements: 2.23_

  - [x] 7.5 Add automatic cleanup mechanism
    - Create `cleanup_old_records(retention_days: int = 90)` method
    - Delete SentimentValidation records older than retention_days
    - Use SQL: `DELETE FROM sentiment_validations WHERE timestamp < NOW() - INTERVAL '{retention_days} days'`
    - Log number of records deleted
    - Add environment variable: `VALIDATION_RETENTION_DAYS` (default 90)
    - Call automatically in __init__ or provide as maintenance method
    - _Bug_Condition: isBugCondition(input) where validation records accumulate without cleanup_
    - _Expected_Behavior: Implement automatic cleanup of old validation records_
    - _Preservation: Maintain existing record storage behavior (Requirements 3.19-3.22)_
    - _Requirements: 2.24_

  - [x] 7.6 Add graceful degradation for database failures
    - Wrap all database operations in try-except blocks
    - In evaluate_and_store(), if database fails, log error but don't crash
    - Return success=False indicator instead of raising exception
    - In get_dynamic_weights_for_regime(), if database fails, return static fallback weights
    - In track_sentiment_accuracy(), if database fails, log error and return error dict
    - Add `self.degraded_mode = False` flag to track if database is unavailable
    - _Bug_Condition: isBugCondition(input) where database connection failures cause agent crashes_
    - _Expected_Behavior: Implement graceful degradation with error handling_
    - _Preservation: Maintain existing behavior for successful database operations (Requirements 3.19-3.22)_
    - _Requirements: 2.25_

  - [x] 7.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - LearningAgent Database Improvements
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - Run `test_bugfix_learning_agent.py` on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms bugs 1.21-1.25 are fixed)
    - Verify SQLite detection and pgvector fallback
    - Verify connection pooling implemented
    - Verify retry logic with exponential backoff
    - Verify embedding dimension configurable
    - Verify automatic cleanup mechanism
    - Verify graceful degradation on database failures
    - _Requirements: 2.21, 2.22, 2.23, 2.24, 2.25_

  - [x] 7.8 Verify preservation tests still pass
    - **Property 2: Preservation** - LearningAgent Existing Functionality
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 - do NOT write new tests
    - Run preservation tests for LearningAgent on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify valid pattern storage produces same results
    - Verify TradePattern and SentimentValidation schemas unchanged
    - Verify dynamic weights calculation unchanged
    - Verify sentiment accuracy metrics unchanged
    - _Requirements: 3.19, 3.20, 3.21, 3.22_


- [x] 8. Fix Graph orchestration failures (Bugs 1.26-1.30)

  - [x] 8.1 Add timeout handling for agent operations
    - Import `signal` and `TimeoutError` modules (or use asyncio.wait_for for async)
    - Create `_run_with_timeout(func: Callable, timeout_seconds: int)` helper
    - Use cross-platform timeout mechanism (threading.Timer or asyncio)
    - Wrap each agent node function with timeout decorator
    - Default timeouts: technical=30s, event=60s, risk=30s, context=30s, fusion=10s
    - If timeout occurs, log error and return error state
    - _Bug_Condition: isBugCondition(input) where agent operations take too long without timeout_
    - _Expected_Behavior: Implement timeout handling with configurable timeout values_
    - _Preservation: Maintain existing workflow structure and agent execution (Requirements 3.23-3.27)_
    - _Requirements: 2.26_

  - [x] 8.2 Add circuit breaker pattern
    - Create `CircuitBreaker` class to track agent failures
    - States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
    - Track consecutive failures per agent type
    - After 3 consecutive failures, open circuit (stop calling agent)
    - After 60 seconds in OPEN state, transition to HALF_OPEN (try once)
    - If HALF_OPEN call succeeds, close circuit; if fails, reopen
    - Store circuit breakers in global dict: `agent_circuit_breakers = {}`
    - _Bug_Condition: isBugCondition(input) where agents repeatedly fail without circuit breaker_
    - _Expected_Behavior: Implement circuit breaker to stop retries after N failures_
    - _Preservation: Maintain existing agent execution for successful operations (Requirements 3.23-3.27)_
    - _Requirements: 2.27_

  - [x] 8.3 Add state validation between nodes
    - Create `_validate_state(state: TradingState, required_fields: List[str])` helper
    - Before each node, validate required fields are present
    - Check field types match expected types (List[PriceData], Dict, etc.)
    - If validation fails, log error and return error state
    - Add validation at key transition points:
      - Before technical/event/risk: validate price_history and news_list
      - Before fusion: validate technical_data, event_data, risk_data
      - Before trade: validate decision_data
    - _Bug_Condition: isBugCondition(input) where state flows between nodes without validation_
    - _Expected_Behavior: Validate state structure and required fields between transitions_
    - _Preservation: Maintain existing state structure and field names (Requirements 3.23-3.27)_
    - _Requirements: 2.28_

  - [x] 8.4 Add rollback mechanism
    - Create `_checkpoint_state(state: TradingState)` to save state snapshots
    - Store last known good state in global variable or state field
    - If node fails, restore from checkpoint
    - Add `last_checkpoint` field to TradingState
    - In each node, checkpoint state before processing
    - On exception, restore from checkpoint and mark node as failed
    - _Bug_Condition: isBugCondition(input) where node fails mid-execution without rollback_
    - _Expected_Behavior: Implement rollback mechanism to restore previous state_
    - _Preservation: Maintain existing state flow for successful operations (Requirements 3.23-3.27)_
    - _Requirements: 2.29_

  - [x] 8.5 Add comprehensive state transition logging
    - Import logging module and configure logger
    - At start of each node function, log entry with timestamp and state summary
    - Log key state values: symbol, regime, data counts, scores
    - At end of each node function, log exit with results
    - Log format: `[SYMBOL] NODE_NAME: entry/exit - key_values`
    - Example: `[AAPL] technical: entry - price_points=50, regime=normal`
    - Example: `[AAPL] technical: exit - score=0.65, trend=bullish`
    - Add exception logging with full traceback for debugging
    - _Bug_Condition: isBugCondition(input) where state transitions occur without logging_
    - _Expected_Behavior: Log all transitions with timestamps and key state values_
    - _Preservation: Maintain existing workflow execution (Requirements 3.23-3.27)_
    - _Requirements: 2.30_

  - [x] 8.6 Wrap all node functions with error handling
    - Create `@safe_node` decorator that wraps node functions
    - Catches all exceptions, logs them, and returns error state
    - Prevents single node failure from crashing entire workflow
    - Error state includes error message and failed node name
    - Allows workflow to continue or gracefully terminate
    - _Bug_Condition: isBugCondition(input) where node failures crash entire workflow_
    - _Expected_Behavior: Wrap nodes with error handling to prevent cascading failures_
    - _Preservation: Maintain existing node execution for successful operations (Requirements 3.23-3.27)_
    - _Requirements: 2.26, 2.27, 2.28, 2.29, 2.30_

  - [x] 8.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Graph Orchestration Resilience
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - Run `test_bugfix_graph_orchestration.py` on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms bugs 1.26-1.30 are fixed)
    - Verify timeout handling prevents indefinite hangs
    - Verify circuit breaker stops repeated failures
    - Verify state validation catches invalid transitions
    - Verify rollback mechanism restores state on failures
    - Verify state transitions logged for debugging
    - _Requirements: 2.26, 2.27, 2.28, 2.29, 2.30_

  - [x] 8.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Graph Orchestration Existing Functionality
    - **IMPORTANT**: Re-run the SAME preservation tests from task 2 - do NOT write new tests
    - Run preservation tests for Graph orchestration on FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify valid workflow produces same results
    - Verify workflow structure unchanged (START → fetch_data → agents → fusion → trade → END)
    - Verify parallel execution of agents unchanged
    - Verify state flow and field names unchanged
    - Verify TradingState structure unchanged
    - _Requirements: 3.23, 3.24, 3.25, 3.26, 3.27_

## Phase 4: Final Validation

- [x] 9. Checkpoint - Ensure all tests pass
  - Run all bug condition exploration tests (tasks 1, 3.8, 4.6, 5.7, 6.7, 7.7, 8.7)
  - Verify all 30 bugs are fixed (all exploration tests pass)
  - Run all preservation tests (tasks 2, 3.9, 4.7, 5.8, 6.8, 7.8, 8.8)
  - Verify no regressions (all preservation tests pass)
  - Run existing test suite (test_technical.py, test_risk.py, etc.)
  - Verify backward compatibility maintained
  - Run full workflow integration test with valid inputs
  - Verify end-to-end functionality unchanged
  - Document any issues or questions for user review
  - Ask the user if questions arise
