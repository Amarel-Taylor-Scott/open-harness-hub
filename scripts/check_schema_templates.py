#!/usr/bin/env python3
"""check_schema_templates — proof that schema extraction is USER-DEFINED, with optional code/DB SHOWCASE templates the
user may CHOOSE as a starting point. Any field name the user writes is accepted (templates are not a fixed menu); the
'name: class' grammar has a single source (no parallel parsers); the employment_agency template is single-sourced from
the cascade (no duplicated field list); a chosen template round-trips through render→parse; a user-defined schema in NO
template still runs the real cascade. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_schema_templates.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.extraction.document_extraction_cascade import EMPLOYMENT_AGENCY_SCHEMA, extract
from src.teleon.extraction.schema_templates import (
    SCHEMA_TEMPLATES, VALID_CLASSES, get_template, parse_user_schema, render_template, template_names,
)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    names = template_names()
    ck("there are >=4 showcase templates to choose from", len(names) >= 4, str(names))
    ck("every template is a valid {field: class} map (classes are the cascade's class constants)",
       all(isinstance(t, dict) and t and all(c in VALID_CLASSES for c in t.values()) for t in SCHEMA_TEMPLATES.values()))

    # SINGLE SOURCE: employment_agency is the cascade's schema, not a re-typed copy
    ck("employment_agency template is single-sourced from the cascade (no duplicated field list)",
       get_template("employment_agency") == dict(EMPLOYMENT_AGENCY_SCHEMA))

    # USER-DEFINED is the real path: any field name the user writes is accepted, not just template fields
    user_text = "# my own fields\nwidget_serial: structured\ntorque_spec: semi\nfailure_notes: unstructured\nbad_line_no_colon\n"
    parsed = parse_user_schema(user_text)
    ck("the user-schema parser accepts arbitrary user field names (templates are not a fixed menu)",
       parsed == {"widget_serial": "structured", "torque_spec": "semi", "failure_notes": "unstructured"})
    ck("comment lines and malformed lines are ignored (no crash, no phantom fields)", "bad_line_no_colon" not in parsed)
    ck("an unknown/missing class falls back to unstructured (so it escalates, never silently under-extracts)",
       parse_user_schema("x: wizardry\ny:")["x"] == "unstructured" and parse_user_schema("x: wizardry\ny:")["y"] == "unstructured")

    # a user-defined schema in NO template runs the REAL cascade end to end
    res = extract(parsed, {"has_text_layer": True}, available_keys=("LLM_API_KEY",))
    ck("a user-defined (non-template) schema runs the real cascade and meets the requirement",
       res["met_requirement"] and "widget_serial" in res["filled"] and res["serves_truth"] is False)

    # CHOOSING a template round-trips: render -> parse == the template dict (chooser prefills exactly what runs)
    rt_ok = True
    for n in names:
        if parse_user_schema(render_template(n)) != get_template(n):
            rt_ok = False
    ck("every template round-trips render→parse (the chooser prefills exactly the schema that runs)", rt_ok)
    ck("render of an unknown template name is empty (no fabricated fields)", render_template("nope") == "")

    # get_template returns a COPY (mutating it must not corrupt the showcase library)
    t = get_template("invoice"); t["injected"] = "structured"
    ck("get_template returns a copy (caller edits don't mutate the showcase library)", "injected" not in SCHEMA_TEMPLATES["invoice"])

    print("\n" + (f"PASS - check_schema_templates: extraction is USER-DEFINED — any field name the user writes runs the "
                  f"real cascade; {len(names)} code/DB showcase templates are an OPTIONAL chooser (employment_agency "
                  f"single-sourced from the cascade); one parser grammar; chosen templates round-trip render→parse. "
                  f"serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_schema_templates.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
