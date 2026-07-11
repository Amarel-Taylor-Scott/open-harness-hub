#!/usr/bin/env python3
"""capability_agent_tool — the DETERMINISTIC developer/agent tool beside the flexible MCP tool.

Owner (2026-07-10): "We should have both an MCP tool and a developer/agent tool; the MCP tool can be more flexible
and learn from the environment and requests, and database." This is the second half of that pair: a deterministic,
ALLOWLISTED, receipt-backed JSON tool any developer, harness, hook, or non-MCP agent can call — same engines the
MCP server serves (no parallel implementation; every handler delegates to the existing modules), none of the
adaptive reordering (the learned lane lives on the MCP side; this tool RECORDS signals deterministically but never
reorders results with them).

Actions (one registry row each — extending the tool = add a row, never a rewrite):
  retrieval.search/get/compose · corpus.status                  -> capability_retrieval_mcp_server engines
  usage.record/report                                           -> primitive_usage_ledger (hash-chained)
  waterfall.levels/plan/apply(guarded)                          -> adaptive_vectorization (the vector spend policy)
  provision.plan/preflight/status/apply(billing-gated)          -> cloud_provisioning (key-based self-service)
  environment.profile · learning.status                         -> environment_request_learning

Key-based operation: set ``OH_AGENT_TOOL_KEY`` (or ``OH_AGENT_TOOL_KEY_FILE``) and every request must carry a
matching ``"key"`` (constant-time compare) — the remote/billed lane. Unset -> open local mode. The raw key is
never written to receipts. Every request appends an audit receipt (action, sanitized-args digest, ok, duration);
guarded actions keep their own guards (waterfall.apply needs confirm; provision.apply needs OH_BILLING_ENABLED=1
+ confirm). All results are governed candidates: serves_truth=false.

    PYTHONPATH=. python3 scripts/capability_agent_tool.py --list-actions
    PYTHONPATH=. python3 scripts/capability_agent_tool.py --request-json '{"action":"retrieval.search","args":{"query":"parse csv header"}}'
    PYTHONPATH=. python3 scripts/capability_agent_tool.py --request-json '{"action":"waterfall.plan"}'
    PYTHONPATH=. python3 scripts/capability_agent_tool.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

AGENT_TOOL_KEY_ENVIRONMENT_VARIABLE = "OH_AGENT_TOOL_KEY"
AGENT_TOOL_KEY_FILE_ENVIRONMENT_VARIABLE = "OH_AGENT_TOOL_KEY_FILE"
#: Redirects receipts into a sandbox dir (test isolation / per-tenant); unset -> the canonical data location.
AGENT_TOOL_DATA_DIR_ENVIRONMENT_VARIABLE = "OH_AGENT_TOOL_DATA_DIR"
_DEFAULT_DATA_DIR = _REPO / "data" / "dev-intel" / "capability_agent_tool"
_ARGS_PREVIEW_CHARS = 240   # bounded sanitized-args snippet on a receipt (digest carries identity)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _digest16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def receipts_path() -> Path:
    override = os.environ.get(AGENT_TOOL_DATA_DIR_ENVIRONMENT_VARIABLE)
    return (Path(override) if override else _DEFAULT_DATA_DIR) / "receipts.jsonl"


def _configured_key() -> Optional[str]:
    direct = os.environ.get(AGENT_TOOL_KEY_ENVIRONMENT_VARIABLE)
    if direct:
        return direct
    key_file = os.environ.get(AGENT_TOOL_KEY_FILE_ENVIRONMENT_VARIABLE)
    if key_file and Path(key_file).exists():
        return Path(key_file).read_text().strip() or None
    return None


# ================================================================================================================
# Action handlers — every one DELEGATES to an existing engine (reuse-first; no parallel implementation)
# ================================================================================================================
def _act_actions_list(args: dict, fixtures: dict) -> dict:
    return {"actions": [{"action": name, "description": row["description"], "side_effects": row["side_effects"],
                         "guarded": row.get("guarded", False)} for name, row in sorted(ACTIONS.items())]}


def _act_retrieval_search(args: dict, fixtures: dict) -> dict:
    from scripts.capability_retrieval_mcp_server import MAX_QUERY_CHARS, run_primitive_search  # noqa: PLC0415
    query = str(args.get("query") or "").strip()[:MAX_QUERY_CHARS]
    if not query:
        raise ValueError("retrieval.search requires a non-empty `query`")
    index = fixtures.get("index")
    response = run_primitive_search(query, _clamped_limit(args.get("limit")), index=index,
                                    scope=str(args.get("scope") or ("governed" if index else "all")),
                                    pool=str(args.get("pool") or "").strip() or None,
                                    evidence=str(args.get("evidence") or "any"))
    if args.get("record", True):
        _record_search_signal(query, response, fixtures)
    return response


def _record_search_signal(query: str, response: dict, fixtures: dict) -> None:
    """Deterministic signal RECORDING (never reordering): the same ledgers the MCP adaptive lane learns from."""
    from scripts import environment_request_learning as _learning  # noqa: PLC0415
    from scripts import primitive_usage_ledger as _usage_ledger  # noqa: PLC0415
    hits = [h for h in (response.get("results") or []) if isinstance(h, dict)]
    _usage_ledger.log_search(query, hits, agent="agent_tool", ts=_now_iso(),
                             ledger_path=fixtures.get("usage_ledger_path"))
    _learning.log_request(surface="agent_tool", action="retrieval.search", query_text=query,
                          environment_profile={"root_digest": "", "technologies": []},
                          result_count=len(hits),
                          top_primitive_ids=[str(h.get("primitive_id") or "") for h in hits])


def _clamped_limit(raw: object) -> int:
    from scripts.capability_retrieval_mcp_server import MAX_SEARCH_LIMIT  # noqa: PLC0415  single-source clamp
    from scripts.build_primitive_search_index import DEFAULT_LIMIT  # noqa: PLC0415
    try:
        return min(MAX_SEARCH_LIMIT, max(1, int(raw)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return DEFAULT_LIMIT


def _view_limit(args: dict, default: int) -> int:
    """A page-size limit for the composition VIEWS (groups/remixes) — no small search cap. A missing value uses
    the default; a NEGATIVE value clamps to 0 (never a slice-from-the-end, which silently drops rows)."""
    if "limit" not in args:
        return default
    try:
        return max(0, int(args["limit"]))
    except (TypeError, ValueError):
        return default


def _act_retrieval_get(args: dict, fixtures: dict) -> dict:
    primitive_id = str(args.get("primitive_id") or "").strip()
    if not primitive_id:
        raise ValueError("retrieval.get requires a non-empty `primitive_id`")
    federation = fixtures.get("federation")
    if federation is None:
        from scripts.primitive_search_federation import PrimitiveSearchFederation  # noqa: PLC0415
        federation = PrimitiveSearchFederation()
    result = federation.get(primitive_id, sync=bool(args.get("sync", False)),
                            load_core_payload=bool(args.get("include_payload", False)))
    if args.get("record", True):
        from scripts import primitive_usage_ledger as _usage_ledger  # noqa: PLC0415
        _usage_ledger.log_download(primitive_id, ts=_now_iso(), ledger_path=fixtures.get("usage_ledger_path"))
    return result


def _act_retrieval_compose(args: dict, fixtures: dict) -> dict:
    from scripts.capability_retrieval_mcp_server import run_capability_compose  # noqa: PLC0415
    request_text = str(args.get("request") or "").strip()
    if not request_text:
        raise ValueError("retrieval.compose requires a non-empty `request`")
    return run_capability_compose(request_text, _clamped_limit(args.get("limit")), cards=fixtures.get("cards"))


def _act_corpus_status(args: dict, fixtures: dict) -> dict:
    from scripts.capability_retrieval_mcp_server import run_primitive_corpus_status  # noqa: PLC0415
    return run_primitive_corpus_status(federation=fixtures.get("federation"))


def _act_usage_record(args: dict, fixtures: dict) -> dict:
    from scripts import primitive_usage_ledger as _usage_ledger  # noqa: PLC0415
    event_type = str(args.get("event_type") or "")
    primitive_ids = [str(p) for p in (args.get("primitive_ids") or []) if str(p).strip()]
    if event_type not in _usage_ledger.EVENT_TYPES or not primitive_ids:
        raise ValueError(f"usage.record requires event_type in {_usage_ledger.EVENT_TYPES} and primitive_ids")
    return _usage_ledger.log_event(event_type, primitive_ids=primitive_ids,
                                   query_text=str(args.get("query_text") or ""),
                                   outcome=str(args.get("outcome") or ""),
                                   session_id=str(args.get("session_id") or ""),
                                   agent=str(args.get("agent") or "agent_tool"),
                                   ts=str(args.get("ts") or _now_iso()),
                                   ledger_path=fixtures.get("usage_ledger_path"))


def _act_usage_report(args: dict, fixtures: dict) -> dict:
    from scripts import primitive_usage_ledger as _usage_ledger  # noqa: PLC0415
    primitive_id = str(args.get("primitive_id") or "").strip()
    if not primitive_id:
        raise ValueError("usage.report requires a non-empty `primitive_id`")
    return _usage_ledger.primitive_usage(primitive_id, fixtures.get("usage_ledger_path"))


def _act_waterfall_levels(args: dict, fixtures: dict) -> dict:
    from scripts import adaptive_vectorization as _waterfall  # noqa: PLC0415
    return _waterfall.levels_view()


def _act_waterfall_plan(args: dict, fixtures: dict) -> dict:
    from scripts import adaptive_vectorization as _waterfall  # noqa: PLC0415
    n_corpus = int(args.get("n_corpus") or _waterfall.DEFAULT_CORPUS_SIZE)
    return _waterfall.waterfall_plan(_waterfall.load_level_state(fixtures.get("waterfall_state_path")),
                                     _waterfall.signals_from_ledger(fixtures.get("usage_ledger_path")),
                                     n_corpus=n_corpus)


def _act_waterfall_apply(args: dict, fixtures: dict) -> dict:
    from scripts import adaptive_vectorization as _waterfall  # noqa: PLC0415
    return _waterfall.apply_plan(confirm=bool(args.get("confirm")),
                                 n_corpus=int(args.get("n_corpus") or _waterfall.DEFAULT_CORPUS_SIZE),
                                 ts=_now_iso(),
                                 state_path=fixtures.get("waterfall_state_path"),
                                 history_path=fixtures.get("waterfall_history_path"),
                                 worklist_path=fixtures.get("waterfall_worklist_path"),
                                 ledger_path=fixtures.get("usage_ledger_path"))


def _act_provision_plan(args: dict, fixtures: dict) -> dict:
    from scripts import cloud_provisioning as _provisioning  # noqa: PLC0415
    return _provisioning.plan(int(args.get("scale") or 100_000_000))


def _act_provision_preflight(args: dict, fixtures: dict) -> dict:
    from scripts import cloud_provisioning as _provisioning  # noqa: PLC0415
    return _provisioning.preflight()


def _act_provision_status(args: dict, fixtures: dict) -> dict:
    from scripts import cloud_provisioning as _provisioning  # noqa: PLC0415
    return _provisioning.status()


def _act_provision_apply(args: dict, fixtures: dict) -> dict:
    from scripts import cloud_provisioning as _provisioning  # noqa: PLC0415
    return _provisioning.apply(confirm=bool(args.get("confirm")))  # its own billing gate stays authoritative


def _act_environment_profile(args: dict, fixtures: dict) -> dict:
    from scripts import environment_request_learning as _learning  # noqa: PLC0415
    return _learning.fingerprint_environment(str(args.get("root") or os.getcwd()))


def _act_learning_status(args: dict, fixtures: dict) -> dict:
    from scripts import environment_request_learning as _learning  # noqa: PLC0415
    return _learning.learning_status()


# ── composition layer (groups · frameworks · deterministic remixers · integrators) — read-only, 0-token ──────
def _composition_corpus(fixtures: dict) -> list[dict[str, Any]]:
    if isinstance(fixtures.get("composition_cards"), list):
        return fixtures["composition_cards"]
    from scripts.primitive_groups_frameworks_and_remixers import default_cards  # noqa: PLC0415
    return default_cards()


def _act_composition_groups(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_groups_frameworks_and_remixers import GROUP_BUILDERS, build_groups  # noqa: PLC0415
    groups = build_groups(_composition_corpus(fixtures))
    builder = str(args.get("builder") or "")
    if builder:
        groups = [g for g in groups if g["builder"] == builder]
    return {"builders": sorted(GROUP_BUILDERS), "count": len(groups),
            "groups": groups[:_view_limit(args, 50)], "candidate": True, "serves_truth": False}


def _act_composition_frameworks(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_groups_frameworks_and_remixers import (  # noqa: PLC0415
        FRAMEWORKS, framework_rows, instantiate_framework)
    cards = _composition_corpus(fixtures)
    name = str(args.get("framework") or "")
    if name:   # a supplied-but-unknown name is an error, not a silent fall-through to the catalog
        if name not in FRAMEWORKS:
            raise ValueError(f"unknown framework {name!r}; known: {sorted(FRAMEWORKS)}")
        return {"instance": instantiate_framework(name, cards, scope_family=args.get("scope_family")),
                "candidate": True, "serves_truth": False}
    return {"frameworks": framework_rows(), "candidate": True, "serves_truth": False}


def _act_composition_remix(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_groups_frameworks_and_remixers import REMIX_TRANSFORMS, build_remixes  # noqa: PLC0415
    remixes = build_remixes(_composition_corpus(fixtures))
    return {"transforms": {n: t["kind"] for n, t in sorted(REMIX_TRANSFORMS.items())},
            "count": len(remixes), "remixes": remixes[:_view_limit(args, 25)],
            "note": "deterministic remixes only; the llm seam is declared, never run here",
            "candidate": True, "serves_truth": False}


def _act_composition_integrate(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_groups_frameworks_and_remixers import (  # noqa: PLC0415
        build_remixes, integrate_exact_route)
    cards = _composition_corpus(fixtures)
    corpus = cards + build_remixes(cards) if args.get("use_aligned_remixes", True) else cards
    return {"integration": integrate_exact_route(corpus, str(args.get("start") or ""),
                                                 str(args.get("goal") or "")),
            "candidate": True, "serves_truth": False}


# ── networks (step lattices) + grid search — the "grid of potential primitives" ──────────────────────────────
def _network_corpus(fixtures: dict) -> list[Any]:
    """The corpus networks resolve over: the same injectable base as the composition views, plus its aligned
    remixes (mirrors primitive_networks_and_grid_search.aligned_corpus, but honoring the fixture seam)."""
    from scripts.primitive_groups_frameworks_and_remixers import build_remixes  # noqa: PLC0415
    cards = _composition_corpus(fixtures)
    return cards + build_remixes(cards)


def _act_network_list(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_networks_and_grid_search import NETWORK_TABLE, build_network  # noqa: PLC0415
    corpus = _network_corpus(fixtures)
    networks = [build_network(row["name"], row["edge_chain"], corpus, row["description"])
                for row in NETWORK_TABLE]
    return {"count": len(networks),
            "networks": [{k: n[k] for k in ("network_id", "name", "description", "edge_chain", "slot_sizes",
                                            "grid_size", "step_count", "candidate", "serves_truth")}
                         for n in networks],
            "candidate": True, "serves_truth": False}


def _act_network_grid_search(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_networks_and_grid_search import (  # noqa: PLC0415
        DEFAULT_MAX_PATHS, NETWORK_TABLE, build_network, grid_search)
    corpus = _network_corpus(fixtures)
    name = str(args.get("network") or "")
    edge_chain = args.get("edge_chain")
    if isinstance(edge_chain, list) and edge_chain:
        network = build_network(str(args.get("name") or "adhoc"), [str(e) for e in edge_chain], corpus,
                                str(args.get("description") or "ad-hoc network"))
    else:
        row = next((r for r in NETWORK_TABLE if r["name"] == name), None)
        if row is None:   # a failed request must fail the envelope, not report ok=true
            raise ValueError(f"unknown network {name!r}; known: {[r['name'] for r in NETWORK_TABLE]} "
                             "(or pass edge_chain=[...])")
        network = build_network(row["name"], row["edge_chain"], corpus, row["description"])
    receipt = grid_search(network, corpus, max_paths=int(args.get("max_paths") or DEFAULT_MAX_PATHS))
    omitted = receipt.pop("paths", [])   # rankings + Pareto are the answer; the path set is re-derivable
    receipt["paths_omitted"] = len(omitted)
    receipt["paths_note"] = ("full per-path scores omitted from this envelope; re-derive deterministically by "
                             "running the module with the same network + max_paths, or read the on-disk "
                             "network_path_candidates.jsonl from --build")
    return {"network": network["name"], "grid_size": network["grid_size"],
            "receipt": receipt, "candidate": True, "serves_truth": False}


# ── deployment + resource estimator (the "agent that calculates resource needs from a use case") ─────────────
def _act_deployment_estimate(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_deployment_profiler import estimate  # noqa: PLC0415
    corpus = _composition_corpus(fixtures)
    ident = str(args.get("primitive") or args.get("primitive_id") or "")
    card = next((c for c in corpus if ident in (c.get("card_id"), c.get("primitive_id"),
                                                c.get("output_edge"), c.get("title"))), None)
    if card is None:
        raise ValueError(f"no primitive matches {ident!r} (try a card_id, output_edge, or title)")
    use_case = dict(args.get("use_case") or {})
    for k in ("records_per_day", "freshness", "latency_sla_ms", "peak_concurrency", "stateful"):
        if k in args:
            use_case[k] = args[k]
    return {"estimate": estimate(card, use_case, with_cloud_stack=bool(args.get("cloud_stack"))),
            "candidate": True, "serves_truth": False}


def _act_deployment_profile_network(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_deployment_profiler import profile_network  # noqa: PLC0415
    from scripts.primitive_networks_and_grid_search import NETWORK_TABLE, build_network  # noqa: PLC0415
    corpus = _network_corpus(fixtures)
    cards = _composition_corpus(fixtures)
    name = str(args.get("network") or "")
    row = next((r for r in NETWORK_TABLE if r["name"] == name), None)
    if row is None:
        raise ValueError(f"unknown network {name!r}; known: {[r['name'] for r in NETWORK_TABLE]}")
    network = build_network(row["name"], row["edge_chain"], corpus, row["description"])
    use_case = dict(args.get("use_case") or {})
    for k in ("records_per_day", "freshness", "latency_sla_ms", "peak_concurrency", "stateful"):
        if k in args:
            use_case[k] = args[k]
    return {"profile": profile_network(network, cards, use_case), "candidate": True, "serves_truth": False}


def _act_robust_lane_coverage(args: dict, fixtures: dict) -> dict:
    from scripts.robust_lane_router import classify_need, robust_lane_coverage  # noqa: PLC0415
    cards = _composition_corpus(fixtures)
    need = str(args.get("need") or "")
    if need:
        from scripts.producer_edge_index import build_producer_edge_index  # noqa: PLC0415
        return {"classification": classify_need(need, build_producer_edge_index(cards)),
                "candidate": True, "serves_truth": False}
    needs = args.get("needs") or sorted({c.get("output_edge") for c in cards if c.get("output_edge")}
                                        | {c.get("input_edge") for c in cards if c.get("input_edge")})
    cov = robust_lane_coverage([str(n) for n in needs], cards)
    return {"n_needs": cov["n_needs"], "per_lane": cov["per_lane"],
            "robust_fraction": cov["robust_fraction"], "note": cov["note"],
            "candidate": True, "serves_truth": False}


def _act_alignment_screen(args: dict, fixtures: dict) -> dict:
    from scripts.edge_alignment_gate import evidence, screen  # noqa: PLC0415
    from scripts.primitive_groups_frameworks_and_remixers import CANONICAL_EDGE_ALIGNMENTS  # noqa: PLC0415
    raw = args.get("proposals") or ([{"from": args.get("from"), "to": args.get("to")}]
                                    if args.get("from") and args.get("to") else [])
    pairs = [(str(p.get("from")), str(p.get("to"))) for p in raw if p.get("from") and p.get("to")]
    if not pairs:
        raise ValueError("pass {from, to} or {proposals: [{from, to}, ...]}")
    verdicts = screen(pairs, existing=dict(CANONICAL_EDGE_ALIGNMENTS))
    cards = _composition_corpus(fixtures)
    for v in verdicts:
        if v["admissible"]:
            v["evidence"] = evidence(v["from_edge"], v["to_edge"], cards, existing=dict(CANONICAL_EDGE_ALIGNMENTS))
    return {"verdicts": verdicts, "admitted": sum(v["admissible"] for v in verdicts),
            "note": "admitted = sound by shape + non-destructive; SEMANTIC review still required before promotion",
            "candidate": True, "serves_truth": False}


def _act_scale_profile(args: dict, fixtures: dict) -> dict:
    from scripts.primitive_scale_and_containment import classify, profile_scale  # noqa: PLC0415
    if "lines" in args or "files" in args:   # classify a raw (lines, files) shape
        tier = classify(int(args.get("lines") or 0), int(args.get("files") or 1))
        return {"tier": tier["tier"], "representation": tier["representation"],
                "prompt_inline_viable": tier["prompt_inline_viable"], "delivery_rungs": tier["delivery_rungs"],
                "typical_media": tier["typical_media"], "note": tier["note"],
                "candidate": True, "serves_truth": False}
    ident = str(args.get("primitive") or args.get("primitive_id") or "")
    card = next((c for c in _composition_corpus(fixtures)
                 if ident in (c.get("card_id"), c.get("primitive_id"), c.get("output_edge"), c.get("title"))),
                None)
    if card is None:
        raise ValueError(f"pass lines/files, or a primitive that matches {ident!r}")
    return {"profile": profile_scale(card), "candidate": True, "serves_truth": False}


#: THE ALLOWLIST — the tool can do exactly this, nothing else. One row per action (adding = one row).
def _telemetry(kind: str, fixtures: dict, *, capability_id: str = "", query: str = "") -> None:
    """Best-effort serve-time telemetry — never let a telemetry error break the response."""
    try:
        from scripts.capability_ops import record  # noqa: PLC0415
        record(kind, capability_id=capability_id, query=query, client=str(fixtures.get("account_id") or ""))
    except Exception:  # noqa: BLE001
        pass


def _act_capability_search(args: dict, fixtures: dict) -> dict:
    from scripts.capability_lane import search  # noqa: PLC0415
    query = str(args.get("query") or "").strip()
    if not query:
        raise ValueError("capability.search requires a non-empty `query`")
    res = search(query, limit=_view_limit(args, 5))
    for h in res.get("results", [])[:3]:
        _telemetry("search", fixtures, capability_id=str(h.get("id") or ""), query=query)
    return res


def _act_capability_get(args: dict, fixtures: dict) -> dict:
    from scripts.capability_lane import get  # noqa: PLC0415
    cid = str(args.get("capability_id") or args.get("id") or "").strip()
    if not cid:
        raise ValueError("capability.get requires a non-empty `capability_id`")
    _telemetry("get", fixtures, capability_id=cid)
    return get(cid)


def _act_capability_remix(args: dict, fixtures: dict) -> dict:
    from scripts.capability_lane import remix  # noqa: PLC0415
    it = str(args.get("input_type") or args.get("from") or "").strip()
    ot = str(args.get("output_type") or args.get("to") or "").strip()
    if not it or not ot:
        raise ValueError("capability.remix requires `input_type` and `output_type`")
    res = remix(it, ot, all_paths=bool(args.get("all_paths")))
    _telemetry("remix", fixtures, query=f"{it}->{ot}")
    return res


def _act_capability_stats(args: dict, fixtures: dict) -> dict:
    from scripts.capability_lane import stats  # noqa: PLC0415
    return stats()


def _act_capability_analytics(args: dict, fixtures: dict) -> dict:
    from scripts.capability_ops import analytics  # noqa: PLC0415
    return analytics()


def _act_capability_reuse(args: dict, fixtures: dict) -> dict:
    """Record a reuse outcome (accepted/dismissed) — the signal the weights learn from."""
    outcome = str(args.get("outcome") or "").strip().lower()
    cid = str(args.get("capability_id") or args.get("id") or "").strip()
    if outcome not in ("accepted", "dismissed") or not cid:
        raise ValueError("capability.reuse requires `capability_id` and outcome in {accepted,dismissed}")
    _telemetry(f"reuse_{outcome}", fixtures, capability_id=cid)
    return {"recorded": True, "capability_id": cid, "outcome": outcome, "candidate": True, "serves_truth": False}


def _act_capability_add(args: dict, fixtures: dict) -> dict:
    """Tenant add of an edge-only capability (gated: not on the trial key). Deterministic enrich + test + store."""
    from scripts.capability_ops import add_capability  # noqa: PLC0415
    name = str(args.get("name") or "").strip()
    if not name:
        raise ValueError("capability.add requires `name`")
    return add_capability(name, registry=str(args.get("registry") or "pypi"),
                          capability_class=args.get("capability_class") or args.get("class"),
                          symbols=args.get("symbols"), recipe=args.get("recipe"),
                          license=str(args.get("license") or "MIT"), write=bool(args.get("write", True)))


ACTIONS: dict[str, dict[str, Any]] = {
    "actions.list": {"handler": _act_actions_list, "side_effects": "none",
                     "description": "List every allowlisted action with its side effects and guards."},
    "retrieval.search": {"handler": _act_retrieval_search, "side_effects": "append:usage+request ledgers (record=true)",
                         "description": "Federated primitive search (same engine as the MCP tool; no adaptive reorder)."},
    "retrieval.get": {"handler": _act_retrieval_get, "side_effects": "append:usage ledger downloaded (record=true)",
                      "description": "Exact primitive lookup with typed edges; optional full payload."},
    "retrieval.compose": {"handler": _act_retrieval_compose, "side_effects": "none",
                          "description": "Compose a capability route from retrieved primitives (signature view)."},
    "corpus.status": {"handler": _act_corpus_status, "side_effects": "none",
                      "description": "Measured search/description/embedding corpus coverage."},
    "usage.record": {"handler": _act_usage_record, "side_effects": "append:usage ledger",
                     "description": "Record searched/downloaded/implemented outcomes (the waterfall's signal)."},
    "usage.report": {"handler": _act_usage_report, "side_effects": "none",
                     "description": "Per-primitive usage rollup (counts + success rate)."},
    "waterfall.levels": {"handler": _act_waterfall_levels, "side_effects": "none",
                         "description": "The vector-richness ladder + promotion thresholds/weights."},
    "waterfall.plan": {"handler": _act_waterfall_plan, "side_effects": "none",
                       "description": "Promotion plan from the real usage ledger (read-only preview)."},
    "waterfall.apply": {"handler": _act_waterfall_apply, "side_effects": "write:level state+history+worklist",
                        "guarded": True,
                        "description": "Persist earned vector-level changes (GUARDED: confirm required)."},
    "provision.plan": {"handler": _act_provision_plan, "side_effects": "none",
                       "description": "Serverless-stack resources + estimated monthly cost at a scale."},
    "provision.preflight": {"handler": _act_provision_preflight, "side_effects": "none",
                            "description": "Which provider credentials are present (names+presence only)."},
    "provision.status": {"handler": _act_provision_status, "side_effects": "none",
                         "description": "What has been provisioned so far."},
    "provision.apply": {"handler": _act_provision_apply, "side_effects": "write:cloud provisioning state",
                        "guarded": True,
                        "description": "Provision the stack (GUARDED: OH_BILLING_ENABLED=1 + confirm)."},
    "environment.profile": {"handler": _act_environment_profile, "side_effects": "write:profile cache",
                            "description": "Fingerprint a workspace's technologies (any language/stack)."},
    "learning.status": {"handler": _act_learning_status, "side_effects": "none",
                        "description": "What the learning layer knows (events, profiles, top boosts)."},
    "composition.groups": {"handler": _act_composition_groups, "side_effects": "none",
                           "description": "Computed typed primitive GROUPS (by family/pack/edge); one builder "
                                          "row each."},
    "composition.frameworks": {"handler": _act_composition_frameworks, "side_effects": "none",
                               "description": "Primitive FRAMEWORKS (ordered stage scaffolds); pass framework="
                                              "+scope_family to instantiate with honest coverage gaps."},
    "composition.remix": {"handler": _act_composition_remix, "side_effects": "none",
                          "description": "Deterministic primitive REMIXES (edge-align/jurisdiction/cadence); "
                                         "each variant carries lineage; the llm seam is declared, never run."},
    "composition.integrate": {"handler": _act_composition_integrate, "side_effects": "none",
                              "description": "DETERMINISTIC INTEGRATOR: compile a composite via an exact edge "
                                             "route (start->goal); honest refusal receipt when no route exists."},
    "capability.search": {"handler": _act_capability_search, "side_effects": "none",
                          "description": "Search edge-only, API-verified package capabilities; each hit carries "
                                         "its usage recipe (invoke in ~tens of tokens, don't read the package)."},
    "capability.get": {"handler": _act_capability_get, "side_effects": "none",
                       "description": "Full verified capability card + usage recipe + canonical typed edges."},
    "capability.remix": {"handler": _act_capability_remix, "side_effects": "none",
                         "description": "DETERMINISTIC 0-token composition: exact-typed-join chain from "
                                        "input_type->output_type + correct-by-construction wiring; refuses when "
                                        "no exact path exists (never hallucinated)."},
    "capability.stats": {"handler": _act_capability_stats, "side_effects": "none",
                         "description": "Serving-corpus size + composable type bridges."},
    "capability.analytics": {"handler": _act_capability_analytics, "side_effects": "none",
                             "description": "Usage analytics rollup: volume by kind, top capabilities, reuse "
                                            "rate, composition frequency (from digest-privacy telemetry)."},
    "capability.reuse": {"handler": _act_capability_reuse, "side_effects": "append:capability telemetry",
                         "description": "Record a reuse outcome (accepted/dismissed) — the signal the "
                                        "adjustable weights learn from."},
    "capability.add": {"handler": _act_capability_add, "side_effects": "append:added capabilities store",
                       "description": "Add an edge-only capability (deterministic enrich + test + store); "
                                      "candidate-only, tenant-gated (not on the trial key)."},
    "network.list": {"handler": _act_network_list, "side_effects": "none",
                     "description": "Primitive NETWORKS: a task as an edge-type chain whose steps are slots of "
                                    "competing primitives, with computed grid sizes."},
    "network.grid_search": {"handler": _act_network_grid_search, "side_effects": "none",
                            "description": "GRID SEARCH a network (by name or ad-hoc edge_chain=[...]) under "
                                           "the scorer zoo; returns non-destructive rankings + the Pareto front."},
    "deployment.estimate": {"handler": _act_deployment_estimate, "side_effects": "none",
                            "description": "Given a primitive + a use case (records_per_day, freshness, "
                                           "latency_sla_ms, peak_concurrency), compute deps, substrate, the "
                                           "medium (K8s vs cloud function vs …), sized vCPU/memory, + a cost band."},
    "deployment.profile_network": {"handler": _act_deployment_profile_network, "side_effects": "none",
                                   "description": "Deployment profile for a whole network: per-step resources, "
                                                  "the critical-path envelope, one pipeline medium, union deps."},
    "scale.profile": {"handler": _act_scale_profile, "side_effects": "none",
                      "description": "Granularity of a primitive (atom→application) from a primitive or a "
                                     "(lines, files) shape: representation (inline vs source-tree reference), "
                                     "viable delivery rungs, and whether prompt-inline is even possible."},
    "alignment.screen": {"handler": _act_alignment_screen, "side_effects": "none",
                         "description": "Screen proposed canonical-edge alignments through the deterministic "
                                        "soundness gate (role/ambiguity/cycle) + corpus enable-evidence; "
                                        "admitted = candidate_for_review, never auto-truth."},
    "robust.coverage": {"handler": _act_robust_lane_coverage, "side_effects": "none",
                        "description": "The robust-lane scoreboard: classify a need (or the whole corpus) into "
                                       "deterministic_compose/package_import (robust, 0-token) vs partial/"
                                       "generate_tail, and report the honest robust fraction."},
}


# ================================================================================================================
# Envelope: key gate -> allowlist -> handler -> receipt
# ================================================================================================================
def handle_request(request: dict, *, fixtures: Optional[dict] = None) -> dict:
    fixtures = fixtures or {}
    started = time.monotonic()
    action = str(request.get("action") or "")
    args = request.get("args") if isinstance(request.get("args"), dict) else {}
    sanitized_args = {k: v for k, v in args.items() if k != "key"}

    configured_key = _configured_key()
    if configured_key is None:
        auth_mode = "local-open"
        authorized = True
    else:
        auth_mode = "key"
        authorized = hmac.compare_digest(str(request.get("key") or ""), configured_key)

    ok, result, error = False, None, None
    if not authorized:
        error = "unauthorized: a matching `key` is required (OH_AGENT_TOOL_KEY is configured)"
    elif action not in ACTIONS:
        error = f"unknown action {action!r}: the allowlist is exactly the actions.list set"
    else:
        try:
            result = ACTIONS[action]["handler"](args, fixtures)
            ok = True
        except Exception as exc:  # noqa: BLE001  every failure is still receipt-backed
            error = str(exc)[:400]

    receipt = {
        "ts": _now_iso(),
        "action": action,
        "ok": ok,
        "auth_mode": auth_mode,
        "args_digest": _digest16(json.dumps(sanitized_args, sort_keys=True)),
        "args_preview": json.dumps(sanitized_args, sort_keys=True)[:_ARGS_PREVIEW_CHARS],
        "result_digest": _digest16(json.dumps(result, sort_keys=True, default=str)) if ok else "",
        "error": error or "",
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
        "candidate": True,
        "serves_truth": False,
    }
    path = receipts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")

    return {"ok": ok, "action": action, "result": result, "error": error, "auth_mode": auth_mode,
            "receipt_path": str(path), "candidate": True, "serves_truth": False}


# ================================================================================================================
def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool, str]] = []
    saved_environment = {name: os.environ.get(name) for name in
                         (AGENT_TOOL_KEY_ENVIRONMENT_VARIABLE, AGENT_TOOL_KEY_FILE_ENVIRONMENT_VARIABLE,
                          AGENT_TOOL_DATA_DIR_ENVIRONMENT_VARIABLE, "OH_BILLING_ENABLED",
                          "OH_LEARNING_DATA_DIR")}
    try:
        with tempfile.TemporaryDirectory() as sandbox:
            os.environ[AGENT_TOOL_DATA_DIR_ENVIRONMENT_VARIABLE] = str(Path(sandbox) / "tool")
            os.environ["OH_LEARNING_DATA_DIR"] = str(Path(sandbox) / "learning")
            os.environ.pop(AGENT_TOOL_KEY_ENVIRONMENT_VARIABLE, None)
            os.environ.pop(AGENT_TOOL_KEY_FILE_ENVIRONMENT_VARIABLE, None)
            os.environ.pop("OH_BILLING_ENABLED", None)
            usage_ledger = Path(sandbox) / "usage.jsonl"
            fixtures = {"usage_ledger_path": usage_ledger,
                        "waterfall_state_path": Path(sandbox) / "state.json",
                        "waterfall_history_path": Path(sandbox) / "history.jsonl",
                        "waterfall_worklist_path": Path(sandbox) / "worklist.jsonl"}

            # (1) the allowlist is discoverable and every row is documented.
            listed = handle_request({"action": "actions.list"})
            checks.append((f"actions.list returns the {len(ACTIONS)}-action allowlist, all documented",
                           listed["ok"] and len(listed["result"]["actions"]) == len(ACTIONS)
                           and all(a["description"] for a in listed["result"]["actions"]), ""))

            # (2) unknown action -> structured refusal (allowlist enforced), still receipt-backed.
            unknown = handle_request({"action": "shell.exec", "args": {"cmd": "rm -rf /"}})
            checks.append(("unknown action refused with a structured error",
                           unknown["ok"] is False and "allowlist" in (unknown["error"] or ""), ""))

            # (3) offline search via the synthetic index fixture; recording lands in the sandbox ledgers.
            from scripts.capability_retrieval_mcp_server import _synthetic_search_index
            search = handle_request({"action": "retrieval.search", "args": {"query": "ofac sanctions screening"}},
                                    fixtures={"index": _synthetic_search_index(), "usage_ledger_path": usage_ledger})
            checks.append(("retrieval.search (offline fixture) returns the target hit + records the signal",
                           search["ok"] and search["result"]["results"][0]["primitive_id"] == "prim:test:target"
                           and usage_ledger.exists(), json.dumps(search.get("error"))))

            # (4) usage.record -> usage.report roundtrip on the sandbox ledger (implemented success counted).
            handle_request({"action": "usage.record",
                            "args": {"event_type": "implemented", "primitive_ids": ["prim:test:target"],
                                     "outcome": "success", "ts": "t1"}}, fixtures=fixtures)
            report = handle_request({"action": "usage.report", "args": {"primitive_id": "prim:test:target"}},
                                    fixtures=fixtures)
            checks.append(("usage.record -> usage.report roundtrip counts the implemented success",
                           report["ok"] and report["result"]["implement_success"] == 1, json.dumps(report["result"])))

            # (5) the waterfall is queryable and its apply guard holds through the tool.
            levels = handle_request({"action": "waterfall.levels"})
            plan = handle_request({"action": "waterfall.plan", "args": {"n_corpus": 100}}, fixtures=fixtures)
            refused = handle_request({"action": "waterfall.apply", "args": {"n_corpus": 100}}, fixtures=fixtures)
            applied = handle_request({"action": "waterfall.apply", "args": {"confirm": True, "n_corpus": 100}},
                                     fixtures=fixtures)
            checks.append(("waterfall levels/plan/apply: guard refuses without confirm, applies with it",
                           levels["ok"] and plan["ok"] and refused["ok"]
                           and refused["result"]["applied"] is False and applied["result"]["applied"] is True, ""))

            # (6) provisioning: plan needs no creds; apply stays billing-gated THROUGH the tool.
            provision_plan = handle_request({"action": "provision.plan", "args": {"scale": 1_000_000}})
            provision_apply = handle_request({"action": "provision.apply", "args": {"confirm": True}})
            checks.append(("provision.plan costed with no creds; provision.apply refused without billing",
                           provision_plan["ok"] and provision_plan["result"]["est_monthly_usd_core"] > 0
                           and provision_apply["ok"] and provision_apply["result"]["applied"] is False, ""))

            # (7) environment profile detects a cross-technology workspace.
            workspace = Path(sandbox) / "ws"
            workspace.mkdir()
            (workspace / "package.json").write_text("{}")
            (workspace / "requirements.txt").write_text("requests")
            profile = handle_request({"action": "environment.profile", "args": {"root": str(workspace)}})
            checks.append(("environment.profile detects javascript+python",
                           profile["ok"] and {"javascript", "python"} <= set(profile["result"]["technologies"]), ""))

            # (8) KEY GATE: configured key -> missing/wrong refused, right one passes; raw key never in receipts.
            secret = "agent-tool-test-key-0123456789abcdef"
            os.environ[AGENT_TOOL_KEY_ENVIRONMENT_VARIABLE] = secret
            missing = handle_request({"action": "actions.list"})
            wrong = handle_request({"action": "actions.list", "key": "nope"})
            right = handle_request({"action": "actions.list", "key": secret})
            os.environ.pop(AGENT_TOOL_KEY_ENVIRONMENT_VARIABLE, None)
            receipts_text = receipts_path().read_text()
            checks.append(("key gate: missing/wrong key refused, matching key passes, raw key never in receipts",
                           missing["ok"] is False and wrong["ok"] is False and right["ok"] is True
                           and right["auth_mode"] == "key" and secret not in receipts_text, ""))

            # (9) every request above is receipt-backed (one line each) and candidate-stamped.
            receipt_lines = [json.loads(line) for line in receipts_text.splitlines() if line.strip()]
            checks.append((f"append-only receipts for every request ({len(receipt_lines)} lines)",
                           len(receipt_lines) >= 12
                           and all(r["serves_truth"] is False for r in receipt_lines), ""))

            # (10) determinism: the allowlist view is byte-identical across calls.
            checks.append(("actions.list deterministic",
                           handle_request({"action": "actions.list"})["result"]
                           == handle_request({"action": "actions.list"})["result"], ""))
    finally:
        for name, value in saved_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    ok = all(passed for _name, passed, _detail in checks)
    print(f"{'PASS' if ok else 'FAIL'} - capability_agent_tool: deterministic allowlisted developer/agent tool "
          f"({len(ACTIONS)} actions) over the SAME engines as the MCP tool — key-gatable, receipt-backed, guards "
          f"preserved, no adaptive reorder. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:300]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic developer/agent tool over the capability engines.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--list-actions", action="store_true")
    parser.add_argument("--request-json", help='e.g. \'{"action":"retrieval.search","args":{"query":"..."}}\'')
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.list_actions:
        print(json.dumps(handle_request({"action": "actions.list"}), indent=2, sort_keys=True))
        return 0
    if args.request_json:
        try:
            request = json.loads(args.request_json)
        except json.JSONDecodeError as exc:
            print(json.dumps({"ok": False, "error": f"invalid request JSON: {exc}"}))
            return 1
        envelope = handle_request(request if isinstance(request, dict) else {})
        print(json.dumps(envelope, indent=2, sort_keys=True, default=str))
        return 0 if envelope["ok"] else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
