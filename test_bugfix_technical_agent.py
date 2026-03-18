"""
Bug Condition Exploration Tests: TechnicalAgent (Bugs 1.1-1.5)

CRITICAL: These tests MUST FAIL on unfixed code.
Failure confirms the bugs exist. DO NOT fix the code when tests fail.
"""
import math
from datetime import datetime, timedelta
from data.schema import PriceData
from agents.technical_agent import TechnicalAgent


def make_price_history(n=60, close=100.0, volume=1000, all_same=False):
    """Helper: generate n PriceData points."""
    base = datetime(2024, 1, 1)
    prices = []
    for i in range(n):
        c = close if all_same else close + (i % 5) - 2  # slight variation
        prices.append(PriceData(
            open=c, high=c + 1, low=c - 1, close=c,
            volume=volume,
            timestamp=base + timedelta(days=i)
        ))
    return prices


def test_bug_1_1_rsi_zero_division():
    """
    Bug 1.1: RSI calculation crashes with ZeroDivisionError when all gains/losses are zero.
    Trigger: flat price history where delta is always 0 → gain=0, loss=0 → rs = 0/0
    FIXED behavior: analyze() detects flat prices and returns a clean error/neutral state
    without crashing or propagating NaN into downstream logic.
    """
    print("\n[Bug 1.1] RSI zero division on flat price history...")
    prices = make_price_history(n=60, close=100.0, all_same=True)
    # Fixed code must not raise ZeroDivisionError and must not silently return NaN score
    result = TechnicalAgent.analyze(prices)
    print(f"  Result: {result}")
    score = result.get("technical_score")
    reason = result.get("reason", "")
    # The fix must either: (a) return a clean error state with NaN/invalid in reason,
    # OR (b) return a valid numeric score (not NaN/inf) — either way no crash and no NaN score
    assert score is not None, "BUG 1.1 CONFIRMED: analyze() returned no score"
    assert not math.isnan(float(score)), \
        f"BUG 1.1 CONFIRMED: technical_score is NaN on flat price history (score={score})"
    print(f"  UNEXPECTED PASS: flat prices handled cleanly, score={score}, reason='{reason}'")


def test_bug_1_2_nan_propagation():
    """
    Bug 1.2: NaN RSI propagates to downstream without validation.
    Trigger: price history with no variation → RSI=NaN → used in comparisons
    EXPECTED: NaN comparison silently evaluates to False (wrong momentum classification)
    FIXED behavior: detect NaN and return error state
    """
    print("\n[Bug 1.2] NaN RSI propagation to decision logic...")
    prices = make_price_history(n=60, close=100.0, all_same=True)
    result = TechnicalAgent.analyze(prices)
    print(f"  Result: {result}")
    # On unfixed code, RSI=NaN, comparison `NaN > 60` is False, `NaN < 40` is False
    # so momentum defaults to "neutral" silently - no error raised, wrong result
    # The bug is that no error/warning is returned when RSI is invalid
    reason = result.get("reason", "")
    assert "nan" in reason.lower() or "invalid" in reason.lower() or "error" in reason.lower(), \
        f"BUG 1.2 CONFIRMED: NaN RSI not detected/reported. reason='{reason}'"
    print("  UNEXPECTED: NaN detected and reported - bug may be fixed")


def test_bug_1_3_all_zero_prices():
    """
    Bug 1.3: All-zero price history causes incorrect EMA/RSI calculations.
    Trigger: price_history with close=0 for all points
    EXPECTED: EMA=0, RSI=NaN or 50, score calculation produces wrong result
    FIXED behavior: validate input and return error state
    """
    print("\n[Bug 1.3] All-zero close prices...")
    prices = make_price_history(n=60, close=0.0, all_same=True)
    result = TechnicalAgent.analyze(prices)
    print(f"  Result: {result}")
    reason = result.get("reason", "")
    assert "zero" in reason.lower() or "invalid" in reason.lower() or "error" in reason.lower(), \
        f"BUG 1.3 CONFIRMED: All-zero prices not detected. reason='{reason}'"
    print("  UNEXPECTED: Zero prices detected - bug may be fixed")


def test_bug_1_4_zero_volume_nan():
    """
    Bug 1.4: Zero volume causes NaN in volume trend (Vol_5/Vol_20 = 0/0).
    Trigger: all volume=0 → Vol_5=0, Vol_20=0 → comparison 0 > 0 is False (silent wrong result)
    EXPECTED: volume comparison silently wrong, no warning
    FIXED behavior: detect zero volume and skip volume scoring with warning
    """
    print("\n[Bug 1.4] Zero volume in price history...")
    prices = make_price_history(n=60, close=100.0, volume=0)
    result = TechnicalAgent.analyze(prices)
    print(f"  Result: {result}")
    reason = result.get("reason", "")
    assert "volume" in reason.lower() and ("unavailable" in reason.lower() or "zero" in reason.lower() or "warn" in reason.lower()), \
        f"BUG 1.4 CONFIRMED: Zero volume not handled. reason='{reason}'"
    print("  UNEXPECTED: Zero volume handled - bug may be fixed")


def test_bug_1_5_nan_indicator_bounds():
    """
    Bug 1.5: NaN indicators used in comparisons without bounds checking.
    Trigger: flat prices → RSI=NaN → `if NaN > 60` evaluates to False silently
    EXPECTED: wrong momentum classification with no error
    FIXED behavior: validate indicators before use, return error if invalid
    """
    print("\n[Bug 1.5] NaN indicator used in comparison without bounds check...")
    prices = make_price_history(n=60, close=100.0, all_same=True)
    result = TechnicalAgent.analyze(prices)
    print(f"  Result: {result}")
    # On unfixed code: momentum="neutral" even though RSI is NaN (invalid)
    # The fix should detect NaN and return an error state, not silently use NaN
    momentum = result.get("momentum", "")
    reason = result.get("reason", "")
    # If momentum is "neutral" but RSI is NaN, that's the bug
    import pandas as pd
    df = pd.DataFrame([p.model_dump() for p in prices])
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi_series = 100 - (100 / (1 + rs))
    latest_rsi = rsi_series.iloc[-1]
    if math.isnan(latest_rsi):
        assert "error" in reason.lower() or "invalid" in reason.lower() or "nan" in reason.lower(), \
            f"BUG 1.5 CONFIRMED: NaN RSI ({latest_rsi}) used in logic without bounds check. momentum='{momentum}', reason='{reason}'"
    print("  UNEXPECTED: Bounds check present - bug may be fixed")


def run():
    """Run all TechnicalAgent bug condition exploration tests."""
    print("=" * 60)
    print("TechnicalAgent Bug Condition Exploration Tests (Bugs 1.1-1.5)")
    print("EXPECTED: Tests FAIL (confirms bugs exist)")
    print("=" * 60)

    tests = [
        test_bug_1_1_rsi_zero_division,
        test_bug_1_2_nan_propagation,
        test_bug_1_3_all_zero_prices,
        test_bug_1_4_zero_volume_nan,
        test_bug_1_5_nan_indicator_bounds,
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
