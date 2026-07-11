#!/usr/bin/env python3
"""semantic_linker_token_bench — measure WHERE the linker reduces tokens (the savings curve + break-even).

The whole point of the semantic linker is token savings + convenience: the model emits a compact plan instead of
re-writing implementations that already exist. This benchmark MEASURES that — honestly — so we can see where it pays
and where it does not.

Two lanes:
  1. COVERAGE SWEEP (controlled, deterministic): take a fixed plan and vary how many of its capabilities the registry
     covers (0% -> 100%). At each level, run the linker (resolve + assemble) and record the STRUCTURAL token savings.
     This yields the savings CURVE and the BREAK-EVEN coverage — the actionable number: "the linker saves once
     coverage exceeds X%." At low coverage the linker COSTS tokens (plan overhead + you still author the residuals);
     that honest crossover is the point.
  2. PER-FAMILY (real corpus): run representative plans across task families against the real 10.28M-vector facet
     store and report per-family resolved coverage + savings — so an auth/security plan (covered) shows real savings
     while a web-CRUD plan (uncovered) honestly shows none, until its primitives are minted.

HONESTY (the standing discipline + the 50M research bundle): this measures **structural / resolved** token savings —
a PROJECTION of implementation tokens the resolved primitives keep out of context. It is NOT "verified reuse
coverage" (which requires EXECUTING the primitive under a hidden oracle and confirming that removing/mutating it
breaks the requirement) and NOT a live-model token count. Those are the reuse fabric's execute->prove path +
`semantic_linker_long_session_benchmark.py` (Codex). The deterministic-composition floor measured here is the robust,
model-independent lower bound; the live number can only be >= or gated by correctness. serves_truth=false.

    PYTHONPATH=. python3 scripts/semantic_linker_token_bench.py --self-test
    PYTHONPATH=. python3 scripts/semantic_linker_token_bench.py --sweep          # the coverage curve + break-even
    PYTHONPATH=. python3 scripts/semantic_linker_token_bench.py --families       # per-family run on the real store
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts import semantic_linker_resolve as _resolve  # noqa: E402
from scripts import semantic_linker_assemble as _assemble  # noqa: E402


def _metrics_for(asm: dict[str, Any], n_steps: int) -> dict[str, Any]:
    """Pull the reportable metrics out of one assemble result."""
    tp = asm.get("token_projection") or {}
    return {"steps": n_steps, "resolved": asm["n_mounted"], "adapters": asm["n_adapters"],
            "residual": asm["n_residual"],
            "resolved_coverage": round(asm["n_mounted"] / n_steps, 4) if n_steps else 0.0,
            "deterministic_composition": asm["deterministic_composition"],
            "baseline_tokens": tp.get("baseline_output_tokens", 0),
            "linked_tokens": tp.get("linked_output_tokens", 0),
            "tokens_saved": tp.get("tokens_saved", 0),
            "savings_fraction": tp.get("savings_fraction", 0.0)}


# ================================================================================================================
# Lane 1 — the controlled COVERAGE SWEEP (clean curve + break-even, deterministic, offline)
# ================================================================================================================
def coverage_sweep(plan: dict[str, Any], covering_cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Vary registry coverage 0..N (N = plan steps) by exposing only the first k covering primitives; measure the
    linker savings at each level. Returns the curve + the break-even coverage (first level with tokens_saved > 0)."""
    steps = plan.get("steps", [])
    n = len(steps)
    # map each step's capability -> its covering card (by keyword retrieval over ALL covering cards)
    curve: list[dict[str, Any]] = []
    break_even: Optional[float] = None
    for k in range(0, n + 1):
        # expose only the covering cards for the FIRST k steps -> those k resolve, the rest become residuals
        exposed_caps = {steps[i]["capability"] for i in range(k)}
        subset = [c for c in covering_cards if c.get("_covers") in exposed_caps]
        retr = _resolve._keyword_retriever(subset) if subset else (lambda q, kk: [])
        asm = _assemble.link_and_assemble(plan, cards=subset, retriever=retr)
        m = _metrics_for(asm, n)
        m["coverage_level"] = round(k / n, 4) if n else 0.0
        curve.append(m)
        if break_even is None and m["tokens_saved"] > 0:
            break_even = m["coverage_level"]
    return {"plan": plan.get("name"), "n_steps": n, "curve": curve, "break_even_coverage": break_even,
            "note": "STRUCTURAL projection; savings rise with coverage and cross zero at break-even. "
                    "At low coverage the linker COSTS tokens (plan overhead + residual authoring). serves_truth=false."}


