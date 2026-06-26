"""src.teleon.io.inference_io — typed inference I/O projectors over the Inference Gateway (OIPS).

make_inference_request builds an InferenceRequest from an object + its preference + input, storing the input as a
HASH (never the raw prompt). project_route_decision names oips.select_provider's output as a ModelRouteDecision
(the governed-fallback trail, recorded — never silent). Pure + deterministic; no src.baltor import (inputs are
plain dicts / strings; the route dict comes from the gateway).
"""
from __future__ import annotations

import hashlib

_ROUTE_FIELDS = ("selected_provider_node_id", "fallback_used", "tier_downgraded", "blocked",
                 "fallback_reason_codes", "rejected_candidates", "requested_tier_code", "selected_tier_code")


def _sha(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()


def make_inference_request(*, object_id: str, requested_model_class: str, input_text: str, now: str,
                           preference_id: str = "", task_intent: str = "", tenant_id: str = "") -> dict:
    """Build an InferenceRequest. The raw prompt is NOT stored — only its hash."""
    input_hash = _sha(input_text)
    rid = "inreq_" + hashlib.blake2b(f"{object_id}|{preference_id}|{now}|{input_hash}".encode(), digest_size=10).hexdigest()
    return {"schema_version": "InferenceRequest", "request_id": rid, "object_id": object_id,
            "preference_id": preference_id or None, "task_intent": task_intent or None,
            "requested_model_class": requested_model_class, "input_hash": input_hash,
            "tenant_id": tenant_id or None, "created_at": now}


def project_route_decision(route: dict) -> dict:
    """Name oips.select_provider's output as a ModelRouteDecision (carrying the recorded fallback trail)."""
    out = {"schema_version": "ModelRouteDecision"}
    for k in _ROUTE_FIELDS:
        if k in route:
            out[k] = route[k]
    return out


__all__ = ["make_inference_request", "project_route_decision"]
