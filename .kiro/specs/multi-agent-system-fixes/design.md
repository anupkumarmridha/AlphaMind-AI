# Multi-Agent System Fixes Bugfix Design

## Overview

The AlphaMind AI multi-agent trading system contains 30 critical bugs across all 6 agents and the graph orchestration layer. These bugs cause system crashes (division by zero, NaN propagation), silent failures (missing validation, parsing errors), incorrect calculations (unbounded values, missing edge cases), and operational instability (database growth, no error recovery). This design outlines a comprehensive fix strategy that adds robust error handling, validation, retry logic, and resilience mechanisms while maintaining backward compatibility with all existing TOON formats and agent interfaces.

The fix approach follows defensive programming principles: validate all inputs, handle all edge cases, log all errors, and fail gracefully. Each agent will gain input validation, calculation safeguards, and error recovery. The graph orchestration will add timeout handling, circuit breakers, and state validation. The LearningAgent will implement connection pooling, cleanup mechanisms, and graceful degradation.

## Glossary

- **Bug_Condition (C)**: The condition that triggers each of the 30 bugs - invalid inputs, edge cases, missing validation, or lack of error handling
- **Property (P)**: The desired behavior when bugs are fixed - proper validation, error handling, logging, and graceful degradation
- **Preservation**: All existing TOON formats, agent interfaces, calculation logic, and decision thresholds must remain unchanged
- **TechnicalAgent**: Agent in `agents/technical_agent.py` that calculates EMA, RSI, and volume indicators from price history
- **RiskAgent**: Agent in `agents/risk_agent.py` that assesses risk using RSI and volatility calculations
- **FusionAgent**: Agent in `agents/fusion_agent.py` that synthesizes signals from all agents using regime-dependent weights
- **TradeAgent**: Agent in `agents/trade_agent.py` that executes paper trades with slippage and commission simulation
- **LearningAgent**: Agent in `agents/learning_agent.py` that stores trade patterns and sentiment validations in PostgreSQL/SQLite
- **EventAgent**: Agent in `agents/event_agent.py` that analyzes news using LLM triage and extraction (already has retry logic)
- **Graph Orchestration**: LangGraph workflow in `agents/graph.py` that orchestrates the multi-agent pipeline
- **TOON Format**: Token-Optimized Object Notation - compact key:value format for inter-agent communication
- **NaN/inf**: Not-a-Number and infinity values from invalid mathematical operations (division by zero, log of negative)
- **Circuit Breaker**: Pattern that stops retries after N consecutive failures to prevent cascading failures
- **Graceful Degradation**: System continues operating with reduced functionality when components fail


## Bug Details

### Bug Condition

The bugs manifest across six categories: calculation errors, validation failures, parsing issues, execution risks, database problems, and orchestration failures. Each category contains multiple specific bug conditions that can cause system crashes, incorrect results, or operational instability.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentInput (price_history, news_list, TOON strings, trade data, or state)
  OUTPUT: boolean
  
  RETURN (
    // TechnicalAgent calculation errors
    (input.type == "price_history" AND hasZeroDivisionRisk(input)) OR
    (input.type == "price_history" AND producesNaNOrInf(input)) OR
    (input.type == "price_history" AND hasInvalidData(input)) OR
    (input.type == "price_history" AND hasZeroVolume(input)) OR
    (input.type == "indicator_value" AND notBoundsChecked(input)) OR
    
    // RiskAgent assessment failures
    (input.type == "price_history" AND length(input) < 14 AND errorMessageVague(input)) OR
    (input.type == "price_history" AND hasExtremeConditions(input) AND noSpecialHandling(input)) OR
    (input.type == "risk_threshold" AND usesHardcodedValues(input)) OR
    (input.type == "risk_calculation" AND noGapRiskAnalysis(input)) OR
    (input.type == "risk_calculation" AND producesNaN(input) AND noLogging(input)) OR
    
    // FusionAgent parsing and validation issues
    (input.type == "toon_string" AND parseError(input) AND noLogging(input)) OR
    (input.type == "weights" AND confidenceAdjusted(input) AND notValidated(input)) OR
    (input.type == "weights" AND contextRedistributed(input) AND notDocumented(input)) OR
    (input.type == "toon_field" AND (missing(input) OR malformed(input)) AND noValidation(input)) OR
    (input.type == "final_signal" AND notBoundsChecked(input)) OR
    
    // TradeAgent execution risks
    (input.type == "new_trade" AND noPositionLimitCheck(input)) OR
    (input.type == "new_trade" AND noCapitalCheck(input)) OR
    (input.type == "stop_loss_target" AND noMarketHoursCheck(input)) OR
    (input.type == "order" AND noPartialFillHandling(input)) OR
    (input.type == "position_size" AND notValidated(input)) OR
    
    // LearningAgent database issues
    (input.type == "database" AND isSQLite(input) AND usesPgVector(input)) OR
    (input.type == "database_operation" AND noConnectionPooling(input)) OR
    (input.type == "embedding" AND dimensionHardcoded(input)) OR
    (input.type == "validation_records" AND noCleanupMechanism(input)) OR
    (input.type == "database_connection" AND failsWithoutHandling(input)) OR
    
    // Graph orchestration failures
    (input.type == "agent_operation" AND noTimeoutHandling(input)) OR
    (input.type == "agent_failure" AND noCircuitBreaker(input)) OR
    (input.type == "state_transition" AND noValidation(input)) OR
    (input.type == "node_failure" AND noRollback(input)) OR
    (input.type == "state_transition" AND noLogging(input))
  )
