#!/usr/bin/env python3
"""Foundry contracts — the one object and protocol every stage shares.

The Evidence-Driven Component Factory threads a single ``Candidate`` through
eight modular stages (``_repos/shared-backend-components/context/architecture/evidence-driven-component-factory.md``).
A stage is ``Stage.run(batch, ctx) -> batch``: it annotates candidates and drops
the unworthy *with a reason*, never silently passing filler downstream.

**The anti-filler guarantee lives here.** ``Candidate.evidence_status()`` requires
all three pillars before a candidate may be minted:

  1. a measured **GAP** — the bare model demonstrably fails the task;
  2. a real licensed **SOURCE** — ``source_url`` + ``author`` + ``license``;
  3. a measured **LIFT** — ``pipeline_score - bare_model_score > 0``.

A cross-product clone (the old ``daily_thousand_component_seeds`` path) has none
of these, so it can never clear the gate. Filler is impossible by construction,
not by cleanup.

stdlib-only; no model calls. Durability taxonomy is imported from its single
source (`scripts.eval.reason_codes`) — never re-defined here (no magic values).

Run ``python -m scripts.foundry.contracts`` for the offline self-test.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, runtime_checkable

from scripts.eval.reason_codes import DURABILITY_CLASSES, durability_class, is_structural

# --- Canonical funnel checkpoints — the ONLY places a count is reported ------
# Ordered narrowing of the pipeline. The daily contract reports this funnel,
# never a flat "generated" number (_repos/_shared/codex/master-goal.md).
FUNNEL_STAGES: tuple[str, ...] = (
    "areas_probed",     # 0  gap discovery: task families examined
    "gaps_confirmed",   # 0  bare model measurably failed + a source plausibly exists
    "sources_found",    # 1  an authoritative, licensed source acquired
    "drafts_built",     # 2  source mined into typed component drafts
    "standardized",     # 3  schema-valid, hashed, canonically-IDed
    "novel",            # 4  survived dedup (SimHash + LSH + source-url)
    "lift_measured",    # 5  bare-vs-pipeline delta computed on held-out tasks
    "promoted",         # 6  cleared the gate: delta>0 AND durable AND sourced AND novel
)

# --- Terminal decisions a candidate may carry --------------------------------
ALIVE = "alive"         # still advancing through the pipeline
CULL = "cull"           # rejected (filler / dup / no lift) — never minted
REVIEW = "review"       # uncertain — routed to a human review ticket
PROMOTED = "promoted"   # minted as a real component (lifecycle: experimental)

# The 14 catalog component types (storage names) -> seven-primitive label.
# Single source for what target_type values are legal; mirrors
# _repos/shared-backend-components/docs/concepts/component-taxonomy-and-stages.md.
PRIMITIVE_BY_TYPE: dict[str, str] = {
    "knowledge-pack": "Knowledge Corpus",
    "dataset": "Knowledge Corpus",
    "rule-pack": "IfStatement",
    "logic-pack": "IfStatement",
    "persona": "Action",
    "tool": "Action",
    "processor": "Action",
    "harness": "Action",
    "adapter": "Action",
    "rubric": "Action",
    "benchmark": "Action",
    "pipeline": "Loop / Flow",
    "pattern": "Loop / Flow",
}
LEGAL_TARGET_TYPES: frozenset[str] = frozenset(PRIMITIVE_BY_TYPE)


@dataclass
class Candidate:
    """One prospective component, threaded through every stage.

    The three evidence dicts (``gap``, ``source``, ``lift``) are the anti-filler
    proof; derived fields are filled by the stages that own them. ``decision``
    + ``reasons`` + ``stage_log`` make every drop auditable.
    """

    # --- the component itself (filled by construction → standardize) ---------
    target_type: str = ""                       # one of LEGAL_TARGET_TYPES
    body: dict[str, Any] = field(default_factory=dict)   # the schema-valid definition
    component_id: str = ""                       # canonical {type}/{slug}
    content_hash: str = ""                        # formatting-invariant body hash
    version_hash: str = ""                        # version-definition hash

    # --- pillar 1: the measured GAP (why this should exist at all) -----------
    # {id, summary, mechanism, lift_reason, retrievability_tier,
    #  model_independent_score, failure_samples: [{task, bare_answer, correct, ...}]}
    gap: dict[str, Any] = field(default_factory=dict)

    # --- pillar 2: the real licensed SOURCE ----------------------------------
    # {source_url, author, license, source_kind}
    source: dict[str, Any] = field(default_factory=dict)

    # --- pillar 3: the measured LIFT -----------------------------------------
    # {bare_score, pipeline_score, delta, n, durability_class, decay_signal, judge}
    lift: dict[str, Any] | None = None

    # --- derived: novelty (filled by Stage 4) --------------------------------
    # {simhash, is_duplicate, nearest_id, hamming, jaccard, source_key, suspect}
    novelty: dict[str, Any] | None = None

    # --- control / audit -----------------------------------------------------
    decision: str = ALIVE
    reasons: list[str] = field(default_factory=list)
    stage_log: list[dict[str, Any]] = field(default_factory=list)

    # ── lifecycle helpers ────────────────────────────────────────────────────
    @property
    def alive(self) -> bool:
        """True while the candidate may still advance to the next stage."""
        return self.decision == ALIVE

    def mark(self, stage: str, status: str, note: str = "", ms: float = 0.0) -> None:
        """Append a per-stage audit record (always, pass or fail)."""
        self.stage_log.append(
            {"stage": stage, "status": status, "note": note, "ms": round(ms, 2)}
        )

    def drop(self, stage: str, reason: str, decision: str = CULL) -> "Candidate":
        """Terminally reject (``cull``) or park for review; records the reason."""
        if decision not in (CULL, REVIEW):
            raise ValueError(f"drop decision must be {CULL!r} or {REVIEW!r}, got {decision!r}")
        self.decision = decision
        self.reasons.append(reason)
        self.mark(stage, decision, reason)
        return self

    def promote(self, stage: str = "gate") -> "Candidate":
        """Mint as a real component. Caller must have checked ``evidence_status``."""
        self.decision = PROMOTED
        self.mark(stage, PROMOTED, self.component_id or self.target_type)
        return self

    # ── the anti-filler gate (the load-bearing invariant) ────────────────────
    def evidence_status(self, *, lift_floor: float = 0.0) -> tuple[bool, list[str]]:
        """Are all three evidence pillars present and a positive measured lift?

        Returns ``(ok, missing)``. ``ok`` is True only when a gap is measured, a
        licensed source is attached, AND a positive lift delta was measured above
        ``lift_floor``. This is exactly the condition the gate enforces; it is the
        reason a clone (no gap, no source, no delta) can never be minted.
        """
        missing: list[str] = []

        # pillar 1 — a measured gap with real failure evidence
        gap_ok = bool(self.gap.get("id")) and (
            bool(self.gap.get("failure_samples"))
            or float(self.gap.get("model_independent_score") or 0.0) > 0.0
        )
        if not gap_ok:
            missing.append("gap: no measured bare-model failure / model-independent signal")

        # pillar 2 — a real, attributable, licensed source
        src = self.source or {}
        if not (src.get("source_url") and src.get("license") and src.get("author")):
            missing.append("source: missing source_url / author / license")

        # pillar 3 — a measured positive lift
        if not self.lift or self.lift.get("delta") is None:
            missing.append("lift: not measured (no bare-vs-pipeline delta)")
        else:
            delta = float(self.lift.get("delta") or 0.0)
            if delta <= lift_floor:
                missing.append(f"lift: delta {delta:+.3f} <= floor {lift_floor:.3f} (no capability gain)")

        return (not missing), missing

    @property
    def is_structural_lift(self) -> bool:
        """True when the lift will survive the next model (the moat)."""
        reason = (self.gap or {}).get("lift_reason")
        return is_structural(reason)

    @property
    def durability(self) -> str:
        return durability_class((self.gap or {}).get("lift_reason"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def short(self) -> str:
        return f"{self.component_id or self.target_type or '<unbuilt>'} [{self.decision}]"


# --------------------------------------------------------------------------- #
# Stage protocol
# --------------------------------------------------------------------------- #
@runtime_checkable
class Stage(Protocol):
    """A pipeline stage: pure-ish transform over a candidate batch.

    Implementations annotate candidates (and ``drop`` the unworthy) and return
    the *same list* — the orchestrator decides which advance (``c.alive``). A
    stage MUST NOT silently discard candidates; every removal is a recorded
    ``drop`` so the funnel and reject log stay honest.
    """

    name: str

    def run(self, batch: list[Candidate], ctx: "FoundryContext") -> list[Candidate]:
        ...


class BaseStage:
    """Convenience base: gives a ``name`` and a timed ``__call__`` wrapper."""

    name: str = "stage"

    def run(self, batch: list[Candidate], ctx: "FoundryContext") -> list[Candidate]:  # pragma: no cover
        raise NotImplementedError

    def __call__(self, batch: list[Candidate], ctx: "FoundryContext") -> list[Candidate]:
        start = time.monotonic()
        out = self.run(batch, ctx)
        ctx.ledger.stage_timings_ms[self.name] = (
            ctx.ledger.stage_timings_ms.get(self.name, 0.0) + (time.monotonic() - start) * 1000.0
        )
        return out


# --------------------------------------------------------------------------- #
# Config + context
# --------------------------------------------------------------------------- #
@dataclass
class FoundryConfig:
    """Tunables for one run. Single source for the knobs; no scattered literals."""

    lift_floor: float = 0.0          # delta MUST exceed this (hard floor)
    require_structural: bool = False  # if True, only structural-durability lifts promote
    # Human-in-the-loop: "the LLM doesn't know what it doesn't know." Gate-passing
    # components of these types are stamped pending_human approval (not auto-visible),
    # as is anything whose gap was confirmed ONLY by an LLM probe.
    human_approval_types: frozenset = frozenset({"knowledge-pack", "dataset"})
    human_approval_for_llm_only_gaps: bool = True
    hamming_max: int = 3              # SimHash near-dup threshold
    jaccard_min: float = 0.60         # structural-fit near-dup threshold
    partition_size: int = 1000        # one partition = one worker = one source vein
    daily_promoted_target: int = 10_000  # the north-star yield (promoted, not generated)
    model_call_budget: int | None = None  # cap model/agent calls per run (None = unbounded)
    offline: bool = True              # offline = deterministic defaults, zero model cost


def new_run_id(now_s: float | None = None) -> str:
    """Stable, sortable run id from wall-clock (no randomness → resume-friendly)."""
    t = time.gmtime(now_s if now_s is not None else time.time())
    return time.strftime("%Y%m%d%H%M%S", t)


@dataclass
class FoundryContext:
    """Shared state threaded into every stage."""

    config: FoundryConfig = field(default_factory=FoundryConfig)
    run_id: str = field(default_factory=new_run_id)
    partition: str = ""               # e.g. an area / source-surface key
    ledger: "FunnelLedger" = None      # type: ignore[assignment]
    live_corpus: list[Any] = field(default_factory=list)  # for novelty (CorpusEntry-like)
    model_calls: int = 0              # running count, checked against budget

    def __post_init__(self) -> None:
        if self.ledger is None:
            self.ledger = FunnelLedger(run_id=self.run_id, partition=self.partition)

    def spend_model_call(self, n: int = 1) -> bool:
        """Account for a model/agent call; return False if the budget is exhausted."""
        budget = self.config.model_call_budget
        if budget is not None and self.model_calls + n > budget:
            return False
        self.model_calls += n
        return True


# --------------------------------------------------------------------------- #
# Funnel ledger — the honest report (promoted, not generated)
# --------------------------------------------------------------------------- #
@dataclass
class FunnelLedger:
    """Per-run funnel + reject log. The daily metric is ``promoted``, never
    ``generated`` — this object exists to keep that honest and auditable."""

    run_id: str
    partition: str = ""
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    checkpoints: dict[str, int] = field(default_factory=dict)      # funnel stage -> alive count
    rejects: dict[str, dict[str, int]] = field(default_factory=dict)  # stage -> reason-head -> count
    stage_timings_ms: dict[str, float] = field(default_factory=dict)
    promoted_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def checkpoint(self, funnel_stage: str, alive_count: int) -> None:
        if funnel_stage not in FUNNEL_STAGES:
            raise ValueError(f"unknown funnel stage {funnel_stage!r}; expected one of {FUNNEL_STAGES}")
        self.checkpoints[funnel_stage] = alive_count

    @staticmethod
    def _reason_head(reason: str) -> str:
        """Bucket a free-text reason by its prefix before the first ':'."""
        return reason.split(":", 1)[0].strip() or "unspecified"

    def record_rejects(self, stage_name: str, dropped: list[Candidate]) -> None:
        bucket = self.rejects.setdefault(stage_name, {})
        for c in dropped:
            head = self._reason_head(c.reasons[-1]) if c.reasons else "unspecified"
            bucket[head] = bucket.get(head, 0) + 1

    def record_promoted(self, candidates: list[Candidate]) -> None:
        for c in candidates:
            if c.decision == PROMOTED:
                self.promoted_ids.append(c.component_id or c.target_type)

    @property
    def promoted(self) -> int:
        return len(self.promoted_ids)

    def summary_line(self) -> str:
        c = self.checkpoints
        ordered = " → ".join(f"{s}={c[s]}" for s in FUNNEL_STAGES if s in c)
        return f"[{self.run_id}{('/' + self.partition) if self.partition else ''}] {ordered}  ::  promoted={self.promoted}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "partition": self.partition,
            "started_at": self.started_at,
            "funnel": {s: self.checkpoints.get(s) for s in FUNNEL_STAGES},
            "promoted": self.promoted,
            "promoted_ids": self.promoted_ids,
            "rejects": self.rejects,
            "stage_timings_ms": {k: round(v, 1) for k, v in self.stage_timings_ms.items()},
            "notes": self.notes,
            "metric_note": "Report PROMOTED, never generated. promoted = cleared the measured-lift gate.",
        }


# --------------------------------------------------------------------------- #
# self-test (offline; no model, no network)
# --------------------------------------------------------------------------- #
def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # A bare clone (no evidence) must fail every pillar.
    clone = Candidate(target_type="knowledge-pack", body={"id": "knowledge-pack/daily-0007"})
    ok, missing = clone.evidence_status()
    check("clone fails evidence gate", not ok)
    check("clone missing all three pillars", len(missing) == 3, str(missing))

    # A fully-evidenced candidate with positive lift passes.
    good = Candidate(
        target_type="knowledge-pack",
        component_id="knowledge-pack/csddd-articles",
        body={"id": "knowledge-pack/csddd-articles", "type": "knowledge-pack"},
        gap={
            "id": "gap/csddd-article-citation",
            "summary": "Bare model misattributes CSDDD articles.",
            "lift_reason": "esoteric_rule",
            "failure_samples": [{"task": "cite art. 8 CSDDD", "bare_answer": "wrong", "correct": False}],
            "model_independent_score": 0.82,
        },
        source={"source_url": "https://eur-lex.europa.eu/x", "author": "EU", "license": "CC-BY-4.0",
                "source_kind": "other"},
        lift={"bare_score": 0.42, "pipeline_score": 0.83, "delta": 0.41, "n": 20,
              "durability_class": "transient", "decay_signal": "watch"},
    )
    ok, missing = good.evidence_status()
    check("fully-evidenced candidate passes", ok, str(missing))

    # Positive structural example must read as structural / durable.
    structural = Candidate(gap={"lift_reason": "no_addressable_source"})
    check("structural lift detected", structural.is_structural_lift)
    check("durability class structural", structural.durability == "structural")

    # Zero/negative measured delta must be rejected even with gap+source.
    no_gain = Candidate(
        target_type="tool",
        gap={"id": "g", "model_independent_score": 0.5},
        source={"source_url": "u", "author": "a", "license": "MIT"},
        lift={"delta": 0.0},
    )
    ok, missing = no_gain.evidence_status()
    check("zero-delta candidate rejected", not ok, str(missing))
    check("zero-delta reason mentions floor", any("floor" in m for m in missing))

    # drop() / alive semantics
    d = Candidate(target_type="tool")
    check("starts alive", d.alive)
    d.drop("novelty", "near-duplicate: of tool/x")
    check("dropped no longer alive", not d.alive)
    check("drop recorded reason", d.reasons and "near-duplicate" in d.reasons[-1])

    # Ledger funnel + reject bucketing
    led = FunnelLedger(run_id="testrun", partition="esg")
    led.checkpoint("areas_probed", 5)
    led.checkpoint("promoted", 2)
    led.record_rejects("novelty", [d])
    check("ledger buckets reject head", led.rejects["novelty"].get("near-duplicate") == 1, str(led.rejects))
    promoted_c = good.promote()
    led.record_promoted([promoted_c])
    check("ledger counts promoted", led.promoted == 1)
    check("ledger funnel stage validated", "areas_probed" in led.to_dict()["funnel"])
    try:
        led.checkpoint("not_a_stage", 1)
        check("rejects unknown funnel stage", False)
    except ValueError:
        check("rejects unknown funnel stage", True)

    # Stage protocol is satisfiable
    class _Noop(BaseStage):
        name = "noop"

        def run(self, batch, ctx):
            for c in batch:
                c.mark(self.name, "ok")
            return batch

    ctx = FoundryContext(partition="esg")
    out = _Noop()([good], ctx)
    check("BaseStage runs + times", out and "noop" in ctx.ledger.stage_timings_ms)
    check("Stage protocol isinstance", isinstance(_Noop(), Stage))

    # type → primitive mapping covers the 14 storage types
    check("primitive map has knowledge-pack", PRIMITIVE_BY_TYPE["knowledge-pack"] == "Knowledge Corpus")
    check("primitive map has rule-pack=IfStatement", PRIMITIVE_BY_TYPE["rule-pack"] == "IfStatement")

    # to_dict round-trips through json
    json.dumps(good.to_dict())
    json.dumps(led.to_dict())
    check("dataclasses json-serializable", True)

    print(f"\n{'all contracts self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    print("  durability classes:", DURABILITY_CLASSES)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
