from analytics.evaluation import EvaluationEngine
from agents.fusion_agent import FusionAgent
from models.trade import Trade


def _build_closed_trade(symbol: str, entry: float, exit_price: float, action: str = "BUY") -> Trade:
    trade = Trade(
        symbol=symbol,
        action=action,
        position_size=0.1,
        desired_entry=entry,
        fill_price=entry,
        commission_fee=0.001,
        stop_loss=entry * 0.98,
        target=entry * 1.04,
    )
    trade.close_trade(exit_price, "Target Hit" if exit_price >= entry else "Stop Loss Hit")
    return trade


def test_evaluation_includes_extended_metrics():
    trades = [
        _build_closed_trade("AAPL", 100.0, 106.0),
        _build_closed_trade("MSFT", 200.0, 194.0),
        _build_closed_trade("TSLA", 300.0, 318.0),
    ]
    metrics = EvaluationEngine.evaluate_performance(trades)

    for key in ("sharpe_ratio", "alpha", "avg_win", "avg_loss", "win_streak", "expected_value", "calmar_ratio"):
        assert key in metrics


def test_fusion_uses_context_signal():
    technical = {"technical_score": 0.6, "reason": "mildly bullish"}
    event = {"event_score": 0.6, "reason": "mildly bullish"}
    risk = {"risk_score": 0.1, "risk_level": "LOW", "reason": "stable"}
    low_context = {"historical_win_rate": 0.3, "confidence_adjustment": -0.1, "reason": "weak history"}
    high_context = {"historical_win_rate": 0.8, "confidence_adjustment": 0.1, "reason": "strong history"}

    low = FusionAgent.synthesize(technical, event, risk, context=low_context)
    high = FusionAgent.synthesize(technical, event, risk, context=high_context)

    assert high["confidence"] >= low["confidence"]


def test_news_service_keeps_missing_publish_time_as_none(monkeypatch):
    import sys
    import types
    import importlib

    class _FakeTicker:
        news = [{"title": "test", "summary": "summary", "link": "https://example.com", "publisher": "x"}]

        def __init__(self, _symbol):
            pass

    fake_yfinance = types.SimpleNamespace(Ticker=_FakeTicker)
    monkeypatch.setitem(sys.modules, "yfinance", fake_yfinance)
    news_service_module = importlib.import_module("data.news_service")
    importlib.reload(news_service_module)
    NewsService = news_service_module.NewsService

    items = NewsService.fetch_news("AAPL", max_items=1)

    assert len(items) == 1
    assert items[0].date is None


def test_event_agent_uses_env_model_names(monkeypatch):
    import importlib
    import sys
    import types

    created_models = []

    class _FakeChatOllama:
        def __init__(self, model, temperature, base_url):
            created_models.append((model, temperature, base_url))

    class _FakePromptTemplate:
        @classmethod
        def from_template(cls, _template):
            return cls()

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.local")
    monkeypatch.setenv("EVENT_TRIAGE_MODEL", "triage-model")
    monkeypatch.setenv("EVENT_EXTRACT_MODEL", "extract-model")
    fake_langchain_ollama = types.SimpleNamespace(ChatOllama=_FakeChatOllama)
    fake_prompts = types.SimpleNamespace(PromptTemplate=_FakePromptTemplate)
    monkeypatch.setitem(sys.modules, "langchain_ollama", fake_langchain_ollama)
    monkeypatch.setitem(sys.modules, "langchain_core", types.SimpleNamespace(prompts=fake_prompts))
    monkeypatch.setitem(sys.modules, "langchain_core.prompts", fake_prompts)
    event_agent_module = importlib.import_module("agents.event_agent")
    importlib.reload(event_agent_module)

    event_agent_module.EventAgent()

    assert created_models[0][0] == "triage-model"
    assert created_models[1][0] == "extract-model"
    assert created_models[0][2] == "http://ollama.local"
