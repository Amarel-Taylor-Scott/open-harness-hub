#!/usr/bin/env python3
"""scripts.real_app_forge — RealAppForge spine: turn REAL public apps (Claude-Code / Polsia-built SaaS,
newsletters, marketplaces, directories) into SOURCE-backed, legally-safe EQUIVALENT buildout tasks, and enforce
the evidence-tier discipline that keeps discovery honest — public claims are SOURCE evidence (A0-A5), never a
benchmark result; only EXECUTED equivalent buildouts (A6) and paired reuse wins (A7) may headline a savings
number (candidate-only).

Owner (2026-07-09): mine real apps -> app genomes -> equivalent tasks -> harness-alone vs harness+primitives ->
decompose -> rerun -> measure real savings. The KEY realization: an app genome is just another LARGE genome, so
it plugs straight into `run_large_project_ab` (executed both-arms A/B, netted tokens, distribution). This module
is the DISCIPLINE + CATALOG + promotion gate; it fabricates nothing. Legal guardrails: EQUIVALENT tasks only
(same feature class, never branding/copy/UI/proprietary code/private data); "real customers" is never asserted
without independent evidence. serves_truth=false throughout.

    python3 scripts/real_app_forge.py --self-test
    python3 scripts/real_app_forge.py --catalog          # the app-family catalog + which are A6-executable
    python3 scripts/real_app_forge.py --promote back_office_ops_saas   # EXECUTE the equivalent buildout -> A6 or not
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"real_app_forge requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_app_buildout"  # A6 promotion EXECUTES a build + hidden oracle via run_large_project_ab
ARTIFACT_DIR_REL = "data/dev-intel/real_app_forge"

# ── the evidence ladder — the discipline that keeps app discovery honest ──────────────────────────────────────
EVIDENCE_TIERS: dict[str, str] = {
    "A0": "mention only — someone claims the app exists",
    "A1": "live URL — a public app/landing page loads",
    "A2": "product surface — public pricing/signup/docs/demo/changelog",
    "A3": "user evidence — testimonials / PH/HN/Reddit / reviews / case study",
    "A4": "revenue/customer evidence — paid plan / public revenue / customer logos / checkout path (SELF-REPORTED)",
    "A5": "owner-permissioned — founder gives repo/logs/analytics/build history",
    "A6": "reproducible EQUIVALENT buildout passes a hidden oracle (EXECUTED)",
    "A7": "primitive reuse PROVEN — harness+primitives beats alone on equivalent apps, paired real receipts",
}
HEADLINE_TIERS = frozenset({"A6", "A7"})  # ONLY executed tiers may back a savings/quality claim
SOURCE_TIERS = frozenset({"A0", "A1", "A2", "A3", "A4", "A5"})  # discovery = source evidence, NOT a result


def headline_eligible(tier: str) -> bool:
    """The core rule: a public-claim tier (A0-A5) can NEVER headline a savings number — only executed A6/A7."""
    return tier in HEADLINE_TIERS


def is_benchmark_result(record: dict[str, Any]) -> bool:
    """Source discovery + app-genome extraction are NEVER benchmark results (owner law). Only an executed
    app-buildout receipt with an oracle_pass at tier A6/A7 counts."""
    return (record.get("record_type") in ("real_app_buildout_receipt", "app_rebuild_ab_result")
            and record.get("oracle_executed") is True
            and headline_eligible(record.get("evidence_tier", "A0")))


# ── app-family catalog: SOURCE-backed equivalent tasks. Families without an executable_genome are A2/A3 SOURCE
#    only (they describe what to build; they are NOT results). Two families map to genomes that ALREADY run a
#    hidden oracle (ops-API, ETL DAG) and so are A6-CAPABLE via run_large_project_ab. ───────────────────────────
_APP_FAMILIES: list[dict[str, Any]] = [
    {"app_type": "newsletter_saas", "domain": "publishing",
     "core_objects": ["subscriber", "segment", "post", "campaign", "sponsor_slot"],
     "feature_modules": ["subscribe", "segment", "publish", "archive_page", "send", "analytics"],
     "macro_primitives": ["newsletter_subscribe_module", "post_editor_module", "campaign_sequence_module",
                          "archive_page_module"],
     "micro_primitives": ["email_validator", "unsubscribe_token", "digest_builder"],
     "hidden_oracle_ideas": ["subscribe", "confirm double-opt-in", "publish post", "verify archive page",
                             "verify segment send count"], "executable_genome": None},
    {"app_type": "qr_feedback_saas", "domain": "customer_feedback",
     "core_objects": ["user", "org", "survey", "qr_code", "response", "dashboard"],
     "feature_modules": ["auth", "create_survey", "qr_generate", "public_response_form", "dashboard", "csv_export",
                         "plan_gate"],
     "macro_primitives": ["email_password_auth_module", "pricing_plan_gate", "dashboard_layout_module"],
     "micro_primitives": ["qr_code_generator", "survey_response_schema", "dashboard_aggregation_query",
                          "csv_rows", "public_form_validator"],
     "hidden_oracle_ideas": ["create survey", "generate QR", "submit hidden response", "verify dashboard aggregate",
                             "verify CSV export", "verify plan limit"], "executable_genome": None},
    {"app_type": "marketplace", "domain": "commerce",
     "core_objects": ["seller", "listing", "order", "review", "dispute"],
     "feature_modules": ["seller_onboarding", "listing", "search_browse", "checkout", "review_rating", "admin"],
     "macro_primitives": ["seller_onboarding_module", "listing_module", "search_browse_module",
                          "checkout_flow_module", "review_rating_module"],
     "micro_primitives": ["price_validator", "rating_aggregate", "search_filter_sort"],
     "hidden_oracle_ideas": ["onboard seller", "create listing", "search+filter", "checkout idempotent",
                             "post review", "verify rating aggregate"], "executable_genome": None},
    {"app_type": "directory_saas", "domain": "listings",
     "core_objects": ["profile", "review", "category", "plan"],
     "feature_modules": ["claim_profile", "reviews", "seo_pages", "moderation", "plan_gate"],
     "macro_primitives": ["pricing_plan_gate", "crud_resource_module", "search_filter_sort_module"],
     "micro_primitives": ["slug_builder", "review_moderation_gate", "rating_aggregate"],
     "hidden_oracle_ideas": ["claim profile", "post review", "moderate", "verify SEO page", "verify plan gate"],
     "executable_genome": None},
    {"app_type": "support_ticket_saas", "domain": "support",
     "core_objects": ["ticket", "agent", "sla", "canned_response"],
     "feature_modules": ["ticket_intake", "assignment", "sla", "canned_responses", "analytics"],
     "macro_primitives": ["queue_worker_module", "audit_event_module", "dashboard_layout_module"],
     "micro_primitives": ["ticket_schema_validator", "sla_timer", "assignment_round_robin"],
     "hidden_oracle_ideas": ["intake ticket", "assign", "breach SLA -> escalate", "canned reply",
                             "verify analytics"], "executable_genome": None},
    # ── A6-CAPABLE: these app-equivalent genomes already RUN a hidden oracle (large executed buildouts) ──
    {"app_type": "back_office_ops_saas", "domain": "b2b_operations",
     "core_objects": ["vendor", "purchase_order", "audit_event", "user"],
     "feature_modules": ["auth", "rbac", "vendor_crud", "po_crud", "pagination", "audit_log", "csv_export",
                         "signed_webhook"],
     "macro_primitives": ["email_password_auth_module", "organization_rbac_module", "crud_resource_module",
                          "audit_event_module", "webhook_idempotency_gate"],
     "micro_primitives": ["validate_vendor", "paginate", "filter_contains", "sort_by", "verify_hmac",
                          "issue_token", "verify_token", "audit_event"],
     "hidden_oracle_ideas": ["auth token", "rbac forbid viewer write", "create vendor idempotent", "paginate/filter",
                             "audit trail", "csv export", "verify signed webhook"],
     "executable_genome": "backoffice_ops_api__stdlib_http__v0"},
    {"app_type": "data_pipeline_service", "domain": "data_engineering",
     "core_objects": ["event", "vendor_dim", "fact_agg", "reject"],
     "feature_modules": ["extract", "validate", "dedupe", "join", "aggregate", "quality", "incremental_load"],
     "macro_primitives": ["queue_worker_module", "migration_validator"],
     "micro_primitives": ["validate_event", "normalize_amount_cents", "dedupe_by_key", "group_net_sum",
                          "topological_order"],
     "hidden_oracle_ideas": ["run DAG", "dedupe", "reject bad rows", "aggregate net", "idempotent rerun"],
     "executable_genome": "sales_etl_pipeline_dag__stdlib_sqlite__v0"},
]


def app_genome(app_type: str, *, evidence_tier: str = "A2", source_urls: list | None = None,
               builder_tool_claim: str = "unknown") -> dict[str, Any]:
    """Build an AppGenome record (candidate=true). evidence_tier defaults to A2 (product surface = SOURCE only).
    A genome NEVER carries a savings claim; it becomes A6 only after promote_to_a6 EXECUTES its equivalent build."""
    fam = next((f for f in _APP_FAMILIES if f["app_type"] == app_type), None)
    if fam is None:
        raise KeyError(f"unknown app_type {app_type!r}; have {[f['app_type'] for f in _APP_FAMILIES]}")
    aid = canonical_id("app", app_type, builder_tool_claim)
    return {"record_type": "app_genome", "app_id": aid, "app_type": app_type, "domain": fam["domain"],
            "evidence_tier": evidence_tier if evidence_tier in EVIDENCE_TIERS else "A0",
            "source_urls": source_urls or [], "builder_tool_claim": builder_tool_claim,
            "core_objects": fam["core_objects"], "feature_modules": fam["feature_modules"],
            "macro_primitives": fam["macro_primitives"], "micro_primitives": fam["micro_primitives"],
            "hidden_oracle_ideas": fam["hidden_oracle_ideas"],
            "executable_genome": fam["executable_genome"],
            "a6_capable": fam["executable_genome"] is not None,
            "allowed_use": "public_page_digest",  # equivalent task only; never clone/branding/private data
            "headline_eligible_now": False,        # a genome is SOURCE evidence until an executed A6 run
            **BOUNDARY}


def promote_to_a6(app_type: str) -> dict[str, Any]:
    """EXECUTE the app-equivalent buildout (its reference good build through the genome's hidden oracle). Marks A6
    iff the oracle actually passes. Only executable genomes can reach A6; a source-only family cannot be promoted."""
    genome = app_genome(app_type)
    if not genome["a6_capable"]:
        return {"record_type": "real_app_buildout_receipt", "app_type": app_type, "evidence_tier": genome["evidence_tier"],
                "promoted": False, "oracle_executed": False,
                "reason": "no executable_genome — a source-only app family cannot reach A6 without a runnable "
                          "equivalent build + hidden oracle", **BOUNDARY}
    from scripts.run_large_project_ab import _registry  # noqa: PLC0415  reuse the executed machinery
    gid = genome["executable_genome"]
    ref_genome, run_buildout = _registry()[gid]
    receipt = run_buildout(gid, ref_genome["good"])  # EXECUTED: build boots/runs + hidden oracle
    passed = bool(receipt.get("oracle_pass"))
    return {"record_type": "real_app_buildout_receipt", "app_type": app_type, "executable_genome": gid,
            "evidence_tier": "A6" if passed else genome["evidence_tier"], "promoted": passed,
            "oracle_executed": True, "oracle_pass": passed,
            "oracle_checks": receipt.get("oracle_checks"), "n_checks": len(receipt.get("oracle_checks") or {}),
            "note": ("A6 = an EQUIVALENT app buildout reproduces + passes the hidden oracle; run "
                     "run_large_project_ab.py --live for the A7 paired-reuse savings number"), **BOUNDARY}


def catalog() -> dict[str, Any]:
    genomes = [app_genome(f["app_type"]) for f in _APP_FAMILIES]
    return {"record_type": "real_app_catalog", "n_families": len(genomes),
            "n_a6_capable": sum(1 for g in genomes if g["a6_capable"]),
            "source_only": [g["app_type"] for g in genomes if not g["a6_capable"]],
            "a6_capable": [g["app_type"] for g in genomes if g["a6_capable"]],
            "evidence_tiers": EVIDENCE_TIERS, "headline_tiers": sorted(HEADLINE_TIERS),
            "genomes": genomes, **BOUNDARY}


def emit() -> dict[str, str]:
    out = resource(ARTIFACT_DIR_REL)
    out.mkdir(parents=True, exist_ok=True)
    cat = catalog()
    (out / "app_catalog.json").write_text(json.dumps(cat, indent=2, sort_keys=True), encoding="utf-8")
    return {"catalog": str(out / "app_catalog.json"), "n_families": str(cat["n_families"]),
            "n_a6_capable": str(cat["n_a6_capable"])}


def self_test() -> bool:
    """Mutation-gated on the DISCIPLINE + an EXECUTED A6 promotion:
    - a public-claim tier (A0-A5) is NEVER headline-eligible; only A6/A7 are;
    - source discovery / genome extraction is NEVER a benchmark result;
    - a source-only app family CANNOT be promoted to A6 (no runnable oracle);
    - an A6-capable app family (ops-API) EXECUTES its equivalent build + hidden oracle and reaches A6."""
    assert headline_eligible("A6") and headline_eligible("A7"), "A6/A7 must be headline-eligible"
    for t in ("A0", "A1", "A2", "A3", "A4", "A5"):
        assert not headline_eligible(t), f"source tier {t} must NEVER headline a savings number"

    g = app_genome("newsletter_saas", evidence_tier="A3")
    assert g["headline_eligible_now"] is False and g["a6_capable"] is False, "a source family is not a result"
    assert not is_benchmark_result(g), "an app_genome record is source evidence, not a benchmark result"

    src_only = promote_to_a6("newsletter_saas")
    assert src_only["promoted"] is False and src_only["oracle_executed"] is False, \
        "a source-only family cannot reach A6 without a runnable equivalent build"

    # EXECUTED A6: the back-office-ops SaaS equivalent build runs + passes its hidden oracle.
    a6 = promote_to_a6("back_office_ops_saas")
    assert a6["oracle_executed"] is True and a6["promoted"] is True and a6["evidence_tier"] == "A6", \
        f"the ops-API equivalent build must EXECUTE + pass its hidden oracle -> A6: {a6}"
    assert a6["n_checks"] >= 20, f"A6 must be backed by a strong hidden oracle: {a6['n_checks']} checks"
    assert is_benchmark_result(a6), "an executed A6 buildout receipt IS a benchmark result"

    cat = catalog()
    assert cat["n_a6_capable"] >= 2 and cat["serves_truth"] is False
    assert BENCHMARK_KIND == "real_app_buildout"
    print(f"OK real_app_forge self-test: {cat['n_families']} app families ({cat['n_a6_capable']} A6-executable: "
          f"{cat['a6_capable']}); source tiers A0-A5 NEVER headline; discovery is not a result; a source-only "
          f"family cannot reach A6; the ops-API equivalent build EXECUTED + passed {a6['n_checks']} hidden checks "
          f"-> A6; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="RealAppForge: app genomes + evidence-tier discipline + A6 promotion.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--catalog", action="store_true")
    ap.add_argument("--promote", metavar="APP_TYPE")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.catalog:
        print(json.dumps(emit(), indent=2))
        c = catalog()
        for g in c["genomes"]:
            print(f"  {g['app_type']:24} tier={g['evidence_tier']} a6_capable={g['a6_capable']} "
                  f"macro={len(g['macro_primitives'])} micro={len(g['micro_primitives'])}")
        return
    if args.promote:
        print(json.dumps(promote_to_a6(args.promote), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
