# News Sentiment Accuracy Fix - Bugfix Design

## Overview

The EventAgent's sentiment analysis suffers from seven critical defects that lead to inaccurate trading decisions. The fix enhances the LLM extraction prompt to return structured confidence and impact data, implements multi-article aggregation with confidence weighting, adds validation against market movements, provides uncertainty quantification in TOON output, implements robust error handling with retry logic, creates a feedback mechanism for the learning agent, and leverages the LLM's full reasoning capabilities for nuanced sentiment analysis. The approach maintains backward compatibility with existing TOON format and agent interfaces while significantly improving sentiment accuracy.

## Glossary

- **Bug_Condition (C)**: The condition that triggers inaccurate sentiment - when the EventAgent produces sentiment scores without confidence quantification, analyzes only single articles, lacks validation mechanisms, or uses simplistic keyword matching
- **Property (P)**: The desired behavior - sentiment scores should be confidence-weighted, multi-article aggregated, validated against market movements, and include uncertainty quantification
- **Preservation**: Existing TOON format, two-stage triage approach, agent interfaces, and 0.0-1.0 scoring scale that must remain unchanged
- **EventAgent**: The agent in `agents/event_agent.py` that analyzes news articles and produces sentiment scores
- **TOON Format**: Token-Optimized Object Notation used for inter-agent communication (key: value pairs)
- **Confidence Score**: A 0.0-1.0 value indicating the LLM's certainty in its sentiment classification
- **Impact Magnitude**: A 0.0-1.0 value indicating the expected market impact strength of the news
- **Multi-Article Aggregation**: Combining sentiment from multiple high-impact articles using confidence-weighted averaging
- **Sentiment Validation**: Comparing predicted sentiment direction against actual price movements post-news
- **LearningAgent**: The agent in `agents/learning_agent.py` that stores trade patterns and optimizes weights

## Bug Details

### Bug Condition

The bug manifests when the EventAgent processes news articles and produces sentiment classifications. The system exhibits multiple failure modes: (1) hardcoded sentiment scores based on keyword matching without considering LLM confidence or impact magnitude, (2) analyzing only the first high-impact article while ignoring subsequent important news, (3) no validation mechanism to track prediction accuracy, (4) no confidence quantification in output for downstream fusion logic, (5) silent failures with neutral defaults when LLM extraction errors occur, (6) no feedback loop to the learning agent for continuous improvement, and (7) inability to capture nuanced sentiment with conditional logic or mixed signals.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type NewsAnalysisContext
  OUTPUT: boolean
  
  RETURN (input.sentiment_score IN [0.2, 0.5, 0.8] AND input.confidence_score IS NULL)
         OR (input.high_impact_articles.length > 1 AND input.analyzed_articles.length == 1)
         OR (input.validation_mechanism_exists == FALSE)
         OR (input.confidence_in_toon_output == FALSE)
         OR (input.llm_extraction_failed AND input.retry_attempted == FALSE)
         OR (input.feedback_to_learning_agent == FALSE)
         OR (input.sentiment_method == "keyword_matching")
