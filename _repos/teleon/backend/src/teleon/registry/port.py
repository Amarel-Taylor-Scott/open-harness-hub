"""registry.port — the universal Registry<T> menu (realizes the ontology's universal_interface).

The federation is a BUFFET; this is the single ORDERING PROTOCOL over it. Every source catalog
(_repos/shared-backend-components/architecture/*.json with a list-of-records) is wrapped by ONE adapter exposing the same verbs, so an agent
building a DAG picks ingredients uniformly:

    from src.teleon.registry import catalog
    catalog("geospatial_sources").search("weather")      # -> [{...}]
    catalog("lookup_portals").lookup("us_nws_weather")    # -> {...}

This is the menu the consumption_model (the demand side) calls. serves_truth=false — a registry returns
pointers/shapes, never truth. Deterministic, stdlib only; the lexical scorer swaps for a learned one behind
the same port without changing any call site (the agnostic-adapter pattern).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

py_var_src_teleon_registry_port___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])          # _repos/teleon/backend/src/teleon/registry/ -> repo root
py_var_src_teleon_registry_port___ARCH = _resource("architecture")
py_var_src_teleon_registry_port___DEFAULT_LIMIT = 10


@lru_cache(maxsize=512)
def py_function_src_teleon_registry_port___cached_catalog_rows(
    py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port___cached_catalog_rows__path: str,
    py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port___cached_catalog_rows__list_key: str,
    py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port___cached_catalog_rows__mtime_ns: int,
) -> tuple[tuple[dict, ...], tuple[tuple[dict, str], ...]]:
    """Load + flatten one immutable-on-disk catalog snapshot once per process/mtime.

    Federated AIDevObserver grounding can search hundreds of catalogs repeatedly during one long session. Reading,
    decoding, and flattening every JSON file for every candidate turn made real-session review take minutes. The
    mtime is part of the key, so a long-running service observes on-disk catalog updates without a manual reset.
    Shallow copies are returned by the public adapter so callers cannot mutate the cached rows themselves.
    """
    del py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port___cached_catalog_rows__mtime_ns
    py_local_src_teleon_registry_port___cached_catalog_rows__records = tuple(
        json.loads(Path(
            py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port___cached_catalog_rows__path
        ).read_text()).get(
            py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port___cached_catalog_rows__list_key,
            [],
        )
    )
    py_local_src_teleon_registry_port___cached_catalog_rows__search_rows = tuple(
        (
            py_local_src_teleon_registry_port___cached_catalog_rows__record,
            " ".join(
                str(py_local_src_teleon_registry_port___cached_catalog_rows__value).lower()
                for py_local_src_teleon_registry_port___cached_catalog_rows__value
                in py_local_src_teleon_registry_port___cached_catalog_rows__record.values()
                if isinstance(py_local_src_teleon_registry_port___cached_catalog_rows__value, (str, int, float))
            ),
        )
        for py_local_src_teleon_registry_port___cached_catalog_rows__record
        in py_local_src_teleon_registry_port___cached_catalog_rows__records
    )
    return (
        py_local_src_teleon_registry_port___cached_catalog_rows__records,
        py_local_src_teleon_registry_port___cached_catalog_rows__search_rows,
    )

# registry id (from registry_ontology) -> the catalog file + how to read it.
py_const_src_teleon_registry_port__CATALOGS: dict[str, dict[str, str]] = {
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
class py_class_src_teleon_registry_port__RegistryPort(Protocol):
    """The uniform menu every registry exposes (the load-bearing subset of the Registry<T> contract)."""

    def list(self) -> list[dict]: ...
    def lookup(self, py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__RegistryPort_lookup__record_id: str) -> dict | None: ...
    def search(self, py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__RegistryPort_search__query: str, *, limit: int = py_var_src_teleon_registry_port___DEFAULT_LIMIT) -> list[dict]: ...
    def explain(self, py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__RegistryPort_explain__record_id: str) -> dict | None: ...


class py_class_src_teleon_registry_port__JsonCatalogRegistry:
    """A RegistryPort over one JSON source catalog: {<list_key>: [{<id_field>: ..., ...}, ...]}."""

    def __init__(self, path: Path, list_key: str, id_field: str = "id") -> None:
        self._path = Path(path)
        self._list_key = list_key
        self._id_field = id_field

    def _records(self) -> list[dict]:
        py_local_src_teleon_registry_port__JsonCatalogRegistry__records, _ = (
            py_function_src_teleon_registry_port___cached_catalog_rows(
                str(self._path), self._list_key, self._path.stat().st_mtime_ns
            )
        )
        return [dict(py_local_src_teleon_registry_port__JsonCatalogRegistry__record)
                for py_local_src_teleon_registry_port__JsonCatalogRegistry__record
                in py_local_src_teleon_registry_port__JsonCatalogRegistry__records]

    def list(self) -> list[dict]:
        return self._records()

    def lookup(self, py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_lookup__record_id: str) -> dict | None:
        for py_local_src_teleon_registry_port__JsonCatalogRegistry_lookup__r in self._records():
            if str(py_local_src_teleon_registry_port__JsonCatalogRegistry_lookup__r.get(self._id_field)) == str(py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_lookup__record_id):
                return py_local_src_teleon_registry_port__JsonCatalogRegistry_lookup__r
        return None

    def explain(self, py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_explain__record_id: str) -> dict | None:
        return self.lookup(py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_explain__record_id)

    def search(self, py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_search__query: str, *, limit: int = py_var_src_teleon_registry_port___DEFAULT_LIMIT) -> list[dict]:
        """Deterministic lexical match: a record matches if ANY query token appears in its flattened text; ranked
        by (# distinct tokens matched, total occurrences) so multi-word queries work + more-relevant rank higher.
        A learned ranker drops in behind this same signature."""
        py_local_src_teleon_registry_port__JsonCatalogRegistry_search__tokens = [t for t in py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_search__query.lower().split() if t]
        py_local_src_teleon_registry_port__JsonCatalogRegistry_search__scored: list[tuple[tuple[int, int], dict]] = []
        _, py_local_src_teleon_registry_port__JsonCatalogRegistry_search__rows = (
            py_function_src_teleon_registry_port___cached_catalog_rows(
                str(self._path), self._list_key, self._path.stat().st_mtime_ns
            )
        )
        for (py_local_src_teleon_registry_port__JsonCatalogRegistry_search__r,
             py_local_src_teleon_registry_port__JsonCatalogRegistry_search__hay) in py_local_src_teleon_registry_port__JsonCatalogRegistry_search__rows:
            py_local_src_teleon_registry_port__JsonCatalogRegistry_search__matched = [t for t in py_local_src_teleon_registry_port__JsonCatalogRegistry_search__tokens if t in py_local_src_teleon_registry_port__JsonCatalogRegistry_search__hay]
            if py_local_src_teleon_registry_port__JsonCatalogRegistry_search__matched:
                py_local_src_teleon_registry_port__JsonCatalogRegistry_search__scored.append(((len(py_local_src_teleon_registry_port__JsonCatalogRegistry_search__matched), sum(py_local_src_teleon_registry_port__JsonCatalogRegistry_search__hay.count(t) for t in py_local_src_teleon_registry_port__JsonCatalogRegistry_search__matched)), py_local_src_teleon_registry_port__JsonCatalogRegistry_search__r))
        py_local_src_teleon_registry_port__JsonCatalogRegistry_search__scored.sort(key=lambda py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_search__sr: py_arg_src_teleon_registry_port__py_class_src_teleon_registry_port__JsonCatalogRegistry_search__sr[0], reverse=True)
        return [dict(py_local_src_teleon_registry_port__JsonCatalogRegistry_search__r) for _, py_local_src_teleon_registry_port__JsonCatalogRegistry_search__r in py_local_src_teleon_registry_port__JsonCatalogRegistry_search__scored[:limit]]


py_var_src_teleon_registry_port___MIN_DISCOVER_RECORDS = 3
py_var_src_teleon_registry_port___DISCOVER_CACHE: dict[str, dict[str, str]] | None = None


def py_function_src_teleon_registry_port__discover_catalogs() -> dict[str, dict[str, str]]:
    """AUTO-DISCOVER catalog-shaped registries: scan _repos/shared-backend-components/architecture/*.json for a list-of-records with a usable id
    field, and register the VALIDATED ones not already curated. Resolves the 'only N on the menu' roadblock so
    federated search spans every record catalog automatically (curated keys win). Cached (one scan). Registries
    that are policy / runtime / derived (no record list) are NOT here — they surface via their backing module."""
    global py_var_src_teleon_registry_port___DISCOVER_CACHE
    if py_var_src_teleon_registry_port___DISCOVER_CACHE is not None:
        return py_var_src_teleon_registry_port___DISCOVER_CACHE
    py_local_src_teleon_registry_port__discover_catalogs__found: dict[str, dict[str, str]] = {}
    py_local_src_teleon_registry_port__discover_catalogs__curated_files = {c["file"] for c in py_const_src_teleon_registry_port__CATALOGS.values()}
    for py_local_src_teleon_registry_port__discover_catalogs__path in sorted(py_var_src_teleon_registry_port___ARCH.glob("*.json")):
        if py_local_src_teleon_registry_port__discover_catalogs__path.name in py_local_src_teleon_registry_port__discover_catalogs__curated_files:
            continue
        try:
            py_local_src_teleon_registry_port__discover_catalogs__d = json.loads(py_local_src_teleon_registry_port__discover_catalogs__path.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(py_local_src_teleon_registry_port__discover_catalogs__d, dict):
            continue
        for py_local_src_teleon_registry_port__discover_catalogs__key, py_local_src_teleon_registry_port__discover_catalogs__val in py_local_src_teleon_registry_port__discover_catalogs__d.items():
            if isinstance(py_local_src_teleon_registry_port__discover_catalogs__val, list) and len(py_local_src_teleon_registry_port__discover_catalogs__val) >= py_var_src_teleon_registry_port___MIN_DISCOVER_RECORDS and isinstance(py_local_src_teleon_registry_port__discover_catalogs__val[0], dict):
                py_local_src_teleon_registry_port__discover_catalogs__rec = py_local_src_teleon_registry_port__discover_catalogs__val[0]
                py_local_src_teleon_registry_port__discover_catalogs__id_field = next((f for f in ("id", "canonical", "name", "key", "code") if f in py_local_src_teleon_registry_port__discover_catalogs__rec), None)
                if py_local_src_teleon_registry_port__discover_catalogs__id_field is None:
                    py_local_src_teleon_registry_port__discover_catalogs__id_field = next((k for k, v in py_local_src_teleon_registry_port__discover_catalogs__rec.items() if isinstance(v, str) and v), None)
                if py_local_src_teleon_registry_port__discover_catalogs__id_field and all(isinstance(r, dict) and py_local_src_teleon_registry_port__discover_catalogs__id_field in r for r in py_local_src_teleon_registry_port__discover_catalogs__val[:py_var_src_teleon_registry_port___MIN_DISCOVER_RECORDS]):
                    py_local_src_teleon_registry_port__discover_catalogs__found[py_local_src_teleon_registry_port__discover_catalogs__path.stem] = {"file": py_local_src_teleon_registry_port__discover_catalogs__path.name, "list_key": py_local_src_teleon_registry_port__discover_catalogs__key, "id_field": py_local_src_teleon_registry_port__discover_catalogs__id_field}
                break  # only the first/main list per file
    py_var_src_teleon_registry_port___DISCOVER_CACHE = py_local_src_teleon_registry_port__discover_catalogs__found
    return py_local_src_teleon_registry_port__discover_catalogs__found


def py_function_src_teleon_registry_port__all_catalogs() -> dict[str, dict[str, str]]:
    """Curated + auto-discovered catalogs (curated keys take precedence)."""
    return {**py_function_src_teleon_registry_port__discover_catalogs(), **py_const_src_teleon_registry_port__CATALOGS}


def py_function_src_teleon_registry_port__available() -> list[str]:
    """Curated registry ids on the menu (stable; the facets + proofs key off these)."""
    return sorted(py_const_src_teleon_registry_port__CATALOGS)


def py_function_src_teleon_registry_port__available_all() -> list[str]:
    """EVERY searchable catalog (curated + auto-discovered) — the full federated-search surface."""
    return sorted(py_function_src_teleon_registry_port__all_catalogs())


def py_function_src_teleon_registry_port__catalog(py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port__catalog__name: str) -> py_class_src_teleon_registry_port__JsonCatalogRegistry:
    """Return the RegistryPort adapter for a registered/discovered registry id (raises KeyError if unknown)."""
    py_local_src_teleon_registry_port__catalog__cats = py_function_src_teleon_registry_port__all_catalogs()
    if py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port__catalog__name not in py_local_src_teleon_registry_port__catalog__cats:
        raise KeyError(f"unknown registry '{py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port__catalog__name}'; available: {py_function_src_teleon_registry_port__available_all()[:8]}...")
    py_local_src_teleon_registry_port__catalog__spec = py_local_src_teleon_registry_port__catalog__cats[py_arg_src_teleon_registry_port__py_function_src_teleon_registry_port__catalog__name]
    return py_class_src_teleon_registry_port__JsonCatalogRegistry(py_var_src_teleon_registry_port___ARCH / py_local_src_teleon_registry_port__catalog__spec["file"], py_local_src_teleon_registry_port__catalog__spec["list_key"], py_local_src_teleon_registry_port__catalog__spec.get("id_field", "id"))


# Public compatibility aliases. The canonical AI-first names above are used by the deterministic graph,
# while these keep existing callers stable until their package slice is migrated.
CATALOGS = py_const_src_teleon_registry_port__CATALOGS
JsonCatalogRegistry = py_class_src_teleon_registry_port__JsonCatalogRegistry
RegistryPort = py_class_src_teleon_registry_port__RegistryPort
discover_catalogs = py_function_src_teleon_registry_port__discover_catalogs
all_catalogs = py_function_src_teleon_registry_port__all_catalogs
available = py_function_src_teleon_registry_port__available
available_all = py_function_src_teleon_registry_port__available_all
catalog = py_function_src_teleon_registry_port__catalog
