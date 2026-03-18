import math
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from models.trade import Trade

logger = logging.getLogger(__name__)


class TradeAgent:
    def __init__(
        self,
        slippage_bps: float = 5.0,
        commission_pct: float = 0.001,
        max_total_exposure: float = 0.50,
        account_balance: float = 100000.0,
        rejection_rate: float = 0.0,
    ):
        """
        slippage_bps: simulated slippage in basis points (e.g. 5.0 bps = 0.05%)
        commission_pct: simulated commission + fees as a percentage of trade value (e.g. 0.001 = 0.1%)
        max_total_exposure: maximum total position exposure across all open trades (e.g. 0.50 = 50%)
        account_balance: account balance used for capital availability checks
        rejection_rate: probability of order rejection (0.0 = no rejections, 0.05 = 5%)
        """
        self.slippage_bps = slippage_bps
        self.commission_pct = commission_pct
        self.max_total_exposure = max_total_exposure
        self.account_balance = account_balance
        self.rejection_rate = rejection_rate
        self.open_trades: List[Trade] = []
        self.trade_history: List[Trade] = []

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _calculate_total_exposure(self) -> float:
        """Sum position_size of all open trades to get total exposure."""
        return sum(t.position_size for t in self.open_trades)

    def _check_capital_available(self, position_size: float, price: float) -> Tuple[bool, str]:
        """
        Check if sufficient capital is available for a new trade.
        required = position_size * account_balance
        """
        required = position_size * self.account_balance
        # Capital already committed to open trades
        committed = sum(t.position_size * self.account_balance for t in self.open_trades)
        available = self.account_balance - committed
        if required > available:
            return False, (
                f"Insufficient capital: required={required:.2f}, "
                f"available={available:.2f} (committed={committed:.2f})"
            )
        return True, "Capital available"

    def _adjust_stops_for_overnight(
        self, action: str, fill_price: float, is_overnight: bool
    ) -> float:
        """
        Compute stop_loss adjusted for overnight gap risk.
        Overnight: widen stops by 50% (3% instead of 2%).
        Intraday: standard 2% stop.
        """
        if is_overnight:
            if action == "BUY":
                return fill_price * 0.97
            else:  # SELL
                return fill_price * 1.03
        else:
            if action == "BUY":
                return fill_price * 0.98
            else:  # SELL
                return fill_price * 1.02

    def _validate_position_size(self, position_size: float) -> Tuple[bool, str]:
        """
        Validate that position_size is within acceptable bounds.
        Returns (is_valid, error_message).
        """
        if position_size is None:
            return False, "position_size is None"
        try:
            ps = float(position_size)
        except (TypeError, ValueError):
            return False, f"position_size is not numeric: {position_size}"
        if math.isnan(ps) or math.isinf(ps):
            return False, f"position_size is NaN or inf: {ps}"
        if ps <= 0:
            return False, f"position_size must be > 0, got {ps}"
        if ps > 0.10:
            return False, f"position_size {ps} exceeds max allocation of 0.10"
        return True, "valid"

    # ------------------------------------------------------------------
    # Core execution
    # ------------------------------------------------------------------

    def execute_trade(
        self,
        decision_data: Dict[str, Any],
        current_price: float,
        symbol: str,
        is_overnight: bool = False,
    ) -> Optional[Trade]:
        """
        Executes a paper trade based on Fusion Agent's decision.
        """
        decision = decision_data.get("decision", "NO_TRADE")
        if decision == "NO_TRADE":
            return None

        position_size = decision_data.get("position_size", 0.0)

        # 6.5 Validate position size
        valid, reason = self._validate_position_size(position_size)
        if not valid:
            logger.warning("Trade rejected - invalid position_size: %s", reason)
            return None

        # 6.1 Enforce position limit
        current_exposure = self._calculate_total_exposure()
        if current_exposure + position_size > self.max_total_exposure:
            logger.warning(
                "Trade rejected - position limit exceeded: current_exposure=%.2f%%, "
                "new_position=%.2f%%, max=%.2f%%",
                current_exposure * 100,
                position_size * 100,
                self.max_total_exposure * 100,
            )
            return None

        # 6.2 Check capital availability
        capital_ok, capital_reason = self._check_capital_available(position_size, current_price)
        if not capital_ok:
            logger.warning("Trade rejected - %s", capital_reason)
            return None

        # 6.6 Simulate order rejection
        if self.rejection_rate > 0 and random.random() < self.rejection_rate:
            logger.warning(
                "Order rejected by broker simulation (rejection_rate=%.2f%%)",
                self.rejection_rate * 100,
            )
            return None

        # Calculate simulated slippage
        slip_pct = (self.slippage_bps / 10000.0) * random.uniform(0.5, 1.5)

        if decision == "BUY":
            fill_price = current_price * (1 + slip_pct)
            tg = fill_price * 1.04  # default 4% target (1:2 RR)
        else:  # SELL
            fill_price = current_price * (1 - slip_pct)
            tg = fill_price * 0.96  # default 4% target (1:2 RR)

        # 6.3 Adjust stop loss for overnight gap risk
        sl = self._adjust_stops_for_overnight(decision, fill_price, is_overnight)

        # 6.4 Simulate partial fills (10% chance of partial fill at 50-100% of position_size)
        if random.random() < 0.10:
            fill_fraction = random.uniform(0.5, 1.0)
            actual_fill_size = position_size * fill_fraction
            logger.warning(
                "Partial fill for %s %s: requested=%.4f, filled=%.4f (%.1f%%)",
                decision,
                symbol,
                position_size,
                actual_fill_size,
                fill_fraction * 100,
            )
        else:
            actual_fill_size = position_size

        trade = Trade(
            symbol=symbol,
            action=decision,
            position_size=position_size,
            desired_entry=current_price,
            fill_price=fill_price,
            commission_fee=self.commission_pct,
            stop_loss=sl,
            target=tg,
            actual_fill_size=actual_fill_size,
        )

        self.open_trades.append(trade)
        return trade

    def monitor_trades(self, current_price: float):
        """
        Checks all open trades against the current price to trigger SL or target.
        """
        for t in self.open_trades[:]:
            if t.action == "BUY":
                if current_price <= t.stop_loss:
                    t.close_trade(current_price, "Stop Loss Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
                elif current_price >= t.target:
                    t.close_trade(current_price, "Target Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
            elif t.action == "SELL":
                if current_price >= t.stop_loss:
                    t.close_trade(current_price, "Stop Loss Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
                elif current_price <= t.target:
                    t.close_trade(current_price, "Target Hit")
                    self.open_trades.remove(t)
                    self.trade_history.append(t)
