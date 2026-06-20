#!/usr/bin/env python3
"""Backs `processor/template-field-gem` (process_kind ``format_convert.template_render``).

The Trove "gem" pattern: parse a prompt template containing ``{{field}}``
placeholders, resolve the fields from a user-provided context object, and
assemble the final one-shot prompt. Supports scalar substitution, dotted
paths, default values (``{{field|default}}``) and conditional blocks
(``{{#field}}...{{/field}}`` rendered only when the field is present and
truthy). ``strict_mode`` controls missing-field behavior: strict raises,
lenient leaves the report to the caller — but NEVER renders a placeholder
silently as empty text without recording it.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs template, context, strict_mode → assembled_prompt, resolved_fields,
missing_fields, conditional_fields_omitted.

CLI / self-test: python3 scripts/processors/template_field_gem.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

_FIELD_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)(?:\|([^{}]*))?\s*\}\}")
_COND_RE = re.compile(r"\{\{#\s*([a-zA-Z0-9_.]+)\s*\}\}(.*?)\{\{/\s*\1\s*\}\}", re.DOTALL)

#: What a missing field renders as in lenient mode — visible, greppable,
#: never silently blank.
LENIENT_MISSING_MARK = "[missing:{field}]"


def _lookup(context: dict[str, Any], path: str) -> tuple[bool, Any]:
    cur: Any = context
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, cur


def run(*, template: str, context: dict[str, Any],
        strict_mode: bool = True) -> dict[str, Any]:
    """Render ``template`` against ``context``."""
    if not isinstance(template, str):
        raise TypeError("template must be str")
    if not isinstance(context, dict):
        raise TypeError("context must be a dict")
    resolved: dict[str, Any] = {}
    missing: list[str] = []
    omitted_conditionals: list[str] = []

    def render_conditionals(text: str) -> str:
        def cond(m: re.Match) -> str:
            present, value = _lookup(context, m.group(1))
            if present and value:
                return m.group(2)
            omitted_conditionals.append(m.group(1))
            return ""
        prev = None
        while prev != text:                      # nested blocks resolve inner-out
            prev = text
            text = _COND_RE.sub(cond, text)
        return text

    def fill(m: re.Match) -> str:
        field, default = m.group(1), m.group(2)
        present, value = _lookup(context, field)
        if present:
            resolved[field] = value
            return str(value)
        if default is not None:
            resolved[field] = default
            return default
        missing.append(field)
        return LENIENT_MISSING_MARK.format(field=field)

    body = render_conditionals(template)
    assembled = _FIELD_RE.sub(fill, body)
    if strict_mode and missing:
        raise ValueError(f"strict_mode: unresolved template fields {sorted(set(missing))}")
    return {"assembled_prompt": assembled,
            "resolved_fields": resolved,
            "missing_fields": sorted(set(missing)),
            "conditional_fields_omitted": sorted(set(omitted_conditionals))}


def _selftest() -> None:
    template = ("Translate the bulletin for {{user.name}}.\n"
                "Region: {{region|nationwide}}.\n"
                "{{#alert_level}}ALERT LEVEL: {{alert_level}}.\n{{/alert_level}}"
                "{{#evacuate}}EVACUATE VIA: {{routes}}.{{/evacuate}}"
                "Text: {{bulletin}}")
    context = {"user": {"name": "Ana"}, "alert_level": "Signal 3",
               "bulletin": "Heavy rainfall expected."}
    out = run(template=template, context=context, strict_mode=False)
    p = out["assembled_prompt"]
    # Dotted path + default + present-conditional all render.
    assert "for Ana." in p and "Region: nationwide." in p
    assert "ALERT LEVEL: Signal 3." in p
    # Absent conditional vanishes and is REPORTED.
    assert "EVACUATE" not in p and "evacuate" in out["conditional_fields_omitted"]
    # Resolution accounting is complete.
    assert out["resolved_fields"]["user.name"] == "Ana"
    assert out["resolved_fields"]["region"] == "nationwide"
    assert out["missing_fields"] == []
    # Lenient mode marks missing fields VISIBLY, never silently blank.
    len_out = run(template="Hello {{nope}}", context={}, strict_mode=False)
    assert len_out["assembled_prompt"] == "Hello [missing:nope]"
    assert len_out["missing_fields"] == ["nope"]
    # Strict mode raises on the same input.
    raised = False
    try:
        run(template="Hello {{nope}}", context={})
    except ValueError as e:
        raised = "nope" in str(e)
    assert raised
    # A field inside an omitted conditional never counts as missing.
    cond_only = run(template="{{#x}}{{deep.field}}{{/x}}done", context={}, strict_mode=True)
    assert cond_only["assembled_prompt"] == "done" and cond_only["missing_fields"] == []
    # Deterministic; on_error=raise for bad types.
    assert json.dumps(run(template=template, context=context, strict_mode=False), sort_keys=True) == \
           json.dumps(run(template=template, context=context, strict_mode=False), sort_keys=True)
    raised = False
    try:
        run(template=1, context={})  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised
    print("PASS — template_field_gem: dotted paths, |defaults, conditional blocks "
          "(omissions reported), strict raises / lenient marks visibly, full "
          "resolution accounting, deterministic verified")


if __name__ == "__main__":
    _selftest()
