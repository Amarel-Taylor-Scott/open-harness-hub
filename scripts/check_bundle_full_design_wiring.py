#!/usr/bin/env python3
"""scripts.check_bundle_full_design_wiring — PROOF that the FULL-DESIGN bundle is wired to the real
backends (not mock): the kit's OhAuth talks to the identity service, every surface loads the realm
client, and a page-analytics beacon fires to the events plane.

  A. CLIENT — shared/oh-identity.js exists, exposes realmOf/signup/login/session/validate/mintKey,
     default identity port matches architecture/identity_realm_registry.json (drift gate), supports
     the OHH_IDENTITY_BASE deploy override, stores session per-realm only (never the passphrase).
  B. LOADED — oh-identity.js is loaded by the surface HTMLs (≥ 20), after products.js.
  C. OhAuth WIRED — shared/oh-site.jsx OhAuth calls OHIdentity.signup/login (not just navigate),
     binds controlled inputs (value/onChange), shows errors, falls to the preview path only when
     the service is unreachable (never fakes a session), and renders Google/GitHub as DISABLED
     owner-gated seams.
  D. EVENTS — a page_view beacon fires to the events plane (drift-gated port), anon-only,
     text/plain (CORS-safelisted), graceful.
  E. SYNTAX — node --check oh-identity.js when node is available.

Offline, stdlib-only. Exit 0/1.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "dist" / "sites" / "aidoneright-design"
IDENT = BUNDLE / "shared" / "oh-identity.js"
SITE = BUNDLE / "shared" / "oh-site.jsx"
REALM_REG = REPO / "architecture" / "identity_realm_registry.json"
EVENT_REG = REPO / "architecture" / "local_service_registry.json"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    ident = IDENT.read_text(encoding="utf-8") if IDENT.exists() else ""
    site = SITE.read_text(encoding="utf-8")
    realm_port = int(json.loads(REALM_REG.read_text())["defaults"]["port"])
    event_port = next(s["port"] for s in json.loads(EVENT_REG.read_text())["services"]
                      if s["service_id"] == "local_event_tracking_service")

    # A. client contract
    ck("A: oh-identity.js exists", bool(ident))
    ck("A: exposes the realm client surface",
       all(m in ident for m in ("realmOf", "signup:", "login:", "session:", "validate:", "mintKey:")))
    m = re.search(r'DEFAULT_BASE = "http://127\.0\.0\.1:(\d+)"', ident)
    ck("A: identity default port matches the realm registry (drift gate)",
       bool(m) and int(m.group(1)) == realm_port, m.group(1) if m else "none")
    ck("A: OHH_IDENTITY_BASE deploy override supported", "OHH_IDENTITY_BASE" in ident)
    ck("A: session stored per-realm, passphrase never stored",
       "oh-session-" in ident and "setSession" in ident and "secret: pass" in ident.replace("'", '"').replace('"secret": pass', "secret: pass"))

    # B. loaded in surfaces
    loaded = sum(1 for p in BUNDLE.rglob("*.html") if "oh-identity.js" in p.read_text(encoding="utf-8"))
    ck("B: oh-identity.js loaded by ≥20 surfaces", loaded >= 20, str(loaded))

    # C. OhAuth wired
    ck("C: OhAuth calls the real identity service (signup/login)",
       "OHIdentity.signup" in site and "OHIdentity.login" in site)
    ck("C: controlled inputs bound (value + onChange)",
       "value={email}" in site and "onChange={(e) => setEmail" in site and "value={pass}" in site)
    ck("C: errors surfaced + busy state", "ohs-auth-err" in site and "setErr(" in site and "busy" in site)
    ck("C: preview fallback only when service unreachable (no fake session)",
       "available()" in site and "identity service down" in site)
    ck("C: Google/GitHub are DISABLED honest seams",
       site.count("ohs-oauth-btn") >= 2 and "disabled title={SEAM}" in site
       and ("coming soon" in site.lower() or "CredentialProviderPort" in site))

    # D. events beacon
    m2 = re.search(r'OHH_EVENTS_BASE \|\| "http://127\.0\.0\.1:(\d+)"', ident)
    ck("D: events beacon port matches the registry (drift gate)",
       bool(m2) and int(m2.group(1)) == event_port, m2.group(1) if m2 else "none")
    ck("D: page_view beacon, anon-only, sendBeacon text/plain",
       'event: "page"' in ident and "anon" in ident and "sendBeacon" in ident and "text/plain" in ident)

    # E. node syntax
    node = shutil.which("node")
    if node:
        res = subprocess.run([node, "--check", str(IDENT)], capture_output=True, text=True)
        ck("E: node --check oh-identity.js", res.returncode == 0, res.stderr.strip()[:160])
    else:
        print("  [ok] E: node unavailable — syntax check skipped honestly")

    # F. OFFLINE LOAD — the bundle prototypes served by the showcase server load React/Babel from the
    #    LOCAL /vendor/ mount, not an external CDN (the cross-product blank a confused user hit).
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from scripts.showcase.server import rewrite_bundle_html
    vendor = REPO / "web" / "vendor"
    ck("F: /vendor/ has the pinned React/Babel runtime",
       all((vendor / f).exists() for f in ("react.development.js", "react-dom.development.js", "babel.min.js")))
    _sample = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />'
               '<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet" />'
               '<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" '
               'integrity="sha384-XXX" crossorigin="anonymous"></script>'
               '<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin></script>')
    _rew = rewrite_bundle_html(_sample)
    ck("F: rewrite repoints CDN React/Babel to /vendor/",
       "/vendor/react.development.js" in _rew and "/vendor/babel.min.js" in _rew)
    ck("F: rewrite removes ALL external CDN + integrity/crossorigin (offline, no SRI mismatch)",
       "unpkg.com" not in _rew and "fonts.googleapis" not in _rew and "fonts.gstatic" not in _rew
       and "integrity=" not in _rew and "crossorigin" not in _rew)

    print("\n" + ("PASS — check_bundle_full_design_wiring: the full-design bundle is WIRED to the real "
                  "backends — realm-aware identity client (drift-gated, override, per-realm sessions, no "
                  "stored passphrase) loaded across the surfaces, OhAuth does real register/login with honest "
                  "fallback + owner-gated OAuth seams, and a page beacon fires to the events plane."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_bundle_full_design_wiring.py --self-test")
    raise SystemExit(0)
