#!/usr/bin/env python3
"""scripts.local_services_lib — shared harness for the Cloud-Run-like LOCAL service registry.

Reads architecture/local_service_registry.json and gives the start/stop/health CLIs and proofs one
implementation: dedupe services into process groups, idempotent startup (health-first — if a group
already answers, never double-start), stop ONLY via the service's own stop_command or the exact
recorded pid (never pkill), structured per-group logs under dist/local-services/, pid files under
.agent/local-services/, and the honest URL map at dist/local-service-urls.md (real local URLs only;
tunnel URLs only when a real recorded manifest exists — never invented).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "architecture" / "local_service_registry.json"
PID_DIR = REPO_ROOT / ".agent" / "local-services"
LOGS_DIR = REPO_ROOT / "dist" / "local-services"
URL_MAP_PATH = REPO_ROOT / "dist" / "local-service-urls.md"
TUNNEL_MANIFEST = REPO_ROOT / "dist" / "portfolio-share-urls.json"   # written by the tunnel launcher
HEALTH_TIMEOUT_SECONDS = 3
START_POLL_SECONDS = 25          # max wait for a freshly started group to answer health


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def services(registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return (registry or load_registry())["services"]


def groups(registry: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    """process_group -> member services (a group is one OS process serving N surfaces)."""
    out: dict[str, list[dict[str, Any]]] = {}
    for svc in services(registry):
        out.setdefault(svc.get("process_group") or svc["service_id"], []).append(svc)
    return out


def is_up(url: str, timeout: float = HEALTH_TIMEOUT_SECONDS) -> bool:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as resp:
            return resp.status < 500
    except urllib.error.HTTPError as err:
        return err.code < 500            # an auth/404 answer still proves the process is alive
    except Exception:
        return False


def group_health(members: list[dict[str, Any]]) -> dict[str, bool]:
    return {m["service_id"]: is_up(m["health_url"]) for m in members if m.get("health_url")}


def start_group(group: str, members: list[dict[str, Any]]) -> str:
    """Idempotent start. Returns one of: already_running | started | no_start_command | failed."""
    starters = [m for m in members if m.get("start_command") and m.get("status") == "active_local"]
    if not starters:
        return "no_start_command"
    if any(group_health(members).values()):
        return "already_running"
    PID_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    cmd = starters[0]["start_command"]
    log_path = LOGS_DIR / f"{group}.log"
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n--- start {group} @ {int(time.time())}: {' '.join(cmd)} ---\n")
        log.flush()
        proc = subprocess.Popen(cmd, cwd=REPO_ROOT, stdout=log, stderr=log,
                                start_new_session=True,
                                env={**os.environ, "PYTHONPATH": str(REPO_ROOT),
                                     **(starters[0].get("env") or {})})
    (PID_DIR / f"{group}.pid").write_text(str(proc.pid), encoding="utf-8")
    deadline = time.time() + START_POLL_SECONDS
    while time.time() < deadline:
        if any(group_health(members).values()):
            return "started"
        if proc.poll() is not None and not any(group_health(members).values()):
            # the launcher may legitimately exit after daemonizing (e.g. serve_portfolio_sites
            # --start) — keep polling health until the deadline before calling it failed
            time.sleep(1.0)
            continue
        time.sleep(1.0)
    return "started" if any(group_health(members).values()) else "failed"


def stop_group(group: str, members: list[dict[str, Any]]) -> str:
    """Stop via the service's own stop_command when declared, else the exact recorded pid."""
    stoppers = [m for m in members if m.get("stop_command")]
    if stoppers:
        subprocess.run(stoppers[0]["stop_command"], cwd=REPO_ROOT, capture_output=True,
                       env={**os.environ, "PYTHONPATH": str(REPO_ROOT)})
        return "stopped_via_command"
    pid_file = PID_DIR / f"{group}.pid"
    if not pid_file.exists():
        return "no_pid_recorded"
    pid = int(pid_file.read_text(encoding="utf-8").strip())
    try:
        os.kill(pid, signal.SIGTERM)     # exact recorded pid only — never a broad sweep
        return "stopped_via_pid"
    except ProcessLookupError:
        return "not_running"
    finally:
        pid_file.unlink(missing_ok=True)


def _tunnel_urls() -> dict[str, str]:
    """Real recorded tunnel URLs only (from the launcher's manifest); never invented."""
    if not TUNNEL_MANIFEST.exists():
        return {}
    try:
        data = json.loads(TUNNEL_MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[str, str] = {}
    for item in data if isinstance(data, list) else data.get("urls", []):
        if isinstance(item, dict) and "trycloudflare.com" in str(item.get("url", "")):
            out[str(item.get("site") or item.get("id") or "")] = item["url"]
    return out


def write_url_map(registry: dict[str, Any] | None = None) -> Path:
    reg = registry or load_registry()
    tunnels = _tunnel_urls()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Local service URLs (generated by scripts/local_services_lib.py — do not hand-edit)",
        "",
        f"Last checked: {now}. Real URLs only: tunnel cells are filled ONLY from the recorded",
        f"launcher manifest ({TUNNEL_MANIFEST.name}); a blank cell means no live tunnel was recorded.",
        "",
        "| service | status | local_url | health | tunnel_url | notes |",
        "|---|---|---|---|---|---|",
    ]
    for svc in services(reg):
        url = svc.get("health_url") or ""
        local = url.rsplit("/", 1)[0] + "/" if url else ""
        health = "up" if (url and svc["status"] == "active_local" and is_up(url)) else (
            "n/a" if svc["status"] != "active_local" else "down")
        note = svc.get("held_reason", "") if svc["status"] != "active_local" else ""
        lines.append(f"| {svc['service_id']} | {svc['status']} | {local} | {health} | "
                     f"{tunnels.get(svc['service_id'], '')} | {note[:90]} |")
    URL_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    URL_MAP_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return URL_MAP_PATH
