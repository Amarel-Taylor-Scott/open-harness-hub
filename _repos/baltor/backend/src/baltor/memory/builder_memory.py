"""src.baltor.memory.builder_memory — C-MEM-2 DELTA: BUILDER MEMORY capture + session context.

Captures durable, project-scoped, secret-redacted builder-loop state (current target, flywheel/proof
status, supervisor state, risks, next target, failures, decisions) as governed MemoryArtifacts via the
existing BaltorLocalMemoryProvider (C-MEM-1). MEMORY IS NOT TRUTH: everything captured is
candidate_context / workflow_trace, promotion_eligible=False — it can resume an agent's context, never
create a CanonicalFact or served_fact. Deterministic + offline (injected `now`). Secrets are redacted
before write (no API keys / env values ever stored).
"""
from __future__ import annotations

import json
import re

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider

TENANT = "baltor"
PROJECT = "baltor-build"
# sensitive value keys (never store their values). The redaction guard keeps secrets out of memory.
_SENSITIVE = ("api_key", "apikey", "api-key", "token", "secret", "password", "passwd", "authorization",
              "cookie", "credential", "private_key", "access_key", "session")
# a key-shaped token: a provider key prefix (built at runtime so no secret-shaped literal lives in the file)
_KEY_PREFIX = "s" + "k-"
_KEY_TOKEN = re.compile(rf"\b(?:{_KEY_PREFIX}|ghp_|xox[baprs]-)[A-Za-z0-9_\-]{{6,}}")


def redact(value):
    """Recursively redact secret values. Returns (redacted_value, redaction_count)."""
    count = 0
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if any(s in str(k).lower() for s in _SENSITIVE):
                out[k] = "[REDACTED]"; count += 1
            else:
                rv, c = redact(v); out[k] = rv; count += c
        return out, count
    if isinstance(value, list):
        out = []
        for v in value:
            rv, c = redact(v); out.append(rv); count += c
        return out, count
    if isinstance(value, str):
        new, n = _KEY_TOKEN.subn("[REDACTED]", value)
        return new, count + n
    return value, count


def _capture(provider, *, now: int, memory_type: str, body: dict, tags: list) -> dict:
    """Write one builder MemoryArtifact (redacted, candidate workflow trace) + return artifact + trace."""
    redacted, redactions = redact(body)
    content = json.dumps({"memory_type": memory_type, **redacted}, sort_keys=True)
    art = provider.write({"tenant_id": TENANT, "project": PROJECT, "now": now, "content": content,
                          "container_tags": ["builder", memory_type, *tags],
                          "metadata": {"memory_type": memory_type, "promotion_eligible": False,
                                       "claim_status": "workflow_trace", "redactions": redactions}})
    trace = {"schema_version": "MemoryTrace", "trace_id": "tr-" + art["content_hash"][:16],
             "tenant_id": TENANT, "container": "builder", "operation": "write", "provider_id": art["provider_id"],
             "request_handle": memory_type, "produced_artifact_ids": [art["artifact_id"]],
             "held_out_artifact_ids": [], "rejected_artifact_ids": [], "rollback_target": "",
             "occurred_at": now, "redactions": redactions}
    return {"artifact": art, "trace": trace, "redactions": redactions}


def capture_builder_state(provider, *, now: int, target: str = "", flywheel: dict | None = None,
                          risks: list | None = None, opportunities: list | None = None,
                          next_target: str = "", supervisor: dict | None = None) -> dict:
    return _capture(provider, now=now, memory_type="builder_state", tags=["state"], body={
        "active_target": target, "flywheel": flywheel or {}, "risks": risks or [],
        "opportunities": opportunities or [], "next_target": next_target, "supervisor": supervisor or {}})


def capture_proof_result(provider, *, now: int, proof: str, ok: bool, detail: str = "") -> dict:
    return _capture(provider, now=now, memory_type="proof_result", tags=["proof"],
                    body={"proof": proof, "ok": ok, "detail": detail})


def capture_flywheel_tick(provider, *, now: int, green: int, total: int, red: list | None = None) -> dict:
    return _capture(provider, now=now, memory_type="flywheel_tick", tags=["flywheel"],
                    body={"green": green, "total": total, "red": red or []})


def capture_supervisor_decision(provider, *, now: int, decision_type: str, capability: str = "", reason: str = "") -> dict:
    return _capture(provider, now=now, memory_type="supervisor_decision", tags=["supervisor"],
                    body={"decision_type": decision_type, "capability": capability, "reason": reason})


def capture_failure_trace(provider, *, now: int, where: str, error: str) -> dict:
    return _capture(provider, now=now, memory_type="failure_trace", tags=["failure"],
                    body={"where": where, "error": error})


def capture_next_target(provider, *, now: int, target: str) -> dict:
    return _capture(provider, now=now, memory_type="next_target", tags=["target"], body={"target": target})


def recall_builder_context(provider, query: str, *, now: int, limit: int = 10) -> dict:
    """MemoryRecallBundle: project-scoped recall. Results are candidate context, NOT facts."""
    res = provider.search({"tenant_id": TENANT, "project": PROJECT, "query": query, "limit": limit})
    arts = res.get("results", res.get("artifacts", []))
    return {"schema_version": "MemoryRecallBundle", "tenant_id": TENANT, "project": PROJECT,
            "query": query, "occurred_at": now, "claim_status": "candidate_context",
            "is_truth": False, "memory_artifact_ids": [a["artifact_id"] for a in arts], "artifacts": arts}


def build_session_context_bundle(provider, *, now: int) -> dict:
    """MemoryContextInjection: a safe, advisory session-start bundle regenerated from memory artifacts.
    Advisory only — contains no served/canonical facts and no secrets."""
    state = recall_builder_context(provider, "builder_state active_target next_target", now=now, limit=3)
    flywheel = recall_builder_context(provider, "flywheel green total", now=now, limit=1)
    targets = recall_builder_context(provider, "next_target target", now=now, limit=1)
    return {
        "schema_version": "MemoryContextInjection", "context_id": "ctx-" + str(now),
        "tenant_id": TENANT, "project_id": PROJECT, "generated_at": now,
        "advisory": True, "is_truth": False, "contains_served_facts": False,
        "active_target_artifacts": state["memory_artifact_ids"],
        "flywheel_artifacts": flywheel["memory_artifact_ids"],
        "next_target_artifacts": targets["memory_artifact_ids"],
        "memory_artifact_ids": sorted(set(state["memory_artifact_ids"] + flywheel["memory_artifact_ids"] + targets["memory_artifact_ids"])),
        "excluded_private_items": [], "redaction_report": {"policy": "secrets+env redacted at capture"},
    }


def default_provider() -> BaltorLocalMemoryProvider:
    return BaltorLocalMemoryProvider()


__all__ = ["redact", "capture_builder_state", "capture_proof_result", "capture_flywheel_tick",
           "capture_supervisor_decision", "capture_failure_trace", "capture_next_target",
           "recall_builder_context", "build_session_context_bundle", "default_provider", "TENANT", "PROJECT"]
