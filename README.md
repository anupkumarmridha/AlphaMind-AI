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

### News Sentiment Accuracy (Completed)

The EventAgent's sentiment analysis had limitations that affected trading decision accuracy. These issues have been addressed through a comprehensive bugfix:

- ✅ **Confidence Scores**: Now uses LLM-generated confidence levels instead of hardcoded keyword matching
- ✅ **Multi-Article Analysis**: Processes all high-impact articles with confidence-weighted aggregation
- ✅ **Sentiment Validation**: Tracks prediction accuracy against actual market movements
- ✅ **Enhanced TOON Output**: Includes confidence_score and impact_magnitude fields
- ✅ **Robust Error Handling**: Retry logic with exponential backoff and detailed error logging
- ✅ **Learning Feedback**: Provides sentiment accuracy data to learning agent for continuous improvement

See `.kiro/specs/news-sentiment-accuracy-fix/` for detailed requirements, design, and implementation.

### Multi-Agent System Reliability

The AlphaMind AI system has identified and is actively fixing critical bugs across all agents. A comprehensive bugfix spec addresses 30 defects across 6 components — all fixed.

**Fix Status:**

- ✅ **TechnicalAgent** (Bugs 1.1-1.5) — Fixed
  - RSI division by zero handled with safe division and epsilon guard
  - Flat price history (gain=0, loss=0) now returns clean neutral state instead of propagating NaN
  - Input validation rejects all-zero, NaN, and inf price data
  - Zero volume handled gracefully with neutral contribution
  - Post-calculation bounds checking on all indicators

- ✅ **RiskAgent** (Bugs 1.6-1.10) — Fixed
  - Detailed error messages include actual vs. required data point counts
  - Extreme condition detection (volatility spikes, price gaps, volume spikes)
  - Regime-specific risk thresholds (normal / earnings / volatile)
  - Gap risk analysis incorporated into risk score
  - NaN detection logged with full context before early return

- ✅ **FusionAgent** (Bugs 1.11-1.15) — Fixed
  - Parse errors logged with field name and problematic value
  - Weight validation and normalization after confidence adjustments
  - Context weight redistribution logic documented inline
  - Comprehensive TOON field validation with defaults for missing fields
  - `final_signal` clamped to [-1, 1] before decision logic

- ✅ **TradeAgent** (Bugs 1.16-1.20) — Fixed
  - Position limit enforcement across all open trades (max 50% total exposure)
  - Capital availability checked before every trade execution
  - Overnight stop loss widened to 3% to account for gap risk
  - Partial fill simulation and order rejection handling with logging
  - Position size validated (bounds, NaN/inf, max allocation) before execution

- ✅ **LearningAgent** (Bugs 1.21-1.25) — Fixed
  - SQLite detected at init; pgvector operations disabled with fallback storage
  - Connection pooling (QueuePool, size=5) with pool_pre_ping for stale connections
  - Retry logic with exponential backoff (1s/2s/4s) for transient DB failures
  - Embedding dimension configurable via `EMBEDDING_DIMENSION` env var (default 1536)
  - Automatic cleanup of old validation records via `VALIDATION_RETENTION_DAYS`
  - Graceful degradation: DB failures return fallback weights instead of crashing

- ✅ **Graph Orchestration** (Bugs 1.26-1.30) — Fixed
  - Per-agent timeout handling (technical=30s, event=60s, risk/fusion=30s/10s)
  - Circuit breaker pattern: opens after 3 consecutive failures, recovers after 60s
  - State validation at each node transition with required-field checks
  - Checkpoint/rollback mechanism restores last known good state on failure
  - Structured transition logging at entry/exit of every node with key state values

See `.kiro/specs/multi-agent-system-fixes/` for detailed requirements, design, and implementation tasks.

## Documentation

- **PRD.md**: Product Requirements Document
- **TRD.md**: Technical Requirements Document
- **ARD.md**: Architecture Requirements Document
- **Implementation Plan.md**: Development roadmap
- **ENVIRONMENT_SETUP_SUMMARY.md**: Environment configuration guide and setup verification
- **.kiro/specs/**: Feature specifications and implementation tasks
  - **backtesting-engine/**: Historical strategy validation and performance analysis
  - **news-sentiment-accuracy-fix/**: EventAgent sentiment analysis improvements (completed)
  - **multi-agent-system-fixes/**: System-wide reliability and error handling improvements (completed — all 6 components fixed, 30 bugs resolved)

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
