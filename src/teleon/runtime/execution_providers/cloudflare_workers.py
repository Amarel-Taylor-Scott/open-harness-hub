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

from src.teleon.runtime.execution_provider import ExecutionResult, ProviderUnavailableResult

PROVIDER_ID = "execution.cloudflare_workers@candidate"
OFFLINE_EQUIVALENT = "execution.local_function_emulator@v1"


class CloudflareWorkersProvider:
    """BYO Cloudflare Workers execution. ``token_secret_ref`` is a tenant SecretRef (e.g.
    secret://tenant/<id>/cloudflare_api_token); ``resolve_secret(ref) -> token | None`` is injected so the raw key is
    never embedded or logged. ``network_ok`` gates the (documented) live dispatch. compute_ownership=customer_account."""

    provider_id = PROVIDER_ID
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
                "offline_equivalent": OFFLINE_EQUIVALENT, "data_residency": "customer_account",
                "owns_truth": False, "token_secret_ref": self.token_secret_ref}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": bool(self._token()) and self.network_ok,
                "has_customer_token": bool(self._token()), "network_ok": self.network_ok}

    def eligible(self, task: dict, policy: dict) -> dict:
        """Eligible only if this backend is allowed by policy AND a customer token is present. SAFETY/CONFIG beats
        the objective — no token => not eligible, never a silent run on our own infra."""
        allowed = self.provider_id.split("@")[0].split(".")[-1] in policy.get("allowed_backends", ["cloudflare_workers"]) \
            or "cloudflare_workers" in policy.get("byo_supported_backends", [])
        has_token = bool(self._token())
        return {"eligible": bool(allowed and has_token), "reason": "ok" if (allowed and has_token)
                else ("no customer Cloudflare token (SecretRef)" if not has_token else "backend not allowed by policy")}

    def estimate(self, task: dict, policy: dict) -> dict:
        # cost lands on the CUSTOMER's Cloudflare bill (≈0 to us); plus a data-residency/locality gain.
        return {"provider_id": self.provider_id, "cost_to_us": 0.0, "billed_to": "customer_account",
                "locality_gain": True, "owns_truth": False}

    def invoke(self, task: dict) -> Any:
        """Run the task on the customer's Cloudflare account. LIVE PATH = a real Cloudflare Workers AI call (the
        representative 'spin up a Cloudflare LLM' dispatch) using the customer token; offline / no token -> a
        non-consumable ProviderUnavailableResult so the dispatcher falls back to the local emulator. Never owns truth."""
        token = self._token()
        if not token:
            return ProviderUnavailableResult(
                self.provider_id, f"no customer Cloudflare API token (set {self.token_secret_ref or 'secret://tenant/<id>/cloudflare_api_token'})")
        if not self.network_ok:
            return ProviderUnavailableResult(
                self.provider_id, f"customer token accepted; network off — use {OFFLINE_EQUIVALENT} for dev")
        if not self.account_id:
            return ProviderUnavailableResult(self.provider_id, "missing customer Cloudflare account_id for live dispatch")
        # LIVE: a real Workers AI call on the customer's account (their compute, their bill). serves_truth stays False.
        try:
            from src.teleon.dag.real_steps import real_cloudflare_ai
            prompt = task.get("input_text") or task.get("prompt") or str(task.get("input", ""))
            res = real_cloudflare_ai(prompt or "ping", token=token, account_id=self.account_id,
                                     model=task.get("model", "@cf/meta/llama-3.3-70b-instruct"), max_tokens=task.get("max_tokens", 256))
            return ExecutionResult(provider_id=self.provider_id, execution_id=f"cf-{abs(hash(prompt)) & 0xffffff:x}",
                                   task_id=str(task.get("task_id", "")), status="succeeded", is_truth=False,
                                   detail={"ran_on": "cloudflare_workers_ai", "billed_to": "customer_account",
                                           "model": res["model"], "chars": len(res["text"]), "usage": res.get("usage", {})})
        except Exception as e:  # noqa: BLE001 — surface auth/network errors as unavailable; the loop falls back
            return ProviderUnavailableResult(self.provider_id, f"live Cloudflare dispatch failed: {type(e).__name__}: {str(e)[:160]}")


__all__ = ["CloudflareWorkersProvider", "PROVIDER_ID", "OFFLINE_EQUIVALENT"]
