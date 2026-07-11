"""src.baltor.determinism — the Determinism Factory CORE engine (observe → mine → replay → shadow → promote).

This package is a **META observe/mine/shadow/promote LEDGER** over Baltor's EXISTING deterministic
authorities (``_repos/shared-backend-components/scripts/artifact_graph/reconciliation.py`` + ``conflict_detector.py``, the optimizer, the
consumption gate). It does NOT create a second reconciliation authority, a second optimizer, or a second
rule engine. It records what those authorities (and the LLMs / consensus runs / human adjudicators that
feed them) decided, finds repeated VERIFIED decisions, and proposes deterministic rules that
ASSERT-EQUIVALENCE to the existing reference outcomes — reproducing them, never replacing them.

Core principle (``_repos/baltor/context/baltor-determinism-factory.md``):
**LLMs propose. Baltor verifies. Repeated *verified* patterns become deterministic.**

Lane B owns the front of the ladder (M0 raw LLM → M4 adjudicated → M5 mined pattern):

* :class:`~src.baltor.determinism.trace_store.TraceStore` — append-only, content-addressed, tenant-scoped
  store of ``WorkflowTrace`` / ``LLMTrace`` / ``ConsensusRun`` / ``AdjudicationRecord``. A
  ``tenant_private`` trace can NEVER be read into a global-rule mining set (``mining_set`` rejects it).
* :func:`~src.baltor.determinism.consensus.record_consensus` — record multi-model outputs into a
  ``ConsensusRun`` (agreement_score + disagreement clusters). Consensus is an EVIDENCE / ambiguity signal,
  NOT truth: ``can_serve_fact`` is always False — only a deterministic validator or authority/policy label
  may serve a fact.
* :func:`~src.baltor.determinism.pattern_miner.mine_patterns` — find repeated VERIFIED decisions across
  the trace store → ``PatternCandidate``s. Only VERIFIED / adjudicated traces are mined; raw / ungrounded
  / consensus-only traces are excluded.

Determinism: ids are ``hashlib`` content hashes, ``created_at`` / timestamps are INJECTED params (never a
wall-clock read), no RNG. Stdlib only, fully offline (no network, no live model).
"""
from __future__ import annotations

from src.baltor.determinism.consensus import (
    ConsensusError,
    ConsensusRun,
    ModelOutput,
    record_consensus,
)
from src.baltor.determinism.pattern_miner import (
    PatternCandidate,
    PatternMinerError,
    mine_patterns,
)
from src.baltor.determinism.trace_store import (
    EPOCH,
    GLOBAL_PUBLIC,
    TENANT_PRIVATE,
    AdjudicationRecord,
    LLMTrace,
    TenantBoundaryError,
    Trace,
    TraceStore,
    TraceStoreError,
    WorkflowTrace,
    make_trace_id,
    parse_trace_id,
)

__all__ = [
    # trace store
    "TraceStore",
    "Trace",
    "WorkflowTrace",
    "LLMTrace",
    "AdjudicationRecord",
    "TraceStoreError",
    "TenantBoundaryError",
    "TENANT_PRIVATE",
    "GLOBAL_PUBLIC",
    "EPOCH",
    "make_trace_id",
    "parse_trace_id",
    # consensus
    "record_consensus",
    "ConsensusRun",
    "ModelOutput",
    "ConsensusError",
    # pattern miner
    "mine_patterns",
    "PatternCandidate",
    "PatternMinerError",
]
