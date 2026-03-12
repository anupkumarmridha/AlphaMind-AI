# Bugfix Requirements Document

## Introduction

The EventAgent's news sentiment analysis produces inaccurate sentiment classifications due to overly simplistic keyword-based scoring, single-article analysis, and lack of validation mechanisms. This leads to poor trading decisions as the system cannot accurately assess the true market impact of news events. The bug affects all news-driven trading decisions and prevents the learning agent from improving event analysis accuracy over time.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the LLM extraction returns "bullish" or "bearish" keywords THEN the system assigns hardcoded scores (0.8 for bullish, 0.2 for bearish, 0.5 default) without considering confidence levels or impact magnitude

1.2 WHEN multiple high-impact news articles are identified during triage THEN the system only analyzes the first article and ignores all subsequent high-impact news

1.3 WHEN the EventAgent produces sentiment classifications THEN the system has no mechanism to validate accuracy or track prediction performance

1.4 WHEN sentiment predictions are made THEN the system provides no confidence scores or uncertainty quantification to downstream agents

1.5 WHEN the LLM extraction fails or returns errors THEN the system falls back to neutral sentiment (0.5) potentially missing critical market-moving information

1.6 WHEN trades are executed based on event analysis THEN the learning agent receives no feedback about sentiment accuracy to improve future predictions

1.7 WHEN news contains nuanced sentiment (mixed signals, conditional statements, or context-dependent impact) THEN the simple keyword matching fails to capture the true sentiment complexity

### Expected Behavior (Correct)

2.1 WHEN the LLM extraction returns sentiment analysis THEN the system SHALL extract and use confidence scores and impact magnitude from the LLM output to compute weighted sentiment scores

2.2 WHEN multiple high-impact news articles are identified during triage THEN the system SHALL analyze all high-impact articles and aggregate their sentiment scores using confidence-weighted averaging

2.3 WHEN the EventAgent produces sentiment classifications THEN the system SHALL implement a validation mechanism that tracks prediction accuracy against actual market movements

2.4 WHEN sentiment predictions are made THEN the system SHALL provide confidence scores and uncertainty quantification in the TOON output for downstream fusion logic

2.5 WHEN the LLM extraction fails or returns errors THEN the system SHALL implement retry logic with fallback models and log failures for analysis rather than silently defaulting to neutral

2.6 WHEN trades are executed based on event analysis THEN the system SHALL provide sentiment accuracy feedback to the learning agent to enable continuous improvement of event analysis

2.7 WHEN news contains nuanced sentiment THEN the system SHALL use the LLM's full reasoning capabilities to extract sentiment with context and conditional logic rather than simple keyword matching

### Unchanged Behavior (Regression Prevention)

3.1 WHEN news articles are triaged for impact level THEN the system SHALL CONTINUE TO use the two-stage LLM approach (triage + deep extraction) with the kimi-k2.5:cloud model

3.2 WHEN no news is available for analysis THEN the system SHALL CONTINUE TO return neutral sentiment with appropriate reason in TOON format

3.3 WHEN the EventAgent returns analysis results THEN the system SHALL CONTINUE TO use TOON format for inter-agent communication

3.4 WHEN low-impact news is detected during triage THEN the system SHALL CONTINUE TO skip deep extraction and return neutral sentiment

3.5 WHEN the EventAgent is called by the LangGraph workflow THEN the system SHALL CONTINUE TO accept List[NewsData] as input and return TOON formatted strings as output

3.6 WHEN event_score is computed THEN the system SHALL CONTINUE TO use the 0.0 to 1.0 scale where 0.5 is neutral, values above 0.5 are bullish, and values below 0.5 are bearish

3.7 WHEN the FusionAgent processes event_toon output THEN the system SHALL CONTINUE TO parse the event_score field and use it in regime-dependent weighting calculations
