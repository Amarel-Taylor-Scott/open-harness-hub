#!/usr/bin/env python3
"""scripts.mailbox_local_service — a VISIBLE inbox for the transactional emails the email PORT
renders (the "appropriate emulation" for email delivery in demos/recordings).

WHY: registration / account-setup / API-key generation are REAL (the identity service does them
for real). The one thing we cannot do in a demo is actually SEND email — so delivery is emulated:
`scripts/email_port.py` renders each message to `dist/email-outbox/` (honest, Mode Protocol: it
does NOT send). This service makes that outbox a navigable INBOX a user (or the recorder) opens,
reads the verification email, and clicks the verify link — so the registration→verify→active flow
is recordable end-to-end by REAL clicks, not by faking the page.

The verify click is FUNCTIONAL, not cosmetic: `/mailbox/verify` completes the real
`verify_identifier` onboarding step against the identity service (the account is named in the
email link). Demo-grade note: the link carries the account id; a cryptographic one-time token is
the production hardening (the email port + identity own that). Nothing here is served as truth.

Endpoints (read-only over the outbox + the one real verify call):
  GET /api/mailbox/messages           → JSON list of caught emails (newest first)
  GET /mailbox  /mailbox/             → the HTML inbox (the recordable surface)
  GET /mailbox/message?file=…         → one message, with the clickable verify button
  GET /mailbox/verify?realm=…&account=… → completes verify_identifier via identity → "Verified" page

Offline, stdlib-only. Binds 127.0.0.1 (OH_BIND_HOST=0.0.0.0 in containers). --self-test included.
"""
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
OUTBOX = REPO / "dist" / "email-outbox"
SERVICE_REGISTRY = REPO / "architecture" / "local_service_registry.json"
IDENTITY_REGISTRY = REPO / "architecture" / "identity_realm_registry.json"
SERVICE_ID = "mailbox_local_service"
DEFAULT_PORT = 9428
VERIFY_LINK_RE = re.compile(r"/mailbox/verify\?[^\s\"'<>]+")


def _port() -> int:
    try:
        for svc in json.loads(SERVICE_REGISTRY.read_text(encoding="utf-8"))["services"]:
            if svc.get("service_id") == SERVICE_ID and svc.get("port"):
                return int(svc["port"])
    except Exception:
        pass
    return DEFAULT_PORT


def _identity_base() -> str:
    if os.environ.get("AIDR_IDENTITY_BASE"):
        return os.environ["AIDR_IDENTITY_BASE"].rstrip("/")
    try:
        port = int(json.loads(IDENTITY_REGISTRY.read_text(encoding="utf-8"))["defaults"]["port"])
    except Exception:
        port = 9410
    return f"http://127.0.0.1:{port}"


def _parse_message(path: Path) -> dict:
    """Parse a rendered outbox .txt (To/From/Subject headers + body) into a message dict."""
    text = path.read_text(encoding="utf-8")
    headers, _, body = text.partition("\n\n")
    hd = {}
    for line in headers.splitlines():
        k, _, v = line.partition(":")
        hd[k.strip().lower()] = v.strip()
    verify = VERIFY_LINK_RE.search(text)
    return {"file": path.name, "to": hd.get("to", ""), "from": hd.get("from", ""),
            "subject": hd.get("subject", ""), "body": body.strip(),
            "verify_link": verify.group(0) if verify else None,
            "ts": int(path.stem.split("-")[0]) if path.stem.split("-")[0].isdigit() else 0}


