#!/usr/bin/env python3
"""scripts.check_pipeline_api — proof (UI-PIPELINE-1): the Pipeline Journey API is a PURE projection over the
existing runtime that returns each of the 8 contracted stage shapes with the LOSSLESS slices intact.

Tests the pure request handler (no socket) so the contract is deterministic + offline. Asserts the REFERENCE
regulatory result holds end-to-end: reconciliation winner is "10 business days" and the held-out value is the
FAQ "30 days" with the authority rule; consumption.answer contains "10 business days" while "30 days" appears
ONLY in held_out_warnings (never in served_facts); every served fact carries a source_handle; the
verification / optimization / consumption receipt ids are present; and the handler performs NO writes (a
projection mutates no truth and emits no secret).

CLI: python3 _repos/shared-backend-components/scripts/check_pipeline_api.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.api_pipeline_handler import ROUTES, handle, owns

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])

#: the contracted keys each endpoint must return (degrade-gracefully keys are checked separately).
_CONTRACT_KEYS = {
    "/api/pipeline/overview": ("run_id", "stages"),
    "/api/pipeline/upload": ("sources", "lineage"),
    "/api/pipeline/decomposition": ("atomic_facts", "held_out", "lineage"),
    "/api/pipeline/reconciliation": ("conflicts",),
    "/api/pipeline/enhancement": ("entities", "fragility", "graph_edges"),
    "/api/pipeline/optimization": ("baseline", "candidates", "promoted_id", "receipt_id"),
    "/api/pipeline/verification": ("checks", "receipt_id"),
    "/api/pipeline/consumption": ("answer", "served_facts", "held_out_warnings", "receipts"),
}


def _no_writes_handle(path: str, query: dict) -> tuple:
    """Call the handler with the real filesystem write surfaces blocked — a projection must never write."""
    import builtins

    real_open = builtins.open
    writes: list = []

    def guard_open(file, mode="r", *a, **k):
        if any(flag in str(mode) for flag in ("w", "a", "x", "+")):
            writes.append((str(file), mode))
        return real_open(file, mode, *a, **k)

    builtins.open = guard_open
    try:
        out = handle("GET", path, query)
    finally:
        builtins.open = real_open
    return out, writes


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    q = {"tenant": "demo", "corpus": "cfpb"}

    # 1) every endpoint returns 200 + a dict with the contracted keys + available=true
    payloads: dict = {}
    for route, keys in _CONTRACT_KEYS.items():
        code, p = handle("GET", route, q)
        payloads[route] = p
        check(f"{route} -> 200", code == 200, str(code))
        check(f"{route} returns a dict", isinstance(p, dict))
        check(f"{route} available", p.get("available") is True, p.get("reason", ""))
        check(f"{route} has contracted keys {keys}", all(k in p for k in keys),
              str([k for k in keys if k not in p]))

    # 2) overview: 7 stages, in order, each with the lossless counts
    ov = payloads["/api/pipeline/overview"]
    stage_ids = [s["id"] for s in ov.get("stages", [])]
    check("overview has 7 stages in journey order",
          stage_ids == ["upload", "decomposition", "reconciliation", "enhancement",
                        "optimization", "verification", "consumption"], str(stage_ids))
    check("every overview stage carries in/out/held_out/rejected counts",
          all(all(k in s for k in ("in_count", "out_count", "held_out_count", "rejected_count"))
              for s in ov.get("stages", [])))
    check("overview run_id present", bool(ov.get("run_id")))

    # 3) decomposition is lossless: atomic facts AND held-out narrative allegations, each with a handle
    dec = payloads["/api/pipeline/decomposition"]
    check("decomposition has atomic facts", len(dec.get("atomic_facts", [])) > 0)
    check("decomposition surfaces held-out narrative (lossless)", len(dec.get("held_out", [])) > 0)
    check("every decomposed fact has a source handle", all(f.get("source_handle") for f in dec["atomic_facts"]))
    check("every held-out item has a source handle + reason",
          all(h.get("source_handle") and h.get("reason") for h in dec["held_out"]))

    # 4) REFERENCE reconciliation: winner 10 business days; held-out loser 30 days; authority rule + receipt
    rec = payloads["/api/pipeline/reconciliation"]
    conf = rec["conflicts"][0]
    dcn = conf["decision"]
    check("reconciliation winner is '10 business days'", dcn.get("winner") == "10 business days", dcn.get("winner"))
    check("reconciliation held_out_value is the FAQ '30 days'", dcn.get("held_out_value") == "30 days", dcn.get("held_out_value"))
    check("reconciliation shows BOTH candidates", len(conf.get("candidates", [])) == 2, str(len(conf.get("candidates", []))))
    check("reconciliation cites the authority rule", bool(dcn.get("rule")))
    check("reconciliation has a receipt_id", bool(dcn.get("receipt_id")), dcn.get("receipt_id", ""))
    cand_vals = {c["value"] for c in conf["candidates"]}
    check("both '10 business days' and '30 days' appear as candidates", {"10 business days", "30 days"} <= cand_vals, str(cand_vals))

    # 5) optimization is lossless: baseline + candidates with promoted vs REJECTED + reasons; a promoted id
    opt = payloads["/api/pipeline/optimization"]
    check("optimization shows a baseline", bool(opt.get("baseline", {}).get("metrics")))
    check("optimization shows multiple candidates", len(opt.get("candidates", [])) > 1, str(len(opt.get("candidates", []))))
    check("optimization surfaces at least one REJECTED candidate (lossless)",
          any(c.get("status") == "rejected" for c in opt["candidates"]))
    check("every rejected candidate carries a reason",
          all(c.get("reason") for c in opt["candidates"] if c.get("status") == "rejected"))
    check("optimization has a promoted_id + receipt_id", bool(opt.get("promoted_id")) and bool(opt.get("receipt_id")))
    check("promoted_id is one of the candidates", opt["promoted_id"] in {c["id"] for c in opt["candidates"]})

    # 6) verification is lossless: per-artifact allow/hold_out decisions + a receipt id
    ver = payloads["/api/pipeline/verification"]
    decisions = {c["decision"] for c in ver.get("checks", [])}
    check("verification returns per-artifact decisions", len(ver.get("checks", [])) > 0)
    check("verification decisions are only allow/hold_out", decisions <= {"allow", "hold_out"}, str(decisions))
    check("verification surfaces both allow AND hold_out (lossless)", {"allow", "hold_out"} <= decisions, str(decisions))
    check("verification has a receipt_id", bool(ver.get("receipt_id")))

    # 7) REFERENCE consumption: answer has '10 business days'; '30 days' ONLY in held_out_warnings; handles; receipts
    con = payloads["/api/pipeline/consumption"]
    check("consumption.answer contains '10 business days'", "10 business days" in con.get("answer", ""), con.get("answer"))
    served_blob = json.dumps(con.get("served_facts", []))
    held_blob = json.dumps(con.get("held_out_warnings", []))
    check("'30 days' / '30' never served as fact", "30 days" not in served_blob and "fact-faq-30" not in served_blob)
    check("the held-out '30' FAQ is surfaced as a warning (lossless)", "fact-faq-30" in held_blob)
    check("consumption surfaces held_out_warnings", len(con.get("held_out_warnings", [])) > 0)
    check("every served fact has a source_handle", all(f.get("source_handle") for f in con.get("served_facts", [])))
    rcp = con.get("receipts", {})
    check("verification + optimization + consumption receipt ids present",
          all(rcp.get(k) for k in ("verification", "optimization", "consumption")), str(rcp))

    # 8) projection-only: GET-only, no truth mutation (no file writes), no secret markers, deterministic
    code405, _ = handle("POST", "/api/pipeline/consumption", q)
    check("non-GET is rejected 405 (projection is read-only)", code405 == 405, str(code405))
    code404, _ = handle("GET", "/api/pipeline/not-a-route", q)
    check("unknown route returns 404 (no crash)", code404 == 404, str(code404))
    code400, _ = handle("GET", "/api/pipeline/overview", {"corpus": "unknown"})
    check("unknown corpus returns 400 (no crash)", code400 == 400, str(code400))
    for route in _CONTRACT_KEYS:
        (wcode, _wp), writes = _no_writes_handle(route, q)
        check(f"{route} performs NO file writes (projection-only)", writes == [], str(writes[:2]))
    # no secret marker anywhere in any projection
    all_blob = json.dumps(payloads, default=str)
    check("no secret/private marker in any projection",
          not any(m in all_blob for m in ("OH_SHOWCASE_TOKEN", "sk-", "MEMORY.md", ".agent/", ".claude/")))
    # deterministic: identical re-run
    c2, p2 = handle("GET", "/api/pipeline/consumption", q)
    check("consumption projection is deterministic (identical re-run)", (c2, p2) == (200, con))

    # 9) owns() covers every owned route + the route set is complete (8 endpoints)
    check("handler owns all 8 contracted routes", all(owns(r) for r in _CONTRACT_KEYS))
    check("ROUTES advertises exactly the 8 journey endpoints", set(ROUTES) == set(_CONTRACT_KEYS), str(set(ROUTES) ^ set(_CONTRACT_KEYS)))

    msg = ("PASS — check_pipeline_api: the Pipeline Journey API projects all 8 stages from the existing runtime "
           "(reconciliation winner '10 business days' beside held-out FAQ '30 days' + rule; consumption answer "
           "'10 business days' with '30' only in held_out_warnings; per-artifact verify allow/hold_out; baseline + "
           "rejected optimization candidates; receipt lineage); GET-only, no writes, no secrets, deterministic.")
    print(f"\n{msg if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline journey projection API.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