END FUNCTION
```

### Examples

**TechnicalAgent Calculation Errors:**
- Bug 1.1: `price_history = [PriceData(close=100, volume=0), ...]` with all gains=0 and losses=0 → `rs = 0/0` → ZeroDivisionError crash
- Bug 1.2: `price_history` with no price variation → RSI calculation produces NaN → propagates to FusionAgent causing invalid comparisons
- Bug 1.3: `price_history = [PriceData(close=0, volume=0), ...]` → EMA calculations produce 0 or NaN → incorrect technical_score
- Bug 1.4: `price_history` with all volume=0 → `Vol_5/Vol_20 = 0/0` → NaN in volume trend → not caught before use
- Bug 1.5: `latest['RSI_14'] = NaN` → comparison `if latest['RSI_14'] > 60` evaluates incorrectly → wrong momentum classification

**RiskAgent Assessment Failures:**
- Bug 1.6: `len(price_history) = 10` → returns "insufficient data" without specifying need for 14+ points → debugging difficult
- Bug 1.7: Flash crash with `volatility = 0.15` (15% daily swing) → no special handling → risk_level may be underestimated
- Bug 1.8: Earnings announcement with `market_regime="earnings"` → uses same thresholds as normal → inappropriate risk assessment
- Bug 1.9: Overnight gap from $100 to $95 → risk calculation only considers intraday volatility → gap risk not captured
- Bug 1.10: `RSI = NaN` → early return with "not enough data" → no log entry for debugging → root cause unknown


**FusionAgent Parsing and Validation Issues:**
- Bug 1.11: `tech_data.get('technical_score', 0)` returns "N/A" → `float("N/A")` raises ValueError → silently defaults to 0 → no log entry
- Bug 1.12: `effective_event_weight = 0.2 * 0.3 = 0.06` → total weights no longer sum to 1.0 → signal calculation skewed
- Bug 1.13: `weights["technical"] += weights.get("context", 0)` → context weight redistributed → no documentation of why or validation
- Bug 1.14: `risk_data.get('risk_level')` returns None → defaults to 'LOW' → no warning logged → silent failure
- Bug 1.15: `final_signal = 1.5` (out of bounds) → used in decision logic without clamping → incorrect decision thresholds

**TradeAgent Execution Risks:**
- Bug 1.16: 5 open trades each with 10% position → total exposure = 50% → no check → over-exposure risk
- Bug 1.17: Account balance = $10,000, new trade requires $15,000 → no capital check → negative balance
- Bug 1.18: Stop loss set at $98 during market hours → overnight gap to $95 → stop not triggered at intended price
- Bug 1.19: Order for 100 shares → only 50 filled → position_size not updated → incorrect exposure tracking
- Bug 1.20: `position_size = -0.05` (negative) → not validated → trade executed with invalid size

**LearningAgent Database Issues:**
- Bug 1.21: `db_url = "sqlite:///:memory:"` → `CREATE EXTENSION IF NOT EXISTS vector` fails → pgvector operations fail silently
- Bug 1.22: Database connection timeout → no retry logic → agent fails → entire workflow stops
- Bug 1.23: Switching from OpenAI (1536 dims) to custom model (768 dims) → hardcoded dimension → insertion fails
- Bug 1.24: 1 million validation records accumulated over 2 years → database size = 10GB → no cleanup → performance degradation
- Bug 1.25: PostgreSQL connection fails → no error handling → LearningAgent crashes → workflow stops

**Graph Orchestration Failures:**
- Bug 1.26: EventAgent LLM call hangs for 5 minutes → no timeout → entire workflow blocked
- Bug 1.27: TechnicalAgent fails 10 times in a row → continues retrying → cascading failures → system unstable
- Bug 1.28: `state["price_history"] = None` → passed to TechnicalAgent → crashes without validation
- Bug 1.29: FusionAgent fails mid-execution → state partially updated → no rollback → inconsistent state
- Bug 1.30: State transitions from fetch_data → technical → fusion → trade → no logs → debugging workflow issues impossible


## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All TOON format outputs must remain exactly the same (field names, value ranges, format structure)
- All agent interfaces must remain unchanged (function signatures, parameter types, return types)
- All calculation logic must remain the same (EMA/RSI formulas, risk thresholds, fusion weights, position sizing)
- All decision thresholds must remain unchanged (±0.4 for BUY/SELL, 0.8 for CRITICAL risk, 10% MAX_ALLOCATION)
- All existing test files must continue to pass without modification
- Graph workflow structure must remain the same (START → fetch_data → [technical, event, risk, context] → fusion → trade → END)
- Database schema must remain unchanged (TradePattern and SentimentValidation tables)
- Frontend API responses must remain unchanged (JSON format, field names)

**Scope:**
All inputs that do NOT trigger the 30 bug conditions should be completely unaffected by this fix. This includes:
- Valid price history with sufficient data points and no edge cases
- Valid TOON strings with all required fields properly formatted
- Valid trade executions within capital and position limits
- Valid database connections with proper configuration
- Valid state transitions with all required fields present

The fixes add defensive layers (validation, error handling, logging) without changing core business logic or output formats.


## Hypothesized Root Cause

Based on the bug analysis across all 30 defects, the root causes fall into six categories:

### 1. **Missing Input Validation and Edge Case Handling**
The agents were designed for the "happy path" without defensive programming. Price history validation assumes clean data, but real market data can have zeros, gaps, or insufficient points. The system lacks pre-calculation validation to catch edge cases before they cause crashes.

**Specific Issues:**
- No validation that price_history has minimum required length before calculations
- No checks for all-zero sequences, missing values, or invalid numeric data
- No validation of TOON field presence or format before parsing
- No bounds checking on calculated values before use in logic

### 2. **Inadequate Mathematical Safeguards**
Pandas calculations can produce NaN or inf values from division by zero, log of negative numbers, or operations on invalid data. The system performs calculations without checking for these invalid results, allowing them to propagate through the pipeline.

**Specific Issues:**
- RSI calculation: `rs = gain / loss` when loss=0 causes ZeroDivisionError
- Volume ratios: `Vol_5 / Vol_20` when Vol_20=0 produces inf
- No post-calculation validation to detect NaN/inf before returning results
- No epsilon values or fallback logic for edge cases

### 3. **Silent Failures and Missing Logging**
When errors occur (parsing failures, NaN values, missing fields), the system defaults to safe values (0, neutral, LOW) without logging the issue. This makes debugging impossible and hides systemic problems.

**Specific Issues:**
- FusionAgent ValueError exceptions caught but not logged
- RiskAgent returns early on NaN without logging the data that caused it
- TradeAgent has no validation logging for position size or capital checks
- Graph orchestration has no transition logging for debugging workflow issues

### 4. **Lack of Resilience Mechanisms**
The system has no retry logic (except EventAgent), circuit breakers, or graceful degradation. A single component failure stops the entire workflow. Database connection issues crash the LearningAgent instead of degrading gracefully.

**Specific Issues:**
- No timeout handling for long-running agent operations
- No circuit breaker to stop repeated failures
- No connection pooling or retry logic for database operations
- No rollback mechanism when nodes fail mid-execution

### 5. **Hardcoded Values and Inflexibility**
Risk thresholds, embedding dimensions, and weight allocations are hardcoded without regime-specific adjustments or configuration options. This reduces adaptability and makes the system brittle to changes.

**Specific Issues:**
- Risk thresholds (0.3, 0.5, 0.8) are static regardless of market regime
- Embedding dimension hardcoded to 1536 (OpenAI-specific)
- No gap risk or overnight risk analysis in risk calculations
- Context weight redistribution logic not documented or validated

### 6. **Database and Resource Management Issues**
The LearningAgent lacks connection pooling, cleanup mechanisms, and SQLite compatibility checks. Validation records accumulate indefinitely, and pgvector operations fail silently on SQLite.

**Specific Issues:**
- No connection pooling causes connection exhaustion under load
- No cleanup mechanism for old validation records (unbounded growth)
- SQLite fallback attempts pgvector operations that fail silently
- No graceful degradation when database is unavailable


## Correctness Properties

Property 1: Bug Condition - Input Validation and Edge Case Handling

_For any_ input where the bug condition holds (invalid data, edge cases, missing validation), the fixed agents SHALL validate inputs before processing, detect edge cases, handle them gracefully with appropriate fallback values, and log all validation failures with context for debugging.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18, 2.19, 2.20, 2.21, 2.22, 2.23, 2.24, 2.25, 2.26, 2.27, 2.28, 2.29, 2.30**

Property 2: Preservation - Existing Functionality and Output Formats

_For any_ input where the bug condition does NOT hold (valid data, proper formatting, sufficient resources), the fixed system SHALL produce exactly the same results as the original system, preserving all TOON formats, agent interfaces, calculation logic, decision thresholds, and workflow structure.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 3.16, 3.17, 3.18, 3.19, 3.20, 3.21, 3.22, 3.23, 3.24, 3.25, 3.26, 3.27**


## Fix Implementation

### Changes Required

The fixes are organized by component, with each agent receiving targeted improvements while maintaining backward compatibility.

#### Component 1: TechnicalAgent (agents/technical_agent.py)

**Bugs Fixed:** 1.1, 1.2, 1.3, 1.4, 1.5

**Specific Changes:**

1. **Add Input Validation Helper**:
   - Create `_validate_price_history()` static method
   - Check minimum length (50 points required)
   - Validate no all-zero sequences in close prices
   - Validate no NaN or inf values in input data
   - Return validation result with detailed error message

2. **Add Safe Division Helper**:
   - Create `_safe_divide(numerator, denominator, default=0.0)` static method
   - Check for zero denominator before division
   - Use small epsilon (1e-10) instead of zero to avoid division errors
   - Return default value if division would produce NaN/inf

3. **Add NaN/Inf Detection Helper**:
   - Create `_is_valid_number(value)` static method
   - Check for NaN using `pd.isna(value)`
   - Check for inf using `np.isinf(value)`
   - Return boolean indicating validity

4. **Modify RSI Calculation**:
   - After calculating `rs = gain / loss`, check for division by zero
   - Use `_safe_divide(gain, loss, default=100.0)` instead of direct division
   - When loss=0 and gain>0, set RSI=100 (maximum bullish)
   - When both gain=0 and loss=0, set RSI=50 (neutral)
   - Validate RSI is in [0, 100] range after calculation

5. **Add Post-Calculation Validation**:
   - After all indicator calculations, validate each indicator value
   - Check `latest['EMA_20']`, `latest['EMA_50']`, `latest['RSI_14']` for NaN/inf
   - If any indicator is invalid, return error state with reason
   - Log validation failures with data context for debugging


6. **Add Volume Validation**:
   - Before volume trend calculation, check if all volumes are zero
   - If zero volume detected, skip volume scoring and log warning
   - Set volume contribution to score as 0 (neutral) instead of NaN
   - Document in reason field: "volume data unavailable"

7. **Add Bounds Checking**:
   - Before using indicators in comparisons, validate they are valid numbers
   - Clamp technical_score to [0.0, 1.0] range (already done, but add validation)
   - Add assertion that final score is valid before returning

**Implementation Pattern:**
```python
@staticmethod
def _validate_price_history(price_history: List[PriceData]) -> tuple[bool, str]:
    if len(price_history) < 50:
        return False, f"insufficient data: need at least 50 points, got {len(price_history)}"
    
    closes = [p.close for p in price_history]
    if all(c == 0 for c in closes):
        return False, "invalid data: all close prices are zero"
    
    if any(pd.isna(c) or np.isinf(c) for c in closes):
        return False, "invalid data: contains NaN or inf values"
    
    return True, ""

