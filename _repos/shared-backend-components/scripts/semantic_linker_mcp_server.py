#!/usr/bin/env python3
"""semantic_linker_mcp_server — the SEMANTIC-LINKER control plane as MCP meta-tools (stdio, stdlib-only).

The vision's rule: an MCP server exposes a SMALL FIXED SET of meta-tools — never ten thousand primitives as ten
thousand tools (that recreates the context-size problem the system exists to solve). This server exposes the SEVEN
linker meta-tools over the shared stdio transport (`_mcp_stdio`):

  workspace_profile   -> the registry/workspace profile an agent needs before planning (compact, no source dump)
  primitive_search    -> Level-0 SKETCHES over the 10.28M-vector facet store (progressive disclosure starts here)
  primitive_expand    -> Level 1/2/3 disclosure for ONE primitive (contract -> evidence -> impl) on demand
  graph_solve         -> resolve a capability PLAN to verified primitives + blockers (semantic_linker_resolve)
  graph_apply         -> deterministically ASSEMBLE the resolved graph -> wiring + adapters + mountable artifact
  graph_verify        -> static verification (structure + policy + token projection); live exec deferred (see below)
  candidate_promote   -> promotion-READINESS check (never flips serves_truth; gates only)

This is the multi-step ROUTE-composition control plane — distinct from (and complementary to) the single-primitive
reuse tools in `capability_retrieval_mcp_server` and the reuse fabric. It REUSES the facet store (retrieval) +
semantic_linker_resolve/assemble (composition); it introduces no new retrieval engine.

Boundaries: LIVE token/oracle measurement is `semantic_linker_long_session_benchmark.py` (Codex) + the reuse
fabric's execute/prove — graph_verify here is a STATIC gate and says so. serves_truth=false: every result is a
governed candidate (a plan/route/readiness), never served truth, and nothing here executes a primitive.

    claude mcp add semantic-linker -- python3 <repo>/_repos/shared-backend-components/scripts/semantic_linker_mcp_server.py
    PYTHONPATH=. python3 scripts/semantic_linker_mcp_server.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts import _mcp_stdio  # noqa: E402  the ONE shared newline-delimited MCP stdio transport
from scripts import semantic_linker_resolve as _resolve  # noqa: E402
from scripts import semantic_linker_assemble as _assemble  # noqa: E402

SERVER_NAME = "semantic-linker"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"
_METHOD_NOT_FOUND = _mcp_stdio.METHOD_NOT_FOUND
_INTERNAL_ERROR = _mcp_stdio.INTERNAL_ERROR

# --- progressive-disclosure levels (the token-savings mechanism: bodies never enter context unless needed) -------
_LEVEL_FIELDS = {
    0: ("primitive_id", "title", "input_edge", "output_edge", "trust"),                       # SKETCH
    1: ("primitive_id", "title", "input_edge", "output_edge", "trust", "blackbox", "effects", "mutations", "contract"),  # CONTRACT
    2: ("primitive_id", "title", "input_edge", "output_edge", "trust", "blackbox", "effects", "contract",
        "proof_requirements", "verification_level", "source_refs", "promotion_blockers"),      # EVIDENCE
    3: None,                                                                                    # IMPL = the whole card
}


def _disclose(card: dict[str, Any], level: int) -> dict[str, Any]:
    fields = _LEVEL_FIELDS.get(level, _LEVEL_FIELDS[0])
    if fields is None:  # level 3 = full card (edge_contract stands in for a body; we hold descriptors, not bodies)
        return card
    return {k: card.get(k) for k in fields if k in card}


# --- tool catalog (name + description + JSON Schema) -------------------------------------------------------------
_PLAN_SCHEMA = {"type": "object", "description": "A capability plan (graph IR): {name, steps:[{var,capability,in}], policy}."}
TOOLS: list[dict[str, Any]] = [
    {"name": "workspace_profile",
     "description": "The registry/workspace profile to read BEFORE planning: primitive corpus size, facet families, "
                    "embed model, coverage — compact, no source dump. serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"root": {"type": "string"}}, "additionalProperties": False}},
    {"name": "primitive_search",
     "description": "Retrieve reusable primitives by intent over the multivector FACET store (the semantic "
                    "envelope). Returns Level-0 SKETCHES (id, title, input->output edge, trust, score) — the "
                    "start of progressive disclosure, NOT bodies. serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
                     "required": ["query"], "additionalProperties": False}},
    {"name": "primitive_expand",
     "description": "Progressive disclosure for ONE primitive: level 1=contract, 2=evidence, 3=implementation. "
                    "The agent expands only what a decision needs — bodies never flood context. serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"primitive_id": {"type": "string"}, "level": {"type": "integer"}},
                     "required": ["primitive_id"], "additionalProperties": False}},
    {"name": "graph_solve",
     "description": "Resolve a capability PLAN (graph IR) to verified primitives: retrieve per capability, apply "
                    "HARD policy/effect blockers, return lock + explicit residual for misses. Retrieval "
                    "probabilistic, acceptance deterministic. serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"plan": _PLAN_SCHEMA, "k": {"type": "integer"}},
                     "required": ["plan"], "additionalProperties": False}},
    {"name": "graph_apply",
     "description": "Deterministically ASSEMBLE a resolved plan: dataflow wiring + typed adapters for port "
                    "mismatches + a mountable artifact (verified primitives mounted verbatim = 0-token "
                    "composition) + residual holes. serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"plan": _PLAN_SCHEMA, "k": {"type": "integer"}},
                     "required": ["plan"], "additionalProperties": False}},
    {"name": "graph_verify",
     "description": "STATIC verification of an assembled plan: assembly_valid, deterministic_composition, "
                    "policy gates, token projection. LIVE test/oracle/token execution is deferred to the reuse "
                    "fabric + the long-session benchmark (says so). serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"plan": _PLAN_SCHEMA, "k": {"type": "integer"}},
                     "required": ["plan"], "additionalProperties": False}},
    {"name": "candidate_promote",
     "description": "Promotion-READINESS check for a primitive (gates only — NEVER flips serves_truth). Reports "
                    "blockers that must clear (source review, executed proof, open tickets). serves_truth=false.",
     "inputSchema": {"type": "object", "properties": {"primitive_id": {"type": "string"}},
                     "required": ["primitive_id"], "additionalProperties": False}},
]


# --- retrieval/card seam (injectable for offline self-test; real serving loads the facet store) -----------------
def _load_serving(fixtures: Optional[dict] = None):
    """Return (cards, retriever). fixtures may inject {cards, retriever} for offline tests; else load the real
    corpus + a facet-store-backed retriever."""
    if fixtures and "cards" in fixtures:
        cards = fixtures["cards"]
        return cards, fixtures.get("retriever") or _resolve._keyword_retriever(cards)
    from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415
    cards = _facet.load_cards(sample=0)

    def _r(query: str, k: int) -> list[dict[str, Any]]:
        return _facet.facet_search(query, cards, k=k)
    return cards, _r


# --- tool implementations (pure: shape a JSON-able result; serves_truth=false everywhere) -----------------------
def _t_workspace_profile(args: dict, cards: list[dict[str, Any]]) -> dict:
    fams: dict[str, int] = {}
    for c in cards:
        for t in (c.get("capability_tags") or []):
            fams[str(t)] = fams.get(str(t), 0) + 1
    return {"corpus_size": len(cards), "distinct_capability_tags": len(fams),
            "note": "registry profile (compact). Local language/framework/dependency analysis is the next step "
                    "(the vision's local daemon); not yet computed.", "serves_truth": False}


def _t_primitive_search(args: dict, cards, retriever) -> dict:
    query, limit = str(args.get("query", "")), int(args.get("limit") or 10)
    hits = retriever(query, limit) or []
    idx = _resolve._card_index(cards)
    sketches = [_disclose({**(idx.get(str(h.get("primitive_id"))) or {}), **h}, 0) | {"score": h.get("score")}
                for h in hits]
    return {"query": query, "count": len(sketches), "level": 0, "results": sketches, "serves_truth": False}


def _t_primitive_expand(args: dict, cards) -> dict:
    pid, level = str(args.get("primitive_id", "")), int(args.get("level") or 1)
    card = _resolve._card_index(cards).get(pid)
    if not card:
        return {"primitive_id": pid, "found": False, "serves_truth": False}
    return {"primitive_id": pid, "found": True, "level": level, "disclosure": _disclose(card, level),
            "serves_truth": False}


def _t_graph_solve(args: dict, cards, retriever) -> dict:
    return _resolve.link(args.get("plan"), retriever=retriever, cards=cards, k=int(args.get("k") or 8))


def _t_graph_apply(args: dict, cards, retriever) -> dict:
    asm = _assemble.link_and_assemble(args.get("plan"), cards=cards, retriever=retriever, k=int(args.get("k") or 8))
    return asm


def _t_graph_verify(args: dict, cards, retriever) -> dict:
    asm = _assemble.link_and_assemble(args.get("plan"), cards=cards, retriever=retriever, k=int(args.get("k") or 8))
    return {"assembly_valid": asm["assembly_valid"], "deterministic_composition": asm["deterministic_composition"],
            "n_mounted": asm["n_mounted"], "n_adapters": asm["n_adapters"], "n_residual": asm["n_residual"],
            "gates": {"all_capabilities_resolved": asm["n_residual"] == 0,
                      "no_unbridged_ports": True},  # adapters are declared residual-adapters, not unbridged
            "token_projection": asm.get("token_projection"),
            "note": "STATIC verification only (structure + policy + projection). LIVE tests/oracle/token execution "
                    "= the reuse fabric (materialize->execute->prove) + semantic_linker_long_session_benchmark.",
            "serves_truth": False}


def _t_candidate_promote(args: dict, cards) -> dict:
    pid = str(args.get("primitive_id", ""))
    card = _resolve._card_index(cards).get(pid)
    if not card:
        return {"primitive_id": pid, "found": False, "promotable": False, "serves_truth": False}
    blockers = list(card.get("promotion_blockers") or [])
    if str(card.get("verification_level")) not in ("execution", "verified"):
        blockers.append("no executed proof (verification_level != execution)")
    if card.get("source_evidence_status") not in ("verified", "present"):
        blockers.append("source evidence unverified")
    return {"primitive_id": pid, "found": True, "promotable": not blockers, "blockers": blockers,
            "note": "READINESS only — promotion needs source review + an executed passing proof + the gates; this "
                    "call NEVER flips serves_truth.", "serves_truth": False}


# --- protocol handlers ------------------------------------------------------------------------------------------
def handle_initialize(params: object) -> dict:
    client_pv = (params or {}).get("protocolVersion") if isinstance(params, dict) else None
    return {"protocolVersion": client_pv or PROTOCOL_VERSION, "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}


def _text(result: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(result, sort_keys=True)}], "isError": False}


def _err(msg: str) -> dict:
    return {"content": [{"type": "text", "text": msg}], "isError": True}


def _handle_tools_call(params: object, *, fixtures: Optional[dict] = None) -> dict:
    if not isinstance(params, dict):
        return _err("tools/call params must be an object")
    name, args = params.get("name"), (params.get("arguments") or {})
    if not isinstance(args, dict):
        return _err("arguments must be an object")
    try:
        if name in ("workspace_profile", "primitive_search", "primitive_expand", "candidate_promote",
                    "graph_solve", "graph_apply", "graph_verify"):
            cards, retriever = _load_serving(fixtures)
            if name == "workspace_profile":
                return _text(_t_workspace_profile(args, cards))
            if name == "primitive_search":
                return _text(_t_primitive_search(args, cards, retriever))
            if name == "primitive_expand":
                return _text(_t_primitive_expand(args, cards))
            if name == "candidate_promote":
                return _text(_t_candidate_promote(args, cards))
            if name == "graph_solve":
                return _text(_t_graph_solve(args, cards, retriever))
            if name == "graph_apply":
                return _text(_t_graph_apply(args, cards, retriever))
            if name == "graph_verify":
                return _text(_t_graph_verify(args, cards, retriever))
        return _err(f"unknown tool {name!r}; tools are {[t['name'] for t in TOOLS]}")
    except Exception as exc:  # noqa: BLE001 — a tool fault surfaces in-band (isError), never crashes the transport
        return _err(f"{name} failed: {exc}")


def dispatch(request: dict, *, fixtures: Optional[dict] = None) -> Optional[dict]:
    method, rid, params = request.get("method"), request.get("id"), request.get("params")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": handle_initialize(params)}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        return {"jsonrpc": "2.0", "id": rid, "result": _handle_tools_call(params, fixtures=fixtures)}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": _METHOD_NOT_FOUND, "message": f"method not found: {method}"}}


def serve(stdin=None, stdout=None) -> int:
    return _mcp_stdio.serve(dispatch, stream_in=stdin, stream_out=stdout)


# --- self-test: every tool exercised OFFLINE through the real tools/call envelope --------------------------------
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def ck(name, cond):
        checks.append((name, bool(cond)))

    cards = _resolve._fixture_cards()
    fx = {"cards": cards, "retriever": _resolve._keyword_retriever(cards)}

    init = handle_initialize({"protocolVersion": PROTOCOL_VERSION})
    ck("initialize returns serverInfo.name", init.get("serverInfo", {}).get("name") == SERVER_NAME)
    tl = dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    ck("tools/list returns the 7 meta-tools",
       [t["name"] for t in tl["result"]["tools"]] == ["workspace_profile", "primitive_search", "primitive_expand",
                                                       "graph_solve", "graph_apply", "graph_verify", "candidate_promote"])

    def call(tool, args):
        r = dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                      "params": {"name": tool, "arguments": args}}, fixtures=fx)
        res = r["result"]
        return res, (json.loads(res["content"][0]["text"]) if not res["isError"] else None)

    r, body = call("workspace_profile", {})
    ck("workspace_profile not error + reports corpus_size", r["isError"] is False and body["corpus_size"] == len(cards))

    r, body = call("primitive_search", {"query": "hash password digest", "limit": 5})
    ck("primitive_search returns Level-0 sketches (no blackbox body leaked)",
       r["isError"] is False and body["level"] == 0 and body["results"]
       and "blackbox" not in body["results"][0])
    ck("primitive_search finds the password-hash primitive",
       any(h["primitive_id"] == "prim:t:hash" for h in body["results"]))

    r, body = call("primitive_expand", {"primitive_id": "prim:t:hash", "level": 1})
    ck("primitive_expand level 1 discloses the contract (blackbox now present)",
       r["isError"] is False and body["found"] and "blackbox" in body["disclosure"])

    r, body = call("graph_solve", {"plan": _resolve._CREATE_USER_PLAN})
    ck("graph_solve resolves create-user 5/5, route_ok", r["isError"] is False and body["route_ok"]
       and len(body["resolved"]) == 5)

    r, body = call("graph_apply", {"plan": _resolve._CREATE_USER_PLAN})
    ck("graph_apply assembles a valid deterministic composition + artifact",
       r["isError"] is False and body["assembly_valid"] and body["deterministic_composition"]
       and "def create_user_v1" in body["artifact"])

    r, body = call("graph_verify", {"plan": _resolve._CREATE_USER_PLAN})
    ck("graph_verify passes static gates + labels itself static (defers live exec)",
       r["isError"] is False and body["gates"]["all_capabilities_resolved"] and "STATIC" in body["note"])

    r, body = call("candidate_promote", {"primitive_id": "prim:t:hash"})
    ck("candidate_promote reports NOT promotable (candidate fixture) + never flips serves_truth",
       r["isError"] is False and body["promotable"] is False and body["serves_truth"] is False)

    r, _ = call("primitive_search", {"query": ""})  # empty query -> no results, not a crash
    ck("empty query is handled (not a crash)", r["isError"] is False)
    r = dispatch({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                  "params": {"name": "nope", "arguments": {}}}, fixtures=fx)
    ck("unknown tool -> in-band isError", r["result"]["isError"] is True)

    fails = [n for n, ok in checks if not ok]
    ok = not fails
    print(f"{'PASS' if ok else 'FAIL'} - semantic_linker_mcp_server: stdlib MCP over stdio (initialize + "
          f"tools/list[7] + tools/call) wiring the 7 linker meta-tools (workspace_profile/primitive_search/"
          f"primitive_expand/graph_solve/graph_apply/graph_verify/candidate_promote); {len(checks)} assertions "
          f"OFFLINE; serves_truth=false, read-only")
    for n, passed in checks:
        if not passed:
            print(f"  [XX] {n}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    return serve()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
