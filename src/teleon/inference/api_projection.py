"""src.teleon.inference.api_projection — PROJECTION-ONLY read views for the shared LLM plane's /api/inference/*.

Pure functions that build the JSON each /api/inference endpoint would serve, from the existing architecture data +
the gateway. PROJECTION-ONLY: no truth is written, no network call, NO raw key or secret VALUE is exposed (provider
projections carry only has_secret_ref booleans). External-provider live calls are NOT made here — health reports an
honest non-live status. The HTTP wiring onto the admin server is a separate slice; this is the testable core.
"""
from __future__ import annotations

from typing import Any

from src.teleon.inference import oips
from src.teleon.inference import free_endpoint_intel as _fe
import json
from pathlib import Path

_A = Path(__file__).resolve().parents[3] / "architecture"

#: the endpoint surface these projections back (declared so a proof can assert the API exists)
ROUTES = {
    "GET /api/inference/providers": "providers",
    "GET /api/inference/model-graph": "model_graph",
    "GET /api/inference/free-endpoints": "free_endpoints",
    "GET /api/inference/preferences": "preferences_coverage",
    "GET /api/inference/health": "health",
    "GET /api/inference/receipts": "receipts",
    "POST /api/inference/resolve-preference": "resolve_preference",
    "POST /api/inference/structured-local": "infer_local",
}


def providers() -> list[dict]:
    """Provider nodes — numeric codes + has_secret_ref boolean ONLY (never a secret value or the ref string)."""
    out = []
    for n in oips.load_graph()["nodes"]:
        out.append({"node_id": n["node_id"], "tier_code": n.get("tier_code"),
                    "specialization_codes": n.get("specialization_codes", []), "status_code": n.get("status_code"),
                    "external": bool(n.get("external")), "has_secret_ref": n.get("secret_ref") is not None,
                    "local_equivalent": n.get("local_equivalent"), "label": n.get("display", "")})
    return out


def model_graph() -> dict:
    g = oips.load_graph()
    return {"nodes": providers(), "edges": g.get("edges", [])}  # nodes already redacted of secret values


def free_endpoints() -> list[dict]:
    return _fe.run_registry()  # EndpointDueDiligenceReport list — is_truth False, no raw keys


def preferences_coverage() -> dict:
    return json.loads((_A / "inference_preference_coverage.json").read_text(encoding="utf-8"))


def health() -> list[dict]:
    """ModelHealthSnapshot-ish — OFFLINE: local nodes healthy; external nodes report a non-live status (no probe)."""
    out = []
    for n in oips.load_graph()["nodes"]:
        out.append({"schema_version": "ModelHealthSnapshot.v1", "provider_node_id": n["node_id"],
                    "status": "requires_secret_ref" if n.get("external") else "healthy_local",
                    "live_checked": False})  # honest: no network probe offline
    return out


def receipts(receipt_store: list[dict] | None = None) -> list[dict]:
    """Projection of recorded ModelInvocationReceipts (caller-provided; no global mutable truth here)."""
    return list(receipt_store or [])


def resolve_preference(layers: list[dict]) -> dict:
    return oips.resolve_preference(layers)


def error_envelope(error_type: str, message: str, *, retryable: bool = False, error_id: str = "inf_err") -> dict:
    return {"schema_version": "ErrorEnvelope.v1", "error_id": error_id, "error_type": error_type,
            "retryable": retryable, "message": message}


def all_projections() -> dict:
    return {"providers": providers(), "model_graph": model_graph(), "free_endpoints": free_endpoints(),
            "preferences": preferences_coverage(), "health": health(), "routes": ROUTES}


__all__ = ["ROUTES", "providers", "model_graph", "free_endpoints", "preferences_coverage", "health",
           "receipts", "resolve_preference", "error_envelope", "all_projections"]
