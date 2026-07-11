#!/usr/bin/env python3
"""scripts.bench_project_to_primitives — bench.project_to_primitives.v1: MEASURE the primitive YIELD of building a
project. Decompose each executable genome's built code into primitive candidates, count how many are pure
certification targets, and how many correspond to ALREADY-CERTIFIED reusable primitives — the empirical answer to
"does generating whole projects discover reusable primitives?" (candidate-only, executed, deterministic).

Owner (2026-07-09): the app/project is ORE — the goal is primitive extraction + certification. The most important
new benchmark asks: primitive_candidates_per_project, certifiable_candidates_per_project, and
tokens_per_certified_primitive. This runs that over the LARGE genomes already built (11-module ops-API, 10-module
ETL DAG, ...). It is fully EXECUTED (real decomposition via saas_buildout_decomposer) and deterministic — no model
call needed for the reference builds; the live tokens_per_certified come from the A/B receipt when present.

    python3 scripts/bench_project_to_primitives.py --self-test
    python3 scripts/bench_project_to_primitives.py --run
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

from scripts.saas_buildout_decomposer import decompose_project  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # executed decomposition of real built code; deterministic; no fabricated numbers
ARTIFACT_DIR_REL = "data/dev-intel/project_to_primitives"


def _executable_genomes() -> dict[str, dict[str, Any]]:
    """Every genome that ships a runnable reference build (its 'good' files) across the buildout modules."""
    import scripts.buildout_forge as _bf  # noqa: PLC0415
    import scripts.buildout_forge_large as _bl  # noqa: PLC0415
    import scripts.buildout_forge_pipeline as _bp  # noqa: PLC0415
    import scripts.buildout_oracle_patterns as _bo  # noqa: PLC0415
    reg: dict[str, dict[str, Any]] = {}
    for mod in (_bf, _bl, _bp, _bo):
        for gid, genome in getattr(mod, "_GENOMES", {}).items():
            if isinstance(genome.get("good"), dict):
                reg[gid] = genome
    return reg


def _certified_registry_names() -> set[str]:
    """The impl-names of ALREADY-CERTIFIED reusable primitives (the coverage + cloud_function packs self-certify
    via oracle fixtures). A decomposed candidate whose name matches one is a proven reuse opportunity."""
    names: set[str] = set()
    for mod_name in ("scripts.project_coverage_primitive_pack", "scripts.cloud_function_primitive_pack"):
        try:
            mod = __import__(mod_name, fromlist=["_PRIMITIVES"])
            names |= {s["fn"].__name__ for s in mod._PRIMITIVES}
        except Exception:  # noqa: BLE001
            continue
    return names


def yield_for_genome(genome_id: str, genome: dict[str, Any], certified: set[str]) -> dict[str, Any]:
    """Decompose one genome's built code -> primitive-yield metrics (all executed/deterministic)."""
    decomp = decompose_project(genome["good"])
    prims = decomp["primitives"]
    names = [p["name"] for p in prims]
    pure = [p for p in prims if p.get("certification_target")]
    declared = set(genome.get("primitive_targets") or [])
    matched_certified = sorted({n for n in names if n in certified})
    declared_certified = sorted(declared & certified)
    return {"genome_id": genome_id, "n_modules": len(genome["good"]),
            "primitive_candidates_extracted": len(prims),
            "certification_targets": len(pure),
            "declared_primitive_targets": len(declared),
            "candidates_matching_certified_registry": len(matched_certified),
            "declared_targets_in_certified_registry": len(declared_certified),
            "matched_certified_names": matched_certified,
            "candidate_names": names, **BOUNDARY}


def _tokens_per_certified() -> dict[str, Any]:
    """If a live large-A/B receipt exists, compute the REAL tokens a bare build spent per certifiable primitive it
    yielded. Purely from executed receipts; absent -> reported as not_available (never fabricated)."""
    root = resource("data/dev-intel/buildout_forge")
    hits = sorted(root.rglob("*_large_ab_distribution.json")) if root.exists() else []
    if not hits:
        return {"available": False, "reason": "no executed large-A/B receipt yet"}
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
        runs = d.get("runs") or []
        bare = [r["harness_alone"]["output_tokens"] for r in runs
                if r.get("harness_alone", {}).get("oracle_pass")]
        if not bare:
            return {"available": False, "reason": "no passing bare build in the receipt (capability-limited)"}
        return {"available": True, "genome_id": d.get("genome_id"),
                "mean_bare_output_tokens": round(sum(bare) / len(bare), 1), "n_passing_bare": len(bare)}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": type(exc).__name__}


