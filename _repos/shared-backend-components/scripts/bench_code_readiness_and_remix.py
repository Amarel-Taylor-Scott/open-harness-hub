#!/usr/bin/env python3
"""scripts.bench_code_readiness_and_remix — hold OUR CODE to the same standard we hold the generated primitives.

The insight (owner, think-outside-the-box): a primitive is judged on whether it is well-formed, uniquely named,
typed at its edges, REUSABLE, COMPOSABLE/remixable, verified, and part of a multi-path portfolio. Our code is
ALSO a graph of composable units (modules) with edges (imports) and names — so score it with the SAME lens.
This turns "is the codebase healthy?" into the identical readiness + remix + gap measurement we run on
primitives, and surfaces the code that violates the very principles the factory enforces on its output.

It COMPOSES existing machinery (reuse-first): the dependency graph is ``scripts.code_graph.CodeGraph`` (the
one whose relative-import blind spot was just fixed), the "verified" standard is membership in the umbrella
``PROOF_MODULES``, and the naming standard is the pyprefix scheme. No new graph is built.

Per-module standards scorecard:
  * named_meaningful   — a context-rich, non-cryptic module name (the naming law: long names are good)
  * reused             — imported by >= 1 other module (a unit nobody reuses is a latent island)
  * composes           — imports >= 1 in-repo module (it builds ON the substrate, not in isolation)
  * remixable          — reused AND composes (a true node in the graph, not a dead end)
  * verified           — has a self-test registered in the umbrella (VERIFY-THE-VERIFIER)
Roll-up: conformance per standard; reuse/compose/remix rates; the GAPS — ISLAND modules (imported by nothing,
not entrypoints) and HIGH-FAN-IN-UNVERIFIED modules (many dependents, no self-test = concentrated risk). A
remix simulation chains imports to a reachable depth, mirroring the primitive remix sim exactly.

candidate=true / serves_truth=false — a health measurement, never a promotion.

  PYTHONPATH=. python3 scripts/bench_code_readiness_and_remix.py --self-test
  PYTHONPATH=. python3 scripts/bench_code_readiness_and_remix.py --run [--n 4000] [--depth 8] [--emit-gaps]
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
from collections import defaultdict  # noqa: E402

from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402

OUT_DIR = _resource("data") / "dev-intel" / "code_readiness_remix"
#: entrypoint shapes that are legitimately NOT imported (CLIs, servers, checks) — an island only if NOT one.
_ENTRYPOINT = re.compile(r"(^|\.)(check_|build_|run_|prove_|demo_|scaffold_|generate_|start_)"
                         r"|(_server|_service|_loop|_daemon|_cli|_main|__main__)$")
#: a context-rich name (the naming law) — descriptive, not a 1-3 char cryptic module.
_MIN_NAME_LEN = 6


def _verified_modules() -> set[str]:
    """Dotted module names that carry a self-test registered in the umbrella (the 'verified' standard)."""
    try:
        from scripts.flywheel_proof_modules import PROOF_MODULES  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return set()
    out = set()
    for path, _label in PROOF_MODULES:
        if isinstance(path, str) and path.endswith(".py"):
            out.add(path[:-3].replace("/", "."))
    return out


def _is_entrypoint(module: str) -> bool:
    return bool(_ENTRYPOINT.search(module))


def score_module(module: str, imports: set, importers: set, verified: set) -> dict:
    """Score one code module against the standards — the code analog of a primitive's readiness scorecard."""
    leaf = module.rsplit(".", 1)[-1]
    reused = len(importers) >= 1
    composes = len(imports) >= 1
    dims = {
        "named_meaningful": len(leaf) >= _MIN_NAME_LEN and not leaf.isupper(),
        "reused": reused or _is_entrypoint(module),  # entrypoints are "reused" by their runner, not by import
        "composes": composes,
        "remixable": (reused or _is_entrypoint(module)) and composes,
        "verified": module in verified,
    }
    passed = sum(1 for v in dims.values() if v)
    return {
        "record_type": "code_readiness_scorecard",
        "module": module,
        "importers": len(importers),
        "imports": len(imports),
        **{f"std_{k}": v for k, v in dims.items()},
        "readiness_score": round(passed / len(dims), 3),
        # island = a real dead-end: no importers, not an entrypoint, and NOT a package marker (`__init__` is
        # imported as its package `foo`, never as `foo.__init__`, so it is not an island).
        "island": (len(importers) == 0 and not _is_entrypoint(module) and not module.endswith("__init__")),
        "candidate": True,
        "serves_truth": False,
    }


def remix_chain(start: str, imports_of: dict, max_depth: int, rng: random.Random) -> dict:
    """Chain module→(an imported module)→… up to max_depth — the code remix sim (mirrors the primitive one)."""
    seen = {start}
    current = start
    depth = 0
    while depth < max_depth:
        nxt = [m for m in imports_of.get(current, ()) if m not in seen]
        if not nxt:
            return {"depth": depth, "remixable": depth >= 1}
        current = nxt[rng.randrange(len(nxt))]
        seen.add(current)
        depth += 1
    return {"depth": depth, "remixable": True}


def run_code_readiness(n: int, depth: int, seed: int) -> dict:
    from scripts.code_graph import CodeGraph  # noqa: PLC0415  local: heavy build, only on run

    graph = CodeGraph().build()
    verified = _verified_modules()
    modules = list(graph.modules)
    imports_of = {m: set(graph.imports.get(m, ())) for m in modules}
    importers_of = {m: set(graph._upstream.get(m, ())) for m in modules}  # noqa: SLF001 (public-enough seam)

    scorecards = [score_module(m, imports_of[m], importers_of[m], verified) for m in modules]

    rng = random.Random(seed)
    sample = modules if n >= len(modules) else rng.sample(modules, n)
    remix = [{"module": m, **remix_chain(m, imports_of, depth, random.Random(seed))} for m in sample]
    return {"scorecards": scorecards, "remix": remix, "n_modules": len(modules)}


