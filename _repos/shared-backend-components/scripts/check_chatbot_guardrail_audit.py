#!/usr/bin/env python3
"""scripts.check_chatbot_guardrail_audit — PROOF: the Baltor Chatbot Guardrail Audit runs on a PROVIDED transcript
under a CONFIGURABLE engagement mode, flags regulated-risk answers in 'appears/requires review' language, and is
gated so it cannot probe a third party's live system without authorization.

Asserts:
  A. MODES: sales_diagnostic_modes.json valid; active_mode=safe_default; safe_default forbids live probe.
  B. AUDIT (safe_default, customer_provided): not blocked; flags the planted wage-deduction + guaranteed-approval
     answers; the safe control turn is NOT flagged.
  C. LANGUAGE: every finding is 'safe' claim language (no legal conclusion) + has recommended_action + safe_replacement.
  D. EVIDENCE PACK: requires_legal_review=True (regulated), public_claim_safe=False, synthetic; passes gate_evidence_pack.
  E. CONFIGURABLE: same audit under public_metadata_only + customer_provided -> BLOCKED; under demo + own_system -> allowed.
  F. LIVE PROBE GATING: safe_default+live -> blocked; authorized_engagement+live+customer_provided -> blocked;
     authorized_engagement+live+written_authorization -> allowed but offline seam (note=live_fetch_unavailable_offline, no fabricated findings).
  G. RULES are config-driven (loaded from sales_chatbot_risk_rules.json).
  H. DETERMINISM.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.sales import claim_guard as G
from src.baltor.sales.diagnostics import audit_transcript, load_risk_rules, resolve_mode

_NOW = "2026-06-07T00:00:00Z"
_FX = json.loads((_resource("fixtures") / "sales" / "chatbot_transcript_synthetic.json").read_text())


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    modes = json.loads((_resource("architecture") / "sales_diagnostic_modes.json").read_text())
    check("A: active_mode=safe_default; safe_default forbids live probe",
          modes["active_mode"] == "safe_default" and modes["modes"]["safe_default"]["allow_live_probe"] is False)

    res = audit_transcript(mode="safe_default", authorization_basis="customer_provided",
                           input_source="provided_transcript", transcript=_FX, company_is_synthetic=True, now=_NOW)
    cats = {f["risk_category"] for f in res.get("findings", [])}
    check("B: audit not blocked + flags wage-deduction + guaranteed-approval",
          not res.get("blocked") and "wage_deduction_or_employment_law_boundary" in cats and "unsafe_financial_guidance" in cats, str(cats))
    check("B: safe control turn (support hours) not flagged",
          all("support" not in f["prompt"].lower() for f in res["findings"]))

    check("C: findings are safe language + actionable",
          all(G.classify_claim_language(f["why"])["class"] == "safe" and f["recommended_action"] and f["safe_replacement"] for f in res["findings"]))

    pack = res["evidence_pack"]
    okp, whyp = G.gate_evidence_pack(pack)
    check("D: evidence pack regulated+private+synthetic and passes the gate",
          pack["requires_legal_review"] is True and pack["public_claim_safe"] is False and pack["company_is_synthetic"] is True and okp, str(whyp))

    blocked_mode = audit_transcript(mode="public_metadata_only", authorization_basis="customer_provided",
                                    input_source="provided_transcript", transcript=_FX, now=_NOW)
    ok_demo = audit_transcript(mode="demo", authorization_basis="own_system", input_source="own_system",
                               transcript=_FX, now=_NOW)
    check("E: configurable — public_metadata_only+customer_provided BLOCKED; demo+own_system allowed",
          blocked_mode.get("blocked") is True and ok_demo.get("blocked") is False)

    live_safe = audit_transcript(mode="safe_default", authorization_basis="customer_provided", input_source="live",
                                 is_live_probe=True, transcript=_FX, now=_NOW)
    live_noauth = audit_transcript(mode="authorized_engagement", authorization_basis="customer_provided",
                                   input_source="live", is_live_probe=True, transcript=_FX, now=_NOW)
    live_auth = audit_transcript(mode="authorized_engagement", authorization_basis="written_authorization",
                                 input_source="live", is_live_probe=True, transcript=_FX, now=_NOW)
    check("F: live probe gating (blocked w/o mode+auth; authorized -> offline seam, no fabricated findings)",
          live_safe.get("blocked") is True and live_noauth.get("blocked") is True
          and live_auth.get("blocked") is False and live_auth.get("note") == "live_fetch_unavailable_offline"
          and live_auth.get("findings") == [])

    rules = load_risk_rules()
    check("G: rules are config-driven", any(r["category"] == "wage_deduction_or_employment_law_boundary" for r in rules))

    res2 = audit_transcript(mode="safe_default", authorization_basis="customer_provided",
                            input_source="provided_transcript", transcript=_FX, company_is_synthetic=True, now=_NOW)
    check("H: deterministic", res2 == res)

    print("\n" + ("PASS — check_chatbot_guardrail_audit: the Baltor guardrail audit runs on a provided transcript "
                  "under a configurable mode, flags regulated-risk answers (appears/requires-review language) with "
                  "holdout/escalation + safe replacements, emits a private synthetic evidence pack that passes the "
                  "gate, and cannot probe a third-party live system without an authorized mode + written "
                  "authorization (then only via an honest offline seam); deterministic."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_chatbot_guardrail_audit.py --self-test")
    raise SystemExit(0)
