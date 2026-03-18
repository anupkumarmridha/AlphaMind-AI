import copy
import logging
import os
import threading
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.event_agent import EventAgent
from agents.fusion_agent import FusionAgent
from agents.learning_agent import LearningAgent
from agents.risk_agent import RiskAgent
from agents.technical_agent import TechnicalAgent
from agents.trade_agent import TradeAgent
from backend.storage import fetch_recent_trades
from data.news_service import NewsService
from data.price_service import PriceService
from data.schema import NewsData, PriceData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Long-lived agent instances
# ---------------------------------------------------------------------------
event_agent = EventAgent()
trade_agent = TradeAgent()
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEARNING_DB = f"sqlite:///{os.path.join(ROOT_DIR, 'backend', 'alphamind_learning.db')}"
learning_agent = LearningAgent(db_url=os.getenv("LEARNING_DATABASE_URL", DEFAULT_LEARNING_DB))

# ---------------------------------------------------------------------------
# 8.1 Timeout helper
# ---------------------------------------------------------------------------
# Default per-node timeouts (seconds)
NODE_TIMEOUTS = {
    "technical": 30,
    "event": 60,
    "risk": 30,
    "context": 30,
    "fusion": 10,
    "trade": 15,
    "fetch_data": 30,
}


def _run_with_timeout(func, timeout_seconds: int, *args, **kwargs):
    """
    Run *func* in a daemon thread; raise TimeoutError if it doesn't finish
    within *timeout_seconds*.  Returns the function's return value on success.
    """
    result_container = [None]
    exc_container = [None]

    def _target():
        try:
            result_container[0] = func(*args, **kwargs)
        except Exception as e:
            exc_container[0] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_seconds)

    if t.is_alive():
        raise TimeoutError(
            f"Operation timed out after {timeout_seconds}s"
        )
    if exc_container[0] is not None:
        raise exc_container[0]
    return result_container[0]


# ---------------------------------------------------------------------------
# 8.2 Circuit breaker
# ---------------------------------------------------------------------------
class CircuitBreaker:
    """
    Simple per-agent circuit breaker.
    States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing recovery).
    """
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 60  # seconds before attempting HALF_OPEN

    def __init__(self, name: str):
        self.name = name
        self.state = "CLOSED"
        self.consecutive_failures = 0
        self._opened_at: float = 0.0

    def record_success(self):
        self.consecutive_failures = 0
        if self.state != "CLOSED":
            logger.info("CircuitBreaker[%s]: closed (recovered)", self.name)
        self.state = "CLOSED"

    def record_failure(self):
        self.consecutive_failures += 1
        if self.state == "HALF_OPEN":
            import time
            self.state = "OPEN"
            self._opened_at = time.time()
            logger.warning(
                "CircuitBreaker[%s]: HALF_OPEN test failed — reopening", self.name
            )
        elif self.consecutive_failures >= self.FAILURE_THRESHOLD:
            import time
            self.state = "OPEN"
            self._opened_at = time.time()
            logger.error(
                "CircuitBreaker[%s]: OPEN after %d consecutive failures",
                self.name, self.consecutive_failures,
            )

    def is_open(self) -> bool:
        if self.state == "OPEN":
            import time
            if time.time() - self._opened_at >= self.RECOVERY_TIMEOUT:
                self.state = "HALF_OPEN"
                logger.info("CircuitBreaker[%s]: transitioning to HALF_OPEN", self.name)
                return False  # allow one attempt
            return True
        return False


# One circuit breaker per agent node
agent_circuit_breakers: Dict[str, CircuitBreaker] = {
    name: CircuitBreaker(name)
    for name in ("fetch_data", "technical", "event", "risk", "context", "fusion", "trade")
}


# ---------------------------------------------------------------------------
# 8.3 State validation helper
# ---------------------------------------------------------------------------
def _validate_state(state: Dict, required_fields: List[str], node_name: str) -> bool:
    """
    Validate that all required fields are present and non-None in *state*.
    Logs an error and returns False if validation fails.
    """
    for field in required_fields:
        if field not in state or state[field] is None:
            logger.error(
                "[%s] %s: state validation failed — required field '%s' is missing or None",
                state.get("symbol", "?"), node_name, field,
            )
            return False
    return True


# ---------------------------------------------------------------------------
# 8.4 Checkpoint / rollback helpers
# ---------------------------------------------------------------------------
def _checkpoint_state(state: Dict) -> Dict:
    """Return a shallow copy of state for rollback purposes."""
    return copy.copy(state)


