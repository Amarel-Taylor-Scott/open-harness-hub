#!/usr/bin/env python3
"""scripts.check_template_catalog — proof: _repos/shared-backend-components/architecture/template_catalog.json is well-formed + buildable.

Asserts: it parses; every template.status is in status_enum; every template.standard_id maps to a real
standard in standard_catalog.json; every "active" template_path EXISTS and its template.json parses, its files'
source paths exist, and its declared variables match the manifest; "candidate" templates declare a planned
template_path + a real standard; the 7 required ACTIVE templates (A-G) are present; and >=17 templates are
catalogued. Deterministic + offline.

CLI: python3 _repos/shared-backend-components/scripts/check_template_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_TMPL = _resource("architecture") / "template_catalog.json"
_STD = _resource("architecture") / "standard_catalog.json"

#: the 7 templates the lane spec requires to be BUILT (status active).
REQUIRED_ACTIVE = {
    "ingestion.source_adapter", "worker.command_handler", "api.projection_route",
    "ui.projection_page", "provider.adapter", "proof.self_test", "docs.section_page",
}
_MIN_TEMPLATES = 17

_REQUIRED_TMPL_KEYS = {
    "template_id", "standard_id", "template_path", "output_paths", "variables",
    "required_commands_after_generation", "required_registry_updates", "required_docs",
    "required_proofs", "status",
}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cat = json.loads(_TMPL.read_text())
    templates = cat.get("templates", [])
    check("template_catalog parses + has templates", bool(templates))
    status_enum = set(cat.get("status_enum", []))
    check("status_enum present", bool(status_enum), str(status_enum))
    check(f"at least {_MIN_TEMPLATES} templates catalogued", len(templates) >= _MIN_TEMPLATES, str(len(templates)))

    std = json.loads(_STD.read_text())
    std_ids = {s["standard_id"] for s in std.get("standards", [])}

    active_ids: set[str] = set()
    for t in templates:
        tid = t.get("template_id", "<?>")
        missing_keys = _REQUIRED_TMPL_KEYS - set(t)
        check(f"{tid}: has all required keys", not missing_keys, str(sorted(missing_keys)))
        check(f"{tid}: status in enum", t.get("status") in status_enum, t.get("status"))
        check(f"{tid}: standard_id maps to a real standard", t.get("standard_id") in std_ids, t.get("standard_id"))
        check(f"{tid}: declares a template_path", bool(t.get("template_path")))

        if t.get("status") == "active":
            active_ids.add(tid)
            mpath = _resource(t["template_path"])
            check(f"{tid}: active template manifest exists", mpath.exists(), str(mpath))
            if mpath.exists():
                manifest = json.loads(mpath.read_text())
                check(f"{tid}: manifest template_id matches catalog", manifest.get("template_id") == tid)
                # every files[].source exists
                for spec in manifest.get("files", []):
                    src = mpath.parent / spec["source"]
                    check(f"{tid}: template source exists -> {spec['source']}", src.exists())
                    check(f"{tid}: file spec has a path_template", bool(spec.get("path_template")))
                # manifest variable names cover the catalog's declared variables
                man_vars = {v["name"] for v in manifest.get("variables", [])}
                cat_vars = set(t.get("variables", []))
                check(f"{tid}: catalog variables covered by manifest", cat_vars <= man_vars,
                      str(sorted(cat_vars - man_vars)))

    missing_active = REQUIRED_ACTIVE - active_ids
    check("all 7 required templates are ACTIVE", not missing_active, str(sorted(missing_active)))

    print(f"{'PASS' if not fails else 'FAIL'} check_template_catalog ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: template_catalog.json is well-formed + buildable.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
