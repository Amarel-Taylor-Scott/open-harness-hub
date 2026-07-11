"""Deterministic one-line primitive pipeline templates for Teleon.

Purpose: make primitive pipelines easy to manage without asking an LLM to write glue code. An LLM may
emit compact JSON step specs, but this module resolves primitives from an allowed callable registry,
executes a bounded one-line-per-step sequence, and records structured candidate logs.

The runtime supports the common state patterns:

* task_value: a primitive accepts the whole task and returns the next task;
* task_patch: a primitive accepts the whole task and returns a dict patch to merge into the task;
* named_inputs: a primitive receives explicit keyword inputs resolved from task/context/node paths;
* artifact_ref: large or durable outputs are stored by digest and only a reference is passed onward.

serves_truth=false: templates, compiled templates, run events, artifacts, and outputs are candidate
execution evidence until a proof/promotion gate verifies them.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from copy import deepcopy


py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH = False
py_const_src_teleon_synthesis_pipeline_templates__TEMPLATE_VERSION = "0.1.0"
py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_RECORD_VERSION = "primitive_record.v0"
py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE = "task_value"
py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH = "task_patch"
py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_NAMED_INPUTS = "named_inputs"
py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE = "inline"
py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_ARTIFACT_REF = "artifact_ref"
py_const_src_teleon_synthesis_pipeline_templates__ALLOWED_STATE_MODES = {
    py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE,
    py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
    py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_NAMED_INPUTS,
}
py_const_src_teleon_synthesis_pipeline_templates__ALLOWED_OUTPUT_STORAGE = {
    py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE,
    py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_ARTIFACT_REF,
}
py_const_src_teleon_synthesis_pipeline_templates__ALLOWED_PATH_ROOTS = {"$task", "$context", "$nodes", "$system"}
py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS = 1
py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_SPEC_ATTR = "__teleon_primitive_spec__"
py_const_src_teleon_synthesis_pipeline_templates__PIPELINE_PRIMITIVES_ATTR = "__teleon_pipeline_primitives__"


def py_function_src_teleon_synthesis_pipeline_templates__annotation_name(py_arg_annotation) -> str:
    """Return a compact deterministic name for a Python annotation."""
    if py_arg_annotation is inspect.Signature.empty:
        return "Any"
    if isinstance(py_arg_annotation, str):
        return py_arg_annotation
    if getattr(py_arg_annotation, "__module__", "") == "builtins" and getattr(py_arg_annotation, "__name__", None):
        return py_arg_annotation.__name__
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__annotation_name__py_var_text = str(py_arg_annotation)
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__annotation_name__py_var_text.replace("typing.", "")


def py_function_src_teleon_synthesis_pipeline_templates__callable_surface(py_arg_callable) -> dict:
    """Return the deterministic Python surface that can identify and describe a primitive callable."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_module = getattr(py_arg_callable, "__module__", "unknown_module")
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_qualname = getattr(py_arg_callable, "__qualname__", getattr(py_arg_callable, "__name__", "unknown_callable"))
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_name = getattr(py_arg_callable, "__name__", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_qualname.rsplit(".", 1)[-1])
    return {
        "module": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_module,
        "qualname": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_qualname,
        "name": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_name,
        "surface_id": f"{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_module}.{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__callable_surface__py_var_qualname}",
    }


def py_function_src_teleon_synthesis_pipeline_templates__stable_json(py_arg_value) -> str:
    """Return deterministic JSON for template digests and candidate logs."""
    return json.dumps(py_arg_value, sort_keys=True, separators=(",", ":"), default=repr)


def py_function_src_teleon_synthesis_pipeline_templates__stable_digest(py_arg_value) -> str:
    """Return a deterministic sha256 digest for task, template, node, and artifact records."""
    return hashlib.sha256(
        py_function_src_teleon_synthesis_pipeline_templates__stable_json(py_arg_value).encode("utf-8")
    ).hexdigest()


def py_function_src_teleon_synthesis_pipeline_templates__path_is_allowed(py_arg_path: str) -> bool:
    """Return whether a template path is inside an allowed state root."""
    return any(py_arg_path == py_var_root or py_arg_path.startswith(f"{py_var_root}.") for py_var_root in py_const_src_teleon_synthesis_pipeline_templates__ALLOWED_PATH_ROOTS)


def py_function_src_teleon_synthesis_pipeline_templates__get_path(py_arg_state: dict, py_arg_path: str):
    """Resolve a simple `$root.key.key` state path without eval or dynamic attribute access."""
    if not py_function_src_teleon_synthesis_pipeline_templates__path_is_allowed(py_arg_path):
        raise KeyError(f"path root is not allowed: {py_arg_path}")
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_parts = py_arg_path.split(".")
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_root = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_parts[0]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_value = {
        "$task": py_arg_state["task"],
        "$context": py_arg_state["context"],
        "$nodes": py_arg_state["nodes"],
        "$system": py_arg_state["system"],
    }[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_root]
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_part in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_parts[1:]:
        if isinstance(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_value, dict) and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_part in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_value:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_value = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_value[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_part]
            continue
        raise KeyError(f"path does not exist: {py_arg_path}")
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__get_path__py_var_value


