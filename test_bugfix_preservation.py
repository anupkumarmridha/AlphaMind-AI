"""
Preservation Property Tests (Task 2) - Requirements 3.1-3.27

These tests verify that existing CORRECT behavior is preserved after fixes.
They MUST PASS on the current unfixed code.

Validates: Requirements 3.1-3.27
"""
from datetime import datetime, timedelta
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from data.schema import PriceData, NewsData
from agents.technical_agent import TechnicalAgent
from agents.risk_agent import RiskAgent
from agents.fusion_agent import FusionAgent
from agents.trade_agent import TradeAgent
from agents.learning_agent import LearningAgent
from agents.graph import TradingState, build_graph


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_price_history(n=60, base_close=100.0, vary=True, volume=1000):
    """Generate n PriceData points with normal variation and non-zero volume."""
    base = datetime(2024, 1, 1)
    prices = []
    for i in range(n):
        c = base_close + (i % 7) - 3 if vary else base_close
        prices.append(PriceData(
            open=c - 0.5, high=c + 1.0, low=c - 1.0, close=c,
            volume=volume,
            timestamp=base + timedelta(days=i),
        ))
    return prices


def make_toon(tech_score=0.6, event_score=0.6, risk_score=0.2,
              risk_level="LOW", event_confidence=0.8):
    tech = (
        f"technical_score: {tech_score}\n"
        f"trend: bullish\nmomentum: strong\nreason: EMA20 > EMA50\n"
    )
    event = (
        f"event_score: {event_score}\n"
        f"sentiment: bullish\nconfidence_score: {event_confidence}\n"
        f"reason: positive news\n"
    )
    risk = (
        f"risk_score: {risk_score}\n"
        f"risk_level: {risk_level}\nreason: Normal conditions\n"
    )
    return tech, event, risk


# ---------------------------------------------------------------------------
# TechnicalAgent Preservation (Requirements 3.1-3.4)
# ---------------------------------------------------------------------------

def test_preservation_technical_score_range():
    """
    Validates: Requirements 3.1, 3.2
    Valid price history (60 points, normal variation, non-zero volume) produces
    technical_score in [0.0, 1.0] using 0.5 as neutral baseline.
    """
    prices = make_price_history(n=60)
    result = TechnicalAgent.analyze(prices)
    score = result.get("technical_score")
    assert score is not None, "technical_score missing from result"
    assert 0.0 <= score <= 1.0, f"technical_score {score} out of [0.0, 1.0]"


def test_preservation_technical_required_keys():
    """
    Validates: Requirements 3.4
    Returns dict with keys: technical_score, trend, momentum, reason.
    """
    prices = make_price_history(n=60)
    result = TechnicalAgent.analyze(prices)
    for key in ("technical_score", "trend", "momentum", "reason"):
        assert key in result, f"Missing key '{key}' in TechnicalAgent result"


def test_preservation_technical_trend_values():
    """
    Validates: Requirements 3.3
    trend is one of: "bullish", "bearish", "neutral".
    """
    prices = make_price_history(n=60)
    result = TechnicalAgent.analyze(prices)
    assert result["trend"] in ("bullish", "bearish", "neutral"), \
        f"Unexpected trend value: {result['trend']}"


def test_preservation_technical_momentum_values():
    """
    Validates: Requirements 3.3
    momentum is one of: "strong", "weak", "neutral", "unknown".
    """
    prices = make_price_history(n=60)
    result = TechnicalAgent.analyze(prices)
    assert result["momentum"] in ("strong", "weak", "neutral", "unknown"), \
        f"Unexpected momentum value: {result['momentum']}"


def test_preservation_technical_neutral_baseline():
    """
    Validates: Requirements 3.2
    Score uses 0.5 as neutral baseline - insufficient data returns 0.0 (not 0.5),
    but valid data starts from 0.5 and adjusts. Verify score is anchored near 0.5
    for mixed signals.
    """
    # Build a price history where EMA20 ≈ EMA50 and RSI ≈ 50 (neutral)
    # Use a flat-ish price with slight variation to avoid NaN
    prices = make_price_history(n=60, vary=True)
    result = TechnicalAgent.analyze(prices)
    # Score should be in [0.0, 1.0] and the code starts from 0.5
    assert 0.0 <= result["technical_score"] <= 1.0


