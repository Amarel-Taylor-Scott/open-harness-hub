#!/usr/bin/env python3
"""src.baltor.determinism.pattern_miner — mine REPEATED VERIFIED decisions into PatternCandidates.

The M5 layer of the ladder: once the same VERIFIED decision has been made enough times, that repetition is
a signal that a deterministic rule could reproduce it. The miner finds those repetitions and emits
:class:`PatternCandidate`s. It does NOT generate the rule itself (that is Lane C's
``rule_candidate_generator``), and it never decides truth — it observes that the EXISTING authorities kept
deciding the same way.

What is mined, and what is NOT:

* **Mined**: VERIFIED traces only — ``workflow`` / ``adjudication`` traces that are source-grounded and
  receipt-backed. These came from a deterministic validator / authority / human adjudication, i.e. the
  outcome was already verified by Baltor.
* **Excluded**: raw ``llm`` proposals, ``consensus`` runs (evidence, never truth), and any unverified
  trace. The miner reads ONLY through :meth:`TraceStore.mining_set`, so the tenant-private boundary is
  enforced upstream — a ``tenant_private`` trace can never enter a global pattern unless anonymized AND
  approved.

A :class:`PatternCandidate` groups traces by ``(decision_key, decision_value)`` — same decision shape, same
decided value — and only emits a candidate when the group has ≥ ``min_support`` DISTINCT verified traces.
Each candidate carries its supporting trace ids (lossless link-back: the candidate never deletes the traces
it was distilled from), the verified decision body, and the union of source handles + receipts backing it.

Determinism: candidate ids are content hashes of ``(decision_key, decision_value, scope)``; grouping +
ordering are stable sorts; no clock, no RNG. Stdlib only, fully offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.baltor.determinism.trace_store import (
    EPOCH,
    GLOBAL_PUBLIC,
    TraceStore,
    Trace,
    _hash,
)

_ID_ALGO = "sha256"
_CAND_PREFIX = f"patcand:{_ID_ALGO}:"

#: a pattern needs at least this many DISTINCT verified traces before it is worth proposing a rule for.
DEFAULT_MIN_SUPPORT = 3


class PatternMinerError(Exception):
    """Base class for pattern-miner failures."""


def _candidate_id(decision_key: str, decision_value: str, scope: str, tenant_id: str) -> str:
    h = _hash({"decision_key": decision_key, "decision_value": decision_value,
               "scope": scope, "tenant": tenant_id})
    return f"{_CAND_PREFIX}{h}:{tenant_id}"


@dataclass(frozen=True)
class PatternCandidate:
    """A repeated VERIFIED decision worth distilling into a deterministic rule.

    ``decision_key`` is the grouped decision shape (e.g. ``"reconcile:deadline_mismatch"``);
    ``decision`` is the canonical verified decision body that recurred; ``support`` is the number of distinct
    verified traces that decided it that way; ``support_trace_ids`` link back to EVERY one of them (lossless —
    the candidate preserves its evidence and never replaces it). ``source_handles`` / ``receipt_ids`` are the
    union backing the pattern. ``tenant_scoped`` is True when the pattern was mined within a single tenant's
    private set (it must NOT be promoted as a global rule).
    """
    candidate_id: str
    tenant_id: str
    scope: str
    decision_key: str
    decision: dict
    decision_value: str
    support: int
    support_trace_ids: tuple[str, ...]
    source_handles: tuple[str, ...]
    receipt_ids: tuple[str, ...]
    workflow_ids: tuple[str, ...]
    tenant_scoped: bool = False
    content_hash: str = ""
    created_at: str = EPOCH

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id, "tenant_id": self.tenant_id, "scope": self.scope,
            "decision_key": self.decision_key, "decision": dict(self.decision),
            "decision_value": self.decision_value, "support": self.support,
            "support_trace_ids": list(self.support_trace_ids),
            "source_handles": list(self.source_handles), "receipt_ids": list(self.receipt_ids),
            "workflow_ids": list(self.workflow_ids), "tenant_scoped": self.tenant_scoped,
            "content_hash": self.content_hash, "created_at": self.created_at,
        }


def mine_patterns(store: TraceStore, *, scope: str = GLOBAL_PUBLIC, tenant: str | None = None,
                  min_support: int = DEFAULT_MIN_SUPPORT,
                  now: str = EPOCH) -> list[PatternCandidate]:
    """Mine repeated VERIFIED decisions from ``store`` → :class:`PatternCandidate`s.

    Reads ONLY through :meth:`TraceStore.mining_set` (``require_verified=True``), so:
    * raw LLM proposals and consensus runs are excluded — only verified outcomes are mined;
    * the tenant-private boundary is enforced upstream — a ``tenant_private`` trace cannot enter a
      ``global_public`` pattern unless it is anonymized AND approved.

    Groups verified traces by ``(decision_key, decision_value)`` and emits a candidate for each group with
    ≥ ``min_support`` DISTINCT traces. Deterministic: stable sorts, content-hash ids, injected ``now``.
    """
    if min_support < 1:
        raise PatternMinerError(f"min_support must be ≥1, got {min_support}")

    # the choke point: mining_set refuses raw/unverified and unapproved tenant_private traces.
    eligible = store.mining_set(scope=scope, tenant=tenant, require_verified=True)

    # group by the decision SHAPE + decided VALUE — same key, same value = the same recurring decision.
    groups: dict[tuple[str, str], list[Trace]] = {}
    for t in eligible:
        groups.setdefault((t.decision_key, t.decision_value), []).append(t)

    out: list[PatternCandidate] = []
    is_tenant_scoped = scope != GLOBAL_PUBLIC
    for (decision_key, decision_value), traces in groups.items():
        # distinct traces (mining_set already returns deduped ids, but be explicit about "distinct support").
        distinct = {t.trace_id: t for t in traces}
        if len(distinct) < min_support:
            continue
        members = sorted(distinct.values(), key=lambda t: t.trace_id)

        # the verified decision body is identical across the group (same decision_value); take the first.
        decision = dict(members[0].decision)

        handles: set[str] = set()
        receipts: set[str] = set()
        workflows: set[str] = set()
        for m in members:
            handles.update(m.input_handles)
            handles.update(m.output_handles)
            receipts.update(m.receipt_ids)
            workflows.add(m.workflow_id)

        # the candidate's home tenant: for a global pattern it is the shared "global" namespace token; for a
        # tenant-private pattern it is the single owning tenant.
        cand_tenant = tenant if is_tenant_scoped else GLOBAL_PUBLIC
        candidate_id = _candidate_id(decision_key, decision_value, scope, cand_tenant)
        content_hash = f"{_ID_ALGO}:" + _hash(
            {"candidate_id": candidate_id, "support_trace_ids": [m.trace_id for m in members],
             "decision": decision})

        out.append(PatternCandidate(
            candidate_id=candidate_id, tenant_id=cand_tenant, scope=scope, decision_key=decision_key,
            decision=decision, decision_value=decision_value, support=len(members),
            support_trace_ids=tuple(m.trace_id for m in members),
            source_handles=tuple(sorted(handles)), receipt_ids=tuple(sorted(receipts)),
            workflow_ids=tuple(sorted(workflows)), tenant_scoped=is_tenant_scoped,
            content_hash=content_hash, created_at=now))

    # deterministic order: most-supported first, ties broken by candidate id.
    out.sort(key=lambda c: (-c.support, c.candidate_id))
    return out
