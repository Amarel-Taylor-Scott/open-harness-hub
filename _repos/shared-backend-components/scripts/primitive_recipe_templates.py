#!/usr/bin/env python3
"""scripts.primitive_recipe_templates — RECIPES: deterministic templates/formulas that string primitives
into common standardization actions (owner-directed 2026-07-07). The three-level compile chain:

    RECIPE (a formula with typed SLOTS + params)
        --instantiate(slot values, params)-->  PLAN (the planned-lane dialect, settings inline)
        --deterministic_build (real_buildout_ab_harness)-->  RUNNABLE CODE (verified primitives wired)

  * A RECIPE is data: a formula string with {slot} holes and {param} settings, a slot schema (which BINDING
    TABLE fills each hole), and a params schema (validated via the settings control plane's validator).
  * BINDING TABLES are versioned data: parser_by_field_type maps person_name -> standardize_person_name,
    us_address -> standardize_us_address, ... — filling a slot is a lookup, never generation.
  * Instantiation is DETERMINISTIC and validated: unknown slot values reject loudly; params clamp against
    their schema; the result carries a canonical fingerprint + full provenance (recipe, bindings, params).
  * Recipes COMPOSE: sequence two instances and the plans concatenate; a record recipe maps field->recipe
    per column of a record.

Shipped formulas: standardize_any_field (type-routed), clean_text_field, person_intake, company_intake,
address_intake, contact_method_intake, dummy_screen_then_standardize, dedupe_key_bundle, record_intake.
The LLM's entire optional contribution is 'recipe name + slot values + params' (~10 tokens); everything
downstream is lookup + template + the deterministic builder. candidate=true, serves_truth=false.

    python3 scripts/primitive_recipe_templates.py --self-test
    python3 scripts/primitive_recipe_templates.py --list
    python3 scripts/primitive_recipe_templates.py --instantiate standardize_any_field --args '{"field_type": "person_name"}'
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.primitive_settings_control_plane import validate_settings  # noqa: E402 — reuse, not copy

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"primitive_recipe_templates requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-recipe"
BINDINGS_VERSION = "recipe-bindings-v1"

# ── BINDING TABLES (versioned data: filling a slot is a LOOKUP) ───────────────────────────────────────────────
SLOT_BINDINGS: dict[str, dict[str, str]] = {
    "parser_by_field_type": {
        "person_name": "standardize_person_name", "party_name": "standardize_party_name",
        "company_name": "standardize_company_name", "us_address": "standardize_us_address",
        "generic_text": "trim_collapse_whitespace", "email": "email_dummy_signals",
        "phone": "phone_dummy_signals"},
    "dummy_detector_by_field_type": {
        "person_name": "name_dummy_signals", "party_name": "name_dummy_signals",
        "company_name": "company_dummy_signals", "email": "email_dummy_signals",
        "phone": "phone_dummy_signals", "us_address": "name_dummy_signals",
        "generic_text": "name_dummy_signals"},
    "match_key_by_field_type": {
        "person_name": "generate_match_keys", "party_name": "generate_match_keys",
        "company_name": "generate_match_keys", "us_address": "generate_match_keys",
        "generic_text": "generate_match_keys", "email": "generate_match_keys",
        "phone": "generate_match_keys"},
    "phonetic_by_locale": {"en": "soundex_key", "default": "soundex_key"},
}

# ── RECIPE TEMPLATES (formulas as data; {slot:table} holes + {param} settings) ───────────────────────────────
RECIPE_TEMPLATES: dict[str, dict[str, Any]] = {
    "clean_text_field": {
        "purpose": "generic string cleanup for any text column",
        "formula": "trim_collapse_whitespace -> unicode_normalize_nfc -> normalize_apostrophes",
        "slots": {}, "params": {}},
    "standardize_any_field": {
        "purpose": "type-routed standardization: clean -> parse -> match keys",
        "formula": ("trim_collapse_whitespace -> unicode_normalize_nfc -> {parser:parser_by_field_type} -> "
                    "{keys:match_key_by_field_type}"),
        "slots": {"parser": "field_type", "keys": "field_type"},
        "params": {}},
    "dummy_screen_then_standardize": {
        "purpose": "rate dummy likelihood first; standardize; suspects routed to review",
        "formula": ("{detector:dummy_detector_by_field_type} -> rate_dummy_likelihood -> "
                    "trim_collapse_whitespace -> {parser:parser_by_field_type}"),
        "slots": {"detector": "field_type", "parser": "field_type"}, "params": {}},
    "dedupe_key_bundle": {
        "purpose": "the full blocking/dedupe key family for one field",
        "formula": ("trim_collapse_whitespace -> tokenize_alnum -> token_sorted_key -> "
                    "{phonetic:phonetic_by_locale} -> blocking_key(parts={blocking_parts})"),
        "slots": {"phonetic": "locale"},
        "params": {"blocking_parts": {"type": "int", "default": 2, "min": 1, "max": 4, "unit": "tokens"}}},
    "person_intake": {
        "purpose": "person-name column intake: screen -> classify -> parse -> keys",
        "formula": ("name_dummy_signals -> rate_dummy_likelihood -> standardize_party_name -> "
                    "standardize_person_name -> generate_match_keys"),
        "slots": {}, "params": {}},
    "company_intake": {
        "purpose": "company column intake: screen -> classify -> parse -> keys",
        "formula": ("company_dummy_signals -> rate_dummy_likelihood -> standardize_party_name -> "
                    "standardize_company_name -> generate_match_keys"),
        "slots": {}, "params": {}},
    "address_intake": {
        "purpose": "US address column intake: clean -> parse -> block key",
        "formula": ("trim_collapse_whitespace -> standardize_us_address -> "
                    "blocking_key(parts={blocking_parts})"),
        "slots": {},
        "params": {"blocking_parts": {"type": "int", "default": 3, "min": 1, "max": 4, "unit": "tokens"}}},
    "contact_method_intake": {
        "purpose": "email/phone column intake: screen -> normalize -> keys",
        "formula": ("{detector:dummy_detector_by_field_type} -> rate_dummy_likelihood -> "
                    "trim_collapse_whitespace -> generate_match_keys"),
        "slots": {"detector": "field_type"}, "params": {}},
    "design_system_from_tokens": {
        "purpose": "UI: token plan -> full design system with WCAG gate",
        "formula": "build_design_system -> validate_design_accessibility",
        "slots": {}, "params": {}},
}
_SLOT_RE = re.compile(r"\{(\w+):(\w+)\}")
_PARAM_RE = re.compile(r"\{(\w+)\}")


# ── the engine ────────────────────────────────────────────────────────────────────────────────────────────────
def list_recipes() -> list[dict[str, str]]:
    return [{"recipe": name, "purpose": spec["purpose"], "formula": spec["formula"],
             "slots": {s: t for s, t in spec["slots"].items()},
             "params": sorted(spec["params"])} for name, spec in sorted(RECIPE_TEMPLATES.items())]


def instantiate_recipe(name: str, args: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """DETERMINISTIC FILL: recipe + slot values + params -> a concrete PLAN (the planned-lane dialect) with
    canonical fingerprint + full provenance. Unknown recipes/slot values reject loudly; params clamp via the
    settings control plane's validator."""
    args = args or {}
    spec = RECIPE_TEMPLATES.get(name)
    if spec is None:
        raise ValueError(f"unknown recipe {name!r}; have {sorted(RECIPE_TEMPLATES)}")
    formula = spec["formula"]
    bindings: dict[str, str] = {}
    for m in _SLOT_RE.finditer(formula):
        slot, table_name = m.group(1), m.group(2)
        table = SLOT_BINDINGS[table_name]
        arg_key = spec["slots"].get(slot, slot)
        value = str(args.get(arg_key, args.get(slot, "default")))
        impl = table.get(value) or table.get("default")
        if impl is None:
            raise ValueError(f"slot {slot!r}: no binding for {value!r} in table {table_name!r} "
                             f"(have {sorted(table)})")
        bindings[slot] = impl
        formula = formula.replace(m.group(0), impl)
    params = validate_settings({k: v for k, v in args.items() if k in spec["params"]}, spec["params"])
    for pname, pvalue in params.items():
        formula = formula.replace("{%s}" % pname, repr(pvalue) if isinstance(pvalue, str) else str(pvalue))
    unfilled = _PARAM_RE.findall(formula)
    if unfilled:
        raise ValueError(f"unfilled holes {unfilled} in recipe {name!r}")
    return {"recipe": name, "purpose": spec["purpose"], "plan": f"PLAN: {formula}",
            "bindings": bindings, "params": params, "args": args,
            "fingerprint": canonical_id(CARD_PREFIX, name, json.dumps([bindings, params], sort_keys=True)),
            "bindings_version": BINDINGS_VERSION, **BOUNDARY}


