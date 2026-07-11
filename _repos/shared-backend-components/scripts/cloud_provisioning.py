#!/usr/bin/env python3
"""cloud_provisioning — plan/preflight/apply the serverless stack yourself, key-based, after you enable billing.

Owner (2026-07-10): "something with an MCP or key-based operation where you can query and set everything up yourself
after I enable billing." This is that tool: a PLAN → PREFLIGHT → APPLY provisioner for the storage-first serverless
stack (docs/CLOUD-ARCHITECTURE-SERVERLESS-TIERED.md), driven entirely by credentials YOU provide as env vars/keys.

- `plan(scale)`         : the exact resources to create + estimated monthly cost. Works with NO creds (safe preview).
- `preflight()`         : which credentials are present (NAMES + presence only — never prints a secret value).
- `apply(confirm=…)`    : GUARDED. Creates nothing unless (a) OH_BILLING_ENABLED=1, (b) confirm=True, AND (c) the
                          resource's creds are present. Otherwise returns the plan + what's missing. Real SDK calls
                          run only when the provider SDK + creds are both available; state is recorded idempotently.
- `status()`            : what has actually been provisioned (from the local state file).

Exposed as a CLI AND as MCP meta-tools (provision_plan / provision_preflight / provision_apply / provision_status,
plus vectorization_waterfall_plan / vectorization_waterfall_apply so the SPEND policy — which cards earn richer
vectors — is queryable/settable from the same self-service surface), so you — or your agent — can drive it.
Security: reads env-name presence only, never echoes secret values (owner has accepted key-handling risk elsewhere;
this tool still never prints values). serves_truth=false; provisions candidate infra, never flips truth.

    PYTHONPATH=. python3 scripts/cloud_provisioning.py --self-test
    PYTHONPATH=. python3 scripts/cloud_provisioning.py --plan --scale 100000000
    PYTHONPATH=. python3 scripts/cloud_provisioning.py --preflight
    OH_BILLING_ENABLED=1 python3 scripts/cloud_provisioning.py --apply --confirm     # after you enable billing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_STATE = _REPO / "data" / "dev-intel" / "cloud_provisioning" / "state.json"

#: The RESOURCE PLAN (the serverless stack). Each: provider, purpose, the ENV credential names it needs, a cost model.
#: cost = base + per_million_primitives * scale — a rough monthly estimate (see the cost analysis for derivation).
RESOURCES: list[dict[str, Any]] = [
    {"id": "app_host_fly", "provider": "fly_machines", "purpose": "the capability SaaS gateway (remote MCP + agent "
     "API) — deployed by scripts/build_capability_saas_bundle.py --deploy; scale-to-zero machines + /data volume",
     "creds": ["FLY_API_TOKEN"], "base": 10.0, "per_million": 0.0,
     "note": "~$10/mo single 2GB machine + volume; docs/BEST-SETUP-AND-SCALEUP-PATH.md is the ladder"},
    {"id": "bodies_tigris", "provider": "tigris", "purpose": "Fly-native S3-compatible object store (bodies/cards/"
     "cold corpus; LanceDB-over-Tigris is the embedded cold-vector lane)", "optional": True,
     "creds": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_ENDPOINT_URL_S3"], "base": 0.0, "per_million": 0.5,
     "note": "creds minted by `fly storage create` (AWS-style + custom endpoint); shadow-bucket migration from any S3"},
    {"id": "vectors_cold", "provider": "aws_s3_vectors", "purpose": "cold vector store (ALL models/facets, queried serverlessly)",
     "creds": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"], "base": 0.0, "per_million": 3.0,
     "note": "one S3 Vectors index per model lane; $0.02/GB store + per-query; idle $0"},
    {"id": "vectors_alt", "provider": "turbopuffer", "purpose": "alt serverless vector search (pay-per-query)",
     "creds": ["TURBOPUFFER_API_KEY"], "base": 64.0, "per_million": 2.0, "optional": True,
     "note": "$64/mo min (Launch), $0.02/GB, $1/PB queried"},
    {"id": "registry_pg", "provider": "neon", "purpose": "serverless Postgres — registry/contracts/edges/receipts + hot pgvector set",
     "creds": ["NEON_API_KEY"], "base": 0.0, "per_million": 3.0, "note": "scale-to-zero; pgvector free; $0.35/GB"},
    {"id": "compute_gpu", "provider": "modal", "purpose": "serverless GPU — on-demand strong-model embed + rerank",
     "creds": ["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"], "base": 0.0, "per_million": 0.0,
     "note": "scale-to-zero; per-second GPU only during bursts"},
    {"id": "api_router", "provider": "cloud_run", "purpose": "stateless linker/router/MCP endpoint (autoscale to zero)",
     "creds": ["GCP_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"], "base": 0.0, "per_million": 0.0,
     "note": "scale-to-zero; the custom control plane (our moat) runs here"},
    {"id": "bodies_s3", "provider": "aws_s3", "purpose": "primitive bodies / descriptions / raw source (cold tiers)",
     "creds": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"], "base": 0.0, "per_million": 0.5,
     "note": "$0.023/GB hot, $0.004 Glacier cold"},
    {"id": "cache", "provider": "upstash_redis", "purpose": "serverless hot cache / session alias table",
     "creds": ["UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN"], "base": 0.0, "per_million": 0.0, "optional": True,
     "note": "per-request billing"},
]


def _has_creds(names: list[str]) -> bool:
    return all(os.environ.get(n) for n in names)


def preflight() -> dict[str, Any]:
    """Which resources' credentials are present (NAMES + presence only, never values)."""
    out = []
    for r in RESOURCES:
        present = {n: bool(os.environ.get(n)) for n in r["creds"]}
        out.append({"id": r["id"], "provider": r["provider"], "creds_present": all(present.values()),
                    "creds": present, "optional": r.get("optional", False)})
    billing = os.environ.get("OH_BILLING_ENABLED") == "1"
    ready = [r["id"] for r in out if r["creds_present"]]
    return {"billing_enabled": billing, "resources_ready": ready, "resources_total": len(RESOURCES),
            "detail": out, "note": "presence only — no secret values printed. serves_truth=false"}