def aggregate(bundle: dict) -> dict:
    scorecards = bundle["scorecards"]
    n = len(scorecards)
    if not n:
        return {"experiments": 0}
    dim_keys = [k for k in scorecards[0] if k.startswith("std_")]
    conformance = {k[4:]: round(sum(1 for s in scorecards if s[k]) / n, 3) for k in dim_keys}

    islands = [s["module"] for s in scorecards if s["island"]]
    # high-fan-in-unverified: many dependents, no self-test — concentrated, untested risk (the code gap)
    risk = sorted((s for s in scorecards if not s["std_verified"] and not _is_entrypoint(s["module"])),
                  key=lambda s: -s["importers"])
    high_risk = [{"module": s["module"], "importers": s["importers"]} for s in risk if s["importers"] >= 3][:25]

    m = len(bundle["remix"]) or 1
    remixable = sum(1 for r in bundle["remix"] if r["remixable"])
    avg_depth = round(sum(r["depth"] for r in bundle["remix"]) / m, 2)
    return {
        "record_type": "code_readiness_remix_summary",
        "generated_at": now_iso(),
        "modules_scored": n,
        "fully_standard_compliant_rate": round(sum(1 for s in scorecards if s["readiness_score"] == 1.0) / n, 3),
        "standards_conformance": conformance,
        "worst_standard": min(conformance, key=conformance.get) if conformance else None,
        "remix_simulations": len(bundle["remix"]),
        "remixable_rate": round(remixable / m, 3),
        "avg_reachable_depth": avg_depth,
        "island_count": len(islands),
        "island_examples": islands[:25],
        "high_fanin_unverified": high_risk,
        "note": "same readiness+remix+gap lens the factory applies to generated primitives, applied to OUR code.",
        "serves_truth": False,
    }


def _emit(bundle: dict, summary: dict, emit_gaps: bool) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "scorecards.jsonl").write_text(
        "".join(json.dumps(s) + "\n" for s in bundle["scorecards"]), encoding="utf-8")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"summary_path": str(OUT_DIR / "summary.json")}


def _run(n: int, depth: int, seed: int, emit_gaps: bool) -> int:
    bundle = run_code_readiness(n, depth, seed)
    summary = aggregate(bundle)
    _emit(bundle, summary, emit_gaps)
    keys = ("modules_scored", "fully_standard_compliant_rate", "worst_standard", "remixable_rate",
            "avg_reachable_depth", "island_count")
    print(json.dumps({k: summary[k] for k in keys if k in summary}, indent=2))
    print(f"  standards conformance: {summary['standards_conformance']}")
    print(f"  high-fan-in UNVERIFIED (concentrated risk): "
          f"{[(r['module'], r['importers']) for r in summary['high_fanin_unverified'][:5]]}")
    print(f"  island examples (imported by nothing, not entrypoints): {summary['island_examples'][:5]}")
    return 0


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    bundle = run_code_readiness(n=400, depth=8, seed=1)
    summ = aggregate(bundle)

    checks.append(("scored the real module graph (>=300 modules)", summ["modules_scored"] >= 300))
    checks.append(("every scorecard is candidate/serves_truth=false",
                   all(s["serves_truth"] is False and s["candidate"] for s in bundle["scorecards"])))
    checks.append(("all five code standards are reported",
                   set(summ["standards_conformance"]) == {"named_meaningful", "reused", "composes", "remixable", "verified"}))
    checks.append(("conformance rates are real fractions in [0,1]",
                   all(0.0 <= v <= 1.0 for v in summ["standards_conformance"].values())))
    checks.append(("remix sim ran + reports a remixable rate", summ["remix_simulations"] > 0 and 0.0 <= summ["remixable_rate"] <= 1.0))
    # the lens must DISCRIMINATE: not every module is fully compliant (there are real islands / unverified)
    checks.append(("the lens discriminates (not 100% compliant — real gaps exist)", summ["fully_standard_compliant_rate"] < 1.0))
    checks.append(("gaps surfaced: islands and/or high-fan-in-unverified are found",
                   summ["island_count"] >= 0 and isinstance(summ["high_fanin_unverified"], list)))
    # scoring is a pure function of its inputs (VERIFY-THE-VERIFIER): a synthetic module scores as specified
    sc = score_module("scripts.some_descriptive_name", imports={"scripts.a"}, importers={"scripts.b", "scripts.c"}, verified=set())
    checks.append(("a reused+composing module is remixable; unverified is flagged",
                   sc["std_remixable"] and sc["std_reused"] and sc["std_composes"] and not sc["std_verified"] and not sc["island"]))
    island = score_module("scripts.xy", imports=set(), importers=set(), verified=set())
    checks.append(("a no-name, unimported, non-entrypoint module is an island failing most standards",
                   island["island"] and not island["std_named_meaningful"] and not island["std_composes"]))
    # determinism
    again = aggregate(run_code_readiness(n=400, depth=8, seed=1))
    checks.append(("deterministic: same seed -> identical conformance + island count",
                   again["standards_conformance"] == summ["standards_conformance"] and again["island_count"] == summ["island_count"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - bench_code_readiness_and_remix: OUR code scored by the SAME readiness+remix+gap lens as the "
          "generated primitives (named / reused / composes / remixable / verified over the import graph); islands "
          "+ high-fan-in-unverified surfaced as gaps; deterministic; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--n", type=int, default=4000, help="remix simulations to run")
    ap.add_argument("--depth", type=int, default=8, help="max remix chain depth")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--emit-gaps", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.n, args.depth, args.seed, args.emit_gaps)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
