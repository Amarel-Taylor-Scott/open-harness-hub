#!/usr/bin/env python3
"""scripts.llm_gateway.validation — the router falls back on BAD OUTPUT, not just failed transport.

Layers: transport · schema (declared JSON schema adherence) · grounding (every cited claim references a
KNOWN input artifact id) · policy (provider allowed for tenant + data classification) · cost (within budget)
· no-unknown-artifact-ids · no-promoted-claim-without-source. A response is accepted only when ALL pass.
"""
from __future__ import annotations

from scripts.llm_gateway.types import LLMRequest, ValidationResult

#: minimal declared output schemas (required keys) — provider output must adhere.
SCHEMAS: dict[str, tuple] = {
    "ConflictExplanation": ("conflict_type", "explanation", "evidence_artifact_ids", "recommended_resolution"),
    "RelationExtraction": ("explanation", "evidence_artifact_ids"),
    "Generic": ("explanation",),
    # a schema the stub deliberately cannot satisfy (lacks severity_score) — used to prove invalid-output handling
    "StrictConflict": ("conflict_type", "explanation", "evidence_artifact_ids", "recommended_resolution", "severity_score"),
}


def validate(output_json: dict, req: LLMRequest, *, transport_ok: bool, policy_ok: bool,
             cost_usd: float, known_artifact_ids: set) -> ValidationResult:
    r = ValidationResult(reasons=[])
    r.transport_valid = bool(transport_ok)
    if not r.transport_valid:
        r.reasons.append("transport_failed"); return r

    required = SCHEMAS.get(req.schema_id, SCHEMAS["Generic"])
    r.schema_valid = isinstance(output_json, dict) and all(k in output_json for k in required)
    if not r.schema_valid:
        r.reasons.append(f"schema_missing:{[k for k in required if k not in (output_json or {})]}")

    cited = set(output_json.get("evidence_artifact_ids", []) or [])
    r.no_unknown_artifact_ids = cited <= set(known_artifact_ids)
    if not r.no_unknown_artifact_ids:
        r.reasons.append("unknown_artifact_ids_cited")
    # grounding: a claim must cite at least one KNOWN input artifact (unless none were provided)
    r.grounding_valid = (not req.input_artifact_ids) or (bool(cited) and r.no_unknown_artifact_ids)
    if not r.grounding_valid:
        r.reasons.append("ungrounded")

    r.policy_valid = bool(policy_ok)
    if not r.policy_valid:
        r.reasons.append("policy_violation")

    r.cost_valid = cost_usd <= req.routing_policy.max_cost_usd
    if not r.cost_valid:
        r.reasons.append("over_budget")

    promoted = bool(output_json.get("promoted"))
    r.no_promoted_claim_without_source = (not promoted) or bool(cited)
    if not r.no_promoted_claim_without_source:
        r.reasons.append("promoted_without_source")

    r.quality_valid = bool(str(output_json.get("explanation", "")).strip())
    return r