def _create_user_covering_cards() -> list[dict[str, Any]]:
    """The 5 primitives that fully cover the create-user plan, tagged with which capability each covers."""
    cards = _resolve._fixture_cards()
    cover_map = {"prim:t:decode": "http.decode-json", "prim:t:validate": "users.validate-create",
                 "prim:t:hash": "security.password-hash", "prim:t:insert": "users.insert",
                 "prim:t:view": "users.public-view"}
    out = []
    for c in cards:
        if c["primitive_id"] in cover_map:
            out.append({**c, "_covers": cover_map[c["primitive_id"]]})
    return out


# ================================================================================================================
# Lane 2 — per-task-family run on the REAL corpus (honest coverage/savings by domain)
# ================================================================================================================
#: Representative plans across task families. Some domains our current corpus covers (auth/security/OpenAPI),
#: others it does not yet (web-CRUD, data-pipeline) — the point is to show the coverage->savings relationship on
#: REAL primitives, not to pretend uniform coverage.
#: Each step declares the OUTPUT TYPE it must produce (typed ports) — so a primitive that merely shares words but
#: produces the wrong type is rejected (the anti-spurious-coverage gate). The types are what each DOMAIN naturally
#: requires; the corpus (auth/edge foundry) decides which resolve — that is the honest coverage signal.
_FAMILY_PLANS: list[dict[str, Any]] = [
    {"name": "auth-openapi-validate", "family": "auth/security",
     "steps": [{"var": "d", "capability": "decode openapi document", "in": ["req"], "out": "OpenApiDocument"},
               {"var": "s", "capability": "validate security schemes", "in": ["d"], "out": "SecuritySchemeValidationReport"},
               {"var": "r", "capability": "emit auth validation report", "in": ["s"], "out": "AuthValidationReport"}],
     "policy": {}},
    {"name": "sanctions-screen", "family": "compliance/sanctions",
     "steps": [{"var": "n", "capability": "normalize party name", "in": ["raw"], "out": "CanonicalPartyName"},
               {"var": "m", "capability": "screen against sanctions list", "in": ["n"], "out": "SanctionsScreeningMatch"},
               {"var": "r", "capability": "emit screening match report", "in": ["m"], "out": "ScreeningMatchReport"}],
     "policy": {}},
    {"name": "create-user-crud", "family": "web-CRUD",
     "steps": _resolve._CREATE_USER_PLAN["steps"], "policy": {"network": "none"}},  # carries UserCreate/…/PublicUserView out types
    {"name": "data-normalize", "family": "data-pipeline",
     "steps": [{"var": "p", "capability": "parse csv records", "in": ["src"], "out": "ParsedRecordBatch"},
               {"var": "n", "capability": "normalize record fields", "in": ["p"], "out": "NormalizedRecordBatch"},
               {"var": "u", "capability": "deduplicate records", "in": ["n"], "out": "DedupedRecordSet"},
               {"var": "o", "capability": "emit normalized output", "in": ["u"], "out": "NormalizedRecordOutput"}],
     "policy": {}},
]


#: RELEVANCE floor for the real cosine (facet_search) retriever — a capability whose best match scores below this
#: is genuinely UNCOVERED (a residual), not a fake bind. Without it, the retriever always returns *something* and
#: every plan looks 100%-covered (dishonest). 0.62 keeps strong domain matches (auth ~0.77-0.85) and drops weak ones.
_REAL_MIN_SCORE = 0.62


