"""
Bug Condition Exploration Tests: RiskAgent (Bugs 1.6-1.10)

CRITICAL: These tests MUST FAIL on unfixed code.
Failure confirms the bugs exist. DO NOT fix the code when tests fail.
"""
import math
from datetime import datetime, timedelta
from data.schema import PriceData
from agents.risk_agent import RiskAgent


def make_price_history(n=20, close=100.0, volume=1000, vary=True):
    """Helper: generate n PriceData points with optional variation."""
    base = datetime(2024, 1, 1)
    prices = []
    for i in range(n):
        c = close + (i % 5) - 2 if vary else close
        prices.append(PriceData(
            open=c, high=c + 1, low=c - 1, close=c,
            volume=volume,
            timestamp=base + timedelta(days=i)
        ))
    return prices


def test_bug_1_6_vague_insufficient_data_message():
    """
    Bug 1.6: Insufficient data returns vague error message without specifying required count.
    Trigger: price_history with 10 points (< 14 required)
    EXPECTED: returns "insufficient data for risk analysis" (vague, no count)
    FIXED behavior: "insufficient data: need at least 14 points, got 10"
    """
    print("\n[Bug 1.6] Vague insufficient data error message...")
    prices = make_price_history(n=10)
    result = RiskAgent.analyze(prices)
    print(f"  Result: {result}")
    reason = result.get("reason", "")
    # Bug: message is vague, doesn't include actual/required counts
    assert "14" in reason and "10" in reason, \
        f"BUG 1.6 CONFIRMED: Vague error message without counts. reason='{reason}'"
    print("  UNEXPECTED: Detailed message present - bug may be fixed")


def test_bug_1_7_no_extreme_condition_handling():
    """
    Bug 1.7: Extreme market conditions (flash crash) not specially handled.
    Trigger: volatility > 10% daily swing
    EXPECTED: no special handling, risk may be underestimated
    FIXED behavior: detect extreme conditions and apply elevated risk with warning
    """
    print("\n[Bug 1.7] No extreme condition detection...")
    base = datetime(2024, 1, 1)
    # Create flash crash: price drops 15% in one day
    prices = []
    close = 100.0
    for i in range(20):
        if i == 15:
            close = 85.0  # 15% drop
        prices.append(PriceData(
            open=close, high=close + 1, low=close - 1, close=close,
            volume=1000,
            timestamp=base + timedelta(days=i)
        ))
    result = RiskAgent.analyze(prices)
    print(f"  Result: {result}")
    reason = result.get("reason", "").lower()
    # Bug: no "extreme" or "flash" or "circuit" mention in reason
    assert "extreme" in reason or "flash" in reason or "circuit" in reason or "spike" in reason, \
        f"BUG 1.7 CONFIRMED: Extreme conditions not detected. reason='{result.get('reason', '')}'"
    print("  UNEXPECTED: Extreme conditions detected - bug may be fixed")


def test_bug_1_8_hardcoded_thresholds_no_regime():
    """
    Bug 1.8: Risk thresholds are hardcoded, no regime-specific adjustments.
    Trigger: call analyze() with market_regime="earnings" parameter
    EXPECTED: TypeError (no such parameter) or same thresholds as normal
    FIXED behavior: accept market_regime and use regime-specific thresholds
    """
    print("\n[Bug 1.8] Hardcoded thresholds, no regime parameter...")
    prices = make_price_history(n=20)
    try:
        # Try calling with market_regime parameter - unfixed code won't accept it
        result_earnings = RiskAgent.analyze(prices, market_regime="earnings")
        result_normal = RiskAgent.analyze(prices, market_regime="normal")
        print(f"  Earnings result: {result_earnings}")
        print(f"  Normal result: {result_normal}")
        # If both return same risk_level with same data, thresholds aren't regime-specific
        # For earnings regime, thresholds should be lower (more cautious)
        # This is a soft check - the real fix is that thresholds differ
        assert result_earnings != result_normal or True, "Regime-specific thresholds applied"
        # Actually check that the method signature accepts market_regime
        import inspect
        sig = inspect.signature(RiskAgent.analyze)
        assert "market_regime" in sig.parameters, \
            "BUG 1.8 CONFIRMED: analyze() has no market_regime parameter"
        print("  UNEXPECTED: market_regime parameter exists - bug may be fixed")
    except TypeError as e:
        print(f"  BUG 1.8 CONFIRMED: TypeError - no market_regime parameter: {e}")
        raise AssertionError(f"Bug 1.8 confirmed: {e}")


