"""src.teleon.runtime.execution_backend_selector — choose an EXECUTION BACKEND for a CapabilityTask by
POLICY + PRICEBOOK + provider health + available credentials. Pure + deterministic (all inputs injected).
Canonical TELEON home (runtime selection is a Teleon concern); imports only the stdlib (never Baltor). Baltor
consumes this through a re-export shim at src/baltor/workers/execution_backend_selector.py (Baltor → Teleon).

The point: the SAME task can run on the local emulator today, a Kubernetes worker tomorrow, or a cloud
function the day after — by changing policy/pricebook, NOT code. Kubernetes and cloud functions are
interchangeable backends that can run side by side. Hard guards keep browser/GPU/open-ended/control-plane
work off generic cloud functions unless a policy explicitly allows it WITH PROOF. Missing credentials or
unhealthy providers fall back to the local/emulator correctness invariant — never crash.
"""
from __future__ import annotations

import json
from pathlib import Path

_A = Path(__file__).resolve().parents[3] / "architecture"
#: CLOUD-AGNOSTIC default: the serverless-function FAMILY. AWS Lambda is just ONE peer here, never canonical.
#: This is only a fallback — the authoritative set is read from the policy matrix's `generic_cloud_functions`
#: (config, not code), so a new serverless provider is added by editing data, not this literal.
GENERIC_FUNCTIONS = {"aws_lambda@candidate", "gcp_cloud_run_function@candidate", "gcp_cloud_function@candidate",
                     "azure_function@candidate", "cloudflare_workers@candidate", "openfaas_knative@candidate"}
_FALLBACK_ORDER = ("local_function_emulator@v1", "local_subprocess@v1")


def generic_functions(policy_matrix: dict | None = None) -> set:
    """The serverless-function family, sourced from CONFIG (`generic_cloud_functions` in the policy matrix) so
    it is cloud-agnostic and extensible without code changes. Falls back to GENERIC_FUNCTIONS if absent."""
    pm = policy_matrix if policy_matrix is not None else _load("execution_backend_policy_matrix.json")
    return set(pm.get("generic_cloud_functions") or GENERIC_FUNCTIONS)


#: any serverless-function backend uses the SAME action (provider-agnostic) — resolved by suffix so a new
#: cloud function provider needs no entry here either.
ACTIONS = {
    "local_function_emulator@v1": "use_local_function_emulator", "local_subprocess@v1": "use_local_subprocess",
    "k8s_deployment_worker@candidate": "use_k8s_deployment_worker", "k8s_job@candidate": "use_k8s_job",
    "cloud_run_job@candidate": "use_cloud_run_job", "browser_pool@candidate": "use_browser_pool",
    "gpu_pool@candidate": "use_gpu_pool", "sandbox_worker@candidate": "use_sandbox_worker",
}


def _action_for(backend: str) -> str:
    """Provider-agnostic action: any serverless-function backend → 'use_cloud_function' (no per-vendor literal)."""
    if backend in ACTIONS:
        return ACTIONS[backend]
    if backend in GENERIC_FUNCTIONS or "function" in backend or backend.startswith(("aws_", "gcp_", "azure_", "cloudflare_", "openfaas_")):
        return "use_cloud_function"
    return "use_backend"


def _load(name: str) -> dict:
    return json.loads((_A / name).read_text())


def _est_cost(backend: str, pricebook: dict, runtime_ms: int) -> float:
    pb = pricebook.get("backends", {}).get(backend, {})
    secs = max(0.0, runtime_ms / 1000.0)
    return pb.get("request_cost", 0.0) + pb.get("duration_cost_per_s", 0.0) * secs + pb.get("idle_cost_per_s", 0.0) * secs


def _decision(action: str, backend: str, reason: str, **extra) -> dict:
    return {"schema_version": "ExecutionProviderDecision", "action": action, "backend": backend,
            "reason": reason, **extra}


def select_backend(task: dict, *, policy_matrix: dict | None = None, pricebook: dict | None = None,
                   provider_health: dict | None = None, available_creds: set | None = None,
                   policy_override: dict | None = None) -> dict:
    """Decide the execution backend for `task`. `task`: {capability_id, worker_bucket, estimated_runtime_ms,
    requires_browser, requires_gpu, tenant_private, payload_bytes}. `provider_health`: backend→bool.
    `available_creds`: set of configured backend ids (local/emulator always available). `policy_override`:
    optional {preferred_backends:[...], excluded_backends:[...]} to force a switch (with proof)."""
    policy_matrix = policy_matrix or _load("execution_backend_policy_matrix.json")
    pricebook = pricebook or _load("execution_backend_pricebook.json")
    health = provider_health or {}
    creds = set(available_creds or set()) | {"local_function_emulator@v1", "local_subprocess@v1"}
    bucket = task.get("worker_bucket", "utility")
    bp = policy_matrix["buckets"].get(bucket, {})
    runtime = int(task.get("estimated_runtime_ms", 500))
    # offline fallback is single-sourced from the matrix (config: offline_default_backend), with the stdlib
    # _FALLBACK_ORDER as the last-resort default so this stdlib-only module never hard-fails if the key is absent.
    offline_default = policy_matrix.get("offline_default_backend", _FALLBACK_ORDER[0])
    fallback_order = (offline_default, *(b for b in _FALLBACK_ORDER if b != offline_default))

    eligible = list((policy_override or {}).get("eligible") or bp.get("eligible", _FALLBACK_ORDER))
    excluded = set(bp.get("excluded_by_default", [])) | set((policy_override or {}).get("excluded_backends", []))

    # HARD GUARDS — browser/gpu/open-ended/control-plane never go to a generic cloud function by default,
    # unless a policy_override explicitly allows it (caller asserts a proof exists).
    allow_generic = bool((policy_override or {}).get("allow_generic_functions"))
    generic = generic_functions(policy_matrix)   # cloud-agnostic serverless family, from CONFIG not a literal
    if not allow_generic and (task.get("requires_browser") or task.get("requires_gpu")
                              or bucket in ("browser", "model_inference", "cpu_gpu_compute", "open_ended_agent", "control_plane")):
        excluded |= generic

    eligible = [b for b in eligible if b not in excluded]
    if not eligible:
        eligible = list(fallback_order)

    # available + healthy candidates (a backend with no creds, or health False, is not runnable now)
    runnable = [b for b in eligible if (b in creds) and health.get(b, True)]
    if not runnable:
        fb = next((b for b in fallback_order if b in eligible), fallback_order[0])
        return _decision("fallback_due_to_provider_health", fb,
                         f"no eligible backend is available+healthy (creds/health) → fall back to {fb}",
                         eligible=eligible, considered=eligible)

    # ranking: an explicit policy preference order wins (a deliberate switch); else cheapest by pricebook
    pref = (policy_override or {}).get("preferred_backends") or bp.get("preferred_backends") or []
    chosen = next((b for b in pref if b in runnable), None)
    basis = "policy preferred_backends"
    if chosen is None:
        chosen = min(runnable, key=lambda b: (_est_cost(b, pricebook, runtime), b))   # cheapest, then stable
        basis = "lowest pricebook cost (telemetry/pricing-driven)"

    return _decision(_action_for(chosen), chosen,
                     f"selected by {basis} for bucket {bucket!r}", eligible=eligible,
                     est_cost=round(_est_cost(chosen, pricebook, runtime), 4), basis=basis)


__all__ = ["select_backend", "GENERIC_FUNCTIONS", "generic_functions", "ACTIONS"]
