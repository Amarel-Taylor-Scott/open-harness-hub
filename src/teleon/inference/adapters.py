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
from src.teleon.inference.receipts import base_host_of

#: controlled vocabulary of API styles (a STYLE label, not a brand display-name; routing is numeric in oips)
ADAPTER_STYLES = ("deterministic_stub", "openai_compatible", "ollama_native", "anthropic_messages")
#: sampling default for live chat calls (one definition — scripts.model_routes imports it for its signature default)
DEFAULT_TEMPERATURE = 0.2
#: live-call socket timeout in seconds (generous: local models can be slow; callers may pass timeout_s to tighten)
_LIVE_CALL_TIMEOUT_S = 300
#: env var holding the single SHARED fallback key — used ONLY when a node declares no secret_ref
_GLOBAL_KEY_ENV = "OH_LLM_API_KEY"


def resolve_secret_ref(secret_ref: str | None) -> str:
    """Resolve a node's secret_ref to its key VALUE at call time — PER NODE, so two external providers (or
    two tenants' BYOK keys) run side by side instead of sharing one global key. Never embedded, never logged.

      secret://env/<VAR>        -> that env var (upper-cased)
      secret://provider/<name>  -> <NAME>_API_KEY   (anthropic -> ANTHROPIC_API_KEY, openai -> OPENAI_API_KEY)
      (no secret_ref)           -> OH_LLM_API_KEY    (the single shared fallback for legacy/local nodes)
      anything else             -> that literal env var name (NEVER silently the global key)

    Returns '' when unset -> the adapter degrades to provider_unavailable (never a fabricated call)."""
    import os as _os
    if not secret_ref:
        return _os.environ.get(_GLOBAL_KEY_ENV, "")
    ref = secret_ref.strip()
    if ref.startswith("secret://env/"):
        return _os.environ.get(ref[len("secret://env/"):].upper(), "")
    if ref.startswith("secret://provider/"):
        name = ref[len("secret://provider/"):].strip("/").upper().replace("-", "_")
        return _os.environ.get(f"{name}_API_KEY", "")
    return _os.environ.get(ref, "")


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
    invoke (NEVER a provider SDK, never at module load). Offline / no-secret ⇒ provider_unavailable (graceful).

    The transport (resolve config + per-node secret + POST + degrade-on-failure) is shared; each API STYLE overrides
    four small seams — `_endpoint_path`, `_build_body`, `_auth_headers`, `_parse_output` (+ optional `_parse_usage`)
    — so a provider-native shape (Ollama /api/generate, Anthropic /v1/messages) is a subclass, not an `if`."""

    requires_network = True
    _endpoint_path = "/chat/completions"  # OpenAI-compatible default; overridden per style

    def __init__(self, node: dict) -> None:
        super().__init__(node)
        # external nodes with a secret_ref require that secret; local HTTP (e.g. Ollama localhost) may need none
        self.requires_secret = bool(self.secret_ref) and bool(node.get("external"))

    # ── per-API-style seams (override in subclasses; the transport below is shared) ──────────────────
    def _build_body(self, *, model: str, system: str, input_text: str,
                    max_tokens: int | None, temperature: float | None) -> dict:
        """OpenAI-compatible chat body (default)."""
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": input_text}]
        body: dict = {"model": model, "temperature": DEFAULT_TEMPERATURE if temperature is None else temperature,
                      "messages": messages, "stream": False}
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        return body

    def _auth_headers(self, key: str) -> dict:
        return {"Authorization": f"Bearer {key}"} if key else {}

    def _parse_output(self, payload: dict) -> str:
        return payload["choices"][0]["message"]["content"] or ""

    def _parse_model(self, payload: dict, default_model: str) -> str:
        return payload.get("model") or default_model

    def _parse_usage(self, payload: dict) -> dict:
        usage = payload.get("usage") or {}
        return {"input": usage.get("prompt_tokens"), "output": usage.get("completion_tokens")}

    def invoke(self, *, object_id, input_text, now, secrets=None, allow_network=False,
               system: str = "", max_tokens: int | None = None, temperature: float | None = None,
               api_key: str | None = None, timeout_s: int | None = None) -> dict:
        # Optional kwargs are per-CALL overrides used by route shims (scripts.model_routes).
        ok, reason = self.available(secrets=secrets, allow_network=allow_network)
        if not ok:
            return provider_unavailable(self.node_id, reason)
        # network IS allowed (+ secret if needed) — the REAL call, lazily imported + SDK-free. Endpoint/model
        # resolve from node config first, env second; the KEY resolves from THIS node's secret_ref (per-node,
        # so providers don't share one global key) with a call-time override winning.
        import json as _json
        import os as _os
        import time as _time
        import urllib.request  # noqa: F401  (stdlib only; the gated live-call path — not exercised offline)
        base_url = str(self.node.get("base_url") or _os.environ.get("OH_LLM_BASE_URL", "")).rstrip("/")
        model = self.node.get("model") or _os.environ.get("OH_LLM_MODEL", "")
        key = api_key if api_key is not None else resolve_secret_ref(self.secret_ref)  # PER-NODE; never embedded/echoed
        if not base_url or not model:
            return provider_unavailable(self.node_id, "no_base_url_or_model_configured")
        body = _json.dumps(self._build_body(model=model, system=system, input_text=input_text,
                                            max_tokens=max_tokens, temperature=temperature)).encode("utf-8")
        headers = {"Content-Type": "application/json", **self._auth_headers(key)}
        req = urllib.request.Request(base_url + self._endpoint_path, data=body, headers=headers, method="POST")
        started = _time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s or _LIVE_CALL_TIMEOUT_S) as resp:
                payload = _json.loads(resp.read().decode("utf-8"))
            output = self._parse_output(payload)
        except Exception as exc:  # any live failure degrades, never fabricates
            return provider_unavailable(self.node_id, f"live_call_failed_{type(exc).__name__}")
        return {"available": True, "executed_node_id": self.node_id, "requested_node_id": self.node_id,
                "reason_code": "live_call", "output": output, "is_truth": False,
                "model": self._parse_model(payload, model),
                # EFFECTIVE base host of the endpoint that actually served the call — hostname[:port]
                # only, never credentials — so the receipt can't name a node another host served.
                "base_host": base_host_of(base_url),
                "latency_ms": int((_time.perf_counter() - started) * 1000),
                "tokens": self._parse_usage(payload)}


class HttpOpenAICompatibleAdapter(_HttpAdapter):
    """One adapter for EVERY OpenAI-compatible endpoint — Ollama (local + cloud), vLLM, OpenRouter, Groq, Gemini's
    OpenAI-compat surface, etc. Swapping among them is just a different graph node (same adapter_style). Uses the
    base-class seams as-is (/chat/completions · messages body · Bearer auth · choices[0].message.content)."""
    adapter_style = "openai_compatible"


class OllamaNativeAdapter(_HttpAdapter):
    """Ollama's native /api/generate surface (a second API method, distinct from openai_compatible): a single-prompt
    body with options.temperature/num_predict, output in `response`. Local Ollama needs no key; Ollama Cloud takes a Bearer."""
    adapter_style = "ollama_native"
    _endpoint_path = "/api/generate"

    def _build_body(self, *, model, system, input_text, max_tokens, temperature):
        prompt = (system + "\n\n" if system else "") + input_text
        body: dict = {"model": model, "prompt": prompt, "stream": False,
                      "options": {"temperature": DEFAULT_TEMPERATURE if temperature is None else temperature}}
        if max_tokens is not None:
            body["options"]["num_predict"] = max_tokens
        return body

    def _parse_output(self, payload):
        return payload.get("response", "") or ""

    def _parse_usage(self, payload):
        return {"input": payload.get("prompt_eval_count"), "output": payload.get("eval_count")}


class AnthropicMessagesAdapter(_HttpAdapter):
    """Anthropic's native Messages API (a third API method) — a distinct shape: /messages, a top-level `system`, a
    REQUIRED max_tokens, x-api-key + anthropic-version headers, output in content[*].text. Proves the base class spans
    non-OpenAI shapes too. (The graph node's base_url already includes /v1, so the path is /messages.)"""
    adapter_style = "anthropic_messages"
    _endpoint_path = "/messages"
    _ANTHROPIC_VERSION = "2023-06-01"
    _DEFAULT_MAX_TOKENS = 1024  # Anthropic requires max_tokens; a sane default when the caller passes none

    def _build_body(self, *, model, system, input_text, max_tokens, temperature):
        body: dict = {"model": model, "max_tokens": max_tokens or self._DEFAULT_MAX_TOKENS,
                      "temperature": DEFAULT_TEMPERATURE if temperature is None else temperature,
                      "messages": [{"role": "user", "content": input_text}]}
        if system:
            body["system"] = system
        return body

    def _auth_headers(self, key):
        h = {"anthropic-version": self._ANTHROPIC_VERSION}
        if key:
            h["x-api-key"] = key
        return h

    def _parse_output(self, payload):
        return "".join(b.get("text", "") for b in (payload.get("content") or []) if b.get("type") == "text")

    def _parse_usage(self, payload):
        u = payload.get("usage") or {}
        return {"input": u.get("input_tokens"), "output": u.get("output_tokens")}


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


__all__ = ["ADAPTER_STYLES", "DEFAULT_TEMPERATURE", "provider_unavailable", "resolve_secret_ref",
           "InferenceProviderAdapter", "LocalStubAdapter", "HttpOpenAICompatibleAdapter",
           "OllamaNativeAdapter", "AnthropicMessagesAdapter", "REGISTRY", "style_for_node", "resolve_adapter"]
