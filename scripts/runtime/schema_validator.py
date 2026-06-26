#!/usr/bin/env python3
"""scripts.runtime.schema_validator — minimal, stdlib-only JSON-Schema validator for the contract layer.

No `jsonschema` dependency (Python 3.14, no pip). Supports exactly what the envelope/artifact schemas need:
``type`` (object/array/string/integer/number/boolean/null), ``required``, ``properties`` (recursive),
``enum``, ``additionalProperties`` (bool), ``items``, plus the small CROSS-FIELD set needed to make a
decision's label match its own gate booleans: ``const`` (instance must equal a fixed value), ``allOf`` (a
list of subschemas that ALL must hold), and ``if``/``then``/``else`` (when the instance matches ``if``,
``then`` must also hold; otherwise ``else``). The HARD RULE: no command, event, artifact, processor result,
API response, or durable queue payload is accepted unless it validates against a versioned schema — a
failure becomes an ErrorEnvelope (``error_type="schema_validation_failed"``, permanent).
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
SCHEMA_DIR = _REPO / "schemas"
_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float),
          "boolean": bool, "null": type(None)}
_cache: dict[str, dict] = {}


def load_schema(ref: str) -> dict:
    """ref like 'envelopes/CommandEnvelope' or 'artifacts/AtomicFact'."""
    if ref in _cache:
        return _cache[ref]
    path = SCHEMA_DIR / f"{ref}.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    _cache[ref] = schema
    return schema


def _check_type(value, t: str, path: str, errs: list) -> bool:
    if t not in _TYPES:
        return True
    if t == "integer" and isinstance(value, bool):  # bool is an int subclass — disallow as integer
        errs.append(f"{path}: expected integer, got boolean"); return False
    if t == "number" and isinstance(value, bool):
        errs.append(f"{path}: expected number, got boolean"); return False
    if not isinstance(value, _TYPES[t]):
        errs.append(f"{path}: expected {t}, got {type(value).__name__}"); return False
    return True


def validate(instance, schema: dict, *, path: str = "$") -> list[str]:
    errs: list[str] = []
    t = schema.get("type")
    if t and not _check_type(instance, t, path, errs):
        return errs
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in enum {schema['enum']}")
    if "const" in schema and instance != schema["const"]:
        errs.append(f"{path}: {instance!r} != const {schema['const']!r}")
    # object constraints apply when the instance is a dict AND the schema declares object semantics — either
    # type:object OR object-ish keywords (so an if/then subschema with only `properties`, no declared type,
    # still constrains its named fields). Behavior for existing type:object schemas is unchanged.
    _object_schema = t == "object" or any(k in schema for k in ("properties", "required", "additionalProperties"))
    if _object_schema and isinstance(instance, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in instance:
                errs.append(f"{path}: missing required '{req}'")
        if schema.get("additionalProperties") is False:
            for k in instance:
                if k not in props:
                    errs.append(f"{path}: additional property '{k}' not allowed")
        for k, sub in props.items():
            if k in instance:
                errs.extend(validate(instance[k], sub, path=f"{path}.{k}"))
    if t == "array" and isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            errs.extend(validate(item, schema["items"], path=f"{path}[{i}]"))
    # ── cross-field composition (used to bind a decision's label to its own gate booleans) ──
    for i, sub in enumerate(schema.get("allOf", [])):
        errs.extend(validate(instance, sub, path=f"{path}/allOf[{i}]"))
    if "if" in schema:
        # `if` matches iff the instance validates against it with NO errors; then `then` (or `else`) applies.
        if not validate(instance, schema["if"], path=f"{path}/if"):
            if "then" in schema:
                errs.extend(validate(instance, schema["then"], path=f"{path}/then"))
        elif "else" in schema:
            errs.extend(validate(instance, schema["else"], path=f"{path}/else"))
    return errs


def validate_ref(instance, ref: str) -> list[str]:
    return validate(instance, load_schema(ref))


def is_valid(instance, ref: str) -> bool:
    return not validate_ref(instance, ref)
