#!/usr/bin/env python3
"""Primitive deconstruction plane database and definition pipeline.

This is the second stage after `continuous_primitive_scrape_loop.py`.

Stage 1 finds source-backed primitive candidates.
Stage 2, this file, builds the persistent deconstruction database:

* deconstruction planes;
* analysis layers;
* dimension rows;
* question database rows;
* plane/layer/question edges;
* completeness rubric;
* fully-defined primitive candidate records;
* staged primitive database feed rows.

Generated records are still candidates. "Fully defined" here means the record
has the full contract, examples, graph refs, proof obligations, remix axes, and
promotion blockers needed by the primitive database. It does not mean promoted
truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install  # noqa: E402

_install()

import argparse
import hashlib
import json
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from scripts._llm_client import DEFAULT_PROVIDER, PROVIDERS, chat, resolve_provider  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.continuous_primitive_scrape_loop import (  # noqa: E402
    DEFAULT_OUT_DIR as CONTINUOUS_OUT_DIR,
    DEFAULT_QUESTION_COUNT,
    generate_question_bank,
    run_loop as run_continuous_loop,
)


RECORD_TYPE = "primitive_deconstruction_plane_pipeline"
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "primitive_deconstruction_plane_pipeline"
DEFAULT_DATABASE_DIR = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "primitive-deconstruction-plane-database"
)
VARIATION_ATLAS = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "primitive-variation-dimension-atlas"
    / "primitive_variation_dimensions_250.jsonl"
)
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class PlaneSpec:
    plane_id: str
    title: str
    purpose: str
    dimensions: tuple[str, ...]
    required_fields: tuple[str, ...]
    proof_implications: tuple[str, ...]


@dataclass(frozen=True)
class LayerSpec:
    layer_id: str
    title: str
    purpose: str
    question_stem: str
    required_output: str


PLANE_SPECS: tuple[PlaneSpec, ...] = (
    PlaneSpec(
        "plane:source_context",
        "Source Context Plane",
        "Provenance, source policy, licensing, freshness, and source support.",
        ("source_kind", "publisher_class", "license_status", "freshness", "source_support_depth"),
        ("source_refs_sample", "license_provenance", "source_support_count"),
        ("source_ref_review", "license_review", "raw_body_exclusion_check"),
    ),
    PlaneSpec(
        "plane:product_surface",
        "Product Surface Plane",
        "User-facing surface, workflow, role, channel, and user/job context.",
        ("surface_kind", "user_role", "job_to_be_done", "workflow_stage", "interaction_mode"),
        ("purpose", "runtime_targets", "design_system_variants"),
        ("workflow_fixture", "role_scope_check"),
    ),
    PlaneSpec(
        "plane:component_boundary",
        "Component Boundary Plane",
        "Subcomponents, boundaries, dependencies, and responsibilities.",
        ("component_family", "responsibility", "dependency", "owned_state", "handoff_boundary"),
        ("component_family", "primitive_group", "hidden_member_edges"),
        ("component_contract_test", "boundary_invariant_test"),
    ),
    PlaneSpec(
        "plane:primitive_contract",
        "Primitive Contract Plane",
        "Visible input/output edges, effects, errors, and postconditions.",
        ("input_edge", "output_edge", "side_effect", "failure_mode", "postcondition"),
        ("input_contract", "output_contract", "effects", "failure_modes"),
        ("input_contract_test", "output_contract_test", "side_effect_audit"),
    ),
    PlaneSpec(
        "plane:data_shape",
        "Data Shape Plane",
        "Schemas, datatypes, cardinality, serialization, and transform shape.",
        ("schema", "datatype", "cardinality", "serialization", "transform_shape"),
        ("input_contract", "output_contract", "edge_contract"),
        ("schema_fixture", "edge_case_fixture"),
    ),
    PlaneSpec(
        "plane:state_transition",
        "State Transition Plane",
        "State model, idempotency, concurrency, retry, rollback, and receipts.",
        ("state", "transition", "idempotency", "concurrency", "rollback"),
        ("edge_contract", "proof_requirements", "effects"),
        ("idempotency_test", "rollback_or_escalation_test"),
    ),
    PlaneSpec(
        "plane:architecture",
        "Architecture Plane",
        "Runtime shape, deployment topology, service boundaries, and integration pattern.",
        ("runtime_shape", "deployment_target", "service_boundary", "integration_pattern", "scaling_mode"),
        ("runtime_targets", "architecture_variants", "composition"),
        ("runtime_fixture", "integration_contract_test"),
    ),
    PlaneSpec(
        "plane:algorithm",
        "Algorithm Plane",
        "Algorithm family, complexity, proof sketch, data structure, and edge cases.",
        ("algorithm_family", "complexity", "data_structure", "proof_style", "edge_case"),
        ("proof_requirements", "examples", "benchmark_hooks"),
        ("correctness_proof", "complexity_check", "edge_case_fixture"),
    ),
    PlaneSpec(
        "plane:ml_notebook",
        "ML Notebook Plane",
        "Dataset loading, features, training, metrics, leakage checks, and submission.",
        ("dataset_shape", "feature_transform", "model_family", "metric", "submission_format"),
        ("input_contract", "output_contract", "benchmark_hooks"),
        ("metric_reproduction_test", "leakage_check"),
    ),
    PlaneSpec(
        "plane:ux_design",
        "UX And Design Plane",
        "Layout, interaction, accessibility, design tokens, and responsive states.",
        ("layout", "interaction", "accessibility", "design_token", "responsive_state"),
        ("design_system_variants", "examples", "runtime_targets"),
        ("visual_snapshot_test", "accessibility_check"),
    ),
    PlaneSpec(
        "plane:security_privacy",
        "Security And Privacy Plane",
        "Auth, permissions, secret handling, data minimization, and abuse controls.",
        ("auth", "permission", "secret", "privacy_boundary", "abuse_control"),
        ("proof_requirements", "promotion_blockers", "effects"),
        ("secret_redaction_test", "auth_scope_test", "privacy_boundary_check"),
    ),
    PlaneSpec(
        "plane:observability",
        "Observability Plane",
        "Logging, traces, metrics, receipts, alerts, and debug surfaces.",
        ("log", "trace", "metric", "receipt", "alert"),
        ("benchmark_hooks", "edge_contract", "proof_requirements"),
        ("receipt_schema_test", "trace_context_test"),
    ),
    PlaneSpec(
        "plane:test_eval",
        "Test And Eval Plane",
        "Unit tests, fixtures, evals, benchmarks, acceptance checks, and regression gates.",
        ("unit_test", "fixture", "eval", "benchmark", "regression_gate"),
        ("proof_requirements", "benchmark_hooks", "examples"),
        ("proof_receipt_required", "benchmark_receipt_required"),
    ),
    PlaneSpec(
        "plane:deployment_runtime",
        "Deployment Runtime Plane",
        "CLI, function, service, job, workflow, notebook, browser, and agent runtimes.",
        ("cli", "function", "service", "job", "workflow", "notebook", "browser", "agent"),
        ("runtime_targets", "effects", "architecture_variants"),
        ("runtime_smoke_test", "resource_policy_check"),
    ),
    PlaneSpec(
        "plane:cost_token",
        "Cost And Token Plane",
        "Token spend, cacheability, reuse rate, latency, and model-routing profile.",
        ("token_cost", "latency", "cacheability", "reuse_rate", "model_route"),
        ("benchmark_hooks", "rank_features", "composition"),
        ("token_savings_receipt", "latency_budget_check"),
    ),
    PlaneSpec(
        "plane:remix_variation",
        "Remix And Variation Plane",
        "Overlays, mutation affordances, specialization axes, and resolver policy.",
        ("variation_axis", "overlay", "mutator", "specialization", "resolver_policy"),
        ("mutation_affordances", "variation_overlay", "mutators"),
        ("overlay_resolution_test", "mutator_contract_test"),
    ),
    PlaneSpec(
        "plane:governance_promotion",
        "Governance And Promotion Plane",
        "Candidate state, promotion blockers, source review, owner review, and truth boundary.",
        ("candidate_state", "promotion_blocker", "owner_review", "truth_boundary", "license_gate"),
        ("candidate", "serves_truth", "promotion_blockers"),
        ("candidate_boundary_gate", "human_promotion_required"),
    ),
    PlaneSpec(
        "plane:negative_memory",
        "Negative Memory Plane",
        "Known traps, avoid-when clauses, misroutes, unsafe side effects, and anti-patterns.",
        ("avoid_when", "trap", "misroute", "unsafe_side_effect", "negative_memory"),
        ("avoid_when", "failure_modes", "negative_memory_refs"),
        ("negative_case_fixture", "misroute_guard"),
    ),
)


LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        "layer:intent",
        "Intent",
        "The user or system goal the primitive serves.",
        "What concrete intent does this plane expose, and what should be reusable across sources?",
        "intent_summary",
    ),
    LayerSpec(
        "layer:scope",
        "Scope",
        "What belongs inside versus outside the primitive boundary.",
        "What is inside this primitive boundary, what is outside, and where are the handoffs?",
        "scope_boundary",
    ),
    LayerSpec(
        "layer:source_evidence",
        "Source Evidence",
        "Which source refs, policies, and evidence support the candidate.",
        "Which source refs, licenses, digests, and evidence receipts are required for this plane?",
        "source_evidence",
    ),
    LayerSpec(
        "layer:componentization",
        "Componentization",
        "The subcomponents and reusable substeps.",
        "How should this plane break into components, component families, and reusable substeps?",
        "component_breakdown",
    ),
    LayerSpec(
        "layer:contract",
        "Contract",
        "Visible inputs, outputs, effects, and failure modes.",
        "What exact inputs, outputs, effects, errors, and postconditions must the primitive declare?",
        "contract_fields",
    ),
    LayerSpec(
        "layer:data_model",
        "Data Model",
        "Schemas, shape, type, and serialization.",
        "What schema, data shape, serialization, and cardinality does this plane need?",
        "data_model",
    ),
    LayerSpec(
        "layer:state",
        "State",
        "State machine, idempotency, and transitions.",
        "What state, idempotency, concurrency, retry, and rollback rules apply?",
        "state_model",
    ),
    LayerSpec(
        "layer:runtime",
        "Runtime",
        "Runtime targets and deployment shape.",
        "Which runtimes, deployment targets, resource classes, and integration shapes can run this primitive?",
        "runtime_targets",
    ),
    LayerSpec(
        "layer:example",
        "Example",
        "Concrete usage examples and fixtures.",
        "What examples, fixtures, and language variants prove this plane is usable?",
        "example_plan",
    ),
    LayerSpec(
        "layer:proof",
        "Proof",
        "Proof obligations and executable checks.",
        "What proof obligations, tests, receipts, and review gates are required before promotion?",
        "proof_requirements",
    ),
    LayerSpec(
        "layer:benchmark",
        "Benchmark",
        "Token, quality, latency, and reuse measurement.",
        "What benchmark hooks prove reuse, token savings, quality, latency, and cacheability?",
        "benchmark_hooks",
    ),
    LayerSpec(
        "layer:governance",
        "Governance",
        "Candidate boundary, privacy, license, and truth-state handling.",
        "What governance, privacy, license, candidate, and serves_truth boundaries apply?",
        "governance_controls",
    ),
    LayerSpec(
        "layer:remix",
        "Remix",
        "Variation axes and overlays.",
        "Which overlays, mutation axes, and remix routes can specialize this primitive safely?",
        "remix_axes",
    ),
    LayerSpec(
        "layer:promotion",
        "Promotion",
        "Promotion criteria and blockers.",
        "What must be true before this candidate can become a promoted primitive?",
        "promotion_checklist",
    ),
)


RUBRIC_ITEMS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("identity", "Stable primitive identity and group.", ("primitive_id", "primitive_group", "name")),
    ("purpose", "Problem/solution statement and fit/avoid guidance.", ("purpose", "fit_when", "avoid_when")),
    ("contract", "Explicit input/output contracts and visible edges.", ("input_contract", "output_contract", "input_edge", "output_edge")),
    ("effects", "Effects, runtime targets, and failure modes.", ("effects", "runtime_targets", "failure_modes")),
    ("source", "Source refs, graph refs, and evidence policy.", ("source_refs_sample", "graph_refs_sample", "license_provenance")),
    ("examples", "Language/runtime examples and acceptance checks.", ("example_refs_sample", "example_contracts")),
    ("proof", "Proof requirements and promotion blockers.", ("proof_requirements", "promotion_blockers")),
    ("remix", "Mutation affordances, overlays, and resolver policy.", ("mutation_affordances", "variation_overlay", "mutators")),
    ("benchmarks", "Token/reuse/quality benchmark hooks.", ("benchmark_hooks", "rank_features")),
    ("governance", "Candidate boundary and truth-state flags.", ("candidate", "serves_truth", "trust")),
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, length: int = 16) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:length]


def _slug(value: str, *, limit: int = 80) -> str:
    chars: list[str] = []
    for char in str(value).lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:limit] or "item"


def _token_estimate(value: Any) -> int:
    return max(1, len(_stable_json(value)) // CHARS_PER_TOKEN)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(row) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def build_plane_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, plane in enumerate(PLANE_SPECS, start=1):
        rows.append(
            {
                "record_type": "primitive_deconstruction_plane",
                "plane_id": plane.plane_id,
                "plane_index": index,
                "title": plane.title,
                "purpose": plane.purpose,
                "dimensions": list(plane.dimensions),
                "required_fields": list(plane.required_fields),
                "proof_implications": list(plane.proof_implications),
                "materialization_policy": "materialize_for_candidate_definition_and_hot_overlays",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def build_layer_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, layer in enumerate(LAYER_SPECS, start=1):
        rows.append(
            {
                "record_type": "primitive_deconstruction_layer",
                "layer_id": layer.layer_id,
                "layer_index": index,
                "title": layer.title,
                "purpose": layer.purpose,
                "question_stem": layer.question_stem,
                "required_output": layer.required_output,
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def _load_variation_atlas(limit: int) -> list[dict[str, Any]]:
    if limit == 0 or not VARIATION_ATLAS.exists():
        return []
    rows = _read_jsonl(VARIATION_ATLAS)
    if limit > 0:
        rows = rows[:limit]
    return rows


def build_dimension_rows(*, max_atlas_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plane in PLANE_SPECS:
        for ordinal, dimension in enumerate(plane.dimensions, start=1):
            rows.append(
                {
                    "record_type": "primitive_deconstruction_dimension",
                    "dimension_id": f"decomp-dim:{_slug(plane.plane_id)}.{_slug(dimension)}",
                    "plane_id": plane.plane_id,
                    "dimension_kind": dimension,
                    "title": dimension.replace("_", " ").title(),
                    "dimension_source": "deconstruction_plane_seed",
                    "values_seed": [],
                    "proof_implications": list(plane.proof_implications),
                    "applies_to": ["primitive_definition", "question_database", "completeness_rubric"],
                    "candidate": True,
                    "serves_truth": False,
                }
            )
    for row in _load_variation_atlas(max_atlas_rows):
        dimension_id = str(row.get("dimension_id") or f"atlas:{_sha(row, length=12)}")
        rows.append(
            {
                "record_type": "primitive_deconstruction_dimension",
                "dimension_id": f"atlas:{dimension_id}",
                "plane_id": "plane:remix_variation",
                "dimension_kind": str(row.get("dimension_kind") or row.get("variation_axis") or "variation"),
                "title": str(row.get("title") or dimension_id).strip(),
                "dimension_source": "primitive_variation_dimension_atlas",
                "variation_axis": str(row.get("variation_axis") or ""),
                "values_seed": row.get("values_seed") or [],
                "proof_implications": row.get("proof_implications") or [],
                "source_dimension_ref": dimension_id,
                "source_evidence_status": row.get("source_evidence_status", ""),
                "applies_to": row.get("applies_to") or ["primitive_contract", "overlay_resolver"],
                "candidate": True,
                "serves_truth": False,
            }
        )
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[row["dimension_id"]] = row
    return list(deduped.values())


def build_rubric_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (key, title, fields) in enumerate(RUBRIC_ITEMS, start=1):
        rows.append(
            {
                "record_type": "primitive_definition_completeness_rubric_item",
                "rubric_id": f"rubric:{key}",
                "rubric_index": index,
                "title": title,
                "required_fields": list(fields),
                "weight": 1,
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def build_question_rows(
    planes: list[dict[str, Any]],
    layers: list[dict[str, Any]],
    dimensions: list[dict[str, Any]],
    *,
    base_question_count: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ordinal = 1
    for plane in planes:
        for layer in layers:
            prompt = (
                f"{layer['question_stem']} Plane: {plane['title']}. "
                f"Required primitive fields: {', '.join(plane['required_fields'])}. "
                "Return candidate-only fields, examples, proofs, gaps, and promotion blockers."
            )
            rows.append(
                {
                    "record_type": "primitive_deconstruction_question",
                    "question_id": f"dq/{_slug(plane['plane_id'])}/{_slug(layer['layer_id'])}",
                    "ordinal": ordinal,
                    "plane_id": plane["plane_id"],
                    "layer_id": layer["layer_id"],
                    "dimension_id": "",
                    "question_family": "plane_layer",
                    "prompt": prompt,
                    "expected_output": layer["required_output"],
                    "candidate": True,
                    "serves_truth": False,
                }
            )
            ordinal += 1
    base_questions = generate_question_bank(base_question_count)
    for base in base_questions:
        rows.append(
            {
                "record_type": "primitive_deconstruction_question",
                "question_id": f"continuous/{base['question_id']}",
                "ordinal": ordinal,
                "plane_id": "plane:component_boundary",
                "layer_id": "layer:componentization",
                "dimension_id": "",
                "question_family": "continuous_source_question_bank",
                "prompt": base["prompt"],
                "expected_output": base["expected_answer_contract"],
                "source_question_id": base["question_id"],
                "candidate": True,
                "serves_truth": False,
            }
        )
        ordinal += 1
    for dimension in dimensions:
        rows.append(
            {
                "record_type": "primitive_deconstruction_question",
                "question_id": f"dimq/{_slug(dimension['dimension_id'], limit=90)}",
                "ordinal": ordinal,
                "plane_id": dimension.get("plane_id", "plane:remix_variation"),
                "layer_id": "layer:remix",
                "dimension_id": dimension["dimension_id"],
                "question_family": "dimension_overlay",
                "prompt": (
                    f"How does dimension '{dimension['title']}' change primitive contracts, examples, "
                    "proof requirements, overlays, resolver behavior, and promotion blockers?"
                ),
                "expected_output": "dimension_overlay_impact",
                "candidate": True,
                "serves_truth": False,
            }
        )
        ordinal += 1
    return rows


def build_plane_question_edges(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for question in questions:
        rows.append(
            {
                "record_type": "primitive_deconstruction_question_edge",
                "edge_id": f"edge/{_sha({'q': question['question_id'], 'plane': question['plane_id'], 'layer': question['layer_id']}, length=16)}",
                "question_id": question["question_id"],
                "plane_id": question["plane_id"],
                "layer_id": question["layer_id"],
                "dimension_id": question.get("dimension_id", ""),
                "relation": "asks_about",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def build_deconstruction_database(
    *,
    database_dir: Path,
    base_question_count: int,
    max_atlas_rows: int,
) -> dict[str, Any]:
    planes = build_plane_rows()
    layers = build_layer_rows()
    dimensions = build_dimension_rows(max_atlas_rows=max_atlas_rows)
    questions = build_question_rows(planes, layers, dimensions, base_question_count=base_question_count)
    edges = build_plane_question_edges(questions)
    rubric = build_rubric_rows()
    manifest = {
        "record_type": "primitive_deconstruction_database_manifest",
        "created_at": _utc(),
        "plane_count": len(planes),
        "layer_count": len(layers),
        "dimension_count": len(dimensions),
        "question_count": len(questions),
        "question_edge_count": len(edges),
        "rubric_item_count": len(rubric),
        "files": {
            "deconstruction_planes": "deconstruction_planes.jsonl",
            "analysis_layers": "analysis_layers.jsonl",
            "deconstruction_dimensions": "deconstruction_dimensions.jsonl",
            "question_database": "question_database.jsonl",
            "plane_question_edges": "plane_question_edges.jsonl",
            "completeness_rubric": "completeness_rubric.jsonl",
            "manifest": "manifest.json",
        },
        "database_digest": "sha256:"
        + hashlib.sha256(_stable_json({"planes": planes, "layers": layers, "dimensions": dimensions, "questions": questions}).encode("utf-8")).hexdigest(),
        "candidate": True,
        "serves_truth": False,
    }
    _write_jsonl(database_dir / "deconstruction_planes.jsonl", planes)
    _write_jsonl(database_dir / "analysis_layers.jsonl", layers)
    _write_jsonl(database_dir / "deconstruction_dimensions.jsonl", dimensions)
    _write_jsonl(database_dir / "question_database.jsonl", questions)
    _write_jsonl(database_dir / "plane_question_edges.jsonl", edges)
    _write_jsonl(database_dir / "completeness_rubric.jsonl", rubric)
    _write_json(database_dir / "manifest.json", manifest)
    return {
        "manifest": manifest,
        "planes": planes,
        "layers": layers,
        "dimensions": dimensions,
        "questions": questions,
        "edges": edges,
        "rubric": rubric,
    }


def _latest_continuous_run_dir() -> Path:
    latest = CONTINUOUS_OUT_DIR / "latest_status.json"
    if not latest.exists():
        raise FileNotFoundError(f"no continuous loop latest status at {latest}")
    status = json.loads(latest.read_text(encoding="utf-8"))
    run_dir = Path(status.get("outputs", {}).get("run_dir") or "")
    if not run_dir.exists():
        raise FileNotFoundError(f"continuous loop run_dir does not exist: {run_dir}")
    return run_dir


def _load_candidate_inputs(run_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        "primitives": _read_jsonl(run_dir / "llm_primitive_candidates.jsonl"),
        "examples": _read_jsonl(run_dir / "primitive_examples.jsonl"),
        "graphs": _read_jsonl(run_dir / "primitive_graphs.jsonl"),
        "decompositions": _read_jsonl(run_dir / "llm_decompositions.jsonl"),
        "snapshots": _read_jsonl(run_dir / "source_snapshots.jsonl"),
    }


def _index_examples(examples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in examples:
        grouped[str(row.get("primitive_id") or "")].append(row)
    return grouped


def _index_graphs(graphs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for graph in graphs:
        primitive_ids = [
            node.get("id")
            for node in graph.get("nodes", [])
            if isinstance(node, dict) and node.get("kind") == "primitive_candidate"
        ]
        for primitive_id in primitive_ids:
            grouped[str(primitive_id)].append(graph)
    return grouped


def _dimension_match_score(primitive: dict[str, Any], dimension: dict[str, Any]) -> int:
    haystack = " ".join(
        [
            str(primitive.get("primitive_id", "")),
            str(primitive.get("name", "")),
            str(primitive.get("purpose", "")),
            str(primitive.get("source_kind", "")),
            str(primitive.get("component_family", "")),
            " ".join(str(x) for x in primitive.get("mutation_affordances", [])),
            " ".join(str(x) for x in primitive.get("language_variants", [])),
            " ".join(str(x) for x in primitive.get("architecture_variants", [])),
            " ".join(str(x) for x in primitive.get("design_system_variants", [])),
        ]
    ).lower()
    score = 0
    for field in ("dimension_kind", "variation_axis", "title"):
        for token in str(dimension.get(field) or "").lower().replace("_", " ").split():
            if len(token) >= 3 and token in haystack:
                score += 2 if field == "variation_axis" else 1
    for token in dimension.get("values_seed", []) or []:
        text = str(token).lower().replace("_", " ")
        if text and any(part in haystack for part in text.split()):
            score += 1
    if dimension.get("plane_id") in {"plane:primitive_contract", "plane:source_context", "plane:governance_promotion"}:
        score += 1
    return score


def _select_overlays(primitive: dict[str, Any], dimensions: list[dict[str, Any]], *, overlays_per_primitive: int) -> list[dict[str, Any]]:
    scored = [(_dimension_match_score(primitive, dim), dim) for dim in dimensions]
    selected = [dim for score, dim in sorted(scored, key=lambda item: (-item[0], item[1]["dimension_id"])) if score > 0]
    if len(selected) < overlays_per_primitive:
        fallback_ids = {
            "decomp-dim:plane-source-context.source-kind",
            "decomp-dim:plane-primitive-contract.input-edge",
            "decomp-dim:plane-test-eval.benchmark",
            "decomp-dim:plane-remix-variation.variation-axis",
            "decomp-dim:plane-governance-promotion.promotion-blocker",
        }
        for dim in dimensions:
            if dim["dimension_id"] in fallback_ids and dim not in selected:
                selected.append(dim)
    return selected[:max(overlays_per_primitive, 0)]


def _edge_name(contract: dict[str, Any], fallback: str) -> str:
    shape = str(contract.get("shape") or fallback)
    required = "+".join(str(item) for item in contract.get("required", [])[:3])
    return f"{shape}{('+' + required) if required else ''}"


def _candidate_checks(row: dict[str, Any], rubric: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for item in rubric:
        fields = item.get("required_fields") or []
        present = []
        missing = []
        for field in fields:
            value = row.get(field)
            if value not in (None, "", [], {}):
                present.append(field)
            else:
                missing.append(field)
        checks.append(
            {
                "rubric_id": item["rubric_id"],
                "present": present,
                "missing": missing,
                "passed": not missing,
            }
        )
    passed = sum(1 for check in checks if check["passed"])
    return {
        "passed": passed,
        "total": len(checks),
        "score": round(passed / max(len(checks), 1), 4),
        "checks": checks,
    }


def _fully_defined_candidate(
    primitive: dict[str, Any],
    *,
    overlay: dict[str, Any] | None,
    examples: list[dict[str, Any]],
    graphs: list[dict[str, Any]],
    planes: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    rubric: list[dict[str, Any]],
    database_manifest: dict[str, Any],
) -> dict[str, Any]:
    primitive_id = str(primitive.get("primitive_id") or f"primitive/unknown/{_sha(primitive, length=8)}")
    overlay_id = str((overlay or {}).get("dimension_id") or "base")
    overlay_slug = _slug(overlay_id, limit=48)
    definition_id = f"fdp/{_slug(primitive_id, limit=70)}/{overlay_slug}"
    input_contract = primitive.get("input_contract") or {"shape": "UnknownInput", "required": []}
    output_contract = primitive.get("output_contract") or {"shape": "UnknownOutput", "required": []}
    mutation_affordances = list(primitive.get("mutation_affordances") or [])
    if overlay and overlay.get("variation_axis") and overlay["variation_axis"] not in mutation_affordances:
        mutation_affordances.append(str(overlay["variation_axis"]))
    proof_requirements = sorted(
        set(
            [
                "candidate_boundary_gate",
                "source_ref_review",
                "license_review",
                "example_contract_tests",
                "benchmark_receipt_required",
                "human_promotion_required",
                *(primitive.get("proof_requirements") or []),
                *((overlay or {}).get("proof_implications") or []),
            ]
        )
    )
    example_contracts = [
        {
            "example_id": example.get("example_id"),
            "language": example.get("language"),
            "acceptance_checks": example.get("acceptance_checks") or [],
        }
        for example in examples[:12]
    ]
    graph_refs = [graph.get("graph_id") for graph in graphs if graph.get("graph_id")]
    source_refs = primitive.get("source_refs_sample") or []
    language_variants = primitive.get("language_variants") or []
    architecture_variants = primitive.get("architecture_variants") or []
    runtime_targets = sorted(
        set(
            [
                "py.fn" if "python" in language_variants else "",
                "ts.module" if "typescript" in language_variants else "",
                "sql.query" if "sql" in language_variants else "",
                *(str(item).replace("_", ".") for item in architecture_variants),
            ]
        )
        - {""}
    )
    row = {
        "record_type": "fully_defined_primitive_candidate",
        "definition_id": definition_id,
        "primitive_id": primitive_id if overlay is None else f"{primitive_id}/overlay/{overlay_slug}",
        "base_primitive_ref": primitive_id,
        "primitive_group": primitive.get("primitive_group") or "",
        "name": primitive.get("name") or primitive_id,
        "title": str(primitive.get("name") or primitive_id).replace(".", " ").replace("-", " ").title(),
        "source_kind": primitive.get("source_kind") or "",
        "component_family": primitive.get("component_family") or "",
        "purpose": primitive.get("purpose") or "",
        "fit_when": f"Use when the task needs {primitive.get('component_family', 'this component')} with explicit source refs, contracts, examples, and proof receipts.",
        "avoid_when": "Avoid promotion or serving truth until source/license/proof review and executable fixtures pass.",
        "input_contract": input_contract,
        "output_contract": output_contract,
        "input_edge": _edge_name(input_contract, "PrimitiveInput"),
        "output_edge": _edge_name(output_contract, "PrimitiveOutput"),
        "edge_contract": {
            "visible_input_edge": _edge_name(input_contract, "PrimitiveInput"),
            "visible_output_edge": _edge_name(output_contract, "PrimitiveOutput"),
            "hidden_member_edges": [
                "SourceRef -> SourceBackedComponent",
                "SourceBackedComponent -> PrimitiveCandidatePayload",
                "PrimitiveCandidatePayload -> ProofReceipt",
            ],
            "preconditions": "Input satisfies declared schema, source authority, privacy policy, and candidate boundary.",
            "postconditions": "Candidate receipt records source refs, effects, examples, proofs, and blockers.",
        },
        "hidden_member_edges": [
            "SourceRef -> ComponentBreakdown",
            "ComponentBreakdown -> PrimitiveContract",
            "PrimitiveContract+ExampleFixture -> ProofReceipt",
        ],
        "effects": primitive.get("effects") or ["cpu", "artifact_write"],
        "runtime_targets": runtime_targets or ["py.fn", "workflow.step"],
        "failure_modes": [
            "schema_drift",
            "missing_source_authority",
            "license_not_reviewed",
            "unsafe_side_effect",
            "insufficient_example_coverage",
        ],
        "source_refs_sample": source_refs,
        "graph_refs_sample": primitive.get("graph_refs_sample") or graph_refs[:20],
        "example_refs_sample": primitive.get("example_refs_sample") or [example.get("example_id") for example in examples[:20]],
        "example_contracts": example_contracts,
        "language_variants": language_variants,
        "architecture_variants": architecture_variants,
        "design_system_variants": primitive.get("design_system_variants") or [],
        "mutation_affordances": mutation_affordances,
        "mutators": [f"mut:{_slug(axis, limit=40)}" for axis in mutation_affordances[:12]],
        "variation_overlay": (
            {
                "overlay_kind": "base_definition",
                "dimension_id": "",
                "title": "Base fully defined candidate",
            }
            if overlay is None
            else {
                "overlay_kind": "dimension_overlay",
                "dimension_id": overlay.get("dimension_id"),
                "title": overlay.get("title"),
                "variation_axis": overlay.get("variation_axis", ""),
                "values_seed": overlay.get("values_seed", []),
                "dimension_source": overlay.get("dimension_source", ""),
            }
        ),
        "deconstruction_coverage": {
            "plane_ids": [plane["plane_id"] for plane in planes],
            "plane_count": len(planes),
            "question_count": len(questions),
            "question_database_digest": database_manifest["database_digest"],
        },
        "proof_requirements": proof_requirements,
        "benchmark_hooks": [
            "token_savings_vs_prompt_only",
            "route_reuse_count",
            "proof_pass_rate",
            "source_escalation_depth",
            "example_fixture_pass_rate",
        ],
        "rank_features": {
            "definition_completeness": 0,
            "source_support_count": primitive.get("source_support_count", 0),
            "example_count": len(examples),
            "graph_count": len(graphs),
            "overlay_specificity": 0 if overlay is None else 1,
        },
        "license_provenance": primitive.get("license_provenance")
        or {"status": "candidate_requires_license_review", "source_policy": "metadata_and_citation_first"},
        "promotion_blockers": [
            "source_refs_need_review",
            "license_review_required",
            "executable_fixture_receipts_required",
            "benchmark_receipt_required",
            "human_promotion_required",
        ],
        "negative_memory_refs": [
            f"neg:{_slug(primitive.get('component_family') or primitive_id, limit=40)}.do_not_serve_truth_from_candidate",
            f"neg:{_slug(primitive.get('component_family') or primitive_id, limit=40)}.do_not_store_raw_source_body",
        ],
        "trust": "candidate",
        "fully_defined_candidate": True,
        "promotion_ready": False,
        "candidate": True,
        "serves_truth": False,
    }
    completeness = _candidate_checks(row, rubric)
    row["completeness"] = completeness
    row["rank_features"]["definition_completeness"] = completeness["score"]
    return row


def _compact_refinement_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Small model payload for refinement. Full rows are stored locally; model calls get a bounded view."""
    completeness = row.get("completeness") or {}
    return {
        "definition_id": row.get("definition_id"),
        "primitive_id": row.get("primitive_id"),
        "base_primitive_ref": row.get("base_primitive_ref"),
        "name": row.get("name"),
        "source_kind": row.get("source_kind"),
        "component_family": row.get("component_family"),
        "purpose": row.get("purpose"),
        "fit_when": row.get("fit_when"),
        "avoid_when": row.get("avoid_when"),
        "input_edge": row.get("input_edge"),
        "output_edge": row.get("output_edge"),
        "input_contract": row.get("input_contract"),
        "output_contract": row.get("output_contract"),
        "effects": row.get("effects", [])[:12],
        "runtime_targets": row.get("runtime_targets", [])[:12],
        "failure_modes": row.get("failure_modes", [])[:12],
        "mutation_affordances": row.get("mutation_affordances", [])[:16],
        "variation_overlay": row.get("variation_overlay"),
        "proof_requirements": row.get("proof_requirements", [])[:16],
        "promotion_blockers": row.get("promotion_blockers", [])[:16],
        "benchmark_hooks": row.get("benchmark_hooks", [])[:12],
        "example_refs_sample": row.get("example_refs_sample", [])[:8],
        "graph_refs_sample": row.get("graph_refs_sample", [])[:8],
        "source_refs_sample": row.get("source_refs_sample", [])[:8],
        "completeness": {
            "score": completeness.get("score"),
            "failed_rubric_ids": [
                check.get("rubric_id")
                for check in completeness.get("checks", [])
                if isinstance(check, dict) and not check.get("passed")
            ],
        },
        "candidate": True,
        "serves_truth": False,
    }


