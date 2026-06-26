#!/usr/bin/env python3
"""scripts.check_{{area}}_api — proof of standard.api_projection for {{title}}.

GENERATED STUB (standard.proof_script). Drives the handler DIRECTLY (no socket): asserts the route is
owned, the response matches {{returns_contract}}, an unknown path -> 404, and NO secret marker is emitted.
Deterministic + offline + --self-test + PASS/FAIL + exit 0/1.

TODO(stub): once api_{{area}}_handler.serve calls the real engine, assert the {{returns_contract}} shape.

CLI: python3 scripts/check_{{area}}_api.py --self-test
"""
from __future__ import annotations

import argparse


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # TODO(stub): from scripts.api_{{area}}_handler import handle, ROUTES; assert handle drives the engine.
    check("TODO: implement {{area}} API proof (standard.api_projection)", False,
          "generated stub — wire api_{{area}}_handler.serve then assert {{returns_contract}} + no secret marker + 404 on unknown path")

    print(f"{'PASS' if not fails else 'FAIL'} check_{{area}}_api ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: {{area}} projection API route.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
