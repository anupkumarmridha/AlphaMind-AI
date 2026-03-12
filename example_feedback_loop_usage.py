"""
Example: How EventAgent can use LearningAgent feedback for continuous improvement

This demonstrates the feedback loop integration between LearningAgent and EventAgent.
"""

from agents.learning_agent import LearningAgent
from datetime import datetime, timedelta

def demonstrate_feedback_loop():
    """
    Demonstrates how EventAgent can query LearningAgent for performance feedback
    and use it to adjust its behavior dynamically.
    """
    
    print("=" * 80)
    print("Feedback Loop Integration Example")
    print("=" * 80)
    
    # Initialize LearningAgent
    learning_agent = LearningAgent(db_url="sqlite:///:memory:")
    
    # Simulate some historical sentiment validations
    print("\n[Step 1] Simulating historical sentiment validations...")
    print("-" * 80)
    
    base_time = datetime.now()
    
    # Earnings regime: Lower accuracy (65%)
    earnings_data = [
        ("AAPL", "bullish", 0.8, 100.0, 105.0, True),
        ("MSFT", "bullish", 0.75, 200.0, 198.0, False),
        ("GOOGL", "bearish", 0.7, 150.0, 145.0, True),
        ("TSLA", "bullish", 0.85, 250.0, 248.0, False),
        ("NVDA", "bearish", 0.65, 300.0, 295.0, True),
        ("META", "bullish", 0.9, 180.0, 185.0, True),
        ("AMZN", "bearish", 0.6, 120.0, 125.0, False),
        ("NFLX", "bullish", 0.7, 400.0, 405.0, True),
        ("AMD", "bearish", 0.55, 90.0, 88.0, True),
        ("INTC", "bullish", 0.8, 50.0, 52.0, True),
    ]
    
    for symbol, sentiment, confidence, entry, exit, is_accurate in earnings_data:
        learning_agent.track_sentiment_accuracy(
            symbol=symbol,
            predicted_sentiment=sentiment,
            predicted_confidence=confidence,
            trade_entry_time=base_time - timedelta(hours=2),
            trade_exit_time=base_time,
            entry_price=entry,
            exit_price=exit,
            market_regime="earnings"
        )
    
    print(f"Tracked {len(earnings_data)} sentiment validations for earnings regime")
    
    # Normal regime: Higher accuracy (80%)
    normal_data = [
        ("AAPL", "bullish", 0.85, 100.0, 102.0, True),
        ("MSFT", "bullish", 0.8, 200.0, 203.0, True),
        ("GOOGL", "neutral", 0.6, 150.0, 150.2, True),
        ("TSLA", "bearish", 0.75, 250.0, 247.0, True),
        ("NVDA", "bullish", 0.9, 300.0, 305.0, True),
        ("META", "neutral", 0.65, 180.0, 180.5, True),
        ("AMZN", "bullish", 0.8, 120.0, 122.0, True),
        ("NFLX", "bearish", 0.7, 400.0, 402.0, False),
        ("AMD", "bullish", 0.85, 90.0, 92.0, True),
        ("INTC", "bearish", 0.75, 50.0, 49.0, True),
    ]
    
    for symbol, sentiment, confidence, entry, exit, is_accurate in normal_data:
        learning_agent.track_sentiment_accuracy(
            symbol=symbol,
            predicted_sentiment=sentiment,
            predicted_confidence=confidence,
            trade_entry_time=base_time - timedelta(hours=2),
            trade_exit_time=base_time,
            entry_price=entry,
            exit_price=exit,
            market_regime="normal"
        )
    
    print(f"Tracked {len(normal_data)} sentiment validations for normal regime")
    
    # [Step 2] EventAgent queries performance before analysis
    print("\n[Step 2] EventAgent queries performance feedback...")
    print("-" * 80)
    
    current_regime = "earnings"  # Detected by regime classifier
    
    performance = learning_agent.get_event_agent_performance(
        market_regime=current_regime,
        min_samples=5
    )
    
    print(f"\nPerformance feedback for '{current_regime}' regime:")
    print(f"  Sentiment Accuracy: {performance['sentiment_accuracy']:.2%}")
    print(f"  Confidence-Weighted Accuracy: {performance['confidence_weighted_accuracy']:.2%}")
    print(f"  Sample Size: {performance['sample_size']}")
    print(f"  Bullish Accuracy: {performance['bullish_accuracy']:.2%}")
    print(f"  Bearish Accuracy: {performance['bearish_accuracy']:.2%}")
    
    # [Step 3] EventAgent adjusts behavior based on feedback
    print("\n[Step 3] EventAgent adjusts behavior based on feedback...")
    print("-" * 80)
    
    # Default confidence threshold
    default_confidence_threshold = 0.6
    
    # Adjust based on recommendations
    if performance['recommendations']['adjust_confidence_threshold']:
        confidence_threshold = performance['recommendations']['suggested_threshold']
        print(f"✓ Adjusting confidence threshold: {default_confidence_threshold} → {confidence_threshold}")
        print(f"  Reason: {performance['recommendations']['notes'][0]}")
    else:
        confidence_threshold = default_confidence_threshold
        print(f"✓ Using default confidence threshold: {confidence_threshold}")
    
    # [Step 4] EventAgent includes performance context in LLM prompt
    print("\n[Step 4] EventAgent includes performance context in LLM prompt...")
    print("-" * 80)
    
    prompt_context = f"""
Historical Performance Context for {current_regime.upper()} regime:
- Overall sentiment accuracy: {performance['sentiment_accuracy']:.1%}
- Bullish prediction accuracy: {performance['bullish_accuracy']:.1%}
- Bearish prediction accuracy: {performance['bearish_accuracy']:.1%}
- Based on {performance['sample_size']} historical predictions

Performance Notes:
{chr(10).join('- ' + note for note in performance['recommendations']['notes'])}

Please provide sentiment analysis with appropriate confidence calibration.
"""
    
    print("Enhanced LLM prompt context:")
    print(prompt_context)
    
    # [Step 5] Compare with normal regime
    print("\n[Step 5] Compare with normal regime performance...")
    print("-" * 80)
    
    normal_performance = learning_agent.get_event_agent_performance(
        market_regime="normal",
        min_samples=5
    )
    
    print(f"\nNormal regime performance:")
    print(f"  Sentiment Accuracy: {normal_performance['sentiment_accuracy']:.2%}")
    print(f"  Confidence-Weighted Accuracy: {normal_performance['confidence_weighted_accuracy']:.2%}")
    print(f"  Sample Size: {normal_performance['sample_size']}")
    
    print(f"\nComparison:")
    accuracy_diff = normal_performance['sentiment_accuracy'] - performance['sentiment_accuracy']
    print(f"  Accuracy difference: {accuracy_diff:+.2%}")
    
    if accuracy_diff > 0.1:
        print(f"  ⚠ EventAgent performs significantly better in normal regime")
        print(f"    Consider additional caution during earnings regime")
    elif accuracy_diff < -0.1:
        print(f"  ⚠ EventAgent performs significantly better in earnings regime")
        print(f"    Can be more aggressive during earnings")
    else:
        print(f"  ✓ EventAgent performance is consistent across regimes")
    
    # [Step 6] Demonstrate continuous improvement cycle
    print("\n[Step 6] Continuous improvement cycle...")
    print("-" * 80)
    
    print("\nFeedback Loop Workflow:")
    print("  1. EventAgent analyzes news → produces sentiment prediction")
    print("  2. Trade is executed based on sentiment")
    print("  3. LearningAgent tracks actual outcome vs prediction")
    print("  4. Performance metrics are updated in database")
    print("  5. EventAgent queries performance before next analysis")
    print("  6. EventAgent adjusts confidence threshold and prompt context")
    print("  7. Cycle repeats → continuous improvement")
    
    print("\n" + "=" * 80)
    print("Feedback Loop Integration Complete ✓")
    print("=" * 80)
    print("\nKey Benefits:")
    print("  • Dynamic confidence threshold adjustment based on historical accuracy")
    print("  • Regime-specific performance tracking and optimization")
    print("  • LLM prompt enhancement with performance context")
    print("  • Actionable recommendations for continuous improvement")
    print("  • Directional bias detection (bullish vs bearish accuracy)")
    print("=" * 80)

if __name__ == "__main__":
    demonstrate_feedback_loop()
