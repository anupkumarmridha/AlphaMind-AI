"""
Test for Task 3.6: Sentiment Validation Mechanism in LearningAgent

This test verifies that the sentiment validation mechanism correctly:
1. Tracks sentiment predictions against actual market movements
2. Calculates accuracy metrics per symbol and market regime
3. Stores validation results in the database
"""

from agents.learning_agent import LearningAgent
from datetime import datetime, timedelta


def test_track_sentiment_accuracy():
    """Test the track_sentiment_accuracy method"""
    print("\n=== Testing Sentiment Validation Mechanism ===\n")
    
    # Initialize LearningAgent with in-memory database
    agent = LearningAgent(db_url="sqlite:///:memory:")
    
    # Test Case 1: Accurate bullish prediction
    print("Test Case 1: Accurate bullish prediction")
    entry_time = datetime.now() - timedelta(hours=2)
    exit_time = datetime.now()
    
    result1 = agent.track_sentiment_accuracy(
        symbol="AAPL",
        predicted_sentiment="bullish",
        predicted_confidence=0.85,
        trade_entry_time=entry_time,
        trade_exit_time=exit_time,
        entry_price=150.0,
        exit_price=152.0,  # 1.33% increase
        market_regime="earnings"
    )
    
    print(f"  Predicted: {result1['predicted_sentiment']}")
    print(f"  Actual: {result1['actual_direction']}")
    print(f"  Price Change: {result1['price_change_percent']:.2f}%")
    print(f"  Is Accurate: {result1['is_accurate']}")
    print(f"  Confidence: {result1['confidence']}")
    assert result1['is_accurate'] == True, "Should be accurate (bullish prediction, price increased)"
    assert result1['actual_direction'] == "bullish"
    print("  ✓ Test passed\n")
    
    # Test Case 2: Inaccurate bearish prediction
    print("Test Case 2: Inaccurate bearish prediction")
    result2 = agent.track_sentiment_accuracy(
        symbol="AAPL",
        predicted_sentiment="bearish",
        predicted_confidence=0.65,
        trade_entry_time=entry_time,
        trade_exit_time=exit_time,
        entry_price=150.0,
        exit_price=151.0,  # 0.67% increase (actually bullish)
        market_regime="earnings"
    )
    
    print(f"  Predicted: {result2['predicted_sentiment']}")
    print(f"  Actual: {result2['actual_direction']}")
    print(f"  Price Change: {result2['price_change_percent']:.2f}%")
    print(f"  Is Accurate: {result2['is_accurate']}")
    assert result2['is_accurate'] == False, "Should be inaccurate (bearish prediction, price increased)"
    assert result2['actual_direction'] == "bullish"
    print("  ✓ Test passed\n")
    
    # Test Case 3: Neutral movement
    print("Test Case 3: Neutral movement")
    result3 = agent.track_sentiment_accuracy(
        symbol="MSFT",
        predicted_sentiment="neutral",
        predicted_confidence=0.50,
        trade_entry_time=entry_time,
        trade_exit_time=exit_time,
        entry_price=300.0,
        exit_price=300.3,  # 0.1% increase (within neutral range)
        market_regime="normal"
    )
    
    print(f"  Predicted: {result3['predicted_sentiment']}")
    print(f"  Actual: {result3['actual_direction']}")
    print(f"  Price Change: {result3['price_change_percent']:.2f}%")
    print(f"  Is Accurate: {result3['is_accurate']}")
    assert result3['is_accurate'] == True, "Should be accurate (neutral prediction, small movement)"
    assert result3['actual_direction'] == "neutral"
    print("  ✓ Test passed\n")
    
    # Test Case 4: Accurate bearish prediction
    print("Test Case 4: Accurate bearish prediction")
    result4 = agent.track_sentiment_accuracy(
        symbol="AAPL",
        predicted_sentiment="bearish",
        predicted_confidence=0.75,
        trade_entry_time=entry_time,
        trade_exit_time=exit_time,
        entry_price=150.0,
        exit_price=148.0,  # -1.33% decrease
        market_regime="earnings"
    )
    
    print(f"  Predicted: {result4['predicted_sentiment']}")
    print(f"  Actual: {result4['actual_direction']}")
    print(f"  Price Change: {result4['price_change_percent']:.2f}%")
    print(f"  Is Accurate: {result4['is_accurate']}")
    assert result4['is_accurate'] == True, "Should be accurate (bearish prediction, price decreased)"
    assert result4['actual_direction'] == "bearish"
    print("  ✓ Test passed\n")
    
    # Test Case 5: Add more samples for AAPL
    print("Test Case 5: Adding more samples for metrics calculation")
    for i in range(3):
        agent.track_sentiment_accuracy(
            symbol="AAPL",
            predicted_sentiment="bullish",
            predicted_confidence=0.80,
            trade_entry_time=entry_time,
            trade_exit_time=exit_time,
            entry_price=150.0,
            exit_price=151.5,
            market_regime="earnings"
        )
    print("  ✓ Added 3 more bullish predictions\n")
    
    return agent


