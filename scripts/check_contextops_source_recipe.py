#!/usr/bin/env python3
"""scripts.check_contextops_source_recipe — proof (CONTEXTOPS SOURCE-RECIPE MODE): the M2 rung builder emits a
SourceRecipe.v1 that carries — REQUIRED — the source's authority + the access method (with retry + rate-limit)
+ selectors/parser hints + a cross-source policy + watch triggers + the parser provider + the expected output
schema + a reliability score back-link, and that the cross-source policy + watch triggers are DERIVED
deterministically from the source's authority/type + whether the fact is a current/moving value.

Concretely:
  - a recipe built for an OFFICIAL regulation gets a single_official_source_ok policy when the fact is settled,
    but a current/moving value (deadline/rate/fee/…) gets current_value_requires_fresh_source + a scheduled +
    high_value_periodic watch (a moving fact must be re-read fresh);
  - a recipe built for a lower-authority restatement (FAQ/secondary) NEVER stands alone — it gets
    two_independent_sources_required (a FAQ can never be a single trusted source);
  - a tenant_private source gets tenant_private_requires_human_signoff;
  - the recipe's expected_output_schema is pinned to fact_assertion_candidate (a recipe reads into a
    CANDIDATE, never a served/canonical fact); the access locator carries no secret;
  - determinism: same inputs + same now -> byte-identical recipe (the id is content-addressed).

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 scripts/check_contextops_source_recipe.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402
from src.baltor.contextops.source_recipe import (  # noqa: E402
    EXPECTED_OUTPUT_SCHEMA,
    build_source_recipe,
    cross_source_policy,
)

_SCHEMA = _REPO / "schemas" / "contextops" / "SourceRecipe.v1.schema.json"
_NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schema = json.loads(_SCHEMA.read_text())

    # ── a recipe for a current/moving regulation value (the CFPB deadline). ──
    reg_recipe = build_source_recipe(
        tenant_id="acme", source_scope="global_public",
        fact_key="reg_e.error_resolution.deadline",
        question="What is the official Regulation E deadline for resolving an alleged error?",
        source_handle="ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i",
        source_type="regulation", authority_rank=90, officialness="official",
        locator="fixtures/cfpb/ecfr-1005-11.html", reliability_score_id="srs-ecfr-1005-11",
        derived_from_report_id="sdr-cfpb-deadline", now=_NOW)
    check("regulation recipe validates against SourceRecipe.v1", _validate(reg_recipe, schema) == [], str(_validate(reg_recipe, schema)[:4]))

    # ── REQUIRED blocks present + correctly populated. ──
    check("recipe carries the source authority block (authority_rank + source_type + officialness)",
          {"authority_rank", "source_type", "officialness"} <= set(reg_recipe["authority"])
          and reg_recipe["authority"]["authority_rank"] == 90)
    check("recipe carries an access method + locator + retry policy + rate limit",
          {"method", "locator", "retry_policy", "rate_limit_per_min"} <= set(reg_recipe["access"]))
    check("recipe access locator carries NO secret (auth is a vault ref if any)",
          "auth_ref" not in reg_recipe["access"] or reg_recipe["access"]["auth_ref"].startswith(("env://", "vault://")))
    check("recipe names the parser provider (it pairs the source with an extractor)",
          bool(reg_recipe.get("parser_provider")))
    check("recipe expected_output_schema is pinned to fact_assertion_candidate (reads into a CANDIDATE, never a fact)",
          reg_recipe["expected_output_schema"] == EXPECTED_OUTPUT_SCHEMA)
    check("recipe carries a reliability score back-link", bool(reg_recipe.get("reliability_score_id")))
    check("recipe carries >=1 watch trigger (when it must re-run)", len(reg_recipe["watch_triggers"]) >= 1)

    # ── the cross-source + watch policy is DERIVED from authority + current-value-ness. ──
    check("a CURRENT/moving regulation value gets current_value_requires_fresh_source (must be re-read fresh)",
          reg_recipe["cross_source"]["policy"] == "current_value_requires_fresh_source")
    check("a current/moving value's watch triggers include scheduled + high_value_periodic + source_change",
          {"scheduled", "high_value_periodic", "source_change"} <= set(reg_recipe["watch_triggers"]))

    # ── a SETTLED regulation value gets single_official_source_ok (an official source-of-record stands alone). ──
    settled_policy, settled_min = cross_source_policy(
        source_type="regulation", source_scope="global_public", is_current_value=False)
    check("a SETTLED official regulation value gets single_official_source_ok (1 source)",
          settled_policy == "single_official_source_ok" and settled_min == 1)

    # ── a lower-authority restatement (FAQ) can NEVER stand alone — two independent sources required. ──
    faq_recipe = build_source_recipe(
        tenant_id="acme", source_scope="global_public",
        fact_key="reg_e.error_resolution.deadline", question="deadline?",
        source_handle="ctx://public/source/cfpb-faq/error-resolution#q12",
        source_type="agency_faq", authority_rank=20, officialness="semi_official",
        locator="fixtures/cfpb/faq.html", now=_NOW)
    check("FAQ recipe validates against SourceRecipe.v1", _validate(faq_recipe, schema) == [])
    check("a FAQ/restatement source NEVER stands alone — two_independent_sources_required (red-team: FAQ cannot be a single trusted source)",
          faq_recipe["cross_source"]["policy"] == "two_independent_sources_required"
          and faq_recipe["cross_source"]["min_independent_sources"] >= 2)

    # ── a tenant_private source requires human signoff. ──
    priv_policy, _ = cross_source_policy(
        source_type="tenant_document", source_scope="tenant_private", is_current_value=False)
    check("a tenant_private source gets tenant_private_requires_human_signoff",
          priv_policy == "tenant_private_requires_human_signoff")

    # ── determinism: same inputs + same now -> byte-identical recipe (id content-addressed). ──
    reg_recipe2 = build_source_recipe(
        tenant_id="acme", source_scope="global_public",
        fact_key="reg_e.error_resolution.deadline",
        question="What is the official Regulation E deadline for resolving an alleged error?",
        source_handle="ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i",
        source_type="regulation", authority_rank=90, officialness="official",
        locator="fixtures/cfpb/ecfr-1005-11.html", reliability_score_id="srs-ecfr-1005-11",
        derived_from_report_id="sdr-cfpb-deadline", now=_NOW)
    check("recipe build is deterministic (same inputs+now -> byte-identical recipe)",
          json.dumps(reg_recipe, sort_keys=True) == json.dumps(reg_recipe2, sort_keys=True))
    check("recipe id is content-addressed (srecipe- prefix + stable hash)",
          reg_recipe["recipe_id"].startswith("srecipe-") and reg_recipe["recipe_id"] == reg_recipe2["recipe_id"])

    # ── a recipe is a METHOD, never a fact: no served/canonical fact value rides on it. ──
    check("recipe carries NO served/canonical fact value (it is a method, not a fact)",
          "value" not in reg_recipe and "fact" not in reg_recipe and "canonical_fact" not in reg_recipe)

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_source_recipe: the M2 builder emits a schema-valid SourceRecipe.v1 "
                "carrying the source authority + access method (retry + rate-limit, no secret) + parser "
                "provider + expected_output_schema pinned to fact_assertion_candidate + reliability back-link + "
                "watch triggers; the cross-source policy + watch triggers are DERIVED from authority + "
                "current-value-ness (a current regulation value -> current_value_requires_fresh_source + "
                "scheduled/high_value_periodic watch; a settled official value -> single_official_source_ok; a "
                "FAQ/restatement -> two_independent_sources_required, never standing alone; a tenant_private "
                "source -> human signoff); the recipe is a method not a fact; and the build is fully "
                "deterministic (content-addressed id)."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the ContextOps SourceRecipe (M2) builder.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
