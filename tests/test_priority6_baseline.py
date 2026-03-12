from agents.fusion_agent import FusionAgent
from agents.trade_agent import TradeAgent
from analytics.evaluation import EvaluationEngine
from models.trade import Trade


def test_fusion_no_trade_when_risk_is_critical():
    tech = {"technical_score": 0.9, "reason": "strong trend"}
    event = {"event_score": 0.9, "reason": "strong event"}
    risk = {"risk_score": 0.9, "risk_level": "CRITICAL", "reason": "extreme volatility"}

    decision = FusionAgent.synthesize(tech, event, risk, market_regime="normal")

    assert decision["decision"] == "NO_TRADE"
    assert decision["confidence"] == 0.0
    assert decision["position_size"] == 0.0


def test_fusion_buy_decision_for_strong_bullish_setup():
    tech = {"technical_score": 0.9, "reason": "EMA breakout"}
    event = {"event_score": 0.8, "reason": "bullish event"}
    risk = {"risk_score": 0.1, "risk_level": "LOW", "reason": "calm market"}

    decision = FusionAgent.synthesize(tech, event, risk, market_regime="normal")

    assert decision["decision"] == "BUY"
    assert decision["confidence"] > 0.0
    assert decision["position_size"] > 0.0


def test_trade_agent_executes_and_closes_buy_trade_at_target():
    agent = TradeAgent(slippage_bps=0.0, commission_pct=0.001)
    trade = agent.execute_trade(
        {"decision": "BUY", "confidence": 0.8, "position_size": 0.08},
        current_price=100.0,
        symbol="AAPL",
    )

    assert trade is not None
    assert trade.action == "BUY"
    assert trade.fill_price == 100.0

    # Move price to target (4% for BUY path with zero slippage).
    agent.monitor_trades(104.0)
    assert len(agent.open_trades) == 0
    assert len(agent.trade_history) == 1
    assert agent.trade_history[0].status == "CLOSED"
    assert agent.trade_history[0].exit_reason == "Target Hit"


def test_evaluation_engine_metrics_from_closed_trades():
    t1 = Trade(
        symbol="AAPL",
        action="BUY",
        position_size=0.1,
        desired_entry=100.0,
        fill_price=100.0,
        commission_fee=0.001,
        stop_loss=90.0,
        target=110.0,
    )
    t1.close_trade(110.0, "Target Hit")

    t2 = Trade(
        symbol="TSLA",
        action="BUY",
        position_size=0.1,
        desired_entry=200.0,
        fill_price=200.0,
        commission_fee=0.001,
        stop_loss=190.0,
        target=220.0,
    )
    t2.close_trade(190.0, "Stop Loss Hit")

    metrics = EvaluationEngine.evaluate_performance([t1, t2])

    assert metrics["total_trades"] == 2
    assert 0.0 <= metrics["win_rate"] <= 1.0
    assert "profit_factor" in metrics
    assert "max_drawdown" in metrics