def test_get_sentiment_accuracy_metrics(agent):
    """Test the get_sentiment_accuracy_metrics method"""
    print("=== Testing Sentiment Accuracy Metrics ===\n")
    
    # Test Case 1: Get metrics for AAPL
    print("Test Case 1: Metrics for AAPL")
    metrics_aapl = agent.get_sentiment_accuracy_metrics(symbol="AAPL")
    
    print(f"  Overall Accuracy: {metrics_aapl['overall_accuracy']:.2%}")
    print(f"  Confidence-Weighted Accuracy: {metrics_aapl['confidence_weighted_accuracy']:.2%}")
    print(f"  Bullish Accuracy: {metrics_aapl['bullish_accuracy']:.2%}")
    print(f"  Bearish Accuracy: {metrics_aapl['bearish_accuracy']:.2%}")
    print(f"  Sample Size: {metrics_aapl['sample_size']}")
    print(f"  Bullish Samples: {metrics_aapl['bullish_samples']}")
    print(f"  Bearish Samples: {metrics_aapl['bearish_samples']}")
    
    assert metrics_aapl['sample_size'] >= 5, "Should have at least 5 samples"
    assert metrics_aapl['overall_accuracy'] is not None, "Should calculate accuracy"
    assert 0.0 <= metrics_aapl['overall_accuracy'] <= 1.0, "Accuracy should be between 0 and 1"
    print("  ✓ Test passed\n")
    
    # Test Case 2: Get metrics by market regime
    print("Test Case 2: Metrics for earnings regime")
    metrics_earnings = agent.get_sentiment_accuracy_metrics(market_regime="earnings")
    
    print(f"  Overall Accuracy: {metrics_earnings['overall_accuracy']:.2%}")
    print(f"  Sample Size: {metrics_earnings['sample_size']}")
    print(f"  Market Regime: {metrics_earnings['market_regime']}")
    
    assert metrics_earnings['market_regime'] == "earnings"
    print("  ✓ Test passed\n")
    
    # Test Case 3: Insufficient samples
    print("Test Case 3: Insufficient samples for MSFT")
    metrics_msft = agent.get_sentiment_accuracy_metrics(symbol="MSFT", min_samples=5)
    
    print(f"  Sample Size: {metrics_msft['sample_size']}")
    print(f"  Message: {metrics_msft.get('message', 'N/A')}")
    
    assert metrics_msft['overall_accuracy'] is None, "Should return None for insufficient samples"
    assert 'message' in metrics_msft, "Should include message about insufficient samples"
    print("  ✓ Test passed\n")


def run():
    """Main test runner"""
    try:
        # Run tests
        agent = test_track_sentiment_accuracy()
        test_get_sentiment_accuracy_metrics(agent)
        
        print("=" * 50)
        print("✓ All tests passed successfully!")
        print("=" * 50)
        print("\nSummary:")
        print("- Sentiment validation mechanism correctly tracks predictions")
        print("- Actual direction calculated based on price movement")
        print("- Accuracy metrics calculated per symbol and market regime")
        print("- Database storage working correctly")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    run()
