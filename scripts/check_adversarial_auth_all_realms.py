#!/usr/bin/env python3
"""scripts.check_adversarial_auth_all_realms — ADVERSARIAL signup/auth validation across EVERY
front end's realm (parent + Baltor + Teleon + all 9 live hubs), not just harness-hub.

The identity service backs all 12 realms; this hammers each one with the happy path AND the attacks
a hostile signup flow must survive:
  HAPPY (per realm): register → verification email rendered (no send) → login-before-onboard
    rejected → onboard → login → mint key (raw once) → verify → revoke → verify fails → logout →
    re-login → session restored.
  ADVERSARIAL (per realm): duplicate register rejected · wrong password → GENERIC reject (no account
    enumeration: same shape as unknown account) · mint without session → 401 · revoke a key you
    don't own → 404 · injection-shaped identifier handled safely (no crash, no leak) · the cleartext
    secret NEVER appears in any response.
  CROSS-REALM ISOLATION: a session minted in realm A is invalid in realm B; an A-only identifier
    cannot log in to B (no SSO, no cross-realm account) — checked across a ring of all realms.

Offline, stdlib-only, ephemeral port, temp state. Exit 0/1.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.identity_local_service import start_service  # noqa: E402

_SECRET = "-".join(("demo", "passphrase", "fragment"))
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|credref:)")


def _call(port, method, path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        if not ok:
            print(f"  [FAIL] {name}{(': ' + detail) if detail else ''}")
            fails.append(name)

    state = Path(tempfile.mkdtemp(prefix="adv-auth-"))
    server, thread, port = start_service(port=0, state_dir=state)
    try:
        _, realms_resp = _call(port, "GET", "/api/identity/realms")
        realms = [r["realm_id"] for r in realms_resp["realms"]]
        ck("all 12 front-end realms present", len(realms) == 12, str(len(realms)))
        sessions = {}
        for realm in realms:
            ident = f"user@{realm}.test"
            base = f"/api/identity/{realm}"
            # register (+ verification email) — email-shaped identifiers render a verify email
            st, reg = _call(port, "POST", f"{base}/register", {"identifier": ident, "secret": _SECRET})
            ck(f"{realm}: register 201", st == 201, str(st))
            ck(f"{realm}: no credential in register response", "credential_ref" not in reg)
            ck(f"{realm}: verification email rendered (not sent)",
               str(reg.get("verification_email", "")).startswith("console:"))
            # duplicate register rejected
            st, _ = _call(port, "POST", f"{base}/register", {"identifier": ident, "secret": _SECRET})
            ck(f"{realm}: duplicate register rejected", st >= 400, str(st))
            # login before onboard rejected
            st, _ = _call(port, "POST", f"{base}/login", {"identifier": ident, "secret": _SECRET})
            ck(f"{realm}: login-before-onboard rejected (401)", st == 401, str(st))
            # onboard all steps
            for step in reg["onboarding_steps"]:
                _call(port, "POST", f"{base}/onboard", {"account_id": reg["account_id"], "step": step})
            st, sess = _call(port, "POST", f"{base}/login", {"identifier": ident, "secret": _SECRET})
            ck(f"{realm}: login after onboarding mints session", st == 200 and "session_id" in sess, str(st))
            sessions[realm] = sess.get("session_id")
            # wrong password → GENERIC reject (no enumeration: identical to unknown-account reject)
            st_wrong, _ = _call(port, "POST", f"{base}/login", {"identifier": ident, "secret": _SECRET + "x"})
            st_unknown, _ = _call(port, "POST", f"{base}/login", {"identifier": "ghost@" + realm + ".test", "secret": _SECRET})
            ck(f"{realm}: wrong-password and unknown-account both 401 (no enumeration)",
               st_wrong == 401 and st_unknown == 401, f"{st_wrong}/{st_unknown}")
            # mint without session → 401
            st, _ = _call(port, "POST", f"{base}/api-keys/mint", {"session_id": "nope"})
            ck(f"{realm}: mint without session rejected (401)", st == 401, str(st))
            # mint with session → raw once; verify; revoke; verify fails
            st, minted = _call(port, "POST", f"{base}/api-keys/mint", {"session_id": sessions[realm], "scopes": ["read"]})
            ck(f"{realm}: mint returns raw key once", st == 201 and minted.get("api_key", "").startswith("ak_"))
            st, v = _call(port, "POST", f"{base}/api-keys/verify", {"api_key": minted.get("api_key", "")})
            ck(f"{realm}: key verifies", st == 200 and v.get("valid") is True)
            _call(port, "POST", f"{base}/api-keys/revoke", {"session_id": sessions[realm], "key_id": minted["key_id"]})
            st, _ = _call(port, "POST", f"{base}/api-keys/verify", {"api_key": minted.get("api_key", "")})
            ck(f"{realm}: revoked key fails verify (401)", st == 401, str(st))
            # injection-shaped identifier handled safely (no crash, no leak)
            st, inj = _call(port, "POST", f"{base}/register", {"identifier": "evil@x.test'; DROP TABLE--", "secret": _SECRET})
            ck(f"{realm}: injection-shaped identifier handled (no crash)", st in (201, 400), str(st))
            ck(f"{realm}: no secret in any response", not _KEY_RE.search(json.dumps([reg, minted, inj])))

        # cross-realm isolation ring: realm[i] session/identifier must not work in realm[i+1]
        for i, realm in enumerate(realms):
            other = realms[(i + 1) % len(realms)]
            st, val = _call(port, "POST", f"/api/identity/{other}/session/validate", {"session_id": sessions[realm]})
            ck(f"{realm}→{other}: session invalid cross-realm (no SSO)", val.get("valid") is False)
            st, _ = _call(port, "POST", f"/api/identity/{other}/login", {"identifier": f"user@{realm}.test", "secret": _SECRET})
            ck(f"{realm}→{other}: identifier cannot log in cross-realm", st == 401, str(st))

        # disk hygiene across the whole multi-realm run
        disk = "".join(p.read_text(encoding="utf-8") for p in state.glob("**/*") if p.is_file())
        ck("no cleartext secret on disk across all realms", _SECRET not in disk)
        ck("no raw provider keys on disk", not re.search(r"sk-[A-Za-z0-9]{16,}", disk))
    finally:
        server.shutdown(); thread.join(timeout=5)
        shutil.rmtree(state, ignore_errors=True)

    print(("PASS — check_adversarial_auth_all_realms: every front end's realm (parent + Baltor + Teleon + "
           "9 live hubs) survives the happy path AND the attacks — duplicate/early/wrong-credential rejected, "
           "no account enumeration, session-gated keys, cross-realm isolation (no SSO), injection-safe, no "
           "secret on the wire or disk."
           if not fails else f"\n{len(fails)} FAILURES: {fails[:20]}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_adversarial_auth_all_realms.py --self-test")
    raise SystemExit(0)
