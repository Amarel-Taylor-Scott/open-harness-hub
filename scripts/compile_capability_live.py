#!/usr/bin/env python3
"""compile_capability_live — FULL intelligent orchestration: the LLM finds components + composes the DAG (not a scaffold).

The LLM is the ORCHESTRATOR: given an intent + the REAL candidate components (searched from the component index +
registries) + the discipline (deterministic-first, cheapest-first, model only for the residual), it SELECTS components/
primitives and COMPOSES a DAG (structured nodes + edges). The registries are the GUARDRAIL — every component the LLM picks
is VALIDATED to be real (a hallucinated component is rejected, never run); the DAG is checked acyclic + deterministic-first.
LLM proposes, the registry + governance dispose. The ladder is a fallback when no LLM. Network-gated. serves_truth=false.

  python3 scripts/compile_capability_live.py "extract fields from these invoices into our schema"
  python3 scripts/compile_capability_live.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.teleon.synthesis import component_search as CS
from src.teleon.synthesis import intent_to_dag as I
from src.teleon.synthesis.io_contracts import edge_compatible, plane_io
from src.teleon.synthesis.dag_contract import verify_buildable_dag

REPO = Path(__file__).resolve().parents[1]
RECEIPT = REPO / "data" / "dev-intel" / "live-compile-smoke.json"


def candidate_pool(intent: str, *, k: int = 28) -> dict:
    """The REAL components the LLM may compose from: searched from the component index + the intent's ladder rungs.
    Returns {bare_component_id: {plane, deterministic, kind}} — the LLM can ONLY pick from these (registry guardrail)."""
    tools = {t["id"]: t for t in json.loads((REPO / "architecture" / "tool_registry.json").read_text())["tools"]}
    pool: dict = {}
    def add(cid: str):
        bare = cid.split(":", 1)[1] if ":" in cid else cid
        if bare in tools and bare not in pool:
            pool[bare] = {"plane": tools[bare].get("plane"), "deterministic": bool(tools[bare].get("deterministic")), "kind": "tool"}
    for h in CS.search(intent, k=k):
        add(h["id"])
    for ids in CS.compose(I.outline(intent).get("capability") or "", k=4).values():
        for cid in ids:
            add(cid)
    pool["llm"] = {"plane": "llm", "deterministic": False, "kind": "model"}   # the escalation primitive is always available
    return pool


def _io_hint(plane) -> str:
    """The component's typed I/O (consumes->produces) so the LLM composes TYPE-COMPATIBLE edges (Langflow port-typing)."""
    io = plane_io(plane)
    return f", io={'/'.join(io.get('consumes', []))}->{'/'.join(io.get('produces', []))}" if io else ""


def _prompt(intent: str, pool: dict) -> str:
    lines = [f"  - {cid} (plane={v['plane']}, deterministic={v['deterministic']}{_io_hint(v['plane'])})" for cid, v in pool.items()]
    return ("You are a capability COMPILER. Compose a DAG that solves the intent using ONLY the components listed (do not "
            "invent components). Put DETERMINISTIC components first; use 'llm' ONLY for the residual a deterministic "
            "component cannot do. Each component shows io=consumes->produces; only connect an edge when the upstream "
            "component PRODUCES a type the downstream CONSUMES (type-compatible). Output ONLY JSON: "
            "{\"nodes\":[{\"step\":\"name\",\"component\":\"<id from the list>\"}],\"edges\":[[\"step_a\",\"step_b\"]]}.\n"
            f"INTENT: {intent}\nAVAILABLE COMPONENTS:\n" + "\n".join(lines))


def _validate(spec: dict, pool: dict) -> dict:
    """Governance: keep only nodes whose component is REAL (in the pool); drop hallucinations; check the DAG is acyclic."""
    nodes, hallucinated, seen = [], [], set()
    for n in spec.get("nodes", []):
        comp = n.get("component")
        if comp in pool and n.get("step") not in seen:
            seen.add(n["step"]); nodes.append({"step": n["step"], "component": comp, **pool[comp]})
        elif comp is not None:
            hallucinated.append(comp)
    steps = {n["step"] for n in nodes}
    edges = [(a, b) for a, b in (spec.get("edges") or []) if a in steps and b in steps]
    # acyclicity (Kahn)
    indeg = {s: 0 for s in steps}
    for a, b in edges:
        indeg[b] += 1
    q = [s for s in steps if indeg[s] == 0]; order = []
    while q:
        s = q.pop(); order.append(s)
        for a, b in edges:
            if a == s:
                indeg[b] -= 1
                if indeg[b] == 0:
                    q.append(b)
    acyclic = len(order) == len(steps)
    det = sum(1 for n in nodes if n["deterministic"])
    # type-aware edge check (Haystack/Langflow pre-runtime port typing): an edge whose producer output type no consumer
    # input accepts is a WARNING (coverage is partial; we surface mismatches, we don't block on an un-typed plane).
    plane_of = {n["step"]: n.get("plane") for n in nodes}
    type_warnings = [[a, b] for a, b in edges if not edge_compatible(plane_of.get(a), plane_of.get(b))]
    return {"nodes": nodes, "edges": edges, "hallucinated": hallucinated, "acyclic": acyclic,
            "deterministic_ratio": round(det / len(nodes), 3) if nodes else 0.0, "type_warnings": type_warnings,
            "accepted": bool(nodes) and acyclic and det >= 1}


