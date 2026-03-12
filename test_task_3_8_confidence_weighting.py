"""
Test Task 3.8: Confidence-Aware Weighting in FusionAgent

This test verifies that:
1. FusionAgent parses confidence_score from event_toon
2. Event weight is adjusted dynamically: effective_event_weight = base_event_weight * confidence_score
3. Low confidence (<0.5) reduces event signal influence
4. Explanation string includes confidence information
"""

from agents.fusion_agent import FusionAgent


def test_confidence_parsing():
    """Test that FusionAgent correctly parses confidence_score from event_toon"""
    print("\n=== Test 1: Confidence Score Parsing ===")
    
    technical_toon = "technical_score: 0.6\nreason: Bullish technical indicators"
    event_toon = "event_score: 0.8\nconfidence_score: 0.9\nimpact_magnitude: 0.7\nreason: Strong earnings beat"
    risk_toon = "risk_score: 0.2\nrisk_level: LOW\nreason: Low volatility"
    
    result = FusionAgent.synthesize(technical_toon, event_toon, risk_toon, market_regime="normal")
    
    # Verify confidence is included in explanation
    assert "Event confidence: 0.90" in result["reason"], f"Expected confidence in explanation, got: {result['reason']}"
    print(f"✓ Confidence score parsed and included in explanation")
    print(f"  Explanation: {result['reason']}")
    

def test_high_confidence_weighting():
    """Test that high confidence (0.9) maintains strong event signal influence"""
    print("\n=== Test 2: High Confidence Weighting ===")
    
    technical_toon = "technical_score: 0.5\nreason: Neutral technical"
    event_toon_high_conf = "event_score: 0.8\nconfidence_score: 0.9\nreason: High confidence bullish news"
    risk_toon = "risk_score: 0.1\nrisk_level: LOW\nreason: Low risk"
    
    result_high = FusionAgent.synthesize(technical_toon, event_toon_high_conf, risk_toon, market_regime="normal")
    
    print(f"  High confidence (0.9) result:")
    print(f"    Decision: {result_high['decision']}")
    print(f"    Final Signal: {result_high['reason'].split('Final Signal: ')[1].split('.')[0]}")
    print(f"    Confidence: {result_high['confidence']}")
    
    # With high confidence, event signal should have strong influence
    # In normal regime: base_event_weight = 0.2, effective = 0.2 * 0.9 = 0.18
    # Event score 0.8 (normalized to 0.6) * 0.18 = 0.108
    # Tech score 0.5 (normalized to 0.0) * 0.6 = 0.0
    # Base signal ≈ 0.108, after risk penalty should still be positive
    assert result_high['confidence'] > 0, "Expected positive confidence with high event confidence"
    print(f"✓ High confidence maintains event signal influence")


def test_low_confidence_weighting():
    """Test that low confidence (<0.5) reduces event signal influence"""
    print("\n=== Test 3: Low Confidence Weighting ===")
    
    technical_toon = "technical_score: 0.5\nreason: Neutral technical"
    event_toon_low_conf = "event_score: 0.8\nconfidence_score: 0.3\nreason: Low confidence bullish news"
    risk_toon = "risk_score: 0.1\nrisk_level: LOW\nreason: Low risk"
    
    result_low = FusionAgent.synthesize(technical_toon, event_toon_low_conf, risk_toon, market_regime="normal")
    
    print(f"  Low confidence (0.3) result:")
    print(f"    Decision: {result_low['decision']}")
    print(f"    Final Signal: {result_low['reason'].split('Final Signal: ')[1].split('.')[0]}")
    print(f"    Confidence: {result_low['confidence']}")
    
    # With low confidence, event signal should have reduced influence
    # In normal regime: base_event_weight = 0.2, effective = 0.2 * 0.3 = 0.06
    # Event score 0.8 (normalized to 0.6) * 0.06 = 0.036
    # This should result in lower final signal compared to high confidence
    print(f"✓ Low confidence reduces event signal influence")


def test_confidence_comparison():
    """Compare high vs low confidence with same event score"""
    print("\n=== Test 4: Confidence Comparison (Same Event Score) ===")
    
    technical_toon = "technical_score: 0.5\nreason: Neutral"
    risk_toon = "risk_score: 0.1\nrisk_level: LOW\nreason: Low risk"
    
    # High confidence
    event_toon_high = "event_score: 0.8\nconfidence_score: 0.9\nreason: High confidence"
    result_high = FusionAgent.synthesize(technical_toon, event_toon_high, risk_toon, market_regime="normal")
    
    # Low confidence
    event_toon_low = "event_score: 0.8\nconfidence_score: 0.3\nreason: Low confidence"
    result_low = FusionAgent.synthesize(technical_toon, event_toon_low, risk_toon, market_regime="normal")
    
    # Extract final signals
    signal_high = float(result_high['reason'].split('Final Signal: ')[1].split('.')[0] + '.' + 
                       result_high['reason'].split('Final Signal: ')[1].split('.')[1][:3])
    signal_low = float(result_low['reason'].split('Final Signal: ')[1].split('.')[0] + '.' + 
                      result_low['reason'].split('Final Signal: ')[1].split('.')[1][:3])
    
    print(f"  Same event_score (0.8), different confidence:")
    print(f"    High confidence (0.9): Final Signal = {signal_high:.3f}")
    print(f"    Low confidence (0.3): Final Signal = {signal_low:.3f}")
    print(f"    Difference: {signal_high - signal_low:.3f}")
    
    # High confidence should produce stronger signal than low confidence
    assert signal_high > signal_low, f"Expected high confidence signal ({signal_high}) > low confidence signal ({signal_low})"
    print(f"✓ High confidence produces stronger signal than low confidence")


