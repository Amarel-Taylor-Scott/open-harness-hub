#!/usr/bin/env python3
"""scripts.check_teleon_agent_gateway_baltor_boundary — PROOF: the Teleon Agent Capability Gateway's
``context.governed_answer.evidence`` capability demonstrates the BALTOR TRUTH BOUNDARY.

Teleon PRODUCES evidence; Baltor's rail DISPOSES of it as served truth. This proof runs the capability via the
gateway for a bounded agent consumer and asserts, deterministically and offline:

  A. EVIDENCE, NOT TRUTH: the run returns a candidate answer with ``serves_truth=False`` on BOTH the gateway
     result and the body; the body's ``status`` is ``candidate`` (a not-final, evidence status), never a
     finalised 'served truth' status (``verified``/``succeeded`` is the gateway's *run* verdict, but the
     answer itself is explicitly a candidate). The authoritative candidate value is present in the answer.
  B. HELD-OUT IS SEPARATE: the contradicting/stale claim is present in ``held_out`` but its value string is
     NOT inside the served output (never blended into the answer). Each held-out item is marked
     ``served=False``.
  C. SOURCE HANDLE: a real ``source_handles`` provenance handle is present (and is a ``ctx://`` handle).
  D. GOVERNANCE MARKER: the body's ``governance`` marker says Baltor owns served truth
     (``served_truth_owner='baltor'``), Teleon's role is ``evidence_only``, and ``requires_baltor_governance``
     is True — i.e. Baltor governs, Teleon does not serve truth.
  E. TELEON ↛ BALTOR (dependency law): ``_repos/teleon/backend/src/teleon/agent_gateway/capabilities.py`` does NOT import
     ``src.baltor`` (line-anchored) — Teleon encodes the governed fixtures locally / reuses the Teleon-infra
     CFPB environment, never importing the Baltor product.
  F. SECOND GOVERNED FIXTURE: a different governed question (GDPR Art. 33) routes to a second fixture and still
     returns evidence with its OWN source handle + its OWN held-out claim held separately (proves it is a
     genuine governed-answer capability, not a CFPB alias).
  G. NO RAW KEYS: the proof + the capability module contain no raw secret-key value.

Deterministic + offline; no network, no live model, no secrets. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agent_gateway import capabilities as caps
from src.teleon.agent_gateway.gateway import py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway, py_class_src_teleon_agent_gateway_gateway__AgentConsumer

_NOW = "2026-06-08T00:00:00Z"  # injected — determinism
_CAP_ID = "context.governed_answer.evidence"
_CAPS_FILE = _resource("src/teleon/agent_gateway/capabilities.py")

#: statuses that would mean the ANSWER itself is finalised served truth — the capability must NEVER use these.
_FINAL_SERVED_TRUTH_STATUSES = {"served_truth", "final", "authoritative", "truth", "adjudicated", "published"}

#: a fake provider key assembled FROM FRAGMENTS (never a real literal) — proves the scanner would catch a
#: leaked value but this proof plants none.
_FAKE_KEY = "sk-" + "live" + "_" + ("Z" * 20)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    gw = py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway()
    agent = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(
        consumer_id="agent.context-consumer",
        allowed_capabilities=frozenset({_CAP_ID}),
    )

    # --- run the capability for a governed-context question (defaults to the CFPB Reg E fixture) -------------
    res = gw.run({"capability_id": _CAP_ID,
                  "payload": {"question": "Under Reg E §1005.11, how many business days to resolve an EFT error?"}},
                 now=_NOW, consumer=agent)
    body = res.get("output", {})
    served_blob = json.dumps(body)          # the ENTIRE agent-visible body (answer + markers), as served

    # A. evidence, not truth -------------------------------------------------------------------------------
    check("A: gateway result serves_truth is False (evidence, not truth)", res.get("serves_truth") is False,
          str(res.get("serves_truth")))
    check("A: body explicitly marks serves_truth False", body.get("serves_truth") is False,
          str(body.get("serves_truth")))
    check("A: body status is 'candidate' (evidence, not a finalised served-truth status)",
          body.get("status") == "candidate", str(body.get("status")))
    check("A: body status is NOT a final 'served truth' status",
          str(body.get("status")) not in _FINAL_SERVED_TRUTH_STATUSES, str(body.get("status")))
    check("A: gateway run status is not a final served-truth status (Teleon returns candidate/evidence)",
          str(res.get("status")) not in _FINAL_SERVED_TRUTH_STATUSES, str(res.get("status")))
    check("A: authoritative candidate value '10 business days' present in the answer",
          "10 business days" in json.dumps(body.get("answer", "")), str(body.get("answer")))
    check("A: a receipt was still written (every run is receipted)", res.get("receipt_id") is not None)

    # B. held-out is SEPARATE from the served output -------------------------------------------------------
    held = res.get("held_out", [])
    held_values = [str(h.get("value", h)) for h in held]
    check("B: held_out is present (a contradiction is surfaced)", bool(held), str(held))
    check("B: held-out '30 days' contradiction is present in held_out",
          any("30 days" in v for v in held_values), str(held_values))
    # the load-bearing assertion: the held-out value string is NOT inside the served output (never blended in).
    leaked = [v for v in held_values if v in served_blob]
    check("B: held-out claim is SEPARATE — its value is NOT inside the served output",
          not leaked, f"leaked-into-output={leaked}")
    check("B: each held-out item is marked served=False",
          all(h.get("served") is False for h in held if isinstance(h, dict)), str(held))

    # C. source handle -------------------------------------------------------------------------------------
    handles = res.get("source_handles", [])
    check("C: source_handles present", bool(handles), str(handles))
    check("C: source handle is a real provenance handle (ctx:// scheme)",
          all(isinstance(h, str) and h.startswith("ctx://") for h in handles), str(handles))

    # D. governance marker — Baltor governs served truth, Teleon = evidence only ---------------------------
    gov = body.get("governance", {})
    check("D: governance marker present on the body", isinstance(gov, dict) and bool(gov), str(gov))
    check("D: governance.served_truth_owner == 'baltor' (Baltor owns served truth)",
          gov.get("served_truth_owner") == "baltor", str(gov.get("served_truth_owner")))
    check("D: governance.teleon_role == 'evidence_only' (Teleon does not serve truth)",
          gov.get("teleon_role") == "evidence_only", str(gov.get("teleon_role")))
    check("D: governance.requires_baltor_governance is True (not finalised until Baltor governs)",
          gov.get("requires_baltor_governance") is True, str(gov.get("requires_baltor_governance")))
    # the marker is single-sourced in the capabilities module (no drift).
    check("D: governance marker equals the module's single-sourced GOVERNANCE_MARKER",
          gov == caps.py_const_src_teleon_agent_gateway_capabilities__GOVERNANCE_MARKER, f"{gov} vs {caps.py_const_src_teleon_agent_gateway_capabilities__GOVERNANCE_MARKER}")

    # E. dependency law: capabilities.py must NOT import src.baltor (line-anchored) -------------------------
    bad_imports: list[str] = []
    for line in _CAPS_FILE.read_text().splitlines():
        s = line.strip()
        if s.startswith("import src.baltor") or s.startswith("from src.baltor"):
            bad_imports.append(s)
    check("E: capabilities.py does NOT import src.baltor (Teleon ↛ Baltor dependency law)",
          not bad_imports, "; ".join(bad_imports))

    # F. second governed fixture (GDPR Art. 33) still returns governed evidence ----------------------------
    res2 = gw.run({"capability_id": _CAP_ID,
                   "payload": {"question": "Under GDPR Article 33, how long to notify a personal-data breach?"}},
                  now=_NOW, consumer=agent)
    body2 = res2.get("output", {})
    served_blob2 = json.dumps(body2)
    held2_values = [str(h.get("value", h)) for h in res2.get("held_out", [])]
    check("F: GDPR question routes to a different fixture (answer '72 hours')",
          "72 hours" in json.dumps(body2.get("answer", "")), str(body2.get("answer")))
    check("F: GDPR run serves_truth False + status candidate + governance marker",
          res2.get("serves_truth") is False and body2.get("status") == "candidate"
          and body2.get("governance", {}).get("served_truth_owner") == "baltor")
    check("F: GDPR source handle present + distinct from CFPB",
          bool(res2.get("source_handles")) and res2.get("source_handles") != handles,
          str(res2.get("source_handles")))
    check("F: GDPR held-out present AND separate from its served output",
          bool(held2_values) and not any(v in served_blob2 for v in held2_values), str(held2_values))

    # G. no raw keys ---------------------------------------------------------------------------------------
    key_pat = re.compile(r"\bsk-(?:live|proj|ant)[-_][A-Za-z0-9]{12,}")
    leaks: list[str] = []
    for f in (_CAPS_FILE, Path(os.path.abspath(__file__))):
        if key_pat.search(f.read_text()):
            leaks.append(str(f.relative_to(_REPO)))
    check("G: no raw secret-key value in the capability module or this proof", not leaks, "; ".join(leaks))
    check("G: leak scanner is wired (matches a fragment-assembled fake key)", bool(key_pat.search(_FAKE_KEY)))

    print("\n" + ("PASS — check_teleon_agent_gateway_baltor_boundary: the Teleon gateway's "
                  "'context.governed_answer.evidence' capability demonstrates the BALTOR TRUTH BOUNDARY — it "
                  "returns a CANDIDATE answer (serves_truth False, status 'candidate'), holds the contradicting "
                  "claim SEPARATELY in held_out (its value never appears in the served output), carries a real "
                  "ctx:// source handle, and stamps a governance marker naming Baltor as the served-truth owner "
                  "with teleon_role 'evidence_only' + requires_baltor_governance True; a second governed fixture "
                  "(GDPR Art. 33) behaves identically with its own handle + held-out; capabilities.py never "
                  "imports src.baltor; no raw keys. Teleon produces evidence, Baltor governs served truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_agent_gateway_baltor_boundary.py --self-test")
    raise SystemExit(0)
