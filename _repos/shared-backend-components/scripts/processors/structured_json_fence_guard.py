#!/usr/bin/env python3
"""Backs `processor/structured-json-fence-guard` (process_kind ``coerce.json_repair``).

Force the model to wrap structured output in a ```json fence — by emitting
the prompt prefix/suffix to inject — then SAFELY extract and validate the
fenced block from the raw reply. Prevents the classic failure where prose
sanitizers (markdown strippers, TTS pre-processors) eat braces and corrupt
the payload. Extraction precedence: fenced block first, then (lenient mode
only) the outermost JSON; strict mode accepts ONLY a fenced block. The
structural validator is shared with `processor/json-repair-coerce` (single
source — `scripts.processors.retrieval.json_repair_coerce`).

Contract: deterministic; side_effects=none; on_error=raise (bad arguments;
an unfenced/unparseable reply is a REPORTED failure the pipeline gates on).

Inputs raw_model_output, target_schema, prompt_prefix_injection, strict_mode
→ parsed_object, extraction_method, validation_errors, fence_found.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/structured_json_fence_guard.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.json_repair_coerce import _shape_errors  # single validator source

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: The injection pair callers add around their prompt to force the fence.
PROMPT_PREFIX_INJECTION = ("Reply with the JSON object wrapped in a ```json code fence. "
                           "No text before or after the fence.")
PROMPT_SUFFIX_INJECTION = "Remember: ```json fence only."

_FENCE_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)

METHOD_FENCE = "fenced_block"
METHOD_OUTERMOST = "outermost_json (lenient fallback)"
METHOD_NONE = "none"


def _outermost(text: str) -> str | None:
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        return None
    depth = 0
    in_str = esc = False
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
    return None


def run(*, raw_model_output: str, target_schema: dict[str, Any] | None = None,
        prompt_prefix_injection: bool = True, strict_mode: bool = False) -> dict[str, Any]:
    """Extract + validate the fenced JSON from ``raw_model_output``."""
    if not isinstance(raw_model_output, str):
        raise TypeError("raw_model_output must be str")
    if target_schema is not None and not isinstance(target_schema, dict):
        raise TypeError("target_schema must be a dict or None")
    fence = _FENCE_RE.search(raw_model_output)
    parsed: Any = None
    method = METHOD_NONE
    if fence:
        try:
            parsed = json.loads(fence.group(1))
            method = METHOD_FENCE
        except (json.JSONDecodeError, ValueError):
            parsed = None
    if parsed is None and not strict_mode:
        outer = _outermost(raw_model_output)
        if outer is not None:
            try:
                parsed = json.loads(outer)
                method = METHOD_OUTERMOST
            except (json.JSONDecodeError, ValueError):
                parsed = None
    errors: list[str] = []
    if parsed is None:
        errors.append("no parseable JSON " + ("fence (strict_mode)" if strict_mode else "found"))
    elif target_schema:
        errors = _shape_errors(parsed, target_schema)
    return {"parsed_object": parsed if not errors else (parsed if parsed is not None else None),
            "extraction_method": method,
            "validation_errors": errors,
            "fence_found": bool(fence),
            "ok": parsed is not None and not errors,
            "prompt_injection": {"prefix": PROMPT_PREFIX_INJECTION,
                                 "suffix": PROMPT_SUFFIX_INJECTION}
                                if prompt_prefix_injection else None}


def _selftest() -> None:
    schema = {"required": ["verdict"], "properties": {"verdict": {"type": "string"}}}
    # Clean fenced reply: extracted via the fence, valid, injection pair exposed.
    ok = run(raw_model_output='Sure!\n```json\n{"verdict": "pass"}\n```', target_schema=schema)
    assert ok["ok"] is True and ok["extraction_method"] == METHOD_FENCE
    assert ok["fence_found"] is True and ok["parsed_object"]["verdict"] == "pass"
    assert "```json" in ok["prompt_injection"]["prefix"]
    # The exact failure this guard exists for: a sanitizer stripped the braces
    # OUTSIDE the fence but the fenced block survives.
    survived = run(raw_model_output='verdict pass\n```json\n{"verdict": "pass"}\n```\ntrailing prose',
                   target_schema=schema)
    assert survived["ok"] is True
    # Lenient mode falls back to outermost JSON when the model forgot the fence.
    bare = run(raw_model_output='Here you go: {"verdict": "pass"} hope that helps')
    assert bare["ok"] is True and bare["extraction_method"] == METHOD_OUTERMOST
    assert bare["fence_found"] is False
    # Strict mode refuses the same unfenced reply (reported, not raised).
    strict = run(raw_model_output='{"verdict": "pass"}', strict_mode=True)
    assert strict["ok"] is False and strict["extraction_method"] == METHOD_NONE
    assert "strict_mode" in strict["validation_errors"][0]
    # Schema violations are reported with the parsed object still available.
    bad = run(raw_model_output='```json\n{"other": 1}\n```', target_schema=schema)
    assert bad["ok"] is False and any("verdict" in e for e in bad["validation_errors"])
    # No JSON at all → honest failure.
    none = run(raw_model_output="I cannot answer.")
    assert none["ok"] is False and none["parsed_object"] is None
    # Deterministic; on_error=raise.
    assert json.dumps(run(raw_model_output='```json\n{"a":1}\n```'), sort_keys=True) == \
           json.dumps(run(raw_model_output='```json\n{"a":1}\n```'), sort_keys=True)
    raised = False
    try:
        run(raw_model_output=7)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised
    print("PASS — structured_json_fence_guard: fence-first extraction (sanitizer-proof), "
          "lenient outermost fallback vs strict fence-only, shared shape validator, "
          "injection pair exposed, honest failures verified")


if __name__ == "__main__":
    _selftest()
