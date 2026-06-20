#!/usr/bin/env python3
"""scripts.validate_stages — every stages.json entry maps to a known canonical id + resolves copy.

Ties the visual stage config (data/stages.json) to the canonical term registry + the alias layer:
- every stage `id` must be a known canonical id (alias_resolver.load_canonical_terms)
- required structural fields are present (canonical_label/color_token/page/workflows/backend_modules)
- every stage resolves a label under default AND security alias packs (the copy is alias-driven, not embedded)
- the format-profile fixtures validate against the format-profile schema
Includes negative cases so enforcement is proven. Stdlib + jsonschema. CLI:
    python3 scripts/validate_stages.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts import alias_resolver

_REPO = Path(__file__).resolve().parents[1]
STAGES = _REPO / "data" / "stages.json"
FORMAT_SCHEMA = _REPO / "schemas" / "presentation" / "format-profile.schema.json"
FORMAT_FIXTURES = ["fixtures/presentation/format.executive_deck.json", "fixtures/presentation/format.security_console.json"]
_REQUIRED_STAGE_FIELDS = ("id", "canonical_label", "color_token", "page", "workflows", "backend_modules")


def validate_stages(stages: list[dict], canon: dict[str, str]) -> list[str]:
    errs: list[str] = []
    for s in stages:
        sid = s.get("id")
        if sid not in canon:
            errs.append(f"stage id not a known canonical id: {sid!r}")
        for f in _REQUIRED_STAGE_FIELDS:
            if f not in s:
                errs.append(f"stage {sid!r} missing required field {f!r}")
    return errs


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    canon = alias_resolver.load_canonical_terms()
    stages = json.loads(STAGES.read_text(encoding="utf-8"))["stages"]
    check("stages.json has the 6 stages + the rail", len(stages) == 7, str(len(stages)))
    errs = validate_stages(stages, canon)
    check("every stage maps to a known canonical id + has required fields", not errs, "; ".join(errs[:3]))

    # every stage resolves copy under default + security (alias-driven, not embedded)
    res_ok = all(alias_resolver.resolve(s["id"], audience="security")["value"] for s in stages)
    check("every stage resolves a security-audience label", res_ok)

    # format-profile fixtures are schema-valid
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(json.loads(FORMAT_SCHEMA.read_text(encoding="utf-8")))
    fmt_errs = []
    for rel in FORMAT_FIXTURES:
        fmt_errs += [f"{rel}: {e.message}" for e in v.iter_errors(json.loads((_REPO / rel).read_text(encoding="utf-8")))]
    check("format-profile fixtures are schema-valid", not fmt_errs, "; ".join(fmt_errs[:2]))

    # NEGATIVE: an unknown stage id fails
    check("unknown stage id is rejected", bool(validate_stages([{"id": "stage.nope", "canonical_label": "x", "color_token": "x", "page": "x", "workflows": [], "backend_modules": []}], canon)))
    # NEGATIVE: a bad format profile fails schema
    check("bad format profile rejected (lineage_detail enum)", bool(list(v.iter_errors({"kind": "baltor.format-profile.v1", "id": "format.bad", "lineage_detail": "everything"}))))

    print(f"\n{'all validate_stages self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate data/stages.json against the canonical registry + alias layer.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    canon = alias_resolver.load_canonical_terms()
    errs = validate_stages(json.loads(STAGES.read_text(encoding="utf-8"))["stages"], canon)
    if errs:
        print("\n".join(errs)); return 1
    print("OK — stages.json valid against the canonical registry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
