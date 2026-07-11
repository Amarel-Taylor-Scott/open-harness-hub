#!/usr/bin/env python3
"""scripts.validate_tool_evidence_cards — validate ToolEvidenceCards + cross-check the catalog.

Each card in data/tool-evidence-cards/ must (1) validate against
schemas/backend/tool-evidence-card.schema.json and (2) name a `capability` that is a real
capability key in data/backend-tools.yaml (so cards can't drift from the verified catalog).
Self-test includes negative cases. Stdlib + jsonschema + PyYAML. CLI:
    python3 _repos/shared-backend-components/scripts/validate_tool_evidence_cards.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
CARDS_DIR = _resource("data") / "tool-evidence-cards"
CARD_SCHEMA = _resource("schemas") / "backend" / "tool-evidence-card.schema.json"
BACKEND_TOOLS = _resource("data") / "backend-tools.yaml"


def _capability_keys() -> set[str]:
    import yaml
    d = yaml.safe_load(BACKEND_TOOLS.read_text(encoding="utf-8"))
    return {c["key"] for c in d.get("capabilities", [])}


def _validator():
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.loads(CARD_SCHEMA.read_text(encoding="utf-8")))


def validate_card(card: dict, *, validator, keys: set[str], where: str) -> list[str]:
    errs = [f"{where}: {e.message}" for e in validator.iter_errors(card)]
    cap = card.get("capability")
    if cap and cap not in keys:
        errs.append(f"{where}: capability {cap!r} is not a known data/backend-tools.yaml capability key")
    return errs


def validate_all() -> tuple[list[str], int]:
    v, keys = _validator(), _capability_keys()
    errors: list[str] = []
    count = 0
    for path in sorted(CARDS_DIR.glob("*.json")):
        count += 1
        errors.extend(validate_card(json.loads(path.read_text(encoding="utf-8")), validator=v, keys=keys, where=path.name))
    return errors, count


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    errs, count = validate_all()
    check(f"all {count} tool-evidence cards valid + capability known", not errs, "; ".join(errs[:3]))
    check("found >= 5 cards", count >= 5, str(count))

    # an 'avoid' card exists for a flagged tool (Kuzu)
    kuzu = json.loads((CARDS_DIR / "kuzu.json").read_text(encoding="utf-8"))
    check("Kuzu card decision=avoid with reason", kuzu["decision"] == "avoid" and "archived" in " ".join(kuzu.get("weaknesses", [])).lower())

    v, keys = _validator(), _capability_keys()
    # NEGATIVE: unknown capability is rejected
    bad = json.loads((CARDS_DIR / "docling.json").read_text(encoding="utf-8")); bad["capability"] = "not_a_capability"
    check("unknown capability rejected", bool(validate_card(bad, validator=v, keys=keys, where="neg")))
    # NEGATIVE: missing decision (required) is rejected
    bad2 = json.loads((CARDS_DIR / "docling.json").read_text(encoding="utf-8")); bad2.pop("decision")
    check("missing decision rejected", bool(validate_card(bad2, validator=v, keys=keys, where="neg2")))

    print(f"\n{'all validate_tool_evidence_cards self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate ToolEvidenceCards against schema + the verified backend-tools catalog.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    errs, count = validate_all()
    if errs:
        print("\n".join(errs)); return 1
    print(f"OK — {count} tool-evidence cards valid against schema + catalog.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
