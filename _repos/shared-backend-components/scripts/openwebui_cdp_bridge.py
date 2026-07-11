#!/usr/bin/env python3
"""scripts.openwebui_cdp_bridge — call the hosted OpenWebUI Gemma-4 lane THROUGH a real logged-in browser,
bypassing Cloudflare. The OpenWebUI instance (ui.iamretarded.net) sits behind Cloudflare's JS challenge, which
blocks the harness's non-browser requests (403 "Just a moment...") even with a valid token. The fix is not a
custom browser — it is to drive the user's ALREADY-LOGGED-IN Chrome (running with --remote-debugging-port) via
the Chrome DevTools Protocol and make the chat-completion request from INSIDE the page (`fetch`), which inherits
the authenticated session AND Cloudflare clearance. Proven live: reload the tab, wait for the browser to
auto-solve the challenge, then the same-origin fetch returns 200.

Pure stdlib (a ~60-line CDP-over-websocket client — no pip install). The token comes from the page's own
localStorage. serves_truth=false (a model call, not truth). NEVER touches the local Ollama gemma4 (overheat).

    python3 scripts/openwebui_cdp_bridge.py --self-test        # offline: the websocket framing round-trips
    python3 scripts/openwebui_cdp_bridge.py --probe            # live: one Gemma call through the browser
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import base64  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import socket  # noqa: E402
import struct  # noqa: E402
import time  # noqa: E402
from typing import Any, Optional  # noqa: E402
from urllib.parse import urlparse  # noqa: E402
from urllib.request import urlopen  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_CDP_HOST = os.environ.get("OH_CDP_HOST", "http://localhost:9222")
_OWUI_ORIGIN = os.environ.get("OPENWEBUI_ORIGIN", "https://ui.iamretarded.net")
_DEFAULT_MODEL = os.environ.get("OH_GEMMA_MODEL", "gemma-4-coding")


# ── minimal stdlib websocket client (RFC 6455 text frames; client masks, server does not) ────────────────────
def _recvn(s: socket.socket, n: int) -> bytes:
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            break
        b += c
    return b


def _encode_client_frame(data: str) -> bytes:
    """A masked client text frame (FIN=1, opcode=1)."""
    payload = data.encode("utf-8")
    header = bytearray([0x81])
    n = len(payload)
    mask = os.urandom(4)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header.append(0x80 | 126)
        header += struct.pack(">H", n)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", n)
    header += mask
    return bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload))


def _decode_frame(raw: bytes) -> str:
    """Decode a websocket text frame (masked or not) — used by the self-test to round-trip _encode_client_frame."""
    b2 = raw[1]
    masked = bool(b2 & 0x80)
    ln = b2 & 0x7f
    off = 2
    if ln == 126:
        ln = struct.unpack(">H", raw[off:off + 2])[0]
        off += 2
    elif ln == 127:
        ln = struct.unpack(">Q", raw[off:off + 8])[0]
        off += 8
    if masked:
        mask = raw[off:off + 4]
        off += 4
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(raw[off:off + ln]))
    else:
        payload = raw[off:off + ln]
    return payload.decode("utf-8", "replace")


def _ws_connect(url: str, timeout: int = 20) -> socket.socket:
    u = urlparse(url)
    s = socket.create_connection((u.hostname, u.port or 80), timeout=timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    path = u.path + (("?" + u.query) if u.query else "")
    s.sendall((f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = s.recv(4096)
        if not chunk:
            break
        resp += chunk
    return s


def _ws_send(s: socket.socket, data: str) -> None:
    s.sendall(_encode_client_frame(data))


def _ws_recv_text(s: socket.socket) -> str:
    b1 = _recvn(s, 1)
    b2 = _recvn(s, 1)
    if not b1 or not b2:
        return ""
    ln = b2[0] & 0x7f
    if ln == 126:
        ln = struct.unpack(">H", _recvn(s, 2))[0]
    elif ln == 127:
        ln = struct.unpack(">Q", _recvn(s, 8))[0]
    return _recvn(s, ln).decode("utf-8", "replace")


# ── CDP: find the logged-in tab, clear Cloudflare, evaluate an in-page fetch ──────────────────────────────────
def _find_owui_tab() -> Optional[dict[str, Any]]:
    try:
        tabs = json.load(urlopen(f"{_CDP_HOST}/json", timeout=5))
    except Exception:  # noqa: BLE001
        return None
    origin = _OWUI_ORIGIN.replace("https://", "").replace("http://", "")
    return next((t for t in tabs if origin in t.get("url", "") and "/auth" not in t.get("url", "")), None)


def _evaluate(s: socket.socket, expr: str, mid: int, *, timeout_frames: int = 60) -> Any:
    _ws_send(s, json.dumps({"id": mid, "method": "Runtime.evaluate",
                            "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
    for _ in range(timeout_frames):
        msg = _ws_recv_text(s)
        if not msg:
            return None
        d = json.loads(msg)
        if d.get("id") == mid:
            return d.get("result", {}).get("result", {}).get("value")
    return None


def _ensure_cleared(s: socket.socket, *, max_wait_s: int = 40) -> bool:
    """If the tab is on a Cloudflare challenge, reload and poll until the browser auto-solves it."""
    tab = _find_owui_tab()
    if tab and "__cf_chl" not in tab.get("url", ""):
        return True
    _ws_send(s, json.dumps({"id": 900, "method": "Page.navigate", "params": {"url": _OWUI_ORIGIN + "/"}}))
    _ws_recv_text(s)
    waited = 0
    while waited < max_wait_s:
        time.sleep(4)
        waited += 4
        u = (_find_owui_tab() or {}).get("url", "")
        if u and "__cf_chl" not in u and "/auth" not in u:
            return True
    return False


def cdp_chat(model: str, system: str, user: str, *, timeout: int = 90) -> dict[str, Any]:
    """One Gemma chat completion through the logged-in browser. Returns {ok, text, provider, error}."""
    tab = _find_owui_tab()
    if not tab or not tab.get("webSocketDebuggerUrl"):
        return {"ok": False, "error": f"no logged-in OpenWebUI tab on {_CDP_HOST} (open {_OWUI_ORIGIN} in Chrome "
                                      "with --remote-debugging-port=9222 and log in)", **BOUNDARY}
    try:
        s = _ws_connect(tab["webSocketDebuggerUrl"], timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"cdp connect failed: {exc}", **BOUNDARY}
    try:
        if not _ensure_cleared(s):
            return {"ok": False, "error": "cloudflare challenge did not clear", **BOUNDARY}
        # rebuild the connection to the (possibly navigated) tab
        s.close()
        tab = _find_owui_tab()
        s = _ws_connect(tab["webSocketDebuggerUrl"], timeout=timeout)
        body = json.dumps({"model": model, "messages": [{"role": "system", "content": system},
                                                        {"role": "user", "content": user}], "stream": False})
        expr = ("(async()=>{try{const r=await fetch('/api/chat/completions',{method:'POST',headers:"
                "{'Content-Type':'application/json','Authorization':'Bearer '+localStorage.token},"
                f"body:{json.dumps(body)}}});const t=await r.text();return r.status+'::'+t;}}"
                "catch(e){return 'ERR::'+e.toString();}})()")
        raw = _evaluate(s, expr, 1, timeout_frames=timeout)
        if not raw:
            return {"ok": False, "error": "no response from the page", **BOUNDARY}
        status, _, payload = str(raw).partition("::")
        if status != "200":
            return {"ok": False, "error": f"http {status}: {payload[:120]}", **BOUNDARY}
        data = json.loads(payload)
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return {"ok": True, "text": text, "provider": "openwebui_cdp", "usage": data.get("usage", {}), **BOUNDARY}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"cdp chat failed: {str(exc)[:120]}", **BOUNDARY}
    finally:
        try:
            s.close()
        except Exception:  # noqa: BLE001
            pass


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # the websocket framing round-trips (encode client frame -> decode)
    for text in ("hi", "x" * 200, json.dumps({"id": 1, "method": "Runtime.evaluate"}), "ünïcodé ✓" * 30):
        frame = _encode_client_frame(text)
        checks.append((f"ws frame round-trips ({len(text)} chars)", _decode_frame(frame) == text))
    # a >64KB payload uses the 8-byte length path
    big = "z" * 70000
    checks.append(("ws frame round-trips a >64KB payload", _decode_frame(_encode_client_frame(big)) == big))
    # cdp_chat with no browser returns a clean error, never a crash / fabrication
    old = globals()["_find_owui_tab"]
    try:
        globals()["_find_owui_tab"] = lambda: None
        r = cdp_chat("gemma-4-coding", "s", "u")
        checks.append(("cdp_chat with no tab returns a recorded error, never fabricates",
                       r["ok"] is False and "no logged-in" in r["error"] and r["serves_truth"] is False))
    finally:
        globals()["_find_owui_tab"] = old
    checks.append(("the CDP host + origin are configurable via env",
                   _CDP_HOST.startswith("http") and _OWUI_ORIGIN.startswith("http")))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - openwebui_cdp_bridge: a pure-stdlib CDP-over-websocket client drives the logged-in Chrome "
          "to call Gemma via an in-page fetch (bypassing Cloudflare); framing round-trips incl. >64KB; missing "
          "browser -> recorded error never fabricated. Never touches local gemma4. serves_truth=false.")
    return 0


def _probe(model: str) -> int:
    r = cdp_chat(model, "Reply with one word.", "Say OK.")
    print(json.dumps({k: r.get(k) for k in ("ok", "text", "provider", "error", "usage")}, indent=2))
    return 0 if r.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--probe", action="store_true", help="live: one Gemma call through the browser")
    ap.add_argument("--model", default=_DEFAULT_MODEL)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.probe:
        return _probe(args.model)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