@staticmethod
def _safe_divide(num: float, denom: float, default: float = 0.0) -> float:
    if denom == 0 or pd.isna(denom) or np.isinf(denom):
        return default
    result = num / denom
    if pd.isna(result) or np.isinf(result):
        return default
    return result
```


#### Component 2: RiskAgent (agents/risk_agent.py)

**Bugs Fixed:** 1.6, 1.7, 1.8, 1.9, 1.10

**Specific Changes:**

1. **Improve Insufficient Data Error Message**:
   - Change error message from "insufficient data for risk analysis" to detailed message
   - Include actual count and required count: f"insufficient data: need at least 14 points, got {len(price_history)}"
   - Add this information to both return dict and any logging

2. **Add Extreme Condition Detection**:
   - Create `_detect_extreme_conditions(df)` static method
   - Check for volatility > 0.10 (10% daily swing) as extreme
   - Check for price gaps > 5% between consecutive closes
   - Check for volume spikes > 3x average volume
   - Return dict with flags and detected conditions

3. **Add Regime-Specific Risk Thresholds**:
   - Create `_get_risk_thresholds(market_regime: str)` static method
   - Return different thresholds based on regime:
     - Normal: {LOW: 0.3, MEDIUM: 0.5, HIGH: 0.8}
     - Earnings: {LOW: 0.2, MEDIUM: 0.4, HIGH: 0.6} (lower thresholds, more cautious)
     - Volatile: {LOW: 0.4, MEDIUM: 0.6, HIGH: 0.9} (higher thresholds, expect volatility)
   - Accept market_regime parameter in analyze() method (default="normal")

4. **Add Gap Risk Analysis**:
   - Calculate overnight gaps: `df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)`
   - Compute max gap in recent history (last 14 days)
   - If max gap > 3%, add 0.2 to risk_score
   - Document gap risk in reasons list

5. **Add Logging for NaN Detection**:
   - Import logging module at top of file
   - When NaN detected in RSI or volatility, log before returning:
     - `logger.warning(f"Risk calculation produced NaN: RSI={rsi}, Vol={vol}, data_points={len(df)}")`
   - Include sample of recent close prices in log for debugging
   - Keep existing early return behavior but add logging


6. **Modify analyze() Signature**:
   - Add optional `market_regime: str = "normal"` parameter
   - Use regime-specific thresholds when assigning risk_level
   - Maintain backward compatibility (defaults to "normal" if not provided)

**Implementation Pattern:**
```python
@staticmethod
def analyze(price_history: List[PriceData], market_regime: str = "normal") -> Dict[str, Any]:
    if len(price_history) < 14:
        return {
            "risk_score": 0.0,
            "risk_level": "LOW",
            "reason": f"insufficient data: need at least 14 points, got {len(price_history)}",
        }
    
    # ... existing calculation code ...
    
    # Add gap risk analysis
    df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
    max_gap = df['gap'].abs().max()
    if max_gap > 0.03:
        risk_score += 0.2
        reasons.append(f"Gap risk detected ({max_gap:.2%})")
    
    # Use regime-specific thresholds
    thresholds = RiskAgent._get_risk_thresholds(market_regime)
    if risk_score >= thresholds['HIGH']:
        risk_level = "HIGH"
    elif risk_score >= thresholds['MEDIUM']:
        risk_level = "MEDIUM"
    # ... etc
