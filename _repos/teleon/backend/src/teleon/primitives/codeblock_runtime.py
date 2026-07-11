"""Candidate primitive codeblock runtime.

This module is the shared execution surface for generated primitive codeblocks.
The generated blocks are intentionally small: each one carries a compact spec
and calls :func:`execute_primitive_codeblock`.

The runtime does not execute external side effects. It validates the invocation
shape and emits a receipt that preserves the primitive contract, problem /
solution core, effects, proof gaps, and promotion blockers. That makes the
codeblocks reusable as candidate scaffolds while keeping promoted-truth status
separate from generated artifacts.
"""
from __future__ import annotations

from src.teleon.experiments.ids import sha256_hex
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping


RECEIPT_HASH_CHARS = 24
UNKNOWN_EDGE = "UnknownEdge"
DEFAULT_STATUS = "candidate_receipt_emitted"


JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class PrimitiveCodeblockSpec:
    """Compact generated primitive contract used by candidate codeblocks."""

    primitive_id: str
    title: str
    input_edge: str
    output_edge: str
    family: str = ""
    industry: str = ""
    region: str = ""
    runtime_targets: tuple[str, ...] = ()
    effects: tuple[str, ...] = ()
    proof_requirements: tuple[str, ...] = ()
    promotion_blockers: tuple[str, ...] = ()
    mutators: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    problem_solution_core: Mapping[str, Any] = field(default_factory=dict)
    candidate: bool = True
    serves_truth: bool = False


