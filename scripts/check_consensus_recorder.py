#!/usr/bin/env python3
"""scripts.check_consensus_recorder — proof: multi-model outputs are recorded as EVIDENCE, agreement is
computed, and CONSENSUS ALONE CAN NEVER SERVE A FACT (the load-bearing safety property).

The consensus recorder is the M2 layer: multiple models propose, we record them, score agreement, and
cluster disagreement. It does NOT decide truth. This proof shows:

* **multiple outputs recorded** — a run captures every model's output + its cluster.
* **agreement_score computed** — it is the fraction of outputs in the largest cluster (1.0 unanimous, low
  for total disagreement), computed purely + deterministically over canonical output hashes (no model call,
  no clock, no RNG); re-running yields the identical run id + score.
* **disagreement does NOT promote truth** — a disagreeing run is routed to human review (an ambiguity flag),
  NEVER served as the majority answer.
* **CONSENSUS ALONE CANNOT SERVE A FACT** (negative-tested every which way) — ``can_serve_fact`` is a hard
  ``False`` even when the models are UNANIMOUS; the projected store trace is ``verified=False``; and a
  consensus trace, fed to the pattern miner, distills NO rule (the miner mines only verified outcomes).

Determinism: injected ``now``, hashlib ids, no RNG, no network/model.

CLI: PYTHONPATH=. python3 scripts/check_consensus_recorder.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.consensus import (  # noqa: E402
    ROUTE_HUMAN_REVIEW,
    ROUTE_VALIDATOR,
    ConsensusError,
    ModelOutput,
    record_consensus,
)
from src.baltor.determinism.pattern_miner import mine_patterns  # noqa: E402
from src.baltor.determinism.trace_store import GLOBAL_PUBLIC, TraceStore  # noqa: E402

_T1 = "2026-01-01T00:00:00Z"
_T2 = "2026-12-31T23:59:59Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    common = dict(tenant_id="acme", scope=GLOBAL_PUBLIC, workflow_id="cfpb-recon",
                  step_id="classify-deadline", decision_key="reconcile:deadline_mismatch")

    # 1) MULTIPLE OUTPUTS RECORDED + agreement computed (a clear majority).
    #    m1,m2,m3 say "reg-e-10bd"; m4 says "faq-30d" → 3/4 agreement, one disagreement cluster.
    majority = record_consensus(
        outputs=[
            ModelOutput("m1", {"winner": "reg-e-10bd"}),
            ModelOutput("m2", {"winner": "reg-e-10bd"}),
            ModelOutput("m3", {"winner": "reg-e-10bd"}),
            ModelOutput("m4", {"winner": "faq-30d"}),
        ], now=_T1, **common)
    check("a run records every model output", len(majority.outputs) == 4)
    check("agreement_score = largest cluster / total (3/4 = 0.75)", abs(majority.agreement_score - 0.75) < 1e-9)
    check("clusters are recorded largest-first", majority.clusters[0][1] == ("m1", "m2", "m3"))
    check("the disagreement cluster is exposed", majority.disagreement_clusters and majority.disagreement_clusters[-1][1] == ("m4",))

    # 2) DETERMINISTIC — same outputs (even re-ordered) + a different clock → SAME id + score.
    reordered = record_consensus(
        outputs=[
            ModelOutput("m4", {"winner": "faq-30d"}),
            ModelOutput("m3", {"winner": "reg-e-10bd"}),
            ModelOutput("m1", {"winner": "reg-e-10bd"}),
            ModelOutput("m2", {"winner": "reg-e-10bd"}),
        ], now=_T2, **common)
    check("re-ordering the same model outputs yields the SAME run id (set identity, not order)",
          reordered.run_id == majority.run_id)
    check("a different injected clock does NOT change the run id (deterministic, clock-independent)",
          reordered.created_at != majority.created_at and reordered.run_id == majority.run_id)
    check("agreement_score is reproducible", reordered.agreement_score == majority.agreement_score)

    # 3) DISAGREEMENT does not promote truth — a split run routes to HUMAN REVIEW, not "serve the majority".
    split = record_consensus(
        outputs=[
            ModelOutput("m1", {"winner": "reg-e-10bd"}),
            ModelOutput("m2", {"winner": "faq-30d"}),
        ], now=_T1, **common)
    check("a 50/50 split has low agreement (0.5)", abs(split.agreement_score - 0.5) < 1e-9)
    check("a low-agreement run routes to HUMAN REVIEW (ambiguity flag, not 'serve majority')",
          split.routing() == ROUTE_HUMAN_REVIEW)
    check("a high-agreement run routes to the DETERMINISTIC VALIDATOR for the label (still not 'serve majority')",
          majority.routing() == ROUTE_VALIDATOR)

    # 4) THE LOAD-BEARING NEGATIVE — CONSENSUS ALONE CAN NEVER SERVE A FACT, even when UNANIMOUS.
    unanimous = record_consensus(
        outputs=[
            ModelOutput("m1", {"winner": "reg-e-10bd"}),
            ModelOutput("m2", {"winner": "reg-e-10bd"}),
            ModelOutput("m3", {"winner": "reg-e-10bd"}),
        ], now=_T1, **common)
    check("a UNANIMOUS run has agreement 1.0 and is flagged unanimous",
          abs(unanimous.agreement_score - 1.0) < 1e-9 and unanimous.is_unanimous)
    check("can_serve_fact is False even when the models are UNANIMOUS (consensus is evidence, not truth)",
          unanimous.can_serve_fact is False)
    check("can_serve_fact is False for the majority run too", majority.can_serve_fact is False)
    check("can_serve_fact is False for the split run too", split.can_serve_fact is False)
    # majority_output is exposed only as evidence — it still cannot serve as a fact.
    check("the majority output is inspectable as EVIDENCE only", unanimous.majority_output() == {"winner": "reg-e-10bd"})
    check("exposing the majority output does NOT make consensus servable", unanimous.can_serve_fact is False)

    # the projected store trace is verified=False — so it can never be mistaken for a verified outcome.
    trace = unanimous.to_trace()
    check("the projected consensus trace is verified=False", trace.verified is False)
    check("the consensus trace records can_serve_fact:False in its decision body",
          trace.decision.get("can_serve_fact") is False)

    # 5) END-TO-END NEGATIVE — a consensus run fed to the pattern miner distills NO rule.
    store = TraceStore()
    # write the SAME unanimous consensus trace several times (different steps) — it should NEVER mine a rule.
    for i in range(5):
        run = record_consensus(
            tenant_id="acme", scope=GLOBAL_PUBLIC, workflow_id="cfpb-recon",
            step_id=f"step-{i}", decision_key="reconcile:deadline_mismatch",
            outputs=[ModelOutput("m1", {"winner": "x"}), ModelOutput("m2", {"winner": "x"})], now=_T1)
        store.append_trace(run.to_trace())
    check("5 consensus traces are recorded in the store", len(store) == 5)
    patterns = mine_patterns(store, scope=GLOBAL_PUBLIC, min_support=1)
    check("the pattern miner distills NO rule from consensus traces alone (consensus is never verified)",
          patterns == [])
    check("the global mining set sees 0 consensus traces (they are unverified evidence)",
          store.mining_set(scope=GLOBAL_PUBLIC, require_verified=True) == [])

    # 6) guard: a run needs ≥2 outputs.
    too_few = False
    try:
        record_consensus(outputs=[ModelOutput("m1", {"winner": "x"})], **common)
    except ConsensusError:
        too_few = True
    check("a consensus run requires ≥2 model outputs", too_few)

    ok = not fails
    print(
        f"\n{'PASS — check_consensus_recorder: multi-model outputs are recorded as evidence; agreement_score is the largest-cluster fraction, computed deterministically (re-order + clock independent); disagreement routes to human review (never serve-the-majority); and CONSENSUS ALONE CAN NEVER SERVE A FACT — can_serve_fact is a hard False even when unanimous, the projected trace is verified=False, and consensus traces fed to the miner distill NO rule.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: consensus recorder (evidence, not truth; consensus alone cannot serve a fact).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
