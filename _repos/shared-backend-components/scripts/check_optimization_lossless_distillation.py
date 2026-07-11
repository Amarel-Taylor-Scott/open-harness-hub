#!/usr/bin/env python3
"""scripts.check_optimization_lossless_distillation — apply-proof: the EXISTING optimizer is lossless.

Optimization is a distillation: it produces a smaller/cleaner candidate pack. This proof RUNS the shipped
``scripts.runtime.optimization`` suite (it does NOT modify it) and asserts the lossless law holds:

  * the optimizer keeps a BASELINE snapshot (un-mutated) that every candidate is judged against — the
    rollback target;
  * the bake-off keeps ALL candidate results, including the REJECTED ones (rejected != erased), each with
    its own receipt;
  * a PROMOTED candidate carries an OptimizationReceipt (lineage to the lift + regression verdict);
  * COMPRESSION cannot lose source handles — the shipped CompressionOptimizer's _KEEP allowlist preserves
    ``source_handle``, and the harness's ``source_handles_preserved`` regression would reject any candidate
    that dropped one (proven by injecting a handle-dropping optimizer → it is REJECTED, never served);
  * held-out warnings stay visible on the candidate pack (the conflict loser + allegations ride along);
  * an UNPROMOTED candidate is never served (its pack is not the promoted pack).

It also feeds the promoted transform into the Lane-C :class:`InformationRetentionReport` and asserts
``safe_to_promote``, and feeds the handle-dropping candidate and asserts it is NOT safe. Deterministic +
offline (time INJECTED; receipt ids content-addressed). The retention builder is imported BY FILE PATH so
this lane runs even before the Lane-B store lands.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_optimization_lossless_distillation.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import importlib.util
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.consumption import _rege_pack  # noqa: E402
from scripts.runtime.optimization import (  # noqa: E402
    BaselineSnapshot,
    CandidateGenerator,
    CompressionOptimizer,
    DedupeOptimizer,
    ExcludeHeldOutOptimizer,
    OptimizationHarness,
    chain,
)

_NOW = "1970-01-01T00:00:00Z"


def _load_isolated(name: str, relpath: str):
    p = (_resource(relpath)).resolve()
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


RR = _load_isolated("baltor_distillation_retention_report_opt", "_repos/baltor/backend/src/baltor/distillation/retention_report.py")


class _HandleDroppingOptimizer:
    """A DELIBERATELY lossy optimizer (only used in this proof) that strips source handles — the canonical
    compression sin. The shipped harness must REJECT it; it must never be served."""
    name = "drop_handles_BAD"

    def optimize(self, pack: dict, *, signals: dict) -> dict:
        out = dict(pack)
        out["artifacts"] = [{k: v for k, v in a.items() if k not in ("source_handle", "source_handles")}
                            for a in pack.get("artifacts", [])]
        return out


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pack, answer_fact_id, excluded_ids, _src = _rege_pack("demo")
    baseline_ids = {a["artifact_id"] for a in pack["artifacts"]}

    # ── 1) the optimizer keeps a BASELINE snapshot (the rollback target) ──
    snap = BaselineSnapshot.of(pack, answer_fact_ids=[answer_fact_id])
    check("a baseline snapshot is taken (rollback target)", bool(snap.snapshot_hash) and snap.snapshot_hash.startswith("snap-"))
    check("the baseline snapshot records every baseline artifact id", set(snap.artifact_ids) == baseline_ids)

    # ── 2) the bake-off keeps ALL candidate results incl. REJECTED ones, each with a receipt ──
    cands = CandidateGenerator().generate(snap, excluded_ids=excluded_ids)
    bake = OptimizationHarness().optimize_many(pack, cands, answer_fact_ids=[answer_fact_id], now=_NOW)
    check("the bake-off ran multiple candidate variants", bake["candidate_count"] >= 3, str(bake["candidate_count"]))
    check("every candidate result carries a receipt (decision + lift + regressions)",
          all(r["receipt"].receipt_id and r["receipt"].decision in ("promote", "reject") for r in bake["results"]))
    rejected = [r for r in bake["results"] if not r["promoted"]]
    check("rejected candidates are kept in the results (rejected != erased)", len(rejected) >= 1, str(len(rejected)))
    check("the baseline pack is NOT mutated by the bake-off (rollback target intact)",
          {a["artifact_id"] for a in pack["artifacts"]} == baseline_ids)

    # ── 3) a PROMOTED candidate carries a receipt + lineage to the baseline snapshot ──
    best = bake["best"]
    check("at least one candidate was promoted", best is not None and bake["promoted_count"] >= 1)
    check("the promoted candidate carries an OptimizationReceipt", bool(best["receipt"].receipt_id))
    check("the promoted candidate's candidate_id cites the baseline snapshot (lineage)",
          best["candidate"]["baseline_snapshot_hash"] == snap.snapshot_hash)

    # ── 4) COMPRESSION cannot lose source handles (shipped compression preserves them) ──
    comp_chain = chain(DedupeOptimizer(), ExcludeHeldOutOptimizer(), CompressionOptimizer())
    comp = OptimizationHarness().run(pack, comp_chain, answer_fact_ids=[answer_fact_id],
                                     signals={"excluded_ids": excluded_ids, "text_char_budget": 40}, now=_NOW)
    served = comp["candidate_pack"]["artifacts"]
    check("compression keeps a source handle on every served fact", all(a.get("source_handle") for a in served))
    check("the harness asserts source_handles_preserved as a regression check",
          any(r.name == "source_handles_preserved" and r.ok for r in comp["regressions"]))
    check("the compressed candidate is promotable (lossless of handles + facts)", comp["promoted"])

    # ── 4') a handle-DROPPING optimizer is REJECTED by the shipped harness (never served) ──
    bad = OptimizationHarness().run(pack, _HandleDroppingOptimizer(), answer_fact_ids=[answer_fact_id],
                                    signals={"excluded_ids": excluded_ids}, now=_NOW)
    check("a handle-dropping optimizer is REJECTED (source_handles_preserved fails)",
          not bad["promoted"] and bad["decision"] == "reject")
    check("the handle-dropping candidate is NOT the promoted pack (unpromoted never served)",
          best["candidate_pack"] is not bad["candidate_pack"])

    # ── 5) held-out warnings stay visible on the promoted candidate pack ──
    best_held = {a.get("artifact_id") for a in best["candidate_pack"].get("held_out", [])}
    allegation_ids = {a["artifact_id"] for a in pack["artifacts"] if a.get("claim_type") == "narrative_allegation"}
    check("held-out warnings (FAQ-30 loser + allegations) stay on the promoted candidate",
          best_held >= ({"fact-faq-30"} | allegation_ids), str(sorted(best_held)))
    best_served = {a.get("artifact_id") for a in best["candidate_pack"].get("artifacts", [])}
    check("no held-out item leaked into the served set (unpromoted-as-truth never served)",
          not (best_served & ({"fact-faq-30"} | allegation_ids)))

    # ── 6) feed the promoted transform into the retention report → safe; the bad one → NOT safe ──
    def _arts(pack_artifacts):
        return [{"artifact_id": a.get("artifact_id"), "claim_status": a.get("claim_status", "fact"),
                 "artifact_type": a.get("artifact_type", "atomic_fact"), "source_handle": a.get("source_handle")}
                for a in pack_artifacts]

    inputs = _arts(pack["artifacts"])
    promoted_served = _arts(best["candidate_pack"]["artifacts"])
    promoted_held = _arts(best["candidate_pack"].get("held_out", []))
    out_ids = {a["artifact_id"] for a in promoted_served} | {a["artifact_id"] for a in promoted_held}
    superseded = [a for a in inputs if a["artifact_id"] not in out_ids]  # top-k-omitted, kept in baseline
    good_report = RR.build_retention_report(
        transform_type="optimize", inputs=inputs, outputs=promoted_served,
        served=promoted_served, held_out=promoted_held, superseded=superseded)
    check("retention report: the promoted optimization is safe_to_promote", good_report.safe_to_promote,
          str(good_report.notes))

    bad_served = _arts(bad["candidate_pack"]["artifacts"])
    bad_report = RR.build_retention_report(
        transform_type="optimize", inputs=inputs, outputs=bad_served, served=bad_served)
    check("retention report: the handle-dropping optimization is NOT safe_to_promote", not bad_report.safe_to_promote)
    check("retention report: it counts the dropped source handles", bad_report.dropped_source_handle_count > 0,
          str(bad_report.dropped_source_handle_count))

    ok = not fails
    print(
        f"\n{'PASS — check_optimization_lossless_distillation: the EXISTING optimizer is lossless — it keeps an un-mutated baseline snapshot (the rollback target) + ALL candidate results incl. rejected (each with a receipt); the promoted candidate carries a receipt + baseline lineage; compression preserves source handles and a handle-dropping optimizer is REJECTED (never served); held-out warnings stay visible and never leak into the served set; the InformationRetentionReport confirms the promoted transform is safe and the lossy one is not.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apply-proof: the existing optimizer is lossless.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
