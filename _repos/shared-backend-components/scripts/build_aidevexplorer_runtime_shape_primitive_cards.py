#!/usr/bin/env python3
"""Build compact AIDevObserver primitive cards from runtime-shape tasks."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_MANIFEST_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_EVIDENCE_STATUS,
    AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_FAMILY,
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPES,
    REPO_ROOT,
)

TASKS_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH)
OUT_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_MANIFEST_PATH)

SOURCE_FAMILY = AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_FAMILY
SOURCE_EVIDENCE_STATUS = AIDEVEXPLORER_RUNTIME_SHAPE_SOURCE_EVIDENCE_STATUS
SURFACE_VISIBILITY = "public_demo_safe_candidate"
READINESS = "R2_benchmark_seed_group_candidate"
TRUST = "candidate"

RUNTIME_TARGETS_BY_SHAPE: dict[str, tuple[str, ...]] = {
    "py.fn": ("py.fn", "local.python", "container.python"),
    "api.endpoint": ("api.endpoint", "cloud.function.http", "container.python", "k8s.deployment"),
    "microservice": ("service.group", "api.endpoint", "queue.consumer", "container.python", "k8s.deployment"),
    "webhook.handler": ("webhook.handler", "api.endpoint", "cloud.function.http", "queue.producer"),
    "queue.consumer": ("queue.consumer", "container.python", "k8s.deployment"),
    "cron.job": ("cron.job", "k8s.cronjob", "container.python"),
    "cli.command": ("cli.command", "local.python", "container.python"),
    "workflow.automation": ("workflow.automation", "workflow.step", "container.python"),
    "kubernetes.job": ("kubernetes.job", "k8s.job", "container.python"),
    "dashboard.report": ("dashboard.report", "web.ui", "artifact.static"),
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any, *, n: int = 16) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()[:n]


def _slug(value: str) -> str:
    out = []
    prev_dash = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "runtime-shape"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    return rows


def _tokens(*values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = _canon(value) if isinstance(value, (dict, list)) else str(value or "")
        token = []
        for char in text.lower():
            if char.isalnum():
                token.append(char)
            elif token:
                word = "".join(token)
                token.clear()
                if len(word) > 1 and word not in seen:
                    seen.add(word)
                    out.append(word)
        if token:
            word = "".join(token)
            if len(word) > 1 and word not in seen:
                seen.add(word)
                out.append(word)
    return out


def _mutation_option(mutator: str, *, input_edge: str, output_edge: str, runtime_shape: str, proofs: list[str]) -> dict[str, Any]:
    return {
        "mutator": mutator,
        "mutator_agent_id": f"mut:deterministic:{mutator}@1",
        "reason": f"Expose the core group through {runtime_shape} while preserving the visible edge contract.",
        "input_edge_before": input_edge,
        "output_edge_before": output_edge,
        "target_edge_template": {
            "input": input_edge,
            "output": output_edge,
            "mutation": mutator,
        },
        "effect_delta": "runtime_wrapper",
        "preconditions": [
            "core_group_edge_declared",
            "wrapper_edges_declared",
            "side_effects_declared",
        ],
        "proof_obligations": proofs,
        "runtime_targets": list(RUNTIME_TARGETS_BY_SHAPE.get(runtime_shape, (runtime_shape,))),
        "candidate": True,
        "serves_truth": False,
    }


def _quality_score(rows: list[dict[str, Any]]) -> int:
    sample = rows[0]
    proofs = len(sample.get("proof_requirements") or [])
    wrappers = len(sample.get("wrapper_edges") or [])
    hidden = len(sample.get("hidden_member_edges") or [])
    return min(94, 70 + proofs + wrappers + hidden)


def _card(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sample = rows[0]
    task_family = str(sample["task_family"])
    runtime_shape = str(sample["runtime_shape"])
    primitive_kind = str(sample["primitive_kind"])
    input_edge = str(sample["input_edge"])
    output_edge = str(sample["output_edge"])
    core_group_edge = str(sample["core_group_edge"])
    card_slug = _slug(f"{task_family}-{runtime_shape}")
    proofs = sorted({str(item) for row in rows for item in row.get("proof_requirements") or []})
    effects = sorted({str(item) for row in rows for item in row.get("effects") or []})
    mutators = sorted({str(item) for row in rows for item in row.get("adapter_mutators") or []})
    industries = sorted({str(row.get("industry") or "") for row in rows if row.get("industry")})
    task_ids = [str(row.get("id") or "") for row in rows[:8] if row.get("id")]
    runtime_targets = list(RUNTIME_TARGETS_BY_SHAPE.get(runtime_shape, (runtime_shape, primitive_kind)))
    mutations = [
        _mutation_option(mutator, input_edge=input_edge, output_edge=output_edge, runtime_shape=runtime_shape, proofs=proofs)
        for mutator in mutators
    ]
    blackbox = {
        "does": (
            f"Expose the reusable {task_family} core group edge `{core_group_edge}` as `{runtime_shape}` "
            "without rebuilding hidden member logic."
        ),
        "llm_context_policy": "show_visible_edge_first; reveal_wrapper_and_hidden_member_edges_only_on_drilldown",
    }
    source_ref = {
        "path": AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
        "name": f"{task_family}.{runtime_shape}",
        "row_count": len(rows),
        "representative_task_ids": task_ids,
    }
    card = {
        "primitive_id": f"grp:aidevexplorer.runtime_shape.{task_family}.{runtime_shape}@candidate",
        "kind": primitive_kind,
        "slug": f"aidevexplorer-runtime-shape-{card_slug}",
        "title": f"{task_family.replace('_', ' ').title()} as {runtime_shape}",
        "label": f"{task_family}.{runtime_shape}",
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": {"input": input_edge, "output": output_edge},
        "group_contract": {
            "visible_input_edge": input_edge,
            "visible_output_edge": output_edge,
            "core_group_edge": core_group_edge,
            "wrapper_edges": sample.get("wrapper_edges") or [],
            "hidden_member_edges": sample.get("hidden_member_edges") or [],
        },
        "blackbox": blackbox,
        "effects": effects,
        "memory": "artifact",
        "cache": "contract_hash",
        "runtime_shape": runtime_shape,
        "runtime_targets": runtime_targets,
        "adapter_mutators": mutators,
        "mutations": mutations,
        "edge_mutation_options": mutations,
        "proof_requirements": proofs,
        "promotion_blockers": [
            "runtime_wrapper_implementation_required",
            "proof_bundle_required",
            "source_backing_required_before_promotion",
        ],
        "blocking_keys": _tokens(
            task_family,
            runtime_shape,
            primitive_kind,
            input_edge,
            output_edge,
            core_group_edge,
            sample.get("wrapper_edges") or [],
            sample.get("hidden_member_edges") or [],
            sample.get("likely_primitives") or [],
            sample.get("expected_primitive_groups") or [],
        ),
        "capability_tags": ["runtime_shape_reuse", task_family, runtime_shape, primitive_kind],
        "domains": ["software_engineering", "runtime_shape_reuse", task_family],
        "business_context_count": len(rows),
        "industry_sample": industries[:12],
        "source_ref": source_ref,
        "source_family": SOURCE_FAMILY,
        "source_evidence_status": SOURCE_EVIDENCE_STATUS,
        "source_digest": _sha({"source_ref": source_ref, "contract": {"input": input_edge, "output": output_edge}}, n=24),
        "surface_visibility": SURFACE_VISIBILITY,
        "readiness": READINESS,
        "trust": TRUST,
        "quality_score": _quality_score(rows),
        "generated_at": _utc(),
        "candidate": True,
        "serves_truth": False,
    }
    return card


def build_cards(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[(str(task.get("task_family") or ""), str(task.get("runtime_shape") or ""))].append(task)
    cards = [_card(rows) for _, rows in sorted(grouped.items()) if rows]
    cards.sort(key=lambda row: (str(row["runtime_shape"]), str(row["primitive_id"])))
    return cards


def write_cards(cards: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        "".join(json.dumps(card, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for card in cards),
        encoding="utf-8",
    )
    by_shape: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for card in cards:
        by_shape[str(card["runtime_shape"])] = by_shape.get(str(card["runtime_shape"]), 0) + 1
        by_kind[str(card["kind"])] = by_kind.get(str(card["kind"]), 0) + 1
    manifest = {
        "record_type": "aidevexplorer_runtime_shape_primitive_cards_manifest",
        "created_at": _utc(),
        "task_corpus_path": AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
        "cards_path": AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH,
        "row_count": len(cards),
        "runtime_shape_counts": dict(sorted(by_shape.items())),
        "primitive_kind_counts": dict(sorted(by_kind.items())),
        "source_family": SOURCE_FAMILY,
        "source_evidence_status": SOURCE_EVIDENCE_STATUS,
        "candidate": True,
        "serves_truth": False,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        tasks = _read_jsonl(TASKS_PATH)
        cards = build_cards(tasks)
        expected = len(AIDEVEXPLORER_RUNTIME_SHAPES) * len({str(task.get("task_family") or "") for task in tasks})
        if len(cards) != expected:
            raise AssertionError(f"built {len(cards)} cards; expected {expected}")
        manifest = {
            "row_count": len(cards),
            "would_write": AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH,
            "candidate": True,
            "serves_truth": False,
        }
        if not args.check_only:
            manifest = write_cards(cards)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
