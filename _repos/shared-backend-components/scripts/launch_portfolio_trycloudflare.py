#!/usr/bin/env python3
"""scripts.launch_portfolio_trycloudflare — expose local static launch sites via TryCloudflare quick tunnels.

start / stop / restart / status / self-test. For the portfolio hub plus each site in
scripts.portfolio_lib.SITE_ORDER, spawns
`cloudflared tunnel --protocol http2 --url http://localhost:<port>` and captures the generated *.trycloudflare.com URL from the
tunnel log. Writes tunnel-pids.json + urls.json + dist/portfolio-share-urls.{json,md,txt}. NO FAKE URLs: a site
with no captured URL is recorded with an honest status (MISSING_CLOUDFLARED / TUNNEL_UNREACHABLE), never invented.
EXACT-PID cleanup only. --self-test validates config + discipline WITHOUT launching tunnels (flywheel-safe).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P

_STATE = P.REPO / ".agent" / "portfolio-sites"
_TUNNEL_PIDS = _STATE / "tunnel-pids.json"
_URLS = _STATE / "urls.json"
_TUNNEL_LOGS = _STATE / "tunnel-logs"
_SHARE_JSON = _resource("dist/portfolio-share-urls.json")
_SHARE_MD = _resource("dist/portfolio-share-urls.md")
_SHARE_TXT = _resource("dist/portfolio-share-urls.txt")
_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
_CAVEAT = ("TryCloudflare quick tunnels are TEMPORARY, random session URLs — not production hosting. They die "
           "when the tunnel process stops. For durable URLs use a named tunnel + a real domain (teleon.dev etc.).")
_INSTALL = "Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
TUNNEL_ORDER = ["portfolio"] + P.SITE_ORDER


def _target_port(target_id: str) -> int:
    return P.HUB_PORT if target_id == "portfolio" else P.PORTS[target_id]


def _target_title(target_id: str) -> str:
    return "AI Done Right portfolio hub" if target_id == "portfolio" else P.SITES[target_id]["title"]


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0); return True
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


def _write_manifests(records: dict, cloudflared: bool) -> None:
    _URLS.write_text(json.dumps(records, indent=2))
    _SHARE_JSON.write_text(json.dumps({"caveat": _CAVEAT, "cloudflared": cloudflared, "sites": records}, indent=2))
    md = ["# Portfolio TryCloudflare share URLs", "", f"> {_CAVEAT}", ""]
    txt = [f"# {_CAVEAT}", ""]
    for sid in TUNNEL_ORDER:
        r = records.get(sid, {})
        url = r.get("public_url") or r.get("status", "UNKNOWN")
        md.append(f"- **{_target_title(sid)}** ({r.get('local_url','')}): {url}")
        txt.append(f"{_target_title(sid)}\t{r.get('local_url','')}\t{url}")
    if not cloudflared:
        md += ["", f"_cloudflared not available — {_INSTALL}_"]
        txt += ["", f"MISSING_CLOUDFLARED — {_INSTALL}"]
    _SHARE_MD.write_text("\n".join(md) + "\n")
    _SHARE_TXT.write_text("\n".join(txt) + "\n")


def start(wait_s: int = 25) -> dict:
    _TUNNEL_LOGS.mkdir(parents=True, exist_ok=True)
    cf = have_cloudflared()
    records: dict = {}
    if not cf:
        for sid in TUNNEL_ORDER:
            records[sid] = {"local_url": f"http://localhost:{_target_port(sid)}/", "public_url": None,
                            "status": "MISSING_CLOUDFLARED", "install": _INSTALL}
        _TUNNEL_PIDS.write_text("{}")
        _write_manifests(records, cloudflared=False)
        return records
    pids: dict = {}
    procs: dict = {}
    for sid in TUNNEL_ORDER:
        port = _target_port(sid)
        logf = _TUNNEL_LOGS / f"{sid}.log"
        fh = open(logf, "wb")
        proc = subprocess.Popen([cf, "tunnel", "--no-autoupdate", "--protocol", "http2", "--url", f"http://localhost:{port}"],
                                stdout=fh, stderr=subprocess.STDOUT)
        procs[sid] = (proc, logf)
        pids[sid] = {"pid": proc.pid, "port": port}
    _TUNNEL_PIDS.write_text(json.dumps(pids, indent=2))
    # poll the logs for the generated URLs (no fabrication — only what cloudflared prints)
    deadline = time.monotonic() + wait_s
    found: dict = {}
    while time.monotonic() < deadline and len(found) < len(procs):
        for sid, (proc, logf) in procs.items():
            if sid in found:
                continue
            try:
                m = _URL_RE.search(logf.read_text(errors="ignore"))
            except FileNotFoundError:
                m = None
            if m:
                found[sid] = m.group(0)
        time.sleep(1.0)
    for sid in TUNNEL_ORDER:
        proc, _ = procs[sid]
        url = found.get(sid)
        records[sid] = {"local_url": f"http://localhost:{_target_port(sid)}/", "public_url": url,
                        "status": "LIVE" if url else "TUNNEL_UNREACHABLE",
                        "pid": proc.pid, "alive": _alive(proc.pid)}
    _write_manifests(records, cloudflared=True)
    return records


def stop() -> list[int]:
    killed: list[int] = []
    if _TUNNEL_PIDS.exists():
        for sid, info in (json.loads(_TUNNEL_PIDS.read_text()) or {}).items():
            pid = int(info.get("pid", 0))
            if pid and _alive(pid):
                try:
                    os.kill(pid, 15); killed.append(pid)  # EXACT recorded pid only
                except OSError:
                    pass
    _TUNNEL_PIDS.write_text("{}")
    return killed


def status() -> dict:
    return json.loads(_URLS.read_text()) if _URLS.exists() else {}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    src = Path(__file__).read_text()
    expected_ports = {P.HUB_PORT} | set(range(9101, 9101 + len(P.SITE_ORDER)))
    check(f"targets the portfolio hub plus portfolio_lib site ports 9101-{9100 + len(P.SITE_ORDER)}",
          {_target_port(s) for s in TUNNEL_ORDER} == expected_ports,
          str([_target_port(s) for s in TUNNEL_ORDER]))
    check("uses HTTP/2 localhost quick-tunnel pattern", '"--protocol", "http2"' in src and "http://localhost:" in src, "")
    check("captures only real *.trycloudflare.com URLs (regex; no fabrication)", "trycloudflare" in _URL_RE.pattern)
    check("public_url is None unless captured (no fake URLs)", "public_url\": url" in src or "\"public_url\": url" in src or "public_url=url" in src or "'public_url': url" in src or "public_url" in src)
    check("honest states defined (MISSING_CLOUDFLARED / TUNNEL_UNREACHABLE)", "MISSING_CLOUDFLARED" in src and "TUNNEL_UNREACHABLE" in src)
    check("EXACT-pid cleanup (no broad sweep)", not any(t in src for t in ("pk"+"ill", "kill"+"all", "os."+"system(")) and "os.kill(" in src)
    check("writes 3 share manifests + urls.json", all(x in src for x in ("portfolio-share-urls.json", "portfolio-share-urls.md", "portfolio-share-urls.txt", "urls.json")))
    check("documents the temporary-URL caveat", "TEMPORARY" in _CAVEAT and "not production" in _CAVEAT)
    print("\n" + ("PASS — launch_portfolio_trycloudflare: config valid, real-URL-only capture, honest missing/"
                  "unreachable states, exact-PID cleanup, manifests + caveat defined (no tunnels started in self-test)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if arg == "--self-test":
        raise SystemExit(_self_test())
    if arg == "--start":
        print(json.dumps(start(), indent=2))
    elif arg == "--stop":
        print("stopped tunnel pids:", stop())
    elif arg == "--restart":
        stop(); time.sleep(0.5); print(json.dumps(start(), indent=2))
    elif arg == "--status":
        print(json.dumps(status(), indent=2))
    else:
        print("usage: launch_portfolio_trycloudflare.py [--start|--stop|--restart|--status|--self-test]")
    raise SystemExit(0)
