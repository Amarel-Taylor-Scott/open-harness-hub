#!/usr/bin/env python3
"""scripts.generate_from_template — the component generator for the Baltor factory.

Reads architecture/template_catalog.json, takes --template <id> --name <n> plus template variables, and
renders a NEW component from templates/<...>/files/ doing {{var}} substitution — so every component starts as
a standards-conformant scaffold (standard_catalog.json) instead of hand-typed drift. It REFUSES on missing
required variables (nonzero exit), refuses to overwrite an existing file unless --force, and writes a
content-addressed generation receipt to .agent/template-generation/<deterministic-id>-<template-id>.json
(deterministic id = sha256 over the rendered output, NOT wall-clock). After rendering it prints the next
required commands (validate/proof/registry updates) from the catalog.

Generated implementation files are STUBS carrying a failing TODO (the proof FAILS until implemented); docs
stubs carry the required headings. This is a META layer over the existing repo — it creates no runtime, bus,
worker, gateway, optimizer, or parser framework.

Deterministic + offline: no network, no wall-clock in any id; the receipt id is content-addressed.

CLI:
    python3 scripts/generate_from_template.py --list
    python3 scripts/generate_from_template.py --template proof.self_test.v1 --proof_name foo \\
        --title "Foo proof" --owner scripts/foo.py --subject_module scripts.foo
    python3 scripts/generate_from_template.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_CATALOG = _REPO / "architecture" / "template_catalog.json"
_RECEIPT_DIR = _REPO / ".agent" / "template-generation"
_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
#: an output path under these roots is treated as an implementation file -> stub gets a failing TODO.
_IMPL_SUFFIXES = (".py", ".html")


def _load_catalog(catalog_path: Path | None = None) -> dict:
    return json.loads((catalog_path or _CATALOG).read_text())


def _template_entry(catalog: dict, template_id: str) -> dict | None:
    for t in catalog.get("templates", []):
        if t["template_id"] == template_id:
            return t
    return None


def _render(text: str, variables: dict) -> str:
    return _VAR_RE.sub(lambda m: str(variables.get(m.group(1), m.group(0))), text)


def _required_vars(manifest: dict) -> list[str]:
    return [v["name"] for v in manifest.get("variables", []) if v.get("required")]


def _all_vars(manifest: dict) -> list[str]:
    return [v["name"] for v in manifest.get("variables", [])]


def _receipt_id(rendered: dict[str, str], template_id: str) -> str:
    """Content-addressed over (template_id + sorted rendered output) — deterministic, no wall-clock."""
    body = {"template_id": template_id, "files": {k: rendered[k] for k in sorted(rendered)}}
    return "gen-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


class GenerationError(Exception):
    pass


def generate(template_id: str, variables: dict, *, repo: Path = _REPO, force: bool = False,
             write_receipt: bool = True, catalog_path: Path | None = None) -> dict:
    """Render a template into `repo`. Returns the receipt dict. Raises GenerationError on a refusal.

    Refusals (nonzero-exit conditions in the CLI): unknown/candidate template, missing required variable,
    or an existing output file without --force.
    """
    catalog = _load_catalog(catalog_path) if catalog_path else _load_catalog()
    entry = _template_entry(catalog, template_id)
    if entry is None:
        raise GenerationError(f"unknown template_id {template_id!r}")
    if entry.get("status") != "active":
        raise GenerationError(f"template {template_id!r} is status {entry.get('status')!r}, not 'active'")

    manifest_path = repo / entry["template_path"]
    if not manifest_path.exists():
        raise GenerationError(f"template manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())

    missing = [v for v in _required_vars(manifest) if not str(variables.get(v, "")).strip()]
    if missing:
        raise GenerationError(f"missing required variable(s): {', '.join(missing)}")

    tmpl_dir = manifest_path.parent
    # render every file: target path (from path_template) + body (from source file)
    rendered: dict[str, str] = {}   # rel_target -> body
    for spec in manifest.get("files", []):
        target_rel = _render(spec["path_template"], variables)
        src = tmpl_dir / spec["source"]
        if not src.exists():
            raise GenerationError(f"template source missing: {src}")
        body = _render(src.read_text(), variables)
        rendered[target_rel] = body

    # refuse to overwrite (unless --force) BEFORE writing anything
    if not force:
        clashes = [t for t in rendered if (repo / t).exists()]
        if clashes:
            raise GenerationError(f"refusing to overwrite existing file(s) without --force: {', '.join(clashes)}")

    written: list[str] = []
    for target_rel, body in rendered.items():
        dest = repo / target_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body)
        written.append(target_rel)

    receipt = {
        "schema_version": "TemplateGenerationReceipt.v1",
        "receipt_id": _receipt_id(rendered, template_id),
        "template_id": template_id,
        "standard_id": entry.get("standard_id"),
        "variables": {k: variables.get(k) for k in _all_vars(manifest)},
        "files_written": sorted(written),
        "impl_files": sorted(f for f in written if f.endswith(_IMPL_SUFFIXES)),
        "required_commands_after_generation": [_render(c, variables) for c in manifest.get("required_commands_after_generation", [])],
        "required_registry_updates": [_render(r, variables) for r in manifest.get("required_registry_updates", [])],
        "required_proofs": [_render(p, variables) for p in manifest.get("required_proofs", [])],
        "required_docs": [_render(d, variables) for d in manifest.get("required_docs", [])],
    }
    if write_receipt:
        rdir = repo / ".agent" / "template-generation"
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / f"{receipt['receipt_id']}-{template_id}.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
    return receipt


def _print_next_steps(receipt: dict) -> None:
    print("\nGenerated files:")
    for f in receipt["files_written"]:
        tag = " (stub: failing TODO until implemented)" if f.endswith(_IMPL_SUFFIXES) else ""
        print(f"  + {f}{tag}")
    if receipt["required_registry_updates"]:
        print("\nRequired registry updates (do these next):")
        for r in receipt["required_registry_updates"]:
            print(f"  - {r}")
    if receipt["required_commands_after_generation"]:
        print("\nRequired commands (run these next):")
        for c in receipt["required_commands_after_generation"]:
            print(f"  $ {c}")
    print(f"\nReceipt: .agent/template-generation/{receipt['receipt_id']}-{receipt['template_id']}.json")


def _list() -> int:
    catalog = _load_catalog()
    print(f"template_catalog v{catalog.get('version')} — {len(catalog['templates'])} templates")
    for t in catalog["templates"]:
        vs = ",".join(t.get("variables", []))
        print(f"  [{t['status']:9}] {t['template_id']:28} -> {t['standard_id']:36} vars: {vs}")
    return 0


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    catalog = _load_catalog()
    check("catalog parses + has templates", bool(catalog.get("templates")))
    active = [t for t in catalog["templates"] if t["status"] == "active"]
    check("at least 7 active templates", len(active) >= 7, str(len(active)))

    # render the proof template into a temp repo (copy templates/ + the catalog so paths resolve)
    tmp = Path(tempfile.mkdtemp(prefix="gen_selftest_"))
    try:
        (tmp / "architecture").mkdir(parents=True, exist_ok=True)
        shutil.copy(_CATALOG, tmp / "architecture" / "template_catalog.json")
        shutil.copytree(_REPO / "templates", tmp / "templates")

        # missing required variable -> refusal
        try:
            generate("proof.self_test.v1", {"proof_name": "demo"}, repo=tmp, write_receipt=False)
            check("refuses missing required variable", False, "did not raise")
        except GenerationError as e:
            check("refuses missing required variable", "missing required" in str(e))

        full = {"proof_name": "demo_gen", "title": "Demo gen proof", "owner": "scripts/demo.py",
                "subject_module": "scripts.demo"}
        rec = generate("proof.self_test.v1", full, repo=tmp)
        gen = tmp / "scripts" / "check_demo_gen.py"
        check("rendered the proof file", gen.exists())
        check("generated proof contains --self-test", "--self-test" in gen.read_text())
        check("no unrendered {{var}} left in proof", "{{" not in gen.read_text())
        check("receipt id is content-addressed (gen-)", rec["receipt_id"].startswith("gen-"))

        # determinism: same inputs -> same receipt id
        tmp2 = Path(tempfile.mkdtemp(prefix="gen_selftest2_"))
        try:
            shutil.copytree(_REPO / "templates", tmp2 / "templates")
            (tmp2 / "architecture").mkdir(parents=True, exist_ok=True)
            shutil.copy(_CATALOG, tmp2 / "architecture" / "template_catalog.json")
            rec2 = generate("proof.self_test.v1", full, repo=tmp2, write_receipt=False)
            check("deterministic receipt id across runs", rec["receipt_id"] == rec2["receipt_id"])
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

        # refuse overwrite without --force
        try:
            generate("proof.self_test.v1", full, repo=tmp, write_receipt=False)
            check("refuses overwrite without --force", False, "did not raise")
        except GenerationError as e:
            check("refuses overwrite without --force", "without --force" in str(e))
        rec3 = generate("proof.self_test.v1", full, repo=tmp, force=True, write_receipt=False)
        check("--force allows overwrite", rec3["receipt_id"] == rec["receipt_id"])

        # docs template renders with required headings
        docs = generate("docs.section_page.v1",
                        {"area": "runtime", "section": "demo-sec", "title": "Demo Sec", "owner": "scripts/x.py"},
                        repo=tmp)
        page = tmp / "docs" / "runtime" / "demo-sec.md"
        body = page.read_text()
        required = ["Purpose", "Owner", "Inputs", "Outputs", "Contracts", "Ports", "Adapters",
                    "Registry entries", "Proofs", "Commands", "Limitations", "Opportunities", "Next steps"]
        check("docs template has all required headings",
              all(f"## {h}" in body for h in required),
              str([h for h in required if f"## {h}" not in body]))
        check("docs receipt records the doc as required", docs["required_docs"] == ["docs/runtime/demo-sec.md"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"{'PASS' if not fails else 'FAIL'} generate_from_template ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate a standards-conformant component from a template.")
    p.add_argument("--template", help="template_id from architecture/template_catalog.json")
    p.add_argument("--name", help="convenience name (alias for the template's primary variable)")
    p.add_argument("--force", action="store_true", help="overwrite existing files")
    p.add_argument("--list", action="store_true", help="list templates")
    p.add_argument("--self-test", action="store_true")
    # template variables are accepted as --<var> <value>
    a, extra = p.parse_known_args(argv)

    if a.self_test:
        return _self_test()
    if a.list:
        return _list()
    if not a.template:
        p.print_help()
        return 0

    # parse the extra --<var> <value> pairs
    variables: dict = {}
    i = 0
    while i < len(extra):
        tok = extra[i]
        if tok.startswith("--"):
            key = tok[2:]
            val = extra[i + 1] if i + 1 < len(extra) and not extra[i + 1].startswith("--") else "true"
            variables[key] = val
            i += 2
        else:
            i += 1

    # --name maps onto the template's first declared variable if that variable isn't already set
    catalog = _load_catalog()
    entry = _template_entry(catalog, a.template)
    if a.name and entry and entry.get("variables"):
        first = entry["variables"][0]
        variables.setdefault(first, a.name)

    try:
        receipt = generate(a.template, variables, force=a.force)
    except GenerationError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    _print_next_steps(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