```


#### Component 3: FusionAgent (agents/fusion_agent.py)

**Bugs Fixed:** 1.11, 1.12, 1.13, 1.14, 1.15

**Specific Changes:**

1. **Add Logging to Parse Errors**:
   - Import logging module at top of file
   - In synthesize() method, wrap float conversions in try-except with logging:
     ```python
     try:
         tech_score = float(tech_data.get('technical_score', 0))
     except ValueError as e:
         logger.warning(f"Failed to parse technical_score: {tech_data.get('technical_score')} - {e}")
         tech_score = 0
     ```
   - Apply same pattern to event_score, risk_score, event_confidence parsing
   - Log the problematic value and field name for debugging

2. **Add Weight Validation and Normalization**:
   - Create `_validate_and_normalize_weights(weights: Dict[str, float])` static method
   - Calculate total weight: `total = sum(weights.values())`
   - Check if total is within tolerance: `abs(total - 1.0) < 0.01`
   - If outside tolerance, normalize: `{k: v/total for k, v in weights.items()}`
   - Log warning if normalization was required
   - Return normalized weights

3. **Document Context Weight Redistribution**:
   - Add inline comment explaining redistribution logic:
     ```python
     # Context agent not yet implemented in MVP, redistribute its weight to technical
     # This maintains total weight sum while giving technical agent more influence
     weights["technical"] += weights.get("context", 0)
     ```
   - Validate weights after redistribution using helper method

4. **Add Comprehensive TOON Field Validation**:
   - Create `_validate_toon_data(data: Dict, required_fields: List[str], source: str)` static method
   - Check that all required fields are present
   - Check that numeric fields can be parsed as floats
   - Log warnings for missing or malformed fields with source context
   - Return validated data dict with defaults for missing fields


5. **Add Final Signal Bounds Checking**:
   - After calculating final_signal, validate it's in valid range
   - Add clamping: `final_signal = max(-1.0, min(1.0, final_signal))`
   - Log warning if clamping was required with original value
   - Ensures signal is always in [-1, 1] range before decision logic

6. **Apply Weight Validation After Confidence Adjustment**:
   - After applying confidence-aware weighting to event signal
   - Call `_validate_and_normalize_weights(weights)` to ensure sum is correct
   - Use normalized weights for signal calculation

**Implementation Pattern:**
```python
@staticmethod
def _validate_and_normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        logger.warning(f"Weights sum to {total:.3f}, normalizing to 1.0")
        return {k: v/total for k, v in weights.items()}
    return weights