# ---------------------------------------------------------------------------
# 8.5 / 8.6 safe_node decorator
# ---------------------------------------------------------------------------
def safe_node(node_name: str):
    """
    Decorator that wraps a graph node function with:
    - 8.5 Entry/exit transition logging
    - 8.6 Exception handling (prevents single-node crash from killing the workflow)
    - 8.1 Timeout enforcement
    - 8.2 Circuit breaker check
    - 8.4 State checkpoint before execution
    """
    def decorator(func):
        def wrapper(state: Dict) -> Dict:
            symbol = state.get("symbol", "?")
            cb = agent_circuit_breakers.get(node_name)

            # 8.2 Circuit breaker check
            if cb and cb.is_open():
                logger.error(
                    "[%s] %s: circuit breaker OPEN — skipping node", symbol, node_name
                )
                return {"error": f"{node_name} circuit breaker open"}

            # 8.4 Checkpoint state before execution
            checkpoint = _checkpoint_state(state)

            # 8.5 Entry log
            logger.info(
                "[%s] %s: entry — price_points=%s, regime=%s",
                symbol, node_name,
                len(state.get("price_history") or []),
                state.get("market_regime", "unknown"),
            )

            timeout = NODE_TIMEOUTS.get(node_name, 30)
            try:
                result = _run_with_timeout(func, timeout, state)
                if cb:
                    cb.record_success()
                # 8.5 Exit log
                logger.info("[%s] %s: exit — result keys=%s", symbol, node_name, list((result or {}).keys()))
                return result
            except TimeoutError as e:
                logger.error("[%s] %s: TIMEOUT after %ds", symbol, node_name, timeout)
                if cb:
                    cb.record_failure()
                # 8.4 Rollback: return checkpoint-derived error state
                return {"error": f"{node_name} timed out after {timeout}s", "last_checkpoint": checkpoint}
            except Exception as e:
                logger.error(
                    "[%s] %s: EXCEPTION — %s: %s",
                    symbol, node_name, type(e).__name__, e, exc_info=True,
                )
                if cb:
                    cb.record_failure()
                return {"error": f"{node_name} failed: {type(e).__name__}: {e}", "last_checkpoint": checkpoint}

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# TradingState
# ---------------------------------------------------------------------------
class TradingState(TypedDict):
    symbol: str
    market_regime: str

    price_history: List[PriceData]
    news_list: List[NewsData]

    technical_data: Dict[str, Any]
    event_data: Dict[str, Any]
    risk_data: Dict[str, Any]
    context_data: Dict[str, Any]

    decision_data: Dict[str, Any]
    trade_executed: Any  # Trade model or None
    closed_trades: List[Any]

    # 8.4 Rollback support
    last_checkpoint: Any
    error: str


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------
@safe_node("fetch_data")
def fetch_market_data(state: TradingState):
    symbol = state["symbol"]
    logger.info("[%s] Fetching Market Data...", symbol)
    prices = PriceService.fetch_price_history(symbol, period="50d")
    news = NewsService.fetch_news(symbol, max_items=5)
    if not prices:
        logger.warning("[%s] No price data fetched.", symbol)
    return {"price_history": prices, "news_list": news}


@safe_node("technical")
def run_technical_agent(state: TradingState):
    symbol = state.get("symbol", "?")
    logger.info("[%s] Running Technical Agent...", symbol)

    # 8.3 State validation
    if not _validate_state(state, ["price_history"], "technical"):
        return {"technical_data": {"error": "invalid state: price_history missing", "technical_score": 0.0}}

    data = TechnicalAgent.analyze(state["price_history"])
    return {"technical_data": data}


@safe_node("event")
def run_event_agent(state: TradingState):
    symbol = state.get("symbol", "?")
    logger.info("[%s] Running Event Agent...", symbol)
    data = event_agent.analyze_news(state["news_list"])
    return {"event_data": data}


@safe_node("risk")
def run_risk_agent(state: TradingState):
    symbol = state.get("symbol", "?")
    logger.info("[%s] Running Risk Agent...", symbol)

    # 8.3 State validation
    if not _validate_state(state, ["price_history"], "risk"):
        return {"risk_data": {"error": "invalid state: price_history missing", "risk_level": "CRITICAL"}}

    data = RiskAgent.analyze(state["price_history"])
    return {"risk_data": data}


@safe_node("context")
def run_context_agent(state: TradingState):
    symbol = state.get("symbol", "?")
    logger.info("[%s] Running Context Agent...", symbol)
    trades = fetch_recent_trades(200)
    closed_trades = [t for t in trades if t.status == "CLOSED"]
    if not closed_trades:
        return {
            "context_data": {
                "historical_win_rate": 0.5,
                "avg_return": 0.0,
                "confidence_adjustment": 0.0,
                "reason": "no closed trade history available",
            }
        }
    wins = sum(1 for t in closed_trades if t.get_pnl_percentage() > 0)
    win_rate = wins / len(closed_trades)
    avg_return = sum(t.get_pnl_percentage() for t in closed_trades) / len(closed_trades)
    confidence_adjustment = max(-0.15, min(0.15, (win_rate - 0.5) * 0.4))
    return {
        "context_data": {
            "historical_win_rate": round(win_rate, 4),
            "avg_return": round(avg_return, 4),
            "confidence_adjustment": round(confidence_adjustment, 4),
            "reason": f"context from {len(closed_trades)} closed trades",
        }
    }


