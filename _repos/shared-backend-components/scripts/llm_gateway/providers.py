#!/usr/bin/env python3
"""scripts.llm_gateway.providers — provider specs + replaceable adapters + registry.

stub.local@v1            — deterministic, offline, no key (the default; proves the gateway end-to-end)
openai.responses@v1      — OpenAI Responses API; loads key ONLY from api_key_ref (env://…); network-guarded
openai_compatible.http@v1 — any OpenAI-compatible base_url (Azure / vLLM / Ollama / custom); network-guarded

Network is OFF unless BALTOR_LLM_ALLOW_NETWORK=1 — so a self-test NEVER makes a network call: a configured-
but-network-disabled provider raises a RETRYABLE error and the router falls back. Provider config carries
``api_key_ref`` (a secret ref), never a raw key.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from scripts.llm_gateway.secrets import SecretsResolver, UnavailableSecret
from scripts.llm_gateway.types import LLMRequest


class ProviderError(Exception):
    def __init__(self, reason: str, *, retryable: bool) -> None:
        super().__init__(reason)
        self.reason = reason
        self.retryable = retryable


def _network_allowed() -> bool:
    return os.environ.get("BALTOR_LLM_ALLOW_NETWORK", "") in ("1", "true", "yes")


@dataclass
class LLMProviderSpec:
    provider_id: str
    adapter: str
    external: bool
    api_key_ref: str = ""        # MUST be a secret ref (env://…), never a raw key
    base_url: str = ""
    models: list = field(default_factory=list)

    def has_raw_key(self) -> bool:
        """True if the config appears to embed a raw key instead of a ref — a hygiene violation."""
        return bool(self.api_key_ref) and not SecretsResolver.is_ref(self.api_key_ref)


def _stub_output(req: LLMRequest) -> dict:
    """Deterministic, schema-shaped, GROUNDED output (cites only the request's input artifacts; never promotes)."""
    return {
        "task_type": req.task_type,
        "explanation": f"[stub] {req.task_type} over {len(req.input_artifact_ids)} artifact(s)",
        "conflict_type": "semantic_tension",
        "recommended_resolution": "needs_human",
        "evidence_artifact_ids": list(req.input_artifact_ids),
        "promoted": False,
        "requires_verification": True,
    }


class ProviderAdapter:
    name = "base"

    def available(self, spec: LLMProviderSpec) -> bool:
        raise NotImplementedError

    def complete(self, spec: LLMProviderSpec, req: LLMRequest) -> dict:
        raise NotImplementedError


class StubAdapter(ProviderAdapter):
    name = "stub.local@v1"

    def available(self, spec: LLMProviderSpec) -> bool:
        return True

    def complete(self, spec: LLMProviderSpec, req: LLMRequest) -> dict:
        return {"output_json": _stub_output(req), "model": "stub", "endpoint": "local",
                "usage": {"input_tokens": 0, "output_tokens": 0, "cost_estimate_usd": 0.0}, "raw": "[stub]"}


class _NetworkAdapter(ProviderAdapter):
    """Shared base for real providers — available iff its secret resolves; network is guarded."""
    def available(self, spec: LLMProviderSpec) -> bool:
        return SecretsResolver.has(spec.api_key_ref)

    def complete(self, spec: LLMProviderSpec, req: LLMRequest) -> dict:
        if not self.available(spec):
            raise ProviderError("unavailable_secret", retryable=False)
        if not _network_allowed():
            # never touch the network in a self-test; let the router fall back
            raise ProviderError("network_disabled", retryable=True)
        # real call would go here (urllib to spec.base_url) using SecretsResolver.get(spec.api_key_ref);
        # intentionally not exercised offline. Returns are validated like any other provider output.
        raise ProviderError("network_call_not_implemented_offline", retryable=True)


class OpenAIResponsesAdapter(_NetworkAdapter):
    name = "openai.responses@v1"


class OpenAICompatibleAdapter(_NetworkAdapter):
    name = "openai_compatible.http@v1"


_ADAPTERS = {a.name: a for a in (StubAdapter(), OpenAIResponsesAdapter(), OpenAICompatibleAdapter())}


class ProviderRegistry:
    def __init__(self) -> None:
        self.specs: dict[str, LLMProviderSpec] = {}

    def register(self, spec: LLMProviderSpec) -> None:
        self.specs[spec.provider_id] = spec

    def adapter_for(self, spec: LLMProviderSpec) -> ProviderAdapter:
        return _ADAPTERS[spec.adapter]

    def get(self, provider_id: str) -> LLMProviderSpec | None:
        return self.specs.get(provider_id)


def default_registry() -> ProviderRegistry:
    r = ProviderRegistry()
    r.register(LLMProviderSpec("stub.local", "stub.local@v1", external=False, models=["stub"]))
    r.register(LLMProviderSpec("openai.default", "openai.responses@v1", external=True,
                               api_key_ref="env://OPENAI_API_KEY", base_url="https://api.openai.com/v1",
                               models=["gpt-5.6-sol"]))
    r.register(LLMProviderSpec("local.openai_compatible", "openai_compatible.http@v1", external=False,
                               api_key_ref="env://LOCAL_LLM_API_KEY", base_url="http://127.0.0.1:11434/v1",
                               models=["qwen"]))
    return r
