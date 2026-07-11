#!/usr/bin/env python3
"""scripts.check_runtime_schema_validation — proof: valid envelopes pass; a missing required field, a wrong
type, an unknown enum, and an additional property all FAIL; and a failure is expressible as an ErrorEnvelope.

CLI: python3 _repos/shared-backend-components/scripts/check_runtime_schema_validation.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.envelopes import CommandEnvelope, ErrorEnvelope
from scripts.runtime.schema_validator import is_valid, validate_ref


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    good = CommandEnvelope(command_type="pipeline.run_step", tenant_id="acme", run_id="r", queue="q").to_dict()
    check("a valid CommandEnvelope passes its schema", is_valid(good, "envelopes/CommandEnvelope"), str(validate_ref(good, "envelopes/CommandEnvelope")))

    missing = dict(good); missing.pop("run_id")
    check("a missing required field FAILS", not is_valid(missing, "envelopes/CommandEnvelope"))

    wrong_type = dict(good); wrong_type["payload"] = "not-an-object"
    check("a wrong type FAILS", not is_valid(wrong_type, "envelopes/CommandEnvelope"))

    bad_enum = dict(good); bad_enum["priority"] = "URGENT"
    check("an unknown enum value FAILS", not is_valid(bad_enum, "envelopes/CommandEnvelope"))

    extra = dict(good); extra["surprise"] = 1
    check("an additional property FAILS (additionalProperties:false)", not is_valid(extra, "envelopes/CommandEnvelope"))

    # artifact payload schemas
    fact = {"text": "t", "field": "company", "claim_status": "fact", "promotion_eligible": True}
    check("a valid AtomicFact payload passes", is_valid(fact, "artifacts/AtomicFact"))
    check("an AtomicFact with claim_status='unverified_allegation' FAILS the fact enum",
          not is_valid({**fact, "claim_status": "unverified_allegation"}, "artifacts/AtomicFact"))
    from scripts.runtime.schema_validator import validate as _v
    check("the validator treats a boolean as NOT an integer",
          _v(True, {"type": "integer"}) != [] and _v(3, {"type": "integer"}) == [])
    check("EventEnvelope requires specversion=1.0", not is_valid({"specversion": "0.3"}, "envelopes/EventEnvelope"))

    # a validation failure becomes an ErrorEnvelope
    errs = validate_ref(missing, "envelopes/CommandEnvelope")
    e = ErrorEnvelope("schema_validation_failed", retryable=False, message=str(errs[:2]), failed_schema="CommandEnvelope")
    check("a validation failure is expressible as a permanent ErrorEnvelope",
          e.error_type == "schema_validation_failed" and e.retryable is False and is_valid(e.to_dict(), "envelopes/ErrorEnvelope"))

    print(f"\n{'PASS — check_runtime_schema_validation: the schema gate accepts valid envelopes and rejects missing/wrong-type/unknown-enum/additional-property payloads; failures become ErrorEnvelopes.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: schema validation gate.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
