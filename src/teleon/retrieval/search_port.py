"""src.teleon.retrieval.search_port — the SEARCH abstraction: any grounded-search provider behind ONE port (agnostic).

Same pattern as ocr/llm/reranker/embedding ports: consumers depend on the PORT, never a specific provider, so a future
provider drops in with ZERO caller change. Selectable providers are POPULATED FROM architecture/search_provider_registry
.json; the WIRED baseline is the keyless grounded search (Wikipedia / US Federal Register via real_steps, registry-
selected — network-gated, honest-unavailable offline). Keyed providers (tavily/brave/serpapi/exa) escalate above it and
are honest 'not wired' until their key is present. serves_truth=false (results carry source URLs = provenance); Teleon layer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

_REPO = Path(__file__).resolve().parents[3]
#: keyed search providers (escalation tier) — honest 'not wired' until their key is present
_KEYED = {"tavily", "brave_search", "serpapi", "exa", "perplexity_sonar", "gemini_grounded"}


@runtime_checkable
class SearchPort(Protocol):
    name: str
    def search(self, query: str, *, limit: int = 3) -> list[dict]: ...


class GroundedSearch:
    """Keyless grounded search (Wikipedia / Federal Register), provider SELECTED from the registry. Network-gated:
    raises honestly offline rather than fabricating results."""
    def __init__(self, provider: str | None = None):
        self.name = provider or "auto"
    def search(self, query: str, *, limit: int = 3) -> list[dict]:
        from src.teleon.dag.real_steps import real_search
        return real_search(query, provider=(None if self.name == "auto" else self.name), limit=limit)


class NotWiredSearch:
    """A keyed provider whose key isn't present — honest, never fabricates results."""
    def __init__(self, name: str):
        self.name = name
    def search(self, query: str, *, limit: int = 3) -> list[dict]:
        raise RuntimeError(f"search provider '{self.name}' not wired (needs its key); use 'auto' for keyless grounded search")


_NAME_ADAPTERS = {"auto": GroundedSearch, "wikipedia": lambda: GroundedSearch("wikipedia"),
                  "federal_register": lambda: GroundedSearch("federal_register")}


def register_search_adapter(name: str, factory) -> None:
    """Future-proofing hook: wire a real search provider by name; callers of select_search never change."""
    _NAME_ADAPTERS[str(name)] = factory


def available_search() -> dict:
    reg = [p["provider_id"] for p in json.loads((_REPO / "architecture" / "search_provider_registry.json").read_text())["providers"]]
    return {"registry_providers": sorted(reg), "wired_keyless": sorted(_NAME_ADAPTERS), "serves_truth": False}


def select_search(provider: str = "auto") -> SearchPort:
    """Resolve a search provider. 'auto' -> the registry-selected keyless grounded baseline; a keyed provider not yet
    wired -> an honest NotWiredSearch; a registered adapter -> that. Never raises (the search() call may, honestly)."""
    if provider in _NAME_ADAPTERS:
        f = _NAME_ADAPTERS[provider]
        return f() if provider != "auto" else GroundedSearch("auto")
    if provider in _KEYED:
        return NotWiredSearch(provider)
    return GroundedSearch("auto")
