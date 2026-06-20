#!/usr/bin/env python3
"""scripts.browser_capture — drive the INSTALLED Chrome via the DevTools Protocol (stdlib-only; no pip/npm) to walk a
page, enumerate + click every clickable, screenshot, and save rendered HTML.

Why CDP-over-stdlib: Python 3.14 here has no pip/ensurepip (can't install playwright/selenium), but Chrome exposes a
CDP endpoint on --remote-debugging-port. We speak just three CDP methods (Page.navigate, Page.captureScreenshot,
Runtime.evaluate) over a minimal stdlib WebSocket client — no third-party deps, no second browser download.

For each URL it: navigates, waits, screenshots, saves the rendered DOM, enumerates EVERY clickable
(a / button / [role=button] / [onclick] / input[type=submit|button]) with text+href+resolution, then CLICKS each
in-page anchor and screenshots the resulting (scrolled) view. Artifacts → <out>/<label>/.

CLI: python3 scripts/browser_capture.py <out_dir> <label>=<url> [<label>=<url> ...]
"""
from __future__ import annotations

import base64, json, os, shutil, socket, subprocess, sys, time, urllib.request
from pathlib import Path

_CHROME = next((shutil.which(c) for c in ("google-chrome-stable", "google-chrome", "chromium") if shutil.which(c)), None)


class CDP:
    """Minimal CDP client over a hand-rolled stdlib WebSocket (text frames, client-masked, extended lengths)."""
    def __init__(self, port: int):
        self.port = port; self._id = 0; self._buf = b""
        # reuse Chrome's existing page target (GET /json; /json/new needs PUT in recent Chrome)
        targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=10).read())
        ws = next(t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl"))
        self.ws_url = ws["webSocketDebuggerUrl"]; self.target = ws["id"]
        host, _, rest = self.ws_url.split("ws://", 1)[1].partition("/")
        h, p = host.split(":"); self.sock = socket.create_connection((h, int(p)), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /{rest} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        while b"\r\n\r\n" not in self._buf:
            self._buf += self.sock.recv(4096)
        self._buf = self._buf.split(b"\r\n\r\n", 1)[1]

    def _send(self, payload: bytes):
        mask = os.urandom(4); n = len(payload)
        hdr = bytearray([0x81])
        if n < 126: hdr.append(0x80 | n)
        elif n < 65536: hdr += bytes([0x80 | 126]) + n.to_bytes(2, "big")
        else: hdr += bytes([0x80 | 127]) + n.to_bytes(8, "big")
        self.sock.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _recv_frame(self) -> bytes:
        def need(n):
            while len(self._buf) < n: self._buf += self.sock.recv(65536)
        need(2); b1 = self._buf[1] & 0x7F; off = 2
        if b1 == 126: need(4); ln = int.from_bytes(self._buf[2:4], "big"); off = 4
        elif b1 == 127: need(10); ln = int.from_bytes(self._buf[2:10], "big"); off = 10
        else: ln = b1
        need(off + ln); data = self._buf[off:off + ln]; self._buf = self._buf[off + ln:]; return data

    def call(self, method: str, params: dict | None = None, timeout: float = 45.0) -> dict:
        self._id += 1; mid = self._id
        self._send(json.dumps({"id": mid, "method": method, "params": params or {}}).encode())
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = json.loads(self._recv_frame().decode("utf-8", "ignore"))
            if msg.get("id") == mid: return msg.get("result", {})
        raise TimeoutError(method)

    def js(self, expr: str):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        return (r.get("result") or {}).get("value")


def capture(cdp: CDP, url: str, outdir: Path, anchors_dir: Path) -> dict:
    cdp.call("Page.navigate", {"url": url}); time.sleep(2.0)
    code = cdp.js("({c: (window.performance.getEntriesByType('navigation')[0]||{}).responseStatus || document.readyState})")
    shot = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
    if shot: (outdir / "page-desktop.png").write_bytes(base64.b64decode(shot))
    html = cdp.js("document.documentElement.outerHTML") or ""
    (outdir / "page.html").write_text(html, encoding="utf-8")
    clickables = cdp.js("""
      Array.from(document.querySelectorAll('a,button,[role=button],[onclick],input[type=submit],input[type=button]'))
        .map(e=>({tag:e.tagName.toLowerCase(), text:(e.innerText||e.value||'').trim().slice(0,60),
                  href:e.getAttribute('href')||null,
                  kind:(e.getAttribute('href')||'').startsWith('#')?'in-page-anchor':
                       (e.getAttribute('href')||'').startsWith('../')?'cross-link':
                       (e.getAttribute('href')||'').startsWith('http')?'external':'other'}))""") or []
    # CLICK each in-page anchor + screenshot the resulting scrolled view
    clicked = []
    for c in clickables:
        if c["kind"] == "in-page-anchor" and c["href"]:
            aid = c["href"][1:]
            present = cdp.js(f"!!document.getElementById({json.dumps(aid)})")
            cdp.js(f"location.hash={json.dumps(c['href'])}; void 0"); time.sleep(0.4)
            s = cdp.call("Page.captureScreenshot", {"format": "png"}).get("data")
            png = f"anchor-{aid}.png"
            if s: (anchors_dir / png).write_bytes(base64.b64decode(s))
            clicked.append({"anchor": c["href"], "id_present": bool(present), "text": c["text"], "screenshot": png})
    return {"url": url, "html_bytes": len(html), "screenshot": "page-desktop.png",
            "clickables": clickables, "clicked_anchors": clicked,
            "clickable_count": len(clickables),
            "by_kind": {k: sum(1 for c in clickables if c["kind"] == k) for k in ("in-page-anchor","cross-link","external","other")}}


def main(argv: list[str]) -> int:
    out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
    targets = dict(a.split("=", 1) for a in argv[2:])
    port = 9355
    proc = subprocess.Popen([_CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                             f"--remote-debugging-port={port}", "--window-size=1280,1200", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try: urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2); break
            except Exception: time.sleep(0.5)
        cdp = CDP(port); cdp.call("Page.enable"); report = {}
        for label, url in targets.items():
            d = out / label; (d / "anchors").mkdir(parents=True, exist_ok=True)
            try:
                report[label] = capture(cdp, url, d, d / "anchors")
                r = report[label]
                print(f"  {label}: {r['clickable_count']} clickables {r['by_kind']} · {len(r['clicked_anchors'])} anchors clicked · html {r['html_bytes']}B")
            except Exception as e:
                report[label] = {"url": url, "error": f"{type(e).__name__}: {e}"}
                print(f"  {label}: ERROR {report[label]['error']}")
        (out / "capture.json").write_text(json.dumps(report, indent=2))
        print(f"wrote {out}/capture.json")
        return 0
    finally:
        proc.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python3 scripts/browser_capture.py <out_dir> <label>=<url> ..."); raise SystemExit(2)
    raise SystemExit(main(sys.argv))
