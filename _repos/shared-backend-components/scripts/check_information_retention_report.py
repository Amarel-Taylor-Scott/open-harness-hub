#!/usr/bin/env python3
"""scripts.check_information_retention_report — proof: the InformationRetentionReport enforces the lossless law.

The retention report is the system-level dual of the optimizer's regression gate: given ONE transform's
input + output artifacts (plus held-out / rejected / superseded lists and lineage signals) it produces a
verdict whose ``safe_to_promote`` is True ONLY when nothing truth-bearing was lost. This proof drives the
canonical attacks and confirms each is caught:

  * a COMPRESSION that drops source handles from a surviving fact → FAILS (dropped_source_handle_count > 0);
  * a DEDUPE that erases the losing artifact's lineage (collapses a duplicate without preserving the loser
    as held-out/superseded) → FAILS (orphaned input, silent loss);
  * a SUMMARY that omits held-out warnings (drops items WITHOUT recording them as held_out) → FAILS;
  * an OPTIMIZED pack that preserves facts + handles + held-out warnings → PASSES;
  * duplicate facts MAY collapse ONLY if BOTH lineages survive (the loser kept as superseded/held-out).

The builder is PURE (dict-in → report-out): no store, no clock, no RNG. ``report_id`` is content-addressed,
so the verdict is reproducible (asserted). Imported BY FILE PATH so this lane runs standalone even before
the Lane-B store lands in the same package.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_information_retention_report.py --self-test
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


def _load_isolated(name: str, relpath: str):
    """Import a module BY FILE PATH (registering it in sys.modules so dataclasses resolve) WITHOUT executing
    the package ``__init__`` — keeps this lane independent of sibling lanes in the same package."""
    p = (_resource(relpath)).resolve()
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


RR = _load_isolated("baltor_distillation_retention_report", "_repos/baltor/backend/src/baltor/distillation/retention_report.py")


def _fact(aid: str, handle: str, value: str = "v") -> dict:
    return {"artifact_id": aid, "claim_status": "fact", "artifact_type": "atomic_fact",
            "source_handle": handle, "object": value, "content_hash": "h-" + aid}


def _allegation(aid: str, handle: str) -> dict:
    return {"artifact_id": aid, "claim_status": "unverified_allegation",
            "artifact_type": "narrative_allegation", "source_handle": handle}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    f1 = _fact("f1", "ctx://reg-e#deadline", "10")
    f2 = _fact("f2", "ctx://cfpb/c1#issue", "billing")
    f3 = _fact("f3", "ctx://cfpb/c1#product", "card")
    alleg = _allegation("a1", "ctx://cfpb/c1#narrative.s0")

    # ── A) the reference lossless transform: facts + handles + held-out warnings all preserved → PASS ──
    rpt = RR.build_retention_report(
        transform_type="optimize",
        inputs=[f1, f2, f3, alleg],
        outputs=[f1, f2, f3],          # the served pack
        served=[f1, f2, f3],
        held_out=[alleg],              # the allegation rides along as a separate warning (not deleted)
    )
    check("reference lossless optimize is safe_to_promote", rpt.safe_to_promote)
    check("served source-handle coverage is 100%", rpt.source_handle_coverage == 1.0, str(rpt.source_handle_coverage))
    check("no dropped handles in the reference transform", rpt.dropped_source_handle_count == 0)
    check("no orphaned (silently dropped) inputs", rpt.orphaned_input_ids == [], str(rpt.orphaned_input_ids))
    check("no orphaned (fabricated) outputs", rpt.orphaned_output_ids == [], str(rpt.orphaned_output_ids))
    check("the held-out allegation is counted, not lost", rpt.held_out_count == 1)
    check("input/output counts recorded", rpt.input_count == 4 and rpt.output_count == 3)

    # ── B) compression that DROPS a source handle from a surviving fact → FAIL ──
    f1_no_handle = {k: v for k, v in f1.items() if k != "source_handle"}  # handle stripped by compression
    comp = RR.build_retention_report(
        transform_type="compress_text",
        inputs=[f1, f2],
        outputs=[f1_no_handle, f2],    # same ids survive, but f1 lost its handle
        served=[f1_no_handle, f2],
    )
    check("compression dropping a source handle is NOT safe_to_promote", not comp.safe_to_promote)
    check("dropped_source_handle_count detects the lost handle", comp.dropped_source_handle_count == 1,
          str(comp.dropped_source_handle_count))
    check("served coverage falls below 100% when a served fact loses its handle",
          comp.source_handle_coverage < 1.0, str(comp.source_handle_coverage))

    # ── C) dedupe that ERASES the losing artifact's lineage → FAIL (orphaned input, silent loss) ──
    # f2 and f2dup are duplicates; dedupe keeps f2 but the loser f2dup vanishes WITHOUT being kept as
    # superseded/held-out — a silent loss of its lineage.
    f2dup = _fact("f2dup", "ctx://cfpb/c1b#issue", "billing")
    dedupe_bad = RR.build_retention_report(
        transform_type="dedupe_facts",
        inputs=[f1, f2, f2dup],
        outputs=[f1, f2],              # f2dup silently gone
        served=[f1, f2],
        # NOTE: no held_out / superseded entry for f2dup → its lineage is erased
    )
    check("dedupe erasing the loser's lineage is NOT safe_to_promote", not dedupe_bad.safe_to_promote)
    check("the erased loser shows up as an orphaned input", "f2dup" in dedupe_bad.orphaned_input_ids,
          str(dedupe_bad.orphaned_input_ids))

    # ── C') duplicate facts MAY collapse ONLY if BOTH lineages survive (loser kept as superseded) → PASS ──
    dedupe_ok = RR.build_retention_report(
        transform_type="dedupe_facts",
        inputs=[f1, f2, f2dup],
        outputs=[f1, f2],
        served=[f1, f2],
        superseded=[f2dup],            # the duplicate loser is kept (superseded != deleted)
    )
    check("duplicate facts collapse safely when the loser is kept as superseded", dedupe_ok.safe_to_promote)
    check("the superseded loser is counted, not orphaned",
          dedupe_ok.superseded_count == 1 and dedupe_ok.orphaned_input_ids == [])

    # ── D) a summary that OMITS held-out warnings (drops them without recording them) → FAIL ──
    summary_bad = RR.build_retention_report(
        transform_type="summarize",
        inputs=[f1, f2, alleg],
        outputs=[f1, f2],              # the allegation is dropped
        served=[f1, f2],
        # held_out is EMPTY → the held-out warning was omitted, not recorded → silent loss
    )
    check("a summary omitting held-out warnings is NOT safe_to_promote", not summary_bad.safe_to_promote)
    check("the omitted held-out item shows up as an orphaned input", "a1" in summary_bad.orphaned_input_ids,
          str(summary_bad.orphaned_input_ids))

    # ── E) a fabricated output (no surviving input lineage) → FAIL ──
    ghost = _fact("ghost", "ctx://nowhere#x", "made up")
    fabricate = RR.build_retention_report(
        transform_type="enhance",
        inputs=[f1],
        outputs=[f1, ghost],           # ghost appeared from nowhere
        served=[f1, ghost],
    )
    check("a fabricated output (no input lineage) is NOT safe_to_promote", not fabricate.safe_to_promote)
    check("the fabricated output is flagged as orphaned", "ghost" in fabricate.orphaned_output_ids,
          str(fabricate.orphaned_output_ids))

    # ── F) a declared LOSSY transform on truth is not safe unless explicitly allowed ──
    lossy_truth = RR.build_retention_report(
        transform_type="lossy_compress", inputs=[f1], outputs=[f1], served=[f1],
        lossy_transform_declared=True, lossy_transform_allowed=False)
    check("a lossy transform on truth (declared, not allowed) is NOT safe_to_promote", not lossy_truth.safe_to_promote)
    lossy_ok = RR.build_retention_report(
        transform_type="text_surface_compress", inputs=[f1], outputs=[f1], served=[f1],
        lossy_transform_declared=True, lossy_transform_allowed=True)
    check("a declared+allowed lossy transform (non-truth surface) can be safe_to_promote", lossy_ok.safe_to_promote)

    # ── G) rehydration / lineage flags gate promotion ──
    no_rehydrate = RR.build_retention_report(transform_type="t", inputs=[f1], outputs=[f1], served=[f1],
                                             raw_rehydration_passed=False)
    check("raw rehydration failure blocks promotion", not no_rehydrate.safe_to_promote)
    no_lineage = RR.build_retention_report(transform_type="t", inputs=[f1], outputs=[f1], served=[f1],
                                           lineage_complete=False)
    check("incomplete lineage blocks promotion", not no_lineage.safe_to_promote)

    # ── H) determinism: same inputs → identical report_id ──
    again = RR.build_retention_report(
        transform_type="optimize", inputs=[f1, f2, f3, alleg], outputs=[f1, f2, f3],
        served=[f1, f2, f3], held_out=[alleg])
    check("report is deterministic (content-addressed report_id reproduces)", rpt.report_id == again.report_id,
          f"{rpt.report_id} vs {again.report_id}")
    check("to_dict round-trips the verdict", again.to_dict()["safe_to_promote"] is True)

    ok = not fails
    print(
        f"\n{'PASS — check_information_retention_report: the report enforces the lossless law — compression dropping handles, dedupe erasing the loser lineage, and a summary omitting held-out warnings all FAIL; an optimized pack that keeps facts+handles+warnings PASSES; duplicates collapse only when both lineages survive; fabrications/rehydration/lineage gate promotion; verdict is deterministic.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: InformationRetentionReport enforces lossless distillation.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
