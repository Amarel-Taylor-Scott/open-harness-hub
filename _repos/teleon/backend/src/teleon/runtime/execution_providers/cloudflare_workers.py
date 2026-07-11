"""src.teleon.runtime.execution_providers.cloudflare_workers — BYO-compute execution on the CUSTOMER's account.

The easiest onboarding for worker compute: a customer supplies a Cloudflare API token (a tenant SecretRef) and
workers spin up on THEIR Cloudflare account. We provision + dispatch; they execute + pay; their data never leaves
their account (a data-residency / `locality` win). This implements the ExecutionProviderPort with
compute_ownership = "customer_account":

  * NO token supplied            -> ProviderUnavailableResult (names the missing SecretRef) -> the dispatcher falls
                                    back to another backend (offline: execution.local_function_emulator@v1). Dev never
                                    needs a customer key.
  * token supplied, offline      -> ProviderUnavailableResult ("token accepted; live Cloudflare dispatch not wired in
                                    the offline build") -> local emulator runs it. Honest: no fake remote execution.
  * token supplied + live (real) -> deploy/dispatch a Worker on the customer's account via the Cloudflare API.

INVARIANTS (mirror the policy matrix): owns_truth=False (a backend RUNS a task, never owns truth — the
DurableFleetLedger + receipts stay ours); the API token is a tenant SecretRef resolved via an injected resolver,
NEVER logged or stored. Teleon-layer; stdlib only. Same pattern adds aws_lambda / gcp BYO providers (config, not code).
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ExecutionResult, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult

py_const_src_teleon_runtime_execution_providers_cloudflare_workers__PROVIDER_ID = "execution.cloudflare_workers@candidate"
py_const_src_teleon_runtime_execution_providers_cloudflare_workers__OFFLINE_EQUIVALENT = "execution.local_function_emulator@v1"


class py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider:
    """BYO Cloudflare Workers execution. ``token_secret_ref`` is a tenant SecretRef (e.g.
    secret://tenant/<id>/cloudflare_api_token); ``resolve_secret(ref) -> token | None`` is injected so the raw key is
    never embedded or logged. ``network_ok`` gates the (documented) live dispatch. compute_ownership=customer_account."""

    provider_id = py_const_src_teleon_runtime_execution_providers_cloudflare_workers__PROVIDER_ID
    compute_ownership = "customer_account"

    def __init__(self, *, account_id: str | None = None, token_secret_ref: str | None = None,
                 resolve_secret: Callable[[str], str | None] | None = None, network_ok: bool = False) -> None:
        self.account_id = account_id
        self.token_secret_ref = token_secret_ref
        self._resolve = resolve_secret or (lambda _ref: None)
        self.network_ok = network_ok

    def _token(self) -> str | None:
        return self._resolve(self.token_secret_ref) if self.token_secret_ref else None

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "serverless_function",
                "compute_ownership": self.compute_ownership, "byo": True,
                "onboarding": "supply a Cloudflare API token (SecretRef) [+ account_id]; workers run on YOUR account",
                "offline_equivalent": py_const_src_teleon_runtime_execution_providers_cloudflare_workers__OFFLINE_EQUIVALENT, "data_residency": "customer_account",
                "owns_truth": False, "token_secret_ref": self.token_secret_ref}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": bool(self._token()) and self.network_ok,
                "has_customer_token": bool(self._token()), "network_ok": self.network_ok}

    def eligible(self, task: dict, policy: dict) -> dict:
        """Eligible only if this backend is allowed by policy AND a customer token is present. SAFETY/CONFIG beats
        the objective — no token => not eligible, never a silent run on our own infra."""
        py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__allowed = self.provider_id.split("@")[0].split(".")[-1] in policy.get("allowed_backends", ["cloudflare_workers"]) \
            or "cloudflare_workers" in policy.get("byo_supported_backends", [])
        py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__has_token = bool(self._token())
        return {"eligible": bool(py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__allowed and py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__has_token), "reason": "ok" if (py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__allowed and py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__has_token)
                else ("no customer Cloudflare token (SecretRef)" if not py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_eligible__has_token else "backend not allowed by policy")}

    def estimate(self, py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_estimate__task: dict, py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_estimate__policy: dict) -> dict:
        # cost lands on the CUSTOMER's Cloudflare bill (≈0 to us); plus a data-residency/locality gain.
        return {"provider_id": self.provider_id, "cost_to_us": 0.0, "billed_to": "customer_account",
                "locality_gain": True, "owns_truth": False}

    def invoke(self, py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task: dict) -> Any:
        """Run the task on the customer's Cloudflare account. LIVE PATH = a real Cloudflare Workers AI call (the
        representative 'spin up a Cloudflare LLM' dispatch) using the customer token; offline / no token -> a
        non-consumable ProviderUnavailableResult so the dispatcher falls back to the local emulator. Never owns truth."""
        py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__token = self._token()
        if not py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__token:
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(
                self.provider_id, f"no customer Cloudflare API token (set {self.token_secret_ref or 'secret://tenant/<id>/cloudflare_api_token'})")
        if not self.network_ok:
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(
                self.provider_id, f"customer token accepted; network off — use {py_const_src_teleon_runtime_execution_providers_cloudflare_workers__OFFLINE_EQUIVALENT} for dev")
        if not self.account_id:
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(self.provider_id, "missing customer Cloudflare account_id for live dispatch")
        # LIVE: a real Workers AI call on the customer's account (their compute, their bill). serves_truth stays False.
        try:
            from src.teleon.dag.real_steps import real_cloudflare_ai
            py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__prompt = py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task.get("input_text") or py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task.get("prompt") or str(py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task.get("input", ""))
            py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__res = real_cloudflare_ai(py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__prompt or "ping", token=py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__token, account_id=self.account_id,
                                     model=py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task.get("model", "@cf/meta/llama-3.3-70b-instruct"), max_tokens=py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task.get("max_tokens", 256))
            return py_class_src_teleon_runtime_execution_provider__ExecutionResult(provider_id=self.provider_id, execution_id=f"cf-{abs(hash(py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__prompt)) & 0xffffff:x}",
                                   task_id=str(py_arg_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__task.get("task_id", "")), status="succeeded", is_truth=False,
                                   detail={"ran_on": "cloudflare_workers_ai", "billed_to": "customer_account",
                                           "model": py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__res["model"], "chars": len(py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__res["text"]), "usage": py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__res.get("usage", {})})
        except Exception as py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__e:  # noqa: BLE001 — surface auth/network errors as unavailable; the loop falls back
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(self.provider_id, f"live Cloudflare dispatch failed: {type(py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__e).__name__}: {str(py_local_src_teleon_runtime_execution_providers_cloudflare_workers__py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider_invoke__e)[:160]}")


__all__ = ["py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider", "py_const_src_teleon_runtime_execution_providers_cloudflare_workers__PROVIDER_ID", "py_const_src_teleon_runtime_execution_providers_cloudflare_workers__OFFLINE_EQUIVALENT"]
