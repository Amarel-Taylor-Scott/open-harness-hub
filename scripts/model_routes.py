"""Provider-neutral chat/LLM route for OpenHubForAI — local now, cloud later.

The text-generation sibling of ``scripts/embeddings.py``: ONE resolver, env-
driven, so builder polish / explanations / labeling run on a **local Gemma via
Ollama** today and a hosted model later with **no code change**. It is optional
and never the source of truth — if no model is reachable, ``complete()`` returns
``None`` and callers fall back to deterministic output.

MODEL-PLANE UNIFICATION (step 1): ``ChatRoute`` is now a SHIM over the OIPS
inference plane (``src.teleon.inference``). The public surface is unchanged for
callers (same constructor, ``.complete()``, ``.health()``, ``.summary()``,
attributes), but internally every attempted completion goes select-provider →
adapter dispatch and mints a ``ModelInvocationReceipt`` (hashes + metadata only,
``llm_output_is_truth: false``), appended durably to
``dist/local-services-state/model-receipts/receipts.jsonl`` with
``plane: "model_routes"``. The receipt records the EFFECTIVE base host
(hostname[:port], never credentials) plus the provider-graph node the configured
``base_url`` binds to, so a receipt can never name a node another host served.

NETWORK GATE (unified with OIPS — one switch): ``OH_INFERENCE_ALLOW_NETWORK=1``
is the same owner switch the OIPS gateway uses for live execution. To preserve
this route's long-standing local-default behavior, loopback base URLs
(localhost / 127.0.0.1 / ::1 / 0.0.0.0) are allowed WITHOUT the switch (offline
dev keeps working unchanged); any non-local base_url requires the switch, for
both ``health()`` and ``complete()`` — a route we may not call is not healthy.

Talks the OpenAI-compatible ``/chat/completions`` shape, which Ollama, vLLM,
LM Studio, OpenAI, Azure, Together, etc. all speak. Stdlib-only (``urllib``).

Environment:

  ==========================  ====================================================
  OH_LLM_BACKEND              auto | http-openai | none           (default: auto)
  OH_LLM_BASE_URL             default http://localhost:11434/v1   (Ollama OpenAI-compat)
  OH_LLM_API_KEY              bearer token (optional for local servers)
  OH_LLM_MODEL                default "gemma4"  (any local/hosted chat model, e.g. Gemma 4)
  OH_INFERENCE_ALLOW_NETWORK  "1" allows NON-local base URLs (same switch as OIPS);
                              loopback base URLs never need it
  ==========================  ====================================================
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

# DEPENDENCY-LAW direction (verified before wiring): architecture/portfolio_dependency_law.json
# forbids import edges only AMONG the three brand package roots (src/openhubforai must not import
# src/teleon, etc.). scripts/ is repo TOOLING, not a brand layer — the law file itself says so and
# scripts/check_portfolio_dependency_law.py scans only the src/* roots; ~46 scripts already import
# src.teleon. So the DIRECT shim (this module → src.teleon.inference) is legal, and the inverted
# design (a parallel receipts emitter in an OHH-importable location) was unnecessary.
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:  # lets `python3 scripts/model_routes.py` work like `-m scripts...`
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import adapters as _adapters  # noqa: E402
from src.teleon.inference import oips as _oips  # noqa: E402
from src.teleon.inference import receipts as _receipts  # noqa: E402

#: provider-graph node ids this route binds to (ids defined in architecture/model_provider_graph.json)
OLLAMA_LOCAL_NODE_ID = "model.ollama_local@candidate"            # exact match for the local default endpoint
LOCAL_OPENAI_COMPATIBLE_NODE_ID = "model.local_openai_compatible@candidate"  # any other loopback endpoint
ENV_OPENAI_COMPATIBLE_NODE_ID = "model.env_openai_compatible@candidate"      # any unmatched non-local endpoint
#: receipt plane stamp for this route (the OIPS gateway stamps "oips"; llm_gateway/foundry come in later waves)
RECEIPT_PLANE = "model_routes"
#: hostnames that count as LOCAL (loopback / this machine) — callable without the network switch,
#: preserving the route's original offline-dev behavior. Anything else is env-gated.
LOCAL_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})
#: stable ids for receipts minted by this plane (object/preference identity, not a model id)
_OBJECT_ID = "plane:model_routes"
_PREFERENCE_ID = "pref.model_routes@v1"
_RECEIPT_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"  # matches the repo's receipt created_at convention


def _graph_node(node_id: str) -> dict:
    """A provider-graph node by id. Raises loudly on a missing id — these ids are load-bearing config."""
    for node in _oips.load_graph()["nodes"]:
        if node["node_id"] == node_id:
            return node
    raise KeyError(f"provider-graph node missing: {node_id}")


# Single source: the local default endpoint is the ollama_local node's base_url BINDING in
# architecture/model_provider_graph.json (never a second literal here), so route and graph cannot drift.
DEFAULT_BASE_URL = _graph_node(OLLAMA_LOCAL_NODE_ID)["base_url"]
DEFAULT_MODEL = "gemma4"                          # swap to your local Gemma tag
_HEALTH_TIMEOUT_S = 2
_COMPLETE_TIMEOUT_S = 120


def _is_local_url(url: str | None) -> bool:
    try:
        return (urlsplit(str(url or "")).hostname or "") in LOCAL_HOSTNAMES
    except Exception:
        return False


def _network_allowed(url: str | None) -> bool:
    """ONE network switch, shared with the OIPS gateway: OH_INFERENCE_ALLOW_NETWORK=1 allows any
    endpoint; loopback endpoints are always allowed (the route's original local-default behavior)."""
    return os.environ.get("OH_INFERENCE_ALLOW_NETWORK", "") == "1" or _is_local_url(url)


def _norm_url(url: str) -> str:
    """Normalized endpoint identity for node binding: lowercased scheme+host, port, path, no trailing /."""
    split = urlsplit(str(url).rstrip("/"))
    port = f":{split.port}" if split.port else ""
    return f"{split.scheme.lower()}://{(split.hostname or '').lower()}{port}{split.path}"


@dataclass
class ChatRoute:
    name: str            # http-openai | none
    model_id: str
    base_url: str | None
    api_key: str | None

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def health(self) -> bool:
        """Quick reachability probe (GET {base}/models). Never raises. A non-local base_url without
        OH_INFERENCE_ALLOW_NETWORK=1 reports unhealthy — a route we may not call is not usable."""
        if self.name == "none" or not self.base_url:
            return False
        if not _network_allowed(self.base_url):
            return False
        try:
            import urllib.request  # lazy stdlib, like the adapter layer — only on an allowed probe
            req = urllib.request.Request(self.base_url.rstrip("/") + "/models", headers=self._headers())
            with urllib.request.urlopen(req, timeout=_HEALTH_TIMEOUT_S) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _bound_node(self) -> dict:
        """The provider-graph node this route's EFFECTIVE base_url binds to: exact base_url match
        first (openai_compatible nodes only), else the generic local node for loopback hosts, else
        the env-configured node. The returned copy overlays THIS route's base_url/model/api-key-less
        binding so the adapter dispatches to exactly the endpoint the receipt names."""
        graph_nodes = _oips.load_graph()["nodes"]
        target = _norm_url(self.base_url or "")
        bound: dict | None = None
        for node in graph_nodes:
            if (node.get("base_url") and _adapters.style_for_node(node) == "openai_compatible"
                    and _norm_url(node["base_url"]) == target):
                bound = node
                break
        if bound is None:
            fallback_id = (LOCAL_OPENAI_COMPATIBLE_NODE_ID if _is_local_url(self.base_url)
                           else ENV_OPENAI_COMPATIBLE_NODE_ID)
            bound = _graph_node(fallback_id)
        return {**bound, "base_url": self.base_url, "model": self.model_id}

    def _complete_via_oips(self, system: str, user: str, *, max_tokens: int, temperature: float) -> str | None:
        """select provider → adapter dispatch → mint + persist a ModelInvocationReceipt. The receipt
        is HONEST: blocked/failed calls record reason codes and allowed_use 'blocked' (output hash of
        the empty string); only metadata + hashes are persisted, never prompts or keys."""
        node = self._bound_node()
        now = datetime.now(timezone.utc).strftime(_RECEIPT_TS_FMT)
        # Presence-only credential set for selection: this route is single-provider BY API CONTRACT
        # (callers configured exactly one endpoint), so auth is delegated to the live server exactly
        # as before — the bearer travels only in the HTTP header, never into routing or receipts.
        creds = {node["secret_ref"]} if node.get("secret_ref") else set()
        resolved = _oips.resolve_preference([{
            "preference_id": _PREFERENCE_ID,
            "model_class_preference": {"tier_code": node["tier_code"]},
            "allowed_provider_nodes": [node["node_id"]],
            "disallowed_provider_nodes": [],
            "fallback_policy": {"allow_fallback": False, "fail_closed_if_unavailable": True},
            "data_policy": {},
        }])
        route = _oips.select_provider(resolved, available_secrets=creds, provider_health={})
        output: str | None = None
        result: dict = {}
        if not route.get("blocked") and route.get("selected_provider_node_id") == node["node_id"]:
            adapter = _adapters.resolve_adapter(node)
            result = adapter.invoke(object_id=_OBJECT_ID, input_text=user, now=now, secrets=creds,
                                    allow_network=_network_allowed(self.base_url),
                                    system=system, max_tokens=max_tokens, temperature=temperature,
                                    api_key=self.api_key or None, timeout_s=_COMPLETE_TIMEOUT_S)
            if result.get("available"):
                output = result.get("output")
        if output is None:
            # no usable output (network-gated / unavailable / live failure) — record it honestly;
            # this route NEVER substitutes stub text (callers own their deterministic fallback).
            reasons = set(route.get("fallback_reason_codes", []))
            if result:
                reasons.add(str(result.get("reason_code") or "live_call_failed"))
            route = {**route, "blocked": True, "fallback_reason_codes": sorted(reasons)}
        receipt = _oips.build_receipt(
            object_id=_OBJECT_ID, preference_id=resolved["preference_id"],
            requested_model_class=f"tier:{node['tier_code']}/", route=route,
            executed_node=node["node_id"], executed_model=str(result.get("model") or self.model_id),
            input_text=f"{system}\n{user}", output_text=output or "", now=now,
            tokens=result.get("tokens"), latency_ms=result.get("latency_ms"),
            base_host=result.get("base_host") or _receipts.base_host_of(self.base_url))
        _receipts.persist_receipt(receipt, plane=RECEIPT_PLANE)
        return output

    def complete(self, system: str, user: str, *, max_tokens: int = 2048,
                 temperature: float = _adapters.DEFAULT_TEMPERATURE) -> str | None:
        """Return assistant text, or None on any failure (caller falls back). Every ATTEMPTED call
        (route not disabled) mints + persists a ModelInvocationReceipt via the OIPS plane."""
        if self.name == "none" or not self.base_url:
            return None
        try:
            return self._complete_via_oips(system, user, max_tokens=max_tokens, temperature=temperature)
        except Exception:
            return None  # contract above all: never raise into callers; they fall back deterministically

    def summary(self) -> dict:
        return {"backend": self.name, "model": self.model_id, "base_url": self.base_url}


def resolve_route(model: str | None = None, backend: str | None = None) -> ChatRoute:
    backend = backend or os.environ.get("OH_LLM_BACKEND") or "auto"
    if backend == "none":
        return ChatRoute("none", model or "none", None, None)
    base_url = os.environ.get("OH_LLM_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.environ.get("OH_LLM_API_KEY")
    model_id = model or os.environ.get("OH_LLM_MODEL") or DEFAULT_MODEL
    return ChatRoute("http-openai", model_id, base_url, api_key)


if __name__ == "__main__":
    r = resolve_route()
    print(json.dumps({**r.summary(), "reachable": r.health()}, indent=2))
