# Preservation Property Test Results

## Test Execution Date
Executed on UNFIXED code before implementing the fix.

## Test Outcome
**✓ ALL 7 PRESERVATION TESTS PASSED**

This confirms the baseline behavior that MUST be preserved after implementing the fix.

## Observed Behaviors (UNFIXED Code)

### Property 1: Low-Impact News Returns Neutral
**Status**: ✓ PASSED

**Observation**: When all news articles are triaged as "LOW" impact, the EventAgent returns:
- `event_score: 0.0` (neutral)
- `impact: neutral`
- Proper TOON format with all required fields (event_type, impact, reason)

**Requirement**: This behavior must continue after the fix (Req 3.2, 3.4)

### Property 2: Empty News List Returns Expected TOON
**Status**: ✓ PASSED

**Observation**: When `analyze_news([])` is called with an empty list, the system returns:
```
event_score: 0.0
event_type: none
impact: neutral
reason: no news available
```

**Requirement**: This exact output must be preserved (Req 3.2, 3.3, 3.5)

### Property 3: TOON Format Parseable by FusionAgent
**Status**: ✓ PASSED

**Observation**: 
- EventAgent output is a string in TOON format
- FusionAgent._parse_toon() successfully parses the output
- The `event_score` field exists and can be extracted
- The `event_score` value is a valid float in range [0.0, 1.0]

**Requirement**: FusionAgent must continue to parse event_toon without modification (Req 3.3, 3.7)

### Property 4: Event Score Scale Preserved
**Status**: ✓ PASSED

**Observation**:
- `event_score` is always in the range [0.0, 1.0]
- The scale semantics: 0.5 = neutral, >0.5 = bullish, <0.5 = bearish
- The `impact` field exists in all outputs

**Requirement**: The 0.0-1.0 scale must be maintained (Req 3.6)

### Property 5: Method Signature Preserved
**Status**: ✓ PASSED

**Observation**:
- `EventAgent.analyze_news()` method exists
- Method accepts `news_list` parameter (List[NewsData])
- Method returns `str` (TOON format)

**Requirement**: Method signature must remain unchanged for backward compatibility (Req 3.5)

### Property 6: Two-Stage Triage Approach Preserved
**Status**: ✓ PASSED

**Observation**:
- `triage_llm` attribute exists (uses kimi-k2.5:cloud model)
- `extract_llm` attribute exists (uses kimi-k2.5:cloud model)
- `triage_prompt` attribute exists
- `extract_prompt` attribute exists
- Two-stage workflow: triage → deep extraction for high-impact only

**Requirement**: Two-stage LLM approach must continue (Req 3.1)

### Property 7: TOON Format Structure Preserved
**Status**: ✓ PASSED

**Observation**:
- Output is a string
- Format follows "key: value\n" pattern
- Each line contains exactly one ':' separator
- Keys are non-empty
- Required fields present: event_score, event_type, impact, reason

**Requirement**: TOON format structure must be maintained (Req 3.3)

## Validation Strategy

These tests use a **property-based testing approach** with concrete test cases:
- Tests validate invariants that must hold across all inputs
- Tests focus on non-buggy scenarios (empty lists, low-impact news)
- Tests avoid LLM calls where possible for reliability and speed
- Tests use mocking for controlled scenarios (low-impact news)

## Next Steps

1. Implement the fix (Tasks 3.1-3.8)
2. Re-run these SAME preservation tests on FIXED code
3. **Expected Outcome**: All 7 tests should STILL PASS
4. If any test fails, the fix has introduced a regression and must be corrected

## Test File Location
`test_news_sentiment_preservation.py`

## Requirements Validated
- 3.1: Two-stage LLM approach with kimi-k2.5:cloud model
- 3.2: Neutral sentiment for no news and low-impact news
- 3.3: TOON format for inter-agent communication
- 3.4: Low-impact news skips deep extraction
- 3.5: Method signature List[NewsData] -> str
- 3.6: Event score 0.0-1.0 scale (0.5 neutral, >0.5 bullish, <0.5 bearish)
- 3.7: FusionAgent parses event_score field
