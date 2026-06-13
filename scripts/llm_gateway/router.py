#!/usr/bin/env python3
"""scripts.llm_gateway.router — the LLM Gateway: the single, policy-aware entry point for model calls.

CANONICAL LAYER: `src/teleon/inference` (OIPS) owns provider-ordering truth; this gateway is the
Baltor-era selection path during the runtime extraction. Keep routing-preference order here in sync
with the OIPS numeric graph — do not fork a second source of provider-ordering truth.

``gateway.complete(request, policy)`` selects a provider by tenant policy + routing preference, calls it,
VALIDATES the output, and FALLS BACK on a retryable failure OR a validation failure — recording every
attempt in an LLMTrace. Policy violations are EXCLUDED up front (never retried as transport). External
providers are never selected for a tenant that disallows external APIs or for restricted-classification data.
A per-(input,prompt,model) cache returns a prior good result without re-calling. Nothing here knows about
CFPB or any domain — processors build requests; only the gateway talks to providers.
"""
from __future__ import annotations

from scripts.llm_gateway.providers import ProviderError, ProviderRegistry, default_registry
from scripts.llm_gateway.types import LLMRequest, LLMResponse, LLMTrace
from scripts.llm_gateway.validation import validate
from scripts.security.tenant_catalog import TenantPolicy


def _model_config_hash(spec) -> str:
    from scripts.llm_gateway.types import _sha
    return _sha({"provider": spec.provider_id, "adapter": spec.adapter, "models": spec.models})


class LLMGateway:
    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or default_registry()
        self._cache: dict[str, LLMResponse] = {}

    def _candidates(self, req: LLMRequest) -> list[str]:
        order = list(req.routing_policy.preferred_providers) + list(req.routing_policy.fallback_providers)
        return order or ["stub.local"]

    def _policy_ok(self, spec, policy: TenantPolicy, data_classification: str) -> bool:
        if data_classification == "restricted" and spec.external:
            return False  # restricted data never leaves to an external API
        return policy.allows_llm_provider(spec.provider_id, external=spec.external)

    def complete(self, req: LLMRequest, policy: TenantPolicy, *, known_artifact_ids: set | None = None) -> LLMResponse:
        known = set(known_artifact_ids or req.input_artifact_ids)
        trace = LLMTrace(request_id=req.request_id)
        attempt = 0

        for pid in self._candidates(req):
            spec = self.registry.get(pid)
            if spec is None:
                trace.record(provider=pid, model="?", prompt_hash=req.prompt_hash(), model_config_hash="",
                             attempt=attempt, status="unknown_provider")
                continue
            mch = _model_config_hash(spec)
            # policy gate — EXCLUDED, not retried as transport
            if not self._policy_ok(spec, policy, req.data_classification):
                trace.record(provider=pid, model="?", prompt_hash=req.prompt_hash(), model_config_hash=mch,
                             attempt=attempt, status="policy_blocked", reason="tenant/classification disallows")
                continue
            adapter = self.registry.adapter_for(spec)
            if not adapter.available(spec):
                trace.record(provider=pid, model="?", prompt_hash=req.prompt_hash(), model_config_hash=mch,
                             attempt=attempt, status="unavailable", reason="secret/provider unavailable")
                continue

            ck = req.cache_key(mch)
            if ck in self._cache:
                cached = self._cache[ck]
                trace.record(provider=pid, model=cached.model, prompt_hash=req.prompt_hash(),
                             model_config_hash=mch, attempt=attempt, status="cache_hit")
                cached.trace = {"attempts": trace.attempts, "cached": True}
                return cached

            if attempt >= req.routing_policy.max_attempts:
                break
            attempt += 1
            try:
                out = adapter.complete(spec, req)
            except ProviderError as e:
                trace.record(provider=pid, model="?", prompt_hash=req.prompt_hash(), model_config_hash=mch,
                             attempt=attempt, status=f"error:{e.reason}", reason=("retryable" if e.retryable else "fatal"))
                continue  # fall back to the next provider

            vr = validate(out["output_json"], req, transport_ok=True, policy_ok=True,
                          cost_usd=out["usage"].get("cost_estimate_usd", 0.0), known_artifact_ids=known)
            trace.record(provider=pid, model=out["model"], prompt_hash=req.prompt_hash(), model_config_hash=mch,
                         attempt=attempt, status="ok" if vr.ok else "invalid", validation=vr.as_dict())
            if vr.ok:
                resp = LLMResponse(request_id=req.request_id, provider=pid, model=out["model"], endpoint=out["endpoint"],
                                   status="ok", output_json=out["output_json"], raw_response_ref="",
                                   usage=out["usage"], validation=vr.as_dict(),
                                   trace={"attempts": trace.attempts, "prompt_hash": req.prompt_hash(),
                                          "model_config_hash": mch})
                self._cache[ck] = resp
                return resp
            # invalid output → fall back to next provider (repair/escalation)

        return LLMResponse(request_id=req.request_id, provider="none", model="none", endpoint="none",
                           status="needs_human", output_json={}, usage={}, validation={},
                           trace={"attempts": trace.attempts, "prompt_hash": req.prompt_hash()})
