#!/usr/bin/env python3
"""Validate the service auth consumption model against services/registry.yaml.

The check is intentionally small and offline. It proves that every registry
service has a distinct service account, every registry-declared communication
edge has an auth policy edge, and no policy field embeds obvious raw secrets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
MODEL = _resource("architecture") / "service_auth_consumption_model.json"
REGISTRY = _resource("services") / "registry.yaml"

SERVICE_GROUPS = ("products", "platform", "infra")
EVENT_SINKS = {"event_bus"}
DATASTORE_SINKS = {"postgres_pgvector", "object_store", "redis", "event_bus"}
ALLOWED_SINKS = EVENT_SINKS | DATASTORE_SINKS
INTERNAL_AUTH = {"internal_service_token", "mtls_spiffe", "queue_identity", "datastore_workload_identity"}
RAW_SECRET_NEEDLES = ("sk-", "xox", "ghp_", "api_key=", "client_secret=", "password=", "private_key=", "token=")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _registry_services(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    services: dict[str, dict[str, Any]] = {}
    for group in SERVICE_GROUPS:
        for item in registry.get(group, []) or []:
            sid = item.get("id")
            if sid:
                services[sid] = item
    return services


def _registry_edges(services: dict[str, dict[str, Any]]) -> set[tuple[str, str, str]]:
    edges: set[tuple[str, str, str]] = set()
    for sid, svc in services.items():
        comms = svc.get("comms") or {}
        for callee in comms.get("sync_reads", []) or []:
            edges.add((sid, callee, "sync_read"))
        for callee in comms.get("enqueues", []) or []:
            edges.add((sid, callee, "enqueue"))
        for callee in comms.get("calls", []) or []:
            edges.add((sid, callee, "call"))
        for event_name in comms.get("emits", []) or []:
            if "." in str(event_name):
                edges.add((sid, "event_bus", "event_emit"))
        for callee in comms.get("reads", []) or []:
            edges.add((sid, callee, "datastore_read"))
    return edges


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_walk_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(_walk_strings(item))
        return out
    return []


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    try:
        model = _load_json(MODEL)
        registry = _load_yaml(REGISTRY)
    except Exception as exc:  # noqa: BLE001
        check("model and service registry load", False, f"{type(exc).__name__}: {exc}")
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1

    services = _registry_services(registry)
    service_ids = set(services)
    accounts = model.get("service_accounts", []) or []
    account_services = {a.get("service") for a in accounts}
    account_ids = [a.get("account_id") for a in accounts]
    auth_methods = set((model.get("allowed_auth_methods") or {}).keys())

    check("every registry service has a service account", service_ids <= account_services, str(sorted(service_ids - account_services)))
    check("service accounts refer only to registry services", account_services <= service_ids, str(sorted(account_services - service_ids)))
    check("service account ids are unique", len(account_ids) == len(set(account_ids)), str(account_ids))
    check("no shared god-token account id", all(aid != "god-token" and aid != "shared" for aid in account_ids if aid))

    for account in accounts:
        sid = account.get("service")
        check(f"{sid}: account_id uses svc- prefix", str(account.get("account_id", "")).startswith("svc-"))
        strategies = account.get("credential_strategy") or {}
        local = strategies.get("local")
        prod = strategies.get("production")
        strategy_ok = bool(local) and bool(prod) and (prod == "mtls_spiffe" or "workload_identity" in str(prod) or prod == "user_session_if_console_enabled")
        check(f"{sid}: local and production credential strategies recorded", strategy_ok, str(strategies))
        scopes = account.get("base_scopes") or []
        audit = account.get("audit_events") or []
        data_classes = account.get("data_classes") or []
        check(f"{sid}: base scopes recorded", bool(scopes))
        check(f"{sid}: audit events recorded", bool(audit))
        check(f"{sid}: data classes recorded", bool(data_classes))
        for method in account.get("external_auth", []) or []:
            check(f"{sid}: external auth method '{method}' is known", method in auth_methods)

    policy_edges = {
        (e.get("caller"), e.get("callee"), e.get("channel")): e
        for e in model.get("service_edges", []) or []
    }
    required_edges = _registry_edges(services)
    check("all registry-declared edges have auth policy edges",
          required_edges <= set(policy_edges),
          str(sorted(required_edges - set(policy_edges))))

    for key, edge in policy_edges.items():
        caller, callee, channel = key
        caller_ok = caller in service_ids
        callee_ok = callee in service_ids or callee in ALLOWED_SINKS
        check(f"edge {caller}->{callee} ({channel}): caller is a registry service", caller_ok)
        check(f"edge {caller}->{callee} ({channel}): callee is service or approved sink", callee_ok)
        method = edge.get("auth_method")
        check(f"edge {caller}->{callee} ({channel}): auth method is known", method in auth_methods)
        if caller in service_ids and callee in service_ids:
            check(f"edge {caller}->{callee} ({channel}): internal calls do not use external API keys",
                  method in INTERNAL_AUTH,
                  str(method))
        check(f"edge {caller}->{callee} ({channel}): scopes present", bool(edge.get("scopes")))
        checks = edge.get("authorization_checks") or []
        check(f"edge {caller}->{callee} ({channel}): tenant or event/object authorization recorded",
              any(c in checks for c in ("tenant_id", "event_type", "table_policy")),
              str(checks))
        check(f"edge {caller}->{callee} ({channel}): receipt/audit recorded", bool(edge.get("receipt")))

    external_edges = model.get("external_edges", []) or []
    check("external edges recorded", bool(external_edges))
    for edge in external_edges:
        method = edge.get("auth_method")
        check(f"external edge {edge.get('caller')}->{edge.get('callee')}: auth method is known", method in auth_methods)
        check(f"external edge {edge.get('caller')}->{edge.get('callee')}: authorization checks present",
              bool(edge.get("authorization_checks")))
        check(f"external edge {edge.get('caller')}->{edge.get('callee')}: receipt/audit recorded",
              bool(edge.get("receipt")))

    strings = _walk_strings(model)
    raw_hits = [s for s in strings if any(needle in s.lower() for needle in RAW_SECRET_NEEDLES)]
    check("no obvious raw secret literals in auth policy", not raw_hits, str(raw_hits[:5]))

    token_req = model.get("token_requirements") or {}
    check("service token requirements include exp/aud/sub/scope",
          {"exp", "aud", "sub", "scope"} <= set(token_req.get("service_tokens_must_include", [])))
    check("api key record requirements include hash/prefix/revoked_at",
          {"hash", "prefix", "revoked_at"} <= set(token_req.get("api_key_records_must_include", [])))

    phases = [p.get("phase") for p in model.get("implementation_phases", []) or []]
    check("implementation phases include local_mvp and production_saas",
          {"local_mvp", "production_saas"} <= set(phases),
          str(phases))

    if fails:
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1
    print("\nPASS - check_service_auth_consumption_model: every registry service has a distinct service account; "
          "registry communication edges are covered by scoped internal auth policy; external edges, token "
          "requirements, audit/receipt requirements, and implementation phases are recorded; no obvious raw "
          "secret literals were found.")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_service_auth_consumption_model.py --self-test")
    raise SystemExit(0)
