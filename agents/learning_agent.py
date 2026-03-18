import logging
import os
import time
from datetime import datetime
from typing import Callable, Dict, Optional

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, create_engine, pool
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text

from models.trade import Trade

logger = logging.getLogger(__name__)

Base = declarative_base()


class TradePattern(Base):
    __tablename__ = "trade_patterns"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50))
    action = Column(String(10))
    reason_toon = Column(Text)
    market_regime = Column(String(50))
    win_rate = Column(Float, default=0.0)
    total_trades_in_pattern = Column(Integer, default=1)
    # Embedding stored as JSON text for SQLite; Vector type used for PostgreSQL
    embedding = Column(Text)  # JSON-serialised list for SQLite; overridden for pg below


class SentimentValidation(Base):
    __tablename__ = "sentiment_validations"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50))
    predicted_sentiment = Column(String(20))  # "bullish", "bearish", "neutral"
    predicted_confidence = Column(Float)
    trade_entry_time = Column(DateTime)
    trade_exit_time = Column(DateTime)
    entry_price = Column(Float)
    exit_price = Column(Float)
    actual_direction = Column(String(20))  # "bullish", "bearish", "neutral"
    price_change_percent = Column(Float)
    is_accurate = Column(Boolean)
    market_regime = Column(String(50))
    timestamp = Column(DateTime, default=datetime.now)


