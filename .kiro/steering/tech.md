---
inclusion: always
---

# Technology Stack & Development Guidelines

## Backend Stack

### Core Technologies
- **Framework**: FastAPI with uvicorn (async ASGI server)
- **Language**: Python 3.x
- **Package Manager**: `uv` (fast Python package installer)
- **Agent Orchestration**: LangGraph with StateGraph for multi-agent workflows
- **Data Processing**: pandas, numpy
- **Data Sources**: yfinance (market data), NewsAPI/scraping (news)
- **Schema Validation**: Pydantic v2 models (strict type validation)
- **Database**: PostgreSQL with pgvector extension (vector embeddings)
- **LLM Integration**: OpenAI API (primary), ollama (local models)

### Key Python Dependencies
```
fastapi, uvicorn, pandas, numpy, yfinance
langchain, langchain-openai, langgraph
sqlalchemy, pgvector, redis, pydantic
```

## Frontend Stack

- **Framework**: React 19.2 (latest features)
- **Build Tool**: Vite (fast HMR and bundling)
- **Styling**: Tailwind CSS with PostCSS
- **Charts**: Chart.js with react-chartjs-2
- **Linting**: ESLint with modern config

## Code Style & Conventions

### Python Backend
- Use type hints for all function signatures
- Pydantic models for all data validation (import from `data.schema`)
- Stateless agent classes with static methods
- TOON format for inter-agent communication (see below)
- Absolute imports from project root: `from agents.technical_agent import TechnicalAgent`
- Test files named `test_<module>.py` with a `run()` function

### React Frontend
- Functional components with hooks (no class components)
- Tailwind utility classes for styling (avoid custom CSS when possible)
- Component files in `frontend/src/` with `.jsx` extension
- Use Vite's fast refresh for development

### TOON Format (Token-Optimized Object Notation)
Internal agent outputs use compact TOON format to minimize LLM token usage:
```
field_name: value
another_field: value
reason: explanation text
```
- Use TOON for agent-to-agent communication
- Use standard JSON for external API responses to frontend

## Development Commands

### Backend Setup & Execution
```bash
# Create virtual environment (first time only)
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install <package-name>

# Run FastAPI server (development)
python backend/app.py
# OR with auto-reload
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# Run individual agent tests
python test_technical.py
python test_event.py
python test_<module>.py

# Run full trading pipeline
python run_all.py
```

### Frontend Development
```bash
cd frontend

# Install dependencies (first time or after package.json changes)
npm install

# Start development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Environment Configuration

### Required Environment Variables
- `OPENAI_API_KEY` - Required for LLM agent operations
- API keys should be stored in `.env` file (not committed to git)

### Development Settings
- CORS enabled for all origins in development mode
- FastAPI runs on port 8000 by default
- Vite dev server runs on port 5173 by default

## Agent Architecture Guidelines

### Agent Implementation Pattern
Each agent in `/agents` follows this pattern:
1. Stateless class with static methods
2. Accepts structured input (Pydantic models or primitives)
3. Returns TOON format strings for internal use
4. Independently testable with dedicated test file

### LangGraph State Flow
State is a TypedDict that flows through the pipeline:
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

### Workflow Execution
```
START → fetch_data → [technical, event, risk] → fusion → trade → END
```
- Agents run in parallel after data fetch
- Results converge at fusion node
- Orchestrated by LangGraph in `agents/graph.py`

## Testing Guidelines

- Each module has a corresponding `test_<module>.py` file
- Test files implement a `run()` function for execution
- Use `run_all.py` to execute the complete trading pipeline
- Validate agent outputs match expected TOON format
- Test with real market data when possible (yfinance)

## Common Patterns

### Adding a New Agent
1. Create `agents/new_agent.py` with static methods
2. Return TOON format strings
3. Create `test_new_agent.py` with `run()` function
4. Integrate into `agents/graph.py` workflow
5. Update `TradingState` TypedDict if needed

### Adding API Endpoints
1. Add route to `backend/app.py`
2. Use Pydantic models for request/response validation
3. Return standard JSON (not TOON) for frontend consumption
4. Enable CORS if needed for frontend access

### Frontend Component Development
1. Create component in `frontend/src/`
2. Use Tailwind classes for styling
3. Import and use in `App.jsx`
4. Test with `npm run dev` hot reload
