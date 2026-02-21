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
from data.schema import PriceData, NewsData

# Initialize long-lived agents
event_agent = EventAgent()
trade_agent = TradeAgent()

class TradingState(TypedDict):
    symbol: str
    market_regime: str
    
    price_history: List[PriceData]
    news_list: List[NewsData]
    
    technical_data: Dict[str, Any]
    event_data: Dict[str, Any]
    risk_data: Dict[str, Any]
    
    decision_data: Dict[str, Any]
    trade_executed: Any # the Trade model object or None

def fetch_market_data(state: TradingState):
    symbol = state["symbol"]
    print(f"[{symbol}] Fetching Market Data...")
    prices = PriceService.fetch_price_history(symbol, period="50d")
    news = NewsService.fetch_news(symbol, max_items=5)
    return {"price_history": prices, "news_list": news}

def run_technical_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Technical Agent...")
    data = TechnicalAgent.analyze(state["price_history"])
    return {"technical_data": data}

def run_event_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Event Agent...")
    data = event_agent.analyze(state["news_list"])
    return {"event_data": data}

def run_risk_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Risk Agent...")
    data = RiskAgent.analyze(state["price_history"])
    return {"risk_data": data}

def run_fusion_agent(state: TradingState):
    print(f"[{state['symbol']}] Running Fusion Engine...")
    decision = FusionAgent.synthesize(
        state["technical_data"], 
        state["event_data"], 
        state["risk_data"], 
        state.get("market_regime", "normal")
    )
    return {"decision_data": decision}

def execute_trade(state: TradingState):
    print(f"[{state['symbol']}] Executing Trade Logic...")
    decision = state["decision_data"]
    if decision["decision"] == "NO_TRADE":
        print(f"[{state['symbol']}] Result: NO TRADE")
        return {"trade_executed": None}
        
    current_price = state["price_history"][-1].close
    trade = trade_agent.execute_trade(decision, current_price, state["symbol"])
    print(f"[{state['symbol']}] Result: {trade.action} {trade.position_size*100}% at {trade.fill_price:.2f}")
    return {"trade_executed": trade}

def build_graph():
    builder = StateGraph(TradingState)

    builder.add_node("fetch_data", fetch_market_data)
    builder.add_node("technical", run_technical_agent)
    builder.add_node("event", run_event_agent)
    builder.add_node("risk", run_risk_agent)
    builder.add_node("fusion", run_fusion_agent)
    builder.add_node("trade", execute_trade)

    # Workflow edges
    builder.add_edge(START, "fetch_data")
    
    # After fetching data, run agents in parallel/sequence
    builder.add_edge("fetch_data", "technical")
    builder.add_edge("fetch_data", "event")
    builder.add_edge("fetch_data", "risk")
    
    # Fusion waits for all three (LangGraph automatically joins them if they all point to "fusion")
    builder.add_edge("technical", "fusion")
    builder.add_edge("event", "fusion")
    builder.add_edge("risk", "fusion")
    
    # Trade execution comes after fusion
    builder.add_edge("fusion", "trade")
    builder.add_edge("trade", END)

    # Compile the graph
    app = builder.compile()
    return app

# Expose compiled app
alphamind_graph = build_graph()
