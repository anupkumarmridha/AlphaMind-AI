from agents.fusion_agent import FusionAgent

def run():
    tech_toon = "technical_score: 0.8\ntrend: bullish\nmomentum: strong\nreason: EMA20 > EMA50, RSI=65"
    event_toon = "event_score: 0.9\nevent_type: earnings\nimpact: bullish\nreason: strong revenue guidance"
    risk_toon = "risk_score: 0.2\nrisk_level: LOW\nreason: normal conditions"
    
    # Test during normal regime
    decision_normal = FusionAgent.synthesize(tech_toon, event_toon, risk_toon, market_regime="normal")
    print("NORMAL REGIME DECISION:\n", decision_normal)

    # Test during earnings regime
    decision_earnings = FusionAgent.synthesize(tech_toon, event_toon, risk_toon, market_regime="earnings")
    print("\nEARNINGS REGIME DECISION:\n", decision_earnings)

    # Test HR Veto
    risk_toon_critical = "risk_score: 0.9\nrisk_level: CRITICAL\nreason: Extreme volatility"
    decision_veto = FusionAgent.synthesize(tech_toon, event_toon, risk_toon_critical, market_regime="normal")
    print("\nCRITICAL RISK DECISION:\n", decision_veto)

if __name__ == "__main__":
    run()
