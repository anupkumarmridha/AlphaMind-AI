"""
Test for Task 3.2: Multi-Article Aggregation Logic

This test verifies that the EventAgent correctly:
1. Analyzes ALL high-impact articles (not just the first one)
2. Implements confidence-weighted averaging
3. Maintains single-article processing for cases with only one high-impact article

**Validates: Requirements 1.2, 2.2**
"""

from unittest.mock import Mock, patch
from datetime import datetime
from data.schema import NewsData
from agents.event_agent import EventAgent


def test_multi_article_aggregation():
    """
    Test that multiple high-impact articles are analyzed and aggregated.
    """
    print("\n=== Test Multi-Article Aggregation ===")
    
    # Create test news data
    news_list = [
        NewsData(
            title="Company Reports Strong Earnings Beat",
            content="Q4 earnings exceeded expectations with 20% revenue growth",
            date=datetime(2024, 1, 15, 10, 0, 0),
            url="https://ft.com/article1",
            publisher="Financial Times"
        ),
        NewsData(
            title="Analyst Upgrades Stock to Buy",
            content="Major investment bank upgrades rating citing strong fundamentals",
            date=datetime(2024, 1, 15, 11, 0, 0),
            url="https://bloomberg.com/article2",
            publisher="Bloomberg"
        ),
        NewsData(
            title="Product Recall Announced",
            content="Company recalls 10% of products due to safety concerns",
            date=datetime(2024, 1, 15, 12, 0, 0),
            url="https://reuters.com/article3",
            publisher="Reuters"
        )
    ]
    
    agent = EventAgent()
    
    # Mock the chain invocations
    def mock_triage_invoke(inputs):
        response = Mock()
        response.content = "HIGH"
        return response
    
    extraction_count = [0]
    extraction_responses = [
        # Article 1: Bullish earnings
        "event_type: earnings\nnumbers: 20% revenue growth\nimpact: bullish\nconfidence: 0.9\nimpact_magnitude: 0.8\nreason: Strong earnings beat with revenue growth",
        # Article 2: Bullish upgrade
        "event_type: deal\nnumbers: none\nimpact: bullish\nconfidence: 0.7\nimpact_magnitude: 0.6\nreason: Analyst upgrade to buy rating",
        # Article 3: Bearish recall
        "event_type: risk\nnumbers: 10% of products\nimpact: bearish\nconfidence: 0.8\nimpact_magnitude: 0.7\nreason: Product recall due to safety concerns"
    ]
    
    def mock_extract_invoke(inputs):
        response = Mock()
        response.content = extraction_responses[extraction_count[0]]
        extraction_count[0] += 1
        return response
    
    # Patch the chain invoke methods
    with patch.object(agent.triage_prompt, '__or__') as mock_triage_chain, \
         patch.object(agent.extract_prompt, '__or__') as mock_extract_chain:
        
        # Create mock chains
        triage_chain = Mock()
        triage_chain.invoke = mock_triage_invoke
        mock_triage_chain.return_value = triage_chain
        
        extract_chain = Mock()
        extract_chain.invoke = mock_extract_invoke
        mock_extract_chain.return_value = extract_chain
        
        # Analyze news
        result = agent.analyze_news(news_list)
        
        print(f"Result:\n{result}")
        
        # Verify all articles were processed
        assert extraction_count[0] == 3, f"Expected 3 extraction calls, got {extraction_count[0]}"
        print(f"✓ All {extraction_count[0]} high-impact articles were analyzed")
        
        # Parse result
        result_dict = {}
        for line in result.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result_dict[key.strip()] = value.strip()
        
        # Verify aggregation fields exist
        assert 'event_score' in result_dict, "event_score missing from output"
        assert 'confidence' in result_dict, "confidence missing from output"
        assert 'impact_magnitude' in result_dict, "impact_magnitude missing from output"
        
        event_score = float(result_dict['event_score'])
        confidence = float(result_dict['confidence'])
        impact_magnitude = float(result_dict['impact_magnitude'])
        
        print(f"✓ Event score: {event_score:.2f}")
        print(f"✓ Confidence: {confidence:.2f}")
        print(f"✓ Impact magnitude: {impact_magnitude:.2f}")
        
        # Verify confidence-weighted averaging was applied
        # With 2 bullish (0.8) and 1 bearish (0.2), weighted by confidence and impact:
        # Article 1: score=0.8, weight=0.9*0.8=0.72
        # Article 2: score=0.8, weight=0.7*0.6=0.42
        # Article 3: score=0.2, weight=0.8*0.7=0.56
        # Expected: (0.8*0.72 + 0.8*0.42 + 0.2*0.56) / (0.72 + 0.42 + 0.56)
        #         = (0.576 + 0.336 + 0.112) / 1.70 = 1.024 / 1.70 = 0.602
        
        expected_score = (0.8 * 0.72 + 0.8 * 0.42 + 0.2 * 0.56) / (0.72 + 0.42 + 0.56)
        print(f"✓ Expected aggregated score: {expected_score:.2f}")
        
        # Allow small tolerance for floating point
        assert abs(event_score - expected_score) < 0.01, \
            f"Event score {event_score:.2f} doesn't match expected {expected_score:.2f}"
        
        print("✓ Confidence-weighted averaging correctly applied")
        
        # Verify reason mentions aggregation
        reason = result_dict.get('reason', '')
        assert 'aggregated' in reason.lower() or '3' in reason, \
            f"Reason should mention aggregation: {reason}"
        print(f"✓ Reason indicates aggregation: {reason}")
        
        return True


