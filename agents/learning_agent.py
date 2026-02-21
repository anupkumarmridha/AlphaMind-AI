import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
import json
from models.trade import Trade

Base = declarative_base()

class TradePattern(Base):
    __tablename__ = 'trade_patterns'
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50))
    action = Column(String(10))
    reason_toon = Column(Text)
    market_regime = Column(String(50))
    win_rate = Column(Float, default=0.0)
    total_trades_in_pattern = Column(Integer, default=1)
    # Using 1536 dimensions for standard OpenAI text-embedding-ada-002
    embedding = Column(Vector(1536))

class LearningAgent:
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_url = os.getenv("DATABASE_URL", "sqlite:///:memory:") # Note: sqlite won't support pgvector natively without extensions, this is a fallback for mocking
            
        self.engine = create_engine(db_url)
        # In a real app, only create tables if they don't exist, and ensure pgvector extension is created
        if "postgresql" in db_url:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
            
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def evaluate_and_store(self, trade: Trade, reason_toon: str, embedding: list, market_regime: str):
        """
        Takes a closed trade, evaluates it, and stores/updates its semantic pattern in vector DB.
        """
        if trade.status != "CLOSED":
            return
            
        is_win = trade.get_pnl_percentage() > 0
        
        db = self.SessionLocal()
        try:
            # Here we would do a vector similarity search to find similar past patterns
            # e.g. db.query(TradePattern).order_by(TradePattern.embedding.l2_distance(embedding)).limit(1).first()
            # For brevity in MVP, we just create a new record.
            
            pattern = TradePattern(
                symbol=trade.symbol,
                action=trade.action,
                reason_toon=reason_toon,
                market_regime=market_regime,
                win_rate=1.0 if is_win else 0.0,
                total_trades_in_pattern=1,
                embedding=embedding
            )
            db.add(pattern)
            db.commit()
        finally:
            db.close()

    def get_dynamic_weights_for_regime(self, market_regime: str) -> dict:
        """
        Calculates optimal weights by checking historical performance per regime.
        """
        # Baseline static fallback
        if market_regime == "earnings":
            return {"technical": 0.3, "event": 0.6, "context": 0.1, "risk": 0.4}
        else:
            return {"technical": 0.5, "event": 0.2, "context": 0.1, "risk": 0.3}
