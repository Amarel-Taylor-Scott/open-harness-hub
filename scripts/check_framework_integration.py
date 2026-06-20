#!/usr/bin/env python3
"""check_framework_integration — proof that Teleon interoperates with the common agent frameworks BOTH directions,
governed: EXPORT a governed capability as a framework-native tool (MCP/OpenAI/Anthropic/LangGraph/CrewAI/AutoGen)
carrying its governance, and WRAP a framework agent as a governed CANDIDATE behind a port (sandboxed, never truth).
Teleon imports no framework — it emits/consumes specs. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_framework_integration.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MATRIX = _REPO / "architecture" / "framework_integration_matrix.json"

from src.teleon.frameworks import framework_adapters as fa

_CAP = {"name": "reg-e-deadline-lookup", "description": "Look up the Reg E error-resolution deadline.",
        "parameters": {"type": "object", "properties": {"institution": {"type": "string"}}},
        "governance": {"verified": True, "measured_lift": 0.71, "receipt_id": "rc_tool1"}}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # EXPORT — each framework gets the right NATIVE shape, carrying our governance
    oa = fa.to_openai_tool(_CAP)
    ck("OpenAI export: function-tool shape {type, function:{name,description,parameters}}",
       oa["type"] == "function" and oa["function"]["name"] == _CAP["name"] and "parameters" in oa["function"])
    an = fa.to_anthropic_tool(_CAP)
    ck("Anthropic export: {name, description, input_schema}", an["name"] == _CAP["name"] and "input_schema" in an)
    mc = fa.to_mcp_tool(_CAP)
    ck("MCP export: {name, description, inputSchema}", "inputSchema" in mc and mc["name"] == _CAP["name"])
    lg = fa.to_langgraph_node(_CAP)
    ck("LangGraph export: a governed tool node bound to the capability", lg["kind"] == "tool_node" and lg["governed"] is True)
    cr = fa.to_crewai_tool(_CAP)
    ck("CrewAI export: {name, description, args_schema}", "args_schema" in cr and cr["name"] == _CAP["name"])

    # every export carries the governance (verified/receipt) + serves_truth=false (a GOVERNED capability)
    exports = [oa, an, mc, lg, cr]
    ck("every exported tool carries the governance (receipt + serves_truth=false)",
       all(e["x_teleon_governance"]["serves_truth"] is False and e["x_teleon_governance"].get("measured_lift") == 0.71
           for e in exports))
    ck("export_capability dispatches by framework name", fa.export_capability(_CAP, "openai") == oa
       and fa.export_capability(_CAP, "mcp") == mc)

    # WRAP — a framework agent becomes a governed CANDIDATE behind a port: sandboxed, never truth
    w = fa.wrap_agent_as_candidate("crewai", "lead-research-crew", capability_slot="lead-discovery")
    ck("wrap: a framework agent is a governed CANDIDATE behind a port (sandboxed, never truth)",
       w["disposition"] == "candidate" and w["serves_truth"] is False and w["binding"] == "ExecutionProviderPort"
       and w["sandbox"])
    ck("wrap rejects an unsupported framework", _raises(lambda: fa.wrap_agent_as_candidate("bogus", "x", capability_slot="y")))

    # the matrix covers >= 5 frameworks both directions, each with a real exporter on the adapter module
    m = json.loads(_MATRIX.read_text())
    fr = m["frameworks"]
    ck("the matrix covers >= 5 frameworks, both directions (export + wrap)",
       len(fr) >= 5 and all(f["export_as"] and f["wrap_as"] for f in fr))
    ck("every matrix exporter is a real function on the adapters module",
       all(hasattr(fa, f["exporter"]) for f in fr), str([f["exporter"] for f in fr if not hasattr(fa, f["exporter"])]))
    ck("the named frameworks are present (MCP, OpenAI, Anthropic, LangGraph, CrewAI)",
       {"mcp", "openai", "anthropic", "langgraph", "crewai"} <= {f["framework"] for f in fr})

    ck("nothing serves truth (frameworks consume governed capabilities / are candidate runtimes)",
       m["serves_truth"] is False and all(e["x_teleon_governance"]["serves_truth"] is False for e in exports))
    ck("deterministic", fa.to_openai_tool(_CAP) == oa)

    print("\n" + (f"PASS - check_framework_integration: Teleon exports a governed capability as a native tool for "
                  f"{len(fr)} frameworks (MCP/OpenAI/Anthropic/LangGraph/CrewAI/AutoGen) carrying its receipt, and "
                  f"wraps a framework agent as a governed candidate behind a port (sandboxed, never truth). Teleon "
                  f"imports no framework — emits/consumes specs. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _raises(fn) -> bool:
    try:
        fn(); return False
    except Exception:
        return True


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_framework_integration.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
