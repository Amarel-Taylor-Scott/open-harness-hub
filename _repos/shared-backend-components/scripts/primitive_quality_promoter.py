#!/usr/bin/env python3
"""Deterministic primitive quality sieve for AIDevObserver and Teleon.

The primitive builder intentionally creates a broad real-source candidate
substrate. This script turns that broad substrate into ranked quality classes:

* noisy symbol-level rows that should not be surfaced by default;
* candidates that need contract enrichment;
* high-value candidates worth review;
* AIDevObserver-surfaceable candidates with clear blackbox + I/O edges.

It does not promote records and never flips ``serves_truth``. Promotion remains
the proof/owner-review gate in ``_repos/shared-backend-components/scripts/check_primitive_registry_promotion_gate.py``.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import ast
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (
    PRIMITIVE_QUALITY_ARTIFACT_FILES,
    PRIMITIVE_QUALITY_CLASS_HIGH_VALUE,
    PRIMITIVE_QUALITY_CLASS_HOLD,
    PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT,
    PRIMITIVE_QUALITY_CLASS_NOISE,
    PRIMITIVE_QUALITY_CLASS_SURFACEABLE,
    PRIMITIVE_QUALITY_DIRNAME,
    PRIMITIVE_QUALITY_DOMAIN_RULES,
    PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE,
    PRIMITIVE_QUALITY_LOW_VALUE_SYMBOL_KINDS,
    PRIMITIVE_QUALITY_GENERIC_HELPER_SYMBOL_NAMES,
    PRIMITIVE_QUALITY_MIN_BLACKBOX_TOKENS,
    PRIMITIVE_QUALITY_NOISE_NAME_MARKERS,
    PRIMITIVE_QUALITY_NOISE_PATH_PARTS,
    PRIMITIVE_QUALITY_PREFERRED_SYMBOL_KINDS,
    PRIMITIVE_QUALITY_READINESS_R3,
    PRIMITIVE_QUALITY_READINESS_R5,
    PRIMITIVE_QUALITY_READINESS_R8,
    PRIMITIVE_QUALITY_SUMMARY_EXAMPLE_LIMIT,
    PRIMITIVE_QUALITY_SURFACEABLE_MIN_SCORE,
    PRIMITIVE_QUALITY_TRUST_CANDIDATE,
    PRIMITIVE_QUALITY_TRUST_VALIDATED,
    PRIMITIVE_QUALITY_UNKNOWN_CONTRACT_MARKERS,
)


DEFAULT_REGISTRY_DIR = (REPO / ".agent") / "primitive-registry"
ASSESSOR_ID = "primitive_quality_promoter.v1"
TOKEN_RE = re.compile(r"[a-z0-9]+")
GENERATED_PURPOSE_MARKER = "candidate primitive generated from real repo symbol"

# Named local weights. They are deliberately local to this scoring policy; the
# cross-script thresholds and output filenames live in scripts._config.
SCORE_REAL_SOURCE = 16
SCORE_NON_SYNTHETIC = 8
SCORE_PREFERRED_SYMBOL = 13
SCORE_LOW_VALUE_SYMBOL_PENALTY = -18
SCORE_AST_CONTRACT_ENRICHED = 18
SCORE_KNOWN_INPUT_EDGE = 10
SCORE_KNOWN_OUTPUT_EDGE = 14
SCORE_BLACKBOX_DOC = 12
SCORE_DOMAIN_MATCH = 11
SCORE_MUTATION_OPTION = 6
SCORE_EFFECT_DECLARED = 4
SCORE_TEST_PATH_PENALTY = -25
SCORE_LOW_LEVEL_NAME_PENALTY = -24
SCORE_UNRESOLVED_OUTPUT_PENALTY = -22
SCORE_UNRESOLVED_INPUT_PENALTY = -10
SCORE_GENERATED_PURPOSE_PENALTY = -8
MAX_DOMAIN_SCORE_MULTIPLIER = 3
MAX_MUTATION_SCORE_COUNT = 2
MAX_QUALITY_SCORE = 100
MIN_QUALITY_SCORE = 0
SEARCH_TEXT_MAX_CHARS = 1600
SOURCE_SNIPPET_MAX_CHARS = 360
SUMMARY_TOP_DOMAIN_LIMIT = 12


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}_{sha256(stable_json(payload))[:24]}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    return len(rows)


def tokens(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 1}


def compact_text(text: str, limit: int = SEARCH_TEXT_MAX_CHARS) -> str:
    collapsed = " ".join(str(text or "").split())
    return collapsed[:limit]


def shape(contract: dict[str, Any] | None) -> str:
    if not isinstance(contract, dict):
        return "unknown"
    return str(contract.get("shape") or contract.get("type") or contract.get("kind") or "unknown").lower()


def is_unknown_contract(contract: dict[str, Any] | None) -> bool:
    current_shape = shape(contract)
    if current_shape in PRIMITIVE_QUALITY_UNKNOWN_CONTRACT_MARKERS:
        return True
    return "unknown_candidate" in stable_json(contract or {}).lower()


def annotation_text(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def literal_type_name(node: ast.AST | None) -> str:
    if node is None:
        return "any_candidate"
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return "string"
        if isinstance(node.value, bool):
            return "boolean"
        if isinstance(node.value, int):
            return "integer"
        if isinstance(node.value, float):
            return "number"
        if node.value is None:
            return "nullable"
    if isinstance(node, ast.List):
        return "list"
    if isinstance(node, ast.Dict):
        return "object"
    if isinstance(node, ast.Compare):
        return "boolean"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in {"len", "sum", "int"}:
            return "integer"
        if node.func.id in {"float"}:
            return "number"
        if node.func.id in {"str"}:
            return "string"
        if node.func.id in {"bool"}:
            return "boolean"
    if isinstance(node, (ast.BinOp, ast.UnaryOp)):
        return "number_candidate"
    return "value_candidate"


def find_function(tree: ast.AST, symbol_name: str, line: int | None) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol_name
    ]
    if not functions:
        return None
    if line is not None:
        exact = [node for node in functions if node.lineno == line]
        if exact:
            return exact[0]
        before = [node for node in functions if node.lineno <= line <= getattr(node, "end_lineno", node.lineno)]
        if before:
            return before[0]
    return functions[0]


def infer_dict_fields_from_returns(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
    fields: dict[str, str] = {}
    for node in ast.walk(function_node):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
            continue
        for key, value in zip(node.value.keys, node.value.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                fields[key.value] = literal_type_name(value)
    return dict(sorted(fields.items()))


def infer_input_fields_from_gets(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
    if not function_node.args.args:
        return {}
    first_param = function_node.args.args[0].arg
    fields: dict[str, str] = {}
    for node in ast.walk(function_node):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == first_param
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            default_node = node.args[1] if len(node.args) > 1 else None
            fields[node.args[0].value] = literal_type_name(default_node)
    return dict(sorted(fields.items()))


def source_snippet(path: Path, line: int | None) -> str:
    if not path.exists() or line is None:
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(0, line - 1)
    return "\n".join(lines[start:start + 12])[:SOURCE_SNIPPET_MAX_CHARS]


def ast_enrichment(record: dict[str, Any]) -> dict[str, Any]:
    provenance = record.get("license_provenance") or {}
    rel_path = str(provenance.get("path") or "")
    symbol_name = str(provenance.get("symbol_name") or "")
    if provenance.get("symbol_kind") not in {"function", "method"} or not rel_path or not symbol_name:
        return {}
    source_path = _resource(rel_path)
    if not source_path.exists() or source_path.suffix != ".py":
        return {}
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return {}
    line = provenance.get("line")
    function_node = find_function(tree, symbol_name, int(line) if isinstance(line, int) else None)
    if function_node is None:
        return {}

    module_doc = ast.get_docstring(tree) or ""
    function_doc = ast.get_docstring(function_node) or ""
    input_fields = infer_input_fields_from_gets(function_node)
    output_fields = infer_dict_fields_from_returns(function_node)
    parameters = []
    for arg in function_node.args.args:
        parameters.append({
            "name": arg.arg,
            "annotation": annotation_text(arg.annotation),
            "required": True,
        })
    enriched_input: dict[str, Any]
    if input_fields:
        enriched_input = {
            "shape": "object",
            "fields": input_fields,
            "source": "python_ast_inputs_get_enrichment",
            "original_parameters": parameters,
        }
    else:
        enriched_input = {
            "shape": "callable_signature_candidate",
            "parameters": parameters,
            "source": "python_ast_signature_enrichment",
        }
    enriched_output: dict[str, Any]
    if output_fields:
        enriched_output = {
            "shape": "object",
            "fields": output_fields,
            "source": "python_ast_return_dict_enrichment",
            "return_annotation": annotation_text(function_node.returns),
        }
    elif function_node.returns is not None:
        enriched_output = {
            "shape": "python_return_annotation_candidate",
            "annotation": annotation_text(function_node.returns),
            "source": "python_ast_return_annotation_enrichment",
        }
    else:
        enriched_output = {}
    return {
        "blackbox_description": compact_text(function_doc or module_doc),
        "blackbox_source": "function_doc" if function_doc else "module_doc" if module_doc else "none",
        "enriched_input_contract": enriched_input,
        "enriched_output_contract": enriched_output,
        "source_snippet": source_snippet(source_path, int(line) if isinstance(line, int) else None),
        "source": "python_ast",
    }


def domain_matches(text_blob: str) -> list[str]:
    text_tokens = tokens(text_blob)
    matches: list[str] = []
    for domain, rules in PRIMITIVE_QUALITY_DOMAIN_RULES.items():
        if text_tokens & set(rules):
            matches.append(domain)
    return sorted(matches)


def grouped(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get(key):
            out[str(row[key])].append(row)
    return out


def classify_assessment(score: int, blockers: list[str]) -> tuple[str, str, str, bool]:
    blocker_set = set(blockers)
    hard_noise = {
        "low_level_symbol",
        "test_or_fixture_path",
        "low_level_generated_name",
        "private_helper_symbol",
        "generic_helper_symbol",
        "missing_direct_function_blackbox",
    } & blocker_set
    contract_blockers = {"input_edge_needs_contract_enrichment", "output_edge_needs_contract_enrichment"} & blocker_set
    surface_blockers = hard_noise | contract_blockers | ({"no_practical_domain", "missing_real_source"} & blocker_set)
    if hard_noise:
        return (
            PRIMITIVE_QUALITY_CLASS_NOISE,
            PRIMITIVE_QUALITY_READINESS_R3,
            PRIMITIVE_QUALITY_TRUST_CANDIDATE,
            False,
        )
    if score >= PRIMITIVE_QUALITY_SURFACEABLE_MIN_SCORE and not surface_blockers:
        return (
            PRIMITIVE_QUALITY_CLASS_SURFACEABLE,
            PRIMITIVE_QUALITY_READINESS_R8,
            PRIMITIVE_QUALITY_TRUST_VALIDATED,
            True,
        )
    if contract_blockers:
        return (
            PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT,
            PRIMITIVE_QUALITY_READINESS_R3,
            PRIMITIVE_QUALITY_TRUST_CANDIDATE,
            False,
        )
    if score >= PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE:
        return (
            PRIMITIVE_QUALITY_CLASS_HIGH_VALUE,
            PRIMITIVE_QUALITY_READINESS_R5,
            PRIMITIVE_QUALITY_TRUST_CANDIDATE,
            False,
        )
    return (
        PRIMITIVE_QUALITY_CLASS_HOLD,
        PRIMITIVE_QUALITY_READINESS_R3,
        PRIMITIVE_QUALITY_TRUST_CANDIDATE,
        False,
    )


def recommended_action(quality_class: str, blockers: list[str]) -> str:
    if quality_class == PRIMITIVE_QUALITY_CLASS_SURFACEABLE:
        return "surface_in_aidevobserver_as_candidate_reuse_card"
    if quality_class == PRIMITIVE_QUALITY_CLASS_HIGH_VALUE:
        return "review_and_add_proof_receipts_before_surface_by_default"
    if quality_class == PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT:
        if "output_edge_needs_contract_enrichment" in blockers:
            return "enrich_or_observe_output_contract_before_surface"
        return "enrich_input_contract_before_surface"
    if quality_class == PRIMITIVE_QUALITY_CLASS_NOISE:
        return "keep_indexed_for_fallback_but_hide_from_default_reuse"
    return "hold_for_more_evidence_or_usage_observations"


def assess_record(
    record: dict[str, Any],
    registry_record: dict[str, Any] | None,
    edges: list[dict[str, Any]],
    mutation_options: list[dict[str, Any]],
    effects: list[dict[str, Any]],
) -> dict[str, Any]:
    provenance = record.get("license_provenance") or {}
    enrichment = ast_enrichment(record)
    enriched_input = enrichment.get("enriched_input_contract") or record.get("input_contract") or {}
    enriched_output = enrichment.get("enriched_output_contract") or record.get("output_contract") or {}
    symbol_kind = str(provenance.get("symbol_kind") or "")
    symbol_name = str(provenance.get("symbol_name") or "")
    rel_path = str(provenance.get("path") or "")
    title = (registry_record or {}).get("title") or record.get("name") or record.get("id")
    original_blackbox = (registry_record or {}).get("blackbox_description") or record.get("purpose") or ""
    blackbox = enrichment.get("blackbox_description") or original_blackbox
    source_text = " ".join([
        str(record.get("id") or ""),
        str(record.get("name") or ""),
        str(record.get("purpose") or ""),
        str(title or ""),
        str(blackbox or ""),
        rel_path,
        stable_json(enriched_input),
        stable_json(enriched_output),
    ])
    domains = domain_matches(source_text)
    signals: list[str] = []
    blockers: list[str] = []
    score = MIN_QUALITY_SCORE

    if provenance.get("generated_from_real_artifact"):
        score += SCORE_REAL_SOURCE
        signals.append("real_source_artifact")
    else:
        blockers.append("missing_real_source")
    if not record.get("synthetic") and not provenance.get("synthetic"):
        score += SCORE_NON_SYNTHETIC
        signals.append("non_synthetic")
    if symbol_kind in PRIMITIVE_QUALITY_PREFERRED_SYMBOL_KINDS:
        score += SCORE_PREFERRED_SYMBOL
        signals.append(f"preferred_symbol_kind:{symbol_kind}")
    if symbol_kind in PRIMITIVE_QUALITY_LOW_VALUE_SYMBOL_KINDS:
        score += SCORE_LOW_VALUE_SYMBOL_PENALTY
        blockers.append("low_level_symbol")
    if enrichment.get("source") == "python_ast":
        score += SCORE_AST_CONTRACT_ENRICHED
        signals.append("python_ast_contract_enrichment")
    if is_unknown_contract(enriched_input):
        score += SCORE_UNRESOLVED_INPUT_PENALTY
        blockers.append("input_edge_needs_contract_enrichment")
    else:
        score += SCORE_KNOWN_INPUT_EDGE
        signals.append(f"input_edge:{shape(enriched_input)}")
    if is_unknown_contract(enriched_output):
        score += SCORE_UNRESOLVED_OUTPUT_PENALTY
        blockers.append("output_edge_needs_contract_enrichment")
    else:
        score += SCORE_KNOWN_OUTPUT_EDGE
        signals.append(f"output_edge:{shape(enriched_output)}")
    if len(tokens(blackbox)) >= PRIMITIVE_QUALITY_MIN_BLACKBOX_TOKENS and GENERATED_PURPOSE_MARKER not in blackbox.lower():
        score += SCORE_BLACKBOX_DOC
        signals.append("clear_blackbox_description")
    else:
        score += SCORE_GENERATED_PURPOSE_PENALTY
        blockers.append("thin_blackbox_description")
    if domains:
        domain_score = min(len(domains), MAX_DOMAIN_SCORE_MULTIPLIER) * SCORE_DOMAIN_MATCH
        score += domain_score
        signals.append("domain:" + ",".join(domains[:SUMMARY_TOP_DOMAIN_LIMIT]))
    else:
        blockers.append("no_practical_domain")
    mutation_count = len([row for row in mutation_options if row.get("precondition_status") in {"satisfied", "possible"}])
    if mutation_count:
        score += min(mutation_count, MAX_MUTATION_SCORE_COUNT) * SCORE_MUTATION_OPTION
        signals.append(f"mutation_options:{mutation_count}")
    if effects:
        score += SCORE_EFFECT_DECLARED
        signals.append("effect_declared")
    path_parts = set(Path(rel_path).parts)
    if path_parts & set(PRIMITIVE_QUALITY_NOISE_PATH_PARTS):
        score += SCORE_TEST_PATH_PENALTY
        blockers.append("test_or_fixture_path")
    lower_name = f"{record.get('name') or ''} {record.get('id') or ''}".lower()
    if any(marker in lower_name for marker in PRIMITIVE_QUALITY_NOISE_NAME_MARKERS):
        score += SCORE_LOW_LEVEL_NAME_PENALTY
        blockers.append("low_level_generated_name")
    if symbol_name.startswith("_"):
        score += SCORE_LOW_LEVEL_NAME_PENALTY
        blockers.append("private_helper_symbol")
    if symbol_name in PRIMITIVE_QUALITY_GENERIC_HELPER_SYMBOL_NAMES and not (rel_path.startswith("code-templates/") and symbol_name == "run"):
        score += SCORE_LOW_LEVEL_NAME_PENALTY
        blockers.append("generic_helper_symbol")
    object_io = shape(enriched_input) == "object" and shape(enriched_output) == "object"
    if enrichment.get("blackbox_source") != "function_doc" and not (rel_path.startswith("code-templates/") and object_io):
        blockers.append("missing_direct_function_blackbox")

    final_score = max(MIN_QUALITY_SCORE, min(MAX_QUALITY_SCORE, int(score)))
    quality_class, readiness_after, trust_after, surfaceable = classify_assessment(final_score, sorted(set(blockers)))
    readiness_before = (registry_record or {}).get("readiness_level") or PRIMITIVE_QUALITY_READINESS_R3
    trust_before = (registry_record or {}).get("trust_status") or PRIMITIVE_QUALITY_TRUST_CANDIDATE
    source_ref = {
        "registry": "primitive_registry",
        "kind": symbol_kind or record.get("execution_surface"),
        "name": provenance.get("symbol_name") or record.get("name"),
        "path": rel_path,
        "line": provenance.get("line"),
        "license": provenance.get("license"),
        "generated_from_real_artifact": bool(provenance.get("generated_from_real_artifact")),
    }
    mutation_summary = [
        {
            "mutation_option_id": row.get("mutation_option_id"),
            "mutator_agent_id": row.get("mutator_agent_id"),
            "fit_class": row.get("fit_class"),
            "precondition_status": row.get("precondition_status"),
            "confidence": row.get("confidence"),
            "target_edge_template": row.get("target_edge_template") or {},
        }
        for row in mutation_options
    ]
    assessment_core = {
        "registry_record_id": record.get("id") or (registry_record or {}).get("registry_record_id"),
        "assessor_id": ASSESSOR_ID,
        "quality_score": final_score,
        "quality_class": quality_class,
        "surfaceable": surfaceable,
        "readiness_before": readiness_before,
        "readiness_after": readiness_after,
        "trust_before": trust_before,
        "trust_after": trust_after,
        "domains": domains,
        "signals": sorted(set(signals)),
        "blockers": sorted(set(blockers)),
        "enriched_input_contract": enriched_input,
        "enriched_output_contract": enriched_output,
        "mutation_options": mutation_summary,
        "recommended_action": recommended_action(quality_class, sorted(set(blockers))),
        "source_ref": source_ref,
        "title": title,
        "blackbox": blackbox,
        "search_text": compact_text(source_text),
        "source_snippet": enrichment.get("source_snippet") or "",
        "candidate": True,
        "serves_truth": False,
    }
    assessment_hash = sha256(stable_json(assessment_core))
    return {
        "primitive_quality_assessment_id": stable_id("primqa", {"record": assessment_core["registry_record_id"], "hash": assessment_hash}),
        **assessment_core,
        "assessment_hash": assessment_hash,
    }


def reuse_card_from_assessment(assessment: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "reuse_card",
        "primitive_id": assessment["registry_record_id"],
        "label": assessment.get("title"),
        "blackbox": assessment.get("blackbox"),
        "domains": assessment.get("domains") or [],
        "quality_score": assessment.get("quality_score"),
        "quality_class": assessment.get("quality_class"),
        "readiness": assessment.get("readiness_after"),
        "trust": assessment.get("trust_after"),
        "contract": {
            "input": assessment.get("enriched_input_contract") or {},
            "output": assessment.get("enriched_output_contract") or {},
        },
        "input_edge": assessment.get("enriched_input_contract") or {},
        "output_edge": assessment.get("enriched_output_contract") or {},
        "edge_mutation_options": assessment.get("mutation_options") or [],
        "source_ref": assessment.get("source_ref") or {},
        "proof_requirements": [
            "passing_proof_receipt",
            "owner_review_before_promotion",
        ],
        "candidate": True,
        "serves_truth": False,
    }


def assessment_to_patch(assessment: dict[str, Any]) -> dict[str, Any]:
    return {
        "registry_record_id": assessment["registry_record_id"],
        "status": "review" if assessment["surfaceable"] else "candidate",
        "trust_status": assessment["trust_after"],
        "readiness_level": assessment["readiness_after"],
        "quality_score": assessment["quality_score"],
        "quality_class": assessment["quality_class"],
        "surfaceable": assessment["surfaceable"],
        "assessment_id": assessment["primitive_quality_assessment_id"],
        "serves_truth": False,
    }


def build(registry_dir: Path, write: bool = True) -> dict[str, Any]:
    candidate_records = read_jsonl(registry_dir / "primitive_candidate_records.jsonl")
    operational_dir = registry_dir / "operational"
    registry_records = read_jsonl(operational_dir / "registry_records.jsonl")
    edges = read_jsonl(operational_dir / "primitive_edges.jsonl")
    mutation_options = read_jsonl(operational_dir / "primitive_mutation_options.jsonl")
    effects = read_jsonl(operational_dir / "primitive_effects.jsonl")

    registry_by_id = {row["registry_record_id"]: row for row in registry_records if row.get("registry_record_id")}
    edges_by_record = grouped(edges, "registry_record_id")
    mutations_by_record = grouped(mutation_options, "registry_record_id")
    effects_by_record = grouped(effects, "registry_record_id")

    assessments = [
        assess_record(
            record,
            registry_by_id.get(record.get("id")),
            edges_by_record.get(record.get("id"), []),
            mutations_by_record.get(record.get("id"), []),
            effects_by_record.get(record.get("id"), []),
        )
        for record in candidate_records
    ]
    assessments.sort(key=lambda row: (-int(row["quality_score"]), str(row["registry_record_id"])))
    high_value = [row for row in assessments if row["quality_class"] in {PRIMITIVE_QUALITY_CLASS_HIGH_VALUE, PRIMITIVE_QUALITY_CLASS_SURFACEABLE}]
    surfaceable = [reuse_card_from_assessment(row) for row in assessments if row["surfaceable"]]
    needs_contract = [row for row in assessments if row["quality_class"] == PRIMITIVE_QUALITY_CLASS_NEEDS_CONTRACT]
    noise = [row for row in assessments if row["quality_class"] == PRIMITIVE_QUALITY_CLASS_NOISE]
    patches = [assessment_to_patch(row) for row in assessments]

    quality_dir = registry_dir / PRIMITIVE_QUALITY_DIRNAME
    counts = Counter(row["quality_class"] for row in assessments)
    domain_counts = Counter(domain for row in assessments for domain in row.get("domains") or [])
    manifest = {
        "created_at": utc_now(),
        "assessor_id": ASSESSOR_ID,
        "source_registry": str(registry_dir),
        "candidate_records": len(candidate_records),
        "assessments": len(assessments),
        "high_value_candidates": len(high_value),
        "aidevobserver_surfaceable_primitives": len(surfaceable),
        "needs_contract_enrichment": len(needs_contract),
        "noise_low_level_symbols": len(noise),
        "quality_class_counts": dict(sorted(counts.items())),
        "domain_counts": dict(domain_counts.most_common(SUMMARY_TOP_DOMAIN_LIMIT)),
        "thresholds": {
            "high_value_min_score": PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE,
            "surfaceable_min_score": PRIMITIVE_QUALITY_SURFACEABLE_MIN_SCORE,
            "min_blackbox_tokens": PRIMITIVE_QUALITY_MIN_BLACKBOX_TOKENS,
        },
        "artifacts": {
            key: str(quality_dir / filename)
            for key, filename in PRIMITIVE_QUALITY_ARTIFACT_FILES.items()
        },
        "candidate": True,
        "serves_truth": False,
    }

    if write:
        quality_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["assessments"], assessments)
        write_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["high_value"], high_value)
        write_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["surfaceable"], surfaceable)
        write_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["needs_contract_enrichment"], needs_contract)
        write_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["noise"], noise)
        write_jsonl(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["registry_record_quality_patches"], patches)
        (quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["manifest"]).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_summary(quality_dir / PRIMITIVE_QUALITY_ARTIFACT_FILES["summary"], manifest, assessments, surfaceable)
    return manifest


def write_summary(path: Path, manifest: dict[str, Any], assessments: list[dict[str, Any]], surfaceable: list[dict[str, Any]]) -> None:
    examples = surfaceable[:PRIMITIVE_QUALITY_SUMMARY_EXAMPLE_LIMIT]
    lines = [
        "# Primitive Quality Promoter",
        "",
        f"- Updated: `{manifest['created_at']}`",
        f"- Assessor: `{manifest['assessor_id']}`",
        f"- Candidate records assessed: `{manifest['candidate_records']}`",
        f"- Surfaceable AIDevObserver candidates: `{manifest['aidevobserver_surfaceable_primitives']}`",
        f"- High-value candidates: `{manifest['high_value_candidates']}`",
        f"- Need contract enrichment: `{manifest['needs_contract_enrichment']}`",
        f"- Noise / hidden by default: `{manifest['noise_low_level_symbols']}`",
        f"- Serves truth: `{manifest['serves_truth']}`",
        "",
        "## Quality Classes",
        "",
        "```json",
        json.dumps(manifest["quality_class_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Top Domains",
        "",
        "```json",
        json.dumps(manifest["domain_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Surfaceable Examples",
        "",
    ]
    for card in examples:
        source = card.get("source_ref") or {}
        lines.extend([
            f"- `{card['primitive_id']}`",
            f"  - Score: `{card['quality_score']}`",
            f"  - Label: `{card.get('label')}`",
            f"  - Source: `{source.get('path')}:{source.get('line')}`",
            f"  - Input: `{shape(card.get('input_edge'))}`",
            f"  - Output: `{shape(card.get('output_edge'))}`",
        ])
    if not examples:
        lines.append("No surfaceable rows yet. Run contract enrichment/proof on high-value candidates first.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        src = root / "code-templates" / "extract_email"
        src.mkdir(parents=True)
        py = src / "extract_email.py"
        py.write_text(
            '"""Extract unique email addresses from text with deterministic regex matching."""\n'
            "from typing import Any\n\n"
            "def run(inputs: dict[str, Any]) -> dict[str, Any]:\n"
            "    text = inputs.get('text', '')\n"
            "    return {'emails': [text], 'count': len(text)}\n",
            encoding="utf-8",
        )
        records = [{
            "id": "primitive.repo.code_templates_extract_email.function.run",
            "name": "py_function_code_templates_extract_email__run",
            "purpose": "Candidate primitive generated from real repo symbol `run`.",
            "input_contract": {"shape": "callable_signature_candidate", "parameters": [{"name": "inputs"}]},
            "output_contract": {"shape": "unknown_candidate"},
            "license_provenance": {
                "generated_from_real_artifact": True,
                "license": "MIT",
                "line": 4,
                "path": "code-templates/extract_email/extract_email.py",
                "symbol_kind": "function",
                "symbol_name": "run",
                "synthetic": False,
            },
            "execution_surface": "python_callable_candidate",
            "candidate": True,
            "serves_truth": False,
        }]
        reg = root / ".agent" / "primitive-registry"
        op = reg / "operational"
        op.mkdir(parents=True)
        write_jsonl(reg / "primitive_candidate_records.jsonl", records)
        write_jsonl(op / "registry_records.jsonl", [{
            "registry_record_id": records[0]["id"],
            "readiness_level": PRIMITIVE_QUALITY_READINESS_R3,
            "trust_status": PRIMITIVE_QUALITY_TRUST_CANDIDATE,
            "title": records[0]["name"],
            "blackbox_description": records[0]["purpose"],
        }])
        write_jsonl(op / "primitive_edges.jsonl", [])
        write_jsonl(op / "primitive_mutation_options.jsonl", [{
            "mutation_option_id": "mut_1",
            "registry_record_id": records[0]["id"],
            "mutator_agent_id": "mutator:core:output_field_wrapper@candidate",
            "fit_class": "deterministic_edit_match",
            "precondition_status": "possible",
            "confidence": 0.5,
            "target_edge_template": {"mutation": "output_field_wrapper"},
        }])
        write_jsonl(op / "primitive_effects.jsonl", [{"registry_record_id": records[0]["id"], "effect_kind": "pure"}])
        old_repo = globals()["REPO"]
        globals()["REPO"] = root
        try:
            manifest = build(reg, write=True)
        finally:
            globals()["REPO"] = old_repo
        surfaceable = read_jsonl(reg / PRIMITIVE_QUALITY_DIRNAME / PRIMITIVE_QUALITY_ARTIFACT_FILES["surfaceable"])
        assessment = read_jsonl(reg / PRIMITIVE_QUALITY_DIRNAME / PRIMITIVE_QUALITY_ARTIFACT_FILES["assessments"])[0]
        check("self-test emits one assessment", manifest["assessments"] == 1)
        check("AST enrichment infers input field", assessment["enriched_input_contract"].get("fields", {}).get("text") == "string")
        check("AST enrichment infers output fields", set(assessment["enriched_output_contract"].get("fields", {})) == {"emails", "count"})
        check("surfaceable row is emitted", len(surfaceable) == 1 and surfaceable[0]["serves_truth"] is False)

    if failures:
        print(f"\nFAIL - primitive_quality_promoter: {len(failures)} failure(s)")
        return 1
    print("\nPASS - primitive_quality_promoter: deterministic quality sieve emits surfaceable candidate cards")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-dir", default=str(DEFAULT_REGISTRY_DIR))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    manifest = build(Path(args.registry_dir), write=True)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
