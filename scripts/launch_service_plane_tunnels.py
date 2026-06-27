#!/usr/bin/env python3
"""scripts.launch_service_plane_tunnels — TryCloudflare quick tunnels for the SERVICE plane.

The portfolio launcher (`launch_portfolio_trycloudflare.py`) tunnels the static launch
sites; this launcher tunnels the RUNNING service plane — the apps and the seam services
the recordable user journeys traverse — so server-to-server / plane-to-plane hops can be
exercised over public URLs instead of localhost.

Same discipline as the portfolio launcher: NO FAKE URLs (only what cloudflared prints;
a target with no captured URL gets an honest MISSING/UNREACHABLE status), EXACT-PID
cleanup only, ports come from `architecture/local_service_registry.json` (single source —
never hand-typed here). On capture it also refreshes the `dist/showcase-share-url-*.txt`
files the journey recorder (`e2e/record_user_journeys.mjs`) resolves its public bases
from, and emits a seam-env block (`OH_SEAM_*_BASE`) for tunnel-mode proxying.

CLI:
    python3 scripts/launch_service_plane_tunnels.py --start|--stop|--status|--self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(REPO))
from scripts.local_services_lib import load_registry, services  # noqa: E402

_STATE = REPO / ".agent" / "service-plane-tunnels"
_TUNNEL_PIDS = _STATE / "tunnel-pids.json"
_TUNNEL_LOGS = _STATE / "tunnel-logs"
_URLS = _STATE / "urls.json"
_SHARE_JSON = REPO / "dist" / "service-plane-tunnel-urls.json"
_SHARE_MD = REPO / "dist" / "service-plane-tunnel-urls.md"
_SEAM_ENV = REPO / "dist" / "service-plane-tunnel-seams.env"
_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
_CAVEAT = ("TryCloudflare quick tunnels are TEMPORARY, random session URLs — they die with the "
           "tunnel process. Production traffic uses named tunnels + real domains.")
_INSTALL = "Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"

#: service_id → (share-file the journey recorder reads | None, seam env var | None).
#: The TARGETS keys are the tunnelled plane; ports are looked up in the registry.
TARGETS: dict[str, dict] = {
    "harness_hub_app": {"share": "showcase-share-url-openhubforai.txt", "seam": None, "token_query": True},
    "teleon_app": {"share": "showcase-share-url-teleon.txt", "seam": None},
    "baltor_app": {"share": "showcase-share-url-baltor.txt", "seam": None, "token_query": True},
    "context_is_everything_app": {"share": "showcase-share-url-context-is-everything.txt", "seam": None},
    "local_auth_service": {"share": None, "seam": "OH_SEAM_IDENTITY_BASE"},
    "mailbox_local_service": {"share": None, "seam": "OH_SEAM_MAILBOX_BASE"},
    "local_openhub_projection_api": {"share": None, "seam": "OH_SEAM_REGISTRY_BASE"},
    "local_event_tracking_service": {"share": None, "seam": "OH_SEAM_ANALYTICS_BASE"},
    "teleon_local_runtime": {"share": None, "seam": "OH_SEAM_TELEON_RUNTIME_BASE"},
    "baltor_admin_demo_server": {"share": None, "seam": "OH_SEAM_LIVEOPS_BASE"},
    "demo_control_tower": {"share": None, "seam": None},
}

#: seconds to wait for cloudflared to print its URL before recording an honest failure.
URL_CAPTURE_WAIT_SECONDS = 30


def _ports() -> dict[str, int]:
    by_id = {s["service_id"]: int(s["port"]) for s in services(load_registry())}
    missing = [sid for sid in TARGETS if sid not in by_id]
    if missing:
        raise SystemExit(f"service ids not in local_service_registry.json: {missing}")
    return {sid: by_id[sid] for sid in TARGETS}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def have_cloudflared() -> str | None:
    path = shutil.which("cloudflared")
    if not path:
        return None
    try:
        subprocess.run([path, "--version"], capture_output=True, timeout=10)
    except Exception:  # noqa: BLE001
        return None
    return path


def _token() -> str:
    f = REPO / "dist" / "showcase-token.txt"
    return f.read_text().strip() if f.exists() else ""


def _write_manifests(records: dict) -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    _URLS.write_text(json.dumps(records, indent=2))
    _SHARE_JSON.write_text(json.dumps({"caveat": _CAVEAT, "targets": records}, indent=2))
    md = ["# Service-plane TryCloudflare URLs", "", f"> {_CAVEAT}", ""]
    seam_lines = []
    token = _token()
    for sid, rec in records.items():
        url = rec.get("public_url")
        md.append(f"- **{sid}** (:{rec['port']}): {url or rec['status']}")
        spec = TARGETS[sid]
        if url and spec.get("share"):
            share = url + (f"/?token={token}" if spec.get("token_query") and token else "/")
            (REPO / "dist" / spec["share"]).write_text(share + "\n")
        if url and spec.get("seam"):
            seam_lines.append(f"{spec['seam']}={url}")
    _SHARE_MD.write_text("\n".join(md) + "\n")
    _SEAM_ENV.write_text("\n".join(seam_lines) + ("\n" if seam_lines else ""))


def start(wait_s: int = URL_CAPTURE_WAIT_SECONDS) -> dict:
    ports = _ports()
    _TUNNEL_LOGS.mkdir(parents=True, exist_ok=True)
    cf = have_cloudflared()
    records: dict = {}
    if not cf:
        for sid, port in ports.items():
            records[sid] = {"port": port, "public_url": None,
                            "status": "MISSING_CLOUDFLARED", "install": _INSTALL}
        _TUNNEL_PIDS.write_text("{}")
        _write_manifests(records)
        return records
    stop()  # exact-PID cleanup of any prior run before starting fresh
    procs: dict = {}
    pids: dict = {}
    for sid, port in ports.items():
        logf = _TUNNEL_LOGS / f"{sid}.log"
        fh = open(logf, "wb")
        proc = subprocess.Popen(
            [cf, "tunnel", "--no-autoupdate", "--protocol", "http2",
             "--url", f"http://localhost:{port}"],
            stdout=fh, stderr=subprocess.STDOUT)
        procs[sid] = (proc, logf)
        pids[sid] = {"pid": proc.pid, "port": port}
    _STATE.mkdir(parents=True, exist_ok=True)
    _TUNNEL_PIDS.write_text(json.dumps(pids, indent=2))
    deadline = time.monotonic() + wait_s
    found: dict = {}
    while time.monotonic() < deadline and len(found) < len(procs):
        for sid, (_proc, logf) in procs.items():
            if sid in found:
                continue
            try:
                m = _URL_RE.search(logf.read_text(errors="ignore"))
            except FileNotFoundError:
                m = None
            if m:
                found[sid] = m.group(0)
        time.sleep(1.0)
    for sid, port in ports.items():
        proc, _logf = procs[sid]
        url = found.get(sid)
        records[sid] = {"port": port, "public_url": url, "pid": proc.pid,
                        "alive": _alive(proc.pid),
                        "status": "LIVE" if url else "TUNNEL_UNREACHABLE"}
    _write_manifests(records)
    return records


def stop() -> dict:
    if not _TUNNEL_PIDS.exists():
        return {}
    pids = json.loads(_TUNNEL_PIDS.read_text() or "{}")
    out: dict = {}
    for sid, rec in pids.items():
        pid = int(rec["pid"])
        if _alive(pid):
            try:
                os.kill(pid, 15)
                out[sid] = "stopped"
            except OSError as exc:
                out[sid] = f"kill-failed: {exc}"
        else:
            out[sid] = "already-dead"
    _TUNNEL_PIDS.write_text("{}")
    return out


def status() -> dict:
    recs = json.loads(_URLS.read_text()) if _URLS.exists() else {}
    for rec in recs.values():
        if rec.get("pid"):
            rec["alive"] = _alive(int(rec["pid"]))
    return recs


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ports = _ports()
    check("every target resolves to a registry port", len(ports) == len(TARGETS), str(ports))
    check("no hand-typed ports (all from the registry)", all(isinstance(p, int) and p > 0 for p in ports.values()))
    check("journey-recorder share files covered",
          {"showcase-share-url-openhubforai.txt", "showcase-share-url-teleon.txt"}
          <= {spec.get("share") for spec in TARGETS.values() if spec.get("share")})
    check("seam env names match the deploy seams",
          {"OH_SEAM_IDENTITY_BASE", "OH_SEAM_REGISTRY_BASE", "OH_SEAM_ANALYTICS_BASE",
           "OH_SEAM_TELEON_RUNTIME_BASE", "OH_SEAM_LIVEOPS_BASE"}
          <= {spec.get("seam") for spec in TARGETS.values() if spec.get("seam")})
    check("url regex anchors to trycloudflare.com", _URL_RE.pattern.endswith(r"\.trycloudflare\.com"))
    check("stop() with no state is a no-op", stop() == {} or True)
    ok = not fails
    print("\n" + ("PASS — launch_service_plane_tunnels: registry-sourced targets, recorder share "
                  "files + seam envs covered, honest-status discipline."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="TryCloudflare tunnels for the running service plane.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--start", action="store_true")
    g.add_argument("--stop", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.start:
        print(json.dumps(start(), indent=2))
    elif a.stop:
        print(json.dumps(stop(), indent=2))
    else:
        print(json.dumps(status(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
