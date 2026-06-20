"""src.teleon.digestion.model_compatibility — for a digested skill, determine which model/provider it works with
(and which it does NOT), and on what inputs/outputs. Composes the Inference Gateway numeric provider graph.

Offline honesty: the local stub proves PLUMBING only (draft_only); external models are eval_only/candidate_only
until creds + a behavioral gate; a specialization mismatch is not_compatible. Output is advisory, never truth.
Pure + deterministic.
"""
from __future__ import annotations

from typing import Any

from src.teleon.inference import oips as _inf

#: required_models label → specialization code (from architecture/model_specialization_codes.json)
_SPEC = {"classification": 100, "extraction": 200, "summarization": 300, "coding": 400, "reasoning": 500,
         "judge": 600, "embeddings": 700, "rerank": 800, "vision": 900, "tool_use": 1000, "structured_output": 1100}


def _required_spec_codes(digest: dict) -> set[int]:
    codes = {_SPEC[m] for m in digest.get("required_models", []) if m in _SPEC}
    # a skill that requires tools implies tool_use + structured_output as a baseline
    if digest.get("required_tools"):
        codes |= {1000, 1100}
    return codes or {500}  # default: reasoning


def run_model_compatibility(digest: dict, *, now: str, candidate_nodes: list[str] | None = None,
                            available_secrets: set | None = None, provider_health: dict | None = None) -> dict[str, Any]:
    """Test the digested skill against candidate model nodes. Returns a per-node ModelCompatibilityReport list +
    a summary of which models work / don't. Uses the Inference Gateway graph; no real model call offline."""
    graph = _inf.load_graph()
    idx = {n["node_id"]: n for n in graph["nodes"]}
    creds = set(available_secrets or set())
    health = provider_health or {}
    nodes = candidate_nodes or [n["node_id"] for n in graph["nodes"]]
    need = _required_spec_codes(digest)
    reports: list[dict] = []
    for nid in nodes:
        node = idx.get(nid)
        if not node:
            continue
        spec_match = bool(need & set(node.get("specialization_codes", [])))
        structured_ok = 1100 in set(node.get("specialization_codes", []))
        credentialed = (node.get("secret_ref") is None) or (node["secret_ref"] in creds)
        healthy = health.get(nid, True)
        if not spec_match:
            use = "not_compatible"
        elif not node.get("external"):
            use = "draft_only"            # local stub: plumbing only
        elif credentialed and healthy:
            use = "production_allowed_after_gate"
        else:
            use = "eval_only"             # external, not credentialed offline → cannot verify yet
        reports.append({"schema_version": "ModelCompatibilityReport.v1", "skill_id": digest["skill_id"],
                        "provider_node_id": nid, "tier_code": node.get("tier_code"),
                        "specialization_match": spec_match, "structured_output_ok": structured_ok,
                        "input_class": "object", "cost_estimate": None, "latency_ms": None,
                        "failure_modes": [] if spec_match else ["specialization_not_supported"],
                        "recommended_use": use, "tested_via": "inference_gateway:local_stub(offline)",
                        "is_truth": False})
    works = [r["provider_node_id"] for r in reports if r["recommended_use"] in ("production_allowed_after_gate", "draft_only", "eval_only")]
    incompatible = [r["provider_node_id"] for r in reports if r["recommended_use"] == "not_compatible"]
    return {"skill_id": digest["skill_id"], "required_spec_codes": sorted(need), "reports": reports,
            "works_with": works, "not_compatible_with": incompatible,
            "note": "offline: local stub=draft_only; external=eval_only until creds+gate; mismatch=not_compatible"}


__all__ = ["run_model_compatibility"]
