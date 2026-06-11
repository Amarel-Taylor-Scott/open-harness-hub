"""src.teleon.purpose_tasks.projections — ONE truth model, TWO redacted views (staff + customer).

The PurposeTask dashboard serves Baltor STAFF (build/debug/govern internals) and CUSTOMERS (capability health,
outputs, evidence, trust, approvals) over the SAME underlying data. Projection-only: these functions READ a
PurposeTask spec + run records and DERIVE views; they never mutate truth (mirrors supervisor_projection).

SAFETY CRUX — the customer view is built by EXPLICIT ALLOWLIST, not by removing a denylist. A field reaches the
customer ONLY if its key is in CUSTOMER_FIELDS; so a NEW staff-only field (a prompt, a secret, candidate code, a
cross-tenant trace) can never leak by default. Deny-by-default is the only safe redaction for a multi-tenant
dashboard. Pure + deterministic.
"""
from __future__ import annotations

from typing import Any

#: customer-visible PurposeTask spec fields (allowlist — deny by default).
CUSTOMER_SPEC_FIELDS = (
    "task_id", "purpose", "capability_slot", "input_contract", "output_contract",
    "connected_to", "capabilities", "success_criteria", "allowed_runtime_classes",
    "safety_class", "tenant_scope",
)
#: customer-visible run/evidence fields (allowlist). NOTE: NO internal prompts, secrets, candidate code,
#: cross-tenant traces, raw provider decisions, redteam payloads, or builder memory.
CUSTOMER_RUN_FIELDS = (
    "run_id", "status", "output", "output_contract", "source_handles", "receipt_id",
    "eval_score", "cost", "latency_ms", "runtime_class", "ran_at",
)
#: keys that must NEVER appear in a customer view (a redteam tripwire — the allowlist already excludes them,
#: this is the second belt: any of these surfacing in a customer projection is a hard failure).
STAFF_ONLY_FORBIDDEN_IN_CUSTOMER = (
    "internal_prompt", "prompt", "secret", "secret_ref", "secrets", "candidate_code", "implementation_src",
    "cross_tenant_trace", "raw_provider_decision", "redteam_payload", "builder_memory", "trace_ref",
    "debug", "candidate_paths", "orientation",
)


def staff_projection(spec: dict[str, Any], runs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Full internal view for Baltor operators — everything (purpose, contracts, candidates, runtime decisions,
    scorecards, orientation, costs, traces). Read-only; returns the source verbatim plus the runs."""
    return {"view": "staff", "spec": dict(spec), "runs": list(runs or []),
            "contract": {"source_of_truth": "PurposeTask spec + TaskRun records", "projection": "read-only"}}


def _allow(d: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {k: d[k] for k in fields if k in d}


#: customer-visible eval_suite summary fields (allowlist — deny by default). NOTE: `examples` is ABSENT on
#: purpose: an example's `expected` is an ANSWER KEY (the same staff-only class as a prompt/candidate code) —
#: only the shape (id, count, gate threshold, holdout policy, judge, gate basis) and a `benchmark_ref` (which
#: names a suite, not its answers) reach the customer.
CUSTOMER_EVAL_FIELDS = (
    "suite_id", "benchmark_ref", "gate_threshold", "holdout_policy", "judge", "gate_basis",
    "example_count", "source",
)


def _eval_contract_summary(suite: Any) -> dict[str, Any] | None:
    """Derive the customer-safe eval_suite summary (allowlist; the `expected` answer key never appears). For
    an inline suite the example COUNT is surfaced (derived) even if the raw suite hasn't been normalized.
    Returns None when the task declares no eval_suite."""
    if not isinstance(suite, dict):
        return None
    out = {k: suite[k] for k in CUSTOMER_EVAL_FIELDS if k in suite}
    if "example_count" not in out and isinstance(suite.get("examples"), list):
        out["example_count"] = len(suite["examples"])  # derived count — never the examples themselves
    return out or None


def customer_projection(spec: dict[str, Any], runs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Customer-safe view, built by ALLOWLIST (deny-by-default). Shows purpose · connected systems · allowed/
    forbidden capabilities · health · outputs + receipts + source handles · cost/latency · approvals — NEVER
    internal prompts, secrets, candidate code, cross-tenant traces, or other staff-only internals."""
    caps = spec.get("capabilities") or {}
    safe_spec = _allow(spec, CUSTOMER_SPEC_FIELDS)
    # data-access summary the customer cares about (derived, not raw): what it reads/writes + the forbidden floor
    safe_spec["data_access"] = {
        "connected_to": spec.get("connected_to", []),
        "forbidden_capabilities": caps.get("forbidden", []),
    }
    # eval_suite (the benchmark that defines DONE) — a SAFE SUMMARY, never the raw suite: the customer sees
    # THAT a benchmark gates their capability + its shape (id, example count, gate threshold, holdout policy,
    # judge), but NEVER the example `expected` outputs — the answer key is staff-only (deny-by-default, same
    # class as prompts/candidate code). benchmark_ref is shown (it names a suite, it is not the answers).
    eval_summary = _eval_contract_summary(spec.get("eval_suite"))
    if eval_summary is not None:
        safe_spec["eval_contract"] = eval_summary
    safe_runs = [_allow(r, CUSTOMER_RUN_FIELDS) for r in (runs or [])]
    # pending boundary-expansion approvals (customer-actionable) — surfaced as a safe summary if present
    approvals = [
        {"kind": a.get("kind"), "reason": a.get("reason"), "requested_at": a.get("requested_at")}
        for a in (spec.get("pending_approvals") or [])
    ]
    return {"view": "customer", "spec": safe_spec, "runs": safe_runs, "pending_approvals": approvals,
            "contract": {"source_of_truth": "PurposeTask spec + TaskRun records", "projection": "read-only",
                         "redaction": "allowlist (deny-by-default)"}}


def customer_view_is_clean(view: dict[str, Any]) -> bool:
    """True iff a customer projection contains NO staff-only/forbidden key anywhere (deep). The dashboard + the
    redteam proof both call this as the final tripwire before a customer view is served."""
    def _scan(obj: Any) -> bool:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in STAFF_ONLY_FORBIDDEN_IN_CUSTOMER:
                    return False
                if not _scan(v):
                    return False
        elif isinstance(obj, list):
            return all(_scan(x) for x in obj)
        return True
    return _scan(view)


__all__ = ["staff_projection", "customer_projection", "customer_view_is_clean",
           "CUSTOMER_SPEC_FIELDS", "CUSTOMER_RUN_FIELDS", "STAFF_ONLY_FORBIDDEN_IN_CUSTOMER",
           "CUSTOMER_EVAL_FIELDS"]
