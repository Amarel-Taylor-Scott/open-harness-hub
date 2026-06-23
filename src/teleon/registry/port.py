"""registry.port — the universal Registry<T> menu (realizes the ontology's universal_interface).

The federation is a BUFFET; this is the single ORDERING PROTOCOL over it. Every source catalog
(architecture/*.json with a list-of-records) is wrapped by ONE adapter exposing the same verbs, so an agent
building a DAG picks ingredients uniformly:

    from src.teleon.registry import catalog
    catalog("geospatial_sources").search("weather")      # -> [{...}]
    catalog("lookup_portals").lookup("us_nws_weather")    # -> {...}

This is the menu the consumption_model (the demand side) calls. serves_truth=false — a registry returns
pointers/shapes, never truth. Deterministic, stdlib only; the lexical scorer swaps for a learned one behind
the same port without changing any call site (the agnostic-adapter pattern).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

_REPO = Path(__file__).resolve().parents[3]          # src/teleon/registry/ -> repo root
_ARCH = _REPO / "architecture"
_DEFAULT_LIMIT = 10

# registry id (from registry_ontology) -> the catalog file + how to read it.
CATALOGS: dict[str, dict[str, str]] = {
    "lookup_portals":        {"file": "lookup_portals.json",         "list_key": "portals",     "id_field": "id"},
    "observability":         {"file": "observability_providers.json", "list_key": "providers",   "id_field": "id"},
    "geospatial_sources":    {"file": "geospatial_sources.json",      "list_key": "sources",     "id_field": "id"},
    "vulnerability_sources": {"file": "vulnerability_sources.json",    "list_key": "sources",     "id_field": "id"},
    "knowledge_taxonomies":  {"file": "knowledge_taxonomies.json",     "list_key": "taxonomies",  "id_field": "id"},
    "human_expert_sources":  {"file": "human_expert_sources.json",     "list_key": "sources",     "id_field": "id"},
    "semantic_ontology":     {"file": "semantic_field_ontology.json",  "list_key": "fields",      "id_field": "canonical"},
}


@runtime_checkable
class RegistryPort(Protocol):
    """The uniform menu every registry exposes (the load-bearing subset of the Registry<T> contract)."""

    def list(self) -> list[dict]: ...
    def lookup(self, record_id: str) -> dict | None: ...
    def search(self, query: str, *, limit: int = _DEFAULT_LIMIT) -> list[dict]: ...
    def explain(self, record_id: str) -> dict | None: ...


class JsonCatalogRegistry:
    """A RegistryPort over one JSON source catalog: {<list_key>: [{<id_field>: ..., ...}, ...]}."""

    def __init__(self, path: Path, list_key: str, id_field: str = "id") -> None:
        self._path = Path(path)
        self._list_key = list_key
        self._id_field = id_field

    def _records(self) -> list[dict]:
        return json.loads(self._path.read_text()).get(self._list_key, [])

    def list(self) -> list[dict]:
        return self._records()

    def lookup(self, record_id: str) -> dict | None:
        for r in self._records():
            if str(r.get(self._id_field)) == str(record_id):
                return r
        return None

    def explain(self, record_id: str) -> dict | None:
        return self.lookup(record_id)

    def search(self, query: str, *, limit: int = _DEFAULT_LIMIT) -> list[dict]:
        """Deterministic lexical match: a record matches if every query token appears in its flattened text;
        score = total token-hit count (a learned ranker drops in behind this same signature)."""
        tokens = [t for t in query.lower().split() if t]
        scored: list[tuple[int, dict]] = []
        for r in self._records():
            hay = " ".join(str(v).lower() for v in r.values() if isinstance(v, (str, int, float)))
            if tokens and all(t in hay for t in tokens):
                scored.append((sum(hay.count(t) for t in tokens), r))
        scored.sort(key=lambda sr: sr[0], reverse=True)
        return [r for _, r in scored[:limit]]


def available() -> list[str]:
    """Registry ids reachable through the menu."""
    return sorted(CATALOGS)


def catalog(name: str) -> JsonCatalogRegistry:
    """Return the RegistryPort adapter for a registered registry id (raises KeyError if unknown)."""
    if name not in CATALOGS:
        raise KeyError(f"unknown registry '{name}'; available: {available()}")
    spec = CATALOGS[name]
    return JsonCatalogRegistry(_ARCH / spec["file"], spec["list_key"], spec.get("id_field", "id"))
