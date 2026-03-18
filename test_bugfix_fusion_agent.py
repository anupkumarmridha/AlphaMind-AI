"""
Bug Condition Exploration Tests: FusionAgent (Bugs 1.11-1.15)

CRITICAL: These tests MUST FAIL on unfixed code.
Failure confirms the bugs exist. DO NOT fix the code when tests fail.
"""
import logging
import io
from agents.fusion_agent import FusionAgent


VALID_TECH_TOON = "technical_score: 0.7\ntrend: bullish\nmomentum: strong\nreason: EMA20 > EMA50\n"
VALID_EVENT_TOON = "event_score: 0.6\nsentiment: bullish\nconfidence_score: 0.8\nreason: positive news\n"
VALID_RISK_TOON = "risk_score: 0.2\nrisk_level: LOW\nreason: Normal conditions\n"


def test_bug_1_11_parse_error_not_logged():
    """
    Bug 1.11: ValueError on TOON parsing silently defaults to 0 without logging.
    Trigger: technical_score = "N/A" → float("N/A") raises ValueError → caught silently
    EXPECTED: no log entry, silently defaults to 0
    FIXED behavior: log the parsing error with field name and value
    """
    print("\n[Bug 1.11] Parse error not logged...")
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Attach to all relevant loggers
    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.DEBUG)

    bad_tech_toon = "technical_score: N/A\ntrend: bullish\nmomentum: strong\nreason: test\n"
    result = FusionAgent.synthesize(bad_tech_toon, VALID_EVENT_TOON, VALID_RISK_TOON)
    print(f"  Result: {result}")

    log_output = log_capture.getvalue()
    print(f"  Log output: '{log_output}'")

    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        logging.getLogger(name).removeHandler(handler)

    assert "technical_score" in log_output.lower() or "n/a" in log_output.lower() or \
           "parse" in log_output.lower() or "failed" in log_output.lower(), \
        f"BUG 1.11 CONFIRMED: Parse error for 'N/A' not logged. Log: '{log_output}'"
    print("  UNEXPECTED: Parse error logged - bug may be fixed")


def test_bug_1_12_weights_not_validated_after_confidence():
    """
    Bug 1.12: After confidence adjustment, weights no longer sum to 1.0 and are not validated.
    Trigger: event_confidence=0.3 → effective_event_weight = 0.2 * 0.3 = 0.06
             total weights = 0.6 + 0.06 + 0.3 = 0.96 (not 1.0)
    EXPECTED: weights used without normalization, signal calculation skewed
    FIXED behavior: validate and normalize weights after confidence adjustment
    """
    print("\n[Bug 1.12] Weights not validated after confidence adjustment...")
    # Low confidence event → weight drops, total != 1.0
    low_conf_event_toon = "event_score: 0.6\nsentiment: bullish\nconfidence_score: 0.3\nreason: low confidence\n"
    result = FusionAgent.synthesize(VALID_TECH_TOON, low_conf_event_toon, VALID_RISK_TOON)
    print(f"  Result: {result}")

    # Manually compute what the weights should be (unfixed code)
    # normal regime: technical=0.5+0.1(context)=0.6, event=0.2*0.3=0.06, risk=0.3
    # total = 0.6 + 0.06 + 0.3 = 0.96 (not 1.0)
    # The bug: no normalization, signal is computed with weights summing to 0.96
    # We can't directly inspect internal weights, so we check via a log warning
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.WARNING)

    result2 = FusionAgent.synthesize(VALID_TECH_TOON, low_conf_event_toon, VALID_RISK_TOON)
    log_output = log_capture.getvalue()
    print(f"  Log output: '{log_output}'")

    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        logging.getLogger(name).removeHandler(handler)

    assert "normaliz" in log_output.lower() or "weight" in log_output.lower() or \
           "sum" in log_output.lower(), \
        f"BUG 1.12 CONFIRMED: Weight normalization not logged after confidence adjustment. Log: '{log_output}'"
    print("  UNEXPECTED: Weight normalization logged - bug may be fixed")


def test_bug_1_13_context_redistribution_not_documented():
    """
    Bug 1.13: Context weight redistributed to technical without documentation or validation.
    Trigger: normal synthesize call → context weight silently added to technical
    EXPECTED: no comment/documentation in code, no validation of redistribution
    FIXED behavior: documented with inline comment, weights validated after redistribution
    """
    print("\n[Bug 1.13] Context weight redistribution not documented/validated...")
    import inspect
    source = inspect.getsource(FusionAgent.synthesize)
    print(f"  Checking source for documentation of context redistribution...")
    # Bug: no comment explaining why context weight is redistributed
    has_comment = (
        "context agent not yet implemented" in source.lower() or
        "redistribute" in source.lower() or
        "mvp" in source.lower()
    )
    assert has_comment, \
        f"BUG 1.13 CONFIRMED: Context weight redistribution has no documentation comment"
    print("  UNEXPECTED: Documentation present - bug may be fixed")