END FUNCTION
```

### Examples

- **Defect 1 - Hardcoded Scores**: LLM returns "The earnings beat expectations with strong guidance" → EventAgent extracts "bullish" keyword → assigns hardcoded 0.8 score regardless of LLM's actual confidence or the magnitude of the earnings beat
- **Defect 2 - Single Article Analysis**: Three high-impact articles identified (earnings beat, analyst upgrade, product recall) → EventAgent only analyzes the first article (earnings) → ignores the negative product recall news → produces overly bullish sentiment
- **Defect 3 - No Validation**: EventAgent predicts bullish sentiment (0.8) for merger news → stock drops 5% next day → system has no mechanism to track this prediction failure or learn from it
- **Defect 4 - No Confidence Quantification**: EventAgent produces "event_score: 0.8" → FusionAgent receives no information about whether this is a high-confidence or low-confidence prediction → treats all 0.8 scores equally in weighting
- **Defect 5 - Silent Failures**: LLM API times out during extraction → EventAgent catches exception → returns "event_score: 0.5" with neutral sentiment → no retry attempted, no logging of failure pattern → potentially critical news is missed
- **Defect 6 - No Learning Feedback**: Trade executed based on event analysis → trade closes with loss → LearningAgent receives no information about whether the sentiment prediction was accurate → cannot improve event analysis weights
- **Defect 7 - Keyword Matching Limitation**: News states "Earnings beat expectations, but guidance was lowered due to supply chain concerns" → Simple keyword matching finds "beat" → assigns bullish score → misses the bearish guidance and conditional nature of the positive earnings

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The two-stage LLM approach (triage with "HIGH"/"LOW" → deep extraction for high-impact) must continue to use the kimi-k2.5:cloud model
- When no news is available, the system must continue to return "event_score: 0.0\nevent_type: none\nimpact: neutral\nreason: no news available\n"
- The EventAgent must continue to return TOON format strings for inter-agent communication
- Low-impact news detected during triage must continue to skip deep extraction and return neutral sentiment
- The EventAgent.analyze_news() method signature must continue to accept List[NewsData] as input and return str (TOON format) as output
- The event_score field must continue to use the 0.0 to 1.0 scale where 0.5 is neutral, >0.5 is bullish, <0.5 is bearish
- The FusionAgent must continue to parse event_toon output and extract the event_score field for regime-dependent weighting

**Scope:**
All inputs that do NOT involve high-impact news analysis should be completely unaffected by this fix. This includes:
- Low-impact news triage and neutral sentiment returns
- Empty news list handling
- TOON format structure and parsing
- Agent orchestration in the LangGraph workflow (agents/graph.py)
- FusionAgent's event_score parsing and weighting logic

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Insufficient LLM Prompt Design**: The DEEP_EXTRACT_PROMPT only asks for "impact: bullish/bearish/neutral" without requesting confidence scores or impact magnitude. The LLM has this information but isn't prompted to return it in a structured format.

2. **Single Article Processing Logic**: In `event_agent.py` line 62, the code explicitly takes only `top_news = high_impact_news[0]` and processes it, with a comment acknowledging "A more advanced version would run a map-reduce over all high impact news." This is a known limitation that was deferred.

3. **Keyword-Based Score Assignment**: Lines 68-72 in `event_agent.py` use simple string matching (`if "bullish" in extraction_result.lower()`) to assign hardcoded scores (0.8, 0.2, 0.5), completely ignoring any nuance the LLM might have provided.

4. **No Validation Infrastructure**: There is no code in the EventAgent or LearningAgent that compares predicted sentiment against actual price movements. The LearningAgent only tracks trade outcomes, not individual agent prediction accuracy.

5. **Minimal Error Handling**: The try-except block in line 66 catches all exceptions and returns a generic error TOON with event_score 0.0, with no retry logic or detailed error logging.

6. **Missing Feedback Loop**: The LearningAgent.evaluate_and_store() method in `learning_agent.py` only receives trade-level data (trade outcome, reason_toon, embedding) but not individual agent prediction accuracy, so it cannot provide feedback to improve the EventAgent's sentiment analysis.

7. **TOON Format Limitations**: The current TOON output format doesn't include fields for confidence_score or impact_magnitude, so even if the LLM provided this data, it wouldn't be communicated to downstream agents.

## Correctness Properties

Property 1: Bug Condition - Confidence-Weighted Multi-Article Sentiment Analysis

_For any_ input where multiple high-impact news articles are identified (isBugCondition returns true for multi-article scenarios), the fixed EventAgent SHALL analyze all high-impact articles, extract confidence scores and impact magnitudes from the LLM for each article, aggregate sentiment using confidence-weighted averaging, and return a TOON output that includes the aggregated event_score, confidence_score, and impact_magnitude fields.

**Validates: Requirements 2.1, 2.2, 2.4**

Property 2: Preservation - TOON Format and Agent Interface Compatibility

_For any_ input where the bug condition does NOT hold (single article analysis, low-impact news, or no news scenarios), the fixed EventAgent SHALL produce TOON output that maintains backward compatibility with the existing format, preserving the event_score field on the 0.0-1.0 scale, maintaining the analyze_news(List[NewsData]) → str method signature, and ensuring FusionAgent can parse the output without modification.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `agents/event_agent.py`

**Function**: `EventAgent.analyze_news()`

**Specific Changes**:

1. **Enhanced LLM Extraction Prompt**: Modify DEEP_EXTRACT_PROMPT to request structured output with confidence and impact fields
   - Add "confidence: <0.0-1.0 value indicating certainty>" to the prompt format
   - Add "impact_magnitude: <0.0-1.0 value indicating expected market impact strength>" to the prompt format
   - Update the prompt instructions to ask the LLM to reason about sentiment with full context rather than just keywords
   - Example: "confidence: 0.85" means the LLM is 85% certain of its sentiment classification

2. **Multi-Article Aggregation Logic**: Replace single-article processing with map-reduce pattern
   - Remove `top_news = high_impact_news[0]` single article selection
   - Implement loop to extract sentiment from ALL high-impact articles
   - Store each article's sentiment, confidence, and impact_magnitude in a list
   - Implement confidence-weighted averaging: `final_score = sum(score_i * confidence_i * impact_i) / sum(confidence_i * impact_i)`
   - Aggregate confidence as the weighted average of individual confidences

3. **Remove Keyword-Based Scoring**: Delete the hardcoded score assignment logic
   - Remove lines 68-72 that use "bullish"/"bearish" string matching
   - Parse the LLM's returned sentiment value directly (it should return a numeric score or clear classification)
   - Trust the LLM's reasoning rather than post-processing with keywords

4. **Enhanced TOON Output Format**: Add new fields to the returned TOON string
   - Add "confidence_score: <value>" field to quantify prediction certainty
   - Add "impact_magnitude: <value>" field to indicate expected market impact strength
   - Maintain backward compatibility by keeping existing fields (event_score, event_type, impact, reason)
   - Example output: "event_score: 0.75\nconfidence_score: 0.82\nimpact_magnitude: 0.68\nevent_type: earnings\nimpact: bullish\nreason: Strong earnings beat with positive guidance\n"

5. **Retry Logic and Error Handling**: Implement robust error handling with fallback strategies
   - Add retry decorator or manual retry loop (3 attempts with exponential backoff)
   - Log detailed error information (timestamp, symbol, article title, error message) to a file or database
   - On final failure after retries, return error TOON with detailed reason rather than silent neutral default
   - Consider fallback to a simpler model if primary model fails repeatedly

**File**: `agents/learning_agent.py`

**Function**: `LearningAgent.evaluate_and_store()`

**Specific Changes**:

6. **Sentiment Validation Mechanism**: Add method to track EventAgent prediction accuracy
   - Create new method `track_sentiment_accuracy(symbol, predicted_sentiment, predicted_confidence, trade_entry_time, trade_exit_time)`
   - Fetch actual price movement during the trade period using PriceService
   - Calculate actual_direction = "bullish" if price increased, "bearish" if decreased
   - Compare predicted_sentiment direction with actual_direction
   - Store validation results in a new table or extend TradePattern table with sentiment_accuracy field
   - Calculate rolling accuracy metrics per symbol and market regime

7. **Feedback Loop to EventAgent**: Create mechanism to provide accuracy feedback
   - Add method `get_event_agent_performance(market_regime)` that returns historical sentiment accuracy
   - This data can be used to adjust confidence thresholds or provide context to the LLM in future prompts
   - Store feedback in a format that can be queried: {"regime": "earnings", "sentiment_accuracy": 0.72, "sample_size": 45}

**File**: `agents/fusion_agent.py`

**Function**: `FusionAgent.synthesize()`

**Specific Changes**:

8. **Confidence-Aware Weighting**: Modify fusion logic to incorporate confidence scores
   - Parse the new confidence_score field from event_toon
   - Adjust event weight dynamically: `effective_event_weight = base_event_weight * confidence_score`
   - If confidence is low (<0.5), reduce the event signal's influence on the final decision
   - Update the explanation string to include confidence information: "Event confidence: 0.82"

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code by running tests that expose the seven defects, then verify the fix works correctly by validating confidence-weighted aggregation, validation mechanisms, and preservation of existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate various news scenarios and assert that the EventAgent exhibits the defective behaviors. Run these tests on the UNFIXED code to observe failures and understand the root causes.

**Test Cases**:
1. **Hardcoded Score Test**: Provide news with "bullish" keyword → Assert that event_score is exactly 0.8 regardless of context → Verify no confidence_score field exists in output (will pass on unfixed code, confirming defect)
2. **Single Article Test**: Provide 3 high-impact articles (2 bullish, 1 bearish) → Assert that only 1 article is analyzed → Verify event_score doesn't reflect the mixed sentiment (will pass on unfixed code, confirming defect)
3. **No Validation Test**: Check if any validation mechanism exists in LearningAgent → Assert that no sentiment accuracy tracking exists (will pass on unfixed code, confirming defect)
4. **No Confidence Output Test**: Parse event_toon output → Assert that confidence_score field is missing (will pass on unfixed code, confirming defect)
5. **Silent Failure Test**: Mock LLM to raise exception → Assert that event_score returns 0.5 with no retry attempted → Verify no detailed error logging (will pass on unfixed code, confirming defect)
6. **No Feedback Test**: Execute a trade based on event analysis → Assert that LearningAgent receives no sentiment accuracy data (will pass on unfixed code, confirming defect)
7. **Keyword Limitation Test**: Provide nuanced news "Earnings beat but guidance lowered" → Assert that sentiment is purely bullish due to "beat" keyword → Verify conditional logic is ignored (will pass on unfixed code, confirming defect)

**Expected Counterexamples**:
- Event scores are hardcoded 0.2, 0.5, or 0.8 based on keyword matching
- Only first article is analyzed when multiple high-impact articles exist
- No validation infrastructure exists to track sentiment prediction accuracy
- TOON output lacks confidence_score and impact_magnitude fields
- LLM failures result in silent neutral defaults without retry
- LearningAgent has no mechanism to receive sentiment accuracy feedback
- Nuanced sentiment with conditional logic is reduced to simple keyword matching

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := EventAgent.analyze_news_fixed(input.news_list)
  
  // Verify confidence-weighted multi-article aggregation
  IF input.high_impact_articles.length > 1 THEN
    ASSERT result.analyzed_articles.length == input.high_impact_articles.length
    ASSERT result.event_score == confidence_weighted_average(input.high_impact_articles)
  END IF
  
  // Verify confidence and impact fields exist
  ASSERT result.confidence_score IS NOT NULL
  ASSERT result.impact_magnitude IS NOT NULL
  ASSERT result.confidence_score BETWEEN 0.0 AND 1.0
  ASSERT result.impact_magnitude BETWEEN 0.0 AND 1.0
  
  // Verify no hardcoded scores
  ASSERT result.event_score NOT IN [0.2, 0.5, 0.8] OR result.has_reasoning == TRUE
  
  // Verify retry logic on failure
  IF input.llm_extraction_fails THEN
    ASSERT result.retry_count > 0
    ASSERT result.error_logged == TRUE
  END IF
  
  // Verify validation mechanism exists
  ASSERT LearningAgent.track_sentiment_accuracy_method_exists == TRUE
  
  // Verify feedback loop exists
  ASSERT LearningAgent.get_event_agent_performance_method_exists == TRUE
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  result_original := EventAgent.analyze_news_original(input.news_list)
  result_fixed := EventAgent.analyze_news_fixed(input.news_list)
  
  // Verify TOON format compatibility
  ASSERT result_fixed.contains_field("event_score")
  ASSERT result_fixed.event_score BETWEEN 0.0 AND 1.0
  ASSERT result_fixed.format == "key: value\n" format
  
  // Verify method signature unchanged
  ASSERT EventAgent.analyze_news_signature == "List[NewsData] -> str"
  
  // Verify low-impact news handling unchanged
  IF input.all_news_low_impact THEN
    ASSERT result_fixed.event_score == 0.0
    ASSERT result_fixed.impact == "neutral"
  END IF
  
  // Verify empty news handling unchanged
  IF input.news_list.length == 0 THEN
    ASSERT result_fixed == "event_score: 0.0\nevent_type: none\nimpact: neutral\nreason: no news available\n"
  END IF
  
  // Verify FusionAgent can still parse output
  ASSERT FusionAgent._parse_toon(result_fixed).contains_key("event_score")
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (empty lists, single articles, low-impact news, various TOON formats)
- It catches edge cases that manual unit tests might miss (unusual news content, edge case scores, malformed LLM responses)
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for low-impact news, empty news lists, and TOON format parsing, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Low-Impact News Preservation**: Observe that low-impact news returns neutral sentiment on unfixed code → Write test to verify this continues after fix with same event_score and reason
2. **Empty News Preservation**: Observe that empty news list returns specific TOON string on unfixed code → Write test to verify exact string match after fix
3. **TOON Format Preservation**: Observe that FusionAgent successfully parses event_toon on unfixed code → Write test to verify parsing continues to work after fix with new fields being optional
4. **Score Scale Preservation**: Observe that event_score is always 0.0-1.0 on unfixed code → Write test to verify this constraint holds after fix
5. **Method Signature Preservation**: Observe that analyze_news accepts List[NewsData] and returns str on unfixed code → Write test to verify signature unchanged after fix

### Unit Tests

- Test enhanced LLM prompt returns confidence and impact fields in expected format
- Test multi-article aggregation with 2, 3, and 5 high-impact articles
- Test confidence-weighted averaging calculation with various confidence and impact values
- Test retry logic with mocked LLM failures (1 retry, 2 retries, 3 retries exhausted)
- Test error logging captures detailed failure information
- Test sentiment validation mechanism correctly identifies prediction accuracy
- Test feedback loop provides accurate performance metrics to learning agent
- Test TOON output includes all required fields (event_score, confidence_score, impact_magnitude, event_type, impact, reason)
- Test backward compatibility with FusionAgent parsing both old and new TOON formats

### Property-Based Tests

- Generate random news lists (0-10 articles, varying impact levels) and verify event_score is always 0.0-1.0
- Generate random LLM responses with confidence and impact values and verify aggregation formula correctness
- Generate random failure scenarios (timeouts, malformed responses, API errors) and verify retry logic and error handling
- Generate random trade outcomes and verify sentiment validation correctly calculates accuracy
- Test that TOON format is always parseable by FusionAgent across many random scenarios

### Integration Tests

- Test full workflow: fetch news → triage → multi-article extraction → aggregation → TOON output → fusion → trade
- Test that confidence scores influence fusion weighting correctly in various market regimes
- Test that sentiment validation tracks accuracy over multiple trades and provides feedback
- Test that learning agent receives and stores sentiment accuracy data
- Test that retry logic works in production-like scenarios with real LLM API calls
- Test that enhanced error handling provides actionable debugging information when failures occur
