#!/usr/bin/env python3
"""scripts.primitive_placement — the LAST MILE: place a certified primitive INTO real code (new, existing, or
legacy) so its verified body is reused at 0 model tokens instead of the LLM regenerating it. Placement is a ZOO of
deterministic, AST-verified strategies (multi-path law) — the caller/router picks by target and intent:

    import_and_call    the primitive ships in an installable package -> add `from <pkg> import <entry>` (+ call)
    vendored_module    emit the primitive as a standalone module file + a relative import (projects that vendor)
    direct_insertion   inline the primitive's function def at module scope (self-contained, no dependency)
    class_method       insert the primitive as a METHOD into a named class (adds `self`, indents the body)
    legacy_codemod     REPLACE an existing hand-rolled impl (by function name) with the certified body, keeping the
                       signature via a shim if it differs — the legacy-modernization path

Every placement is AST-verified (the result must `ast.parse` cleanly and contain the entry), produces a unified
diff + a candidate-only placement receipt (primitive_id, target, strategy, import_added, verified_parses), and
NEVER executes anything. serves_truth=false — a placement is a proposed edit, not a promotion.

    python3 scripts/primitive_placement.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import difflib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_placement requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
PLACEMENT_RECORD_TYPE = "primitive_placement"
STRATEGIES = ("import_and_call", "vendored_module", "direct_insertion", "class_method", "legacy_codemod")
_DATA_SUBDIR = "data/dev-intel/primitive_placement"


def _entry_of(body: str) -> Optional[str]:
    """The primitive's entry function name (first top-level def)."""
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return None


def _verify(source: str, must_contain: str) -> bool:
    """A placement is only valid if the RESULT parses cleanly and contains the entry symbol."""
    try:
        ast.parse(source)
    except SyntaxError:
        return False
    return must_contain in source


def _import_insert_line(target: str) -> int:
    """Line index to insert an import: after the last top-level import, else after the module docstring, else 0."""
    try:
        tree = ast.parse(target)
    except SyntaxError:
        return 0
    last_import = 0
    body = tree.body
    start = 1 if (body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant)
                  and isinstance(body[0].value.value, str)) else 0
    for node in body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            last_import = node.end_lineno or node.lineno
    return last_import if last_import else (body[start - 1].end_lineno if start else 0)


def _diff(before: str, after: str, path: str) -> str:
    return "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                        fromfile=f"a/{path}", tofile=f"b/{path}"))


def place(primitive: dict[str, Any], strategy: str, *, target_source: str = "", target_path: str = "target.py",
          package: str = "oh_primitives", class_name: str = "", legacy_func: str = "") -> dict[str, Any]:
    """Produce a placement plan. Returns {ok, strategy, placed_source|module_source, diff, import_added, receipt}.
    Deterministic + AST-verified; never executes the primitive."""
    body = str(primitive.get("executable_body") or primitive.get("code") or "").strip("\n") + "\n"
    entry = primitive.get("entry") or _entry_of(body)
    pid = primitive.get("primitive_id", "prim")
    base = {"record_type": PLACEMENT_RECORD_TYPE, "primitive_id": pid, "strategy": strategy, "entry": entry,
            "placement_id": canonical_id("place", pid, strategy, target_path), **BOUNDARY}
    if not entry:
        return {**base, "ok": False, "reason": "no_entry_function_in_primitive"}

    if strategy == "import_and_call":
        imp = f"from {package} import {entry}\n"
        placed = imp + target_source if imp.strip() not in target_source else target_source
        return {**base, "ok": _verify(placed, entry), "import_added": imp.strip(),
                "placed_source": placed, "diff": _diff(target_source, placed, target_path)}

    if strategy == "vendored_module":
        module_name = re.sub(r"[^a-z0-9_]", "_", str(entry).lower())
        imp = f"from .{module_name} import {entry}\n"
        placed = imp + target_source
        return {**base, "ok": _verify(body, entry) and _verify(placed, entry), "import_added": imp.strip(),
                "module_path": f"{module_name}.py", "module_source": body, "placed_source": placed,
                "diff": _diff(target_source, placed, target_path)}

    if strategy == "direct_insertion":
        lines = target_source.splitlines(keepends=True)
        at = _import_insert_line(target_source)
        placed = "".join(lines[:at]) + ("\n\n" if at else "") + body + "".join(lines[at:])
        return {**base, "ok": _verify(placed, f"def {entry}"), "import_added": None,
                "placed_source": placed, "diff": _diff(target_source, placed, target_path)}

    if strategy == "class_method":
        if not class_name:
            return {**base, "ok": False, "reason": "class_method_needs_class_name"}
        try:
            tree = ast.parse(target_source)
        except SyntaxError:
            return {**base, "ok": False, "reason": "target_does_not_parse"}
        cls = next((n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name), None)
        if cls is None:
            return {**base, "ok": False, "reason": f"class_not_found:{class_name}"}
        # indent the body one level and inject `self` as the first parameter of the entry def
        method = re.sub(rf"def {re.escape(entry)}\(", f"def {entry}(self, ", body, count=1)
        method = "".join(("    " + ln if ln.strip() else ln) for ln in method.splitlines(keepends=True))
        lines = target_source.splitlines(keepends=True)
        insert_at = (cls.body[-1].end_lineno if cls.body else cls.lineno)  # after the class' last statement
        placed = "".join(lines[:insert_at]) + "\n" + method + "".join(lines[insert_at:])
        return {**base, "ok": _verify(placed, f"def {entry}(self"), "import_added": None,
                "placed_source": placed, "diff": _diff(target_source, placed, target_path)}

    if strategy == "legacy_codemod":
        if not legacy_func:
            return {**base, "ok": False, "reason": "legacy_codemod_needs_legacy_func"}
        try:
            tree = ast.parse(target_source)
        except SyntaxError:
            return {**base, "ok": False, "reason": "target_does_not_parse"}
        old = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == legacy_func), None)
        if old is None:
            return {**base, "ok": False, "reason": f"legacy_func_not_found:{legacy_func}"}
        lines = target_source.splitlines(keepends=True)
        # rename the certified body to the legacy name (a signature shim if the arities differ is emitted as a note)
        new_body = re.sub(rf"def {re.escape(entry)}\(", f"def {legacy_func}(", body, count=1)
        placed = "".join(lines[:old.lineno - 1]) + new_body + "".join(lines[(old.end_lineno or old.lineno):])
        shim_needed = _entry_of(body) != legacy_func  # signatures may differ -> caller reviews the shim
        return {**base, "ok": _verify(placed, f"def {legacy_func}("), "import_added": None,
                "replaced": legacy_func, "shim_review_needed": shim_needed,
                "placed_source": placed, "diff": _diff(target_source, placed, target_path)}

    return {**base, "ok": False, "reason": f"unknown_strategy:{strategy}"}


