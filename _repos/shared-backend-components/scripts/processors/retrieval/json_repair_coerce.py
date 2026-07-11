#!/usr/bin/env python3
"""Backs `processor/json-repair-coerce` (process_kind ``coerce.json_repair``).

The deterministic post-call recovery the typed-envelope contract relies on:
parse the model output as JSON; if malformed, apply ONE bounded repair pass
(strip code fences / prose around the outermost JSON, remove trailing
commas, balance truncated closers) and re-validate against the expected
schema shape. Every result reports exactly what was done (``recovered`` +
``repairs``) — a repaired parse is never passed off as a clean one, and an
unrepairable output is an honest failure, never a guessed object.

Contract: deterministic; side_effects=none; on_error=raise (bad arguments;
unparseable model output is a REPORTED failure, not an exception — the
pipeline gates on ``ok``).

Inputs model_output, schema → outputs json, recovered.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/retrieval/json_repair_coerce.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Repair pass names, applied in this order, each at most once (bounded — a
#: repair loop that keeps mutating is how guessed objects happen).
REPAIR_FENCE = "strip_code_fence"
REPAIR_EXTRACT = "extract_outermost_json"
REPAIR_TRAILING_COMMAS = "remove_trailing_commas"
REPAIR_BALANCE = "balance_truncated_closers"

_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _try(text: str) -> Any | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_outermost(text: str) -> str | None:
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        return None
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            esc = (ch == "\\" and not esc)
            if ch == '"' and not esc:
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]  # truncated — balancing may still rescue it


def _balance(text: str) -> str:
    stack: list[str] = []
    in_str = False
    esc = False
    for ch in text:
        if in_str:
            esc = (ch == "\\" and not esc)
            if ch == '"' and not esc:
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    fixed = text.rstrip().rstrip(",")
    if in_str:
        fixed += '"'
    return fixed + "".join(reversed(stack))


def _shape_errors(data: Any, schema: dict[str, Any]) -> list[str]:
    """Minimal structural check: required keys + primitive type names."""
    errors: list[str] = []
    for key in schema.get("required", []):
        if not isinstance(data, dict) or key not in data:
            errors.append(f"missing required key {key!r}")
    types = {"object": dict, "array": list, "string": str, "number": (int, float),
             "integer": int, "boolean": bool}
    for key, spec in (schema.get("properties") or {}).items():
        if isinstance(data, dict) and key in data and isinstance(spec, dict):
            want = types.get(spec.get("type"))
            if want and not isinstance(data[key], want):
                errors.append(f"key {key!r} should be {spec['type']}")
    return errors


def run(*, model_output: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parse-or-repair ``model_output``; validate the shape against ``schema``."""
    if not isinstance(model_output, str):
        raise TypeError(f"model_output must be str, got {type(model_output).__name__}")
    if schema is not None and not isinstance(schema, dict):
        raise TypeError("schema must be a dict or None")
    repairs: list[str] = []
    text = model_output.strip()

    data = _try(text)
    if data is None and _FENCE_RE.search(text):
        text = _FENCE_RE.sub("", text).strip()
        repairs.append(REPAIR_FENCE)
        data = _try(text)
    if data is None:
        extracted = _extract_outermost(text)
        if extracted is not None and extracted != text:
            text = extracted
            repairs.append(REPAIR_EXTRACT)
            data = _try(text)
    if data is None and _TRAILING_COMMA_RE.search(text):
        text = _TRAILING_COMMA_RE.sub(r"\1", text)
        repairs.append(REPAIR_TRAILING_COMMAS)
        data = _try(text)
    if data is None:
        balanced = _balance(text)
        if balanced != text:
            repairs.append(REPAIR_BALANCE)
            data = _try(balanced)

    if data is None:
        return {"json": None, "recovered": {
            "ok": False, "recovered": False, "repairs": repairs,
            "error": "unparseable after one bounded repair pass — refusing to guess",
            "schema_errors": []}}
    schema_errors = _shape_errors(data, schema) if schema else []
    return {"json": data, "recovered": {
        "ok": not schema_errors, "recovered": bool(repairs), "repairs": repairs,
        "error": None, "schema_errors": schema_errors}}


def _selftest() -> None:
    schema = {"required": ["verdict", "score"],
              "properties": {"verdict": {"type": "string"}, "score": {"type": "number"}}}
    # Clean JSON: ok, NOT marked recovered.
    clean = run(model_output='{"verdict": "pass", "score": 0.9}', schema=schema)
    assert clean["recovered"]["ok"] is True and clean["recovered"]["recovered"] is False
    # Fenced + prose-wrapped: repaired, and the repairs are itemized.
    messy = run(model_output='Sure! Here is the result:\n```json\n{"verdict": "pass", "score": 0.9}\n```\nLet me know!',
                schema=schema)
    assert messy["json"]["verdict"] == "pass" and messy["recovered"]["recovered"] is True
    assert REPAIR_EXTRACT in messy["recovered"]["repairs"] or REPAIR_FENCE in messy["recovered"]["repairs"]
    # Trailing comma: repaired.
    tc = run(model_output='{"verdict": "pass", "score": 1,}', schema=schema)
    assert tc["json"]["score"] == 1 and REPAIR_TRAILING_COMMAS in tc["recovered"]["repairs"]
    # Truncated output: closers balanced.
    trunc = run(model_output='{"verdict": "pass", "score": 0.5, "notes": ["a", "b"',
                schema=schema)
    assert trunc["json"] is not None and REPAIR_BALANCE in trunc["recovered"]["repairs"]
    # Schema shape errors are REPORTED, not papered over.
    bad = run(model_output='{"verdict": 7}', schema=schema)
    assert bad["recovered"]["ok"] is False
    assert any("score" in e for e in bad["recovered"]["schema_errors"])
    # Unrepairable: honest failure, json stays None, never a guessed object.
    hopeless = run(model_output="I cannot answer that question.", schema=schema)
    assert hopeless["json"] is None and hopeless["recovered"]["ok"] is False
    assert "refusing to guess" in hopeless["recovered"]["error"]
    # Deterministic; on_error=raise for bad args.
    assert json.dumps(run(model_output='{"a":1}'), sort_keys=True) == \
           json.dumps(run(model_output='{"a":1}'), sort_keys=True)
    raised = False
    try:
        run(model_output=42)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised
    print("PASS — json_repair_coerce: one bounded repair pass (fence/extract/commas/"
          "balance) with itemized repairs, schema-shape reporting, honest "
          "refuse-to-guess on unparseable output verified")


if __name__ == "__main__":
    _selftest()
