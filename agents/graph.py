import os
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, START, END

from data.price_service import PriceService
from data.news_service import NewsService
from agents.technical_agent import TechnicalAgent
from agents.event_agent import EventAgent
from agents.risk_agent import RiskAgent
from agents.fusion_agent import FusionAgent
from agents.trade_agent import TradeAgent
from agents.learning_agent import LearningAgent
from backend.storage import fetch_recent_trades
from data.schema import PriceData, NewsData

# Initialize long-lived agents
event_agent = EventAgent()
trade_agent = TradeAgent()
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEARNING_DB = f"sqlite:///{os.path.join(ROOT_DIR, 'backend', 'alphamind_learning.db')}"
learning_agent = LearningAgent(db_url=os.getenv("LEARNING_DATABASE_URL", DEFAULT_LEARNING_DB))

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
    trade_executed: Any # the Trade model object or None
    closed_trades: List[Any]

def fetch_market_data(state: TradingState):
    symbol = state["symbol"]
    print(f"[{symbol}] Fetching Market Data...")
    prices = PriceService.fetch_price_history(symbol, period="50d")
    news = NewsService.fetch_news(symbol, max_items=5)
    if not prices:
        print(f"[{symbol}] Warning: No price data fetched.")
    return {"price_history": prices, "news_list": news}

def run_technical_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Technical Agent...")
    data = TechnicalAgent.analyze(state["price_history"])
    return {"technical_data": data}

def run_event_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Event Agent...")
    data = event_agent.analyze_news(state["news_list"])
    return {"event_data": data}

def run_risk_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Risk Agent...")
    data = RiskAgent.analyze(state["price_history"])
    return {"risk_data": data}

def run_context_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Context Agent...")
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

def run_fusion_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Fusion Engine...")
    dynamic_weights = learning_agent.get_dynamic_weights_for_regime(state.get("market_regime", "normal"))
    decision = FusionAgent.synthesize(
        state["technical_data"], 
        state["event_data"], 
        state["risk_data"], 
        state.get("market_regime", "normal"),
        context=state.get("context_data", {}),
        dynamic_weights=dynamic_weights,
    )
    return {"decision_data": decision}

def execute_trade(state: TradingState):
    print(f"[{state['symbol']}] Executing Trade Logic...")
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
                print(f"[{state['symbol']}] Learning update warning: {exc}")

    decision = state["decision_data"]
    if decision["decision"] == "NO_TRADE":
        print(f"[{state['symbol']}] Result: NO TRADE")
        return {"trade_executed": None, "closed_trades": closed_trades}

    if not state.get("price_history"):
        print(f"[{state['symbol']}] Result: NO TRADE (no price data)")
        state["decision_data"]["decision"] = "NO_TRADE"
        state["decision_data"]["confidence"] = 0.0
        state["decision_data"]["position_size"] = 0.0
        state["decision_data"]["reason"] = (
            f"{state['decision_data'].get('reason', '')} | "
            "Trade blocked: no price data available for execution."
        )
        return {"trade_executed": None, "decision_data": state["decision_data"], "closed_trades": closed_trades}
        
    current_price = state["price_history"][-1].close
    trade = trade_agent.execute_trade(decision, current_price, state["symbol"])
    print(f"[{state['symbol']}] Result: {trade.action} {trade.position_size*100}% at {trade.fill_price:.2f}")
    return {"trade_executed": trade, "closed_trades": closed_trades}

def build_graph():
    builder = StateGraph(TradingState)

    builder.add_node("fetch_data", fetch_market_data)
    builder.add_node("technical", run_technical_agent)
    builder.add_node("event", run_event_agent)
    builder.add_node("risk", run_risk_agent)
    builder.add_node("context", run_context_agent)
    builder.add_node("fusion", run_fusion_agent)
    builder.add_node("trade", execute_trade)

    # Workflow edges
    builder.add_edge(START, "fetch_data")
    
    # After fetching data, run agents in parallel/sequence
    builder.add_edge("fetch_data", "technical")
    builder.add_edge("fetch_data", "event")
    builder.add_edge("fetch_data", "risk")
    builder.add_edge("fetch_data", "context")
    
    # Fusion waits for all three (LangGraph automatically joins them if they all point to "fusion")
    builder.add_edge("technical", "fusion")
    builder.add_edge("event", "fusion")
    builder.add_edge("risk", "fusion")
    builder.add_edge("context", "fusion")
    
    # Trade execution comes after fusion
    builder.add_edge("fusion", "trade")
    builder.add_edge("trade", END)

    # Compile the graph
    app = builder.compile()
    return app

# Expose compiled app
alphamind_graph = build_graph()
