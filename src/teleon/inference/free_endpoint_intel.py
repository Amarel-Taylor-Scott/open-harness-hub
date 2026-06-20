"""src.teleon.inference.free_endpoint_intel — FREE / LIMITED LLM ENDPOINT INTELLIGENCE.

A governed due-diligence layer for free/limited LLM endpoints, discovery/gateway repos, and browser runtimes.
It feeds OpenToolsHub (metadata), the Inference Gateway (routing proposals), and Teleon/Baltor (governed use).

Core law (no exceptions):
  * Free endpoint discovery is METADATA. Official provider docs decide eligibility.
  * Third-party free-tier claims are UNVERIFIED until confirmed against official docs.
  * The Inference Gateway decides routing; the ModelInvocationReceipt records reality.
  * A browser/WebContainer runtime (ClawLess) is NOT an LLM endpoint — it is a sandbox/runtime candidate.
  * Shared-key / bypass / reverse-engineered repos are QUARANTINE — never an approved provider.
  * Raw keys are never stored. LLM output is never truth; Baltor governs serving.

Branches on NUMERIC class codes (architecture/free_endpoint_class_codes.json), never on display strings.
Composes the Inference Gateway (src.teleon.inference.oips) for provider-node proposals. Pure + deterministic;
no network, no SDK import, no src.baltor import (Teleon-side; Baltor consumes via Baltor->Teleon).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.teleon.inference import oips as _inf

_A = Path(__file__).resolve().parents[3] / "architecture"
_cache: dict[str, Any] = {}


def _load(name: str) -> dict:
    if name not in _cache:
        _cache[name] = json.loads((_A / name).read_text(encoding="utf-8"))
    return _cache[name]


def _codes() -> dict[str, Any]:
    return _load("free_endpoint_class_codes.json")


def _policy() -> dict[str, Any]:
    return _load("free_limited_llm_endpoint_policy.json")


def _class_label(code: int) -> str:
    for c in _codes()["classes"]:
        if c["code"] == code:
            return c["label"]
    return "unknown_quarantine"


def _quarantine_floor() -> int:
    return _codes()["quarantine_floor"]


# A raw provider key looks like a known prefix + a long token. Built so this module never contains a literal key.
# (OpenRouter "sk-or-..." keys are caught by the "sk-" prefix; the bare "or-" prefix is too common in prose.)
_KEY_PREFIXES = ("sk-", "gsk_", "hf_", "AIza", "nvapi-")
_MARKER_RE = re.compile("|".join(re.escape(m) for m in _policy()["quarantine_markers"]), re.IGNORECASE)


def _has_raw_key(blob: str) -> bool:
    for p in _KEY_PREFIXES:
        if re.search(re.escape(p) + r"[A-Za-z0-9_\-]{16,}", blob):
            return True
    return False


def _string_values(obj: Any) -> list[str]:
    """Recursively collect string VALUES (never dict keys) — so field names like 'reverse_engineered_markers'
    or human notes that DESCRIBE what a repo excludes never trip the marker/key scanners."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _string_values(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _string_values(v)]
    return []


# ── classification ──────────────────────────────────────────────────────────────────────────────────────────
def classify(*, signals: dict, free_text: str = "", declared_role: str | None = None) -> tuple[int, list[str]]:
    """Return (class_code, reasons). Driven by SIGNAL booleans + an EXPLICIT markers_text (the repo's own
    marketing language) — never by scanning field names or descriptive notes (a discovery list that says it
    'excludes reverse-engineered services' must NOT be quarantined). Quarantine markers and reverse-engineering
    DOMINATE (a free-key/bypass repo can never be re-described into 'official'). Browser runtimes are never
    LLM endpoints. An 'official' claim WITHOUT official docs cannot reach candidate (unknown_quarantine)."""
    sig = signals or {}
    text = free_text or ""

    if sig.get("reverse_engineered_markers"):
        return 910, ["reverse_engineered_access_marker"]
    if sig.get("shared_key_markers") or (text and _MARKER_RE.search(text)):
        return 900, ["shared_key_or_bypass_marker"]
    if text and _has_raw_key(text):
        return 900, ["raw_key_present_in_listing"]
    if sig.get("browser_runtime") or sig.get("webcontainer") or declared_role == "browser_agent_runtime":
        return 700, ["browser_webcontainer_runtime_not_an_llm_endpoint"]
    if declared_role == "discovery_list":
        return 600, ["discovery_list_metadata_only"]
    if declared_role == "self_hosted_gateway":
        return 500, ["self_hosted_gateway_lab_candidate_only"]
    if declared_role == "inference_aggregator" or sig.get("aggregator"):
        return 400, ["official_inference_aggregator"]
    # official provider path — REQUIRES official docs
    if sig.get("has_official_docs"):
        if sig.get("paid_required"):
            return 300, ["official_but_payment_required_not_free"]
        if sig.get("trial_credit_only"):
            return 200, ["official_trial_credit_only"]
        return 100, ["official_free_limited_provider"]
    return 990, ["claims_free_but_no_official_docs"]


