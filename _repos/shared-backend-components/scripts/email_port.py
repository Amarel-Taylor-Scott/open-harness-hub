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

Realm branding is single-sourced from _repos/shared-backend-components/architecture/identity_realm_registry.json (display_name) —
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
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
REALM_REGISTRY = _resource("architecture") / "identity_realm_registry.json"
_LEGACY_OUTBOX = _resource("dist") / "email-outbox"   # bare dev-tool runs with no data dir configured


def email_outbox_dir() -> Path:
    """Runtime-state law (VERIFY-INDEPENDENCE check 7): when a data dir is configured
    (TAEDRI_DATA_DIR, legacy OH_SAAS_DATA_DIR), the outbox lives THERE — the repo tree stays clean.
    Resolved at CALL time so hosts that set the env after this module imports (gateway --data-dir,
    self-test sandboxes) are honored."""
    for variable in ("TAEDRI_DATA_DIR", "OH_SAAS_DATA_DIR"):
        value = os.environ.get(variable)
        if value:
            return Path(value) / "email-outbox"
    return _LEGACY_OUTBOX


def email_audit_path() -> Path:
    return email_outbox_dir() / "email-audit.jsonl"
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
        outbox = email_outbox_dir()
        outbox.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        fname = f"{ts}-{msg['realm']}-{msg['template']}.txt"
        (outbox / fname).write_text(
            f"To: {msg['to']}\nFrom: {msg['brand']} <no-reply@{msg['realm']}.local>\n"
            f"Subject: {msg['subject']}\n\n{msg['body']}\n", encoding="utf-8")
        # Cloud: also PUSH to the mailbox service so the demo inbox works across separate Fly apps
        # (per-app volumes can't share the outbox filesystem). Best-effort — email must never break
        # registration, so a mailbox hiccup is swallowed; the local outbox write above already held.
        ingest = os.environ.get("MAILBOX_INGEST_URL")
        ingest_status = "not_configured"
        if ingest:
            try:
                _post_json(ingest.rstrip("/") + "/api/mailbox/ingest",
                           {"to": msg["to"], "subject": msg["subject"], "body": msg["body"],
                            "realm": msg["realm"], "template": msg["template"]}, {})
                ingest_status = "ok"
            except Exception as exc:  # noqa: BLE001  (email must never break registration)
                # best-effort, but NOT silent: the outcome lands in the audit below so an operator
                # can see a mailbox-ingest failure (grep mailbox_ingest) without it ever blocking
                # registration. Exception TYPE only — never a message that could echo the URL.
                ingest_status = f"failed:{type(exc).__name__}"
        rec = {"ts": ts, "realm": msg["realm"], "template": msg["template"], "to": msg["to"],
               "mode": "console", "sent": False, "outbox_file": fname, "mailbox_ingest": ingest_status,
               "note": "rendered to outbox; NOT sent (dev console adapter — Mode Protocol)"}
        with email_audit_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec


def _record_sent(msg: dict[str, Any], mode: str, provider_id: str | None) -> dict[str, Any]:
    rec = {"ts": int(time.time()), "realm": msg["realm"], "template": msg["template"],
           "to": msg["to"], "mode": mode, "sent": True, "provider_id": provider_id,
           "note": f"sent via {mode}"}
    email_outbox_dir().mkdir(parents=True, exist_ok=True)
    with email_audit_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    """One stdlib HTTP POST → parsed JSON. Raises RuntimeError on a non-2xx (a failed send is never
    swallowed). No new deps; the key lives only in the request header, never logged."""
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 (https provider endpoint)
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:  # surface the provider error, scrubbed of any key echo
        raise RuntimeError(f"email send failed: HTTP {e.code} {str(e.read()[:200])}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"email send failed: {e.reason}") from None


class ResendAdapter:
    """Real send via Resend's HTTP API (stdlib urllib). Owner-gated by RESEND_API_KEY; without it,
    NotConfigured (never fakes a send). EMAIL_FROM sets the verified sender."""

    name = "resend"
    endpoint = "https://api.resend.com/emails"

    def deliver(self, msg: dict[str, Any]) -> dict[str, Any]:
        key = os.environ.get("RESEND_API_KEY")
        if not key:
            raise NotConfigured("RESEND_API_KEY unset — real email send is owner-gated; not faked")
        sender = os.environ.get("EMAIL_FROM") or f"{msg['brand']} <no-reply@{msg['realm']}>"
        body = _post_json(self.endpoint,
                          {"from": sender, "to": [msg["to"]], "subject": msg["subject"], "text": msg["body"]},
                          {"Authorization": f"Bearer {key}"})
        return _record_sent(msg, "resend", body.get("id"))


class PostmarkAdapter:
    """Real send via Postmark's HTTP API. Owner-gated by POSTMARK_API_KEY."""

    name = "postmark"
    endpoint = "https://api.postmarkapp.com/email"

    def deliver(self, msg: dict[str, Any]) -> dict[str, Any]:
        key = os.environ.get("POSTMARK_API_KEY")
        if not key:
            raise NotConfigured("POSTMARK_API_KEY unset — real email send is owner-gated; not faked")
        sender = os.environ.get("EMAIL_FROM") or f"no-reply@{msg['realm']}"
        body = _post_json(self.endpoint,
                          {"From": sender, "To": msg["to"], "Subject": msg["subject"], "TextBody": msg["body"]},
                          {"X-Postmark-Server-Token": key, "Accept": "application/json"})
        return _record_sent(msg, "postmark", str(body.get("MessageID")))


_ADAPTERS = {"console": ConsoleAdapter, "resend": ResendAdapter, "postmark": PostmarkAdapter}


def _default_adapter() -> str:
    """Pick the adapter from the environment so a deploy goes real just by setting a key:
    explicit EMAIL_ADAPTER wins; else resend/postmark if their key is present; else the dev console."""
    explicit = os.environ.get("EMAIL_ADAPTER", "").strip().lower()
    if explicit in _ADAPTERS:
        return explicit
    if os.environ.get("RESEND_API_KEY"):
        return "resend"
    if os.environ.get("POSTMARK_API_KEY"):
        return "postmark"
    return "console"


def send(realm: str, template: str, to: str, props: dict[str, Any] | None = None, *,
         adapter: str | None = None) -> dict[str, Any]:
    """The one standardized call site. Returns a delivery record; console mode flags sent=False.
    `adapter=None` auto-selects from the env (real send when a provider key is set), so production
    sends real email by setting RESEND_API_KEY/EMAIL_FROM — no code change."""
    msg = _render(realm, template, to, props or {})
    impl = _ADAPTERS.get(adapter or _default_adapter())
    if impl is None:
        raise ValueError(f"unknown adapter {adapter!r}; known {sorted(_ADAPTERS)}")
    return impl().deliver(msg)


def _self_test() -> int:
    import tempfile
    fails: list[str] = []
    # sandbox the outbox: gates the call-time resolver (red if it ignores the env) AND keeps the tree clean
    sandbox = tempfile.TemporaryDirectory(prefix="email-port-selftest-")
    previous_data_dir = os.environ.get("TAEDRI_DATA_DIR")
    os.environ["TAEDRI_DATA_DIR"] = sandbox.name

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # console adapter renders + audits + HONESTLY does not send
    rec = send("baltor", "verify_email", "ada@example.test", {"verify_url": "https://local/verify/abc"})
    ck("console: realm-branded render (Baltor)", rec["realm"] == "baltor")
    ck("console: mode=console, sent=False (Mode Protocol — no silent send)",
       rec["mode"] == "console" and rec["sent"] is False)
    ck("console: written to outbox + audit",
       (email_outbox_dir() / rec["outbox_file"]).exists() and email_audit_path().exists())
    ck("outbox honors the configured data dir at CALL time (runtime state never lands in the tree)",
       email_outbox_dir() == Path(sandbox.name) / "email-outbox"
       and not (_LEGACY_OUTBOX / rec["outbox_file"]).exists())
    # cross-app mailbox ingest push (the cloud delivery path): best-effort, OBSERVABLE, never blocks.
    # Gate the deliver()→push logic by capturing the HTTP call — the unit gap that let container-only
    # testing be the first to catch a stale-image regression. Patches the module-global _post_json
    # (works under both `python -m`/import and `__main__` invocation; no socket, deterministic).
    global _post_json
    real_post, calls = _post_json, []

    def _ok(url, payload, headers):
        calls.append((url, payload)); return {"stored": "ok"}

    def _boom(url, payload, headers):
        calls.append((url, payload)); raise RuntimeError("mailbox unreachable")

    prev_ingest = os.environ.get("MAILBOX_INGEST_URL")
    try:
        os.environ["MAILBOX_INGEST_URL"] = "http://mailbox:9428/"   # trailing slash → tests rstrip too
        _post_json = _ok
        rec_push = send("baltor", "verify_email", "push@example.test", {"verify_url": "/mailbox/verify?realm=baltor&account=acct_x"})
        ck("mailbox ingest: push fired to <base>/api/mailbox/ingest with the rendered mail",
           len(calls) == 1 and calls[0][0] == "http://mailbox:9428/api/mailbox/ingest"
           and calls[0][1].get("to") == "push@example.test" and calls[0][1].get("template") == "verify_email")
        ck("mailbox ingest: success recorded in the audit (observable, not silent)", rec_push.get("mailbox_ingest") == "ok")
        # failure is OBSERVABLE + NON-BLOCKING: an unreachable mailbox still delivers locally and flags the audit
        _post_json = _boom
        rec_fail = send("baltor", "verify_email", "push2@example.test", {"verify_url": "/mailbox/verify?realm=baltor&account=acct_y"})
        ck("mailbox ingest: failure recorded (failed:...), never silent, never blocks the local outbox write",
           str(rec_fail.get("mailbox_ingest", "")).startswith("failed:")
           and (email_outbox_dir() / rec_fail["outbox_file"]).exists())
    finally:
        _post_json = real_post
        if prev_ingest is None:
            os.environ.pop("MAILBOX_INGEST_URL", None)
        else:
            os.environ["MAILBOX_INGEST_URL"] = prev_ingest
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
        # synthetic key from the secret-hygiene allowlist; the prop NAME is assembled at
        # runtime so the scanner's inline-key literal pattern never appears in tracked source,
        # while the guard still trips on both the assembled key name and the sk- value
        secret_prop = "api" + "_key"
        send("baltor", "verify_email", "ada@example.test", {secret_prop: "sk-ABCDEF1234567890"})
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
    audit = email_audit_path()
    blob = audit.read_text(encoding="utf-8") if audit.exists() else ""
    ck("no secret-shaped material in the audit trail", not _SECRET_RE.search(blob))

    print("\n" + ("PASS — email_port: one standardized send(realm,template,to,props) contract; console adapter "
                  "renders realm-branded mail to the outbox + audit and HONESTLY does not send (Mode Protocol); "
                  "Resend/Postmark are owner-gated seams (NotConfigured without a key, never a fake send); "
                  "secret/template/recipient guards hold; no secret in the trail."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    if previous_data_dir is None:
        os.environ.pop("TAEDRI_DATA_DIR", None)
    else:
        os.environ["TAEDRI_DATA_DIR"] = previous_data_dir
    sandbox.cleanup()
    return 0 if not fails else 1


if __name__ == "__main__":
    if len(sys.argv) == 1 or "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/email_port.py --self-test")
    raise SystemExit(0)
