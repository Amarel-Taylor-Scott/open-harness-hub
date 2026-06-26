#!/usr/bin/env python3
"""scripts.check_{{source_family}}_adapter — proof of standard.source_adapter for {{title}}.

GENERATED STUB (standard.proof_script). Asserts: the adapter declares source_type/parser_provider, ingest
is content-addressed (same payload -> same ids), narrative vs structured split, and the NON-CONSUMABLE
boundary. Deterministic + offline + --self-test + PASS/FAIL + exit 0/1.

TODO(stub): once {{source_family}}Adapter.ingest is implemented, replace the failing-TODO assertion below.

CLI: python3 scripts/check_{{source_family}}_adapter.py --self-test
"""
from __future__ import annotations

import argparse


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # TODO(stub): import scripts.ingest.{{source_family}} and assert the real adapter contract.
    check("TODO: implement {{source_family}} adapter proof (standard.source_adapter)", False,
          "generated stub — implement {{source_family}}Adapter.ingest then assert determinism + held-out + non-consumable")

    print(f"{'PASS' if not fails else 'FAIL'} check_{{source_family}}_adapter ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: {{source_family}} source adapter (standard.source_adapter).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
