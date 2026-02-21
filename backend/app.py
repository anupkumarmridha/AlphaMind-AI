from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.graph import alphamind_graph
from analytics.evaluation import EvaluationEngine
from backend.storage import (
    fetch_recent_decisions,
    fetch_recent_events,
    fetch_recent_trades,
    insert_decision,
    insert_event,
    insert_trade,
)
from models.trade import Trade

app = FastAPI(
    title="AlphaMind AI",
    description="Agentic Trading Intelligence Platform API",
    version="1.0.0",
)

# Setup CORS formatting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyticsEvent(BaseModel):
    name: str
    payload: Dict[str, Any] = {}
    timestamp: str | None = None

class TradeRunRequest(BaseModel):
    symbol: str
    market_regime: Optional[str] = "normal"

def _serialize_trade(trade: Trade | None) -> Dict[str, Any] | None:
    if trade is None:
        return None
    return trade.model_dump()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AlphaMind AI API is running"}

@app.post("/events")
def track_event(event: AnalyticsEvent):
    enriched = {
        "name": event.name,
        "payload": event.payload,
        "timestamp": event.timestamp or datetime.utcnow().isoformat() + "Z",
    }
    insert_event(enriched["name"], enriched["payload"], enriched["timestamp"])
    return {"status": "ok"}

@app.post("/trade/run")
def run_trade(request: TradeRunRequest):
    """
    Run the LangGraph pipeline for a symbol and return the decision + trade (if any).
    """
    state = {
        "symbol": request.symbol,
        "market_regime": request.market_regime or "normal",
    }
    try:
        result = alphamind_graph.invoke(state)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"pipeline execution failed: {exc}") from exc

    decision = result.get("decision_data", {})
    trade = result.get("trade_executed")

    if trade:
        insert_trade(trade)

    insert_decision(
        symbol=request.symbol,
        market_regime=request.market_regime or "normal",
        decision=decision.get("decision"),
        confidence=decision.get("confidence"),
        payload=decision,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    return {
        "symbol": request.symbol,
        "market_regime": request.market_regime or "normal",
        "decision": decision,
        "trade": _serialize_trade(trade),
    }

@app.get("/dashboard")
def get_dashboard():
    """
    Minimal dashboard payload for the frontend. Uses SQLite persistence for now.
    """
    trades = fetch_recent_trades(50)
    metrics = EvaluationEngine.evaluate_performance(trades)
    serialized_trades = [_serialize_trade(t) for t in trades]
    decisions = fetch_recent_decisions(50)
    events = fetch_recent_events(100)
    return {
        "metrics": metrics,
        "trades": serialized_trades,
        "decisions": decisions,
        "events": events,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