class LearningAgent:
    def __init__(
        self,
        db_url: str = None,
        embedding_dim: int = None,
    ):
        if db_url is None:
            db_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")

        # 7.4 Configurable embedding dimension (env var fallback → 1536 default)
        if embedding_dim is None:
            embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
        self.embedding_dim = embedding_dim

        # 7.1 SQLite detection — disable pgvector for SQLite
        self.supports_pgvector = "postgresql" in db_url
        if not self.supports_pgvector:
            logger.warning(
                "LearningAgent: SQLite detected — pgvector operations disabled, "
                "using JSON text fallback for embeddings"
            )

        # 7.6 Graceful degradation flag
        self.degraded_mode = False

        # 7.2 Connection pooling (QueuePool for PostgreSQL; StaticPool for SQLite in-memory)
        try:
            if "sqlite" in db_url:
                # SQLite in-memory needs StaticPool to share the same connection
                from sqlalchemy.pool import StaticPool
                self.engine = create_engine(
                    db_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self.engine = create_engine(
                    db_url,
                    poolclass=pool.QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                )

            # PostgreSQL: ensure pgvector extension and use Vector column type
            if self.supports_pgvector:
                from pgvector.sqlalchemy import Vector
                # Patch TradePattern.embedding to use Vector type at runtime
                TradePattern.__table__.c["embedding"].type = Vector(self.embedding_dim)
                with self.engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()

            try:
                Base.metadata.create_all(self.engine)
            except Exception as e:
                logger.warning("LearningAgent: Could not create tables: %s", e)

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        except Exception as e:
            logger.error("LearningAgent: Database initialisation failed: %s", e)
            self.degraded_mode = True
            self.engine = None
            self.SessionLocal = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _retry_db_operation(self, operation: Callable, max_retries: int = 3):
        """
        7.3 Retry transient DB failures with exponential backoff (1s, 2s, 4s).
        Raises the last exception if all retries are exhausted.
        """
        delay = 1
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exc = e
                logger.warning(
                    "LearningAgent: DB operation failed (attempt %d/%d): %s",
                    attempt, max_retries, e,
                )
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2
        raise last_exc

    def _serialize_embedding(self, embedding: list) -> str:
        """Serialise embedding list to JSON text for SQLite storage."""
        import json
        return json.dumps(embedding)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_and_store(
        self,
        trade: Trade,
        reason_toon: str,
        embedding: list,
        market_regime: str,
    ):
        """
        Takes a closed trade, evaluates it, and stores its semantic pattern.
        7.6 Graceful degradation: logs error and returns on DB failure.
        """
        if trade.status != "CLOSED":
            return

        if self.degraded_mode or self.SessionLocal is None:
            logger.error("LearningAgent: degraded mode — skipping evaluate_and_store")
            return

        is_win = trade.get_pnl_percentage() > 0

        def _store():
            db = self.SessionLocal()
            try:
                stored_embedding = (
                    embedding if self.supports_pgvector
                    else self._serialize_embedding(embedding)
                )
                pattern = TradePattern(
                    symbol=trade.symbol,
                    action=trade.action,
                    reason_toon=reason_toon,
                    market_regime=market_regime,
                    win_rate=1.0 if is_win else 0.0,
                    total_trades_in_pattern=1,
                    embedding=stored_embedding,
                )
                db.add(pattern)
                db.commit()
            finally:
                db.close()

        try:
            self._retry_db_operation(_store)
        except Exception as e:
            logger.error("LearningAgent: evaluate_and_store failed after retries: %s", e)

    def get_dynamic_weights_for_regime(self, market_regime: str) -> dict:
        """
        Returns optimal weights for the given regime.
        7.6 Falls back to static weights on DB failure.
        """
        # Static fallback weights (also used in degraded mode)
        if market_regime == "earnings":
            fallback = {"technical": 0.3, "event": 0.6, "context": 0.1, "risk": 0.4}
        else:
            fallback = {"technical": 0.5, "event": 0.2, "context": 0.1, "risk": 0.3}

        if self.degraded_mode or self.SessionLocal is None:
            logger.warning(
                "LearningAgent: degraded mode — returning static fallback weights for regime '%s'",
                market_regime,
            )
            return fallback

        try:
            # Future: query DB for learned weights; for now return static fallback
            return fallback
        except Exception as e:
            logger.error(
                "LearningAgent: get_dynamic_weights_for_regime failed, using fallback: %s", e
            )
            return fallback

    def track_sentiment_accuracy(
        self,
        symbol: str,
        predicted_sentiment: str,
        predicted_confidence: float,
        trade_entry_time: datetime,
        trade_exit_time: datetime,
        entry_price: float,
        exit_price: float,
        market_regime: str = "unknown",
    ) -> Dict:
        """
        Validates sentiment predictions against actual market movements.
        7.6 Returns error dict on DB failure instead of raising.
        """
        # Calculate actual price movement
        price_change_percent = ((exit_price - entry_price) / entry_price) * 100

        if price_change_percent > 0.5:
            actual_direction = "bullish"
        elif price_change_percent < -0.5:
            actual_direction = "bearish"
        else:
            actual_direction = "neutral"

        is_accurate = predicted_sentiment == actual_direction

        if self.degraded_mode or self.SessionLocal is None:
            logger.error("LearningAgent: degraded mode — skipping track_sentiment_accuracy DB write")
            return {
                "validation_id": None,
                "is_accurate": is_accurate,
                "predicted_sentiment": predicted_sentiment,
                "actual_direction": actual_direction,
                "price_change_percent": price_change_percent,
                "confidence": predicted_confidence,
                "error": "database unavailable (degraded mode)",
            }

        def _store():
            db = self.SessionLocal()
            try:
                validation = SentimentValidation(
                    symbol=symbol,
                    predicted_sentiment=predicted_sentiment,
                    predicted_confidence=predicted_confidence,
                    trade_entry_time=trade_entry_time,
                    trade_exit_time=trade_exit_time,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    actual_direction=actual_direction,
                    price_change_percent=price_change_percent,
                    is_accurate=is_accurate,
                    market_regime=market_regime,
                    timestamp=datetime.now(),
                )
                db.add(validation)
                db.commit()
                db.refresh(validation)
                return {
                    "validation_id": validation.id,
                    "is_accurate": is_accurate,
                    "predicted_sentiment": predicted_sentiment,
                    "actual_direction": actual_direction,
                    "price_change_percent": price_change_percent,
                    "confidence": predicted_confidence,
                }
            finally:
                db.close()

        try:
            return self._retry_db_operation(_store)
        except Exception as e:
            logger.error("LearningAgent: track_sentiment_accuracy failed after retries: %s", e)
            return {
                "validation_id": None,
                "is_accurate": is_accurate,
                "predicted_sentiment": predicted_sentiment,
                "actual_direction": actual_direction,
                "price_change_percent": price_change_percent,
                "confidence": predicted_confidence,
                "error": str(e),
            }

    def get_sentiment_accuracy_metrics(
        self,
        symbol: Optional[str] = None,
        market_regime: Optional[str] = None,
        min_samples: int = 5,
    ) -> Dict:
        """
        Calculate rolling accuracy metrics for sentiment predictions.
        7.6 Returns error dict on DB failure.
        """
        if self.degraded_mode or self.SessionLocal is None:
            return {
                "overall_accuracy": None,
                "sample_size": 0,
                "error": "database unavailable (degraded mode)",
            }

        def _query():
            db = self.SessionLocal()
            try:
                query = db.query(SentimentValidation)
                if symbol:
                    query = query.filter(SentimentValidation.symbol == symbol)
                if market_regime:
                    query = query.filter(SentimentValidation.market_regime == market_regime)
                return query.all()
            finally:
                db.close()

        try:
            validations = self._retry_db_operation(_query)
        except Exception as e:
            logger.error("LearningAgent: get_sentiment_accuracy_metrics failed: %s", e)
            return {"overall_accuracy": None, "sample_size": 0, "error": str(e)}

        if len(validations) < min_samples:
            return {
                "overall_accuracy": None,
                "sample_size": len(validations),
                "min_samples_required": min_samples,
                "message": "Insufficient samples for meaningful metrics",
            }

        accurate_count = sum(1 for v in validations if v.is_accurate)
        overall_accuracy = accurate_count / len(validations)

        bullish_v = [v for v in validations if v.predicted_sentiment == "bullish"]
        bearish_v = [v for v in validations if v.predicted_sentiment == "bearish"]
        neutral_v = [v for v in validations if v.predicted_sentiment == "neutral"]

        def _acc(lst):
            return sum(1 for v in lst if v.is_accurate) / len(lst) if lst else None

        total_weighted = sum(
            (1.0 if v.is_accurate else 0.0) * v.predicted_confidence for v in validations
        )
        total_conf = sum(v.predicted_confidence for v in validations)
        conf_weighted_acc = total_weighted / total_conf if total_conf > 0 else None

        return {
            "overall_accuracy": overall_accuracy,
            "confidence_weighted_accuracy": conf_weighted_acc,
            "bullish_accuracy": _acc(bullish_v),
            "bearish_accuracy": _acc(bearish_v),
            "neutral_accuracy": _acc(neutral_v),
            "sample_size": len(validations),
            "bullish_samples": len(bullish_v),
            "bearish_samples": len(bearish_v),
            "neutral_samples": len(neutral_v),
            "symbol": symbol,
            "market_regime": market_regime,
        }

    def cleanup_old_records(self, retention_days: int = None) -> int:
        """
        7.5 Delete SentimentValidation records older than retention_days.
        Returns the number of records deleted.
        """
        if retention_days is None:
            retention_days = int(os.getenv("VALIDATION_RETENTION_DAYS", "90"))

        if self.degraded_mode or self.SessionLocal is None:
            logger.error("LearningAgent: degraded mode — skipping cleanup_old_records")
            return 0

        def _cleanup():
            db = self.SessionLocal()
            try:
                cutoff = datetime.now()
                from datetime import timedelta
                cutoff = cutoff - timedelta(days=retention_days)
                deleted = (
                    db.query(SentimentValidation)
                    .filter(SentimentValidation.timestamp < cutoff)
                    .delete()
                )
                db.commit()
                logger.info(
                    "LearningAgent: cleanup_old_records deleted %d records older than %d days",
                    deleted, retention_days,
                )
                return deleted
            finally:
                db.close()

        try:
            return self._retry_db_operation(_cleanup)
        except Exception as e:
            logger.error("LearningAgent: cleanup_old_records failed: %s", e)
            return 0

    def get_event_agent_performance(
        self,
        market_regime: Optional[str] = None,
        min_samples: int = 5,
    ) -> Dict:
        """
        Provides feedback on EventAgent's historical sentiment accuracy.
        7.6 Returns error dict on DB failure.
        """
        if self.degraded_mode or self.SessionLocal is None:
            return {
                "regime": market_regime or "all",
                "sentiment_accuracy": None,
                "sample_size": 0,
                "error": "database unavailable (degraded mode)",
                "recommendations": {
                    "adjust_confidence_threshold": False,
                    "suggested_threshold": None,
                    "notes": ["Database unavailable — cannot generate recommendations"],
                },
            }

        def _query():
            db = self.SessionLocal()
            try:
                query = db.query(SentimentValidation)
                if market_regime:
                    query = query.filter(SentimentValidation.market_regime == market_regime)
                return query.all()
            finally:
                db.close()

        try:
            validations = self._retry_db_operation(_query)
        except Exception as e:
            logger.error("LearningAgent: get_event_agent_performance failed: %s", e)
            return {
                "regime": market_regime or "all",
                "sentiment_accuracy": None,
                "sample_size": 0,
                "error": str(e),
                "recommendations": {
                    "adjust_confidence_threshold": False,
                    "suggested_threshold": None,
                    "notes": [f"DB error: {e}"],
                },
            }

        if len(validations) < min_samples:
            return {
                "regime": market_regime or "all",
                "sentiment_accuracy": None,
                "sample_size": len(validations),
                "min_samples_required": min_samples,
                "message": "Insufficient samples for meaningful feedback",
                "recommendations": {
                    "adjust_confidence_threshold": False,
                    "suggested_threshold": None,
                    "notes": [f"Need at least {min_samples - len(validations)} more samples"],
                },
            }

        accurate_count = sum(1 for v in validations if v.is_accurate)
        overall_accuracy = accurate_count / len(validations)

        bullish_v = [v for v in validations if v.predicted_sentiment == "bullish"]
        bearish_v = [v for v in validations if v.predicted_sentiment == "bearish"]
        neutral_v = [v for v in validations if v.predicted_sentiment == "neutral"]

        def _acc(lst):
            return sum(1 for v in lst if v.is_accurate) / len(lst) if lst else None

        total_weighted = sum(
            (1.0 if v.is_accurate else 0.0) * v.predicted_confidence for v in validations
        )
        total_conf = sum(v.predicted_confidence for v in validations)
        conf_weighted_acc = total_weighted / total_conf if total_conf > 0 else None

        recommendations = self._generate_performance_recommendations(
            overall_accuracy=overall_accuracy,
            confidence_weighted_accuracy=conf_weighted_acc,
            bullish_accuracy=_acc(bullish_v),
            bearish_accuracy=_acc(bearish_v),
            neutral_accuracy=_acc(neutral_v),
            sample_size=len(validations),
        )

        return {
            "regime": market_regime or "all",
            "sentiment_accuracy": overall_accuracy,
            "sample_size": len(validations),
            "bullish_accuracy": _acc(bullish_v),
            "bearish_accuracy": _acc(bearish_v),
            "neutral_accuracy": _acc(neutral_v),
            "confidence_weighted_accuracy": conf_weighted_acc,
            "bullish_samples": len(bullish_v),
            "bearish_samples": len(bearish_v),
            "neutral_samples": len(neutral_v),
            "recommendations": recommendations,
        }

    def _generate_performance_recommendations(
        self,
        overall_accuracy: float,
        confidence_weighted_accuracy: Optional[float],
        bullish_accuracy: Optional[float],
        bearish_accuracy: Optional[float],
        neutral_accuracy: Optional[float],
        sample_size: int,
    ) -> Dict:
        """Generate actionable recommendations based on sentiment accuracy performance."""
        recommendations = {
            "adjust_confidence_threshold": False,
            "suggested_threshold": None,
            "notes": [],
        }

        if overall_accuracy < 0.6:
            recommendations["adjust_confidence_threshold"] = True
            recommendations["suggested_threshold"] = 0.7
            recommendations["notes"].append(
                f"Overall accuracy ({overall_accuracy:.2%}) is below 60%. "
                "Consider increasing confidence threshold to 0.7."
            )
        elif overall_accuracy > 0.75:
            recommendations["adjust_confidence_threshold"] = True
            recommendations["suggested_threshold"] = 0.5
            recommendations["notes"].append(
                f"Overall accuracy ({overall_accuracy:.2%}) is strong. "
                "Can lower confidence threshold to 0.5."
            )

        if confidence_weighted_accuracy and abs(confidence_weighted_accuracy - overall_accuracy) > 0.1:
            if confidence_weighted_accuracy > overall_accuracy:
                recommendations["notes"].append(
                    "High-confidence predictions are more accurate — consider weighting them more heavily."
                )
            else:
                recommendations["notes"].append(
                    "High-confidence predictions are less accurate than expected — review LLM confidence calibration."
                )

        if bullish_accuracy and bearish_accuracy:
            gap = abs(bullish_accuracy - bearish_accuracy)
            if gap > 0.15:
                if bullish_accuracy > bearish_accuracy:
                    recommendations["notes"].append(
                        f"Bullish ({bullish_accuracy:.2%}) significantly more accurate than bearish ({bearish_accuracy:.2%})."
                    )
                else:
                    recommendations["notes"].append(
                        f"Bearish ({bearish_accuracy:.2%}) significantly more accurate than bullish ({bullish_accuracy:.2%})."
                    )

        if sample_size < 20:
            recommendations["notes"].append(
                f"Sample size ({sample_size}) is small — recommendations will improve with more data."
            )

        if not recommendations["notes"]:
            recommendations["notes"].append(
                f"Performance is stable at {overall_accuracy:.2%} accuracy. Continue monitoring."
            )

        return recommendations
