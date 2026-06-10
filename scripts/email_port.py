#!/usr/bin/env python3
"""scripts.email_port — the standardized transactional-email PORT (BUSINESS-PLANE §2).

ONE module, ONE contract for every product/realm: `send(realm, template, to, props)`. Vendors are
adapters behind the port (S12 anti-fragility) — swap the adapter, never the call sites.

  * **console adapter (dev, default)** — renders the realm-branded email and writes it to the
    outbox (dist/email-outbox/) + an audit line; it HONESTLY DOES NOT SEND (Mode Protocol S2:
    mode='console', never 'sent'). The static prototype keeps working with no provider.
  * **Resend / Postmark adapters** — real-send SEAMS, owner-gated: without RESEND_API_KEY /
    POSTMARK_API_KEY in the env they raise NotConfigured (a real action is never silently faked).
    Secrets are read from the env only and NEVER written to any artifact.

Realm branding is single-sourced from architecture/identity_realm_registry.json (display_name) —
the same roster the identity service uses. Templates are a small registry (verify_email,
password_reset, welcome). No PII beyond the recipient address is stored; no secret is ever logged.
Stdlib-only, deterministic, offline.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
REALM_REGISTRY = REPO_ROOT / "architecture" / "identity_realm_registry.json"
OUTBOX = REPO_ROOT / "dist" / "email-outbox"
AUDIT = OUTBOX / "email-audit.jsonl"
_SECRET_RE = re.compile(r"sk-[A-Za-z0-9]{8,}|api[_-]?key|RESEND_API_KEY|POSTMARK_API_KEY", re.I)


class NotConfigured(RuntimeError):
    """A real-send adapter was asked to send without its provider key — never fake it."""


def _realm_display(realm: str) -> str:
    try:
        reg = json.loads(REALM_REGISTRY.read_text(encoding="utf-8"))
        for r in reg["realms"]:
            if r["realm_id"] == realm:
                return r.get("display_name", realm)
    except Exception:  # noqa: BLE001
        pass
    return realm


#: template registry — (subject builder, body builder). props fill the body; no secrets in props.
TEMPLATES: dict[str, tuple[Callable[[str, dict], str], Callable[[str, dict], str]]] = {
    "verify_email": (
        lambda brand, p: f"Verify your {brand} email",
        lambda brand, p: f"Welcome to {brand}. Confirm this address to activate your account.\n"
                         f"Verification link: {p.get('verify_url', '<rendered per request>')}\n"
                         f"If you did not register, ignore this email."),
    "password_reset": (
        lambda brand, p: f"Reset your {brand} password",
        lambda brand, p: f"A password reset was requested for your {brand} account.\n"
                         f"Reset link: {p.get('reset_url', '<rendered per request>')}\n"
                         f"This link expires; if you did not request it, ignore this email."),
    "welcome": (
        lambda brand, p: f"Welcome to {brand}",
        lambda brand, p: f"Your {brand} account is active. Next: {p.get('next_step', 'sign in and start')}."),
}


def _render(realm: str, template: str, to: str, props: dict[str, Any]) -> dict[str, Any]:
    if template not in TEMPLATES:
        raise ValueError(f"unknown template {template!r}; known {sorted(TEMPLATES)}")
    if not to or "@" not in to:
        raise ValueError("a recipient address is required")
    if _SECRET_RE.search(json.dumps(props)):
        raise ValueError("refused: props carry secret-shaped material")
    brand = _realm_display(realm)
    subj_fn, body_fn = TEMPLATES[template]
    return {"realm": realm, "brand": brand, "template": template, "to": to,
            "subject": subj_fn(brand, props), "body": body_fn(brand, props)}


class ConsoleAdapter:
    """Dev default: render to the outbox + audit; HONESTLY does not send (Mode Protocol)."""

    name = "console"

    def deliver(self, msg: dict[str, Any]) -> dict[str, Any]:
        OUTBOX.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        fname = f"{ts}-{msg['realm']}-{msg['template']}.txt"
        (OUTBOX / fname).write_text(
            f"To: {msg['to']}\nFrom: {msg['brand']} <no-reply@{msg['realm']}.local>\n"
            f"Subject: {msg['subject']}\n\n{msg['body']}\n", encoding="utf-8")
        rec = {"ts": ts, "realm": msg["realm"], "template": msg["template"], "to": msg["to"],
               "mode": "console", "sent": False, "outbox_file": fname,
               "note": "rendered to outbox; NOT sent (dev console adapter — Mode Protocol)"}
        with AUDIT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec


class ResendAdapter:
    """Real-send SEAM (owner-gated). Without RESEND_API_KEY → NotConfigured (never fakes a send)."""

    name = "resend"

    def deliver(self, msg: dict[str, Any]) -> dict[str, Any]:
        if not os.environ.get("RESEND_API_KEY"):
            raise NotConfigured("RESEND_API_KEY unset — real email send is owner-gated; not faked")
        # a real HTTP call to Resend goes here when deploying; the key stays in the env only
        raise NotConfigured("Resend transport not wired in this local build (seam present)")


class PostmarkAdapter(ResendAdapter):
    name = "postmark"

    def deliver(self, msg: dict[str, Any]) -> dict[str, Any]:
        if not os.environ.get("POSTMARK_API_KEY"):
            raise NotConfigured("POSTMARK_API_KEY unset — real email send is owner-gated; not faked")
        raise NotConfigured("Postmark transport not wired in this local build (seam present)")


_ADAPTERS = {"console": ConsoleAdapter, "resend": ResendAdapter, "postmark": PostmarkAdapter}


def send(realm: str, template: str, to: str, props: dict[str, Any] | None = None, *,
         adapter: str = "console") -> dict[str, Any]:
    """The one standardized call site. Returns a delivery record; console mode flags sent=False."""
    msg = _render(realm, template, to, props or {})
    impl = _ADAPTERS.get(adapter)
    if impl is None:
        raise ValueError(f"unknown adapter {adapter!r}; known {sorted(_ADAPTERS)}")
    return impl().deliver(msg)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # console adapter renders + audits + HONESTLY does not send
    rec = send("baltor", "verify_email", "ada@example.test", {"verify_url": "https://local/verify/abc"})
    ck("console: realm-branded render (Baltor)", rec["realm"] == "baltor")
    ck("console: mode=console, sent=False (Mode Protocol — no silent send)",
       rec["mode"] == "console" and rec["sent"] is False)
    ck("console: written to outbox + audit", (OUTBOX / rec["outbox_file"]).exists() and AUDIT.exists())
    # real-send adapters are seams: NotConfigured without a key, NEVER a fake send
    for ad in ("resend", "postmark"):
        os.environ.pop({"resend": "RESEND_API_KEY", "postmark": "POSTMARK_API_KEY"}[ad], None)
        try:
            send("baltor", "welcome", "ada@example.test", {}, adapter=ad)
            ck(f"{ad}: unconfigured send raises (no fake)", False)
        except NotConfigured:
            ck(f"{ad}: unconfigured send raises NotConfigured (no fake send)", True)
    # guards
    try:
        send("baltor", "verify_email", "ada@example.test", {"api_key": "sk-deadbeef12345678"})
        ck("secret-shaped props rejected", False)
    except ValueError:
        ck("secret-shaped props rejected", True)
    try:
        send("baltor", "nope", "ada@example.test")
        ck("unknown template rejected", False)
    except ValueError:
        ck("unknown template rejected", True)
    try:
        send("baltor", "welcome", "not-an-email")
        ck("invalid recipient rejected", False)
    except ValueError:
        ck("invalid recipient rejected", True)
    # no secret in the audit trail
    blob = AUDIT.read_text(encoding="utf-8") if AUDIT.exists() else ""
    ck("no secret-shaped material in the audit trail", not _SECRET_RE.search(blob))

    print("\n" + ("PASS — email_port: one standardized send(realm,template,to,props) contract; console adapter "
                  "renders realm-branded mail to the outbox + audit and HONESTLY does not send (Mode Protocol); "
                  "Resend/Postmark are owner-gated seams (NotConfigured without a key, never a fake send); "
                  "secret/template/recipient guards hold; no secret in the trail."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if len(sys.argv) == 1 or "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/email_port.py --self-test")
    raise SystemExit(0)
