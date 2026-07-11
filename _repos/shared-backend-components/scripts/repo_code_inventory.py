#!/usr/bin/env python3
"""Exhaustive owned-source code inventory.

This command creates durable artifacts for the review surface the owner asked for:
every owned text/source file, every owned Python module/package, every definition symbol, every
reference, every import, and every structural edge that the deterministic analyzers can see.

It intentionally follows the repo's owned-source contract and excludes vendored/reference/generated/data/cache
surfaces unless a caller points it at a narrower explicit path. The inventory is evidence, not truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from scripts import pyprefix
from scripts import repo_line_review_loop
py_const_scripts_repo_code_inventory__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
py_const_scripts_repo_code_inventory__DEFAULT_OUT = (py_const_scripts_repo_code_inventory__REPO / ".agent") / "repo-code-inventory"


def py_function_scripts_repo_code_inventory__now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def py_function_scripts_repo_code_inventory__repo_rel(py_arg_path):
    try:
        return str(Path(py_arg_path).resolve().relative_to(py_const_scripts_repo_code_inventory__REPO.resolve()))
    except ValueError:
        return str(py_arg_path)


def py_function_scripts_repo_code_inventory__jsonl_write(py_arg_path, py_arg_rows):
    py_arg_path.parent.mkdir(parents=True, exist_ok=True)
    py_var_count = 0
    with py_arg_path.open("w", encoding="utf-8") as py_var_fh:
        for py_var_row in py_arg_rows:
            py_var_fh.write(json.dumps(py_var_row, sort_keys=True) + "\n")
            py_var_count += 1
    return py_var_count


def py_function_scripts_repo_code_inventory__symbol_row(py_arg_info, py_arg_def, py_arg_refs_by_name):
    py_var_path = Path(py_arg_info["path"])
    py_var_rel = py_function_scripts_repo_code_inventory__repo_rel(py_var_path)
    py_var_target = pyprefix.qualified_name(
        py_arg_def["kind"],
        py_arg_def["name"],
        py_var_rel,
        py_arg_def.get("scope", "<module>"),
    )
    py_var_refs = py_arg_refs_by_name.get(py_arg_def["name"], [])
    return {
        "path": py_var_rel,
        "line": py_arg_def["line"],
        "col": py_arg_def["col"],
        "kind": py_arg_def["kind"],
        "name": py_arg_def["name"],
        "scope": py_arg_def.get("scope", "<module>"),
        "target": py_var_target,
        "conforms": py_arg_def["name"] == py_var_target or pyprefix.is_dunder(py_arg_def["name"]),
        "ref_count": len(py_var_refs),
        "sample_refs": py_var_refs[:8],
    }


def py_function_scripts_repo_code_inventory__build(py_arg_root, py_arg_out):
    py_arg_out.mkdir(parents=True, exist_ok=True)

    py_var_file_records = repo_line_review_loop.discover_files(py_arg_root)
    py_var_python_files = pyprefix._py_files(py_arg_root)
    py_var_python_infos = [pyprefix.analyze_file(py_var_file) for py_var_file in py_var_python_files]

    py_var_file_rows = []
    for py_var_rec in py_var_file_records:
        py_var_file_rows.append({
            "path": py_var_rec.rel,
            "size": py_var_rec.size,
            "sha256": py_var_rec.sha256,
            "line_count": py_var_rec.line_count,
        })

    py_var_refs_by_name = defaultdict(list)
    for py_var_info in py_var_python_infos:
        py_var_rel = py_function_scripts_repo_code_inventory__repo_rel(py_var_info["path"])
        for py_var_ref in py_var_info["refs"]:
            py_var_refs_by_name[py_var_ref["name"]].append({
                "path": py_var_rel,
                "line": py_var_ref["line"],
                "col": py_var_ref["col"],
                "scope": py_var_ref.get("scope", "<module>"),
                "attr": bool(py_var_ref.get("attr")),
            })

    py_var_module_rows = []
    py_var_symbol_rows = []
    py_var_reference_rows = []
    py_var_import_rows = []
    py_var_edge_rows = []
    py_var_packages = Counter()
    py_var_symbol_kind_counts = Counter()
    py_var_violation_kind_counts = Counter()
    py_var_import_module_counts = Counter()
    py_var_edge_type_counts = Counter()
    py_var_errors = []

    for py_var_info in py_var_python_infos:
        py_var_path = Path(py_var_info["path"])
        py_var_rel = py_function_scripts_repo_code_inventory__repo_rel(py_var_path)
        py_var_module = pyprefix._module_name(py_var_path, py_arg_root if py_arg_root.is_dir() else py_arg_root.parent)
        py_var_package = py_var_module.split(".", 1)[0] if py_var_module else "<module>"
        py_var_packages[py_var_package] += 1
        if py_var_info.get("error"):
            py_var_errors.append({"path": py_var_rel, "error": py_var_info["error"]})

        py_var_defs_by_kind = Counter(py_var_def["kind"] for py_var_def in py_var_info["defs"])
        py_var_import_modules = []
        for py_var_import in py_var_info["imports"]:
            py_var_import_row = {
                "path": py_var_rel,
                "line": py_var_import["line"],
                "module": py_var_import.get("module"),
                "name": py_var_import.get("name"),
                "asname": py_var_import.get("asname"),
            }
            py_var_import_rows.append(py_var_import_row)
            py_var_import_modules.append(py_var_import.get("module"))
            py_var_import_module_counts[py_var_import.get("module") or ""] += 1

        for py_var_def in py_var_info["defs"]:
            py_var_row = py_function_scripts_repo_code_inventory__symbol_row(py_var_info, py_var_def, py_var_refs_by_name)
            py_var_symbol_rows.append(py_var_row)
            py_var_symbol_kind_counts[py_var_row["kind"]] += 1
            if not py_var_row["conforms"]:
                py_var_violation_kind_counts[py_var_row["kind"]] += 1

        for py_var_ref in py_var_info["refs"]:
            py_var_reference_rows.append({
                "path": py_var_rel,
                "line": py_var_ref["line"],
                "col": py_var_ref["col"],
                "name": py_var_ref["name"],
                "scope": py_var_ref.get("scope", "<module>"),
                "attr": bool(py_var_ref.get("attr")),
            })

        for py_var_edge in py_var_info["edges"]:
            py_var_edge_row = {
                "path": py_var_rel,
                "src": py_var_edge.get("src"),
                "dst": py_var_edge.get("dst"),
                "type": py_var_edge.get("type"),
            }
            py_var_edge_rows.append(py_var_edge_row)
            py_var_edge_type_counts[py_var_edge.get("type") or ""] += 1

        py_var_module_rows.append({
            "path": py_var_rel,
            "module": py_var_module,
            "package": py_var_package,
            "defs": len(py_var_info["defs"]),
            "defs_by_kind": dict(py_var_defs_by_kind),
            "refs": len(py_var_info["refs"]),
            "imports": len(py_var_info["imports"]),
            "import_modules": sorted({py_var_mod for py_var_mod in py_var_import_modules if py_var_mod}),
            "edges": len(py_var_info["edges"]),
            "error": py_var_info.get("error"),
        })

    py_var_file_count = py_function_scripts_repo_code_inventory__jsonl_write(py_arg_out / "files.jsonl", py_var_file_rows)
    py_var_module_count = py_function_scripts_repo_code_inventory__jsonl_write(py_arg_out / "python_modules.jsonl", py_var_module_rows)
    py_var_symbol_count = py_function_scripts_repo_code_inventory__jsonl_write(py_arg_out / "symbols.jsonl", py_var_symbol_rows)
    py_var_reference_count = py_function_scripts_repo_code_inventory__jsonl_write(py_arg_out / "references.jsonl", py_var_reference_rows)
    py_var_import_count = py_function_scripts_repo_code_inventory__jsonl_write(py_arg_out / "imports.jsonl", py_var_import_rows)
    py_var_edge_count = py_function_scripts_repo_code_inventory__jsonl_write(py_arg_out / "edges.jsonl", py_var_edge_rows)

    py_var_findings_path = (py_const_scripts_repo_code_inventory__REPO / ".agent") / "repo-line-review" / "findings.jsonl"
    py_var_finding_counts = Counter()
    py_var_severity_counts = Counter()
    if py_var_findings_path.exists():
        for py_var_line in py_var_findings_path.read_text(encoding="utf-8").splitlines():
            if not py_var_line.strip():
                continue
            py_var_row = json.loads(py_var_line)
            py_var_finding_counts[py_var_row.get("kind", "")] += 1
            py_var_severity_counts[py_var_row.get("severity", "")] += 1

    py_var_manifest = {
        "created_at": py_function_scripts_repo_code_inventory__now(),
        "serves_truth": False,
        "root": str(py_arg_root),
        "scope": "owned text/source files and owned Python source; excludes repo-configured reference/generated/data/cache/scratch paths",
        "files": py_var_file_count,
        "python_modules": py_var_module_count,
        "packages": len(py_var_packages),
        "symbols": py_var_symbol_count,
        "references": py_var_reference_count,
        "imports": py_var_import_count,
        "edges": py_var_edge_count,
        "symbol_kinds": dict(py_var_symbol_kind_counts),
        "pyprefix_violations": sum(py_var_violation_kind_counts.values()),
        "violations_by_kind": dict(py_var_violation_kind_counts),
        "edge_types": dict(py_var_edge_type_counts),
        "top_packages": [{"package": py_var_pkg, "modules": py_var_count} for py_var_pkg, py_var_count in py_var_packages.most_common(30)],
        "top_import_modules": [{"module": py_var_mod, "count": py_var_count} for py_var_mod, py_var_count in py_var_import_module_counts.most_common(30)],
        "finding_kinds": dict(py_var_finding_counts.most_common(30)),
        "finding_severity": dict(py_var_severity_counts),
        "errors": py_var_errors,
        "artifacts": {
            "files": str(py_arg_out / "files.jsonl"),
            "python_modules": str(py_arg_out / "python_modules.jsonl"),
            "symbols": str(py_arg_out / "symbols.jsonl"),
            "references": str(py_arg_out / "references.jsonl"),
            "imports": str(py_arg_out / "imports.jsonl"),
            "edges": str(py_arg_out / "edges.jsonl"),
            "summary": str(py_arg_out / "summary.md"),
        },
    }
    (py_arg_out / "manifest.json").write_text(json.dumps(py_var_manifest, indent=2, sort_keys=True), encoding="utf-8")
    py_function_scripts_repo_code_inventory__write_summary(py_arg_out, py_var_manifest)
    return py_var_manifest


def py_function_scripts_repo_code_inventory__write_summary(py_arg_out, py_arg_manifest):
    py_var_lines = [
        "# Repo Code Inventory",
        "",
        f"- Updated: `{py_arg_manifest['created_at']}`",
        f"- Root: `{py_arg_manifest['root']}`",
        f"- Scope: `{py_arg_manifest['scope']}`",
        f"- Files: `{py_arg_manifest['files']}`",
        f"- Python modules: `{py_arg_manifest['python_modules']}`",
        f"- Packages: `{py_arg_manifest['packages']}`",
        f"- Symbols: `{py_arg_manifest['symbols']}`",
        f"- References: `{py_arg_manifest['references']}`",
        f"- Imports: `{py_arg_manifest['imports']}`",
        f"- Structural edges: `{py_arg_manifest['edges']}`",
        f"- Pyprefix violations: `{py_arg_manifest['pyprefix_violations']}`",
        f"- Serves truth: `{py_arg_manifest['serves_truth']}`",
        "",
        "## Symbol Kinds",
        "",
        "```json",
        json.dumps(py_arg_manifest["symbol_kinds"], indent=2, sort_keys=True),
        "```",
        "",
        "## Edge Types",
        "",
        "```json",
        json.dumps(py_arg_manifest["edge_types"], indent=2, sort_keys=True),
        "```",
        "",
        "## Finding Severity",
        "",
        "```json",
        json.dumps(py_arg_manifest["finding_severity"], indent=2, sort_keys=True),
        "```",
        "",
        "Artifacts:",
        "",
        "- `files.jsonl`",
        "- `python_modules.jsonl`",
        "- `symbols.jsonl`",
        "- `references.jsonl`",
        "- `imports.jsonl`",
        "- `edges.jsonl`",
        "- `manifest.json`",
    ]
    (py_arg_out / "summary.md").write_text("\n".join(py_var_lines) + "\n", encoding="utf-8")


def py_function_scripts_repo_code_inventory___self_test():
    import tempfile
    py_var_failures = []

    def py_function_scripts_repo_code_inventory___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    with tempfile.TemporaryDirectory() as py_var_dir:
        py_var_root = Path(py_var_dir)
        (py_var_root / "scripts").mkdir()
        (py_var_root / "scripts" / "sample.py").write_text(
            "import json\n\n"
            "class Cart:\n"
            "    def add(self, item):\n"
            "        total = len(item)\n"
            "        return total\n\n"
            "def run(value):\n"
            "    c = Cart()\n"
            "    return c.add(json.dumps(value))\n",
            encoding="utf-8",
        )
        py_var_out = py_var_root / ".agent" / "inventory"
        py_var_old_repo = pyprefix.REPO_ROOT
        py_var_old_review_repo = repo_line_review_loop.REPO
        try:
            pyprefix.REPO_ROOT = py_var_root
            repo_line_review_loop.REPO = py_var_root
            py_var_manifest = py_function_scripts_repo_code_inventory__build(py_var_root, py_var_out)
        finally:
            pyprefix.REPO_ROOT = py_var_old_repo
            repo_line_review_loop.REPO = py_var_old_review_repo
        py_function_scripts_repo_code_inventory___self_test__check("inventory writes file/module/symbol/import artifacts",
            all((py_var_out / py_var_name).exists() for py_var_name in ("files.jsonl", "python_modules.jsonl", "symbols.jsonl", "imports.jsonl", "references.jsonl", "edges.jsonl")))
        py_function_scripts_repo_code_inventory___self_test__check("inventory counted defs/imports/refs",
            py_var_manifest["symbols"] >= 6 and py_var_manifest["imports"] == 1 and py_var_manifest["references"] >= 4,
            json.dumps(py_var_manifest, sort_keys=True)[:500])
        py_function_scripts_repo_code_inventory___self_test__check("inventory is candidate evidence, not truth",
            py_var_manifest["serves_truth"] is False)

    if py_var_failures:
        print(f"\nFAIL - repo_code_inventory: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - repo_code_inventory: emits exhaustive owned-source files/modules/symbols/references/imports/edges inventory")
    return 0


def py_function_scripts_repo_code_inventory__main(py_arg_argv=None):
    py_var_parser = argparse.ArgumentParser(description="Build exhaustive owned-source code inventory artifacts.")
    py_var_parser.add_argument("root", nargs="?", default=".")
    py_var_parser.add_argument("--out", default=str(py_const_scripts_repo_code_inventory__DEFAULT_OUT))
    py_var_parser.add_argument("--self-test", action="store_true")
    py_var_args = py_var_parser.parse_args(py_arg_argv)
    if py_var_args.self_test:
        return py_function_scripts_repo_code_inventory___self_test()
    py_var_root = Path(py_var_args.root)
    if not py_var_root.is_absolute():
        py_var_root = (py_const_scripts_repo_code_inventory__REPO / py_var_root).resolve()
    py_var_out = Path(py_var_args.out)
    if not py_var_out.is_absolute():
        py_var_out = (py_const_scripts_repo_code_inventory__REPO / py_var_out).resolve()
    py_var_manifest = py_function_scripts_repo_code_inventory__build(py_var_root, py_var_out)
    print(json.dumps(py_var_manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_repo_code_inventory__main())
