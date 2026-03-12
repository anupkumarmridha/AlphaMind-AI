"""
Test for Task 3.3: Remove keyword-based scoring logic in EventAgent

This test verifies that:
1. The hardcoded keyword-based scoring (0.2, 0.5, 0.8) has been removed
2. The LLM's numeric sentiment_score is parsed directly
3. The prompt asks for sentiment_score in the output format
"""

import inspect
from agents.event_agent import EventAgent, DEEP_EXTRACT_PROMPT

def test_keyword_removal():
    """Verify that keyword-based scoring logic has been removed."""
    print("=" * 80)
    print("TASK 3.3: KEYWORD-BASED SCORING REMOVAL TEST")
    print("=" * 80)
    
    # Get the source code of the EventAgent class
    source = inspect.getsource(EventAgent)
    
    print("\n=== Test 1: Verify hardcoded scores removed ===")
    # Check that hardcoded scores are NOT in the code
    has_hardcoded_08 = 'sentiment_score = 0.8' in source
    has_hardcoded_02 = 'sentiment_score = 0.2' in source
    has_hardcoded_05 = 'sentiment_score = 0.5' in source
    
    print(f"Has 'sentiment_score = 0.8': {has_hardcoded_08}")
    print(f"Has 'sentiment_score = 0.2': {has_hardcoded_02}")
    print(f"Has 'sentiment_score = 0.5': {has_hardcoded_05}")
    
    if not (has_hardcoded_08 or has_hardcoded_02 or has_hardcoded_05):
        print("✓ PASS: No hardcoded sentiment scores found")
    else:
        print("✗ FAIL: Hardcoded sentiment scores still exist")
        return False
    
    print("\n=== Test 2: Verify keyword matching removed ===")
    # Check that keyword-based conversion is NOT in the code
    has_bullish_check = 'if impact_str == "bullish":' in source or 'if "bullish" in' in source
    has_bearish_check = 'if impact_str == "bearish":' in source or 'if "bearish" in' in source
    
    # Note: We still derive impact_str FROM sentiment_score for backward compatibility
    # But we should NOT be converting FROM impact_str TO sentiment_score
    has_keyword_to_score = (
        ('if impact_str == "bullish":\n        sentiment_score' in source) or
        ('if "bullish" in extraction_result.lower():\n        sentiment_score' in source)
    )
    
    print(f"Has keyword-to-score conversion: {has_keyword_to_score}")
    
    if not has_keyword_to_score:
        print("✓ PASS: Keyword-based score assignment removed")
    else:
        print("✗ FAIL: Keyword-based score assignment still exists")
        return False
    
    print("\n=== Test 3: Verify LLM sentiment_score parsing ===")
    # Check that we're parsing sentiment_score from LLM output
    has_sentiment_score_parse = 'parsed.get("sentiment_score"' in source
    
    print(f"Has sentiment_score parsing: {has_sentiment_score_parse}")
    
    if has_sentiment_score_parse:
        print("✓ PASS: LLM's sentiment_score is parsed directly")
    else:
        print("✗ FAIL: sentiment_score parsing not found")
        return False
    
    print("\n=== Test 4: Verify prompt asks for sentiment_score ===")
    # Check that the prompt asks for sentiment_score
    has_sentiment_score_in_prompt = 'sentiment_score:' in DEEP_EXTRACT_PROMPT
    
    print(f"Prompt asks for sentiment_score: {has_sentiment_score_in_prompt}")
    
    if has_sentiment_score_in_prompt:
        print("✓ PASS: Prompt requests sentiment_score from LLM")
    else:
        print("✗ FAIL: Prompt doesn't request sentiment_score")
        return False
    
    print("\n=== Test 5: Verify 0.0-1.0 scale preservation ===")
    # Check that we're clamping to [0.0, 1.0] range
    has_range_check = 'max(0.0, min(1.0, sentiment_score))' in source or 'min(1.0, sentiment_score)' in source
    
    print(f"Has range validation: {has_range_check}")
    
    if has_range_check:
        print("✓ PASS: Sentiment score is validated to 0.0-1.0 range")
    else:
        print("✗ FAIL: No range validation found")
        return False
    
    print("\n" + "=" * 80)
    print("TASK 3.3 VERIFICATION: ALL TESTS PASSED ✓")
    print("=" * 80)
    print("\nSummary:")
    print("  ✓ Hardcoded scores (0.2, 0.5, 0.8) removed")
    print("  ✓ Keyword-based score assignment removed")
    print("  ✓ LLM's numeric sentiment_score parsed directly")
    print("  ✓ Prompt asks for sentiment_score")
    print("  ✓ 0.0-1.0 scale preserved with validation")
    print("\nThe EventAgent now trusts the LLM's reasoning rather than")
    print("post-processing with hardcoded keyword matching.")
    
    return True

if __name__ == "__main__":
    success = test_keyword_removal()
    exit(0 if success else 1)
