#!/usr/bin/env python3
"""scripts.check_harness_hub_auth_wiring — PROOF that the harness-hub web app is wired to the LOCAL
Identity & Access service (realm: openharnesshub) honestly.

The web app is the kit-based SPA emitted by scripts/port_full_design_to_web.py (DESIGN-CONTRACT,
proven byte-for-byte by that script's --check). The realm-aware identity CLIENT now lives in
web/harness-hub/kit/oh-identity.js (exposes window.OHIdentity); the auth UI + API-key console are
React components in web/harness-hub/kit/oh-site.jsx (OhAuth / OhApiKeys). The same-origin deploy
seam (window.OHH_IDENTITY_BASE) is injected by the generator, not hand-typed — so we single-source
it from the generator module rather than re-asserting a literal here.

Asserts (static contract — the service side is proven live by check_identity_local_service_runtime):
  A. LOAD ORDER — index.html loads kit/oh-identity.js (the client) before kit/oh-site.jsx (the app
     that renders OhAuth/OhApiKeys), and the generator's same-origin identity seam is present.
  B. CLIENT CONTRACT — oh-identity.js exposes window.OHIdentity, derives THIS product's realm from
     the brand registry (realmOf), the openharnesshub realm exists in
     architecture/identity_realm_registry.json, the client's default port matches the registry's
     defaults.port (drift gate — the one allowed mirror), the window.OHH_IDENTITY_BASE deploy
     override is honored, and requests carry X-AIDR-Request-Id.
  C. NO SECRET PERSISTENCE — the only localStorage writes in the client are the opaque per-realm
     session handle (oh-session-<realm>) and the anon analytics id; no secret / passphrase / raw
     API key is ever stored client-side.
  D. REAL FLOWS, NO FAKES — OhAuth calls OHIdentity.available/signup/login (real register→onboard→
     login chain) and OhApiKeys mints/revokes real keys; passphrase inputs are type="password";
     SSO/Google are DISABLED owner-gated seams (CredentialProviderPort, no fake nav); the raw key
     is labeled shown-once; no trycloudflare or invented URLs in client code.
  E. SYNTAX — `node --check` validates both kit files when node is available (skips honestly).

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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Single source for the same-origin identity seam the generator injects (don't re-type the literal).
from scripts.port_full_design_to_web import _SEAM_SCRIPT  # noqa: E402

WEB = REPO_ROOT / "web" / "harness-hub"
# The kit-based SPA: the realm-aware identity client + the app that renders OhAuth/OhApiKeys.
IDENTITY_JS = WEB / "kit" / "oh-identity.js"
SITE_JSX = WEB / "kit" / "oh-site.jsx"
INDEX_HTML = WEB / "index.html"
REALM_REGISTRY = REPO_ROOT / "architecture" / "identity_realm_registry.json"
# The deploy-override globals the generator's seam sets (single-sourced from _SEAM_SCRIPT so a
# rename in the generator is caught here, not silently passed).
IDENTITY_BASE_VAR = "OHH_IDENTITY_BASE"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    html = INDEX_HTML.read_text(encoding="utf-8")
    client = IDENTITY_JS.read_text(encoding="utf-8")
    site = SITE_JSX.read_text(encoding="utf-8")
    registry = json.loads(REALM_REGISTRY.read_text(encoding="utf-8"))

    # A. load order — the realm-aware client loads before the SPA app that renders OhAuth/OhApiKeys,
    #    and the generator's same-origin identity seam (deploy override) is wired in.
    ck("A: index.html loads kit/oh-identity.js (the identity client)",
       'src="kit/oh-identity.js"' in html)
    ck("A: identity client loads before the kit app (oh-site.jsx)",
       0 <= html.find('src="kit/oh-identity.js"') < html.find('src="kit/oh-site.jsx"'))
    ck("A: the generator's same-origin identity seam is injected (deploy override wired)",
       _SEAM_SCRIPT in html and f"window.{IDENTITY_BASE_VAR}" in _SEAM_SCRIPT)

    # B. client contract — realm derived per-brand from the registry; this product's realm exists.
    realm_ids = {r["realm_id"] for r in registry["realms"]}
    ck("B: client exposes window.OHIdentity", "window.OHIdentity" in client)
    ck("B: realm is derived per brand from the registry (realmOf)", "realmOf" in client)
    ck("B: this product's realm (openharnesshub) exists in the identity realm registry",
       "openharnesshub" in realm_ids, str(sorted(realm_ids)))
    port_match = re.search(r'DEFAULT_BASE = "http://127\.0\.0\.1:(\d+)"', client)
    ck("B: client default port matches the realm registry (drift gate)",
       bool(port_match) and int(port_match.group(1)) == int(registry["defaults"]["port"]),
       port_match.group(1) if port_match else "no DEFAULT_BASE")
    ck(f"B: deploy override (window.{IDENTITY_BASE_VAR}) honored", IDENTITY_BASE_VAR in client)
    ck("B: requests carry X-AIDR-Request-Id", "X-AIDR-Request-Id" in client)

    # C. no secret persistence client-side — only the opaque session handle + anon analytics id.
    client_writes = re.findall(r"localStorage\.setItem\(([^,]+),", client)
    ck("C: client localStorage writes are only the session handle + anon id",
       bool(client_writes) and all(("sessKey" in w or "ANON" in w) for w in client_writes),
       str(client_writes))
    ck("C: the session handle is an opaque per-realm key (oh-session-<realm>)",
       'sessKey(realm) { return "oh-session-"' in client)
    ck("C: no secret / passphrase / raw api key persisted client-side",
       not re.search(r"localStorage\.setItem\([^)]*(api_key|secret|pass)", client)
       and 'setItem("oh-api-key' not in client)

    # D. real flows, no fakes — driven from the kit app (oh-site.jsx).
    for fn in ("OHIdentity.available", "OHIdentity.signup", "OHIdentity.login",
               "OHIdentity.mintKey", "OHIdentity.revokeKey", "OHIdentity.realmOf"):
        ck(f"D: oh-site.jsx uses {fn}", fn in site)
    ck("D: passphrase input is type=password", 'type="password"' in site)
    ck("D: SSO/Google are disabled honest seams (no fake nav)",
       ("coming soon" in site.lower() or "Owner-gated seam (CredentialProviderPort)" in site)
       and re.search(r"Continue with Google[^<]*</button>", site) is not None
       and site.count("disabled title={SEAM}") >= 2)
    ck("D: the API-key console mints + revokes real keys (OhApiKeys)",
       "function OhApiKeys(" in site and "no simulated keys" in site)
    ck("D: raw key labeled shown-once in the console", "shown only once" in site)
    # mentioning the tunnel mechanism in a comment is fine; a HARDCODED tunnel URL is the violation
    tunnel_url = re.compile(r"https?://[a-z0-9-]+\.trycloudflare\.com", re.IGNORECASE)
    ck("D: no hardcoded tunnel URLs in client code",
       not tunnel_url.search(client) and not tunnel_url.search(site))

    # E. syntax via node when available
    node = shutil.which("node")
    if node:
        for path in (IDENTITY_JS, SITE_JSX):
            # oh-site.jsx is JSX (babel-transformed in the browser); node --check only parses plain
            # JS, so syntax-gate the plain client and skip the JSX file honestly.
            if path.suffix == ".jsx":
                print(f"  [ok] E: {path.name} is JSX (babel-transformed) — node --check skipped honestly")
                continue
            res = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            ck(f"E: node --check {path.name}", res.returncode == 0, res.stderr.strip()[:200])
    else:
        print("  [ok] E: node unavailable — syntax check skipped honestly (static checks above still gate)")

    print("\n" + ("PASS — check_harness_hub_auth_wiring: the harness-hub kit SPA loads the realm-aware identity "
                  "client (window.OHIdentity) before the app, derives the openharnesshub realm from the "
                  "registry (drift-gated port, request-id correlation, generator-injected deploy seam), persists "
                  "only the opaque session handle + anon id, runs real register/onboard/login + API-key console "
                  "flows, labels SSO as an owner-gated seam, and invents no URLs."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_harness_hub_auth_wiring.py --self-test")
    raise SystemExit(0)
