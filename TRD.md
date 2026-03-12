# 📄 Technical Requirement Document (TRD)

## 🧠 System Name

**AlphaMind AI – Agentic Trading Intelligence System**

---

# 1. 🎯 Objective

Build a **modular, scalable, agent-based system** that:

* Ingests market + news data
* Performs multi-agent investigation
* Generates explainable trading decisions
* Executes paper trades
* Learns and improves over time

---

# 2. 🏗️ High-Level Architecture

```text
[ Data Sources ]
     ↓
[ Data Layer ]
     ↓
[ Investigation Layer (Agents) ]
     ↓
[ Fusion & Decision Layer ]
     ↓
[ Execution Layer (Paper Trading) ]
     ↓
[ Evaluation Layer ]
     ↓
[ Learning Layer ]
```

---

# 3. 🧩 Module Breakdown

---

## 3.1 📥 Data Layer

### Responsibilities:

* Fetch and normalize data

### Components:

* Price Data Service
* News Data Service
* Real-time Event Pub/Sub (e.g. Redis Queue / asyncio Queue)

### Flow:

#### Event-Driven Updates
Instead of polling, the system uses an event-driven approach. When Data Layer receives a new price tick or news item, it pushes the event to the LangGraph Agents automatically.

```json
[
  {
    "type": "price_update",
    "data": { ... }
  },
  {
    "type": "news_alert",
    "data": { ... }
  }
]
```

---

## 3.2 🔍 Investigation Layer (Agents)

---

### 3.2.1 Technical Agent

#### Input:

* OHLC data

#### Logic:

* EMA (20, 50)
* RSI (14)
* Volume analysis

#### Output:

```json
{
  "technical_score": float,
  "trend": "bullish/bearish",
  "momentum": "strong/weak",
  "reason": string
}
```

---

### 3.2.2 Event Agent

#### Input:

* News articles

#### Logic:

* **LLM Router (Triage)**:
  * Fast model (configurable via `EVENT_TRIAGE_MODEL`) to filter noise
  * Defaults to `OLLAMA_MODEL` if not specified
* **Deep Extraction**:
  * Heavy model (configurable via `EVENT_EXTRACT_MODEL`) for high impact news:
    * event type
    * numbers (revenue, profit)
    * sentiment with confidence scores
* **Fallback Model**:
  * Configurable via `EVENT_FALLBACK_MODEL` (defaults to `llama3.2:latest`)
  * Used when primary models fail
* QoQ / YoY comparison

#### Configuration:
Models are configured via environment variables in `.env`:
* `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)
* `OLLAMA_MODEL`: Default model for all agents (default: kimi-k2.5:cloud)
* `EVENT_TRIAGE_MODEL`: Fast model for news relevance filtering (defaults to `OLLAMA_MODEL`)
* `EVENT_EXTRACT_MODEL`: Heavy model for sentiment extraction (defaults to `OLLAMA_MODEL`)
* `EVENT_FALLBACK_MODEL`: Fallback when primary models fail (default: llama3.2:latest)

**Environment Variable Loading:**
- Automatically loads from `.env` file using `python-dotenv`
- Falls back to system environment variables if library not available
- No code changes needed to switch models

This allows optimization by using faster models for triage and more capable models for extraction, with automatic fallback for resilience.

#### Output Format:
* Use **TOON (Token-Optimized Object Notation)** for LLM outputs to save tokens and reduce latency.

```yaml
# Example TOON Output
event_score: float
confidence_score: float
impact_magnitude: float
event_type: earnings/deal/risk
impact: bullish/bearish
reason: string
```

---

### 3.2.3 Risk Agent

#### Input:

* Technical + market context

#### Logic:

* RSI extremes
* Volatility (ATR optional)
* Index trend

#### Output:

```json
{
  "risk_score": float,
  "risk_level": "low/medium/high",
  "reason": string
}
```

---

### 3.2.4 Context (Memory) Agent

#### Input:

* Current pattern

#### Logic:

* Query historical trades

#### Output:

```json
{
  "historical_win_rate": float,
  "avg_return": float,
  "confidence_adjustment": float
}
```

---

## 3.3 🔗 Fusion & Decision Layer

### Input:

* Technical + Event + Risk + Context

### Logic:

```python
# dynamic regime-dependent weights based on market conditions
if market_regime == "earnings":
    weights = {"technical": 0.3, "event": 0.6, "context": 0.1, "risk": 0.4}
