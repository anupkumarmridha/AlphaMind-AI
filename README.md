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
- Ollama with required models installed (kimi-k2.5:cloud, llama3.2:latest)

### Backend Setup

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
uv pip install fastapi uvicorn pandas numpy yfinance langchain langchain-openai langgraph sqlalchemy pydantic python-dotenv

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration (Ollama URL, models, database paths)

# Verify environment configuration (recommended first step)
python test_env_config.py

# Run the server
python backend/app.py
```

### Configuration

The system uses environment variables for flexible configuration without code changes. Copy `.env.example` to `.env` and customize:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=kimi-k2.5:cloud

# Event Agent Models (optional - defaults to OLLAMA_MODEL)
EVENT_TRIAGE_MODEL=kimi-k2.5:cloud      # Fast model for news triage
EVENT_EXTRACT_MODEL=kimi-k2.5:cloud     # Heavy model for sentiment extraction
EVENT_FALLBACK_MODEL=llama3.2:latest    # Fallback when primary model fails

# Database Configuration
DATABASE_URL=sqlite:///backend/alphamind.db
LEARNING_DATABASE_URL=sqlite:///backend/alphamind_learning.db
ALPHAMIND_DB_PATH=backend/alphamind.db

# Logging
LOG_LEVEL=INFO
```

**Environment Variable Loading:**
- EventAgent automatically loads variables from `.env` using `python-dotenv`
- Falls back to system environment variables if `python-dotenv` is not installed
- No code changes needed to switch models - just edit `.env`

**EventAgent Model Configuration:**
- `EVENT_TRIAGE_MODEL`: Fast news relevance filtering (defaults to `OLLAMA_MODEL`)
- `EVENT_EXTRACT_MODEL`: Deep sentiment analysis (defaults to `OLLAMA_MODEL`)
- `EVENT_FALLBACK_MODEL`: Fallback when primary models fail (defaults to `llama3.2:latest`)

This three-tier model strategy optimizes performance by using faster models for triage and more capable models for extraction, with automatic fallback for resilience.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173 and the backend API at http://localhost:8000.

## Usage

### Verifying Configuration

**Important**: Before running the trading pipeline, verify your environment configuration:

```bash
# Test environment variables and Ollama integration
python test_env_config.py
```

This verification test will:
- ✅ Verify all environment variables are loaded correctly
- ✅ Check EventAgent model configuration (triage, extract, fallback)
- ✅ Test Ollama connectivity and model availability
- ✅ Perform a simple news analysis to confirm functionality
- ✅ Confirm TOON format output with confidence scores

**Expected Output:**
```
=== Environment Configuration Test ===
✅ All environment variables loaded correctly

=== EventAgent Initialization Test ===
✅ EventAgent initialized with correct models:
  - Triage Model: kimi-k2.5:cloud
  - Extract Model: kimi-k2.5:cloud
  - Fallback Model: llama3.2:latest
  - Base URL: http://localhost:11434

=== Simple News Analysis Test ===
✅ Successfully analyzed test news article
✅ Generated proper TOON format output with confidence scores
```

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
- **ENVIRONMENT_SETUP_SUMMARY.md**: Environment configuration guide and setup verification
- **.kiro/specs/**: Feature specifications and implementation tasks
  - **backtesting-engine/**: Historical strategy validation and performance analysis
  - **news-sentiment-accuracy-fix/**: EventAgent sentiment analysis improvements

## Configuration Management

### Environment Variables
All configuration is managed through environment variables in `.env`:
- **Flexibility**: Switch between Ollama models without code changes
- **Security**: Sensitive configuration excluded from version control
- **Portability**: Each developer can maintain their own local configuration
- **Testing**: Easy to test with different model configurations

### Model Selection Strategy
The system uses a three-tier model approach for optimal performance:
1. **Triage Model**: Fast filtering of irrelevant news (configurable via `EVENT_TRIAGE_MODEL`)
2. **Extract Model**: Deep sentiment analysis for high-impact news (configurable via `EVENT_EXTRACT_MODEL`)
3. **Fallback Model**: Automatic fallback when primary models fail (configurable via `EVENT_FALLBACK_MODEL`)

See `ENVIRONMENT_SETUP_SUMMARY.md` for detailed setup instructions and troubleshooting.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
