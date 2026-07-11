#!/usr/bin/env python3
"""Report runtime adapter and deterministic mutator coverage.

This is a proof-gated bookkeeping layer for the primitive foundry. It does not
execute adapters and does not promote primitives. It checks whether the current
source-backed edge corpus has enough compact evidence for runtime wrapper
families such as API endpoints, cloud functions, CLI commands, Kubernetes Jobs,
Deployments, and CronJobs.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
    AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION,
    AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB,
    AIDEVOBSERVER_RUNTIME_TARGET_LOCAL,
)

DEFAULT_EDGE_CARDS = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "primitive_edge_cards.jsonl"
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "runtime_adapter_coverage"
DEFAULT_MIN_REQUIRED_COUNT = 1
DEFAULT_LOW_COVERAGE_COUNT = 25
DEFAULT_FIXTURES_PER_TARGET = 12
DEFAULT_MAX_CARDS = 0

RUNTIME_MUTATOR_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION: (
        AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
        AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
    ),
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB: (AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,),
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT: (AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,),
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB: (AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,),
}

TRACKED_RUNTIME_TARGETS: tuple[str, ...] = (
    AIDEVOBSERVER_RUNTIME_TARGET_LOCAL,
    AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER,
    AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB,
)

TRACKED_RUNTIME_MUTATORS: tuple[str, ...] = (
    AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _read_jsonl(path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL in {path} line {line_no}: {exc}") from exc
        if isinstance(value, dict):
            rows.append(value)
            if limit > 0 and len(rows) >= limit:
                break
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_canon(row) + "\n")
            count += 1
    return count


def _quality(card: dict[str, Any]) -> int:
    try:
        return int(card.get("quality_score") or 0)
    except (TypeError, ValueError):
        return 0


def _contract(card: dict[str, Any]) -> dict[str, str]:
    contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
    return {
        "input": str(card.get("input_edge") or contract.get("input") or ""),
        "output": str(card.get("output_edge") or contract.get("output") or ""),
    }


def _mutations(card: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in card.get("mutations") or [] if isinstance(item, dict)]


def _mutator_ids(card: dict[str, Any]) -> set[str]:
    return {str(item.get("mutator")) for item in _mutations(card) if item.get("mutator")}


def _runtime_targets(card: dict[str, Any]) -> set[str]:
    return {str(item) for item in card.get("runtime_targets") or [] if item}


def _mutation_for(card: dict[str, Any], mutator: str) -> dict[str, Any]:
    for mutation in _mutations(card):
        if str(mutation.get("mutator") or "") == mutator:
            return mutation
    return {}


def _eligible_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        card
        for card in cards
        if card.get("candidate") is True
        and card.get("serves_truth") is False
        and card.get("primitive_id")
        and (_runtime_targets(card) or _mutator_ids(card))
    ]
    rows.sort(key=lambda card: (-_quality(card), str(card.get("primitive_id") or "")))
    return rows


def _fixture_for(card: dict[str, Any], *, runtime_target: str, mutator: str) -> dict[str, Any]:
    mutation = _mutation_for(card, mutator)
    target_edge = mutation.get("target_edge_template") if isinstance(mutation.get("target_edge_template"), dict) else {}
    contract = _contract(card)
    return {
        "record_type": "runtime_adapter_fixture",
        "fixture_id": f"runtime_fixture:{runtime_target}:{mutator}:{card.get('primitive_id')}",
        "runtime_target": runtime_target,
        "required_mutator": mutator,
        "prompt": (
            f"Emit `{card.get('label') or card.get('title') or card.get('primitive_id')}` "
            f"as `{runtime_target}` using `{mutator}` without rewriting the primitive."
        ),
        "component": {
            "primitive_id": card.get("primitive_id"),
            "label": card.get("label") or card.get("title") or card.get("slug"),
            "contract": contract,
            "target_contract": {
                "input": target_edge.get("input") or contract["input"],
                "output": target_edge.get("output") or contract["output"],
            },
            "source_ref": card.get("source_ref") or {},
            "source_family": card.get("source_family"),
            "quality_score": _quality(card),
            "runtime_targets": sorted(_runtime_targets(card)),
            "candidate": True,
            "serves_truth": False,
        },
        "proof_obligations": mutation.get("proof_obligations") or [],
        "preconditions": mutation.get("preconditions") or [],
        "effect_delta": mutation.get("effect_delta"),
        "expected_plan_delta": {"v": 1, "p": "pairs", "t": 0, "b": [[0, 0]], "r": [[0, mutator]], "g": []},
        "candidate": True,
        "serves_truth": False,
        "created_at": _utc(),
    }


def build_runtime_adapter_report(
    edge_cards: list[dict[str, Any]],
    *,
    min_required_count: int,
    low_coverage_count: int,
    fixtures_per_target: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    cards = _eligible_cards(edge_cards)
    runtime_counts: Counter[str] = Counter()
    mutator_counts: Counter[str] = Counter()
    cards_by_runtime_mutator: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for card in cards:
        targets = _runtime_targets(card)
        mutators = _mutator_ids(card)
        for target in targets:
            runtime_counts[target] += 1
        for mutator in mutators:
            mutator_counts[mutator] += 1
        for target, required_mutators in RUNTIME_MUTATOR_REQUIREMENTS.items():
            for mutator in required_mutators:
                if target in targets or mutator in mutators:
                    if mutator in mutators:
                        cards_by_runtime_mutator[(target, mutator)].append(card)

    gaps: list[dict[str, Any]] = []
    fixtures: list[dict[str, Any]] = []
    for runtime_target, required_mutators in RUNTIME_MUTATOR_REQUIREMENTS.items():
        runtime_count = runtime_counts.get(runtime_target, 0)
        if runtime_count < min_required_count:
            gaps.append({
                "record_type": "runtime_adapter_coverage_gap",
                "gap_kind": "missing_runtime_target",
                "runtime_target": runtime_target,
                "observed_count": runtime_count,
                "required_count": min_required_count,
                "candidate": True,
                "serves_truth": False,
            })
        elif runtime_count < low_coverage_count:
            gaps.append({
                "record_type": "runtime_adapter_coverage_gap",
                "gap_kind": "low_runtime_target_coverage",
                "runtime_target": runtime_target,
                "observed_count": runtime_count,
                "recommended_minimum": low_coverage_count,
                "candidate": True,
                "serves_truth": False,
            })
        for mutator in required_mutators:
            mutator_count = mutator_counts.get(mutator, 0)
            if mutator_count < min_required_count:
                gaps.append({
                    "record_type": "runtime_adapter_coverage_gap",
                    "gap_kind": "missing_required_mutator",
                    "runtime_target": runtime_target,
                    "mutator": mutator,
                    "observed_count": mutator_count,
                    "required_count": min_required_count,
                    "candidate": True,
                    "serves_truth": False,
                })
            elif mutator_count < low_coverage_count:
                gaps.append({
                    "record_type": "runtime_adapter_coverage_gap",
                    "gap_kind": "low_required_mutator_coverage",
                    "runtime_target": runtime_target,
                    "mutator": mutator,
                    "observed_count": mutator_count,
                    "recommended_minimum": low_coverage_count,
                    "candidate": True,
                    "serves_truth": False,
                })
            for card in cards_by_runtime_mutator.get((runtime_target, mutator), [])[:fixtures_per_target]:
                fixtures.append(_fixture_for(card, runtime_target=runtime_target, mutator=mutator))

    report = {
        "record_type": "runtime_adapter_coverage_report",
        "created_at": _utc(),
        "edge_cards_read": len(edge_cards),
        "eligible_cards": len(cards),
        "runtime_target_counts": {target: runtime_counts.get(target, 0) for target in TRACKED_RUNTIME_TARGETS},
        "runtime_mutator_counts": {mutator: mutator_counts.get(mutator, 0) for mutator in TRACKED_RUNTIME_MUTATORS},
        "required_runtime_mutators": {
            runtime: list(mutators)
            for runtime, mutators in RUNTIME_MUTATOR_REQUIREMENTS.items()
        },
        "gap_count": len(gaps),
        "blocking_gap_count": sum(1 for gap in gaps if str(gap.get("gap_kind") or "").startswith("missing_")),
        "low_coverage_gap_count": sum(1 for gap in gaps if str(gap.get("gap_kind") or "").startswith("low_")),
        "fixture_count": len(fixtures),
        "min_required_count": min_required_count,
        "low_coverage_count": low_coverage_count,
        "fixtures_per_target": fixtures_per_target,
        "ok": not any(str(gap.get("gap_kind") or "").startswith("missing_") for gap in gaps),
        "candidate": True,
        "serves_truth": False,
    }
    return report, gaps, fixtures


def write_runtime_adapter_artifacts(
    *,
    edge_cards_path: Path,
    out_dir: Path,
    min_required_count: int,
    low_coverage_count: int,
    fixtures_per_target: int,
    max_cards: int,
    write: bool = True,
) -> dict[str, Any]:
    cards = _read_jsonl(edge_cards_path, limit=max_cards)
    report, gaps, fixtures = build_runtime_adapter_report(
        cards,
        min_required_count=min_required_count,
        low_coverage_count=low_coverage_count,
        fixtures_per_target=fixtures_per_target,
    )
    report = {
        **report,
        "edge_cards_path": str(edge_cards_path),
        "out_dir": str(out_dir),
        "artifacts": {
            "report": str(out_dir / "runtime_adapter_coverage_report.json"),
            "gaps": str(out_dir / "runtime_adapter_gaps.jsonl"),
            "fixtures": str(out_dir / "runtime_adapter_fixtures.jsonl"),
            "summary": str(out_dir / "summary.md"),
        },
    }
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "runtime_adapter_coverage_report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        _write_jsonl(out_dir / "runtime_adapter_gaps.jsonl", gaps)
        _write_jsonl(out_dir / "runtime_adapter_fixtures.jsonl", fixtures)
        _write_summary(out_dir / "summary.md", report, gaps, fixtures)
    return report


def _write_summary(path: Path, report: dict[str, Any], gaps: list[dict[str, Any]], fixtures: list[dict[str, Any]]) -> None:
    lines = [
        "# Runtime Adapter Coverage",
        "",
        f"- Updated: `{report['created_at']}`",
        f"- Edge cards read: `{report['edge_cards_read']}`",
        f"- Eligible cards: `{report['eligible_cards']}`",
        f"- Runtime adapter fixtures: `{report['fixture_count']}`",
        f"- Blocking gaps: `{report['blocking_gap_count']}`",
        f"- Low-coverage gaps: `{report['low_coverage_gap_count']}`",
        f"- Serves truth: `{report['serves_truth']}`",
        "",
        "## Runtime Targets",
        "",
        "```json",
        json.dumps(report["runtime_target_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Runtime Mutators",
        "",
        "```json",
        json.dumps(report["runtime_mutator_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Gaps",
        "",
    ]
    if gaps:
        for gap in gaps[:40]:
            lines.append(f"- `{gap.get('gap_kind')}` target=`{gap.get('runtime_target')}` mutator=`{gap.get('mutator') or '-'}` observed=`{gap.get('observed_count')}`")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Example Fixtures",
        "",
    ])
    for fixture in fixtures[:12]:
        lines.append(f"- `{fixture['fixture_id']}` -> `{fixture['runtime_target']}` via `{fixture['required_mutator']}`")
    lines.extend([
        "",
        "All rows are candidate-only coverage/proof artifacts and do not promote primitives.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cards_path = root / "cards.jsonl"
        out_dir = root / "out"
        cards = [
            {
                "primitive_id": "prim:api",
                "label": "handle_request",
                "contract": {"input": "dict[str,object]", "output": "dict[str,object]"},
                "input_edge": "dict[str,object]",
                "output_edge": "dict[str,object]",
                "runtime_targets": [AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION],
                "mutations": [
                    {"mutator": AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER, "target_edge_template": {"input": "CloudFunctionRequest[dict[str,object]]", "output": "CloudFunctionResponse[dict[str,object]]"}, "proof_obligations": ["handler_contract_declared"], "candidate": True, "serves_truth": False},
                    {"mutator": AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER, "target_edge_template": {"input": "HttpRequest[dict[str,object]]", "output": "HttpResponse[dict[str,object]]"}, "proof_obligations": ["request_schema_validated"], "candidate": True, "serves_truth": False},
                ],
                "candidate": True,
                "serves_truth": False,
                "quality_score": 90,
            },
            {
                "primitive_id": "prim:k8s",
                "label": "apply_manifest",
                "contract": {"input": "KubernetesManifest", "output": "KubernetesApplyReceipt"},
                "input_edge": "KubernetesManifest",
                "output_edge": "KubernetesApplyReceipt",
                "runtime_targets": [
                    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB,
                    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT,
                    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB,
                ],
                "mutations": [
                    {"mutator": AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER, "target_edge_template": {"input": "KubernetesJobSpec[KubernetesManifest]", "output": "KubernetesJobReceipt[KubernetesApplyReceipt]"}, "candidate": True, "serves_truth": False},
                    {"mutator": AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER, "target_edge_template": {"input": "KubernetesDeploymentSpec[KubernetesManifest]", "output": "KubernetesServiceReceipt[KubernetesApplyReceipt]"}, "candidate": True, "serves_truth": False},
                    {"mutator": AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER, "target_edge_template": {"input": "KubernetesCronJobSpec[KubernetesManifest]", "output": "KubernetesCronJobReceipt[KubernetesApplyReceipt]"}, "candidate": True, "serves_truth": False},
                ],
                "candidate": True,
                "serves_truth": False,
                "quality_score": 88,
            },
        ]
        _write_jsonl(cards_path, cards)
        report = write_runtime_adapter_artifacts(
            edge_cards_path=cards_path,
            out_dir=out_dir,
            min_required_count=1,
            low_coverage_count=2,
            fixtures_per_target=2,
            max_cards=0,
            write=True,
        )
        fixtures = _read_jsonl(out_dir / "runtime_adapter_fixtures.jsonl")
        assert report["ok"] is True
        assert report["blocking_gap_count"] == 0
        assert report["fixture_count"] >= 5
        assert all(row.get("serves_truth") is False for row in fixtures)
        assert (out_dir / "summary.md").exists()
    print("PASS - runtime adapter coverage report: runtime targets, mutator families, gaps, and candidate fixtures verified.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edge-cards", default=str(DEFAULT_EDGE_CARDS))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--min-required-count", type=int, default=DEFAULT_MIN_REQUIRED_COUNT)
    parser.add_argument("--low-coverage-count", type=int, default=DEFAULT_LOW_COVERAGE_COUNT)
    parser.add_argument("--fixtures-per-target", type=int, default=DEFAULT_FIXTURES_PER_TARGET)
    parser.add_argument("--max-cards", type=int, default=DEFAULT_MAX_CARDS)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    report = write_runtime_adapter_artifacts(
        edge_cards_path=Path(args.edge_cards),
        out_dir=Path(args.out_dir),
        min_required_count=args.min_required_count,
        low_coverage_count=args.low_coverage_count,
        fixtures_per_target=args.fixtures_per_target,
        max_cards=args.max_cards,
        write=True,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
