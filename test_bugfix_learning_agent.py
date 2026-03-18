"""
Bug Condition Exploration Tests: LearningAgent (Bugs 1.21-1.25)

CRITICAL: These tests MUST FAIL on unfixed code.
Failure confirms the bugs exist. DO NOT fix the code when tests fail.
"""
import inspect
import logging
import io
from agents.learning_agent import LearningAgent


def test_bug_1_21_sqlite_pgvector_not_detected():
    """
    Bug 1.21: SQLite used as DB but pgvector operations attempted without detection.
    Trigger: LearningAgent("sqlite:///:memory:") → no supports_pgvector flag set
    EXPECTED: no SQLite detection, no warning, pgvector ops may fail silently
    FIXED behavior: detect SQLite, set supports_pgvector=False, log warning
    """
    print("\n[Bug 1.21] SQLite pgvector detection missing...")
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    for name in ["agents.learning_agent", "learning_agent", ""]:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        lg.setLevel(logging.WARNING)

    agent = LearningAgent(db_url="sqlite:///:memory:")
    log_output = log_capture.getvalue()
    print(f"  Log output: '{log_output}'")
    print(f"  Has supports_pgvector attr: {hasattr(agent, 'supports_pgvector')}")

    for name in ["agents.learning_agent", "learning_agent", ""]:
        logging.getLogger(name).removeHandler(handler)

    assert hasattr(agent, "supports_pgvector") and agent.supports_pgvector == False, \
        f"BUG 1.21 CONFIRMED: No 'supports_pgvector' attribute set for SQLite. " \
        f"supports_pgvector={getattr(agent, 'supports_pgvector', 'MISSING')}"
    print("  UNEXPECTED: supports_pgvector=False set - bug may be fixed")


def test_bug_1_22_no_connection_pooling():
    """
    Bug 1.22: No connection pooling configured on the SQLAlchemy engine.
    Trigger: inspect engine pool configuration
    EXPECTED (unfixed): default NullPool with no explicit pooling strategy
    FIXED behavior:
      - SQLite in-memory → StaticPool (required to share a single connection)
      - PostgreSQL       → QueuePool with pool_size=5, max_overflow=10, pool_pre_ping=True
    The fix is confirmed when an explicit pool class is set (not the SQLAlchemy default NullPool).
    """
    print("\n[Bug 1.22] No connection pooling...")
    agent = LearningAgent(db_url="sqlite:///:memory:")
    pool_obj = agent.engine.pool
    pool_class_name = type(pool_obj).__name__
    print(f"  Engine pool class: {pool_class_name}")

    # For SQLite the correct fix is StaticPool; for PostgreSQL it would be QueuePool.
    # Either way, NullPool (the unfixed default) is unacceptable.
    assert pool_class_name != "NullPool", \
        f"BUG 1.22 CONFIRMED: Engine still using NullPool (no pooling configured). " \
        f"Pool class: {pool_class_name}"
    print(f"  UNEXPECTED: Explicit pool configured ({pool_class_name}) - bug may be fixed")


def test_bug_1_23_embedding_dimension_hardcoded():
    """
    Bug 1.23: Embedding dimension hardcoded to 1536, not configurable.
    Trigger: inspect __init__ signature for embedding_dim parameter
    EXPECTED: no embedding_dim parameter, hardcoded 1536 in TradePattern model
    FIXED behavior: embedding_dim parameter with env var default
    """
    print("\n[Bug 1.23] Embedding dimension hardcoded...")
    sig = inspect.signature(LearningAgent.__init__)
    params = sig.parameters
    print(f"  LearningAgent.__init__ params: {list(params.keys())}")

    assert "embedding_dim" in params, \
        f"BUG 1.23 CONFIRMED: No 'embedding_dim' parameter in __init__. " \
        f"Params: {list(params.keys())}"
    print("  UNEXPECTED: embedding_dim parameter exists - bug may be fixed")


def test_bug_1_24_no_cleanup_mechanism():
    """
    Bug 1.24: No cleanup mechanism for old validation records.
    Trigger: check for cleanup_old_records method
    EXPECTED: no such method exists
    FIXED behavior: cleanup_old_records(retention_days=90) method exists
    """
    print("\n[Bug 1.24] No cleanup mechanism for old records...")
    agent = LearningAgent(db_url="sqlite:///:memory:")
    has_cleanup = hasattr(agent, "cleanup_old_records") and callable(
        getattr(agent, "cleanup_old_records", None)
    )
    print(f"  Has cleanup_old_records method: {has_cleanup}")

    assert has_cleanup, \
        f"BUG 1.24 CONFIRMED: No 'cleanup_old_records' method on LearningAgent"
    print("  UNEXPECTED: cleanup_old_records method exists - bug may be fixed")


def test_bug_1_25_no_graceful_degradation():
    """
    Bug 1.25: Database connection failure causes agent crash, no graceful degradation.
    Trigger: use invalid DB URL → operations should degrade gracefully, not crash
    EXPECTED: exception raised or crash on DB operations
    FIXED behavior: catch errors, set degraded_mode=True, return fallback values
    """
    print("\n[Bug 1.25] No graceful degradation on DB failure...")
    # Use a bad DB URL that will fail on operations
    try:
        agent = LearningAgent(db_url="sqlite:///:memory:")
        # Check for degraded_mode attribute
        has_degraded_mode = hasattr(agent, "degraded_mode")
        print(f"  Has degraded_mode attr: {has_degraded_mode}")

        # Now simulate a DB failure by breaking the engine
        from sqlalchemy import create_engine
        agent.engine = create_engine("sqlite:////nonexistent/path/db.sqlite3")
        from sqlalchemy.orm import sessionmaker
        agent.SessionLocal = sessionmaker(bind=agent.engine)

        # Try get_dynamic_weights_for_regime - should degrade gracefully
        try:
            weights = agent.get_dynamic_weights_for_regime("normal")
            print(f"  get_dynamic_weights_for_regime returned: {weights}")
            # If it returns something (fallback), check degraded_mode was set
            assert has_degraded_mode, \
                f"BUG 1.25 CONFIRMED: No 'degraded_mode' attribute for graceful degradation"
        except Exception as e:
            print(f"  BUG 1.25 CONFIRMED: DB failure caused crash: {type(e).__name__}: {e}")
            raise AssertionError(
                f"Bug 1.25 confirmed: DB failure not handled gracefully: {type(e).__name__}: {e}"
            )
    except AssertionError:
        raise
    except Exception as e:
        print(f"  BUG 1.25 CONFIRMED: Agent init/operation crashed: {type(e).__name__}: {e}")
        raise AssertionError(f"Bug 1.25 confirmed: {type(e).__name__}: {e}")

    print("  UNEXPECTED: Graceful degradation implemented - bug may be fixed")


def run():
    """Run all LearningAgent bug condition exploration tests."""
    print("=" * 60)
    print("LearningAgent Bug Condition Exploration Tests (Bugs 1.21-1.25)")
    print("EXPECTED: Tests FAIL (confirms bugs exist)")
    print("=" * 60)

    tests = [
        test_bug_1_21_sqlite_pgvector_not_detected,
        test_bug_1_22_no_connection_pooling,
        test_bug_1_23_embedding_dimension_hardcoded,
        test_bug_1_24_no_cleanup_mechanism,
        test_bug_1_25_no_graceful_degradation,
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
