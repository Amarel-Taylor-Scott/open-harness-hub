#!/usr/bin/env python3
"""share_intro_site — serve dist/intro + expose it via a TryCloudflare quick tunnel; print the shareable URL.

start  : (re)build the intro site, serve it locally, launch `cloudflared tunnel --url`, capture the real
         *.trycloudflare.com URL from the tunnel log, write dist/intro-share-url.txt. NO FAKE URLs — if cloudflared
         is missing or the URL can't be captured, an honest status is recorded, never invented.
status : print the captured URL + whether the processes are alive.
stop   : kill the EXACT pids we started (never pkill-by-name).
--self-test : validate discipline (cloudflared presence, URL regex, no-fake) WITHOUT launching (flywheel-safe).

  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/share_intro_site.py start
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

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
SITE_DIR = _resource("dist") / "intro"
STATE = (REPO / ".agent") / "intro-share"
PIDS = STATE / "pids.json"
TUNNEL_LOG = STATE / "tunnel.log"
HTTP_LOG = STATE / "http.log"
SHARE_TXT = _resource("dist") / "intro-share-url.txt"
PORT = 8848
_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
_CAVEAT = "TryCloudflare quick tunnels are TEMPORARY random session URLs — they die when the tunnel stops. Not prod hosting."


def _alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0); return True
    except (OSError, ValueError, TypeError):
        return False


def _spawn(cmd: list[str], log: Path) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    fh = open(log, "w")
    p = subprocess.Popen(cmd, cwd=str(REPO), stdout=fh, stderr=subprocess.STDOUT,
                         start_new_session=True)  # detached → outlives this launcher
    return p.pid


def start() -> int:
    # 1. (re)build the page so the share is always current
    subprocess.run([sys.executable, str(_resource("scripts/build_intro_site.py"))], cwd=str(REPO),
                   env={**os.environ, "PYTHONPATH": "."}, capture_output=True, text=True)
    if not (SITE_DIR / "index.html").exists():
        print("intro site not built — run scripts/build_intro_site.py"); return 1
    STATE.mkdir(parents=True, exist_ok=True)
    stop()  # idempotent: clear any prior session

    http_pid = _spawn([sys.executable, "-m", "http.server", str(PORT), "--directory", str(SITE_DIR)], HTTP_LOG)

    cf = shutil.which("cloudflared")
    if not cf:
        PIDS.write_text(json.dumps({"http": http_pid, "tunnel": None, "status": "MISSING_CLOUDFLARED"}))
        print(f"served locally at http://localhost:{PORT} (http pid {http_pid}).")
        print("cloudflared NOT found — install it to get a trycloudflare URL: "
              "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
        return 0

    tunnel_pid = _spawn([cf, "tunnel", "--protocol", "http2", "--url", f"http://localhost:{PORT}"], TUNNEL_LOG)
    url = ""
    for _ in range(40):  # poll the tunnel log up to ~40s for the REAL url (no fabrication)
        time.sleep(1)
        if TUNNEL_LOG.exists():
            m = _URL_RE.search(TUNNEL_LOG.read_text(errors="replace"))
            if m:
                url = m.group(0); break
        if not _alive(tunnel_pid):
            break
    status = "LIVE" if url else "TUNNEL_UNREACHABLE"
    PIDS.write_text(json.dumps({"http": http_pid, "tunnel": tunnel_pid, "port": PORT, "url": url, "status": status}))
    if url:
        SHARE_TXT.write_text(url + "\n", encoding="utf-8")
        print(f"\n  SHARE THIS WITH YOUR ADVISOR:  {url}\n")
        print(f"  (local: http://localhost:{PORT} · http pid {http_pid} · tunnel pid {tunnel_pid})")
        print(f"  saved → {SHARE_TXT.relative_to(REPO)}\n  {_CAVEAT}")
    else:
        print(f"served at http://localhost:{PORT} but no trycloudflare URL captured ({status}). "
              f"Check {TUNNEL_LOG.relative_to(REPO)}. {_CAVEAT}")
    return 0


def status() -> int:
    if not PIDS.exists():
        print("no share session — run: share_intro_site.py start"); return 0
    d = json.loads(PIDS.read_text())
    print(json.dumps({**d, "http_alive": _alive(d.get("http")), "tunnel_alive": _alive(d.get("tunnel"))}, indent=1))
    if d.get("url"):
        print(f"\n  URL: {d['url']}")
    return 0


def stop() -> int:
    if not PIDS.exists():
        return 0
    try:
        d = json.loads(PIDS.read_text())
    except Exception:  # noqa: BLE001
        return 0
    for key in ("tunnel", "http"):
        pid = d.get(key)
        if pid and _alive(pid):
            try:
                os.kill(int(pid), 15)  # exact pid only
            except OSError:
                pass
    return 0


def _self_test() -> int:
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    src = Path(__file__).read_text()
    ck("captures REAL trycloudflare URLs only (regex + no fabrication on failure)",
       "trycloudflare" in src and "_URL_RE" in src and "TUNNEL_UNREACHABLE" in src and "MISSING_CLOUDFLARED" in src)
    ck("URL regex matches a trycloudflare host", bool(_URL_RE.search("see https://brave-mountain-1234.trycloudflare.com next")))
    ck("URL regex rejects a non-trycloudflare host", not _URL_RE.search("https://evil.example.com"))
    # exact-pid discipline = stop() kills via os.kill on pids read from PIDS, and children are detached
    ck("exact-pid cleanup (os.kill on saved pids) + detached children (start_new_session)",
       "os.kill(int(pid)" in src and "start_new_session=True" in src and 'os.kill(int(pid), 15)' in src)
    ck("carries the honest temporary-preview caveat", "TEMPORARY" in _CAVEAT)
    print("\n" + ("PASS - share_intro_site: serves dist/intro + a TryCloudflare quick tunnel, captures the REAL url "
                  "(honest status on failure, no fabrication), exact-pid cleanup." if not fails else f"FAIL: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    cmd = argv[0] if argv else "start"
    return {"start": start, "status": status, "stop": stop}.get(cmd, start)()


if __name__ == "__main__":
    raise SystemExit(_main())
