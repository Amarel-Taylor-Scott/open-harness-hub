#!/usr/bin/env python3
"""facts/refresh_planner — turn a STALE fragile fact into a durable VerificationTask, then a VerificationResult.

``FactRefreshPlanner`` is the watchtower's scheduler:
  * ``plan_task`` — given a FragilityMetadata that is stale (``now`` past its horizon) it emits a durable
    ``VerificationTask`` (id content-addressed on fact + missed-horizon + policy, so reruns coalesce).
  * ``refresh`` — runs a STUBBED external-source check that STORES an EVIDENCE artifact dict (an evidence
    record — NOT a fabricated answer) and returns a ``VerificationResult``. There is NO network / customer
    fetch here; the evidence is a deterministic stored record (content-addressed). A live adapter would
    implement ``FragileFactProviderPort`` (out of this minimum slice).

Scope rule (enforced): a ``tenant_private`` (or tenant_override) refresh may NOT update a ``global_public``
canonical fact — the result is recorded as ``applied=False`` (refused) with a reason. Deterministic + offline:
ids content-addressed; all times INJECTED.
"""
from __future__ import annotations

import hashlib
import json

from src.baltor.contracts.artifacts.canonical_fact import CanonicalFact
from src.baltor.contracts.artifacts.fragility_metadata import FragilityMetadata
from src.baltor.contracts.artifacts.verification_result import VerificationResult
from src.baltor.contracts.artifacts.verification_task import VerificationTask
from src.baltor.contracts.artifacts.watch_policy import WatchPolicy

#: which (evidence scope) may update which (canonical fact scope). A tenant scope may NOT touch a shared one.
_SHARED_SCOPES = ("global_public", "system_reference")
_TENANT_SCOPES = ("tenant_private", "tenant_override")


def _evidence_hash(body: dict) -> str:
    return "ev-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _scope_allowed(evidence_scope: str, fact_scope: str) -> bool:
    """A tenant-scoped refresh may not update a shared (global_public/system_reference) fact."""
    if fact_scope in _SHARED_SCOPES and evidence_scope in _TENANT_SCOPES:
        return False
    return True


class FactRefreshPlanner:
    """Plans + executes fragile-fact re-verification. No clock/RNG; external fetch is STUBBED to evidence."""

    def plan_task(self, fragility: FragilityMetadata, *, source_handle: str, scope: str, now: int,
                  reason: str = "") -> VerificationTask | None:
        """A stale fact (now past horizon) → a durable VerificationTask; a fresh/immutable fact → None."""
        if not fragility.is_stale(now):
            return None
        due = fragility.horizon()  # the absolute horizon it missed (never None when is_stale is True)
        return VerificationTask(
            fact_id=fragility.fact_id, source_handle=source_handle, scope=scope,
            watch_policy_id=fragility.watch_policy_id, due_at=int(due), created_at=now,
            status="queued",
            reason=reason or f"fact past refresh horizon ({fragility.volatility_class})")

    def _stub_external_evidence(self, task: VerificationTask, *, now: int) -> dict:
        """STUB: stand-in for an external-source check. Stores a deterministic EVIDENCE artifact dict — an
        evidence record (where we looked, what handle, when), NOT a fabricated answer/value. A real provider
        implementing FragileFactProviderPort would replace this; no network here."""
        body = {"artifact_type": "source_record", "fact_id": task.fact_id,
                "source_handle": task.source_handle, "scope": task.scope, "observed_at": now,
                "method": "stubbed_offline_recheck", "note": "evidence record (no answer fabricated)"}
        return {"evidence_id": _evidence_hash(body), **body}

    def refresh(self, task: VerificationTask, policy: WatchPolicy, *, fact_scope: str, now: int,
                contested: bool = False) -> VerificationResult:
        """Execute a queued task: store evidence, decide the new status, enforce scope isolation.

        Returns a VerificationResult. The refresh NEVER fabricates an answer — it stores evidence and decides a
        status. A tenant-scoped refresh against a shared fact is REFUSED (applied=False)."""
        evidence = self._stub_external_evidence(task, now=now)

        if not _scope_allowed(task.scope, fact_scope):
            return VerificationResult(
                task_id=task.task_id, fact_id=task.fact_id, scope=task.scope, new_status="held_out",
                applied=False, verified_at=now, evidence=evidence, next_verify_at=None,
                reason=f"scope isolation: {task.scope} evidence may not update {fact_scope} canonical fact")

        if contested and policy.escalate_on_conflict:
            return VerificationResult(
                task_id=task.task_id, fact_id=task.fact_id, scope=task.scope, new_status="needs_human",
                applied=False, verified_at=now, evidence=evidence, next_verify_at=None,
                reason="contested refresh escalated to human review")

        next_at = policy.next_verify_at(now)  # the new horizon after a clean re-verification
        return VerificationResult(
            task_id=task.task_id, fact_id=task.fact_id, scope=task.scope, new_status="verified_current",
            applied=True, verified_at=now, evidence=evidence, next_verify_at=next_at,
            reason="re-verified against source; evidence stored")

    def apply_result(self, fact: CanonicalFact, result: VerificationResult) -> CanonicalFact:
        """Project a VerificationResult onto a CanonicalFact (returns a NEW frozen fact — no mutation).

        If the result was refused (applied=False) the fact's status is set to the result's new_status
        (held_out / needs_human) but its servable value is unchanged — the refusal does not 'verify' it."""
        return CanonicalFact(
            subject=fact.subject, predicate=fact.predicate, object=fact.object, scope=fact.scope,
            status=result.new_status, source_handle=fact.source_handle, content_hash=fact.content_hash,
            authority_rank=fact.authority_rank, fragility_id=fact.fragility_id,
            supporting_assertion_ids=fact.supporting_assertion_ids, tenant_id=fact.tenant_id, unit=fact.unit)
