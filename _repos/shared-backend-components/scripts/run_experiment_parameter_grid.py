#!/usr/bin/env python3
"""scripts.run_experiment_parameter_grid — the systematic PARAMETER-GRID SWEEP over the experiment harnesses.

The path bake-off (``run_path_bakeoff``) races a FIXED set of execution strategies. This is the missing
complement: it sweeps the KNOBS of the measurement harnesses themselves — top-k, intent mode, remix depth —
runs every cell of the grid as a REAL experiment, and ranks them. So "try another way of doing this step" is
no longer a code edit + a guess; it is a grid cell with a receipt. Obeys the MULTI-PATH law: the sweep NEVER
locks in a single setting — it returns the winner PLUS every other cell as a labelled portfolio (the losers
are kept, not discarded), so a later re-run can re-adapt as the corpus changes.

It COMPOSES the existing harnesses (reuse-first — it builds no new measurement):
  * ``scripts.run_token_savings_experiments`` (reuse-vs-rebuild savings + retrieval precision)
  * ``scripts.bench_primitive_readiness_and_remix`` (standards + remixability over the edge graph)

Each grid cell is a real run on a bounded corpus (the grid COMPARES settings; scale is the individual
harness's job via its own --n). Every row is candidate=true / serves_truth=false.

  PYTHONPATH=. python3 scripts/run_experiment_parameter_grid.py --self-test
  PYTHONPATH=. python3 scripts/run_experiment_parameter_grid.py --run [--corpus 4000] [--n 800]
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
import itertools  # noqa: E402
import json  # noqa: E402

from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402
from scripts import run_token_savings_experiments as _ts  # noqa: E402
from scripts import bench_primitive_readiness_and_remix as _rr  # noqa: E402

OUT_DIR = _resource("data") / "dev-intel" / "experiment_parameter_grid"

#: The grid. Each axis is a KNOB we want to experiment with; the sweep runs the cartesian product. Adding a
#: value here = adding an experiment path (the multi-path way to extend — a new row, never an `if`). The
#: `primary` metric names the number a cell is ranked by (higher is better).
GRID = {
    "token_savings_selfretrieval": {
        "harness": "token_savings",
        "axes": {"intent_mode": ["descriptive", "paraphrase"], "k": [3, 5, 10, 20]},
        "primary": "avg_net_saved_tokens",
        "also": ["precision_at_1", "hit_rate", "break_even_precision"],
    },
    "token_savings_external": {  # external intents use different metrics -> its own grid (apples-to-apples)
        "harness": "token_savings_external",
        "axes": {"k": [3, 5, 10, 20]},
        "primary": "avg_net_saved_on_covered",
        "also": ["coverage_rate", "verified_precision_on_labeled"],
    },
    "readiness_remix": {
        "harness": "readiness_remix",
        "axes": {"depth": [2, 4, 6, 10, 15]},
        "primary": "remixable_rate",
        "also": ["avg_reachable_depth", "fully_standard_compliant_rate"],
    },
}


def _cells(axes: dict) -> list[dict]:
    """The cartesian product of the axes → one dict of concrete params per grid cell."""
    keys = list(axes)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(axes[k] for k in keys))]


def _run_token_savings_cell(cards: list, n: int, params: dict) -> dict:
    """One self-retrieval token-savings cell — a REAL run at (intent_mode, k)."""
    rows = _ts.run_experiments(cards, n, params["k"], seed=1, paraphrase=(params["intent_mode"] == "paraphrase"))
    return _ts.aggregate(rows)


def _run_token_savings_external_cell(cards: list, n: int, params: dict) -> dict:
    """One EXTERNAL-intent token-savings cell — a REAL run at k (external metrics: coverage + verified precision)."""
    return _ts.aggregate_external(_ts.run_external(cards, n, params["k"], seed=1))


def _run_readiness_cell(cards: list, n: int, params: dict) -> dict:
    """One readiness/remix grid cell — a REAL run at this remix depth."""
    return _rr.aggregate(_rr.run_readiness(cards, n, params["depth"], seed=1))


#: harness id -> its cell runner (adding a harness = a new row here, never an `if` chain — the multi-path way).
_RUNNERS = {
    "token_savings": _run_token_savings_cell,
    "token_savings_external": _run_token_savings_external_cell,
    "readiness_remix": _run_readiness_cell,
}


def sweep(cards: list, n: int) -> dict:
    """Run every cell of every grid, rank each grid's cells by its primary metric, and return the full
    portfolio (winner + all labelled fallbacks) per grid — never a single locked-in setting."""
    grids = {}
    for name, spec in GRID.items():
        runner = _RUNNERS[spec["harness"]]
        cells = []
        for params in _cells(spec["axes"]):
            summ = runner(cards, n, params)
            metrics = {spec["primary"]: summ.get(spec["primary"])}
            metrics.update({m: summ.get(m) for m in spec["also"]})
            cells.append({"params": params, "metrics": metrics,
                          "primary_value": summ.get(spec["primary"])})
        # rank by the primary metric (higher better); winner + fallbacks = the portfolio (multi-path law)
        ranked = sorted(cells, key=lambda c: (c["primary_value"] is not None, c["primary_value"] or 0), reverse=True)
        grids[name] = {
            "primary_metric": spec["primary"],
            "cells_run": len(ranked),
            "winner": {"params": ranked[0]["params"], "metrics": ranked[0]["metrics"]},
            "portfolio_ranked": ranked,  # ALL cells kept (losers labelled, not discarded)
        }
    return {
        "record_type": "experiment_parameter_grid_summary",
        "generated_at": now_iso(),
        "grids": grids,
        "total_cells": sum(g["cells_run"] for g in grids.values()),
        "note": "winner is a routing DEFAULT, not a lock-in; every cell is kept as a labelled fallback so a "
                "re-run can re-adapt (MULTI-PATH law). candidate evidence.",
        "serves_truth": False,
    }


def _run(corpus: int, n: int) -> int:
    cards = _ts._load_cards(corpus)
    if not cards:
        print("no real cards found (factory scratch may be gitignored on this checkout); run the factory first")
        return 1
    summary = sweep(cards, n)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "grid_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for name, g in summary["grids"].items():
        print(f"=== grid: {name}  (ranked by {g['primary_metric']}, {g['cells_run']} cells) ===")
        print(f"  WINNER: {g['winner']['params']}  ->  {g['winner']['metrics']}")
        for c in g["portfolio_ranked"]:
            print(f"    {c['params']}  ->  {c['metrics']}")
    print(f"\n  total cells: {summary['total_cells']}  |  written: {OUT_DIR / 'grid_summary.json'}")
    return 0


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # cartesian product is correct + deterministic
    cells = _cells({"a": [1, 2], "b": ["x", "y", "z"]})
    checks.append(("cartesian grid enumerates every cell (2×3=6)", len(cells) == 6 and {"a": 2, "b": "z"} in cells))

    # a real sweep over a tiny synthetic corpus (reuses both harnesses' runners) ranks + keeps the portfolio
    def card(pid, inp, out):
        return {"primitive_id": pid, "title": pid, "kind": "route.primitive", "input_edge": inp,
                "output_edge": out, "contract": {"in": inp, "out": out}, "quality_score": 0.8,
                "readiness": "candidate", "effects": ["e"], "serves_truth": False, "blackbox": pid * 12}
    corpus = [card("prim:aa11aa11aa11", "Raw", "Parsed"), card("prim:bb22bb22bb22", "Parsed", "Norm"),
              card("prim:cc33cc33cc33", "Norm", "Scored"), card("prim:dd44dd44dd44", "Screen", "SanctionsHit")]
    summ = sweep(corpus, n=len(corpus))

    checks.append(("all three grids ran their cells (8 + 4 + 5 = 17)",
                   set(summ["grids"]) == {"token_savings_selfretrieval", "token_savings_external", "readiness_remix"}
                   and summ["grids"]["token_savings_selfretrieval"]["cells_run"] == 8
                   and summ["grids"]["token_savings_external"]["cells_run"] == 4
                   and summ["grids"]["readiness_remix"]["cells_run"] == 5))
    checks.append(("each grid returns a WINNER + the full ranked portfolio (losers kept, not discarded)", all(
        g.get("winner") and len(g["portfolio_ranked"]) == g["cells_run"] for g in summ["grids"].values())))
    checks.append(("winner is the top of the ranking by the primary metric", all(
        g["portfolio_ranked"][0]["params"] == g["winner"]["params"] for g in summ["grids"].values())))
    checks.append(("portfolio is sorted best-first on the primary metric", all(
        [c["primary_value"] or 0 for c in g["portfolio_ranked"]]
        == sorted([c["primary_value"] or 0 for c in g["portfolio_ranked"]], reverse=True)
        for g in summ["grids"].values())))
    # determinism (seed fixed inside the runners) — same corpus -> identical winner
    again = sweep(corpus, n=len(corpus))
    checks.append(("deterministic: same corpus -> identical winners", all(
        again["grids"][k]["winner"]["params"] == summ["grids"][k]["winner"]["params"] for k in summ["grids"])))
    checks.append(("candidate / serves_truth=false", summ["serves_truth"] is False)  # noqa: E712 (explicit)
                  )

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - run_experiment_parameter_grid: sweeps the harness knobs (intent mode / k / remix depth) as a "
          "cartesian grid of REAL runs, ranks each grid by its primary metric, and returns winner + the full "
          "labelled portfolio (MULTI-PATH: losers kept for re-adaptation); deterministic; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--corpus", type=int, default=4000, help="cards per cell (comparison, not scale)")
    ap.add_argument("--n", type=int, default=800, help="experiments per cell")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.corpus, args.n)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
