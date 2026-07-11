#!/usr/bin/env python3
"""scripts.check_open_hubs_bridge_graph — PROOF: the public artifact hubs relate cleanly and none is a truth authority.

Portfolio (owner-directed 2026-06-06): OpenContextHub (context) → OpenSkillsHub (how) → OpenToolsHub (execution)
→ OpenMCPHub (tool connectivity) → OpenCompressionHub (efficiency) → OpenBenchmarkHub (measurement)
→ OpenHubForAI (proof) → Teleon (runs) → Baltor (governs truth). Sources:
_repos/shared-backend-components/architecture/open_hubs_bridge_graph.json + _repos/shared-backend-components/architecture/company_portfolio_map.json.

Asserts:
  A. WELL-FORMED: relationship_chain present; artifact kinds each owned by a DISTINCT modeled open hub; nodes/edges present.
  B. OWNERS REAL: every artifact owner is an open-hub company in the portfolio map (opencontext/skills/tools/harness).
  C. NO TRUTH AUTHORITY: truth_authority == 'baltor'; runtime == 'teleon'; all modeled hubs are listed as
     hubs_are_not_truth_authorities (an open hub never serves truth).
  D. EDGES VALID: every edge's from/to is a known node; the canonical relations exist (Context EVALUATED_BY
     Harness; Skill USES Tool; Tool EVALUATED_BY Harness; Harness TESTS CapabilitySlot).
  E. CONSUMPTION + GOVERNANCE: Teleon CONSUMES the core artifact kinds; Baltor GOVERNS ContextArtifact.
  F. GOVERNANCE RULE stated (discovery is not trust / output is not truth / Baltor governs before serving).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_A = _resource("architecture")
_OPEN_HUBS = {"opencontexthub", "openskillshub", "opentoolshub", "openhubforai",
              "openbenchmarkhub", "openmcphub", "opencompressionhub"}
#: each open hub owns exactly one artifact kind (benchmark/mcp/compression added 2026-06-07)
_ARTIFACT_KINDS = {"ContextArtifact", "SkillArtifact", "ToolArtifact", "HarnessArtifact",
                   "BenchmarkArtifact", "MCPServerArtifact", "CompressionCandidate"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    g = json.loads((_A / "open_hubs_bridge_graph.json").read_text())
    pmap = json.loads((_A / "company_portfolio_map.json").read_text())
    owners = g["artifact_owners"]
    nodes = set(g["nodes"])
    edges = g["edges"]
    rels = {(e["from"], e["rel"], e["to"]) for e in edges}

    # A
    check("A: relationship_chain present", bool(g.get("relationship_chain")))
    check("A: 7 artifact kinds present", set(owners) == _ARTIFACT_KINDS, str(sorted(owners)))
    check("A: each artifact owned by a DISTINCT hub", len(set(owners.values())) == len(_OPEN_HUBS), str(owners))
    check("A: nodes + edges present", bool(nodes) and len(edges) >= 8)

    # B
    check("B: artifact owners are real open-hub companies", set(owners.values()) == _OPEN_HUBS, str(set(owners.values())))
    check("B: owners exist in the portfolio map", all(o in pmap["companies"] for o in owners.values()))

    # C
    check("C: truth authority is Baltor", g.get("truth_authority") == "baltor")
    check("C: runtime is Teleon", g.get("runtime") == "teleon")
    check("C: all open hubs are NOT truth authorities", set(g.get("hubs_are_not_truth_authorities", [])) == _OPEN_HUBS)

    # D
    check("D: every edge references known nodes",
          all(e["from"] in nodes and e["to"] in nodes for e in edges),
          str([(e["from"], e["to"]) for e in edges if e["from"] not in nodes or e["to"] not in nodes]))
    for frm, rel, to in [("ContextArtifact", "EVALUATED_BY", "HarnessArtifact"),
                         ("SkillArtifact", "USES", "ToolArtifact"),
                         ("ToolArtifact", "EVALUATED_BY", "HarnessArtifact"),
                         ("HarnessArtifact", "TESTS", "CapabilitySlot")]:
        check(f"D: edge {frm} {rel} {to}", (frm, rel, to) in rels)

    # D (new hubs): benchmark is RUN_BY a harness (benchmark != harness); mcp provides tools; compression optimizes context
    for frm, rel, to in [("BenchmarkArtifact", "RUN_BY", "HarnessArtifact"),
                         ("MCPServerArtifact", "PROVIDES", "ToolArtifact"),
                         ("CompressionCandidate", "OPTIMIZES", "ContextArtifact")]:
        check(f"D: edge {frm} {rel} {to}", (frm, rel, to) in rels)

    # E
    for kind in ("ContextArtifact", "SkillArtifact", "ToolArtifact", "HarnessArtifact"):
        check(f"E: Teleon CONSUMES {kind}", ("TeleonPurposeTask", "CONSUMES", kind) in rels)
    check("E: Baltor GOVERNS ContextArtifact", ("Baltor", "GOVERNS", "ContextArtifact") in rels)

    # boundary laws (added with the 3 new hubs)
    bl = g.get("boundary_laws", {})
    check("BL: benchmark != harness boundary stated", "harness" in bl.get("benchmark_vs_harness", "").lower())
    check("BL: a benchmark result cannot promote by itself", bl.get("benchmark_result_cannot_promote") is True)
    check("BL: MCP discovery is not trust", bool(bl.get("mcp_discovery_not_trust")))
    check("BL: compression must preserve fidelity/source-handles", "source handle" in bl.get("compression_must_preserve_fidelity", "").lower())

    # F
    gr = g.get("governance_rule", "").lower()
    check("F: governance rule stated (not trust / not truth / Baltor governs)",
          "discovery is not trust" in gr and "not truth" in gr and "baltor governs" in gr)

    print("\n" + ("PASS — check_open_hubs_bridge_graph: the public artifact hubs each own one artifact kind, relate via a "
                  "valid bridge graph, feed Teleon and Baltor (governs context), and NONE is a "
                  "truth authority — Baltor governs, Teleon runs." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_open_hubs_bridge_graph.py --self-test")
    raise SystemExit(0)