@staticmethod
def _validate_toon_data(data: Dict, required_fields: List[str], source: str) -> Dict:
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.warning(f"Missing field '{field}' in {source} TOON data")
            data[field] = 0 if field.endswith('_score') else 'unknown'
    return data
```


#### Component 4: TradeAgent (agents/trade_agent.py)

**Bugs Fixed:** 1.16, 1.17, 1.18, 1.19, 1.20

**Specific Changes:**

1. **Add Position Limit Enforcement**:
   - Add `max_total_exposure: float = 0.50` parameter to __init__ (default 50% of equity)
   - Create `_calculate_total_exposure()` method to sum position_size of all open trades
   - In execute_trade(), check total exposure before opening new trade
   - If `current_exposure + new_position_size > max_total_exposure`, reject trade
   - Return None and log rejection reason

2. **Add Capital Availability Check**:
   - Add `account_balance: float` parameter to __init__ (required for capital checks)
   - Create `_check_capital_available(position_size: float, price: float)` method
   - Calculate required capital: `required = position_size * account_balance * price`
   - Check if required capital is available (considering existing open trades)
   - Return boolean and reason string

3. **Add Market Hours and Gap Risk Handling**:
   - Create `_adjust_stops_for_overnight(action: str, fill_price: float, is_overnight: bool)` method
   - If is_overnight=True, widen stops by 50% to account for gap risk
   - For BUY: `sl = fill_price * 0.97` (3% instead of 2%)
   - For SELL: `sl = fill_price * 1.03` (3% instead of 2%)
   - Add `is_overnight: bool = False` parameter to execute_trade()

4. **Add Partial Fill Handling**:
   - Add `actual_fill_size: float` parameter to Trade model (defaults to position_size)
   - In execute_trade(), simulate partial fills randomly (10% chance of 50-100% fill)
   - Update trade.actual_fill_size with filled amount
   - Log partial fills with warning level
   - Update position tracking to use actual_fill_size instead of position_size


5. **Add Position Size Validation**:
   - Create `_validate_position_size(position_size: float)` method
   - Check that position_size > 0 for actual trades
   - Check that position_size <= max_allocation (0.10)
   - Check that position_size is not NaN or inf
   - Return validation result and error message
   - Call before executing trade, reject if invalid

6. **Add Order Rejection Handling**:
   - Add `rejection_rate: float = 0.05` parameter to __init__ (5% of orders rejected)
   - In execute_trade(), simulate random rejections
   - If rejected, log warning and return None
   - Include rejection reason in log

**Implementation Pattern:**
```python
def execute_trade(self, decision_data: Dict[str, Any], current_price: float, 
                  symbol: str, is_overnight: bool = False) -> Trade:
    decision = decision_data.get("decision", "NO_TRADE")
    if decision == "NO_TRADE":
        return None
    
    position_size = decision_data.get("position_size", 0.0)
    
    # Validate position size
    valid, error = self._validate_position_size(position_size)
    if not valid:
        logger.warning(f"Trade rejected: {error}")
        return None
    
    # Check position limits
    current_exposure = self._calculate_total_exposure()
    if current_exposure + position_size > self.max_total_exposure:
        logger.warning(f"Trade rejected: would exceed max exposure")
        return None
    
    # Check capital availability
    capital_ok, reason = self._check_capital_available(position_size, current_price)
    if not capital_ok:
        logger.warning(f"Trade rejected: {reason}")
        return None
    
    # ... rest of execution logic ...
