"""src.baltor.sales.diagnostics.chatbot_guardrail_audit — the Baltor wedge diagnostic.

Runs CONFIGURABLE deterministic risk rules (architecture/sales_chatbot_risk_rules.json) over a chatbot transcript
and produces a DiagnosticRun + an EvidencePack. Mode-aware via the runner: by default it audits a PROVIDED
transcript (customer_provided / own_system); a LIVE probe of a third party is only attempted under an
authorized_engagement mode with written authorization, and even then the network fetch is a labeled offline seam
here (returns unavailable — never silently fabricated). Output is observed-pattern, 'appears/requires review'
language — never a legal conclusion. Pure + deterministic.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.baltor.sales import claim_guard as _guard
from src.baltor.sales.diagnostics import runner as _runner

_A = Path(__file__).resolve().parents[4] / "architecture"


def load_risk_rules() -> list[dict]:
    return json.loads((_A / "sales_chatbot_risk_rules.json").read_text(encoding="utf-8"))["rules"]


def _fetch_live_transcript(live_target: Any) -> None:
    """Labeled SEAM: a real live probe would fetch here. Offline/in this environment there is no network, so we
    return None (unavailable) rather than fabricate a transcript. A real adapter goes behind this seam, gated by
    written authorization."""
    return None


def _classify_turn(turn: dict, rules: list[dict]) -> list[dict]:
    resp = (turn.get("response") or "").lower()
    out: list[dict] = []
    for r in rules:
        if any(p.lower() in resp for p in r["any_phrases"]):
            why = r["why"]
            # safety: the rule wording must read as 'appears/requires review', never a legal conclusion
            if _guard.classify_claim_language(why)["class"] == "legal_conclusion":
                why = _guard.safe_rewrite(why)
            out.append({
                "prompt": turn.get("prompt", ""), "response": turn.get("response", ""),
                "risk_category": r["category"], "regulated": bool(r.get("regulated")),
                "why": why, "recommended_action": r["recommended_action"],
                "safe_replacement": r["safe_replacement"], "claim_language_class": "safe",
            })
    return out


def audit_transcript(*, mode: str | None = None, authorization_basis: str = "customer_provided",
                     input_source: str = "provided_transcript", company_id: str = "exemplar.consumer_finance_chatbot",
                     company_is_synthetic: bool = True, now: str, transcript: dict | None = None,
                     is_live_probe: bool = False, live_target: Any = None) -> dict:
    """Audit a chatbot transcript under a configurable mode. Returns {blocked} or {diagnostic_run, evidence_pack,
    findings, note}."""
    run, reasons = _runner.start_diagnostic(tool="chatbot_guardrail_audit", mode=mode,
                                            authorization_basis=authorization_basis, input_source=input_source,
                                            is_live_probe=is_live_probe, company_id=company_id, now=now)
    if run is None:
        return {"blocked": True, "reasons": reasons}

    note = ""
    turns = (transcript or {}).get("turns", []) if transcript else []
    if is_live_probe:
        live = _fetch_live_transcript(live_target)
        if live is None:
            note = "live_fetch_unavailable_offline"  # authorized, but no network here — honest, not fabricated
            turns = []
        else:
            turns = live.get("turns", [])

    rules = load_risk_rules()
    findings: list[dict] = []
    for t in turns:
        findings.extend(_classify_turn(t, rules))
    run["findings"] = findings

    risk_categories = sorted({f["risk_category"] for f in findings})
    regulated = [f["risk_category"] for f in findings if f["regulated"]]
    pain = regulated[0] if regulated else ("chatbot_guardrail_failure" if findings else "no_finding")
    pack = {
        "schema_version": "EvidencePack.v1",
        "evidence_pack_id": "ep_" + hashlib.blake2b((run["run_id"] + now).encode(), digest_size=10).hexdigest(),
        "company_id": company_id, "company_is_synthetic": company_is_synthetic, "target_product": "Baltor",
        "pain_hypothesis": pain, "authorization_basis": authorization_basis,
        "diagnostic_run_ids": [run["run_id"]],
        "observed_artifacts": [{"kind": "chatbot_answer", "summary": f["why"], "source_ref": input_source} for f in findings],
        "source_urls": [], "risk_categories": risk_categories,
        "confidence": "low" if is_live_probe else "medium",
        "public_claim_safe": False, "requires_legal_review": bool(regulated),
        "review_status": "pending" if regulated else "not_required",
        "claim_language_class": "safe", "recommended_outreach_ref": None, "demo_url": None, "created_at": now,
    }
    return {"blocked": False, "diagnostic_run": run, "evidence_pack": pack, "findings": findings, "note": note}


__all__ = ["audit_transcript", "load_risk_rules"]
