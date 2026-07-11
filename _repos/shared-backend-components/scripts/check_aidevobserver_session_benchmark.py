"""Validate AIDevObserver session-review benchmark fixtures.

These benchmark fixtures are candidate evidence only. The checker validates
fixture shape, transcript links, current reviewer behavior, token-estimate
presence, and candidate-only posture. It does not claim the current reviewer
already satisfies every target expected finding.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
sys.path.insert(0, str(REPO))

from scripts.check_aidevobserver_example_sessions import (  # noqa: E402
    EXAMPLES_DIR,
    MANIFEST_PATH,
    has_secret_like_text,
    parse_text_transcript,
)
from src.teleon.observer.review import review_session  # noqa: E402

BENCHMARK_PATH = _resource("fixtures") / "benchmarks" / "aidevobserver_session_review_v0" / "kaggle_public_project_cases.json"
ALLOWED_TOKEN_ESTIMATE_BASES = {
    "deterministic_proxy_from_recreated_helper_count",
    "tokenizer_estimate_from_transcript",
    "exact_model_log_tokens",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_examples() -> dict[str, dict[str, Any]]:
    manifest = _load_json(MANIFEST_PATH)
    return {str(item.get("id")): item for item in manifest.get("sessions", []) if isinstance(item, dict)}


def _check_source_refs(case_id: str, finding: dict[str, Any], fails: list[str]) -> None:
    refs = finding.get("source_ref_contains")
    if not isinstance(refs, list) or not refs:
        fails.append(f"{case_id}: expected finding missing source_ref_contains")
        return
    for ref in refs:
        if not isinstance(ref, str) or "." not in ref:
            fails.append(f"{case_id}: weak source_ref_contains value {ref!r}")


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_flatten_strings(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_flatten_strings(item))
        return out
    return []


def _source_ref_blob(finding: dict[str, Any]) -> str:
    return "\n".join(sorted(_flatten_strings(finding.get("source_ref", {}))))


def _source_ref_metrics(expected: list[dict[str, Any]], observed: list[dict[str, Any]]) -> dict[str, int | float]:
    total_refs = 0
    covered_refs = 0
    expected_findings = 0
    top1_hits = 0
    top3_hits = 0

    observed_by_type: dict[str, list[dict[str, Any]]] = {}
    for finding in observed:
        observed_by_type.setdefault(str(finding.get("type") or ""), []).append(finding)

    all_observed_blob = "\n".join(_source_ref_blob(finding) for finding in observed)
    for finding in expected:
        if not isinstance(finding, dict):
            continue
        refs = [ref for ref in finding.get("source_ref_contains") or [] if isinstance(ref, str)]
        if not refs:
            continue
        expected_findings += 1
        total_refs += len(refs)
        covered_refs += sum(1 for ref in refs if ref in all_observed_blob)

        same_type = observed_by_type.get(str(finding.get("type") or ""), [])
        top1_blob = _source_ref_blob(same_type[0]) if same_type else ""
        top3_blob = "\n".join(_source_ref_blob(item) for item in same_type[:3])
        if all(ref in top1_blob for ref in refs):
            top1_hits += 1
        if all(ref in top3_blob for ref in refs):
            top3_hits += 1

    return {
        "expected_source_refs": total_refs,
        "covered_source_refs": covered_refs,
        "expected_findings": expected_findings,
        "top1_source_ref_hits": top1_hits,
        "top3_source_ref_hits": top3_hits,
        "source_ref_coverage": round(covered_refs / total_refs, 4) if total_refs else 0.0,
        "top1_source_ref_accuracy": round(top1_hits / expected_findings, 4) if expected_findings else 0.0,
        "top3_source_ref_accuracy": round(top3_hits / expected_findings, 4) if expected_findings else 0.0,
    }


def _check_case(case: dict[str, Any], examples: dict[str, dict[str, Any]], fails: list[str]) -> tuple[int, int, dict[str, int | float]]:
    case_id = str(case.get("case_id") or "<missing>")
    if case.get("serves_truth") is not False:
        fails.append(f"{case_id}: serves_truth must be false")
    example_id = str(case.get("example_id") or "")
    manifest_entry = examples.get(example_id)
    if not manifest_entry:
        fails.append(f"{case_id}: example_id {example_id!r} not found in example manifest")
        return (0, 0, {})
    if manifest_entry.get("source_kind") != "synthetic_from_public_project":
        fails.append(f"{case_id}: manifest entry must be synthetic_from_public_project")

    transcript = case.get("transcript")
    if not isinstance(transcript, str):
        fails.append(f"{case_id}: transcript path missing")
        return (0, 0, {})
    transcript_path = _resource(transcript)
    if not transcript_path.exists():
        fails.append(f"{case_id}: transcript path does not exist")
        return (0, 0, {})
    if EXAMPLES_DIR not in transcript_path.parents:
        fails.append(f"{case_id}: transcript must live under AIDevObserver examples")
    text = transcript_path.read_text(encoding="utf-8")
    if has_secret_like_text(text):
        fails.append(f"{case_id}: transcript contains secret-like text")
    if "synthetic_from_public_project" not in text:
        fails.append(f"{case_id}: transcript must preserve synthetic_from_public_project label")

    expected = case.get("expected_findings")
    if not isinstance(expected, list) or not expected:
        fails.append(f"{case_id}: expected_findings must be a non-empty list")
    else:
        for finding in expected:
            if not isinstance(finding, dict):
                fails.append(f"{case_id}: expected finding is not an object")
                continue
            if finding.get("type") not in {"reinvention", "wasted_context", "missed_registry_route", "loop_or_thrash"}:
                fails.append(f"{case_id}: unsupported expected finding type {finding.get('type')!r}")
            _check_source_refs(case_id, finding, fails)

    token_estimate = case.get("token_estimate")
    if not isinstance(token_estimate, dict):
        fails.append(f"{case_id}: token_estimate missing")
    else:
        if token_estimate.get("basis") not in ALLOWED_TOKEN_ESTIMATE_BASES:
            fails.append(f"{case_id}: unsupported token estimate basis")
        if not isinstance(token_estimate.get("prompt_tokens_avoided"), int) or token_estimate["prompt_tokens_avoided"] <= 0:
            fails.append(f"{case_id}: prompt_tokens_avoided must be positive integer")
        if not isinstance(token_estimate.get("model_calls_avoided"), int) or token_estimate["model_calls_avoided"] < 0:
            fails.append(f"{case_id}: model_calls_avoided must be non-negative integer")

    if not isinstance(case.get("false_positive_traps"), list) or not case["false_positive_traps"]:
        fails.append(f"{case_id}: false_positive_traps missing")

    messages = parse_text_transcript(text)
    report = review_session(messages)
    if report.get("serves_truth") is not False:
        fails.append(f"{case_id}: reviewer output must be candidate-only")
    if not all(f.get("candidate") is True and f.get("serves_truth") is False for f in report.get("report", [])):
        fails.append(f"{case_id}: reviewer findings must be governed candidates")
    observed_source_ref_values: list[str] = []
    for observed in report.get("report", []):
        observed_source_ref_values.extend(_flatten_strings(observed.get("source_ref", {})))
    observed_source_refs = "\n".join(sorted(observed_source_ref_values))
    if isinstance(expected, list):
        for finding in expected:
            if not isinstance(finding, dict):
                continue
            for ref in finding.get("source_ref_contains") or []:
                if isinstance(ref, str) and ref not in observed_source_refs:
                    fails.append(f"{case_id}: expected source ref {ref!r} not found in reviewer output")
    metrics = _source_ref_metrics(expected if isinstance(expected, list) else [], report.get("report", []))
    observed_findings = len(report.get("report", []))
    current = case.get("current_engine_expectation") or {}
    min_findings = current.get("min_findings")
    if not isinstance(min_findings, int):
        fails.append(f"{case_id}: current_engine_expectation.min_findings missing")
    elif observed_findings < min_findings:
        fails.append(f"{case_id}: observed {observed_findings} findings below minimum {min_findings}")
    return (len(expected) if isinstance(expected, list) else 0, observed_findings, metrics)


def _self_test() -> int:
    fails: list[str] = []
    benchmark = _load_json(BENCHMARK_PATH)
    if benchmark.get("serves_truth") is not False:
        fails.append("benchmark serves_truth must be false")
    if benchmark.get("source_kind") != "synthetic_from_public_project":
        fails.append("benchmark source_kind must be synthetic_from_public_project")
    cases = benchmark.get("cases")
    if not isinstance(cases, list) or len(cases) < 3:
        fails.append("benchmark must contain at least 3 cases")
        cases = []

    examples = _manifest_examples()
    target_expected = 0
    observed = 0
    aggregate_metrics = {
        "expected_source_refs": 0,
        "covered_source_refs": 0,
        "expected_findings": 0,
        "top1_source_ref_hits": 0,
        "top3_source_ref_hits": 0,
    }
    for case in cases:
        if not isinstance(case, dict):
            fails.append("case is not an object")
            continue
        case_expected, case_observed, case_metrics = _check_case(case, examples, fails)
        target_expected += case_expected
        observed += case_observed
        for key in aggregate_metrics:
            value = case_metrics.get(key, 0) if isinstance(case_metrics, dict) else 0
            if isinstance(value, int):
                aggregate_metrics[key] += value

    expected_refs = aggregate_metrics["expected_source_refs"]
    expected_findings = aggregate_metrics["expected_findings"]
    source_ref_coverage = round(aggregate_metrics["covered_source_refs"] / expected_refs, 4) if expected_refs else 0.0
    top1_accuracy = round(aggregate_metrics["top1_source_ref_hits"] / expected_findings, 4) if expected_findings else 0.0
    top3_accuracy = round(aggregate_metrics["top3_source_ref_hits"] / expected_findings, 4) if expected_findings else 0.0

    thresholds = benchmark.get("required_metric_thresholds") or {}
    if isinstance(thresholds, dict):
        for metric_name, actual in (
            ("source_ref_coverage", source_ref_coverage),
            ("top1_source_ref_accuracy", top1_accuracy),
            ("top3_source_ref_accuracy", top3_accuracy),
        ):
            threshold = thresholds.get(metric_name)
            if isinstance(threshold, (int, float)) and actual < float(threshold):
                fails.append(f"{metric_name} {actual} below threshold {threshold}")

    if fails:
        print("FAIL - aidevobserver session benchmark")
        for fail in fails:
            print(f"  [XX] {fail}")
        return 1

    print(
        "PASS - aidevobserver session benchmark: "
        f"{len(cases)} Kaggle synthetic public-project cases, "
        f"{target_expected} target expected findings, "
        f"{observed} current reviewer findings; "
        f"source_ref_coverage={source_ref_coverage:.2f}, "
        f"top1_source_ref_accuracy={top1_accuracy:.2f}, "
        f"top3_source_ref_accuracy={top3_accuracy:.2f}; serves_truth=false."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    return _self_test()


if __name__ == "__main__":
    sys.exit(main())
