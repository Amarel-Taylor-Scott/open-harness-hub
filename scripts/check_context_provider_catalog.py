#!/usr/bin/env python3
"""scripts.check_context_provider_catalog — proof (C-RESEARCH-1): the context-layer providers from the
research (memory, mcp, temporal-graph, observability, lineage, research-agent) are cataloged as CANDIDATES
behind ports, each with a working stub fallback and the right named candidates (mem0/letta/supermemory,
graphiti, langfuse/phoenix/langsmith, openlineage, OWL/hermes/browser-use). Every such candidate is
candidate-only (never active/primary-wired), so none is the Baltor runtime/authority.

CLI: PYTHONPATH=. python3 scripts/check_context_provider_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_CAT = Path(__file__).resolve().parents[1] / "architecture" / "external_capability_catalog.json"

#: the context-provider slots this pass adds, and a named candidate each must carry.
_REQUIRED = {
    "memory_provider": ["memory.mem0@candidate", "memory.letta@candidate", "memory.supermemory_api@candidate"],
    "mcp_tool_provider": ["mcp.supermemory@candidate"],
    "temporal_graph_provider": ["temporal_graph.graphiti@candidate"],
    "observability_provider": ["observability.langfuse@candidate", "observability.phoenix@candidate", "observability.langsmith@candidate"],
    "lineage_provider": ["lineage.openlineage@candidate"],
    "research_agent": ["research.owl@candidate", "research.hermes@candidate", "research.browser_use@candidate"],
}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cat = json.loads(_CAT.read_text())
    slots = {s["capability_slot"]: s for s in cat["capability_slots"]}

    for slot, cands in _REQUIRED.items():
        s = slots.get(slot)
        chk(f"slot {slot} present", s is not None)
        if not s:
            continue
        ids = {a["adapter_id"] for a in s["adapters"]}
        roles = {a["adapter_id"]: a["role"] for a in s["adapters"]}
        statuses = {a["adapter_id"]: a["status"] for a in s["adapters"]}
        chk(f"{slot} ships a working stub adapter", any(a["role"] == "stub" and a["status"] == "active" for a in s["adapters"]))
        chk(f"{slot} input+output contracts declared", bool(s.get("input_schema")) and bool(s.get("output_schema")))
        for c in cands:
            chk(f"{slot} catalogs candidate {c}", c in ids, str(sorted(ids)))
            if c in ids:
                chk(f"{c} is candidate-only (never active runtime)", statuses[c] == "candidate" and roles[c] in ("primary", "fallback"))

    # the governance invariant: no context provider is wired as the active runtime authority (the stub is)
    for slot in _REQUIRED:
        s = slots[slot]
        wired = s.get("adapter_id")
        wired_role = next((a["role"] for a in s["adapters"] if a["adapter_id"] == wired), None)
        chk(f"{slot} wired adapter is the local stub (not an external candidate)", wired_role == "stub", f"wired={wired} role={wired_role}")

    print(f"\n{'PASS — check_context_provider_catalog: 6 context-provider slots cataloged (memory/mcp/temporal-graph/observability/lineage/research-agent); named candidates (mem0/letta/graphiti/langfuse/phoenix/langsmith/openlineage/OWL/hermes/browser-use) are candidate-only behind ports; each wired to a working local stub — Baltor stays the authority.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: context provider catalog.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
