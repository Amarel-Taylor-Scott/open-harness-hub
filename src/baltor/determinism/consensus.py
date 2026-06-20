#!/usr/bin/env python3
"""src.baltor.determinism.consensus — record multi-model outputs as EVIDENCE, never as truth.

The M2 layer of the ladder: multiple models (or multiple runs of one model) produce candidate outputs for
one decision step. We record them, compute an agreement score, and cluster the disagreements. We do NOT
decide truth.

**Consensus is an evidence / ambiguity signal, NOT a label.** This is the load-bearing safety property of
the whole factory, and it is enforced here, not merely documented:

* :attr:`ConsensusRun.can_serve_fact` is ALWAYS ``False``. There is no code path, no agreement threshold,
  not even unanimity, that flips it to ``True``. A fact is served only by a deterministic validator or an
  authority/policy decision (Baltor reconciliation / the consumption gate) — never by "the models agreed".
* :meth:`ConsensusRun.to_trace` writes a ``consensus``-kind trace whose ``verified`` flag is ``False``, so
  the pattern miner (which mines only VERIFIED traces) can never distill a rule from consensus alone.
* High agreement → still routes to the deterministic validator / authority for the label. Low agreement →
  routes to human review (it is an ambiguity flag). :meth:`ConsensusRun.routing` returns which, but neither
  is "serve the majority as the answer".

Determinism: agreement is a pure count over canonical hashes of the outputs (no model call, no clock, no
RNG). The run id is a content hash of the recorded outputs. Stdlib only, fully offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.baltor.determinism.trace_store import (
    EPOCH,
    KIND_CONSENSUS,
    Trace,
    _hash,
    make_trace_id,
)

_ID_ALGO = "sha256"

#: routing destinations when consensus is recorded. NEITHER is "serve the majority as truth".
ROUTE_VALIDATOR = "deterministic_validator"   # agreement high enough → hand to the authority for the LABEL
ROUTE_HUMAN_REVIEW = "human_review"           # disagreement → ambiguity flag, escalate to a human

#: default agreement threshold (fraction of outputs in the largest cluster) below which a run is routed to
#: human review. This gates ROUTING ONLY — it NEVER promotes an output to truth.
DEFAULT_AGREEMENT_THRESHOLD = 0.66


class ConsensusError(Exception):
    """Base class for consensus-recorder failures."""


def _canon_output(output: Any) -> str:
    """Canonical hash of one model's output body — two byte-identical decisions cluster together."""
    return f"{_ID_ALGO}:{_hash(output)}"


@dataclass(frozen=True)
class ModelOutput:
    """One model's (or one run's) structured output for a consensus step.

    ``output`` is the structured decision the model proposed (e.g. ``{"winner": "...", "reason": "..."}``).
    ``model_id`` / ``provider_id`` identify the producer; ``prompt_hash`` is a content hash of the prompt
    (never the prompt text — private prompts stay out of the recorder). It is a PROPOSAL, never a label.
    """
    model_id: str
    output: dict
    provider_id: str = ""
    prompt_hash: str = ""

    @property
    def output_hash(self) -> str:
        return _canon_output(self.output)

    def to_dict(self) -> dict:
        return {"model_id": self.model_id, "provider_id": self.provider_id,
                "prompt_hash": self.prompt_hash, "output": dict(self.output),
                "output_hash": self.output_hash}


