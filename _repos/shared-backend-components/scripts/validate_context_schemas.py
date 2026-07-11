#!/usr/bin/env python3
"""scripts.validate_context_schemas — validate context-layer fixtures against their JSON Schemas.

Extensible companion to validate_flywheel_schemas.py for the flat schemas/ context-layer schemas.
Currently covers the net-new `parser-run` (parse provenance). Add (fixture, schema) PAIRS as new
context schemas + fixtures land. Uses the same Draft202012Validator _repos/shared-backend-components/scripts/validate.py uses; the
self-test includes negative cases so enforcement is proven, not assumed.

CLI:
    python3 _repos/shared-backend-components/scripts/validate_context_schemas.py --self-test
    python3 _repos/shared-backend-components/scripts/validate_context_schemas.py            # validate + print results
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])

#: (fixture, schema it must satisfy). Extend as context-layer schemas + fixtures are added.
PAIRS: list[tuple[str, str]] = [
    ("fixtures/parser-run.example.json", "schemas/parser-run.schema.json"),
    ("fixtures/context-debt-item.example.json", "schemas/context-debt-item.schema.json"),
    ("fixtures/steward-review-request.example.json", "schemas/governance/steward-review-request.schema.json"),
    ("fixtures/steward-review-decision.example.json", "schemas/governance/steward-review-decision.schema.json"),
    ("fixtures/queue-message.example.json", "schemas/queue/queue-message.schema.json"),
    ("fixtures/worker-run.example.json", "schemas/queue/worker-run.schema.json"),
    ("fixtures/pipeline-object.example.json", "schemas/pipeline/pipeline-object.schema.json"),
    ("fixtures/graph-interrogation-run.example.json", "schemas/graph/graph-interrogation-run.schema.json"),
    ("fixtures/compression-run.example.json", "schemas/context/compression-run.schema.json"),
    ("fixtures/source-locator.example.json", "schemas/context/source-locator.schema.json"),
    ("fixtures/lineage-manifest.example.json", "schemas/context/lineage-manifest.schema.json"),
    ("fixtures/swarm-finding.example.json", "schemas/swarm/swarm-finding.schema.json"),
    ("fixtures/swarm-consensus.example.json", "schemas/swarm/swarm-consensus.schema.json"),
    ("fixtures/swarm-run.example.json", "schemas/swarm/swarm-run.schema.json"),
    ("fixtures/source-expansion-request.example.json", "schemas/context/source-expansion-request.schema.json"),
    ("fixtures/source-expansion-response.example.json", "schemas/context/source-expansion-response.schema.json"),
]


def _validator(schema_rel: str):
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.loads((_resource(schema_rel)).read_text(encoding="utf-8")))


def validate_all() -> list[str]:
    errors: list[str] = []
    for fixture_rel, schema_rel in PAIRS:
        v = _validator(schema_rel)
        doc = json.loads((_resource(fixture_rel)).read_text(encoding="utf-8"))
        errors.extend(f"{fixture_rel}: {e.message}" for e in v.iter_errors(doc))
    return errors


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    for fixture_rel, schema_rel in PAIRS:
        check(f"{Path(fixture_rel).name} exists", (_resource(fixture_rel)).exists())
        check(f"{Path(schema_rel).name} exists", (_resource(schema_rel)).exists())
    check("all context fixtures validate against their schemas", not validate_all(), "; ".join(validate_all()[:3]))

    # NEGATIVE: a parser-run with an out-of-enum status MUST fail (enforcement proof).
    v = _validator("schemas/parser-run.schema.json")
    bad = json.loads((_resource("fixtures/parser-run.example.json")).read_text(encoding="utf-8"))
    bad["status"] = "not-a-status"
    check("parser-run with bad status is rejected", bool(list(v.iter_errors(bad))))
    # NEGATIVE: missing required source_handle MUST fail.
    bad2 = json.loads((_resource("fixtures/parser-run.example.json")).read_text(encoding="utf-8"))
    bad2.pop("source_handle", None)
    check("parser-run without source_handle is rejected", bool(list(v.iter_errors(bad2))))

    print(f"\n{'all validate_context_schemas self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate context-layer fixtures against their JSON Schemas.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    errs = validate_all()
    if errs:
        print("\n".join(errs)); return 1
    print(f"OK — {len(PAIRS)} context fixtures valid against their schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