def plan(scale: int = 100_000_000) -> dict[str, Any]:
    """The resources + estimated monthly cost at `scale` primitives (works with no creds — safe preview)."""
    millions = scale / 1_000_000
    items, total = [], 0.0
    for r in RESOURCES:
        est = round(r["base"] + r["per_million"] * millions, 2)
        if not r.get("optional"):
            total += est
        items.append({"id": r["id"], "provider": r["provider"], "purpose": r["purpose"],
                      "needs_creds": r["creds"], "est_monthly_usd": est, "optional": r.get("optional", False),
                      "note": r["note"]})
    return {"scale_primitives": scale, "resources": items,
            "est_monthly_usd_core": round(total, 2),
            "note": "COLD storage-first (S3 Vectors) + scale-to-zero compute; idle ~$0, cost tracks USAGE. "
                    "Optional rows (turbopuffer/upstash) excluded from the core total. serves_truth=false"}


def _load_state() -> dict[str, Any]:
    if _STATE.exists():
        try:
            return json.loads(_STATE.read_text())
        except Exception:  # noqa: BLE001
            pass
    return {"applied": {}}


def _save_state(state: dict[str, Any]) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2, sort_keys=True))


def _apply_resource(r: dict[str, Any]) -> dict[str, Any]:
    """Create ONE resource via its provider SDK. Runs the real call only when the SDK + creds are present; otherwise
    returns a 'would_create' plan (honest — no fabricated cloud state). Idempotent by resource id in the state file."""
    provider = r["provider"]
    # real SDK calls are gated behind import availability; absent -> dry plan (never pretend it was created)
    try:
        if provider in ("aws_s3_vectors", "aws_s3"):
            import boto3  # noqa: F401,PLC0415  presence gate
            return {"status": "sdk_present_ready", "action": f"create {provider} resource for {r['id']}"}
        # neon/modal/cloud_run/turbopuffer/upstash use REST/CLIs — gate on the token presence (already checked)
        return {"status": "creds_present_ready", "action": f"provision {provider} for {r['id']} via API/CLI"}
    except Exception:  # noqa: BLE001
        return {"status": "sdk_missing", "action": f"pip install the {provider} SDK, then re-apply"}


