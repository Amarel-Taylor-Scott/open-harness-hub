#!/usr/bin/env python3
"""scripts.check_builder_memory_capture — proof (C-MEM-2 delta): builder-memory captures loop state/proofs/
failures/decisions/next-target as project-scoped MemoryArtifacts (candidate workflow_trace, NOT facts),
REDACTS secrets, writes a MemoryTrace per op, and recall/session-context return project-scoped candidate
context (never served facts).

CLI: PYTHONPATH=. python3 scripts/check_builder_memory_capture.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.memory import builder_memory as bm


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    p = bm.default_provider()
    secret = "s" + "k-" + "LEAK" + "0123456789"   # built at runtime; never a secret-shaped literal in the file

    st = bm.capture_builder_state(p, now=1000, target="C-MEM-2 delta", flywheel={"green": 290, "total": 290},
                                  risks=["data-gravity"], next_target="parallel",
                                  supervisor={"leader": "sup-1", "api_key": secret})
    chk("captures builder state → MemoryArtifact", st["artifact"].get("artifact_id", "").startswith("memart-"))
    chk("secret REDACTED (not stored in memory)", secret not in st["artifact"]["content"] and st["redactions"] >= 1)
    chk("captured memory is candidate, not a verified fact", st["artifact"].get("claim_status") == "candidate")
    chk("MemoryTrace written for the capture", st["trace"]["operation"] == "write" and st["trace"]["produced_artifact_ids"])

    pr = bm.capture_proof_result(p, now=1001, proof="check_x", ok=False, detail="boom")
    chk("captures proof result", pr["artifact"]["artifact_id"].startswith("memart-"))
    fw = bm.capture_flywheel_tick(p, now=1002, green=289, total=290, red=["check_x"])
    chk("captures flywheel tick", "flywheel_tick" in fw["artifact"]["content"])
    sd = bm.capture_supervisor_decision(p, now=1003, decision_type="spawn_worker", capability="memory.write")
    chk("captures supervisor decision", "supervisor_decision" in sd["artifact"]["content"])
    ft = bm.capture_failure_trace(p, now=1004, where="memory_worker", error="bad payload")
    chk("captures failure trace", "failure_trace" in ft["artifact"]["content"])
    nt = bm.capture_next_target(p, now=1005, target="parallel multi-worker")
    chk("captures next target", "next_target" in nt["artifact"]["content"])

    rec = bm.recall_builder_context(p, "builder_state", now=1006)
    chk("recall returns project-scoped candidate context", rec["is_truth"] is False and len(rec["artifacts"]) >= 1)
    chk("recall is candidate_context (not served facts)", rec["claim_status"] == "candidate_context")

    ctx = bm.build_session_context_bundle(p, now=1007)
    chk("session context bundle is advisory + not truth", ctx["advisory"] is True and ctx["is_truth"] is False)
    chk("session context contains no served facts", ctx["contains_served_facts"] is False)
    chk("session context points to memory artifacts", len(ctx["memory_artifact_ids"]) >= 1)

    # determinism: same capture content → same content-addressed artifact id (idempotent, lossless)
    a = bm.capture_next_target(bm.default_provider(), now=1005, target="dup")["artifact"]["artifact_id"]
    b = bm.capture_next_target(bm.default_provider(), now=1005, target="dup")["artifact"]["artifact_id"]
    chk("deterministic content-addressed capture", a == b)

    print(f"\n{'PASS — check_builder_memory_capture: builder state/proof/flywheel/decision/failure/target captured as candidate MemoryArtifacts + traces; secrets redacted; recall/session-context are project-scoped candidate context, never facts.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
