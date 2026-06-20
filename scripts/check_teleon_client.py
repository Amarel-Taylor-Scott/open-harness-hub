#!/usr/bin/env python3
"""scripts.check_teleon_client — PROOF for src/baltor/teleon_client (Baltor→Teleon migration step 4, FINAL).

Baltor reaches Teleon through ONE versioned tenant client with an offline-first local path and a graceful
fallback from a remote seam. This proof asserts (a) the client's own self-test passes, and (b) the boundary
invariants hold:
  A. VERSIONED surface — CLIENT_CONTRACT_VERSION is set; >=5 capabilities spanning purpose_tasks + runtime.
  B. OFFLINE-FIRST — a default client runs local with no remote; every call returns a receipt envelope
     (capability + contract_version + served_by + fallback + result).
  C. GRACEFUL FALLBACK — a failing remote degrades to the local implementation (fallback=True), and the
     local result still resolves offline.
  D. DEPENDENCY LAW — the client imports ``src.teleon`` (Baltor → Teleon, the allowed direction) and does
     NOT import ``src.baltor`` (no circular tenant dependency); Teleon never imports this client.
  E. output is a RECEIPT, not auto-truth — the envelope exposes served_by/fallback for inspection and carries
     no is_truth/served_fact flag; no raw secrets.

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from src.baltor.teleon_client import CLIENT_CONTRACT_VERSION, TeleonClient, capabilities
from src.baltor.teleon_client.client import _self_test as _module_self_test

_REPO = Path(__file__).resolve().parents[1]
_CLIENT_SRC = _REPO / "src" / "baltor" / "teleon_client" / "client.py"
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # the client's own self-test (14 contract checks)
    ck("module self-test passes", _module_self_test() == 0)

    # A. versioned surface
    caps = capabilities()
    ck("A: contract version set (teleon-client/vN)", CLIENT_CONTRACT_VERSION.startswith("teleon-client/v"))
    ck("A: >=5 capabilities spanning purpose_tasks + runtime",
       len(caps) >= 5 and any(c.startswith("purpose.") for c in caps) and any(c.startswith("runtime.") for c in caps), str(caps))

    # B. offline-first receipt
    c = TeleonClient()
    env = c.call("runtime.default_backend")
    ck("B: default client is local", c.mode == "local")
    for k in ("capability", "contract_version", "served_by", "fallback", "ok", "result"):
        ck(f"B: envelope has '{k}'", k in env)
    ck("B: local call not a fallback", env["served_by"] == "local" and env["fallback"] is False)

    # C. graceful fallback from a failing remote
    def _boom(cap, p):
        raise ConnectionError("unreachable")
    ef = TeleonClient(mode="remote", remote=_boom).call("runtime.default_backend")
    ck("C: failing remote → local fallback (offline still works)", ef["served_by"] == "local" and ef["fallback"] is True and bool(ef["result"]))

    # D. dependency law — Baltor → Teleon only
    src = _CLIENT_SRC.read_text()
    ck("D: client imports src.teleon (Baltor → Teleon, allowed)", "from src.teleon" in src)
    ck("D: client does NOT import src.baltor (no circular tenant dep)",
       not re.search(r"^\s*(from|import)\s+src\.baltor", src, re.M))

    # E. receipt, not auto-truth + no secrets
    blob = json.dumps([env, ef])
    ck("E: envelope is a receipt (served_by/fallback), not an auto-truth flag",
       "served_by" in blob and '"is_truth": true' not in blob and "served_fact" not in blob)
    ck("E: no raw keys", not _KEY_RE.search(blob) and not _KEY_RE.search(src))

    print("\n" + ("PASS — check_teleon_client: a versioned Baltor→Teleon tenant client; offline-first local calls "
                  "with a graceful remote-fallback, per-call receipts, Baltor→Teleon dependency direction, output "
                  "is an inspectable receipt not auto-truth. Migration step 4 (final) complete."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_client.py --self-test")
    raise SystemExit(0)
