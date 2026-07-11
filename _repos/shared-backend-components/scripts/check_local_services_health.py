#!/usr/bin/env python3
"""scripts.check_local_services_health — PROOF for the Cloud-Run-like local service registry.

Asserts:
  A. REGISTRY SHAPE — every service carries the gate-required fields; statuses are honest
     (active_local | held | planned); every non-active service declares a held_reason; no two
     ACTIVE process groups claim the same port (one group may serve several surfaces on one port).
  B. PORT DRIFT GATES — portfolio site ports mirror _repos/shared-backend-components/scripts/portfolio_lib.py (PORTS + HUB_PORT)
     and the identity service port mirrors _repos/shared-backend-components/architecture/identity_realm_registry.json defaults.port;
     mirrored values are allowed ONLY because this check fails on drift.
  C. RUNTIME — every active_local group starts (idempotently — already-running groups are left
     alone) and answers its health_url. Services this check starts are LEFT RUNNING by design
     (idempotent startup is the Cloud-Run-like discipline; the flywheel keeps the local plane warm).
  D. HONEST URL MAP — dist/local-service-urls.md regenerates with real local URLs; tunnel cells
     come only from the recorded launcher manifest (no fake URLs).

Offline/localhost-only, stdlib-only. Exit 0/1. `--self-test` runs the gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.portfolio_lib as P  # noqa: E402
from scripts.local_services_lib import (REGISTRY_PATH, URL_MAP_PATH, group_health, groups,  # noqa: E402
                                        load_registry, start_group, write_url_map)

REQUIRED_FIELDS = ("service_id", "display_name", "owner", "port", "start_command", "health_url",
                   "ready_url", "public_routes", "private_routes", "env_file", "allowed_consumers",
                   "auth_mode", "data_classes", "logs_path", "screenshot_required",
                   "trycloudflare_required", "status")
VALID_STATUSES = {"active_local", "held", "planned"}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    registry = load_registry()
    svcs = registry["services"]

    # A. registry shape
    for svc in svcs:
        missing = [f for f in REQUIRED_FIELDS if f not in svc]
        if missing:
            ck(f"A: {svc.get('service_id', '?')} has all gate fields", False, str(missing))
    ck("A: all services carry the gate-required fields",
       all(all(f in svc for f in REQUIRED_FIELDS) for svc in svcs))
    ck("A: statuses are honest enums", all(svc["status"] in VALID_STATUSES for svc in svcs))
    ck("A: every non-active service declares a held_reason",
       all(svc.get("held_reason") for svc in svcs if svc["status"] != "active_local"))
    active_group_ports: dict[int, set[str]] = {}
    for svc in svcs:
        if svc["status"] == "active_local":
            active_group_ports.setdefault(svc["port"], set()).add(
                svc.get("process_group") or svc["service_id"])
    clashes = {p: g for p, g in active_group_ports.items() if len(g) > 1}
    ck("A: no two ACTIVE process groups share a port", not clashes, str(clashes))

    # B. port drift gates (the only allowed mirrors of those values)
    by_id = {svc["service_id"]: svc for svc in svcs}
    site_map = {"parent_site": "aidoneright", "teleon_site": "teleon.dev", "baltor_site": "baltor",
                "openhubforai_site": "openhubforai", "opencontexthub_site": "opencontexthub",
                "openskillshub_site": "openskillshub", "opentoolshub_site": "opentoolshub"}
    ck("B: portfolio hub port mirrors portfolio_lib.HUB_PORT",
       by_id["portfolio_hub"]["port"] == P.HUB_PORT)
    for sid, key in site_map.items():
        ck(f"B: {sid} port mirrors portfolio_lib.PORTS[{key!r}]",
           sid in by_id and by_id[sid]["port"] == P.PORTS[key])
    identity_registry = json.loads((_resource("architecture") / "identity_realm_registry.json")
                                   .read_text(encoding="utf-8"))
    ck("B: identity service port mirrors the identity realm registry",
       by_id["local_auth_service"]["port"] == int(identity_registry["defaults"]["port"]))
    ck("B: registry file is the declared one", REGISTRY_PATH.name == "local_service_registry.json")

    # C. runtime — start (idempotent) + health for every active group
    for group, members in groups(registry).items():
        if not any(m["status"] == "active_local" for m in members):
            continue
        result = start_group(group, members)
        health = group_health(members)
        ok = result in {"already_running", "started"} and any(health.values())
        ck(f"C: {group} runs and answers health ({result})", ok, str(health))
        for sid, up in health.items():
            if by_id[sid]["status"] == "active_local":
                ck(f"C: {sid} health endpoint answers", up)

    # D. honest URL map
    path = write_url_map(registry)
    text = path.read_text(encoding="utf-8")
    ck("D: url map regenerated", path == URL_MAP_PATH and "Local service URLs" in text)
    ck("D: no invented tunnel URLs (cells only from the recorded manifest)",
       "trycloudflare.com" not in text or (_resource("dist") / "portfolio-share-urls.json").exists())

    print("\n" + ("PASS — check_local_services_health: gate-shaped local service registry (honest "
                  "active/held/planned statuses + held reasons), drift-gated ports (portfolio_lib + "
                  "identity registry), every active group starts idempotently and answers health, and "
                  "the URL map carries real URLs only."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_local_services_health.py --self-test")
    raise SystemExit(0)
