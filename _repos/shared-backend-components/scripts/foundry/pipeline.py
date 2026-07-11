#!/usr/bin/env python3
"""Foundry pipeline — the orchestrator that threads the eight stages.

Threads a ``Candidate`` batch through gaps → sources → construction → standardize →
novelty → measure → gate → stage_load, recording the **funnel** after each stage
and routing promoted/review candidates to row emission. Partitioned for a worker
fleet (one partition = one source vein = one worker), the design's affordable path
to volume. The reported metric is **promoted**, never "generated".

This is the spine ``run_factory`` always wanted: same walk→gate→dedup→emit shape,
but with the stub proposer replaced by real construction, the orphaned lift gate
wired in, and the **measurement loop** that decides on evidence rather than
heuristics.

Run ``python -m scripts.foundry.pipeline --self-test`` for the end-to-end OFFLINE
proof (gap → source → construct → standardize → novelty → measure → gate →
promoted), or ``--demo`` to print the funnel for the built-in fixture.
"""
from __future__ import annotations

import argparse
import json
import sys

from scripts.foundry.construction import ConstructionStage
from scripts.foundry.contracts import (
    CULL,
    FUNNEL_STAGES,
    PROMOTED,
    REVIEW,
    Candidate,
    FoundryConfig,
    FoundryContext,
)
from scripts.foundry.gaps import GapDiscoveryStage
from scripts.foundry.gate import GateStage
from scripts.foundry.measure import MeasurementStage
from scripts.foundry.novelty import NoveltyStage
from scripts.foundry.sources import RecordedSourceScout, SourceStage
from scripts.foundry.stage_load import StageLoadStage
from scripts.foundry.standardize import StandardizeStage


class Foundry:
    """Configurable eight-stage pipeline. Defaults are the offline (no-cost) impls;
    inject model-backed stages (scout, author, prober, judge, embedder) for production."""

    def __init__(
        self,
        *,
        gaps: GapDiscoveryStage | None = None,
        sources: SourceStage | None = None,
        construction: ConstructionStage | None = None,
        standardize: StandardizeStage | None = None,
        novelty: NoveltyStage | None = None,
        measure: MeasurementStage | None = None,
        gate: GateStage | None = None,
        stage_load: StageLoadStage | None = None,
        config: FoundryConfig | None = None,
    ) -> None:
        self.config = config or FoundryConfig()
        self.gaps = gaps or GapDiscoveryStage()
        self.sources = sources or SourceStage()
        self.construction = construction or ConstructionStage()
        self.standardize = standardize or StandardizeStage()
        self.novelty = novelty or NoveltyStage()
        self.measure = measure or MeasurementStage()
        self.gate = gate or GateStage()
        self.stage_load = stage_load or StageLoadStage()
        # (funnel checkpoint, stage) in execution order
        self.stages = [
            ("gaps_confirmed", self.gaps),
            ("sources_found", self.sources),
            ("drafts_built", self.construction),
            ("standardized", self.standardize),
            ("novel", self.novelty),
            ("lift_measured", self.measure),
            ("promoted", self.gate),
        ]

    def run_partition(self, seeds: list[Candidate], *, partition: str = "", ctx: FoundryContext | None = None) -> dict:
        ctx = ctx or FoundryContext(config=self.config, partition=partition)
        working = [c for c in seeds if c.alive]
        promoted: list[Candidate] = []
        review: list[Candidate] = []

        for funnel_stage, stage in self.stages:
            returned = stage(working, ctx)   # BaseStage.__call__ records timing
            just_dropped = [
                c for c in returned
                if c.decision in (CULL, REVIEW) and c.stage_log and c.stage_log[-1]["stage"] == stage.name
            ]
            ctx.ledger.record_rejects(stage.name, just_dropped)

            if stage is self.gate:
                promoted = [c for c in returned if c.decision == PROMOTED]
                review = [c for c in returned if c.decision == REVIEW]
                ctx.ledger.checkpoint("promoted", len(promoted))
                ctx.ledger.record_promoted(promoted)
                working = []
            else:
                working = [c for c in returned if c.alive]
                count = (
                    len([c for c in working if c.lift is not None])
                    if funnel_stage == "lift_measured" else len(working)
                )
                ctx.ledger.checkpoint(funnel_stage, count)

        # Stage 7 — emit row families for promoted (+ review tickets)
        self.stage_load(promoted + review, ctx)

        return {
            "ledger": ctx.ledger,
            "promoted": promoted,
            "review": review,
            "rows": dict(self.stage_load.rows),
        }

    def run_fleet(self, partitions: dict[str, list[Candidate]]) -> dict:
        """Run each partition (a real fleet parallelizes; here sequential). Aggregates the funnel."""
        results: dict[str, dict] = {}
        agg: dict[str, int] = {s: 0 for s in FUNNEL_STAGES}
        for name, seeds in partitions.items():
            res = self.run_partition(seeds, partition=name)
            results[name] = res
            for s in FUNNEL_STAGES:
                agg[s] += res["ledger"].checkpoints.get(s, 0)
        return {"partitions": results, "aggregate_funnel": agg, "total_promoted": agg.get("promoted", 0)}


