#!/usr/bin/env python3
"""scripts.local_services_lib — shared harness for the Cloud-Run-like LOCAL service registry.

Reads _repos/shared-backend-components/architecture/local_service_registry.json and gives the start/stop/health CLIs and proofs one
implementation: dedupe services into process groups, idempotent startup (health-first — if a group
already answers, never double-start), stop ONLY via the service's own stop_command or the exact
recorded pid (never pkill), structured per-group logs under dist/local-services/, pid files under
.agent/local-services/, and the honest URL map at dist/local-service-urls.md (real local URLs only;
tunnel URLs only when a real recorded manifest exists — never invented).
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*` on
# a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch. install() prepends every code root.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402

import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

# REPO_ROOT stays the MONOREPO root — services spawn with cwd=REPO_ROOT (their commands are repo-root-relative).
REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
REGISTRY_PATH = _resource("architecture") / "local_service_registry.json"
PID_DIR = (REPO_ROOT / ".agent") / "local-services"
LOGS_DIR = _resource("dist") / "local-services"
URL_MAP_PATH = _resource("dist") / "local-service-urls.md"
TUNNEL_MANIFEST = _resource("dist") / "portfolio-share-urls.json"   # written by the tunnel launcher
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


def _resolve_cmd(cmd: list[str]) -> list[str]:
    """Rewrite each repo-relative resource path in a start/stop command (e.g.
    'scripts/serve_portfolio_sites.py') to its REAL post-`_repos/`-migration location via `_resource`, so a
    spawn with cwd=REPO_ROOT works even though scripts/ now lives under _repos/shared-backend-components/.
    Non-path tokens (python3, -m, --start, a bare port, a dotted `scripts.x` module) are left untouched —
    only a token that `_resource` resolves to an EXISTING file/dir is rewritten (so this is a no-op for
    module-form commands and for any path that never moved)."""
    out: list[str] = []
    for tok in cmd:
        if isinstance(tok, str) and "/" in tok and not tok.startswith(("-", "/")):
            resolved = _resource(tok)
            out.append(str(resolved) if resolved.exists() else tok)
        else:
            out.append(tok)
    return out


def start_group(group: str, members: list[dict[str, Any]]) -> str:
    """Idempotent start. Returns one of: already_running | started | no_start_command | failed."""
    starters = [m for m in members if m.get("start_command") and m.get("status") == "active_local"]
    if not starters:
        return "no_start_command"
    if any(group_health(members).values()):
        return "already_running"
    PID_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    cmd = _resolve_cmd(starters[0]["start_command"])
    log_path = LOGS_DIR / f"{group}.log"
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n--- start {group} @ {int(time.time())}: {' '.join(cmd)} ---\n")
        log.flush()
        proc = subprocess.Popen(cmd, cwd=REPO_ROOT, stdout=log, stderr=log,
                                start_new_session=True,
                                env={**os.environ, "PYTHONPATH": _pythonpath("."),
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
        subprocess.run(_resolve_cmd(stoppers[0]["stop_command"]), cwd=REPO_ROOT, capture_output=True,
                       env={**os.environ, "PYTHONPATH": _pythonpath(".")})
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