def store_message(*, to: str, subject: str, body: str, realm: str = "mail", template: str = "msg",
                  sender: str = "", now: float = 0.0, outbox: Path | None = None) -> str:
    """Write a received email to the outbox in the format `_parse_message` reads. This lets the
    mailbox RECEIVE mail over HTTP (cloud: the identity service pushes here, because Fly per-app
    volumes can't share a filesystem) instead of only reading a co-located outbox (local dev)."""
    outbox = outbox or OUTBOX
    outbox.mkdir(parents=True, exist_ok=True)
    ts = int(now) if now else int(time.time())
    fname = f"{ts}-{re.sub(r'[^a-zA-Z0-9_-]', '_', realm)}-{re.sub(r'[^a-zA-Z0-9_-]', '_', template)}.txt"
    frm = sender or f"no-reply@{realm}"
    (outbox / fname).write_text(f"To: {to}\nFrom: {frm}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
    return fname


def list_messages(outbox: Path | None = None) -> list[dict]:
    outbox = outbox or OUTBOX  # resolve the (possibly reassigned) module global at CALL time
    if not outbox.is_dir():
        return []
    msgs = [_parse_message(p) for p in outbox.glob("*.txt")]
    msgs.sort(key=lambda m: m["ts"], reverse=True)
    return msgs


def complete_verify(realm: str, account: str, *, identity_base: str | None = None) -> tuple[bool, str]:
    """Complete the REAL verify_identifier onboarding step for the account (the functional verify
    behind the email link). Returns (ok, status). Honest: a failure is reported, never faked."""
    base = (identity_base or _identity_base()).rstrip("/")
    try:
        req = urllib.request.Request(
            f"{base}/api/identity/{realm}/onboard",
            data=json.dumps({"account_id": account, "step": "verify_identifier"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            out = json.loads(resp.read().decode("utf-8"))
            return True, str(out.get("status", "onboarding"))
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}"


# ---------------------------------------------------------------------------- HTML (the recordable UI)

_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:'Hanken Grotesk',system-ui,sans-serif;max-width:720px;margin:2rem auto;color:#1a1a2e}}
.msg{{border:1px solid #e0e0ee;border-radius:10px;padding:1rem 1.25rem;margin:.75rem 0}}
.msg a.verify,.btn{{display:inline-block;background:#ff6b35;color:#fff;padding:.55rem 1rem;border-radius:8px;
text-decoration:none;font-weight:600;margin-top:.5rem}} .sub{{font-weight:600}} .to{{color:#666;font-size:.9rem}}
h1{{font-size:1.4rem}} pre{{white-space:pre-wrap;color:#333}}</style></head><body>{body}</body></html>"""


def _inbox_html() -> str:
    msgs = list_messages()
    if not msgs:
        rows = "<p>No messages yet. Register an account and the verification email lands here.</p>"
    else:
        rows = "".join(
            f'<div class="msg"><div class="to">To: {html.escape(m["to"])}</div>'
            f'<div class="sub">{html.escape(m["subject"])}</div>'
            f'<a class="btn" href="/mailbox/message?file={html.escape(m["file"])}">Open</a></div>'
            for m in msgs)
    return _PAGE.format(title="Inbox", body=f"<h1>📬 Inbox</h1>{rows}")


def _message_html(file: str) -> str:
    p = OUTBOX / Path(file).name
    if not p.is_file():
        return _PAGE.format(title="Not found", body="<h1>Message not found</h1>")
    m = _parse_message(p)
    verify = (f'<a class="verify" href="{html.escape(m["verify_link"])}">Verify your email</a>'
              if m["verify_link"] else "")
    return _PAGE.format(title=m["subject"], body=(
        f'<h1>{html.escape(m["subject"])}</h1><div class="to">From: {html.escape(m["from"])}<br>'
        f'To: {html.escape(m["to"])}</div><pre>{html.escape(m["body"])}</pre>{verify}'
        f'<p><a href="/mailbox/">← Inbox</a></p>'))


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        path = parsed.path
        if path in ("/healthz", "/readyz"):
            return self._send(200, b'{"ok":true}', "application/json")
        if path == "/api/mailbox/messages":
            return self._send(200, json.dumps({"messages": list_messages()}).encode(), "application/json")
        if path in ("/mailbox", "/mailbox/"):
            return self._send(200, _inbox_html().encode(), "text/html; charset=utf-8")
        if path == "/mailbox/message":
            return self._send(200, _message_html((qs.get("file") or [""])[0]).encode(), "text/html; charset=utf-8")
        if path == "/mailbox/verify":
            realm, account = (qs.get("realm") or [""])[0], (qs.get("account") or [""])[0]
            ok, status = complete_verify(realm, account)
            body = (f'<h1>{"✅ Email verified" if ok else "⚠️ Could not verify"}</h1>'
                    f'<p>{"Your email is verified — account status: <b>" + html.escape(status) + "</b>." if ok else "The identity service was unreachable; nothing was faked."}</p>'
                    f'<p><a href="/mailbox/">← Inbox</a></p>')
            return self._send(200 if ok else 502, _PAGE.format(title="Verify", body=body).encode(),
                              "text/html; charset=utf-8")
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        # Ingest a rendered email over HTTP (the cloud delivery path: identity pushes here). The
        # message lands in this service's own outbox/volume and is then served like any caught mail.
        if urlparse(self.path).path != "/api/mailbox/ingest":
            return self._send(404, b'{"error":"not_found"}', "application/json")
        try:
            n = int(self.headers.get("content-length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            fname = store_message(to=str(data.get("to", "")), subject=str(data.get("subject", "")),
                                  body=str(data.get("body", "")), realm=str(data.get("realm", "mail")),
                                  template=str(data.get("template", "msg")), sender=str(data.get("from", "")),
                                  now=float(data.get("now", 0.0)))
            self._send(201, json.dumps({"stored": fname}).encode(), "application/json")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")

    def log_message(self, *a):  # quiet
        pass


def main() -> int:
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")
    port = _port()
    httpd = ThreadingHTTPServer((bind_host, port), _Handler)
    print(f"mailbox (transactional-email inbox) → http://{bind_host}:{port}/mailbox/  "
          f"(reads {OUTBOX.relative_to(REPO)}, verify completes verify_identifier — real)")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


def _self_test() -> int:
    import tempfile
    checks = []

    def ck(n, ok):
        checks.append((n, ok))
    global OUTBOX
    real = OUTBOX
    with tempfile.TemporaryDirectory() as tmp:
        OUTBOX = Path(tmp)
        ck("empty outbox → no messages (honest)", list_messages() == [])
        (OUTBOX / "1700000000-openharnesshub-verify_email.txt").write_text(
            "To: ada@example.com\nFrom: AI Done Right <no-reply@openharnesshub.local>\n"
            "Subject: Verify your email\n\nWelcome! Verification link: "
            "/mailbox/verify?realm=openharnesshub&account=acct_abcdef123456\n", encoding="utf-8")
        msgs = list_messages()
        ck("caught email parsed (to/subject/verify link)", len(msgs) == 1
           and msgs[0]["to"] == "ada@example.com" and msgs[0]["subject"] == "Verify your email"
           and msgs[0]["verify_link"] == "/mailbox/verify?realm=openharnesshub&account=acct_abcdef123456")
        ck("inbox HTML renders the message + an Open button", "Inbox" in _inbox_html()
           and "Verify your email" in _inbox_html())
        ck("message HTML renders a clickable Verify button to the real link",
           'class="verify"' in _message_html(msgs[0]["file"])
           and "/mailbox/verify?realm=openharnesshub" in _message_html(msgs[0]["file"]))
        # the cross-app ingest path: cloud identity pushes mail here over HTTP (Fly per-app volumes
        # can't share a filesystem), so store_message() must round-trip into the same inbox a local
        # co-located outbox would. This is what POST /api/mailbox/ingest writes.
        rt = store_message(to="grace@example.com", subject="Verify your email",
                           body="Click: /mailbox/verify?realm=baltor&account=acct_999",
                           realm="baltor", template="verify_email", now=1700000002)
        rtmsgs = list_messages()
        ck("store_message round-trips into the inbox (cross-app HTTP ingest)",
           rt.endswith(".txt") and "baltor" in rt and any(
               m["to"] == "grace@example.com" and m["subject"] == "Verify your email"
               and m["verify_link"] == "/mailbox/verify?realm=baltor&account=acct_999"
               for m in rtmsgs))
        ok, status = complete_verify("openharnesshub", "acct_x", identity_base="http://127.0.0.1:1")
        ck("verify against an unreachable identity is HONEST (failed, not faked)", ok is False)
    OUTBOX = real
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"mailbox: {len(checks) - len(failed)}/{len(checks)} — a visible inbox over the email "
            "outbox; the verify click completes the REAL verify_identifier step (never faked offline).")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_test() if "--self-test" in sys.argv else main())