@dataclass(frozen=True, slots=True)
class PrimitiveExecutionReceipt:
    """Receipt returned by a candidate primitive codeblock invocation."""

    ok: bool
    status: str
    primitive_id: str
    title: str
    input_edge: str
    output_edge: str
    payload_key_count: int
    payload_fingerprint: str
    policy_fingerprint: str
    context_fingerprint: str
    runtime_targets: tuple[str, ...]
    effects_declared: tuple[str, ...]
    proof_requirements_remaining: tuple[str, ...]
    promotion_blockers: tuple[str, ...]
    problem_solution_core: Mapping[str, Any]
    candidate: bool
    serves_truth: bool
    receipt_hash: str
    emitted_at: str
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _stable_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    except TypeError:
        return json.dumps(str(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any, chars: int = RECEIPT_HASH_CHARS) -> str:
    return sha256_hex(_stable_json(value))[:chars]


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return tuple(f"{k}:{v}" for k, v in sorted(value.items()) if str(k) or str(v))
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                if item:
                    out.append(item)
            elif isinstance(item, Mapping):
                if "effect" in item and "target" in item:
                    out.append(f"{item.get('effect')}->{item.get('target')}")
                elif "url" in item:
                    out.append(str(item.get("url")))
                elif "label" in item:
                    out.append(str(item.get("label")))
                else:
                    out.append(_stable_json(item))
            elif item is not None:
                out.append(str(item))
        return tuple(out)
    return (str(value),)


def _problem_solution_core(row: Mapping[str, Any]) -> dict[str, Any]:
    contract = row.get("contract") if isinstance(row.get("contract"), Mapping) else {}
    edge_contract = row.get("edge_contract") if isinstance(row.get("edge_contract"), Mapping) else {}
    return {
        "problem": contract.get("problem", ""),
        "solution_summary": contract.get("summary") or row.get("blackbox", ""),
        "fit_when": contract.get("fit_when", ""),
        "avoid_when": contract.get("avoid_when", ""),
        "preconditions": edge_contract.get("preconditions", ""),
        "postconditions": edge_contract.get("postconditions", ""),
        "failure_modes": edge_contract.get("failure_modes") or contract.get("errors", ""),
        "input_edge_description": edge_contract.get("input_edge_description", ""),
        "output_edge_description": edge_contract.get("output_edge_description", ""),
        "composition_notes": edge_contract.get("composition_notes", ""),
        "human_action_core": row.get("human_action_core", {}),
        "rank_features": row.get("rank_features", {}),
    }


def spec_from_candidate(row: Mapping[str, Any]) -> PrimitiveCodeblockSpec:
    """Create a candidate codeblock spec from a verified primitive row."""

    return PrimitiveCodeblockSpec(
        primitive_id=str(row.get("primitive_id") or row.get("id") or "primitive_candidate"),
        title=str(row.get("title") or row.get("primitive_id") or "Primitive candidate"),
        input_edge=str(row.get("input_edge") or UNKNOWN_EDGE),
        output_edge=str(row.get("output_edge") or UNKNOWN_EDGE),
        family=str(row.get("family") or ""),
        industry=str(row.get("industry") or ""),
        region=str(row.get("region") or ""),
        runtime_targets=_tuple_of_strings(row.get("runtime_targets")),
        effects=_tuple_of_strings(row.get("effects")),
        proof_requirements=_tuple_of_strings(row.get("proof_requirements")),
        promotion_blockers=_tuple_of_strings(row.get("promotion_blockers")),
        mutators=_tuple_of_strings(row.get("mutators")),
        source_refs=_tuple_of_strings(row.get("source_refs")),
        problem_solution_core=_problem_solution_core(row),
        candidate=bool(row.get("candidate", True)),
        serves_truth=bool(row.get("serves_truth", False)),
    )


def coerce_spec(spec: PrimitiveCodeblockSpec | Mapping[str, Any]) -> PrimitiveCodeblockSpec:
    if isinstance(spec, PrimitiveCodeblockSpec):
        return spec
    return PrimitiveCodeblockSpec(
        primitive_id=str(spec.get("primitive_id") or "primitive_candidate"),
        title=str(spec.get("title") or spec.get("primitive_id") or "Primitive candidate"),
        input_edge=str(spec.get("input_edge") or UNKNOWN_EDGE),
        output_edge=str(spec.get("output_edge") or UNKNOWN_EDGE),
        family=str(spec.get("family") or ""),
        industry=str(spec.get("industry") or ""),
        region=str(spec.get("region") or ""),
        runtime_targets=_tuple_of_strings(spec.get("runtime_targets")),
        effects=_tuple_of_strings(spec.get("effects")),
        proof_requirements=_tuple_of_strings(spec.get("proof_requirements")),
        promotion_blockers=_tuple_of_strings(spec.get("promotion_blockers")),
        mutators=_tuple_of_strings(spec.get("mutators")),
        source_refs=_tuple_of_strings(spec.get("source_refs")),
        problem_solution_core=dict(spec.get("problem_solution_core") or {}),
        candidate=bool(spec.get("candidate", True)),
        serves_truth=bool(spec.get("serves_truth", False)),
    )


def execute_primitive_codeblock(
    spec: PrimitiveCodeblockSpec | Mapping[str, Any],
    payload: Mapping[str, Any] | None,
    *,
    policy: Mapping[str, Any] | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one candidate invocation and emit a deterministic receipt.

    This is intentionally a receipt-level execution. External effects declared
    in the primitive are recorded, not performed.
    """

    s = coerce_spec(spec)
    errors: list[str] = []
    if payload is None:
        payload_map: Mapping[str, Any] = {}
    elif isinstance(payload, Mapping):
        payload_map = payload
    else:
        payload_map = {}
        errors.append("payload_must_be_mapping")
    policy_map = policy if isinstance(policy, Mapping) else {}
    context_map = context if isinstance(context, Mapping) else {}

    payload_fingerprint = _digest(payload_map)
    policy_fingerprint = _digest(policy_map)
    context_fingerprint = _digest(context_map)
    receipt_seed = {
        "primitive_id": s.primitive_id,
        "input_edge": s.input_edge,
        "output_edge": s.output_edge,
        "payload": payload_fingerprint,
        "policy": policy_fingerprint,
        "context": context_fingerprint,
        "candidate": s.candidate,
        "serves_truth": False,
        "errors": errors,
    }
    receipt = PrimitiveExecutionReceipt(
        ok=not errors,
        status=DEFAULT_STATUS if not errors else "candidate_receipt_rejected",
        primitive_id=s.primitive_id,
        title=s.title,
        input_edge=s.input_edge,
        output_edge=s.output_edge,
        payload_key_count=len(payload_map),
        payload_fingerprint=payload_fingerprint,
        policy_fingerprint=policy_fingerprint,
        context_fingerprint=context_fingerprint,
        runtime_targets=s.runtime_targets,
        effects_declared=s.effects,
        proof_requirements_remaining=s.proof_requirements,
        promotion_blockers=s.promotion_blockers,
        problem_solution_core=s.problem_solution_core,
        candidate=s.candidate,
        serves_truth=False,
        receipt_hash=_digest(receipt_seed),
        emitted_at=_utc_now(),
        errors=tuple(errors),
    )
    return receipt.to_dict()


__all__ = [
    "PrimitiveCodeblockSpec",
    "PrimitiveExecutionReceipt",
    "coerce_spec",
    "execute_primitive_codeblock",
    "spec_from_candidate",
]
