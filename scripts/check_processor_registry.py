#!/usr/bin/env python3
"""scripts.check_processor_registry — proof: processors load only via the registry by processor_id@version,
an unknown ref is a permanent unavailable_processor error, and the runtime runner/harness imports NO
domain (CFPB) implementation directly.

CLI: python3 scripts/check_processor_registry.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.runtime.processor_registry import UnavailableProcessor, default_registry

_REPO = Path(__file__).resolve().parents[1]
#: runtime CORE must stay domain-agnostic — these files must not import CFPB/decompose modules.
_RUNTIME_CORE = ("processor_harness.py", "processor_registry.py", "processor.py", "context.py", "envelopes.py")
_DOMAIN_IMPORTS = ("decompose_structured", "demo_cfpb", "cfpb_artifacts", "integrate_cfpb")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = default_registry()
    for ref in ("source.cfpb_fixture@v1", "decompose.cfpb_structured@v1", "package.context_pack@v1",
                "vectorize.deterministic_local@v1", "graph.deterministic_edges@v1"):
        check(f"registry loads {ref}", reg.has(ref) and reg.resolve(ref).spec.ref == ref)

    check("get(id, version) resolves the same processor",
          reg.get("decompose.cfpb_structured", "v1").processor_id == "decompose.cfpb_structured")

    raised = False
    try:
        reg.resolve("does.not_exist@v9")
    except UnavailableProcessor:
        raised = True
    check("an unknown processor ref raises UnavailableProcessor (permanent)", raised)

    # runtime CORE files must not import a domain implementation directly (only builtin_processors adapts them)
    offenders = []
    for fn in _RUNTIME_CORE:
        text = (_REPO / "scripts" / "runtime" / fn).read_text(encoding="utf-8")
        if any(d in text for d in _DOMAIN_IMPORTS):
            offenders.append(fn)
    check("runtime core imports NO CFPB/domain implementation directly", offenders == [], str(offenders))

    print(f"\n{'PASS — check_processor_registry: processors load only via the registry; unknown refs are permanent errors; runtime core is domain-agnostic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: processor registry + domain-agnostic runtime core.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
