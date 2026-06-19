"""Teleon egress intent and route-policy decisions.

This module is the deterministic control layer before transport. A worker asks
for an outbound action by creating an ``EgressIntent.v1``; the route broker
chooses an ``EgressRouteDecision.v1`` from the repo-owned policy taxonomy.

The decision is evidence only. It never asserts that a response is true.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from src.teleon.egress.traffic_graph import EGRESS_SERVES_TRUTH
from src.teleon.egress.transports import UrllibHttpTransport
from src.teleon.experiments.ids import canonical_id, sha256_hex

_REPO = Path(__file__).resolve().parents[3]
_ROUTE_POLICY_PATH = _REPO / "architecture" / "egress_route_policy_taxonomy.json"

INTENT_SCHEMA_VERSION = "EgressIntent.v1"
ROUTE_DECISION_SCHEMA_VERSION = "EgressRouteDecision.v1"
DEFAULT_ROUTE_POLICY_ID = "direct_public_internet"
BLOCKED_ROUTE_POLICY_ID = "manual_review_blocked"
#: transport kind stamped on an allowed decision — single-sourced from the approved transport adapter so the
#: string can never drift between policy.py and transports.py.
ALLOWED_TRANSPORT_KIND = UrllibHttpTransport.transport_kind


class EgressPolicyError(ValueError):
    """Raised when an egress intent or route policy is malformed."""


def _redact_url_for_policy(url: str) -> dict[str, str]:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.port:
        host = f"{host}:{parts.port}"
    destination_key = urlunsplit((parts.scheme.lower(), host, parts.path or "/", "", ""))
    return {
        "scheme": parts.scheme.lower(),
        "destination_host": host,
        "destination_key": destination_key,
        "destination_url": destination_key,
    }


def route_policy_taxonomy() -> dict[str, Any]:
    return json.loads(_ROUTE_POLICY_PATH.read_text(encoding="utf-8"))


def route_policies_by_id() -> dict[str, dict[str, Any]]:
    taxonomy = route_policy_taxonomy()
    return {route["route_policy_id"]: route for route in taxonomy["routes"]}


def approval_required_route_ids(policies: dict[str, dict[str, Any]] | None = None) -> set[str]:
    """Routes that need an explicit approval ref before they may be allowed — DERIVED from the taxonomy (the
    single source), never a hand-kept literal: any route that is not ``default_allowed`` and is not the
    ``blocked`` kind. Adding or restricting a route is a taxonomy edit, not a code change, so the set can never
    silently drift from the policy file (the bug a hardcoded set caused: ``browser_pool_render`` was
    default_allowed=false yet absent from the literal, so it was wrongly allowed without approval)."""
    policies = policies if policies is not None else route_policies_by_id()
    return {rid for rid, p in policies.items()
            if not p.get("default_allowed", False) and p.get("route_kind") != "blocked"}


def _query_id(tenant_id: str, run_id: str, query_text: str) -> str:
    return canonical_id("egq", tenant_id, run_id, query_text)


def make_egress_intent(
    *,
    tenant_id: str,
    run_id: str,
    worker_id: str,
    worker_kind: str,
    operation: str,
    destination_url: str,
    method: str = "GET",
    query_text: str = "",
    query_id: str = "",
    route_policy_id: str = DEFAULT_ROUTE_POLICY_ID,
    request_summary: dict[str, Any] | None = None,
    requested_at: str,
    tool_name: str = "",
    trace_id: str = "",
) -> dict[str, Any]:
    required = {
        "tenant_id": tenant_id,
        "run_id": run_id,
        "worker_id": worker_id,
        "worker_kind": worker_kind,
        "operation": operation,
        "destination_url": destination_url,
        "requested_at": requested_at,
    }
    missing = [key for key, value in required.items() if not str(value or "").strip()]
    if missing:
        raise EgressPolicyError(f"missing required egress intent fields: {missing}")
    destination = _redact_url_for_policy(destination_url)
    query_text = query_text or f"{method.upper()} {destination['destination_host']}"
    qid = query_id or _query_id(tenant_id, run_id, query_text)
    intent_identity = {
        "tenant_id": tenant_id,
        "run_id": run_id,
        "worker_id": worker_id,
        "operation": operation,
        "method": method.upper(),
        "destination_key": destination["destination_key"],
        "query_id": qid,
        "requested_at": requested_at,
    }
    return {
        "schema_version": INTENT_SCHEMA_VERSION,
        "intent_id": canonical_id("egi", json.dumps(intent_identity, sort_keys=True)),
        "tenant_id": tenant_id,
        "run_id": run_id,
        "worker_id": worker_id,
        "worker_kind": worker_kind,
        "tool_name": tool_name,
        "operation": operation,
        "method": method.upper(),
        "destination": destination,
        "query_id": qid,
        "query_text_redacted": query_text,
        "query_hash": "sha256:" + sha256_hex(query_text),
        "route_policy_id": route_policy_id or DEFAULT_ROUTE_POLICY_ID,
        "request_summary": request_summary or {},
        "requested_at": requested_at,
        "trace_id": trace_id,
        "serves_truth": EGRESS_SERVES_TRUTH,
    }


def decide_route(
    intent: dict[str, Any],
    *,
    approved_route_refs: set[str] | None = None,
    now: str,
    policies: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return an ``EgressRouteDecision.v1`` for ``intent``.

    High-risk route families require an explicit approval ref. Unknown policies,
    unsupported URL schemes, or blocked policies produce a blocked decision
    instead of falling through to another network path.
    """
    if intent.get("schema_version") != INTENT_SCHEMA_VERSION:
        raise EgressPolicyError("intent must be EgressIntent.v1")
    policies = policies or route_policies_by_id()
    approved_route_refs = approved_route_refs or set()
    requested_policy_id = str(intent.get("route_policy_id") or DEFAULT_ROUTE_POLICY_ID)
    policy = policies.get(requested_policy_id)
    action = "allow"
    reason = "route policy allowed"
    selected_policy_id = requested_policy_id
    if not policy:
        action = "blocked"
        reason = f"unknown route policy {requested_policy_id!r}"
        selected_policy_id = BLOCKED_ROUTE_POLICY_ID
        policy = policies[selected_policy_id]
    elif requested_policy_id == BLOCKED_ROUTE_POLICY_ID or policy.get("route_kind") == "blocked":
        action = "blocked"
        reason = "route policy requires manual review"
    elif intent["destination"].get("scheme") not in {"http", "https"}:
        action = "blocked"
        reason = "unsupported destination scheme"
        selected_policy_id = BLOCKED_ROUTE_POLICY_ID
        policy = policies[selected_policy_id]
    elif not policy.get("default_allowed", False) and not approved_route_refs:
        action = "blocked"
        reason = f"route policy {requested_policy_id} is not default-allowed and requires an explicit approval ref"
        selected_policy_id = BLOCKED_ROUTE_POLICY_ID
        policy = policies[selected_policy_id]

    decision_identity = {
        "intent_id": intent["intent_id"],
        "route_policy_id": selected_policy_id,
        "action": action,
        "reason": reason,
        "decided_at": now,
    }
    return {
        "schema_version": ROUTE_DECISION_SCHEMA_VERSION,
        "decision_id": canonical_id("egd", json.dumps(decision_identity, sort_keys=True)),
        "intent_id": intent["intent_id"],
        "tenant_id": intent["tenant_id"],
        "run_id": intent["run_id"],
        "worker_id": intent["worker_id"],
        "query_id": intent["query_id"],
        "destination": intent["destination"],
        "requested_route_policy_id": requested_policy_id,
        "route_policy_id": selected_policy_id,
        "route_kind": policy["route_kind"],
        "policy_version": route_policy_taxonomy()["version"],
        "action": action,
        "reason": reason,
        "transport_kind": ALLOWED_TRANSPORT_KIND if action == "allow" else "blocked",
        "capture_required": bool(policy.get("capture_required")),
        "decision_receipt_required": bool(policy.get("decision_receipt_required")),
        "approved_route_refs": sorted(approved_route_refs),
        "decided_at": now,
        "serves_truth": EGRESS_SERVES_TRUTH,
    }


__all__ = [
    "ALLOWED_TRANSPORT_KIND",
    "BLOCKED_ROUTE_POLICY_ID",
    "DEFAULT_ROUTE_POLICY_ID",
    "EgressPolicyError",
    "INTENT_SCHEMA_VERSION",
    "ROUTE_DECISION_SCHEMA_VERSION",
    "approval_required_route_ids",
    "decide_route",
    "make_egress_intent",
    "route_policies_by_id",
    "route_policy_taxonomy",
]
