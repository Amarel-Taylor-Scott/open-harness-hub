"""src.baltor.sales.claim_guard — deterministic guards that make the sales/lead-proof system safe.

Reads the two policy files (single source) and enforces:
  * claim language: flag legal-conclusion / accusatory wording; offer a safe rewrite ("appears" / "requires review").
  * evidence-pack gating: a NAMED real company cannot be public_claim_safe without review_status=approved;
    regulated categories force legal review; observed artifacts need a source/authorization; no legal-conclusion text.
  * authorization: a live third-party probe requires written_authorization; otherwise only own/provided/public-static.
  * outreach: draft-only (never auto-send), evidence-based, no public accusation.

Pure + deterministic; no network. Lives in Baltor (applied GTM). Output never asserts legal conclusions.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_A = Path(__file__).resolve().parents[3] / "architecture"


def load_public_claim_policy() -> dict:
    return json.loads((_A / "sales_public_claim_policy.json").read_text(encoding="utf-8"))


def load_engagement_policy() -> dict:
    return json.loads((_A / "sales_engagement_policy.json").read_text(encoding="utf-8"))


def classify_claim_language(text: str) -> dict:
    """Classify a claim string. legal_conclusion (forbidden) > accusatory > safe. Returns class + flagged terms."""
    pol = load_public_claim_policy()
    low = (text or "").lower()
    legal = [t for t in pol["forbidden_legal_conclusion_terms"] if t in low]
    if legal:
        return {"class": "legal_conclusion", "flagged_terms": legal}
    # accusatory = a soften_map key present that wasn't already a legal term
    acc = [k for k in pol["soften_map"] if k in low]
    if acc:
        return {"class": "accusatory", "flagged_terms": acc}
    return {"class": "safe", "flagged_terms": []}


def safe_rewrite(text: str) -> str:
    """Replace forbidden/accusatory terms with policy-approved softer wording (longest keys first)."""
    pol = load_public_claim_policy()
    out = text or ""
    for k in sorted(pol["soften_map"], key=len, reverse=True):
        out = re.sub(re.escape(k), pol["soften_map"][k], out, flags=re.IGNORECASE)
    return out


def authorization_ok(diagnostic: dict) -> tuple[bool, list[str]]:
    """A diagnostic run is allowed only with a valid authorization basis; a live third-party probe REQUIRES
    written_authorization."""
    eng = load_engagement_policy()
    reasons: list[str] = []
    basis = diagnostic.get("authorization_basis")
    if basis not in eng["authorization_bases"]:
        reasons.append("missing_or_unknown_authorization_basis")
    if diagnostic.get("is_live_probe") and basis != eng["live_probe_requires"]:
        reasons.append("live_probe_requires_written_authorization")
    return (not reasons), reasons


def gate_evidence_pack(pack: dict, *, claim_text: str = "") -> tuple[bool, list[str]]:
    """Decide whether an evidence pack may be treated as PUBLISHABLE/public-safe. Returns (publishable, reasons).
    Conservative: anything that trips a rule is NOT publishable (it can still exist privately)."""
    pol = load_public_claim_policy()
    reasons: list[str] = []
    text = claim_text or " ".join(str(a.get("summary", "")) for a in pack.get("observed_artifacts", []))
    cls = classify_claim_language(text)["class"]
    if cls == "legal_conclusion":
        reasons.append("contains_legal_conclusion")

    named_real = not pack.get("company_is_synthetic", False)
    public_safe = pack.get("public_claim_safe", False)
    approved = pack.get("review_status") == "approved"

    if named_real and public_safe and not approved:
        reasons.append("named_real_company_public_claim_without_approval")
    if pack.get("pain_hypothesis") in pol["regulated_categories_requiring_legal_review"] or \
       any(rc in pol["regulated_categories_requiring_legal_review"] for rc in pack.get("risk_categories", [])):
        if not pack.get("requires_legal_review"):
            reasons.append("regulated_category_must_set_requires_legal_review")
        if public_safe and not approved:
            reasons.append("regulated_public_claim_requires_approved_review")
    # every observed artifact needs a source/authorization handle
    if not (pack.get("source_urls") or pack.get("authorization_basis")):
        reasons.append("missing_source_or_authorization")
    return (not reasons), sorted(set(reasons))


def gate_outreach(outreach: dict) -> tuple[bool, list[str]]:
    """Outreach must be draft-only, evidence-based, no public accusation, with an opt-out."""
    eng = load_engagement_policy()["outreach"]
    reasons: list[str] = []
    if outreach.get("auto_send") or outreach.get("mode") not in (None, "draft", "draft_only"):
        reasons.append("outreach_must_be_draft_only_never_auto_send")
    if eng.get("require_opt_out") and not outreach.get("opt_out"):
        reasons.append("outreach_missing_opt_out")
    if classify_claim_language(outreach.get("body", ""))["class"] == "legal_conclusion":
        reasons.append("outreach_contains_legal_conclusion")
    return (not reasons), sorted(set(reasons))


def product_message_ok(product: str, blurb: str) -> tuple[bool, list[str]]:
    """Block forbidden product claims (Baltor: legal advice/guarantees; Teleon: replaces K8s/cloud functions)."""
    pol = load_public_claim_policy()["product_message_guardrails"]
    bad = pol.get(f"{product.lower()}_must_not_claim", [])
    low = (blurb or "").lower()
    hits = [p for p in bad if p.lower() in low]
    return (not hits), hits


__all__ = ["classify_claim_language", "safe_rewrite", "gate_evidence_pack", "authorization_ok",
           "gate_outreach", "product_message_ok", "load_public_claim_policy", "load_engagement_policy"]
