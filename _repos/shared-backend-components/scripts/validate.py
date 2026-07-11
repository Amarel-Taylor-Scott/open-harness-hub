#!/usr/bin/env python3
"""Validate every manifest under _repos/shared-backend-components/catalog/ against its JSON Schema.

Also checks:
  - every `ref` field points to an existing component id;
  - every leaf type referenced is in vocabularies/leaf-types.yaml;
  - industry / capability / modality / lifecycle tags are in their vocabularies;
  - prompt_abi.cache_scope values are in vocabularies/cache-scopes.yaml;
  - pipeline DAGs have no cycles or dangling step refs;
  - (release scope) every `implementations[].path` callable contract that points
    at an in-repo module actually resolves — a catalog that declares an
    executable `kind: callable` path must not point at a module that does not
    exist. Reported as a warning by default; `--check-impl-paths` makes it fatal.

Exit code is non-zero on the first failure.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*` on
# a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch. install() prepends every code root so
# `from scripts.*` (and `from src.*`) resolve; ROOT below (parents[1]) stays the substrate root used for logic.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    sys.stderr.write("jsonschema is required: pip install jsonschema\n")
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCHEMAS = _resource("schemas")
CATALOG = _resource("catalog")
VOCABS = _resource("vocabularies")
COMPONENT_ID_INDEX = _resource("dist") / "catalog-component-ids.json"
MANIFEST_BRIDGE_DIR = _resource("dist") / "catalog-manifest-bridge"
MANIFEST_BRIDGE_RECORDS = MANIFEST_BRIDGE_DIR / "manifest_import_records.jsonl"
SCHEMA_SQL = _resource("db") / "postgres" / "schema.sql"
DB_SEEDS = _resource("db") / "seeds"
DRIFT_WARNING_SAMPLE_LIMIT = 5

from scripts._config import (
    OBJECT_GOVERNANCE_PACKAGE_TABLES,
    OBJECT_GOVERNANCE_REQUIRED_FAMILIES,
    OBJECT_GOVERNANCE_RUBRIC_ID,
    PRIMITIVE_REGISTRY_OPERATIONAL_TABLES,
    PRIMITIVE_REGISTRY_OPERATIONAL_VIEWS,
)

TYPE_TO_SCHEMA = {
    "harness":        "harness.schema.json",
    "pipeline":       "pipeline.schema.json",
    "benchmark":      "benchmark.schema.json",
    "rule-pack":      "rule-pack.schema.json",
    "knowledge-pack": "knowledge-pack.schema.json",
    "logic-pack":     "logic-pack.schema.json",
    "tool":           "tool.schema.json",
    "persona":        "persona.schema.json",
    "adapter":        "adapter.schema.json",
    "rubric":         "rubric.schema.json",
    "dataset":        "dataset.schema.json",
    "processor":      "processor.schema.json",
    "pattern":        "pattern.schema.json",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schemas() -> dict[str, dict]:
    common = json.loads((SCHEMAS / "_common.schema.json").read_text())
    schemas: dict[str, dict] = {"_common.schema.json": common}
    for name in TYPE_TO_SCHEMA.values():
        schemas[name] = json.loads((SCHEMAS / name).read_text())
    return schemas


def load_vocab(name: str) -> set[str]:
    path = VOCABS / f"{name}.yaml"
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text())
    keys = list(data.keys())
    if not keys:
        return set()
    items = data[keys[0]]
    out: set[str] = set()
    for item in items:
        out.add(item["id"])
        for sub in item.get("sub", []) or []:
            out.add(sub["id"])
    return out


def make_validator(schemas: dict[str, dict], schema_name: str) -> Draft202012Validator:
    schema = schemas[schema_name]
    base = (SCHEMAS).as_uri() + "/"
    resolver = jsonschema.RefResolver(base_uri=base, referrer=schema, store={
        base + name: doc for name, doc in schemas.items()
    })
    return Draft202012Validator(schema, resolver=resolver)


def collect_manifests(paths: list[Path] | None = None) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    candidates = paths if paths is not None else list(CATALOG.rglob("*.yaml"))
    for path in candidates:
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix not in {".yaml", ".yml"}:
            continue
        if "_inbox" in path.parts:
            continue
        data = load_yaml(path)
        if not isinstance(data, dict) or "type" not in data:
            continue
        out.append((path, data))
    return out


def _cache_path_fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.relative_to(ROOT)),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def _component_id_index_is_fresh(cache: dict[str, Any]) -> tuple[bool, str]:
    cached_paths = cache.get("paths")
    if not isinstance(cached_paths, dict):
        return False, "missing paths map"
    current_paths = {
        str(path.relative_to(ROOT)): path
        for path in CATALOG.rglob("*.yaml")
        if "_inbox" not in path.parts and "data" not in path.parts
    }
    if set(cached_paths) != set(current_paths):
        return False, "manifest path set changed"
    for rel, path in current_paths.items():
        cached = cached_paths.get(rel) or {}
        now = _cache_path_fingerprint(path)
        if cached.get("mtime_ns") != now["mtime_ns"] or cached.get("size") != now["size"]:
            return False, f"stale manifest: {rel}"
    return True, "fresh"


def load_component_id_index() -> tuple[set[str] | None, str]:
    if not COMPONENT_ID_INDEX.exists():
        return None, "component id index missing"
    try:
        cache = json.loads(COMPONENT_ID_INDEX.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"component id index unreadable: {exc}"
    if not isinstance(cache, dict) or cache.get("version") != "0.1.0":
        return None, "component id index has unsupported version"
    fresh, reason = _component_id_index_is_fresh(cache)
    if not fresh:
        return None, reason
    components = cache.get("components")
    if not isinstance(components, dict):
        return None, "component id index missing components map"
    return set(components), f"loaded {len(components)} ids from dist/catalog-component-ids.json"


def check_refs(manifest: dict, known_ids: set[str], errors: list[str]) -> None:
    """Walk the manifest looking for ref-shaped strings that must resolve."""
    def walk(node: Any, key_path: str = "") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                # `examples`/`example` carry illustrative I/O payloads, not
                # component wiring. Their values can legitimately look like a
                # `type/slug` ref (e.g. a tenant namespace "pipeline/gdpr-review"
                # or a sample message), so they must not be resolved as refs.
                # Real wiring refs live in declared fields (consumes/emits/
                # steps[].ref/model_targets/packs), never inside examples.
                if k in {"examples", "example"}:
                    continue
                walk(v, f"{key_path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{key_path}[{i}]")
        elif isinstance(node, str):
            if re.fullmatch(r"(harness|pipeline|benchmark|rule-pack|knowledge-pack|logic-pack|tool|persona|adapter|rubric|dataset|schema|processor|pattern)/[a-z0-9]+(-[a-z0-9]+)*", node):
                if node not in known_ids and not key_path.endswith(".id"):
                    errors.append(f"  unresolved ref {node!r} at {key_path}")
    walk(manifest)


# Only `tool` and `processor` schemas carry an `implementations[]` array whose
# entries can declare an executable callable. Keep this in sync with those
# schemas' `implementations.items.properties.kind` enums — both list "callable".
_CALLABLE_IMPL_KIND = "callable"


def _in_repo_top_levels() -> set[str]:
    """Top-level Python package/module names that live in *this* repository.

    A callable `path` like `scripts.processors.cache.cache_exact.run` is an
    in-repo contract we can resolve; a path like `tools.web_search.run`,
    `anthropic.Anthropic.messages.create`, or `src/middleware/...` is a
    descriptive / third-party contract whose module is *not* shipped here and
    must not be resolved (resolving it would always fail for reasons unrelated
    to a broken stub). We detect "in-repo" structurally — a top-level segment
    is ours iff a directory `<ROOT>/<seg>` or a module `<ROOT>/<seg>.py` exists
    — rather than hard-coding a namespace list (no-magic-values).
    """
    out: set[str] = set()
    for child in ROOT.iterdir():
        if child.is_dir() and (child / "__init__.py").exists():
            out.add(child.name)
        elif child.is_file() and child.suffix == ".py":
            out.add(child.stem)
    return out


def _ensure_root_importable() -> None:
    """Put the repo root on sys.path so in-repo packages (e.g. `scripts`) import.

    When this file runs as `python3 _repos/shared-backend-components/scripts/validate.py`, `sys.path[0]` is the
    *_repos/shared-backend-components/scripts/* directory, not the repo root, so `import scripts` (and any other
    top-level repo package) would fail under `importlib.util.find_spec` even
    though the package exists. Insert ROOT once, idempotently; running as a
    module already has ROOT on the path so this is a no-op there.
    """
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _callable_path_resolves(path: str) -> tuple[bool, str]:
    """Return (ok, reason) for a dotted callable path's *module* (and attr).

    `importlib.util.find_spec` only locates the module — it does not import or
    execute it, so this is side-effect-free and safe to run in CI. We try the
    longest module prefix first (treating the final dotted segment as a callable
    attribute, e.g. `…structural_compress.run`); if that module exists we accept
    it (we do not import to confirm the attribute, since that would run code).
    If the prefix module is absent we fall back to treating the whole dotted
    path as a module (some paths point straight at a module, no attribute).
    """
    candidates: list[str] = []
    if "." in path:
        module, _attr = path.rsplit(".", 1)
        candidates.append(module)
    candidates.append(path)
    for module in candidates:
        try:
            spec = importlib.util.find_spec(module)
        except (ImportError, ValueError, AttributeError, TypeError) as exc:
            # ModuleNotFoundError (a subclass of ImportError) is raised when a
            # *parent* package is missing; treat every locate failure as "not
            # this candidate" and try the next, never crash the validator.
            spec = None
            last = f"{type(exc).__name__}: {exc}"
        else:
            last = "module not found"
        if spec is not None:
            return True, "resolves"
    return False, last


def check_impl_paths(manifest: dict, in_repo: set[str], errors: list[str]) -> None:
    """Flag `implementations[].path` callables whose in-repo module is missing.

    Only `kind: callable` entries with a `path` are checked, and only when the
    path's first dotted segment names a package/module that lives in this repo.
    Descriptive or third-party callable paths (whose top-level package is not
    shipped here) are skipped — exactly the way `examples` are skipped in
    `check_refs` — because they are contracts, not in-repo wiring.
    """
    impls = manifest.get("implementations")
    if not isinstance(impls, list):
        return
    for idx, impl in enumerate(impls):
        if not isinstance(impl, dict):
            continue
        if impl.get("kind") != _CALLABLE_IMPL_KIND:
            continue
        path = impl.get("path")
        if not isinstance(path, str) or not path:
            continue
        top = path.split(".", 1)[0]
        if top not in in_repo:
            continue  # third-party / descriptive contract, not ours to resolve
        ok, reason = _callable_path_resolves(path)
        if not ok:
            errors.append(
                f"  implementations[{idx}].path {path!r} does not resolve ({reason})"
            )


def _catalog_manifest_paths() -> list[Path]:
    return [
        path
        for path in CATALOG.rglob("*.yaml")
        if "_inbox" not in path.parts and "data" not in path.parts
    ]


def _manifest_bridge_warnings() -> list[str]:
    manifests = _catalog_manifest_paths()
    if not manifests:
        return []
    if not MANIFEST_BRIDGE_RECORDS.exists():
        return [
            (
                "database-backed catalog drift: manifest bridge records are "
                f"missing at {MANIFEST_BRIDGE_RECORDS.relative_to(ROOT)}; "
                "run scripts/db/catalog_manifest_bridge.py before treating YAML "
                "manifests as imported operational rows."
            )
        ]

    bridge_mtime = MANIFEST_BRIDGE_RECORDS.stat().st_mtime_ns
    stale = [
        path.relative_to(ROOT)
        for path in manifests
        if path.stat().st_mtime_ns > bridge_mtime
    ]
    if not stale:
        return []
    sample = ", ".join(str(path) for path in stale[:DRIFT_WARNING_SAMPLE_LIMIT])
    return [
        (
            "database-backed catalog drift: "
            f"{len(stale)} catalog manifest(s) are newer than "
            f"{MANIFEST_BRIDGE_RECORDS.relative_to(ROOT)}; refresh the bridge "
            f"output. Sample: {sample}"
        )
    ]


def _hardcoded_setting_warnings() -> list[str]:
    try:
        from scripts.audit_context_storage import audit_hardcoded_settings
    except Exception as exc:  # pragma: no cover - defensive release warning.
        return [f"hard-coded setting drift audit unavailable: {type(exc).__name__}: {exc}"]

    report = audit_hardcoded_settings()
    warnings: list[str] = []
    if report.get("unregistered_repeated_model_literal_count", 0):
        warnings.append(
            "hard-coded setting drift: "
            f"{report['unregistered_repeated_model_literal_count']} unregistered "
            "repeated model literal group(s) should move to scripts._config or "
            "setting_profile rows."
        )
    if report.get("unregistered_repeated_backend_literal_count", 0):
        warnings.append(
            "hard-coded setting drift: "
            f"{report['unregistered_repeated_backend_literal_count']} unregistered "
            "repeated backend literal group(s) should move to scripts._config or "
            "setting_profile rows."
        )
    if report.get("repeated_vector_dimension_count", 0):
        warnings.append(
            "hard-coded setting drift: "
            f"{report['repeated_vector_dimension_count']} repeated unregistered "
            "vector dimension group(s) should use the shared embedding/vector "
            "profile registry."
        )
    if report.get("private_runtime_setting_resolver_bypass_count", 0):
        warnings.append(
            "hard-coded setting drift: "
            f"{report['private_runtime_setting_resolver_bypass_count']} private "
            "runtime setting resolver bypass(es) should use "
            "scripts.db.runtime_settings.runtime_setting."
        )

    candidates = report.get("migration_candidates") or []
    for candidate in candidates[:DRIFT_WARNING_SAMPLE_LIMIT]:
        locations = candidate.get("first_locations") or []
        first = locations[0] if locations else {}
        location = f"{first.get('path')}:{first.get('line')}" if first else "unknown"
        warnings.append(
            "  setting migration candidate: "
            f"{candidate.get('kind')} {candidate.get('value')!r} "
            f"({candidate.get('occurrences')} occurrences; first {location})"
        )
    return warnings


def _schema_table_present(schema_text: str, table_name: str) -> bool:
    pattern = rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{re.escape(table_name)}\b"
    return re.search(pattern, schema_text, re.IGNORECASE) is not None


def _schema_view_present(schema_text: str, view_name: str) -> bool:
    pattern = rf"CREATE\s+OR\s+REPLACE\s+VIEW\s+{re.escape(view_name)}\b"
    return re.search(pattern, schema_text, re.IGNORECASE) is not None


def _schema_vector_dimension_warnings(schema_text: str, *, warning_prefix: str) -> list[str]:
    """Return drift warnings for every vector(N) column/type in schema.sql."""
    try:
        from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS
    except Exception as exc:  # pragma: no cover - defensive
        return [f"{warning_prefix}: embedding-dimension check unavailable: {type(exc).__name__}"]

    warnings: list[str] = []
    dimensions = sorted({int(match) for match in re.findall(r"\bvector\((\d+)\)", schema_text)})
    mismatches = [dimension for dimension in dimensions if dimension != DEFAULT_EMBEDDING_DIMENSIONS]
    if mismatches:
        warnings.append(
            f"{warning_prefix}: schema.sql vector dimensions {mismatches} != "
            f"DEFAULT_EMBEDDING_DIMENSIONS ({DEFAULT_EMBEDDING_DIMENSIONS}) — render vector types "
            "from scripts._config.pgvector_type"
        )
    return warnings


def _primitive_registry_schema_warnings() -> list[str]:
    if not SCHEMA_SQL.exists():
        return [f"primitive registry schema drift: missing {SCHEMA_SQL.relative_to(ROOT)}"]

    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    warnings: list[str] = []
    missing_tables = [
        table for table in PRIMITIVE_REGISTRY_OPERATIONAL_TABLES
        if not _schema_table_present(schema_text, table)
    ]
    if missing_tables:
        warnings.append(
            "primitive registry schema drift: canonical schema is missing "
            f"expected table(s): {', '.join(missing_tables)}"
        )
    missing_views = [
        view for view in PRIMITIVE_REGISTRY_OPERATIONAL_VIEWS
        if not _schema_view_present(schema_text, view)
    ]
    if missing_views:
        warnings.append(
            "primitive registry schema drift: canonical schema is missing "
            f"expected operational view(s): {', '.join(missing_views)}"
        )
    warnings.extend(
        _schema_vector_dimension_warnings(
            schema_text,
            warning_prefix="primitive registry schema drift",
        )
    )
    return warnings


def _object_governance_package_warnings(known_ids: set[str]) -> list[str]:
    if not SCHEMA_SQL.exists():
        return [f"object governance package drift: missing {SCHEMA_SQL.relative_to(ROOT)}"]

    schema_text = SCHEMA_SQL.read_text(encoding="utf-8")
    missing_tables = [
        table for table in OBJECT_GOVERNANCE_PACKAGE_TABLES
        if not _schema_table_present(schema_text, table)
    ]
    warnings: list[str] = []
    if missing_tables:
        warnings.append(
            "object governance package drift: canonical schema is missing "
            f"expected table(s): {', '.join(missing_tables)}"
        )

    # vector(N) drift guard (no-magic-values): every canonical pgvector column
    # dimension MUST equal the single source in scripts._config. A model swap
    # there must not silently leave `psql -f schema.sql` creating wrong-width
    # columns the live load then rejects.
    warnings.extend(
        _schema_vector_dimension_warnings(
            schema_text,
            warning_prefix="object governance package drift",
        )
    )

    try:
        from scripts.db.object_governance_view_probe import probe_object_governance_views
    except Exception as exc:  # pragma: no cover - defensive release warning.
        warnings.append(
            "object governance package drift: operational view check unavailable: "
            f"{type(exc).__name__}: {exc}"
        )
    else:
        view_probe = probe_object_governance_views(schema_sql=SCHEMA_SQL)
        missing_views = [
            str(view.get("name"))
            for view in view_probe.get("schema_views", [])
            if not view.get("present")
        ]
        if missing_views:
            warnings.append(
                "object governance package drift: canonical schema is missing "
                f"expected operational view(s): {', '.join(missing_views)}"
            )

    if OBJECT_GOVERNANCE_RUBRIC_ID not in known_ids:
        warnings.append(
            "object governance package drift: required review rubric "
            f"{OBJECT_GOVERNANCE_RUBRIC_ID!r} is not present in the catalog."
        )

    package_row_candidates: list[Path] = []
    seed_bases = (
        _resource("seed"),
        _resource("seeds"),
        DB_SEEDS,
        MANIFEST_BRIDGE_DIR,
    )
    for base in seed_bases:
        if not base.exists():
            continue
        package_row_candidates.extend(
            path for path in base.rglob("*")
            if path.is_file() and "object_governance" in path.name
        )

    if not package_row_candidates:
        warnings.append(
            "object governance package drift: governance tables/rubric exist, "
            "but no object_governance seed/export row artifacts were found for "
            f"required families: {', '.join(OBJECT_GOVERNANCE_REQUIRED_FAMILIES)}."
        )
    else:
        profile_families: set[str] = set()
        for path in package_row_candidates:
            if path.name != "object_governance_profile.jsonl":
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                family = row.get("object_family")
                if isinstance(family, str) and family:
                    profile_families.add(family)
        if profile_families:
            missing_families = [
                family for family in OBJECT_GOVERNANCE_REQUIRED_FAMILIES
                if family not in profile_families
            ]
            if missing_families:
                warnings.append(
                    "object governance package drift: profile seed/export rows "
                    "are missing required object family baseline(s): "
                    f"{', '.join(missing_families)}."
                )
        try:
            from scripts.db.object_governance_registry import package_seed_coverage_errors
        except Exception as exc:  # pragma: no cover - defensive release warning.
            warnings.append(
                "object governance package drift: seed coverage check unavailable: "
                f"{type(exc).__name__}: {exc}"
            )
        else:
            for error in package_seed_coverage_errors():
                warnings.append(f"object governance package drift: {error}")
    return warnings


def collect_release_drift_warnings(known_ids: set[str]) -> list[str]:
    """Return warning-first release drift findings.

    These checks intentionally do not change the validation exit code yet.
    They make database-backed migration drift, hard-coded setting drift, and
    object-governance package gaps visible before later promotion to gates.
    """
    warnings: list[str] = []
    warnings.extend(_manifest_bridge_warnings())
    warnings.extend(_hardcoded_setting_warnings())
    warnings.extend(_primitive_registry_schema_warnings())
    warnings.extend(_object_governance_package_warnings(known_ids))
    return warnings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OpenHubForAI manifests.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional manifest paths to validate. Defaults to every manifest under catalog/.",
    )
    parser.add_argument(
        "--global-ref-check",
        action="store_true",
        help="For selected-path validation, also scan the full catalog to verify cross-component refs.",
    )
    parser.add_argument(
        "--no-component-id-cache",
        action="store_true",
        help="Do not use dist/catalog-component-ids.json for selected-path global ref checks.",
    )
    parser.add_argument(
        "--check-impl-paths",
        action="store_true",
        help=(
            "Make a dangling in-repo implementations[].path callable a hard "
            "failure. Without this flag the resolver still runs during release "
            "scope (full run or --global-ref-check) but only warns, so the "
            "current tree's not-yet-built stubs do not block the build."
        ),
    )
    parser.add_argument(
        "--skip-drift-warnings",
        action="store_true",
        help=(
            "Skip non-fatal release-scope drift warnings for database-backed "
            "migration state, hard-coded settings, and object-governance packages."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    schemas = load_schemas()
    industries  = load_vocab("industries")
    capabilities = load_vocab("capabilities")
    modalities  = load_vocab("modalities")
    leaf_types  = load_vocab("leaf-types")
    cache_scopes = load_vocab("cache-scopes")

    if args.paths:
        selected_paths = [(_resource(p)).resolve() if not Path(p).is_absolute() else Path(p).resolve() for p in args.paths]
        manifests = collect_manifests(selected_paths)
        if args.global_ref_check:
            known_ids = None
            cache_msg = ""
            if not args.no_component_id_cache:
                known_ids, cache_msg = load_component_id_index()
            if known_ids is None:
                if cache_msg:
                    print(f"  note: component id cache not used ({cache_msg}); scanning catalog")
                all_manifests = collect_manifests()
                known_ids = {m["id"] for _, m in all_manifests if "id" in m}
            else:
                print(f"  note: {cache_msg}")
            run_ref_check = True
        else:
            known_ids = {m["id"] for _, m in manifests if "id" in m}
            run_ref_check = False
    else:
        manifests = collect_manifests()
        known_ids = {m["id"] for _, m in manifests if "id" in m}
        run_ref_check = True

    scope = "selected" if args.paths else "all"
    print(f"validating {len(manifests)} {scope} manifests …")
    if args.paths and not run_ref_check:
        print("  note: global cross-component ref check skipped; use --global-ref-check for release validation")
    failures = 0
    # In-repo callable-path resolution is release-scope (full run or
    # --global-ref-check), like the cross-component ref check. Resolve the set
    # of in-repo top-level packages once. Dangling in-repo callables are fatal
    # only under --check-impl-paths; otherwise they are collected as warnings so
    # not-yet-built stubs in the current tree do not block the build.
    in_repo = _in_repo_top_levels() if run_ref_check else set()
    if in_repo:
        _ensure_root_importable()
    impl_path_warnings: list[str] = []

    for path, manifest in manifests:
        rel = path.relative_to(ROOT)
        type_ = manifest.get("type")
        schema_name = TYPE_TO_SCHEMA.get(type_)
        if schema_name is None:
            print(f"FAIL {rel}: unknown type {type_!r}")
            failures += 1
            continue

        validator = make_validator(schemas, schema_name)
        errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
        msg_errors = [f"  {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]

        # vocabulary checks
        for ind in manifest.get("industry", []) or []:
            if industries and ind not in industries:
                msg_errors.append(f"  industry/{ind} not in vocabularies/industries.yaml")
        for cap in manifest.get("capability", []) or []:
            if capabilities and cap not in capabilities:
                msg_errors.append(f"  capability/{cap} not in vocabularies/capabilities.yaml")
        for mod in manifest.get("modality", []) or []:
            if modalities and mod not in modalities:
                msg_errors.append(f"  modality/{mod} not in vocabularies/modalities.yaml")
        for lt in manifest.get("consumes", []) or []:
            if leaf_types and lt not in leaf_types:
                msg_errors.append(f"  consumes/{lt} not in vocabularies/leaf-types.yaml")
        for lt in manifest.get("emits", []) or []:
            if leaf_types and lt not in leaf_types:
                msg_errors.append(f"  emits/{lt} not in vocabularies/leaf-types.yaml")
        prompt_abi = manifest.get("prompt_abi")
        if isinstance(prompt_abi, dict):
            cache_scope = prompt_abi.get("cache_scope")
            if cache_scope and cache_scopes and cache_scope not in cache_scopes:
                msg_errors.append(f"  prompt_abi.cache_scope/{cache_scope} not in vocabularies/cache-scopes.yaml")

        if run_ref_check:
            ref_errors: list[str] = []
            check_refs(manifest, known_ids, ref_errors)
            msg_errors.extend(ref_errors)

            impl_errors: list[str] = []
            check_impl_paths(manifest, in_repo, impl_errors)
            if args.check_impl_paths:
                msg_errors.extend(impl_errors)
            else:
                impl_path_warnings.extend(f"  {rel}\n  {line.lstrip()}" for line in impl_errors)

        if msg_errors:
            print(f"FAIL {rel}")
            for line in msg_errors:
                print(line)
            failures += 1
        else:
            print(f"  ok {rel}")

    if impl_path_warnings:
        print(
            f"\nwarning: {len(impl_path_warnings)} in-repo implementations[].path "
            "callable(s) do not resolve (not-yet-built stubs); pass "
            "--check-impl-paths to make these fatal:"
        )
        for line in impl_path_warnings:
            print(line)

    if run_ref_check and not args.skip_drift_warnings:
        drift_warnings = collect_release_drift_warnings(known_ids)
        if drift_warnings:
            print(
                "\nwarning: release drift findings are advisory for now; "
                "resolve or baseline them before promoting to hard gates:"
            )
            for warning in drift_warnings:
                print(f"  {warning}")

    if failures:
        print(f"\n{failures} manifest(s) failed validation.")
        return 1
    print("\nall manifests valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
