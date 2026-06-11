"""src.teleon.inference.adapters — standardized, governed, swappable inference-provider adapters.

Every way of using a model — the local deterministic stub, an OpenAI-compatible HTTP endpoint (Ollama / vLLM /
OpenRouter / Groq / Gemini-OpenAI / …), or a provider-native HTTP API (Ollama native, Anthropic messages) — is a
subclass of ONE base class, `InferenceProviderAdapter`, with ONE contract. The Inference Gateway resolves an adapter
for a provider-graph node by its `adapter_style` (CONFIG, not code) and calls `.available()` / `.invoke()`. So:

  - STANDARDIZED: one base class + one result shape (`provider_unavailable` / an invoke result).
  - MULTIPLE API METHODS: distinct adapter subclasses, one per API style; add a new style = add a subclass + one
    REGISTRY entry. No `if provider == "x"` scattered through business logic.
  - EASY TO SWAP/CONFIGURE: a node's `adapter_style` (in architecture/model_provider_graph.json) decides the adapter;
    flipping it swaps the implementation with zero code change. Routing stays NUMERIC in oips; adapters are the
    pluggable execution layer beneath it.
  - GOVERNED: no provider SDK is imported at module load (HTTP uses stdlib urllib, imported LAZILY, and only when the
    caller explicitly allows network); secrets are referenced by `secret_ref`, never embedded; offline / no-secret /
    no-network ⇒ a `ProviderUnavailableResult` (graceful degradation to the gateway's local fallback); every result
    is `is_truth=False` — model output is a candidate, never served truth.

This module imports oips ONLY for the deterministic-stub format + the offline-default node id (so the LocalStub adapter
is byte-consistent with the live gateway). oips does NOT import this module (no cycle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.teleon.inference.oips import _stable, OFFLINE_DEFAULT_NODE

#: controlled vocabulary of API styles (a STYLE label, not a brand display-name; routing is numeric in oips)
ADAPTER_STYLES = ("deterministic_stub", "openai_compatible", "ollama_native", "anthropic_messages")


def provider_unavailable(node_id: str, reason_code: str) -> dict:
    """The single standard 'this provider could not run' result. Never carries output or a secret."""
    return {"available": False, "executed_node_id": None, "requested_node_id": node_id,
            "reason_code": reason_code, "output": None, "is_truth": False}


class InferenceProviderAdapter(ABC):
    """Base class every provider adapter extends. Subclasses set adapter_style + requires_secret/requires_network
    and implement invoke(). available() is a governed default: a provider that needs a secret it does not have, or a
    network call it is not allowed to make, is unavailable (so the gateway falls back) — never a silent failure."""

    adapter_style: str = "deterministic_stub"
    requires_secret: bool = False
    requires_network: bool = False

    def __init__(self, node: dict) -> None:
        self.node = node
        self.node_id = node["node_id"]
        self.secret_ref = node.get("secret_ref")  # a ref like secret://... — NEVER a raw key

    def available(self, *, secrets: set | None = None, allow_network: bool = False) -> tuple[bool, str]:
        secrets = secrets or set()
        if self.requires_network and not allow_network:
            return False, "network_disabled_offline"
        if self.requires_secret and (not self.secret_ref or self.secret_ref not in secrets):
            return False, "secret_ref_unavailable"
        return True, "available"

    @abstractmethod
    def invoke(self, *, object_id: str, input_text: str, now: str,
               secrets: set | None = None, allow_network: bool = False) -> dict:
        """Run the model. Return an invoke result (available=True, output, is_truth=False) or provider_unavailable()."""

    def describe(self) -> dict:
        return {"node_id": self.node_id, "adapter_style": self.adapter_style,
                "requires_secret": self.requires_secret, "requires_network": self.requires_network,
                "external": bool(self.node.get("external")), "has_secret_ref": self.secret_ref is not None}


class LocalStubAdapter(InferenceProviderAdapter):
    """The deterministic offline golden path. Always available; no secret; no network. Output is byte-identical to the
    gateway's stub (reuses oips._stable) so the adapter layer is consistent with infer_local."""

    adapter_style = "deterministic_stub"
    requires_secret = False
    requires_network = False

    def invoke(self, *, object_id, input_text, now, secrets=None, allow_network=False) -> dict:
        output = f"[local-stub deterministic output for {object_id}] " + _stable("out", input_text, now)
        return {"available": True, "executed_node_id": self.node_id, "requested_node_id": self.node_id,
                "reason_code": "deterministic_stub", "output": output, "is_truth": False}


