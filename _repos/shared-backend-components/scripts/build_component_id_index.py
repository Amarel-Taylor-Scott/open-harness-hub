#!/usr/bin/env python3
"""Build a lightweight component-id cache for fast selected validation.

The cache stores id -> path/type plus per-manifest mtime/size. It lets
`_repos/shared-backend-components/scripts/validate.py --global-ref-check <changed paths>` verify references
against a persisted id set instead of parsing every YAML manifest on each run.

Usage:
    python3 _repos/shared-backend-components/scripts/build_component_id_index.py
    python3 _repos/shared-backend-components/scripts/build_component_id_index.py --check-fresh
    python3 _repos/shared-backend-components/scripts/build_component_id_index.py --update catalog/tools/example.yaml
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
CATALOG = _resource("catalog")
DIST = _resource("dist")
OUT = DIST / "catalog-component-ids.json"


def iter_manifest_paths() -> list[Path]:
    return [
        path
        for path in sorted(CATALOG.rglob("*.yaml"))
        if "_inbox" not in path.parts and "data" not in path.parts
    ]


def path_fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.relative_to(ROOT)),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
    }


def load_cache(path: Path = OUT) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or data.get("version") != "0.1.0":
        return None
    return data


def cache_is_fresh(cache: dict[str, Any]) -> tuple[bool, str]:
    cached_paths = cache.get("paths")
    if not isinstance(cached_paths, dict):
        return False, "missing paths map"
    current_paths = {str(path.relative_to(ROOT)): path for path in iter_manifest_paths()}
    if set(cached_paths) != set(current_paths):
        return False, "manifest path set changed"
    for rel, path in current_paths.items():
        cached = cached_paths.get(rel) or {}
        now = path_fingerprint(path)
        if cached.get("mtime_ns") != now["mtime_ns"] or cached.get("size") != now["size"]:
            return False, f"stale manifest: {rel}"
    return True, "fresh"


def build_index() -> dict[str, Any]:
    components: dict[str, dict[str, Any]] = {}
    paths: dict[str, dict[str, Any]] = {}
    duplicates: dict[str, list[str]] = {}
    for path in iter_manifest_paths():
        rel = str(path.relative_to(ROOT))
        paths[rel] = path_fingerprint(path)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise RuntimeError(f"failed to parse {rel}: {exc}") from exc
        if not isinstance(data, dict) or not data.get("id") or not data.get("type"):
            continue
        component_id = data["id"]
        row = {
            "id": component_id,
            "type": data["type"],
            "path": rel,
            "name": data.get("name", component_id),
        }
        if component_id in components:
            duplicates.setdefault(component_id, [components[component_id]["path"]]).append(rel)
        components[component_id] = row
    return {
        "version": "0.1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(ROOT),
        "component_count": len(components),
        "components": components,
        "paths": paths,
        "duplicates": duplicates,
    }


def _normalize_rel_path(path_value: str | Path) -> tuple[Path, str]:
    path = Path(path_value)
    if not path.is_absolute():
        path = _resource(path)
    path = path.resolve()
    try:
        rel = str(path.relative_to(ROOT))
    except ValueError as exc:
        raise ValueError(f"path is outside repository root: {path}") from exc
    return path, rel


def _load_component_row(path: Path, rel: str) -> dict[str, Any] | None:
    if "_inbox" in path.parts or "data" in path.parts or path.suffix not in {".yaml", ".yml"}:
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeError(f"failed to parse {rel}: {exc}") from exc
    if not isinstance(data, dict) or not data.get("id") or not data.get("type"):
        return None
    component_id = str(data["id"])
    return {
        "id": component_id,
        "type": str(data["type"]),
        "path": rel,
        "name": data.get("name", component_id),
    }


def update_index_paths(path_values: list[str], *, cache_path: Path = OUT) -> dict[str, Any]:
    cache = load_cache(cache_path)
    if cache is None:
        cache = build_index()
    components = cache.setdefault("components", {})
    paths = cache.setdefault("paths", {})
    if not isinstance(components, dict) or not isinstance(paths, dict):
        raise ValueError("component id cache is malformed")

    changed: list[str] = []
    removed: list[str] = []
    for raw_path in path_values:
        path, rel = _normalize_rel_path(raw_path)
        old_ids = [
            component_id
            for component_id, row in list(components.items())
            if isinstance(row, dict) and row.get("path") == rel
        ]
        for component_id in old_ids:
            components.pop(component_id, None)
        if path.exists():
            paths[rel] = path_fingerprint(path)
            row = _load_component_row(path, rel)
            if row:
                existing = components.get(row["id"])
                if isinstance(existing, dict) and existing.get("path") != rel:
                    cache.setdefault("duplicates", {}).setdefault(row["id"], [existing.get("path")]).append(rel)
                components[row["id"]] = row
            changed.append(rel)
        else:
            paths.pop(rel, None)
            removed.append(rel)

    cache["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cache["component_count"] = len(components)
    cache["last_incremental_update"] = {
        "changed_paths": changed,
        "removed_paths": removed,
        "updated_at": cache["generated_at"],
    }
    return cache


def write_index(index: dict[str, Any], path: Path = OUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check the component-id cache.")
    parser.add_argument("--check-fresh", action="store_true", help="Exit 0 only if the existing cache is fresh")
    parser.add_argument(
        "--update",
        nargs="*",
        default=[],
        help="Incrementally update the cache for changed manifest paths instead of reparsing the full catalog.",
    )
    args = parser.parse_args(argv)

    if args.check_fresh and args.update:
        parser.error("--check-fresh and --update cannot be combined")

    if args.check_fresh:
        cache = load_cache()
        if cache is None:
            print("component id index missing or unreadable")
            return 1
        fresh, reason = cache_is_fresh(cache)
        print(json.dumps({"fresh": fresh, "reason": reason, "component_count": cache.get("component_count")}, indent=2))
        return 0 if fresh else 1

    if args.update:
        index = update_index_paths(args.update)
        write_index(index)
        print(json.dumps({
            "updated": len(args.update),
            "component_count": index.get("component_count"),
            "duplicates": index.get("duplicates", {}),
            "last_incremental_update": index.get("last_incremental_update"),
        }, indent=2, sort_keys=True))
        return 1 if index.get("duplicates") else 0

    index = build_index()
    write_index(index)
    if index["duplicates"]:
        print(json.dumps({"duplicates": index["duplicates"]}, indent=2), file=sys.stderr)
        return 1
    print(f"wrote {OUT.relative_to(ROOT)} with {index['component_count']} component ids")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