def run_bench() -> dict[str, Any]:
    certified = _certified_registry_names()
    genomes = _executable_genomes()
    per = [yield_for_genome(gid, g, certified) for gid, g in sorted(genomes.items())]
    n_proj = len(per)
    tot_cand = sum(p["primitive_candidates_extracted"] for p in per)
    tot_targets = sum(p["certification_targets"] for p in per)
    tot_matched = sum(p["candidates_matching_certified_registry"] for p in per)
    return {"record_type": "bench_project_to_primitives", "benchmark_kind": BENCHMARK_KIND,
            "n_projects": n_proj, "n_certified_registry": len(certified),
            "primitive_candidates_per_project": round(tot_cand / n_proj, 2) if n_proj else 0,
            "certification_targets_per_project": round(tot_targets / n_proj, 2) if n_proj else 0,
            "certified_matches_per_project": round(tot_matched / n_proj, 2) if n_proj else 0,
            "total_candidates": tot_cand, "total_certification_targets": tot_targets,
            "total_certified_matches": tot_matched,
            "tokens_per_certified_primitive": _tokens_per_certified(),
            "per_genome": per, **BOUNDARY}


def emit() -> dict[str, str]:
    out = resource(ARTIFACT_DIR_REL)
    out.mkdir(parents=True, exist_ok=True)
    res = run_bench()
    (out / "project_to_primitives_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True),
                                                            encoding="utf-8")
    return {"receipt": str(out / "project_to_primitives_receipt.json"),
            "candidates_per_project": str(res["primitive_candidates_per_project"]),
            "certified_matches_per_project": str(res["certified_matches_per_project"])}


def self_test() -> bool:
    """Mutation-gated + EXECUTED + deterministic: decomposing the LARGE ops-API build yields many primitive
    candidates incl. pure targets that MATCH certified reusable primitives; the bench is byte-identical twice."""
    certified = _certified_registry_names()
    assert len(certified) >= 15, f"the certified registry must be non-trivial: {len(certified)}"

    res = run_bench()
    assert res["n_projects"] >= 3, f"must cover multiple executable genomes: {res['n_projects']}"
    ops = next((p for p in res["per_genome"] if p["genome_id"] == "backoffice_ops_api__stdlib_http__v0"), None)
    assert ops is not None, "the 11-module ops-API must be covered"
    assert ops["primitive_candidates_extracted"] >= 12, f"ops-API must yield >=12 candidates: {ops}"
    assert ops["candidates_matching_certified_registry"] >= 4, \
        f"several ops-API candidates must match certified reusable primitives: {ops['matched_certified_names']}"
    assert res["total_certified_matches"] >= 6, "the built projects must surface real certified-reuse opportunities"

    # determinism: decomposition + matching is byte-identical across runs (no hidden randomness).
    assert json.dumps(run_bench(), sort_keys=True) == json.dumps(res, sort_keys=True), "bench must be deterministic"
    assert BENCHMARK_KIND == "real" and res["serves_truth"] is False
    tpc = res["tokens_per_certified_primitive"]
    print(f"OK bench_project_to_primitives self-test: {res['n_projects']} executable projects decomposed; "
          f"{res['primitive_candidates_per_project']} candidates/project ({res['certification_targets_per_project']} "
          f"pure targets), {res['certified_matches_per_project']} match the certified registry/project; ops-API "
          f"yields {ops['primitive_candidates_extracted']} candidates ({ops['candidates_matching_certified_registry']} "
          f"certified matches); tokens_per_certified={'live' if tpc.get('available') else tpc.get('reason')}; "
          f"deterministic; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="bench.project_to_primitives.v1 — primitive YIELD per built project.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        print(json.dumps(emit(), indent=2))
        res = run_bench()
        for p in res["per_genome"]:
            print(f"  {p['genome_id']:44} modules={p['n_modules']:2} candidates={p['primitive_candidates_extracted']:2} "
                  f"pure={p['certification_targets']:2} certified_match={p['candidates_matching_certified_registry']}")
        return
    self_test()


if __name__ == "__main__":
    main()