def _build_learning_embedding(trade: Any) -> List[float]:
    vec = [0.0] * 1536
    vec[0] = 1.0 if trade.action == "BUY" else -1.0
    vec[1] = float(trade.position_size)
    vec[2] = float(trade.get_pnl_percentage())
    vec[3] = 1.0 if str(trade.exit_reason or "").lower().startswith("target") else 0.0
    return vec


@safe_node("fusion")
def run_fusion_agent(state: TradingState):
    symbol = state.get("symbol", "?")
    logger.info("[%s] Running Fusion Engine...", symbol)

    # 8.3 State validation
    if not _validate_state(state, ["technical_data", "event_data", "risk_data"], "fusion"):
        return {"decision_data": {"decision": "NO_TRADE", "confidence": 0.0, "position_size": 0.0,
                                  "reason": "invalid state: missing agent data"}}

    dynamic_weights = learning_agent.get_dynamic_weights_for_regime(
        state.get("market_regime", "normal")
    )
    decision = FusionAgent.synthesize(
        state["technical_data"],
        state["event_data"],
        state["risk_data"],
        state.get("market_regime", "normal"),
        context=state.get("context_data", {}),
        dynamic_weights=dynamic_weights,
    )
    return {"decision_data": decision}


@safe_node("trade")
def execute_trade(state: TradingState):
    symbol = state.get("symbol", "?")
    logger.info("[%s] Executing Trade Logic...", symbol)

    closed_trades: List[Any] = []
    if state.get("price_history"):
        current_price = state["price_history"][-1].close
        history_len = len(trade_agent.trade_history)
        trade_agent.monitor_trades(current_price)
        closed_trades = trade_agent.trade_history[history_len:]
        for closed in closed_trades:
            try:
                learning_agent.evaluate_and_store(
                    closed,
                    reason_toon=str(state.get("decision_data", {}).get("reason", "")),
                    embedding=_build_learning_embedding(closed),
                    market_regime=state.get("market_regime", "normal"),
                )
            except Exception as exc:
                logger.warning("[%s] Learning update warning: %s", symbol, exc)

    # 8.3 State validation
    if not _validate_state(state, ["decision_data"], "trade"):
        return {"trade_executed": None, "closed_trades": closed_trades}

    decision = state["decision_data"]
    if decision["decision"] == "NO_TRADE":
        logger.info("[%s] Result: NO TRADE", symbol)
        return {"trade_executed": None, "closed_trades": closed_trades}

    if not state.get("price_history"):
        logger.warning("[%s] Result: NO TRADE (no price data)", symbol)
        decision = dict(decision)
        decision["decision"] = "NO_TRADE"
        decision["confidence"] = 0.0
        decision["position_size"] = 0.0
        decision["reason"] = (
            f"{decision.get('reason', '')} | Trade blocked: no price data available."
        )
        return {"trade_executed": None, "decision_data": decision, "closed_trades": closed_trades}

    current_price = state["price_history"][-1].close
    trade = trade_agent.execute_trade(decision, current_price, symbol)
    if trade:
        logger.info(
            "[%s] Result: %s %.0f%% at %.2f",
            symbol, trade.action, trade.position_size * 100, trade.fill_price,
        )
    else:
        logger.info("[%s] Result: trade rejected by TradeAgent", symbol)
    return {"trade_executed": trade, "closed_trades": closed_trades}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------
def build_graph():
    builder = StateGraph(TradingState)

    builder.add_node("fetch_data", fetch_market_data)
    builder.add_node("technical", run_technical_agent)
    builder.add_node("event", run_event_agent)
    builder.add_node("risk", run_risk_agent)
    builder.add_node("context", run_context_agent)
    builder.add_node("fusion", run_fusion_agent)
    builder.add_node("trade", execute_trade)

    builder.add_edge(START, "fetch_data")
    builder.add_edge("fetch_data", "technical")
    builder.add_edge("fetch_data", "event")
    builder.add_edge("fetch_data", "risk")
    builder.add_edge("fetch_data", "context")
    builder.add_edge("technical", "fusion")
    builder.add_edge("event", "fusion")
    builder.add_edge("risk", "fusion")
    builder.add_edge("context", "fusion")
    builder.add_edge("fusion", "trade")
    builder.add_edge("trade", END)

    return builder.compile()


# Expose compiled graph
alphamind_graph = build_graph()
