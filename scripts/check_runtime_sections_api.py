#!/usr/bin/env python3
"""scripts.check_runtime_sections_api — proof (C-CONSUME-1): GET /api/runtime/sections projects the section
maturity matrix (the honest scoreboard) and GET /api/runtime/consumption summarizes the latest served response.
api_runtime is M10 only because its API proofs pass; non-M10 sections stay honestly candidate/pending.

CLI: python3 scripts/check_runtime_sections_api.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.api_context_handler import handle

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    code, payload = handle("GET", "/api/runtime/sections", None)
    check("GET /api/runtime/sections returns 200", code == 200)
    secs = {s["section_id"]: s for s in payload.get("sections", [])}
    check("the matrix summary is projected (all sections)", len(secs) >= 34, str(len(secs)))
    check("summary reports each section's status + owner + proofs + reference flag",
          all({"section_id", "status", "owner", "proof_scripts", "critical_path_required"} <= set(s) for s in secs.values()))

    matrix = json.loads((_REPO / "architecture" / "section_maturity_matrix.json").read_text())["sections"]
    check("api_runtime is M10 (because its API proofs pass)", secs.get("api_runtime", {}).get("status") == "m10_complete")
    reference_not_m10 = [s["section_id"] for s in matrix if s.get("critical_path_required") and s.get("status") != "m10_complete"]
    check("every critical-path section remains M10", reference_not_m10 == [], str(reference_not_m10))
    candidates = sorted(s["section_id"] for s in matrix if s.get("status") in ("candidate", "experimental"))
    check("non-M10 sections remain honestly candidate/pending", candidates and "unstructured_document_decomposition" in candidates, str(candidates))
    check("summary reports reference m10 count", payload.get("reference_m10", 0) == payload.get("reference_total", -1))

    # latest-consumption summary works after a serve
    handle("POST", "/api/context/serve", {"tenant_id": "demo", "corpus": "cfpb"})
    c2, cons = handle("GET", "/api/runtime/consumption", None)
    check("GET /api/runtime/consumption summarizes the latest response", c2 == 200
          and "10 business days" in (cons.get("answer") or "") and cons.get("served_fact_count", 0) > 0)

    print(f"\n{'PASS — check_runtime_sections_api: /api/runtime/sections projects the honest maturity scoreboard (api_runtime M10, reference sections M10, candidates flagged); /api/runtime/consumption summarizes the latest served response.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: runtime sections API.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
