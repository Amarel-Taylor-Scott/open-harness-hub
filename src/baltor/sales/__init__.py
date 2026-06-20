"""src.baltor.sales — the GUARDRAIL core for the sales/lead-proof system.

This is the safety gate every later sales artifact (diagnostics, evidence packs, outreach) must pass: it keeps
public claims out of legal-conclusion territory, blocks public accusations against named real companies without
review, requires an authorization basis for any live third-party probe, and keeps outreach draft-only. Built
BEFORE any outward-facing tool so the rest cannot ship unsafe.
"""
from .claim_guard import (classify_claim_language, safe_rewrite, gate_evidence_pack, authorization_ok,
                          gate_outreach, load_public_claim_policy, load_engagement_policy)

__all__ = ["classify_claim_language", "safe_rewrite", "gate_evidence_pack", "authorization_ok",
           "gate_outreach", "load_public_claim_policy", "load_engagement_policy"]
