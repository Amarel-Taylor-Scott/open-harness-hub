#!/usr/bin/env python3
"""scripts.check_contextops_source_discovery — proof (CONTEXTOPS SOURCE-DISCOVERY MODE): for the CFPB reference
fact_key ``reg_e.error_resolution.deadline`` the discovery driver finds an OFFICIAL-REGULATION source
candidate, ranks the FAQ candidate LOWER (a FAQ can NEVER outrank a regulation), serves NO truth, searches
EXISTING Baltor artifacts FIRST (cheapest rung), and PROPOSES a SourceRecipe for the winning candidate.

Concretely:
  - the driver returns a schema-valid SourceDiscoveryReport.v1 (serves_truth pinned False) plus full
    SourceCandidate.v1 + SourceReliabilityScore.v1 objects (served_as_truth pinned False on every score);
  - the eCFR regulation candidate is classified source_type=regulation with a HIGHER authority_rank than the
    agency-FAQ candidate (the load-bearing precedence invariant: FAQ < regulation);
  - the WINNER is the regulation, never the FAQ; the proposed SourceRecipe targets the regulation handle and
    validates against SourceRecipe.v1;
  - the "search existing artifacts FIRST" rung: when the regulation handle is already held, reused_existing is
    True (no new research needed for a source we already hold);
  - determinism: same task + same now -> byte-identical output; nothing is served as a fact.

Deterministic, stdlib-only, offline (no network, no RNG, no wall-clock).
CLI: PYTHONPATH=. python3 scripts/check_contextops_source_discovery.py --self-test
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
from src.baltor.contextops.source_discovery import SourceDiscoveryDriver  # noqa: E402

_SCHEMA_DIR = _REPO / "schemas" / "contextops"
_NOW = "2026-06-05T00:00:00Z"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"

_TASK = {
    "schema_version": "ResearchTask.v1",
    "task_id": "rtask-cfpb-deadline-disc",
    "tenant_id": "acme",
    "source_scope": "global_public",
    "triage_id": "triage-cfpb-faq30-disc",
    "fact_key": "reg_e.error_resolution.deadline",
    "question": "What is the official Regulation E deadline for resolving an alleged error?",
    "authority_bar": "source_of_law",
    "bounds": {"max_steps": 8, "allowed_access": ["fixture"], "offline": True, "secrets_allowed": False},
    "produces": "source_discovery_report",
    "agent_may_serve_truth": False,
    "created_at": _NOW,
}


def _schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / f"{name}.v1.schema.json").read_text())


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    driver = SourceDiscoveryDriver()
    out = driver.discover(_TASK, existing_handles=[], now=_NOW)

    # ── the report is schema-valid + serves no truth. ──
    report = out["report"]
    check("discovery returns a schema-valid SourceDiscoveryReport.v1",
          _validate(report, _schema("SourceDiscoveryReport")) == [])
    check("discovery report serves_truth is pinned FALSE (the report serves no truth)",
          report.get("serves_truth") is False and out.get("serves_truth") is False)

    # ── candidates + scores are schema-valid; scores never serve truth. ──
    cands = {c["candidate_id"]: c for c in out["candidates"]}
    scores = {s["candidate_id"]: s for s in out["scores"]}
    for cid, c in cands.items():
        check(f"candidate {c['source_type']} validates against SourceCandidate.v1",
              _validate(c, _schema("SourceCandidate")) == [])
    for cid, s in scores.items():
        check(f"reliability score for {cands[cid]['source_type']} validates against SourceReliabilityScore.v1",
              _validate(s, _schema("SourceReliabilityScore")) == [])
        check(f"reliability score for {cands[cid]['source_type']} pins served_as_truth FALSE",
              s.get("served_as_truth") is False)

    # ── an official-regulation candidate is found; the FAQ is found at LOWER authority. ──
    reg = next((c for c in out["candidates"] if c["source_handle"] == _REG_HANDLE), None)
    faq = next((c for c in out["candidates"] if c["source_handle"] == _FAQ_HANDLE), None)
    check("an official-regulation source candidate is found (eCFR 12 CFR 1005.11)",
          reg is not None and reg["source_type"] == "regulation" and reg["officialness"] == "official")
    check("an agency-FAQ candidate is also found", faq is not None and faq["source_type"] == "agency_faq")
    check("THE PRECEDENCE INVARIANT: regulation authority_rank > FAQ authority_rank (a FAQ can NEVER outrank a regulation)",
          reg is not None and faq is not None and reg["authority_rank"] > faq["authority_rank"],
          f"reg={reg and reg['authority_rank']} faq={faq and faq['authority_rank']}")
    check("the regulation's reliability composite > the FAQ's composite",
          reg is not None and faq is not None
          and scores[reg["candidate_id"]]["composite_score"] > scores[faq["candidate_id"]]["composite_score"])

    # ── the WINNER is the regulation, never the FAQ. ──
    winner = cands.get(out["winner_candidate_id"])
    check("the WINNING candidate is the regulation, NOT the FAQ (red-team: FAQ cannot win)",
          winner is not None and winner["source_handle"] == _REG_HANDLE)
    check("the ranked order puts the regulation first",
          out["ranked_candidate_ids"] and out["ranked_candidate_ids"][0] == (reg and reg["candidate_id"]))

    # ── a SourceRecipe is PROPOSED for the winner + validates. ──
    recipe = out["proposed_recipe"]
    check("discovery PROPOSES a SourceRecipe for the winning candidate",
          recipe is not None and recipe.get("source_handle") == _REG_HANDLE)
    check("the proposed SourceRecipe validates against SourceRecipe.v1",
          recipe is not None and _validate(recipe, _schema("SourceRecipe")) == [])
    check("the proposed recipe is lineage-linked back to the discovery report (M1->M2)",
          recipe is not None and recipe.get("derived_from_report_id") == report["report_id"])
    check("the proposed recipe encodes the regulation's authority (precedence is in the recipe, not re-derived)",
          recipe is not None and recipe["authority"]["source_type"] == "regulation"
          and recipe["authority"]["authority_rank"] == reg["authority_rank"])
    check("the proposed recipe carries a cross_source policy + >=1 watch trigger (M2 rung encoded)",
          recipe is not None and bool(recipe["cross_source"]["policy"]) and len(recipe["watch_triggers"]) >= 1)

    # ── the 'search existing artifacts FIRST' rung: a held source is flagged reused (no new research). ──
    out_held = driver.discover(_TASK, existing_handles=[_REG_HANDLE], now=_NOW)
    check("when the regulation source is already held, reused_existing is True (cheapest rung — no re-research)",
          out_held.get("reused_existing") is True)
    out_none = driver.discover(_TASK, existing_handles=[], now=_NOW)
    check("when no source is held, reused_existing is False",
          out_none.get("reused_existing") is False)

    # ── determinism: same task + same now -> byte-identical output. ──
    out2 = driver.discover(_TASK, existing_handles=[], now=_NOW)
    check("discovery is deterministic (same task+now -> byte-identical output)",
          json.dumps(out, sort_keys=True) == json.dumps(out2, sort_keys=True))

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_source_discovery: for the CFPB verified fact_key the driver finds an "
                "official eCFR regulation candidate, finds the agency FAQ at LOWER authority (regulation rank > "
                "FAQ rank — a FAQ can never outrank a regulation), produces schema-valid SourceDiscoveryReport "
                "+ SourceCandidate + SourceReliabilityScore objects that serve NO truth (serves_truth / "
                "served_as_truth pinned false), ranks the regulation as the WINNER (never the FAQ), PROPOSES a "
                "schema-valid SourceRecipe for the winner lineage-linked to the report with the authority + "
                "cross_source policy + watch triggers encoded, flags reused_existing when the source is already "
                "held (search-existing-first), and is fully deterministic offline."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the ContextOps source-discovery driver (ResearchTask -> ranked candidates -> recipe).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
