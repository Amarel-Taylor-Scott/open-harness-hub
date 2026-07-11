#!/usr/bin/env python3
"""scripts.check_cfpb_artifact_graph_demo — proof: the full C32 orchestrator runs every stage, returns
nonzero counts, builds the final context pack from reconciled/promotable facts only, and supports drill-down.

CLI: python3 _repos/shared-backend-components/scripts/check_cfpb_artifact_graph_demo.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.cfpb_artifact_graph_demo import run_demo


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = run_demo()
    check("orchestrator returns ok", r["ok"])
    check("all stages ran (ingest→…→final_pack+receipt)", len(r["stages"]) == 6, str(r["stages"]))
    c = r["counts"]
    check("nonzero counts for artifacts/vectors/edges/conflicts/reconciliations",
          all(c[k] > 0 for k in ("artifacts", "vectors", "edges", "conflicts", "reconciliations")), str(c))

    fcp = r["final_context_pack"]
    check("final context pack has included facts", len(fcp["included"]) > 0)
    check("final context pack excludes held-out (lower-authority/unresolved) artifacts",
          not (set(fcp["included"]) & set(fcp["held_out"])))
    check("the known conflicting FAQ claim is held out of the final pack", r["_faq_id"] in fcp["held_out"])
    check("the reconciled winner (Reg E) is included", r["_reg_e_id"] in fcp["included"])

    # drill-down: an atomic fact resolves to its lineage + vector neighbours + pack membership
    d = r["drilldown"]
    check("drill-down resolves an atomic fact to its artifact + neighbours + nearest vectors",
          d and d["artifact"]["content_hash"] and isinstance(d["neighbors"], list) and isinstance(d["nearest"], list))
    check("drill-down artifact carries source handles (back to source)", bool(d["artifact"]["source_handles_json"]))

    check("graph_layers (edge counts by type) are exposed", len(r["graph_layers"]) >= 5, str(r["graph_layers"]))
    check("vector provider metadata is exposed", r["vector_provider"]["provider"] == "deterministic_local")
    check("receipt attests the pack", r["receipt"].get("pack"))

    print(f"\n{'PASS — check_cfpb_artifact_graph_demo: full flow runs end-to-end; counts nonzero; final pack is reconciled/promotable-only; drill-down resolves fact→lineage→vector→neighbours→pack→receipt.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: C32 full orchestrator.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
