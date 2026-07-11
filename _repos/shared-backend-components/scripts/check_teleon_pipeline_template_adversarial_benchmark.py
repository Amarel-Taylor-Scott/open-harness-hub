#!/usr/bin/env python3
"""Adversarial benchmark for Teleon pipeline-template authoring variants.

The checker compares several ways to express the same local business workflow:
vendor invoice normalization -> validation -> risk scoring -> review packet.

The goal is not to crown one universal syntax. It measures current incumbents by
usage lane while proving that all allowed variants compile to the same deterministic
runtime shape, and that malformed/adversarial variants are rejected.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import time
from pathlib import Path

py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
import sys
if str(py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REPO))

from src.teleon.synthesis import pipeline_templates as py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime


py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__CONTRACT = (
    _resource("architecture/teleon_pipeline_template_adversarial_benchmark.json")
)
py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__TASK = {
    "invoice_id": "inv-100",
    "vendor_id": "vendor-new-77",
    "vendor_name": "  Northwind Risk Supply  ",
    "amount": "12500.50",
    "currency": "usd",
    "purchase_order": "",
}
py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS = {
    "normalize": "business.vendor_invoice.normalize",
    "validate": "business.vendor_invoice.validate_required",
    "score": "business.vendor_invoice.score_risk",
    "emit": "business.vendor_invoice.emit_review_packet",
}


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__token_proxy(py_arg_value) -> int:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__token_proxy__py_var_chars = len(py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__stable_json(py_arg_value))
    return max(1, (py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__token_proxy__py_var_chars + 3) // 4)


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest(py_arg_result: dict) -> str:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest__py_var_task = py_arg_result.get("task", {})
    return py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__stable_digest({
        "is_valid": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest__py_var_task.get("is_valid"),
        "risk_score": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest__py_var_task.get("risk_score"),
        "risk_flags": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest__py_var_task.get("risk_flags"),
        "review_packet": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest__py_var_task.get("review_packet"),
    })


@py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
    py_arg_primitive_id=py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["normalize"],
    py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
)
def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__normalize_vendor_invoice(py_arg_task: dict) -> dict:
    """Normalize a vendor invoice candidate."""
    return {
        "vendor_name": str(py_arg_task.get("vendor_name", "")).strip(),
        "amount": round(float(py_arg_task.get("amount", 0.0)), 2),
        "currency": str(py_arg_task.get("currency", "")).upper(),
        "has_purchase_order": bool(str(py_arg_task.get("purchase_order", "")).strip()),
    }


@py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
    py_arg_primitive_id=py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["validate"],
    py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
)
def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice(py_arg_task: dict) -> dict:
    """Validate required vendor invoice fields."""
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_errors = []
    for py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_field in ("invoice_id", "vendor_id", "vendor_name", "amount", "currency"):
        if py_arg_task.get(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_field) in (None, ""):
            py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_errors.append(f"missing:{py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_field}")
    return {
        "validation_errors": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_errors,
        "is_valid": not py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice__py_var_errors,
    }


@py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
    py_arg_primitive_id=py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["score"],
    py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
)
def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk(py_arg_task: dict) -> dict:
    """Score invoice review risk deterministically."""
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk__py_var_flags = []
    if float(py_arg_task.get("amount", 0.0)) >= 10000.0:
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk__py_var_flags.append("high_amount")
    if not py_arg_task.get("has_purchase_order"):
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk__py_var_flags.append("missing_purchase_order")
    if "new" in str(py_arg_task.get("vendor_id", "")).lower():
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk__py_var_flags.append("new_vendor")
    return {
        "risk_flags": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk__py_var_flags,
        "risk_score": len(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk__py_var_flags),
    }


@py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_metadata(
    py_arg_primitive_id=py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["emit"],
    py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
)
def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__emit_vendor_invoice_review_packet(py_arg_task: dict) -> dict:
    """Emit a compact invoice review packet."""
    return {
        "review_packet": {
            "invoice_id": py_arg_task["invoice_id"],
            "vendor_id": py_arg_task["vendor_id"],
            "amount": py_arg_task["amount"],
            "currency": py_arg_task["currency"],
            "is_valid": py_arg_task["is_valid"],
            "risk_score": py_arg_task["risk_score"],
            "risk_flags": list(py_arg_task["risk_flags"]),
        }
    }


py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVES = [
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__normalize_vendor_invoice,
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice,
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk,
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__emit_vendor_invoice_review_packet,
]
py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REGISTRY = {
    py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["normalize"]: py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__normalize_vendor_invoice,
    py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["validate"]: py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice,
    py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["score"]: py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk,
    py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["emit"]: py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__emit_vendor_invoice_review_packet,
}


class py_class_scripts_check_teleon_pipeline_template_adversarial_benchmark__InvoiceReviewFlow:
    """Opt-in object graph; the runtime should use this method, not crawl internals."""

    def __init__(self) -> None:
        self.py_var_private_decoy = ["do_not_crawl"]

    def to_teleon_primitives(self):
        return {
            "intake": [
                py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__normalize_vendor_invoice,
                py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice,
            ],
            "review": [
                py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk,
                py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__emit_vendor_invoice_review_packet,
            ],
        }


class py_class_scripts_check_teleon_pipeline_template_adversarial_benchmark__ArbitraryObjectWithHiddenPrimitive:
    def __init__(self) -> None:
        self.py_var_hidden = py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__normalize_vendor_invoice


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__verbose_json_steps_variant() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__verbose_json_steps_variant__py_var_steps = [
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
            "normalize_vendor_invoice",
            py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["normalize"],
            py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
        ),
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
            "validate_vendor_invoice",
            py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["validate"],
            py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
        ),
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
            "score_vendor_invoice_risk",
            py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["score"],
            py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
        ),
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
            "emit_vendor_invoice_review_packet",
            py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["emit"],
            py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
        ),
    ]
    return {
        "payload": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__verbose_json_steps_variant__py_var_steps,
        "compiled": py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
            py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
                "verbose_json_steps",
                py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__verbose_json_steps_variant__py_var_steps,
                "Verbose JSON step specs for invoice review.",
            ),
            py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REGISTRY,
        ),
        "flexibility_score": 2,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant__py_var_ids = [
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["normalize"],
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["validate"],
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["score"],
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["emit"],
    ]
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant__py_var_steps = [
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle(
            py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
                None,
                py_arg_primitive_id=py_var_id,
                py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
            )
        )
        for py_var_id in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant__py_var_ids
    ]
    return {
        "payload": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant__py_var_ids,
        "compiled": py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
            py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
                "compact_json_ids",
                py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant__py_var_steps,
                "Compact primitive-id plan delta for invoice review.",
            ),
            py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REGISTRY,
        ),
        "flexibility_score": 1,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__callable_list_variant() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__callable_list_variant__py_var_compiled = py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives(
        "callable_list",
        list(py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVES),
        "Callable list for invoice review.",
    )
    return {
        "payload": [py_var_callable.__name__ for py_var_callable in py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVES],
        "compiled": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__callable_list_variant__py_var_compiled,
        "flexibility_score": 4,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__primitive_handle_list_variant() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__primitive_handle_list_variant__py_var_handles = [
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
            py_var_callable,
            py_arg_state_mode=py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_const_src_teleon_synthesis_pipeline_templates__STATE_MODE_TASK_PATCH,
        )
        for py_var_callable in py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVES
    ]
    return {
        "payload": [
            {
                "primitive_id": py_var_handle["primitive_id"],
                "state_mode": py_var_handle["state_mode"],
            }
            for py_var_handle in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__primitive_handle_list_variant__py_var_handles
        ],
        "compiled": py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_primitives(
            "primitive_handle_list",
            py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__primitive_handle_list_variant__py_var_handles,
            "Explicit primitive handles for invoice review.",
        ),
        "flexibility_score": 5,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__object_graph_matrix_variant() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__object_graph_matrix_variant__py_var_graph = {
        "intake": [
            py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__normalize_vendor_invoice,
            py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__validate_vendor_invoice,
        ],
        "review": [
            [
                py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__score_vendor_invoice_risk,
                py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__emit_vendor_invoice_review_packet,
            ]
        ],
    }
    return {
        "payload": {"intake": ["normalize", "validate"], "review": [["score", "emit"]]},
        "compiled": py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph(
            "object_graph_matrix",
            py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__object_graph_matrix_variant__py_var_graph,
            "Object graph matrix for invoice review.",
        ),
        "flexibility_score": 6,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__opt_in_object_graph_variant() -> dict:
    return {
        "payload": {"object": "InvoiceReviewFlow.to_teleon_primitives"},
        "compiled": py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template_from_object_graph(
            "opt_in_object_graph",
            py_class_scripts_check_teleon_pipeline_template_adversarial_benchmark__InvoiceReviewFlow(),
            "Opt-in domain object graph for invoice review.",
        ),
        "flexibility_score": 7,
    }


py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__VARIANT_BUILDERS = {
    "verbose_json_steps": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__verbose_json_steps_variant,
    "compact_json_ids": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__compact_json_ids_variant,
    "callable_list": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__callable_list_variant,
    "primitive_handle_list": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__primitive_handle_list_variant,
    "object_graph_matrix": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__object_graph_matrix_variant,
    "opt_in_object_graph": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__opt_in_object_graph_variant,
}


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant(py_arg_variant_id: str, py_arg_builder) -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_variant = py_arg_builder()
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_compiled = py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_variant["compiled"]
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_start_ns = time.perf_counter_ns()
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_results = [
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__execute_compiled_pipeline_template(
            py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_compiled,
            dict(py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__TASK),
            py_arg_run_id=f"run_{py_arg_variant_id}",
        )
        for py_var_index in range(3)
    ]
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_runtime_ns = time.perf_counter_ns() - py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_start_ns
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_semantic_digests = [
        py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__semantic_digest(py_var_result)
        for py_var_result in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_results
    ]
    return {
        "variant_id": py_arg_variant_id,
        "ok": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_compiled.get("ok") and all(py_var_result.get("ok") for py_var_result in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_results),
        "errors": list(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_compiled.get("errors", [])),
        "planner_payload_token_proxy": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__token_proxy(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_variant["payload"]),
        "authoring_surface_token_proxy": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__token_proxy(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_variant["payload"]),
        "compiled_step_token_proxy": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__token_proxy(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_compiled.get("template", {}).get("steps", [])),
        "deterministic_digest_count": len(set(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_semantic_digests)),
        "semantic_output_digest": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_semantic_digests[0],
        "runtime_ns": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_runtime_ns,
        "flexibility_score": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant__py_var_variant["flexibility_score"],
        "serves_truth": False,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_unknown = py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
            "bad_unknown",
            [py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step("bad", "business.missing")],
            "unknown primitive",
        ),
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REGISTRY,
    )
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_bad_path = py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
            "bad_path",
            [
                py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step(
                    "bad_path",
                    py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__PRIMITIVE_IDS["normalize"],
                    py_arg_input_path="$env.SECRET",
                )
            ],
            "bad path",
        ),
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REGISTRY,
    )
    try:
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__flatten_primitive_object_graph(
            py_class_scripts_check_teleon_pipeline_template_adversarial_benchmark__ArbitraryObjectWithHiddenPrimitive()
        )
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_crawl_rejected = False
    except TypeError:
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_crawl_rejected = True
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_object_graph = py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__object_graph_matrix_variant()
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_import_compiled = py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__compile_pipeline_template(
        py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__pipeline_template(
            "bad_import",
            [
                py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_step_from_handle(
                    py_var_scripts_check_teleon_pipeline_template_adversarial_benchmark__runtime.py_function_src_teleon_synthesis_pipeline_templates__primitive_handle(
                        None,
                        py_arg_primitive_id="python:os.system",
                    )
                )
            ],
            "bad import surface",
        ),
        py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__REGISTRY,
    )
    return {
        "unknown_primitive_rejected": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_unknown.get("ok") is False,
        "invalid_state_path_rejected": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_bad_path.get("ok") is False,
        "arbitrary_object_crawl_rejected": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_crawl_rejected,
        "json_import_surface_rejected": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_import_compiled.get("ok") is False,
        "structure_paths_preserved": "$.review[0][1]" in [
            py_var_step["step"].get("structure_path")
            for py_var_step in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results__py_var_object_graph["compiled"].get("compiled_steps", [])
        ],
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report() -> dict:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_variants = [
        py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__evaluate_variant(py_var_variant_id, py_var_builder)
        for py_var_variant_id, py_var_builder in py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__VARIANT_BUILDERS.items()
    ]
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_by_id = {
        py_var_variant["variant_id"]: py_var_variant
        for py_var_variant in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_variants
    }
    return {
        "serves_truth": False,
        "business_problem": "vendor_invoice_review",
        "variants": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_variants,
        "best_by_lane": {
            "llm_boundary_min_tokens": min(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_variants, key=lambda py_var_variant: py_var_variant["planner_payload_token_proxy"])["variant_id"],
            "python_flexibility": max(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_variants, key=lambda py_var_variant: py_var_variant["flexibility_score"])["variant_id"],
            "compiled_runtime": "compiled_step_specs",
        },
        "adversarial": py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__adversarial_results(),
        "by_id": py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report__py_var_by_id,
    }


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test() -> int:
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_failures = []

    def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_failures.append(py_arg_name)

    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract = json.loads(py_const_scripts_check_teleon_pipeline_template_adversarial_benchmark__CONTRACT.read_text(encoding="utf-8"))
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report = py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__benchmark_report()
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract_variants = set(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract.get("variants_under_test", []))
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report_variants = set(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["by_id"])
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "contract is candidate-only and evaluates at least six variants",
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract.get("serves_truth") is False
        and len(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract_variants) >= 6
        and py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract_variants == py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report_variants,
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "contract explicitly avoids a single universal winner",
        "no single universal winner" in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract.get("default_recommendation", {}).get("law", "").lower(),
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "all allowed variants compile and execute successfully",
        all(py_var_variant["ok"] and py_var_variant["serves_truth"] is False for py_var_variant in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["variants"]),
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "all variants produce the same semantic business output",
        len({py_var_variant["semantic_output_digest"] for py_var_variant in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["variants"]}) == 1,
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "every variant is deterministic across repeated runs",
        all(py_var_variant["deterministic_digest_count"] == 1 for py_var_variant in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["variants"]),
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "compact JSON is cheaper than verbose JSON for the LLM boundary",
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["by_id"]["compact_json_ids"]["planner_payload_token_proxy"]
        < py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["by_id"]["verbose_json_steps"]["planner_payload_token_proxy"],
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "highest flexibility is an explicit Python object-graph lane",
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["best_by_lane"]["python_flexibility"] in {"object_graph_matrix", "opt_in_object_graph"},
    )
    py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_incumbents = {
        py_var_lane.get("current_incumbent")
        for py_var_lane in py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_contract.get("usage_lanes", [])
        if py_var_lane.get("current_incumbent")
    }
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "every usage-lane incumbent is evaluated",
        py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_incumbents <= py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report_variants,
        str(sorted(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_incumbents - py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report_variants)),
    )
    py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test__check(
        "adversarial malformed variants are rejected",
        all(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["adversarial"].values()),
        str(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_report["adversarial"]),
    )

    if py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_failures:
        print(f"\nFAIL - check_teleon_pipeline_template_adversarial_benchmark: {len(py_local_scripts_check_teleon_pipeline_template_adversarial_benchmark__py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__self_test__py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_teleon_pipeline_template_adversarial_benchmark: multi-variant authoring benchmark is deterministic, non-binary, and adversarially guarded")
    return 0


def py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__main() -> int:
    return py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_teleon_pipeline_template_adversarial_benchmark__main())
