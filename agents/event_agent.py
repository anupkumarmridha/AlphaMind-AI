import os
from typing import Any, Dict, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from data.schema import NewsData

TRIAGE_PROMPT = """
You are a financial news triage router.
Determine if the following news article is high impact (earnings, mergers, major product launches, regulatory issues) or low impact/irrelevant.
Return ONLY "HIGH" or "LOW".

Title: {title}
Content: {content}
"""

DEEP_EXTRACT_PROMPT = """
Extract using compact Token-Optimized Object Notation (TOON). Do NOT use braces or quotes.
Format strictly as follows:
event_type: earnings/deal/risk/product/other
numbers: <any financial numbers or none>
impact: bullish/bearish/neutral
reason: <short 1 sentence reason>

Title: {title}
Content: {content}
"""

class EventAgent:
    def __init__(self):
        # Using Local Ollama
        # We will use llama3 as the default, but you can change this to any installed model
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Fast model for Triage
        self.triage_llm = ChatOllama(
            model="kimi-k2.5:cloud", 
            temperature=0.0,
            base_url=ollama_base_url
        )
        
        # Heavy model for deep extraction
        self.extract_llm = ChatOllama(
            model="kimi-k2.5:cloud", 
            temperature=0.0,
            base_url=ollama_base_url
        )
        
        self.triage_prompt = PromptTemplate.from_template(TRIAGE_PROMPT)
        self.extract_prompt = PromptTemplate.from_template(DEEP_EXTRACT_PROMPT)

    @staticmethod
    def _parse_toon(toon: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for line in toon.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
        return data

    @staticmethod
    def to_toon(payload: Dict[str, Any]) -> str:
        return (
            f"event_score: {payload.get('event_score', 0.0)}\n"
            f"event_type: {payload.get('event_type', 'other')}\n"
            f"impact: {payload.get('impact', 'neutral')}\n"
            f"reason: {payload.get('reason', '')}\n"
        )

    def analyze(self, news_list: List[NewsData]) -> Dict[str, Any]:
        """
        Analyzes a list of news articles and returns structured event data.
        """
        if not news_list:
            return {
                "event_score": 0.0,
                "event_type": "none",
                "impact": "neutral",
                "reason": "no news available",
            }

        high_impact_news = []
        
        # 1. Triage
        for news in news_list:
            triage_chain = self.triage_prompt | self.triage_llm
            try:
                triage_result = triage_chain.invoke({"title": news.title, "content": news.content}).content.strip().upper()
                if "HIGH" in triage_result:
                    high_impact_news.append(news)
            except Exception as e:
                # Fallback on API errors: assume high impact just to be safe
                print(f"Triage error: {e}")
                high_impact_news.append(news)
                
        if not high_impact_news:
            return {
                "event_score": 0.0,
                "event_type": "low_impact",
                "impact": "neutral",
                "reason": "only low impact news detected",
            }

        # 2. Deep Extract (just taking the most recent high impact news for the final score, or combining them)
        # For simplicity, we summarize the first high impact one to present the TOON output format.
        # A more advanced version would run a map-reduce over all high impact news.
        top_news = high_impact_news[0]
        
        extract_chain = self.extract_prompt | self.extract_llm
        try:
            extraction_result = extract_chain.invoke({"title": top_news.title, "content": top_news.content}).content.strip()
            parsed = self._parse_toon(extraction_result)

            # Since the LLM returns TOON, infer event score from impact.
            event_score = 0.5
            impact = str(parsed.get("impact", "neutral")).lower()
            if impact == "bullish":
                event_score = 0.8
            elif impact == "bearish":
                event_score = 0.2

            return {
                "event_score": round(event_score, 2),
                "event_type": parsed.get("event_type", "other"),
                "impact": parsed.get("impact", "neutral"),
                "reason": parsed.get("reason", "no reason provided"),
            }
            
        except Exception as e:
            return {
                "event_score": 0.0,
                "event_type": "error",
                "impact": "neutral",
                "reason": f"LLM extraction failed: {str(e)}",
            }

    def analyze_news(self, news_list: List[NewsData]) -> str:
        """
        Backward-compatible TOON output helper.
        """
        return self.to_toon(self.analyze(news_list))