def py_function_src_teleon_synthesis_pipeline_templates__set_path(py_arg_state: dict, py_arg_path: str, py_arg_value) -> None:
    """Set a simple `$task.foo`, `$context.foo`, or `$nodes.node.output` path."""
    if not py_function_src_teleon_synthesis_pipeline_templates__path_is_allowed(py_arg_path):
        raise KeyError(f"path root is not allowed: {py_arg_path}")
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_parts = py_arg_path.split(".")
    if len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_parts) == 1:
        if py_arg_path == "$task":
            py_arg_state["task"] = py_arg_value
            return
        raise KeyError(f"root path is read-only for direct set: {py_arg_path}")
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_root = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_parts[0]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_container = {
        "$task": py_arg_state["task"],
        "$context": py_arg_state["context"],
        "$nodes": py_arg_state["nodes"],
        "$system": py_arg_state["system"],
    }[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_root]
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_part in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_parts[1:-1]:
        if not isinstance(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_container, dict):
            raise KeyError(f"path parent is not a dict: {py_arg_path}")
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_container = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_container.setdefault(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_part, {})
    if not isinstance(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_container, dict):
        raise KeyError(f"path parent is not a dict: {py_arg_path}")
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_container[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__set_path__py_var_parts[-1]] = py_arg_value


def py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
    py_arg_step_id: str,
    py_arg_primitive_id: str,
    py_arg_input_path: str = "$task",
    py_arg_output_path: str = "$task",
    py_arg_state_mode: str = py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE,
    py_arg_input_bindings: dict | None = None,
    py_arg_output_storage: str = py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE,
    py_arg_max_attempts: int = py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS,
    py_arg_required: bool = True,
) -> dict:
    """Create a one-line primitive step spec.

    This is the ergonomic authoring surface. A generated Python template can be a list of these calls;
    an LLM-facing template can use the same fields as JSON without the callable object.
    """
    return {
        "step_id": py_arg_step_id,
        "primitive_id": py_arg_primitive_id,
        "input_path": py_arg_input_path,
        "output_path": py_arg_output_path,
        "state_mode": py_arg_state_mode,
        "input_bindings": dict(py_arg_input_bindings or {}),
        "output_storage": py_arg_output_storage,
        "max_attempts": int(py_arg_max_attempts),
        "required": bool(py_arg_required),
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__derive_step_id(
    py_arg_primitive_id: str,
    py_arg_occurrence: int = 1,
) -> str:
    """Derive a stable step id from a primitive id instead of requiring hand-typed labels."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_text = str(py_arg_primitive_id)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_chunks = []
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current = []
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_char in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_text:
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_char.isalnum():
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current.append(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_char.lower())
        elif py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_chunks.append("".join(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current))
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current = []
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_chunks.append("".join(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_current))
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_clean_chunks = [
        py_var_chunk
        for py_var_chunk in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_chunks
        if not (py_var_chunk.startswith("v") and py_var_chunk[1:].isdigit())
    ]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_base = "_".join(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_clean_chunks[-3:] or ["primitive"])
    if int(py_arg_occurrence) <= 1:
        return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_base
    return f"{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__derive_step_id__py_var_base}__{int(py_arg_occurrence)}"


def py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable(py_arg_callable) -> str:
    """Return an attached primitive id or derive one from a Python callable surface."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable__py_var_spec = getattr(py_arg_callable, py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_SPEC_ATTR, None)
    if isinstance(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable__py_var_spec, dict) and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable__py_var_spec.get("primitive_id"):
        return str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable__py_var_spec["primitive_id"])
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable__py_var_surface = py_function_src_teleon_synthesis_pipeline_templates__callable_surface(py_arg_callable)
    return f"python:{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable__py_var_surface['surface_id']}"