@dataclass(frozen=True)
class ConsensusRun:
    """A recorded multi-model run: agreement score + disagreement clusters, recorded as EVIDENCE.

    ``can_serve_fact`` is a hard ``False`` — consensus is never truth. ``agreement_score`` is the fraction
    of outputs in the largest agreement cluster (1.0 = unanimous, near 0 = total disagreement).
    ``clusters`` maps each distinct output hash → the sorted model_ids that produced it.
    """
    run_id: str
    tenant_id: str
    scope: str
    workflow_id: str
    step_id: str
    decision_key: str
    outputs: tuple[ModelOutput, ...]
    agreement_score: float
    clusters: tuple[tuple[str, tuple[str, ...]], ...]  # (output_hash, (model_id, ...)) sorted
    agreement_threshold: float = DEFAULT_AGREEMENT_THRESHOLD
    created_at: str = EPOCH

    #: HARD INVARIANT — consensus can never serve a fact. Not a field a caller can set; a constant property.
    @property
    def can_serve_fact(self) -> bool:
        return False

    @property
    def is_unanimous(self) -> bool:
        return self.agreement_score >= 1.0 and len(self.clusters) == 1

    @property
    def disagreement_clusters(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Every cluster when there is disagreement (>1 distinct output), else empty."""
        return self.clusters if len(self.clusters) > 1 else ()

    def routing(self) -> str:
        """Where this run routes NEXT. NEITHER destination serves the majority output as the answer:
        high agreement → the deterministic validator / authority decides the label; low agreement →
        human review (the disagreement is an ambiguity flag)."""
        return ROUTE_VALIDATOR if self.agreement_score >= self.agreement_threshold else ROUTE_HUMAN_REVIEW

    def majority_output(self) -> dict | None:
        """The output of the LARGEST cluster — exposed ONLY as evidence for a human/validator to inspect.

        This is explicitly NOT a label: callers must route through :meth:`routing` and let the deterministic
        authority decide. Returning it here does not, and cannot, serve it as a fact (``can_serve_fact`` is
        permanently False)."""
        if not self.clusters:
            return None
        top_hash = self.clusters[0][0]  # clusters are sorted largest-first then by hash
        for o in self.outputs:
            if o.output_hash == top_hash:
                return dict(o.output)
        return None

    def to_trace(self) -> Trace:
        """Project this run as a ``consensus``-kind store trace. ``verified`` is ALWAYS False — a consensus
        run is evidence, so the (verified-only) pattern miner can never distill a rule from it."""
        decision = {
            "consensus": True, "agreement_score": round(self.agreement_score, 6),
            "clusters": [[h, list(ms)] for h, ms in self.clusters],
            "routing": self.routing(), "can_serve_fact": False,
        }
        return Trace(
            trace_id=self.run_id, tenant_id=self.tenant_id, scope=self.scope, trace_kind=KIND_CONSENSUS,
            workflow_id=self.workflow_id, step_id=self.step_id, decision_key=self.decision_key,
            decision=decision, decision_value=f"{_ID_ALGO}:{_hash(decision)}",
            verified=False,  # HARD: consensus is never a verified outcome
            content_hash=f"{_ID_ALGO}:{_hash(decision)}", created_at=self.created_at)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id, "tenant_id": self.tenant_id, "scope": self.scope,
            "workflow_id": self.workflow_id, "step_id": self.step_id, "decision_key": self.decision_key,
            "outputs": [o.to_dict() for o in self.outputs],
            "agreement_score": round(self.agreement_score, 6),
            "clusters": [[h, list(ms)] for h, ms in self.clusters],
            "disagreement_clusters": [[h, list(ms)] for h, ms in self.disagreement_clusters],
            "agreement_threshold": self.agreement_threshold, "routing": self.routing(),
            "is_unanimous": self.is_unanimous, "can_serve_fact": self.can_serve_fact,
            "created_at": self.created_at,
        }


def _cluster(outputs: Iterable[ModelOutput]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Group model outputs by identical output hash → sorted clusters (largest first, then by hash)."""
    by_hash: dict[str, list[str]] = {}
    for o in outputs:
        by_hash.setdefault(o.output_hash, []).append(o.model_id)
    clusters = [(h, tuple(sorted(models))) for h, models in by_hash.items()]
    # deterministic order: largest cluster first; ties broken by the (stable) output hash.
    clusters.sort(key=lambda c: (-len(c[1]), c[0]))
    return tuple(clusters)


def record_consensus(*, tenant_id: str, scope: str, workflow_id: str, step_id: str, decision_key: str,
                     outputs: Iterable[ModelOutput],
                     agreement_threshold: float = DEFAULT_AGREEMENT_THRESHOLD,
                     now: str = EPOCH) -> ConsensusRun:
    """Record a multi-model run → :class:`ConsensusRun` (agreement score + disagreement clusters).

    Pure + deterministic: agreement is a count over canonical output hashes; the run id is a content hash
    of the identity-bearing fields. NO model is called (offline). The returned run is EVIDENCE — it never
    decides truth (``can_serve_fact`` is permanently False); the caller routes via :meth:`ConsensusRun.routing`.
    """
    outs = tuple(outputs)
    if len(outs) < 2:
        raise ConsensusError("a consensus run needs ≥2 model outputs (it records multi-model agreement)")
    if not decision_key:
        raise ConsensusError("decision_key is required (the decision step the models are voting on)")

    clusters = _cluster(outs)
    largest = max(len(models) for _, models in clusters)
    agreement_score = largest / len(outs)

    identity = {
        "tenant": tenant_id, "scope": scope, "workflow_id": workflow_id, "step_id": step_id,
        "decision_key": decision_key,
        # order-independent identity: sort canonical JSON of each output so re-ordering the same set of
        # model outputs yields the SAME run id (the set, not the listing order, is the identity).
        "outputs": sorted(json.dumps(o.to_dict(), sort_keys=True, default=str) for o in outs),
        "threshold": agreement_threshold,
    }
    run_id = make_trace_id(_hash(identity), tenant_id)

    return ConsensusRun(
        run_id=run_id, tenant_id=tenant_id, scope=scope, workflow_id=workflow_id, step_id=step_id,
        decision_key=decision_key, outputs=outs, agreement_score=agreement_score, clusters=clusters,
        agreement_threshold=agreement_threshold, created_at=now)
