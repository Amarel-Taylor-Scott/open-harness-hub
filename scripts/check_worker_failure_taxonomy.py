#!/usr/bin/env python3
"""scripts.check_worker_failure_taxonomy — proof (C-FLEET-2): the failure taxonomy is complete and
well-formed, the loader resolves entries (and falls back to `unknown` safely), retryable/opens_circuit
flags are coherent, and every failure declares which records it must produce.

CLI: PYTHONPATH=. python3 scripts/check_worker_failure_taxonomy.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.baltor.workers.failure_taxonomy import failure_policy, failure_types, is_retryable, opens_circuit

_A = Path(__file__).resolve().parents[1] / "architecture"
_MUST_INCLUDE = {"provider_unavailable", "browser_launch_failed", "navigation_timeout", "selector_not_found",
                 "auth_required", "captcha_or_bot_block", "rate_limited", "network_error", "content_changed",
                 "parse_failed", "schema_validation_failed", "tenant_policy_violation", "unsupported_domain",
                 "worker_crash", "lease_expired", "duplicate_idempotency_key", "output_contract_invalid",
                 "forbidden_output_attempted", "gpu_unavailable", "model_load_failed", "memory_limit_exceeded",
                 "unknown"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    d = json.loads((_A / "worker_failure_taxonomy.json").read_text())
    records_enum = set(d["records_enum"])
    types = failure_types()

    chk("all required failure types present", _MUST_INCLUDE <= types, str(_MUST_INCLUDE - types))
    chk("unknown is defined (safe default)", "unknown" in types)
    chk("unknown is NOT retryable (never loops forever)", is_retryable("unknown") is False)
    chk("unclassified falls back to unknown policy", failure_policy("totally_made_up")["failure_type"] == "unknown")

    for f in d["failures"]:
        ft = f["failure_type"]
        chk(f"{ft} declares retryable + opens_circuit + category + produces",
            all(k in f for k in ("retryable", "opens_circuit", "category", "produces")))
        chk(f"{ft} produces ⊆ records_enum", set(f["produces"]) <= records_enum, str(f["produces"]))
        # coherence: a failure that opens a circuit must be retryable (else fallback is pointless)
        if f["opens_circuit"]:
            chk(f"{ft} opens_circuit ⇒ retryable", f["retryable"] is True)
        # coherence: a failure that opens a circuit must emit a ProviderFailureRecord
        if f["opens_circuit"]:
            chk(f"{ft} opens_circuit ⇒ emits ProviderFailureRecord", "ProviderFailureRecord" in f["produces"])

    chk("loader opens_circuit matches data", opens_circuit("rate_limited") is True and opens_circuit("parse_failed") is False)

    print(f"\n{'PASS — check_worker_failure_taxonomy: 22 failure types complete + coherent; unknown is the safe non-retryable default; opens_circuit ⇒ retryable + ProviderFailureRecord.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