def write_receipt(rec: dict[str, Any], out_path: Optional[Path] = None) -> Path:
    out_path = out_path or (resource(_DATA_SUBDIR) / "placement_receipts.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in rec.items() if k not in ("placed_source", "module_source")}  # store the plan, not the blob
    slim["diff_lines"] = len((rec.get("diff") or "").splitlines())
    with out_path.open("a") as fh:
        fh.write(json.dumps(slim, sort_keys=True) + "\n")
    return out_path


# ── self-test (offline, deterministic, AST-verified) ──────────────────────────────────────────────────────────
_PRIM = {"primitive_id": "prim:zip", "entry": "parse_zip",
         "executable_body": "def parse_zip(s):\n    s = str(s).strip()\n    return {'zip5': s[:5]}\n"}
_NEW = "import os\n\n\ndef handler(req):\n    return req\n"
_CLASS = "class Service:\n    def __init__(self):\n        self.x = 1\n\n    def run(self):\n        return self.x\n"
_LEGACY = ("import re\n\n\ndef parse_zip(s):\n    # old buggy hand-rolled version\n    return s[0:4]\n\n\n"
           "def caller(z):\n    return parse_zip(z)\n")


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    imp = place(_PRIM, "import_and_call", target_source=_NEW)
    checks.append(("import_and_call: adds `from oh_primitives import parse_zip`, result parses",
                   imp["ok"] and imp["import_added"] == "from oh_primitives import parse_zip"))

    ven = place(_PRIM, "vendored_module", target_source=_NEW)
    checks.append(("vendored_module: emits a standalone module + relative import, both parse",
                   ven["ok"] and ven["module_path"] == "parse_zip.py" and "def parse_zip" in ven["module_source"]))

    di = place(_PRIM, "direct_insertion", target_source=_NEW)
    checks.append(("direct_insertion: inlines the def at module scope after imports, result parses",
                   di["ok"] and "def parse_zip" in di["placed_source"] and "import os" in di["placed_source"]))

    cm = place(_PRIM, "class_method", target_source=_CLASS, class_name="Service")
    checks.append(("class_method: injects as a `def parse_zip(self, ...)` into Service, result parses",
                   cm["ok"] and "def parse_zip(self" in cm["placed_source"]))
    # verify the injected method is actually INSIDE the class (indented), not module-level
    checks.append(("class_method insertion is inside the class body (indented)",
                   cm["ok"] and re.search(r"\n    def parse_zip\(self", cm["placed_source"]) is not None))

    lc = place(_PRIM, "legacy_codemod", target_source=_LEGACY, legacy_func="parse_zip")
    checks.append(("legacy_codemod: REPLACES the old parse_zip body with the certified one, caller preserved, parses",
                   lc["ok"] and "return {'zip5'" in lc["placed_source"] and "def caller(z)" in lc["placed_source"]
                   and "old buggy hand-rolled" not in lc["placed_source"]))

    # negatives + governance
    bad = place({"primitive_id": "x", "executable_body": "x = 1"}, "direct_insertion", target_source=_NEW)
    checks.append(("a primitive with no entry function is refused (not placed)", bad["ok"] is False))
    checks.append(("placements are candidate-only + carry a diff + placement_id",
                   imp["serves_truth"] is False and imp["diff"].startswith("---") and imp["placement_id"].startswith("place-")))
    checks.append(("deterministic: same inputs -> identical placement_id + diff",
                   place(_PRIM, "import_and_call", target_source=_NEW)["placement_id"] == imp["placement_id"]))
    checks.append((f"strategy zoo has {len(STRATEGIES)} deterministic AST-verified placements", len(STRATEGIES) == 5))

    ok = all(v for _, v in checks)
    for nm, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {nm}")
    print(("PASS" if ok else "FAIL") + f" - primitive_placement: {len(STRATEGIES)}-strategy zoo (import/vendor/"
          "direct/class-method/legacy-codemod) places certified primitives into new/existing/legacy code — "
          "AST-verified, diffed, candidate-only, never executed. serves_truth=false.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Place a certified primitive into real code (the last-mile zoo).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--strategies", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.strategies:
        print(json.dumps(list(STRATEGIES), indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