```


#### Component 5: LearningAgent (agents/learning_agent.py)

**Bugs Fixed:** 1.21, 1.22, 1.23, 1.24, 1.25

**Specific Changes:**

1. **Add SQLite Detection and Pgvector Compatibility Check**:
   - In __init__, detect if db_url contains "sqlite"
   - Set `self.supports_pgvector = False` for SQLite
   - Log warning: "SQLite detected: pgvector operations disabled, using fallback storage"
   - In evaluate_and_store(), skip vector similarity search if not supports_pgvector
   - Store embeddings as JSON text field instead of Vector type for SQLite

2. **Add Connection Pooling**:
   - Import `pool` from sqlalchemy
   - Modify engine creation to use connection pooling:
     ```python
     self.engine = create_engine(
         db_url,
         poolclass=pool.QueuePool,
         pool_size=5,
         max_overflow=10,
         pool_pre_ping=True  # Verify connections before use
     )
     ```
   - Add pool_pre_ping to detect stale connections

3. **Add Retry Logic with Exponential Backoff**:
   - Create `_retry_db_operation(operation: Callable, max_retries: int = 3)` method
   - Implement exponential backoff: 1s, 2s, 4s delays
   - Catch SQLAlchemy connection errors and retry
   - Log each retry attempt with context
   - Raise exception after max retries exhausted

4. **Make Embedding Dimension Configurable**:
   - Add `embedding_dim: int` parameter to __init__
   - Default to `int(os.getenv("EMBEDDING_DIMENSION", "1536"))`
   - Modify TradePattern model to use dynamic dimension:
     ```python
     embedding = Column(Vector(self.embedding_dim))
     ```
   - Note: This requires creating table dynamically, not using declarative_base
   - Alternative: Keep 1536 in schema, validate input dimension matches


5. **Add Automatic Cleanup Mechanism**:
   - Create `cleanup_old_records(retention_days: int = 90)` method
   - Delete SentimentValidation records older than retention_days
   - Use SQL: `DELETE FROM sentiment_validations WHERE timestamp < NOW() - INTERVAL '{retention_days} days'`
   - Log number of records deleted
   - Call automatically in __init__ or provide as maintenance method
   - Add environment variable: `VALIDATION_RETENTION_DAYS` (default 90)

6. **Add Graceful Degradation for Database Failures**:
   - Wrap all database operations in try-except blocks
   - In evaluate_and_store(), if database fails, log error but don't crash
   - Return success=False indicator instead of raising exception
   - In get_dynamic_weights_for_regime(), if database fails, return static fallback weights
   - In track_sentiment_accuracy(), if database fails, log error and return error dict
   - Add `self.degraded_mode = False` flag to track if database is unavailable

**Implementation Pattern:**
```python
def __init__(self, db_url: str = None, embedding_dim: int = None):
    if db_url is None:
        db_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    
    if embedding_dim is None:
        embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    
    self.embedding_dim = embedding_dim
    self.supports_pgvector = "postgresql" in db_url
    self.degraded_mode = False
    
    if not self.supports_pgvector:
        logger.warning("SQLite detected: pgvector operations disabled")
    
    try:
        self.engine = create_engine(
            db_url,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        # ... rest of init ...
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        self.degraded_mode = True
```


#### Component 6: Graph Orchestration (agents/graph.py)

**Bugs Fixed:** 1.26, 1.27, 1.28, 1.29, 1.30

**Specific Changes:**

1. **Add Timeout Handling for Agent Operations**:
   - Import `signal` and `TimeoutError` modules
   - Create `_run_with_timeout(func: Callable, timeout_seconds: int)` helper
   - Use `signal.alarm()` for Unix or `threading.Timer` for cross-platform
   - Wrap each agent node function with timeout decorator
   - Default timeouts: technical=30s, event=60s, risk=30s, context=30s, fusion=10s
   - If timeout occurs, log error and return error state
   - Alternative: Use asyncio with `asyncio.wait_for()` if converting to async

2. **Add Circuit Breaker Pattern**:
   - Create `CircuitBreaker` class to track agent failures
   - States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)
   - Track consecutive failures per agent type
   - After 3 consecutive failures, open circuit (stop calling agent)
   - After 60 seconds in OPEN state, transition to HALF_OPEN (try once)
   - If HALF_OPEN call succeeds, close circuit; if fails, reopen
   - Store circuit breakers in global dict: `agent_circuit_breakers = {}`

3. **Add State Validation Between Nodes**:
   - Create `_validate_state(state: TradingState, required_fields: List[str])` helper
   - Before each node, validate required fields are present
   - Check field types match expected types (List[PriceData], Dict, etc.)
   - If validation fails, log error and return error state
   - Add validation at key transition points:
     - Before technical/event/risk: validate price_history and news_list
     - Before fusion: validate technical_data, event_data, risk_data
     - Before trade: validate decision_data

4. **Add Rollback Mechanism**:
   - Create `_checkpoint_state(state: TradingState)` to save state snapshots
   - Store last known good state in global variable or state field
   - If node fails, restore from checkpoint
   - Add `last_checkpoint` field to TradingState
   - In each node, checkpoint state before processing
   - On exception, restore from checkpoint and mark node as failed


5. **Add Comprehensive State Transition Logging**:
   - Import logging module and configure logger
   - At start of each node function, log entry with timestamp and state summary
   - Log key state values: symbol, regime, data counts, scores
   - At end of each node function, log exit with results
   - Log format: `[SYMBOL] NODE_NAME: entry/exit - key_values`
   - Example: `[AAPL] technical: entry - price_points=50, regime=normal`
   - Example: `[AAPL] technical: exit - score=0.65, trend=bullish`
   - Add exception logging with full traceback for debugging

6. **Wrap All Node Functions with Error Handling**:
   - Create `@safe_node` decorator that wraps node functions
   - Catches all exceptions, logs them, and returns error state
   - Prevents single node failure from crashing entire workflow
   - Error state includes error message and failed node name
   - Allows workflow to continue or gracefully terminate

**Implementation Pattern:**
```python
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

agent_circuit_breakers = {
    "technical": CircuitBreaker(),
    "event": CircuitBreaker(),
    "risk": CircuitBreaker(),
    "context": CircuitBreaker(),
    "fusion": CircuitBreaker()
}

def safe_node(node_name: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(state: TradingState):
            logger.info(f"[{state.get('symbol', 'UNKNOWN')}] {node_name}: entry")
            try:
                result = func(state)
                logger.info(f"[{state.get('symbol', 'UNKNOWN')}] {node_name}: exit - success")
                return result
            except Exception as e:
                logger.error(f"[{state.get('symbol', 'UNKNOWN')}] {node_name}: error - {e}", exc_info=True)
                return {"error": str(e), "failed_node": node_name}
        return wrapper
    return decorator
```


## Testing Strategy

### Validation Approach

The testing strategy follows a three-phase approach: first, demonstrate bugs on unfixed code (exploratory), then verify fixes work correctly (fix checking), and finally ensure existing functionality is preserved (preservation checking). Each of the 30 bugs will have dedicated test cases that fail on unfixed code and pass on fixed code.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate each of the 30 bugs BEFORE implementing fixes. Confirm root cause analysis. If tests pass unexpectedly, re-hypothesize the root cause.

**Test Plan**: Write targeted test cases for each bug category that trigger the bug conditions on unfixed code. Run tests and observe failures (crashes, incorrect values, silent failures). Document the exact failure modes to guide fix implementation.

**Test Cases by Category:**

**TechnicalAgent Tests (Bugs 1.1-1.5):**
1. **Division by Zero Test**: Create price_history with no price variation → RSI calculation crashes with ZeroDivisionError
2. **NaN Propagation Test**: Create price_history that produces NaN RSI → verify NaN propagates to output without detection
3. **All-Zero Data Test**: Create price_history with all close=0 → verify incorrect indicator calculations
4. **Zero Volume Test**: Create price_history with all volume=0 → verify NaN in volume trend calculation
5. **Unbounded Indicator Test**: Mock RSI=NaN → verify comparison logic fails or produces incorrect results

**RiskAgent Tests (Bugs 1.6-1.10):**
1. **Insufficient Data Test**: Pass 10 price points → verify error message is vague (doesn't specify 14 required)
2. **Extreme Volatility Test**: Create flash crash scenario (15% volatility) → verify no special handling
3. **Hardcoded Threshold Test**: Pass earnings regime → verify same thresholds used as normal regime
4. **Gap Risk Test**: Create overnight gap scenario → verify gap risk not captured in risk_score
5. **NaN Logging Test**: Create data that produces NaN RSI → verify no log entry before early return

**FusionAgent Tests (Bugs 1.11-1.15):**
1. **Parse Error Test**: Pass TOON with technical_score="N/A" → verify ValueError caught but not logged
2. **Weight Sum Test**: Apply confidence adjustment → verify weights no longer sum to 1.0
3. **Context Redistribution Test**: Check context weight redistribution → verify no documentation or validation
4. **Missing Field Test**: Pass TOON with missing risk_level → verify silent default without warning
5. **Signal Bounds Test**: Mock calculation that produces final_signal=1.5 → verify no clamping before use


**TradeAgent Tests (Bugs 1.16-1.20):**
1. **Position Limit Test**: Open 5 trades with 10% each → verify no check prevents 50% total exposure
2. **Capital Check Test**: Attempt trade requiring more capital than available → verify no rejection
3. **Market Hours Test**: Set stop loss during market hours → verify no adjustment for overnight gaps
4. **Partial Fill Test**: Execute order → verify no handling for partial fills (assumes 100% fill)
5. **Position Size Validation Test**: Pass negative position_size → verify no validation before execution

**LearningAgent Tests (Bugs 1.21-1.25):**
1. **SQLite Pgvector Test**: Initialize with SQLite → attempt pgvector operation → verify silent failure
2. **Connection Retry Test**: Simulate connection timeout → verify no retry logic, immediate failure
3. **Embedding Dimension Test**: Try to store 768-dim embedding with 1536-dim schema → verify insertion fails
4. **Cleanup Test**: Check database after 1000 validation records → verify no cleanup mechanism
5. **Connection Failure Test**: Simulate database unavailable → verify agent crashes instead of degrading

**Graph Orchestration Tests (Bugs 1.26-1.30):**
1. **Timeout Test**: Mock EventAgent to hang for 5 minutes → verify workflow blocks indefinitely
2. **Circuit Breaker Test**: Make TechnicalAgent fail 10 times → verify continuous retry without circuit breaker
3. **State Validation Test**: Pass state with price_history=None to TechnicalAgent → verify no validation, crashes
4. **Rollback Test**: Make FusionAgent fail mid-execution → verify no rollback, inconsistent state
5. **Logging Test**: Run full workflow → verify no state transition logs for debugging

**Expected Counterexamples:**
- TechnicalAgent: ZeroDivisionError on line `rs = gain / loss`
- RiskAgent: Vague error message "insufficient data for risk analysis"
- FusionAgent: Silent ValueError with no log entry
- TradeAgent: Over-exposure with 5 open trades totaling 50%
- LearningAgent: Silent pgvector failure on SQLite
- Graph: Workflow hangs indefinitely on slow agent operation


### Fix Checking

**Goal**: Verify that for all inputs where bug conditions hold, the fixed system produces expected behavior (validation, error handling, logging, graceful degradation).

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedAgent(input)
  ASSERT expectedBehavior(result)
  ASSERT noSystemCrash()
  ASSERT appropriateLogging()
  ASSERT gracefulDegradation()
END FOR
```

**Test Plan**: Re-run all exploratory tests on fixed code. Verify that:
- No crashes occur (ZeroDivisionError, NaN propagation eliminated)
- Validation catches edge cases and returns error states with detailed messages
- All errors are logged with context for debugging
- System degrades gracefully (returns safe defaults, continues operation)
- All 30 bugs are resolved

**Verification Criteria:**
- TechnicalAgent: Division by zero handled with epsilon or RSI=100, NaN detected and logged
- RiskAgent: Detailed error messages, regime-specific thresholds, gap risk analysis
- FusionAgent: Parse errors logged, weights validated and normalized, signals clamped
- TradeAgent: Position limits enforced, capital checked, partial fills handled
- LearningAgent: SQLite compatibility, connection pooling, retry logic, cleanup mechanism
- Graph: Timeouts enforced, circuit breakers active, state validated, transitions logged


### Preservation Checking

**Goal**: Verify that for all inputs where bug conditions do NOT hold, the fixed system produces exactly the same results as the original system.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT fixedAgent(input) = originalAgent(input)
  ASSERT toonFormatUnchanged(input)
  ASSERT calculationLogicUnchanged(input)
  ASSERT thresholdsUnchanged(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the valid input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs
- It validates TOON format consistency across thousands of generated inputs

**Test Plan**: Use existing test files (test_technical.py, test_risk.py, etc.) as baseline. Run on both unfixed and fixed code with valid inputs. Compare outputs to ensure exact match.

**Test Cases:**

**TechnicalAgent Preservation:**
1. **Valid Price History Test**: 50+ data points with normal price variation → verify same technical_score, trend, momentum
2. **TOON Format Test**: Verify output format exactly matches: "technical_score: X.XX\ntrend: ...\nmomentum: ...\nreason: ..."
3. **Calculation Logic Test**: Verify EMA_20, EMA_50, RSI_14 formulas unchanged
4. **Threshold Test**: Verify RSI thresholds (40, 60) and score clamping [0, 1] unchanged

**RiskAgent Preservation:**
1. **Valid Risk Calculation Test**: 14+ data points with normal volatility → verify same risk_score, risk_level
2. **TOON Format Test**: Verify output format: "risk_score: X.XX\nrisk_level: ...\nreason: ..."
3. **Indicator Test**: Verify RSI_14 and 14-period volatility calculations unchanged
4. **Threshold Test**: Verify baseline thresholds (0.3, 0.5, 0.8) used for normal regime

**FusionAgent Preservation:**
1. **Valid Synthesis Test**: Valid TOON inputs → verify same decision, confidence, position_size
2. **Regime Weights Test**: Verify earnings/volatile/normal regime weights unchanged
3. **Veto Test**: CRITICAL risk → verify hard veto still enforced
4. **Decision Thresholds Test**: Verify ±0.4 thresholds for BUY/SELL unchanged
5. **Position Sizing Test**: Verify MAX_ALLOCATION=0.10 and confidence scaling unchanged


**TradeAgent Preservation:**
1. **Valid Trade Execution Test**: Valid decision with sufficient capital → verify same slippage, commission, stops
2. **Slippage Test**: Verify slippage_bps calculation unchanged
3. **Commission Test**: Verify commission_pct application unchanged
4. **Stop/Target Test**: Verify 2% stop loss and 4% target (1:2 RR) unchanged for normal trades
5. **Trade Monitoring Test**: Verify stop loss and target hit detection logic unchanged

**LearningAgent Preservation:**
1. **Valid Pattern Storage Test**: Valid trade with PostgreSQL → verify same storage behavior
2. **Schema Test**: Verify TradePattern and SentimentValidation tables unchanged
3. **Dynamic Weights Test**: Verify regime-specific weight dictionaries unchanged
4. **Sentiment Accuracy Test**: Verify accuracy calculation formulas unchanged

**Graph Orchestration Preservation:**
1. **Valid Workflow Test**: Valid inputs → verify same workflow sequence
2. **Workflow Structure Test**: Verify START → fetch_data → [technical, event, risk, context] → fusion → trade → END unchanged
3. **Parallel Execution Test**: Verify agents still run in parallel after fetch_data
4. **State Flow Test**: Verify TradingState structure and field names unchanged

### Unit Tests

- Test each validation helper function independently (e.g., _validate_price_history, _safe_divide)
- Test each error handling path (division by zero, NaN detection, parse errors)
- Test each new feature (circuit breaker state transitions, timeout enforcement, weight normalization)
- Test edge cases for each bug fix (exactly 14 data points, exactly 0 loss, exactly 50% exposure)
- Test logging output (verify log messages contain expected context)

### Property-Based Tests

- Generate random valid price histories (50-200 points, normal distributions) → verify outputs match original
- Generate random TOON strings with valid formats → verify parsing produces same results
- Generate random trade scenarios within limits → verify execution behavior unchanged
- Generate random market regimes and verify regime-specific logic works correctly
- Test that all TOON outputs maintain exact format across thousands of generated inputs

### Integration Tests

- Test full workflow with valid inputs → verify end-to-end behavior unchanged
- Test full workflow with each bug condition → verify graceful handling
- Test database operations with PostgreSQL and SQLite → verify compatibility
- Test circuit breaker recovery → verify system resumes after failures
- Test timeout recovery → verify workflow continues after slow operations
- Test logging output → verify all state transitions are logged for debugging