# ── risk scoring ──────────────────────────────────────────────────────────────────────────────────────────
_RISK_DIMS = ["official_docs_confidence_inv", "tos_risk", "data_retention_risk", "free_tier_stability_inv",
              "rate_limit_clarity_inv", "key_custody_risk", "secret_handling_risk", "prompt_logging_risk",
              "intermediary_risk", "production_suitability_inv"]


def score_risk(class_code: int, signals: dict) -> tuple[int, dict]:
    """Deterministic risk across dimensions (each 0=low .. 100=high). Quarantine classes pin to max risk."""
    sig = signals or {}
    if class_code >= _quarantine_floor():
        return 100, {d: 100 for d in _RISK_DIMS}
    d: dict[str, int] = {}
    d["official_docs_confidence_inv"] = 0 if sig.get("has_official_docs") else 80
    d["tos_risk"] = 20 if sig.get("has_official_docs") else 60
    d["data_retention_risk"] = {"free_tier_used_to_improve_products": 70, "partial": 40}.get(
        str(sig.get("data_retention_documented")), 55)
    d["free_tier_stability_inv"] = 30 if class_code == 300 else (45 if class_code in (200, 400) else 35)
    d["rate_limit_clarity_inv"] = 20 if sig.get("rate_limit_documented") is True else 55
    d["key_custody_risk"] = 50 if class_code in (400, 500) else 25  # aggregators/proxies hold/forward keys
    d["secret_handling_risk"] = 60 if class_code == 500 else (45 if class_code == 700 else 25)
    d["prompt_logging_risk"] = 60 if str(sig.get("data_retention_documented")) == "free_tier_used_to_improve_products" else 35
    d["intermediary_risk"] = 55 if class_code in (400, 500) else 10
    d["production_suitability_inv"] = {300: 25}.get(class_code, 70)  # only paid/official is production-suitable
    score = round(sum(d.values()) / len(d))
    return score, d


# ── due diligence ──────────────────────────────────────────────────────────────────────────────────────────
def _phase_from_risk(risk: int) -> int:
    if risk >= 80:
        return 0
    if risk >= 60:
        return 1
    if risk >= 45:
        return 2
    if risk >= 30:
        return 3
    return 4


def due_diligence(endpoint: dict) -> dict:
    """Full per-endpoint verdict: classify -> risk -> policy-capped recommended phase + governed uses.
    The recommended phase is the MINIMUM of (policy.max_recommended_phase, risk-derived phase); an official
    claim without official docs is quarantined; raw keys force rejection. Output is advisory; is_truth is false."""
    values_blob = " ".join(_string_values(endpoint))
    code, reasons = classify(signals=endpoint.get("signals", {}), free_text=endpoint.get("markers_text", ""),
                             declared_role=endpoint.get("declared_role"))
    risk, dims = score_risk(code, endpoint.get("signals", {}))
    pol = _policy()["by_class"][str(code)]
    raw_key = _has_raw_key(values_blob)
    if raw_key and code < _quarantine_floor():
        code, reasons = 900, reasons + ["raw_key_present_force_quarantine"]
        risk, dims = score_risk(code, endpoint.get("signals", {}))
        pol = _policy()["by_class"][str(code)]
    phase = min(int(pol["max_recommended_phase"]), _phase_from_risk(risk))
    if pol["max_recommended_phase"] < 0:
        phase = -1
    is_provider = code in (100, 200, 300, 400)  # only official endpoints/aggregators are inference providers
    proposal = propose_provider_node(endpoint, code) if is_provider and phase >= 1 else None
    return {
        "schema_version": "EndpointDueDiligenceReport.v1",
        "endpoint_id": endpoint.get("endpoint_id") or endpoint.get("repo_id") or "(unknown)",
        "class_code": code, "class_label": _class_label(code),
        "risk_score": risk, "risk_dimensions": dims,
        "recommended_phase": phase,
        "teleon_use": pol["teleon_use"], "baltor_use": pol["baltor_use"], "executable": pol["executable"],
        "allowed_data_class": pol["max_data_class_without_review"],
        "raw_key_detected": raw_key, "is_inference_provider": is_provider,
        "provider_node_proposal": proposal,
        "reasons": reasons + [f"policy_max_phase={pol['max_recommended_phase']}", f"risk_phase={_phase_from_risk(risk)}"],
        "is_truth": False,
    }


