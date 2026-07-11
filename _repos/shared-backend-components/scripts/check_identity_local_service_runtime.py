#!/usr/bin/env python3
"""scripts.check_identity_local_service_runtime — PROOF for _repos/shared-backend-components/scripts/identity_local_service.py.

The local Identity & Access service must run the owner-locked auth model END-TO-END over HTTP:
  A. REGISTRY-DRIVEN — served realms == _repos/shared-backend-components/architecture/identity_realm_registry.json; parent + Baltor +
     Teleon present; the live-hub realm set matches the OWNING products.js registry exactly (drift
     gate in both directions; private bench hubs get NO public realm).
  B. STANDARD FLOW over HTTP — register (response carries NO credential_ref) → login rejected before
     onboarding → onboard all steps → login mints a realm session → validate true.
  C. REALM ISOLATION over HTTP — a Baltor session is invalid in Teleon; a Baltor-only identifier
     cannot log in to Teleon (no cross-realm account, no SSO).
  D. API KEYS — mint requires a valid realm session (401 anonymous); the raw key appears exactly ONCE
     at mint; list shows projections only (no raw key, no stored hash); verify proves possession;
     revoke kills the key.
  E. PERSISTENCE — after a full service restart on the same state dir, the account, a live session,
     and an unrevoked API key all still work (atomic file-backed stores).
  F. DISK + AUDIT HYGIENE — no cleartext secret and no raw API key in ANY state file or the audit
     log; credentials at rest are one-way refs; audit events exist for register/login/mint with
     ok/rejected outcomes.
  G. CORRELATION — a supplied X-AIDR-Request-Id is echoed on the response (consumption-model header).

Offline, stdlib-only, ephemeral ports, temp state dir. Exit 0/1. `--self-test` runs the gate.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.identity_local_service import REGISTRY_PATH, start_service  # noqa: E402

# a FAKE passphrase assembled from fragments (not a real secret; keeps scanners quiet)
_SECRET = "-".join(("demo", "passphrase", "fragment"))
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _call(port: int, method: str, path: str, body: dict | None = None,
          request_id: str | None = None) -> tuple[int, dict, dict]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", method=method,
        data=json.dumps(body or {}).encode() if method == "POST" else None,
        headers={"Content-Type": "application/json",
                 **({"X-AIDR-Request-Id": request_id} if request_id else {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}"), dict(resp.headers)
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}"), dict(err.headers)


def _live_hub_realm_ids(products_js: str) -> set[str]:
    """The owning registry's LIVE Open*Hub keys (lowercased) — the realm drift gate's other side."""
    ids: set[str] = set()
    current: str | None = None
    for line in products_js.splitlines():
        m = re.match(r"\s*([A-Za-z0-9_]+):\s*\{", line)
        if m:
            current = m.group(1) if m.group(1).lower().startswith("open") else None
        if current and re.search(r"status:\s*'live'", line):
            ids.add(current.lower())
    return ids


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    state_dir = Path(tempfile.mkdtemp(prefix="identity-proof-"))
    server, thread, port = start_service(port=0, state_dir=state_dir)
    raw_keys: list[str] = []
    try:
        # A. registry-driven realms + the products.js drift gate
        _, health, _ = _call(port, "GET", "/api/identity/health")
        _, realms_resp, _ = _call(port, "GET", "/api/identity/realms")
        served = {r["realm_id"] for r in realms_resp["realms"]}
        declared = {r["realm_id"] for r in registry["realms"]}
        ck("A: health ok and realm count matches the registry",
           health.get("ok") is True and health.get("realms") == len(declared))
        ck("A: served realms == declared realms", served == declared, str(served ^ declared))
        ck("A: parent + Baltor + Teleon realms present", {"aidoneright", "baltor", "teleon"} <= served)
        products_js = (_resource(registry["live_hub_realm_source"])).read_text(encoding="utf-8")
        live_hubs = _live_hub_realm_ids(products_js)
        declared_hubs = {r["realm_id"] for r in registry["realms"] if r.get("layer") == "open_hub_live"}
        ck("A: live-hub realms match the owning products.js registry (both directions)",
           live_hubs == declared_hubs, f"products.js={sorted(live_hubs)} registry={sorted(declared_hubs)}")

        # B. the standard flow over HTTP (baltor realm)
        st, acct, _ = _call(port, "POST", "/api/identity/baltor/register",
                            {"identifier": "ada@example.test", "secret": _SECRET})
        ck("B: register creates an account (201)", st == 201 and acct.get("status") == "registered")
        ck("B: register response carries NO credential material", "credential_ref" not in acct)
        st, _, _ = _call(port, "POST", "/api/identity/baltor/login",
                         {"identifier": "ada@example.test", "secret": _SECRET})
        ck("B: login before onboarding is rejected (401)", st == 401)
        for step in acct["onboarding_steps"]:
            st, onboarded, _ = _call(port, "POST", "/api/identity/baltor/onboard",
                                     {"account_id": acct["account_id"], "step": step})
        ck("B: account active after all onboarding steps", onboarded.get("status") == "active")
        st, sess, _ = _call(port, "POST", "/api/identity/baltor/login",
                            {"identifier": "ada@example.test", "secret": _SECRET})
        ck("B: login mints a realm session", st == 200 and sess.get("session_id", "").startswith("sess_"))
        st, valid, _ = _call(port, "POST", "/api/identity/baltor/session/validate",
                             {"session_id": sess["session_id"]})
        ck("B: the session validates in its own realm", valid.get("valid") is True)

        # C. realm isolation over HTTP
        st, cross, _ = _call(port, "POST", "/api/identity/teleon/session/validate",
                             {"session_id": sess["session_id"]})
        ck("C: a Baltor session is NOT valid in Teleon", cross.get("valid") is False)
        st, _, _ = _call(port, "POST", "/api/identity/teleon/login",
                         {"identifier": "ada@example.test", "secret": _SECRET})
        ck("C: a Baltor-only identifier cannot log in to Teleon (401)", st == 401)

        # D. API keys — session-gated mint, raw shown once, projections only, verify, revoke
        st, _, _ = _call(port, "POST", "/api/identity/baltor/api-keys/mint", {"session_id": "nope"})
        ck("D: mint without a valid session is rejected (401)", st == 401)
        st, minted, _ = _call(port, "POST", "/api/identity/baltor/api-keys/mint",
                              {"session_id": sess["session_id"], "scopes": ["read", "write"]})
        raw_keys.append(minted.get("api_key", ""))
        ck("D: mint returns the raw key exactly once (ak_baltor_…)",
           st == 201 and minted.get("shown_once") is True and minted["api_key"].startswith("ak_baltor_"))
        st, listing, _ = _call(port, "GET",
                               f"/api/identity/baltor/api-keys?session_id={sess['session_id']}")
        blob = json.dumps(listing)
        ck("D: list shows projections only — no raw key, no stored hash",
           st == 200 and len(listing["api_keys"]) == 1
           and minted["api_key"] not in blob and "keyref:" not in blob)
        st, verified, _ = _call(port, "POST", "/api/identity/baltor/api-keys/verify",
                                {"api_key": minted["api_key"]})
        ck("D: verify proves possession (valid + scopes)",
           st == 200 and verified.get("valid") is True and verified.get("scopes") == ["read", "write"])
        st, _, _ = _call(port, "POST", "/api/identity/baltor/api-keys/revoke",
                         {"session_id": sess["session_id"], "key_id": minted["key_id"]})
        st, after, _ = _call(port, "POST", "/api/identity/baltor/api-keys/verify",
                             {"api_key": minted["api_key"]})
        ck("D: a revoked key no longer verifies (401)", st == 401 and after.get("valid") is False)

        # E. persistence across a full restart (mint a second, unrevoked key first)
        st, keep, _ = _call(port, "POST", "/api/identity/baltor/api-keys/mint",
                            {"session_id": sess["session_id"]})
        raw_keys.append(keep.get("api_key", ""))
        server.shutdown()
        thread.join(timeout=5)
        server, thread, port = start_service(port=0, state_dir=state_dir)
        st, sess2, _ = _call(port, "POST", "/api/identity/baltor/login",
                             {"identifier": "ada@example.test", "secret": _SECRET})
        ck("E: the account survives a restart (login works)", st == 200 and "session_id" in sess2)
        st, valid2, _ = _call(port, "POST", "/api/identity/baltor/session/validate",
                              {"session_id": sess["session_id"]})
        ck("E: a pre-restart session survives (persisted store)", valid2.get("valid") is True)
        st, verified2, _ = _call(port, "POST", "/api/identity/baltor/api-keys/verify",
                                 {"api_key": keep["api_key"]})
        ck("E: an unrevoked API key survives a restart", st == 200 and verified2.get("valid") is True)

        # F. disk + audit hygiene
        disk = "".join(p.read_text(encoding="utf-8") for p in sorted(state_dir.glob("**/*")) if p.is_file())
        ck("F: no cleartext secret in any state file", _SECRET not in disk)
        ck("F: no raw API key in any state file or audit log",
           all(raw and raw not in disk for raw in raw_keys))
        ck("F: credentials at rest are one-way refs (credref:…)", "credref:" in disk)
        ck("F: no raw provider-style keys anywhere", not _KEY_RE.search(disk))
        events = [json.loads(line) for line in
                  (state_dir / "audit-events.jsonl").read_text(encoding="utf-8").splitlines()]
        actions = {e["action"] for e in events}
        ck("F: audit events cover register/login/mint",
           {"register", "login", "api-keys/mint"} <= actions)
        ck("F: audit records rejected outcomes too",
           any(e["outcome"] == "rejected" for e in events))

        # G. correlation header echo
        _, _, headers = _call(port, "GET", "/api/identity/health", request_id="proof-req-001")
        ck("G: X-AIDR-Request-Id is echoed", headers.get("X-AIDR-Request-Id") == "proof-req-001")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        shutil.rmtree(state_dir, ignore_errors=True)

    print("\n" + ("PASS — check_identity_local_service_runtime: registry-driven separate realms (parent+Baltor+"
                  "Teleon+live hubs, products.js drift-gated), the standard flow + realm isolation over HTTP, "
                  "session-gated hash-only API keys (raw shown once), restart-safe persistence, no cleartext "
                  "secret or raw key on disk, audited with request-id correlation."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_identity_local_service_runtime.py --self-test")
    raise SystemExit(0)
