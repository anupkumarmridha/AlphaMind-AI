import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class Trade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    action: str # BUY / SELL
    position_size: float # percentage of equity (e.g., 0.05 for 5%)
    
    desired_entry: float
    fill_price: float # includes slippage
    commission_fee: float
    
    stop_loss: float
    target: float
    
    status: str = "OPEN" # OPEN, CLOSED
    timestamp: datetime = Field(default_factory=datetime.now)
    
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    exit_timestamp: Optional[datetime] = None
    
    def close_trade(self, price: float, reason: str):
        self.status = "CLOSED"
        self.exit_price = price
        self.exit_reason = reason
        self.exit_timestamp = datetime.now()
        
    def get_pnl_percentage(self) -> float:
        if self.status != "CLOSED" or self.exit_price is None:
            return 0.0
            
        exit_p = float(self.exit_price)
        
        # simplified PnL% relative to entry value
        if self.action == "BUY":
            raw_pnl = (exit_p - self.fill_price) / self.fill_price
        elif self.action == "SELL":
            raw_pnl = (self.fill_price - exit_p) / self.fill_price
        else:
            raw_pnl = 0.0
            
        # Deduct standardized fractional commission fee from percentage return
        # Adjusting the percent return natively
        final_pnl = raw_pnl - self.commission_fee
        return final_pnl
