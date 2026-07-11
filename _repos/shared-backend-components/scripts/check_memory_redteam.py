#!/usr/bin/env python3
"""scripts.check_memory_redteam — proof (C-MEM-2 delta): memory cannot become truth. Attacks fail safely:
builder memory / recall is never a fact; the memory worker emits no CanonicalFact/ContextResponse;
secrets are redacted; tenant + project isolation hold; empty-content writes are rejected; invalid ops
safe-fail; the provider has no truth-serving method.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_memory_redteam.py --self-test
"""
from __future__ import annotations

import argparse

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider
from src.baltor.memory import builder_memory as bm
from src.baltor.memory.memory_worker import process_memory_task


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    p = bm.default_provider()

    # 1 — builder memory is candidate, never a verified fact
    st = bm.capture_builder_state(p, now=1, target="x")
    chk("1 builder memory is candidate (not verified fact)", st["artifact"]["claim_status"] == "candidate")
    rec = bm.recall_builder_context(p, "x", now=2)
    chk("1 recall is_truth=False", rec["is_truth"] is False)

    # 2 — memory worker emits NO CanonicalFact / ContextResponse / served_facts
    pr = BaltorLocalMemoryProvider()
    w = process_memory_task(pr, {"capability_id": "memory.write", "tenant_id": "t",
                                 "payload_json": '{"request":{"content":"c","tenant_id":"t","project":"p","now":1}}'})
    out_keys = set(w.get("result", {}))
    chk("2 memory.write emits no truth keys", not (out_keys & {"canonical_fact", "served_facts", "context_response"}))
    chk("2 memory.write result is_truth=False", w.get("is_truth") is False)

    # 3 — secrets redacted (never stored)
    secret = "s" + "k-" + "LEAK987654321"
    s2 = bm.capture_builder_state(p, now=3, supervisor={"api_key": secret})
    chk("3 secret redacted from builder memory", secret not in s2["artifact"]["content"])
    w2 = process_memory_task(pr, {"capability_id": "memory.write", "tenant_id": "t",
                                  "payload_json": '{"request":{"content":"tok=' + secret + '","tenant_id":"t","project":"p","now":1}}'})
    art = pr.search({"tenant_id": "t", "project": "p", "query": "tok"})
    leaked = any(secret in a.get("content", "") for a in art.get("results", []))
    chk("3 memory.write redacts secrets before storing", not leaked)

    # 4 — tenant isolation: tenant A cannot recall tenant B's memory
    iso = BaltorLocalMemoryProvider()
    iso.write({"tenant_id": "A", "project": "p", "now": 1, "content": "secret-A-only"})
    res_b = iso.search({"tenant_id": "B", "project": "p", "query": "secret"})
    chk("4 tenant B cannot see tenant A memory", len(res_b.get("results", [])) == 0)

    # 5 — project isolation
    iso.write({"tenant_id": "A", "project": "p1", "now": 1, "content": "proj1-only"})
    res_p2 = iso.search({"tenant_id": "A", "project": "p2", "query": "proj1"})
    chk("5 project p2 cannot see project p1 memory", len(res_p2.get("results", [])) == 0)

    # 6 — empty-content write rejected (no empty-memory injection)
    bad = process_memory_task(pr, {"capability_id": "memory.write", "tenant_id": "t",
                                   "payload_json": '{"request":{"content":"  ","tenant_id":"t","project":"p","now":1}}'})
    chk("6 empty-content memory.write rejected", bool(bad.get("error")))

    # 7 — session context advisory, no served facts
    ctx = bm.build_session_context_bundle(p, now=9)
    chk("7 session context advisory + no served facts", ctx["advisory"] and not ctx["contains_served_facts"])

    # 8 — unknown memory op safe-fails (no crash)
    unk = process_memory_task(pr, {"capability_id": "memory.frobnicate", "tenant_id": "t", "payload_json": "{}"})
    chk("8 unknown memory op safe-fails", bool(unk.get("error")))

    # 9 — provider exposes no truth-serving / canonical-write method
    banned = [m for m in ("serve_fact", "write_canonical_fact", "promote_to_fact", "emit_context_response") if hasattr(pr, m)]
    chk("9 provider has no truth-serving method", banned == [], str(banned))

    print(f"\n{'PASS — check_memory_redteam: memory stays candidate (no fact/served-fact/ContextResponse), secrets redacted, tenant+project isolated, empty/unknown ops safe-fail, no truth-serving method.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
