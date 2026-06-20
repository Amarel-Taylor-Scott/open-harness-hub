#!/usr/bin/env python3
"""scripts.runtime.verification_gate — the MANDATORY gate between Enhancement and Optimization.

An enhanced artifact may only enter Optimization / Consumption after it is proven source-grounded, governed,
schema-valid, conflict-clean, tenant-safe, fresh-or-queued, and traceable. The gate is a DECISION + RECEIPT
maker — it never mutates canonical truth (promotion happens downstream): it returns, per artifact,
``allow`` (promotable now) or ``hold_out`` (retain, but NOT as verified truth), plus a receipt explaining
every decision. Optimizers consume only ``allow`` artifacts; held-out items ride along as warnings.

Single sources of truth (no parallel rulebook): artifact governance is read from
``scripts.pipeline_runtime.artifact_types`` (the governed type registry); schemas are checked through the
runtime ``schema_validator``; conflict/reconciliation state is passed in (the reconciler stays the authority).
Deterministic + offline: time is INJECTED (``now``), receipt ids are content-addressed — no clock/RNG.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from scripts.pipeline_runtime import artifact_types as AT
from scripts.runtime.schema_validator import SCHEMA_DIR, validate_ref

#: a per-artifact check outcome. blocking → a failure forces hold_out.
@dataclass
class CheckResult:
    name: str
    passed: bool
    blocking: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed, "blocking": self.blocking, "detail": self.detail}


@dataclass
class VerificationReport:
    artifact_id: str
    artifact_type: str
    checks: list = field(default_factory=list)
    promotable: bool = False

    @property
    def violations(self) -> list:
        return [c for c in self.checks if c.blocking and not c.passed]

    @property
    def ok(self) -> bool:
        return self.violations == []


@dataclass
class PromotionDecision:
    decision: str           # "allow" | "hold_out"
    reasons: list = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"


@dataclass
class VerificationReceipt:
    receipt_id: str
    artifact_id: str
    artifact_type: str
    decision: str
    reasons: list
    checks: list
    created_at: str
    schema_version: str = "VerificationReceipt.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "receipt_id": self.receipt_id,
                "artifact_id": self.artifact_id, "artifact_type": self.artifact_type,
                "decision": self.decision, "reasons": list(self.reasons), "checks": list(self.checks),
                "created_at": self.created_at}


def _stale(fragility: dict, now: int) -> bool:
    """A fragile fact is stale if it is past its refresh horizon. Immutable/no-refresh facts never go stale."""
    if not fragility:
        return False
    if fragility.get("no_refresh") or fragility.get("volatility_class") == "stable":
        return False
    nva = fragility.get("next_verify_at")
    if isinstance(nva, int):
        return now > nva
    lva, ttl = fragility.get("last_verified_at"), fragility.get("ttl_seconds")
    if isinstance(lva, int) and isinstance(ttl, int):
        return now > lva + ttl
    return False  # fragility declared but no horizon → treat as not-yet-stale (the Watchtower will set one)


class VerificationGate:
    """Runs the Enhancement→Optimization checks over one artifact and returns report + decision + receipt."""

    def __init__(self, *, default_ttl_seconds: int = 30 * 86400) -> None:
        self.default_ttl_seconds = default_ttl_seconds

    # ---- the checks -----------------------------------------------------------
    def verify(self, artifact: dict, *, context: dict | None = None) -> VerificationReport:
        ctx = context or {}
        now = int(ctx.get("now", 0))
        open_conflicts = set(ctx.get("open_conflict_ids", ()))      # artifacts in unresolved/held-out conflicts
        held_out_ids = set(ctx.get("held_out_ids", ()))            # reconciliation losers
        pending = set(ctx.get("pending_verification_ids", ()))      # facts with a queued verification task
        requested_scope = ctx.get("requested_scope", "")           # where the caller wants to promote it

        at = str(artifact.get("artifact_type", ""))
        aid = str(artifact.get("artifact_id", artifact.get("fact_id", "")))
        spec = AT.REGISTRY.get(at)
        handles = artifact.get("source_handles") or ([artifact["source_handle"]] if artifact.get("source_handle") else [])
        checks: list[CheckResult] = []

        def add(name, passed, blocking, detail=""):
            checks.append(CheckResult(name, bool(passed), bool(blocking), detail))

        # 4) governance: the type must be known (drives every other governance rule)
        add("artifact_type_governed", spec is not None, True, "" if spec else f"unknown artifact_type {at!r}")

        # 1) source handles exist for source-grounded artifacts (derived ones cite supports instead)
        needs_handle = bool(spec and spec.source_grounded)
        add("source_handles_present", (not needs_handle) or len(handles) >= 1, True,
            "" if (not needs_handle or handles) else "source-grounded artifact has no source handle")

        # 2) content hash exists
        add("content_hash_present", bool(artifact.get("content_hash")), True,
            "" if artifact.get("content_hash") else "missing content_hash")

        # 3 + 12) schema validity: validate the declared artifact payload schema if one exists
        asv = str(artifact.get("artifact_schema_version", ""))
        if asv and (SCHEMA_DIR / "artifacts" / f"{asv}.schema.json").exists():
            errs = validate_ref(artifact.get("payload", {}), f"artifacts/{asv}")
            add("artifact_schema_valid", errs == [], True, str(errs[:2]) if errs else "")
        else:
            add("artifact_schema_valid", True, False, "no declared payload schema (n/a)")

        # 5) a narrative allegation (a type that cannot be a fact) must NOT claim promotion eligibility
        is_allegation = bool(spec and not spec.can_be_used_as_fact and at == "narrative_allegation")
        misrepresented = is_allegation and bool(artifact.get("promotion_eligible"))
        add("allegation_not_promoted_as_fact", not misrepresented, True,
            "narrative_allegation claims promotion_eligible=true" if misrepresented else "")

        # 6) a conclusion must cite supporting artifacts
        is_conclusion = at == "conclusion"
        supports = artifact.get("supports") or artifact.get("supporting_artifact_ids") or []
        add("conclusion_support_present", (not is_conclusion) or len(supports) >= 1, True,
            "conclusion cites no supporting artifacts" if (is_conclusion and not supports) else "")

        # 7) conflicts absent or reconciled (the reconciler is the authority; the gate only reads its verdict)
        in_conflict = aid in open_conflicts or aid in held_out_ids
        add("conflict_absent_or_reconciled", not in_conflict, True,
            "artifact is in an unresolved/held-out conflict" if in_conflict else "")

        # 8) fragile facts are current OR have a queued verification task (graceful until the Watchtower lands)
        frag = artifact.get("fragility") or {}
        stale = _stale(frag, now)
        add("fragile_fact_current_or_queued", (not stale) or (aid in pending), True,
            "fragile fact is stale and has no queued verification task" if (stale and aid not in pending) else "")

        # 9) tenant-private data must not be promoted into the global/shared fact base
        scope = str(artifact.get("scope", ""))
        leak = scope == "tenant_private" and requested_scope in ("global_public", "system_reference")
        add("tenant_isolation_preserved", not leak, True,
            "tenant_private artifact requested for promotion to a shared scope" if leak else "")

        # 10) model-dependent output must carry processor metadata + be traceable to a source/support
        needs_md = bool(spec and spec.requires_processor_metadata)
        traceable = bool(handles or supports)
        has_md = bool(artifact.get("processor_metadata"))
        add("model_output_grounded", (not needs_md) or (has_md and traceable), True,
            "model-dependent artifact missing processor metadata or source traceability" if (needs_md and not (has_md and traceable)) else "")

        # 11) gate invariant: this is a projection/decision, not a canonical mutation (informational)
        add("decision_is_advisory_not_canonical_mutation", True, False,
            "gate returns a decision + receipt; promotion happens downstream")

        # promotable = the type can carry truth (fact or legitimately promotion-eligible) and is not an allegation/derived hold-out type
        promotable = bool(spec and (spec.can_be_used_as_fact or spec.promotion_eligible_default)
                          and not is_allegation)
        return VerificationReport(artifact_id=aid, artifact_type=at, checks=checks, promotable=promotable)

    def decide(self, report: VerificationReport) -> PromotionDecision:
        reasons = [f"{c.name}: {c.detail or 'failed'}" for c in report.violations]
        if not report.promotable and report.ok:
            reasons.append(f"held out: {report.artifact_type} is not promotable as a verified fact")
        decision = "allow" if (report.ok and report.promotable) else "hold_out"
        return PromotionDecision(decision=decision, reasons=reasons)

    def receipt(self, report: VerificationReport, decision: PromotionDecision, *, now: str) -> VerificationReceipt:
        checks = [c.to_dict() for c in report.checks]
        body = {"artifact_id": report.artifact_id, "decision": decision.decision,
                "checks": [(c["name"], c["passed"]) for c in checks]}
        rid = "vrcpt-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        return VerificationReceipt(receipt_id=rid, artifact_id=report.artifact_id, artifact_type=report.artifact_type,
                                   decision=decision.decision, reasons=decision.reasons, checks=checks, created_at=now)

    def evaluate(self, artifact: dict, *, context: dict | None = None, now: str = "1970-01-01T00:00:00Z") -> dict:
        """One call → report + decision + receipt (the convenience the worker/API/proofs use)."""
        report = self.verify(artifact, context=context)
        decision = self.decide(report)
        receipt = self.receipt(report, decision, now=now)
        return {"report": report, "decision": decision, "receipt": receipt}
