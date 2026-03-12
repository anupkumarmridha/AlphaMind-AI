"""
Test for Task 3.4: Enhance TOON output format in EventAgent

Verifies that the EventAgent TOON output includes:
- confidence_score field
- impact_magnitude field
- All existing fields (event_score, event_type, impact, reason)
- Backward compatibility with existing format structure
"""

from agents.event_agent import EventAgent
from data.schema import NewsData
from datetime import datetime


def test_toon_output_has_confidence_and_impact_fields():
    """
    Test that TOON output includes confidence_score and impact_magnitude fields.
    
    Requirements: 1.4, 2.4, 3.3
    """
    agent = EventAgent()
    
    # Test with a single high-impact news article
    news_list = [
        NewsData(
            title="Apple Reports Record Q4 Earnings, Beats Expectations",
            content="Apple Inc. reported record quarterly earnings with revenue up 15% year-over-year, significantly beating analyst expectations.",
            date=datetime.now(),
            publisher="Financial Times",
            url="https://example.com/apple-earnings"
        )
    ]
    
    result = agent.analyze_news(news_list)
    
    print("TOON Output:")
    print(result)
    print()
    
    # Verify all required fields are present
    assert "event_score:" in result, "Missing event_score field"
    assert "event_type:" in result, "Missing event_type field"
    assert "impact:" in result, "Missing impact field"
    assert "confidence_score:" in result, "Missing confidence_score field"
    assert "impact_magnitude:" in result, "Missing impact_magnitude field"
    assert "reason:" in result, "Missing reason field"
    
    # Parse the TOON output
    parsed = {}
    for line in result.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            parsed[key.strip()] = value.strip()
    
    # Verify confidence_score is a valid number between 0.0 and 1.0
    confidence_score = float(parsed.get("confidence_score", "-1"))
    assert 0.0 <= confidence_score <= 1.0, f"confidence_score {confidence_score} not in valid range [0.0, 1.0]"
    
    # Verify impact_magnitude is a valid number between 0.0 and 1.0
    impact_magnitude = float(parsed.get("impact_magnitude", "-1"))
    assert 0.0 <= impact_magnitude <= 1.0, f"impact_magnitude {impact_magnitude} not in valid range [0.0, 1.0]"
    
    # Verify event_score is still present and valid
    event_score = float(parsed.get("event_score", "-1"))
    assert 0.0 <= event_score <= 1.0, f"event_score {event_score} not in valid range [0.0, 1.0]"
    
    print("✓ All required fields present in TOON output")
    print(f"✓ confidence_score: {confidence_score}")
    print(f"✓ impact_magnitude: {impact_magnitude}")
    print(f"✓ event_score: {event_score}")
    print()


def test_toon_output_backward_compatibility():
    """
    Test that existing fields are maintained for backward compatibility.
    
    Requirements: 3.3, 3.4
    """
    agent = EventAgent()
    
    # Test with empty news list
    result = agent.analyze_news([])
    
    print("Empty news TOON output:")
    print(result)
    print()
    
    # Verify backward compatibility - existing fields still present
    assert "event_score: 0.0" in result or "event_score: 0.00" in result, "Missing event_score in empty news case"
    assert "event_type:" in result, "Missing event_type in empty news case"
    assert "impact: neutral" in result, "Missing neutral impact in empty news case"
    assert "reason:" in result, "Missing reason in empty news case"
    
    print("✓ Backward compatibility maintained for empty news case")
    print()


def test_toon_output_multi_article_aggregation():
    """
    Test that multi-article aggregation includes confidence_score and impact_magnitude.
    
    Requirements: 1.4, 2.4
    """
    agent = EventAgent()
    
    # Test with multiple high-impact articles
    news_list = [
        NewsData(
            title="Tesla Announces Major Battery Breakthrough",
            content="Tesla unveiled a revolutionary battery technology that could double EV range and reduce costs by 40%.",
            date=datetime.now(),
            publisher="Tech News",
            url="https://example.com/tesla-battery"
        ),
        NewsData(
            title="Tesla Faces Regulatory Investigation",
            content="Federal regulators opened an investigation into Tesla's autopilot safety features following recent incidents.",
            date=datetime.now(),
            publisher="Reuters",
            url="https://example.com/tesla-investigation"
        ),
        NewsData(
            title="Tesla Q4 Deliveries Beat Estimates",
            content="Tesla reported Q4 vehicle deliveries that exceeded analyst expectations by 12%, showing strong demand.",
            date=datetime.now(),
            publisher="Bloomberg",
            url="https://example.com/tesla-deliveries"
        )
    ]
    
    result = agent.analyze_news(news_list)
    
    print("Multi-article TOON output:")
    print(result)
    print()
    
    # Verify all required fields are present
    assert "confidence_score:" in result, "Missing confidence_score in multi-article case"
    assert "impact_magnitude:" in result, "Missing impact_magnitude in multi-article case"
    assert "event_score:" in result, "Missing event_score in multi-article case"
    
    # Parse and verify values
    parsed = {}
    for line in result.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            parsed[key.strip()] = value.strip()
    
    confidence_score = float(parsed.get("confidence_score", "-1"))
    impact_magnitude = float(parsed.get("impact_magnitude", "-1"))
    event_score = float(parsed.get("event_score", "-1"))
    
    assert 0.0 <= confidence_score <= 1.0, f"Invalid confidence_score: {confidence_score}"
    assert 0.0 <= impact_magnitude <= 1.0, f"Invalid impact_magnitude: {impact_magnitude}"
    assert 0.0 <= event_score <= 1.0, f"Invalid event_score: {event_score}"
    
    print("✓ Multi-article aggregation includes confidence_score and impact_magnitude")
    print(f"✓ Aggregated confidence_score: {confidence_score}")
    print(f"✓ Aggregated impact_magnitude: {impact_magnitude}")
    print(f"✓ Aggregated event_score: {event_score}")
    print()


def run():
    """Run all Task 3.4 tests."""
    print("=" * 70)
    print("Task 3.4: Enhance TOON Output Format in EventAgent")
    print("=" * 70)
    print()
    
    try:
        test_toon_output_has_confidence_and_impact_fields()
        test_toon_output_backward_compatibility()
        test_toon_output_multi_article_aggregation()
        
        print("=" * 70)
        print("✓ ALL TASK 3.4 TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("- TOON output includes confidence_score field")
        print("- TOON output includes impact_magnitude field")
        print("- All existing fields maintained (event_score, event_type, impact, reason)")
        print("- Backward compatibility preserved")
        print("- Multi-article aggregation works correctly")
        print()
        
    except AssertionError as e:
        print("=" * 70)
        print("✗ TEST FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        raise
    except Exception as e:
        print("=" * 70)
        print("✗ TEST ERROR")
        print("=" * 70)
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    run()
