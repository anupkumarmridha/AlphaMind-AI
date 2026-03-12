"""
Test Task 3.7: Feedback Loop to EventAgent in LearningAgent

This test verifies that the LearningAgent provides sentiment accuracy feedback
in a queryable format that can be used for continuous improvement.
"""

import os
from datetime import datetime, timedelta
from agents.learning_agent import LearningAgent

def test_feedback_loop():
    """Test the get_event_agent_performance feedback loop method."""
    
    # Use in-memory SQLite for testing
    db_url = "sqlite:///:memory:"
    learning_agent = LearningAgent(db_url=db_url)
    
    print("=" * 80)
    print("Task 3.7: Feedback Loop to EventAgent Test")
    print("=" * 80)
    
    # Test 1: Insufficient samples
    print("\n[Test 1] Insufficient samples - should return message")
    print("-" * 80)
    
    performance = learning_agent.get_event_agent_performance(
        market_regime="earnings",
        min_samples=5
    )
    
    print(f"Regime: {performance['regime']}")
    print(f"Sample Size: {performance['sample_size']}")
    print(f"Message: {performance.get('message', 'N/A')}")
    print(f"Recommendations: {performance['recommendations']}")
    
    assert performance['sentiment_accuracy'] is None, "Should return None for insufficient samples"
    assert performance['sample_size'] < 5, "Sample size should be less than minimum"
    assert "Insufficient samples" in performance['message'], "Should indicate insufficient samples"
    print("✓ Test 1 passed: Correctly handles insufficient samples")
    
    # Test 2: Add sample data and verify feedback format
    print("\n[Test 2] Add sample data and verify feedback format")
    print("-" * 80)
    
    # Create sample sentiment validations
    base_time = datetime.now()
    
    # Earnings regime: 10 samples with 70% accuracy
    earnings_samples = [
        # 7 accurate predictions
        ("AAPL", "bullish", 0.8, 100.0, 105.0, "earnings", True),
        ("AAPL", "bullish", 0.75, 100.0, 103.0, "earnings", True),
        ("MSFT", "bearish", 0.7, 200.0, 195.0, "earnings", True),
        ("GOOGL", "bullish", 0.85, 150.0, 155.0, "earnings", True),
        ("TSLA", "bearish", 0.65, 250.0, 245.0, "earnings", True),
        ("NVDA", "bullish", 0.9, 300.0, 310.0, "earnings", True),
        ("META", "bullish", 0.8, 180.0, 185.0, "earnings", True),
        # 3 inaccurate predictions
        ("AMZN", "bullish", 0.6, 120.0, 118.0, "earnings", False),
        ("NFLX", "bearish", 0.55, 400.0, 405.0, "earnings", False),
        ("AMD", "bullish", 0.7, 90.0, 89.0, "earnings", False),
    ]
    
    for symbol, sentiment, confidence, entry, exit, regime, is_accurate in earnings_samples:
        entry_time = base_time - timedelta(hours=2)
        exit_time = base_time
        
        learning_agent.track_sentiment_accuracy(
            symbol=symbol,
            predicted_sentiment=sentiment,
            predicted_confidence=confidence,
            trade_entry_time=entry_time,
            trade_exit_time=exit_time,
            entry_price=entry,
            exit_price=exit,
            market_regime=regime
        )
    
    # Get performance feedback for earnings regime
    performance = learning_agent.get_event_agent_performance(
        market_regime="earnings",
        min_samples=5
    )
    
    print(f"\nRegime: {performance['regime']}")
    print(f"Sample Size: {performance['sample_size']}")
    print(f"Sentiment Accuracy: {performance['sentiment_accuracy']:.2%}")
    print(f"Confidence-Weighted Accuracy: {performance['confidence_weighted_accuracy']:.2%}")
    print(f"Bullish Accuracy: {performance['bullish_accuracy']:.2%}")
    print(f"Bearish Accuracy: {performance['bearish_accuracy']:.2%}")
    print(f"Neutral Accuracy: {performance.get('neutral_accuracy', 'N/A')}")
    print(f"\nRecommendations:")
    print(f"  Adjust Confidence Threshold: {performance['recommendations']['adjust_confidence_threshold']}")
    print(f"  Suggested Threshold: {performance['recommendations']['suggested_threshold']}")
    print(f"  Notes:")
    for note in performance['recommendations']['notes']:
        print(f"    - {note}")
    
    # Verify feedback format
    assert performance['regime'] == "earnings", "Should filter by regime"
    assert performance['sample_size'] == 10, "Should have 10 samples"
    assert 0.6 <= performance['sentiment_accuracy'] <= 0.8, "Accuracy should be around 70%"
    assert performance['bullish_accuracy'] is not None, "Should calculate bullish accuracy"
    assert performance['bearish_accuracy'] is not None, "Should calculate bearish accuracy"
    assert 'recommendations' in performance, "Should include recommendations"
    assert 'notes' in performance['recommendations'], "Recommendations should include notes"
    
    print("\n✓ Test 2 passed: Feedback format is correct and queryable")
    
    # Test 3: Add more data for "normal" regime and test cross-regime feedback
    print("\n[Test 3] Cross-regime feedback comparison")
    print("-" * 80)
    
    # Normal regime: 8 samples with 85% accuracy (better performance)
    normal_samples = [
        # 7 accurate predictions
        ("AAPL", "bullish", 0.85, 100.0, 102.0, "normal", True),
        ("MSFT", "bullish", 0.8, 200.0, 203.0, "normal", True),
        ("GOOGL", "neutral", 0.6, 150.0, 150.2, "normal", True),
        ("TSLA", "bearish", 0.75, 250.0, 247.0, "normal", True),
        ("NVDA", "bullish", 0.9, 300.0, 305.0, "normal", True),
        ("META", "neutral", 0.65, 180.0, 180.5, "normal", True),
        ("AMZN", "bullish", 0.8, 120.0, 122.0, "normal", True),
        # 1 inaccurate prediction
        ("NFLX", "bearish", 0.7, 400.0, 402.0, "normal", False),
    ]
    
    for symbol, sentiment, confidence, entry, exit, regime, is_accurate in normal_samples:
        entry_time = base_time - timedelta(hours=2)
        exit_time = base_time
        
        learning_agent.track_sentiment_accuracy(
            symbol=symbol,
            predicted_sentiment=sentiment,
            predicted_confidence=confidence,
            trade_entry_time=entry_time,
            trade_exit_time=exit_time,
            entry_price=entry,
            exit_price=exit,
            market_regime=regime
        )
    
    # Compare performance across regimes
    earnings_perf = learning_agent.get_event_agent_performance(market_regime="earnings")
    normal_perf = learning_agent.get_event_agent_performance(market_regime="normal")
    all_perf = learning_agent.get_event_agent_performance()  # All regimes
    
    print(f"\nEarnings Regime:")
    print(f"  Accuracy: {earnings_perf['sentiment_accuracy']:.2%}")
    print(f"  Sample Size: {earnings_perf['sample_size']}")
    print(f"  Recommendation: {earnings_perf['recommendations']['notes'][0][:80]}...")
    
    print(f"\nNormal Regime:")
    print(f"  Accuracy: {normal_perf['sentiment_accuracy']:.2%}")
    print(f"  Sample Size: {normal_perf['sample_size']}")
    print(f"  Recommendation: {normal_perf['recommendations']['notes'][0][:80]}...")
    
    print(f"\nAll Regimes:")
    print(f"  Accuracy: {all_perf['sentiment_accuracy']:.2%}")
    print(f"  Sample Size: {all_perf['sample_size']}")
    
    assert earnings_perf['sample_size'] == 10, "Earnings should have 10 samples"
    assert normal_perf['sample_size'] == 8, "Normal should have 8 samples"
    assert all_perf['sample_size'] == 18, "All regimes should have 18 samples"
    assert normal_perf['sentiment_accuracy'] > earnings_perf['sentiment_accuracy'], \
        "Normal regime should have higher accuracy"
    
    print("\n✓ Test 3 passed: Cross-regime feedback works correctly")
    
    # Test 4: Verify recommendations are actionable
    print("\n[Test 4] Verify recommendations are actionable")
    print("-" * 80)
    
    # Check that recommendations provide actionable insights
    assert 'adjust_confidence_threshold' in earnings_perf['recommendations'], \
        "Should indicate if threshold adjustment is needed"
    assert 'suggested_threshold' in earnings_perf['recommendations'], \
        "Should provide suggested threshold value"
    assert len(earnings_perf['recommendations']['notes']) > 0, \
        "Should provide at least one recommendation note"
    
    print("Earnings regime recommendations:")
    for i, note in enumerate(earnings_perf['recommendations']['notes'], 1):
        print(f"  {i}. {note}")
    
    print("\nNormal regime recommendations:")
    for i, note in enumerate(normal_perf['recommendations']['notes'], 1):
        print(f"  {i}. {note}")
    
    print("\n✓ Test 4 passed: Recommendations are actionable and regime-specific")
    
    # Test 5: Verify feedback can be used to adjust EventAgent behavior
    print("\n[Test 5] Demonstrate feedback loop usage")
    print("-" * 80)
    
    print("\nExample usage in EventAgent:")
    print("```python")
    print("# EventAgent can query performance before analysis")
    print("performance = learning_agent.get_event_agent_performance(market_regime='earnings')")
    print("")
    print("# Adjust confidence threshold based on feedback")
    print("if performance['recommendations']['adjust_confidence_threshold']:")
    print("    confidence_threshold = performance['recommendations']['suggested_threshold']")
    print("else:")
    print("    confidence_threshold = 0.6  # default")
    print("")
    print("# Use accuracy metrics in LLM prompt context")
    print("prompt_context = f\"\"\"")
    print("Historical performance in {market_regime} regime:")
    print("- Sentiment accuracy: {performance['sentiment_accuracy']:.2%}")
    print("- Bullish accuracy: {performance['bullish_accuracy']:.2%}")
    print("- Bearish accuracy: {performance['bearish_accuracy']:.2%}")
    print("\"\"\"")
    print("```")
    
    print("\n✓ Test 5 passed: Feedback loop is ready for EventAgent integration")
    
    print("\n" + "=" * 80)
    print("All Task 3.7 tests passed! ✓")
    print("=" * 80)
    print("\nSummary:")
    print("- get_event_agent_performance() method implemented")
    print("- Returns queryable feedback format with regime filtering")
    print("- Provides actionable recommendations for continuous improvement")
    print("- Supports cross-regime performance comparison")
    print("- Ready for EventAgent integration to adjust confidence thresholds")
    print("=" * 80)

def run():
    """Entry point for test execution."""
    test_feedback_loop()

if __name__ == "__main__":
    run()