def py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract(py_arg_callable) -> dict:
    """Infer a lightweight contract from callable parameters and return annotation."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_signature = inspect.signature(py_arg_callable)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_inputs = {}
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_name, py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_parameter in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_signature.parameters.items():
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_inputs[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_name] = {
            "type": py_function_src_teleon_synthesis_pipeline_templates__annotation_name(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_parameter.annotation),
            "required": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_parameter.default is inspect.Signature.empty,
            "kind": str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_parameter.kind),
        }
    return {
        "inputs": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_inputs,
        "output": {
            "type": py_function_src_teleon_synthesis_pipeline_templates__annotation_name(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract__py_var_signature.return_annotation),
        },
    }


def py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable(py_arg_callable, py_arg_handle: dict | None = None) -> dict:
    """Build a candidate primitive record from the callable object itself."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle = dict(py_arg_handle or {})
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_surface = py_function_src_teleon_synthesis_pipeline_templates__callable_surface(py_arg_callable)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_contract = py_function_src_teleon_synthesis_pipeline_templates__primitive_signature_contract(py_arg_callable)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_doc = inspect.getdoc(py_arg_callable) or ""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_primitive_id = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle.get("primitive_id") or py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable(py_arg_callable))
    return {
        "schema_version": py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_RECORD_VERSION,
        "primitive_id": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_primitive_id,
        "surface": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_surface,
        "purpose": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_doc.splitlines()[0] if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_doc else py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_surface["name"].replace("_", " "),
        "input_contract": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_contract["inputs"],
        "output_contract": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_contract["output"],
        "state_mode": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle.get("state_mode", py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE),
        "input_path": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle.get("input_path", "$task"),
        "output_path": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle.get("output_path", "$task"),
        "input_bindings": dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle.get("input_bindings", {})),
        "output_storage": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable__py_var_handle.get("output_storage", py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE),
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record(py_arg_record: dict) -> dict:
    """Return a compact JSON-safe view that an LLM can plan over without source code."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record__py_var_inputs = py_arg_record.get("input_contract", {})
    return {
        "id": py_arg_record.get("primitive_id"),
        "do": py_arg_record.get("purpose"),
        "in": list(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record__py_var_inputs),
        "out": py_arg_record.get("output_contract", {}).get("type", "Any"),
        "mode": py_arg_record.get("state_mode"),
        "storage": py_arg_record.get("output_storage"),
        "truth": py_arg_record.get("serves_truth"),
    }


def py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
    py_arg_callable=None,
    py_arg_primitive_id: str | None = None,
    py_arg_state_mode: str = py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE,
    py_arg_input_path: str = "$task",
    py_arg_output_path: str = "$task",
    py_arg_input_bindings: dict | None = None,
    py_arg_output_storage: str = py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE,
    py_arg_max_attempts: int = py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS,
    py_arg_required: bool = True,
    py_arg_structure_path: str | None = None,
) -> dict:
    """Create a callable-backed primitive handle for Python authoring.

    JSON plans still use primitive ids. Python templates can use handles so the pipeline site does not
    repeat magic strings; the id is attached once or derived from the callable surface.
    """
    if py_arg_primitive_id is None:
        if py_arg_callable is None:
            raise ValueError("primitive handle requires a callable or primitive_id")
        py_arg_primitive_id = py_function_src_teleon_synthesis_pipeline_templates__primitive_id_from_callable(py_arg_callable)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle = {
        "primitive_id": str(py_arg_primitive_id),
        "callable": py_arg_callable,
        "state_mode": py_arg_state_mode,
        "input_path": py_arg_input_path,
        "output_path": py_arg_output_path,
        "input_bindings": dict(py_arg_input_bindings or {}),
        "output_storage": py_arg_output_storage,
        "max_attempts": int(py_arg_max_attempts),
        "required": bool(py_arg_required),
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }
    if py_arg_structure_path is not None:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle["structure_path"] = py_arg_structure_path
    if py_arg_callable is not None:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle["primitive_record"] = py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable(
            py_arg_callable,
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle,
        )
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle["llm_view"] = py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record(
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle["primitive_record"],
        )
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_handle__py_var_handle


def py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
    py_arg_primitive_id: str | None = None,
    py_arg_state_mode: str = py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE,
    py_arg_input_path: str = "$task",
    py_arg_output_path: str = "$task",
    py_arg_input_bindings: dict | None = None,
    py_arg_output_storage: str = py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE,
    py_arg_max_attempts: int = py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS,
    py_arg_required: bool = True,
    py_arg_structure_path: str | None = None,
):
    """Attach primitive metadata once to a callable; pipeline templates can then reference the callable."""

    def py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata__py_function_decorator(py_arg_callable):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata_py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata__py_function_decorator__py_var_handle = py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
            py_arg_callable,
            py_arg_primitive_id=py_arg_primitive_id,
            py_arg_state_mode=py_arg_state_mode,
            py_arg_input_path=py_arg_input_path,
            py_arg_output_path=py_arg_output_path,
            py_arg_input_bindings=py_arg_input_bindings,
            py_arg_output_storage=py_arg_output_storage,
            py_arg_max_attempts=py_arg_max_attempts,
            py_arg_required=py_arg_required,
            py_arg_structure_path=py_arg_structure_path,
        )
        setattr(py_arg_callable, py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_SPEC_ATTR, dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata_py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata__py_function_decorator__py_var_handle))
        return py_arg_callable

    return py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata__py_function_decorator


def py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle(py_arg_primitive) -> dict:
    """Normalize callable/string/dict primitive references into a primitive handle."""
    if callable(py_arg_primitive):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle__py_var_spec = getattr(py_arg_primitive, py_const_src_teleon_synthesis_pipeline_templates__PRIMITIVE_SPEC_ATTR, None)
        if isinstance(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle__py_var_spec, dict):
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle__py_var_handle = dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle__py_var_spec)
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle__py_var_handle["callable"] = py_arg_primitive
            return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle__py_var_handle
        return py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(py_arg_primitive)
    if isinstance(py_arg_primitive, str):
        return py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
            None,
            py_arg_primitive_id=py_arg_primitive,
        )
    if isinstance(py_arg_primitive, dict) and py_arg_primitive.get("primitive_id"):
        return py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
            py_arg_primitive.get("callable"),
            py_arg_primitive_id=str(py_arg_primitive["primitive_id"]),
            py_arg_state_mode=py_arg_primitive.get("state_mode", py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE),
            py_arg_input_path=py_arg_primitive.get("input_path", "$task"),
            py_arg_output_path=py_arg_primitive.get("output_path", "$task"),
            py_arg_input_bindings=py_arg_primitive.get("input_bindings", {}),
            py_arg_output_storage=py_arg_primitive.get("output_storage", py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE),
            py_arg_max_attempts=py_arg_primitive.get("max_attempts", py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS),
            py_arg_required=py_arg_primitive.get("required", True),
            py_arg_structure_path=py_arg_primitive.get("structure_path"),
        )
    raise TypeError(f"unsupported primitive reference: {py_arg_primitive!r}")


def py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle(
    py_arg_primitive_handle: dict,
    py_arg_step_id: str | None = None,
    py_arg_occurrence: int = 1,
    py_arg_overrides: dict | None = None,
) -> dict:
    """Create a primitive step from a handle, deriving step_id when not explicitly supplied."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle = dict(py_arg_primitive_handle)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides = dict(py_arg_overrides or {})
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_primitive_id = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("primitive_id", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle["primitive_id"]))
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_step_id = py_arg_step_id or str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("step_id") or py_function_src_teleon_synthesis_pipeline_templates__derive_step_id(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_primitive_id,
        py_arg_occurrence,
    ))
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_step = py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_step_id,
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_primitive_id,
        py_arg_input_path=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("input_path", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("input_path", "$task")),
        py_arg_output_path=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("output_path", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("output_path", "$task")),
        py_arg_state_mode=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("state_mode", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("state_mode", py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE)),
        py_arg_input_bindings=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("input_bindings", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("input_bindings", {})),
        py_arg_output_storage=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("output_storage", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("output_storage", py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_INLINE)),
        py_arg_max_attempts=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("max_attempts", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("max_attempts", py_const_src_teleon_synthesis_pipeline_templates__DEFAULT_MAX_ATTEMPTS)),
        py_arg_required=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("required", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("required", True)),
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_structure_path = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_overrides.get("structure_path", py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_handle.get("structure_path"))
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_structure_path is not None:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_step["structure_path"] = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_structure_path)
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle__py_var_step