def test_single_article_preservation():
    """
    Test that single-article processing is preserved when only one high-impact article exists.
    """
    print("\n=== Test Single Article Preservation ===")
    
    # Create test news data with only one article
    news_list = [
        NewsData(
            title="Company Reports Strong Earnings Beat",
            content="Q4 earnings exceeded expectations with 20% revenue growth",
            date=datetime(2024, 1, 15, 10, 0, 0),
            url="https://ft.com/article1",
            publisher="Financial Times"
        )
    ]
    
    agent = EventAgent()
    
    # Mock the chain invocations
    def mock_triage_invoke(inputs):
        response = Mock()
        response.content = "HIGH"
        return response
    
    def mock_extract_invoke(inputs):
        response = Mock()
        response.content = "event_type: earnings\nnumbers: 20% revenue growth\nimpact: bullish\nconfidence: 0.9\nimpact_magnitude: 0.8\nreason: Strong earnings beat with revenue growth"
        return response
    
    # Patch the chain invoke methods
    with patch.object(agent.triage_prompt, '__or__') as mock_triage_chain, \
         patch.object(agent.extract_prompt, '__or__') as mock_extract_chain:
        
        # Create mock chains
        triage_chain = Mock()
        triage_chain.invoke = mock_triage_invoke
        mock_triage_chain.return_value = triage_chain
        
        extract_chain = Mock()
        extract_chain.invoke = mock_extract_invoke
        mock_extract_chain.return_value = extract_chain
        
        # Analyze news
        result = agent.analyze_news(news_list)
        
        print(f"Result:\n{result}")
        
        # Parse result
        result_dict = {}
        for line in result.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result_dict[key.strip()] = value.strip()
        
        # Verify values match the single article
        event_score = float(result_dict['event_score'])
        confidence = float(result_dict['confidence'])
        impact_magnitude = float(result_dict['impact_magnitude'])
        
        assert event_score == 0.8, f"Expected event_score 0.8 for bullish, got {event_score}"
        assert confidence == 0.9, f"Expected confidence 0.9, got {confidence}"
        assert impact_magnitude == 0.8, f"Expected impact_magnitude 0.8, got {impact_magnitude}"
        
        print(f"✓ Single article values preserved: score={event_score}, confidence={confidence}, impact={impact_magnitude}")
        
        return True


def run():
    """
    Run all Task 3.2 tests.
    """
    print("=" * 70)
    print("TASK 3.2: MULTI-ARTICLE AGGREGATION LOGIC TEST")
    print("=" * 70)
    
    results = []
    
    try:
        results.append(("Multi-Article Aggregation", test_multi_article_aggregation()))
    except Exception as e:
        print(f"✗ Multi-Article Aggregation test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Multi-Article Aggregation", False))
    
    try:
        results.append(("Single Article Preservation", test_single_article_preservation()))
    except Exception as e:
        print(f"✗ Single Article Preservation test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Single Article Preservation", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Task 3.2 implementation verified")
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run()
    exit(0 if success else 1)
