#!/usr/bin/env python3
"""scripts.check_{{handler_name}}_handler — proof of standard.durable_command for {{title}}.

GENERATED STUB (standard.proof_script). Asserts: idempotency_key is content-addressed (no wall-clock,
stable across runs), a wrong command_type dead-letters (PermanentJobError), and a duplicate is skipped.
Deterministic + offline + --self-test + PASS/FAIL + exit 0/1.

TODO(stub): once {{handler_name}}.handle implements the effect, assert the real result + durable event.

CLI: python3 scripts/check_{{handler_name}}_handler.py --self-test
"""
from __future__ import annotations

import argparse


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # TODO(stub): import scripts.handlers.{{handler_name}} and assert determinism + DLQ + idempotency.
    check("TODO: implement {{handler_name}} handler proof (standard.durable_command)", False,
          "generated stub — implement {{handler_name}}.handle then assert idempotency + permanent/retryable split")

    print(f"{'PASS' if not fails else 'FAIL'} check_{{handler_name}}_handler ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: {{handler_name}} durable command handler.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