# --------------------------------------------------------------------------- #
# built-in offline fixture (a realistic ESG/CSDDD vein) — used by --demo/--self-test
# --------------------------------------------------------------------------- #
def _fixture() -> tuple[Foundry, list[Candidate]]:
    csddd_tasks = [
        {"prompt": "Which CSDDD article sets the due-diligence obligation?",
         "correct_answer": "Article 8", "bare_answer": "Article 19 wrong guess", "pipeline_answer": "Article 8"},
        {"prompt": "Which CSDDD article covers civil liability?",
         "correct_answer": "Article 29", "bare_answer": "Article 4 wrong guess", "pipeline_answer": "Article 29"},
    ]
    nolift_tasks = [  # the pipeline does no better than the bare model → delta 0 → culled
        {"prompt": "trivia the model already knows",
         "correct_answer": "paris", "bare_answer": "paris", "pipeline_answer": "paris"},
    ]
    seeds = [
        Candidate(gap={"id": "gap/csddd-articles", "summary": "Bare model misattributes CSDDD articles.",
                       "lift_reason": "esoteric_rule", "model_independent_score": 0.82,
                       "retrievability_tier": 3, "failure_samples": [{"task": "cite art 8", "correct": False}],
                       "eval_tasks": csddd_tasks}),
        Candidate(gap={"id": "gap/csddd-dup", "summary": "Duplicate from the same source.",
                       "lift_reason": "esoteric_rule", "model_independent_score": 0.8,
                       "failure_samples": [{"x": 1}], "eval_tasks": csddd_tasks}),
        Candidate(gap={"id": "gap/weak", "summary": "Model-flattering, weak gap.",
                       "lift_reason": "long_tail_fact", "model_independent_score": 0.1,
                       "failure_samples": [{"x": 1}], "eval_tasks": csddd_tasks}),
        Candidate(gap={"id": "gap/nolift", "summary": "No real lift — model already does it.",
                       "lift_reason": "weak_reasoning_at_scale", "model_independent_score": 0.6,
                       "failure_samples": [{"x": 1}], "eval_tasks": nolift_tasks}),
    ]
    csddd_source = {"source_url": "https://eur-lex.europa.eu/eli/dir/csddd", "author": "European Union",
                    "license": "CC-BY-4.0", "source_kind": "regulation",
                    "payload": {"name": "CSDDD article corpus", "industry": ["esg", "supply_chain"],
                                "facts": [{"anchor": "Article 8", "text": "Due-diligence obligation."},
                                          {"anchor": "Article 22", "text": "Climate transition plan."},
                                          {"anchor": "Article 29", "text": "Civil liability."}],
                                "rule_family": "grep",
                                "rules": [{"id": "forced-labor-indicator",
                                           "when": "text matches an ILO forced-labour indicator",
                                           "then": "flag for human review",
                                           "pattern": "(?i)forced labou?r|debt bondage", "severity": "high",
                                           "label": "ILO forced-labour indicator"},
                                          {"id": "art8-due-diligence",
                                           "when": "supplier lacks a due-diligence statement",
                                           "then": "cite CSDDD Article 8", "severity": "medium",
                                           "label": "CSDDD Art. 8"}]}}
    catalog = {
        "gap/csddd-articles": csddd_source,
        "gap/csddd-dup": csddd_source,   # SAME source_url ⇒ novelty source-key clone
        "gap/nolift": {"source_url": "https://example.gov/trivia", "author": "Gov", "license": "CC0-1.0",
                       "source_kind": "other",
                       "payload": {"name": "Trivia corpus", "facts": [{"anchor": "x", "text": "y"}]}},
    }
    foundry = Foundry(sources=SourceStage(RecordedSourceScout(catalog)))
    return foundry, seeds


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    foundry, seeds = _fixture()
    res = foundry.run_partition(seeds, partition="esg")
    led = res["ledger"]
    cp = led.checkpoints

    print("\n  FUNNEL: " + led.summary_line() + "\n")

    check("areas_probed = 4", cp.get("areas_probed") == 4, str(cp))
    check("gaps_confirmed = 3 (weak gap dropped)", cp.get("gaps_confirmed") == 3, str(cp))
    check("sources_found = 3", cp.get("sources_found") == 3, str(cp))
    check("drafts_built = 5 (2 types × csddd + dup, 1 × nolift)", cp.get("drafts_built") == 5, str(cp))
    check("standardized = 5", cp.get("standardized") == 5, str(cp))
    check("novel = 3 (same-source clones of both types dropped)", cp.get("novel") == 3, str(cp))
    check("lift_measured = 3", cp.get("lift_measured") == 3, str(cp))
    check("promoted = 2 (no-lift candidate culled)", cp.get("promoted") == 2, str(cp))

    # the promoted set spans TWO primitives from one source — the "beyond harnesses" point
    check("exactly two promoted", len(res["promoted"]) == 2, str([c.short() for c in res["promoted"]]))
    types = {c.target_type for c in res["promoted"]}
    check("promoted a Knowledge Corpus AND a IfStatement", types == {"knowledge-pack", "rule-pack"}, str(types))
    for p in res["promoted"]:
        check(f"{p.target_type} id well-formed", p.component_id.startswith(f"{p.target_type}/"), p.component_id)
        check(f"{p.target_type} has measured positive lift", bool(p.lift) and p.lift["delta"] > 0, str(p.lift))
        check(f"{p.target_type} minted experimental", p.body.get("lifecycle") == "experimental")
        check(f"{p.target_type} satisfies all 3 evidence pillars", p.evidence_status()[0])
    # human-in-the-loop: knowledge is pending_human; the public-regulation rule-pack auto-approves
    statuses = {p.target_type: (p.lift or {}).get("approval_status") for p in res["promoted"]}
    check("knowledge promoted BUT pending human approval", statuses.get("knowledge-pack") == "pending_human", str(statuses))
    check("public-reg rule-pack auto-approved", statuses.get("rule-pack") == "auto", str(statuses))

    # rows: the promoted corpus emitted its 3 knowledge entries (the "knowledge pages")
    rc = {k: len(v) for k, v in res["rows"].items()}
    check("knowledge_entry rows = 3", rc.get("knowledge_entry") == 3, str(rc))
    check("normalized_object rows = 2 (corpus + conditional)", rc.get("normalized_object") == 2, str(rc))
    check("object_embedding flagged placeholder", res["rows"]["object_embedding"][0]["is_placeholder"] is True)

    # reject log is honest about WHY each non-promotion happened
    rj = led.rejects
    check("weak gap rejected at gaps", "weak gap" in json.dumps(rj.get("gaps", {})), str(rj.get("gaps")))
    check("clone rejected at novelty", bool(rj.get("novelty")), str(rj.get("novelty")))
    check("no-lift rejected at gate", bool(rj.get("gate")), str(rj.get("gate")))

    # fleet aggregation across two partitions
    fleet = foundry.run_fleet({"esg-a": _fixture()[1], "esg-b": _fixture()[1]})
    check("fleet aggregates promoted across partitions", fleet["total_promoted"] == 4, str(fleet["aggregate_funnel"]))

    # the anti-filler invariant: NOTHING promotes without gap+source+measured lift
    all_promoted = res["promoted"]
    check("anti-filler: every promoted row is fully evidenced",
          all(c.evidence_status()[0] for c in all_promoted))

    print(f"\n{'ALL pipeline self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _demo() -> int:
    foundry, seeds = _fixture()
    res = foundry.run_partition(seeds, partition="esg")
    print(json.dumps(res["ledger"].to_dict(), indent=2))
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Evidence-driven component foundry — orchestrator.")
    p.add_argument("--self-test", action="store_true", help="end-to-end offline proof")
    p.add_argument("--demo", action="store_true", help="print the funnel ledger for the built-in fixture")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.demo:
        return _demo()
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
