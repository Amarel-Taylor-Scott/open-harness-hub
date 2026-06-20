"""src.teleon.extraction.schema_templates — SHOWCASE schema templates + the shared user-schema parser.

Schemas are USER-DEFINED. The field set a deployment extracts is whatever the user writes; these named templates are
code/DB-defined SHOWCASE starting points the user may CHOOSE and then edit — they are not the extraction surface, just
a convenience so a first-time user has something to bend. This module is the SINGLE SOURCE of the "name: class"
grammar so the demo page and any caller agree on it (no parallel parsers). ``employment_agency`` is single-sourced
from the cascade module (no duplicated field list). serves_truth False; Teleon-layer (never imports baltor).
"""
from __future__ import annotations

from src.teleon.extraction.document_extraction_cascade import (
    EMPLOYMENT_AGENCY_SCHEMA, SEMI, STRUCTURED, UNSTRUCTURED,
)

#: the only legal field classes (single-sourced from the cascade's class constants).
VALID_CLASSES = (STRUCTURED, SEMI, UNSTRUCTURED)

#: SHOWCASE templates only — optional starting points. The real extraction schema is whatever the user writes.
SCHEMA_TEMPLATES: dict[str, dict] = {
    "employment_agency": dict(EMPLOYMENT_AGENCY_SCHEMA),                  # single-sourced; the DueCare showcase domain
    "invoice": {
        "invoice_number": STRUCTURED, "invoice_date": STRUCTURED, "total_amount": STRUCTURED,
        "vendor_name": STRUCTURED, "bill_to": SEMI, "line_items": SEMI, "payment_terms": UNSTRUCTURED,
    },
    "resume": {
        "full_name": STRUCTURED, "email": STRUCTURED, "phone": STRUCTURED,
        "skills": SEMI, "employment_history": SEMI, "summary": UNSTRUCTURED,
    },
    "purchase_order": {
        "po_number": STRUCTURED, "order_date": STRUCTURED, "supplier": STRUCTURED,
        "ship_to": SEMI, "items": SEMI, "special_instructions": UNSTRUCTURED,
    },
    "lab_report": {
        "report_id": STRUCTURED, "collected_date": STRUCTURED, "patient_id": STRUCTURED,
        "analyte_values": SEMI, "reference_ranges": SEMI, "interpretation": UNSTRUCTURED,
    },
}


def template_names() -> list[str]:
    return sorted(SCHEMA_TEMPLATES)


def get_template(name: str) -> dict | None:
    """A COPY of a showcase template (or None) — callers may mutate it freely as their own starting point."""
    t = SCHEMA_TEMPLATES.get(name)
    return dict(t) if t else None


def parse_user_schema(text: str) -> dict:
    """SINGLE SOURCE of the 'field_name: structured|semi|unstructured' grammar. One field per line; '#' lines are
    comments; an unknown or missing class -> unstructured (so it escalates rather than silently under-extracting).
    USER-DEFINED is the point: ANY field name the user writes is accepted — templates are optional starting text,
    never a fixed menu."""
    fields: dict[str, str] = {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        name, _, cls = line.partition(":")
        name, cls = name.strip(), cls.strip().lower()
        if name:
            fields[name] = cls if cls in VALID_CLASSES else UNSTRUCTURED
    return fields


def render_template(name: str) -> str:
    """The 'name: class' text a chosen template drops into the user's EDITABLE schema box (empty for unknown names)."""
    t = SCHEMA_TEMPLATES.get(name)
    return "\n".join(f"{f}: {c}" for f, c in t.items()) if t else ""
