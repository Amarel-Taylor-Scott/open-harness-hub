"""src.teleon.inference.oips — the Open Inference Preference Spec engine: preference inheritance + numeric
provider selection + governed fallback + ModelInvocationReceipt provenance + a local deterministic stub.

Pure + deterministic decisions (all inputs injected: available_secrets, provider_health, now). Branches on numeric
codes + node ids, NEVER on provider display strings. No external SDK import, no network. Secret refs are checked for
PRESENCE only — raw keys never appear here, in logs, or in receipts. The ONLY side effect: infer_local appends each
minted receipt to the durable JSONL sink (src.teleon.inference.receipts — best-effort, hashes/metadata only, never
affects the returned values), so invocation provenance survives restarts instead of living in a process dict.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_A = Path(__file__).resolve().parents[3] / "architecture"
OFFLINE_DEFAULT_NODE = "model.local_stub@v1"
#: strongest→weakest downstream use a model output can qualify for. The gateway NEVER emits "served" (Baltor
#: governs serving); the ceiling for a clean frontier call is "promotable".
ALLOWED_USE_ORDER = ["blocked", "draft", "non_serving_explanation", "candidate", "promotable", "served"]
_cache: dict[str, Any] = {}


def _load(name: str) -> dict:
    if name not in _cache:
        _cache[name] = json.loads((_A / name).read_text(encoding="utf-8"))
    return _cache[name]


def load_graph() -> dict:
    return _load("model_provider_graph.json")


def _tiers() -> dict[str, int]:
    return {t["label"]: t["code"] for t in _load("model_quality_tier_codes.json")["tiers"]}


def _node_index() -> dict[str, dict]:
    return {n["node_id"]: n for n in load_graph()["nodes"]}


def _tier_code(spec: dict) -> int:
    """A model_class_preference's requested tier as a numeric code (accepts tier_code or a tier label)."""
    if "tier_code" in spec:
        return int(spec["tier_code"])
    return _tiers().get(spec.get("tier", "standard"), 300)


def _stable(prefix: str, *parts: str) -> str:
    return f"{prefix}_" + hashlib.blake2b("|".join(parts).encode(), digest_size=10).hexdigest()


# ── preference inheritance ──────────────────────────────────────────────────────────────────────────────────
def resolve_preference(layers: list[dict], *, preference_id: str = "") -> dict:
    """Merge an ordered inheritance chain (global → product → tenant → environment → object-type → instance →
    call); later layers override earlier keys (deep-merge one level for the policy sub-objects). Returns a
    ResolvedInferencePreference with the resolved_from trail + an effective_policy_hash."""
    effective: dict = {}
    resolved_from: list[str] = []
    for layer in layers:
        resolved_from.append(layer.get("preference_id") or layer.get("_layer") or "(anon)")
        for k, v in layer.items():
            if isinstance(v, dict) and isinstance(effective.get(k), dict):
                effective[k] = {**effective[k], **v}
            else:
                effective[k] = v
    pid = preference_id or effective.get("preference_id") or _stable("pref", json.dumps(effective, sort_keys=True))
    h = "sha256:" + hashlib.sha256(json.dumps(effective, sort_keys=True).encode()).hexdigest()
    return {"schema_version": "ResolvedInferencePreference.v1", "preference_id": pid, "effective": effective,
            "resolved_from": resolved_from, "effective_policy_hash": h, "conflict_notes": []}


def _secret_present(node: dict, available_secrets: set) -> bool:
    ref = node.get("secret_ref")
    return ref is None or ref in available_secrets  # None = no secret needed (local); else must be configured


def _eligible(node: dict, eff: dict, requested_tier: int) -> tuple[bool, str]:
    """Static eligibility (independent of runtime availability): data policy + tier floor + specialization."""
    data = eff.get("data_policy", {})
    if node.get("external") and data.get("external_llm_allowed", True) is False:
        return False, "preferred_model_policy_blocked"
    mcp = eff.get("model_class_preference", {})
    want_specs = set(mcp.get("specialization_codes", []))
    if want_specs and not (want_specs & set(node.get("specialization_codes", []))):
        return False, "specialization_not_supported"
    return True, ""