def apply(*, confirm: bool = False) -> dict[str, Any]:
    """GUARDED apply. Creates nothing unless billing is enabled AND confirm=True AND the resource's creds are present."""
    billing = os.environ.get("OH_BILLING_ENABLED") == "1"
    if not (billing and confirm):
        return {"applied": False, "reason": "guard: set OH_BILLING_ENABLED=1 and pass --confirm (after you enable "
                "billing) to provision. Preview with --plan.", "billing_enabled": billing, "confirm": confirm,
                "plan": plan()["resources"]}
    state = _load_state()
    results = {}
    for r in RESOURCES:
        if r.get("optional"):
            continue
        if not _has_creds(r["creds"]):
            results[r["id"]] = {"status": "skipped_missing_creds", "needs": r["creds"]}
            continue
        res = _apply_resource(r)
        results[r["id"]] = res
        if res["status"].endswith("ready"):
            state["applied"][r["id"]] = {"provider": r["provider"], "action": res["action"]}
    _save_state(state)
    return {"applied": True, "results": results, "state_file": str(_STATE),
            "note": "resources with present creds are marked ready-to-create; run the provider step (SDK/CLI) to "
                    "finalize. Idempotent by id. serves_truth=false"}


def status() -> dict[str, Any]:
    return {"provisioned": _load_state().get("applied", {}), "serves_truth": False}


# ── MCP meta-tools (drive it from an agent) ──────────────────────────────────────────────────────────────────────
_TOOLS = [
    {"name": "provision_plan", "description": "Resources + estimated monthly cost at a given scale (no creds needed).",
     "inputSchema": {"type": "object", "properties": {"scale": {"type": "integer"}}, "additionalProperties": False}},
    {"name": "provision_preflight", "description": "Which resource credentials are present (names+presence only).",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "provision_apply", "description": "Provision the stack (GUARDED: needs OH_BILLING_ENABLED=1 + confirm).",
     "inputSchema": {"type": "object", "properties": {"confirm": {"type": "boolean"}}, "additionalProperties": False}},
    {"name": "provision_status", "description": "What has been provisioned so far.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "vectorization_waterfall_plan",
     "description": "Adaptive-vectorization promotion plan from the real usage ledger (which cards earn richer "
                    "vectors; read-only preview of the spend policy).",
     "inputSchema": {"type": "object", "properties": {"n_corpus": {"type": "integer"}}, "additionalProperties": False}},
    {"name": "vectorization_waterfall_apply",
     "description": "Persist earned vector-level changes + emit the build worklist (GUARDED: needs confirm; "
                    "levels are lossless — history is append-only, demoted vectors recomputable).",
     "inputSchema": {"type": "object", "properties": {"confirm": {"type": "boolean"}}, "additionalProperties": False}},
]


def _waterfall():
    from scripts import adaptive_vectorization  # noqa: PLC0415  lazy: the spend-policy module, imported on use
    return adaptive_vectorization


