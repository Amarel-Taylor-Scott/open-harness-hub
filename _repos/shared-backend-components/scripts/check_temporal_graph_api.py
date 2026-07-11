#!/usr/bin/env python3
"""scripts.check_temporal_graph_api — proof: the temporal-graph API is projection-only, never serves a
held-out/stale fact as current, and answers every route. Deterministic + offline.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_temporal_graph_api.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.api_temporal_graph_handler import handle, owns


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    q = {"tenant": "global"}
    code, facts = handle("GET", "/api/graph/temporal/facts", q)
    chk("GET facts -> 200 with facts", code == 200 and facts["facts"])
    code, cur = handle("GET", "/api/graph/temporal/current/reg_e.error_resolution.deadline", q)
    chk("GET current -> 10 business days served", code == 200 and any(f["value"] == "10 business days" for f in cur["served_facts"]))
    chk("GET current -> 30 days NOT served (held-out warning only)",
        all(f["value"] != "30 days" for f in cur["served_facts"]) and any(h["value"] == "30 days" for h in cur["held_out_warnings"]))
    code, conf = handle("GET", "/api/graph/temporal/conflicts", q)
    chk("GET conflicts -> CONTRADICTS edge", code == 200 and any(e["edge_type"] == "CONTRADICTS" for e in conf["conflicts"]))
    code, ho = handle("GET", "/api/graph/temporal/held-out", q)
    chk("GET held-out -> FAQ 30 preserved", code == 200 and any(n["value_normalized"] == "30 days" for n in ho["held_out"]))
    code, tl = handle("GET", "/api/graph/temporal/timeline/reg_e.error_resolution.deadline", q)
    chk("GET timeline -> observations", code == 200 and tl["observations"])
    code, ps = handle("GET", "/api/graph/temporal/provider-status", q)
    chk("GET provider-status -> local active + graphiti candidate + emulator", code == 200 and len(ps["providers"]) == 3)
    code, rb = handle("POST", "/api/graph/temporal/rebuild", q)
    chk("POST rebuild -> receipt, projection_only", code == 200 and rb["projection_only"] and rb["current"] == "10 business days")
    chk("every GET route is projection_only", all(handle("GET", r, q)[1].get("projection_only") for r in (
        "/api/graph/temporal/facts", "/api/graph/temporal/edges", "/api/graph/temporal/conflicts", "/api/graph/temporal/held-out")))
    code, _ = handle("GET", "/api/graph/temporal/bogus", q)
    chk("unknown route -> 404", code == 404)
    code, _ = handle("PUT", "/api/graph/temporal/facts", q)
    chk("non-GET/POST -> 405", code == 405)
    chk("owns() recognizes the routes", owns("/api/graph/temporal/facts") and not owns("/api/other"))

    print(f"\n{'PASS — check_temporal_graph_api: projection-only routes answer; current serves 10 business days, FAQ-30 only as held-out warning; conflicts/held-out/timeline/provider-status/rebuild all work; unknown 404, non-GET/POST 405.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: temporal graph API.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
