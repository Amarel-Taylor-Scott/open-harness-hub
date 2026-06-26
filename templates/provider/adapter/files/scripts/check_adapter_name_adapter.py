#!/usr/bin/env python3
"""scripts.check_{{adapter_name}}_adapter — proof of standard.provider_adapter for {{title}}.

GENERATED STUB (standard.proof_script). Asserts the adapter satisfies the structural {{port_name}}
(isinstance against the runtime_checkable Protocol), carries no key literal, and resolves secrets only by ref.
Deterministic + offline + --self-test + PASS/FAIL + exit 0/1.

TODO(stub): once {{adapter_name}}Adapter implements {{port_name}}, assert the isinstance + a swappable test adapter.

CLI: python3 scripts/check_{{adapter_name}}_adapter.py --self-test
"""
from __future__ import annotations

import argparse


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # TODO(stub): from scripts.runtime.ports import {{port_name}}; assert isinstance({{adapter_name}}Adapter(...), {{port_name}}).
    check("TODO: implement {{adapter_name}} adapter proof (standard.provider_adapter)", False,
          "generated stub — implement {{port_name}} then assert the adapter satisfies the structural port + no key literal")

    print(f"{'PASS' if not fails else 'FAIL'} check_{{adapter_name}}_adapter ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: {{adapter_name}} provider adapter.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