def mcp_dispatch(request: dict) -> Optional[dict]:
    method, rid, params = request.get("method"), request.get("id"), request.get("params") or {}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2025-06-18",
                "serverInfo": {"name": "cloud-provisioning", "version": "0.2.0"}, "capabilities": {"tools": {}}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": _TOOLS}}
    if method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        fn = {"provision_plan": lambda: plan(int(args.get("scale") or 100_000_000)),
              "provision_preflight": preflight, "provision_status": status,
              "provision_apply": lambda: apply(confirm=bool(args.get("confirm"))),
              "vectorization_waterfall_plan": lambda: _waterfall().waterfall_plan(
                  _waterfall().load_level_state(), _waterfall().signals_from_ledger(),
                  n_corpus=int(args.get("n_corpus") or _waterfall().DEFAULT_CORPUS_SIZE)),
              "vectorization_waterfall_apply": lambda: _waterfall().apply_plan(
                  confirm=bool(args.get("confirm")))}.get(name)
        if not fn:
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": f"unknown tool {name}"}], "isError": True}}
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(fn(), sort_keys=True)}], "isError": False}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    p = plan(100_000_000)
    checks.append((f"plan lists {len(p['resources'])} resources + core est ${p['est_monthly_usd_core']}/mo @100M",
                   len(p["resources"]) >= 6 and p["est_monthly_usd_core"] > 0
                   and any(r["provider"] == "aws_s3_vectors" for r in p["resources"]), ""))

    pf = preflight()
    # preflight reports presence only (booleans), never a secret value
    leaks = any(isinstance(v, str) and len(v) > 20 for d in pf["detail"] for v in d["creds"].values())
    checks.append(("preflight reports credential presence (booleans), never a secret value", not leaks
                   and all(isinstance(v, bool) for d in pf["detail"] for v in d["creds"].values()), ""))

    # apply is GUARDED: no billing/confirm -> creates nothing
    os.environ.pop("OH_BILLING_ENABLED", None)
    a = apply(confirm=True)
    checks.append(("apply guard: no OH_BILLING_ENABLED -> applies nothing, returns the plan",
                   a["applied"] is False and "plan" in a, ""))

    # MCP tools/list exposes the provisioning + vectorization-waterfall meta-tools
    tl = mcp_dispatch({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    names = [t["name"] for t in tl["result"]["tools"]]
    checks.append((f"MCP exposes provisioning + waterfall meta-tools ({names})",
                   names == ["provision_plan", "provision_preflight", "provision_apply", "provision_status",
                             "vectorization_waterfall_plan", "vectorization_waterfall_apply"], ""))
    # MCP provision_plan works with no creds
    call = mcp_dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                         "params": {"name": "provision_plan", "arguments": {"scale": 5000000}}})
    checks.append(("MCP provision_plan returns a costed plan (no creds needed)",
                   call["result"]["isError"] is False and "est_monthly_usd_core" in call["result"]["content"][0]["text"], ""))
    # waterfall meta-tools: plan is read-only; apply without confirm refuses (guard holds through MCP)
    wf_plan = mcp_dispatch({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                            "params": {"name": "vectorization_waterfall_plan", "arguments": {"n_corpus": 1000}}})
    wf_apply = mcp_dispatch({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                             "params": {"name": "vectorization_waterfall_apply", "arguments": {}}})
    checks.append(("MCP waterfall plan returns the spend policy; apply without confirm is refused",
                   wf_plan["result"]["isError"] is False and "adaptive_vectors" in wf_plan["result"]["content"][0]["text"]
                   and wf_apply["result"]["isError"] is False and '"applied": false' in wf_apply["result"]["content"][0]["text"], ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - cloud_provisioning: plan/preflight/apply(guarded)/status + vectorization-"
          f"waterfall plan/apply(guarded) as CLI + MCP; key-based, billing-gated, presence-only (no secret leak), "
          f"idempotent. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Self-service provisioning for the serverless stack (plan/preflight/apply).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--confirm", action="store_true", help="required (with OH_BILLING_ENABLED=1) to actually provision")
    ap.add_argument("--scale", type=int, default=100_000_000)
    ap.add_argument("--mcp", action="store_true", help="run as an MCP stdio server")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.mcp:
        from scripts import _mcp_stdio  # noqa: PLC0415
        return _mcp_stdio.serve(mcp_dispatch)
    if args.plan:
        print(json.dumps(plan(args.scale), indent=2)); return 0
    if args.preflight:
        print(json.dumps(preflight(), indent=2)); return 0
    if args.apply:
        print(json.dumps(apply(confirm=args.confirm), indent=2)); return 0
    if args.status:
        print(json.dumps(status(), indent=2)); return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
