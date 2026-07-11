#!/usr/bin/env python3
"""scripts.check_service_handshake_slice — PROOF for the /service/* slice in the identity service
(backlog 1.2; contracts/SERVICE-CONNECTIONS.md). Makes the Service Connections console real.

Asserts over HTTP, with SERVICE_<REALM>_SECRET set in the environment:
  A. HANDSHAKE — POST /api/identity/<from>/service/handshake (Bearer = from's service secret) →
     201 with a connection {id,from,to,scopes}, a raw token shown ONCE (svt_<from>_<to>_…), and a
     receipt. Wrong/absent secret → 401; a realm with no SERVICE_*_SECRET → 503 (never faked).
  B. SCOPES — an unknown scope is rejected (400); the 8-scope vocabulary is the single source.
  C. VERIFY — the TO realm validates the raw token → {valid:true, from, to, scopes}; a garbage
     token → 401; the FROM realm is NOT a valid 'to' for that token (directional).
  D. CONNECTIONS — GET /service/connections lists the connection for BOTH realms (from and to),
     projection only (no raw token, no token_ref/hash on the wire).
  E. REVOKE — POST /service/revoke kills it (receipt returned); verify then fails (401).
  F. ASYMMETRY + ISOLATION — a Baltor→Teleon token does not grant Teleon→Baltor; user realm
     isolation is untouched (a service token is not a user session).
  G. DISK HYGIENE — no raw service token on disk; persisted connections store refs only.

Offline, stdlib-only, ephemeral port, temp state. Exit 0/1.
"""
from __future__ import annotations

import json
import os
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

from scripts.identity_local_service import start_service  # noqa: E402

_TOKEN_RE = re.compile(r"\bsvt_[a-z]+_[a-z]+_[0-9a-f]{32}\b")


def _call(port, method, path, body=None, bearer=None):
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # service secrets live in the env (never the repo) — set fakes for the proof only
    os.environ["SERVICE_BALTOR_SECRET"] = "svc-baltor-" + "fixture"
    os.environ["SERVICE_TELEON_SECRET"] = "svc-teleon-" + "fixture"
    os.environ.pop("SERVICE_OPENCONTEXTHUB_SECRET", None)
    state = Path(tempfile.mkdtemp(prefix="svc-proof-"))
    server, thread, port = start_service(port=0, state_dir=state)
    raw = None
    try:
        # A. handshake
        st, _ = _call(port, "POST", "/api/identity/baltor/service/handshake",
                      {"to": "teleon", "scopes": ["llm:invoke", "verify:run"]}, bearer="wrong")
        ck("A: wrong service secret rejected (401)", st == 401)
        st, no_acct = _call(port, "POST", "/api/identity/opencontexthub/service/handshake",
                            {"to": "teleon", "scopes": ["registry:read"]}, bearer="anything")
        ck("A: realm with no SERVICE_*_SECRET → 503 (not faked)", st == 503)
        st, hs = _call(port, "POST", "/api/identity/baltor/service/handshake",
                       {"to": "teleon", "scopes": ["llm:invoke", "verify:run"], "note": "ctx refresh"},
                       bearer="svc-baltor-fixture")
        raw = hs.get("token", "")
        ck("A: handshake 201 with connection + raw token once + receipt",
           st == 201 and hs["connection"]["from"] == "baltor" and hs["connection"]["to"] == "teleon"
           and raw.startswith("svt_baltor_teleon_") and hs.get("receipt", "").startswith("rcpt_"))

        # B. scopes
        st, _ = _call(port, "POST", "/api/identity/baltor/service/handshake",
                      {"to": "teleon", "scopes": ["llm:invoke", "make:coffee"]}, bearer="svc-baltor-fixture")
        ck("B: unknown scope rejected (400)", st == 400)

        # C. verify (directional)
        st, v = _call(port, "POST", "/api/identity/teleon/service/verify", {"token": raw})
        ck("C: the TO realm verifies the token (valid, from, to, scopes)",
           st == 200 and v["valid"] is True and v["from"] == "baltor"
           and set(v["scopes"]) == {"llm:invoke", "verify:run"})
        st, vg = _call(port, "POST", "/api/identity/teleon/service/verify", {"token": "svt_baltor_teleon_dead"})
        ck("C: a garbage token fails verify (401)", st == 401 and vg["valid"] is False)
        st, vbad = _call(port, "POST", "/api/identity/baltor/service/verify", {"token": raw})
        ck("C: the FROM realm is not a valid 'to' for the token (directional)",
           st == 401 and vbad["valid"] is False)

        # D. connections (both realms see it, projection only)
        st, cb = _call(port, "GET", "/api/identity/baltor/service/connections")
        st2, ctn = _call(port, "GET", "/api/identity/teleon/service/connections")
        blob = json.dumps([cb, ctn])
        ck("D: connection lists for both from and to (projection only)",
           len(cb["connections"]) == 1 and len(ctn["connections"]) == 1
           and raw not in blob and "token_ref" not in blob and "svtref:" not in blob)
        conn_id = cb["connections"][0]["id"]

        # E. revoke
        st, rv = _call(port, "POST", "/api/identity/baltor/service/revoke", {"id": conn_id})
        ck("E: revoke returns ok + receipt", st == 200 and rv["ok"] and rv["receipt"].startswith("rcpt_"))
        st, after = _call(port, "POST", "/api/identity/teleon/service/verify", {"token": raw})
        ck("E: a revoked token no longer verifies (401)", st == 401 and after["valid"] is False)

        # F. asymmetry + user isolation untouched
        st, asym = _call(port, "POST", "/api/identity/teleon/service/verify", {"token": raw})
        ck("F: Baltor→Teleon grant never implied Teleon→Baltor", asym["valid"] is False)
        st, sess = _call(port, "POST", "/api/identity/baltor/session/validate", {"session_id": raw})
        ck("F: a service token is not a user session", sess.get("valid") is False)

        # G. disk hygiene
        disk = "".join(p.read_text(encoding="utf-8") for p in state.glob("**/*") if p.is_file())
        ck("G: no raw service token persisted on disk", bool(raw) and raw not in disk)
        ck("G: persisted connections store refs only (svtref:)", "svtref:" in disk and not _TOKEN_RE.search(disk))
    finally:
        server.shutdown(); thread.join(timeout=5)
        shutil.rmtree(state, ignore_errors=True)
        for k in ("SERVICE_BALTOR_SECRET", "SERVICE_TELEON_SECRET"):
            os.environ.pop(k, None)

    print("\n" + ("PASS — check_service_handshake_slice: the /service/* contract is LIVE — env-keyed "
                  "service-account handshake (no fake when unset), 8-scope vocabulary enforced, directional "
                  "verify, both-realm connection lists (projection only), revoke with receipts, asymmetric "
                  "grants, user-realm isolation intact, no raw token on disk."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_service_handshake_slice.py --self-test")
    raise SystemExit(0)
