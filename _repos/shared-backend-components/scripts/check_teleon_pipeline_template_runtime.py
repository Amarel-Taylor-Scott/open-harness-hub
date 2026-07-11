#!/usr/bin/env python3
"""Proof: Teleon pipeline templates compile LLM JSON into deterministic primitive-step runtimes.

This checker binds the ergonomic runtime law:

* a pipeline is one primitive step per line / one JSON object per step;
* the LLM names primitive ids and bindings, not callables or code;
* deterministic compilation resolves primitive ids from an allowed registry;
* execution owns task state, artifact refs, bounded retries, and JSON events;
* every artifact/event remains candidate-only until proof/promotion.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import ast
import json
from pathlib import Path

py_const_scripts_check_teleon_pipeline_template_runtime__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
import sys
if str(py_const_scripts_check_teleon_pipeline_template_runtime__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_teleon_pipeline_template_runtime__REPO))

from src.teleon.synthesis import pipeline_templates as py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates
from src.teleon.synthesis import pipeline_object_api as py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api


py_const_scripts_check_teleon_pipeline_template_runtime__CONTRACT = (
    _resource("architecture/teleon_pipeline_template_runtime_contracts.json")
)
py_const_scripts_check_teleon_pipeline_template_runtime__RUNTIME = (
    _resource("src/teleon/synthesis/pipeline_templates.py")
)

py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_STATE_PATTERNS = {
    "task_value",
    "task_patch",
    "named_inputs",
    "artifact_ref",
    "object_graph",
}
py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_LOG_FIELDS = {
    "event_index",
    "run_id",
    "step_id",
    "primitive_id",
    "attempt",
    "status",
    "input_digest",
    "output_digest",
    "error",
    "serves_truth",
}
py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_COMPILE_CHECKS = {
    "template serves_truth=false",
    "every step has a step_id",
    "step_id is unique",
    "primitive_id exists in allowed callable registry",
    "state_mode is one of task_value/task_patch/named_inputs",
    "state paths use only $task/$context/$nodes/$system",
    "output_storage is inline or artifact_ref",
    "max_attempts is bounded and explicit",
    "callable object graphs flatten to serializable step specs before execution",
    "callable introspection emits candidate primitive records and compact LLM views only",
    "compiled output serves_truth=false",
}
py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_PYTHON_AUTHORING_SURFACES = {
    "primitive_metadata decorator",
    "primitive_handle",
    "callable_surface",
    "primitive_id_from_callable",
    "primitive_record_from_callable",
    "compact_llm_view_from_primitive_record",
    "derive_step_id",
    "primitive_step_from_handle",
    "pipeline_template_from_primitives",
    "compile_pipeline_template_from_primitives",
    "flatten_primitive_object_graph",
    "handles_from_primitive_object_graph",
    "pipeline_template_from_object_graph",
    "compile_pipeline_template_from_object_graph",
    "object-first Primitive facade",
    "object-first Pipeline facade",
    "operator composition with >>",
    "namespace primitive discovery",
    "standard compact alias lines",
}
py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_OBJECT_API_SYMBOLS = {
    "SERVES_TRUTH",
    "Primitive",
    "Pipeline",
    "primitive",
    "pipeline",
    "discover_primitives",
    "compact_alias_lines",
}
py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_NO_MAGIC_POLICIES = {
    "canonical primitive ids remain the JSON/wire format for LLM plans and lockfiles",
    "Python pipeline sites should prefer callable-backed primitive handles for local primitives",
    "step ids are derived from primitive ids by the deterministic compiler unless an explicit alias is required",
    "duplicate primitive use receives deterministic suffixes instead of manually invented labels",
    "nested Python containers may organize primitives, but the runtime records structure_path instead of requiring hand-authored step labels",
}
py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_FUNCTIONS = {
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_step",
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata",
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_handle",
    "py_function_src_teleon_synthesis_pipeline_templates__callable_surface",
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract",
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable",
    "py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record",
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable",
    "py_function_src_teleon_synthesis_pipeline_templates__derive_step_id",
    "py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle",
    "py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives",
    "py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives",
    "py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph",
    "py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph",
    "py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_object_graph",
    "py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph",
    "py_function_src_teleon_synthesis_pipeline_templates__pipeline_template",
    "py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template",
    "py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template",
    "py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref",
}


def py_function_scripts_check_teleon_pipeline_template_runtime__load_contract() -> dict:
    return json.loads(py_const_scripts_check_teleon_pipeline_template_runtime__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_teleon_pipeline_template_runtime__runtime_has_no_while_loops() -> bool:
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__runtime_has_no_while_loops__py_var_tree = ast.parse(py_const_scripts_check_teleon_pipeline_template_runtime__RUNTIME.read_text(encoding="utf-8"))
    return not any(isinstance(py_var_node, ast.While) for py_var_node in ast.walk(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__runtime_has_no_while_loops__py_var_tree))


def py_function_scripts_check_teleon_pipeline_template_runtime___self_test() -> int:
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_failures = []

    def py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        py_arg_name,
        py_arg_ok,
        py_arg_detail="",
    ):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_failures.append(py_arg_name)

    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract = py_function_scripts_check_teleon_pipeline_template_runtime__load_contract()
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract and runtime are candidate-only",
        py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("serves_truth") is False
        and py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates.py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH is False,
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract preserves the one-line-per-step authoring law",
        "one primitive step per line" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("core_law", ""),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "LLM boundary forbids direct callables/code execution",
        "may not emit callable objects" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("llm_boundary", ""),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "Python authoring law avoids magic strings at pipeline call sites",
        "callable" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("python_authoring_law", "")
        and "derived" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("python_authoring_law", ""),
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_python_surfaces = set(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("python_authoring_surfaces", []))
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract names callable-backed Python authoring surfaces",
        py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_PYTHON_AUTHORING_SURFACES <= py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_python_surfaces,
        str(sorted(py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_PYTHON_AUTHORING_SURFACES - py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_python_surfaces)),
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_no_magic_policies = set(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("no_magic_string_policy", []))
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract keeps IDs as wire format but discourages stringly Python pipelines",
        py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_NO_MAGIC_POLICIES <= py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_no_magic_policies,
        str(sorted(py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_NO_MAGIC_POLICIES - py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_no_magic_policies)),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract supports object-graph authoring without arbitrary object crawling",
        "lists, tuples, dicts, or matrices" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("object_graph_authoring_law", "")
        and "does not crawl arbitrary object internals" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("object_graph_authoring_law", ""),
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_introspection_contract = py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("introspection_contract", {})
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract covers callable introspection into primitive records and compact views",
        "inspect.signature parameters" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_introspection_contract.get("deterministic_fields", [])
        and "candidate primitive record" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_introspection_contract.get("outputs", [])
        and "compact LLM view" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_introspection_contract.get("outputs", []),
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_state_patterns = {py_var_pattern.get("id") for py_var_pattern in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("state_patterns", [])}
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "contract covers task, binding, and artifact state patterns",
        py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_STATE_PATTERNS <= py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_state_patterns,
        str(sorted(py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_STATE_PATTERNS - py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_state_patterns)),
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_log_fields = set(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("logging_contract", {}).get("required_fields", []))
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "logging contract has required JSON event fields",
        py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_LOG_FIELDS <= py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_log_fields,
        str(sorted(py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_LOG_FIELDS - py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_log_fields)),
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_compile_checks = set(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_contract.get("compile_checks", []))
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "compile checks enforce registry-only deterministic resolution",
        py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_COMPILE_CHECKS <= py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_compile_checks,
        str(sorted(py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_COMPILE_CHECKS - py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_compile_checks)),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "runtime exports required pyprefix functions",
        all(hasattr(py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates, py_var_name) for py_var_name in py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_FUNCTIONS),
        str([py_var_name for py_var_name in py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_FUNCTIONS if not hasattr(py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates, py_var_name)]),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "object-first facade exports clean Python authoring objects",
        py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api.SERVES_TRUTH is False
        and all(hasattr(py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api, py_var_name) for py_var_name in py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_OBJECT_API_SYMBOLS),
        str([py_var_name for py_var_name in py_const_scripts_check_teleon_pipeline_template_runtime__REQUIRED_OBJECT_API_SYMBOLS if not hasattr(py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api, py_var_name)]),
    )

    @py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api.primitive(
        state_mode=py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
    )
    def py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_normalize_invoice(py_arg_task: dict) -> dict:
        """Normalize a business task without hand-authored primitive ids."""
        return {
            "vendor_name": str(py_arg_task.get("vendor_name", "")).strip(),
            "amount": round(float(py_arg_task.get("amount", 0.0)), 2),
        }

    @py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api.primitive(
        state_mode=py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
    )
    def py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_validate_invoice(py_arg_task: dict) -> dict:
        """Validate the normalized business task."""
        return {
            "is_valid": bool(py_arg_task.get("vendor_name")) and float(py_arg_task.get("amount", 0.0)) > 0.0,
        }

    @py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api.primitive(
        state_mode=py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
    )
    def py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_emit_packet(py_arg_task: dict) -> dict:
        """Emit the review packet."""
        return {
            "review_packet": {
                "vendor_name": py_arg_task["vendor_name"],
                "amount": py_arg_task["amount"],
                "is_valid": py_arg_task["is_valid"],
            }
        }

    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_flow = (
        py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_normalize_invoice
        >> py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_validate_invoice
        >> py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_emit_packet
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_compiled = py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_flow.compile(
        "object_api_invoice_review",
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_result = py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_flow.run(
        {"record_id": "object_api", "vendor_name": "  Example Vendor  ", "amount": "42.25"},
        template_id="object_api_invoice_review",
        run_id="run_object_api",
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "object-first pipeline composes Python objects and compiles to step specs",
        py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_compiled["ok"]
        and len(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_compiled["compiled_steps"]) == 3
        and all(py_var_compiled_step["step"]["serves_truth"] is False for py_var_compiled_step in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_compiled["compiled_steps"]),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "object-first pipeline executes through the existing deterministic runtime",
        py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_result["ok"]
        and py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_result["task"]["review_packet"]["vendor_name"] == "Example Vendor"
        and py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_result["task"]["review_packet"]["is_valid"] is True,
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_discovered_primitives = py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api.discover_primitives({
        "normalize": py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_normalize_invoice,
        "validate": py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_validate_invoice,
        "emit": py_function_scripts_check_teleon_pipeline_template_runtime___self_test__object_api_emit_packet,
    })
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_alias_lines = py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_object_api.compact_alias_lines(
        py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_discovered_primitives,
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "object-first facade emits standardized compact alias lines",
        len(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_alias_lines) == 3
        and py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_alias_lines[0].startswith("P0 ")
        and "mode:task_patch" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_alias_lines[0]
        and "truth:0" in py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_alias_lines[0],
    )
    py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_graph_compiled = py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph(
        "object_api_as_opt_in_graph",
        py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_flow,
        "Object-first pipeline accepted as an opt-in primitive graph.",
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "object-first Pipeline is an opt-in object graph, not arbitrary object crawling",
        py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_graph_compiled["ok"]
        and len(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_object_graph_compiled["compiled_steps"]) == 3,
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "template runtime uses bounded for-retry loops, not while loops",
        py_function_scripts_check_teleon_pipeline_template_runtime__runtime_has_no_while_loops(),
    )
    py_function_scripts_check_teleon_pipeline_template_runtime___self_test__check(
        "pipeline template runtime self-test passes",
        py_var_scripts_check_teleon_pipeline_template_runtime__pipeline_templates.py_function_src_teleon_synthesis_pipeline_templates___self_test() == 0,
    )

    if py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_failures:
        print(f"\nFAIL - check_teleon_pipeline_template_runtime: {len(py_local_scripts_check_teleon_pipeline_template_runtime__py_function_scripts_check_teleon_pipeline_template_runtime__self_test__py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_teleon_pipeline_template_runtime: one-line primitive templates compile/run deterministically with task state, JSON logs, retries, and artifact refs")
    return 0


def py_function_scripts_check_teleon_pipeline_template_runtime__main() -> int:
    return py_function_scripts_check_teleon_pipeline_template_runtime___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_teleon_pipeline_template_runtime__main())
