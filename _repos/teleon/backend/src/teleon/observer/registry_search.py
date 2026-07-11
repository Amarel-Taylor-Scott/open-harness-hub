"""Registry/reuse-card search adapter for AIDevObserver.

This module is the shared seam between observer findings and reusable
candidate objects. HTTP, MCP, hooks, and future route-mode surfaces should use
this adapter instead of rebuilding local-registry search, outcome-memory
ranking, or reuse-card shaping in their own layer.

The current implementation is intentionally conservative:

* exact/local source-ref search first;
* outcome-memory boost/suppress second;
* compact reuse cards with input/output contracts;
* candidate-only responses, never truth claims.

The pgvector/global primitive service can plug in behind this module later
without changing the review or UI surfaces.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import csv
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from scripts._config import (
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY,
    AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY,
    AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_FAMILY,
    AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVE_SOURCE_FAMILY,
    AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY,
    AIDEVOBSERVER_INTELLIGENCE_TOGGLE_DEFAULTS,
    AIDEVOBSERVER_ROUTE_LEVEL_KINDS,
    AIDEVOBSERVER_ROUTE_LEVEL_OUTPUT_EDGES,
    AIDEVOBSERVER_ROUTE_SLOT_KINDS,
    AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY,
    AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE,
    AIDEVOBSERVER_VISIBILITY_SCOPE_ALL,
    AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL,
    AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
    AIDEVOBSERVER_VISIBILITY_SCOPES,
    PRIMITIVE_GLOBAL_SEARCH_STOPWORDS,
    REPO_ROOT,
)

from . import session_store
from .local_registry_connector import (
    cached_index_local_repo,
    primitive_candidate_from_local_record,
    search_local_records,
    search_local_repo,
)
from .settings import GLOBAL_PRIMITIVE_SETTINGS, SERVICE_SETTINGS

LOCAL_REGISTRY_ENV = "OH_OBSERVER_EXPOSE_LOCAL_REGISTRY"
_TRUE_VALUES = {"1", "true", "yes", "on"}
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_GLOBAL_PRIMITIVE_CACHE: dict[str, tuple[object, list[dict[str, Any]]]] = {}
_OPERATIONAL_PRIMITIVE_CACHE: dict[str, tuple[tuple[float, ...], dict[str, Any]]] = {}
_GLOBAL_PRIMITIVES_ENABLED_OVERRIDE: bool | None = None
EDGE_FOUNDRY_SOURCE_KIND = "edge_foundry_candidate_registry"
PROOF_INTENT_QUERY_TOKENS = {
    "assert",
    "check",
    "proof",
    "pytest",
    "regression",
    "selftest",
    "test",
    "tests",
    "verify",
    "verification",
    "vitest",
}
JS_TEST_INTENT_QUERY_TOKENS = {"browser", "frontend", "javascript", "jest", "playwright", "typescript", "vitest"}
PY_TEST_INTENT_QUERY_TOKENS = {"py", "pytest", "python"}
PROOF_PRIMITIVE_KINDS = {"py.proof_fn", "py.test_fn", "js.test_case"}
PROOF_OUTPUT_EDGES = {"ProofRunReceipt", "TestProofReceipt"}
ROUTE_LEVEL_INDEX_CACHE_KEY = "edge_foundry_route_level"


def normalize_visibility_scope(value: str | None, *, has_private_context: bool = False) -> str:
    """Return the candidate visibility scope for source-backed primitive search."""

    raw = str(value or "").strip().lower()
    if raw in AIDEVOBSERVER_VISIBILITY_SCOPES:
        return raw
    return AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL if has_private_context else AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC


def _edge_foundry_visible(card: dict[str, Any], visibility_scope: str) -> bool:
    visibility = str(card.get("surface_visibility") or AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE)
    if visibility_scope == AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC:
        return visibility == AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE
    if visibility_scope in {AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL, AIDEVOBSERVER_VISIBILITY_SCOPE_ALL}:
        return True
    return visibility == AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE


def _visibility_rank(card: dict[str, Any]) -> int:
    visibility = str(card.get("surface_visibility") or AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE)
    if visibility == AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE:
        return 0
    if visibility == AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY:
        return 1
    return 2


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:SERVICE_SETTINGS.digest_chars]


def _proof_intent_boost(q_tokens: set[str], card: dict[str, Any]) -> int:
    if not (q_tokens & PROOF_INTENT_QUERY_TOKENS):
        return 0
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    output_edge = str(card.get("output_edge") or contract.get("output") or "")
    kind = str(card.get("kind") or "")
    if kind in PROOF_PRIMITIVE_KINDS or output_edge in PROOF_OUTPUT_EDGES:
        boost = int(GLOBAL_PRIMITIVE_SETTINGS.proof_intent_boost)
        if kind == "js.test_case" and q_tokens & JS_TEST_INTENT_QUERY_TOKENS:
            boost += int(GLOBAL_PRIMITIVE_SETTINGS.proof_intent_boost)
        if kind in {"py.proof_fn", "py.test_fn"} and q_tokens & PY_TEST_INTENT_QUERY_TOKENS:
            boost += int(GLOBAL_PRIMITIVE_SETTINGS.proof_intent_boost)
        return boost
    return 0


def local_registry_enabled() -> bool:
    """Return whether local source-ref search is enabled.

    Precedence: explicit OH_OBSERVER_EXPOSE_LOCAL_REGISTRY (operator intent) >
    public-demo mode (OH_OBSERVER_PUBLIC_DEMO=1 forces OFF — a public surface must
    never search the local filesystem by default) > the dev-mode toggle default (ON).
    """

    raw = os.environ.get(LOCAL_REGISTRY_ENV)
    if raw is None or not raw.strip():
        from scripts._config import AIDEVOBSERVER_PUBLIC_DEMO_ENV  # single definition of the mode env
        if (os.environ.get(AIDEVOBSERVER_PUBLIC_DEMO_ENV) or "").strip().lower() in _TRUE_VALUES:
            return False
        return bool(AIDEVOBSERVER_INTELLIGENCE_TOGGLE_DEFAULTS.get("local_registry", False))
    return raw.strip().lower() in _TRUE_VALUES


def global_primitives_enabled() -> bool:
    if _GLOBAL_PRIMITIVES_ENABLED_OVERRIDE is not None:
        return _GLOBAL_PRIMITIVES_ENABLED_OVERRIDE
    return bool(GLOBAL_PRIMITIVE_SETTINGS.enabled)


def set_global_primitives_enabled(value: bool | None) -> None:
    """Runtime override used by the local AIDevObserver control deck."""

    global _GLOBAL_PRIMITIVES_ENABLED_OVERRIDE
    _GLOBAL_PRIMITIVES_ENABLED_OVERRIDE = value
    _GLOBAL_PRIMITIVE_CACHE.clear()


def _tokens(text: str) -> set[str]:
    stopwords = set(PRIMITIVE_GLOBAL_SEARCH_STOPWORDS)
    return {
        token
        for token in _TOKEN_RE.findall(str(text or "").lower())
        if len(token) > 1 and token not in stopwords
    }


def _surfaceable_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.surfaceable_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _edge_foundry_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.edge_foundry_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _curated_groups_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.curated_groups_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _runtime_shape_cards_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.runtime_shape_cards_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _primitive_kind_cards_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.primitive_kind_cards_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _benchmark_decomposition_cards_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.benchmark_decomposition_cards_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _source_backed_group_cards_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.source_backed_group_cards_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _source_backed_group_proof_bundles_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.source_backed_group_proof_bundles_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _source_backed_group_promotion_gates_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.source_backed_group_promotion_gates_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _implemented_code_primitives_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.implemented_code_primitives_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _verified_factory_cards_path() -> Path:
    path = Path(GLOBAL_PRIMITIVE_SETTINGS.verified_factory_cards_path).expanduser()
    return path if path.is_absolute() else _resource(path)


def _edge_foundry_paths() -> tuple[Path, ...]:
    paths = [
        _edge_foundry_path(),
        _curated_groups_path(),
        _runtime_shape_cards_path(),
        _primitive_kind_cards_path(),
        _benchmark_decomposition_cards_path(),
        _source_backed_group_cards_path(),
        _implemented_code_primitives_path(),
        _verified_factory_cards_path(),
    ]
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return tuple(unique)


def _settings_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else _resource(path)


def _json_or_default(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def _csv_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in _TRUE_VALUES


def _csv_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def load_global_surfaceable_primitives() -> list[dict[str, Any]]:
    """Load quality-gated global primitive reuse cards.

    The file is generated by ``_repos/shared-backend-components/scripts/primitive_quality_promoter.py`` and
    contains only candidate cards that passed the deterministic surfaceability
    sieve. Raw R3 symbol rows are intentionally not read here.
    """

    path = _surfaceable_path()
    if not global_primitives_enabled() or not path.exists():
        return []
    mtime = path.stat().st_mtime
    cache_key = str(path)
    cached = _GLOBAL_PRIMITIVE_CACHE.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and row.get("candidate") is True and row.get("serves_truth") is False:
            rows.append(row)
    _GLOBAL_PRIMITIVE_CACHE.clear()
    _GLOBAL_PRIMITIVE_CACHE[cache_key] = (mtime, rows)
    return rows


def edge_foundry_primitives_enabled() -> bool:
    return global_primitives_enabled() and bool(GLOBAL_PRIMITIVE_SETTINGS.edge_foundry_enabled)


def load_edge_foundry_primitives() -> list[dict[str, Any]]:
    """Load source-backed edge-foundry candidate cards.

    These are intentionally lower-trust than the surfaceable quality file. They
    let AIDevObserver find real, source-backed capabilities early while keeping
    the truth boundary clear: every row remains candidate-only.
    """

    paths = tuple(path for path in _edge_foundry_paths() if path.exists())
    if not edge_foundry_primitives_enabled() or not paths:
        return []
    evidence_paths = tuple(
        path
        for path in (
            _source_backed_group_proof_bundles_path(),
            _source_backed_group_promotion_gates_path(),
        )
        if path.exists()
    )
    mtimes = tuple(path.stat().st_mtime for path in (*paths, *evidence_paths))
    cache_key = "edge_foundry:" + "|".join(str(path) for path in (*paths, *evidence_paths))
    cached = _GLOBAL_PRIMITIVE_CACHE.get(cache_key)
    if cached and cached[0] == mtimes:
        return cached[1]
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_load_edge_foundry_path(path))
    _GLOBAL_PRIMITIVE_CACHE[cache_key] = (mtimes, rows)
    return rows


def load_edge_foundry_primitive_count() -> int:
    return len(load_edge_foundry_primitives())


def load_runtime_shape_primitive_count() -> int:
    return sum(
        1
        for row in load_edge_foundry_primitives()
        if row.get("source_family") == AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_FAMILY
    )


def load_primitive_kind_primitive_count() -> int:
    return sum(
        1
        for row in load_edge_foundry_primitives()
        if row.get("source_family") == AIDEVEXPLORER_PRIMITIVE_KIND_SOURCE_FAMILY
    )


def load_benchmark_decomposition_primitive_count() -> int:
    return sum(
        1
        for row in load_edge_foundry_primitives()
        if row.get("source_family") == AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_SOURCE_FAMILY
    )


def load_source_backed_group_primitive_count() -> int:
    return sum(
        1
        for row in load_edge_foundry_primitives()
        if row.get("source_family") == AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY
    )


def load_implemented_code_primitive_count() -> int:
    return sum(
        1
        for row in load_edge_foundry_primitives()
        if row.get("source_family") == AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVE_SOURCE_FAMILY
    )


def _count_jsonl_records(path: Path, *, required_record_type: str | None = None) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if required_record_type and row.get("record_type") != required_record_type:
            continue
        if row.get("candidate") is True and row.get("serves_truth") is False:
            count += 1
    return count


def load_source_backed_group_proof_bundle_count() -> int:
    return _count_jsonl_records(_source_backed_group_proof_bundles_path(), required_record_type="proof_bundle")


def load_source_backed_group_promotion_gate_count() -> int:
    return _count_jsonl_records(
        _source_backed_group_promotion_gates_path(),
        required_record_type="source_backed_group_promotion_gate",
    )


def _compact_proof_bundle(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "proof_bundle_id": row.get("proof_bundle_id"),
        "subject_id": row.get("subject_id"),
        "subject_kind": row.get("subject_kind"),
        "proof_kind": row.get("proof_kind"),
        "status": row.get("status"),
        "proof_command": row.get("proof_command"),
        "proof_hash": row.get("proof_hash"),
        "proof_requirements": row.get("proof_requirements") or [],
        "created_at": row.get("created_at"),
        "candidate": True,
        "serves_truth": False,
    }


def _compact_promotion_gate(row: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {"name": check.get("name"), "status": check.get("status")}
        for check in (row.get("gate_checks") or [])
        if isinstance(check, dict)
    ]
    return {
        "gate_id": row.get("gate_id"),
        "primitive_id": row.get("primitive_id"),
        "proof_bundle_id": row.get("proof_bundle_id"),
        "promotion_gate_status": row.get("promotion_gate_status"),
        "promotion_allowed": row.get("promotion_allowed"),
        "promotable_without_review": row.get("promotable_without_review"),
        "review_required": row.get("review_required"),
        "promotion_blockers": row.get("promotion_blockers") or [],
        "gate_checks": checks,
        "gate_hash": row.get("gate_hash"),
        "created_at": row.get("created_at"),
        "candidate": True,
        "serves_truth": False,
    }


def load_source_backed_group_proof_bundle_index() -> dict[str, dict[str, Any]]:
    path = _source_backed_group_proof_bundles_path()
    if not path.exists():
        return {}
    mtime = path.stat().st_mtime
    cache_key = f"source_backed_group_proofs:{path}"
    cached = _GLOBAL_PRIMITIVE_CACHE.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]
    index: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(row, dict)
            and row.get("record_type") == "proof_bundle"
            and row.get("candidate") is True
            and row.get("serves_truth") is False
        ):
            subject_id = str(row.get("subject_id") or "")
            if subject_id:
                index[subject_id] = _compact_proof_bundle(row)
    _GLOBAL_PRIMITIVE_CACHE[cache_key] = (mtime, index)
    return index


def load_source_backed_group_promotion_gate_index() -> dict[str, dict[str, Any]]:
    path = _source_backed_group_promotion_gates_path()
    if not path.exists():
        return {}
    mtime = path.stat().st_mtime
    cache_key = f"source_backed_group_gates:{path}"
    cached = _GLOBAL_PRIMITIVE_CACHE.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]
    index: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(row, dict)
            and row.get("record_type") == "source_backed_group_promotion_gate"
            and row.get("candidate") is True
            and row.get("serves_truth") is False
        ):
            primitive_id = str(row.get("primitive_id") or "")
            if primitive_id:
                index[primitive_id] = _compact_promotion_gate(row)
    _GLOBAL_PRIMITIVE_CACHE[cache_key] = (mtime, index)
    return index


def _source_backed_group_evidence(card: dict[str, Any]) -> dict[str, Any]:
    if card.get("source_family") != AIDEVOBSERVER_SOURCE_BACKED_GROUP_SOURCE_FAMILY:
        return {}
    primitive_id = str(card.get("primitive_id") or "")
    if not primitive_id:
        return {}
    proof_bundle = load_source_backed_group_proof_bundle_index().get(primitive_id)
    promotion_gate = load_source_backed_group_promotion_gate_index().get(primitive_id)
    evidence: dict[str, Any] = {
        "candidate": True,
        "serves_truth": False,
    }
    if proof_bundle:
        evidence["proof_bundle"] = proof_bundle
        evidence["proof_status"] = proof_bundle.get("status")
    if promotion_gate:
        evidence["promotion_gate"] = promotion_gate
        evidence["promotion_gate_status"] = promotion_gate.get("promotion_gate_status")
        evidence["promotion_allowed"] = promotion_gate.get("promotion_allowed")
    return evidence if len(evidence) > 2 else {}


def _load_edge_foundry_path(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            continue
        if row.get("candidate") is not True or row.get("serves_truth") is not False:
            continue
        is_implemented_code = row.get("record_type") == "implemented_code_primitive_candidate"
        blackbox = row.get("blackbox")
        if isinstance(blackbox, dict):
            blackbox_text = blackbox.get("does")
        else:
            blackbox_text = blackbox
        source_span = row.get("source_span") if isinstance(row.get("source_span"), dict) else {}
        rank_features = row.get("rank_features") if isinstance(row.get("rank_features"), dict) else {}
        implemented_source_ref = {
            "registry": AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVE_SOURCE_FAMILY,
            "kind": row.get("code_kind") or "python_symbol",
            "name": row.get("qualname") or row.get("code_object_id"),
            "path": row.get("source_path"),
            "line": source_span.get("start_line"),
            "end_line": source_span.get("end_line"),
            "language": row.get("language"),
            "code_sha256": row.get("code_sha256"),
            "verification_level": row.get("verification_level"),
        } if is_implemented_code else {}
        item = {
            **row,
            "label": row.get("label") or row.get("title") or row.get("slug") or row.get("qualname"),
            "blackbox": blackbox_text,
            "contract": row.get("contract") or {
                "input": row.get("input_edge"),
                "output": row.get("output_edge"),
            },
            "quality_score": int(row.get("quality_score") or rank_features.get("source_priority_score") or 0),
            "source_family": row.get("source_family") or (
                AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVE_SOURCE_FAMILY
                if is_implemented_code
                else row.get("source_family")
            ),
            "source_kind": (
                AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND
                if is_implemented_code
                else row.get("source_kind") or EDGE_FOUNDRY_SOURCE_KIND
            ),
            "source_ref": implemented_source_ref if is_implemented_code else row.get("source_ref"),
            "surface_visibility": row.get("surface_visibility") or (
                AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY
                if is_implemented_code
                else AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE
            ),
        }
        evidence = _source_backed_group_evidence(item)
        if evidence:
            item["proof_evidence"] = evidence
            item["proof_status"] = evidence.get("proof_status")
            item["promotion_gate_status"] = evidence.get("promotion_gate_status")
            item["promotion_allowed"] = evidence.get("promotion_allowed")
        rows.append(item)
    return rows


def _edge_foundry_card_kind(card: dict[str, Any]) -> str:
    return str(card.get("kind") or card.get("record_type") or "").strip()


def _edge_foundry_card_contract(card: dict[str, Any]) -> dict[str, Any]:
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    return {
        "input": contract.get("input") or card.get("input_edge") or "",
        "output": contract.get("output") or card.get("output_edge") or "",
    }


def _edge_foundry_card_output_edge(card: dict[str, Any]) -> str:
    return str(_edge_foundry_card_contract(card).get("output") or "").strip()


def _edge_foundry_card_is_route_level(card: dict[str, Any]) -> bool:
    return (
        _edge_foundry_card_output_edge(card) in set(AIDEVOBSERVER_ROUTE_LEVEL_OUTPUT_EDGES)
        or _edge_foundry_card_kind(card) in set(AIDEVOBSERVER_ROUTE_LEVEL_KINDS)
    )


def _edge_foundry_card_is_route_slot(card: dict[str, Any]) -> bool:
    return _edge_foundry_card_kind(card) in set(AIDEVOBSERVER_ROUTE_SLOT_KINDS)


def load_edge_foundry_route_cards() -> list[dict[str, Any]]:
    """Return cached route/template/slot candidate cards from the edge foundry."""

    paths = tuple(path for path in _edge_foundry_paths() if path.exists())
    if not edge_foundry_primitives_enabled() or not paths:
        return []
    mtimes = tuple(path.stat().st_mtime for path in paths)
    cache_key = f"{ROUTE_LEVEL_INDEX_CACHE_KEY}:" + "|".join(str(path) for path in paths)
    cached = _GLOBAL_PRIMITIVE_CACHE.get(cache_key)
    if cached and cached[0] == mtimes:
        return cached[1]
    cards = [
        card
        for card in load_edge_foundry_primitives()
        if _edge_foundry_card_is_route_level(card) or _edge_foundry_card_is_route_slot(card)
    ]
    _GLOBAL_PRIMITIVE_CACHE[cache_key] = (mtimes, cards)
    return cards


def operational_primitives_enabled() -> bool:
    return global_primitives_enabled() and bool(GLOBAL_PRIMITIVE_SETTINGS.operational_enabled)


def _operational_paths() -> tuple[Path, Path, Path]:
    return (
        _settings_path(GLOBAL_PRIMITIVE_SETTINGS.operational_quality_csv_path),
        _settings_path(GLOBAL_PRIMITIVE_SETTINGS.operational_registry_record_csv_path),
        _settings_path(GLOBAL_PRIMITIVE_SETTINGS.operational_blocking_key_csv_path),
    )


def _source_ref_from_registry_record(row: dict[str, Any]) -> dict[str, Any]:
    canonical = _json_or_default(row.get("canonical_json"), {})
    license_provenance = canonical.get("license_provenance") if isinstance(canonical, dict) else {}
    if not isinstance(license_provenance, dict):
        license_provenance = {}
    call_surface = canonical.get("call_surface") if isinstance(canonical, dict) else {}
    if not isinstance(call_surface, dict):
        call_surface = {}
    line = license_provenance.get("line")
    return {
        "registry": "primitive_operational_registry",
        "kind": (
            license_provenance.get("symbol_kind")
            or call_surface.get("kind")
            or row.get("kind")
            or "primitive"
        ),
        "name": (
            license_provenance.get("symbol_name")
            or call_surface.get("python_symbol")
            or row.get("title")
            or row.get("slug")
        ),
        "path": (
            license_provenance.get("path")
            or call_surface.get("python_path")
            or ""
        ),
        "line": line if isinstance(line, int) else _csv_int(line, 0) or None,
        "license": license_provenance.get("license") or row.get("source_license"),
        "generated_from_real_artifact": bool(license_provenance.get("generated_from_real_artifact", True)),
        "synthetic": bool(license_provenance.get("synthetic", False)),
    }


def _compact_registry_record(row: dict[str, Any]) -> dict[str, Any]:
    canonical = _json_or_default(row.get("canonical_json"), {})
    return {
        "primitive_id": row.get("registry_record_id"),
        "label": row.get("title") or row.get("slug"),
        "slug": row.get("slug"),
        "blackbox": row.get("blackbox_description") or (canonical.get("purpose") if isinstance(canonical, dict) else None),
        "status": row.get("status"),
        "trust": row.get("trust_status"),
        "readiness": row.get("readiness_level"),
        "source_ref": _source_ref_from_registry_record(row),
    }


def _read_operational_index() -> dict[str, Any]:
    quality_path, record_path, blocking_path = _operational_paths()
    paths = (quality_path, record_path, blocking_path)
    if not operational_primitives_enabled() or any(not path.exists() for path in paths):
        return {
            "enabled": operational_primitives_enabled(),
            "available": False,
            "quality": {},
            "records": {},
            "blocking": {},
            "indexed_records": 0,
        }
    mtimes = tuple(path.stat().st_mtime for path in paths)
    cache_key = "|".join(str(path) for path in paths)
    cached = _OPERATIONAL_PRIMITIVE_CACHE.get(cache_key)
    if cached and cached[0] == mtimes:
        return cached[1]

    records: dict[str, dict[str, Any]] = {}
    with record_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            primitive_id = str(row.get("registry_record_id") or "").strip()
            if primitive_id:
                records[primitive_id] = _compact_registry_record(row)

    quality: dict[str, dict[str, Any]] = {}
    with quality_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            primitive_id = str(row.get("registry_record_id") or "").strip()
            if not primitive_id:
                continue
            quality[primitive_id] = {
                "quality_score": _csv_int(row.get("quality_score")),
                "quality_class": row.get("quality_class") or "",
                "surfaceable": _csv_bool(row.get("surfaceable")),
                "readiness": row.get("readiness_after") or row.get("readiness_before"),
                "trust": row.get("trust_after") or row.get("trust_before"),
                "domains": _json_or_default(row.get("domains"), []),
                "signals": _json_or_default(row.get("signals"), []),
                "blockers": _json_or_default(row.get("blockers"), []),
                "input_edge": _json_or_default(row.get("enriched_input_contract"), {}),
                "output_edge": _json_or_default(row.get("enriched_output_contract"), {}),
                "edge_mutation_options": _json_or_default(row.get("mutation_options"), []),
                "recommended_action": row.get("recommended_action") or "",
                "serves_truth": False,
            }

    blocking: dict[str, list[tuple[str, str, float]]] = {}
    with blocking_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            primitive_id = str(row.get("registry_record_id") or "").strip()
            key = str(row.get("key") or "").strip().lower()
            if not primitive_id or not key:
                continue
            try:
                weight = float(row.get("weight") or 0.0)
            except ValueError:
                weight = 0.0
            blocking.setdefault(key, []).append((primitive_id, str(row.get("lane") or ""), weight))

    index = {
        "enabled": True,
        "available": True,
        "quality": quality,
        "records": records,
        "blocking": blocking,
        "indexed_records": len(quality),
    }
    _OPERATIONAL_PRIMITIVE_CACHE.clear()
    _OPERATIONAL_PRIMITIVE_CACHE[cache_key] = (mtimes, index)
    return index


def load_operational_primitive_count() -> int:
    return int(_read_operational_index().get("indexed_records") or 0)


def _operational_search_text(record: dict[str, Any], quality: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in (
            record.get("primitive_id"),
            record.get("label"),
            record.get("slug"),
            record.get("blackbox"),
            " ".join(str(domain) for domain in (quality.get("domains") or [])),
            _stable_json(quality.get("input_edge") or {}),
            _stable_json(quality.get("output_edge") or {}),
        )
        if value
    )


def _quality_rank_boost(quality: dict[str, Any]) -> int:
    quality_class = str(quality.get("quality_class") or "")
    if quality.get("surfaceable") or quality_class == GLOBAL_PRIMITIVE_SETTINGS.operational_surfaceable_quality_class:
        return GLOBAL_PRIMITIVE_SETTINGS.operational_surfaceable_boost
    if quality_class == GLOBAL_PRIMITIVE_SETTINGS.operational_high_value_quality_class:
        return GLOBAL_PRIMITIVE_SETTINGS.operational_high_value_boost
    return 0


def _blocking_query_keys(
    query_tokens: set[str],
    requested_input_tokens: set[str],
    requested_output_tokens: set[str],
) -> list[str]:
    keys: list[str] = []
    for token in sorted(query_tokens):
        keys.extend((f"exact:{token}", f"keyword:{token}", f"label:{token}", f"graph:{token}"))
    for token in sorted(requested_input_tokens):
        keys.extend((f"input_field:{token}", f"input_shape:{token}"))
    for token in sorted(requested_output_tokens):
        keys.extend((f"output_field:{token}", f"output_shape:{token}"))
    return keys


def _operational_card(
    primitive_id: str,
    *,
    record: dict[str, Any],
    quality: dict[str, Any],
    score: int,
    matched_terms: list[str],
    edge_matches: list[str],
    blocking_matches: list[str],
) -> dict[str, Any]:
    input_edge = quality.get("input_edge") or {}
    output_edge = quality.get("output_edge") or {}
    return {
        "kind": "reuse_card",
        "primitive_id": primitive_id,
        "label": record.get("label") or primitive_id,
        "source_kind": "operational_primitive_registry",
        "contract": {"input": input_edge, "output": output_edge},
        "input_edge": input_edge,
        "output_edge": output_edge,
        "blackbox": record.get("blackbox"),
        "domains": quality.get("domains") or [],
        "quality_class": quality.get("quality_class"),
        "quality_score": quality.get("quality_score") or 0,
        "readiness": quality.get("readiness") or record.get("readiness"),
        "trust": quality.get("trust") or record.get("trust"),
        "source_ref": record.get("source_ref") or {},
        "edge_fit": {
            "fit_class": "candidate_edge_match" if edge_matches else "candidate_text_match",
            "required_mutations": [
                option.get("target_edge_template", {}).get("mutation") or option.get("mutator_agent_id")
                for option in (quality.get("edge_mutation_options") or [])
                if isinstance(option, dict)
            ],
        },
        "edge_mutation_options": quality.get("edge_mutation_options") or [],
        "match_reason": {
            "matched_terms": matched_terms[:8],
            "edge_matches": edge_matches[:8],
            "blocking_matches": blocking_matches[:8],
            "quality_class": quality.get("quality_class"),
            "score": score,
            "registry_scope": "operational_primitive_registry",
        },
        "proof_requirements": ["contract_check", "proof_receipt_before_promotion"],
        "candidate": True,
        "serves_truth": False,
        "score": score,
    }


def search_operational_primitives(
    query: str,
    *,
    limit: int | None = None,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
) -> list[dict[str, Any]]:
    """Return compact cards from the full operational primitive export.

    This is a file-backed stand-in for the Postgres/pgvector operational
    search service. It uses precomputed blocking keys, enriched I/O contracts,
    quality rows, and mutation options, and it never returns raw source.
    """

    q_tokens = _tokens(query)
    if not q_tokens:
        return []
    index = _read_operational_index()
    if not index.get("available"):
        return []
    requested_input_tokens = _tokens(_stable_json(requested_input)) if requested_input is not None else set()
    requested_output_tokens = _tokens(_stable_json(requested_output)) if requested_output is not None else set()
    blocking: dict[str, list[tuple[str, str, float]]] = index["blocking"]
    quality_by_id: dict[str, dict[str, Any]] = index["quality"]
    records_by_id: dict[str, dict[str, Any]] = index["records"]
    candidates: dict[str, dict[str, Any]] = {}

    per_key_limit = max(1, GLOBAL_PRIMITIVE_SETTINGS.operational_per_key_candidate_limit)
    for key in _blocking_query_keys(q_tokens, requested_input_tokens, requested_output_tokens):
        for primitive_id, lane, weight in blocking.get(key, [])[:per_key_limit]:
            bucket = candidates.setdefault(
                primitive_id,
                {"blocking_matches": set(), "blocking_score": 0.0},
            )
            bucket["blocking_matches"].add(key)
            if lane == "exact":
                bucket["blocking_score"] += 12.0 * max(weight, 1.0)
            elif lane in {"input_field", "output_field", "input_shape", "output_shape"}:
                bucket["blocking_score"] += 7.0 * max(weight, 1.0)
            elif lane == "label":
                bucket["blocking_score"] += 5.0 * max(weight, 1.0)
            elif lane == "keyword":
                bucket["blocking_score"] += 4.0 * max(weight, 1.0)
            else:
                bucket["blocking_score"] += 1.0 * max(weight, 1.0)

    if not candidates:
        for primitive_id, quality in quality_by_id.items():
            record = records_by_id.get(primitive_id) or {}
            if q_tokens & _tokens(_operational_search_text(record, quality)):
                candidates[primitive_id] = {"blocking_matches": set(), "blocking_score": 1.0}
                if len(candidates) >= GLOBAL_PRIMITIVE_SETTINGS.operational_candidate_pool_limit:
                    break

    ranked: list[dict[str, Any]] = []
    for primitive_id, match in list(candidates.items())[: GLOBAL_PRIMITIVE_SETTINGS.operational_candidate_pool_limit]:
        quality = quality_by_id.get(primitive_id)
        record = records_by_id.get(primitive_id)
        if not quality or not record:
            continue
        text_tokens = _tokens(_operational_search_text(record, quality))
        matched_terms = sorted(q_tokens & text_tokens)
        input_tokens = _tokens(_stable_json(quality.get("input_edge") or {}))
        output_tokens = _tokens(_stable_json(quality.get("output_edge") or {}))
        edge_matches = sorted((requested_input_tokens & input_tokens) | (requested_output_tokens & output_tokens))
        quality_score = int(quality.get("quality_score") or 0)
        score = (
            int(match["blocking_score"])
            + len(matched_terms) * GLOBAL_PRIMITIVE_SETTINGS.exact_term_score
            + len(edge_matches) * GLOBAL_PRIMITIVE_SETTINGS.edge_score
            + quality_score // 20
            + _quality_rank_boost(quality)
        )
        blockers = quality.get("blockers") or []
        if blockers:
            score -= min(18, len(blockers) * 4)
        if score < GLOBAL_PRIMITIVE_SETTINGS.min_score:
            continue
        ranked.append(_operational_card(
            primitive_id,
            record=record,
            quality=quality,
            score=score,
            matched_terms=matched_terms,
            edge_matches=edge_matches,
            blocking_matches=sorted(match["blocking_matches"]),
        ))

    ranked.sort(key=lambda row: (
        -int(row.get("score") or 0),
        -int(row.get("quality_score") or 0),
        str(row.get("primitive_id") or ""),
    ))
    preferred = [
        row for row in ranked
        if row.get("quality_class") not in {
            GLOBAL_PRIMITIVE_SETTINGS.operational_noise_quality_class,
            GLOBAL_PRIMITIVE_SETTINGS.operational_hold_quality_class,
        }
    ]
    if preferred:
        ranked = preferred
    return ranked[: max(1, int(limit or GLOBAL_PRIMITIVE_SETTINGS.default_limit))]


def _global_primitive_search_text(card: dict[str, Any]) -> str:
    source_ref = card.get("source_ref") or {}
    contract = card.get("contract") or {}
    return " ".join(
        str(value)
        for value in (
            card.get("primitive_id"),
            card.get("label"),
            card.get("blackbox"),
            " ".join(card.get("domains") or []),
            source_ref.get("path"),
            source_ref.get("name"),
            _stable_json(contract.get("input") or {}),
            _stable_json(contract.get("output") or {}),
        )
        if value
    )


def _global_primitive_identifier_text(card: dict[str, Any]) -> str:
    source_ref = card.get("source_ref") or {}
    return " ".join(
        str(value)
        for value in (
            card.get("primitive_id"),
            card.get("label"),
            source_ref.get("path"),
            source_ref.get("name"),
        )
        if value
    )


def search_global_primitives(
    query: str,
    *,
    limit: int | None = None,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
) -> list[dict[str, Any]]:
    """Return global surfaceable primitive cards ranked for the query."""

    q_tokens = _tokens(query)
    if not q_tokens:
        return []
    requested_input_tokens = _tokens(_stable_json(requested_input)) if requested_input is not None else set()
    requested_output_tokens = _tokens(_stable_json(requested_output)) if requested_output is not None else set()
    ranked: list[dict[str, Any]] = []
    for card in load_global_surfaceable_primitives():
        text = _global_primitive_search_text(card)
        text_tokens = _tokens(text)
        matched = sorted(q_tokens & text_tokens)
        if not matched:
            continue
        domains = set(str(domain).lower() for domain in (card.get("domains") or []))
        domain_matches = sorted(q_tokens & domains)
        identifier_matches = sorted(q_tokens & _tokens(_global_primitive_identifier_text(card)))
        contract = card.get("contract") or {}
        input_tokens = _tokens(_stable_json(contract.get("input") or {}))
        output_tokens = _tokens(_stable_json(contract.get("output") or {}))
        edge_matches = sorted((requested_input_tokens & input_tokens) | (requested_output_tokens & output_tokens))
        score = (
            len(matched) * GLOBAL_PRIMITIVE_SETTINGS.exact_term_score
            + len(identifier_matches) * GLOBAL_PRIMITIVE_SETTINGS.identifier_score
            + len(domain_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score
            + len(edge_matches) * GLOBAL_PRIMITIVE_SETTINGS.edge_score
            + int(card.get("quality_score") or 0) // 25
        )
        if score < GLOBAL_PRIMITIVE_SETTINGS.min_score:
            continue
        item = dict(card)
        item["source_kind"] = "global_surfaceable_primitive_registry"
        item["score"] = score
        item["match_reason"] = {
            **(item.get("match_reason") or {}),
            "matched_terms": matched[:8],
            "identifier_matches": identifier_matches[:8],
            "domain_matches": domain_matches[:8],
            "edge_matches": edge_matches[:8],
            "score": score,
            "registry_scope": "global_surfaceable_primitives",
        }
        ranked.append(item)
    ranked.sort(key=lambda row: (-int(row.get("score") or 0), -int(row.get("quality_score") or 0), str(row.get("primitive_id") or "")))
    return ranked[: max(1, int(limit or GLOBAL_PRIMITIVE_SETTINGS.default_limit))]


def search_edge_foundry_primitives(
    query: str,
    *,
    limit: int | None = None,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    visibility_scope: str | None = None,
) -> list[dict[str, Any]]:
    """Search source-backed foundry candidate cards by text and edge overlap."""

    q_tokens = _tokens(query)
    if not q_tokens:
        return []
    scope = normalize_visibility_scope(visibility_scope)
    requested_input_tokens = _tokens(_stable_json(requested_input)) if requested_input is not None else set()
    requested_output_tokens = _tokens(_stable_json(requested_output)) if requested_output is not None else set()
    ranked: list[dict[str, Any]] = []
    for card in load_edge_foundry_primitives():
        if not _edge_foundry_visible(card, scope):
            continue
        source_ref = card.get("source_ref") if isinstance(card.get("source_ref"), dict) else {}
        source_path = str(source_ref.get("path") or "").lower()
        if "/vendor/" in f"/{source_path}" or ".min." in source_path:
            continue
        contract = card.get("contract") or {}
        mutation_text = " ".join(
            " ".join(str(value) for value in (
                option.get("mutator"),
                option.get("mutator_agent_id"),
                option.get("reason"),
                _stable_json(option.get("target_edge_template") or {}),
                _stable_json(option.get("preconditions") or []),
                _stable_json(option.get("proof_obligations") or []),
                _stable_json(option.get("runtime_targets") or []),
            ) if value)
            for option in (card.get("mutations") or [])
            if isinstance(option, dict)
        )
        domain_text = " ".join(str(domain) for domain in (card.get("domains") or []))
        runtime_text = " ".join(str(target) for target in (card.get("runtime_targets") or []))
        text = " ".join(str(value) for value in (
            _global_primitive_search_text(card),
            " ".join(card.get("blocking_keys") or []),
            runtime_text,
            mutation_text,
        ) if value)
        text_tokens = _tokens(text)
        matched = sorted(q_tokens & text_tokens)
        identifier_matches = sorted(q_tokens & _tokens(_global_primitive_identifier_text(card)))
        domain_matches = sorted(q_tokens & _tokens(domain_text))
        runtime_matches = sorted(q_tokens & _tokens(runtime_text))
        mutation_matches = sorted(q_tokens & _tokens(mutation_text))
        input_tokens = _tokens(_stable_json(contract.get("input") or card.get("input_edge") or ""))
        output_tokens = _tokens(_stable_json(contract.get("output") or card.get("output_edge") or ""))
        edge_matches = sorted((requested_input_tokens & input_tokens) | (requested_output_tokens & output_tokens))
        if not matched and not edge_matches:
            continue
        proof_boost = _proof_intent_boost(q_tokens, card)
        proof_evidence = card.get("proof_evidence") if isinstance(card.get("proof_evidence"), dict) else {}
        source_backed_proof_boost = 0
        if proof_evidence.get("proof_status") == "pass":
            source_backed_proof_boost += GLOBAL_PRIMITIVE_SETTINGS.domain_score * 2
        if proof_evidence.get("promotion_gate_status") == "blocked_pending_owner_review":
            source_backed_proof_boost += GLOBAL_PRIMITIVE_SETTINGS.domain_score
        score = (
            len(matched) * GLOBAL_PRIMITIVE_SETTINGS.exact_term_score
            + len(identifier_matches) * GLOBAL_PRIMITIVE_SETTINGS.identifier_score * 2
            + len(domain_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score * 2
            + len(runtime_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score
            + len(mutation_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score
            + len(edge_matches) * GLOBAL_PRIMITIVE_SETTINGS.edge_score
            + int(card.get("quality_score") or 0) // 8
            + proof_boost
            + source_backed_proof_boost
        )
        if score < GLOBAL_PRIMITIVE_SETTINGS.min_score:
            continue
        item = dict(card)
        item_source_kind = str(card.get("source_kind") or EDGE_FOUNDRY_SOURCE_KIND)
        item["source_kind"] = item_source_kind
        item["visibility_scope"] = scope
        item["score"] = score
        item["match_reason"] = {
            **(item.get("match_reason") or {}),
            "matched_terms": matched[:8],
            "identifier_matches": identifier_matches[:8],
            "domain_matches": domain_matches[:8],
            "runtime_matches": runtime_matches[:8],
            "mutation_matches": mutation_matches[:8],
            "edge_matches": edge_matches[:8],
            "proof_intent_boost": proof_boost,
            "source_backed_proof_boost": source_backed_proof_boost,
            "score": score,
            "registry_scope": (
                "implemented_code_primitives"
                if item_source_kind == AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND
                else "edge_foundry_candidate_primitives"
            ),
            "visibility_scope": scope,
            "surface_visibility": item.get("surface_visibility") or AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE,
        }
        ranked.append(item)
    ranked.sort(key=lambda row: (-int(row.get("score") or 0), _visibility_rank(row), str(row.get("primitive_id") or "")))
    return ranked[: max(1, int(limit or GLOBAL_PRIMITIVE_SETTINGS.default_limit))]


def _route_card_rank(card: dict[str, Any]) -> int:
    if _edge_foundry_card_is_route_level(card):
        return 0
    if _edge_foundry_card_is_route_slot(card):
        return 1
    return 2


def search_route_level_primitives(
    query: str,
    *,
    limit: int | None = None,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    visibility_scope: str | None = None,
) -> list[dict[str, Any]]:
    """Search only route/template/slot cards for broad IDE planning.

    This keeps broad "build an app/system" requests from scoring the full
    source-backed primitive corpus before the planner sees candidate routes.
    Rows remain candidate-only and are not promoted by search.
    """

    q_tokens = _tokens(query)
    requested_input_tokens = _tokens(_stable_json(requested_input)) if requested_input is not None else set()
    requested_output_tokens = _tokens(_stable_json(requested_output)) if requested_output is not None else set()
    if not q_tokens and not requested_input_tokens and not requested_output_tokens:
        return []
    scope = normalize_visibility_scope(visibility_scope)
    ranked: list[dict[str, Any]] = []
    for card in load_edge_foundry_route_cards():
        if not _edge_foundry_visible(card, scope):
            continue
        source_ref = card.get("source_ref") if isinstance(card.get("source_ref"), dict) else {}
        source_path = str(source_ref.get("path") or "").lower()
        if "/vendor/" in f"/{source_path}" or ".min." in source_path:
            continue
        contract = _edge_foundry_card_contract(card)
        mutation_text = " ".join(
            " ".join(
                str(value)
                for value in (
                    option.get("mutator"),
                    option.get("mutator_agent_id"),
                    option.get("reason"),
                    _stable_json(option.get("target_edge_template") or {}),
                    _stable_json(option.get("preconditions") or []),
                    _stable_json(option.get("proof_obligations") or []),
                    _stable_json(option.get("runtime_targets") or []),
                )
                if value
            )
            for option in (card.get("mutations") or [])
            if isinstance(option, dict)
        )
        domain_text = " ".join(str(domain) for domain in (card.get("domains") or []))
        runtime_text = " ".join(str(target) for target in (card.get("runtime_targets") or []))
        route_text = " ".join(
            str(value)
            for value in (
                _global_primitive_search_text(card),
                _edge_foundry_card_kind(card),
                " ".join(card.get("blocking_keys") or []),
                runtime_text,
                mutation_text,
            )
            if value
        )
        text_tokens = _tokens(route_text)
        matched = sorted(q_tokens & text_tokens)
        identifier_matches = sorted(q_tokens & _tokens(_global_primitive_identifier_text(card)))
        domain_matches = sorted(q_tokens & _tokens(domain_text))
        runtime_matches = sorted(q_tokens & _tokens(runtime_text))
        mutation_matches = sorted(q_tokens & _tokens(mutation_text))
        input_tokens = _tokens(_stable_json(contract.get("input") or ""))
        output_tokens = _tokens(_stable_json(contract.get("output") or ""))
        edge_matches = sorted((requested_input_tokens & input_tokens) | (requested_output_tokens & output_tokens))
        if not matched and not edge_matches:
            continue
        route_boost = GLOBAL_PRIMITIVE_SETTINGS.edge_score if _edge_foundry_card_is_route_level(card) else 0
        score = (
            len(matched) * GLOBAL_PRIMITIVE_SETTINGS.exact_term_score
            + len(identifier_matches) * GLOBAL_PRIMITIVE_SETTINGS.identifier_score * 2
            + len(domain_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score * 2
            + len(runtime_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score
            + len(mutation_matches) * GLOBAL_PRIMITIVE_SETTINGS.domain_score
            + len(edge_matches) * GLOBAL_PRIMITIVE_SETTINGS.edge_score
            + int(card.get("quality_score") or 0) // 8
            + route_boost
        )
        if score < GLOBAL_PRIMITIVE_SETTINGS.min_score:
            continue
        item = dict(card)
        item["source_kind"] = card.get("source_kind") or EDGE_FOUNDRY_SOURCE_KIND
        item["visibility_scope"] = scope
        item["score"] = score
        item["match_reason"] = {
            **(item.get("match_reason") or {}),
            "matched_terms": matched[:8],
            "identifier_matches": identifier_matches[:8],
            "domain_matches": domain_matches[:8],
            "runtime_matches": runtime_matches[:8],
            "mutation_matches": mutation_matches[:8],
            "edge_matches": edge_matches[:8],
            "route_level": _edge_foundry_card_is_route_level(card),
            "route_slot": _edge_foundry_card_is_route_slot(card),
            "score": score,
            "registry_scope": ROUTE_LEVEL_INDEX_CACHE_KEY,
            "visibility_scope": scope,
            "surface_visibility": item.get("surface_visibility") or AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE,
        }
        ranked.append(item)
    ranked.sort(
        key=lambda row: (
            _route_card_rank(row),
            -int(row.get("score") or 0),
            -int(row.get("quality_score") or 0),
            _visibility_rank(row),
            str(row.get("primitive_id") or ""),
        )
    )
    return ranked[: max(1, int(limit or GLOBAL_PRIMITIVE_SETTINGS.default_limit))]


def _primitive_hit_source_kind(hit: dict[str, Any]) -> str:
    return str(hit.get("source_kind") or "")


def _source_diverse_primitive_hits(ranked: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    """Preserve a compact, source-diverse slice for planner tools.

    Pure score sorting can let one registry family monopolize the top-k list.
    The planner needs at least one operational-registry card when those cards
    match, because operational cards carry the wide generated registry's I/O
    contracts and mutator evidence. This keeps rows candidate-only; it only
    affects compact result visibility.
    """

    selected = ranked[:limit]
    if limit < 2 or not selected:
        return selected
    selected_ids = {str(row.get("primitive_id") or "") for row in selected}
    priority_sources = (
        "global_surfaceable_primitive_registry",
        "operational_primitive_registry",
        AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND,
        EDGE_FOUNDRY_SOURCE_KIND,
    )
    for source_kind in priority_sources:
        if any(_primitive_hit_source_kind(row) == source_kind for row in selected):
            continue
        best = next((row for row in ranked if _primitive_hit_source_kind(row) == source_kind), None)
        if not best:
            continue
        best_id = str(best.get("primitive_id") or "")
        if best_id in selected_ids:
            continue
        replacement_index = len(selected) - 1
        source_counts: dict[str, int] = {}
        for row in selected:
            source_counts[_primitive_hit_source_kind(row)] = source_counts.get(_primitive_hit_source_kind(row), 0) + 1
        for index in range(len(selected) - 1, -1, -1):
            row_kind = _primitive_hit_source_kind(selected[index])
            if source_counts.get(row_kind, 0) > 1:
                replacement_index = index
                break
        old_id = str(selected[replacement_index].get("primitive_id") or "")
        selected[replacement_index] = best
        selected_ids.discard(old_id)
        selected_ids.add(best_id)
    selected.sort(key=lambda row: (
        -int(row.get("score") or 0),
        -int(row.get("quality_score") or 0),
        {
            "global_surfaceable_primitive_registry": 0,
            "operational_primitive_registry": 1,
            AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND: 2,
            EDGE_FOUNDRY_SOURCE_KIND: 3,
        }.get(str(row.get("source_kind") or ""), 3),
        str(row.get("primitive_id") or ""),
    ))
    return selected[:limit]


def _dedupe_primitive_hits(hits: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for hit in hits:
        primitive_id = str(hit.get("primitive_id") or "")
        if not primitive_id:
            continue
        existing = by_id.get(primitive_id)
        if existing is None:
            by_id[primitive_id] = hit
            continue
        existing_kind = existing.get("source_kind")
        hit_kind = hit.get("source_kind")
        if existing_kind == "global_surfaceable_primitive_registry" and hit_kind == "operational_primitive_registry":
            existing["score"] = max(int(existing.get("score") or 0), int(hit.get("score") or 0))
            existing["match_reason"] = {
                **(existing.get("match_reason") or {}),
                "operational_match_reason": hit.get("match_reason") or {},
            }
            continue
        if existing_kind == "operational_primitive_registry" and hit_kind == "global_surfaceable_primitive_registry":
            item = dict(hit)
            item["score"] = max(int(existing.get("score") or 0), int(hit.get("score") or 0))
            item["match_reason"] = {
                **(item.get("match_reason") or {}),
                "operational_match_reason": existing.get("match_reason") or {},
            }
            by_id[primitive_id] = item
            continue
        if (
            int(hit.get("score") or 0),
            int(hit.get("quality_score") or 0),
        ) > (
            int(existing.get("score") or 0),
            int(existing.get("quality_score") or 0),
        ):
            by_id[primitive_id] = hit
    ranked = sorted(
        by_id.values(),
        key=lambda row: (
            -int(row.get("score") or 0),
            -int(row.get("quality_score") or 0),
            {
                "global_surfaceable_primitive_registry": 0,
                "operational_primitive_registry": 1,
                AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND: 2,
                EDGE_FOUNDRY_SOURCE_KIND: 3,
            }.get(str(row.get("source_kind") or ""), 3),
            str(row.get("primitive_id") or ""),
        ),
    )
    return _source_diverse_primitive_hits(ranked, limit=limit)


def _registry_hit_rank_key(hit: dict[str, Any]) -> tuple[int, int, int, int, str]:
    card = hit.get("reuse_card") if isinstance(hit.get("reuse_card"), dict) else hit
    source_kind = str(card.get("source_kind") or hit.get("source_kind") or "")
    source_ref = card.get("source_ref") if isinstance(card.get("source_ref"), dict) else hit.get("source_ref") or {}
    source_path = str(source_ref.get("path") or "").lower()
    score = int(
        card.get("score")
        or hit.get("score_adjusted")
        or hit.get("score")
        or 0
    )
    quality_score = int(card.get("quality_score") or hit.get("quality_score") or 0)
    source_rank = {
        "global_surfaceable_primitive_registry": 0,
        "operational_primitive_registry": 1,
        AIDEVOBSERVER_IMPLEMENTED_CODE_SOURCE_KIND: 2,
        EDGE_FOUNDRY_SOURCE_KIND: 3,
        "first_party_repo_record": 3,
    }.get(source_kind, 3)
    test_rank = 1 if "/tests/" in source_path or source_path.startswith("tests/") or "fixtures" in source_path else 0
    return (-score, -quality_score, test_rank, source_rank, str(card.get("primitive_id") or hit.get("id") or ""))


def search_reusable_primitives(
    query: str,
    *,
    limit: int | None = None,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    visibility_scope: str | None = None,
) -> list[dict[str, Any]]:
    """Search every reusable primitive lane exposed to AIDevObserver."""

    n = max(1, int(limit or GLOBAL_PRIMITIVE_SETTINGS.default_limit))
    scope = normalize_visibility_scope(visibility_scope)
    hits = [
        *search_global_primitives(
            query,
            limit=n,
            requested_input=requested_input,
            requested_output=requested_output,
        ),
        *search_operational_primitives(
            query,
            limit=n,
            requested_input=requested_input,
            requested_output=requested_output,
        ),
        *search_edge_foundry_primitives(
            query,
            limit=n,
            requested_input=requested_input,
            requested_output=requested_output,
            visibility_scope=scope,
        ),
    ]
    return _dedupe_primitive_hits(hits, limit=n)


def compact_local_source_ref(hit: dict) -> dict:
    """Shrink one connector hit to the source-ref payload safe for reports."""

    ref = dict(hit.get("source_ref") or {})
    if hit.get("score") is not None:
        ref["score"] = hit["score"]
    if hit.get("score_adjusted") is not None:
        ref["score_adjusted"] = hit["score_adjusted"]
    if hit.get("outcome_memory"):
        ref["outcome_memory"] = dict(hit["outcome_memory"])
    if hit.get("matched_terms"):
        ref["matched_terms"] = list(hit["matched_terms"])[:8]
    return ref


def normalize_reuse_card(card: dict) -> dict:
    """Return a card carrying the LLM-readable reuse-card contract shape.

    Every hit a service surface attaches — whatever registry plane it came from
    (surfaceable/operational/edge-foundry/runtime-shape/benchmark) — must be a
    `reuse_card` with the truth boundary stamped and a contract an agent can
    compose from (input/output edges; "Unknown" is the honest fallback, same as
    the local-hit builder). Normalization never drops plane-specific fields.
    """

    out = dict(card)
    # A raw card's `kind` is its PRIMITIVE kind (py.fn / api.endpoint / ...); the envelope kind is
    # always reuse_card. Preserve the primitive kind losslessly under `primitive_kind`.
    if out.get("kind") and out.get("kind") != "reuse_card":
        out.setdefault("primitive_kind", out["kind"])
    out["kind"] = "reuse_card"
    out.setdefault("candidate", True)
    out.setdefault("serves_truth", False)
    contract = out.get("contract") if isinstance(out.get("contract"), dict) else {}
    if not (contract.get("input") and contract.get("output")):
        out["contract"] = {
            "input": contract.get("input") or out.get("input_edge") or "Unknown",
            "output": contract.get("output") or out.get("output_edge") or "Unknown",
        }
    return out


def reuse_card_from_local_hit(hit: dict, finding: dict) -> dict:
    """Return the compact object/edge an agent can reuse without reading source."""

    primitive = primitive_candidate_from_local_record(hit)
    source_ref = compact_local_source_ref(hit)
    matched_terms = source_ref.get("matched_terms") or []
    edge_fit = hit.get("edge_fit") or {}
    return {
        "kind": "reuse_card",
        "primitive_id": primitive["primitive_id"],
        "label": primitive.get("slug") or hit.get("name"),
        "record_type": primitive.get("record_type", "primitive_draft"),
        "source_kind": primitive.get("source_kind", "first_party_repo_record"),
        "contract": primitive.get("contract") or {"input": "Unknown", "output": "Unknown"},
        "effects": primitive.get("effects") or [],
        "memory": primitive.get("memory"),
        "cache": primitive.get("cache"),
        "readiness": primitive.get("readiness"),
        "trust": primitive.get("trust"),
        "source_ref": source_ref,
        "input_edge": primitive.get("input_edge"),
        "output_edge": primitive.get("output_edge"),
        "blackbox": primitive.get("blackbox"),
        "edge_fit": edge_fit,
        "edge_mutation_options": primitive.get("edge_mutation_options") or [],
        "match_reason": {
            "finding_type": finding.get("type"),
            "matched_terms": matched_terms,
            "score": source_ref.get("score"),
            "score_adjusted": source_ref.get("score_adjusted"),
            "edge_fit_class": edge_fit.get("fit_class"),
            "required_mutations": edge_fit.get("required_mutations") or [],
            "query_mutation_hints": edge_fit.get("query_mutation_hints") or [],
        },
        "proof_requirements": primitive.get("proof_requirements") or [],
        "candidate": True,
        "serves_truth": False,
    }


def enrich_report_with_global_primitives(
    rep: dict,
    *,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    visibility_scope: str | None = None,
) -> dict:
    """Attach quality-gated global primitive reuse cards to findings."""

    if not global_primitives_enabled():
        return {
            **rep,
            "global_primitive_registry": {
                "enabled": False,
                "reason": "disabled",
                "candidate": True,
                "serves_truth": False,
            },
        }

    enriched = []
    hits_attached = 0
    searched = 0
    for finding in rep.get("report", []):
        item = dict(finding)
        query = local_registry_query_for_finding(item)
        if query:
            searched += 1
            hits = search_reusable_primitives(
                query,
                limit=GLOBAL_PRIMITIVE_SETTINGS.review_hit_limit,
                requested_input=requested_input,
                requested_output=requested_output,
                visibility_scope=visibility_scope,
            )
        else:
            hits = []
        if hits:
            source_ref = dict(item.get("source_ref") or {})
            existing = dict(source_ref.get("existing") or {})
            existing["global_primitives"] = [
                {
                    "primitive_id": hit.get("primitive_id"),
                    "label": hit.get("label"),
                    "score": hit.get("score"),
                    "quality_score": hit.get("quality_score"),
                    "source_ref": hit.get("source_ref"),
                    "surface_visibility": hit.get("surface_visibility"),
                    "matched_terms": (hit.get("match_reason") or {}).get("matched_terms") or [],
                }
                for hit in hits
            ]
            source_ref["existing"] = existing
            source_ref["grounded_in_global_primitive_registry"] = "AIDevObserver surfaceable primitive quality file"
            item["source_ref"] = source_ref
            item["reuse_cards"] = [*(item.get("reuse_cards") or []), *(normalize_reuse_card(hit) for hit in hits)]
            hits_attached += len(hits)
        enriched.append(item)
    return {
        **rep,
        "report": enriched,
        "global_primitive_registry": {
            "enabled": True,
            "source": "surfaceable_quality_file+operational_primitive_export",
            "surfaceable_records": len(load_global_surfaceable_primitives()),
            "operational_records": load_operational_primitive_count(),
            "edge_foundry_records": load_edge_foundry_primitive_count(),
            "runtime_shape_records": load_runtime_shape_primitive_count(),
            "primitive_kind_records": load_primitive_kind_primitive_count(),
            "source_backed_group_records": load_source_backed_group_primitive_count(),
            "implemented_code_records": load_implemented_code_primitive_count(),
            "source_backed_group_proof_bundles": load_source_backed_group_proof_bundle_count(),
            "source_backed_group_promotion_gates": load_source_backed_group_promotion_gate_count(),
            "visibility_scope": normalize_visibility_scope(visibility_scope),
            "searched_findings": searched,
            "hits_attached": hits_attached,
            "candidate": True,
            "serves_truth": False,
        },
    }


def source_ref_key(ref: dict) -> str | None:
    """Stable memory key for one source ref, without raw transcript text."""

    if not isinstance(ref, dict):
        return None
    registry = str(ref.get("registry") or "").strip()
    kind = str(ref.get("kind") or "").strip()
    name = str(ref.get("name") or "").strip()
    path = str(ref.get("path") or "").strip()
    if not (registry and kind and name and path):
        return None
    material = {"registry": registry, "kind": kind, "name": name, "path": path, "line": ref.get("line")}
    return "src_" + _digest(material)


def source_ref_keys_from_value(value) -> list[str]:
    """Extract source-ref memory keys from a finding/source_ref payload."""

    keys: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            key = source_ref_key(node)
            if key:
                keys.append(key)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return sorted(set(keys))


def outcome_memory_scores() -> dict[str, dict]:
    """Return source-ref-key -> acted/rejected score from latest-wins outcomes."""

    records = session_store.load_recent(limit_files=SERVICE_SETTINGS.outcome_memory_files)
    latest: dict[tuple[str, str], dict] = {}
    for record in records:
        if record.get("record") != "outcome":
            continue
        sid = record.get("session_id")
        iid = record.get("intervention_id")
        if not isinstance(sid, str) or not isinstance(iid, str):
            continue
        if not record.get("source_ref_keys"):
            continue
        latest[(sid, iid)] = record

    scores: dict[str, dict] = {}
    for record in latest.values():
        outcome = str(record.get("outcome") or "")
        delta = SERVICE_SETTINGS.outcome_memory_deltas.get(outcome, 0)
        if delta == 0:
            continue
        for key in record.get("source_ref_keys") or []:
            if not isinstance(key, str) or not key:
                continue
            bucket = scores.setdefault(key, {"score": 0, "acted": 0, "rejected": 0})
            bucket["score"] += delta
            if delta > 0:
                bucket["acted"] += 1
            else:
                bucket["rejected"] += 1
    return scores


def apply_outcome_memory_to_hits(hits: list[dict]) -> list[dict]:
    """Boost/suppress local registry hits using prior Accept/Reuse/Dismiss metadata."""

    memory = outcome_memory_scores()
    if not memory:
        return hits

    out: list[dict] = []
    for hit in hits:
        item = dict(hit)
        key = source_ref_key(item.get("source_ref") or {})
        base_score = int(item.get("score") or 0)
        score_delta = int((memory.get(key or "") or {}).get("score") or 0)
        item["score_adjusted"] = base_score + score_delta
        if score_delta:
            item["outcome_memory"] = {
                "score": score_delta,
                "acted": int(memory[key]["acted"]),
                "rejected": int(memory[key]["rejected"]),
            }
        out.append(item)

    out.sort(key=lambda hit: (
        -int(hit.get("score_adjusted") if hit.get("score_adjusted") is not None else hit.get("score") or 0),
        -int(hit.get("score") or 0),
        str((hit.get("source_ref") or {}).get("kind") or ""),
        str((hit.get("source_ref") or {}).get("path") or ""),
        str((hit.get("source_ref") or {}).get("name") or ""),
    ))
    return out


def local_registry_query_for_finding(finding: dict) -> str:
    evidence = str(finding.get("evidence") or "").strip()
    if evidence:
        return " ".join((str(finding.get("type") or ""), evidence)).strip()
    return " ".join(
        str(finding.get(key) or "")
        for key in ("type", "message", "suggestion")
    ).strip()


def enrich_report_with_local_registry(
    rep: dict,
    *,
    root_value: str | Path | None,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
) -> dict:
    """Attach opt-in local source refs to review findings.

    This is candidate-only enrichment. It never fails the review and never
    includes the raw local root in the response.
    """

    has_private_context = bool(root_value) and local_registry_enabled()
    rep = enrich_report_with_global_primitives(
        rep,
        requested_input=requested_input,
        requested_output=requested_output,
        visibility_scope=normalize_visibility_scope(None, has_private_context=has_private_context),
    )

    if not root_value:
        return rep
    if not local_registry_enabled():
        return {
            **rep,
            "local_registry": {
                "enabled": False,
                "reason": "disabled_for_public_demo",
                "candidate": True,
                "serves_truth": False,
            },
        }

    root = Path(str(root_value)).expanduser()
    if not root.is_dir():
        return {
            **rep,
            "local_registry": {
                "enabled": True,
                "error": "cwd must be a directory",
                "candidate": True,
                "serves_truth": False,
            },
        }

    enriched = []
    hits_attached = 0
    searched = 0
    try:
        local_records = cached_index_local_repo(root)
    except OSError as exc:
        return {
            **rep,
            "local_registry": {
                "enabled": True,
                "error": f"cannot index repo: {exc}",
                "candidate": True,
                "serves_truth": False,
            },
        }
    for finding in rep.get("report", []):
        item = dict(finding)
        query = local_registry_query_for_finding(item)
        if query:
            searched += 1
            hits = apply_outcome_memory_to_hits(
                search_local_records(
                    query,
                    local_records,
                    limit=SERVICE_SETTINGS.local_review_hit_limit,
                    requested_input=requested_input,
                    requested_output=requested_output,
                )
            )
        else:
            hits = []
        if hits:
            compact_hits = [compact_local_source_ref(hit) for hit in hits]
            reuse_cards = [reuse_card_from_local_hit(hit, item) for hit in hits]
            source_ref = dict(item.get("source_ref") or {})
            existing = dict(source_ref.get("existing") or {})
            existing["local_repo"] = compact_hits
            source_ref["existing"] = existing
            source_ref["grounded_in_local_registry"] = "AIDevObserver local registry connector"
            item["source_ref"] = source_ref
            item["reuse_cards"] = [*(item.get("reuse_cards") or []), *reuse_cards]
            hits_attached += len(compact_hits)
        enriched.append(item)

    return {
        **rep,
        "report": enriched,
        "local_registry": {
            "enabled": True,
            "root": "explicit_cwd_or_process_cwd",
            "index_mode": "cached_in_process",
            "indexed_records": len(local_records),
            "searched_findings": searched,
            "hits_attached": hits_attached,
            "candidate": True,
            "serves_truth": False,
        },
    }


def registry_search_response(
    query: str | None,
    cwd: str | None = None,
    limit: str | int | None = None,
    *,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    visibility_scope: str | None = None,
) -> tuple[int, dict]:
    """Candidate-only local repo source-ref search response for service surfaces."""

    q = str(query or "").strip()
    if not q:
        return 400, {"error": "provide q", "serves_truth": False}
    try:
        n = int(limit or SERVICE_SETTINGS.local_registry_default_limit)
    except (TypeError, ValueError):
        n = SERVICE_SETTINGS.local_registry_default_limit
    n = max(1, min(n, SERVICE_SETTINGS.local_registry_default_limit))
    scope = normalize_visibility_scope(
        visibility_scope,
        has_private_context=bool(cwd) and local_registry_enabled(),
    )

    global_hits = [
        {
            "source_kind": hit.get("source_kind"),
            "primitive_id": hit.get("primitive_id"),
            "score": hit.get("score"),
            "quality_score": hit.get("quality_score"),
            "surface_visibility": hit.get("surface_visibility"),
            "visibility_scope": hit.get("visibility_scope") or scope,
            "candidate": True,
            "serves_truth": False,
            "reuse_card": normalize_reuse_card(hit),
        }
        for hit in search_reusable_primitives(
            q,
            limit=n,
            requested_input=requested_input,
            requested_output=requested_output,
            visibility_scope=scope,
        )
    ]

    if not local_registry_enabled():
        return 200, {
            "query": q,
            "visibility_scope": scope,
            "hits": global_hits,
            "global_primitive_registry": {
                "enabled": global_primitives_enabled(),
                "surfaceable_records": len(load_global_surfaceable_primitives()),
                "operational_records": load_operational_primitive_count(),
                "edge_foundry_records": load_edge_foundry_primitive_count(),
                "runtime_shape_records": load_runtime_shape_primitive_count(),
                "primitive_kind_records": load_primitive_kind_primitive_count(),
                "benchmark_decomposition_records": load_benchmark_decomposition_primitive_count(),
                "source_backed_group_records": load_source_backed_group_primitive_count(),
                "implemented_code_records": load_implemented_code_primitive_count(),
                "source_backed_group_proof_bundles": load_source_backed_group_proof_bundle_count(),
                "source_backed_group_promotion_gates": load_source_backed_group_promotion_gate_count(),
                "visibility_scope": scope,
                "hits": len(global_hits),
                "candidate": True,
                "serves_truth": False,
            },
            "local_registry_enabled": False,
            "reason": "disabled_for_public_demo",
            "candidate": True,
            "serves_truth": False,
        }

    root = Path(cwd).expanduser() if cwd else Path.cwd()
    if not root.is_dir():
        return 400, {"error": "cwd must be a directory", "serves_truth": False}
    try:
        hits = apply_outcome_memory_to_hits(
            search_local_repo(
                q,
                root,
                limit=n,
                requested_input=requested_input,
                requested_output=requested_output,
            )
        )
    except OSError as exc:
        return 400, {"error": f"cannot search repo: {exc}", "serves_truth": False}

    hits_with_cards = [
        {**hit, "reuse_card": reuse_card_from_local_hit(hit, {
            "type": "registry_search",
            "evidence": q,
            "suggestion": "reuse this local repo object instead of rebuilding it",
        })}
        for hit in hits
    ] + global_hits
    hits_with_cards.sort(key=_registry_hit_rank_key)
    return 200, {
        "query": q,
        "requested_input": requested_input,
        "requested_output": requested_output,
        "visibility_scope": scope,
        "hits": hits_with_cards,
        "global_primitive_registry": {
            "enabled": global_primitives_enabled(),
            "surfaceable_records": len(load_global_surfaceable_primitives()),
            "operational_records": load_operational_primitive_count(),
            "edge_foundry_records": load_edge_foundry_primitive_count(),
            "runtime_shape_records": load_runtime_shape_primitive_count(),
            "primitive_kind_records": load_primitive_kind_primitive_count(),
            "benchmark_decomposition_records": load_benchmark_decomposition_primitive_count(),
            "source_backed_group_records": load_source_backed_group_primitive_count(),
            "implemented_code_records": load_implemented_code_primitive_count(),
            "source_backed_group_proof_bundles": load_source_backed_group_proof_bundle_count(),
            "source_backed_group_promotion_gates": load_source_backed_group_promotion_gate_count(),
            "visibility_scope": scope,
            "hits": len(global_hits),
            "candidate": True,
            "serves_truth": False,
        },
        "local_registry_enabled": True,
        "root": "explicit_cwd_or_process_cwd",
        "candidate": True,
        "serves_truth": False,
    }


__all__ = [
    "LOCAL_REGISTRY_ENV",
    "apply_outcome_memory_to_hits",
    "compact_local_source_ref",
    "enrich_report_with_global_primitives",
    "enrich_report_with_local_registry",
    "global_primitives_enabled",
    "load_benchmark_decomposition_primitive_count",
    "load_edge_foundry_primitive_count",
    "load_global_surfaceable_primitives",
    "load_implemented_code_primitive_count",
    "local_registry_enabled",
    "normalize_reuse_card",
    "local_registry_query_for_finding",
    "load_operational_primitive_count",
    "load_primitive_kind_primitive_count",
    "load_runtime_shape_primitive_count",
    "load_source_backed_group_primitive_count",
    "load_source_backed_group_proof_bundle_count",
    "load_source_backed_group_proof_bundle_index",
    "load_source_backed_group_promotion_gate_count",
    "load_source_backed_group_promotion_gate_index",
    "normalize_visibility_scope",
    "outcome_memory_scores",
    "operational_primitives_enabled",
    "registry_search_response",
    "reuse_card_from_local_hit",
    "search_global_primitives",
    "search_operational_primitives",
    "search_route_level_primitives",
    "search_reusable_primitives",
    "source_ref_key",
    "source_ref_keys_from_value",
]
