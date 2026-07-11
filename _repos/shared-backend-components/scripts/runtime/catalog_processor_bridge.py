#!/usr/bin/env python3
"""scripts.runtime.catalog_processor_bridge — dispatch the 97 catalog processors at runtime.

The governed processor method-components under `_repos/shared-backend-components/scripts/processors/**` each resolve to a
`run(...)` callable named by a catalog manifest (`process_kind` + `implementations[].path`).
This bridge resolves `process_kind → component-id → callable` and invokes the real callable
by id or by process_kind. It is the lookup layer that lets the product use the components
that already exist; the companion `catalog_runtime_adapter` wraps these as runtime
`Processor`s for the consumption runtime.

The governed runtime is **stdlib-only** (proof C35), so this bridge reads the committed
`_repos/shared-backend-components/architecture/processor_dispatch_index.json` with stdlib `json` — it does NOT parse YAML.
That index is built from the manifests (the single source) by the out-of-scope builder
`_repos/shared-backend-components/scripts/build_processor_dispatch_index.py`; a flywheel drift gate keeps it in sync, so the
manifests remain authoritative without dragging a YAML dependency into the runtime.

Resolution:
  * by **component id** (`processor/cache-exact`) — always unambiguous.
  * by **process_kind** (`cache.exact_hash`) — when exactly one component owns it; an
    ambiguous kind (e.g. `retrieve.tree_walk`, owned by several walkers) raises with the
    candidate ids so the caller disambiguates by id.

This only DISPATCHES; it does not decide truth — a processor's output is whatever its
governed `run()` returns (most pin `serves_truth=False`); the verification gate promotes.

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/runtime/catalog_processor_bridge.py
    python3 _repos/shared-backend-components/scripts/runtime/catalog_processor_bridge.py --list
    python3 -m scripts.runtime.catalog_processor_bridge --self-test
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)
from scripts._repo_paths import resource as _resource

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
#: The committed, stdlib-json-readable dispatch index (built from the manifests by the
#: out-of-scope `_repos/shared-backend-components/scripts/build_processor_dispatch_index.py`; a flywheel drift gate keeps it
#: fresh). The runtime reads THIS, never the YAML manifests.
_INDEX_PATH = _resource("architecture") / "processor_dispatch_index.json"

#: Only in-repo callables are dispatchable; the index already filters to these.
_IN_REPO_PREFIXES = ("scripts.", "src.")


class ProcessorSpec:
    """One dispatchable processor, from the committed dispatch index."""

    __slots__ = ("component_id", "process_kind", "path", "deterministic",
                 "side_effects", "inputs", "outputs")

    def __init__(self, component_id: str, entry: dict[str, Any]) -> None:
        self.component_id = component_id
        self.process_kind = str(entry.get("process_kind", ""))
        self.path = str(entry["callable_path"])
        self.deterministic = bool(entry.get("deterministic", False))
        self.side_effects = entry.get("side_effects", "unknown")
        self.inputs = list(entry.get("inputs", []))
        self.outputs = list(entry.get("outputs", []))

    def load(self) -> Callable[..., dict[str, Any]]:
        """Import and return the `run` callable named by the index path."""
        module_name, attr = self.path.rsplit(".", 1)
        fn = getattr(importlib.import_module(module_name), attr)
        if not callable(fn):
            raise TypeError(f"{self.path} is not callable")
        return fn

    def to_dict(self) -> dict[str, Any]:
        return {"component_id": self.component_id, "process_kind": self.process_kind,
                "path": self.path, "deterministic": self.deterministic,
                "side_effects": self.side_effects, "inputs": self.inputs, "outputs": self.outputs}


@lru_cache(maxsize=1)
def _discover() -> tuple[dict[str, ProcessorSpec], dict[str, list[str]]]:
    """Load the committed dispatch index → ({component_id: spec}, {process_kind: [ids]})."""
    if not _INDEX_PATH.exists():
        raise FileNotFoundError(
            f"{_INDEX_PATH.relative_to(_REPO)} is missing — run "
            f"`python3 scripts/build_processor_dispatch_index.py --write`")
    index = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    by_id: dict[str, ProcessorSpec] = {}
    by_kind: dict[str, list[str]] = {}
    for component_id, entry in index.get("by_id", {}).items():
        spec = ProcessorSpec(component_id, entry)
        by_id[component_id] = spec
        if spec.process_kind:
            by_kind.setdefault(spec.process_kind, []).append(component_id)
    return by_id, {k: sorted(v) for k, v in by_kind.items()}


def all_specs() -> list[ProcessorSpec]:
    by_id, _ = _discover()
    return [by_id[k] for k in sorted(by_id)]


def resolve(id_or_kind: str) -> ProcessorSpec:
    """Resolve a component id or a (unique) process_kind to its spec.

    Raises KeyError on an unknown name, ValueError on an ambiguous process_kind
    (listing candidate ids so the caller can pick one by id)."""
    by_id, by_kind = _discover()
    if id_or_kind in by_id:
        return by_id[id_or_kind]
    if id_or_kind in by_kind:
        ids = by_kind[id_or_kind]
        if len(ids) == 1:
            return by_id[ids[0]]
        raise ValueError(
            f"process_kind {id_or_kind!r} is owned by {len(ids)} components {ids} — "
            f"disambiguate by component id")
    raise KeyError(f"no processor for {id_or_kind!r} (try a component id like 'processor/cache-exact' "
                   f"or a unique process_kind)")


def invoke(id_or_kind: str, /, **inputs: Any) -> dict[str, Any]:
    """Resolve, import, and call the processor's `run(**inputs)` — the dispatch primitive."""
    return resolve(id_or_kind).load()(**inputs)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    specs = all_specs()
    check("discovers the processor fleet (>= 90)", len(specs) >= 90, str(len(specs)))
    check("every spec has an in-repo callable path",
          all(s.path.startswith(_IN_REPO_PREFIXES) for s in specs))

    spec = resolve("processor/cache-exact")
    check("resolve by id", spec.process_kind == "cache.exact_hash")
    out = invoke("processor/cache-exact", key={"task": "t", "components": [], "inputs": {"x": 1}})
    check("invoke by id returns the run() envelope", "hit" in out and out["hit"]["hit"] is False, str(out)[:80])

    bm25 = invoke("retrieve.lexical_bm25", query="provisional credit",
                  corpus=[{"id": "d1", "text": "provisional credit rule"}], top_k=3)
    check("invoke by unique process_kind", bm25["candidates"] and bm25["candidates"][0]["id"] == "d1")

    raised = False
    try:
        resolve("retrieve.tree_walk")  # owned by several walkers
    except ValueError as e:
        raised = "disambiguate" in str(e)
    check("ambiguous process_kind raises with candidates", raised)

    raised = False
    try:
        resolve("processor/does-not-exist")
    except KeyError:
        raised = True
    check("unknown name raises KeyError", raised)

    # The load-bearing assertion: the runtime can dispatch ALL of them (every callable imports).
    bad = []
    for s in specs:
        try:
            assert callable(s.load())
        except Exception as e:  # noqa: BLE001
            bad.append(f"{s.component_id}: {type(e).__name__}")
    check("ALL discovered processors import + are callable", not bad, str(bad[:5]))

    check("specs carry deterministic + side_effects metadata",
          all(isinstance(s.deterministic, bool) and s.side_effects is not None for s in specs))

    ok = not fails
    print("\n" + (f"PASS — catalog_processor_bridge: bridged {len(specs)} catalog processors "
                  "(single-sourced from manifests); resolve/invoke by id or unique process_kind, "
                  "ambiguous-kind raises with candidates, ALL callables import."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Catalog→runtime processor dispatch bridge.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--list", action="store_true", help="print the discovered process_kind → id map")
    a = p.parse_args(argv)
    if a.list:
        _, by_kind = _discover()
        for kind in sorted(by_kind):
            print(f"{kind:<34} {by_kind[kind]}")
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