def propose_provider_node(endpoint: dict, class_code: int) -> dict:
    """Propose a model_provider_graph node (status candidate) for an official endpoint. This is a PROPOSAL only
    — it is NOT written to the graph (agents propose, Baltor disposes). It declares secret_ref required + a
    local_equivalent (the offline stub) + ModelInvocationReceipt required, matching the gateway node shape."""
    return {
        "proposed_node_id": endpoint.get("endpoint_id", "endpoint.unknown") + "#provider",
        "status": "candidate", "status_code": 200, "external": True,
        "secret_ref": endpoint.get("secret_ref"),
        "secret_ref_required": True,
        "local_equivalent": _inf.OFFLINE_DEFAULT_NODE,
        "receipt_required": True,
        "allowed_data_classes": ["public", "synthetic"],
        "written_to_graph": False,
        "note": "PROPOSAL only; not added to model_provider_graph.json. Requires secret_ref + local_equivalent "
                "+ ModelInvocationReceipt; routing decided by the Inference Gateway, never a direct call.",
    }


def assess_gateway_repo(repo: dict) -> dict:
    """Assess a gateway/discovery repo or browser runtime. Metadata only — never imports/executes the repo."""
    code, reasons = classify(signals=repo.get("signals", {}), free_text=repo.get("markers_text", ""),
                             declared_role=repo.get("role"))
    if code < _quarantine_floor() and _has_raw_key(" ".join(_string_values(repo))):
        code, reasons = 900, ["raw_key_present_in_listing"]
    pol = _policy()["by_class"][str(code)]
    return {
        "schema_version": "GatewayRepoAssessment.v1",
        "repo_id": repo.get("repo_id") or repo.get("example_id") or "(unknown)",
        "class_code": code, "class_label": _class_label(code), "role": pol["role"],
        "executable": pol["executable"], "is_inference_provider": code in (100, 200, 300, 400),
        "import_allowed": False,  # slice 1: metadata only, nothing imported
        "recommended_phase": int(pol["max_recommended_phase"]),
        "portfolio_mapping": repo.get("portfolio_mapping", {}),
        "reasons": reasons, "is_truth": False,
    }


def to_opentools_metadata(report: dict) -> dict:
    """Project a due-diligence report into OpenToolsHub ToolArtifact-style METADATA. Executable use is gated
    through Teleon/Inference Gateway — the public hub never exposes an executable credentialed endpoint."""
    return {
        "object_type": "ToolArtifact", "tool_id": f"endpoint:{report['endpoint_id']}",
        "provider_class": report["class_label"], "risk_score": report["risk_score"],
        "free_or_limited": True, "executable": False,
        "executable_use_gated_through": "teleon_inference_gateway",
        "secret_policy": "secret_ref_only_no_raw_keys",
        "allowed_data_class": report["allowed_data_class"], "recommended_phase": report["recommended_phase"],
        "is_truth": False,
    }


# ── batch over the seeded registry + watchlist ───────────────────────────────────────────────────────────────
def run_registry() -> list[dict]:
    return [due_diligence(e) for e in _load("free_limited_llm_endpoint_registry.json")["endpoints"]]


def run_watchlist() -> list[dict]:
    wl = _load("gateway_repo_watchlist.json")
    return [assess_gateway_repo(r) for r in (wl.get("repos", []) + wl.get("quarantine_examples", []))]


__all__ = ["classify", "score_risk", "due_diligence", "propose_provider_node", "assess_gateway_repo",
           "to_opentools_metadata", "run_registry", "run_watchlist"]
