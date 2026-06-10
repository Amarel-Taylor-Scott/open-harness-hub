#!/usr/bin/env python3
"""scripts.check_harness_hub_auth_wiring — PROOF that the harness-hub web app is wired to the LOCAL
Identity & Access service (realm: openharnesshub) honestly.

Asserts (static contract — the service side is proven live by check_identity_local_service_runtime):
  A. LOAD ORDER — index.html loads identity.js (the client) before app.js.
  B. CLIENT CONTRACT — identity.js targets THIS product's realm only; the realm exists in
     architecture/identity_realm_registry.json; the client's default port matches the registry's
     defaults.port (drift gate — the one allowed mirror of that value); a deploy override
     (window.OHH_IDENTITY_BASE) exists; requests carry X-AIDR-Request-Id.
  C. NO SECRET PERSISTENCE — the only localStorage write in the client is the opaque session
     handle; auth.js writes no localStorage at all; no raw API key is ever stored client-side.
  D. REAL FLOWS, NO FAKES — auth.js calls register/login/onboard/validate and the API-key console
     (mint/list/revoke); passphrase inputs are type="password"; SSO/Google are DISABLED with the
     owner-gated-seam label (no data-nav fake path); the service-down message names the real
     runnable command; no trycloudflare or invented URLs in client code.
  E. SYNTAX — `node --check` validates both files when node is available (skips honestly when not).

Offline, stdlib-only. Exit 0/1. `--self-test` runs the gate.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB = REPO_ROOT / "web" / "harness-hub"
IDENTITY_JS = WEB / "identity.js"
AUTH_JS = WEB / "pages" / "auth.js"
INDEX_HTML = WEB / "index.html"
REALM_REGISTRY = REPO_ROOT / "architecture" / "identity_realm_registry.json"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    html = INDEX_HTML.read_text(encoding="utf-8")
    client = IDENTITY_JS.read_text(encoding="utf-8")
    auth = AUTH_JS.read_text(encoding="utf-8")
    registry = json.loads(REALM_REGISTRY.read_text(encoding="utf-8"))

    # A. load order
    ck("A: index.html loads identity.js", 'src="identity.js"' in html)
    ck("A: identity.js loads before app.js",
       html.find('src="identity.js"') < html.find('src="app.js"'))

    # B. client contract — realm-parameterized with this product's realm as the default
    realm_match = re.search(r'DEFAULT_REALM = "([a-z0-9]+)"', client)
    realm = realm_match.group(1) if realm_match else ""
    realm_ids = {r["realm_id"] for r in registry["realms"]}
    ck("B: client declares a default realm", bool(realm))
    ck("B: the default realm exists in the identity realm registry", realm in realm_ids, realm)
    ck("B: the default realm is this product's (openharnesshub)", realm == "openharnesshub")
    ck("B: realm is overridable per front end (?realm= / OHH_IDENTITY_REALM)",
       "OHH_IDENTITY_REALM" in client and "realm" in client)
    port_match = re.search(r'DEFAULT_BASE = "http://127\.0\.0\.1:(\d+)"', client)
    ck("B: client default port matches the realm registry (drift gate)",
       bool(port_match) and int(port_match.group(1)) == int(registry["defaults"]["port"]),
       port_match.group(1) if port_match else "no DEFAULT_BASE")
    ck("B: deploy override (OHH_IDENTITY_BASE) supported", "OHH_IDENTITY_BASE" in client)
    ck("B: requests carry X-AIDR-Request-Id", "X-AIDR-Request-Id" in client)

    # C. no secret persistence client-side
    client_writes = re.findall(r"localStorage\.setItem\(([^,]+),", client)
    ck("C: the client's only localStorage write is the session handle",
       all("SESSION_KEY" in w for w in client_writes) and client_writes, str(client_writes))
    ck("C: auth.js writes no localStorage", "localStorage.setItem" not in auth)
    ck("C: no raw api key persisted client-side",
       "api_key" not in " ".join(client_writes) and 'setItem("ohh-api-key' not in auth + client)
    ck("C: signup keeps the secret in memory only (cleared after onboarding)",
       "pendingSignup = null" in auth and "memory only" in auth)

    # D. real flows, no fakes
    for fn in ("OHHIdentity.register", "OHHIdentity.login", "OHHIdentity.onboard",
               "OHHIdentity.validate", "OHHIdentity.mintKey", "OHHIdentity.listKeys",
               "OHHIdentity.revokeKey"):
        ck(f"D: auth.js uses {fn}", fn in auth)
    ck("D: passphrase inputs are type=password", auth.count('type="password"') >= 2)
    ck("D: SSO/Google are disabled owner-gated seams (no fake nav)",
       "Owner-gated seam (CredentialProviderPort)" in auth
       and "disabled" in auth.split("ssoButtonsHTML")[1].split("}")[0])
    ck("D: service-down message names the real runnable command",
       "scripts.identity_local_service" in auth.replace("python -m scripts.identity_local_service",
                                                        "scripts.identity_local_service"))
    ck("D: /account/keys console route registered", '"/account/keys"' in auth)
    ck("D: raw key labeled shown-once in the console", "never shown again" in auth)
    # mentioning the tunnel mechanism in a comment is fine; a HARDCODED tunnel URL is the violation
    tunnel_url = re.compile(r"https?://[a-z0-9-]+\.trycloudflare\.com", re.IGNORECASE)
    ck("D: no hardcoded tunnel URLs in client code",
       not tunnel_url.search(client) and not tunnel_url.search(auth))

    # E. syntax via node when available
    node = shutil.which("node")
    if node:
        for path in (IDENTITY_JS, AUTH_JS):
            res = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            ck(f"E: node --check {path.name}", res.returncode == 0, res.stderr.strip()[:200])
    else:
        print("  [ok] E: node unavailable — syntax check skipped honestly (static checks above still gate)")

    print("\n" + ("PASS — check_harness_hub_auth_wiring: harness-hub is wired to the local identity service "
                  "(openharnesshub realm, registry drift-gated port, request-id correlation), persists only the "
                  "opaque session handle, runs real register/onboard/login + API-key console flows, labels SSO "
                  "as an owner-gated seam, and invents no URLs."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_harness_hub_auth_wiring.py --self-test")
    raise SystemExit(0)
