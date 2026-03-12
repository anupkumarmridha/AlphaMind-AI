from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from backtesting.simulator import BacktestSimulator
from backtesting.models import StrategyConfig, BacktestResult
from backtesting.storage import BacktestStorage
from backtesting.validation import validate_and_raise, BacktestValidationError
from backtesting.report_generator import ReportGenerator

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

# Initialize storage
backtest_storage = BacktestStorage()

# In-memory job tracking (for MVP)
backtest_jobs = {}


# Request/Response Models
class BacktestRequest(BaseModel):
    symbol: str
    start_date: str  # ISO format
    end_date: str    # ISO format
    interval: str = "1d"
    strategy_config: Optional[StrategyConfig] = None
    initial_capital: float = 100000.0


class BacktestJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class BacktestStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    result_id: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
def read_root():
    return {"status": "ok", "message": "AlphaMind AI API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



# Backtest Endpoints

@app.post("/api/backtest/run", response_model=BacktestJobResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Execute a backtest asynchronously.
    Returns job ID immediately for progress monitoring.
    """
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # Use default strategy config if not provided
        strategy_config = request.strategy_config or StrategyConfig()
        
        # Validate configuration
        validate_and_raise(request.symbol, start_date, end_date, strategy_config)
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        backtest_jobs[job_id] = {
            "status": "queued",
            "progress": 0.0,
            "result_id": None,
            "error": None
        }
        
        # Execute backtest in background
        background_tasks.add_task(
            execute_backtest_job,
            job_id,
            request.symbol,
            start_date,
            end_date,
            request.interval,
            strategy_config,
            request.initial_capital
        )
        
        return BacktestJobResponse(
            job_id=job_id,
            status="queued",
            message=f"Backtest queued for {request.symbol}"
        )
        
    except BacktestValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start backtest: {str(e)}")


def execute_backtest_job(
    job_id: str,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    interval: str,
    strategy_config: StrategyConfig,
    initial_capital: float
):
    """Background task to execute backtest."""
    try:
        # Update status to running
        backtest_jobs[job_id]["status"] = "running"
        
        # Create simulator
        simulator = BacktestSimulator(
            strategy_config=strategy_config,
            initial_capital=initial_capital
        )
        
        # Run backtest
        result = simulator.run_backtest(symbol, start_date, end_date, interval)
        
        # Save result
        result_id = backtest_storage.save_result(result)
        
        # Update job status
        backtest_jobs[job_id]["status"] = "completed"
        backtest_jobs[job_id]["progress"] = 100.0
        backtest_jobs[job_id]["result_id"] = result_id
        
    except Exception as e:
        backtest_jobs[job_id]["status"] = "failed"
        backtest_jobs[job_id]["error"] = str(e)


@app.get("/api/backtest/status/{job_id}", response_model=BacktestStatusResponse)
async def get_backtest_status(job_id: str):
    """Get status of a running or completed backtest."""
    if job_id not in backtest_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = backtest_jobs[job_id]
    
    return BacktestStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        result_id=job.get("result_id"),
        error=job.get("error")
    )


@app.get("/api/backtest/results/{result_id}")
async def get_backtest_result(result_id: str):
    """Retrieve complete backtest result by ID."""
    try:
        result = backtest_storage.load_result(result_id)
        
        # Generate summary report
        report = ReportGenerator.generate_summary_report(result)
        
        return report
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Result {result_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load result: {str(e)}")


@app.get("/api/backtest/results")
async def query_backtest_results(
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    strategy_name: Optional[str] = None
):
    """Query backtest results with optional filters."""
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Query results
        results = backtest_storage.query_results(
            symbol=symbol,
            start_date=start_dt,
            end_date=end_dt,
            strategy_name=strategy_name
        )
        
        # Return summary list
        summaries = []
        for result in results:
            summaries.append({
                "id": result.id,
                "symbol": result.symbol,
                "strategy": result.strategy_config.name,
                "start_date": result.start_date.isoformat(),
                "end_date": result.end_date.isoformat(),
                "total_return_pct": result.metrics.total_return_pct,
                "win_rate": result.metrics.win_rate,
                "sharpe_ratio": result.metrics.sharpe_ratio,
                "created_at": result.created_at.isoformat()
            })
        
        return {"results": summaries, "count": len(summaries)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query results: {str(e)}")


@app.post("/api/backtest/compare")
async def compare_backtest_results(result_ids: List[str]):
    """Compare multiple backtest results side-by-side."""
    try:
        comparison_df = backtest_storage.compare_results(result_ids)
        
        # Convert DataFrame to dict for JSON response
        comparison = comparison_df.to_dict(orient='records')
        
        return {"comparison": comparison}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare results: {str(e)}")
