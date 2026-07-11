"""Deterministic primitive variation helpers for Teleon.

Purpose: mutate simple Python primitives cheaply without asking an LLM to rewrite solved code. The
first supported mutations are runtime-safe wrappers: scalar -> sequence, output field wrapping, linear
graph composition, and structured variation/run records. AST/source codemods can come later; this module
keeps the first layer deterministic, inspectable, and proofable.

serves_truth=false: contracts, variation records, and run logs are candidate evidence until promoted.
"""
from __future__ import annotations

import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

py_const_src_teleon_synthesis_primitive_variations__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(py_const_src_teleon_synthesis_primitive_variations__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_src_teleon_synthesis_primitive_variations__REPO))
from src.teleon.synthesis import primitive_blocks as py_var_src_teleon_synthesis_primitive_variations__primitive_blocks


py_const_src_teleon_synthesis_primitive_variations__DEFAULT_VARIATION_STATUS = "candidate"
py_const_src_teleon_synthesis_primitive_variations__SCALAR_TO_SEQUENCE_MUTATION = "scalar_to_sequence"
py_const_src_teleon_synthesis_primitive_variations__LINEAR_GRAPH_KIND = "linear_primitive_graph"


def py_function_src_teleon_synthesis_primitive_variations__utc_now():
    """Return an ISO timestamp for candidate run/variation records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def py_function_src_teleon_synthesis_primitive_variations__stable_json(py_arg_value):
    """Return deterministic JSON for contracts and logs.

    Purpose: variation records need stable comparison/diff behavior for git-like storage. Non-JSON values
    are represented with repr so the record remains serializable candidate evidence.
    """
    return json.dumps(py_arg_value, sort_keys=True, separators=(",", ":"), default=repr)


def py_function_src_teleon_synthesis_primitive_variations__primitive_contract(
    py_arg_primitive_id,
    py_arg_purpose,
    py_arg_input_contract,
    py_arg_output_contract,
    py_arg_dependencies=None,
    py_arg_guardrails=None,
    py_arg_execution_surface="python_callable",
    py_arg_logs_schema=None,
    py_arg_version="0.1.0",
):
    """Create the standard primitive contract envelope.

    Purpose: every primitive, whether local code, private service, or third-party API, should expose the
    same searchable I/O envelope so Teleon can assemble graphs without reading full source.
    """
    return {
        "id": py_arg_primitive_id,
        "version": py_arg_version,
        "purpose": py_arg_purpose,
        "input_contract": dict(py_arg_input_contract),
        "output_contract": dict(py_arg_output_contract),
        "dependencies": list(py_arg_dependencies or []),
        "guardrails": list(py_arg_guardrails or []),
        "execution_surface": py_arg_execution_surface,
        "logs_schema": dict(py_arg_logs_schema or {
            "event": "primitive_run",
            "required": ["primitive_id", "status", "started_at", "completed_at"],
        }),
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable(
    py_arg_primitive_id,
    py_arg_callable,
    py_arg_purpose,
):
    """Infer a minimal contract from a Python callable signature.

    Purpose: cheap bootstrap for local primitives. The inferred contract is intentionally weak and marked
    candidate; observed runtime shapes and explicit schemas should refine it before promotion.
    """
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_signature = inspect.signature(py_arg_callable)
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_inputs = []
    for py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_name, py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_param in py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_signature.parameters.items():
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_inputs.append({
            "name": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_name,
            "kind": str(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_param.kind).replace("Parameter.", "").lower(),
            "required": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_param.default is inspect._empty,
            "annotation": None if py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_param.annotation is inspect._empty else repr(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_param.annotation),
        })
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_return_annotation = py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_signature.return_annotation
    return py_function_src_teleon_synthesis_primitive_variations__primitive_contract(
        py_arg_primitive_id,
        py_arg_purpose,
        {"shape": "callable_signature", "parameters": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_inputs},
        {
            "shape": "unknown_candidate",
            "annotation": None if py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_return_annotation is inspect._empty else repr(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable__py_var_return_annotation),
        },
    )


def py_function_src_teleon_synthesis_primitive_variations__variation_record(
    py_arg_base_contract,
    py_arg_new_contract,
    py_arg_mutation_kind,
    py_arg_mutation_summary,
    py_arg_proofs=None,
    py_arg_status=py_const_src_teleon_synthesis_primitive_variations__DEFAULT_VARIATION_STATUS,
):
    """Create a git-like primitive variation record.

    Purpose: baseline, forks, tuned variants, and regression fixes should be stored as records with
    diffable before/after contracts, not as untracked prompt output.
    """
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__variation_record__py_var_base_id = py_arg_base_contract["id"]
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__variation_record__py_var_new_id = py_arg_new_contract["id"]
    return {
        "id": f"{py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__variation_record__py_var_new_id}::variation::{py_arg_mutation_kind}",
        "variation_of": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__variation_record__py_var_base_id,
        "variant": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__variation_record__py_var_new_id,
        "mutation_kind": py_arg_mutation_kind,
        "mutation_summary": py_arg_mutation_summary,
        "base_contract": py_arg_base_contract,
        "new_contract": py_arg_new_contract,
        "proofs": list(py_arg_proofs or []),
        "status": py_arg_status,
        "created_at": py_function_src_teleon_synthesis_primitive_variations__utc_now(),
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation(
    py_arg_base_contract,
    py_arg_scalar_callable,
    py_arg_variant_id=None,
):
    """Return a scalar->sequence wrapper plus contracts and variation metadata.

    Purpose: the common mutation "this takes one item; make it take an array" should be deterministic and
    cheap. The wrapper delegates to primitive_blocks.map_sequence, so retries/logging/envelopes stay
    consistent across generated pipelines.
    """
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_variant_id = py_arg_variant_id or f"{py_arg_base_contract['id']}__batch"
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_sequence_callable = py_var_src_teleon_synthesis_primitive_variations__primitive_blocks.py_function_src_teleon_synthesis_primitive_blocks__lift_scalar_step_to_sequence_step(
        py_arg_scalar_callable
    )
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_new_contract = dict(py_arg_base_contract)
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_new_contract.update({
        "id": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_variant_id,
        "purpose": f"Batch/sequence variant of {py_arg_base_contract['id']}: {py_arg_base_contract.get('purpose', '')}",
        "input_contract": {
            "shape": "scalar_or_sequence",
            "items_contract": py_arg_base_contract.get("input_contract", {}),
        },
        "output_contract": {
            "shape": "candidate_sequence_envelope",
            "item_output_contract": py_arg_base_contract.get("output_contract", {}),
        },
        "serves_truth": False,
    })
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_record = py_function_src_teleon_synthesis_primitive_variations__variation_record(
        py_arg_base_contract,
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_new_contract,
        py_const_src_teleon_synthesis_primitive_variations__SCALAR_TO_SEQUENCE_MUTATION,
        "Wrap scalar callable with normalize_to_sequence + map_sequence; no business logic rewrite.",
        py_arg_proofs=["wrapper_executes", "outputs_candidate_envelopes"],
    )
    return {
        "callable": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_sequence_callable,
        "contract": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_new_contract,
        "variation": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation__py_var_record,
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation(
    py_arg_base_contract,
    py_arg_callable,
    py_arg_output_field,
    py_arg_variant_id=None,
):
    """Wrap a primitive output into a named dict field without changing the underlying callable."""
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_var_variant_id = py_arg_variant_id or f"{py_arg_base_contract['id']}__output_as_{py_arg_output_field}"

    def py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_function_wrapper(*py_arg_args, **py_arg_kwargs):
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation_py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_function_wrapper__py_var_value = py_arg_callable(*py_arg_args, **py_arg_kwargs)
        return {py_arg_output_field: py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation_py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_function_wrapper__py_var_value, "serves_truth": False}

    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_var_new_contract = dict(py_arg_base_contract)
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_var_new_contract.update({
        "id": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_var_variant_id,
        "output_contract": {
            "shape": "object",
            "fields": {
                py_arg_output_field: py_arg_base_contract.get("output_contract", {}),
                "serves_truth": {"const": False},
            },
        },
        "serves_truth": False,
    })
    return {
        "callable": py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_function_wrapper,
        "contract": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_var_new_contract,
        "variation": py_function_src_teleon_synthesis_primitive_variations__variation_record(
            py_arg_base_contract,
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation__py_var_new_contract,
            "wrap_output_field",
            f"Wrap callable result into output field {py_arg_output_field!r}.",
            py_arg_proofs=["wrapper_executes"],
        ),
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract(
    py_arg_graph_id,
    py_arg_steps,
    py_arg_purpose,
    py_arg_guardrails=None,
):
    """Create a compact primitive graph plan from ordered primitive contracts."""
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract__py_var_edges = []
    for py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract__py_var_index in range(max(0, len(py_arg_steps) - 1)):
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract__py_var_edges.append({
            "type": "maps_output_to_input",
            "from": py_arg_steps[py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract__py_var_index]["id"],
            "to": py_arg_steps[py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract__py_var_index + 1]["id"],
            "serves_truth": False,
        })
    return {
        "id": py_arg_graph_id,
        "kind": py_const_src_teleon_synthesis_primitive_variations__LINEAR_GRAPH_KIND,
        "purpose": py_arg_purpose,
        "steps": [py_var_step["id"] for py_var_step in py_arg_steps],
        "input_contract": py_arg_steps[0].get("input_contract", {}) if py_arg_steps else {},
        "output_contract": py_arg_steps[-1].get("output_contract", {}) if py_arg_steps else {},
        "guardrails": list(py_arg_guardrails or []),
        "graph_edges": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract__py_var_edges,
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph(
    py_arg_graph_contract,
    py_arg_step_callables,
    py_arg_input_value,
):
    """Execute a simple ordered primitive graph and return structured logs.

    Purpose: keep primitive assembly observable. Every step produces a log record with before/after shape
    classes, timing placeholders, status, and candidate-only state.
    """
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_value = py_arg_input_value
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_logs = []
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_started_at = py_function_src_teleon_synthesis_primitive_variations__utc_now()
    for py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_step_id in py_arg_graph_contract.get("steps", []):
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_step_started_at = py_function_src_teleon_synthesis_primitive_variations__utc_now()
        try:
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_value = py_arg_step_callables[py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_step_id](py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_value)
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_status = "ok"
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_error = None
        except Exception as py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_exc:  # noqa: BLE001 - candidate execution logs must capture all failure modes
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_status = "error"
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_error = f"{type(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_exc).__name__}: {py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_exc}"
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_logs.append({
            "event": "primitive_step_run",
            "graph_id": py_arg_graph_contract["id"],
            "primitive_id": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_step_id,
            "status": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_status,
            "error": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_error,
            "started_at": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_step_started_at,
            "completed_at": py_function_src_teleon_synthesis_primitive_variations__utc_now(),
            "output_shape": type(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_value).__name__,
            "serves_truth": False,
        })
        if py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_status != "ok":
            break
    return {
        "graph_id": py_arg_graph_contract["id"],
        "started_at": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_started_at,
        "completed_at": py_function_src_teleon_synthesis_primitive_variations__utc_now(),
        "status": "ok" if all(py_var_log["status"] == "ok" for py_var_log in py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_logs) else "error",
        "value": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_value,
        "logs": py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph__py_var_logs,
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_variations___self_test():
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_failures = []

    def py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(py_arg_name, py_arg_ok):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}")
        if not py_arg_ok:
            py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_failures.append(py_arg_name)

    def py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_double(py_arg_value):
        return py_arg_value * 2

    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_contract = py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable(
        "primitive.math.double",
        py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_double,
        "Double one scalar value.",
    )
    py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(
        "infer callable contract captures parameter shape",
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_contract["input_contract"]["parameters"][0]["name"] == "py_arg_value",
    )

    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_batch = py_function_src_teleon_synthesis_primitive_variations__lift_scalar_callable_to_sequence_variation(
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_contract,
        py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_double,
    )
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_batch_result = py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_batch["callable"]([1, 2, 3])
    py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(
        "scalar callable mutates to sequence callable without rewriting logic",
        [py_var_row["value"] for py_var_row in py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_batch_result["outputs"]] == [2, 4, 6],
    )
    py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(
        "variation record stores before/after contracts and mutation kind",
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_batch["variation"]["variation_of"] == "primitive.math.double"
        and py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_batch["variation"]["mutation_kind"] == py_const_src_teleon_synthesis_primitive_variations__SCALAR_TO_SEQUENCE_MUTATION,
    )

    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_wrapped = py_function_src_teleon_synthesis_primitive_variations__wrap_output_field_variation(
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_contract,
        py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_double,
        "doubled",
    )
    py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(
        "output wrapper adapts shape deterministically",
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_wrapped["callable"](4)["doubled"] == 8,
    )

    def py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_plus_one(py_arg_value):
        return py_arg_value + 1

    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_plus_contract = py_function_src_teleon_synthesis_primitive_variations__infer_contract_from_callable(
        "primitive.math.plus_one",
        py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_plus_one,
        "Add one.",
    )
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_graph = py_function_src_teleon_synthesis_primitive_variations__linear_graph_contract(
        "graph.double_then_plus_one",
        [py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_contract, py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_plus_contract],
        "Double a value then add one.",
    )
    py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_run = py_function_src_teleon_synthesis_primitive_variations__execute_linear_graph(
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_graph,
        {
            "primitive.math.double": py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_double,
            "primitive.math.plus_one": py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_plus_one,
        },
        5,
    )
    py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(
        "linear graph executes with structured logs",
        py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_run["value"] == 11 and len(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_run["logs"]) == 2 and py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_run["logs"][0]["event"] == "primitive_step_run",
    )
    py_function_src_teleon_synthesis_primitive_variations___self_test__py_function_check(
        "contract and logs are deterministic-json serializable",
        "primitive.math.double" in py_function_src_teleon_synthesis_primitive_variations__stable_json(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_run),
    )

    if py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_failures:
        print(f"\nFAIL - primitive_variations: {len(py_local_src_teleon_synthesis_primitive_variations__py_function_src_teleon_synthesis_primitive_variations__self_test__py_var_failures)} failure(s)")
        return 1
    print("\nPASS - primitive_variations: deterministic primitive contracts, scalar->sequence variants, output adapters, graph execution logs")
    return 0


if __name__ == "__main__":
    raise SystemExit(py_function_src_teleon_synthesis_primitive_variations___self_test())