def test_bug_1_14_missing_toon_fields_not_validated():
    """
    Bug 1.14: Missing/malformed TOON fields default silently without comprehensive validation.
    Trigger: risk_toon missing risk_level field → defaults to 'LOW' silently
    EXPECTED: no warning logged for missing field
    FIXED behavior: log warning for missing/malformed fields
    """
    print("\n[Bug 1.14] Missing TOON fields not validated with warnings...")
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.WARNING)

    # risk_toon missing risk_level field
    incomplete_risk_toon = "risk_score: 0.2\nreason: Normal conditions\n"
    result = FusionAgent.synthesize(VALID_TECH_TOON, VALID_EVENT_TOON, incomplete_risk_toon)
    print(f"  Result: {result}")

    log_output = log_capture.getvalue()
    print(f"  Log output: '{log_output}'")

    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        logging.getLogger(name).removeHandler(handler)

    assert "risk_level" in log_output.lower() or "missing" in log_output.lower() or \
           "warn" in log_output.lower(), \
        f"BUG 1.14 CONFIRMED: Missing 'risk_level' field not warned. Log: '{log_output}'"
    print("  UNEXPECTED: Missing field warned - bug may be fixed")


def test_bug_1_15_final_signal_not_bounds_checked():
    """
    Bug 1.15: final_signal not bounds-checked before use in decision logic.
    Trigger: extreme scores that could push final_signal outside [-1, 1]
    EXPECTED: final_signal used without clamping
    FIXED behavior: clamp final_signal to [-1, 1] and log if clamping occurred
    """
    print("\n[Bug 1.15] final_signal not bounds-checked...")
    # Construct scenario where signal could exceed bounds
    # tech_score=1.0 → tech_norm=1.0, event_score=1.0 → event_norm=1.0
    # normal: weights tech=0.6, event=0.2, risk=0.3
    # base_signal = 1.0*0.6 + 1.0*0.2 = 0.8
    # risk_score=0.0 → final_signal = max(0, 0.8 - 0) = 0.8 (within bounds here)
    # For earnings regime: tech=0.3+0.1=0.4, event=0.6, risk=0.4
    # base_signal = 1.0*0.4 + 1.0*0.6 = 1.0 → final_signal = 1.0 (at boundary)
    extreme_tech = "technical_score: 1.0\ntrend: bullish\nmomentum: strong\nreason: extreme\n"
    extreme_event = "event_score: 1.0\nsentiment: bullish\nconfidence_score: 1.0\nreason: extreme\n"
    low_risk = "risk_score: 0.0\nrisk_level: LOW\nreason: no risk\n"

    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.WARNING)

    result = FusionAgent.synthesize(extreme_tech, extreme_event, low_risk, market_regime="earnings")
    print(f"  Result: {result}")
    log_output = log_capture.getvalue()
    print(f"  Log output: '{log_output}'")

    for name in ["agents.fusion_agent", "fusion_agent", ""]:
        logging.getLogger(name).removeHandler(handler)

    confidence = result.get("confidence", 0)
    # Manually compute expected final_signal for earnings regime
    # tech=0.4, event=0.6*1.0=0.6, risk=0.4
    # base_signal = (1.0-0.5)*2*0.4 + (1.0-0.5)*2*0.6 = 0.4 + 0.6 = 1.0
    # final_signal = max(0, 1.0 - 0.0*0.4) = 1.0
    # confidence = abs(1.0) = 1.0 → this is at boundary, not exceeding
    # Let's verify the code doesn't clamp (no log warning for clamping)
    # The real bug is that there's NO clamping code at all
    import inspect
    source = inspect.getsource(FusionAgent.synthesize)
    has_clamp = "max(-1" in source or "min(1" in source or "clamp" in source.lower()
    assert has_clamp, \
        f"BUG 1.15 CONFIRMED: No bounds clamping of final_signal in synthesize()"
    print("  UNEXPECTED: Bounds clamping present - bug may be fixed")


def run():
    """Run all FusionAgent bug condition exploration tests."""
    print("=" * 60)
    print("FusionAgent Bug Condition Exploration Tests (Bugs 1.11-1.15)")
    print("EXPECTED: Tests FAIL (confirms bugs exist)")
    print("=" * 60)

    tests = [
        test_bug_1_11_parse_error_not_logged,
        test_bug_1_12_weights_not_validated_after_confidence,
        test_bug_1_13_context_redistribution_not_documented,
        test_bug_1_14_missing_toon_fields_not_validated,
        test_bug_1_15_final_signal_not_bounds_checked,
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