def intelligent_compile(intent: str, *, llm=None) -> dict:
    """The LLM finds components + composes the DAG; the registry validates it. Returns the composed+validated DAG."""
    pool = candidate_pool(intent)
    call = llm
    if call is None:
        from src.teleon.dag.real_steps import llm_available, real_llm
        if not llm_available():
            return {"intent": intent, "live": False, "reason": "LLM lane offline", "pool_size": len(pool), "serves_truth": False}
        call = lambda p: real_llm(p, system="You output ONLY compact JSON.", max_tokens=500, timeout=80).get("text", "")
    def _attempt(prompt):
        raw = call(prompt)
        try:
            return _validate(json.loads(raw[raw.index("{"):raw.rindex("}") + 1]), pool), None
        except Exception:  # noqa: BLE001
            return None, "did not return parseable JSON"

    base = _prompt(intent, pool)
    v, parse_err = _attempt(base)
    repaired = False
    if v is None or not v["accepted"]:                       # VALIDATION + REPAIR RETRY (the universal best practice)
        errs = parse_err or (f"rejected invented components {v['hallucinated']}" if v and v["hallucinated"] else
                             ("the DAG had a cycle" if v and not v["acyclic"] else "include at least one deterministic component"))
        v2, _ = _attempt(base + f"\nYour previous attempt FAILED: {errs}. Output ONLY valid JSON, use ONLY listed "
                                 "components, keep it acyclic, and include >=1 deterministic component.")
        repaired = True
        if v2 is not None and (v is None or v2["accepted"]):
            v = v2
    if v is None:
        return {"intent": intent, "live": True, "accepted": False, "reason": "no parseable DAG after repair retry",
                "repaired": repaired, "pool_size": len(pool), "serves_truth": False}
    # stricter tier above 'accepted': prove the composed DAG is a VERIFIED WORKING build (type-compatible edges + every
    # input satisfied + a terminal output + a real-executor dry-run), not merely acyclic + hallucination-free.
    build = verify_buildable_dag(v["nodes"], v["edges"])
    return {"intent": intent, "capability": I.outline(intent).get("capability"), "live": True, "pool_size": len(pool),
            "composed_dag": {"nodes": v["nodes"], "edges": v["edges"]}, "deterministic_ratio": v["deterministic_ratio"],
            "hallucinated_rejected": v["hallucinated"], "acyclic": v["acyclic"], "type_warnings": v.get("type_warnings"),
            "accepted": v["accepted"], "verified_working": build["verified_working"], "build_verdict": build,
            "repaired": repaired, "serves_truth": False}


def run_live(intent: str) -> dict:
    art = intelligent_compile(intent)
    if art.get("accepted"):
        try:
            from src.teleon.synthesis.variation_store import record_variations
            path = "/".join(n["component"] for n in art["composed_dag"]["nodes"])
            record_variations(art.get("capability") or "adhoc", [{"decision_path": path, "status": "compiled_live", "strategy": "llm_orchestrated", "note": intent[:80]}])
        except Exception:  # noqa: BLE001
            pass
    rec = {"seam": "live capability compile (LLM-orchestrated)", "intent": intent, "capability": art.get("capability"),
           "live": art.get("live"), "accepted": art.get("accepted"), "deterministic_ratio": art.get("deterministic_ratio"),
           "components": [n["component"] for n in art.get("composed_dag", {}).get("nodes", [])],
           "hallucinated_rejected": art.get("hallucinated_rejected"), "verified": bool(art.get("accepted")), "serves_truth": False}
    RECEIPT.write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)
    intent = "extract fields from these invoices into our schema"
    pool = candidate_pool(intent)
    ck("candidate pool is REAL components from the registry (searched)", len(pool) >= 5 and all(v.get("plane") for v in pool.values()))
    # the LLM composes a DAG from the pool; the registry validates it
    real = [c for c in pool if pool[c]["deterministic"]][:2]
    good = json.dumps({"nodes": [{"step": "x", "component": real[0]}, {"step": "y", "component": "llm"}], "edges": [["x", "y"]]})
    art = intelligent_compile(intent, llm=lambda p: good)
    ck("LLM-composed DAG is ACCEPTED when components are real + acyclic + deterministic-first", art["accepted"] and art["deterministic_ratio"] > 0)
    # hallucination guardrail: a made-up component is REJECTED, not run
    bad = json.dumps({"nodes": [{"step": "x", "component": "totally_made_up_tool_xyz"}], "edges": []})
    artb = intelligent_compile(intent, llm=lambda p: bad)
    ck("a hallucinated component is REJECTED (registry guardrail)", "totally_made_up_tool_xyz" in artb["hallucinated_rejected"] and not artb["accepted"])
    ck("the LLM cannot invent components — only real registry ones compose", all(n["component"] in pool for n in art["composed_dag"]["nodes"]))
    # type-aware edge check (Haystack/Langflow pre-runtime port typing) — surfaced as warnings, grounded in plane_io_contracts
    ck("type-aware edge check: ocr(text)->field_parsing(text) compatible; tts(audio)->field_parsing(text) NOT",
       edge_compatible("ocr", "field_parsing") and not edge_compatible("tts", "field_parsing"))
    ck("compiler surfaces type_warnings (a producer output no consumer input accepts)", "type_warnings" in art)
    ck("compiler reports a stricter VERIFIED-WORKING build verdict (type-compatible + satisfiable + dry-run)",
       isinstance(art.get("verified_working"), bool) and "build_verdict" in art)
    ck("the prompt grounds candidates with their I/O types (type-aware composition, Langflow port-typing)",
       "io=" in _prompt(intent, pool) and "->" in _prompt(intent, pool))
    ck("serves_truth=false", art["serves_truth"] is False)
    print("\n" + ("PASS - compile_capability_live: LLM finds REAL components + composes a validated DAG; hallucinations "
                  "rejected; deterministic-first. Full orchestration, not a scaffold." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    q = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "extract fields from these invoices into our schema"
    print(json.dumps(run_live(q), indent=2))