def py_function_src_teleon_synthesis_pipeline_templates__is_primitive_leaf(py_arg_value) -> bool:
    """Return whether a value is one primitive reference rather than a structural container."""
    return callable(py_arg_value) or isinstance(py_arg_value, str) or (isinstance(py_arg_value, dict) and bool(py_arg_value.get("primitive_id")))


def py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(
    py_arg_value,
    py_arg_structure_path: str = "$",
) -> list[dict]:
    """Flatten callables/handles nested in lists, tuples, dicts, matrices, or explicit objects."""
    if py_function_src_teleon_synthesis_pipeline_templates__is_primitive_leaf(py_arg_value):
        return [{
            "primitive": py_arg_value,
            "structure_path": py_arg_structure_path,
        }]
    if isinstance(py_arg_value, (list, tuple)):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_entries = []
        for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_index, py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_item in enumerate(py_arg_value):
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_entries.extend(
                py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_item,
                    f"{py_arg_structure_path}[{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_index}]",
                )
            )
        return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_entries
    if isinstance(py_arg_value, dict):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_entries = []
        for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_key, py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_item in py_arg_value.items():
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_entries.extend(
                py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_item,
                    f"{py_arg_structure_path}.{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_key}",
                )
            )
        return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_entries
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_explicit = getattr(py_arg_value, py_const_src_teleon_synthesis_pipeline_templates__PIPELINE_PRIMITIVES_ATTR, None)
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_explicit is not None:
        if callable(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_explicit):
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_explicit = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_explicit()
        return py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_explicit,
            py_arg_structure_path,
        )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_to_primitives = getattr(py_arg_value, "to_teleon_primitives", None)
    if callable(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_to_primitives):
        return py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph__py_var_to_primitives(),
            py_arg_structure_path,
        )
    raise TypeError(f"unsupported primitive object graph value at {py_arg_structure_path}: {py_arg_value!r}")


def py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph(py_arg_value) -> list[dict]:
    """Return primitive handles from an explicit object graph, preserving each structural path."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_handles = []
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_entry in py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(py_arg_value):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_handle = py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_entry["primitive"])
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_handle["structure_path"] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_entry["structure_path"]
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_handles.append(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_handle)
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph__py_var_handles


def py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives(
    py_arg_template_id: str,
    py_arg_primitives: list,
    py_arg_purpose: str,
    py_arg_state_policy: str = "single_task_object",
    py_arg_logging_policy: str = "structured_json_events",
    py_arg_storage_policy: str = "inline_until_artifact_ref_requested",
) -> dict:
    """Create a template bundle from callable handles, deriving unique step ids deterministically."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handles = [py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle(py_var_primitive) for py_var_primitive in py_arg_primitives]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_seen: dict[str, int] = {}
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_steps = []
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_callable_registry = {}
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_primitive_records = []
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_llm_views = []
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handles:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_base_step_id = py_function_src_teleon_synthesis_pipeline_templates__derive_step_id(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle["primitive_id"])
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_seen[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_base_step_id] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_seen.get(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_base_step_id, 0) + 1
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_step = py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle(
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle,
            py_arg_occurrence=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_seen[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_base_step_id],
        )
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_steps.append(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_step)
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle.get("callable") is not None:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_callable_registry[py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle["primitive_id"]] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle["callable"]
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle.get("primitive_record"):
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_primitive_records.append(dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle["primitive_record"]))
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle.get("llm_view"):
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_llm_views.append(dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handle["llm_view"]))
    return {
        "template": py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
            py_arg_template_id,
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_steps,
            py_arg_purpose,
            py_arg_state_policy=py_arg_state_policy,
            py_arg_logging_policy=py_arg_logging_policy,
            py_arg_storage_policy=py_arg_storage_policy,
        ),
        "callable_registry": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_callable_registry,
        "primitive_handles": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_handles,
        "primitive_records": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_primitive_records,
        "llm_views": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives__py_var_llm_views,
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_object_graph(
    py_arg_template_id: str,
    py_arg_object_graph,
    py_arg_purpose: str,
    py_arg_state_policy: str = "single_task_object",
    py_arg_logging_policy: str = "structured_json_events",
    py_arg_storage_policy: str = "inline_until_artifact_ref_requested",
) -> dict:
    """Create a template from primitives nested in lists, tuples, dicts, matrices, or opt-in objects."""
    return py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives(
        py_arg_template_id,
        py_function_src_teleon_synthesis_pipeline_templates__handles_from_primitive_object_graph(py_arg_object_graph),
        py_arg_purpose,
        py_arg_state_policy=py_arg_state_policy,
        py_arg_logging_policy=py_arg_logging_policy,
        py_arg_storage_policy=py_arg_storage_policy,
    )