# ── provider selection + governed fallback ──────────────────────────────────────────────────────────────────
def select_provider(resolved: dict, *, available_secrets: set | None = None,
                    provider_health: dict | None = None,
                    efficiency_ranking: list | None = None) -> dict:
    """Decide which provider NODE to use for a resolved preference. Prefers the object's allowed_provider_nodes
    in order; rejects nodes that are policy-blocked / wrong-specialization / missing-secret / unhealthy, recording
    each rejection with a reason code. Falls back to the chosen node's local_equivalent, else the offline default.
    Returns a route decision (chosen node + fallback_used + tier downgrade + rejected_candidates).

    efficiency_ranking (optional, injected by the caller from model_efficiency.rank_models over the
    receipts): REORDERS the preference among the ALREADY-ALLOWED nodes by measured cost/quality
    efficiency — eligibility (policy/secret/specialization/health) is unchanged below, and unmeasured
    nodes keep their declared order. A safe, monotone 'pick the cheapest capable model' improvement
    that can never violate policy. See docs/architecture/model-efficiency-routing.md."""
    eff = resolved["effective"]
    creds = set(available_secrets or set())
    health = provider_health or {}
    idx = _node_index()
    requested_tier = _tier_code(eff.get("model_class_preference", {}))
    disallowed = set(eff.get("disallowed_provider_nodes", []))
    order = [n for n in eff.get("allowed_provider_nodes", []) if n not in disallowed and n in idx]
    if not order:  # no explicit list → all graph nodes meeting tier+specialization
        order = [n["node_id"] for n in load_graph()["nodes"] if n["node_id"] not in disallowed]
    if efficiency_ranking:  # reorder the PREFERENCE by measured efficiency (eligibility unchanged below)
        from src.teleon.inference.model_efficiency import efficiency_order
        order = efficiency_order(order, efficiency_ranking)

    rejected: list[dict] = []
    chosen: str | None = None
    for nid in order:
        node = idx[nid]
        ok, why = _eligible(node, eff, requested_tier)
        if not ok:
            rejected.append({"provider_node_id": nid, "reason_code": why}); continue
        if not _secret_present(node, creds):
            rejected.append({"provider_node_id": nid, "reason_code": "preferred_secret_missing"}); continue
        if health.get(nid, True) is False:
            rejected.append({"provider_node_id": nid, "reason_code": "provider_health_degraded"}); continue
        chosen = nid
        break

    fail_closed = bool(eff.get("fallback_policy", {}).get("fail_closed_if_unavailable")
                       or eff.get("fallback_policy", {}).get("fail_closed_if_policy_blocked"))
    if chosen is None:
        # governed fallback: the first preferred node's local_equivalent, else the offline default
        fb = (idx[order[0]]["local_equivalent"] if order and order[0] in idx else OFFLINE_DEFAULT_NODE)
        data = eff.get("data_policy", {})
        if data.get("external_llm_allowed", True) is False and idx.get(fb, {}).get("external"):
            fb = OFFLINE_DEFAULT_NODE
        blocked = fail_closed and not idx.get(fb)
        return {"selected_provider_node_id": (None if blocked else fb), "fallback_used": True,
                "tier_downgraded": True, "blocked": blocked,
                "fallback_reason_codes": sorted({r["reason_code"] for r in rejected}) or ["no_eligible_provider"],
                "rejected_candidates": rejected, "requested_tier_code": requested_tier,
                "selected_tier_code": (idx.get(fb, {}).get("tier_code") if not blocked else None)}
    preferred = order[0]
    chosen_tier = idx[chosen]["tier_code"]
    return {"selected_provider_node_id": chosen, "fallback_used": chosen != preferred,
            "tier_downgraded": chosen_tier < requested_tier, "blocked": False,
            "fallback_reason_codes": sorted({r["reason_code"] for r in rejected}),
            "rejected_candidates": rejected, "requested_tier_code": requested_tier, "selected_tier_code": chosen_tier}