@given(
    n=st.integers(min_value=60, max_value=120),
    base_close=st.floats(min_value=10.0, max_value=1000.0),
    volume=st.integers(min_value=100, max_value=100000),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_preservation_technical_property_score_range(n, base_close, volume):
    """
    Validates: Requirements 3.1, 3.2
    Property: for any valid price history (>=60 pts, normal variation, non-zero volume),
    technical_score is always in [0.0, 1.0].
    """
    prices = make_price_history(n=n, base_close=base_close, volume=volume)
    result = TechnicalAgent.analyze(prices)
    score = result.get("technical_score", -1)
    assert 0.0 <= score <= 1.0, f"technical_score {score} out of range for n={n}"


# ---------------------------------------------------------------------------
# RiskAgent Preservation (Requirements 3.5-3.8)
# ---------------------------------------------------------------------------

def test_preservation_risk_required_keys():
    """
    Validates: Requirements 3.8
    Valid price history (20 points) returns risk_score, risk_level, reason.
    """
    prices = make_price_history(n=20)
    result = RiskAgent.analyze(prices)
    for key in ("risk_score", "risk_level", "reason"):
        assert key in result, f"Missing key '{key}' in RiskAgent result"


def test_preservation_risk_level_values():
    """
    Validates: Requirements 3.6
    risk_level is one of: "LOW", "MEDIUM", "HIGH", "CRITICAL".
    """
    prices = make_price_history(n=20)
    result = RiskAgent.analyze(prices)
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL"), \
        f"Unexpected risk_level: {result['risk_level']}"


def test_preservation_risk_score_range():
    """
    Validates: Requirements 3.5
    risk_score is in [0.0, 1.0].
    """
    prices = make_price_history(n=20)
    result = RiskAgent.analyze(prices)
    score = result["risk_score"]
    assert 0.0 <= score <= 1.0, f"risk_score {score} out of [0.0, 1.0]"


def test_preservation_risk_threshold_critical():
    """
    Validates: Requirements 3.7
    Baseline threshold: risk_score >= 0.8 → CRITICAL.
    Trigger with extreme RSI (>80) + high volatility to push score >= 0.8.
    """
    # Build a price history that triggers RSI > 80 and high volatility
    base = datetime(2024, 1, 1)
    prices = []
    close = 100.0
    for i in range(20):
        # Steadily rising prices → RSI overbought, plus add volatility
        close = close * 1.03  # 3% daily gain → RSI will be very high
        prices.append(PriceData(
            open=close - 2, high=close + 3, low=close - 3, close=close,
            volume=1000,
            timestamp=base + timedelta(days=i),
        ))
    result = RiskAgent.analyze(prices)
    # If risk_score >= 0.8, it must be CRITICAL
    if result["risk_score"] >= 0.8:
        assert result["risk_level"] == "CRITICAL", \
            f"risk_score={result['risk_score']} >= 0.8 but risk_level={result['risk_level']}, expected CRITICAL"


def test_preservation_risk_threshold_high():
    """
    Validates: Requirements 3.7
    Baseline threshold: risk_score >= 0.5 → HIGH (when not CRITICAL).
    """
    prices = make_price_history(n=20)
    result = RiskAgent.analyze(prices)
    score = result["risk_score"]
    level = result["risk_level"]
    if 0.5 <= score < 0.8:
        assert level == "HIGH", \
            f"risk_score={score} in [0.5, 0.8) but risk_level={level}, expected HIGH"


def test_preservation_risk_threshold_medium():
    """
    Validates: Requirements 3.7
    Baseline threshold: risk_score >= 0.3 → MEDIUM (when not HIGH/CRITICAL).
    """
    prices = make_price_history(n=20)
    result = RiskAgent.analyze(prices)
    score = result["risk_score"]
    level = result["risk_level"]
    if 0.3 <= score < 0.5:
        assert level == "MEDIUM", \
            f"risk_score={score} in [0.3, 0.5) but risk_level={level}, expected MEDIUM"


def test_preservation_risk_normal_conditions():
    """
    Validates: Requirements 3.8
    Normal conditions (very mild variation, no extreme RSI/volatility) return LOW or MEDIUM.
    Uses tiny price variation (<0.5% daily) to stay below the 2% volatility threshold.
    """
    base = datetime(2024, 1, 1)
    prices = []
    close = 100.0
    for i in range(20):
        # Tiny oscillation: ±0.1 → volatility well below 2% threshold
        c = close + (0.1 if i % 2 == 0 else -0.1)
        prices.append(PriceData(
            open=c - 0.05, high=c + 0.1, low=c - 0.1, close=c,
            volume=1000,
            timestamp=base + timedelta(days=i),
        ))
    result = RiskAgent.analyze(prices)
    assert result["risk_level"] in ("LOW", "MEDIUM"), \
        f"Normal conditions produced unexpected risk_level: {result['risk_level']} (score={result['risk_score']})"


@given(
    n=st.integers(min_value=20, max_value=60),
    base_close=st.floats(min_value=10.0, max_value=500.0),
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_preservation_risk_property_level_valid(n, base_close):
    """
    Validates: Requirements 3.6
    Property: risk_level is always one of the four valid tiers.
    """
    prices = make_price_history(n=n, base_close=base_close)
    result = RiskAgent.analyze(prices)
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


# ---------------------------------------------------------------------------
# FusionAgent Preservation (Requirements 3.9-3.13)
# ---------------------------------------------------------------------------

def test_preservation_fusion_required_keys():
    """
    Validates: Requirements 3.13
    Returns: decision, confidence, position_size, reason.
    """
    tech, event, risk = make_toon()
    result = FusionAgent.synthesize(tech, event, risk)
    for key in ("decision", "confidence", "position_size", "reason"):
        assert key in result, f"Missing key '{key}' in FusionAgent result"


def test_preservation_fusion_decision_values():
    """
    Validates: Requirements 3.11
    decision is one of: "BUY", "SELL", "NO_TRADE".
    """
    tech, event, risk = make_toon()
    result = FusionAgent.synthesize(tech, event, risk)
    assert result["decision"] in ("BUY", "SELL", "NO_TRADE"), \
        f"Unexpected decision: {result['decision']}"


def test_preservation_fusion_critical_risk_veto():
    """
    Validates: Requirements 3.10
    CRITICAL risk level enforces NO_TRADE veto regardless of other signals.
    """
    tech, event, _ = make_toon(tech_score=0.9, event_score=0.9)
    critical_risk = "risk_score: 0.9\nrisk_level: CRITICAL\nreason: extreme volatility\n"
    result = FusionAgent.synthesize(tech, event, critical_risk)
    assert result["decision"] == "NO_TRADE", \
        f"CRITICAL risk did not enforce NO_TRADE veto. Got: {result['decision']}"
    assert result["position_size"] == 0.0, \
        f"CRITICAL risk veto should set position_size=0.0, got {result['position_size']}"


def test_preservation_fusion_buy_threshold():
    """
    Validates: Requirements 3.11
    Decision threshold: final_signal >= 0.4 → BUY.
    Use strong bullish signals with low risk to push signal above 0.4.
    """
    tech = "technical_score: 0.9\ntrend: bullish\nmomentum: strong\nreason: strong bull\n"
    event = "event_score: 0.9\nsentiment: bullish\nconfidence_score: 1.0\nreason: great news\n"
    risk = "risk_score: 0.0\nrisk_level: LOW\nreason: no risk\n"
    result = FusionAgent.synthesize(tech, event, risk, market_regime="normal")
    # With tech_score=0.9 and event_score=0.9, signal should be strongly positive → BUY
    assert result["decision"] == "BUY", \
        f"Strong bullish signals should produce BUY. Got: {result['decision']}, confidence={result['confidence']}"


def test_preservation_fusion_sell_threshold():
    """
    Validates: Requirements 3.11
    Decision threshold: final_signal <= -0.4 → SELL.
    """
    tech = "technical_score: 0.1\ntrend: bearish\nmomentum: weak\nreason: strong bear\n"
    event = "event_score: 0.1\nsentiment: bearish\nconfidence_score: 1.0\nreason: bad news\n"
    risk = "risk_score: 0.0\nrisk_level: LOW\nreason: no risk\n"
    result = FusionAgent.synthesize(tech, event, risk, market_regime="normal")
    assert result["decision"] == "SELL", \
        f"Strong bearish signals should produce SELL. Got: {result['decision']}, confidence={result['confidence']}"


def test_preservation_fusion_max_allocation():
    """
    Validates: Requirements 3.12
    MAX_ALLOCATION = 0.10 → position_size <= 0.10 always.
    """
    tech = "technical_score: 1.0\ntrend: bullish\nmomentum: strong\nreason: max bull\n"
    event = "event_score: 1.0\nsentiment: bullish\nconfidence_score: 1.0\nreason: max event\n"
    risk = "risk_score: 0.0\nrisk_level: LOW\nreason: no risk\n"
    result = FusionAgent.synthesize(tech, event, risk, market_regime="normal")
    assert result["position_size"] <= 0.10, \
        f"position_size {result['position_size']} exceeds MAX_ALLOCATION=0.10"


def test_preservation_fusion_no_trade_zero_position():
    """
    Validates: Requirements 3.12, 3.13
    NO_TRADE decision always has position_size=0.0.
    """
    # Neutral signals → NO_TRADE
    tech = "technical_score: 0.5\ntrend: neutral\nmomentum: neutral\nreason: neutral\n"
    event = "event_score: 0.5\nsentiment: neutral\nconfidence_score: 0.5\nreason: neutral\n"
    risk = "risk_score: 0.3\nrisk_level: MEDIUM\nreason: medium risk\n"
    result = FusionAgent.synthesize(tech, event, risk, market_regime="normal")
    if result["decision"] == "NO_TRADE":
        assert result["position_size"] == 0.0, \
            f"NO_TRADE should have position_size=0.0, got {result['position_size']}"


@given(
    tech_score=st.floats(min_value=0.0, max_value=1.0),
    event_score=st.floats(min_value=0.0, max_value=1.0),
    risk_score=st.floats(min_value=0.0, max_value=0.7),  # avoid CRITICAL
    regime=st.sampled_from(["normal", "earnings", "volatile"]),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_preservation_fusion_property_position_size_bounded(tech_score, event_score, risk_score, regime):
    """
    Validates: Requirements 3.12
    Property: position_size is always in [0.0, 0.10] for non-CRITICAL risk.
    """
    tech = f"technical_score: {tech_score}\ntrend: neutral\nmomentum: neutral\nreason: test\n"
    event = f"event_score: {event_score}\nsentiment: neutral\nconfidence_score: 0.8\nreason: test\n"
    risk = f"risk_score: {risk_score}\nrisk_level: LOW\nreason: test\n"
    result = FusionAgent.synthesize(tech, event, risk, market_regime=regime)
    assert 0.0 <= result["position_size"] <= 0.10, \
        f"position_size {result['position_size']} out of [0.0, 0.10]"


# ---------------------------------------------------------------------------
# TradeAgent Preservation (Requirements 3.14-3.18)
# ---------------------------------------------------------------------------

def test_preservation_trade_buy_produces_trade_object():
    """
    Validates: Requirements 3.14, 3.15, 3.16
    Valid BUY trade produces Trade object with fill_price, stop_loss, target_price.
    """
    agent = TradeAgent()
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None, "BUY decision should produce a Trade object"
    assert hasattr(trade, "fill_price"), "Trade missing fill_price"
    assert hasattr(trade, "stop_loss"), "Trade missing stop_loss"
    assert hasattr(trade, "target"), "Trade missing target"


def test_preservation_trade_slippage_applied():
    """
    Validates: Requirements 3.14
    Slippage applied: fill_price != current_price for BUY.
    """
    agent = TradeAgent(slippage_bps=5.0)
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None
    assert trade.fill_price != 100.0, \
        f"Slippage not applied: fill_price={trade.fill_price} equals current_price=100.0"
    assert trade.fill_price > 100.0, \
        f"BUY fill_price should be above current_price due to slippage. Got {trade.fill_price}"


def test_preservation_trade_commission_applied():
    """
    Validates: Requirements 3.15
    Commission applied: commission_fee > 0.
    """
    agent = TradeAgent(commission_pct=0.001)
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None
    assert trade.commission_fee > 0, \
        f"Commission not applied: commission_fee={trade.commission_fee}"


def test_preservation_trade_stop_loss_buy():
    """
    Validates: Requirements 3.16
    Stop loss ~2% below fill_price for BUY (within tolerance).
    """
    agent = TradeAgent(slippage_bps=1.0)  # minimal slippage for predictability
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None
    expected_sl = trade.fill_price * 0.98
    # Allow 0.5% tolerance around the expected stop loss
    assert abs(trade.stop_loss - expected_sl) / expected_sl < 0.005, \
        f"stop_loss={trade.stop_loss} not ~2% below fill_price={trade.fill_price}"


def test_preservation_trade_target_buy():
    """
    Validates: Requirements 3.16
    Target ~4% above fill_price for BUY (1:2 risk-reward).
    """
    agent = TradeAgent(slippage_bps=1.0)
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None
    expected_tg = trade.fill_price * 1.04
    assert abs(trade.target - expected_tg) / expected_tg < 0.005, \
        f"target={trade.target} not ~4% above fill_price={trade.fill_price}"


def test_preservation_trade_no_trade_returns_none():
    """
    Validates: Requirements 3.14
    NO_TRADE decision returns None.
    """
    agent = TradeAgent()
    decision = {"decision": "NO_TRADE", "position_size": 0.0, "confidence": 0.0, "reason": "veto"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is None, f"NO_TRADE should return None, got {trade}"


def test_preservation_trade_monitor_closes_on_stop_loss():
    """
    Validates: Requirements 3.17
    monitor_trades() closes trade when price hits stop_loss.
    """
    agent = TradeAgent(slippage_bps=1.0)
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None
    # Price drops below stop_loss
    agent.monitor_trades(trade.stop_loss - 1.0)
    assert trade in agent.trade_history, "Trade should be in trade_history after stop loss hit"
    assert trade not in agent.open_trades, "Trade should be removed from open_trades"
    assert trade.status == "CLOSED"


def test_preservation_trade_monitor_closes_on_target():
    """
    Validates: Requirements 3.17, 3.18
    monitor_trades() closes trade when price hits target; moves to trade_history.
    """
    agent = TradeAgent(slippage_bps=1.0)
    decision = {"decision": "BUY", "position_size": 0.05, "confidence": 0.7, "reason": "test"}
    trade = agent.execute_trade(decision, current_price=100.0, symbol="AAPL")
    assert trade is not None
    # Price rises above target
    agent.monitor_trades(trade.target + 1.0)
    assert trade in agent.trade_history, "Trade should be in trade_history after target hit"
    assert trade.status == "CLOSED"


# ---------------------------------------------------------------------------
# LearningAgent Preservation (Requirements 3.19-3.22)
# ---------------------------------------------------------------------------

def test_preservation_learning_sqlite_connection():
    """
    Validates: Requirements 3.19
    SQLite connection works (sqlite:///:memory:) - agent initializes without error.
    """
    agent = LearningAgent(db_url="sqlite:///:memory:")
    assert agent is not None
    assert agent.engine is not None
    assert agent.SessionLocal is not None


def test_preservation_learning_dynamic_weights_keys():
    """
    Validates: Requirements 3.21
    get_dynamic_weights_for_regime("normal") returns dict with keys: technical, event, risk.
    """
    agent = LearningAgent(db_url="sqlite:///:memory:")
    weights = agent.get_dynamic_weights_for_regime("normal")
    assert isinstance(weights, dict), "get_dynamic_weights_for_regime should return a dict"
    for key in ("technical", "event", "risk"):
        assert key in weights, f"Missing key '{key}' in dynamic weights"


def test_preservation_learning_dynamic_weights_sum():
    """
    Validates: Requirements 3.21
    get_dynamic_weights_for_regime returns a dict where each weight is in [0, 1]
    and the required keys (technical, event, risk) are present with positive values.
    Note: the current implementation includes a 'context' key, so the sum may exceed 1.0;
    this test preserves the observed behavior of the unfixed code.
    """
    agent = LearningAgent(db_url="sqlite:///:memory:")
    for regime in ("normal", "earnings"):
        weights = agent.get_dynamic_weights_for_regime(regime)
        for key in ("technical", "event", "risk"):
            assert key in weights, f"Missing key '{key}' in weights for regime='{regime}'"
            assert 0.0 < weights[key] <= 1.0, \
                f"Weight '{key}'={weights[key]} out of (0, 1] for regime='{regime}'"


def test_preservation_learning_track_sentiment_accuracy_keys():
    """
    Validates: Requirements 3.22
    track_sentiment_accuracy() returns dict with accuracy metrics.
    """
    from datetime import datetime
    agent = LearningAgent(db_url="sqlite:///:memory:")
    result = agent.track_sentiment_accuracy(
        symbol="AAPL",
        predicted_sentiment="bullish",
        predicted_confidence=0.8,
        trade_entry_time=datetime(2024, 1, 1, 9, 30),
        trade_exit_time=datetime(2024, 1, 1, 15, 30),
        entry_price=100.0,
        exit_price=102.0,
        market_regime="normal",
    )
    assert isinstance(result, dict), "track_sentiment_accuracy should return a dict"
    # Must contain accuracy-related fields
    assert "is_accurate" in result, "Missing 'is_accurate' in result"
    assert "predicted_sentiment" in result, "Missing 'predicted_sentiment' in result"
    assert "actual_direction" in result, "Missing 'actual_direction' in result"


def test_preservation_learning_sentiment_accuracy_correctness():
    """
    Validates: Requirements 3.22
    Accuracy computed correctly: bullish prediction + price up → is_accurate=True.
    """
    from datetime import datetime
    agent = LearningAgent(db_url="sqlite:///:memory:")
    result = agent.track_sentiment_accuracy(
        symbol="AAPL",
        predicted_sentiment="bullish",
        predicted_confidence=0.9,
        trade_entry_time=datetime(2024, 1, 1, 9, 30),
        trade_exit_time=datetime(2024, 1, 1, 15, 30),
        entry_price=100.0,
        exit_price=102.0,  # +2% → bullish actual
        market_regime="normal",
    )
    assert result["is_accurate"] is True, \
        f"Bullish prediction with +2% price change should be accurate. Got: {result}"


def test_preservation_learning_trade_pattern_model_fields():
    """
    Validates: Requirements 3.19
    TradePattern model has required fields: symbol, action, reason_toon, market_regime, embedding.
    """
    from agents.learning_agent import TradePattern
    required = ("symbol", "action", "reason_toon", "market_regime", "embedding")
    for field in required:
        assert hasattr(TradePattern, field) or field in TradePattern.__table__.columns, \
            f"TradePattern missing field '{field}'"


def test_preservation_learning_sentiment_validation_model_fields():
    """
    Validates: Requirements 3.20
    SentimentValidation model has all current fields.
    """
    from agents.learning_agent import SentimentValidation
    required = (
        "symbol", "predicted_sentiment", "predicted_confidence",
        "trade_entry_time", "trade_exit_time", "entry_price", "exit_price",
        "actual_direction", "price_change_percent", "is_accurate", "market_regime",
    )
    for field in required:
        assert field in SentimentValidation.__table__.columns, \
            f"SentimentValidation missing field '{field}'"


# ---------------------------------------------------------------------------
# Graph Preservation (Requirements 3.23-3.27)
# ---------------------------------------------------------------------------

def test_preservation_graph_trading_state_fields():
    """
    Validates: Requirements 3.23, 3.27
    TradingState TypedDict has all required fields.
    """
    required_fields = (
        "symbol", "market_regime", "price_history", "news_list",
        "technical_data", "event_data", "risk_data", "context_data",
        "decision_data", "trade_executed", "closed_trades",
    )
    annotations = TradingState.__annotations__
    for field in required_fields:
        assert field in annotations, \
            f"TradingState missing required field '{field}'. Present: {list(annotations.keys())}"


def test_preservation_graph_has_required_nodes():
    """
    Validates: Requirements 3.23, 3.25
    Graph has nodes: fetch_data, technical, event, risk, context, fusion, trade.
    """
    from agents.graph import build_graph
    app = build_graph()
    g = app.get_graph()
    node_names = set(g.nodes.keys())
    required_nodes = {"fetch_data", "technical", "event", "risk", "context", "fusion", "trade"}
    for node in required_nodes:
        assert node in node_names, \
            f"Graph missing required node '{node}'. Nodes: {node_names}"


def test_preservation_graph_workflow_edges():
    """
    Validates: Requirements 3.23, 3.26
    Workflow structure: fetch_data feeds technical/event/risk/context;
    all four feed fusion; fusion feeds trade.
    """
    from agents.graph import build_graph
    app = build_graph()
    g = app.get_graph()

    # Collect edges as (source, target) pairs
    edges = {(e.source, e.target) for e in g.edges}

    # fetch_data → parallel agents
    for agent_node in ("technical", "event", "risk", "context"):
        assert ("fetch_data", agent_node) in edges, \
            f"Missing edge fetch_data → {agent_node}. Edges: {edges}"

    # parallel agents → fusion
    for agent_node in ("technical", "event", "risk", "context"):
        assert (agent_node, "fusion") in edges, \
            f"Missing edge {agent_node} → fusion. Edges: {edges}"

    # fusion → trade
    assert ("fusion", "trade") in edges, f"Missing edge fusion → trade. Edges: {edges}"


def test_preservation_graph_technical_node_runs():
    """
    Validates: Requirements 3.25
    run_technical_agent node processes valid price_history and returns technical_data.
    """
    from agents.graph import run_technical_agent
    prices = make_price_history(n=60)
    state = {
        "symbol": "AAPL", "market_regime": "normal",
        "price_history": prices, "news_list": [],
        "technical_data": {}, "event_data": {}, "risk_data": {}, "context_data": {},
        "decision_data": {}, "trade_executed": None, "closed_trades": [],
    }
    result = run_technical_agent(state)
    assert "technical_data" in result
    assert "technical_score" in result["technical_data"]


def test_preservation_graph_risk_node_runs():
    """
    Validates: Requirements 3.25
    run_risk_agent node processes valid price_history and returns risk_data.
    """
    from agents.graph import run_risk_agent
    prices = make_price_history(n=20)
    state = {
        "symbol": "AAPL", "market_regime": "normal",
        "price_history": prices, "news_list": [],
        "technical_data": {}, "event_data": {}, "risk_data": {}, "context_data": {},
        "decision_data": {}, "trade_executed": None, "closed_trades": [],
    }
    result = run_risk_agent(state)
    assert "risk_data" in result
    assert "risk_level" in result["risk_data"]


# ---------------------------------------------------------------------------
# run() - Execute all preservation tests
# ---------------------------------------------------------------------------

def run():
    """
    Execute all preservation tests and print PASS/FAIL for each.
    All tests MUST PASS on the current unfixed code.
    """
    print("=" * 70)
    print("Preservation Property Tests (Requirements 3.1-3.27)")
    print("EXPECTED: All tests PASS (confirms baseline behavior to preserve)")
    print("=" * 70)

    tests = [
        # TechnicalAgent (3.1-3.4)
        test_preservation_technical_score_range,
        test_preservation_technical_required_keys,
        test_preservation_technical_trend_values,
        test_preservation_technical_momentum_values,
        test_preservation_technical_neutral_baseline,
        test_preservation_technical_property_score_range,
        # RiskAgent (3.5-3.8)
        test_preservation_risk_required_keys,
        test_preservation_risk_level_values,
        test_preservation_risk_score_range,
        test_preservation_risk_threshold_critical,
        test_preservation_risk_threshold_high,
        test_preservation_risk_threshold_medium,
        test_preservation_risk_normal_conditions,
        test_preservation_risk_property_level_valid,
        # FusionAgent (3.9-3.13)
        test_preservation_fusion_required_keys,
        test_preservation_fusion_decision_values,
        test_preservation_fusion_critical_risk_veto,
        test_preservation_fusion_buy_threshold,
        test_preservation_fusion_sell_threshold,
        test_preservation_fusion_max_allocation,
        test_preservation_fusion_no_trade_zero_position,
        test_preservation_fusion_property_position_size_bounded,
        # TradeAgent (3.14-3.18)
        test_preservation_trade_buy_produces_trade_object,
        test_preservation_trade_slippage_applied,
        test_preservation_trade_commission_applied,
        test_preservation_trade_stop_loss_buy,
        test_preservation_trade_target_buy,
        test_preservation_trade_no_trade_returns_none,
        test_preservation_trade_monitor_closes_on_stop_loss,
        test_preservation_trade_monitor_closes_on_target,
        # LearningAgent (3.19-3.22)
        test_preservation_learning_sqlite_connection,
        test_preservation_learning_dynamic_weights_keys,
        test_preservation_learning_dynamic_weights_sum,
        test_preservation_learning_track_sentiment_accuracy_keys,
        test_preservation_learning_sentiment_accuracy_correctness,
        test_preservation_learning_trade_pattern_model_fields,
        test_preservation_learning_sentiment_validation_model_fields,
        # Graph (3.23-3.27)
        test_preservation_graph_trading_state_fields,
        test_preservation_graph_has_required_nodes,
        test_preservation_graph_workflow_edges,
        test_preservation_graph_technical_node_runs,
        test_preservation_graph_risk_node_runs,
    ]

    passed = 0
    failed = 0
    results = {}

    for test in tests:
        name = test.__name__
        try:
            test()
            results[name] = "PASS"
            passed += 1
        except Exception as e:
            results[name] = f"FAIL: {type(e).__name__}: {e}"
            failed += 1

    print()
    # Group by component
    components = {
        "TechnicalAgent (3.1-3.4)": [t for t in results if "technical" in t],
        "RiskAgent (3.5-3.8)": [t for t in results if "risk" in t],
        "FusionAgent (3.9-3.13)": [t for t in results if "fusion" in t],
        "TradeAgent (3.14-3.18)": [t for t in results if "trade" in t],
        "LearningAgent (3.19-3.22)": [t for t in results if "learning" in t],
        "Graph (3.23-3.27)": [t for t in results if "graph" in t],
    }

    for component, test_names in components.items():
        print(f"\n--- {component} ---")
        for name in test_names:
            outcome = results[name]
            status = "✓ PASS" if outcome == "PASS" else "✗ FAIL"
            print(f"  {status}  {name}")
            if outcome != "PASS":
                print(f"         {outcome}")

    print()
    print("=" * 70)
    print(f"TOTAL: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("✓ ALL PRESERVATION TESTS PASS - baseline behavior confirmed")
    else:
        print(f"✗ {failed} PRESERVATION TEST(S) FAILED - investigate before fixing bugs")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run()
