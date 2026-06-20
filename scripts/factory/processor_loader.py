#!/usr/bin/env python3
"""Generic processor loader — resolves processor manifests to callables.

Hosted/runtime consumers should prefer database-shaped catalog rows and keep
YAML as bootstrap/static-site fallback. This loader follows that boundary by
reading `components.jsonl` exports when available, then falling back to
`catalog/processors/*.yaml` only when no row snapshot is present.

Allows new walkers + processors to be added without touching any runner code.
A processor manifest with:

    implementations:
      - kind: callable
        path: scripts.processors.foo_walker.run
        language: python

is loaded with `load_processor("processor/foo-walker")` and invoked.

CLI:
    python -m scripts.factory.processor_loader --list
    python -m scripts.factory.processor_loader --resolve processor/wikipedia-category-walker
    python -m scripts.factory.processor_loader --row-dir dist/catalog-db-export-rows-smoke --list
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._config import CATALOG_DIR, OH_CATALOG_ROW_DIR_ENV
from scripts.db.catalog_row_source import (
    CatalogRowComponent,
    iter_components_from_rows,
    resolve_catalog_row_dir,
)

CATALOG_PROCESSORS = CATALOG_DIR / "processors"


def _load_yaml() -> Any:
    try:
        import yaml
        return yaml
    except ImportError:
        sys.stderr.write("pyyaml is required: pip install pyyaml\n")
        sys.exit(2)


def _processor_components_from_rows(row_dir: Path | str | None = None) -> list[CatalogRowComponent] | None:
    resolved = resolve_catalog_row_dir(row_dir)
    if resolved is None:
        return None
    return [
        component
        for component in iter_components_from_rows(resolved)
        if component.type == "processor"
    ]


def _iter_yaml_processor_manifests() -> list[tuple[dict[str, Any], str]]:
    yaml = _load_yaml()
    manifests: list[tuple[dict[str, Any], str]] = []
    for path in CATALOG_PROCESSORS.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if not isinstance(data, dict) or data.get("type") != "processor":
            continue
        manifests.append((data, str(path.relative_to(ROOT))))
    return manifests


def _processor_manifest_entries(row_dir: Path | str | None = None) -> tuple[list[tuple[dict[str, Any], str]], str]:
    components = _processor_components_from_rows(row_dir)
    if components is not None:
        return [
            (component.manifest, component.source_path)
            for component in components
        ], "database_rows"
    return _iter_yaml_processor_manifests(), "catalog_yaml_fallback"


def list_processors(row_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """Return a summary of every processor manifest with its implementations."""
    entries, source = _processor_manifest_entries(row_dir)
    out: list[dict[str, Any]] = []
    for data, manifest_path in entries:
        impls = data.get("implementations") or []
        callable_paths = [
            i.get("path", "") for i in impls if isinstance(i, dict) and i.get("kind") == "callable"
        ]
        out.append(
            {
                "id": data.get("id"),
                "name": data.get("name"),
                "process_kind": data.get("process_kind"),
                "callable_paths": callable_paths,
                "manifest_path": manifest_path,
                "catalog_source": source,
            }
        )
    return out


def load_manifest(processor_id: str, row_dir: Path | str | None = None) -> dict | None:
    """Load a processor manifest by id."""
    entries, _source = _processor_manifest_entries(row_dir)
    for data, _manifest_path in entries:
        if isinstance(data, dict) and data.get("id") == processor_id and data.get("type") == "processor":
            return data
    return None


def resolve_callable(processor_id: str, row_dir: Path | str | None = None) -> Callable | None:
    """Resolve a processor id to its Python `run` callable.

    Returns the callable, or None if no `kind: callable` implementation is
    declared OR the module can't be imported.
    """
    manifest = load_manifest(processor_id, row_dir=row_dir)
    if not manifest:
        return None
    for impl in manifest.get("implementations") or []:
        if not isinstance(impl, dict) or impl.get("kind") != "callable":
            continue
        path = impl.get("path", "")
        if not path or "." not in path:
            continue
        module_path, _, attr = path.rpartition(".")
        try:
            mod = importlib.import_module(module_path)
        except ImportError:
            continue
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
    return None


def load_processor(processor_id: str, row_dir: Path | str | None = None) -> Callable:
    """Like resolve_callable but raises if not found (for orchestrator-side use)."""
    fn = resolve_callable(processor_id, row_dir=row_dir)
    if fn is None:
        raise RuntimeError(f"no callable implementation found for {processor_id!r}")
    return fn


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Resolve processor manifests to Python callables.")
    p.add_argument(
        "--row-dir",
        type=Path,
        default=os.environ.get(OH_CATALOG_ROW_DIR_ENV),
        help="Database-shaped catalog row directory. Defaults to OH_CATALOG_ROW_DIR or the bridge export if present.",
    )
    p.add_argument("--list", action="store_true", help="List all processors + their declared callable paths")
    p.add_argument("--resolve", help="Resolve a specific processor id and print verification result")
    args = p.parse_args(argv)

    if args.list:
        rows = list_processors(row_dir=args.row_dir)
        n_callable = sum(1 for r in rows if r["callable_paths"])
        source = rows[0]["catalog_source"] if rows else "none"
        print(f"{len(rows)} processor manifests from {source}, {n_callable} with callable implementations declared:")
        for r in sorted(rows, key=lambda r: r["id"] or ""):
            mark = "✓" if r["callable_paths"] else " "
            print(f"  {mark} {r['id']:50s}  {r['callable_paths']}")
        return 0

    if args.resolve:
        fn = resolve_callable(args.resolve, row_dir=args.row_dir)
        if fn is None:
            sys.stderr.write(f"failed to resolve {args.resolve!r}\n")
            return 1
        print(json.dumps({
            "processor_id": args.resolve,
            "module": fn.__module__,
            "callable": fn.__qualname__,
            "doc": (fn.__doc__ or "").strip()[:200],
        }, indent=2, ensure_ascii=False))
        return 0

    p.error("--list or --resolve required")
    return 2


if __name__ == "__main__":
    sys.exit(_main())
