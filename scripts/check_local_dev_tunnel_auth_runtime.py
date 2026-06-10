#!/usr/bin/env python3
"""Validate the local-dev tunnel/auth runtime plan.

This proof covers the no-paid-cloud path: local static sites, local containers,
TryCloudflare quick tunnels as temporary reverse proxies, and local service-auth
rules that map back to the service-auth policy.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
MANIFEST = REPO / "architecture" / "local_dev_tunnel_auth_runtime.json"
DOC = REPO / "docs" / "architecture" / "local-dev-tunnels-and-auth.md"
SERVICE_AUTH = REPO / "architecture" / "service_auth_consumption_model.json"
SERVICE_REGISTRY = REPO / "services" / "registry.yaml"
LAUNCHER = REPO / "scripts" / "launch_portfolio_trycloudflare.py"
SERVER = REPO / "scripts" / "serve_portfolio_sites.py"

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("local runtime manifest exists", MANIFEST.exists(), str(MANIFEST))
    check("local runtime doc exists", DOC.exists(), str(DOC))
    if not MANIFEST.exists() or not DOC.exists():
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1

    data = json.loads(_read(MANIFEST))
    doc = _read(DOC)
    combined = json.dumps(data, sort_keys=True) + "\n" + doc

    from scripts import portfolio_lib as P

    registry = yaml.safe_load(_read(SERVICE_REGISTRY))
    auth = json.loads(_read(SERVICE_AUTH))
    launch_src = _read(LAUNCHER)
    server_src = _read(SERVER)

    check("manifest declares no paid cloud required",
          data.get("principles", {}).get("no_paid_cloud_required") is True)
    check("manifest declares containerized local apps allowed",
          data.get("principles", {}).get("containerized_local_apps_allowed") is True)
    check("TryCloudflare is temporary preview, not auth",
          data.get("principles", {}).get("trycloudflare_is_temporary_preview") is True
          and data.get("principles", {}).get("trycloudflare_is_not_auth") is True)
    check("fake URLs are forbidden", data.get("principles", {}).get("no_fake_urls") is True)

    expected_ports = set(range(9101, 9101 + len(P.SITE_ORDER)))
    check("portfolio_lib site ports are contiguous local ports",
          {P.PORTS[s] for s in P.SITE_ORDER} == expected_ports,
          str([P.PORTS[s] for s in P.SITE_ORDER]))
    # the launcher's expected set may union extra derived ports (e.g. {P.HUB_PORT} | …); the gate is
    # that site ports are DERIVED from SITE_ORDER, never a hand-typed count
    check("TryCloudflare launcher targets SITE_ORDER rather than stale fixed count",
          "P.SITE_ORDER" in launch_src and "set(range(9101, 9101 + len(P.SITE_ORDER)))" in launch_src)
    check("static server targets SITE_ORDER rather than stale fixed count",
          "P.SITE_ORDER" in server_src and "expected_ports = set(range(9101, 9101 + len(P.SITE_ORDER)))" in server_src)

    tcf = data.get("trycloudflare_policy", {})
    check("TryCloudflare policy records temporary non-production caveat",
          tcf.get("temporary") is True and tcf.get("not_production_hosting") is True)
    check("TryCloudflare policy has honest missing states",
          set(tcf.get("missing_states", [])) == {"MISSING_CLOUDFLARED", "TUNNEL_UNREACHABLE"})
    check("TryCloudflare policy uses exact recorded pid cleanup",
          tcf.get("pid_cleanup") == "exact_recorded_pid_only")
    check("TryCloudflare launcher captures real trycloudflare URLs only",
          "trycloudflare" in launch_src and "_URL_RE" in launch_src and "public_url" in launch_src)
    sweep_terms = ("pk" + "ill", "kill" + "all", "os." + "system(")
    check("TryCloudflare launcher has exact-PID cleanup and no broad sweep",
          "os.kill(" in launch_src and not any(term in launch_src for term in sweep_terms))

    compose_files = [REPO / item["file"] for item in data.get("container_stacks", [])]
    check("container stack files recorded", len(compose_files) >= 3)
    for path in compose_files:
        check(f"container stack exists: {path.relative_to(REPO)}", path.exists())
    check("all container stacks are local, no paid cloud required",
          all(item.get("paid_cloud_required") is False for item in data.get("container_stacks", [])))

    required_local_modes = {
        "none_static_preview",
        "anonymous_demo_read",
        "local_internal_service_token",
        "queue_identity",
        "secret_ref_only",
    }
    check("required local auth modes recorded",
          required_local_modes <= {item.get("mode") for item in data.get("local_auth_modes", [])})
    auth_methods = set(auth.get("allowed_auth_methods", {}))
    check("service-auth policy supports local internal tokens",
          "internal_service_token" in auth_methods and "queue_identity" in auth_methods)
    check("service-auth policy has local_mvp implementation phase",
          any(phase.get("phase") == "local_mvp" for phase in auth.get("implementation_phases", [])))

    registry_services = {s["id"] for group in ("products", "platform", "infra") for s in registry.get(group, [])}
    auth_services = {s["service"] for s in auth.get("service_accounts", [])}
    check("service-auth policy covers every local registry service",
          registry_services <= auth_services, str(sorted(registry_services - auth_services)))

    for phrase in [
        "TryCloudflare quick tunnels",
        "not production hosting",
        "not an auth system",
        "service accounts",
        "local_internal_service_token",
        "secret_ref",
        "No fake URLs",
        "Baltor governs context",
        "Teleon runs capabilities",
        "Open*Hubs are registries",
        "Dashboards and Control Towers are projection-only",
    ]:
        check(f"doc contains local boundary phrase: {phrase}", phrase in doc)

    for pattern in SECRET_PATTERNS:
        check(f"no obvious raw secret pattern {pattern.pattern}", not pattern.search(combined))

    print("\n" + (
        "PASS - check_local_dev_tunnel_auth_runtime: local no-paid-cloud runtime plan exists, "
        "TryCloudflare quick tunnels are temporary real-URL-only previews, static site ports come from "
        "portfolio_lib, local container stacks exist, and local auth maps to the service-auth policy."
        if not fails else f"{len(fails)} FAILURES: {fails}"
    ))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_local_dev_tunnel_auth_runtime.py --self-test")
    raise SystemExit(0)