class _HttpAdapter(InferenceProviderAdapter):
    """Shared base for HTTP providers. requires_network=True; the real call uses stdlib urllib imported LAZILY inside
    invoke (NEVER a provider SDK, never at module load). Offline / no-secret ⇒ provider_unavailable (graceful)."""

    requires_network = True

    def __init__(self, node: dict) -> None:
        super().__init__(node)
        # external nodes with a secret_ref require that secret; local HTTP (e.g. Ollama localhost) may need none
        self.requires_secret = bool(self.secret_ref) and bool(node.get("external"))

    def invoke(self, *, object_id, input_text, now, secrets=None, allow_network=False) -> dict:
        ok, reason = self.available(secrets=secrets, allow_network=allow_network)
        if not ok:
            return provider_unavailable(self.node_id, reason)
        if self.adapter_style != "openai_compatible":
            # the other API styles keep their seam until their live wiring lands (honest degrade)
            return provider_unavailable(self.node_id, "live_call_not_provisioned_for_this_api_style")
        # network IS allowed (+ secret if needed) — the REAL call, lazily imported + SDK-free.
        # Endpoint/model/key resolve from the node config first, env second (single source: .env),
        # so Ollama local/cloud, OpenRouter, vLLM are all just config on this ONE adapter.
        import json as _json
        import os as _os
        import time as _time
        import urllib.request  # noqa: F401  (stdlib only; the gated live-call path — not exercised offline)
        base_url = str(self.node.get("base_url") or _os.environ.get("OH_LLM_BASE_URL", "")).rstrip("/")
        model = self.node.get("model") or _os.environ.get("OH_LLM_MODEL", "")
        api_key = _os.environ.get("OH_LLM_API_KEY", "")  # resolved at call time; never embedded/echoed
        if not base_url or not model:
            return provider_unavailable(self.node_id, "no_base_url_or_model_configured")
        body = _json.dumps({"model": model, "temperature": 0.2,
                            "messages": [{"role": "user", "content": input_text}]}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(base_url + "/chat/completions", data=body, headers=headers, method="POST")
        started = _time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                payload = _json.loads(resp.read().decode("utf-8"))
            output = payload["choices"][0]["message"]["content"] or ""
        except Exception as exc:  # any live failure degrades, never fabricates
            return provider_unavailable(self.node_id, f"live_call_failed_{type(exc).__name__}")
        usage = payload.get("usage") or {}
        return {"available": True, "executed_node_id": self.node_id, "requested_node_id": self.node_id,
                "reason_code": "live_call", "output": output, "is_truth": False,
                "model": payload.get("model") or model,
                "latency_ms": int((_time.perf_counter() - started) * 1000),
                "tokens": {"input": usage.get("prompt_tokens"), "output": usage.get("completion_tokens")}}


class HttpOpenAICompatibleAdapter(_HttpAdapter):
    """One adapter for EVERY OpenAI-compatible endpoint — Ollama (local + cloud), vLLM, OpenRouter, Groq, Gemini's
    OpenAI-compat surface, etc. Swapping among them is just a different graph node (same adapter_style)."""
    adapter_style = "openai_compatible"


class OllamaNativeAdapter(_HttpAdapter):
    """Ollama's native /api/generate surface (a second 'method of using the API', distinct from openai_compatible)."""
    adapter_style = "ollama_native"


class AnthropicMessagesAdapter(_HttpAdapter):
    """Anthropic's native messages API (a third API method) — shows the base class spans non-OpenAI shapes too."""
    adapter_style = "anthropic_messages"


#: adapter_style -> adapter class. Add a provider METHOD by adding a subclass + one entry here (easy to extend).
REGISTRY: dict[str, type[InferenceProviderAdapter]] = {
    "deterministic_stub": LocalStubAdapter,
    "openai_compatible": HttpOpenAICompatibleAdapter,
    "ollama_native": OllamaNativeAdapter,
    "anthropic_messages": AnthropicMessagesAdapter,
}


def style_for_node(node: dict) -> str:
    """The adapter style for a node — from CONFIG (node['adapter_style']) with a safe default: the offline-default node
    is the deterministic stub; any other node defaults to openai_compatible (the broadest HTTP method)."""
    style = node.get("adapter_style")
    if style in REGISTRY:
        return style
    return "deterministic_stub" if node.get("node_id") == OFFLINE_DEFAULT_NODE else "openai_compatible"


def resolve_adapter(node: dict, *, registry: dict | None = None) -> InferenceProviderAdapter:
    """Resolve a node to a governed adapter instance by its configured adapter_style. This is the ONE swap point."""
    reg = registry or REGISTRY
    return reg[style_for_node(node)](node)


__all__ = ["ADAPTER_STYLES", "provider_unavailable", "InferenceProviderAdapter", "LocalStubAdapter",
           "HttpOpenAICompatibleAdapter", "OllamaNativeAdapter", "AnthropicMessagesAdapter",
           "REGISTRY", "style_for_node", "resolve_adapter"]