def materialize_fully_defined_primitives(
    *,
    run_dir: Path,
    database: dict[str, Any],
    overlays_per_primitive: int,
    max_base_primitives: int,
) -> list[dict[str, Any]]:
    inputs = _load_candidate_inputs(run_dir)
    primitives = inputs["primitives"]
    if max_base_primitives > 0:
        primitives = primitives[:max_base_primitives]
    examples_by_primitive = _index_examples(inputs["examples"])
    graphs_by_primitive = _index_graphs(inputs["graphs"])
    dimensions = database["dimensions"]
    rows: list[dict[str, Any]] = []
    for primitive in primitives:
        primitive_id = str(primitive.get("primitive_id") or "")
        examples = examples_by_primitive.get(primitive_id, [])
        graphs = graphs_by_primitive.get(primitive_id, [])
        rows.append(
            _fully_defined_candidate(
                primitive,
                overlay=None,
                examples=examples,
                graphs=graphs,
                planes=database["planes"],
                questions=database["questions"],
                rubric=database["rubric"],
                database_manifest=database["manifest"],
            )
        )
        for overlay in _select_overlays(primitive, dimensions, overlays_per_primitive=overlays_per_primitive):
            rows.append(
                _fully_defined_candidate(
                    primitive,
                    overlay=overlay,
                    examples=examples,
                    graphs=graphs,
                    planes=database["planes"],
                    questions=database["questions"],
                    rubric=database["rubric"],
                    database_manifest=database["manifest"],
                )
            )
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[row["definition_id"]] = row
    return list(deduped.values())