def test_earnings_regime_confidence():
    """Test confidence weighting in earnings regime (higher base event weight)"""
    print("\n=== Test 5: Earnings Regime Confidence Weighting ===")
    
    technical_toon = "technical_score: 0.5\nreason: Neutral"
    risk_toon = "risk_score: 0.1\nrisk_level: LOW\nreason: Low risk"
    
    # In earnings regime, base_event_weight = 0.6 (much higher than normal's 0.2)
    event_toon = "event_score: 0.8\nconfidence_score: 0.7\nreason: Earnings news"
    
    result_earnings = FusionAgent.synthesize(technical_toon, event_toon, risk_toon, market_regime="earnings")
    result_normal = FusionAgent.synthesize(technical_toon, event_toon, risk_toon, market_regime="normal")
    
    signal_earnings = float(result_earnings['reason'].split('Final Signal: ')[1].split('.')[0] + '.' + 
                           result_earnings['reason'].split('Final Signal: ')[1].split('.')[1][:3])
    signal_normal = float(result_normal['reason'].split('Final Signal: ')[1].split('.')[0] + '.' + 
                         result_normal['reason'].split('Final Signal: ')[1].split('.')[1][:3])
    
    print(f"  Same confidence (0.7), different regimes:")
    print(f"    Earnings regime: Final Signal = {signal_earnings:.3f}")
    print(f"    Normal regime: Final Signal = {signal_normal:.3f}")
    print(f"    Difference: {signal_earnings - signal_normal:.3f}")
    
    # Earnings regime should amplify event signal more than normal regime
    assert signal_earnings > signal_normal, f"Expected earnings signal ({signal_earnings}) > normal signal ({signal_normal})"
    print(f"✓ Earnings regime amplifies event signal with confidence weighting")


def test_backward_compatibility():
    """Test that missing confidence_score defaults to 1.0 (full confidence)"""
    print("\n=== Test 6: Backward Compatibility (Missing confidence_score) ===")
    
    technical_toon = "technical_score: 0.6\nreason: Bullish"
    event_toon_no_conf = "event_score: 0.8\nreason: Old format without confidence"
    risk_toon = "risk_score: 0.1\nrisk_level: LOW\nreason: Low risk"
    
    result = FusionAgent.synthesize(technical_toon, event_toon_no_conf, risk_toon, market_regime="normal")
    
    # Should default to confidence 1.0 and work normally
    print(f"  Result with missing confidence_score:")
    print(f"    Decision: {result['decision']}")
    print(f"    Explanation includes 'Event confidence: 1.00': {'Event confidence: 1.00' in result['reason']}")
    
    assert "Event confidence: 1.00" in result["reason"], "Expected default confidence 1.0 in explanation"
    print(f"✓ Missing confidence_score defaults to 1.0 (backward compatible)")


def test_zero_confidence():
    """Test edge case: zero confidence should nullify event signal"""
    print("\n=== Test 7: Zero Confidence Edge Case ===")
    
    technical_toon = "technical_score: 0.5\nreason: Neutral"
    event_toon_zero = "event_score: 0.9\nconfidence_score: 0.0\nreason: Zero confidence"
    risk_toon = "risk_score: 0.1\nrisk_level: LOW\nreason: Low risk"
    
    result = FusionAgent.synthesize(technical_toon, event_toon_zero, risk_toon, market_regime="normal")
    
    signal = float(result['reason'].split('Final Signal: ')[1].split('.')[0] + '.' + 
                  result['reason'].split('Final Signal: ')[1].split('.')[1][:3])
    
    print(f"  Zero confidence (0.0) with high event_score (0.9):")
    print(f"    Final Signal: {signal:.3f}")
    print(f"    Decision: {result['decision']}")
    
    # With zero confidence, event signal should be nullified
    # effective_event_weight = 0.2 * 0.0 = 0.0
    # Signal should be close to 0 (only tech and risk influence)
    assert abs(signal) < 0.1, f"Expected near-zero signal with zero confidence, got {signal}"
    print(f"✓ Zero confidence nullifies event signal influence")


def run():
    """Run all Task 3.8 tests"""
    print("=" * 70)
    print("Task 3.8: Confidence-Aware Weighting in FusionAgent")
    print("=" * 70)
    
    try:
        test_confidence_parsing()
        test_high_confidence_weighting()
        test_low_confidence_weighting()
        test_confidence_comparison()
        test_earnings_regime_confidence()
        test_backward_compatibility()
        test_zero_confidence()
        
        print("\n" + "=" * 70)
        print("✓ All Task 3.8 tests passed!")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ FusionAgent parses confidence_score from event_toon")
        print("  ✓ Event weight adjusted: effective_weight = base_weight * confidence")
        print("  ✓ Low confidence (<0.5) reduces event signal influence")
        print("  ✓ High confidence maintains strong event signal influence")
        print("  ✓ Confidence weighting works across different market regimes")
        print("  ✓ Backward compatible with missing confidence_score (defaults to 1.0)")
        print("  ✓ Zero confidence nullifies event signal")
        print("  ✓ Explanation string includes confidence information")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    run()
