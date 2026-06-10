#!/usr/bin/env python3
"""src.baltor.determinism.trace_store — the append-only, content-addressed, tenant-scoped TRACE STORE.

The Determinism Factory's front end: it records what the EXISTING authorities (and the LLMs / consensus
runs / human adjudicators that feed them) decided, so the pattern miner can later find repeated VERIFIED
decisions. It is a LEDGER, not an authority — it never decides truth; it only records traces of decisions
already made by Baltor reconciliation / the validator / a human adjudicator.

Four trace kinds live here (one ``Trace`` shape, distinguished by ``trace_kind``):

* ``workflow``     — :class:`WorkflowTrace`: a full decision step (input/output handles, the deterministic
  validation that ran, the final served decision, the receipt that backs it).
* ``llm``          — :class:`LLMTrace`: a single model's structured output for a step (model/provider ids,
  prompt_hash). An LLM trace is a PROPOSAL — never, on its own, a verified outcome.
* ``adjudication`` — :class:`AdjudicationRecord`: a human/policy decision that produced a VERIFIED label
  (this is the M4 layer — it becomes training/eval data for mining).
* ``consensus``    — recorded via :mod:`src.baltor.determinism.consensus` as a ``ConsensusRun`` and stored
  here as a trace whose ``verified`` flag is ALWAYS False (consensus is evidence, never truth).

Guarantees, structurally enforced:

* **append-only** — :meth:`TraceStore.append` never mutates or removes an existing trace; an idempotent
  re-append of the same body returns the same id and overwrites nothing observable.
* **content-addressed** — a trace id ``dtrace:sha256:<hex>:<tenant>`` is derived from the identity-bearing
  fields only (NOT from ``created_at``), so the same logical trace is byte-stable across runs.
* **tenant-scoped** — every read is tenant-checked (the id embeds the tenant); a cross-tenant read raises
  :class:`TenantBoundaryError`.
* **tenant_private never trains a global rule** — :meth:`TraceStore.mining_set` (the ONLY surface the
  pattern miner reads from) refuses to return a ``tenant_private`` trace into a ``global_public`` mining
  set unless it has been anonymized AND approved. Trying to force one in raises
  :class:`TenantBoundaryError`.

Determinism: ids are ``hashlib`` content hashes, ``created_at`` is an INJECTED ``now`` param (never a clock
read), no RNG. Stdlib only, fully offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

EPOCH = "1970-01-01T00:00:00Z"  # deterministic default stamp (no wall-clock in compared bytes)

#: id scheme — one definition, reused for build + parse so they can never drift.
_ID_SCHEME = "dtrace"
_ID_ALGO = "sha256"
_ID_PREFIX = f"{_ID_SCHEME}:{_ID_ALGO}:"  # "dtrace:sha256:"

#: the two scopes a trace can carry. tenant_private must never enter a global_public mining set.
TENANT_PRIVATE = "tenant_private"
GLOBAL_PUBLIC = "global_public"
_SCOPES = (TENANT_PRIVATE, GLOBAL_PUBLIC)

#: the four trace kinds. Single source — consensus.py + pattern_miner.py read these names, never re-literal.
KIND_WORKFLOW = "workflow"
KIND_LLM = "llm"
KIND_ADJUDICATION = "adjudication"
KIND_CONSENSUS = "consensus"
_KINDS = (KIND_WORKFLOW, KIND_LLM, KIND_ADJUDICATION, KIND_CONSENSUS)

#: a VERIFIED trace is one whose decision was produced by a deterministic validator / authority / human
#: adjudication AND is source-grounded (carries source handles) AND receipt-backed. ONLY these kinds may
#: ever be verified; an LLM or consensus trace is NEVER verified (it is a proposal / evidence signal).
_VERIFIABLE_KINDS = (KIND_WORKFLOW, KIND_ADJUDICATION)


class TraceStoreError(Exception):
    """Base class for trace-store failures."""


class TenantBoundaryError(TraceStoreError):
    """A read crossed a tenant boundary, or a tenant_private trace tried to enter a global mining set."""


def _canon(body: Any) -> bytes:
    """Canonical JSON bytes for content hashing (sorted keys, compact, str-coerced)."""
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _hash(body: Any) -> str:
    return hashlib.sha256(_canon(body)).hexdigest()


def make_trace_id(content_hash_hex: str, tenant_id: str) -> str:
    """Build the content-addressed trace id: ``dtrace:sha256:<hex>:<tenant>``."""
    return f"{_ID_PREFIX}{content_hash_hex}:{tenant_id}"


def parse_trace_id(trace_id: str) -> tuple[str, str]:
    """Parse a trace id → ``(content_hash_hex, tenant_id)``. Raise on any malformation."""
    if not isinstance(trace_id, str) or not trace_id.startswith(_ID_PREFIX):
        raise TraceStoreError(f"not a {_ID_PREFIX!r} id: {trace_id!r}")
    rest = trace_id[len(_ID_PREFIX):]
    parts = rest.split(":", 1)  # tenant ids may not contain ':'
    if len(parts) != 2:
        raise TraceStoreError(f"id missing tenant segment: {trace_id!r}")
    content_hash_hex, tenant_id = parts
    if len(content_hash_hex) != 64 or any(c not in "0123456789abcdef" for c in content_hash_hex):
        raise TraceStoreError(f"id hash is not a sha256 hex digest: {trace_id!r}")
    if not tenant_id:
        raise TraceStoreError(f"id has empty tenant: {trace_id!r}")
    return content_hash_hex, tenant_id


def _as_tuple(x: Iterable[str] | None) -> tuple[str, ...]:
    return tuple(x) if x else ()


@dataclass(frozen=True)
class Trace:
    """One immutable trace in the store. Append-only: once written it is never mutated.

    ``trace_kind`` is one of ``workflow`` / ``llm`` / ``adjudication`` / ``consensus``. ``decision`` is the
    decision THIS trace records (e.g. ``{"winner": ..., "reason": "deadline_mismatch"}``). ``verified`` is
    True only for a source-grounded, receipt-backed workflow/adjudication trace — never for an LLM or
    consensus trace.

    ``decision_key`` is the stable shape the miner groups on (e.g. ``"reconcile:deadline_mismatch"``);
    repeated identical ``(decision_key, decision_value)`` pairs across VERIFIED traces are what become a
    PatternCandidate. ``decision_value`` is the canonical hash of the verified ``decision`` body — two
    traces that decided the same thing share a ``decision_value``.
    """
    trace_id: str
    tenant_id: str
    scope: str                       # tenant_private | global_public
    trace_kind: str                  # workflow | llm | adjudication | consensus
    workflow_id: str
    step_id: str
    decision_key: str                # the grouped decision shape, e.g. "reconcile:deadline_mismatch"
    decision: dict                   # the decision this trace records
    decision_value: str              # canonical hash of `decision` (same decision → same value)
    verified: bool = False           # True only for source-grounded + receipt-backed workflow/adjudication
    anonymized: bool = False         # a tenant_private trace stripped of tenant-identifying content
    approved_for_global: bool = False  # explicit approval to use an anonymized private trace globally
    input_handles: tuple[str, ...] = ()    # ctx://… source handles feeding the decision
    output_handles: tuple[str, ...] = ()   # ctx://… source handles backing the served output
    receipt_ids: tuple[str, ...] = ()      # reconciliation/optimization/promotion/verification receipts
    model_id: str = ""               # LLM traces only — model id
    provider_id: str = ""            # LLM traces only — provider id
    prompt_hash: str = ""            # LLM traces only — content hash of the prompt (NOT the prompt text)
    parent_trace_ids: tuple[str, ...] = ()  # e.g. an adjudication points at the LLM proposals it ruled on
    content_hash: str = ""           # sha256:<hex> of the identity-bearing body
    created_at: str = EPOCH

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id, "tenant_id": self.tenant_id, "scope": self.scope,
            "trace_kind": self.trace_kind, "workflow_id": self.workflow_id, "step_id": self.step_id,
            "decision_key": self.decision_key, "decision": dict(self.decision),
            "decision_value": self.decision_value, "verified": self.verified,
            "anonymized": self.anonymized, "approved_for_global": self.approved_for_global,
            "input_handles": list(self.input_handles), "output_handles": list(self.output_handles),
            "receipt_ids": list(self.receipt_ids), "model_id": self.model_id,
            "provider_id": self.provider_id, "prompt_hash": self.prompt_hash,
            "parent_trace_ids": list(self.parent_trace_ids), "content_hash": self.content_hash,
            "created_at": self.created_at,
        }


# Friendly type aliases by kind — the engine interface names these; they are all the one ``Trace`` shape.
WorkflowTrace = Trace
LLMTrace = Trace
AdjudicationRecord = Trace


class TraceStore:
    """Append-only, content-addressed, tenant-scoped store of decision traces.

    This is the LEDGER the Determinism Factory mines. It records decisions; it never makes them. The only
    surface the pattern miner reads is :meth:`mining_set`, which enforces the tenant-private boundary so a
    private trace can never train a global rule.
    """

    def __init__(self) -> None:
        # trace_id -> Trace (the immutable, append-only trace table)
        self._traces: dict[str, Trace] = {}
        # append order, for deterministic, stable iteration that does not depend on dict internals
        self._order: list[str] = []

    # ── write path (the ONLY place a trace is created) ─────────────────────────────────────────────
    def append(self, *, tenant_id: str, scope: str, trace_kind: str, workflow_id: str, step_id: str,
               decision_key: str, decision: dict, verified: bool = False, anonymized: bool = False,
               approved_for_global: bool = False, input_handles: Iterable[str] | None = None,
               output_handles: Iterable[str] | None = None, receipt_ids: Iterable[str] | None = None,
               model_id: str = "", provider_id: str = "", prompt_hash: str = "",
               parent_trace_ids: Iterable[str] | None = None, now: str = EPOCH) -> Trace:
        """Append a trace. Returns the immutable :class:`Trace`. Idempotent: the same identity-bearing body
        for the same tenant returns the existing trace and overwrites nothing.

        Verification law (enforced here, not advisory): a trace may be ``verified=True`` ONLY if it is a
        ``workflow`` or ``adjudication`` kind AND it is source-grounded (carries ≥1 output handle) AND it is
        receipt-backed (carries ≥1 receipt id). An ``llm`` or ``consensus`` trace can NEVER be verified —
        it is a proposal / an evidence signal, never truth.
        """
        if not tenant_id:
            raise TraceStoreError("tenant_id is required")
        if scope not in _SCOPES:
            raise TraceStoreError(f"scope must be one of {_SCOPES}, got {scope!r}")
        if trace_kind not in _KINDS:
            raise TraceStoreError(f"trace_kind must be one of {_KINDS}, got {trace_kind!r}")
        if not decision_key:
            raise TraceStoreError("decision_key is required (the shape the miner groups on)")

        if verified:
            if trace_kind not in _VERIFIABLE_KINDS:
                raise TraceStoreError(
                    f"a {trace_kind!r} trace can NEVER be verified — consensus/LLM output is evidence, "
                    f"not truth; only {_VERIFIABLE_KINDS} traces carry a verified decision")
            outs = _as_tuple(output_handles)
            recs = _as_tuple(receipt_ids)
            if not outs:
                raise TraceStoreError(
                    "a verified trace must be source-grounded (≥1 output_handle); a decision without "
                    "handles is not a verified outcome and must not be mined")
            if not recs:
                raise TraceStoreError(
                    "a verified trace must be receipt-backed (≥1 receipt_id); an outcome without a receipt "
                    "is not a verified outcome and must not be mined")

        # decision_value: same decision body → same value, regardless of which trace recorded it.
        decision_value = f"{_ID_ALGO}:{_hash(decision)}"

        identity = {
            "tenant": tenant_id, "scope": scope, "kind": trace_kind, "workflow_id": workflow_id,
            "step_id": step_id, "decision_key": decision_key, "decision": decision,
            "verified": verified, "anonymized": anonymized, "approved_for_global": approved_for_global,
            "input_handles": sorted(_as_tuple(input_handles)),
            "output_handles": sorted(_as_tuple(output_handles)),
            "receipt_ids": sorted(_as_tuple(receipt_ids)),
            "model_id": model_id, "provider_id": provider_id, "prompt_hash": prompt_hash,
            "parents": sorted(_as_tuple(parent_trace_ids)),
        }
        h = _hash(identity)
        trace_id = make_trace_id(h, tenant_id)

        # append-only: an existing trace is NEVER overwritten. Idempotent re-append returns the existing one.
        existing = self._traces.get(trace_id)
        if existing is not None:
            return existing

        trace = Trace(
            trace_id=trace_id, tenant_id=tenant_id, scope=scope, trace_kind=trace_kind,
            workflow_id=workflow_id, step_id=step_id, decision_key=decision_key, decision=dict(decision),
            decision_value=decision_value, verified=verified, anonymized=anonymized,
            approved_for_global=approved_for_global, input_handles=_as_tuple(input_handles),
            output_handles=_as_tuple(output_handles), receipt_ids=_as_tuple(receipt_ids),
            model_id=model_id, provider_id=provider_id, prompt_hash=prompt_hash,
            parent_trace_ids=_as_tuple(parent_trace_ids), content_hash=f"{_ID_ALGO}:{h}", created_at=now)
        self._traces[trace_id] = trace
        self._order.append(trace_id)
        return trace

    def append_trace(self, trace: Trace) -> Trace:
        """Append a pre-built :class:`Trace` (e.g. one produced by :mod:`consensus`). Re-derives the id from
        the identity-bearing fields so a forged/mismatched id cannot smuggle in — the stored id is always the
        content hash. Idempotent + append-only like :meth:`append`."""
        return self.append(
            tenant_id=trace.tenant_id, scope=trace.scope, trace_kind=trace.trace_kind,
            workflow_id=trace.workflow_id, step_id=trace.step_id, decision_key=trace.decision_key,
            decision=trace.decision, verified=trace.verified, anonymized=trace.anonymized,
            approved_for_global=trace.approved_for_global, input_handles=trace.input_handles,
            output_handles=trace.output_handles, receipt_ids=trace.receipt_ids, model_id=trace.model_id,
            provider_id=trace.provider_id, prompt_hash=trace.prompt_hash,
            parent_trace_ids=trace.parent_trace_ids, now=trace.created_at)

    # ── reads (tenant-scoped projections; the store is the truth) ──────────────────────────────────
    def get(self, trace_id: str, *, tenant: str | None = None) -> Trace:
        """Return the (immutable) trace by id. If ``tenant`` is given it MUST match the trace's tenant — a
        cross-tenant read raises :class:`TenantBoundaryError` (the id embeds the tenant, so this is
        structural)."""
        _, id_tenant = parse_trace_id(trace_id)
        trace = self._traces.get(trace_id)
        if trace is None:
            raise TraceStoreError(f"no trace for id {trace_id!r}")
        if tenant is not None and tenant != trace.tenant_id:
            raise TenantBoundaryError(
                f"cross-tenant read: caller tenant {tenant!r} != trace tenant {trace.tenant_id!r}")
        return trace

    def has(self, trace_id: str) -> bool:
        return trace_id in self._traces

    def __len__(self) -> int:
        return len(self._traces)

    def all(self) -> list[Trace]:
        """Every trace, in deterministic append order."""
        return [self._traces[tid] for tid in self._order]

    def query(self, *, tenant: str | None = None, trace_kind: str | None = None,
              decision_key: str | None = None, verified: bool | None = None) -> list[Trace]:
        """Traces filtered by tenant / kind / decision_key / verified, in deterministic append order."""
        out = self.all()
        if tenant is not None:
            out = [t for t in out if t.tenant_id == tenant]
        if trace_kind is not None:
            out = [t for t in out if t.trace_kind == trace_kind]
        if decision_key is not None:
            out = [t for t in out if t.decision_key == decision_key]
        if verified is not None:
            out = [t for t in out if t.verified is verified]
        return out

    # ── the ONLY surface the pattern miner reads — enforces the tenant-private boundary ────────────
    def mining_set(self, *, scope: str = GLOBAL_PUBLIC, tenant: str | None = None,
                   require_verified: bool = True) -> list[Trace]:
        """Return the set of traces eligible to mine deterministic rules.

        This is the choke point for the tenant-private law. For a ``global_public`` mining set, a
        ``tenant_private`` trace is REFUSED unless it has been anonymized AND explicitly approved for global
        use (``anonymized and approved_for_global``). A raw private trace can therefore NEVER train a global
        rule — the miner physically cannot see it through this surface.

        For a ``tenant_private`` mining set you MUST pass the owning ``tenant``; only that tenant's traces
        are returned (a tenant can mine rules over its own private decisions).

        With ``require_verified=True`` (the default and the safe path) only VERIFIED traces are returned —
        raw LLM proposals and consensus runs are excluded from rule mining entirely.
        """
        if scope not in _SCOPES:
            raise TraceStoreError(f"scope must be one of {_SCOPES}, got {scope!r}")

        if scope == GLOBAL_PUBLIC:
            out: list[Trace] = []
            for t in self.all():
                if require_verified and not t.verified:
                    continue
                if t.scope == TENANT_PRIVATE:
                    # the law: a tenant_private trace may only enter a global mining set when anonymized AND
                    # approved. Otherwise it is silently excluded — it cannot train a global rule.
                    if not (t.anonymized and t.approved_for_global):
                        continue
                out.append(t)
            return out

        # tenant_private mining set — scoped strictly to ONE tenant's own traces.
        if not tenant:
            raise TenantBoundaryError(
                "a tenant_private mining set requires the owning tenant — refusing an unscoped private read")
        out = []
        for t in self.all():
            if t.tenant_id != tenant:
                continue
            if require_verified and not t.verified:
                continue
            out.append(t)
        return out

    def assert_mineable_global(self, trace: Trace) -> None:
        """Raise :class:`TenantBoundaryError` if ``trace`` is NOT allowed into a global mining set.

        A caller that tries to force a specific ``tenant_private`` trace into the global miner hits this and
        fails loudly — there is no silent path for a private trace into a global rule."""
        if trace.scope == TENANT_PRIVATE and not (trace.anonymized and trace.approved_for_global):
            raise TenantBoundaryError(
                f"tenant_private trace {trace.trace_id!r} cannot train a global rule unless anonymized AND "
                f"approved (anonymized={trace.anonymized}, approved_for_global={trace.approved_for_global})")
        if not trace.verified:
            raise TraceStoreError(
                f"trace {trace.trace_id!r} is not verified — only verified outcomes may be mined into rules")
