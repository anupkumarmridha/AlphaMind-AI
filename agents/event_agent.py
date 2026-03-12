import os
import time
import logging
from datetime import datetime
from typing import List, Callable, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from data.schema import NewsData

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use system environment variables

# Configure logging for error tracking
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"event_agent_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TRIAGE_PROMPT = """
You are a financial news triage router.
Determine if the following news article is high impact (earnings, mergers, major product launches, regulatory issues) or low impact/irrelevant.
Return ONLY "HIGH" or "LOW".

Title: {title}
Content: {content}
"""

DEEP_EXTRACT_PROMPT = """
Extract using compact Token-Optimized Object Notation (TOON). Do NOT use braces or quotes.

Analyze the news article with full context and reasoning. Consider the complete narrative, conditional statements, mixed signals, and market implications rather than just keywords.

Format strictly as follows:
event_type: earnings/deal/risk/product/other
numbers: <any financial numbers or none>
sentiment_score: <0.0-1.0 numeric value where 0.5 is neutral, >0.5 is bullish, <0.5 is bearish>
impact: bullish/bearish/neutral
confidence: <0.0-1.0 value indicating certainty in your sentiment classification>
impact_magnitude: <0.0-1.0 value indicating expected market impact strength>
reason: <short 1 sentence reason explaining your sentiment analysis>

Guidelines:
- sentiment_score: Provide a numeric score from 0.0 to 1.0 based on your full analysis. 0.5 = neutral, 0.0 = extremely bearish, 1.0 = extremely bullish. Use the full range to capture nuanced sentiment.
- confidence: How certain are you about the sentiment? 1.0 = very certain, 0.5 = uncertain, 0.0 = no basis for judgment
- impact_magnitude: How strong is the expected market impact? 1.0 = major market-moving event, 0.5 = moderate impact, 0.0 = minimal impact
- Consider nuanced sentiment: mixed signals, conditional statements, context-dependent implications
- Reason about the full context rather than relying on individual keywords
- The sentiment_score should reflect your complete analysis, not just simple keyword matching