def _refine_with_model(
    row: dict[str, Any],
    *,
    provider_name: str,
    mode: str,
    model: str,
    max_tokens: int,
    timeout: int,
    cdp_url: str,
) -> dict[str, Any]:
    system = (
        "You review primitive candidate definitions. Return JSON only with missing_fields, "
        "extra_proof_requirements, extra_failure_modes, and concise_rationale. Candidate-only; never truth."
    )
    prompt = json.dumps(
        {
            "task": "Review this fully defined primitive candidate for missing deconstruction dimensions.",
            "candidate": _compact_refinement_payload(row),
            "return_contract": {
                "missing_fields": "list[str]",
                "extra_proof_requirements": "list[str]",
                "extra_failure_modes": "list[str]",
                "concise_rationale": "string",
                "candidate": True,
                "serves_truth": False,
            },
        },
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
    )
    if provider_name == "openwebui" and mode == "cdp":
        try:
            from scripts.openwebui_cdp_client import cdp_chat  # noqa: E402

            normalized = cdp_chat(prompt, system=system, model=model or None, cdp_url=cdp_url or None, max_tokens=max_tokens, timeout=timeout)
            return {
                "provider": "openwebui",
                "mode": "cdp",
                "model": normalized.get("model") or model,
                "text": normalized.get("assistant_content") or "",
                "usage": normalized.get("usage") or {},
                "finish_reason": normalized.get("finish_reason"),
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            return {"provider": provider_name, "mode": mode, "model": model, "text": "", "usage": {}, "finish_reason": None, "error": f"{type(exc).__name__}: {exc}"}
    provider = resolve_provider(provider_name)
    model_id = model or (PROVIDERS.get(provider_name, {}).get("models") or [""])[0]
    result = chat(model_id, system, prompt, provider, max_tokens=max_tokens, timeout=timeout)
    return {
        "provider": provider_name,
        "mode": "direct",
        "model": model_id,
        "text": result.get("text") or "",
        "usage": result.get("usage") or {},
        "finish_reason": result.get("finish_reason"),
        "error": result.get("error"),
    }


def build_database_feed(run_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    feed: list[dict[str, Any]] = []
    for row in rows:
        feed.append(
            {
                "record_type": "primitive_database_feed_row",
                "feed_id": f"feed/fully-defined/{_slug(row['definition_id'], limit=80)}-{_sha({'run': run_id, 'id': row['definition_id']}, length=10)}",
                "run_id": run_id,
                "target_registry": "fully_defined_primitive_candidates",
                "operation": "stage_candidate",
                "payload_id": row["definition_id"],
                "payload_digest": "sha256:" + hashlib.sha256(_stable_json(row).encode("utf-8")).hexdigest(),
                "payload": row,
                "promotion_state": "staged_requires_source_license_proof_and_benchmark",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return feed


def _assert_candidate_rows(path: Path) -> None:
    for jsonl_path in path.rglob("*.jsonl"):
        for row in _read_jsonl(jsonl_path):
            if row.get("candidate") is not True:
                raise AssertionError(f"{jsonl_path}: row must be candidate")
            if row.get("serves_truth") is not False:
                raise AssertionError(f"{jsonl_path}: row must have serves_truth=false")


def run_pipeline(
    *,
    output_dir: Path,
    database_dir: Path,
    from_run_dir: Path | None = None,
    run_continuous_first: bool = False,
    source_limit: int = 36,
    question_count: int = DEFAULT_QUESTION_COUNT,
    max_atlas_rows: int = 250,
    overlays_per_primitive: int = 4,
    max_base_primitives: int = 0,
    use_llm: bool = False,
    provider_name: str = DEFAULT_PROVIDER,
    mode: str = "direct",
    model: str = "",
    llm_refine_limit: int = 0,
    llm_max_tokens: int = 1024,
    llm_timeout: int = 120,
    cdp_url: str = "",
) -> dict[str, Any]:
    started = time.time()
    run_id = f"primitive-deconstruction-plane-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    pipeline_run_dir = output_dir / "runs" / run_id
    database = build_deconstruction_database(
        database_dir=database_dir,
        base_question_count=question_count,
        max_atlas_rows=max_atlas_rows,
    )
    if run_continuous_first:
        continuous_summary = run_continuous_loop(
            output_dir=CONTINUOUS_OUT_DIR,
            source_limit=source_limit,
            question_count=question_count,
            max_components=5,
            max_sources_per_partition=25,
        )
        source_run_dir = Path(continuous_summary["outputs"]["run_dir"])
    else:
        source_run_dir = from_run_dir or _latest_continuous_run_dir()
    definitions = materialize_fully_defined_primitives(
        run_dir=source_run_dir,
        database=database,
        overlays_per_primitive=overlays_per_primitive,
        max_base_primitives=max_base_primitives,
    )
    model_refinements: list[dict[str, Any]] = []
    if use_llm:
        limit = llm_refine_limit if llm_refine_limit > 0 else len(definitions)
        for row in definitions[:limit]:
            result = _refine_with_model(
                row,
                provider_name=provider_name,
                mode=mode,
                model=model,
                max_tokens=llm_max_tokens,
                timeout=llm_timeout,
                cdp_url=cdp_url,
            )
            row["model_refinement"] = {
                "provider": result["provider"],
                "mode": result["mode"],
                "model": result["model"],
                "response_digest": "sha256:" + hashlib.sha256(str(result.get("text") or "").encode("utf-8")).hexdigest(),
                "usage": result.get("usage") or {},
                "finish_reason": result.get("finish_reason"),
                "error": result.get("error"),
                "candidate": True,
                "serves_truth": False,
            }
            model_refinements.append(row["model_refinement"])
    feed = build_database_feed(run_id, definitions)
    completeness_scores = [row.get("completeness", {}).get("score", 0) for row in definitions]
    source_counts = Counter(row.get("source_kind", "unknown") for row in definitions)
    summary = {
        "record_type": RECORD_TYPE,
        "run_id": run_id,
        "created_at": _utc(),
        "seconds": round(time.time() - started, 3),
        "source_run_dir": str(source_run_dir),
        "database_dir": str(database_dir),
        "plane_count": database["manifest"]["plane_count"],
        "layer_count": database["manifest"]["layer_count"],
        "dimension_count": database["manifest"]["dimension_count"],
        "question_count": database["manifest"]["question_count"],
        "question_edge_count": database["manifest"]["question_edge_count"],
        "rubric_item_count": database["manifest"]["rubric_item_count"],
        "fully_defined_primitive_candidates": len(definitions),
        "primitive_database_feed_rows": len(feed),
        "source_kind_counts": dict(sorted(source_counts.items())),
        "avg_completeness_score": round(sum(completeness_scores) / max(len(completeness_scores), 1), 4),
        "llm_enabled": use_llm,
        "llm_provider": provider_name if use_llm else "",
        "llm_mode": mode if use_llm else "",
        "llm_model_refinements": len(model_refinements),
        "llm_errors": sum(1 for row in model_refinements if row.get("error")),
        "token_proxy": {
            "database_tokens": _token_estimate(database["manifest"]),
            "definition_tokens": _token_estimate(definitions),
            "feed_digest_tokens": _token_estimate(
                [{"payload_id": row["payload_id"], "payload_digest": row["payload_digest"]} for row in feed]
            ),
        },
        "outputs": {
            "run_dir": str(pipeline_run_dir),
            "fully_defined_primitive_candidates": "fully_defined_primitive_candidates.jsonl",
            "primitive_database_feed": "primitive_database_feed.jsonl",
            "model_refinements": "model_refinements.jsonl",
            "benchmark_receipt": "benchmark_receipt.json",
            "latest_status": str(output_dir / "latest_status.json"),
            "loop_ledger": str(output_dir / "loop_ledger.jsonl"),
        },
        "governance": {
            "generated_rows_are_candidates": True,
            "serves_truth": False,
            "promotion_required": "source/license/proof review plus primitive registry promotion gate",
            "fully_defined_means": "candidate record has full contract/examples/proofs/bench hooks, not promoted truth",
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_jsonl(pipeline_run_dir / "fully_defined_primitive_candidates.jsonl", definitions)
    _write_jsonl(pipeline_run_dir / "primitive_database_feed.jsonl", feed)
    _write_jsonl(pipeline_run_dir / "model_refinements.jsonl", model_refinements)
    _write_json(pipeline_run_dir / "benchmark_receipt.json", summary)
    _write_json(output_dir / "latest_status.json", summary)
    _append_jsonl(output_dir / "loop_ledger.jsonl", summary)
    return summary


def _fixture_run_dir(root: Path) -> Path:
    run_dir = root / "continuous-run"
    primitive = {
        "record_type": "llm_primitive_candidate",
        "primitive_id": "primitive/app/state-model",
        "primitive_group": "grp:app.state-model@candidate",
        "name": "app.state_model",
        "purpose": "Reusable state model primitive for workflow apps.",
        "source_kind": "app",
        "component_family": "state_model",
        "input_contract": {"shape": "SourceBackedComponent", "required": ["source_ref", "payload"]},
        "output_contract": {"shape": "PrimitiveCandidatePayload", "required": ["candidate", "proof_obligation"]},
        "mutation_affordances": ["role_policy", "state_backend", "event_model"],
        "language_variants": ["python", "typescript", "sql"],
        "architecture_variants": ["service_endpoint", "agent_tool"],
        "design_system_variants": ["dashboard_component", "headless_contract"],
        "source_refs_sample": ["src/test/app/state"],
        "source_support_count": 1,
        "graph_refs_sample": ["graph/app/test"],
        "example_refs_sample": ["example/python/test", "example/typescript/test", "example/sql/test"],
        "license_provenance": {"status": "candidate_requires_license_review", "source_policy": "metadata_and_citation_first"},
        "trust": "candidate",
        "candidate": True,
        "serves_truth": False,
    }
    examples = [
        {
            "record_type": "primitive_example_candidate",
            "example_id": f"example/{language}/test",
            "primitive_id": "primitive/app/state-model",
            "language": language,
            "acceptance_checks": ["input contract", "output contract", "candidate receipt"],
            "candidate": True,
            "serves_truth": False,
        }
        for language in ("python", "typescript", "sql")
    ]
    graph = {
        "record_type": "primitive_graph_candidate",
        "graph_id": "graph/app/test",
        "nodes": [
            {"id": "src/test/app/state", "kind": "source"},
            {"id": "primitive/app/state-model", "kind": "primitive_candidate"},
        ],
        "edges": [{"from": "src/test/app/state", "to": "primitive/app/state-model", "relation": "maps_to"}],
        "candidate": True,
        "serves_truth": False,
    }
    _write_jsonl(run_dir / "llm_primitive_candidates.jsonl", [primitive])
    _write_jsonl(run_dir / "primitive_examples.jsonl", examples)
    _write_jsonl(run_dir / "primitive_graphs.jsonl", [graph])
    _write_jsonl(run_dir / "llm_decompositions.jsonl", [])
    _write_jsonl(run_dir / "source_snapshots.jsonl", [])
    return run_dir


def _self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="primitive-deconstruction-plane-test-") as temp:
        root = Path(temp)
        source_run_dir = _fixture_run_dir(root)
        output_dir = root / "out"
        database_dir = root / "database"
        summary = run_pipeline(
            output_dir=output_dir,
            database_dir=database_dir,
            from_run_dir=source_run_dir,
            question_count=120,
            max_atlas_rows=20,
            overlays_per_primitive=3,
            max_base_primitives=1,
        )
        _assert_candidate_rows(output_dir)
        _assert_candidate_rows(database_dir)
        assert summary["plane_count"] >= 15
        assert summary["layer_count"] >= 10
        assert summary["dimension_count"] >= 80
        assert summary["question_count"] >= 300
        assert summary["fully_defined_primitive_candidates"] == 4
        assert summary["primitive_database_feed_rows"] == 4
        assert summary["avg_completeness_score"] >= 0.9
        latest = json.loads((output_dir / "latest_status.json").read_text(encoding="utf-8"))
        assert latest["run_id"] == summary["run_id"]
        rows = _read_jsonl(Path(summary["outputs"]["run_dir"]) / "fully_defined_primitive_candidates.jsonl")
        assert all(row["fully_defined_candidate"] is True and row["promotion_ready"] is False for row in rows)
    print(
        "PASS - primitive_deconstruction_plane_pipeline: builds deconstruction planes/layers/"
        "dimensions/questions/rubric and materializes fully-defined primitive candidate feed rows."
    )
    return 0


def _run_watch(args: argparse.Namespace) -> int:
    tick = 0
    while True:
        tick += 1
        summary = run_pipeline(
            output_dir=Path(args.out_dir),
            database_dir=Path(args.database_dir),
            from_run_dir=Path(args.from_run_dir) if args.from_run_dir else None,
            run_continuous_first=args.run_continuous_first,
            source_limit=args.source_limit,
            question_count=args.question_count,
            max_atlas_rows=args.max_atlas_rows,
            overlays_per_primitive=args.overlays_per_primitive,
            max_base_primitives=args.max_base_primitives,
            use_llm=args.use_llm,
            provider_name=args.provider,
            mode=args.mode,
            model=args.model,
            llm_refine_limit=args.llm_refine_limit,
            llm_max_tokens=args.llm_max_tokens,
            llm_timeout=args.llm_timeout,
            cdp_url=args.cdp_url,
        )
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
        print(f"written: {Path(args.out_dir)}")
        if args.max_ticks and tick >= args.max_ticks:
            return 0
        time.sleep(args.interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deconstruction-plane DB and materialize fully-defined primitive candidates.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=3600)
    parser.add_argument("--max-ticks", type=int, default=0)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--database-dir", default=str(DEFAULT_DATABASE_DIR))
    parser.add_argument("--from-run-dir", default="", help="Continuous loop run directory to consume. Defaults to latest.")
    parser.add_argument("--run-continuous-first", action="store_true", help="Run continuous_primitive_scrape_loop first, then materialize definitions.")
    parser.add_argument("--source-limit", type=int, default=36)
    parser.add_argument("--question-count", type=int, default=360)
    parser.add_argument("--max-atlas-rows", type=int, default=250, help="0 disables primitive variation atlas import.")
    parser.add_argument("--overlays-per-primitive", type=int, default=4)
    parser.add_argument("--max-base-primitives", type=int, default=0, help="0 means all base primitives from the source run.")
    parser.add_argument("--use-llm", action="store_true", help="Optionally refine definitions with a model lane.")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=sorted(PROVIDERS))
    parser.add_argument("--mode", default="direct", choices=["direct", "cdp"], help="Use cdp only with provider=openwebui.")
    parser.add_argument("--model", default="")
    parser.add_argument("--llm-refine-limit", type=int, default=0)
    parser.add_argument("--llm-max-tokens", type=int, default=1024)
    parser.add_argument("--llm-timeout", type=int, default=120)
    parser.add_argument("--cdp-url", default="")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.watch:
        return _run_watch(args)
    if not args.run:
        parser.error("pass --run, --watch, or --self-test")
    summary = run_pipeline(
        output_dir=Path(args.out_dir),
        database_dir=Path(args.database_dir),
        from_run_dir=Path(args.from_run_dir) if args.from_run_dir else None,
        run_continuous_first=args.run_continuous_first,
        source_limit=args.source_limit,
        question_count=args.question_count,
        max_atlas_rows=args.max_atlas_rows,
        overlays_per_primitive=args.overlays_per_primitive,
        max_base_primitives=args.max_base_primitives,
        use_llm=args.use_llm,
        provider_name=args.provider,
        mode=args.mode,
        model=args.model,
        llm_refine_limit=args.llm_refine_limit,
        llm_max_tokens=args.llm_max_tokens,
        llm_timeout=args.llm_timeout,
        cdp_url=args.cdp_url,
    )
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    print(f"written: {Path(args.out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
