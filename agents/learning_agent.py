import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text
from pgvector.sqlalchemy import Vector
import json
from datetime import datetime
from typing import Optional, Dict
import yfinance as yf
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

class SentimentValidation(Base):
    __tablename__ = 'sentiment_validations'
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

    def track_sentiment_accuracy(
        self, 
        symbol: str, 
        predicted_sentiment: str, 
        predicted_confidence: float,
        trade_entry_time: datetime,
        trade_exit_time: datetime,
        entry_price: float,
        exit_price: float,
        market_regime: str = "unknown"
    ) -> Dict:
        """
        Validates sentiment predictions against actual market movements.
        
        Args:
            symbol: Trading symbol
            predicted_sentiment: "bullish", "bearish", or "neutral"
            predicted_confidence: 0.0-1.0 confidence score
            trade_entry_time: When the trade was entered
            trade_exit_time: When the trade was exited
            entry_price: Entry price of the trade
            exit_price: Exit price of the trade
            market_regime: Market regime during the trade
            
        Returns:
            Dict with validation results including accuracy and price movement
        """
        # Calculate actual price movement
        price_change_percent = ((exit_price - entry_price) / entry_price) * 100
        
        # Determine actual direction based on price movement
        if price_change_percent > 0.5:  # More than 0.5% increase
            actual_direction = "bullish"
        elif price_change_percent < -0.5:  # More than 0.5% decrease
            actual_direction = "bearish"
        else:  # Within +/- 0.5%
            actual_direction = "neutral"
        
        # Compare predicted vs actual
        is_accurate = (predicted_sentiment == actual_direction)
        
        # Store validation result
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
                timestamp=datetime.now()
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
                "confidence": predicted_confidence
            }
        finally:
            db.close()

    def get_sentiment_accuracy_metrics(
        self, 
        symbol: Optional[str] = None, 
        market_regime: Optional[str] = None,
        min_samples: int = 5
    ) -> Dict:
        """
        Calculate rolling accuracy metrics for sentiment predictions.
        
        Args:
            symbol: Optional filter by symbol
            market_regime: Optional filter by market regime
            min_samples: Minimum number of samples required for meaningful metrics
            
        Returns:
            Dict with accuracy metrics including overall accuracy, by sentiment type, and sample size
        """
        db = self.SessionLocal()
        try:
            query = db.query(SentimentValidation)
            
            if symbol:
                query = query.filter(SentimentValidation.symbol == symbol)
            if market_regime:
                query = query.filter(SentimentValidation.market_regime == market_regime)
            
            validations = query.all()
            
            if len(validations) < min_samples:
                return {
                    "overall_accuracy": None,
                    "sample_size": len(validations),
                    "min_samples_required": min_samples,
                    "message": "Insufficient samples for meaningful metrics"
                }
            
            # Calculate overall accuracy
            accurate_count = sum(1 for v in validations if v.is_accurate)
            overall_accuracy = accurate_count / len(validations)
            
            # Calculate accuracy by sentiment type
            bullish_validations = [v for v in validations if v.predicted_sentiment == "bullish"]
            bearish_validations = [v for v in validations if v.predicted_sentiment == "bearish"]
            neutral_validations = [v for v in validations if v.predicted_sentiment == "neutral"]
            
            bullish_accuracy = (
                sum(1 for v in bullish_validations if v.is_accurate) / len(bullish_validations)
                if bullish_validations else None
            )
            bearish_accuracy = (
                sum(1 for v in bearish_validations if v.is_accurate) / len(bearish_validations)
                if bearish_validations else None
            )
            neutral_accuracy = (
                sum(1 for v in neutral_validations if v.is_accurate) / len(neutral_validations)
                if neutral_validations else None
            )
            
            # Calculate confidence-weighted accuracy
            total_weighted_accuracy = sum(
                (1.0 if v.is_accurate else 0.0) * v.predicted_confidence 
                for v in validations
            )
            total_confidence = sum(v.predicted_confidence for v in validations)
            confidence_weighted_accuracy = (
                total_weighted_accuracy / total_confidence if total_confidence > 0 else None
            )
            
            return {
                "overall_accuracy": overall_accuracy,
                "confidence_weighted_accuracy": confidence_weighted_accuracy,
                "bullish_accuracy": bullish_accuracy,
                "bearish_accuracy": bearish_accuracy,
                "neutral_accuracy": neutral_accuracy,
                "sample_size": len(validations),
                "bullish_samples": len(bullish_validations),
                "bearish_samples": len(bearish_validations),
                "neutral_samples": len(neutral_validations),
                "symbol": symbol,
                "market_regime": market_regime
            }
        finally:
            db.close()


    def get_event_agent_performance(
        self,
        market_regime: Optional[str] = None,
        min_samples: int = 5
    ) -> Dict:
        """
        Provides feedback on EventAgent's historical sentiment accuracy for continuous improvement.
        This data can be used to adjust confidence thresholds or provide context to LLM in future prompts.

        Args:
            market_regime: Optional filter by market regime (e.g., "earnings", "normal", "volatile")
            min_samples: Minimum number of samples required for meaningful feedback

        Returns:
            Dict with queryable feedback format:
            {
                "regime": "earnings",
                "sentiment_accuracy": 0.72,
                "sample_size": 45,
                "bullish_accuracy": 0.78,
                "bearish_accuracy": 0.65,
                "neutral_accuracy": 0.70,
                "confidence_weighted_accuracy": 0.75,
                "recommendations": {
                    "adjust_confidence_threshold": True/False,
                    "suggested_threshold": 0.6,
                    "notes": "..."
                }
            }
        """
        db = self.SessionLocal()
        try:
            query = db.query(SentimentValidation)

            if market_regime:
                query = query.filter(SentimentValidation.market_regime == market_regime)

            validations = query.all()

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
                        "notes": f"Need at least {min_samples - len(validations)} more samples"
                    }
                }

            # Calculate overall accuracy
            accurate_count = sum(1 for v in validations if v.is_accurate)
            overall_accuracy = accurate_count / len(validations)

            # Calculate accuracy by sentiment type
            bullish_validations = [v for v in validations if v.predicted_sentiment == "bullish"]
            bearish_validations = [v for v in validations if v.predicted_sentiment == "bearish"]
            neutral_validations = [v for v in validations if v.predicted_sentiment == "neutral"]

            bullish_accuracy = (
                sum(1 for v in bullish_validations if v.is_accurate) / len(bullish_validations)
                if bullish_validations else None
            )
            bearish_accuracy = (
                sum(1 for v in bearish_validations if v.is_accurate) / len(bearish_validations)
                if bearish_validations else None
            )
            neutral_accuracy = (
                sum(1 for v in neutral_validations if v.is_accurate) / len(neutral_validations)
                if neutral_validations else None
            )

            # Calculate confidence-weighted accuracy
            total_weighted_accuracy = sum(
                (1.0 if v.is_accurate else 0.0) * v.predicted_confidence
                for v in validations
            )
            total_confidence = sum(v.predicted_confidence for v in validations)
            confidence_weighted_accuracy = (
                total_weighted_accuracy / total_confidence if total_confidence > 0 else None
            )

            # Generate recommendations based on performance
            recommendations = self._generate_performance_recommendations(
                overall_accuracy=overall_accuracy,
                confidence_weighted_accuracy=confidence_weighted_accuracy,
                bullish_accuracy=bullish_accuracy,
                bearish_accuracy=bearish_accuracy,
                neutral_accuracy=neutral_accuracy,
                sample_size=len(validations)
            )

            return {
                "regime": market_regime or "all",
                "sentiment_accuracy": overall_accuracy,
                "sample_size": len(validations),
                "bullish_accuracy": bullish_accuracy,
                "bearish_accuracy": bearish_accuracy,
                "neutral_accuracy": neutral_accuracy,
                "confidence_weighted_accuracy": confidence_weighted_accuracy,
                "bullish_samples": len(bullish_validations),
                "bearish_samples": len(bearish_validations),
                "neutral_samples": len(neutral_validations),
                "recommendations": recommendations
            }
        finally:
            db.close()

    def _generate_performance_recommendations(
        self,
        overall_accuracy: float,
        confidence_weighted_accuracy: Optional[float],
        bullish_accuracy: Optional[float],
        bearish_accuracy: Optional[float],
        neutral_accuracy: Optional[float],
        sample_size: int
    ) -> Dict:
        """
        Generate actionable recommendations based on sentiment accuracy performance.

        Returns:
            Dict with recommendations for adjusting EventAgent behavior
        """
        recommendations = {
            "adjust_confidence_threshold": False,
            "suggested_threshold": None,
            "notes": []
        }

        # Recommendation 1: Overall accuracy threshold
        if overall_accuracy < 0.6:
            recommendations["adjust_confidence_threshold"] = True
            recommendations["suggested_threshold"] = 0.7
            recommendations["notes"].append(
                f"Overall accuracy ({overall_accuracy:.2%}) is below 60%. "
                "Consider increasing confidence threshold to 0.7 to filter low-quality predictions."
            )
        elif overall_accuracy > 0.75:
            recommendations["adjust_confidence_threshold"] = True
            recommendations["suggested_threshold"] = 0.5
            recommendations["notes"].append(
                f"Overall accuracy ({overall_accuracy:.2%}) is strong. "
                "Can lower confidence threshold to 0.5 to capture more trading opportunities."
            )

        # Recommendation 2: Confidence-weighted vs raw accuracy gap
        if confidence_weighted_accuracy and abs(confidence_weighted_accuracy - overall_accuracy) > 0.1:
            if confidence_weighted_accuracy > overall_accuracy:
                recommendations["notes"].append(
                    "High-confidence predictions are more accurate. "
                    "Consider weighting high-confidence signals more heavily in fusion."
                )
            else:
                recommendations["notes"].append(
                    "High-confidence predictions are less accurate than expected. "
                    "Review LLM prompt to ensure confidence calibration is correct."
                )

        # Recommendation 3: Directional bias detection
        if bullish_accuracy and bearish_accuracy:
            accuracy_gap = abs(bullish_accuracy - bearish_accuracy)
            if accuracy_gap > 0.15:
                if bullish_accuracy > bearish_accuracy:
                    recommendations["notes"].append(
                        f"Bullish predictions ({bullish_accuracy:.2%}) significantly more accurate "
                        f"than bearish ({bearish_accuracy:.2%}). "
                        "Consider adjusting bearish sentiment detection in LLM prompt."
                    )
                else:
                    recommendations["notes"].append(
                        f"Bearish predictions ({bearish_accuracy:.2%}) significantly more accurate "
                        f"than bullish ({bullish_accuracy:.2%}). "
                        "Consider adjusting bullish sentiment detection in LLM prompt."
                    )

        # Recommendation 4: Sample size adequacy
        if sample_size < 20:
            recommendations["notes"].append(
                f"Sample size ({sample_size}) is small. "
                "Recommendations will become more reliable with more data."
            )

        # Default message if no specific recommendations
        if not recommendations["notes"]:
            recommendations["notes"].append(
                f"Performance is stable with {overall_accuracy:.2%} accuracy. "
                "Continue monitoring for changes."
            )

        return recommendations

