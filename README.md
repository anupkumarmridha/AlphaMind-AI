# AlphaMind AI

A self-improving agentic trading intelligence platform that combines technical analysis, event intelligence, and risk assessment to generate explainable trading decisions.

## Features

- **Multi-Agent Architecture**: Specialized agents for technical analysis, event intelligence, risk assessment, and decision fusion
- **Paper Trading Simulation**: Realistic trade execution with slippage and commission modeling
- **Backtesting Engine**: Evaluate strategies on historical data with comprehensive performance metrics
- **Continuous Learning**: Self-improving feedback loop that learns from trade outcomes
- **Explainable AI**: Full transparency into agent reasoning and decision-making process
- **Real-Time Data Integration**: Live market data (price + news) via yfinance and news APIs

## Architecture

### Agent Pipeline

```
START → fetch_data → [technical, event, risk] → fusion → trade → END
```

Agents run in parallel after data fetch and converge at the fusion node, orchestrated by LangGraph.

### Core Components

- **Technical Agent**: EMA, RSI, volume analysis
- **Event Agent**: News analysis with LLM triage and extraction
- **Risk Agent**: Risk assessment with hard veto capability
- **Fusion Agent**: Signal combination with regime-dependent weighting
- **Trade Agent**: Paper trading execution
- **Learning Agent**: Pattern recognition and strategy optimization
- **Backtesting Engine**: Historical strategy validation and performance analysis

## Technology Stack

### Backend
- Python 3.x with FastAPI
- LangGraph for agent orchestration
- Pydantic v2 for data validation
- yfinance for market data
- PostgreSQL with pgvector for storage

### Frontend
- React 19.2 with Vite
- Tailwind CSS
- Chart.js for visualizations

## Getting Started

### Prerequisites

- Python 3.x
- Node.js and npm
- `uv` package manager
- OpenAI API key

### Backend Setup

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv pip install fastapi uvicorn pandas numpy yfinance langchain langchain-openai langgraph sqlalchemy pydantic

# Set environment variables
export OPENAI_API_KEY=your_api_key_here

# Run the server
python backend/app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173 and the backend API at http://localhost:8000.

## Usage

### Running the Trading Pipeline

```bash
# Run full trading pipeline
python run_all.py

# Test individual agents
python test_technical.py
python test_event.py
python test_risk.py
```

### Backtesting

The backtesting engine allows you to evaluate trading strategies on historical data:

- **Historical Data Retrieval**: Fetch price and news data for any time period
- **Time-Series Simulation**: Step-by-step execution preventing look-ahead bias
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio, drawdown, and more
- **Strategy Configuration**: Test different agent weights and risk parameters
- **Multi-Symbol Support**: Portfolio-level backtesting across multiple assets
- **Walk-Forward Analysis**: Validate strategy robustness across time periods
- **Regime Analysis**: Performance breakdown by market conditions
- **Report Generation**: Automated reports with equity curves and trade analysis

See `.kiro/specs/backtesting-engine/` for detailed requirements and implementation plan.

## Project Structure

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

## Key Concepts

### TOON Format
Token-Optimized Object Notation for efficient inter-agent communication:
```
field_name: value
another_field: value
reason: explanation text
```

### Trading State
State flows through the pipeline as a TypedDict:
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

### Regime-Dependent Weighting
Agent signals are weighted dynamically based on market conditions (normal, volatile, trending, earnings).

## Known Issues

### News Sentiment Accuracy (In Progress)

The EventAgent's sentiment analysis currently has limitations that affect trading decision accuracy:

- **Hardcoded Scores**: Uses keyword matching ("bullish"/"bearish") with fixed scores (0.8/0.2/0.5) instead of LLM confidence levels
- **Single Article Analysis**: Only processes the first high-impact article, ignoring subsequent important news
- **No Validation**: Lacks mechanism to track sentiment prediction accuracy against actual market movements
- **Missing Confidence Scores**: Doesn't provide uncertainty quantification to downstream fusion logic
- **Limited Error Handling**: Silent failures with neutral defaults when LLM extraction errors occur
- **No Learning Feedback**: Learning agent receives no sentiment accuracy data for continuous improvement
- **Keyword Limitations**: Cannot capture nuanced sentiment with conditional logic or mixed signals

**Fix Status**: A comprehensive bugfix specification is available in `.kiro/specs/news-sentiment-accuracy-fix/` that addresses all seven defects through confidence-weighted multi-article aggregation, sentiment validation against market movements, enhanced TOON output with confidence scores, robust retry logic, and feedback loops to the learning agent.

See `.kiro/specs/news-sentiment-accuracy-fix/` for detailed requirements, design, and implementation tasks.

## Documentation

- **PRD.md**: Product Requirements Document
- **TRD.md**: Technical Requirements Document
- **ARD.md**: Architecture Requirements Document
- **Implementation Plan.md**: Development roadmap
- **.kiro/specs/**: Feature specifications and implementation tasks
  - **backtesting-engine/**: Historical strategy validation and performance analysis
  - **news-sentiment-accuracy-fix/**: EventAgent sentiment analysis improvements

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