def compose_recipes(instances: list[dict[str, Any]]) -> dict[str, Any]:
    """Sequence recipe instances into one plan (formulas compose like the primitives they wire)."""
    steps = " -> ".join(inst["plan"].removeprefix("PLAN: ") for inst in instances)
    return {"recipe": "+".join(i["recipe"] for i in instances), "plan": f"PLAN: {steps}",
            "composed_from": [i["fingerprint"] for i in instances],
            "fingerprint": canonical_id(CARD_PREFIX, "composed", steps), **BOUNDARY}


def record_intake_recipe(field_types: dict[str, str]) -> dict[str, Any]:
    """RECORD-LEVEL formula: {column -> field_type} -> a per-column plan bundle (one lookup per column)."""
    plans = {col: instantiate_recipe("standardize_any_field", {"field_type": ftype})
             for col, ftype in sorted(field_types.items())}
    return {"recipe": "record_intake", "columns": {c: p["plan"] for c, p in plans.items()},
            "fingerprint": canonical_id(CARD_PREFIX, "record",
                                        json.dumps(sorted(field_types.items()))), **BOUNDARY}


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in (instantiate_recipe, compose_recipes, record_intake_recipe):
        src = inspect.getsource(fn)
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, src), "impl_name": fn.__name__,
                      "record_type": "recipe_engine_primitive", "kind": "primitive", "title": title,
                      "executable_body": src, "language": "python",
                      "input_edge": "RecipeInvocation", "output_edge": "InstantiatedPlan",
                      "blackbox": f"Recipe-engine primitive: {title} Input: recipe name + slot values + "
                                  f"params. Output: a concrete plan for the deterministic builder.",
                      "tier": "common", **BOUNDARY})
    for name, spec in sorted(RECIPE_TEMPLATES.items()):
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, "recipe", name, spec["formula"]),
                      "impl_name": f"recipe__{name}", "record_type": "standardization_recipe",
                      "kind": "primitive_group", "title": f"Recipe: {name} — {spec['purpose']}"[:160],
                      "executable_body": f"# recipe formula (instantiate via primitive_recipe_templates)\n"
                                         f"# {spec['formula']}\n",
                      "language": "recipe_dialect", "plan_steps": re.findall(r"[a-z_]+", spec["formula"]),
                      "input_edge": "RawDataInput", "output_edge": "StandardizedFieldBundle",
                      "blackbox": f"Standardization recipe '{name}': {spec['purpose']}. Formula: "
                                  f"{spec['formula']}. Slots fill by lookup; params clamp by schema.",
                      "tier": "common", **BOUNDARY})
    return cards


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    inst = instantiate_recipe("standardize_any_field", {"field_type": "person_name"})
    checks.append(("SLOT FILL is a lookup: person_name routes to standardize_person_name + match keys",
                   inst["bindings"] == {"parser": "standardize_person_name", "keys": "generate_match_keys"}
                   and "standardize_person_name" in inst["plan"]))
    inst2 = instantiate_recipe("standardize_any_field", {"field_type": "us_address"})
    checks.append(("same recipe, different slot value -> different parser (the formula is reusable)",
                   "standardize_us_address" in inst2["plan"] and inst["fingerprint"] != inst2["fingerprint"]))
    try:
        instantiate_recipe("standardize_any_field", {"field_type": "martian_glyphs"})
        checks.append(("unknown slot value REJECTS loudly", False))
    except ValueError:
        checks.append(("unknown slot value REJECTS loudly", True))
    dk = instantiate_recipe("dedupe_key_bundle", {"locale": "en", "blocking_parts": 9})
    checks.append(("params clamp via the settings control plane (9 -> 4) and land INLINE in the plan",
                   "blocking_key(parts=4)" in dk["plan"] and dk["params"] == {"blocking_parts": 4}))
    checks.append(("instantiation is deterministic (identical args -> identical fingerprint + plan)",
                   json.dumps(instantiate_recipe("person_intake"), sort_keys=True)
                   == json.dumps(instantiate_recipe("person_intake"), sort_keys=True)))
    comp = compose_recipes([instantiate_recipe("clean_text_field"), inst])
    checks.append(("recipes COMPOSE: sequenced formulas concatenate into one plan",
                   comp["plan"].count("->") >= 5 and comp["recipe"] == "clean_text_field+standardize_any_field"))
    rec = record_intake_recipe({"full_name": "person_name", "company": "company_name",
                                "shipping_address": "us_address"})
    checks.append(("RECORD formula: column->field_type map yields a per-column plan bundle",
                   set(rec["columns"]) == {"full_name", "company", "shipping_address"}
                   and "standardize_company_name" in rec["columns"]["company"]))
    # END-TO-END: recipe -> plan -> the harness's DETERMINISTIC BUILDER -> sandboxed run PASSES
    from scripts.real_buildout_ab_harness import (  # noqa: PLC0415
        deterministic_build, execute_lane, extract_files, load_exec_cards, parse_arrow_plan)
    import tempfile  # noqa: PLC0415
    clean = instantiate_recipe("clean_text_field")
    steps = parse_arrow_plan(clean["plan"])
    exec_by_name = {str(c.get("impl_name")): c for c in load_exec_cards() if c.get("impl_name")}
    built = deterministic_build(steps, exec_by_name)
    tests = extract_files('```python filename=tests/test_main.py\nfrom main import run\n\n'
                          'def test_run():\n    assert run("  Acme\\u2019s   Widgets ") == "Acme\'s Widgets"\n```\n')
    with tempfile.TemporaryDirectory() as td:
        v = execute_lane({**built, **tests}, Path(td) / "e2e")
        checks.append(("END-TO-END: recipe -> plan -> deterministic build -> sandbox PASS on real pack "
                       "primitives (0 LLM tokens)", v["compile_ok"] and v["self_tests_passed"]))
    cards = all_cards()
    checks.append(("cards: engine primitives + every recipe as a primitive_group with steps; boundary",
                   len(cards) == 3 + len(RECIPE_TEMPLATES)
                   and all(c.get("serves_truth") is False for c in cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_recipe_templates: {len(RECIPE_TEMPLATES)} formulas x slot-lookup fill x "
          f"clamped params -> plans -> deterministic build -> verified runs. Recipes compose; records map "
          f"per-column. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--instantiate", metavar="RECIPE", default=None)
    ap.add_argument("--args", default="{}")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.list:
        for r in list_recipes():
            print(f"  {r['recipe']:32s} {r['purpose']}")
        return 0
    if args.instantiate:
        print(json.dumps(instantiate_recipe(args.instantiate, json.loads(args.args)),
                         indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
