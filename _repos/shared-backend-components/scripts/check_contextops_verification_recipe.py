#!/usr/bin/env python3
"""scripts.check_contextops_verification_recipe — proof (CONTEXTOPS VERIFICATION-RECIPE MODE): the M3 rung
builder emits a VerificationRecipe that carries — REQUIRED — the fact_key + input SourceRecipe ids + the
extractor id + deterministic validators + success criteria + an authority policy + a cross-source confirmation
policy + a freshness policy + a tenant scope, and that produces a fact_verification_run (a candidate result +
receipt), NEVER a served/canonical fact.

THE LOAD-BEARING AUTHORITY INVARIANT: a FAQ/secondary source can NEVER be the winning source of a verification
— the builder REJECTS a non-high-authority winning_source_type at build time (not only via the schema). The
freshness policy is DERIVED: a current/moving value (deadline/rate/fee/…) gets a tight staleness horizon +
requires_fresh_for_current_values; a settled value tolerates a 30-day window.

Concretely:
  - a recipe whose winner is a regulation builds + validates against VerificationRecipe, produces a
    fact_verification_run (never a canonical fact), and carries an authority + cross_source + freshness +
    tenant_scope block;
  - building with winning_source_type=agency_faq RAISES ValueError (a FAQ can never win);
  - a current value gets the tight freshness horizon; a settled value gets the wide one;
  - determinism: same inputs + same now -> byte-identical recipe.

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_contextops_verification_recipe.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.schema_validator import validate as _validate  # noqa: E402
from src.baltor.contextops.verification_recipe import (  # noqa: E402
    PRODUCES,
    WINNING_SOURCE_TYPES,
    build_verification_recipe,
    freshness_policy,
)

_SCHEMA = _resource("schemas") / "contextops" / "VerificationRecipe.schema.json"
_NOW = "2026-06-05T00:00:00Z"


def _build_reg(**over):
    kw = dict(tenant_id="acme", source_scope="global_public",
              fact_key="reg_e.error_resolution.deadline",
              input_source_recipe_ids=["srecipe-ecfr-1005-11"], extractor_id="xsnip-duration-1005-11",
              winning_source_type="regulation", min_authority_rank=80,
              cross_source_policy="current_value_requires_fresh_source", min_independent_sources=1, now=_NOW)
    kw.update(over)
    return build_verification_recipe(**kw)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schema = json.loads(_SCHEMA.read_text())

    # ── a regulation-winning recipe builds + validates. ──
    vr = _build_reg()
    check("verification recipe validates against VerificationRecipe", _validate(vr, schema) == [], str(_validate(vr, schema)[:4]))

    # ── REQUIRED blocks present + correctly populated. ──
    check("recipe carries fact_key + input source recipe ids + extractor id",
          bool(vr.get("fact_key")) and vr.get("input_source_recipe_ids") and bool(vr.get("extractor_id")))
    check("recipe carries deterministic validators + success criteria",
          len(vr.get("validators", [])) >= 1 and bool(vr.get("success_criteria")))
    check("recipe carries an authority policy (min_authority_rank + winning_source_type)",
          {"min_authority_rank", "winning_source_type"} <= set(vr["authority"]))
    check("recipe carries a cross_source confirmation policy",
          {"policy", "min_independent_sources"} <= set(vr["cross_source"]))
    check("recipe carries a freshness policy (max_staleness_seconds + requires_fresh_for_current_values)",
          {"max_staleness_seconds", "requires_fresh_for_current_values"} <= set(vr["freshness"]))
    check("recipe carries a tenant_scope (a tenant_private verification can never publish a global fact)",
          bool(vr.get("tenant_scope")))

    # ── produces a fact_verification_run (candidate + receipt), NEVER a canonical/served fact. ──
    check("recipe produces is pinned to fact_verification_run (a recipe verifies; it never promotes a fact)",
          vr["produces"] == PRODUCES)
    check("recipe carries NO served/canonical fact value (it is a verification method, not a fact)",
          "value" not in vr and "fact" not in vr and "canonical_fact" not in vr)

    # ── THE AUTHORITY INVARIANT: only a high-authority type may win; a FAQ can never win. ──
    check("winning_source_type is a high-authority type (regulation)",
          vr["authority"]["winning_source_type"] in WINNING_SOURCE_TYPES)
    for bad in ("agency_faq", "secondary_summary", "blog", "vendor_doc"):
        try:
            _build_reg(winning_source_type=bad)
            check(f"build REJECTS winning_source_type={bad!r} (red-team: a FAQ/secondary can never win)",
                  False, "no exception raised")
        except ValueError as e:
            check(f"build RAISES ValueError for winning_source_type={bad!r} (red-team: FAQ/secondary cannot win)",
                  bad in str(e) or "high-authority" in str(e))

    # ── the freshness policy is DERIVED from current-value-ness. ──
    cur = freshness_policy(fact_key="reg_e.error_resolution.deadline")
    settled = freshness_policy(fact_key="reg_e.error_resolution.process_overview")
    check("a CURRENT/moving value gets a TIGHTER freshness horizon than a settled value",
          cur["max_staleness_seconds"] < settled["max_staleness_seconds"])
    check("freshness requires a fresh read for current values",
          cur["requires_fresh_for_current_values"] is True)

    # ── determinism: same inputs + same now -> byte-identical recipe. ──
    vr2 = _build_reg()
    check("verification recipe build is deterministic (same inputs+now -> byte-identical recipe)",
          json.dumps(vr, sort_keys=True) == json.dumps(vr2, sort_keys=True))
    check("recipe id is content-addressed (vrecipe- prefix + stable hash)",
          vr["recipe_id"].startswith("vrecipe-") and vr["recipe_id"] == vr2["recipe_id"])

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_verification_recipe: the M3 builder emits a schema-valid "
                "VerificationRecipe carrying the fact_key + input source recipe ids + extractor id + "
                "deterministic validators + success criteria + an authority policy + a cross_source policy + a "
                "freshness policy + a tenant scope; it produces a fact_verification_run (candidate + receipt), "
                "NEVER a canonical/served fact; it ENFORCES the authority invariant at build time — a "
                "FAQ/secondary winning_source_type RAISES (a FAQ can never win); the freshness horizon is "
                "DERIVED (current values get a tight window + requires_fresh); and the build is fully "
                "deterministic (content-addressed id)."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the ContextOps VerificationRecipe (M3) builder.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