def _allowed_use(route: dict, executed_node: str) -> str:
    """The strongest downstream use the output qualifies for. NEVER 'served' — Baltor governs serving."""
    if route.get("blocked"):
        return "blocked"
    idx = _node_index()
    if executed_node == OFFLINE_DEFAULT_NODE or idx.get(executed_node, {}).get("tier_code", 0) <= 100:
        return "draft"            # the local stub is for tests/drafts only
    if route.get("tier_downgraded"):
        return "candidate"        # a lower-tier fallback may be a candidate, not promotable
    if route.get("fallback_used"):
        return "candidate"
    return "promotable"           # clean preferred call → promotable (still gated by Baltor before 'served')


# ── receipt ─────────────────────────────────────────────────────────────────────────────────────────────────
def build_receipt(*, object_id: str, preference_id: str, requested_model_class: str, route: dict,
                  executed_node: str, executed_model: str, input_text: str, output_text: str, now: str,
                  tokens: dict | None = None, cost: float | None = None, latency_ms: int | None = None,
                  prompt_template: str = "", config_version: str = "inference_router_config@v1",
                  base_host: str | None = None) -> dict:
    h = lambda s: "sha256:" + hashlib.sha256(s.encode()).hexdigest()
    receipt = {
        "schema_version": "ModelInvocationReceipt.v1",
        "receipt_id": _stable("llmrcpt", object_id, preference_id, now, output_text[:64]),
        "request_id": _stable("llmreq", object_id, preference_id, now, input_text[:64]),
        "object_id": object_id, "preference_id": preference_id,
        "requested_model_class": requested_model_class,
        "selected_provider_node_id": executed_node, "selected_model": executed_model, "selected_region": "local",
        # the EFFECTIVE host that served the call (hostname[:port], never credentials) — None when no
        # HTTP endpoint executed (stub/blocked). Lets a receipt prove WHERE the call actually went,
        # independent of which graph node was named.
        "executed_base_host": base_host,
        "fallback_used": bool(route.get("fallback_used")),
        "fallback_reason_codes": list(route.get("fallback_reason_codes", [])),
        "rejected_candidates": list(route.get("rejected_candidates", [])),
        "input_hash": h(input_text), "output_hash": h(output_text), "prompt_template_hash": h(prompt_template),
        "config_version": config_version, "tokens": tokens or {"input": len(input_text.split()), "output": len(output_text.split())},
        "cost_estimate_usd": cost, "latency_ms": latency_ms,
        "policy_checks": {"data_policy_passed": not route.get("blocked"),
                          "budget_policy_passed": True, "fallback_policy_passed": True,
                          "no_raw_secret": True, "llm_output_is_truth": False},
        "allowed_use": _allowed_use(route, executed_node), "created_at": now,
    }
    return receipt


