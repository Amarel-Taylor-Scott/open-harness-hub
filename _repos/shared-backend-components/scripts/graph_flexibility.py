#!/usr/bin/env python3
"""scripts.graph_flexibility — ENFORCE the path-graph's flexibility invariants as a gated conformance test, so
the promise "you can add a stage / add an option / turn things on and off with no rewrite" cannot silently
regress. It mutates a SNAPSHOT of the live graph (restored after) exactly the way a real edit would, and asserts
the graph adapts every time. Wired into the proof umbrella → this goes RED the moment a hardcoded count, a
skipped stage, or a broken option contract creeps in.

Invariants enforced:
  1. ADD OPTION      — a new option row grows the graph, enumerates, and runs.
  2. INSERT STAGE    — a new stage dropped BETWEEN two existing stages runs in order, enumerates, and is skippable.
  3. TOGGLE ON/OFF   — disabling an option shrinks the graph + drops it from enumeration; re-enabling restores it.
  4. COMPUTED COUNTS — graph_summary total == product of enabled option counts == enumerate length (no literal).
  5. CONTRACT        — every option is a contract-substitutable ``fn(ctx, llm) -> ctx`` with a declared ``kind``.
  6. ROUTABILITY     — every stage is skippable (has none/skip) OR is a declared MANDATORY stage (pick-one).

serves_truth=false — a conformance receipt is a measurement, never truth.

    PYTHONPATH=. python3 scripts/graph_flexibility.py --self-test
    PYTHONPATH=. python3 scripts/graph_flexibility.py --report
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import contextlib  # noqa: E402
import copy  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Iterator  # noqa: E402

from scripts import pipeline_path_graph as _g  # noqa: E402  the graph under test

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: stages with NO none/skip option — you MUST pick one (they are load-bearing: you can't retrieve/fuse nothing).
#: A stage outside this set MUST be skippable. This is the documented, enforced routability contract.
MANDATORY_STAGES: frozenset[str] = frozenset({"preprocess", "search", "fuse"})

_CARDS = [
    {"primitive_id": "p:dedup", "title": "Deduplicate records", "blackbox": "Remove duplicate rows.",
     "input_edge": "Batch", "output_edge": "DedupedBatch", **BOUNDARY},
    {"primitive_id": "p:store", "title": "Store records", "blackbox": "Write records to a datastore.",
     "input_edge": "DedupedBatch", "output_edge": "Stored", **BOUNDARY},
]


@contextlib.contextmanager
def _graph_sandbox() -> Iterator[None]:
    """Snapshot STAGES + STAGE_OPTIONS and restore on exit, so a conformance mutation never leaks to other
    tests. deepcopy keeps function refs (functions are atomic to copy) while giving a fresh dict structure."""
    saved_stages, saved_opts = _g.STAGES, _g.STAGE_OPTIONS
    _g.STAGES = tuple(saved_stages)
    _g.STAGE_OPTIONS = copy.deepcopy(saved_opts)
    try:
        yield
    finally:
        _g.STAGES, _g.STAGE_OPTIONS = saved_stages, saved_opts


def _one_per_stage() -> dict[str, str]:
    """A valid full path = the first enabled option of every stage."""
    return {s: _g._enabled_options(s)[0] for s in _g.STAGES}


def conformance() -> dict[str, Any]:
    """Run every flexibility invariant against a sandboxed graph; return a structured pass/fail receipt."""
    results: list[dict[str, Any]] = []

    def _check(name: str, ok: bool, detail: str = "") -> None:
        results.append({"invariant": name, "pass": bool(ok), "detail": detail})

    base_total = _g.graph_summary()["total_paths"]

    # 1) ADD OPTION — a new row grows the graph, enumerates, runs
    with _graph_sandbox():
        _g.STAGE_OPTIONS["rerank"]["conformance_probe"] = {"fn": lambda ctx, llm: ctx, "kind": "heuristic"}
        grew = _g.graph_summary()["total_paths"] > base_total
        path = {**_one_per_stage(), "rerank": "conformance_probe"}
        ran = _g.run_path("dedupe the rows", _CARDS, path)
        enumerable = any(p.get("rerank") == "conformance_probe" for p in _g.enumerate_paths())
        _check("add_option_grows_enumerates_runs",
               grew and enumerable and any(t["option"] == "conformance_probe" for t in ran["trace"]),
               f"total {base_total}->{_g.graph_summary()['total_paths']}")

    # 2) INSERT STAGE between two existing stages — runs in order, enumerates, skippable
    with _graph_sandbox():
        _g.STAGE_OPTIONS["probe_stage"] = {"none": {"fn": lambda ctx, llm: ctx, "kind": "deterministic"},
                                           "mark": {"fn": lambda ctx, llm: {**ctx, "probed": True},
                                                    "kind": "heuristic"}}
        stages = list(_g.STAGES)
        stages.insert(stages.index("expand"), "probe_stage")  # squarely BETWEEN preprocess and expand
        _g.STAGES = tuple(stages)
        doubled = _g.graph_summary()["total_paths"] == base_total * 2
        through = _g.run_path("dedupe the rows", _CARDS, {**_one_per_stage(), "probe_stage": "mark"})
        order = [t["stage"] for t in through["trace"]]
        in_order = ("probe_stage" in order
                    and order.index("preprocess") < order.index("probe_stage") < order.index("expand"))
        around = _g.run_path("dedupe the rows", _CARDS,
                             {k: v for k, v in _one_per_stage().items() if k != "probe_stage"})
        skippable = "probe_stage" not in [t["stage"] for t in around["trace"]]
        enumerable = all("probe_stage" in p for p in _g.enumerate_paths()[:20])
        _check("insert_stage_adapts_order_enumerate_skip", doubled and in_order and skippable and enumerable,
               f"stages -> {list(_g.STAGES)}")

    # 3) TOGGLE ON/OFF — disable shrinks + drops from enumeration; enable restores
    with _graph_sandbox():
        before = _g.graph_summary()["total_paths"]
        _g.set_enabled("fuse", "combmnz", False)
        off = _g.graph_summary()["total_paths"]
        dropped = all(p.get("fuse") != "combmnz" for p in _g.enumerate_paths())
        _g.set_enabled("fuse", "combmnz", True)
        _check("toggle_off_shrinks_drops_and_on_restores",
               off < before and dropped and _g.graph_summary()["total_paths"] == before,
               f"{before}->{off}->{_g.graph_summary()['total_paths']}")

    # 4) COMPUTED COUNTS — three independent computations agree, no hardcoded literal
    expected = 1
    for s in _g.STAGES:
        expected *= len(_g._enabled_options(s))
    _check("counts_computed_and_consistent",
           _g.graph_summary()["total_paths"] == expected == len(_g.enumerate_paths()),
           f"total={expected}")

    # 5) CONTRACT — every option is a callable fn(ctx, llm)->ctx with a declared kind
    contract_ok, bad = True, []
    for stage in _g.STAGES:
        for name, spec in _g.STAGE_OPTIONS[stage].items():
            fn = spec.get("fn")
            has_kind = isinstance(spec.get("kind"), str)
            try:
                arity = len(inspect.signature(fn).parameters)
            except (TypeError, ValueError):
                arity = -1
            if not (callable(fn) and has_kind and arity == 2):
                contract_ok = False
                bad.append(f"{stage}/{name}")
    _check("every_option_is_contract_substitutable_fn_ctx_llm", contract_ok, f"violations={bad[:5]}")

    # 6) ROUTABILITY — every stage is skippable (none/skip) OR a declared MANDATORY pick-one stage
    route_ok, offenders = True, []
    for stage in _g.STAGES:
        skippable = any(o in _g.STAGE_OPTIONS[stage] for o in ("none", "skip"))
        if not skippable and stage not in MANDATORY_STAGES:
            route_ok = False
            offenders.append(stage)
    _check("every_stage_skippable_or_declared_mandatory", route_ok, f"offenders={offenders}")

    passed = all(r["pass"] for r in results)
    return {"record_type": "graph_flexibility_conformance", "all_pass": passed,
            "invariants_checked": len(results), "results": results,
            "graph": {"stages": len(_g.STAGES), "total_paths": base_total,
                      "mandatory_stages": sorted(MANDATORY_STAGES)}, **BOUNDARY}


def _self_test() -> int:
    rec = conformance()
    for r in rec["results"]:
        print(f"  [{'ok' if r['pass'] else 'FAIL'}] {r['invariant']}  {r['detail']}")
    # the graph is left UNMUTATED by the conformance run (sandbox restored)
    unchanged = _g.graph_summary()["total_paths"] == rec["graph"]["total_paths"]
    print(f"  [{'ok' if unchanged else 'FAIL'}] the live graph is unchanged after conformance (sandbox restored)")
    if not (rec["all_pass"] and unchanged):
        print("\nFAILURES in graph flexibility conformance")
        return 1
    print(f"\nPASS - graph_flexibility: all {rec['invariants_checked']} flexibility invariants ENFORCED — add "
          f"option, insert stage mid-pipeline, toggle on/off, computed counts, contract-substitutable options, "
          f"and routability (skippable-or-mandatory) all hold against a sandboxed graph, and the live graph is "
          f"restored untouched. Adding a stage/option/primitive or turning things off cannot silently regress. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true", help="print the full conformance receipt")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.report:
        print(json.dumps(conformance(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
