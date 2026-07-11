#!/usr/bin/env python3
"""Primitive registry builder.

Turns real repo-code inventory artifacts into primitive candidate records:

  .agent/repo-code-inventory/symbols.jsonl + modules/imports/edges
    -> primitive candidate records
    -> vector/search export rows
    -> manifest + summary

This script does not promote anything. It creates candidate evidence only; promotion is handled by
_repos/shared-backend-components/scripts/check_primitive_registry_promotion_gate.py.
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
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


py_const_scripts_primitive_registry_builder__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(py_const_scripts_primitive_registry_builder__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_primitive_registry_builder__REPO))

from src.teleon.registry.enrich import py_var_src_teleon_registry_enrich___EMBED_DIM as EMBED_DIM, py_function_src_teleon_registry_enrich__enrich_record
from src.teleon.registry import primitive_match
from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS


py_const_scripts_primitive_registry_builder__DEFAULT_INVENTORY = (py_const_scripts_primitive_registry_builder__REPO / ".agent") / "repo-code-inventory"
py_const_scripts_primitive_registry_builder__DEFAULT_OUT = (py_const_scripts_primitive_registry_builder__REPO / ".agent") / "primitive-registry"
py_const_scripts_primitive_registry_builder__VERSION = "0.1.0"
py_const_scripts_primitive_registry_builder__PRIMITIVE_SYMBOL_KINDS = {"function", "method", "class", "const", "var", "instance"}
py_const_scripts_primitive_registry_builder__REQUIRED_RECORD_FIELDS = {
    "id",
    "version",
    "name",
    "purpose",
    "input_contract",
    "output_contract",
    "call_surface",
    "composition",
    "mutation_affordances",
    "dependencies",
    "license_provenance",
    "execution_surface",
    "proof_command",
    "logs_schema",
    "graph_edges",
    "candidate",
    "serves_truth",
}
py_const_scripts_primitive_registry_builder__PLACEHOLDER_RE = re.compile(r"(?i)\b(todo|tbd|lorem ipsum|replace me|dummy|placeholder text|sample sample)\b")
py_const_scripts_primitive_registry_builder__MAX_GRAPH_EDGES_PER_RECORD = 30
py_const_scripts_primitive_registry_builder__MAX_DEFAULT_RECORDS = 5000
py_const_scripts_primitive_registry_builder__MUTATION_SURFACE_MODULE = "src.teleon.synthesis.primitive_variations"
py_const_scripts_primitive_registry_builder__VERIFIED_MUTATION_CALL_SURFACES = {
    "scalar_to_sequence": {
        "mutation": "scalar_to_sequence",
        "status": "verified_runtime_wrapper",
        "python_module": py_const_scripts_primitive_registry_builder__MUTATION_SURFACE_MODULE,
        "python_function": "py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation",
        "call_shape": "primitive_contract + scalar_callable -> {callable, contract, variation, serves_truth=false}",
        "proof_command": "PYTHONPATH=. python3 scripts/check_teleon_primitive_variation_contracts.py",
        "deterministic": True,
        "serves_truth": False,
    },
    "output_field_wrapper": {
        "mutation": "output_field_wrapper",
        "status": "verified_runtime_wrapper",
        "python_module": py_const_scripts_primitive_registry_builder__MUTATION_SURFACE_MODULE,
        "python_function": "py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation",
        "call_shape": "primitive_contract + callable + output_field -> {callable, contract, variation, serves_truth=false}",
        "proof_command": "PYTHONPATH=. python3 scripts/check_teleon_primitive_variation_contracts.py",
        "deterministic": True,
        "serves_truth": False,
    },
    "linear_graph_composition": {
        "mutation": "linear_graph_composition",
        "status": "verified_graph_wrapper",
        "python_module": py_const_scripts_primitive_registry_builder__MUTATION_SURFACE_MODULE,
        "python_function": "py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract",
        "call_shape": "graph_id + ordered primitive contracts -> linear graph contract with maps_output_to_input edges",
        "proof_command": "PYTHONPATH=. python3 scripts/check_teleon_primitive_variation_contracts.py",
        "deterministic": True,
        "serves_truth": False,
    },
    "linear_graph_execution": {
        "mutation": "linear_graph_execution",
        "status": "verified_local_runner",
        "python_module": py_const_scripts_primitive_registry_builder__MUTATION_SURFACE_MODULE,
        "python_function": "py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph",
        "call_shape": "graph_contract + callables + input_value -> {output, logs, serves_truth=false}",
        "proof_command": "PYTHONPATH=. python3 scripts/check_teleon_primitive_variation_contracts.py",
        "deterministic": True,
        "serves_truth": False,
    },
}
py_const_scripts_primitive_registry_builder__FUTURE_MUTATION_SURFACES = {
    "field_rename_adapter": "candidate explicit field-map adapter; requires field map + schema proof before promotion",
    "retry_cache_rate_limit_adapter": "candidate policy adapter; requires retry/cache/rate-limit log proof before promotion",
    "model_cost_downshift": "candidate optimization; requires guardrail pass-rate and cost/latency receipts",
    "browser_to_deterministic_extractor": "candidate extraction optimization; requires observed-structure stability proof",
    "local_api_implementation_swap": "candidate implementation swap; requires same I/O contract, dependency, license, and runtime receipts",
    "generated_adapter_candidate": "non-deterministic last resort; requires owner/human review plus deterministic proofs before promotion",
}
py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES = {
    "registry_record": "registry_records.jsonl",
    "primitive_edge": "primitive_edges.jsonl",
    "primitive_effect": "primitive_effects.jsonl",
    "registry_embedding": "registry_embeddings.jsonl",
    "primitive_blocking_profile": "primitive_blocking_profiles.jsonl",
    "primitive_blocking_key": "primitive_blocking_keys.jsonl",
    "mutator_agent": "mutator_agents.jsonl",
    "primitive_mutation_option": "primitive_mutation_options.jsonl",
    "registry_source": "registry_sources.jsonl",
    "registry_source_link": "registry_source_links.jsonl",
}
py_const_scripts_primitive_registry_builder__BLOCKING_KEY_LANES = (
    "exact",
    "keyword",
    "label",
    "input_shape",
    "input_field",
    "output_shape",
    "output_field",
    "graph",
    "mutation",
    "semantic_bucket",
)


def py_function_scripts_primitive_registry_builder__now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def py_function_scripts_primitive_registry_builder__slug(py_arg_scripts_primitive_registry_builder__slug__value):
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", str(py_arg_scripts_primitive_registry_builder__slug__value)).strip("_")).lower() or "record"


def py_function_scripts_primitive_registry_builder__load_jsonl(py_arg_scripts_primitive_registry_builder__load_jsonl__path):
    if not py_arg_scripts_primitive_registry_builder__load_jsonl__path.exists():
        return []
    py_local_scripts_primitive_registry_builder__load_jsonl__rows = []
    for py_local_scripts_primitive_registry_builder__load_jsonl__line in py_arg_scripts_primitive_registry_builder__load_jsonl__path.read_text(encoding="utf-8").splitlines():
        if py_local_scripts_primitive_registry_builder__load_jsonl__line.strip():
            py_local_scripts_primitive_registry_builder__load_jsonl__rows.append(json.loads(py_local_scripts_primitive_registry_builder__load_jsonl__line))
    return py_local_scripts_primitive_registry_builder__load_jsonl__rows


def py_function_scripts_primitive_registry_builder__write_jsonl(py_arg_scripts_primitive_registry_builder__write_jsonl__path, py_arg_scripts_primitive_registry_builder__write_jsonl__rows):
    py_arg_scripts_primitive_registry_builder__write_jsonl__path.parent.mkdir(parents=True, exist_ok=True)
    py_local_scripts_primitive_registry_builder__write_jsonl__count = 0
    with py_arg_scripts_primitive_registry_builder__write_jsonl__path.open("w", encoding="utf-8") as py_local_scripts_primitive_registry_builder__write_jsonl__fh:
        for py_local_scripts_primitive_registry_builder__write_jsonl__row in py_arg_scripts_primitive_registry_builder__write_jsonl__rows:
            py_local_scripts_primitive_registry_builder__write_jsonl__fh.write(json.dumps(py_local_scripts_primitive_registry_builder__write_jsonl__row, sort_keys=True) + "\n")
            py_local_scripts_primitive_registry_builder__write_jsonl__count += 1
    return py_local_scripts_primitive_registry_builder__write_jsonl__count


def py_function_scripts_primitive_registry_builder__stable_json(py_arg_scripts_primitive_registry_builder__stable_json__value):
    return json.dumps(py_arg_scripts_primitive_registry_builder__stable_json__value, sort_keys=True, separators=(",", ":"))


def py_function_scripts_primitive_registry_builder__sha256(py_arg_scripts_primitive_registry_builder__sha256__value):
    return hashlib.sha256(str(py_arg_scripts_primitive_registry_builder__sha256__value).encode("utf-8")).hexdigest()


def py_function_scripts_primitive_registry_builder__stable_id(py_arg_scripts_primitive_registry_builder__stable_id__prefix, py_arg_scripts_primitive_registry_builder__stable_id__payload):
    return f"{py_arg_scripts_primitive_registry_builder__stable_id__prefix}_{py_function_scripts_primitive_registry_builder__sha256(py_function_scripts_primitive_registry_builder__stable_json(py_arg_scripts_primitive_registry_builder__stable_id__payload))[:24]}"


def py_function_scripts_primitive_registry_builder__function_scope(py_arg_scripts_primitive_registry_builder__function_scope__symbol):
    py_local_scripts_primitive_registry_builder__function_scope__scope = py_arg_scripts_primitive_registry_builder__function_scope__symbol.get("scope") or "<module>"
    py_local_scripts_primitive_registry_builder__function_scope__name = py_arg_scripts_primitive_registry_builder__function_scope__symbol.get("name") or ""
    return py_local_scripts_primitive_registry_builder__function_scope__name if py_local_scripts_primitive_registry_builder__function_scope__scope == "<module>" else f"{py_local_scripts_primitive_registry_builder__function_scope__scope}.{py_local_scripts_primitive_registry_builder__function_scope__name}"


def py_function_scripts_primitive_registry_builder__records_by_path(py_arg_scripts_primitive_registry_builder__records_by_path__rows):
    py_local_scripts_primitive_registry_builder__records_by_path__out = defaultdict(list)
    for py_local_scripts_primitive_registry_builder__records_by_path__row in py_arg_scripts_primitive_registry_builder__records_by_path__rows:
        py_local_scripts_primitive_registry_builder__records_by_path__out[py_local_scripts_primitive_registry_builder__records_by_path__row.get("path", "")].append(py_local_scripts_primitive_registry_builder__records_by_path__row)
    return py_local_scripts_primitive_registry_builder__records_by_path__out


def py_function_scripts_primitive_registry_builder__module_imports_by_path(py_arg_scripts_primitive_registry_builder__module_imports_by_path__module_rows):
    py_local_scripts_primitive_registry_builder__module_imports_by_path__out = {}
    for py_local_scripts_primitive_registry_builder__module_imports_by_path__row in py_arg_scripts_primitive_registry_builder__module_imports_by_path__module_rows:
        py_local_scripts_primitive_registry_builder__module_imports_by_path__out[py_local_scripts_primitive_registry_builder__module_imports_by_path__row.get("path", "")] = sorted(py_local_scripts_primitive_registry_builder__module_imports_by_path__row.get("import_modules") or [])
    return py_local_scripts_primitive_registry_builder__module_imports_by_path__out


def py_function_scripts_primitive_registry_builder__args_by_symbol_scope(py_arg_scripts_primitive_registry_builder__args_by_symbol_scope__symbol_rows):
    py_local_scripts_primitive_registry_builder__args_by_symbol_scope__out = defaultdict(list)
    for py_local_scripts_primitive_registry_builder__args_by_symbol_scope__row in py_arg_scripts_primitive_registry_builder__args_by_symbol_scope__symbol_rows:
        if py_local_scripts_primitive_registry_builder__args_by_symbol_scope__row.get("kind") == "arg":
            py_local_scripts_primitive_registry_builder__args_by_symbol_scope__out[(py_local_scripts_primitive_registry_builder__args_by_symbol_scope__row.get("path", ""), py_local_scripts_primitive_registry_builder__args_by_symbol_scope__row.get("scope", ""))].append(py_local_scripts_primitive_registry_builder__args_by_symbol_scope__row)
    for py_local_scripts_primitive_registry_builder__args_by_symbol_scope__key in list(py_local_scripts_primitive_registry_builder__args_by_symbol_scope__out):
        py_local_scripts_primitive_registry_builder__args_by_symbol_scope__out[py_local_scripts_primitive_registry_builder__args_by_symbol_scope__key] = sorted(py_local_scripts_primitive_registry_builder__args_by_symbol_scope__out[py_local_scripts_primitive_registry_builder__args_by_symbol_scope__key], key=lambda py_arg_scripts_primitive_registry_builder__args_by_symbol_scope__item: (py_arg_scripts_primitive_registry_builder__args_by_symbol_scope__item.get("line", 0), py_arg_scripts_primitive_registry_builder__args_by_symbol_scope__item.get("col", 0)))
    return py_local_scripts_primitive_registry_builder__args_by_symbol_scope__out


def py_function_scripts_primitive_registry_builder__graph_edges_for_symbol(py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol, py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__edge_rows_by_path):
    py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_name = py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("name")
    py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_scope = py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("scope")
    py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edges = []
    for py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edge in py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__edge_rows_by_path.get(py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("path", ""), []):
        py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__src = str(py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edge.get("src") or "")
        py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__dst = str(py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edge.get("dst") or "")
        if py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_name and (py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_name == py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__src or py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_name == py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__dst or py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__src.endswith(f".{py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_name}") or py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__dst.endswith(f".{py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_name}")):
            py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edges.append({
                "type": py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edge.get("type") or "related",
                "from": py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__src,
                "to": py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__dst,
                "path": py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("path"),
                "scope": py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_scope,
                "serves_truth": False,
            })
        if len(py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edges) >= py_const_scripts_primitive_registry_builder__MAX_GRAPH_EDGES_PER_RECORD:
            break
    if not py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edges:
        py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edges.append({
            "type": "defined_in",
            "from": f"{py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get('path')}:{py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get('line')}",
            "to": py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("target") or py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("name"),
            "path": py_arg_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol.get("path"),
            "scope": py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__symbol_scope,
            "serves_truth": False,
        })
    return py_local_scripts_primitive_registry_builder__graph_edges_for_symbol__edges


def py_function_scripts_primitive_registry_builder__input_contract_for_symbol(py_arg_scripts_primitive_registry_builder__input_contract_for_symbol__symbol, py_arg_scripts_primitive_registry_builder__input_contract_for_symbol__args_for_scope):
    py_local_scripts_primitive_registry_builder__input_contract_for_symbol__kind = py_arg_scripts_primitive_registry_builder__input_contract_for_symbol__symbol.get("kind")
    if py_local_scripts_primitive_registry_builder__input_contract_for_symbol__kind in {"function", "method"}:
        py_local_scripts_primitive_registry_builder__input_contract_for_symbol__params = [
            {
                "name": arg.get("name"),
                "kind": "python_parameter",
                "source_line": arg.get("line"),
                "required": True,
            }
            for arg in py_arg_scripts_primitive_registry_builder__input_contract_for_symbol__args_for_scope.get((py_arg_scripts_primitive_registry_builder__input_contract_for_symbol__symbol.get("path", ""), py_function_scripts_primitive_registry_builder__function_scope(py_arg_scripts_primitive_registry_builder__input_contract_for_symbol__symbol)), [])
        ]
        return {
            "shape": "callable_signature_candidate",
            "parameters": py_local_scripts_primitive_registry_builder__input_contract_for_symbol__params,
            "source": "repo_code_inventory",
        }
    if py_local_scripts_primitive_registry_builder__input_contract_for_symbol__kind == "class":
        return {"shape": "python_class_candidate", "constructor_contract": "unknown_candidate"}
    return {"shape": "source_symbol_candidate", "kind": py_local_scripts_primitive_registry_builder__input_contract_for_symbol__kind}


def py_function_scripts_primitive_registry_builder__output_contract_for_symbol(py_arg_scripts_primitive_registry_builder__output_contract_for_symbol__symbol):
    py_local_scripts_primitive_registry_builder__output_contract_for_symbol__kind = py_arg_scripts_primitive_registry_builder__output_contract_for_symbol__symbol.get("kind")
    if py_local_scripts_primitive_registry_builder__output_contract_for_symbol__kind in {"function", "method"}:
        return {
            "shape": "unknown_candidate",
            "reason": "repo inventory does not prove return shape; promote only after proof receipts or observed logs",
        }
    if py_local_scripts_primitive_registry_builder__output_contract_for_symbol__kind == "class":
        return {"shape": "python_class_object_candidate"}
    return {"shape": "python_value_candidate", "kind": py_local_scripts_primitive_registry_builder__output_contract_for_symbol__kind}


def py_function_scripts_primitive_registry_builder__execution_surface_for_symbol(py_arg_scripts_primitive_registry_builder__execution_surface_for_symbol__symbol):
    if py_arg_scripts_primitive_registry_builder__execution_surface_for_symbol__symbol.get("kind") in {"function", "method"}:
        return "python_callable_candidate"
    if py_arg_scripts_primitive_registry_builder__execution_surface_for_symbol__symbol.get("kind") == "class":
        return "python_class_candidate"
    return "python_source_symbol_candidate"


def py_function_scripts_primitive_registry_builder__contract_fields(py_arg_scripts_primitive_registry_builder__contract_fields__contract):
    py_local_scripts_primitive_registry_builder__contract_fields__fields = py_arg_scripts_primitive_registry_builder__contract_fields__contract.get("fields") or py_arg_scripts_primitive_registry_builder__contract_fields__contract.get("properties") or {}
    if isinstance(py_local_scripts_primitive_registry_builder__contract_fields__fields, dict):
        return sorted(str(key) for key in py_local_scripts_primitive_registry_builder__contract_fields__fields)
    if isinstance(py_local_scripts_primitive_registry_builder__contract_fields__fields, list):
        return sorted(str(key) for key in py_local_scripts_primitive_registry_builder__contract_fields__fields)
    py_local_scripts_primitive_registry_builder__contract_fields__parameters = py_arg_scripts_primitive_registry_builder__contract_fields__contract.get("parameters") or []
    if isinstance(py_local_scripts_primitive_registry_builder__contract_fields__parameters, list):
        return sorted(str(row.get("name")) for row in py_local_scripts_primitive_registry_builder__contract_fields__parameters if isinstance(row, dict) and row.get("name"))
    return []


def py_function_scripts_primitive_registry_builder__call_surface_for_symbol(py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__symbol, py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__input_contract, py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__output_contract):
    py_local_scripts_primitive_registry_builder__call_surface_for_symbol__path = py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__symbol.get("path")
    py_local_scripts_primitive_registry_builder__call_surface_for_symbol__target = py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__symbol.get("target") or py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__symbol.get("name")
    return {
        "kind": py_function_scripts_primitive_registry_builder__execution_surface_for_symbol(py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__symbol),
        "python_path": py_local_scripts_primitive_registry_builder__call_surface_for_symbol__path,
        "python_symbol": py_local_scripts_primitive_registry_builder__call_surface_for_symbol__target,
        "entrypoint_candidate": f"{py_local_scripts_primitive_registry_builder__call_surface_for_symbol__path}:{py_local_scripts_primitive_registry_builder__call_surface_for_symbol__target}",
        "input_contract_shape": py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__input_contract.get("shape"),
        "output_contract_shape": py_arg_scripts_primitive_registry_builder__call_surface_for_symbol__output_contract.get("shape"),
        "call_boundary": "candidate_only_until_proof",
        "serves_truth": False,
    }


def py_function_scripts_primitive_registry_builder__composition_for_symbol(py_arg_scripts_primitive_registry_builder__composition_for_symbol__symbol, py_arg_scripts_primitive_registry_builder__composition_for_symbol__input_contract, py_arg_scripts_primitive_registry_builder__composition_for_symbol__output_contract):
    py_local_scripts_primitive_registry_builder__composition_for_symbol__kind = py_arg_scripts_primitive_registry_builder__composition_for_symbol__symbol.get("kind")
    py_local_scripts_primitive_registry_builder__composition_for_symbol__input_fields = py_function_scripts_primitive_registry_builder__contract_fields(py_arg_scripts_primitive_registry_builder__composition_for_symbol__input_contract)
    py_local_scripts_primitive_registry_builder__composition_for_symbol__output_fields = py_function_scripts_primitive_registry_builder__contract_fields(py_arg_scripts_primitive_registry_builder__composition_for_symbol__output_contract)
    return {
        "consumes_state": py_local_scripts_primitive_registry_builder__composition_for_symbol__input_fields or [py_arg_scripts_primitive_registry_builder__composition_for_symbol__input_contract.get("shape", "unknown_input")],
        "produces_state": py_local_scripts_primitive_registry_builder__composition_for_symbol__output_fields or [py_arg_scripts_primitive_registry_builder__composition_for_symbol__output_contract.get("shape", "unknown_output")],
        "invalidates": [],
        "repeatable": py_local_scripts_primitive_registry_builder__composition_for_symbol__kind in {"function", "method", "class"},
        "idempotent": "unknown_candidate",
        "pure": "unknown_candidate",
        "side_effect_boundary": False,
        "edge_policy": "compiler_must_validate_bindings_before_execution",
        "serves_truth": False,
    }


def py_function_scripts_primitive_registry_builder__mutation_affordances_for_record(py_arg_scripts_primitive_registry_builder__mutation_affordances_for_record__record):
    py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__kind = py_arg_scripts_primitive_registry_builder__mutation_affordances_for_record__record["license_provenance"].get("symbol_kind")
    py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__hints = primitive_match.py_function_src_teleon_registry_primitive_match__mutation_hints(py_arg_scripts_primitive_registry_builder__mutation_affordances_for_record__record)
    py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__verified = []
    if py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__kind in {"function", "method"}:
        py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__verified.extend([
            py_const_scripts_primitive_registry_builder__VERIFIED_MUTATION_CALL_SURFACES["scalar_to_sequence"],
            py_const_scripts_primitive_registry_builder__VERIFIED_MUTATION_CALL_SURFACES["output_field_wrapper"],
        ])
    py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__verified.extend([
        py_const_scripts_primitive_registry_builder__VERIFIED_MUTATION_CALL_SURFACES["linear_graph_composition"],
        py_const_scripts_primitive_registry_builder__VERIFIED_MUTATION_CALL_SURFACES["linear_graph_execution"],
    ])
    return {
        "applicable_hints": py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__hints,
        "verified_call_surfaces": py_local_scripts_primitive_registry_builder__mutation_affordances_for_record__verified,
        "future_candidate_surfaces": py_const_scripts_primitive_registry_builder__FUTURE_MUTATION_SURFACES,
        "deterministic_first": True,
        "llm_generated_adapter_last_resort": True,
        "promotion_required_for_variants": True,
        "serves_truth": False,
    }


def py_function_scripts_primitive_registry_builder__candidate_purpose(py_arg_scripts_primitive_registry_builder__candidate_purpose__symbol):
    return (
        f"Candidate primitive generated from real repo symbol `{py_arg_scripts_primitive_registry_builder__candidate_purpose__symbol.get('name')}` "
        f"({py_arg_scripts_primitive_registry_builder__candidate_purpose__symbol.get('kind')}) at `{py_arg_scripts_primitive_registry_builder__candidate_purpose__symbol.get('path')}:{py_arg_scripts_primitive_registry_builder__candidate_purpose__symbol.get('line')}`. "
        "Use as searchable graph evidence; enrich and prove before promotion."
    )


def py_function_scripts_primitive_registry_builder__candidate_record_allowed(py_arg_scripts_primitive_registry_builder__candidate_record_allowed__record):
    py_local_scripts_primitive_registry_builder__candidate_record_allowed__text = " ".join(str(py_arg_scripts_primitive_registry_builder__candidate_record_allowed__record.get(key, "")) for key in ("id", "name", "purpose", "description"))
    if py_const_scripts_primitive_registry_builder__PLACEHOLDER_RE.search(py_local_scripts_primitive_registry_builder__candidate_record_allowed__text):
        return False, "placeholder_text"
    if py_arg_scripts_primitive_registry_builder__candidate_record_allowed__record.get("synthetic") and not py_arg_scripts_primitive_registry_builder__candidate_record_allowed__record.get("example_record"):
        return False, "unmarked_synthetic_record"
    if py_arg_scripts_primitive_registry_builder__candidate_record_allowed__record.get("serves_truth") is not False:
        return False, "serves_truth_must_be_false"
    return True, "ok"


def py_function_scripts_primitive_registry_builder__primitive_record_from_symbol(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol, py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__module_imports, py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__args_for_scope, py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__edge_rows_by_path):
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__target = py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("target") or py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("name")
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__primitive_id = f"primitive.repo.{py_function_scripts_primitive_registry_builder__slug(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get('path'))}.{py_function_scripts_primitive_registry_builder__slug(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get('kind'))}.{py_function_scripts_primitive_registry_builder__slug(py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__target)}"
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__deps = py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__module_imports.get(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("path", ""), [])
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__graph_edges = py_function_scripts_primitive_registry_builder__graph_edges_for_symbol(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol, py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__edge_rows_by_path)
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__input_contract = py_function_scripts_primitive_registry_builder__input_contract_for_symbol(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol, py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__args_for_scope)
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__output_contract = py_function_scripts_primitive_registry_builder__output_contract_for_symbol(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol)
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw = {
        "id": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__primitive_id,
        "version": py_const_scripts_primitive_registry_builder__VERSION,
        "name": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__target,
        "purpose": py_function_scripts_primitive_registry_builder__candidate_purpose(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol),
        "labels": [
            "repo_code",
            f"kind:{py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get('kind')}",
            f"path:{py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get('path')}",
            "candidate",
        ],
        "tags": ["primitive_candidate", py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("kind"), "real_code_artifact"],
        "input_contract": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__input_contract,
        "output_contract": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__output_contract,
        "dependencies": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__deps,
        "license_provenance": {
            "license": "repo_default_or_unknown",
            "source": "repo_code_inventory",
            "path": py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("path"),
            "line": py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("line"),
            "symbol_kind": py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("kind"),
            "symbol_name": py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get("name"),
            "generated_from_real_artifact": True,
            "synthetic": False,
        },
        "execution_surface": py_function_scripts_primitive_registry_builder__execution_surface_for_symbol(py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol),
        "call_surface": py_function_scripts_primitive_registry_builder__call_surface_for_symbol(
            py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol,
            py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__input_contract,
            py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__output_contract,
        ),
        "composition": py_function_scripts_primitive_registry_builder__composition_for_symbol(
            py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol,
            py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__input_contract,
            py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__output_contract,
        ),
        "proof_command": "PYTHONPATH=. python3 scripts/run_proofs.py",
        "logs_schema": {
            "event": "primitive_candidate_evaluation",
            "required": ["primitive_id", "status", "started_at", "completed_at", "proof_command"],
            "serves_truth": False,
        },
        "graph_edges": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__graph_edges,
        "graph_neighbors": sorted({edge.get("from", "") for edge in py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__graph_edges} | {edge.get("to", "") for edge in py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__graph_edges}),
        "source_ref": f"{py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get('path')}:{py_arg_scripts_primitive_registry_builder__primitive_record_from_symbol__symbol.get('line')}",
        "candidate": True,
        "synthetic": False,
        "llm_generated": False,
        "promotion_status": "candidate_only",
        "serves_truth": False,
    }
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment = py_function_src_teleon_registry_enrich__enrich_record(py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw)["_enrichment"]
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["metadata"] = {
        "keywords": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment["keywords"],
        "labels": sorted(set(py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["labels"]) | set(py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment["labels"])),
        "use_cases": py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment["use_cases"],
    }
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["description"] = py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment["description"]
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["long_description"] = py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment["long_description"]
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["embedding"] = py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__enrichment["embedding"]
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["embedding_dim"] = EMBED_DIM
    py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw["mutation_affordances"] = py_function_scripts_primitive_registry_builder__mutation_affordances_for_record(py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw)
    return py_local_scripts_primitive_registry_builder__primitive_record_from_symbol__raw


def py_function_scripts_primitive_registry_builder__validate_candidate_record(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record):
    py_local_scripts_primitive_registry_builder__validate_candidate_record__missing = sorted(field for field in py_const_scripts_primitive_registry_builder__REQUIRED_RECORD_FIELDS if field not in py_arg_scripts_primitive_registry_builder__validate_candidate_record__record)
    if py_local_scripts_primitive_registry_builder__validate_candidate_record__missing:
        return False, f"missing_required_fields:{','.join(py_local_scripts_primitive_registry_builder__validate_candidate_record__missing)}"
    py_local_scripts_primitive_registry_builder__validate_candidate_record__allowed, py_local_scripts_primitive_registry_builder__validate_candidate_record__reason = py_function_scripts_primitive_registry_builder__candidate_record_allowed(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record)
    if not py_local_scripts_primitive_registry_builder__validate_candidate_record__allowed:
        return False, py_local_scripts_primitive_registry_builder__validate_candidate_record__reason
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("input_contract"), dict) or not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("output_contract"), dict):
        return False, "contracts_must_be_objects"
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("call_surface"), dict) or py_arg_scripts_primitive_registry_builder__validate_candidate_record__record["call_surface"].get("serves_truth") is not False:
        return False, "missing_call_surface"
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("composition"), dict) or py_arg_scripts_primitive_registry_builder__validate_candidate_record__record["composition"].get("serves_truth") is not False:
        return False, "missing_composition"
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("mutation_affordances"), dict) or py_arg_scripts_primitive_registry_builder__validate_candidate_record__record["mutation_affordances"].get("serves_truth") is not False:
        return False, "missing_mutation_affordances"
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("license_provenance"), dict) or not py_arg_scripts_primitive_registry_builder__validate_candidate_record__record["license_provenance"].get("generated_from_real_artifact"):
        return False, "missing_real_artifact_provenance"
    if not py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("proof_command"):
        return False, "missing_proof_command"
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("logs_schema"), dict) or not py_arg_scripts_primitive_registry_builder__validate_candidate_record__record["logs_schema"].get("required"):
        return False, "missing_logs_schema"
    if not isinstance(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("graph_edges"), list) or not py_arg_scripts_primitive_registry_builder__validate_candidate_record__record["graph_edges"]:
        return False, "missing_graph_edges"
    if len(py_arg_scripts_primitive_registry_builder__validate_candidate_record__record.get("embedding", [])) != EMBED_DIM:
        return False, "missing_embedding"
    return True, "ok"


def py_function_scripts_primitive_registry_builder__search_row(py_arg_scripts_primitive_registry_builder__search_row__record):
    py_local_scripts_primitive_registry_builder__search_row__blocking_profile = primitive_match.py_function_src_teleon_registry_primitive_match__blocking_profile(py_arg_scripts_primitive_registry_builder__search_row__record)
    return {
        "id": py_arg_scripts_primitive_registry_builder__search_row__record["id"],
        "name": py_arg_scripts_primitive_registry_builder__search_row__record["name"],
        "purpose": py_arg_scripts_primitive_registry_builder__search_row__record["purpose"],
        "keywords": py_arg_scripts_primitive_registry_builder__search_row__record["metadata"]["keywords"],
        "labels": py_arg_scripts_primitive_registry_builder__search_row__record["metadata"]["labels"],
        "tags": py_arg_scripts_primitive_registry_builder__search_row__record["tags"],
        "input_contract": py_arg_scripts_primitive_registry_builder__search_row__record["input_contract"],
        "output_contract": py_arg_scripts_primitive_registry_builder__search_row__record["output_contract"],
        "call_surface": py_arg_scripts_primitive_registry_builder__search_row__record["call_surface"],
        "composition": py_arg_scripts_primitive_registry_builder__search_row__record["composition"],
        "mutation_affordances": py_arg_scripts_primitive_registry_builder__search_row__record["mutation_affordances"],
        "graph_neighbors": py_arg_scripts_primitive_registry_builder__search_row__record["graph_neighbors"],
        "embedding": py_arg_scripts_primitive_registry_builder__search_row__record["embedding"],
        "embedding_dim": py_arg_scripts_primitive_registry_builder__search_row__record["embedding_dim"],
        "search_dimensions": list(primitive_match.py_const_src_teleon_registry_primitive_match__SEARCH_DIMENSIONS),
        "blocking_profile": py_local_scripts_primitive_registry_builder__search_row__blocking_profile,
        "blocking_profile_fields": list(primitive_match.py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS),
        "candidate": True,
        "serves_truth": False,
    }


def py_function_scripts_primitive_registry_builder__vector_row(py_arg_scripts_primitive_registry_builder__vector_row__record):
    return {
        "id": py_arg_scripts_primitive_registry_builder__vector_row__record["id"],
        "embedding": py_arg_scripts_primitive_registry_builder__vector_row__record["embedding"],
        "embedding_dim": py_arg_scripts_primitive_registry_builder__vector_row__record["embedding_dim"],
        "metadata": {
            "name": py_arg_scripts_primitive_registry_builder__vector_row__record["name"],
            "kind": py_arg_scripts_primitive_registry_builder__vector_row__record["license_provenance"]["symbol_kind"],
            "path": py_arg_scripts_primitive_registry_builder__vector_row__record["license_provenance"]["path"],
            "candidate": True,
            "serves_truth": False,
        },
    }


def py_function_scripts_primitive_registry_builder__contract_notation(py_arg_scripts_primitive_registry_builder__contract_notation__contract):
    py_local_scripts_primitive_registry_builder__contract_notation__shape = str(py_arg_scripts_primitive_registry_builder__contract_notation__contract.get("shape") or "unknown")
    py_local_scripts_primitive_registry_builder__contract_notation__fields = py_function_scripts_primitive_registry_builder__contract_fields(py_arg_scripts_primitive_registry_builder__contract_notation__contract)
    if py_local_scripts_primitive_registry_builder__contract_notation__fields:
        return f"{py_local_scripts_primitive_registry_builder__contract_notation__shape}({','.join(py_local_scripts_primitive_registry_builder__contract_notation__fields)})"
    return py_local_scripts_primitive_registry_builder__contract_notation__shape


def py_function_scripts_primitive_registry_builder__edge_row(py_arg_scripts_primitive_registry_builder__edge_row__record, py_arg_scripts_primitive_registry_builder__edge_row__role, py_arg_scripts_primitive_registry_builder__edge_row__contract):
    py_local_scripts_primitive_registry_builder__edge_row__payload = {
        "record": py_arg_scripts_primitive_registry_builder__edge_row__record["id"],
        "role": py_arg_scripts_primitive_registry_builder__edge_row__role,
        "contract": py_arg_scripts_primitive_registry_builder__edge_row__contract,
    }
    return {
        "primitive_edge_id": py_function_scripts_primitive_registry_builder__stable_id("edge", py_local_scripts_primitive_registry_builder__edge_row__payload),
        "registry_record_id": py_arg_scripts_primitive_registry_builder__edge_row__record["id"],
        "edge_role": py_arg_scripts_primitive_registry_builder__edge_row__role,
        "edge_name": py_arg_scripts_primitive_registry_builder__edge_row__role,
        "contract_uid": py_function_scripts_primitive_registry_builder__stable_id("contract", py_arg_scripts_primitive_registry_builder__edge_row__contract),
        "contract_notation": py_function_scripts_primitive_registry_builder__contract_notation(py_arg_scripts_primitive_registry_builder__edge_row__contract),
        "shape": str(py_arg_scripts_primitive_registry_builder__edge_row__contract.get("shape") or "unknown"),
        "field_keys": py_function_scripts_primitive_registry_builder__contract_fields(py_arg_scripts_primitive_registry_builder__edge_row__contract),
        "schema_json": py_arg_scripts_primitive_registry_builder__edge_row__contract,
        "artifact_policy": {},
        "secret_policy": {},
        "edge_hash": py_function_scripts_primitive_registry_builder__sha256(py_function_scripts_primitive_registry_builder__stable_json(py_local_scripts_primitive_registry_builder__edge_row__payload)),
    }


def py_function_scripts_primitive_registry_builder__mutator_agent_rows():
    py_local_scripts_primitive_registry_builder__mutator_agent_rows__rows = {}
    py_local_scripts_primitive_registry_builder__mutator_agent_rows__shape_defaults = {
        "scalar_to_sequence": ("scalar", "sequence"),
        "output_field_wrapper": ("any", "object"),
        "linear_graph_composition": ("primitive_sequence", "graph_contract"),
        "linear_graph_execution": ("graph_contract", "runtime_logs"),
        "field_rename_adapter": ("object", "object"),
        "retry_cache_rate_limit_adapter": ("any", "policy_wrapped_any"),
        "model_cost_downshift": ("model_call", "cheaper_model_call"),
        "browser_to_deterministic_extractor": ("browser_or_llm_extractor", "deterministic_extractor_candidate"),
        "local_api_implementation_swap": ("api_call", "local_or_self_hosted_call"),
        "generated_adapter_candidate": ("incompatible_contracts", "generated_candidate_adapter"),
    }
    py_local_scripts_primitive_registry_builder__mutator_agent_rows__proofs = {
        "scalar_to_sequence": ["singleton_equivalence", "order_preserved", "error_mapping_preserved"],
        "output_field_wrapper": ["payload_preserved", "output_schema_matches"],
        "linear_graph_composition": ["edge_order_preserved", "contract_chain_valid"],
        "linear_graph_execution": ["json_logs_emitted", "contract_chain_executes"],
        "field_rename_adapter": ["explicit_field_map_present", "schema_matches"],
        "retry_cache_rate_limit_adapter": ["policy_logs_retries_cache_and_rate_limits"],
        "model_cost_downshift": ["guardrail_pass_rate", "latency_cost_receipts"],
        "browser_to_deterministic_extractor": ["observed_structure_stability", "extractor_replay"],
        "local_api_implementation_swap": ["same_io_contract", "dependency_license_receipts"],
        "generated_adapter_candidate": ["contract_fixture", "replay_smoke", "human_or_owner_review"],
    }
    for py_local_scripts_primitive_registry_builder__mutator_agent_rows__name, py_local_scripts_primitive_registry_builder__mutator_agent_rows__surface in py_const_scripts_primitive_registry_builder__VERIFIED_MUTATION_CALL_SURFACES.items():
        py_local_scripts_primitive_registry_builder__mutator_agent_rows__from_shape, py_local_scripts_primitive_registry_builder__mutator_agent_rows__to_shape = py_local_scripts_primitive_registry_builder__mutator_agent_rows__shape_defaults.get(py_local_scripts_primitive_registry_builder__mutator_agent_rows__name, ("any", "any"))
        py_local_scripts_primitive_registry_builder__mutator_agent_rows__rows[py_local_scripts_primitive_registry_builder__mutator_agent_rows__name] = {
            "mutator_agent_id": f"mutator:core:{py_local_scripts_primitive_registry_builder__mutator_agent_rows__name}@candidate",
            "tenant_id": "system",
            "kind": "deterministic",
            "short_code": py_local_scripts_primitive_registry_builder__mutator_agent_rows__name,
            "name": py_local_scripts_primitive_registry_builder__mutator_agent_rows__name,
            "from_shape": py_local_scripts_primitive_registry_builder__mutator_agent_rows__from_shape,
            "to_shape": py_local_scripts_primitive_registry_builder__mutator_agent_rows__to_shape,
            "preconditions": [],
            "effect_delta": {"mode": "preserve"},
            "memory_delta": {},
            "cache_delta": {},
            "runtime_delta": {},
            "proof_obligations": py_local_scripts_primitive_registry_builder__mutator_agent_rows__proofs.get(py_local_scripts_primitive_registry_builder__mutator_agent_rows__name, []),
            "auto_apply_policy": "compiler_may_apply_if_preconditions_pass",
            "implementation_ref": py_local_scripts_primitive_registry_builder__mutator_agent_rows__surface,
            "serves_truth": False,
        }
    for py_local_scripts_primitive_registry_builder__mutator_agent_rows__name, py_local_scripts_primitive_registry_builder__mutator_agent_rows__summary in py_const_scripts_primitive_registry_builder__FUTURE_MUTATION_SURFACES.items():
        py_local_scripts_primitive_registry_builder__mutator_agent_rows__from_shape, py_local_scripts_primitive_registry_builder__mutator_agent_rows__to_shape = py_local_scripts_primitive_registry_builder__mutator_agent_rows__shape_defaults.get(py_local_scripts_primitive_registry_builder__mutator_agent_rows__name, ("any", "any"))
        py_local_scripts_primitive_registry_builder__mutator_agent_rows__rows.setdefault(
            py_local_scripts_primitive_registry_builder__mutator_agent_rows__name,
            {
                "mutator_agent_id": f"mutator:core:{py_local_scripts_primitive_registry_builder__mutator_agent_rows__name}@candidate",
                "tenant_id": "system",
                "kind": "nondeterministic" if py_local_scripts_primitive_registry_builder__mutator_agent_rows__name == "generated_adapter_candidate" else "deterministic",
                "short_code": py_local_scripts_primitive_registry_builder__mutator_agent_rows__name,
                "name": py_local_scripts_primitive_registry_builder__mutator_agent_rows__name,
                "from_shape": py_local_scripts_primitive_registry_builder__mutator_agent_rows__from_shape,
                "to_shape": py_local_scripts_primitive_registry_builder__mutator_agent_rows__to_shape,
                "preconditions": [py_local_scripts_primitive_registry_builder__mutator_agent_rows__summary],
                "effect_delta": {"mode": "candidate"},
                "memory_delta": {},
                "cache_delta": {},
                "runtime_delta": {},
                "proof_obligations": py_local_scripts_primitive_registry_builder__mutator_agent_rows__proofs.get(py_local_scripts_primitive_registry_builder__mutator_agent_rows__name, []),
                "auto_apply_policy": "never_auto_apply_without_proof" if py_local_scripts_primitive_registry_builder__mutator_agent_rows__name == "generated_adapter_candidate" else "compiler_may_apply_after_specific_preconditions",
                "implementation_ref": {"summary": py_local_scripts_primitive_registry_builder__mutator_agent_rows__summary},
                "serves_truth": False,
            },
        )
    return list(py_local_scripts_primitive_registry_builder__mutator_agent_rows__rows.values())


def py_function_scripts_primitive_registry_builder__operational_rows(py_arg_scripts_primitive_registry_builder__operational_rows__records, py_arg_scripts_primitive_registry_builder__operational_rows__search_rows):
    py_local_scripts_primitive_registry_builder__operational_rows__rows = {key: [] for key in py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES}
    py_local_scripts_primitive_registry_builder__operational_rows__mutators = py_function_scripts_primitive_registry_builder__mutator_agent_rows()
    py_local_scripts_primitive_registry_builder__operational_rows__mutator_ids = {row["short_code"]: row["mutator_agent_id"] for row in py_local_scripts_primitive_registry_builder__operational_rows__mutators}
    py_local_scripts_primitive_registry_builder__operational_rows__rows["mutator_agent"].extend(py_local_scripts_primitive_registry_builder__operational_rows__mutators)
    py_local_scripts_primitive_registry_builder__operational_rows__search_by_id = {row["id"]: row for row in py_arg_scripts_primitive_registry_builder__operational_rows__search_rows}
    py_local_scripts_primitive_registry_builder__operational_rows__source_seen = set()
    py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_seen = set()

    for py_local_scripts_primitive_registry_builder__operational_rows__record in py_arg_scripts_primitive_registry_builder__operational_rows__records:
        py_local_scripts_primitive_registry_builder__operational_rows__record_id = py_local_scripts_primitive_registry_builder__operational_rows__record["id"]
        py_local_scripts_primitive_registry_builder__operational_rows__license = py_local_scripts_primitive_registry_builder__operational_rows__record.get("license_provenance") or {}
        py_local_scripts_primitive_registry_builder__operational_rows__search = py_local_scripts_primitive_registry_builder__operational_rows__search_by_id.get(py_local_scripts_primitive_registry_builder__operational_rows__record_id, {})
        py_local_scripts_primitive_registry_builder__operational_rows__profile = py_local_scripts_primitive_registry_builder__operational_rows__search.get("blocking_profile") or primitive_match.py_function_src_teleon_registry_primitive_match__blocking_profile(py_local_scripts_primitive_registry_builder__operational_rows__record)
        py_local_scripts_primitive_registry_builder__operational_rows__record_hash = py_function_scripts_primitive_registry_builder__sha256(py_function_scripts_primitive_registry_builder__stable_json(py_local_scripts_primitive_registry_builder__operational_rows__record))
        py_local_scripts_primitive_registry_builder__operational_rows__rows["registry_record"].append({
            "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
            "tenant_id": "system",
            "kind": "primitive",
            "slug": py_function_scripts_primitive_registry_builder__slug(py_local_scripts_primitive_registry_builder__operational_rows__record_id),
            "version": py_local_scripts_primitive_registry_builder__operational_rows__record.get("version") or py_const_scripts_primitive_registry_builder__VERSION,
            "status": "candidate",
            "trust_status": "candidate",
            "readiness_level": "R3_contract_known",
            "serves_truth": False,
            "title": py_local_scripts_primitive_registry_builder__operational_rows__record.get("name") or py_local_scripts_primitive_registry_builder__operational_rows__record_id,
            "blackbox_description": py_local_scripts_primitive_registry_builder__operational_rows__record.get("purpose") or "",
            "canonical_json": py_local_scripts_primitive_registry_builder__operational_rows__record,
            "record_hash": py_local_scripts_primitive_registry_builder__operational_rows__record_hash,
            "source_license": py_local_scripts_primitive_registry_builder__operational_rows__license.get("license"),
            "privacy_boundary": "local",
        })

        py_local_scripts_primitive_registry_builder__operational_rows__input_edge = py_function_scripts_primitive_registry_builder__edge_row(py_local_scripts_primitive_registry_builder__operational_rows__record, "input", py_local_scripts_primitive_registry_builder__operational_rows__record["input_contract"])
        py_local_scripts_primitive_registry_builder__operational_rows__output_edge = py_function_scripts_primitive_registry_builder__edge_row(py_local_scripts_primitive_registry_builder__operational_rows__record, "output", py_local_scripts_primitive_registry_builder__operational_rows__record["output_contract"])
        py_local_scripts_primitive_registry_builder__operational_rows__rows["primitive_edge"].extend([py_local_scripts_primitive_registry_builder__operational_rows__input_edge, py_local_scripts_primitive_registry_builder__operational_rows__output_edge])

        py_local_scripts_primitive_registry_builder__operational_rows__composition = py_local_scripts_primitive_registry_builder__operational_rows__record.get("composition") or {}
        py_local_scripts_primitive_registry_builder__operational_rows__effect_kind = "pure" if py_local_scripts_primitive_registry_builder__operational_rows__composition.get("pure") is True else "external_effect_candidate" if py_local_scripts_primitive_registry_builder__operational_rows__composition.get("side_effect_boundary") else "unknown_candidate"
        py_local_scripts_primitive_registry_builder__operational_rows__rows["primitive_effect"].append({
            "primitive_effect_id": py_function_scripts_primitive_registry_builder__stable_id("effect", {"record": py_local_scripts_primitive_registry_builder__operational_rows__record_id, "kind": py_local_scripts_primitive_registry_builder__operational_rows__effect_kind}),
            "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
            "effect_kind": py_local_scripts_primitive_registry_builder__operational_rows__effect_kind,
            "effect_scope": {"execution_surface": py_local_scripts_primitive_registry_builder__operational_rows__record.get("execution_surface")},
            "requires_gate": py_local_scripts_primitive_registry_builder__operational_rows__effect_kind != "pure",
            "requires_receipt": py_local_scripts_primitive_registry_builder__operational_rows__effect_kind == "external_effect_candidate",
            "idempotency_required": py_local_scripts_primitive_registry_builder__operational_rows__effect_kind == "external_effect_candidate",
        })

        py_local_scripts_primitive_registry_builder__operational_rows__semantic_text = py_local_scripts_primitive_registry_builder__operational_rows__profile.get("semantic_text") or py_local_scripts_primitive_registry_builder__operational_rows__record.get("purpose") or py_local_scripts_primitive_registry_builder__operational_rows__record_id
        py_local_scripts_primitive_registry_builder__operational_rows__text_hash = py_function_scripts_primitive_registry_builder__sha256(py_local_scripts_primitive_registry_builder__operational_rows__semantic_text)
        py_local_scripts_primitive_registry_builder__operational_rows__source_embedding = py_local_scripts_primitive_registry_builder__operational_rows__search.get("embedding") or py_local_scripts_primitive_registry_builder__operational_rows__record.get("embedding")
        py_local_scripts_primitive_registry_builder__operational_rows__source_embedding_dim = len(py_local_scripts_primitive_registry_builder__operational_rows__source_embedding or [])
        py_local_scripts_primitive_registry_builder__operational_rows__rows["registry_embedding"].append({
            "registry_embedding_id": py_function_scripts_primitive_registry_builder__stable_id("regemb", {"record": py_local_scripts_primitive_registry_builder__operational_rows__record_id, "profile": "planning", "text_hash": py_local_scripts_primitive_registry_builder__operational_rows__text_hash}),
            "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
            "object_embedding_id": None,
            "view_profile": "planning",
            "embedding_model_id": "canonical_embedding_pending",
            "text_hash": py_local_scripts_primitive_registry_builder__operational_rows__text_hash,
            "embedded_text": py_local_scripts_primitive_registry_builder__operational_rows__semantic_text,
            "embedding": py_local_scripts_primitive_registry_builder__operational_rows__source_embedding if py_local_scripts_primitive_registry_builder__operational_rows__source_embedding_dim == DEFAULT_EMBEDDING_DIMENSIONS else None,
            "metadata": {
                "source_embedding_dim": py_local_scripts_primitive_registry_builder__operational_rows__source_embedding_dim,
                "canonical_embedding_dim": DEFAULT_EMBEDDING_DIMENSIONS,
                "source": "primitive_registry_builder",
                "serves_truth": False,
            },
        })

        py_local_scripts_primitive_registry_builder__operational_rows__profile_hash = py_function_scripts_primitive_registry_builder__sha256(py_function_scripts_primitive_registry_builder__stable_json(py_local_scripts_primitive_registry_builder__operational_rows__profile))
        py_local_scripts_primitive_registry_builder__operational_rows__rows["primitive_blocking_profile"].append({
            "blocking_profile_id": py_function_scripts_primitive_registry_builder__stable_id("blockprofile", {"record": py_local_scripts_primitive_registry_builder__operational_rows__record_id, "profile_hash": py_local_scripts_primitive_registry_builder__operational_rows__profile_hash}),
            "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
            "exact_keys": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("exact_keys") or [],
            "keyword_keys": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("keyword_keys") or [],
            "label_keys": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("label_keys") or [],
            "input_signature": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("input_signature") or {},
            "output_signature": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("output_signature") or {},
            "graph_signature": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("graph_signature") or [],
            "semantic_text_hash": py_local_scripts_primitive_registry_builder__operational_rows__text_hash,
            "semantic_bucket_keys": primitive_match.py_function_src_teleon_registry_primitive_match__semantic_bucket_keys(py_local_scripts_primitive_registry_builder__operational_rows__profile.get("semantic_embedding") or []),
            "mutation_hints": py_local_scripts_primitive_registry_builder__operational_rows__profile.get("mutation_hints") or [],
            "profile_hash": py_local_scripts_primitive_registry_builder__operational_rows__profile_hash,
            "serves_truth": False,
        })
        for py_local_scripts_primitive_registry_builder__operational_rows__key in primitive_match.py_function_src_teleon_registry_primitive_match__blocking_profile_keys(py_local_scripts_primitive_registry_builder__operational_rows__profile):
            py_local_scripts_primitive_registry_builder__operational_rows__lane = py_local_scripts_primitive_registry_builder__operational_rows__key.split(":", 1)[0]
            py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_identity = ("system", py_local_scripts_primitive_registry_builder__operational_rows__lane, py_local_scripts_primitive_registry_builder__operational_rows__key, py_local_scripts_primitive_registry_builder__operational_rows__record_id, py_local_scripts_primitive_registry_builder__operational_rows__profile_hash)
            if py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_identity in py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_seen:
                continue
            py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_seen.add(py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_identity)
            py_local_scripts_primitive_registry_builder__operational_rows__rows["primitive_blocking_key"].append({
                "blocking_key_id": py_function_scripts_primitive_registry_builder__stable_id("blockkey", py_local_scripts_primitive_registry_builder__operational_rows__blocking_key_identity),
                "tenant_id": "system",
                "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
                "lane": py_local_scripts_primitive_registry_builder__operational_rows__lane if py_local_scripts_primitive_registry_builder__operational_rows__lane in py_const_scripts_primitive_registry_builder__BLOCKING_KEY_LANES else "keyword",
                "key": py_local_scripts_primitive_registry_builder__operational_rows__key,
                "weight": 1.0,
                "profile_hash": py_local_scripts_primitive_registry_builder__operational_rows__profile_hash,
            })

        py_local_scripts_primitive_registry_builder__operational_rows__hints = set(py_local_scripts_primitive_registry_builder__operational_rows__profile.get("mutation_hints") or [])
        py_local_scripts_primitive_registry_builder__operational_rows__hints |= set((py_local_scripts_primitive_registry_builder__operational_rows__record.get("mutation_affordances") or {}).get("applicable_hints") or [])
        for py_local_scripts_primitive_registry_builder__operational_rows__hint in sorted(py_local_scripts_primitive_registry_builder__operational_rows__hints):
            if py_local_scripts_primitive_registry_builder__operational_rows__hint not in py_local_scripts_primitive_registry_builder__operational_rows__mutator_ids:
                continue
            py_local_scripts_primitive_registry_builder__operational_rows__rows["primitive_mutation_option"].append({
                "mutation_option_id": py_function_scripts_primitive_registry_builder__stable_id("mutationoption", {"record": py_local_scripts_primitive_registry_builder__operational_rows__record_id, "hint": py_local_scripts_primitive_registry_builder__operational_rows__hint}),
                "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
                "mutator_agent_id": py_local_scripts_primitive_registry_builder__operational_rows__mutator_ids[py_local_scripts_primitive_registry_builder__operational_rows__hint],
                "from_edge_id": py_local_scripts_primitive_registry_builder__operational_rows__input_edge["primitive_edge_id"] if py_local_scripts_primitive_registry_builder__operational_rows__hint == "scalar_to_sequence" else py_local_scripts_primitive_registry_builder__operational_rows__output_edge["primitive_edge_id"],
                "target_edge_template": {"mutation": py_local_scripts_primitive_registry_builder__operational_rows__hint},
                "fit_class": "nondeterministic_edit_match" if py_local_scripts_primitive_registry_builder__operational_rows__hint == "generated_adapter_candidate" else "deterministic_edit_match",
                "precondition_status": "possible",
                "confidence": 0.5,
                "reason": "precomputed_from_candidate_blocking_profile",
                "serves_truth": False,
            })

        py_local_scripts_primitive_registry_builder__operational_rows__source_path = py_local_scripts_primitive_registry_builder__operational_rows__license.get("path") or "unknown"
        py_local_scripts_primitive_registry_builder__operational_rows__source_id = py_function_scripts_primitive_registry_builder__stable_id("source", {"path": py_local_scripts_primitive_registry_builder__operational_rows__source_path})
        if py_local_scripts_primitive_registry_builder__operational_rows__source_id not in py_local_scripts_primitive_registry_builder__operational_rows__source_seen:
            py_local_scripts_primitive_registry_builder__operational_rows__source_seen.add(py_local_scripts_primitive_registry_builder__operational_rows__source_id)
            py_local_scripts_primitive_registry_builder__operational_rows__rows["registry_source"].append({
                "registry_source_id": py_local_scripts_primitive_registry_builder__operational_rows__source_id,
                "source_kind": "local_repo",
                "source_uri": py_local_scripts_primitive_registry_builder__operational_rows__source_path,
                "archive_uri": None,
                "publisher": "repo",
                "license": py_local_scripts_primitive_registry_builder__operational_rows__license.get("license"),
                "content_hash": py_function_scripts_primitive_registry_builder__sha256(py_local_scripts_primitive_registry_builder__operational_rows__source_path),
                "privacy_boundary": "local",
                "republish_policy": {"raw_source_republish": False},
                "metadata": {"source": py_local_scripts_primitive_registry_builder__operational_rows__license.get("source")},
            })
        py_local_scripts_primitive_registry_builder__operational_rows__rows["registry_source_link"].append({
            "registry_record_id": py_local_scripts_primitive_registry_builder__operational_rows__record_id,
            "registry_source_id": py_local_scripts_primitive_registry_builder__operational_rows__source_id,
            "role": "derived_from",
            "evidence_span": {"line": py_local_scripts_primitive_registry_builder__operational_rows__license.get("line"), "symbol": py_local_scripts_primitive_registry_builder__operational_rows__license.get("symbol_name")},
            "license_status": "candidate",
        })

    return py_local_scripts_primitive_registry_builder__operational_rows__rows


def py_function_scripts_primitive_registry_builder__write_operational_rows(py_arg_scripts_primitive_registry_builder__write_operational_rows__out_dir, py_arg_scripts_primitive_registry_builder__write_operational_rows__rows):
    py_local_scripts_primitive_registry_builder__write_operational_rows__dir = py_arg_scripts_primitive_registry_builder__write_operational_rows__out_dir / "operational"
    py_local_scripts_primitive_registry_builder__write_operational_rows__dir.mkdir(parents=True, exist_ok=True)
    py_local_scripts_primitive_registry_builder__write_operational_rows__counts = {}
    for py_local_scripts_primitive_registry_builder__write_operational_rows__table, py_local_scripts_primitive_registry_builder__write_operational_rows__filename in sorted(py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES.items()):
        py_local_scripts_primitive_registry_builder__write_operational_rows__count = py_function_scripts_primitive_registry_builder__write_jsonl(
            py_local_scripts_primitive_registry_builder__write_operational_rows__dir / py_local_scripts_primitive_registry_builder__write_operational_rows__filename,
            py_arg_scripts_primitive_registry_builder__write_operational_rows__rows.get(py_local_scripts_primitive_registry_builder__write_operational_rows__table, []),
        )
        py_local_scripts_primitive_registry_builder__write_operational_rows__counts[py_local_scripts_primitive_registry_builder__write_operational_rows__table] = py_local_scripts_primitive_registry_builder__write_operational_rows__count
    return py_local_scripts_primitive_registry_builder__write_operational_rows__counts


def py_function_scripts_primitive_registry_builder__build_records_from_inventory(py_arg_scripts_primitive_registry_builder__build_records_from_inventory__inventory_dir, py_arg_scripts_primitive_registry_builder__build_records_from_inventory__limit=py_const_scripts_primitive_registry_builder__MAX_DEFAULT_RECORDS):
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__symbols = py_function_scripts_primitive_registry_builder__load_jsonl(py_arg_scripts_primitive_registry_builder__build_records_from_inventory__inventory_dir / "symbols.jsonl")
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__modules = py_function_scripts_primitive_registry_builder__load_jsonl(py_arg_scripts_primitive_registry_builder__build_records_from_inventory__inventory_dir / "python_modules.jsonl")
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__edges = py_function_scripts_primitive_registry_builder__load_jsonl(py_arg_scripts_primitive_registry_builder__build_records_from_inventory__inventory_dir / "edges.jsonl")
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__module_imports = py_function_scripts_primitive_registry_builder__module_imports_by_path(py_local_scripts_primitive_registry_builder__build_records_from_inventory__modules)
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__args_for_scope = py_function_scripts_primitive_registry_builder__args_by_symbol_scope(py_local_scripts_primitive_registry_builder__build_records_from_inventory__symbols)
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__edges_by_path = py_function_scripts_primitive_registry_builder__records_by_path(py_local_scripts_primitive_registry_builder__build_records_from_inventory__edges)
    py_local_scripts_primitive_registry_builder__build_records_from_inventory__records = []
    py_inst_scripts_primitive_registry_builder__build_records_from_inventory__rejected = Counter()
    for py_local_scripts_primitive_registry_builder__build_records_from_inventory__symbol in py_local_scripts_primitive_registry_builder__build_records_from_inventory__symbols:
        if py_local_scripts_primitive_registry_builder__build_records_from_inventory__symbol.get("kind") not in py_const_scripts_primitive_registry_builder__PRIMITIVE_SYMBOL_KINDS:
            continue
        py_local_scripts_primitive_registry_builder__build_records_from_inventory__record = py_function_scripts_primitive_registry_builder__primitive_record_from_symbol(py_local_scripts_primitive_registry_builder__build_records_from_inventory__symbol, py_local_scripts_primitive_registry_builder__build_records_from_inventory__module_imports, py_local_scripts_primitive_registry_builder__build_records_from_inventory__args_for_scope, py_local_scripts_primitive_registry_builder__build_records_from_inventory__edges_by_path)
        py_local_scripts_primitive_registry_builder__build_records_from_inventory__ok, py_local_scripts_primitive_registry_builder__build_records_from_inventory__reason = py_function_scripts_primitive_registry_builder__validate_candidate_record(py_local_scripts_primitive_registry_builder__build_records_from_inventory__record)
        if py_local_scripts_primitive_registry_builder__build_records_from_inventory__ok:
            py_local_scripts_primitive_registry_builder__build_records_from_inventory__records.append(py_local_scripts_primitive_registry_builder__build_records_from_inventory__record)
        else:
            py_inst_scripts_primitive_registry_builder__build_records_from_inventory__rejected[py_local_scripts_primitive_registry_builder__build_records_from_inventory__reason] += 1
        if py_arg_scripts_primitive_registry_builder__build_records_from_inventory__limit and len(py_local_scripts_primitive_registry_builder__build_records_from_inventory__records) >= py_arg_scripts_primitive_registry_builder__build_records_from_inventory__limit:
            break
    return py_local_scripts_primitive_registry_builder__build_records_from_inventory__records, dict(py_inst_scripts_primitive_registry_builder__build_records_from_inventory__rejected)


def py_function_scripts_primitive_registry_builder__write_summary(py_arg_scripts_primitive_registry_builder__write_summary__out_dir, py_arg_scripts_primitive_registry_builder__write_summary__manifest):
    py_local_scripts_primitive_registry_builder__write_summary__operational_counts = py_arg_scripts_primitive_registry_builder__write_summary__manifest.get("operational_rows") or {}
    py_local_scripts_primitive_registry_builder__write_summary__lines = [
        "# Primitive Registry Builder",
        "",
        f"- Updated: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['created_at']}`",
        f"- Candidate records: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['candidate_records']}`",
        f"- Rejected records: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['rejected_records']}`",
        f"- Embedding dim: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['embedding_dim']}`",
        f"- Blocking index candidates: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['blocking_index_candidates']}`",
        f"- Blocking index keys: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['blocking_index_keys']}`",
        f"- Operational row families: `{len(py_local_scripts_primitive_registry_builder__write_summary__operational_counts)}`",
        f"- Serves truth: `{py_arg_scripts_primitive_registry_builder__write_summary__manifest['serves_truth']}`",
        "",
        "## Required Fields",
        "",
        "```json",
        json.dumps(py_arg_scripts_primitive_registry_builder__write_summary__manifest["required_record_fields"], indent=2, sort_keys=True),
        "```",
        "",
        "## Operational Rows",
        "",
        "```json",
        json.dumps(py_local_scripts_primitive_registry_builder__write_summary__operational_counts, indent=2, sort_keys=True),
        "```",
        "",
        "## Rejections",
        "",
        "```json",
        json.dumps(py_arg_scripts_primitive_registry_builder__write_summary__manifest["rejections"], indent=2, sort_keys=True),
        "```",
        "",
    ]
    (py_arg_scripts_primitive_registry_builder__write_summary__out_dir / "summary.md").write_text("\n".join(py_local_scripts_primitive_registry_builder__write_summary__lines), encoding="utf-8")


def py_function_scripts_primitive_registry_builder__build(py_arg_scripts_primitive_registry_builder__build__inventory_dir, py_arg_scripts_primitive_registry_builder__build__out_dir, py_arg_scripts_primitive_registry_builder__build__limit=py_const_scripts_primitive_registry_builder__MAX_DEFAULT_RECORDS, py_arg_scripts_primitive_registry_builder__build__write=True):
    py_local_scripts_primitive_registry_builder__build__records, py_local_scripts_primitive_registry_builder__build__rejected = py_function_scripts_primitive_registry_builder__build_records_from_inventory(py_arg_scripts_primitive_registry_builder__build__inventory_dir, py_arg_scripts_primitive_registry_builder__build__limit)
    py_local_scripts_primitive_registry_builder__build__search_rows = [py_function_scripts_primitive_registry_builder__search_row(record) for record in py_local_scripts_primitive_registry_builder__build__records]
    py_local_scripts_primitive_registry_builder__build__vector_rows = [py_function_scripts_primitive_registry_builder__vector_row(record) for record in py_local_scripts_primitive_registry_builder__build__records]
    py_local_scripts_primitive_registry_builder__build__blocking_index = primitive_match.py_function_src_teleon_registry_primitive_match__blocking_index(py_local_scripts_primitive_registry_builder__build__search_rows)
    py_local_scripts_primitive_registry_builder__build__operational_rows = py_function_scripts_primitive_registry_builder__operational_rows(py_local_scripts_primitive_registry_builder__build__records, py_local_scripts_primitive_registry_builder__build__search_rows)
    py_local_scripts_primitive_registry_builder__build__operational_counts = {
        py_local_scripts_primitive_registry_builder__build__table: len(py_local_scripts_primitive_registry_builder__build__rows)
        for py_local_scripts_primitive_registry_builder__build__table, py_local_scripts_primitive_registry_builder__build__rows in sorted(py_local_scripts_primitive_registry_builder__build__operational_rows.items())
    }
    py_local_scripts_primitive_registry_builder__build__manifest = {
        "created_at": py_function_scripts_primitive_registry_builder__now(),
        "version": py_const_scripts_primitive_registry_builder__VERSION,
        "serves_truth": False,
        "purpose": "Primitive candidate registry generated from real repo-code inventory artifacts.",
        "source_inventory": str(py_arg_scripts_primitive_registry_builder__build__inventory_dir),
        "candidate_records": len(py_local_scripts_primitive_registry_builder__build__records),
        "search_rows": len(py_local_scripts_primitive_registry_builder__build__search_rows),
        "vector_rows": len(py_local_scripts_primitive_registry_builder__build__vector_rows),
        "blocking_index_candidates": py_local_scripts_primitive_registry_builder__build__blocking_index["candidate_count"],
        "blocking_index_keys": len(py_local_scripts_primitive_registry_builder__build__blocking_index["inverted"]),
        "rejected_records": sum(py_local_scripts_primitive_registry_builder__build__rejected.values()),
        "rejections": py_local_scripts_primitive_registry_builder__build__rejected,
        "embedding_dim": EMBED_DIM,
        "required_record_fields": sorted(py_const_scripts_primitive_registry_builder__REQUIRED_RECORD_FIELDS),
        "operational_rows": py_local_scripts_primitive_registry_builder__build__operational_counts,
        "artifacts": {
            "candidate_records": str(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_candidate_records.jsonl"),
            "search_index": str(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_search_index.jsonl"),
            "blocking_index": str(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_blocking_index.json"),
            "vector_export": str(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_vector_export.jsonl"),
            "manifest": str(py_arg_scripts_primitive_registry_builder__build__out_dir / "manifest.json"),
            "summary": str(py_arg_scripts_primitive_registry_builder__build__out_dir / "summary.md"),
            "operational_rows": {
                py_local_scripts_primitive_registry_builder__build__table: str(py_arg_scripts_primitive_registry_builder__build__out_dir / "operational" / py_local_scripts_primitive_registry_builder__build__filename)
                for py_local_scripts_primitive_registry_builder__build__table, py_local_scripts_primitive_registry_builder__build__filename in sorted(py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES.items())
            },
        },
    }
    if py_arg_scripts_primitive_registry_builder__build__write:
        py_arg_scripts_primitive_registry_builder__build__out_dir.mkdir(parents=True, exist_ok=True)
        py_function_scripts_primitive_registry_builder__write_jsonl(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_candidate_records.jsonl", py_local_scripts_primitive_registry_builder__build__records)
        py_function_scripts_primitive_registry_builder__write_jsonl(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_search_index.jsonl", py_local_scripts_primitive_registry_builder__build__search_rows)
        (py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_blocking_index.json").write_text(json.dumps(py_local_scripts_primitive_registry_builder__build__blocking_index, indent=2, sort_keys=True), encoding="utf-8")
        py_function_scripts_primitive_registry_builder__write_jsonl(py_arg_scripts_primitive_registry_builder__build__out_dir / "primitive_vector_export.jsonl", py_local_scripts_primitive_registry_builder__build__vector_rows)
        py_function_scripts_primitive_registry_builder__write_operational_rows(py_arg_scripts_primitive_registry_builder__build__out_dir, py_local_scripts_primitive_registry_builder__build__operational_rows)
        (py_arg_scripts_primitive_registry_builder__build__out_dir / "manifest.json").write_text(json.dumps(py_local_scripts_primitive_registry_builder__build__manifest, indent=2, sort_keys=True), encoding="utf-8")
        py_function_scripts_primitive_registry_builder__write_summary(py_arg_scripts_primitive_registry_builder__build__out_dir, py_local_scripts_primitive_registry_builder__build__manifest)
    return py_local_scripts_primitive_registry_builder__build__manifest, py_local_scripts_primitive_registry_builder__build__records, py_local_scripts_primitive_registry_builder__build__search_rows, py_local_scripts_primitive_registry_builder__build__vector_rows


def py_function_scripts_primitive_registry_builder__write_fixture_inventory(py_arg_scripts_primitive_registry_builder__write_fixture_inventory__root):
    py_local_scripts_primitive_registry_builder__write_fixture_inventory__inv = py_arg_scripts_primitive_registry_builder__write_fixture_inventory__root / "inventory"
    py_local_scripts_primitive_registry_builder__write_fixture_inventory__inv.mkdir(parents=True, exist_ok=True)
    py_local_scripts_primitive_registry_builder__write_fixture_inventory__symbols = [
        {
            "path": "_repos/teleon/backend/src/teleon/example_rates.py",
            "line": 10,
            "col": 0,
            "kind": "function",
            "name": "normalize_rate",
            "scope": "<module>",
            "target": "py_function_src_teleon_example_rates__normalize_rate",
            "conforms": False,
        },
        {
            "path": "_repos/teleon/backend/src/teleon/example_rates.py",
            "line": 10,
            "col": 19,
            "kind": "arg",
            "name": "rate_text",
            "scope": "normalize_rate",
            "target": "py_arg_src_teleon_example_rates__normalize_rate__rate_text",
            "conforms": False,
        },
        {
            "path": "_repos/teleon/backend/src/teleon/example_rates.py",
            "line": 30,
            "col": 0,
            "kind": "class",
            "name": "RateRecord",
            "scope": "<module>",
            "target": "py_class_src_teleon_example_rates__RateRecord",
            "conforms": False,
        },
    ]
    py_local_scripts_primitive_registry_builder__write_fixture_inventory__modules = [
        {
            "path": "_repos/teleon/backend/src/teleon/example_rates.py",
            "module": "src.teleon.example_rates",
            "package": "src",
            "defs": 3,
            "refs": 2,
            "imports": 1,
            "import_modules": ["re"],
            "edges": 1,
        }
    ]
    py_local_scripts_primitive_registry_builder__write_fixture_inventory__edges = [
        {
            "path": "_repos/teleon/backend/src/teleon/example_rates.py",
            "src": "normalize_rate",
            "dst": "RateRecord",
            "type": "calls",
        }
    ]
    py_function_scripts_primitive_registry_builder__write_jsonl(py_local_scripts_primitive_registry_builder__write_fixture_inventory__inv / "symbols.jsonl", py_local_scripts_primitive_registry_builder__write_fixture_inventory__symbols)
    py_function_scripts_primitive_registry_builder__write_jsonl(py_local_scripts_primitive_registry_builder__write_fixture_inventory__inv / "python_modules.jsonl", py_local_scripts_primitive_registry_builder__write_fixture_inventory__modules)
    py_function_scripts_primitive_registry_builder__write_jsonl(py_local_scripts_primitive_registry_builder__write_fixture_inventory__inv / "edges.jsonl", py_local_scripts_primitive_registry_builder__write_fixture_inventory__edges)
    return py_local_scripts_primitive_registry_builder__write_fixture_inventory__inv


def py_function_scripts_primitive_registry_builder__self_test():
    py_local_scripts_primitive_registry_builder__self_test__failures = []

    def py_function_scripts_primitive_registry_builder__self_test__check(py_arg_scripts_primitive_registry_builder__self_test_check__name, py_arg_scripts_primitive_registry_builder__self_test_check__ok, py_arg_scripts_primitive_registry_builder__self_test_check__detail=""):
        print(f"  [{'ok' if py_arg_scripts_primitive_registry_builder__self_test_check__ok else 'FAIL'}] {py_arg_scripts_primitive_registry_builder__self_test_check__name}{(': ' + py_arg_scripts_primitive_registry_builder__self_test_check__detail) if py_arg_scripts_primitive_registry_builder__self_test_check__detail and not py_arg_scripts_primitive_registry_builder__self_test_check__ok else ''}")
        if not py_arg_scripts_primitive_registry_builder__self_test_check__ok:
            py_local_scripts_primitive_registry_builder__self_test__failures.append(py_arg_scripts_primitive_registry_builder__self_test_check__name)

    with tempfile.TemporaryDirectory() as py_local_scripts_primitive_registry_builder__self_test__tmp:
        py_inst_scripts_primitive_registry_builder__self_test__root = Path(py_local_scripts_primitive_registry_builder__self_test__tmp)
        py_local_scripts_primitive_registry_builder__self_test__inventory = py_function_scripts_primitive_registry_builder__write_fixture_inventory(py_inst_scripts_primitive_registry_builder__self_test__root)
        py_local_scripts_primitive_registry_builder__self_test__out = py_inst_scripts_primitive_registry_builder__self_test__root / "out"
        py_local_scripts_primitive_registry_builder__self_test__manifest, py_local_scripts_primitive_registry_builder__self_test__records, py_local_scripts_primitive_registry_builder__self_test__search_rows, py_local_scripts_primitive_registry_builder__self_test__vector_rows = py_function_scripts_primitive_registry_builder__build(py_local_scripts_primitive_registry_builder__self_test__inventory, py_local_scripts_primitive_registry_builder__self_test__out, 100, True)
        py_local_scripts_primitive_registry_builder__self_test__first = py_local_scripts_primitive_registry_builder__self_test__records[0]
        py_local_scripts_primitive_registry_builder__self_test__blocking_index = json.loads((py_local_scripts_primitive_registry_builder__self_test__out / "primitive_blocking_index.json").read_text(encoding="utf-8"))
        py_function_scripts_primitive_registry_builder__self_test__check("builder writes manifest and candidate/search/blocking/vector artifacts", (py_local_scripts_primitive_registry_builder__self_test__out / "manifest.json").exists() and (py_local_scripts_primitive_registry_builder__self_test__out / "primitive_candidate_records.jsonl").exists() and (py_local_scripts_primitive_registry_builder__self_test__out / "primitive_search_index.jsonl").exists() and (py_local_scripts_primitive_registry_builder__self_test__out / "primitive_blocking_index.json").exists() and (py_local_scripts_primitive_registry_builder__self_test__out / "primitive_vector_export.jsonl").exists())
        py_function_scripts_primitive_registry_builder__self_test__check(
            "builder writes operational row-family artifacts",
            all((py_local_scripts_primitive_registry_builder__self_test__out / "operational" / py_local_scripts_primitive_registry_builder__self_test__filename).exists() for py_local_scripts_primitive_registry_builder__self_test__filename in py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES.values())
            and py_local_scripts_primitive_registry_builder__self_test__manifest["operational_rows"]["registry_record"] == len(py_local_scripts_primitive_registry_builder__self_test__records)
            and py_local_scripts_primitive_registry_builder__self_test__manifest["operational_rows"]["primitive_edge"] == len(py_local_scripts_primitive_registry_builder__self_test__records) * 2
            and py_local_scripts_primitive_registry_builder__self_test__manifest["operational_rows"]["mutator_agent"] == len(py_function_scripts_primitive_registry_builder__mutator_agent_rows()),
        )
        py_function_scripts_primitive_registry_builder__self_test__check("records come from real inventory artifacts", all(record["license_provenance"]["generated_from_real_artifact"] and record["synthetic"] is False for record in py_local_scripts_primitive_registry_builder__self_test__records))
        py_function_scripts_primitive_registry_builder__self_test__check("every record has required primitive fields", all(set(record) >= py_const_scripts_primitive_registry_builder__REQUIRED_RECORD_FIELDS for record in py_local_scripts_primitive_registry_builder__self_test__records), str(set(py_local_scripts_primitive_registry_builder__self_test__first)))
        py_function_scripts_primitive_registry_builder__self_test__check("records are candidate-only and never serve truth", all(record["candidate"] is True and record["serves_truth"] is False for record in py_local_scripts_primitive_registry_builder__self_test__records))
        py_function_scripts_primitive_registry_builder__self_test__check("record includes input/output contracts and proof/log schema", isinstance(py_local_scripts_primitive_registry_builder__self_test__first["input_contract"], dict) and isinstance(py_local_scripts_primitive_registry_builder__self_test__first["output_contract"], dict) and py_local_scripts_primitive_registry_builder__self_test__first["proof_command"] and py_local_scripts_primitive_registry_builder__self_test__first["logs_schema"]["required"])
        py_function_scripts_primitive_registry_builder__self_test__check("record includes dependencies/license provenance/graph edges", py_local_scripts_primitive_registry_builder__self_test__first["dependencies"] == ["re"] and py_local_scripts_primitive_registry_builder__self_test__first["license_provenance"]["path"] and py_local_scripts_primitive_registry_builder__self_test__first["graph_edges"])
        py_function_scripts_primitive_registry_builder__self_test__check("search and vector rows carry embeddings", len(py_local_scripts_primitive_registry_builder__self_test__search_rows[0]["embedding"]) == EMBED_DIM and len(py_local_scripts_primitive_registry_builder__self_test__vector_rows[0]["embedding"]) == EMBED_DIM)
        py_function_scripts_primitive_registry_builder__self_test__check("search row carries precomputed hybrid blocking profile", set(primitive_match.py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS) <= set(py_local_scripts_primitive_registry_builder__self_test__search_rows[0]["blocking_profile"]) and py_local_scripts_primitive_registry_builder__self_test__search_rows[0]["blocking_profile"]["serves_truth"] is False)
        py_function_scripts_primitive_registry_builder__self_test__check("blocking index carries inverted keys for every search row", set(primitive_match.py_const_src_teleon_registry_primitive_match__BLOCKING_INDEX_FIELDS) <= set(py_local_scripts_primitive_registry_builder__self_test__blocking_index) and py_local_scripts_primitive_registry_builder__self_test__blocking_index["candidate_count"] == len(py_local_scripts_primitive_registry_builder__self_test__search_rows) and py_local_scripts_primitive_registry_builder__self_test__blocking_index["serves_truth"] is False)
        py_function_scripts_primitive_registry_builder__self_test__check("manifest is candidate evidence only", py_local_scripts_primitive_registry_builder__self_test__manifest["serves_truth"] is False and py_local_scripts_primitive_registry_builder__self_test__manifest["candidate_records"] == len(py_local_scripts_primitive_registry_builder__self_test__records))
        py_local_scripts_primitive_registry_builder__self_test__placeholder = dict(py_local_scripts_primitive_registry_builder__self_test__first)
        py_local_scripts_primitive_registry_builder__self_test__placeholder["purpose"] = "TODO placeholder text"
        py_local_scripts_primitive_registry_builder__self_test__ok_placeholder, py_local_scripts_primitive_registry_builder__self_test__reason_placeholder = py_function_scripts_primitive_registry_builder__validate_candidate_record(py_local_scripts_primitive_registry_builder__self_test__placeholder)
        py_function_scripts_primitive_registry_builder__self_test__check("placeholder candidate is rejected", not py_local_scripts_primitive_registry_builder__self_test__ok_placeholder and py_local_scripts_primitive_registry_builder__self_test__reason_placeholder == "placeholder_text")
        py_local_scripts_primitive_registry_builder__self_test__synthetic = dict(py_local_scripts_primitive_registry_builder__self_test__first)
        py_local_scripts_primitive_registry_builder__self_test__synthetic["synthetic"] = True
        py_local_scripts_primitive_registry_builder__self_test__synthetic["license_provenance"] = {**py_local_scripts_primitive_registry_builder__self_test__synthetic["license_provenance"], "synthetic": True}
        py_local_scripts_primitive_registry_builder__self_test__ok_synthetic, py_local_scripts_primitive_registry_builder__self_test__reason_synthetic = py_function_scripts_primitive_registry_builder__validate_candidate_record(py_local_scripts_primitive_registry_builder__self_test__synthetic)
        py_function_scripts_primitive_registry_builder__self_test__check("unmarked synthetic candidate is rejected", not py_local_scripts_primitive_registry_builder__self_test__ok_synthetic and py_local_scripts_primitive_registry_builder__self_test__reason_synthetic == "unmarked_synthetic_record")

        py_local_scripts_primitive_registry_builder__self_test__request = {
            "intent": "normalize rate text",
            "labels": ["repo_code", "normalize"],
            "input_contract": py_local_scripts_primitive_registry_builder__self_test__first["input_contract"],
            "output_contract": py_local_scripts_primitive_registry_builder__self_test__first["output_contract"],
            "graph_neighbors": py_local_scripts_primitive_registry_builder__self_test__first["graph_neighbors"],
        }
        py_local_scripts_primitive_registry_builder__self_test__hits = primitive_match.py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_scripts_primitive_registry_builder__self_test__request, py_local_scripts_primitive_registry_builder__self_test__records)
        py_function_scripts_primitive_registry_builder__self_test__check("builder records are compatible with hybrid primitive search", bool(py_local_scripts_primitive_registry_builder__self_test__hits) and py_local_scripts_primitive_registry_builder__self_test__hits[0]["serves_truth"] is False)

    if py_local_scripts_primitive_registry_builder__self_test__failures:
        print(f"\nFAIL - primitive_registry_builder: {len(py_local_scripts_primitive_registry_builder__self_test__failures)} failure(s)")
        return 1
    print("\nPASS - primitive_registry_builder: real-code primitive candidates + search/vector exports + rejection rules")
    return 0


def main(py_arg_scripts_primitive_registry_builder__main__argv=None):
    py_local_scripts_primitive_registry_builder__main__parser = argparse.ArgumentParser(description=__doc__)
    py_local_scripts_primitive_registry_builder__main__parser.add_argument("--inventory", default=str(py_const_scripts_primitive_registry_builder__DEFAULT_INVENTORY))
    py_local_scripts_primitive_registry_builder__main__parser.add_argument("--out", default=str(py_const_scripts_primitive_registry_builder__DEFAULT_OUT))
    py_local_scripts_primitive_registry_builder__main__parser.add_argument("--limit", type=int, default=py_const_scripts_primitive_registry_builder__MAX_DEFAULT_RECORDS)
    py_local_scripts_primitive_registry_builder__main__parser.add_argument("--self-test", action="store_true")
    py_local_scripts_primitive_registry_builder__main__args = py_local_scripts_primitive_registry_builder__main__parser.parse_args(py_arg_scripts_primitive_registry_builder__main__argv)
    if py_local_scripts_primitive_registry_builder__main__args.self_test:
        return py_function_scripts_primitive_registry_builder__self_test()
    py_local_scripts_primitive_registry_builder__main__manifest, py_local_scripts_primitive_registry_builder__main___, py_local_scripts_primitive_registry_builder__main___, py_local_scripts_primitive_registry_builder__main___ = py_function_scripts_primitive_registry_builder__build(Path(py_local_scripts_primitive_registry_builder__main__args.inventory), Path(py_local_scripts_primitive_registry_builder__main__args.out), py_local_scripts_primitive_registry_builder__main__args.limit, True)
    print(json.dumps(py_local_scripts_primitive_registry_builder__main__manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
