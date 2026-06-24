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
    # menu expansion (the federated-search rollout): high-value existing catalogs + the new ones, keyed by their
    # ontology registry id so the search facets (build/troubleshoot/improve) query them directly.
    "component":             {"file": "tool_registry.json",            "list_key": "tools",       "id_field": "id"},
    "capability":            {"file": "capability_ladders.json",       "list_key": "ladders",     "id_field": "canonical"},
    "failure":               {"file": "worker_failure_taxonomy.json",  "list_key": "failures",    "id_field": "failure_type"},
    "optimization_pass":     {"file": "optimization_passes.json",      "list_key": "passes",      "id_field": "pass"},
    "formulas":              {"file": "formula_registry.json",         "list_key": "formulas",    "id_field": "id"},
    "vertical_playbooks":    {"file": "vertical_playbooks.json",       "list_key": "playbooks",   "id_field": "id"},
    "information_acquisition": {"file": "acquisition_strategies.json",  "list_key": "strategies",  "id_field": "id"},
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
        """Deterministic lexical match: a record matches if ANY query token appears in its flattened text; ranked
        by (# distinct tokens matched, total occurrences) so multi-word queries work + more-relevant rank higher.
        A learned ranker drops in behind this same signature."""
        tokens = [t for t in query.lower().split() if t]
        scored: list[tuple[tuple[int, int], dict]] = []
        for r in self._records():
            hay = " ".join(str(v).lower() for v in r.values() if isinstance(v, (str, int, float)))
            matched = [t for t in tokens if t in hay]
            if matched:
                scored.append(((len(matched), sum(hay.count(t) for t in matched)), r))
        scored.sort(key=lambda sr: sr[0], reverse=True)
        return [r for _, r in scored[:limit]]


_MIN_DISCOVER_RECORDS = 3
_DISCOVER_CACHE: dict[str, dict[str, str]] | None = None


def discover_catalogs() -> dict[str, dict[str, str]]:
    """AUTO-DISCOVER catalog-shaped registries: scan architecture/*.json for a list-of-records with a usable id
    field, and register the VALIDATED ones not already curated. Resolves the 'only N on the menu' roadblock so
    federated search spans every record catalog automatically (curated keys win). Cached (one scan). Registries
    that are policy / runtime / derived (no record list) are NOT here — they surface via their backing module."""
    global _DISCOVER_CACHE
    if _DISCOVER_CACHE is not None:
        return _DISCOVER_CACHE
    found: dict[str, dict[str, str]] = {}
    curated_files = {c["file"] for c in CATALOGS.values()}
    for path in sorted(_ARCH.glob("*.json")):
        if path.name in curated_files:
            continue
        try:
            d = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(d, dict):
            continue
        for key, val in d.items():
            if isinstance(val, list) and len(val) >= _MIN_DISCOVER_RECORDS and isinstance(val[0], dict):
                rec = val[0]
                id_field = next((f for f in ("id", "canonical", "name", "key", "code") if f in rec), None)
                if id_field is None:
                    id_field = next((k for k, v in rec.items() if isinstance(v, str) and v), None)
                if id_field and all(isinstance(r, dict) and id_field in r for r in val[:_MIN_DISCOVER_RECORDS]):
                    found[path.stem] = {"file": path.name, "list_key": key, "id_field": id_field}
                break  # only the first/main list per file
    _DISCOVER_CACHE = found
    return found


def all_catalogs() -> dict[str, dict[str, str]]:
    """Curated + auto-discovered catalogs (curated keys take precedence)."""
    return {**discover_catalogs(), **CATALOGS}


def available() -> list[str]:
    """Curated registry ids on the menu (stable; the facets + proofs key off these)."""
    return sorted(CATALOGS)


def available_all() -> list[str]:
    """EVERY searchable catalog (curated + auto-discovered) — the full federated-search surface."""
    return sorted(all_catalogs())


def catalog(name: str) -> JsonCatalogRegistry:
    """Return the RegistryPort adapter for a registered/discovered registry id (raises KeyError if unknown)."""
    cats = all_catalogs()
    if name not in cats:
        raise KeyError(f"unknown registry '{name}'; available: {available_all()[:8]}...")
    spec = cats[name]
    return JsonCatalogRegistry(_ARCH / spec["file"], spec["list_key"], spec.get("id_field", "id"))
