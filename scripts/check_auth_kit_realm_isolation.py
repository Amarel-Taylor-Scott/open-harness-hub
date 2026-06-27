#!/usr/bin/env python3
"""scripts.check_auth_kit_realm_isolation — PROOF for src/openhubforai/auth_kit (shared kit, separate realms).

Owner decision (2026-06-09): completely SEPARATE and INDEPENDENT login / register / onboarding per product,
but a SHARED kit (similar UI / backend elements). Asserts:
  A. SHARED KIT, SEPARATE REALMS — two realms built from the same make_realm() share the standard flow shape
     but have INDEPENDENT stores: the same identifier registered in both yields different accounts, and one
     realm's account is not in the other's store.
  B. STANDARD FLOW — register → (login rejected until onboarded) → onboard all steps → active → login mints a
     valid session; a wrong credential is rejected.
  C. ISOLATION — a session minted in realm A is NOT valid in realm B; an identifier registered only in A
     cannot log in to B (no cross-realm account).
  D. NO CROSS-REALM SSO — the realms' session stores are disjoint.
  E. NO CLEARTEXT SECRET — the cleartext secret is never stored or echoed; the credential is a one-way ref
     (credref:…); no raw keys anywhere.
  F. DETERMINISTIC + injected clock — the account handle is deterministic; a session expires by the injected
     `now` (no wall-clock).

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import json
import re
import sys

from src.openhubforai.auth_kit import DEFAULT_ONBOARDING_STEPS, STANDARD_FLOW, make_realm

# a FAKE passphrase assembled from fragments (not a real secret; keeps scanners quiet)
_SECRET = "-".join(("demo", "passphrase", "fragment"))
_NOW = 100
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    baltor = make_realm("baltor", display_name="Baltor")
    teleon = make_realm("teleon", display_name="Teleon")

    # A. shared kit, separate realms
    ck("A: the standard flow shape is shared", STANDARD_FLOW == ("register", "onboarding", "login"))
    a_b = baltor.register("ada@example.test", _SECRET, now=_NOW)
    a_t = teleon.register("ada@example.test", _SECRET, now=_NOW)
    ck("A: same identifier → INDEPENDENT accounts per realm",
       a_b["account_id"] != a_t["account_id"] and a_b["realm_id"] == "baltor" and a_t["realm_id"] == "teleon")
    ck("A: a realm's account is NOT in the other realm's store",
       a_b["account_id"] in baltor.accounts and a_b["account_id"] not in teleon.accounts)

    # B. standard flow
    try:
        baltor.login("ada@example.test", _SECRET, now=_NOW)
        ck("B: login before onboarding is rejected", False)
    except ValueError:
        ck("B: login before onboarding is rejected", True)
    for step in DEFAULT_ONBOARDING_STEPS:
        baltor.onboard(a_b["account_id"], step, now=_NOW)
    ck("B: account is active after all onboarding steps", baltor.accounts[a_b["account_id"]]["status"] == "active")
    sess = baltor.login("ada@example.test", _SECRET, now=_NOW)
    ck("B: login after onboarding mints a valid session",
       sess["session_id"].startswith("sess_") and baltor.validate_session(sess["session_id"], now=_NOW))
    try:
        baltor.login("ada@example.test", _SECRET + "x", now=_NOW)
        ck("B: a wrong credential is rejected", False)
    except ValueError:
        ck("B: a wrong credential is rejected", True)

    # C. isolation
    ck("C: a baltor session is NOT valid in teleon (realm-scoped)",
       not teleon.validate_session(sess["session_id"], now=_NOW))
    baltor.register("solo@baltor.test", _SECRET, now=_NOW)
    try:
        teleon.login("solo@baltor.test", _SECRET, now=_NOW)
        ck("C: a baltor-only identifier cannot log in to teleon", False)
    except ValueError:
        ck("C: a baltor-only identifier cannot log in to teleon", True)

    # D. no cross-realm SSO
    ck("D: the realms' session stores are disjoint (no shared SSO)",
       set(baltor.sessions) & set(teleon.sessions) == set())

    # E. no cleartext secret
    blob = json.dumps([baltor.accounts, baltor.sessions, a_b, sess])
    ck("E: the cleartext secret is never stored or echoed", _SECRET not in blob)
    ck("E: the credential is stored as a one-way ref (credref:…)",
       a_b["credential_ref"].startswith("credref:") and _SECRET not in a_b["credential_ref"])
    ck("E: no raw keys anywhere", not _KEY_RE.search(blob))

    # F. deterministic + injected-clock expiry
    a_b2 = make_realm("baltor").register("ada@example.test", _SECRET, now=_NOW)
    ck("F: the account handle is deterministic", a_b2["account_id"] == a_b["account_id"])
    ck("F: a session expires by the injected clock (no wall-clock)",
       not baltor.validate_session(sess["session_id"], now=_NOW + 10_000))

    print("\n" + ("PASS — check_auth_kit_realm_isolation: one SHARED auth kit, COMPLETELY SEPARATE + INDEPENDENT "
                  "realms per product (own accounts/sessions/registration, no cross-realm account, no SSO); the "
                  "standard register→onboard→login flow; credentials are one-way refs (no cleartext, real "
                  "crypto/OAuth/SSO is a seam); deterministic + injected clock."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_auth_kit_realm_isolation.py --self-test")
    raise SystemExit(0)