else:
    weights = {"technical": 0.5, "event": 0.2, "context": 0.1, "risk": 0.3}

final_score = (
    technical_score * weights["technical"] +
    event_score * weights["event"] +
    context_score * weights["context"] -
    risk_score * weights["risk"]
)

# Hard Risk Veto
if risk_level == "CRITICAL":
    decision = "NO_TRADE"
```

### Output:

```json
{
  "decision": "BUY/SELL/NO_TRADE",
  "confidence": float,
  "position_size": float
}
```

---

## 3.4 🧾 Trade Execution Layer (Paper Trading)

### Responsibilities:

* Simulate trades

---

### Trade Schema:

```json
{
  "id": uuid,
  "symbol": string,
  "action": "BUY/SELL",
  "position_size": float,
  "entry_price": float,
  "fill_price": float,   // Includes simulated slippage
  "commission_fee": float,
  "stop_loss": float,
  "target": float,
  "timestamp": datetime,
  "status": "OPEN/CLOSED"
}
```

---

### Exit Conditions:

* Target hit
* Stop-loss hit
* Time expiry
* Indicator reversal

---

## 3.5 📊 Evaluation Layer

### Metrics:

* Win rate
* Profit factor
* Drawdown
* Avg trade return

---

### Output:

```json
{
  "result": "WIN/LOSS",
  "profit_percent": float,
  "duration": string
}
```

---

## 3.6 🔁 Learning Layer

### Responsibilities:

* Improve system over time

---

### Functions:

#### 1. Weight Adjustment

* Adjust weights dynamically

#### 2. Pattern Storage

```json
{
  "pattern": string,
  "win_rate": float,
  "avg_return": float
}
```

#### 3. Confidence Calibration

---

# 4. 🤖 Agent Orchestration (LangGraph)

---

## State Definition

```python
class TradingState(TypedDict):
    symbol: str
    price_data: dict
    news: list

    technical: dict
    event: dict
    risk: dict
    context: dict

    decision: str
    trade: dict
    result: dict
```

---

## Graph Flow

```python
data → technical → event → risk → context → fusion → trade → evaluation → learning
```

---

# 5. 🗄️ Database Design

---

## Tables

### trades

* id
* symbol
* action
* entry_price
* exit_price
* result
* timestamp

---

### patterns

* id
* pattern
* win_rate
* avg_return

---

### logs

* id
* agent
* input
* output
* timestamp

---

# 6. ⚙️ Tech Stack

* Backend: FastAPI (Python)
* AI: OpenAI / LLM / local Llama
* Orchestration: LangGraph
* DB: PostgreSQL (with `pgvector` for similarity matching)
* Frontend: React
* Charts: Chart.js / Recharts

---

# 7. 🚀 Deployment

* Backend → Docker container
* DB → PostgreSQL (cloud/local)
* Frontend → Vercel / Netlify

---

# 8. 🧪 Testing Strategy

* Unit tests for agents
* Backtesting with historical data
* Paper trading validation

---

# 9. 📈 Performance Requirements

* API response < 500ms (excluding LLM)
* LLM processing < 3s
* System handles 100+ trades/day

---

# 10. 🔒 Constraints

* No real trading initially
* Data reliability dependency
* Market unpredictability

---

# 11. ✅ Completion Criteria

System is complete when:

* Generates valid trade signals
* Executes paper trades
* Tracks performance
* Shows improvement over time

---

# 🎯 Final Note

This TRD defines a **modular, extensible, self-improving AI system**.

👉 Each module can be independently built, tested, and improved.
