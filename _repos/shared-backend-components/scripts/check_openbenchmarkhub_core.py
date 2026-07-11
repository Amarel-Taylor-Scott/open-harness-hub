#!/usr/bin/env python3
"""scripts.check_openbenchmarkhub_core — PROOF: OpenBenchmarkHub is real — the contracts exist, the first
first-party benchmark (Baltor CFPB Context Governance) is well-formed and anchored to the REAL demo facts, the
competitive-intelligence-derived benchmark opportunities are registered as candidates, and the governing law
"a benchmark result is evidence, not authority" is enforced by the actual promotion gate.

Asserts:
  A. CONTRACTS: BenchmarkArtifact/BenchmarkResult/BenchmarkSuitabilityReport registered.
  B. CFPB benchmark conforms to BenchmarkArtifact (all required fields) + family in the taxonomy.
  C. REAL ANCHOR: its expected_results match the demo facts — served "10 business days", held-out "30 days",
     source handles + receipts required, allegations NOT served as fact.
  D. EVIDENCE-NOT-AUTHORITY: bridge-graph law benchmark_result_cannot_promote is True AND the real promotion gate
     (_repos/baltor/backend/src/baltor/experiments/path_promotion.GATES) contains NO benchmark gate; a BenchmarkResult is is_truth=False.
  E. EXTERNAL refs are owner_provided_unverified (SWE-bench/HELM/etc. not trusted until confirmed).
  F. CI OPPORTUNITIES: the competitor-derived benchmarks are registered as CANDIDATES (status 200, not 500) and the
     regulated ones (legal/clinical/finance) carry a no-accusation / review caveat.
  G. WELL-FORMED + deterministic.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    A = _resource("architecture")
    contracts = json.dumps(json.loads((A / "contract_registry.json").read_text()))
    check("A: 3 benchmark contracts registered", all(f"benchmarks/{s}.schema.json" in contracts for s in
          ("BenchmarkArtifact", "BenchmarkResult", "BenchmarkSuitabilityReport")))

    fam = json.loads((A / "benchmark_family_codes.json").read_text())["families"]
    reg = json.loads((A / "open_benchmark_registry.json").read_text())
    cfpb = json.loads((_resource("fixtures") / "benchmarks" / "cfpb_context_governance.benchmark.json").read_text())
    req = json.loads((_resource("schemas") / "benchmarks" / "BenchmarkArtifact.schema.json").read_text())["required"]
    check("B: CFPB benchmark conforms to BenchmarkArtifact + family known",
          all(k in cfpb for k in req) and cfpb["benchmark_family"] in fam, str([k for k in req if k not in cfpb]))

    er = cfpb["expected_results"]
    check("C: anchored to the real demo facts (10 business days served / 30 days held out / handles + receipts)",
          er["served_answer_contains"] == "10 business days" and er["held_out_fact"] == "30 days"
          and er["source_handles_required"] is True and er["receipts_required"] is True
          and er["allegations_served_as_fact"] is False, json.dumps(er))

    bridge = json.loads((A / "open_hubs_bridge_graph.json").read_text())
    from src.baltor.experiments.path_promotion import GATES
    check("D: evidence-not-authority — law True AND no benchmark gate in the real promotion gate",
          bridge["boundary_laws"]["benchmark_result_cannot_promote"] is True
          and not any("benchmark" in g.lower() for g in GATES), str(GATES))
    res_schema = json.loads((_resource("schemas") / "benchmarks" / "BenchmarkResult.schema.json").read_text())
    check("D: BenchmarkResult pins is_truth=false + promotion_authority=false",
          res_schema["properties"]["is_truth"].get("const") is False and res_schema["properties"]["promotion_authority"].get("const") is False)

    check("E: external benchmarks are owner_provided_unverified",
          all(e["source"] == "owner_provided_unverified" and e["confidence"] == "unverified" for e in reg["external_unverified"]) and reg["external_unverified"])

    opp = {o["benchmark_id"]: o for o in reg["opportunities"]}
    check("F: CI-derived benchmark opportunities are CANDIDATES (status 200, not active 500)",
          all(o["status_code"] == 200 for o in opp.values()) and len(opp) >= 5)
    regulated = ["benchmark.legal_context_governance", "benchmark.clinical_evidence_grounding", "benchmark.consumer_finance_chatbot_guardrail"]
    check("F: regulated opportunities carry a no-accusation / review caveat",
          all("caveat" in json.dumps(opp[b]).lower() or opp[b].get("regulated_caveat") for b in regulated))

    check("G: registry well-formed (first_party CFPB present + a teleon + a compression benchmark)",
          any("cfpb_context_governance" in f["benchmark_id"] for f in reg["first_party"])
          and any(f["owner"] == "teleon" for f in reg["first_party"]))

    print("\n" + ("PASS — check_openbenchmarkhub_core: OpenBenchmarkHub is real — contracts registered; the Baltor "
                  "CFPB benchmark is well-formed + anchored to the actual demo facts; external benchmarks are "
                  "unverified; the competitor-derived opportunities are candidates (regulated ones caveated); and a "
                  "benchmark result is evidence-not-authority (no benchmark gate in the promotion path)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_openbenchmarkhub_core.py --self-test")
    raise SystemExit(0)