def family_run(cards: list[dict[str, Any]], *, k: int = 8, min_score: float = _REAL_MIN_SCORE) -> dict[str, Any]:
    """Resolve+assemble each family plan against the real store; report per-family coverage + structural savings.
    A RELEVANCE floor (min_score) is applied so uncovered capabilities are honest residuals, not fake binds."""
    from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415

    def _r(query, kk):
        return _facet.facet_search(query, cards, k=kk)

    rows = []
    for plan in _FAMILY_PLANS:
        asm = _assemble.link_and_assemble(plan, cards=cards, retriever=_r, k=k, min_score=min_score)
        m = _metrics_for(asm, len(plan["steps"]))
        rows.append({"plan": plan["name"], "family": plan["family"], **m})
    covered = [r for r in rows if r["resolved_coverage"] >= 0.5]
    return {"record_type": "linker_family_token_run", "n_plans": len(rows), "per_plan": rows,
            "families_with_savings": [r["plan"] for r in rows if r["tokens_saved"] > 0],
            "high_coverage_plans": [r["plan"] for r in covered],
            "note": "STRUCTURAL/RESOLVED projection on the real facet store; savings track coverage. Live executed "
                    "number = the reuse fabric (execute->prove) + semantic_linker_long_session_benchmark. serves_truth=false."}


# ================================================================================================================
# Self-test
# ================================================================================================================
def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    cover = _create_user_covering_cards()
    sweep = coverage_sweep(_resolve._CREATE_USER_PLAN, cover)
    curve = sweep["curve"]

    # (1) FULL coverage -> deterministic composition + positive savings; ZERO coverage -> no savings (costs tokens).
    full, zero = curve[-1], curve[0]
    checks.append((f"full coverage: det-composition + saves ({full['tokens_saved']} tok, {full['savings_fraction']:.0%}); "
                   f"zero coverage: no save ({zero['tokens_saved']})",
                   full["deterministic_composition"] and full["tokens_saved"] > 0 and zero["tokens_saved"] <= 0,
                   f"full={full['tokens_saved']} zero={zero['tokens_saved']}"))

    # (2) MONOTONIC: savings never DECREASE as coverage rises (more reuse never costs more, structurally).
    saved_seq = [c["tokens_saved"] for c in curve]
    monotonic = all(saved_seq[i] <= saved_seq[i + 1] for i in range(len(saved_seq) - 1))
    checks.append((f"savings monotonic in coverage: {saved_seq}", monotonic, str(saved_seq)))

    # (3) BREAK-EVEN exists and is between 0 and 1 (there is a coverage threshold where the linker starts saving).
    be = sweep["break_even_coverage"]
    checks.append((f"break-even coverage exists in (0,1]: {be}", be is not None and 0 < be <= 1.0, str(be)))

    # (4) COVERAGE tracks resolved: at level k, resolved_coverage == k/n.
    ok_cov = all(abs(c["coverage_level"] - c["resolved_coverage"]) < 1e-9 for c in curve)
    checks.append(("resolved coverage matches the exposed coverage level at every point", ok_cov, ""))

    # (5) DETERMINISM: the whole sweep is byte-identical twice.
    s2 = json.dumps(coverage_sweep(_resolve._CREATE_USER_PLAN, cover), sort_keys=True)
    checks.append(("sweep deterministic (byte-identical twice)",
                   json.dumps(sweep, sort_keys=True) == s2, "hash match"))

    # (6) FAMILY RUN shape (offline, injected fixture cards so it needs no real store): produces per-plan rows.
    fam = family_run(cover)  # cover cards only cover create-user; other families -> low coverage (honest)
    cu = next((r for r in fam["per_plan"] if r["plan"] == "create-user-crud"), None)
    checks.append(("family run produces per-plan rows incl. create-user",
                   fam["n_plans"] == len(_FAMILY_PLANS) and cu is not None, f"{fam['n_plans']} plans"))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - semantic_linker_token_bench: coverage SWEEP (curve + break-even) + "
          f"per-family run; STRUCTURAL/resolved token savings (deterministic floor; live = fabric + long-session bench)")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Measure where the semantic linker reduces tokens (coverage curve + per-family).")
    ap.add_argument("--self-test", action="store_true", help="offline gates (sweep monotonic + break-even + determinism)")
    ap.add_argument("--sweep", action="store_true", help="print the create-user coverage->savings curve + break-even")
    ap.add_argument("--families", action="store_true", help="per-task-family run on the REAL facet store")
    ap.add_argument("--k", type=int, default=8)
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.sweep:
        print(json.dumps(coverage_sweep(_resolve._CREATE_USER_PLAN, _create_user_covering_cards()), indent=2))
        return 0
    if args.families:
        from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415
        cards = _facet.load_cards(sample=0)
        print(json.dumps(family_run(cards, k=args.k), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