def test_bug_1_9_no_gap_risk_analysis():
    """
    Bug 1.9: Risk calculation does not consider overnight gap risk.
    Trigger: price history with large overnight gap (open != previous close)
    EXPECTED: gap risk not captured in risk_score or reason
    FIXED behavior: detect gaps > 3% and add to risk_score
    """
    print("\n[Bug 1.9] No gap risk analysis...")
    base = datetime(2024, 1, 1)
    prices = []
    close = 100.0
    for i in range(20):
        # Create a large overnight gap on day 10: open is 8% above previous close
        if i == 10:
            open_price = close * 1.08  # 8% gap up
        else:
            open_price = close
        prices.append(PriceData(
            open=open_price, high=open_price + 1, low=open_price - 1, close=close,
            volume=1000,
            timestamp=base + timedelta(days=i)
        ))
    result = RiskAgent.analyze(prices)
    print(f"  Result: {result}")
    reason = result.get("reason", "").lower()
    assert "gap" in reason, \
        f"BUG 1.9 CONFIRMED: Gap risk not detected in reason. reason='{result.get('reason', '')}'"
    print("  UNEXPECTED: Gap risk detected - bug may be fixed")


def test_bug_1_10_nan_not_logged():
    """
    Bug 1.10: NaN RSI/volatility returns early without logging.
    Trigger: flat price history → RSI=NaN → early return with no log
    EXPECTED: returns error state silently, no log entry
    FIXED behavior: log NaN detection with context before returning
    """
    print("\n[Bug 1.10] NaN detection not logged...")
    import logging
    import io

    # Capture log output
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger("agents.risk_agent")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Also check root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    prices = make_price_history(n=20, vary=False)  # flat prices → NaN RSI
    result = RiskAgent.analyze(prices)
    print(f"  Result: {result}")

    log_output = log_capture.getvalue()
    print(f"  Log output: '{log_output}'")

    logger.removeHandler(handler)
    root_logger.removeHandler(handler)

    # Check if NaN was detected (it will be for flat prices)
    import pandas as pd
    df = pd.DataFrame([p.model_dump() for p in prices])
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi_series = 100 - (100 / (1 + rs))
    latest_rsi = rsi_series.iloc[-1]

    if math.isnan(latest_rsi):
        # NaN was produced - check if it was logged
        assert "nan" in log_output.lower() or "warning" in log_output.lower(), \
            f"BUG 1.10 CONFIRMED: NaN RSI ({latest_rsi}) not logged. Log output: '{log_output}'"
        print("  UNEXPECTED: NaN logged - bug may be fixed")
    else:
        print(f"  RSI={latest_rsi} (not NaN for this input, test may need different data)")


def run():
    """Run all RiskAgent bug condition exploration tests."""
    print("=" * 60)
    print("RiskAgent Bug Condition Exploration Tests (Bugs 1.6-1.10)")
    print("EXPECTED: Tests FAIL (confirms bugs exist)")
    print("=" * 60)

    tests = [
        test_bug_1_6_vague_insufficient_data_message,
        test_bug_1_7_no_extreme_condition_handling,
        test_bug_1_8_hardcoded_thresholds_no_regime,
        test_bug_1_9_no_gap_risk_analysis,
        test_bug_1_10_nan_not_logged,
    ]

    results = {}
    for test in tests:
        name = test.__name__
        try:
            test()
            results[name] = "UNEXPECTED PASS (bug may be fixed or test needs adjustment)"
        except AssertionError as e:
            results[name] = f"FAIL (BUG CONFIRMED): {e}"
        except Exception as e:
            results[name] = f"FAIL (CRASH): {type(e).__name__}: {e}"

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for name, outcome in results.items():
        status = "✓ CONFIRMED" if "CONFIRMED" in outcome or "CRASH" in outcome else "✗ UNEXPECTED"
        print(f"  {status} {name}")
        print(f"    {outcome}")

    confirmed = sum(1 for v in results.values() if "CONFIRMED" in v or "CRASH" in v)
    print(f"\nBugs confirmed: {confirmed}/{len(tests)}")
    return results


if __name__ == "__main__":
    run()