def py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives(
    py_arg_template_id: str,
    py_arg_primitives: list,
    py_arg_purpose: str,
) -> dict:
    """Build and compile a candidate template directly from Python primitive handles."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_bundle = py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_primitives(
        py_arg_template_id,
        py_arg_primitives,
        py_arg_purpose,
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_bundle["template"],
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_bundle["callable_registry"],
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_compiled["template_bundle"] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_bundle
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives__py_var_compiled


def py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph(
    py_arg_template_id: str,
    py_arg_object_graph,
    py_arg_purpose: str,
) -> dict:
    """Build and compile a candidate template from an explicit Python object graph."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_bundle = py_function_src_teleon_synthesis_pipeline_templates__pipeline_template_from_object_graph(
        py_arg_template_id,
        py_arg_object_graph,
        py_arg_purpose,
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_bundle["template"],
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_bundle["callable_registry"],
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_compiled["template_bundle"] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_bundle
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph__py_var_compiled


def py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
    py_arg_template_id: str,
    py_arg_steps: list[dict],
    py_arg_purpose: str,
    py_arg_state_policy: str = "single_task_object",
    py_arg_logging_policy: str = "structured_json_events",
    py_arg_storage_policy: str = "inline_until_artifact_ref_requested",
) -> dict:
    """Create a serializable candidate pipeline template from one-line step specs."""
    return {
        "template_id": py_arg_template_id,
        "version": py_const_src_teleon_synthesis_pipeline_templates__TEMPLATE_VERSION,
        "purpose": py_arg_purpose,
        "state_policy": py_arg_state_policy,
        "logging_policy": py_arg_logging_policy,
        "storage_policy": py_arg_storage_policy,
        "steps": list(py_arg_steps),
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
    py_arg_template: dict,
    py_arg_callable_registry: dict,
) -> dict:
    """Resolve primitive ids to callables and return a deterministic compiled candidate template."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors = []
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_compiled_steps = []
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_seen_steps = set()
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step in py_arg_template.get("steps", []):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("step_id", ""))
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_primitive_id = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("primitive_id", ""))
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_state_mode = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("state_mode", ""))
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_output_storage = str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("output_storage", ""))
        if not py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append("step missing step_id")
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_seen_steps:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append(f"duplicate step_id {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id}")
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_seen_steps.add(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id)
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_primitive_id not in py_arg_callable_registry:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append(f"primitive not in callable registry: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_primitive_id}")
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_state_mode not in py_const_src_teleon_synthesis_pipeline_templates__ALLOWED_STATE_MODES:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append(f"unsupported state_mode for {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id}: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_state_mode}")
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_output_storage not in py_const_src_teleon_synthesis_pipeline_templates__ALLOWED_OUTPUT_STORAGE:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append(f"unsupported output_storage for {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id}: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_output_storage}")
        for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_path in [str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("input_path", "$task")), str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("output_path", "$task"))]:
            if not py_function_src_teleon_synthesis_pipeline_templates__path_is_allowed(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_path):
                py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append(f"unsupported state path for {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id}: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_path}")
        for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_binding_path in (py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step.get("input_bindings") or {}).values():
            if not py_function_src_teleon_synthesis_pipeline_templates__path_is_allowed(str(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_binding_path)):
                py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors.append(f"unsupported input binding for {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step_id}: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_binding_path}")
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_compiled_steps.append({
            "step": dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_step),
            "callable": py_arg_callable_registry.get(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_primitive_id),
            "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
        })
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_template_digest = py_function_src_teleon_synthesis_pipeline_templates__stable_digest({
        "template_id": py_arg_template.get("template_id"),
        "version": py_arg_template.get("version"),
        "steps": py_arg_template.get("steps", []),
    })
    return {
        "ok": not py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors,
        "errors": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors,
        "template": deepcopy(py_arg_template),
        "compiled_steps": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_compiled_steps if not py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_errors else [],
        "template_digest": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template__py_var_template_digest,
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state(
    py_arg_task,
    py_arg_context: dict | None = None,
    py_arg_system: dict | None = None,
    py_arg_run_id: str | None = None,
) -> dict:
    """Return the standard runtime state object shared across primitive steps."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state__py_var_task = deepcopy(py_arg_task)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state__py_var_run_id = py_arg_run_id or "run_" + py_function_src_teleon_synthesis_pipeline_templates__stable_digest(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state__py_var_task)[:16]
    return {
        "run_id": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state__py_var_run_id,
        "task": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state__py_var_task,
        "context": dict(py_arg_context or {}),
        "system": dict(py_arg_system or {}),
        "nodes": {},
        "artifacts": {},
        "events": [],
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref(
    py_arg_state: dict,
    py_arg_step_id: str,
    py_arg_value,
) -> dict:
    """Store a value in the state artifact table and return a small digest reference."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_digest = py_function_src_teleon_synthesis_pipeline_templates__stable_digest(py_arg_value)
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_artifact_id = f"artifact_{py_arg_step_id}_{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_digest[:16]}"
    py_arg_state["artifacts"][py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_artifact_id] = {
        "artifact_id": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_artifact_id,
        "step_id": py_arg_step_id,
        "sha256": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_digest,
        "value": py_arg_value,
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }
    return {
        "artifact_ref": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_artifact_id,
        "sha256": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref__py_var_digest,
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates__call_step(py_arg_callable, py_arg_step: dict, py_arg_state: dict):
    """Call one primitive according to its state passing mode."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_state_mode = py_arg_step["state_mode"]
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_state_mode == py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_VALUE:
        return py_arg_callable(py_function_src_teleon_synthesis_pipeline_templates__get_path(py_arg_state, py_arg_step["input_path"]))
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_state_mode == py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH:
        return py_arg_callable(py_function_src_teleon_synthesis_pipeline_templates__get_path(py_arg_state, py_arg_step["input_path"]))
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_state_mode == py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_NAMED_INPUTS:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_kwargs = {
            py_var_name: py_function_src_teleon_synthesis_pipeline_templates__get_path(py_arg_state, str(py_var_path))
            for py_var_name, py_var_path in (py_arg_step.get("input_bindings") or {}).items()
        }
        return py_arg_callable(**py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_kwargs)
    raise ValueError(f"unsupported state_mode: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__call_step__py_var_state_mode}")


def py_function_src_teleon_synthesis_pipeline_templates__apply_step_output(
    py_arg_state: dict,
    py_arg_step: dict,
    py_arg_output,
) -> object:
    """Apply a primitive output to task/context/nodes and return the stored output value."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_step_id = py_arg_step["step_id"]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_state_mode = py_arg_step["state_mode"]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_stored_output = py_arg_output
    if py_arg_step["output_storage"] == py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_ARTIFACT_REF:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_stored_output = py_function_src_teleon_synthesis_pipeline_templates__store_artifact_ref(
            py_arg_state,
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_step_id,
            py_arg_output,
        )
    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_state_mode == py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH:
        if not isinstance(py_arg_output, dict):
            raise TypeError(f"task_patch step must return dict: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_step_id}")
        py_arg_state["task"].update(py_arg_output)
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_stored_output = py_arg_output
    elif py_arg_step["output_path"] == "$task":
        py_arg_state["task"] = py_arg_output
    else:
        py_function_src_teleon_synthesis_pipeline_templates__set_path(py_arg_state, py_arg_step["output_path"], py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_stored_output)
    py_arg_state["nodes"].setdefault(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_step_id, {})
    py_arg_state["nodes"][py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_step_id]["output"] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_stored_output
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__apply_step_output__py_var_stored_output


def py_function_src_teleon_synthesis_pipeline_templates__append_event(
    py_arg_state: dict,
    py_arg_step: dict,
    py_arg_attempt: int,
    py_arg_status: str,
    py_arg_input_digest: str,
    py_arg_output=None,
    py_arg_error: str | None = None,
) -> dict:
    """Append one structured JSON-safe runtime event."""
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__append_event__py_var_event = {
        "event": "primitive_step",
        "event_index": len(py_arg_state["events"]),
        "run_id": py_arg_state["run_id"],
        "step_id": py_arg_step["step_id"],
        "primitive_id": py_arg_step["primitive_id"],
        "attempt": py_arg_attempt,
        "status": py_arg_status,
        "input_digest": py_arg_input_digest,
        "output_digest": None if py_arg_output is None else py_function_src_teleon_synthesis_pipeline_templates__stable_digest(py_arg_output),
        "error": py_arg_error,
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }
    py_arg_state["events"].append(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__append_event__py_var_event)
    return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__append_event__py_var_event


def py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
    py_arg_compiled_template: dict,
    py_arg_task,
    py_arg_context: dict | None = None,
    py_arg_system: dict | None = None,
    py_arg_run_id: str | None = None,
) -> dict:
    """Execute a compiled template with bounded retries and structured candidate logs."""
    if not py_arg_compiled_template.get("ok"):
        return {
            "ok": False,
            "errors": list(py_arg_compiled_template.get("errors", [])),
            "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
        }
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state = py_function_src_teleon_synthesis_pipeline_templates__new_pipeline_state(
        py_arg_task,
        py_arg_context=py_arg_context,
        py_arg_system=py_arg_system,
        py_arg_run_id=py_arg_run_id,
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_errors = []
    for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_compiled_step in py_arg_compiled_template["compiled_steps"]:
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_compiled_step["step"]
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_callable = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_compiled_step["callable"]
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_input_digest = py_function_src_teleon_synthesis_pipeline_templates__stable_digest({
            "input_path": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step.get("input_path"),
            "input_bindings": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step.get("input_bindings", {}),
            "task": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state["task"],
            "context": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state["context"],
            "nodes": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state["nodes"],
        })
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step_ok = False
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_last_error = None
        for py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_attempt in range(1, max(1, int(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step.get("max_attempts", 1))) + 1):
            try:
                py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_output = py_function_src_teleon_synthesis_pipeline_templates__call_step(
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_callable,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state,
                )
                py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_stored_output = py_function_src_teleon_synthesis_pipeline_templates__apply_step_output(
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_output,
                )
                py_function_src_teleon_synthesis_pipeline_templates__append_event(
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_attempt,
                    "ok",
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_input_digest,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_stored_output,
                )
                py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step_ok = True
                break
            except Exception as py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_exc:  # noqa: BLE001
                py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_last_error = f"{type(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_exc).__name__}: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_exc}"
                py_function_src_teleon_synthesis_pipeline_templates__append_event(
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step,
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_attempt,
                    "error",
                    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_input_digest,
                    py_arg_error=py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_last_error,
                )
        if not py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step_ok:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_errors.append(f"{py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step['step_id']}: {py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_last_error}")
            if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_step.get("required", True):
                break
    return {
        "ok": not py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_errors,
        "errors": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_errors,
        "state": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state,
        "task": py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state["task"],
        "events": list(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state["events"]),
        "artifacts": dict(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template__py_var_state["artifacts"]),
        "serves_truth": py_const_src_teleon_synthesis_pipeline_templates__SERVES_TRUTH,
    }


def py_function_src_teleon_synthesis_pipeline_templates___self_test() -> int:
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_failures = []

    def py_function_src_teleon_synthesis_pipeline_templates___self_test__check(py_arg_name, py_arg_ok):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}")
        if not py_arg_ok:
            py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_failures.append(py_arg_name)

    def py_function_src_teleon_synthesis_pipeline_templates___self_test__add_random_emphasis(py_arg_task):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test_py_function_src_teleon_synthesis_pipeline_templates__self_test__add_random_emphasis__py_var_next = dict(py_arg_task)
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test_py_function_src_teleon_synthesis_pipeline_templates__self_test__add_random_emphasis__py_var_next["prompt"] = py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test_py_function_src_teleon_synthesis_pipeline_templates__self_test__add_random_emphasis__py_var_next["prompt"] + " vivid"
        return py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test_py_function_src_teleon_synthesis_pipeline_templates__self_test__add_random_emphasis__py_var_next

    def py_function_src_teleon_synthesis_pipeline_templates___self_test__standardize_colors(py_arg_task):
        return {"prompt": py_arg_task["prompt"].replace("blu", "blue")}

    def py_function_src_teleon_synthesis_pipeline_templates___self_test__make_caption(py_arg_prompt):
        return {"caption": py_arg_prompt.title()}

    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_steps = [
        py_function_src_teleon_synthesis_pipeline_templates__primitive_step("emphasis", "prompt.add_emphasis"),
        py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
            "colors",
            "prompt.standardize_colors",
            py_arg_state_mode=py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
        ),
        py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
            "caption",
            "caption.from_prompt",
            py_arg_state_mode=py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_NAMED_INPUTS,
            py_arg_input_bindings={"py_arg_prompt": "$task.prompt"},
            py_arg_output_path="$task.caption_result",
            py_arg_output_storage=py_const_src_teleon_synthesis_pipeline_templates__OUTPUT_STORAGE_ARTIFACT_REF,
        ),
    ]
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_template = py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
        "prompt_pipeline",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_steps,
        "Prompt cleanup expressed as one line per primitive.",
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_registry = {
        "prompt.add_emphasis": py_function_src_teleon_synthesis_pipeline_templates___self_test__add_random_emphasis,
        "prompt.standardize_colors": py_function_src_teleon_synthesis_pipeline_templates___self_test__standardize_colors,
        "caption.from_prompt": py_function_src_teleon_synthesis_pipeline_templates___self_test__make_caption,
    }
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_template,
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_registry,
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result = py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_compiled,
        {"record_id": "task_1", "prompt": "blu flower"},
        py_arg_run_id="run_test",
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "one-line primitive steps compile from a callable registry",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_compiled["ok"] and len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_compiled["compiled_steps"]) == 3,
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "task_value and task_patch modes update the shared task object",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result["ok"] and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result["task"]["prompt"] == "blue flower vivid",
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "named_inputs can write an artifact ref instead of inlining large output",
        "artifact_ref" in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result["task"]["caption_result"] and len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result["artifacts"]) == 1,
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "runtime emits one JSON-safe candidate event per successful step",
        len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result["events"]) == 3 and all(py_var_event["serves_truth"] is False for py_var_event in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_result["events"]),
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_bad_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
            "bad",
            [py_function_src_teleon_synthesis_pipeline_templates__primitive_step("missing", "missing.primitive")],
            "bad template",
        ),
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_registry,
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "compiler rejects primitive ids outside the deterministic registry",
        not py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_bad_compiled["ok"] and "missing.primitive" in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_bad_compiled["errors"][0],
    )

    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_attempt_counter = {"count": 0}

    def py_function_src_teleon_synthesis_pipeline_templates___self_test__flaky(py_arg_task):
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_attempt_counter["count"] += 1
        if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_attempt_counter["count"] == 1:
            raise RuntimeError("first failure")
        return py_arg_task

    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_template = py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
        "retry",
        [py_function_src_teleon_synthesis_pipeline_templates__primitive_step("flaky", "test.flaky", py_arg_max_attempts=2)],
        "bounded retry template",
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_template,
        {"test.flaky": py_function_src_teleon_synthesis_pipeline_templates___self_test__flaky},
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_result = py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_compiled,
        {"record_id": "retry"},
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "bounded retry records failed attempt then success",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_result["ok"]
        and [py_var_event["status"] for py_var_event in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_retry_result["events"]] == ["error", "ok"],
    )

    @py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
        py_arg_state_mode=py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
    )
    def py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_callable_prompt_patch(py_arg_task):
        return {"prompt": py_arg_task["prompt"] + " callable"}

    @py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
        py_arg_state_mode=py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_NAMED_INPUTS,
        py_arg_input_bindings={"py_arg_prompt": "$task.prompt"},
        py_arg_output_path="$task.summary",
    )
    def py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_callable_summary(py_arg_prompt):
        return {"summary": py_arg_prompt.upper()}

    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives(
        "callable_handle_pipeline",
        [
            py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_callable_prompt_patch,
            py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_callable_summary,
            py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_callable_summary,
        ],
        "Pipeline built from callable handles instead of magic step strings.",
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_result = py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_compiled,
        {"record_id": "callable", "prompt": "seed"},
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_step_ids = [
        py_var_compiled_step["step"]["step_id"]
        for py_var_compiled_step in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_compiled["compiled_steps"]
    ]
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "callable handles compile without hand-typed primitive ids at the pipeline site",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_compiled["ok"]
        and all(py_var_step_id for py_var_step_id in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_step_ids),
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "derived duplicate step ids are deterministic and collision-safe",
        len(set(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_step_ids)) == 3
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_step_ids[-1].endswith("__2"),
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "callable-handle pipeline runs through the same task/named-input runtime",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_result["ok"]
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_result["task"]["prompt"] == "seed callable"
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_callable_result["task"]["summary"]["summary"] == "SEED CALLABLE",
    )

    @py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
        py_arg_state_mode=py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
    )
    def py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_annotated_patch(py_arg_task: dict) -> dict:
        """Append a deterministic marker to the task."""
        return {"marker": py_arg_task.get("marker", "") + "x"}

    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record = py_function_src_teleon_synthesis_pipeline_templates__primitive_record_from_callable(
        py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_annotated_patch,
        py_function_src_teleon_synthesis_pipeline_templates__coerce_primitive_handle(py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_annotated_patch),
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_view = py_function_src_teleon_synthesis_pipeline_templates__compact_llm_view_from_primitive_record(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record,
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "callable introspection creates candidate primitive records from names, annotations, and docstrings",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record["serves_truth"] is False
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record["input_contract"]["py_arg_task"]["type"] == "dict"
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record["output_contract"]["type"] == "dict"
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record["purpose"] == "Append a deterministic marker to the task.",
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "primitive records produce compact LLM views without source code",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_view["id"] == py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_record["primitive_id"]
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_view["in"] == ["py_arg_task"]
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_view["truth"] is False,
    )

    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_compiled = py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph(
        "object_graph_pipeline",
        {
            "phase": [
                py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_annotated_patch,
                [
                    py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_annotated_patch,
                    py_function_src_teleon_synthesis_pipeline_templates___self_test__py_function_annotated_patch,
                ],
            ],
        },
        "Pipeline built from primitives nested in a Python object graph.",
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_result = py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_compiled,
        {"record_id": "object_graph", "marker": ""},
    )
    py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_paths = [
        py_var_compiled_step["step"].get("structure_path")
        for py_var_compiled_step in py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_compiled["compiled_steps"]
    ]
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "nested lists, dicts, and matrices flatten into deterministic one-line steps",
        py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_compiled["ok"]
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_paths == ["$.phase[0]", "$.phase[1][0]", "$.phase[1][1]"]
        and py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_result["task"]["marker"] == "xxx",
    )
    py_function_src_teleon_synthesis_pipeline_templates___self_test__check(
        "object-graph templates carry generated primitive records and LLM views",
        len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_compiled["template_bundle"]["primitive_records"]) == 3
        and len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_object_graph_compiled["template_bundle"]["llm_views"]) == 3,
    )

    if py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_failures:
        print(f"FAIL - pipeline_templates: {len(py_local_src_teleon_synthesis_pipeline_templates__py_function_src_teleon_synthesis_pipeline_templates__self_test__py_var_failures)} failure(s)")
        return 1
    print("PASS - pipeline_templates: one-line primitive templates compile/run with task state, JSON events, retries, and artifact refs")
    return 0


if __name__ == "__main__":
    raise SystemExit(py_function_src_teleon_synthesis_pipeline_templates___self_test())
