#!/usr/bin/env python3
"""scripts.validate_flywheel_schemas — validate flywheel fixtures against their JSON Schemas.

Proves the flywheel/decision-context/decision-receipt schemas + fixtures agree, using the same
`Draft202012Validator` `scripts/validate.py` uses. Self-test also includes a NEGATIVE case (an
agent flywheel/decision missing a required field MUST fail) so the validator is shown to actually
enforce, not just pass. Stdlib + jsonschema (already a repo dep).

CLI:
    python3 scripts/validate_flywheel_schemas.py --self-test
    python3 scripts/validate_flywheel_schemas.py            # validate + print results
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

#: fixture → schema it must satisfy.
PAIRS: list[tuple[str, str]] = [
    ("fixtures/flywheel/context-rot-flywheel.example.json", "schemas/flywheel/flywheel-spec.schema.json"),
    ("fixtures/flywheel/agent-decision-context.example.json", "schemas/flywheel/decision-context.schema.json"),
    ("fixtures/flywheel/agent-decision-receipt.example.json", "schemas/flywheel/decision-receipt.schema.json"),
]


def _validator(schema_rel: str):
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.loads((_REPO / schema_rel).read_text(encoding="utf-8")))


def _errors_for(fixture_rel: str, schema_rel: str) -> list[str]:
    v = _validator(schema_rel)
    doc = json.loads((_REPO / fixture_rel).read_text(encoding="utf-8"))
    return [f"{fixture_rel}: {e.message}" for e in v.iter_errors(doc)]


def validate_all() -> list[str]:
    errors: list[str] = []
    for fixture_rel, schema_rel in PAIRS:
        errors.extend(_errors_for(fixture_rel, schema_rel))
    return errors


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    for fixture_rel, schema_rel in PAIRS:
        check(f"{Path(fixture_rel).name} exists", (_REPO / fixture_rel).exists())
        check(f"{Path(schema_rel).name} exists", (_REPO / schema_rel).exists())

    errs = validate_all()
    check("all flywheel fixtures validate against their schemas", not errs, "; ".join(errs[:3]))

    # NEGATIVE: a decision-context missing the required stop_conditions MUST fail (enforcement proof).
    v = _validator("schemas/flywheel/decision-context.schema.json")
    bad = json.loads((_REPO / "fixtures/flywheel/agent-decision-context.example.json").read_text(encoding="utf-8"))
    bad.pop("stop_conditions", None)
    check("decision-context WITHOUT stop_conditions is rejected (enforcement)", bool(list(v.iter_errors(bad))))
    # NEGATIVE: a flywheel-spec with no triggers MUST fail.
    vf = _validator("schemas/flywheel/flywheel-spec.schema.json")
    badf = json.loads((_REPO / "fixtures/flywheel/context-rot-flywheel.example.json").read_text(encoding="utf-8"))
    badf["triggers"] = []
    check("flywheel-spec with empty triggers is rejected (enforcement)", bool(list(vf.iter_errors(badf))))

    print(f"\n{'all validate_flywheel_schemas self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate flywheel fixtures against their JSON Schemas.")
    p.add_argument("--self-test", action="store_true", help="validate + negative-case enforcement checks")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    errs = validate_all()
    if errs:
        print("\n".join(errs))
        return 1
    print(f"OK — {len(PAIRS)} flywheel fixtures valid against their schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
