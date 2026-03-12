"""
Backtest Simulator for AlphaMind AI

Core simulation engine that orchestrates time-series execution of the trading pipeline
on historical data while maintaining temporal isolation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from backtesting.models import StrategyConfig, SlippageModel, BacktestResult, PerformanceMetrics, DecisionLog
from backtesting.historical_data import HistoricalDataProvider
from backtesting.time_window import TimeWindowManager
from backtesting.storage import BacktestStorage
from agents.trade_agent import TradeAgent
from agents.graph import alphamind_graph, TradingState
from models.trade import Trade
from data.schema import PriceData, NewsData


class BacktestSimulator:
    """Core backtesting simulation engine."""
    
    def __init__(
        self,
        strategy_config: StrategyConfig,
        slippage_model: Optional[SlippageModel] = None,
        initial_capital: float = 100000.0
    ):
        """
        Initialize simulator with strategy configuration.
        
        Args:
            strategy_config: Strategy parameters for backtesting
            slippage_model: Model for calculating slippage (optional)
            initial_capital: Starting capital for simulation
        """
        self.strategy_config = strategy_config
        self.slippage_model = slippage_model or SlippageModel()
        self.initial_capital = initial_capital
        
        # Initialize TradeAgent for position tracking
        self.trade_agent = TradeAgent(
            slippage_bps=strategy_config.slippage_bps,
            commission_pct=strategy_config.commission_pct
        )
        
        # Equity curve tracking
        self.equity_curve: List[tuple] = []
        
        # Decision logging
        self.decision_logs: List[DecisionLog] = []
        
        # Error tracking
        self.failed_steps: List[tuple] = []
        self.total_steps = 0
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> BacktestResult:
        """
        Execute complete backtest for a single symbol.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date of backtest period
            end_date: End date of backtest period
            interval: Time interval (1d, 1h, 15m, etc.)
            
        Returns:
            BacktestResult with complete simulation results
        """
        self.logger.info(f"Starting backtest for {symbol} from {start_date} to {end_date}")
        
        # Fetch historical data
        all_prices = HistoricalDataProvider.fetch_historical_prices(
            symbol, start_date, end_date, interval
        )
        all_news = HistoricalDataProvider.fetch_historical_news(
            symbol, start_date, end_date
        )
        
        if not all_prices:
            raise ValueError(f"No historical price data available for {symbol}")
        
        # Create time window manager
        time_manager = TimeWindowManager(start_date, end_date, interval)
        time_steps = time_manager.generate_time_steps()
        self.total_steps = len(time_steps)
        
        self.logger.info(f"Generated {self.total_steps} time steps")
        
        # Execute simulation for each time step
        for i, current_time in enumerate(time_steps):
            try:
                # Get historical slice (prevents look-ahead bias)
                price_slice, news_slice = time_manager.get_historical_slice(
                    current_time, all_prices, all_news
                )
                
                if not price_slice:
                    continue
                
                # Execute time step
                self._execute_time_step(current_time, price_slice, news_slice, symbol)
                
                # Monitor open positions
                current_price = price_slice[-1].close
                self._monitor_positions(current_price, current_time)
                
                # Update equity curve
                self._update_equity_curve(current_time)
                
                # Progress reporting
                if (i + 1) % 10 == 0:
                    progress = ((i + 1) / self.total_steps) * 100
                    self.logger.info(f"Progress: {progress:.1f}% ({i + 1}/{self.total_steps})")
                
            except Exception as e:
                self.logger.error(f"Time step {current_time} failed: {e}")
                self.failed_steps.append((current_time, str(e)))
                
                # Abort if failure rate exceeds threshold
                failure_rate = len(self.failed_steps) / self.total_steps
                if failure_rate > 0.10:
                    raise RuntimeError(
                        f"Failure rate {failure_rate:.1%} exceeds 10% threshold"
                    )
                
                continue
        
        # Calculate performance metrics
        from backtesting.performance import PerformanceTracker
        tracker = PerformanceTracker()
        
        for trade in self.trade_agent.trade_history:
            tracker.record_trade(trade)
        
        for timestamp, equity in self.equity_curve:
            tracker.record_equity_point(timestamp, equity)
        
        metrics = tracker.calculate_metrics()
        
        # Calculate buy-and-hold baseline
        start_price = all_prices[0].close
        end_price = all_prices[-1].close
        buy_hold_return = ((end_price - start_price) / start_price) * 100
        
        # Create result
        result = BacktestResult(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            strategy_config=self.strategy_config,
            initial_capital=self.initial_capital,
            trades=self.trade_agent.trade_history,
            metrics=metrics,
            equity_curve=self.equity_curve,
            decision_logs=self.decision_logs if self.decision_logs else None,
            buy_hold_return_pct=buy_hold_return
        )
        
        self.logger.info(f"Backtest complete: {len(self.trade_agent.trade_history)} trades executed")
        
        return result
    
    def _execute_time_step(
        self,
        current_time: datetime,
        price_slice: List[PriceData],
        news_slice: List[NewsData],
        symbol: str
    ) -> Optional[Trade]:
        """
        Execute LangGraph pipeline for a single time step.
        
        Args:
            current_time: Current time in simulation
            price_slice: Historical price data up to current time
            news_slice: Historical news data up to current time
            symbol: Stock ticker symbol
            
        Returns:
            Trade object if executed, None otherwise
        """
        # Build TradingState with historical context
        state: TradingState = {
            "symbol": symbol,
            "market_regime": self.strategy_config.market_regime or "normal",
            "price_history": price_slice,
            "news_list": news_slice,
            "technical_toon": "",
            "event_toon": "",
            "risk_toon": "",
            "decision_data": {},
            "trade_executed": None
        }
        
        # Execute LangGraph pipeline (bypasses fetch_data node)
        # We manually run the agent nodes to use historical data
        from agents.technical_agent import TechnicalAgent
        from agents.event_agent import EventAgent
        from agents.risk_agent import RiskAgent
        from agents.fusion_agent import FusionAgent
        
        # Run agents
        technical_toon = TechnicalAgent.calculate_technical_score(price_slice)
        event_toon = EventAgent().analyze_news(news_slice) if news_slice else "sentiment: neutral\nconfidence: 0.0\nreason: No news available"
        risk_toon = RiskAgent.analyze_risk(price_slice)
        
        # Fusion
        decision_data = FusionAgent.synthesize(
            technical_toon,
            event_toon,
            risk_toon,
            state["market_regime"]
        )
        
        # Execute trade with slippage
        trade = None
        if decision_data["decision"] != "NO_TRADE":
            current_price = price_slice[-1].close
            
            # Check position limits
            if len(self.trade_agent.open_trades) >= self.strategy_config.max_open_positions:
                self.logger.debug(f"Max position limit reached at {current_time}")
            else:
                trade = self.trade_agent.execute_trade(decision_data, current_price, symbol)
        
        # Log decision
        if self.decision_logs is not None:
            self.decision_logs.append(DecisionLog(
                timestamp=current_time,
                symbol=symbol,
                technical_toon=technical_toon,
                event_toon=event_toon,
                risk_toon=risk_toon,
                fusion_decision=decision_data,
                trade_executed=trade
            ))
        
        return trade
    
    def _monitor_positions(
        self,
        current_price: float,
        current_time: datetime
    ):
        """
        Check open positions for stop loss or target exits.
        
        Args:
            current_price: Current market price
            current_time: Current time in simulation
        """
        self.trade_agent.monitor_trades(current_price)
    
    def _update_equity_curve(self, current_time: datetime):
        """
        Calculate and record current portfolio equity.
        
        Args:
            current_time: Current time in simulation
        """
        # Calculate current equity
        equity = self.initial_capital
        
        # Add closed trade P&L
        for trade in self.trade_agent.trade_history:
            if trade.status == "CLOSED":
                pnl_pct = trade.get_pnl_percentage()
                pnl_amount = self.initial_capital * trade.position_size * pnl_pct
                equity += pnl_amount
        
        # Record equity point
        self.equity_curve.append((current_time, equity))
    
    def run_multi_symbol_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> BacktestResult:
        """
        Execute backtest across multiple symbols with portfolio-level tracking.
        
        Args:
            symbols: List of stock ticker symbols
            start_date: Start date of backtest period
            end_date: End date of backtest period
            interval: Time interval (1d, 1h, 15m, etc.)
            
        Returns:
            BacktestResult with aggregated portfolio results
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("Multi-symbol backtesting not yet implemented")
