#!/usr/bin/env python3
"""scripts.build_processor_dispatch_index — build the committed processor dispatch index.

The governed runtime is stdlib-only (proof C35 / `check_no_uncataloged_github_repos`), so the
runtime's `catalog_processor_bridge` must NOT parse YAML. This builder lives OUTSIDE the
governed scope (it may use pyyaml), scans the processor manifests, and writes
`_repos/shared-backend-components/architecture/processor_dispatch_index.json` — the single, committed, stdlib-`json`-readable
map the runtime dispatches from:

    {"version": 1, "generated_from": "_repos/shared-backend-components/catalog/processors", "by_id": {
       "processor/cache-exact": {"process_kind": "cache.exact_hash",
                                 "callable_path": "scripts.processors.cache.cache_exact.run",
                                 "deterministic": true, "side_effects": "read",
                                 "inputs": ["key"], "outputs": ["hit"]}, ...}}

`--check-fresh` rebuilds in memory and exits nonzero if the committed file has drifted from the
manifests (the drift gate; wired into the flywheel). `--write` regenerates it.

CLI:
    python3 _repos/shared-backend-components/scripts/build_processor_dispatch_index.py --write
    python3 _repos/shared-backend-components/scripts/build_processor_dispatch_index.py --check-fresh
    python3 _repos/shared-backend-components/scripts/build_processor_dispatch_index.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

_REPO = Path(__file__).resolve().parent.parent
_CATALOG_PROCESSORS = _resource("catalog") / "processors"
_INDEX_PATH = _resource("architecture") / "processor_dispatch_index.json"

_IN_REPO_PREFIXES = ("scripts.", "src.")
_CALLABLE_KIND = "callable"
_INDEX_VERSION = 1


def build_index() -> dict[str, Any]:
    """Scan the processor manifests → the dispatch index (deterministic, sorted)."""
    by_id: dict[str, dict[str, Any]] = {}
    for p in sorted(_CATALOG_PROCESSORS.rglob("*.yaml")):
        if "_inbox" in p.parts:
            continue
        try:
            manifest = yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(manifest, dict) or manifest.get("type") != "processor" or "id" not in manifest:
            continue
        for impl in manifest.get("implementations") or []:
            if not isinstance(impl, dict) or impl.get("kind") != _CALLABLE_KIND:
                continue
            path = impl.get("path")
            if not isinstance(path, str) or not path.startswith(_IN_REPO_PREFIXES):
                continue
            by_id[str(manifest["id"])] = {
                "process_kind": str(manifest.get("process_kind", "")),
                "callable_path": path,
                "deterministic": bool(manifest.get("deterministic", False)),
                "side_effects": manifest.get("side_effects", "unknown"),
                "inputs": [i.get("name") for i in (manifest.get("inputs") or []) if isinstance(i, dict)],
                "outputs": [o.get("name") for o in (manifest.get("outputs") or []) if isinstance(o, dict)],
            }
            break
    return {"version": _INDEX_VERSION, "generated_from": "catalog/processors",
            "component_count": len(by_id), "by_id": dict(sorted(by_id.items()))}


def _serialize(index: dict[str, Any]) -> str:
    return json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_index() -> dict[str, Any]:
    index = build_index()
    _INDEX_PATH.write_text(_serialize(index), encoding="utf-8")
    return index


def check_fresh() -> tuple[bool, str]:
    fresh_index = build_index()
    if not _INDEX_PATH.exists():
        return False, "index file missing — run --write"
    on_disk = _INDEX_PATH.read_text(encoding="utf-8")
    if on_disk != _serialize(fresh_index):
        return False, "index drifted from the manifests — run --write and commit"
    return True, f"fresh ({fresh_index['component_count']} processors)"


def _self_test() -> int:
    idx = build_index()
    ok = (idx["component_count"] >= 90
          and idx["by_id"]["processor/cache-exact"]["process_kind"] == "cache.exact_hash"
          and idx["by_id"]["processor/cache-exact"]["callable_path"].endswith("cache_exact.run")
          and all(v["callable_path"].startswith(_IN_REPO_PREFIXES) for v in idx["by_id"].values()))
    fresh, reason = check_fresh()
    print(f"  built {idx['component_count']} processors; committed index fresh: {fresh} ({reason})")
    print("PASS — build_processor_dispatch_index" if ok and fresh
          else f"FAIL — built_ok={ok} fresh={fresh} ({reason})")
    return 0 if ok and fresh else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the runtime processor dispatch index.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check-fresh", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.write:
        idx = write_index()
        print(json.dumps({"written": str(_INDEX_PATH.relative_to(_REPO)),
                          "component_count": idx["component_count"]}, indent=2))
        return 0
    if a.check_fresh:
        fresh, reason = check_fresh()
        print(json.dumps({"fresh": fresh, "reason": reason}, indent=2))
        return 0 if fresh else 1
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
