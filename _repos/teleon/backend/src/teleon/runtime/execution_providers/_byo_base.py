"""src.teleon.runtime.execution_providers._byo_base — shared base for BYO / customer compute providers.

Common BYO behavior across Kubernetes / cloud functions / Cloudflare: resolve tenant credentials (SecretRefs, NEVER
logged), be ELIGIBLE only when creds are present (config/safety beats the objective — no silent run on our infra),
ESTIMATE as billed-to-the-customer, and on offline / missing creds / error return a non-consumable
ProviderUnavailableResult so the dispatcher falls back to the declared offline equivalent. A BYO provider NEVER owns
truth (the DurableFleetLedger + receipts stay ours). Subclasses implement ``_live(task)`` (the real dispatch).
Teleon-layer; stdlib only; never imports src.baltor.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ExecutionResult, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult


class py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider:
    provider_id = "execution.byo@candidate"
    backend = "byo"
    compute_ownership = "customer_account"        # customer_account (BYO key) | customer_managed (their cluster)
    offline_equivalent = "execution.local_function_emulator@v1"
    required_secrets: tuple = ()                   # SecretRef names the customer must supply

    def __init__(self, *, secret_refs: dict | None = None, resolve_secret: Callable[[str], str | None] | None = None,
                 endpoint: str | None = None, network_ok: bool = False, region: str | None = None) -> None:
        self.secret_refs = secret_refs or {}
        self._resolve = resolve_secret or (lambda _ref: None)
        self.endpoint = endpoint
        self.network_ok = network_ok
        self.region = region

    def _secret(self, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__secret__name: str) -> str | None:
        return self._resolve(self.secret_refs.get(py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__secret__name)) if self.secret_refs.get(py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__secret__name) else None

    def _creds_present(self) -> bool:
        return all(self._secret(s) for s in self.required_secrets)

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "backend": self.backend, "compute_ownership": self.compute_ownership,
                "byo": True, "required_secrets": list(self.required_secrets), "offline_equivalent": self.offline_equivalent,
                "data_residency": "customer", "owns_truth": False, "secret_refs": self.secret_refs}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": self._creds_present() and self.network_ok,
                "has_customer_creds": self._creds_present(), "network_ok": self.network_ok}

    def eligible(self, task: dict, policy: dict) -> dict:
        py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__allowed = (self.backend in policy.get("allowed_backends", [self.backend])
                   or self.backend in policy.get("byo_supported_backends", [self.backend]))
        py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__has = self._creds_present()
        return {"eligible": bool(py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__allowed and py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__has),
                "reason": "ok" if (py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__allowed and py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__has) else ("missing customer credentials " + str(list(self.required_secrets))
                                                          if not py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_eligible__has else "backend not allowed by policy")}

    def estimate(self, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_estimate__task: dict, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_estimate__policy: dict) -> dict:
        return {"provider_id": self.provider_id, "cost_to_us": 0.0, "billed_to": "customer", "owns_truth": False}

    def invoke(self, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_invoke__task: dict) -> Any:
        if not self._creds_present():
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(self.provider_id, f"missing customer credentials {list(self.required_secrets)}")
        if not self.network_ok:
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(self.provider_id, f"creds accepted; network off — use {self.offline_equivalent} for dev")
        try:
            return self._live(py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_invoke__task)
        except Exception as py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_invoke__e:  # noqa: BLE001 — surface as unavailable so the loop falls back; never crash
            return py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult(self.provider_id, f"live dispatch failed: {type(py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_invoke__e).__name__}: {str(py_local_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider_invoke__e)[:160]}")

    def _live(self, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__live__task: dict) -> Any:
        raise NotImplementedError

    def _result(self, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__result__task: dict, py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__result__detail: dict) -> py_class_src_teleon_runtime_execution_provider__ExecutionResult:
        return py_class_src_teleon_runtime_execution_provider__ExecutionResult(provider_id=self.provider_id, execution_id=f"{self.backend}-{abs(hash(str(py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__result__task))) & 0xffffff:x}",
                               task_id=str(py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__result__task.get("task_id", "")), status="succeeded", is_truth=False,
                               detail={**py_arg_src_teleon_runtime_execution_providers__byo_base__py_class_src_teleon_runtime_execution_providers__byo_base__ByoComputeProvider__result__detail, "compute_ownership": self.compute_ownership, "billed_to": "customer"})
