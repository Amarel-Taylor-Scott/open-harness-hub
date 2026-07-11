#!/usr/bin/env python3
"""scripts.run_code_execution_benchmark — the HONEST code-execution benchmark: does the composed route actually RUN
and produce the CORRECT output (vs merely being retrieved / vs an ESTIMATED savings number)?

The proven-count red-team (2026-07-03) found the factory reports "estimated tokens saved" and "retrievable routes"
but never EXECUTES a composed route end-to-end to confirm it produces the right bytes. This module closes that gap:
it defines ~20+ EXECUTABLE route tasks — each a {task_id, task_class, input_fixture, expected_output, route} where
`route` is an ordered list of REAL mutators from scripts.mutator_registry — and it ACTUALLY chains apply_mutator over
the route IN-PROCESS, then asserts executed_output == expected_output. A route that passes is an *executed proof*
(serves_truth=true is then correct + required per repo law); a route that does not stays candidate.

What this proves that retrieval/estimation cannot: the composed route RUNS. Multi-step routes (e.g. type_cast ->
field_rename -> output_receipt_wrapper) exercise composition correctness — the output of step N really is a valid input
to step N+1. A set of deliberately-broken NEGATIVE CONTROLS (wrong expected_output) MUST fail, proving the equality
check is real and not a rubber stamp.

Honesty rules kept: `tokens_saved_vs_handwritten` is an ESTIMATE (labeled `is_estimate: true`), built from a single
named constant — NOT a measured number; the pass rates, route counts, and route lengths are COMPUTED from the task
manifest, never typed. Deterministic body (no wall-clock/RNG; --run takes a fixed `now`). All manifest/estimate rows
are candidate=true/serves_truth=false; only an executed PASSING route carries serves_truth=true. ADD-ONLY module —
imports existing machinery, edits nothing. CLI: --self-test (pure/offline) | --run [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# ── REQUIRED reuse (stable siblings; import directly) ─────────────────────────────────────────────────────────────
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _hash,
    apply_mutator,
    run_primitive_proof,
)

# ── retrieval-context reuse (stable; the plane under which routes are composed/retrieved) ─────────────────────────
try:
    from scripts.build_retrieval_backend_portfolio import (  # noqa: E402
        dim_compatible,
        resolve_active_backends,
    )
except Exception:  # pragma: no cover - defensive
    resolve_active_backends = None  # type: ignore[assignment]
    dim_compatible = None  # type: ignore[assignment]

# ── OPTIONAL reuse (built by a concurrent workflow; import must NEVER break self-test if absent) ──────────────────
_OPTIONAL: dict[str, Any] = {}
for _mod, _name in (
    ("scripts.primitive_runtime", "compose_solution"),
    ("scripts.build_primitive_search_index", "fast_search"),
    ("scripts.build_edge_type_retrofit", "canonicalize_edge"),
    ("scripts.check_primitive_composability", "composability_report"),
    ("scripts.prove_leaf_primitives", "proven_primitive_index"),
):
    try:
        _module = __import__(_mod, fromlist=[_name])
        _OPTIONAL[_name] = getattr(_module, _name, None)
    except Exception:  # pragma: no cover - concurrent module may be absent/partial
        _OPTIONAL[_name] = None

OUT_DIR = _resource("data") / "dev-intel" / "code_execution_benchmark"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: ESTIMATE ONLY — median tokens we judge it would take to hand-write ONE transform step (parse + edit + reserialize +
#: a receipt). This is an editorial estimate for the savings headline, NOT a measurement; the pass rates and route
#: counts below are computed, never estimated.
ESTIMATED_TOKENS_TO_HANDWRITE_ONE_TRANSFORM = 40


def _idem_key(user: str, op: str) -> str:
    """Reconstruct idempotency_wrapper's deterministic key so a route's expected_output can be declared, not run."""
    return hashlib.sha256(f"{user}|{op}".encode()).hexdigest()[:24]


def _receipt_expected(inner: Any) -> dict[str, Any]:
    """The exact shape output_receipt_wrapper emits, declared via the canonical hasher (single source)."""
    return {"output": inner, "receipt": {"output_hash": _hash(inner), "verified_first": True}}


# ── EXECUTABLE route tasks. `route` steps are [mutator_name, kwargs]; the output of step N feeds step N+1. ─────────
# expected_output is HAND-DECLARED (not produced by running the route) so executed==expected is a real check.
ROUTE_TASKS: list[dict[str, Any]] = [
    # ---- single-step ----
    {"task_id": "rename_basic", "task_class": "rename",
     "input_fixture": {"a": 1, "b": 2}, "route": [["field_rename", {"mapping": {"a": "x"}}]],
     "expected_output": {"x": 1, "b": 2}},
    {"task_id": "rename_multi_field", "task_class": "rename",
     "input_fixture": {"first": "A", "last": "B", "age": 30},
     "route": [["field_rename", {"mapping": {"first": "given_name", "last": "family_name"}}]],
     "expected_output": {"given_name": "A", "family_name": "B", "age": 30}},
    {"task_id": "project_keep_two", "task_class": "project",
     "input_fixture": {"a": 1, "b": 2, "c": 3}, "route": [["field_project", {"keep": ["a", "c"]}]],
     "expected_output": {"a": 1, "c": 3}},
    {"task_id": "project_drop_secret", "task_class": "project",
     "input_fixture": {"id": "x", "secret": "s", "name": "n"}, "route": [["field_project", {"keep": ["id", "name"]}]],
     "expected_output": {"id": "x", "name": "n"}},
    {"task_id": "cast_int", "task_class": "cast",
     "input_fixture": {"n": "5"}, "route": [["type_cast", {"casts": {"n": "int"}}]],
     "expected_output": {"n": 5}},
    {"task_id": "cast_multi", "task_class": "cast",
     "input_fixture": {"n": "5", "f": "2.5", "flag": 1},
     "route": [["type_cast", {"casts": {"n": "int", "f": "float", "flag": "bool"}}]],
     "expected_output": {"n": 5, "f": 2.5, "flag": True}},
    {"task_id": "wrap_envelope", "task_class": "envelope",
     "input_fixture": {"p": 1}, "route": [["envelope_wrap", {"policy": {"pol": "x"}}]],
     "expected_output": {"payload": {"p": 1}, "policy": {"pol": "x"}, "envelope_version": 1}},
    {"task_id": "unwrap_envelope", "task_class": "envelope",
     "input_fixture": {"payload": {"p": 1}, "policy": {"pol": "x"}, "envelope_version": 1},
     "route": [["envelope_unwrap", {}]], "expected_output": {"p": 1}},
    {"task_id": "serialize_row", "task_class": "serialize",
     "input_fixture": {"z": 9}, "route": [["row_to_json", {}]], "expected_output": '{"z": 9}'},
    {"task_id": "parse_json", "task_class": "serialize",
     "input_fixture": '{"z": 9}', "route": [["json_to_row", {}]], "expected_output": {"z": 9}},
    {"task_id": "validate_ok", "task_class": "validate",
     "input_fixture": {"name": "n", "email": "e"}, "route": [["schema_validator_inserter", {"required": ["name", "email"]}]],
     "expected_output": {"name": "n", "email": "e",
                         "_validation": {"required": ["name", "email"], "missing": [], "valid": True}}},
    {"task_id": "validate_missing", "task_class": "validate",
     "input_fixture": {"name": "n"}, "route": [["schema_validator_inserter", {"required": ["name", "email"]}]],
     "expected_output": {"name": "n",
                         "_validation": {"required": ["name", "email"], "missing": ["email"], "valid": False}}},
    {"task_id": "idempotency_key", "task_class": "idempotency",
     "input_fixture": {"user": "u1", "op": "pay"}, "route": [["idempotency_wrapper", {"key_fields": ["user", "op"]}]],
     "expected_output": {"user": "u1", "op": "pay", "idempotency_key": _idem_key("u1", "pay")}},
    {"task_id": "dedupe_by_k", "task_class": "dedupe",
     "input_fixture": [{"k": 1, "id": "a"}, {"k": 1, "id": "b"}, {"k": 2, "id": "c"}],
     "route": [["dedupe_by_key", {"key": "k"}]],
     "expected_output": [{"k": 1, "id": "a"}, {"k": 2, "id": "c"}]},
    {"task_id": "receipt_wrap", "task_class": "receipt",
     "input_fixture": {"result": 42}, "route": [["output_receipt_wrapper", {}]],
     "expected_output": _receipt_expected({"result": 42})},
    # ---- multi-step (composition correctness: step N output IS step N+1 input) ----
    {"task_id": "rename_then_receipt", "task_class": "multi_step",
     "input_fixture": {"a": 1, "b": 2},
     "route": [["field_rename", {"mapping": {"a": "x"}}], ["output_receipt_wrapper", {}]],
     "expected_output": _receipt_expected({"x": 1, "b": 2})},
    {"task_id": "cast_rename_receipt", "task_class": "multi_step",
     "input_fixture": {"count": "10"},
     "route": [["type_cast", {"casts": {"count": "int"}}], ["field_rename", {"mapping": {"count": "total"}}],
               ["output_receipt_wrapper", {}]],
     "expected_output": _receipt_expected({"total": 10})},
    {"task_id": "rename_then_serialize", "task_class": "multi_step",
     "input_fixture": {"a": 1}, "route": [["field_rename", {"mapping": {"a": "x"}}], ["row_to_json", {}]],
     "expected_output": '{"x": 1}'},
    {"task_id": "project_then_rename", "task_class": "multi_step",
     "input_fixture": {"a": 1, "b": 2, "c": 3},
     "route": [["field_project", {"keep": ["a", "b"]}], ["field_rename", {"mapping": {"a": "x"}}]],
     "expected_output": {"x": 1, "b": 2}},
    {"task_id": "wrap_then_unwrap_roundtrip", "task_class": "multi_step",
     "input_fixture": {"p": 1}, "route": [["envelope_wrap", {"policy": {"pol": "x"}}], ["envelope_unwrap", {}]],
     "expected_output": {"p": 1}},
    {"task_id": "serialize_then_parse_roundtrip", "task_class": "multi_step",
     "input_fixture": {"z": 9}, "route": [["row_to_json", {}], ["json_to_row", {}]],
     "expected_output": {"z": 9}},
    {"task_id": "validate_then_receipt", "task_class": "multi_step",
     "input_fixture": {"name": "n", "email": "e"},
     "route": [["schema_validator_inserter", {"required": ["name", "email"]}], ["output_receipt_wrapper", {}]],
     "expected_output": _receipt_expected(
         {"name": "n", "email": "e",
          "_validation": {"required": ["name", "email"], "missing": [], "valid": True}})},
    {"task_id": "cast_then_validate", "task_class": "multi_step",
     "input_fixture": {"age": "30"},
     "route": [["type_cast", {"casts": {"age": "int"}}], ["schema_validator_inserter", {"required": ["age"]}]],
     "expected_output": {"age": 30, "_validation": {"required": ["age"], "missing": [], "valid": True}}},
]

# ── NEGATIVE CONTROLS: identical shape but a WRONG expected_output — these MUST fail, proving the check is real. ───
NEGATIVE_CONTROLS: list[dict[str, Any]] = [
    {"task_id": "neg_wrong_rename", "task_class": "rename",
     "input_fixture": {"a": 1}, "route": [["field_rename", {"mapping": {"a": "x"}}]],
     "expected_output": {"WRONG": 999}},
    {"task_id": "neg_wrong_multi", "task_class": "multi_step",
     "input_fixture": {"count": "10"},
     "route": [["type_cast", {"casts": {"count": "int"}}], ["field_rename", {"mapping": {"count": "total"}}]],
     "expected_output": {"total": "10"}},  # still a string -> type_cast makes it int 10, so this fails (real check)
]


def _normalize_step(step: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(step, str):
        return step, {}
    if isinstance(step, (list, tuple)):
        name = step[0]
        kwargs = step[1] if len(step) > 1 and step[1] else {}
        return name, dict(kwargs)
    if isinstance(step, dict):
        return step["mutator"], dict(step.get("args", {}))
    raise TypeError(f"unrecognized route step: {step!r}")


def execute_route(input_fixture: Any, route: list[Any]) -> tuple[Any, list[dict[str, Any]], str | None]:
    """ACTUALLY run the route in-process: chain apply_mutator, feeding each step's output into the next.

    Returns (executed_output, step_receipts, error). `error` is a string if any step raised (route did not run),
    else None. A deep copy guards the declared fixtures from in-place mutation across tasks.
    """
    payload = copy.deepcopy(input_fixture)
    receipts: list[dict[str, Any]] = []
    for step in route:
        name, kwargs = _normalize_step(step)
        try:
            payload, rec = apply_mutator(name, payload, **kwargs)
        except Exception as exc:  # noqa: BLE001 - a raising step means the route did NOT execute
            return None, receipts, f"{name}: {type(exc).__name__}: {exc}"
        receipts.append(rec)
    return payload, receipts, None


def score_task(task: dict[str, Any]) -> dict[str, Any]:
    """Run one task and produce an executed-proof receipt. A PASS is an executed proof -> serves_truth=true."""
    executed, receipts, error = execute_route(task["input_fixture"], task["route"])
    executed_ok = error is None
    passed = executed_ok and executed == task["expected_output"]
    return {
        "record_type": "code_execution_route_result",
        "task_id": task["task_id"], "task_class": task["task_class"],
        "route": [_normalize_step(s)[0] for s in task["route"]], "route_length": len(task["route"]),
        "executed": executed_ok, "execution_error": error,
        "output_matches_expected": passed,
        "executed_output_hash": _hash(executed) if executed_ok else None,
        "expected_output_hash": _hash(task["expected_output"]),
        # An executed, output-correct route IS an executed proof -> serves_truth flips true (repo law); else candidate.
        "verification_level": "L7_executed_route_proof" if passed else "L4_executed_but_unverified",
        "candidate": not passed, "serves_truth": bool(passed),
    }


def run_benchmark() -> dict[str, Any]:
    """Execute every real route + every negative control; compute (never type) all pass rates and route stats."""
    results = [score_task(t) for t in ROUTE_TASKS]
    controls = [score_task(t) for t in NEGATIVE_CONTROLS]

    total = len(results)
    passes = sum(1 for r in results if r["output_matches_expected"])
    executed_n = sum(1 for r in results if r["executed"])
    multi = [r for r in results if r["route_length"] >= 2]

    per_class: dict[str, dict[str, int]] = {}
    for r in results:
        c = per_class.setdefault(r["task_class"], {"passed": 0, "total": 0})
        c["total"] += 1
        c["passed"] += int(r["output_matches_expected"])
    per_class_rate = {
        c: {"passed": v["passed"], "total": v["total"], "pass_rate": round(v["passed"] / v["total"], 4)}
        for c, v in sorted(per_class.items())
    }

    mean_route_length = round(sum(r["route_length"] for r in results) / total, 4) if total else 0.0
    controls_all_failed = all(not c["output_matches_expected"] for c in controls)

    # honest ESTIMATE (labeled): tokens we judge saved by NOT hand-writing each passing route's transforms.
    saved_steps = sum(r["route_length"] for r in results if r["output_matches_expected"])
    tokens_saved_estimate = saved_steps * ESTIMATED_TOKENS_TO_HANDWRITE_ONE_TRANSFORM

    return {
        "results": results, "controls": controls,
        "summary": {
            "total_routes": total,
            "routes_executed": executed_n,
            "routes_passed": passes,
            "exec_pass_rate": round(passes / total, 4) if total else 0.0,
            "multi_step_routes": len(multi),
            "multi_step_passed": sum(1 for r in multi if r["output_matches_expected"]),
            "mean_route_length": mean_route_length,
            "per_class_pass_rate": per_class_rate,
            "negative_controls": len(controls),
            "negative_controls_all_failed": controls_all_failed,
            "tokens_saved_vs_handwritten": {
                "value": tokens_saved_estimate,
                "is_estimate": True,
                "basis": f"{saved_steps} passing transform-steps * "
                         f"{ESTIMATED_TOKENS_TO_HANDWRITE_ONE_TRANSFORM} est tokens/step (editorial estimate; "
                         "divide-by-1 composed cost). NOT a measurement — the pass rates are the measured signal.",
            },
        },
    }


def _retrieval_context() -> dict[str, Any]:
    """Reuse the retrieval-backend resolver so the report records the plane under which routes are composed."""
    if resolve_active_backends is None:
        return {"available": False}
    try:
        active = resolve_active_backends()
        emb = active.get("embedder", {})
        return {
            "available": True,
            "active_embedder": emb.get("backend_id"),
            "active_embedder_dim": emb.get("dim"),
            "active_search_method": active.get("search_method", {}).get("method_id"),
            "dim_self_consistent": bool(dim_compatible and dim_compatible(emb.get("dim", 0), emb.get("dim", 0))),
        }
    except Exception:  # pragma: no cover
        return {"available": False}


def build_report(*, date: str) -> dict[str, Any]:
    bench = run_benchmark()
    s = bench["summary"]
    canonical = "\n".join(
        json.dumps(r, sort_keys=True, ensure_ascii=False, default=str)
        for r in bench["results"] + bench["controls"]
    )
    return {
        "record_type": "code_execution_benchmark_report",
        "report_id": "code-execution-benchmark",
        "generator": "scripts/run_code_execution_benchmark.py",
        "generated_utc": date,
        "row_counts": {"route_tasks": len(bench["results"]), "negative_controls": len(bench["controls"])},
        "total_rows": len(bench["results"]) + len(bench["controls"]),
        "mutators_available": sorted(MUTATOR_REGISTRY),
        "summary": s,
        "retrieval_context": _retrieval_context(),
        "optional_integrations_available": {k: (v is not None) for k, v in _OPTIONAL.items()},
        "results": bench["results"],
        "controls": bench["controls"],
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def _render_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# Code-Execution Benchmark",
        "",
        f"_Generated: {report['generated_utc']} · generator: `{report['generator']}`_",
        "",
        "The honest test: does the COMPOSED route actually RUN in-process and produce the CORRECT output — vs merely "
        "being retrieved, vs an ESTIMATED savings number. Each route chains real mutators from "
        "`scripts.mutator_registry`; a passing route is an executed proof.",
        "",
        "## Summary (computed, not typed)",
        "",
        f"- Total routes: **{s['total_routes']}**",
        f"- Routes executed (no exception): **{s['routes_executed']}**",
        f"- Routes passed (output == expected): **{s['routes_passed']}**",
        f"- **exec_pass_rate: {s['exec_pass_rate']}**",
        f"- Multi-step routes: **{s['multi_step_routes']}** (passed: {s['multi_step_passed']})",
        f"- Mean route length: **{s['mean_route_length']}**",
        f"- Negative controls: **{s['negative_controls']}** · all failed as designed: "
        f"**{s['negative_controls_all_failed']}**",
        "",
        "### tokens_saved_vs_handwritten (ESTIMATE — not a measurement)",
        "",
        f"- value: **{s['tokens_saved_vs_handwritten']['value']}** · `is_estimate: "
        f"{s['tokens_saved_vs_handwritten']['is_estimate']}`",
        f"- basis: {s['tokens_saved_vs_handwritten']['basis']}",
        "",
        "## Per-class pass rate",
        "",
        "| task_class | passed | total | pass_rate |",
        "| --- | --- | --- | --- |",
    ]
    for c, v in s["per_class_pass_rate"].items():
        lines.append(f"| {c} | {v['passed']} | {v['total']} | {v['pass_rate']} |")
    lines += ["", "## Routes", "", "| task_id | class | route | len | executed | passed | serves_truth |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in report["results"]:
        lines.append(
            f"| {r['task_id']} | {r['task_class']} | {' → '.join(r['route'])} | {r['route_length']} | "
            f"{r['executed']} | {r['output_matches_expected']} | {r['serves_truth']} |")
    lines += ["", "## Negative controls (MUST all fail)", "",
              "| task_id | passed (should be False) |", "| --- | --- |"]
    for c in report["controls"]:
        lines.append(f"| {c['task_id']} | {c['output_matches_expected']} |")
    lines.append("")
    return "\n".join(lines)


def write_report(*, date: str) -> dict[str, Any]:
    report = build_report(date=date)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"exec_report_{date_slug(date)}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / f"exec_report_{date_slug(date)}.md").write_text(_render_md(report), encoding="utf-8")
    return report


def date_slug(date: str) -> str:
    """'2026-07-03T00:00:00Z' or '2026-07-03' -> '2026-07-03' for the filename."""
    return date.split("T", 1)[0]


def self_test() -> int:
    checks: list[tuple[str, bool]] = []
    bench = run_benchmark()
    s = bench["summary"]

    checks.append((">=20 route tasks defined", len(ROUTE_TASKS) >= 20))
    checks.append(("every route actually EXECUTES (no exception)", all(r["executed"] for r in bench["results"])))
    checks.append(("exec_pass_rate computes to a float in [0,1]", isinstance(s["exec_pass_rate"], float)
                   and 0.0 <= s["exec_pass_rate"] <= 1.0))
    checks.append(("all real routes PASS (executed_output == expected_output)", s["exec_pass_rate"] == 1.0))
    checks.append(("multi-step routes exist and pass",
                   s["multi_step_routes"] >= 5 and s["multi_step_passed"] == s["multi_step_routes"]))
    checks.append(("mean_route_length computed > 1", s["mean_route_length"] > 1.0))
    checks.append(("per-class pass_rate computed for every class",
                   set(s["per_class_pass_rate"]) == {t["task_class"] for t in ROUTE_TASKS}))
    checks.append(("multi_step is a real class in the per-class table", "multi_step" in s["per_class_pass_rate"]))

    # THE key honesty check: a deliberately-broken route (wrong expected) FAILS — the equality check is real.
    checks.append(("negative controls all FAIL (the check is not a rubber stamp)",
                   s["negative_controls_all_failed"] and s["negative_controls"] >= 2))
    neg = score_task(NEGATIVE_CONTROLS[0])
    checks.append(("a wrong-expected route stays candidate (serves_truth False)",
                   neg["output_matches_expected"] is False and neg["serves_truth"] is False))

    # a PASSING executed route carries serves_truth=true (repo law: executed proof only).
    a_pass = next(r for r in bench["results"] if r["output_matches_expected"])
    checks.append(("a passing executed route is serves_truth=true (executed proof)",
                   a_pass["serves_truth"] is True and a_pass["verification_level"] == "L7_executed_route_proof"))

    # composition correctness: a specific 3-step route lands the exact bytes.
    out, _rec, err = execute_route({"count": "10"},
                                   [["type_cast", {"casts": {"count": "int"}}],
                                    ["field_rename", {"mapping": {"count": "total"}}],
                                    ["output_receipt_wrapper", {}]])
    checks.append(("3-step composition produces correct chained output",
                   err is None and out == _receipt_expected({"total": 10})))

    # tokens_saved is clearly an ESTIMATE (labeled), not passed off as measured.
    checks.append(("tokens_saved is labeled an estimate", s["tokens_saved_vs_handwritten"]["is_estimate"] is True))

    # genuine reuse of run_primitive_proof on a single-step route (integration with the proof-runner).
    rp = run_primitive_proof("prim:exec:field_rename", "field_rename", {"a": 1}, {"x": 1},
                             mutator_args={"mapping": {"a": "x"}})
    checks.append(("run_primitive_proof reused end-to-end (single-step route promotes on pass)",
                   rp["serves_truth"] is True))

    # report builds + counts come from the manifest, not prose.
    report = build_report(date="2026-07-03T00:00:00Z")
    checks.append(("report total_rows equals routes + controls (counts from manifest)",
                   report["total_rows"] == len(ROUTE_TASKS) + len(NEGATIVE_CONTROLS)
                   and report["row_counts"]["route_tasks"] == len(ROUTE_TASKS)))
    checks.append(("report is deterministic (same content_sha256 on rebuild)",
                   build_report(date="2026-07-03T00:00:00Z")["content_sha256"] == report["content_sha256"]))
    checks.append(("report boundary held (manifest candidate/serves_truth False)",
                   report["candidate"] is True and report["serves_truth"] is False))
    checks.append(("optional concurrent imports are graceful (dict of bools)",
                   all(isinstance(v, bool) for v in report["optional_integrations_available"].values())))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - run_code_execution_benchmark:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - run_code_execution_benchmark: {len(ROUTE_TASKS)} executable routes actually RAN in-process "
          f"(exec_pass_rate={s['exec_pass_rate']}, {s['multi_step_routes']} multi-step), "
          f"{s['negative_controls']} negative controls all failed (the equality check is real), passing routes carry "
          "serves_truth=true as executed proofs, and tokens_saved is a labeled ESTIMATE. Composition correctness "
          "proven — routes RUN, not just retrieve.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--date", default="2026-07-03T00:00:00Z",
                        help="fixed timestamp for deterministic output (no wall-clock)")
    args = parser.parse_args(argv)
    if args.run:
        report = write_report(date=args.date)
        printable = {k: v for k, v in report.items() if k not in ("results", "controls", "content_sha256")}
        print(json.dumps(printable, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
