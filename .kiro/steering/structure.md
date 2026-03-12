# Project Structure

## Directory Organization

```
alphamind-ai/
├── agents/           # AI agent implementations
├── analytics/        # Performance evaluation and metrics
├── backend/          # FastAPI application
├── data/             # Data services and schemas
├── frontend/         # React UI application
├── models/           # Data models (Trade, etc.)
├── logs/             # Runtime logs
└── test_*.py         # Test files for each module
```

## Core Modules

### `/agents`
Agent implementations following the agentic architecture pattern:
- `technical_agent.py` - Technical indicator analysis (EMA, RSI, volume)
- `event_agent.py` - News analysis with LLM triage and extraction
- `risk_agent.py` - Risk assessment and veto logic
- `fusion_agent.py` - Signal combination with regime-dependent weights
- `trade_agent.py` - Paper trading execution
- `learning_agent.py` - Continuous improvement and pattern learning
- `graph.py` - LangGraph orchestration (main workflow)

### `/data`
Data fetching and normalization:
- `price_service.py` - Market data via yfinance
- `news_service.py` - News data fetching
- `schema.py` - Pydantic models (PriceData, NewsData)

### `/models`
Business domain models:
- `trade.py` - Trade lifecycle model with slippage and commission

### `/analytics`
Performance measurement:
- `evaluation.py` - Win rate, profit factor, drawdown calculations

### `/backend`
API layer:
- `app.py` - FastAPI application with CORS configuration

### `/frontend`
React application with standard Vite structure:
- `src/` - React components and application code
- `public/` - Static assets

## Architectural Patterns

### Agent Pattern
Each agent is a stateless class with static methods that:
- Accept structured input (Pydantic models or primitives)
- Return TOON format strings (for internal agent communication)
- Are independently testable

### State Management
LangGraph `TradingState` (TypedDict) flows through the pipeline:
```python
TradingState = {
    "symbol": str,
    "market_regime": str,
    "price_history": List[PriceData],
    "news_list": List[NewsData],
    "technical_toon": str,
    "event_toon": str,
    "risk_toon": str,
    "decision_data": Dict,
    "trade_executed": Trade | None
}
```

### Workflow Graph
```
START → fetch_data → [technical, event, risk] → fusion → trade → END
```

Agents run in parallel after data fetch, converge at fusion node.

## Testing Convention

Test files follow `test_<module>.py` naming:
- Each test file has a `run()` function
- Tests validate individual agent outputs
- `run_all.py` executes the full pipeline

## Import Conventions

- Absolute imports from project root (e.g., `from agents.technical_agent import TechnicalAgent`)
- Pydantic models imported from `data.schema`
- Services imported from respective modules
