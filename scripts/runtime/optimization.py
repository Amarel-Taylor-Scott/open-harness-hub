#!/usr/bin/env python3
"""scripts.runtime.optimization — the governed Optimization Harness (C43): a SUITE of wrappable, chainable
optimizers + a baseline/candidate/regression/promotion loop.

Optimization is governed improvement, NOT silent speed. Each optimizer is a swappable wrapper behind ONE
stable contract (``optimize(pack, signals) -> pack``) so optimizers compose into a chain. The harness runs a
candidate chain against a BaselineSnapshot, measures lift, runs a RegressionGate (no answer-fact loss, source
handles preserved, no held-out/allegation promoted, no tenant leak, nothing fabricated), and only PROMOTES on
measured lift + zero regressions — emitting a content-addressed OptimizationReceipt. Optimizers consume only
verified (gate-``allow``) artifacts; held-out items never re-enter the promoted pack.

Deterministic + offline: token estimates from string length, receipt ids content-addressed, time INJECTED.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

#: rough, DETERMINISTIC token proxy (≈4 chars/token) — good enough to measure relative reduction offline.
def _tokens(obj) -> int:
    return len(json.dumps(obj, sort_keys=True, ensure_ascii=False)) // 4


def _handles(a: dict) -> list:
    return a.get("source_handles") or ([a["source_handle"]] if a.get("source_handle") else [])


@dataclass
class MetricBundle:
    artifact_count: int
    token_estimate: int
    source_handle_coverage: float   # fraction of artifacts carrying ≥1 source handle
    held_out_present: int           # held-out/allegation artifacts still in the pack (must be 0 after opt)
    duplicate_groups: int

    def to_dict(self) -> dict:
        return {"artifact_count": self.artifact_count, "token_estimate": self.token_estimate,
                "source_handle_coverage": round(self.source_handle_coverage, 4),
                "held_out_present": self.held_out_present, "duplicate_groups": self.duplicate_groups}


def measure(pack: dict, *, signals: dict | None = None) -> MetricBundle:
    arts = pack.get("artifacts", [])
    sig = signals or {}
    excluded = set(sig.get("excluded_ids", ()))
    seen, dup = {}, 0
    for a in arts:
        key = a.get("content_hash") or (a.get("subject"), a.get("predicate"), a.get("object"))
        seen[key] = seen.get(key, 0) + 1
    dup = sum(1 for v in seen.values() if v > 1)
    with_handle = sum(1 for a in arts if _handles(a))
    held = sum(1 for a in arts if a.get("artifact_id") in excluded or a.get("claim_type") == "narrative_allegation")
    return MetricBundle(artifact_count=len(arts), token_estimate=sum(_tokens(a) for a in arts),
                        source_handle_coverage=(with_handle / len(arts)) if arts else 1.0,
                        held_out_present=held, duplicate_groups=dup)


# ── the optimizer wrapper contract: one stable surface so optimizers are swappable + chainable ──
@runtime_checkable
class Optimizer(Protocol):
    name: str
    def optimize(self, pack: dict, *, signals: dict) -> dict: ...


def _clone(pack: dict, artifacts: list) -> dict:
    out = dict(pack)
    out["artifacts"] = artifacts
    return out


class DedupeOptimizer:
    """Collapse artifacts that repeat the same fact (same content_hash, or same subject/predicate/object)."""
    name = "dedupe_facts"

    def optimize(self, pack: dict, *, signals: dict) -> dict:
        seen, kept = set(), []
        for a in pack.get("artifacts", []):
            key = a.get("content_hash") or (a.get("subject"), a.get("predicate"), a.get("object"))
            if key in seen:
                continue
            seen.add(key); kept.append(a)
        return _clone(pack, kept)


class ExcludeHeldOutOptimizer:
    """Drop held-out / conflicted / stale artifacts from the promoted pack; keep them as separate warnings."""
    name = "exclude_held_out"

    def optimize(self, pack: dict, *, signals: dict) -> dict:
        excluded = set(signals.get("excluded_ids", ()))
        kept, warnings = [], list(pack.get("held_out", []))
        for a in pack.get("artifacts", []):
            if a.get("artifact_id") in excluded or a.get("claim_type") == "narrative_allegation":
                warnings.append(a)
            else:
                kept.append(a)
        out = _clone(pack, kept)
        out["held_out"] = warnings
        return out


class AuthorityRankOptimizer:
    """Order by authority rank (then freshness), keeping the strongest support first; optional top-k cap."""
    name = "authority_rank"

    def optimize(self, pack: dict, *, signals: dict) -> dict:
        k = signals.get("top_k")
        ranked = sorted(pack.get("artifacts", []),
                        key=lambda a: (a.get("authority_rank", 0), a.get("freshness", 0), a.get("artifact_id", "")),
                        reverse=True)
        if isinstance(k, int) and k >= 0:
            ranked = ranked[:k]
        return _clone(pack, ranked)


@runtime_checkable
class CompressionProvider(Protocol):
    name: str
    def compress(self, text: str) -> str: ...


class DeterministicCompressionProvider:
    """Offline stdlib stub (the wired adapter). LLMLingua is the cataloged candidate primary behind this seam."""
    name = "compression.stub@v1"

    def compress(self, text: str) -> str:
        return " ".join(str(text).split())  # collapse redundant whitespace; deterministic, lossless of words


class CompressionOptimizer:
    """Compress verbose free-text fields via a CompressionProvider while PRESERVING source handles + structure."""
    name = "compress_text"
    _KEEP = ("artifact_id", "artifact_type", "subject", "predicate", "object", "unit", "source_handle",
             "source_handles", "content_hash", "claim_type", "scope", "tenant_id", "authority_rank",
             "freshness", "fragility")

    def __init__(self, provider: CompressionProvider | None = None) -> None:
        self.provider = provider or DeterministicCompressionProvider()

    def optimize(self, pack: dict, *, signals: dict) -> dict:
        out = []
        budget = signals.get("text_char_budget", 80)
        for a in pack.get("artifacts", []):
            na = {k: v for k, v in a.items() if k in self._KEEP}
            if a.get("text"):
                na["text"] = self.provider.compress(a["text"])[:budget]
            out.append(na)
        return _clone(pack, out)


class CompositeOptimizer:
    """A CHAIN of optimizers applied in order — the 'easily chained' contract. Itself an Optimizer."""

    def __init__(self, optimizers: list) -> None:
        self.optimizers = list(optimizers)
        self.name = "chain[" + ">".join(o.name for o in self.optimizers) + "]"

    def optimize(self, pack: dict, *, signals: dict) -> dict:
        for o in self.optimizers:
            pack = o.optimize(pack, signals=signals)
        return pack


#: the shipped suite — multiple variations of optimization, all behind the one Optimizer contract.
def default_suite() -> dict:
    return {o.name: o for o in (DedupeOptimizer(), ExcludeHeldOutOptimizer(),
                                AuthorityRankOptimizer(), CompressionOptimizer())}


def chain(*optimizers) -> CompositeOptimizer:
    return CompositeOptimizer(list(optimizers))


@dataclass
class Regression:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class OptimizationReceipt:
    receipt_id: str
    pack_id: str
    optimizer: str
    baseline: dict
    candidate: dict
    lift: dict
    regressions: list
    decision: str
    created_at: str
    schema_version: str = "OptimizationReceipt"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "receipt_id": self.receipt_id, "pack_id": self.pack_id,
                "optimizer": self.optimizer, "baseline": self.baseline, "candidate": self.candidate,
                "lift": self.lift, "regressions": list(self.regressions), "decision": self.decision,
                "created_at": self.created_at}


class OptimizationHarness:
    """Run a candidate optimizer against a baseline; promote ONLY on measured lift + zero regressions."""

    def regressions(self, baseline: dict, candidate: dict, *, answer_fact_ids, signals: dict) -> list:
        base_ids = {a.get("artifact_id") for a in baseline.get("artifacts", [])}
        cand = candidate.get("artifacts", [])
        cand_ids = {a.get("artifact_id") for a in cand}
        excluded = set(signals.get("excluded_ids", ()))
        tenant = baseline.get("tenant_id", "")
        base_handles = {a.get("artifact_id"): set(_handles(a)) for a in baseline.get("artifacts", [])}

        regs = []
        regs.append(Regression("answer_facts_preserved", set(answer_fact_ids) <= cand_ids,
                               str(sorted(set(answer_fact_ids) - cand_ids))))
        lost_handles = [a.get("artifact_id") for a in cand if base_handles.get(a.get("artifact_id")) and not set(_handles(a))]
        regs.append(Regression("source_handles_preserved", lost_handles == [], str(lost_handles)))
        promoted_bad = [a.get("artifact_id") for a in cand
                        if a.get("artifact_id") in excluded or a.get("claim_type") == "narrative_allegation"]
        regs.append(Regression("no_held_out_or_allegation_promoted", promoted_bad == [], str(promoted_bad)))
        leaks = [a.get("artifact_id") for a in cand if a.get("tenant_id") and a.get("tenant_id") != tenant
                 and a.get("scope") == "tenant_private"]
        regs.append(Regression("no_tenant_leak", leaks == [], str(leaks)))
        fabricated = sorted(cand_ids - base_ids)
        regs.append(Regression("nothing_fabricated", fabricated == [], str(fabricated)))
        return regs

    def run(self, baseline_pack: dict, optimizer, *, answer_fact_ids, signals: dict | None = None,
            now: str = "1970-01-01T00:00:00Z") -> dict:
        signals = signals or {}
        base_m = measure(baseline_pack, signals=signals)
        candidate_pack = optimizer.optimize(baseline_pack, signals=signals)
        cand_m = measure(candidate_pack, signals=signals)
        regs = self.regressions(baseline_pack, candidate_pack, answer_fact_ids=answer_fact_ids, signals=signals)
        token_saved = base_m.token_estimate - cand_m.token_estimate
        lift = {"token_reduction": token_saved,
                "token_reduction_pct": round(token_saved / base_m.token_estimate, 4) if base_m.token_estimate else 0.0,
                "artifact_reduction": base_m.artifact_count - cand_m.artifact_count}
        improved = token_saved > 0 or lift["artifact_reduction"] > 0
        no_regress = all(r.ok for r in regs)
        decision = "promote" if (improved and no_regress) else "reject"
        body = {"pack_id": baseline_pack.get("pack_id", ""), "optimizer": optimizer.name,
                "decision": decision, "lift": lift}
        rid = "optrcpt-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        receipt = OptimizationReceipt(receipt_id=rid, pack_id=baseline_pack.get("pack_id", ""), optimizer=optimizer.name,
                                      baseline=base_m.to_dict(), candidate=cand_m.to_dict(), lift=lift,
                                      regressions=[r.__dict__ for r in regs], decision=decision, created_at=now)
        return {"decision": decision, "promoted": decision == "promote", "lift": lift,
                "baseline_metrics": base_m, "candidate_metrics": cand_m, "regressions": regs,
                "candidate_pack": candidate_pack, "receipt": receipt}

    def optimize_many(self, baseline_pack: dict, candidates: list, *, answer_fact_ids,
                      now: str = "1970-01-01T00:00:00Z") -> dict:
        """Run MANY candidate variants against the SAME baseline (a bake-off); promote the best non-regressing
        candidate by measured lift. This is what makes Optimization a SUITE of variations, not one optimizer."""
        results = []
        for cand in candidates:
            out = self.run(baseline_pack, cand.optimizer, answer_fact_ids=answer_fact_ids,
                           signals=cand.signals, now=now)
            out["candidate"] = cand.to_dict()
            results.append(out)
        winners = [r for r in results if r["promoted"]]
        winners.sort(key=lambda r: (r["lift"]["token_reduction"], r["lift"]["artifact_reduction"]), reverse=True)
        best = winners[0] if winners else None
        return {"results": results, "best": best, "promoted_count": len(winners), "candidate_count": len(results)}


# ── the SUITE layer: baseline snapshot → candidate variants → bake-off → consumption-readiness ──
@dataclass
class BaselineSnapshot:
    """A frozen fingerprint of the baseline a candidate is judged against (same snapshot for every variant)."""
    pack_id: str
    snapshot_hash: str
    answer_fact_ids: list
    artifact_ids: list
    source_handle_coverage: float

    @staticmethod
    def of(pack: dict, *, answer_fact_ids) -> "BaselineSnapshot":
        arts = pack.get("artifacts", [])
        fp = [(a.get("artifact_id"), a.get("content_hash")) for a in arts]
        h = hashlib.sha256(json.dumps({"fp": sorted(fp), "ans": sorted(answer_fact_ids)}, sort_keys=True).encode()).hexdigest()
        m = measure(pack)
        return BaselineSnapshot(pack_id=pack.get("pack_id", ""), snapshot_hash="snap-" + h[:16],
                                answer_fact_ids=list(answer_fact_ids), artifact_ids=[a.get("artifact_id") for a in arts],
                                source_handle_coverage=m.source_handle_coverage)

    def to_dict(self) -> dict:
        return {"pack_id": self.pack_id, "snapshot_hash": self.snapshot_hash, "answer_fact_ids": self.answer_fact_ids,
                "artifact_ids": self.artifact_ids, "source_handle_coverage": round(self.source_handle_coverage, 4)}


@dataclass
class OptimizationCandidate:
    candidate_id: str
    baseline_snapshot_hash: str
    candidate_type: str
    changed_knobs: dict
    optimizer: object                 # an Optimizer (chain) — runnable
    signals: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"candidate_id": self.candidate_id, "baseline_snapshot_hash": self.baseline_snapshot_hash,
                "candidate_type": self.candidate_type, "changed_knobs": self.changed_knobs,
                "optimizer": getattr(self.optimizer, "name", "?")}


class CandidateGenerator:
    """Generate multiple candidate variants from a baseline by varying knobs. Each candidate is a concrete
    optimizer chain + signals — deterministic, so a bake-off is reproducible."""

    def generate(self, snapshot: BaselineSnapshot, *, excluded_ids=None) -> list:
        excluded = set(excluded_ids or ())
        base = [DedupeOptimizer(), ExcludeHeldOutOptimizer()]
        grid = [
            ("context_pack_dedupe", {"dedupe": True}, chain(DedupeOptimizer()), {"excluded_ids": excluded}),
            ("exclude_held_out", {"exclude_held_out": True}, chain(*base), {"excluded_ids": excluded}),
            ("authority_topk_3", {"top_k": 3}, chain(*base, AuthorityRankOptimizer()), {"excluded_ids": excluded, "top_k": 3}),
            ("compression_budget_80", {"compression": 80}, chain(*base, CompressionOptimizer()), {"excluded_ids": excluded, "text_char_budget": 80}),
            ("compression_budget_40", {"compression": 40}, chain(*base, CompressionOptimizer()), {"excluded_ids": excluded, "text_char_budget": 40}),
            ("strict_conflict_exclusion", {"strict": True, "compression": 60}, chain(*base, AuthorityRankOptimizer(), CompressionOptimizer()), {"excluded_ids": excluded, "text_char_budget": 60}),
        ]
        out = []
        for ctype, knobs, opt, signals in grid:
            cid = "optcand-" + hashlib.sha256(json.dumps({"s": snapshot.snapshot_hash, "t": ctype, "k": knobs}, sort_keys=True).encode()).hexdigest()[:14]
            out.append(OptimizationCandidate(candidate_id=cid, baseline_snapshot_hash=snapshot.snapshot_hash,
                                             candidate_type=ctype, changed_knobs=knobs, optimizer=opt, signals=signals))
        return out


@dataclass
class ConsumptionReadinessReport:
    report_id: str
    pack_id: str
    consumable: bool
    checks: list
    verification_receipt_id: str
    optimization_receipt_id: str
    created_at: str
    schema_version: str = "ConsumptionReadinessReport"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "report_id": self.report_id, "pack_id": self.pack_id,
                "consumable": self.consumable, "checks": list(self.checks),
                "verification_receipt_id": self.verification_receipt_id,
                "optimization_receipt_id": self.optimization_receipt_id, "created_at": self.created_at}


class ConsumptionReadinessGate:
    """The bridge to Consumption: a pack is consumable ONLY if it was verified (gate-allow) AND promoted by the
    optimization harness AND carries receipts AND leaks no held-out/conflict/tenant data. No artifact is
    consumable merely because it exists."""

    def assess(self, pack: dict, *, verification_receipt: dict, optimization_receipt: dict,
               signals: dict | None = None, now: str = "1970-01-01T00:00:00Z") -> ConsumptionReadinessReport:
        sig = signals or {}
        excluded = set(sig.get("excluded_ids", ()))
        arts = pack.get("artifacts", [])
        tenant = pack.get("tenant_id", "")
        checks = []

        def add(name, ok, detail=""):
            checks.append({"name": name, "ok": bool(ok), "detail": detail})

        add("verified", verification_receipt.get("decision") == "allow")
        add("promoted", optimization_receipt.get("decision") == "promote")
        add("receipts_present", bool(verification_receipt.get("receipt_id")) and bool(optimization_receipt.get("receipt_id")))
        leaked = [a.get("artifact_id") for a in arts if a.get("artifact_id") in excluded or a.get("claim_type") == "narrative_allegation"]
        add("no_held_out_or_conflict_served", leaked == [], str(leaked))
        no_handle = [a.get("artifact_id") for a in arts if not _handles(a)]
        add("source_handles_present", no_handle == [], str(no_handle))
        cross = [a.get("artifact_id") for a in arts if a.get("tenant_id") and a.get("tenant_id") != tenant and a.get("scope") == "tenant_private"]
        add("tenant_consistent", cross == [], str(cross))
        consumable = all(c["ok"] for c in checks)
        body = {"pack_id": pack.get("pack_id", ""), "consumable": consumable,
                "vr": verification_receipt.get("receipt_id", ""), "or": optimization_receipt.get("receipt_id", "")}
        rid = "consrdy-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        return ConsumptionReadinessReport(report_id=rid, pack_id=pack.get("pack_id", ""), consumable=consumable,
                                          checks=checks, verification_receipt_id=verification_receipt.get("receipt_id", ""),
                                          optimization_receipt_id=optimization_receipt.get("receipt_id", ""), created_at=now)
