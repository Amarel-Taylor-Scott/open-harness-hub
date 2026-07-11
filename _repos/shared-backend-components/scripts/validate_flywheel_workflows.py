#!/usr/bin/env python3
"""scripts.validate_flywheel_workflows — validate flywheel workflow YAMLs + enforce the L5 rule.

Loads every `workflows/flywheel-*.workflow.yaml`, validates it against
`schemas/workflow/flywheel-workflow.schema.json` (Draft202012Validator), and enforces the
architecture invariant: **an AI-agent (L5) flywheel MUST carry a `decision_context`** (no agent
runs from unbounded context). Self-test includes negative cases so enforcement is proven.

Stdlib + PyYAML + jsonschema (repo deps). CLI:
    python3 _repos/shared-backend-components/scripts/validate_flywheel_workflows.py --self-test
    python3 _repos/shared-backend-components/scripts/validate_flywheel_workflows.py            # validate + print results
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
WORKFLOW_DIR = _resource("workflows")
WORKFLOW_SCHEMA = _resource("schemas") / "workflow" / "flywheel-workflow.schema.json"


def _validator():
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.loads(WORKFLOW_SCHEMA.read_text(encoding="utf-8")))


def _is_agent_flywheel(doc: dict) -> bool:
    fid = str(doc.get("flywheel_id", ""))
    name = str(doc.get("name", "")).lower()
    return fid.endswith("agent-decision") or "agent decision" in name


def _errors_for(doc: dict, where: str) -> list[str]:
    import yaml  # noqa: F401 (ensures dep present)
    errs = [f"{where}: {e.message}" for e in _validator().iter_errors(doc)]
    # L5 rule: an agent-decision flywheel MUST declare a decision_context.
    if _is_agent_flywheel(doc) and not isinstance(doc.get("decision_context"), dict):
        errs.append(f"{where}: agent-decision flywheel missing required 'decision_context' (L5 rule)")
    return errs


def validate_all() -> tuple[list[str], int]:
    import yaml
    errors: list[str] = []
    count = 0
    for path in sorted(WORKFLOW_DIR.glob("flywheel-*.workflow.yaml")):
        count += 1
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors.extend(_errors_for(doc, path.name))
    return errors, count


def _self_test() -> int:
    import yaml
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    check("workflow schema exists", WORKFLOW_SCHEMA.exists())
    errs, count = validate_all()
    check(f"all {count} flywheel workflows valid (+ L5 rule)", not errs, "; ".join(errs[:3]))
    check("found >= 4 flywheel workflows", count >= 4, str(count))

    # the agent-decision workflow actually carries a decision_context
    agent = yaml.safe_load((WORKFLOW_DIR / "flywheel-agent-decision.workflow.yaml").read_text(encoding="utf-8"))
    check("agent-decision workflow declares decision_context", isinstance(agent.get("decision_context"), dict))

    # NEGATIVE 1: a workflow missing required 'steps' is rejected.
    bad = dict(agent); bad.pop("steps", None)
    check("workflow without steps is rejected", bool(_errors_for(bad, "neg1")))
    # NEGATIVE 2: an agent flywheel WITHOUT decision_context is rejected by the L5 rule.
    bad2 = dict(agent); bad2.pop("decision_context", None)
    check("agent flywheel without decision_context is rejected (L5 rule)", bool(_errors_for(bad2, "neg2")))

    print(f"\n{'all validate_flywheel_workflows self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate flywheel workflow YAMLs + enforce the L5 decision-context rule.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    errs, count = validate_all()
    if errs:
        print("\n".join(errs))
        return 1
    print(f"OK — {count} flywheel workflows valid against the schema (+ L5 rule).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
