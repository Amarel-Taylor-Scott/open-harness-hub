"""src.teleon.retrieval.search_port — the SEARCH abstraction: any grounded-search provider behind ONE port (agnostic).

Same pattern as ocr/llm/reranker/embedding ports: consumers depend on the PORT, never a specific provider, so a future
provider drops in with ZERO caller change. Selectable providers are POPULATED FROM architecture/search_provider_registry
.json; the WIRED baseline is the keyless grounded search (Wikipedia / US Federal Register via real_steps, registry-
selected — network-gated, honest-unavailable offline). Keyed providers (tavily/brave/serpapi/exa) escalate above it and
are honest 'not wired' until their key is present. serves_truth=false (results carry source URLs = provenance); Teleon layer.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

py_var_src_teleon_retrieval_search_port___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
#: keyed search providers (escalation tier) — honest 'not wired' until their key is present
py_var_src_teleon_retrieval_search_port___KEYED = {"tavily", "brave_search", "serpapi", "exa", "perplexity_sonar", "gemini_grounded"}


@runtime_checkable
class py_class_src_teleon_retrieval_search_port__SearchPort(Protocol):
    name: str
    def search(self, py_arg_src_teleon_retrieval_search_port__py_class_src_teleon_retrieval_search_port__SearchPort_search__query: str, *, limit: int = 3) -> list[dict]: ...


class py_class_src_teleon_retrieval_search_port__GroundedSearch:
    """Keyless grounded search (Wikipedia / Federal Register), provider SELECTED from the registry. Network-gated:
    raises honestly offline rather than fabricating results."""
    def __init__(self, provider: str | None = None):
        self.name = provider or "auto"
    def search(self, py_arg_src_teleon_retrieval_search_port__py_class_src_teleon_retrieval_search_port__GroundedSearch_search__query: str, *, limit: int = 3) -> list[dict]:
        from src.teleon.dag.real_steps import real_search
        return real_search(py_arg_src_teleon_retrieval_search_port__py_class_src_teleon_retrieval_search_port__GroundedSearch_search__query, provider=(None if self.name == "auto" else self.name), limit=limit)


class py_class_src_teleon_retrieval_search_port__NotWiredSearch:
    """A keyed provider whose key isn't present — honest, never fabricates results."""
    def __init__(self, name: str):
        self.name = name
    def search(self, py_arg_src_teleon_retrieval_search_port__py_class_src_teleon_retrieval_search_port__NotWiredSearch_search__query: str, *, limit: int = 3) -> list[dict]:
        raise RuntimeError(f"search provider '{self.name}' not wired (needs its key); use 'auto' for keyless grounded search")


py_var_src_teleon_retrieval_search_port___NAME_ADAPTERS = {"auto": py_class_src_teleon_retrieval_search_port__GroundedSearch, "wikipedia": lambda: py_class_src_teleon_retrieval_search_port__GroundedSearch("wikipedia"),
                  "federal_register": lambda: py_class_src_teleon_retrieval_search_port__GroundedSearch("federal_register")}


def py_function_src_teleon_retrieval_search_port__register_search_adapter(py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__register_search_adapter__name: str, py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__register_search_adapter__factory) -> None:
    """Future-proofing hook: wire a real search provider by name; callers of select_search never change."""
    py_var_src_teleon_retrieval_search_port___NAME_ADAPTERS[str(py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__register_search_adapter__name)] = py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__register_search_adapter__factory


def py_function_src_teleon_retrieval_search_port__available_search() -> dict:
    py_local_src_teleon_retrieval_search_port__available_search__reg = [p["provider_id"] for p in json.loads((_resource("architecture") / "search_provider_registry.json").read_text())["providers"]]
    return {"registry_providers": sorted(py_local_src_teleon_retrieval_search_port__available_search__reg), "wired_keyless": sorted(py_var_src_teleon_retrieval_search_port___NAME_ADAPTERS), "serves_truth": False}


def py_function_src_teleon_retrieval_search_port__select_search(py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__select_search__provider: str = "auto") -> py_class_src_teleon_retrieval_search_port__SearchPort:
    """Resolve a search provider. 'auto' -> the registry-selected keyless grounded baseline; a keyed provider not yet
    wired -> an honest NotWiredSearch; a registered adapter -> that. Never raises (the search() call may, honestly)."""
    if py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__select_search__provider in py_var_src_teleon_retrieval_search_port___NAME_ADAPTERS:
        py_local_src_teleon_retrieval_search_port__select_search__f = py_var_src_teleon_retrieval_search_port___NAME_ADAPTERS[py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__select_search__provider]
        return py_local_src_teleon_retrieval_search_port__select_search__f() if py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__select_search__provider != "auto" else py_class_src_teleon_retrieval_search_port__GroundedSearch("auto")
    if py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__select_search__provider in py_var_src_teleon_retrieval_search_port___KEYED:
        return py_class_src_teleon_retrieval_search_port__NotWiredSearch(py_arg_src_teleon_retrieval_search_port__py_function_src_teleon_retrieval_search_port__select_search__provider)
    return py_class_src_teleon_retrieval_search_port__GroundedSearch("auto")
