"""src.teleon.llm_port — the LLM ABSTRACTION LAYER: any LLM behind ONE uniform port.

Why (owner 2026-06-21): more LLMs keep arriving. Components must depend on a model-AGNOSTIC port, never a concrete
provider, so a FUTURE model drops in with ZERO component change. The port's selectable LLMs are POPULATED FROM our
registries — the model index (_repos/shared-backend-components/architecture/model_index.json) + the provider lanes (scripts/_llm_client.PROVIDERS) —
so adding a model to a registry makes it selectable everywhere; routing reuses the Teleon inference plane
(_repos/teleon/backend/src/teleon/inference) and never re-implements it. serves_truth=false (an LLM is never a source of truth).

  port = select_llm("auto")             # route via the gateway (the plane picks the lane)
  port = select_llm("claude-opus-4-8")  # a model_id from the model index → its provider lane
  port = select_llm("ollama")           # a named provider lane
  text = port.complete(system, user)    # uniform call; port.available() is honest about keys
  fn   = as_callable(port)              # adapt to a (prompt)->str, or None if unavailable (→ caller's deterministic path)
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

_MODEL_INDEX = _resource("architecture") / "model_index.json"
_SYSTEM = "You are a precise extraction/answering assistant. Answer ONLY what is asked."


@runtime_checkable
class LLMPort(Protocol):
    name: str
    def available(self) -> bool: ...
    def complete(self, system: str, user: str, *, max_tokens: int = 400) -> str: ...


class CallableLLM:
    """Wrap any (prompt)->str callable (tests / custom integrations)."""
    def __init__(self, fn: Callable[[str], str], *, name: str = "callable"):
        self._fn, self.name = fn, name
    def available(self) -> bool:
        return True
    def complete(self, system: str, user: str, *, max_tokens: int = 400) -> str:
        try:
            return self._fn(f"{system}\n\n{user}" if system else user) or ""
        except Exception:  # noqa: BLE001
            return ""


class ProviderLLM:
    """Wrap a named _llm_client lane (ollama / cloudflare / …) + an optional model_id. available iff the lane key is set."""
    def __init__(self, provider: str = "ollama", model: str | None = None):
        self.name, self._p, self._model = f"provider:{provider}", provider, model
    def _prov(self) -> dict:
        from scripts._llm_client import resolve_provider
        return resolve_provider(self._p)
    def available(self) -> bool:
        try:
            return bool(self._prov().get("key"))
        except Exception:  # noqa: BLE001
            return False
    def complete(self, system: str, user: str, *, max_tokens: int = 400) -> str:
        try:
            import os
            from scripts._llm_client import chat
            prov = self._prov()
            if not prov.get("key"):
                return ""
            model = self._model or os.environ.get("OH_LLM_MODEL") or prov.get("model") or "qwen2.5:7b"
            return chat(model, system, user, prov, max_tokens=max_tokens).get("text", "")
        except Exception:  # noqa: BLE001
            return ""


class GatewayLLM:
    """Route via the Teleon inference plane (lane selection) → the chosen provider lane. Degrades to the default lane.
    Never re-implements routing — it delegates to _repos/teleon/backend/src/teleon/inference."""
    def __init__(self, objective: str = "cheapest"):
        self.name, self._obj = "gateway", objective
    def _delegate(self) -> ProviderLLM:
        try:
            from src.teleon.inference.lane_selection import select_lane
            lane = select_lane(self._obj) or {}
            prov = lane.get("provider") or lane.get("lane")
            if prov:
                return ProviderLLM(prov, lane.get("model"))
        except Exception:  # noqa: BLE001
            pass
        try:
            from scripts._llm_client import DEFAULT_PROVIDER
            return ProviderLLM(DEFAULT_PROVIDER)
        except Exception:  # noqa: BLE001
            return ProviderLLM("ollama")
    def available(self) -> bool:
        return self._delegate().available()
    def complete(self, system: str, user: str, *, max_tokens: int = 400) -> str:
        return self._delegate().complete(system, user, max_tokens=max_tokens)


class DeterministicLLM:
    """Honest no-LLM port — never fabricates; signals unavailable so callers fall back to their deterministic path."""
    name = "deterministic"
    def available(self) -> bool:
        return False
    def complete(self, system: str, user: str, *, max_tokens: int = 400) -> str:
        return ""


#: registered adapter factories — a FUTURE provider that isn't a simple lane drops in here, zero component change.
_ADAPTERS: dict[str, Callable[[], LLMPort]] = {
    "auto": GatewayLLM, "gateway": GatewayLLM, "deterministic": DeterministicLLM,
}


def register_llm_adapter(name: str, factory: Callable[[], LLMPort]) -> None:
    """Register a new LLM adapter by name (the future-proofing hook — components consuming select_llm() never change)."""
    _ADAPTERS[str(name)] = factory


def _model_index() -> list[dict]:
    try:
        return json.loads(_MODEL_INDEX.read_text(encoding="utf-8")).get("entries", [])
    except Exception:  # noqa: BLE001
        return []


def _lanes() -> dict:
    try:
        from scripts._llm_client import PROVIDERS
        return dict(PROVIDERS)
    except Exception:  # noqa: BLE001
        return {}


def available_llms() -> dict:
    """The selectable LLMs, POPULATED FROM the registries: model-index model_ids + provider lanes + adapters.
    Adding a model to _repos/shared-backend-components/architecture/model_index.json (or a lane to _llm_client) makes it selectable here, no code change."""
    return {"adapters": sorted(_ADAPTERS), "lanes": sorted(_lanes()),
            "models": [e.get("model_id") for e in _model_index() if e.get("model_id")], "serves_truth": False}


def select_llm(name: str = "auto", **kw) -> LLMPort:
    """Resolve a name to an LLMPort. Accepts: a registered adapter; a model_id from the model index (→ its provider
    lane); a 'provider:<lane>' or bare lane name; else the gateway. Never raises — unknown/unconfigured degrades to a
    DeterministicLLM (honest)."""
    if name in _ADAPTERS:
        return _ADAPTERS[name]()
    if isinstance(name, str):
        for e in _model_index():                          # a model_id from the registry → its provider lane
            if e.get("model_id") == name:
                return ProviderLLM(e.get("provider", "ollama"), name)
        bare = name.split(":", 1)[-1]
        if name.startswith("provider:") or bare in _lanes():
            return ProviderLLM(bare)
    return GatewayLLM()


def as_callable(port) -> Callable[[str], str] | None:
    """Adapt an LLMPort / a (prompt)->str callable / a name / None to a (prompt)->str callable, or None when no LLM is
    available (so the caller uses its deterministic fallback — honest, never fabricated)."""
    if port is None:
        return None
    if callable(port) and not isinstance(port, str) and not hasattr(port, "complete"):
        return port                                       # already a (prompt)->str callable
    p = port if hasattr(port, "complete") else select_llm(port if isinstance(port, str) else "auto")
    if not p.available():
        return None
    return lambda prompt: p.complete(_SYSTEM, prompt)


__all__ = ["LLMPort", "CallableLLM", "ProviderLLM", "GatewayLLM", "DeterministicLLM",
           "register_llm_adapter", "available_llms", "select_llm", "as_callable"]