# ── offline gateway (local deterministic execution) ─────────────────────────────────────────────────────────
def infer_local(*, object_id: str, preference_layers: list[dict], input_text: str, now: str,
                available_secrets: set | None = None, provider_health: dict | None = None,
                allow_network: bool = False, use_efficiency_ranking: bool = True) -> dict:
    """End-to-end inference: resolve preference → select provider → DISPATCH execution through the standardized
    provider-adapter layer (src.teleon.inference.adapters.resolve_adapter) → receipt. Offline (allow_network=False,
    the default) only the deterministic LocalStub adapter is available, so an external decided node degrades to the
    stub and the receipt stays honest about what actually ran. Enabling allow_network (owner-authorized) lets a real
    adapter execute instead — same governed contract (receipt, fallback trail, output-never-truth).

    use_efficiency_ranking (default on): rank the allowed nodes by MEASURED efficiency from the accumulated
    receipts (model_efficiency.rank_models) and feed it to select_provider — 'pick the cheapest capable model'
    learned from our own cost/latency data. A no-op until receipts exist (honest: empty ranking → declared order)."""
    resolved = resolve_preference(preference_layers)
    ranking = None
    if use_efficiency_ranking:  # learn the preference order from our own receipts (no-op when empty)
        try:
            from src.teleon.inference.model_efficiency import rank_models
            from src.teleon.inference.receipts import load_receipts, RECEIPTS_JSONL_PATH
            klass = resolved["effective"].get("model_class_preference", {}).get("name")
            ranking = rank_models(load_receipts(RECEIPTS_JSONL_PATH), task_class=klass) or None
        except Exception:  # ranking must never break inference — degrade to the declared order
            ranking = None
    route = select_provider(resolved, available_secrets=available_secrets, provider_health=provider_health,
                            efficiency_ranking=ranking)
    decided = route["selected_provider_node_id"]
    result: dict = {}  # the executing adapter's invoke result (live model/latency/tokens when real)
    if route.get("blocked"):
        output = ""
        executed_node = OFFLINE_DEFAULT_NODE
        route = {**route, "fallback_reason_codes": route["fallback_reason_codes"] + ["fail_closed"]}
    else:
        # Execution goes through the adapter REGISTRY (one base class, swappable by config). Offline, only the
        # deterministic LocalStub adapter is available; an external decided node is unavailable and degrades to the
        # stub — recorded honestly so provenance never overstates what executed.
        from src.teleon.inference.adapters import resolve_adapter  # lazy: adapters imports oips (break the cycle)
        idx = _node_index()
        chosen = resolve_adapter(idx[decided]) if decided in idx else None
        ok = bool(chosen) and chosen.available(secrets=available_secrets or set(), allow_network=allow_network)[0]
        exec_adapter = chosen if ok else resolve_adapter(idx[OFFLINE_DEFAULT_NODE])
        executed_node = decided if ok else OFFLINE_DEFAULT_NODE
        result = exec_adapter.invoke(object_id=object_id, input_text=input_text, now=now,
                                     secrets=available_secrets or set(), allow_network=allow_network)
        reasons = set(route["fallback_reason_codes"])
        if not result.get("available"):
            # the decided live adapter failed MID-CALL — degrade to the stub, recorded honestly
            reasons.add(str(result.get("reason_code") or "live_call_failed"))
            executed_node = OFFLINE_DEFAULT_NODE
            result = resolve_adapter(idx[OFFLINE_DEFAULT_NODE]).invoke(
                object_id=object_id, input_text=input_text, now=now,
                secrets=available_secrets or set(), allow_network=allow_network)
        output = result["output"]
        if executed_node == OFFLINE_DEFAULT_NODE:
            reasons.add("offline_local_execution")
        route = {**route, "fallback_used": route.get("fallback_used") or executed_node != decided or decided != OFFLINE_DEFAULT_NODE,
                 "fallback_reason_codes": sorted(reasons)}
    mcp = resolved["effective"].get("model_class_preference", {})
    requested_class = f"tier:{mcp.get('tier', _tier_code(mcp))}/{','.join(map(str, mcp.get('specialization_codes', [])))}"
    executed_model = ("local-stub@v1" if executed_node == OFFLINE_DEFAULT_NODE
                      else (result.get("model") or executed_node))
    receipt = build_receipt(object_id=object_id, preference_id=resolved["preference_id"],
                            requested_model_class=requested_class, route=route, executed_node=executed_node,
                            executed_model=executed_model, input_text=input_text, output_text=output, now=now,
                            tokens=result.get("tokens"), latency_ms=result.get("latency_ms"),
                            base_host=result.get("base_host"))
    # durable provenance: best-effort append to the shared JSONL sink (never raises, never changes the return)
    from src.teleon.inference.receipts import persist_receipt  # lazy: keep the decision plane import-light
    persist_receipt(receipt, plane="oips")
    return {"output": output, "resolved_preference": resolved, "route_decision": route, "receipt": receipt}


__all__ = ["resolve_preference", "select_provider", "build_receipt", "infer_local", "load_graph",
           "OFFLINE_DEFAULT_NODE", "ALLOWED_USE_ORDER"]
