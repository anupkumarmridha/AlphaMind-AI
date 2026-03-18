"""
Bug Condition Exploration Tests: TradeAgent (Bugs 1.16-1.20)

CRITICAL: These tests MUST FAIL on unfixed code.
Failure confirms the bugs exist. DO NOT fix the code when tests fail.
"""
import inspect
from agents.trade_agent import TradeAgent


def make_decision(decision="BUY", position_size=0.05):
    return {"decision": decision, "position_size": position_size, "confidence": 0.8,
            "reason": "test decision"}


def test_bug_1_16_no_position_limit_enforcement():
    """
    Bug 1.16: No maximum position limit check across all open trades.
    Trigger: open 6 trades each at 10% → total exposure = 60% (exceeds any reasonable limit)
    EXPECTED: all trades accepted, no limit enforcement
    FIXED behavior: reject trades that would exceed max_total_exposure (50%)
    """
    print("\n[Bug 1.16] No position limit enforcement...")
    agent = TradeAgent()
    # Open 6 trades at 10% each = 60% total exposure
    trades = []
    for i in range(6):
        t = agent.execute_trade(make_decision("BUY", 0.10), current_price=100.0, symbol="AAPL")
        if t is not None:
            trades.append(t)

    total_exposure = sum(t.position_size for t in agent.open_trades)
    print(f"  Open trades: {len(agent.open_trades)}, Total exposure: {total_exposure:.2%}")

    # Bug: all 6 trades accepted, total exposure = 60%
    assert total_exposure <= 0.50, \
        f"BUG 1.16 CONFIRMED: Total exposure {total_exposure:.2%} exceeds 50% limit. " \
        f"No position limit enforcement. {len(agent.open_trades)} trades open."
    print("  UNEXPECTED: Position limit enforced - bug may be fixed")


def test_bug_1_17_no_capital_check():
    """
    Bug 1.17: No capital availability check before trade execution.
    Trigger: TradeAgent has no account_balance parameter
    EXPECTED: trades execute without any capital check
    FIXED behavior: check capital availability, reject if insufficient
    """
    print("\n[Bug 1.17] No capital availability check...")
    sig = inspect.signature(TradeAgent.__init__)
    params = sig.parameters
    print(f"  TradeAgent.__init__ params: {list(params.keys())}")
    assert "account_balance" in params, \
        f"BUG 1.17 CONFIRMED: TradeAgent.__init__ has no 'account_balance' parameter. " \
        f"Params: {list(params.keys())}"
    print("  UNEXPECTED: account_balance parameter exists - bug may be fixed")


def test_bug_1_18_no_overnight_stop_adjustment():
    """
    Bug 1.18: Stop loss not adjusted for overnight/gap risk.
    Trigger: execute_trade() has no is_overnight parameter
    EXPECTED: same 2% stop loss regardless of market hours
    FIXED behavior: accept is_overnight=True and widen stops to 3%
    """
    print("\n[Bug 1.18] No overnight stop loss adjustment...")
    agent = TradeAgent()
    sig = inspect.signature(agent.execute_trade)
    params = sig.parameters
    print(f"  execute_trade params: {list(params.keys())}")
    assert "is_overnight" in params, \
        f"BUG 1.18 CONFIRMED: execute_trade() has no 'is_overnight' parameter. " \
        f"Params: {list(params.keys())}"
    print("  UNEXPECTED: is_overnight parameter exists - bug may be fixed")


def test_bug_1_19_no_partial_fill_handling():
    """
    Bug 1.19: No partial fill handling - position_size not updated on partial fills.
    Trigger: execute a trade and check Trade model for actual_fill_size field
    EXPECTED: Trade model has no actual_fill_size field
    FIXED behavior: Trade model has actual_fill_size, updated on partial fills
    """
    print("\n[Bug 1.19] No partial fill handling...")
    from models.trade import Trade
    agent = TradeAgent()
    trade = agent.execute_trade(make_decision("BUY", 0.05), current_price=100.0, symbol="AAPL")
    if trade is None:
        print("  Trade returned None (unexpected for valid BUY decision)")
        return

    print(f"  Trade fields: {list(trade.model_fields.keys())}")
    assert hasattr(trade, "actual_fill_size"), \
        f"BUG 1.19 CONFIRMED: Trade model has no 'actual_fill_size' field. " \
        f"Fields: {list(trade.model_fields.keys())}"
    print("  UNEXPECTED: actual_fill_size field exists - bug may be fixed")


def test_bug_1_20_no_position_size_validation():
    """
    Bug 1.20: Negative or invalid position_size not validated before trade execution.
    Trigger: position_size = -0.05 (negative)
    EXPECTED: trade executes with negative position_size (invalid)
    FIXED behavior: validate position_size > 0, reject if invalid
    """
    print("\n[Bug 1.20] No position size validation...")
    agent = TradeAgent()
    # Negative position size - should be rejected
    bad_decision = make_decision("BUY", position_size=-0.05)
    trade = agent.execute_trade(bad_decision, current_price=100.0, symbol="AAPL")
    print(f"  Trade with position_size=-0.05: {trade}")
    assert trade is None, \
        f"BUG 1.20 CONFIRMED: Trade executed with invalid position_size=-0.05. " \
        f"Trade: {trade}"
    print("  UNEXPECTED: Negative position_size rejected - bug may be fixed")


def run():
    """Run all TradeAgent bug condition exploration tests."""
    print("=" * 60)
    print("TradeAgent Bug Condition Exploration Tests (Bugs 1.16-1.20)")
    print("EXPECTED: Tests FAIL (confirms bugs exist)")
    print("=" * 60)

    tests = [
        test_bug_1_16_no_position_limit_enforcement,
        test_bug_1_17_no_capital_check,
        test_bug_1_18_no_overnight_stop_adjustment,
        test_bug_1_19_no_partial_fill_handling,
        test_bug_1_20_no_position_size_validation,
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
