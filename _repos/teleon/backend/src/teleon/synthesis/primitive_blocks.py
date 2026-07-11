"""AI-first primitive blocks for Teleon-generated code.

Teleon writes candidate code, so the generated code must be born graphable and scalable:

* every exported object uses long, location-derived pyprefix names;
* scalar inputs can be lifted to repeatable sequence processing without rewriting business logic;
* loops are explicit, bounded, and receipt-like;
* dispatch is data/table driven instead of hidden in rigid if/elif chains;
* each block returns plain dict/list shapes so typing can be added later during optimization.

These are intentionally small primitives. Codegen should compose these before inventing bespoke loops.
serves_truth=false: generated code and primitive outputs are candidate execution artifacts until verified.
"""
from __future__ import annotations

from collections.abc import Iterable


py_const_src_teleon_synthesis_primitive_blocks__DEFAULT_MAX_ITERATIONS = 8
py_const_src_teleon_synthesis_primitive_blocks__SEQUENCE_KIND = "sequence"
py_const_src_teleon_synthesis_primitive_blocks__SCALAR_KIND = "scalar"


def py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence(
    py_arg_value,
    py_arg_none_policy="empty",
    py_arg_dict_policy="single",
):
    """Return a normalized list plus shape metadata for scalar-or-array codegen.

    Purpose: make every generated function easy to batch/loop later. Strings and dicts are treated as
    single scalar values by default because iterating their characters/keys is usually accidental.
    Inputs: any value, with explicit policies for None and dict.
    Output: {items, input_kind, count, was_none}; never serves truth.
    """
    if py_arg_value is None:
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = [] if py_arg_none_policy == "empty" else [None]
        return {
            "items": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items,
            "input_kind": "none",
            "count": len(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items),
            "was_none": True,
            "serves_truth": False,
        }
    if isinstance(py_arg_value, list):
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = list(py_arg_value)
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind = py_const_src_teleon_synthesis_primitive_blocks__SEQUENCE_KIND
    elif isinstance(py_arg_value, tuple):
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = list(py_arg_value)
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind = py_const_src_teleon_synthesis_primitive_blocks__SEQUENCE_KIND
    elif isinstance(py_arg_value, set):
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = sorted(py_arg_value, key=repr)
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind = py_const_src_teleon_synthesis_primitive_blocks__SEQUENCE_KIND
    elif isinstance(py_arg_value, dict) and py_arg_dict_policy == "items":
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = [{"key": py_var_key, "value": py_var_value} for py_var_key, py_var_value in py_arg_value.items()]
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind = py_const_src_teleon_synthesis_primitive_blocks__SEQUENCE_KIND
    elif isinstance(py_arg_value, Iterable) and not isinstance(py_arg_value, (str, bytes, bytearray, dict)):
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = list(py_arg_value)
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind = py_const_src_teleon_synthesis_primitive_blocks__SEQUENCE_KIND
    else:
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items = [py_arg_value]
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind = py_const_src_teleon_synthesis_primitive_blocks__SCALAR_KIND
    return {
        "items": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items,
        "input_kind": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_kind,
        "count": len(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence__py_var_items),
        "was_none": False,
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_blocks__wrap_candidate_result(
    py_arg_value,
    py_arg_status="ok",
    py_arg_index=None,
    py_arg_error=None,
):
    """Return a uniform candidate envelope for generated-code steps.

    Purpose: generated blocks should produce records that can be graphed, retried, filtered, and
    reviewed. The envelope is intentionally untyped dict data; strict model types can be optimized in
    after the runtime shape is proven.
    """
    return {
        "status": py_arg_status,
        "index": py_arg_index,
        "value": py_arg_value,
        "error": py_arg_error,
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_blocks__map_sequence(
    py_arg_items,
    py_arg_step_function,
    py_arg_context=None,
    py_arg_stop_on_error=False,
):
    """Apply a step function to every item and return candidate envelopes.

    Purpose: replace copy-pasted repeated calls with a loop primitive that records index, errors, and
    candidate-only status. The step may accept (item) or (item, context); both forms are supported so
    codegen can start simple and specialize later.
    """
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_normalized = py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence(py_arg_items)
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_outputs = []
    for py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_index, py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_item in enumerate(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_normalized["items"]):
        try:
            if py_arg_context is None:
                py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_result = py_arg_step_function(py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_item)
            else:
                py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_result = py_arg_step_function(
                    py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_item,
                    py_arg_context,
                )
            py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_outputs.append(py_function_src_teleon_synthesis_primitive_blocks__wrap_candidate_result(
                py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_result,
                py_arg_index=py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_index,
            ))
        except Exception as py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_exc:  # noqa: BLE001
            py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_outputs.append(py_function_src_teleon_synthesis_primitive_blocks__wrap_candidate_result(
                None,
                py_arg_status="error",
                py_arg_index=py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_index,
                py_arg_error=f"{type(py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_exc).__name__}: {py_local_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_exc}",
            ))
            if py_arg_stop_on_error:
                break
    return {
        "input": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_normalized,
        "outputs": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_outputs,
        "ok": all(py_var_row["status"] == "ok" for py_var_row in py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__map_sequence__py_var_outputs),
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_blocks__lift_scalar_step_to_sequence_step(py_arg_step_function):
    """Wrap a scalar step so callers can pass either one item or many items.

    Purpose: Teleon can generate the smallest useful scalar function first, then get batch behavior by
    composition instead of rewriting its business logic. This is the main scalar->array upgrade path.
    """
    def py_function_src_teleon_synthesis_primitive_blocks__lift_scalar_step_to_sequence_step__py_function_sequence_wrapper(
        py_arg_value,
        py_arg_context=None,
    ):
        return py_function_src_teleon_synthesis_primitive_blocks__map_sequence(
            py_arg_value,
            py_arg_step_function,
            py_arg_context=py_arg_context,
        )

    return py_function_src_teleon_synthesis_primitive_blocks__lift_scalar_step_to_sequence_step__py_function_sequence_wrapper


def py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable(
    py_arg_seed,
    py_arg_step_function,
    py_arg_is_stable_function=None,
    py_arg_max_iterations=py_const_src_teleon_synthesis_primitive_blocks__DEFAULT_MAX_ITERATIONS,
):
    """Run a bounded candidate loop until the state is stable or max_iterations is reached.

    Purpose: generated code should express iteration as a contract, not an unbounded while loop. The
    default stability check is equality with the previous state; callers can provide a richer predicate.
    """
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_history = []
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state = py_arg_seed
    for py_local_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_iteration in range(int(py_arg_max_iterations)):
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_next_state = py_arg_step_function(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state)
        if py_arg_is_stable_function is None:
            py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_stable = py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_next_state == py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state
        else:
            py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_stable = bool(py_arg_is_stable_function(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state, py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_next_state))
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_history.append({
            "iteration": py_local_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_iteration,
            "before": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state,
            "after": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_next_state,
            "stable": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_stable,
            "serves_truth": False,
        })
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state = py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_next_state
        if py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_stable:
            break
    return {
        "final": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_state,
        "iterations": len(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_history),
        "stable": bool(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_history and py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_history[-1]["stable"]),
        "history": py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable__py_var_history,
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key(
    py_arg_key,
    py_arg_dispatch_table,
    py_arg_payload=None,
    py_arg_default_key=None,
):
    """Use a dispatch table instead of a rigid if/elif branch chain.

    Purpose: generated code stays extensible: add a handler by adding a table row, not by editing branch
    logic. The handler may accept zero args or one payload arg.
    """
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_handler = py_arg_dispatch_table.get(py_arg_key)
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_selected_key = py_arg_key
    if py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_handler is None and py_arg_default_key is not None:
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_handler = py_arg_dispatch_table.get(py_arg_default_key)
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_selected_key = py_arg_default_key
    if py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_handler is None:
        return py_function_src_teleon_synthesis_primitive_blocks__wrap_candidate_result(
            None,
            py_arg_status="missing_handler",
            py_arg_error=f"no handler for {py_arg_key!r}",
        )
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_value = py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_handler() if py_arg_payload is None else py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_handler(py_arg_payload)
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_envelope = py_function_src_teleon_synthesis_primitive_blocks__wrap_candidate_result(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_value)
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_envelope["selected_key"] = py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_selected_key
    return py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key__py_var_envelope


def py_function_src_teleon_synthesis_primitive_blocks__generated_code_contract(
    py_arg_purpose,
    py_arg_input_shape="scalar_or_sequence",
    py_arg_output_shape="candidate_envelope_or_sequence",
    py_arg_uses=None,
):
    """Return a standard contract object to embed beside generated code.

    Purpose: give LLMs and deterministic checkers a concise, greppable contract before formal type
    schemas are optimized. Generated code should include this data or equivalent docstring fields.
    """
    return {
        "purpose": py_arg_purpose,
        "input_shape": py_arg_input_shape,
        "output_shape": py_arg_output_shape,
        "uses": list(py_arg_uses or []),
        "naming": "py_<kind>_<file>__<scope>__<name>",
        "typing_stage": "defer_strict_parameter_typing_until_optimization",
        "serves_truth": False,
    }


def py_function_src_teleon_synthesis_primitive_blocks___self_test():
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_failures = []

    def py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(py_arg_name, py_arg_ok):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}")
        if not py_arg_ok:
            py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_failures.append(py_arg_name)

    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_scalar = py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence("abc")
    py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(
        "strings stay scalar, not char arrays",
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_scalar["items"] == ["abc"] and py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_scalar["input_kind"] == "scalar",
    )
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_batch = py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence((3, 1, 2))
    py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(
        "tuples become repeatable sequence inputs",
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_batch["items"] == [3, 1, 2] and py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_batch["input_kind"] == "sequence",
    )

    def py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_plus_one(py_arg_value):
        return py_arg_value + 1

    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_lifted = py_function_src_teleon_synthesis_primitive_blocks__lift_scalar_step_to_sequence_step(
        py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_plus_one
    )
    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_lifted_result = py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_lifted([1, 2, 3])
    py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(
        "scalar step lifts to batch processing",
        [py_var_row["value"] for py_var_row in py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_lifted_result["outputs"]] == [2, 3, 4],
    )

    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_loop = py_function_src_teleon_synthesis_primitive_blocks__loop_until_stable(
        0,
        lambda py_arg_value: min(py_arg_value + 1, 2),
        py_arg_max_iterations=5,
    )
    py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(
        "loop primitive is bounded and records history",
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_loop["stable"] and py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_loop["final"] == 2 and len(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_loop["history"]) == 3,
    )

    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_dispatch = py_function_src_teleon_synthesis_primitive_blocks__dispatch_by_key(
        "double",
        {"double": lambda py_arg_value: py_arg_value * 2},
        4,
    )
    py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(
        "dispatch table replaces rigid branch chains",
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_dispatch["value"] == 8 and py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_dispatch["selected_key"] == "double",
    )

    py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_contract = py_function_src_teleon_synthesis_primitive_blocks__generated_code_contract(
        "normalize a generated step to scalar-or-sequence execution",
        py_arg_uses=["normalize_to_sequence", "map_sequence"],
    )
    py_function_src_teleon_synthesis_primitive_blocks___self_test__py_function_check(
        "generated-code contract carries purpose and typing stage",
        py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_contract["purpose"] and py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_contract["typing_stage"].startswith("defer"),
    )

    if py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_failures:
        print(f"FAIL - primitive_blocks: {len(py_local_src_teleon_synthesis_primitive_blocks__py_function_src_teleon_synthesis_primitive_blocks__self_test__py_var_failures)} failure(s)")
        return 1
    print("PASS - primitive_blocks: scalar-to-sequence, bounded loop, dispatch, and candidate contract primitives")
    return 0


if __name__ == "__main__":
    raise SystemExit(py_function_src_teleon_synthesis_primitive_blocks___self_test())