Title: {title}
Content: {content}
"""

class EventAgent:
    def __init__(self):
        # Using local Ollama; models are configurable by environment variables.
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        default_model = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")
        triage_model = os.getenv("EVENT_TRIAGE_MODEL", default_model)
        extract_model = os.getenv("EVENT_EXTRACT_MODEL", default_model)
        fallback_model = os.getenv("EVENT_FALLBACK_MODEL", "llama3.2:latest")
        
        # Fast model for Triage
        self.triage_llm = ChatOllama(
            model=triage_model,
            temperature=0.0,
            base_url=ollama_base_url
        )
        
        # Heavy model for deep extraction
        self.extract_llm = ChatOllama(
            model=extract_model,
            temperature=0.0,
            base_url=ollama_base_url
        )
        
        # Fallback model for when primary model fails
        self.fallback_llm = ChatOllama(
            model=fallback_model,
            temperature=0.0,
            base_url=ollama_base_url
        )
        
        self.triage_prompt = PromptTemplate.from_template(TRIAGE_PROMPT)
        self.extract_prompt = PromptTemplate.from_template(DEEP_EXTRACT_PROMPT)
    
    def _retry_with_backoff(self, func: Callable, *args, max_retries: int = 3, 
                           initial_delay: float = 1.0, backoff_factor: float = 2.0,
                           context: str = "", **kwargs) -> Any:
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds (default: 1.0)
            backoff_factor: Multiplier for delay after each retry (default: 2.0)
            context: Context string for logging (e.g., article title)
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retries are exhausted
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1} for {context}")
                return result
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for {context}: "
                    f"{type(e).__name__}: {str(e)}"
                )
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    delay *= backoff_factor
        
        # All retries exhausted
        logger.error(
            f"All {max_retries} retry attempts exhausted for {context}. "
            f"Final error: {type(last_exception).__name__}: {str(last_exception)}"
        )
        raise last_exception

    def analyze_news(self, news_list: List[NewsData]) -> str:
        """
        Analyzes a list of news articles. Triages them, and deep extracts High-impact ones.
        Returns a TOON formatted string of events.
        """
        if not news_list:
            return "event_score: 0.0\nevent_type: none\nimpact: neutral\nconfidence_score: 0.0\nimpact_magnitude: 0.0\nreason: no news available\n"

        high_impact_news = []
        
        # 1. Triage with retry logic
        for news in news_list:
            triage_chain = self.triage_prompt | self.triage_llm
            try:
                triage_result = self._retry_with_backoff(
                    triage_chain.invoke,
                    {"title": news.title, "content": news.content},
                    context=f"triage for '{news.title[:50]}...'"
                )
                if "HIGH" in triage_result.content.strip().upper():
                    high_impact_news.append(news)
            except Exception as e:
                # Fallback on API errors: assume high impact just to be safe
                logger.error(
                    f"Triage failed after retries for article '{news.title}': "
                    f"{type(e).__name__}: {str(e)}. Assuming high impact."
                )
                high_impact_news.append(news)
                
        if not high_impact_news:
            return "event_score: 0.0\nevent_type: low_impact\nimpact: neutral\nconfidence_score: 0.0\nimpact_magnitude: 0.0\nreason: only low impact news detected\n"

        # 2. Deep Extract - analyze ALL high-impact articles and aggregate
        extract_chain = self.extract_prompt | self.extract_llm
        article_analyses = []
        failed_articles = []
        
        for news in high_impact_news:
            try:
                # Try primary model with retry
                extraction_result = self._retry_with_backoff(
                    extract_chain.invoke,
                    {"title": news.title, "content": news.content},
                    context=f"extraction for '{news.title[:50]}...'"
                )
                
                # Parse the TOON output to extract sentiment, confidence, and impact_magnitude
                parsed = self._parse_toon(extraction_result.content.strip())
                
                # Parse the LLM's numeric sentiment score directly (no keyword matching)
                sentiment_score = float(parsed.get("sentiment_score", 0.5))
                
                # Ensure sentiment_score is within valid range [0.0, 1.0]
                sentiment_score = max(0.0, min(1.0, sentiment_score))
                
                confidence = float(parsed.get("confidence", 0.5))
                impact_magnitude = float(parsed.get("impact_magnitude", 0.5))
                
                # Derive impact label from sentiment_score for backward compatibility
                impact_str = "bullish" if sentiment_score > 0.5 else ("bearish" if sentiment_score < 0.5 else "neutral")
                
                article_analyses.append({
                    "sentiment_score": sentiment_score,
                    "confidence": confidence,
                    "impact_magnitude": impact_magnitude,
                    "event_type": parsed.get("event_type", "other"),
                    "impact": impact_str,
                    "reason": parsed.get("reason", ""),
                    "numbers": parsed.get("numbers", "none")
                })
                
            except Exception as e:
                # Primary model failed after retries, try fallback model
                logger.warning(
                    f"Primary model failed for article '{news.title}'. "
                    f"Attempting fallback model..."
                )
                
                try:
                    fallback_chain = self.extract_prompt | self.fallback_llm
                    extraction_result = self._retry_with_backoff(
                        fallback_chain.invoke,
                        {"title": news.title, "content": news.content},
                        max_retries=2,  # Fewer retries for fallback
                        context=f"fallback extraction for '{news.title[:50]}...'"
                    )
                    
                    parsed = self._parse_toon(extraction_result.content.strip())
                    sentiment_score = max(0.0, min(1.0, float(parsed.get("sentiment_score", 0.5))))
                    confidence = float(parsed.get("confidence", 0.5))
                    impact_magnitude = float(parsed.get("impact_magnitude", 0.5))
                    impact_str = "bullish" if sentiment_score > 0.5 else ("bearish" if sentiment_score < 0.5 else "neutral")
                    
                    article_analyses.append({
                        "sentiment_score": sentiment_score,
                        "confidence": confidence * 0.8,  # Reduce confidence for fallback model
                        "impact_magnitude": impact_magnitude,
                        "event_type": parsed.get("event_type", "other"),
                        "impact": impact_str,
                        "reason": parsed.get("reason", "") + " (fallback model)",
                        "numbers": parsed.get("numbers", "none")
                    })
                    
                    logger.info(f"Fallback model succeeded for article '{news.title}'")
                    
                except Exception as fallback_error:
                    # Both primary and fallback failed
                    logger.error(
                        f"Both primary and fallback models failed for article '{news.title}': "
                        f"Primary: {type(e).__name__}: {str(e)}, "
                        f"Fallback: {type(fallback_error).__name__}: {str(fallback_error)}"
                    )
                    failed_articles.append({
                        "title": news.title,
                        "primary_error": f"{type(e).__name__}: {str(e)}",
                        "fallback_error": f"{type(fallback_error).__name__}: {str(fallback_error)}"
                    })
                    continue
        
        # Handle case where all extractions failed
        if not article_analyses:
            error_details = "; ".join([
                f"{fa['title'][:30]}: {fa['primary_error']}" 
                for fa in failed_articles[:3]  # Limit to first 3 for brevity
            ])
            logger.error(
                f"All LLM extractions failed for {len(failed_articles)} articles. "
                f"Details: {error_details}"
            )
            return (
                f"event_score: 0.0\n"
                f"event_type: error\n"
                f"impact: neutral\n"
                f"confidence_score: 0.0\n"
                f"impact_magnitude: 0.0\n"
                f"reason: All LLM extractions failed after retries ({len(failed_articles)} articles). "
                f"Check logs for details.\n"
            )
        
        # Log partial failures
        if failed_articles:
            logger.warning(
                f"Partial extraction failure: {len(failed_articles)} of {len(high_impact_news)} "
                f"articles failed. Proceeding with {len(article_analyses)} successful extractions."
            )
        
        # 3. Aggregate using confidence-weighted averaging
        if len(article_analyses) == 1:
            # Single article - use its values directly
            analysis = article_analyses[0]
            final_score = analysis["sentiment_score"]
            final_confidence = analysis["confidence"]
            final_impact_magnitude = analysis["impact_magnitude"]
            final_event_type = analysis["event_type"]
            final_impact = analysis["impact"]
            final_reason = analysis["reason"]
        else:
            # Multiple articles - apply confidence-weighted averaging
            weighted_sum = 0.0
            weight_sum = 0.0
            confidence_sum = 0.0
            impact_magnitude_sum = 0.0
            
            for analysis in article_analyses:
                weight = analysis["confidence"] * analysis["impact_magnitude"]
                weighted_sum += analysis["sentiment_score"] * weight
                weight_sum += weight
                confidence_sum += analysis["confidence"] * weight
                impact_magnitude_sum += analysis["impact_magnitude"] * weight
            
            final_score = weighted_sum / weight_sum if weight_sum > 0 else 0.5
            final_confidence = confidence_sum / weight_sum if weight_sum > 0 else 0.5
            final_impact_magnitude = impact_magnitude_sum / weight_sum if weight_sum > 0 else 0.5
            
            # Use the most common event_type and impact
            final_event_type = article_analyses[0]["event_type"]
            final_impact = "bullish" if final_score > 0.5 else ("bearish" if final_score < 0.5 else "neutral")
            final_reason = f"Aggregated from {len(article_analyses)} high-impact articles"
            
            # Add note about partial failures if any
            if failed_articles:
                final_reason += f" ({len(failed_articles)} failed)"
        
        # 4. Build final TOON output
        final_toon = (
            f"event_score: {final_score:.2f}\n"
            f"event_type: {final_event_type}\n"
            f"impact: {final_impact}\n"
            f"confidence_score: {final_confidence:.2f}\n"
            f"impact_magnitude: {final_impact_magnitude:.2f}\n"
            f"reason: {final_reason}\n"
        )
        
        return final_toon
    
    def _parse_toon(self, toon_str: str) -> dict:
        """Parse TOON format string into a dictionary."""
        result = {}
        for line in toon_str.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        return result
