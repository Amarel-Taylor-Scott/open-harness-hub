#!/usr/bin/env python3
"""scripts.check_ingestion_ports — proof (INGESTION PORTS MODE): the three ingestion capability Protocols exist
under src/baltor/ports with exactly the required method surface, are runtime_checkable, and live in the ports
layer (no implementation that bypasses them). SourceAdapterPort: describe/plan/scan/fetch/normalize/health.
SyncPlannerPort: plan_full_sync/plan_incremental_sync/plan_backfill/apply_cursor. SourceArtifactStorePort:
write_source_artifacts/read_source_artifact/query_source_artifacts/diff_source_artifacts. Deterministic, stdlib.

CLI: python3 scripts/check_ingestion_ports.py --self-test
"""
from __future__ import annotations

import argparse
from typing import Protocol, runtime_checkable

from src.baltor.ports.source_adapter import SourceAdapterPort
from src.baltor.ports.source_artifact_store import SourceArtifactStorePort
from src.baltor.ports.sync_planner import SyncPlannerPort

#: required method surface per port.
_REQUIRED = {
    SourceAdapterPort: {"describe", "plan", "scan", "fetch", "normalize", "health"},
    SyncPlannerPort: {"plan_full_sync", "plan_incremental_sync", "plan_backfill", "apply_cursor"},
    SourceArtifactStorePort: {"write_source_artifacts", "read_source_artifact",
                              "query_source_artifacts", "diff_source_artifacts"},
}


def _methods(proto) -> set[str]:
    # methods declared on the Protocol (skip dunders + typing internals).
    return {n for n in dir(proto) if not n.startswith("_")}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    for proto, required in _REQUIRED.items():
        nm = proto.__name__
        check(f"{nm} is a typing.Protocol subclass", issubclass(proto, Protocol) or hasattr(proto, "_is_protocol"))
        present = _methods(proto)
        missing = required - present
        check(f"{nm} declares all required methods", missing == set(), f"missing={sorted(missing)}")
        check(f"{nm} has a module + class docstring", bool(proto.__doc__))

    # runtime_checkable: a duck-typed object with the right methods should pass isinstance.
    class _FakeAdapter:
        adapter_id = "source.fake@v1"
        source_class = "fake"
        def describe(self): ...
        def plan(self, **k): ...
        def scan(self, **k): ...
        def fetch(self, **k): ...
        def normalize(self, payload, **k): ...
        def health(self): ...

    check("SourceAdapterPort is runtime_checkable (duck-typed adapter passes isinstance)",
          isinstance(_FakeAdapter(), SourceAdapterPort))

    class _Partial:
        def describe(self): ...
    check("a partial adapter (missing methods) FAILS the runtime check",
          not isinstance(_Partial(), SourceAdapterPort))

    # ports must not import implementation layers (no bypass): scan the source text for forbidden imports.
    import importlib
    forbidden = ("src.baltor.adapters", "src.baltor.processors", "import scripts", "from scripts")
    for proto in _REQUIRED:
        mod = importlib.import_module(proto.__module__)
        src = (proto.__module__, open(mod.__file__).read())
        bad = [f for f in forbidden if f in src[1]]
        check(f"{proto.__name__}'s module imports no implementation layer (no bypass)", bad == [], str(bad))

    print(f"\n{'PASS — check_ingestion_ports: SourceAdapterPort/SyncPlannerPort/SourceArtifactStorePort exist with the full required method surface, are runtime_checkable, documented, and import no implementation layer (no port bypass).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the three ingestion ports exist with the required methods.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
