"""src.teleon.blackboard — the local-first GOVERNED-BLACKBOARD store implementations (Teleon-owned).

The deterministic OFFLINE :class:`local_sqlite_blackboard.LocalSqliteBlackboard` is the correctness invariant +
the local-first golden path for the blackboard spine: an APPEND-ONLY, tenant-isolated, source-backed typed store
where bounded workers post signals/observations/gaps/calculations/analyses/synthesis across iterations instead of
re-reading docs every turn. External/hosted blackboard stores are CANDIDATES behind the same
:class:`~src.teleon.ports.blackboard_provider.BlackboardProviderPort` — never imported/executed here.

A blackboard entry is analytical WORKING STATE, never served truth: every stored entry carries
``serves_truth=False``; Teleon RUNS the blackboard, Baltor GOVERNS what (if anything) becomes truth. Imports only
the stdlib + Teleon id helpers — never Baltor. Deterministic when ``now`` is injected.
"""
from src.teleon.blackboard.local_sqlite_blackboard import (
    py_const_src_teleon_blackboard_local_sqlite_blackboard__LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID,
    py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard,
    py_function_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard,
)

__all__ = [
    "py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard",
    "py_const_src_teleon_blackboard_local_sqlite_blackboard__LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID",
    "py_function_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard",
]
