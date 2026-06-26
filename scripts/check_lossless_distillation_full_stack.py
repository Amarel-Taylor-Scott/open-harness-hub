#!/usr/bin/env python3
"""scripts.check_lossless_distillation_full_stack — MASTER PROOF: the lossless law is a checkable subsystem.

This proof ties the whole lossless-distillation subsystem together and shows, per critical-path transform,
that the law holds end to end. For each of the four core transforms — ingest, decompose, reconcile,
optimize — it builds (or, for the apply-proofs, RUNS the existing flow's proof) and checks the five
guarantees the law demands, then prints one matrix row:

    TRANSFORM | RAW_PRESERVED | LINEAGE | REHYDRATION | ROLLBACK | PROOF | STATUS

  * RAW_PRESERVED — the raw layer the transform descends from is still gettable (append-only store).
  * LINEAGE      — ``LineageBundle.build`` for the transform's output is_complete() (reaches raw+source,
                   carries handles, names its transform_run).
  * REHYDRATION  — ``rehydrate`` walks the output back to its raw + source (no distillation without a path).
  * ROLLBACK     — a ``RollbackPlan`` exists for the transform's promotable key (moves the pointer only).
  * PROOF        — the lane's apply/unit proof for that transform exits 0 (run as a subprocess, --self-test).

It also (a) LOADS the six distillation contract schemas and validates one in-store-shaped DistillationRun
example against ``DistillationRun`` via the stdlib validator, and (b) prints each apply-proof's PASS line.
Every critical-path transform row must be green for the proof to pass.

Determinism: ``--self-test``, offline, injected ``now`` (the in-memory store + the sub-proofs all inject
time), hashlib ids, no RNG. PASS/FAIL lines, exit 0/1.

CLI: PYTHONPATH=. python3 scripts/check_lossless_distillation_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402
from src.baltor.distillation.lineage import LineageBundle  # noqa: E402
from src.baltor.distillation.lossless_store import LosslessStore  # noqa: E402
from src.baltor.distillation.rehydration import rehydrate, rehydrate_payload  # noqa: E402
from src.baltor.distillation.rollback import RollbackPlan, execute  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"
_HANDLE = "ctx://cfpb/consumer-complaints/complaint/demo-1001#timely"
_FAQ_HANDLE = "ctx://cfpb/faq/30"
_RAW_BYTES = b'{"native_id":"demo-1001","timely":"Yes","faq30":"FAQ #30 superseded by Reg E 1005.11"}'

_SCHEMA_DIR = _REPO / "schemas" / "distillation"
#: the four critical-path transforms whose losslessness this master proof verifies, in pipeline order.
_TRANSFORMS = ("ingest", "decompose", "reconcile", "optimize")
#: the lane's apply/unit proof backing each transform's losslessness (run as a subprocess, --self-test).
_TRANSFORM_PROOF = {
    "ingest": "scripts/check_ingestion_decomposition_lossless.py",
    "decompose": "scripts/check_ingestion_decomposition_lossless.py",
    "reconcile": "scripts/check_lineage_bundle_complete.py",
    "optimize": "scripts/check_optimization_lossless_distillation.py",
}
#: the six distillation contract schemas the subsystem ships (filename stems under schemas/distillation).
_CONTRACT_STEMS = ["DistillationRun", "LineageBundle", "RehydrationReport", "InformationRetentionReport",
                   "PromotionRecord", "RollbackPlan"]


def _build_graph(store: LosslessStore) -> dict:
    """One lossless graph exercising every critical-path transform: ingest→decompose→reconcile→optimize→promote.

    Returns, per transform, the OUTPUT entry whose losslessness the matrix verifies, plus the promotable
    pack key (whose pointer rollback moves) and the raw layer everything descends from.
    """
    # INGEST: raw bytes preserved out-of-body via a content-addressed payload_ref.
    raw = store.put_raw(_TENANT, key="cfpb/raw/demo-1001", raw_bytes=_RAW_BYTES,
                        mime_type="application/json", now=_NOW)
    src = store.put_source(_TENANT, key="cfpb/source/demo-1001", body={"native_id": "demo-1001"},
                           parent_ids=[raw.entry_id], source_handles=[_HANDLE],
                           transform_run_id="run-normalize-1", now=_NOW)
    # DECOMPOSE: an atomic fact + a held-out FAQ-30 (omitted from the view, kept + rehydratable).
    fact = store.put_derived(_TENANT, key="cfpb/fact/demo-1001/timely",
                             body={"text": "timely response is Yes.", "field": "timely"},
                             parent_ids=[src.entry_id], source_handles=[_HANDLE],
                             transform_type="decompose", transform_run_id="run-decompose-1",
                             role="atomic_fact", now=_NOW)
    faq30 = store.put_derived(_TENANT, key="cfpb/faq/30", body={"text": "FAQ #30: old guidance.", "field": "faq30"},
                              parent_ids=[src.entry_id], source_handles=[_FAQ_HANDLE],
                              transform_type="decompose", transform_run_id="run-decompose-1",
                              role="held_out", receipt_ids=["recon-faq30-receipt"], now=_NOW)
    # RECONCILE: fact (winner) vs FAQ-30 (loser, held out); reaches BOTH; receipt preserved.
    reconciliation = store.put_derived(_TENANT, key="cfpb/reconciliation/demo-1001",
                                       body={"decision": "resolved_by_authority", "winner": "fact", "loser": "faq30"},
                                       parent_ids=[fact.entry_id, faq30.entry_id], source_handles=[_HANDLE],
                                       transform_type="reconcile", transform_run_id="run-reconcile-1",
                                       held_out_ids=[faq30.entry_id], receipt_ids=["recon-faq30-receipt"],
                                       role="winner", now=_NOW)
    # OPTIMIZE: baseline + promoted candidate on the same source snapshot; rejected candidate kept.
    pack_key = "cfpb/pack/regE"
    baseline = store.put_derived(_TENANT, key=pack_key, body={"answer": "10 business days", "v": "baseline"},
                                 parent_ids=[reconciliation.entry_id], source_handles=[_HANDLE],
                                 transform_type="optimize", transform_run_id="run-opt-baseline",
                                 role="baseline", now=_NOW)
    rejected = store.put_derived(_TENANT, key=pack_key, body={"answer": "10 business days", "v": "rejected"},
                                 parent_ids=[baseline.entry_id], source_handles=[_HANDLE],
                                 transform_type="optimize", transform_run_id="run-opt-rejected",
                                 role="rejected", now=_NOW)
    optimized = store.put_derived(_TENANT, key=pack_key, body={"answer": "10 business days", "v": "candidate", "compressed": True},
                                  parent_ids=[baseline.entry_id], source_handles=[_HANDLE],
                                  transform_type="optimize", transform_run_id="run-opt-candidate",
                                  rejected_ids=[rejected.entry_id], rollback_target_ids=[baseline.entry_id],
                                  role="winner", now=_NOW)
    store.set_current(pack_key, optimized.entry_id, tenant=_TENANT)
    return {"raw": raw, "src": src, "pack_key": pack_key, "baseline": baseline,
            # the OUTPUT entry whose losslessness the matrix row checks, per transform:
            "ingest": src, "decompose": fact, "reconcile": reconciliation, "optimize": optimized}


def _run_proof(relpath: str) -> tuple[bool, str]:
    """Run a lane proof as a subprocess with --self-test; return (passed, its final PASS/FAIL line)."""
    proc = subprocess.run([sys.executable, str(_REPO / relpath), "--self-test"],
                          cwd=str(_REPO), capture_output=True, text=True,
                          env={"PYTHONPATH": str(_REPO), "PATH": ""})
    last = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    return proc.returncode == 0, (last[-1] if last else f"(no output; rc={proc.returncode})")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── (a) LOAD the six contract schemas + validate a store-shaped DistillationRun against the contract ──
    print("Contracts:")
    schemas: dict[str, dict] = {}
    for stem in _CONTRACT_STEMS:
        sp = _SCHEMA_DIR / f"{stem}.schema.json"
        present = sp.is_file()
        check(f"contract {stem} schema loads", present, str(sp))
        if present:
            schemas[stem] = json.loads(sp.read_text())

    store = LosslessStore()
    g = _build_graph(store)

    # a DistillationRun describing the OPTIMIZE transform of the in-store graph, validated against the contract.
    opt = g["optimize"]
    bundle = LineageBundle.build(store, opt.entry_id, tenant=_TENANT)
    run_doc = {
        "schema_version": "DistillationRun",
        "run_id": "run-opt-candidate", "tenant_id": _TENANT, "source_scope": "tenant_private",
        "input_artifact_ids": [g["baseline"].entry_id], "output_artifact_ids": [opt.entry_id],
        "input_hashes": [store.get(g["baseline"].entry_id, tenant=_TENANT).content_hash],
        "output_hashes": [opt.content_hash],
        "transform_type": "optimize", "transform_purpose": "compress the served pack losslessly",
        "config_hash": "sha256:" + "0" * 64,
        "created_at": _NOW,
        "lineage": {"raw_artifact_ids": bundle.raw_ids, "source_artifact_ids": bundle.source_ids,
                    "source_handles": bundle.source_handles, "transform_run_ids": bundle.transform_run_ids},
        "receipts": list(bundle.receipt_ids),
        "omitted_artifact_ids": [], "held_out_artifact_ids": list(bundle.held_out_ids),
        "rejected_candidate_ids": list(opt.rejected_ids),
        "rollback_target_id": g["baseline"].entry_id,
    }
    if "DistillationRun" in schemas:
        errs = _validate(run_doc, schemas["DistillationRun"])
        check("a store-shaped DistillationRun validates against DistillationRun", errs == [], str(errs[:4]))

    # ── (b) THE TRANSFORM MATRIX — one row per critical-path transform ──────────────────────────────
    print("\nMatrix:")
    header = f"  {'TRANSFORM':<11} | {'RAW_PRESERVED':<13} | {'LINEAGE':<7} | {'REHYDRATION':<11} | {'ROLLBACK':<8} | {'PROOF':<5} | STATUS"
    print(header)
    print("  " + "-" * (len(header) - 2))

    proof_cache: dict[str, tuple[bool, str]] = {}
    proof_lines: list[tuple[str, str]] = []

    for tname in _TRANSFORMS:
        out = g[tname]

        # RAW_PRESERVED: the raw layer reachable from this output is still gettable + exact bytes rehydrate.
        b = LineageBundle.build(store, out.entry_id, tenant=_TENANT)
        raw_ok = (bool(b.raw_ids) and store.has(g["raw"].entry_id)
                  and rehydrate_payload(store, out.entry_id, _TENANT) == _RAW_BYTES)

        # LINEAGE: the output's bundle is complete (reaches raw+source, has handles, names its run).
        lineage_ok = b.is_complete()

        # REHYDRATION: walking the output back yields its raw + source layers.
        rh = rehydrate(store, out.entry_id, _TENANT)
        rehydr_ok = bool(rh["raw"]) and bool(rh["source"])

        # ROLLBACK: a valid plan exists for the promotable pack key (pointer-only move, candidate kept).
        try:
            plan = RollbackPlan.of(store, key=g["pack_key"], tenant=_TENANT, to_id=g["baseline"].entry_id,
                                   reason=f"verify {tname}")
            rollback_ok = (plan.to_id == g["baseline"].entry_id and plan.deletes_nothing()
                           if hasattr(plan, "deletes_nothing")
                           else plan.to_id == g["baseline"].entry_id)
        except Exception:
            rollback_ok = False

        # PROOF: the lane proof backing this transform exits 0.
        prel = _TRANSFORM_PROOF[tname]
        if prel not in proof_cache:
            proof_cache[prel] = _run_proof(prel)
        proof_ok, proof_line = proof_cache[prel]
        proof_lines.append((prel, proof_line))

        status_ok = raw_ok and lineage_ok and rehydr_ok and rollback_ok and proof_ok

        def yn(x: bool) -> str:
            return "yes" if x else "NO"

        print(f"  {tname:<11} | {yn(raw_ok):<13} | {yn(lineage_ok):<7} | {yn(rehydr_ok):<11} | "
              f"{yn(rollback_ok):<8} | {yn(proof_ok):<5} | {'GREEN' if status_ok else 'RED'}")
        check(f"transform '{tname}' is lossless end to end (raw+lineage+rehydration+rollback+proof)", status_ok,
              f"raw={raw_ok} lineage={lineage_ok} rehydr={rehydr_ok} rollback={rollback_ok} proof={proof_ok}")

    # ── (c) the actual rollback executes and is itself lossless (pointer-only; candidate kept) ────
    versions_before = len(store.versions(g["pack_key"], tenant=_TENANT))
    plan = RollbackPlan.of(store, key=g["pack_key"], tenant=_TENANT, to_id=g["baseline"].entry_id, reason="full-stack")
    receipt = execute(store, plan, now=_NOW)
    check("rollback moves the pack pointer back to the baseline",
          store.current_id(g["pack_key"], tenant=_TENANT) == g["baseline"].entry_id)
    check("rollback kept the promoted candidate (lossless: nothing deleted)",
          store.has(g["optimize"].entry_id) and receipt.candidate_preserved)
    check("rollback removed no version of the pack key",
          len(store.versions(g["pack_key"], tenant=_TENANT)) == versions_before)

    # ── (d) print each apply-proof's PASS line (the human-readable evidence) ──────────────────────
    print("\nApply-proof summaries:")
    seen: set[str] = set()
    extra_proofs = ["scripts/check_cfpb_lossless_distillation.py",
                    "scripts/check_lossless_distillation_redteam.py"]
    for prel, line in proof_lines + [(p, None) for p in extra_proofs]:
        if prel in seen:
            continue
        seen.add(prel)
        if line is None:
            ok, line = _run_proof(prel)
            check(f"apply-proof {Path(prel).name} exits 0", ok, line)
        print(f"  - {Path(prel).name}: {line.split(' — ', 1)[-1][:140]}")

    ok = not fails
    print("\n" + ("PASS — check_lossless_distillation_full_stack: the lossless law is a checkable subsystem — the six "
                  "contract schemas load and a store-shaped DistillationRun validates against DistillationRun; "
                  "every critical-path transform (ingest, decompose, reconcile, optimize) is GREEN across "
                  "RAW_PRESERVED | LINEAGE | REHYDRATION | ROLLBACK | PROOF; the rollback executes pointer-only "
                  "(candidate kept, no version removed); and the CFPB + red-team apply-proofs pass."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Master proof: the lossless distillation law is a checkable subsystem.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
