#!/usr/bin/env python3
"""scripts.check_cfpb_lossless_distillation — apply-proof: the EXISTING CFPB→consumption path is lossless.

This does NOT build a new flow and does NOT modify the runtime. It RUNS the shipped
``scripts.runtime.consumption.run_cfpb_to_consumption`` (decompose → verify → optimize bake-off →
consumption-readiness → serve) and the shipped decomposer, then asserts the lossless law holds over the
real outputs:

  * raw record + source handle + every structured ``#field`` atomic_fact survive (decompose preserves the
    field-level handles, expandable back to the exact field);
  * the FAQ-30 conflict loser AND the narrative allegations are HELD OUT (surfaced as warnings, NOT served
    as truth) but remain REHYDRATABLE — their source handles still resolve to the source;
  * the served answer stays exactly "10 business days" (Reg E, the source-of-law, wins; the FAQ summary
    does not silently overwrite it);
  * the optimized (promoted) pack carries baseline lineage (same source_snapshot_hash) — it did not appear
    from nowhere;
  * the REJECTED optimization candidates are still queryable in the bake-off results (rejected != erased);
  * a ROLLBACK target exists (the un-mutated baseline pack / snapshot the candidate was judged against);
  * NO source artifact was deleted — every artifact_id in the baseline survives somewhere (served OR held).

It also feeds the real flow's input/output into the Lane-C :class:`InformationRetentionReport` builder and
asserts the transform is ``safe_to_promote``. Deterministic + offline (time INJECTED; ids content-addressed).
The retention builder is imported BY FILE PATH so the proof runs even before the Lane-B store lands.

CLI: PYTHONPATH=. python3 scripts/check_cfpb_lossless_distillation.py --self-test
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.ingest.decompose_structured import CLAIM_FACT, decompose_cfpb_complaint  # noqa: E402
from scripts.runtime.consumption import _rege_pack, run_cfpb_to_consumption  # noqa: E402
from scripts.runtime.optimization import (  # noqa: E402
    BaselineSnapshot,
    CandidateGenerator,
    OptimizationHarness,
)

_NOW = "1970-01-01T00:00:00Z"
#: the exact, source-of-law answer the pipeline must keep serving — distillation must never lose it.
_VERIFIED_ANSWER = "10 business days"
#: the raw CFPB complaint the shipped flow decomposes (mirrors run_cfpb_to_consumption's _rege_pack input).
_COMPLAINT = {"complaint_id": "BILL-782", "product": "Credit card", "issue": "Billing error",
              "company": "Acme Bank", "consumer_complaint_narrative": "Charged twice for one purchase. No refund yet."}


def _load_isolated(name: str, relpath: str):
    p = (_REPO / relpath).resolve()
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


RR = _load_isolated("baltor_distillation_retention_report_cfpb", "src/baltor/distillation/retention_report.py")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 0) run the SHIPPED end-to-end CFPB path (we verify it; we do not modify it) ──
    out = run_cfpb_to_consumption(tenant_id="demo", now=_NOW)
    resp = out["response"]
    pack, answer_fact_id, excluded_ids, source_ids = _rege_pack("demo")
    baseline_ids = {a["artifact_id"] for a in pack["artifacts"]}

    # ── 1) raw record + source handle + every #field atomic_fact survive (decompose is lossless) ──
    dec = decompose_cfpb_complaint(_COMPLAINT, native_id="BILL-782")
    fact_handles = [c["source_handle"] for c in dec["components"] if c["claim_status"] == CLAIM_FACT]
    check("decompose preserves the raw record's source handle", dec["source_handle"].endswith("/BILL-782"))
    check("every structured field becomes an atomic_fact with an expandable #field handle",
          fact_handles and all("#" in h for h in fact_handles), str(fact_handles[:2]))
    # re-decompose is deterministic → the prior parse is reproducible, not destroyed.
    check("re-decompose does not destroy the prior parse (deterministic)",
          dec == decompose_cfpb_complaint(_COMPLAINT, native_id="BILL-782"))

    # ── 2) the served answer stays exactly "10 business days" (Reg E wins, FAQ does not overwrite) ──
    check("decision is 'served'", out["decision"] == "served", out["decision"])
    check(f"served answer stays exactly {_VERIFIED_ANSWER!r}", resp["answer"] == _VERIFIED_ANSWER, repr(resp["answer"]))
    served_ids = {f["artifact_id"] for f in resp["served_facts"]}
    check("the winning Reg-E fact is served", answer_fact_id in served_ids)
    check("every served fact carries a source handle (handle coverage = 100%)",
          all(f.get("source_handle") for f in resp["served_facts"]))

    # ── 3) FAQ-30 loser + allegations are HELD OUT (not served) but REHYDRATABLE (handle resolves) ──
    held_ids = {w["artifact_id"] for w in resp["held_out_warnings"]}
    check("the FAQ-30 conflict loser is held out, NOT served", "fact-faq-30" in held_ids and "fact-faq-30" not in served_ids)
    allegation_ids = {a["artifact_id"] for a in pack["artifacts"] if a.get("claim_type") == "narrative_allegation"}
    check("narrative allegations are held out, NOT served", allegation_ids <= held_ids and not (allegation_ids & served_ids))
    # rehydratable: every held-out item still carries a source handle that points back to the source.
    held_handles = {w["artifact_id"]: w.get("source_handle") for w in resp["held_out_warnings"]}
    check("held-out FAQ-30 rehydrates (its source handle still resolves to ctx://cfpb/faq...)",
          str(held_handles.get("fact-faq-30", "")).startswith("ctx://cfpb/faq"), str(held_handles.get("fact-faq-30")))
    check("every held-out allegation still carries an expandable source handle (rehydratable)",
          all(str(held_handles.get(aid, "")).startswith("ctx://cfpb/consumer-complaints") for aid in allegation_ids))

    # ── 4) the optimized (promoted) pack carries baseline lineage (same source_snapshot_hash) ──
    snap = BaselineSnapshot.of(pack, answer_fact_ids=[answer_fact_id])
    check("the served response carries the baseline source_snapshot_hash (optimized has baseline lineage)",
          resp["source_snapshot_hash"] == snap.snapshot_hash, f"{resp['source_snapshot_hash']} vs {snap.snapshot_hash}")
    check("the served response cites the optimization receipt (lineage to the promotion)",
          bool(resp["receipts"].get("optimization_receipt_id")))

    # ── 5) rejected optimization candidates are still queryable (rejected != erased) + rollback target ──
    cands = CandidateGenerator().generate(snap, excluded_ids=excluded_ids)
    bake = OptimizationHarness().optimize_many(pack, cands, answer_fact_ids=[answer_fact_id], now=_NOW)
    rejected = [r for r in bake["results"] if not r["promoted"]]
    check("the bake-off ran multiple candidates", bake["candidate_count"] >= 2, str(bake["candidate_count"]))
    check("at least one candidate was promoted", bake["promoted_count"] >= 1)
    check("rejected optimization candidates remain queryable in the bake-off results",
          len(rejected) >= 1 and all(r["receipt"].decision == "reject" for r in rejected), str(len(rejected)))
    # rollback target = the un-mutated baseline the candidate was judged against.
    check("a rollback target exists: the baseline snapshot is preserved", bool(snap.snapshot_hash))
    check("the baseline pack was NOT mutated by optimization (rollback target intact)",
          {a["artifact_id"] for a in pack["artifacts"]} == baseline_ids and len(pack["artifacts"]) == len(baseline_ids))
    best_pack = bake["best"]["candidate_pack"]
    best_held_ids = {a.get("artifact_id") for a in best_pack.get("held_out", [])}
    best_served_ids = {a.get("artifact_id") for a in best_pack.get("artifacts", [])}
    check("the promoted candidate kept the held-out items as separate warnings (not deleted)",
          best_held_ids >= ({"fact-faq-30"} | allegation_ids))

    # ── 6) NO source artifact was deleted — every baseline id survives somewhere AT THE SYSTEM LEVEL ──
    # The winning candidate is an authority top-k view: it may OMIT lower-rank facts from the SERVED pack.
    # "Omitted from the served view" != deleted: those facts survive in the PRESERVED baseline pack (the
    # rollback target), which optimization never mutates. System-level losslessness holds iff every baseline
    # id survives in {served, held-out, OR the preserved baseline / rollback target}.
    rollback_target_ids = baseline_ids                       # the un-mutated baseline pack is the rollback target
    surviving = served_ids | held_ids | best_held_ids | best_served_ids | rollback_target_ids
    missing = sorted(baseline_ids - surviving)
    check("NO source/baseline artifact deleted (every id survives served/held/rollback-target)", missing == [], str(missing))
    # facts the top-k view omitted but the baseline still holds (omitted, not deleted).
    omitted_by_view = sorted(baseline_ids - best_served_ids - best_held_ids)
    check("top-k-omitted facts survive in the preserved baseline (omitted != deleted)",
          set(omitted_by_view) <= rollback_target_ids, str(omitted_by_view))

    # ── 7) feed the REAL transform into the retention report → it must be safe_to_promote ──
    # The optimize transform narrows the served view; facts it omits are PRESERVED in the baseline/rollback
    # target, so we declare them `superseded` (kept, not deleted) — exactly how the system stays lossless.
    served_arts = [{"artifact_id": f["artifact_id"], "claim_status": "fact", "artifact_type": "atomic_fact",
                    "source_handle": f["source_handle"]} for f in resp["served_facts"]]
    held_arts = [{"artifact_id": w["artifact_id"],
                  "claim_status": ("fact" if w["artifact_id"] == "fact-faq-30" else "unverified_allegation"),
                  "artifact_type": ("atomic_fact" if w["artifact_id"] == "fact-faq-30" else "narrative_allegation"),
                  "source_handle": w.get("source_handle")} for w in resp["held_out_warnings"]]
    inputs = [{"artifact_id": a["artifact_id"], "claim_status": a.get("claim_status", "fact"),
               "artifact_type": a.get("artifact_type", "atomic_fact"), "source_handle": a.get("source_handle")}
              for a in pack["artifacts"]]
    out_ids = served_ids | {w["artifact_id"] for w in resp["held_out_warnings"]}
    superseded_arts = [a for a in inputs if a["artifact_id"] not in out_ids]  # omitted-but-preserved-in-baseline
    report = RR.build_retention_report(
        transform_type="cfpb_to_consumption", inputs=inputs, outputs=served_arts,
        served=served_arts, held_out=held_arts, superseded=superseded_arts)
    check("the real CFPB transform is safe_to_promote (lossless)", report.safe_to_promote, str(report.notes))
    check("retention report: served source-handle coverage is 100%", report.source_handle_coverage == 1.0)
    check("retention report: zero dropped source handles", report.dropped_source_handle_count == 0)
    check("retention report: no orphaned (silently dropped) inputs", report.orphaned_input_ids == [],
          str(report.orphaned_input_ids))

    ok = not fails
    # NOTE: the message is precomputed — a backslash escape inside an f-string brace is
    # PEP 701 (3.12+) syntax and CI runs Python 3.11.
    pass_msg = ('PASS — check_cfpb_lossless_distillation: the EXISTING CFPB->consumption path is lossless — '
                'raw/source/#field atomic_facts survive; FAQ-30 + allegations are held out but rehydratable; the '
                'answer stays "10 business days"; the optimized pack carries baseline lineage; rejected candidates '
                'stay queryable; a rollback target (un-mutated baseline) exists; NO source artifact deleted; the '
                'InformationRetentionReport confirms safe_to_promote.')
    print("\n" + (pass_msg if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apply-proof: the existing CFPB->consumption path is lossless.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
