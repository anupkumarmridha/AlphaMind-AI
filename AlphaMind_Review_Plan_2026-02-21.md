# AlphaMind AI Review + High-Impact Implementation Plan

Date: 2026-02-21

## 1) Detailed Review (With File References)

### Backend API
- `AlphaMind-AI/backend/app.py`
  - Only exposes `GET /` and `POST /events`. There is no API to run the LangGraph pipeline, generate decisions, execute paper trades, or fetch analytics. This blocks end-to-end system behavior and frontend integration.
  - `EVENT_BUFFER` is in-memory and capped at 200, which loses audit history and makes analytics unreliable across restarts.
  - Recommendation: add endpoints such as `POST /decision` or `POST /trade/run`, `GET /trades`, `GET /analytics/summary`, and a persistence layer for events/logs.

### Data Layer
- `AlphaMind-AI/data/price_service.py`
  - Uses yfinance without retries or empty-result handling. Downstream code assumes non-empty history.
  - Recommendation: add explicit empty-history handling and optional retries/backoff.

- `AlphaMind-AI/data/news_service.py`
  - yfinance `ticker.news` is often empty or inconsistent. Missing publish time is replaced with `datetime.now()`, which can create misleading timestamps.
  - Recommendation: keep missing timestamps as `None` or a sentinel so callers can decide how to treat them.

- `AlphaMind-AI/data/schema.py`
  - Good Pydantic models, but `NormalizedMarketData` is not used in the runtime flow. Consider enforcing the normalized schema at the boundary of the graph.

### Agents
- `AlphaMind-AI/agents/technical_agent.py`
  - Returns TOON strings directly. Fusion then parses strings with `_parse_toon`, which is fragile if formatting changes.
  - Recommendation: return structured dicts internally, then render TOON at the LLM boundary if needed.

- `AlphaMind-AI/agents/event_agent.py`
  - Uses `langchain_ollama` with `model="kimi-k2.5:cloud"`. This will fail unless the local Ollama instance has that model. Tests, however, check for `OPENAI_API_KEY`, which doesn’t match the Ollama implementation.
  - Recommendation: standardize LLM provider configuration and update tests.

- `AlphaMind-AI/agents/risk_agent.py`
  - RSI + volatility logic is OK but thresholds are hardcoded. Risk veto can block trades in volatile regimes even when strategy expects volatility.
  - Recommendation: make thresholds configurable, and align with market regime logic.

- `AlphaMind-AI/agents/fusion_agent.py`
  - TOON parsing is brittle when values include colons or multiline text.
  - Context weight is reassigned to technical without explicit commentary or configuration.
  - Recommendation: accept typed dicts and only do string formatting at IO boundaries.

- `AlphaMind-AI/agents/trade_agent.py`
  - `execute_trade` returns `None` for `NO_TRADE`, but signature expects `Trade`. This mismatch can lead to runtime errors.
  - Trades are stored only in memory; no persistence or analytics pipeline.
  - Recommendation: adjust return type to `Trade | None` and add persistence.

- `AlphaMind-AI/agents/learning_agent.py`
  - Missing import for `text` in the Postgres branch (will crash).
  - pgvector `Vector` is declared even for SQLite fallback, which will likely fail.
  - Recommendation: split DB backends or guard pgvector usage to Postgres only.

- `AlphaMind-AI/agents/graph.py`
  - Graph is defined and compiled, but no API endpoint triggers it.
  - Agents are global singletons; acceptable for MVP but should move to DI for scale.

### Models and Analytics
- `AlphaMind-AI/models/trade.py`
  - PnL calculation uses commission as a fraction deducted from return. This is okay if consistent with trade sizing elsewhere.
  - No serialization helpers for API responses.

- `AlphaMind-AI/analytics/evaluation.py`
  - Good baseline metrics, but PRD mentions Sharpe/alpha. Currently missing those.

### Frontend
- `AlphaMind-AI/frontend/src/App.jsx`
  - UI is high-fidelity but fully mocked. No data is fetched from backend other than analytics events.
  - Recommendation: add a dashboard snapshot API and replace mocks with real data.

### Tests
- `AlphaMind-AI/test_*`
  - Test scripts are manual and not assertion-based. Event test checks for `OPENAI_API_KEY` but implementation uses Ollama.
  - Recommendation: convert to pytest with minimal deterministic checks and align provider configuration.

---

## 2) High-Impact Implementation Plan

### Goal
Enable a real end-to-end system run: fetch data → run agents → fuse decision → execute paper trade → persist results → render in frontend.

### Priority 1: Add Core API Endpoints
- Add `POST /decision` or `POST /trade/run` in `backend/app.py`
  - Inputs: `symbol`, optional `market_regime`
  - Outputs: decision, confidence, position size, trade (if executed), and agent reasons
- Add `GET /dashboard` in `backend/app.py`
  - Outputs: aggregated metrics, last N trades, recent logs, equity curve stub

### Priority 2: Introduce Persistence (MVP)
- Use SQLite for local dev (Postgres optional later).
- Add a minimal DB layer with tables for:
  - trades
  - events/logs
  - decisions
- Wire `TradeAgent` and `FusionAgent` output to persistence.

### Priority 3: Stabilize Learning Agent
- Fix missing import and guard pgvector usage:
  - Use pgvector only when Postgres is configured
  - Skip vector column for SQLite
- Make a stubbed `LearningAgent` call optional in pipeline until DB is ready.

### Priority 4: Normalize Agent Output Types
- Refactor agents to return dicts internally instead of TOON strings.
- Convert to TOON only when necessary (e.g., for LLM routing or logging).
- Update `FusionAgent` to accept dicts.

### Priority 5: Frontend Integration
- Replace mock data in `frontend/src/App.jsx` with real API calls:
  - `GET /dashboard` for metrics and charts
  - `POST /trade/run` to trigger a new pipeline run
- Keep the mock fallback as a dev option (toggle via env or query param).

### Priority 6: Testing Baseline
- Convert current test scripts to pytest with deterministic checks:
  - `test_fusion`: assert decision thresholds
  - `test_trade`: assert stop/target logic
  - `test_eval`: assert metrics from mock trades

---

## Assumptions / Defaults
- Default DB: SQLite for local dev, Postgres + pgvector for production.
- LLM provider: keep Ollama as default but expose env config for OpenAI if needed.
- Frontend pulls data from backend; no real-time streaming required for MVP.

---

## Next Steps (If You Want Me To Implement)
1. Add the backend endpoints and persistence scaffolding.
2. Refactor agents to structured outputs and update fusion.
3. Wire frontend to the new endpoints.
4. Add pytest coverage for the core pipeline.
