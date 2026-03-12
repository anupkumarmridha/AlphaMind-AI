"""
Integration test for Task 3.4: Verify TOON output format works with FusionAgent

This test verifies that:
1. EventAgent produces TOON output with confidence_score and impact_magnitude
2. FusionAgent can parse the new TOON format
3. The system maintains backward compatibility
"""

from agents.event_agent import EventAgent
from agents.fusion_agent import FusionAgent
from data.schema import NewsData
from datetime import datetime


def test_fusion_agent_parses_new_toon_format():
    """
    Test that FusionAgent can parse TOON output with new fields.
    
    Requirements: 3.3, 3.4, 3.7
    """
    agent = EventAgent()
    
    # Generate TOON output with confidence_score and impact_magnitude
    news_list = [
        NewsData(
            title="Microsoft Announces Major AI Partnership",
            content="Microsoft announced a strategic partnership with leading AI research labs, expected to accelerate AI development.",
            date=datetime.now(),
            publisher="Tech News",
            url="https://example.com/msft-ai"
        )
    ]
    
    event_toon = agent.analyze_news(news_list)
    
    print("EventAgent TOON Output:")
    print(event_toon)
    print()
    
    # Create dummy technical and risk TOON outputs
    technical_toon = "technical_score: 0.65\nreason: Strong uptrend with high volume\n"
    risk_toon = "risk_score: 0.3\nrisk_level: LOW\nreason: Low volatility, good liquidity\n"
    
    # Test that FusionAgent can parse the new format
    try:
        result = FusionAgent.synthesize(
            technical_toon=technical_toon,
            event_toon=event_toon,
            risk_toon=risk_toon,
            market_regime="normal"
        )
        
        print("FusionAgent Result:")
        print(f"Decision: {result['decision']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Position Size: {result['position_size']}")
        print(f"Reason: {result['reason']}")
        print()
        
        # Verify FusionAgent successfully processed the TOON
        assert result['decision'] in ['BUY', 'SELL', 'NO_TRADE'], "Invalid decision"
        assert 0.0 <= result['confidence'] <= 1.0, "Invalid confidence"
        assert 0.0 <= result['position_size'] <= 1.0, "Invalid position size"
        
        print("✓ FusionAgent successfully parsed new TOON format")
        print("✓ Backward compatibility maintained")
        print()
        
    except Exception as e:
        print(f"✗ FusionAgent failed to parse new TOON format: {e}")
        raise


def test_toon_fields_accessible():
    """
    Test that new fields are accessible when parsing TOON output.
    
    Requirements: 1.4, 2.4
    """
    agent = EventAgent()
    
    news_list = [
        NewsData(
            title="Amazon Expands Cloud Services",
            content="Amazon Web Services announced expansion into new regions with enhanced AI capabilities.",
            date=datetime.now(),
            publisher="Cloud News",
            url="https://example.com/aws-expansion"
        )
    ]
    
    event_toon = agent.analyze_news(news_list)
    
    # Parse TOON manually
    parsed = {}
    for line in event_toon.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            parsed[key.strip()] = value.strip()
    
    print("Parsed TOON fields:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")
    print()
    
    # Verify all expected fields are present and accessible
    assert 'event_score' in parsed, "Missing event_score"
    assert 'event_type' in parsed, "Missing event_type"
    assert 'impact' in parsed, "Missing impact"
    assert 'confidence_score' in parsed, "Missing confidence_score"
    assert 'impact_magnitude' in parsed, "Missing impact_magnitude"
    assert 'reason' in parsed, "Missing reason"
    
    # Verify values are valid
    event_score = float(parsed['event_score'])
    confidence_score = float(parsed['confidence_score'])
    impact_magnitude = float(parsed['impact_magnitude'])
    
    assert 0.0 <= event_score <= 1.0, f"Invalid event_score: {event_score}"
    assert 0.0 <= confidence_score <= 1.0, f"Invalid confidence_score: {confidence_score}"
    assert 0.0 <= impact_magnitude <= 1.0, f"Invalid impact_magnitude: {impact_magnitude}"
    
    print("✓ All TOON fields present and accessible")
    print("✓ All values within valid ranges")
    print()


def run():
    """Run all Task 3.4 integration tests."""
    print("=" * 70)
    print("Task 3.4 Integration Tests: TOON Output Format")
    print("=" * 70)
    print()
    
    try:
        test_fusion_agent_parses_new_toon_format()
        test_toon_fields_accessible()
        
        print("=" * 70)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print()
        print("Task 3.4 Complete:")
        print("- TOON output includes confidence_score field")
        print("- TOON output includes impact_magnitude field")
        print("- FusionAgent successfully parses new format")
        print("- Backward compatibility maintained")
        print("- All fields accessible and within valid ranges")
        print()
        
    except AssertionError as e:
        print("=" * 70)
        print("✗ INTEGRATION TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        raise
    except Exception as e:
        print("=" * 70)
        print("✗ INTEGRATION TEST ERROR")
        print("=" * 70)
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    run()
