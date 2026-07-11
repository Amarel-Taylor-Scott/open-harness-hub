#!/usr/bin/env python3
"""scripts.pyprefix — typed, greppable Python identifiers for DETERMINISTIC code maps.

Encode each definition's KIND in its name so structural search needs no symbol resolver:

    class Cart            ->  class py_class_Cart
    def add(self, x)      ->      def py_method_add(self, x)
    def open_cart()       ->  def py_function_open_cart
    c = Cart()            ->      py_inst_cart = py_class_Cart()
    MAX_RETRIES = 5       ->  py_const_MAX_RETRIES = 5

Dunders (__init__, __repr__, ...) are exempt; underscores are preserved (_helper -> py_function__helper).

WHY. Resolving "what is this name?" in Python normally needs scope/type analysis. If the name SAYS what
it is, that analysis is free: grep is exact, codemaps are unambiguous, and deterministic graph tools get
a clean, typed symbol stream. This is the CONVENTION-based complement to _repos/shared-backend-components/scripts/codegraph.py (the AST
graph): codegraph PARSES to resolve; pyprefix makes the names self-describing so even grep resolves.

SCOPE + HONESTY. Read-only by default (check / map / find / stats / standard). The renaming codemod
(`apply`) is intentionally NOT implemented here as a blanket operation: retrofitting an entire production
tree of thousands of symbols is destructive and would break imports + the proof gate. The convention is
best adopted for NEW code (gated by `check`) or applied per-package with the test suite as the oracle.
Stdlib only.

CLI:
  pyprefix standard                  print the convention (single source of truth)
  pyprefix check  <path> [--strict]  conformance lint; exit 1 on violations (CI-ready, read-only)
  pyprefix map    <path> [--json f]  typed symbol map: each definition + its reference locations
  pyprefix find   <name> <path>      every definition + reference of a symbol (exact)
  pyprefix stats  <path>             conformance % + kind counts + most-referenced
  pyprefix --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])

# ---------------------------------------------------------------- the convention (one source of truth)
#: kind -> the required identifier prefix
PREFIX = {
    "class": "py_class_",
    "function": "py_function_",
    "method": "py_method_",
    "const": "py_const_",
    "instance": "py_inst_",
    "var": "py_var_",          # a module-level binding that is neither ALL-CAPS const nor an instantiation
    "arg": "py_arg_",
    "local": "py_local_",
}
#: dunders are never touched (they are protocol, not user names)
_DUNDER = re.compile(r"^__[A-Za-z0-9_]+__$")
#: a module-level NAME is a constant when it is ALL-CAPS (with digits/underscores)
_CONST = re.compile(r"^[A-Z][A-Z0-9_]*$")


def is_dunder(name: str) -> bool:
    return bool(_DUNDER.match(name))


def target_name(kind: str, name: str) -> str:
    """The conforming name for a definition of `kind` currently called `name` (idempotent)."""
    if is_dunder(name):
        return name
    pfx = PREFIX[kind]
    return name if name.startswith(pfx) else pfx + name


def conforms(kind: str, name: str) -> bool:
    """A definition conforms if it is a dunder OR already carries its kind's prefix."""
    return is_dunder(name) or name.startswith(PREFIX[kind])


def definition_conforms(definition: dict, file_path: str = "") -> bool:
    """Strict migration conformance: a definition must equal its location-derived qualified name."""
    name = definition["name"]
    if is_dunder(name):
        return True
    return name == qualified_name(definition["kind"], name, file_path, definition.get("scope", "<module>"))


def _slug(text: str) -> str:
    """A path / dotted string as an identifier-safe slug: every non-word char becomes a single _."""
    return re.sub(r"_{3,}", "__", re.sub(r"\W+", "_", text)).strip("_")


def qualified_name(kind: str, name: str, file_path: str = "", scope: str = "") -> str:
    """The GLOBALLY-UNIQUE, context-bearing name (owner law 2026-06-27): the original name prefixed by its
    KIND and its full location — FILE then enclosing class/method SCOPE — all concatenated:

        py_function_src__teleon__runtime__credentials__is_present
        py_method_shop__Cart__add
        py_var_shop__open_cart__total

    No hashes (they destroy the context an AI needs); the meaning lives in the name. File is the literal
    relative path (slashes -> __, '.py' dropped), so two same-named files never collide and we do not lean
    on Python's import resolution. Idempotent: a name already carrying its kind prefix is returned unchanged."""
    if is_dunder(name):
        return name
    pfx = PREFIX[kind]
    if name.startswith(pfx):
        return name
    parts: list[str] = []
    if file_path:
        # A backend staged under `_repos/<x>/backend/` keeps its CANONICAL `src/<x>/…` name — the relocation
        # must not rename thousands of symbols, and location-derived names must be STABLE across the move.
        # Strip the staging prefix so the name is identical before and after the move.
        _fp = file_path.split("/")
        if len(_fp) >= 3 and _fp[0] == "_repos" and _fp[2] == "backend":
            file_path = "/".join(_fp[3:])
        parts.append(_slug(file_path[:-3] if file_path.endswith(".py") else file_path))
    if scope and scope != "<module>":
        parts.append(_slug(scope))
    parts.append(name)
    return pfx + "__".join(parts)


# ---------------------------------------------------------------- AST analysis (defs, refs, imports, edges)
class _Analyzer(ast.NodeVisitor):
    """From one module collect: typed DEFINITIONS (position + enclosing scope), bare-NAME references,
    IMPORTS (for cross-file resolution), and structural EDGES — contains (class->method), calls
    (caller->callee), inherits (class->base). This is the structure pyprefix map could not express:
    relationships, not just a name index."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.defs: list[dict] = []        # {kind, name, line, col, scope}
        self.refs: list[dict] = []        # {name, line, col, scope}
        self.imports: list[dict] = []     # {module, name, asname, line}  (name=None for `import M`)
        self.edges: list[dict] = []       # {src, dst, type}  type in contains|calls|inherits
        self._scope: list[tuple[str, str]] = []   # stack of (kind, name)
        self._args_by_scope: dict[str, set[str]] = {}
        self._globals_by_scope: dict[str, set[str]] = {}

    def _qual(self) -> str:
        return ".".join(n for _, n in self._scope) or "<module>"

    def _enclosing_kind(self) -> str | None:
        return self._scope[-1][0] if self._scope else None

    def _is_function_scope(self) -> bool:
        return self._enclosing_kind() in {"function", "method"}

    def _binding_kind(self, name: str, value: ast.AST | None = None) -> str:
        is_ctor = isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id[:1].isupper()
        if (_CONST.match(name) or name.startswith("py_const_")) and not self._scope:
            return "const"
        if is_ctor:
            return "instance"
        if not self._scope or self._enclosing_kind() == "class":
            return "var"
        if self._is_function_scope() and name in self._args_by_scope.get(self._qual(), set()):
            return "arg"
        return "local"

    def _record_binding(self, target: ast.AST, value: ast.AST | None = None) -> None:
        if isinstance(target, ast.Name):
            if target.id in self._globals_by_scope.get(self._qual(), set()):
                return
            kind = self._binding_kind(target.id, value)
            if kind == "arg":
                return
            self.defs.append({"kind": kind, "name": target.id, "line": target.lineno,
                              "col": target.col_offset, "scope": self._qual()})
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._record_binding(elt, value)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for a in node.names:
            self.imports.append({"module": a.name, "name": None, "asname": a.asname or a.name, "line": node.lineno})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        mod = ("." * (node.level or 0)) + (node.module or "")
        for a in node.names:
            self.imports.append({"module": mod, "name": a.name, "asname": a.asname or a.name, "line": node.lineno})

    def visit_Global(self, node: ast.Global) -> None:  # noqa: N802
        self._globals_by_scope.setdefault(self._qual(), set()).update(node.names)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.defs.append({"kind": "class", "name": node.name, "line": node.lineno, "col": node.col_offset, "scope": self._qual()})
        if self._scope:
            self.edges.append({"src": self._qual(), "dst": node.name, "type": "contains"})
        for b in node.bases:
            base = b.id if isinstance(b, ast.Name) else (b.attr if isinstance(b, ast.Attribute) else None)
            if base:
                self.edges.append({"src": node.name, "dst": base, "type": "inherits"})
        self._scope.append(("class", node.name))
        self.generic_visit(node)
        self._scope.pop()

    def _func(self, node) -> None:
        kind = "method" if self._enclosing_kind() == "class" else "function"
        self.defs.append({"kind": kind, "name": node.name, "line": node.lineno, "col": node.col_offset, "scope": self._qual()})
        if self._scope:
            self.edges.append({"src": self._qual(), "dst": node.name, "type": "contains"})
        self._scope.append((kind, node.name))
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._func(node)

    def visit_arg(self, node: ast.arg) -> None:  # noqa: N802
        if node.arg not in {"self", "cls"}:
            self._args_by_scope.setdefault(self._qual(), set()).add(node.arg)
            self.defs.append({"kind": "arg", "name": node.arg, "line": node.lineno,
                              "col": node.col_offset, "scope": self._qual()})
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        for tgt in node.targets:
            self._record_binding(tgt, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        self._record_binding(node.target, node.value)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:  # noqa: N802
        self._record_binding(node.target, node.value)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # noqa: N802
        self._record_binding(node.target, None)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:  # noqa: N802
        self._record_binding(node.target, None)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:  # noqa: N802
        for item in node.items:
            if item.optional_vars is not None:
                self._record_binding(item.optional_vars, item.context_expr)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:  # noqa: N802
        for item in node.items:
            if item.optional_vars is not None:
                self._record_binding(item.optional_vars, item.context_expr)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        if node.name:
            self.defs.append({"kind": "local", "name": node.name, "line": node.lineno,
                              "col": node.col_offset, "scope": self._qual()})
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        callee = node.func.id if isinstance(node.func, ast.Name) else (node.func.attr if isinstance(node.func, ast.Attribute) else None)
        if callee:
            self.edges.append({"src": self._qual(), "dst": callee, "type": "calls"})
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, ast.Load):
            self.refs.append({"name": node.id, "line": node.lineno, "col": node.col_offset, "scope": self._qual()})
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: N802
        # Record `obj.attr` access as a reference to `attr`. Closes the cross-file-safety hole that broke
        # the repo-wide rename: a symbol read as `module.SYMBOL` now counts as a reference, so safe_targets
        # will not call it safe. Marked attr=True so the in-file codemod does NOT rewrite it (its col is the
        # object start, not the attr) — only bare-name refs are rewrite points.
        if isinstance(node.ctx, ast.Load):
            self.refs.append({"name": node.attr, "line": node.lineno, "col": node.col_offset, "scope": self._qual(), "attr": True})
        self.generic_visit(node)


def analyze_file(path: Path) -> dict:
    """Defs + refs + imports + structural edges for one file. Unparseable files degrade honestly."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return {"path": str(path), "defs": [], "refs": [], "imports": [], "edges": [], "error": f"{type(exc).__name__}: {exc}"}
    a = _Analyzer(str(path))
    a.visit(tree)
    return {"path": str(path), "defs": a.defs, "refs": a.refs, "imports": a.imports, "edges": a.edges, "error": None}


_EXCLUDE_PARTS = {
    ".agent",
    ".agents",
    ".claude",
    ".codex",
    ".git",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "_reference",
    "archive",
    "artifacts",
    "data",
    "dist",
    "node_modules",
    "site",
}

# When the repo root itself is requested, "repo-wide" means owned Python source, not vendored,
# generated, reference, data, or environment code. Explicit subdirectory targets still work.
_DEFAULT_SOURCE_ROOTS = (
    "scripts",
    "src",
    "tools",
    "hf-space",
    "templates",
    "code-templates",
)


def _excluded_path(path: Path) -> bool:
    return any(part in _EXCLUDE_PARTS for part in path.parts)


def _repo_root_requested(root: Path) -> bool:
    try:
        return root.resolve() == REPO_ROOT.resolve()
    except FileNotFoundError:
        return False


def _py_files(root: Path) -> list[Path]:
    if root.is_file():
        return [] if _excluded_path(root) else [root]
    if _repo_root_requested(root):
        # At the REAL monorepo root (has the .aidoneright-root marker) the old top-level source dirs moved
        # under _repos/, so resolve their real homes via _resource. When REPO_ROOT is OVERRIDDEN (tests point
        # it at a temp tree with no marker), scan that tree directly so a nonexistent root contributes nothing.
        if (root / ".aidoneright-root").exists():
            roots = [_resource(r) for r in _DEFAULT_SOURCE_ROOTS]
        else:
            roots = [root / r for r in _DEFAULT_SOURCE_ROOTS]
        roots += sorted((root / "_repos").glob("*/backend/src")) + sorted((root / "_repos").glob("*/scripts"))
    else:
        roots = [root]
    files: list[Path] = []
    for base in roots:
        if not base.exists() or _excluded_path(base):
            continue
        files.extend(p for p in base.rglob("*.py") if not _excluded_path(p))
    return sorted(set(files))


# ---------------------------------------------------------------- check (conformance lint, read-only)
#: entry-point names that must NOT be renamed — the module's external contract (the proof gate,
#: the CLI, and test runners call these by name). Extend per-package via --exempt as needed.
ENTRY_EXEMPT = {"main", "_self_test", "setup", "teardown", "setUp", "tearDown"}

# Keyword-only runtime/context injection names are often called through dynamic callback registries
# (`handler(payload, now=...)`, `step(input, context=...)`) where the callable is stored in a table and
# invoked through a variable. Static keyword-call indexing cannot prove those links, so safe-arg migration
# must leave them alone unless a coordinated contract codemod handles the registry and every caller.
RESERVED_RUNTIME_KEYWORD_ARGS = {"now", "context", "ctx"}


def check_path(root: Path, exempt: set | None = None) -> list[dict]:
    """Every non-conforming definition with its location + the target name it should carry.

    `exempt` adds names that are intentionally left alone (beyond dunders) — e.g. entry points the
    gate/CLI call by name. Functions/classes/constants are checked unconditionally; methods/instances
    too (the convention covers them) — but see codemod_file for the SAFE rename scope."""
    skip = ENTRY_EXEMPT | (exempt or set())
    violations: list[dict] = []
    for f in _py_files(root):
        info = analyze_file(f)
        rel = _repo_rel(f)
        for d in info["defs"]:
            if d["name"] in skip or is_dunder(d["name"]):
                continue
            expected = qualified_name(d["kind"], d["name"], rel, d.get("scope", "<module>"))
            if d["name"] != expected:
                violations.append({"path": info["path"], "line": d["line"], "kind": d["kind"],
                                   "name": d["name"], "target": expected})
    return violations


# ---------------------------------------------------------------- apply (the codemod: rename + verify + rollback)
#: SAFE rename kinds for the position-guided in-file codemod. Functions / classes / constants are
#: referenced by BARE NAME (ast.Name), which is exactly resolvable in-file. Methods + instances are
#: referenced as ATTRIBUTES (obj.method) which static analysis cannot resolve across duck-typed
#: receivers — they are deferred to the cross-file phase (see the migration doc). compile()-verify
#: guarantees SYNTACTIC safety; it does NOT guarantee a cross-file caller was updated, so the
#: migration protocol is: apply per file/package, then run the full proof gate as the oracle.
_SAFE_KINDS = ("function", "class", "const", "var")


def _rename_map(defs: list[dict], exempt: set, kinds: tuple, file_path: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for d in defs:
        if d["kind"] not in kinds or is_dunder(d["name"]) or d["name"] in exempt:
            continue
        if not conforms(d["kind"], d["name"]):
            # location-derived global-unique name (owner law): py_<kind>_<file>__<scope>__<name>
            out[d["name"]] = qualified_name(d["kind"], d["name"], file_path, d.get("scope", "<module>"))
    return out


def _repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def codemod_file(path: Path, exempt: set | None = None, kinds: tuple = _SAFE_KINDS,
                 only: set | None = None) -> dict:
    """Rename non-conforming definitions of `kinds` + their in-file bare-name references, by exact
    position (formatting / comments / strings untouched), then compile()-verify and ROLL BACK if the
    result would not parse. Can never leave broken syntax. If `only` is given, rename ONLY those names
    (used to migrate just the cross-file-SAFE symbols a package at a time)."""
    skip = ENTRY_EXEMPT | (exempt or set())
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except (SyntaxError, UnicodeDecodeError) as exc:
        return {"path": str(path), "renamed": 0, "ok": False, "reason": f"unparseable: {exc}"}
    a = _Analyzer(str(path))
    a.visit(tree)
    rmap = _rename_map(a.defs, skip, kinds, _repo_rel(path))
    if only is not None:
        rmap = {k: v for k, v in rmap.items() if k in only}
    if not rmap:
        return {"path": str(path), "renamed": 0, "ok": True, "reason": "already conformant"}
    lines = src.split("\n")
    edits: list[tuple[int, int, str, str]] = []   # (line_idx, col, old, new)
    for d in a.defs:                              # the definition's NAME position
        if d["name"] not in rmap:
            continue
        li = d["line"] - 1
        if d["kind"] in ("function", "class"):
            m = re.search(r"\b(?:class|def)\s+(" + re.escape(d["name"]) + r")\b", lines[li])
            if m:
                edits.append((li, m.start(1), d["name"], rmap[d["name"]]))
        else:                                    # const target: col is the Name target itself
            edits.append((li, d["col"], d["name"], rmap[d["name"]]))
    for r in a.refs:                             # every bare-name reference (NOT attribute access)
        if r["name"] in rmap and not r.get("attr"):
            edits.append((r["line"] - 1, r["col"], r["name"], rmap[r["name"]]))
    for li, col, old, new in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        ln = lines[li]
        if ln[col:col + len(old)] == old:        # position-guard: only rewrite an exact token match
            lines[li] = ln[:col] + new + ln[col + len(old):]
    out = "\n".join(lines)
    try:
        compile(out, str(path), "exec")
    except SyntaxError as exc:
        return {"path": str(path), "renamed": 0, "ok": False, "reason": f"compile failed, rolled back: {exc}"}
    path.write_text(out, encoding="utf-8")
    return {"path": str(path), "renamed": len(rmap), "ok": True, "reason": "applied", "names": rmap}


# ---------------------------------------------------------------- map (typed symbol index)
def build_map(root: Path) -> dict:
    """A typed symbol map: each definition (kind + location) and the locations that reference its name.

    Reference resolution is NAME-based (the whole point: typed names make a name an exact key). For a
    repo that has NOT adopted the convention this is still a useful greppable index; once names are typed
    it is unambiguous."""
    files = [analyze_file(f) for f in _py_files(root)]
    # index references by bare name across the tree
    refs_by_name: dict[str, list[dict]] = {}
    for info in files:
        for r in info["refs"]:
            refs_by_name.setdefault(r["name"], []).append({"path": info["path"], "line": r["line"]})
    symbols: list[dict] = []
    for info in files:
        rel = _repo_rel(Path(info["path"]))
        for d in info["defs"]:
            refs = [r for r in refs_by_name.get(d["name"], []) if not (r["path"] == info["path"] and r["line"] == d["line"])]
            symbols.append({"name": d["name"], "kind": d["kind"], "conforms": d["name"] == qualified_name(d["kind"], d["name"], rel, d.get("scope", "<module>")),
                            "def": {"path": info["path"], "line": d["line"]}, "refs": refs, "ref_count": len(refs)})
    return {"root": str(root), "symbols": symbols, "files": len(files),
            "errors": [info["path"] for info in files if info["error"]]}


# ---------------------------------------------------------------- project graph (cross-file structure)
def _module_name(path: Path, root: Path) -> str:
    """Dotted module name relative to the root (the import path)."""
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = Path(path.name)
    return ".".join(rel.with_suffix("").parts)


def build_project(root: Path) -> dict:
    """Analyze every file once; index per module its analysis + the SET of every identifier it mentions
    (def names, references, import names/aliases, edge targets). The name set is what makes cross-file
    safety SOUND: a symbol is safe to rename in-file iff its name appears in no OTHER module."""
    files = _py_files(root)
    modules: dict[str, dict] = {}
    all_names: dict[str, set] = {}
    for f in files:
        info = analyze_file(f)
        mod = _module_name(f, root if root.is_dir() else root.parent)
        info["module"] = mod
        modules[mod] = info
        names = {d["name"] for d in info["defs"]} | {r["name"] for r in info["refs"]}
        names |= {i["asname"] for i in info["imports"]} | {i["name"] for i in info["imports"] if i["name"]}
        names |= {e["dst"] for e in info["edges"]}
        all_names[mod] = names
    return {"root": str(root), "modules": modules, "all_names": all_names, "files": len(files)}


def safe_targets(target: Path, repo_root: Path) -> list[dict]:
    """Module-level definitions IN `target` whose name appears in NO OTHER module across `repo_root` —
    SOUND (conservative) targets for the in-file codemod: renaming them cannot break a cross-file caller.
    Only the non-conforming safe kinds (function/class/const) are proposed."""
    repo = build_project(repo_root)
    tgt_paths = {str(p.resolve()) for p in _py_files(target)}
    out: list[dict] = []
    for mod, info in repo["modules"].items():
        if str(Path(info["path"]).resolve()) not in tgt_paths:
            continue
        others = set().union(*[ns for m, ns in repo["all_names"].items() if m != mod]) if len(repo["all_names"]) > 1 else set()
        for d in info["defs"]:
            if (d["kind"] in _SAFE_KINDS and d.get("scope", "<module>") == "<module>"
                    and not is_dunder(d["name"]) and d["name"] not in ENTRY_EXEMPT
                    and not conforms(d["kind"], d["name"]) and d["name"] not in others):
                out.append({"module": mod, "name": d["name"], "kind": d["kind"], "path": info["path"],
                            "line": d["line"], "target": qualified_name(d["kind"], d["name"], _repo_rel(Path(info["path"])), d.get("scope", "<module>"))})
    return out


def migrate_safe(target: Path, repo_root: Path) -> list[dict]:
    """Rename ONLY the cross-file-safe symbols in `target` (from safe_targets), one file at a time, each
    compile-verified + rollback-safe. This is how the migration advances a package at a time without
    breaking importers. The full proof gate is the final oracle — run it after, and revert if red."""
    by_file: dict[str, set] = {}
    for t in safe_targets(target, repo_root):
        by_file.setdefault(t["path"], set()).add(t["name"])
    return [codemod_file(Path(p), only=names) for p, names in sorted(by_file.items())]


# --------------------------------------------------- cross-file rename (rewrite importers, gate-as-oracle)
def _resolve_import_module(module_str: str, file_module: str) -> str:
    """Resolve an import's module string to a full dotted module name, handling relative imports."""
    if not module_str.startswith("."):
        return module_str
    dots = len(module_str) - len(module_str.lstrip("."))
    base = file_module.split(".")
    parent = base[:-dots] if dots <= len(base) else []
    rest = module_str.lstrip(".")
    return ".".join(parent + ([rest] if rest else []))


def globally_unique_targets(target: Path, repo_root: Path) -> dict:
    """Non-conforming safe-kind module-level defs IN `target` whose name is defined in EXACTLY ONE module
    repo-wide (so a reference to the name is unambiguous). Returns {(module, name): newname}."""
    repo = build_project(repo_root)
    def_mods: dict[str, set] = {}
    for mod, info in repo["modules"].items():
        for d in info["defs"]:
            if d.get("scope", "<module>") == "<module>":
                def_mods.setdefault(d["name"], set()).add(mod)
    tgt = {str(p.resolve()) for p in _py_files(target)}
    out: dict = {}
    for mod, info in repo["modules"].items():
        if str(Path(info["path"]).resolve()) not in tgt:
            continue
        for d in info["defs"]:
            if (d["kind"] in _SAFE_KINDS and d.get("scope", "<module>") == "<module>"
                    and not is_dunder(d["name"]) and d["name"] not in ENTRY_EXEMPT
                    and not conforms(d["kind"], d["name"]) and len(def_mods.get(d["name"], set())) == 1):
                out[(mod, d["name"])] = qualified_name(d["kind"], d["name"], _repo_rel(Path(info["path"])), d.get("scope", "<module>"))
    return out


def module_scope_targets(target: Path, repo_root: Path) -> dict:
    """Every non-conforming module-scope safe-kind definition in target, keyed by its actual module.

    Unlike globally_unique_targets, this does NOT require the bare name to be unique repo-wide. The rename
    is still deterministic because cross_file_rename resolves by defining module/import edge, not by a
    global bare-name namespace. This handles common private module constants like _REPO repeated in many
    files without pretending they are the same symbol.
    """
    repo = build_project(repo_root)
    tgt = {str(p.resolve()) for p in _py_files(target)}
    out: dict = {}
    for mod, info in repo["modules"].items():
        if str(Path(info["path"]).resolve()) not in tgt:
            continue
        for d in info["defs"]:
            if (d["kind"] in _SAFE_KINDS and d.get("scope", "<module>") == "<module>"
                    and not is_dunder(d["name"]) and d["name"] not in ENTRY_EXEMPT
                    and not definition_conforms(d, _repo_rel(Path(info["path"])))):
                out[(mod, d["name"])] = qualified_name(d["kind"], d["name"], _repo_rel(Path(info["path"])), d.get("scope", "<module>"))
    return out


def _module_imports_and_all(info: dict, module: str) -> tuple[dict[str, tuple[str, str]], set[str]]:
    """Return ({local_name: (source_module, source_name)}, __all__ string names) for a module."""
    path = Path(info["path"])
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return {}, set()
    imported: dict[str, tuple[str, str]] = {}
    exported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            rm = _resolve_import_module(("." * (node.level or 0)) + (node.module or ""), module)
            for alias in node.names:
                imported[alias.asname or alias.name] = (rm, alias.name)
        elif isinstance(node, ast.Assign):
            if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                continue
            if isinstance(node.value, (ast.List, ast.Tuple)):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        exported.add(elt.value)
    return imported, exported


def _with_facade_reexports(repo: dict, renames: dict) -> dict:
    """Extend renames through explicit re-export facades.

    If module F does `from M import X` and `__all__ = ["X"]`, and (M, X) is being renamed, then
    consumers of F.X must be rewritten too. This returns a fixed point containing (F, X) -> new_name.
    """
    out = dict(renames)
    changed = True
    while changed:
        changed = False
        for mod, info in repo["modules"].items():
            imported, exported = _module_imports_and_all(info, mod)
            for local, source in imported.items():
                if local in exported and source in out and (mod, local) not in out:
                    out[(mod, local)] = out[source]
                    changed = True
    return out


def _string_constant_edit(lines: list[str], node: ast.Constant, old: str, new: str) -> tuple[int, int, str, str] | None:
    """Exact-position edit for a string constant's content, preserving quote style/prefix."""
    if not isinstance(node.value, str):
        return None
    li = node.lineno - 1
    start = node.col_offset
    end = getattr(node, "end_col_offset", None) or len(lines[li])
    segment = lines[li][start:end]
    pos = segment.find(old)
    if pos < 0:
        return None
    return (li, start + pos, old, new)


def _identifier_token_col(line: str, name: str, start: int = 0) -> int:
    """Find `name` as a full Python identifier token, not as a substring of another identifier.

    This prevents `catalog` from matching the `catalog` suffix inside `all_catalogs` when rewriting
    multi-import lines like `from .port import all_catalogs, catalog`.
    """
    ident = r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])"
    for m in re.finditer(ident, line):
        if m.start() >= start:
            return m.start()
    return -1


def cross_file_rename(repo_root: Path, renames: dict, dry_run: bool = False) -> list[dict]:
    """Rewrite a def + ALL its references across the repo for `renames` ({(module, name): newname}):
    the def, in-file bare refs, `from M import name` import statements + the bare refs they bind, and
    qualified `M.name` / `alias.name` attribute access. Per file: compile()-verify + ROLLBACK. The proof
    gate is the final oracle (static analysis can't see dynamic getattr/strings). If `dry_run` is true,
    every edit is planned and compile-checked but not written."""
    proj = build_project(repo_root)
    renames = _with_facade_reexports(proj, renames)
    results: list[dict] = []
    for mod, info in proj["modules"].items():
        path = Path(info["path"])
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError):
            continue
        lines = src.split("\n")
        edits: list[tuple[int, int, str, str]] = []
        fromimp: dict[str, tuple[str, str]] = {}    # local -> (module, orig)
        modalias: dict[str, str] = {}               # local -> module
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                rm = _resolve_import_module(("." * (node.level or 0)) + (node.module or ""), mod)
                for a in node.names:
                    fromimp[a.asname or a.name] = (rm, a.name)
                    modalias[a.asname or a.name] = rm + "." + a.name   # `from PKG import MOD` submodule
                    if (rm, a.name) in renames:
                        li = (getattr(a, "lineno", None) or node.lineno) - 1
                        col = _identifier_token_col(lines[li], a.name, node.col_offset)
                        if col >= 0:
                            edits.append((li, col, a.name, renames[(rm, a.name)]))
            elif isinstance(node, ast.Import):
                for a in node.names:
                    modalias[a.asname or a.name] = a.name
            elif isinstance(node, ast.Assign):
                if not any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                    continue
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
                            continue
                        local = elt.value
                        target = None
                        if (mod, local) in renames:
                            target = renames[(mod, local)]
                        elif local in fromimp and fromimp[local] in renames:
                            target = renames[fromimp[local]]
                        if target:
                            edit = _string_constant_edit(lines, elt, local, target)
                            if edit:
                                edits.append(edit)
        for d in info["defs"]:                       # defs renamed in their own module
            if d.get("scope", "<module>") == "<module>" and (mod, d["name"]) in renames:
                if d["kind"] in ("function", "class"):
                    m = re.search(r"\b(?:class|def)\s+(" + re.escape(d["name"]) + r")\b", lines[d["line"] - 1])
                    if m:
                        edits.append((d["line"] - 1, m.start(1), d["name"], renames[(mod, d["name"])]))
                else:
                    edits.append((d["line"] - 1, d["col"], d["name"], renames[(mod, d["name"])]))
        for node in ast.walk(tree):                  # references
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Load, ast.Store)):
                nm = node.id
                if (mod, nm) in renames:
                    edits.append((node.lineno - 1, node.col_offset, nm, renames[(mod, nm)]))
                elif nm in fromimp and nm == fromimp[nm][1] and fromimp[nm] in renames:
                    edits.append((node.lineno - 1, node.col_offset, nm, renames[fromimp[nm]]))
            elif isinstance(node, ast.Global):
                for nm in node.names:
                    if (mod, nm) in renames:
                        li = node.lineno - 1
                        col = _identifier_token_col(lines[li], nm, node.col_offset)
                        if col >= 0:
                            edits.append((li, col, nm, renames[(mod, nm)]))
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                tgtmod = modalias.get(node.value.id)
                if tgtmod and (tgtmod, node.attr) in renames and getattr(node.value, "end_col_offset", None) is not None:
                    edits.append((node.lineno - 1, node.value.end_col_offset + 1, node.attr, renames[(tgtmod, node.attr)]))
        uniq, seen = [], set()
        for e in edits:
            if e[:2] not in seen:
                seen.add(e[:2])
                uniq.append(e)
        if not uniq:
            continue
        for li, col, old, new in sorted(uniq, key=lambda x: (x[0], x[1]), reverse=True):
            if lines[li][col:col + len(old)] == old:
                lines[li] = lines[li][:col] + new + lines[li][col + len(old):]
        out = "\n".join(lines)
        try:
            compile(out, str(path), "exec")
        except SyntaxError as exc:
            results.append({"path": str(path), "renamed": 0, "ok": False, "reason": f"rolled back: {exc}"})
            continue
        if not dry_run:
            path.write_text(out, encoding="utf-8")
        results.append({"path": str(path), "renamed": len(uniq), "ok": True, "dry_run": dry_run})
    return results


def migrate_package(target: Path, repo_root: Path, dry_run: bool = False) -> dict:
    """Migrate a package toward 100% conformance: rename every globally-unique non-conforming safe symbol
    in `target` AND rewrite its references repo-wide (cross_file_rename). Run the proof gate after; revert
    (git checkout) if red. Returns {renames, files_changed, failures}."""
    renames = globally_unique_targets(target, repo_root)
    res = cross_file_rename(repo_root, renames, dry_run=dry_run)
    return {"renames": len(renames), "dry_run": dry_run, "targets": [
                {"module": mod, "name": name, "target": new} for (mod, name), new in sorted(renames.items())
            ],
            "files_changed": [r for r in res if r.get("renamed")],
            "failures": [r for r in res if not r["ok"]]}


def migrate_module_scope(target: Path, repo_root: Path, dry_run: bool = False) -> dict:
    """Migrate all remaining module-scope safe-kind definitions in target by resolved module edges."""
    renames = module_scope_targets(target, repo_root)
    res = cross_file_rename(repo_root, renames, dry_run=dry_run)
    return {"renames": len(renames), "dry_run": dry_run, "targets": [
                {"module": mod, "name": name, "target": new} for (mod, name), new in sorted(renames.items())
            ],
            "files_changed": [r for r in res if r.get("renamed")],
            "failures": [r for r in res if not r["ok"]]}


def _scoped_rename_map(path: Path, kinds: set[str], exempt: set | None = None,
                       only: set[tuple[str, str]] | None = None) -> dict[tuple[str, str], str]:
    """Scoped definition map for intra-file names keyed by (scope, old_name)."""
    skip = ENTRY_EXEMPT | (exempt or set())
    info = analyze_file(path)
    rel = _repo_rel(path)
    arg_bindings = {(d.get("scope", "<module>"), d["name"]) for d in info["defs"] if d["kind"] == "arg"}
    out: dict[tuple[str, str], str] = {}
    for d in info["defs"]:
        name = d["name"]
        if d["kind"] not in kinds or name in skip or is_dunder(name):
            continue
        if only is not None and (d.get("scope", "<module>"), name) not in only:
            continue
        if d["kind"] == "local" and (d.get("scope", "<module>"), name) in arg_bindings and "arg" not in kinds:
            continue
        target = qualified_name(d["kind"], name, rel, d.get("scope", "<module>"))
        if name != target:
            out[(d.get("scope", "<module>"), name)] = target
    return out


class _ScopedNamePlanner(ast.NodeVisitor):
    """Plan exact-position edits for scoped names, resolving loads through enclosing scopes."""

    def __init__(self, rename_map: dict[tuple[str, str], str], include_args: bool,
                 shadowed_by_scope: dict[str, set[str]]) -> None:
        self.rename_map = rename_map
        self.include_args = include_args
        self.shadowed_by_scope = shadowed_by_scope
        self.edits: list[tuple[int, int, str, str]] = []
        self._scope: list[str] = []
        self._global_stack: list[set[str]] = []

    def _qual(self) -> str:
        return ".".join(self._scope) or "<module>"

    def _scope_candidates(self) -> list[str]:
        return [".".join(self._scope[:i]) or "<module>" for i in range(len(self._scope), -1, -1)]

    def _resolve(self, name: str) -> str | None:
        if self._global_stack and name in self._global_stack[-1]:
            return None
        for scope in self._scope_candidates():
            target = self.rename_map.get((scope, name))
            if target:
                return target
            if name in self.shadowed_by_scope.get(scope, set()):
                return None
        return None

    def _edit(self, node: ast.AST, old: str, new: str) -> None:
        self.edits.append((node.lineno - 1, node.col_offset, old, new))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        target = self.rename_map.get((self._qual(), node.name))
        if target:
            self._edit(node, node.name, target)
        self._scope.append(node.name)
        self._global_stack.append(set())
        self.generic_visit(node)
        self._global_stack.pop()
        self._scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_Global(self, node: ast.Global) -> None:  # noqa: N802
        if self._global_stack:
            self._global_stack[-1].update(node.names)

    def visit_arg(self, node: ast.arg) -> None:  # noqa: N802
        if self.include_args:
            target = self.rename_map.get((self._qual(), node.arg))
            if target:
                self._edit(node, node.arg, target)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)):
            target = self._resolve(node.id)
            if target:
                self._edit(node, node.id, target)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        if node.name:
            target = self.rename_map.get((self._qual(), node.name))
            if target:
                self.edits.append((node.lineno - 1, -1, node.name, target))
        self.generic_visit(node)


def codemod_scoped_file(path: Path, kinds: set[str], exempt: set | None = None,
                        dry_run: bool = False, only: set[tuple[str, str]] | None = None) -> dict:
    """Rename intra-file scoped names (currently safest for locals; args are opt-in).

    The planner resolves loads through enclosing scopes so closure reads of renamed outer locals are updated.
    It compile-verifies before writing, but the full proof gate remains the runtime oracle.
    """
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return {"path": str(path), "renamed": 0, "ok": False, "reason": f"unparseable: {exc}"}
    info = analyze_file(path)
    rmap = _scoped_rename_map(path, kinds, exempt=exempt, only=only)
    if not rmap:
        return {"path": str(path), "renamed": 0, "ok": True, "reason": "already conformant", "dry_run": dry_run}
    shadowed_by_scope: dict[str, set[str]] = {}
    for d in info["defs"]:
        if (d.get("scope", "<module>"), d["name"]) not in rmap:
            shadowed_by_scope.setdefault(d.get("scope", "<module>"), set()).add(d["name"])
    planner = _ScopedNamePlanner(rmap, include_args="arg" in kinds, shadowed_by_scope=shadowed_by_scope)
    planner.visit(tree)
    lines = src.split("\n")
    applied = 0
    skipped = 0
    for li, col, old, new in sorted(set(planner.edits), key=lambda e: (e[0], e[1]), reverse=True):
        if lines[li][col:col + len(old)] == old:
            lines[li] = lines[li][:col] + new + lines[li][col + len(old):]
            applied += 1
            continue
        matches = list(re.finditer(r"\b" + re.escape(old) + r"\b", lines[li]))
        if len(matches) == 1:
            m = matches[0]
            lines[li] = lines[li][:m.start()] + new + lines[li][m.end():]
            applied += 1
            continue
        if len(matches) > 1 and col >= 0:
            # Python's AST gives approximate columns for repeated names inside f-strings. Pick the
            # nearest token on the same line so repeated formatted values are still deterministic.
            m = min(matches, key=lambda match: abs(match.start() - col))
            lines[li] = lines[li][:m.start()] + new + lines[li][m.end():]
            applied += 1
            continue
        skipped += 1
    if skipped:
        return {"path": str(path), "renamed": 0, "tokens": applied, "ok": False,
                "reason": f"{skipped} planned token edit(s) could not be applied exactly; rolled back",
                "dry_run": dry_run}
    out = "\n".join(lines)
    try:
        compile(out, str(path), "exec")
    except SyntaxError as exc:
        return {"path": str(path), "renamed": 0, "ok": False, "reason": f"compile failed, rolled back: {exc}"}
    if not dry_run:
        path.write_text(out, encoding="utf-8")
    return {"path": str(path), "renamed": len(rmap), "tokens": applied, "ok": True, "reason": "applied",
            "dry_run": dry_run}


def migrate_scoped(target: Path, kinds: set[str], dry_run: bool = False) -> dict:
    """Run scoped intra-file renames across a target path."""
    res = [codemod_scoped_file(f, kinds=kinds, dry_run=dry_run) for f in _py_files(target)]
    return {"kinds": sorted(kinds), "dry_run": dry_run, "files_changed": [r for r in res if r.get("tokens")],
            "failures": [r for r in res if not r["ok"]]}


def migrate_safe_args(target: Path, repo_root: Path, dry_run: bool = False) -> dict:
    """Rename only args whose arg-report says no visible keyword-call risk exists."""
    report = arg_safety_report(target, repo_root)
    by_file: dict[str, set[tuple[str, str]]] = {}
    for row in report["args"]:
        if not row["conforms"] and row["keyword_safe"]:
            by_file.setdefault(row["path"], set()).add((row["scope"], row["name"]))
    res = [codemod_scoped_file(Path(path), kinds={"arg"}, dry_run=dry_run, only=only)
           for path, only in sorted(by_file.items())]
    return {"dry_run": dry_run, "candidate_args": sum(len(v) for v in by_file.values()),
            "files_changed": [r for r in res if r.get("tokens")],
            "failures": [r for r in res if not r["ok"]]}


def _call_keyword_index(repo_root: Path) -> dict[tuple[str, str], list[dict]]:
    """Index visible keyword calls by (callee_simple_name, keyword_name)."""
    out: dict[tuple[str, str], list[dict]] = {}
    for f in _py_files(repo_root):
        src = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            callee = None
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
            if not callee:
                continue
            for kw in node.keywords:
                key = kw.arg if kw.arg is not None else "**"
                out.setdefault((callee, key), []).append({"path": str(f), "line": node.lineno})
    return out


def arg_safety_report(target: Path, repo_root: Path) -> dict:
    """Conservative report for parameter migration.

    An arg is `keyword_safe` only when no visible call to the owning function/method uses that arg as a
    keyword and no visible **kwargs call targets the owning function/method name. This may skip safe args,
    but it avoids silent keyword-call breakage.
    """
    keyword_index = _call_keyword_index(repo_root)
    rows: list[dict] = []
    for info in [analyze_file(f) for f in _py_files(target)]:
        rel = _repo_rel(Path(info["path"]))
        for d in info["defs"]:
            if d["kind"] != "arg" or d["name"] in {"self", "cls"} or is_dunder(d["name"]):
                continue
            scope = d.get("scope", "<module>")
            owner = scope.split(".")[-1] if scope != "<module>" else "<module>"
            keyword_refs = keyword_index.get((owner, d["name"]), [])
            dynamic_refs = keyword_index.get((owner, "**"), [])
            reserved_runtime_keyword = d["name"] in RESERVED_RUNTIME_KEYWORD_ARGS
            expected = qualified_name("arg", d["name"], rel, scope)
            rows.append({
                "path": info["path"],
                "line": d["line"],
                "scope": scope,
                "owner": owner,
                "name": d["name"],
                "target": expected,
                "conforms": d["name"] == expected,
                "keyword_refs": len(keyword_refs),
                "dynamic_kwargs_refs": len(dynamic_refs),
                "reserved_runtime_keyword": reserved_runtime_keyword,
                "keyword_safe": not keyword_refs and not dynamic_refs and not reserved_runtime_keyword,
                "sample_keyword_refs": keyword_refs[:5],
            })
    return {"root": str(target), "counts": {
                "args": len(rows),
                "nonconforming": sum(1 for r in rows if not r["conforms"]),
                "keyword_safe": sum(1 for r in rows if not r["conforms"] and r["keyword_safe"]),
                "keyword_risky": sum(1 for r in rows if not r["conforms"] and not r["keyword_safe"]),
            }, "args": rows}


def _expr_name(node: ast.AST) -> str | None:
    """Best-effort dotted/simple name for decorators, bases, and callees."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _expr_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    return None


class _ClassMetadata(ast.NodeVisitor):
    """Collect class decorators/bases using the same scope shape as _Analyzer."""

    def __init__(self) -> None:
        self._scope: list[str] = []
        self.classes: dict[str, dict] = {}

    def _qual(self, name: str) -> str:
        return ".".join(self._scope + [name])

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        qual = self._qual(node.name)
        self.classes[qual] = {
            "name": node.name,
            "decorators": [_expr_name(d) for d in node.decorator_list if _expr_name(d)],
            "bases": [_expr_name(b) for b in node.bases if _expr_name(b)],
            "line": node.lineno,
        }
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()


def _class_metadata(path: Path) -> dict[str, dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return {}
    meta = _ClassMetadata()
    meta.visit(tree)
    return meta.classes


def _contract_ref_indexes(repo_root: Path) -> dict:
    """Index references that make method/field renames observable contracts.

    Attribute references catch `obj.name`; dynamic refs catch `getattr(obj, "name")` /
    `setattr` / `hasattr`; string refs catch likely serialization/schema keys. These are
    intentionally conservative: a false positive delays a rename, a false negative breaks runtime.
    """
    attr_refs: dict[str, list[dict]] = {}
    dynamic_refs: dict[str, list[dict]] = {}
    string_refs: dict[str, list[dict]] = {}
    for f in _py_files(repo_root):
        src = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                attr_refs.setdefault(node.attr, []).append({"path": str(f), "line": node.lineno})
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", node.value):
                    string_refs.setdefault(node.value, []).append({"path": str(f), "line": getattr(node, "lineno", 0)})
            elif isinstance(node, ast.Call):
                callee = _expr_name(node.func)
                if callee in {"getattr", "setattr", "hasattr", "builtins.getattr", "builtins.setattr", "builtins.hasattr"}:
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                        dynamic_refs.setdefault(node.args[1].value, []).append({"path": str(f), "line": node.lineno, "callee": callee})
    return {"attr_refs": attr_refs, "dynamic_refs": dynamic_refs, "string_refs": string_refs}


def contract_risk_report(target: Path, repo_root: Path) -> dict:
    """Read-only risk report for the remaining high-contract symbols.

    Methods and class/body vars are not renamed by the safe codemods because their names frequently form
    protocols, dataclass fields, constructor keywords, JSON/dict keys, or dynamic getattr contracts. This
    report makes those risks explicit before a coordinated interface rename is attempted.
    """
    indexes = _contract_ref_indexes(repo_root)
    keyword_index = _call_keyword_index(repo_root)
    repo_infos = [analyze_file(f) for f in _py_files(repo_root)]
    method_defs_by_name: dict[str, list[dict]] = {}
    class_var_defs_by_name: dict[str, list[dict]] = {}
    for info in repo_infos:
        for d in info["defs"]:
            row = {"path": info["path"], "line": d["line"], "scope": d.get("scope", "<module>")}
            if d["kind"] == "method":
                method_defs_by_name.setdefault(d["name"], []).append(row)
            elif d["kind"] == "var" and d.get("scope", "<module>") != "<module>":
                class_var_defs_by_name.setdefault(d["name"], []).append(row)

    method_rows: list[dict] = []
    field_rows: list[dict] = []
    for info in [analyze_file(f) for f in _py_files(target)]:
        path = Path(info["path"])
        rel = _repo_rel(path)
        class_meta = _class_metadata(path)
        for d in info["defs"]:
            name = d["name"]
            scope = d.get("scope", "<module>")
            if is_dunder(name):
                continue
            if d["kind"] == "method" and not definition_conforms(d, rel):
                attr_refs = indexes["attr_refs"].get(name, [])
                dynamic_refs = indexes["dynamic_refs"].get(name, [])
                same_name_defs = method_defs_by_name.get(name, [])
                reasons: list[str] = []
                if not name.startswith("_"):
                    reasons.append("public_method")
                if len(same_name_defs) > 1:
                    reasons.append(f"shared_method_name:{len(same_name_defs)}")
                if attr_refs:
                    reasons.append(f"attribute_refs:{len(attr_refs)}")
                if dynamic_refs:
                    reasons.append(f"dynamic_string_refs:{len(dynamic_refs)}")
                candidate_safe = name.startswith("_") and len(same_name_defs) == 1 and not attr_refs and not dynamic_refs
                method_rows.append({
                    "path": info["path"], "line": d["line"], "scope": scope, "name": name,
                    "target": qualified_name("method", name, rel, scope),
                    "candidate_safe": candidate_safe,
                    "reasons": reasons,
                    "attribute_refs": len(attr_refs),
                    "dynamic_refs": len(dynamic_refs),
                    "same_name_method_defs": len(same_name_defs),
                    "sample_refs": (attr_refs + dynamic_refs)[:6],
                })
            elif d["kind"] == "var" and scope != "<module>" and not definition_conforms(d, rel):
                class_name = scope.split(".")[-1]
                meta = class_meta.get(scope, {})
                decorators = meta.get("decorators", [])
                attr_refs = indexes["attr_refs"].get(name, [])
                string_refs = indexes["string_refs"].get(name, [])
                keyword_refs = keyword_index.get((class_name, name), [])
                same_name_defs = class_var_defs_by_name.get(name, [])
                dataclass_field = any(dec == "dataclass" or dec.endswith(".dataclass") for dec in decorators)
                reasons: list[str] = []
                if dataclass_field:
                    reasons.append("dataclass_or_struct_field")
                if len(same_name_defs) > 1:
                    reasons.append(f"shared_field_name:{len(same_name_defs)}")
                if attr_refs:
                    reasons.append(f"attribute_refs:{len(attr_refs)}")
                if keyword_refs:
                    reasons.append(f"constructor_keyword_refs:{len(keyword_refs)}")
                if string_refs:
                    reasons.append(f"string_key_refs:{len(string_refs)}")
                candidate_safe = name.startswith("_") and not dataclass_field and not attr_refs and not keyword_refs and not string_refs
                field_rows.append({
                    "path": info["path"], "line": d["line"], "scope": scope, "class": class_name, "name": name,
                    "target": qualified_name("var", name, rel, scope),
                    "candidate_safe": candidate_safe,
                    "reasons": reasons,
                    "dataclass_field": dataclass_field,
                    "attribute_refs": len(attr_refs),
                    "keyword_refs": len(keyword_refs),
                    "string_refs": len(string_refs),
                    "same_name_field_defs": len(same_name_defs),
                    "sample_refs": (attr_refs + keyword_refs + string_refs)[:6],
                })

    return {"root": str(target), "counts": {
                "methods": len(method_rows),
                "method_candidate_safe": sum(1 for r in method_rows if r["candidate_safe"]),
                "method_risky": sum(1 for r in method_rows if not r["candidate_safe"]),
                "class_vars": len(field_rows),
                "class_var_candidate_safe": sum(1 for r in field_rows if r["candidate_safe"]),
                "class_var_risky": sum(1 for r in field_rows if not r["candidate_safe"]),
            }, "methods": method_rows, "class_vars": field_rows}


_KIND_SHAPE = {"class": ('["', '"]'), "function": ('("', '")'), "method": ('>"', '"]'),
               "const": ('{{"', '"}}'), "instance": ('[/"', '"/]')}


_BINOP = {
    ast.Add: "add", ast.Sub: "sub", ast.Mult: "mult", ast.MatMult: "matmult", ast.Div: "div",
    ast.Mod: "mod", ast.Pow: "pow", ast.LShift: "lshift", ast.RShift: "rshift", ast.BitOr: "bitor",
    ast.BitXor: "bitxor", ast.BitAnd: "bitand", ast.FloorDiv: "floordiv",
}
_BOOLOP = {ast.And: "and", ast.Or: "or"}
_UNARYOP = {ast.Invert: "invert", ast.Not: "not", ast.UAdd: "uadd", ast.USub: "usub"}
_CMPOP = {
    ast.Eq: "eq", ast.NotEq: "noteq", ast.Lt: "lt", ast.LtE: "lte", ast.Gt: "gt", ast.GtE: "gte",
    ast.Is: "is", ast.IsNot: "isnot", ast.In: "in", ast.NotIn: "notin",
}


def _op_suffix(op: ast.AST, mapping: dict[type, str]) -> str:
    return mapping.get(type(op), type(op).__name__.lower())


def _operation_kind(node: ast.AST) -> str:
    if isinstance(node, ast.BinOp):
        return f"op_binop_{_op_suffix(node.op, _BINOP)}"
    if isinstance(node, ast.BoolOp):
        return f"op_boolop_{_op_suffix(node.op, _BOOLOP)}"
    if isinstance(node, ast.UnaryOp):
        return f"op_unaryop_{_op_suffix(node.op, _UNARYOP)}"
    if isinstance(node, ast.Compare):
        return "op_compare_" + "_".join(_op_suffix(op, _CMPOP) for op in node.ops)
    return "op_" + type(node).__name__.lower()


def _names_in(node: ast.AST, ctx_type: type | tuple[type, ...] = ast.Load) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ctx_type):
            names.append(child.id)
    return names


def _node_code(src: str, node: ast.AST) -> str:
    seg = ast.get_source_segment(src, node) or ""
    return " ".join(seg.strip().split())


class _OperationGraph(ast.NodeVisitor):
    """Code Property Graph seed: AST operation nodes + child/control/data edges, stdlib-only."""

    def __init__(self, path: Path, rel: str, src: str) -> None:
        self.path = path
        self.rel = rel
        self.src = src
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self._node_ids: set[str] = set()
        self._scope: list[str] = []
        self._ids: dict[int, str] = {}
        self._seq = 0
        self._defs_by_name: dict[str, list[str]] = {}

    def _qual(self) -> str:
        return ".".join(self._scope) or "<module>"

    def _id(self, node: ast.AST) -> str:
        existing = self._ids.get(id(node))
        if existing:
            return existing
        line = getattr(node, "lineno", 0)
        col = getattr(node, "col_offset", 0)
        self._seq += 1
        node_id = f"{self.rel}:{line}:{col}:{_operation_kind(node)}:{self._seq}"
        self._ids[id(node)] = node_id
        return node_id

    def _record(self, node: ast.AST) -> str | None:
        if not hasattr(node, "lineno"):
            return None
        node_id = self._id(node)
        if node_id not in self._node_ids:
            self._node_ids.add(node_id)
            stores = _names_in(node, ast.Store)
            loads = _names_in(node, ast.Load)
            self.nodes.append({
                "id": node_id,
                "kind": _operation_kind(node),
                "file": str(self.path),
                "line": getattr(node, "lineno", 0),
                "col": getattr(node, "col_offset", 0),
                "end_line": getattr(node, "end_lineno", None),
                "end_col": getattr(node, "end_col_offset", None),
                "scope": self._qual(),
                "code": _node_code(self.src, node),
                "defines": stores,
                "uses": loads,
            })
            for name in stores:
                self._defs_by_name.setdefault(name, []).append(node_id)
            for name in loads:
                for def_id in self._defs_by_name.get(name, [])[-1:]:
                    self.edges.append({"src": def_id, "dst": node_id, "type": "data_def_use", "name": name,
                                       "confidence": "local_last_assignment"})
        return node_id

    def _body_control_edges(self, body: list[ast.stmt]) -> None:
        visible = [stmt for stmt in body if hasattr(stmt, "lineno")]
        for prev, nxt in zip(visible, visible[1:]):
            self.edges.append({"src": self._id(prev), "dst": self._id(nxt), "type": "control_next"})

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._record(node)
        self._body_control_edges(node.body)
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._record(node)
        self._body_control_edges(node.body)
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def generic_visit(self, node: ast.AST) -> None:
        parent_id = self._record(node)
        if isinstance(node, (ast.Module, ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)):
            for field in ("body", "orelse", "finalbody"):
                body = getattr(node, field, None)
                if isinstance(body, list):
                    self._body_control_edges([x for x in body if isinstance(x, ast.stmt)])
        for child in ast.iter_child_nodes(node):
            child_id = self._record(child)
            if parent_id and child_id:
                self.edges.append({"src": parent_id, "dst": child_id, "type": "ast_child"})
        super().generic_visit(node)


def build_operation_graph(root: Path) -> dict:
    """Operation-level deterministic graph: AST/CPG seed with locations, code, operands and edges."""
    nodes: list[dict] = []
    edges: list[dict] = []
    errors: list[dict] = []
    for f in _py_files(root):
        src = f.read_text(encoding="utf-8", errors="replace")
        rel = _repo_rel(f)
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError as exc:
            errors.append({"path": str(f), "error": str(exc)})
            continue
        graph = _OperationGraph(f, rel, src)
        graph.visit(tree)
        nodes.extend(graph.nodes)
        edges.extend(graph.edges)
    by_kind = Counter(n["kind"] for n in nodes)
    by_edge = Counter(e["type"] for e in edges)
    return {"root": str(root), "nodes": nodes, "edges": edges, "errors": errors,
            "counts": {"nodes": len(nodes), "edges": len(edges), "by_kind": dict(by_kind), "by_edge": dict(by_edge)}}


def build_graph(root: Path) -> dict:
    """Structural graph: nodes = definitions (module-qualified, kind-typed), edges = contains / calls /
    inherits resolved within the project. The relationships pyprefix map could not express, deterministic
    and LLM-free — the parser-side complement to _repos/shared-backend-components/scripts/codegraph.py."""
    proj = build_project(root)
    nodes: list[dict] = []
    def_names: set = set()
    for mod, info in proj["modules"].items():
        for d in info["defs"]:
            nodes.append({"id": f"{mod}:{d['name']}", "name": d["name"], "kind": d["kind"], "module": mod, "line": d["line"]})
            def_names.add(d["name"])
    edges: list[dict] = []
    for mod, info in proj["modules"].items():
        local = {d["name"] for d in info["defs"]}
        for e in info["edges"]:
            src = mod if e["src"] == "<module>" else f"{mod}:{e['src'].split('.')[-1]}"
            if e["dst"] in local:
                edges.append({"src": src, "dst": f"{mod}:{e['dst']}", "type": e["type"]})
            elif e["dst"] in def_names:
                edges.append({"src": src, "dst": e["dst"], "type": e["type"], "cross_module": True})
    by_kind: dict[str, int] = {}
    for n in nodes:
        by_kind[n["kind"]] = by_kind.get(n["kind"], 0) + 1
    by_edge: dict[str, int] = {}
    for e in edges:
        by_edge[e["type"]] = by_edge.get(e["type"], 0) + 1
    return {"root": str(root), "nodes": nodes, "edges": edges,
            "counts": {"nodes": len(nodes), "edges": len(edges), "by_kind": by_kind, "by_edge": by_edge}}


def to_mermaid(graph: dict, limit: int = 240) -> str:
    """Mermaid flowchart of the structural graph (renders inline on GitHub)."""
    arrow = {"contains": "-->", "calls": "-.->", "inherits": "==>"}
    out = ["flowchart LR"]
    keep = {n["id"] for n in graph["nodes"][:limit]}
    for n in graph["nodes"][:limit]:
        op, cl = _KIND_SHAPE.get(n["kind"], ('["', '"]'))
        out.append(f'  {re.sub(chr(92) + "W", "_", n["id"])}{op}{n["name"]}{cl}')
    for e in graph["edges"]:
        if e["src"] in keep and isinstance(e["dst"], str) and e["dst"] in keep:
            out.append(f'  {re.sub(chr(92) + "W", "_", e["src"])} {arrow.get(e["type"], "-->")} {re.sub(chr(92) + "W", "_", e["dst"])}')
    return "\n".join(out)


def find_symbol(name: str, root: Path) -> list[dict]:
    """Every definition + reference of `name` (exact), across the tree."""
    m = build_map(root)
    hits = [s for s in m["symbols"] if s["name"] == name or s["name"] == target_name(s["kind"], name)
            or s["name"].endswith("_" + name)]
    return hits


def stats(root: Path) -> dict:
    m = build_map(root)
    syms = m["symbols"]
    by_kind = Counter(s["kind"] for s in syms)
    conforming = sum(1 for s in syms if s["conforms"])
    top = sorted(syms, key=lambda s: s["ref_count"], reverse=True)[:8]
    return {"symbols": len(syms), "conforming": conforming,
            "conformance_pct": round(100 * conforming / len(syms), 1) if syms else 100.0,
            "violations": len(syms) - conforming, "by_kind": dict(by_kind),
            "most_referenced": [{"name": s["name"], "kind": s["kind"], "refs": s["ref_count"]} for s in top],
            "files": m["files"], "unparseable": len(m["errors"])}


def _audit_bucket(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(REPO_ROOT.resolve())
        return rel.parts[0] if rel.parts else "."
    except ValueError:
        return str(path.parent)


def migration_audit(root: Path) -> dict:
    """Repo/package-level migration audit with corner-case counts.

    This is the formal preflight for a full migration: it scopes to owned Python files, summarizes
    conformance, and makes static-analysis hazards explicit before codemods run.
    """
    files = _py_files(root)
    by_kind: Counter = Counter()
    violations_by_kind: Counter = Counter()
    by_bucket: dict[str, Counter] = {}
    violation_bucket: dict[str, Counter] = {}
    corner_cases: Counter = Counter()
    errors: list[dict] = []
    for f in files:
        info = analyze_file(f)
        bucket = _audit_bucket(f)
        by_bucket.setdefault(bucket, Counter())
        violation_bucket.setdefault(bucket, Counter())
        if info["error"]:
            errors.append({"path": info["path"], "error": info["error"]})
            continue
        rel = _repo_rel(Path(info["path"]))
        for d in info["defs"]:
            by_kind[d["kind"]] += 1
            by_bucket[bucket][d["kind"]] += 1
            if d["name"] in ENTRY_EXEMPT or is_dunder(d["name"]):
                continue
            if not definition_conforms(d, rel):
                violations_by_kind[d["kind"]] += 1
                violation_bucket[bucket][d["kind"]] += 1
        try:
            tree = ast.parse(Path(info["path"]).read_text(encoding="utf-8"), filename=info["path"])
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append({"path": info["path"], "error": str(exc)})
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                corner_cases["f_string"] += 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                corner_cases["comprehension"] += 1
            elif hasattr(ast, "Match") and isinstance(node, ast.Match):
                corner_cases["match_stmt"] += 1
            elif isinstance(node, ast.Lambda):
                corner_cases["lambda"] += 1
            elif isinstance(node, ast.Call):
                callee = _expr_name(node.func) or ""
                if any(kw.arg is None for kw in node.keywords):
                    corner_cases["dynamic_kwargs_call"] += 1
                if callee in {"getattr", "setattr", "hasattr", "globals", "locals", "eval", "exec", "__import__"}:
                    corner_cases[f"dynamic_call:{callee}"] += 1
                if callee == "importlib.import_module":
                    corner_cases["dynamic_import:importlib.import_module"] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if getattr(node, "decorator_list", None):
                    corner_cases["decorated_def"] += len(node.decorator_list)
                if isinstance(node, ast.ClassDef):
                    decs = [_expr_name(d) or "" for d in node.decorator_list]
                    bases = [_expr_name(b) or "" for b in node.bases]
                    if any(d == "dataclass" or d.endswith(".dataclass") for d in decs):
                        corner_cases["dataclass"] += 1
                    if any(b.endswith("Protocol") or b.endswith("ABC") for b in bases):
                        corner_cases["protocol_or_abc"] += 1

    total = sum(by_kind.values())
    violations = sum(violations_by_kind.values())
    roots = []
    for bucket, counts in sorted(by_bucket.items()):
        bucket_total = sum(counts.values())
        bucket_violations = sum(violation_bucket.get(bucket, Counter()).values())
        roots.append({
            "root": bucket,
            "symbols": bucket_total,
            "violations": bucket_violations,
            "conformance_pct": round(100 * (bucket_total - bucket_violations) / bucket_total, 1) if bucket_total else 100.0,
            "by_kind": dict(counts),
            "violations_by_kind": dict(violation_bucket.get(bucket, Counter())),
        })
    return {
        "root": str(root),
        "files": len(files),
        "symbols": total,
        "conforming": total - violations,
        "violations": violations,
        "conformance_pct": round(100 * (total - violations) / total, 1) if total else 100.0,
        "by_kind": dict(by_kind),
        "violations_by_kind": dict(violations_by_kind),
        "roots": sorted(roots, key=lambda r: r["violations"], reverse=True),
        "corner_cases": dict(corner_cases),
        "errors": errors,
        "methodology": {
            "scope": "owned Python source only; excludes virtualenv, references, generated dist/site/artifacts, data, archive, caches, and assistant scratch",
            "next_phase": "migrate only candidate-safe names automatically; contract-risky args/methods/fields require coordinated interface codemods and full proof gate",
        },
    }


STANDARD_TEXT = """pyprefix convention (typed, greppable Python identifiers)

  strict pattern:
    py_<kind>_<file>__<scope>__<name>

  kinds:
    class, function, method, const, instance, var, arg, local

  examples:
    py_function_src_teleon_runtime_credentials__is_present
    py_method_src_teleon_runtime_key_holder__KeyHolder__get
    py_local_scripts_pyprefix___self_test__fails

  - idempotent (safe to re-run); dunders exempt (__init__ never touched).
  - the win: the identifier carries kind + file + scope + original meaning, so grep is an
    exact resolver for both humans and AI.
  - `graph` emits definition/call/contains/inherits edges.
  - `opgraph` emits operation-level AST/CPG nodes for assignments, calls, operators,
    comparisons, branches, returns, child edges, control-next edges, and local def-use edges."""


# ---------------------------------------------------------------- self-test (offline proof)
_FIXTURE = '''
class Cart:
    def add(self, x):
        y = x + 0
        return y

MAX = 5

def open_cart():
    c = Cart()
    return c.add(MAX)

class py_class_Wallet:
    def py_method_pay(self):
        return 1
'''


def _self_test() -> int:
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    ck("convention covers the 8 kinds (incl var/arg/local)",
       set(PREFIX) == {"class", "function", "method", "const", "instance", "var", "arg", "local"})
    ck("target_name is idempotent", target_name("class", "py_class_Cart") == "py_class_Cart")
    ck("qualified_name encodes file + scope + name (globally unique, no hash)",
       qualified_name("function", "is_present", "_repos/teleon/backend/src/teleon/runtime/credentials.py", "<module>") == "py_function_src_teleon_runtime_credentials__is_present"
       and qualified_name("method", "add", "shop.py", "Cart") == "py_method_shop__Cart__add")
    ck("qualified_name idempotent + dunder-exempt",
       qualified_name("function", "py_function_x__foo", "x.py") == "py_function_x__foo" and qualified_name("method", "__init__", "x.py", "C") == "__init__")
    ck("qualified_name disambiguates the same name in different scopes (no reuse)",
       qualified_name("var", "x", "m.py", "foo") != qualified_name("var", "x", "m.py", "bar"))
    ck("dunders are exempt", target_name("method", "__init__") == "__init__" and conforms("method", "__init__"))
    ck("underscores preserved", target_name("function", "_helper") == "py_function__helper")
    ck("non-conforming detected", not conforms("class", "Cart") and conforms("class", "py_class_Cart"))

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "sample.py"
        f.write_text(_FIXTURE, encoding="utf-8")
        info = analyze_file(f)
        kinds = Counter(x["kind"] for x in info["defs"])
        ck("analyzer finds class/function/method/const/instance/arg/local",
           kinds["class"] == 2 and kinds["function"] == 1 and kinds["method"] == 2
           and kinds["const"] == 1 and kinds["instance"] == 1 and kinds["arg"] == 1 and kinds["local"] == 1)
        viols = check_path(Path(d))
        # Cart, add, x, y, MAX, open_cart, c are non-conforming; py_class_Wallet + py_method_pay conform
        names = {v["name"] for v in viols}
        ck("check flags exactly the non-conforming defs",
           {"Cart", "add", "x", "y", "MAX", "open_cart", "c"} <= names and "py_class_Wallet" not in names)
        ck("check proposes the location-derived target name",
           any(v["name"] == "Cart" and v["target"] == "py_class_sample__Cart" for v in viols))
        m = build_map(Path(d))
        cart = next((s for s in m["symbols"] if s["name"] == "Cart"), None)
        ck("map indexes a definition + its references (Cart is referenced)", cart is not None and cart["ref_count"] >= 1)
        st = stats(Path(d))
        ck("stats computes conformance % + kind counts", 0 < st["conformance_pct"] < 100 and st["by_kind"]["class"] == 2)
        ck("find locates a symbol exactly", any(s["name"] == "Cart" for s in find_symbol("Cart", Path(d))))

        # structural graph: nodes + typed edges (the 'beyond pyprefix map' relationships)
        g = build_graph(Path(d))
        ck("graph has nodes + contains/calls/inherits edges (relationships, not just names)",
           g["counts"]["nodes"] >= 4 and any(e["type"] == "contains" for e in g["edges"])
           and any(e["type"] == "calls" for e in g["edges"]))
        ck("mermaid export renders the structural graph", to_mermaid(g).startswith("flowchart"))
        ck("safe-targets finds in-file-only renamable defs (sound: no cross-file name)",
           any(t["name"] == "open_cart" for t in safe_targets(Path(d), Path(d))))
        og = build_operation_graph(Path(d))
        ck("opgraph emits operation nodes for assignments/calls/operators with edges",
           og["counts"]["nodes"] > g["counts"]["nodes"] and any(k.startswith("op_assign") for k in og["counts"]["by_kind"])
           and og["counts"]["by_kind"].get("op_binop_add", 0) > 0
           and og["counts"]["by_edge"].get("ast_child", 0) > 0 and og["counts"]["by_edge"].get("control_next", 0) > 0)

        # codemod: rename funcs/classes/consts in a temp copy, verify conformance + it still runs
        f2 = Path(d) / "mod.py"
        f2.write_text(_FIXTURE, encoding="utf-8")
        res = codemod_file(f2)
        ck("apply renames + compiles (rollback-safe)", res["ok"] and res["renamed"] >= 1)
        after = check_path(f2)
        ck("after apply, no function/class/const violation remains",
           not any(v["kind"] in ("function", "class", "const") for v in after))
        ns: dict = {}
        exec(compile(f2.read_text(encoding="utf-8"), str(f2), "exec"), ns)  # noqa: S102 (hermetic fixture)
        ck("renamed module executes; name is location-derived (py_function_mod__open_cart() == 5)",
           "py_function_mod__open_cart" in ns and ns["py_function_mod__open_cart"]() == 5)
        ck("entry points + dunders are exempt from rename", "__init__" not in {v["name"] for v in after})

        scoped = Path(d) / "scoped.py"
        scoped.write_text(
            "def outer(flag):\n"
            "    total = 1\n"
            "    def inner():\n"
            "        return total + flag\n"
            "    return inner()\n",
            encoding="utf-8")
        dry_scoped = codemod_scoped_file(scoped, {"local"}, dry_run=True)
        ck("scoped local rename dry-run plans closure-safe edits without writing",
           dry_scoped["tokens"] >= 2 and "total = 1" in scoped.read_text(encoding="utf-8"))
        live_scoped = codemod_scoped_file(scoped, {"local"})
        scoped_txt = scoped.read_text(encoding="utf-8")
        ns2: dict = {}
        exec(compile(scoped_txt, str(scoped), "exec"), ns2)  # noqa: S102 (hermetic fixture)
        ck("scoped local rename updates definition + closure read and still executes",
           live_scoped["ok"] and "py_local_scoped__outer__total = 1" in scoped_txt
           and "return py_local_scoped__outer__total + flag" in scoped_txt and ns2["outer"](3) == 4)

        param_reassign = Path(d) / "param_reassign.py"
        param_reassign.write_text(
            "def normalize(value=None):\n"
            "    value = value or 'x'\n"
            "    label = 'seen'\n"
            "    return f'{label}:{value}'\n",
            encoding="utf-8")
        res_param = codemod_scoped_file(param_reassign, {"local"})
        param_txt = param_reassign.read_text(encoding="utf-8")
        ns3: dict = {}
        exec(compile(param_txt, str(param_reassign), "exec"), ns3)  # noqa: S102 (hermetic fixture)
        ck("scoped local rename skips parameter reassignment but rewrites f-string local use",
           res_param["ok"] and "value = value or 'x'" in param_txt
           and "py_local_param_reassign__normalize__label = 'seen'" in param_txt
           and "f'{py_local_param_reassign__normalize__label}:{value}'" in param_txt
           and ns3["normalize"]() == "seen:x")

        except_binding = Path(d) / "except_binding.py"
        except_binding.write_text(
            "def catch():\n"
            "    try:\n"
            "        raise ValueError('x')\n"
            "    except ValueError as e:\n"
            "        return str(e)\n",
            encoding="utf-8")
        res_except = codemod_scoped_file(except_binding, {"local"})
        except_txt = except_binding.read_text(encoding="utf-8")
        ns4: dict = {}
        exec(compile(except_txt, str(except_binding), "exec"), ns4)  # noqa: S102 (hermetic fixture)
        ck("scoped local rename rewrites except-as binding + use",
           res_except["ok"]
           and "except ValueError as py_local_except_binding__catch__e" in except_txt
           and "return str(py_local_except_binding__catch__e)" in except_txt
           and ns4["catch"]() == "x")

        global_binding = Path(d) / "global_binding.py"
        global_binding.write_text(
            "cache = None\n\n"
            "def load():\n"
            "    global cache\n"
            "    if cache is not None:\n"
            "        return cache\n"
            "    found = {'ok': True}\n"
            "    cache = found\n"
            "    return found\n",
            encoding="utf-8")
        res_global = codemod_scoped_file(global_binding, {"local"})
        global_txt = global_binding.read_text(encoding="utf-8")
        ns5: dict = {}
        exec(compile(global_txt, str(global_binding), "exec"), ns5)  # noqa: S102 (hermetic fixture)
        ck("scoped local rename skips names declared global but renames true locals",
           res_global["ok"] and "global cache" in global_txt and "if cache is not None" in global_txt
           and "py_local_global_binding__load__found = {'ok': True}" in global_txt
           and ns5["load"]() == {"ok": True} and ns5["load"]() == {"ok": True})

        shadow_binding = Path(d) / "shadow_binding.py"
        shadow_binding.write_text(
            "def outer():\n"
            "    item = 2\n"
            "    def pred(item):\n"
            "        return item + 1\n"
            "    return pred(4) + item\n",
            encoding="utf-8")
        res_shadow = codemod_scoped_file(shadow_binding, {"local"})
        shadow_txt = shadow_binding.read_text(encoding="utf-8")
        ns6: dict = {}
        exec(compile(shadow_txt, str(shadow_binding), "exec"), ns6)  # noqa: S102 (hermetic fixture)
        ck("scoped local rename respects inner arg shadowing of an outer renamed local",
           res_shadow["ok"] and "def pred(item):" in shadow_txt and "return item + 1" in shadow_txt
           and "return pred(4) + py_local_shadow_binding__outer__item" in shadow_txt
           and ns6["outer"]() == 7)

        scoped_function = Path(d) / "scoped_function.py"
        scoped_function.write_text(
            "def outer(xs):\n"
            "    def keep(x):\n"
            "        return x > 0\n"
            "    return [x for x in xs if keep(x)]\n",
            encoding="utf-8")
        res_scoped_function = codemod_scoped_file(scoped_function, {"function"})
        scoped_function_txt = scoped_function.read_text(encoding="utf-8")
        ns7: dict = {}
        exec(compile(scoped_function_txt, str(scoped_function), "exec"), ns7)  # noqa: S102 (hermetic fixture)
        ck("scoped function rename updates nested def name and call sites",
           res_scoped_function["ok"]
           and "def py_function_scoped_function__outer__keep" in scoped_function_txt
           and "if py_function_scoped_function__outer__keep(x)" in scoped_function_txt
           and ns7["py_function_scoped_function__outer"]([-1, 2]) == [2])

    # cross-file rename: a 2-module package; rename a globally-unique function + const, importer rewritten
    with tempfile.TemporaryDirectory() as d2:
        root = Path(d2)
        (root / "m.py").write_text("MAXV = 5\n\n\ndef helper(x):\n    return x + MAXV\n", encoding="utf-8")
        (root / "other.py").write_text(
            "from m import helper\nimport m\n\n\ndef run():\n    return helper(1) + m.MAXV\n", encoding="utf-8")
        (root / "facade.py").write_text("from m import helper\n\n__all__ = [\"helper\"]\n", encoding="utf-8")
        (root / "consumer.py").write_text(
            "from facade import helper\n\n\ndef via_facade():\n    return helper(2)\n", encoding="utf-8")
        renames = globally_unique_targets(root / "m.py", root)   # target m.py only; other.py's run() is left callable
        ck("cross-file: finds globally-unique safe targets (helper, MAXV)",
           {("m", "helper"), ("m", "MAXV")} == set(renames))
        dry = migrate_package(root / "m.py", root, dry_run=True)
        ck("migrate-package dry-run plans cross-file/facade edits without writing",
           dry["renames"] == 2 and dry["files_changed"] and "def helper" in (root / "m.py").read_text(encoding="utf-8"))
        cross_file_rename(root, renames)
        m_txt = (root / "m.py").read_text(encoding="utf-8")
        o_txt = (root / "other.py").read_text(encoding="utf-8")
        ck("cross-file: def renamed in its own module (location-derived)", "def py_function_m__helper" in m_txt and "py_const_m__MAXV = 5" in m_txt)
        ck("cross-file: importer's from-import + bare ref + qualified m.MAXV all rewritten",
           "from m import py_function_m__helper" in o_txt and "py_function_m__helper(1)" in o_txt and "m.py_const_m__MAXV" in o_txt)
        facade_txt = (root / "facade.py").read_text(encoding="utf-8")
        consumer_txt = (root / "consumer.py").read_text(encoding="utf-8")
        ck("cross-file: re-export facade __all__ + facade consumers rewritten",
           "from m import py_function_m__helper" in facade_txt
           and '"py_function_m__helper"' in facade_txt
           and "from facade import py_function_m__helper" in consumer_txt
           and "py_function_m__helper(2)" in consumer_txt)
        sys.path.insert(0, d2)
        try:
            import importlib
            om = importlib.import_module("other")
            ck("cross-file: the migrated package still executes correctly (run() == 11)", om.run() == 11)
            cm = importlib.import_module("consumer")
            ck("cross-file: migrated facade consumer still executes correctly (via_facade() == 7)", cm.via_facade() == 7)
        finally:
            sys.path.remove(d2)
            for _m in ("m", "other", "facade", "consumer"):
                sys.modules.pop(_m, None)

    # module-scope rename: duplicate bare names in unrelated modules are not the same symbol.
    with tempfile.TemporaryDirectory() as d3:
        root = Path(d3)
        (root / "m.py").write_text("def helper():\n    return 'm'\n", encoding="utf-8")
        (root / "other.py").write_text("def helper():\n    return 'other'\n", encoding="utf-8")
        (root / "consumer.py").write_text(
            "import m\nimport other\n\n\ndef run():\n    return m.helper(), other.helper()\n", encoding="utf-8")
        dry_mod = migrate_module_scope(root / "m.py", root, dry_run=True)
        ck("module-scope dry-run targets duplicate bare name by module, not global name",
           dry_mod["renames"] == 1 and dry_mod["targets"][0]["module"] == "m")
        migrate_module_scope(root / "m.py", root)
        ck("module-scope rename updates m.helper but leaves unrelated other.helper",
           "def py_function_m__helper" in (root / "m.py").read_text(encoding="utf-8")
           and "def helper" in (root / "other.py").read_text(encoding="utf-8")
           and "m.py_function_m__helper()" in (root / "consumer.py").read_text(encoding="utf-8")
           and "other.helper()" in (root / "consumer.py").read_text(encoding="utf-8"))
        (root / "names.py").write_text(
            "cache = None\n\n"
            "def catalog():\n"
            "    return 1\n\n"
            "def all_catalogs():\n"
            "    global cache\n"
            "    if cache is None:\n"
            "        cache = catalog() + 1\n"
            "    return cache\n",
            encoding="utf-8")
        (root / "names_consumer.py").write_text(
            "from names import all_catalogs, catalog\n\n"
            "def combo():\n"
            "    return all_catalogs() + catalog()\n",
            encoding="utf-8")
        migrate_module_scope(root / "names.py", root)
        names_txt = (root / "names.py").read_text(encoding="utf-8")
        names_consumer_txt = (root / "names_consumer.py").read_text(encoding="utf-8")
        ck("module-scope rename rewrites globals and avoids substring import matches",
           "global py_var_names__cache" in names_txt
           and "py_var_names__cache = py_function_names__catalog() + 1" in names_txt
           and "all_py_function" not in names_consumer_txt
           and "from names import py_function_names__all_catalogs, py_function_names__catalog" in names_consumer_txt)
        sys.path.insert(0, d3)
        try:
            import importlib
            nm = importlib.import_module("names_consumer")
            ck("module-scope renamed all_catalogs/catalog import line still executes", nm.combo() == 3)
        finally:
            sys.path.remove(d3)
            for _m in ("m", "other", "consumer", "names", "names_consumer"):
                sys.modules.pop(_m, None)

    # arg safety: no keyword calls -> candidate-safe; visible keyword call -> risky.
    with tempfile.TemporaryDirectory() as d4:
        root = Path(d4)
        (root / "a.py").write_text(
            "def f(x, y):\n    return x + y\n\n\ndef g(z):\n    return z\n\n\ndef handler(payload, *, now):\n    return payload\n",
            encoding="utf-8")
        (root / "b.py").write_text("from a import f, g, handler\n\nf(1, y=2)\ng(3)\nhandler({})\n", encoding="utf-8")
        rep = arg_safety_report(root, root)
        by_name = {r["name"]: r for r in rep["args"]}
        ck("arg-report marks visible keyword-call args risky and positional-only args candidate-safe",
           by_name["y"]["keyword_safe"] is False and by_name["z"]["keyword_safe"] is True)
        ck("arg-report marks reserved runtime keyword args risky even through dynamic callback registries",
           by_name["now"]["keyword_safe"] is False and by_name["now"]["reserved_runtime_keyword"] is True)
        safe_arg = migrate_safe_args(root, root, dry_run=True)
        ck("safe-arg migration dry-run includes only keyword-safe args", safe_arg["candidate_args"] == 3)
        migrate_safe_args(root, root)
        migrated_a = (root / "a.py").read_text(encoding="utf-8")
        migrated_b = (root / "b.py").read_text(encoding="utf-8")
        ck("safe-arg migration renames safe args but leaves keyword-called arg unchanged",
           "def f(py_arg_a__f__x, y)" in migrated_a
           and "def g(py_arg_a__g__z)" in migrated_a
           and "def handler(py_arg_a__handler__payload, *, now)" in migrated_a
           and "f(1, y=2)" in migrated_b)

    # contract report: methods and class vars are migration contracts, not blind rename targets.
    with tempfile.TemporaryDirectory() as d5:
        root = Path(d5)
        (root / "model.py").write_text(
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class Item:\n"
            "    id: str\n"
            "    status = 'new'\n"
            "    def describe(self):\n"
            "        return self.id\n"
            "    def _private_token(self):\n"
            "        return self.status\n\n"
            "def use(item):\n"
            "    return getattr(item, 'describe')()\n",
            encoding="utf-8")
        crep = contract_risk_report(root, root)
        describe = next(r for r in crep["methods"] if r["name"] == "describe")
        private_method = next(r for r in crep["methods"] if r["name"] == "_private_token")
        field_id = next(r for r in crep["class_vars"] if r["name"] == "id")
        ck("contract-report marks public/dynamic methods risky and isolated private methods candidate-safe",
           not describe["candidate_safe"] and "public_method" in describe["reasons"]
           and describe["dynamic_refs"] == 1 and private_method["candidate_safe"])
        ck("contract-report marks dataclass/attribute fields risky before field renames",
           not field_id["candidate_safe"] and field_id["dataclass_field"] and field_id["attribute_refs"] >= 1)
        audit = migration_audit(root)
        ck("audit summarizes conformance and corner cases for owned Python files",
           audit["files"] == 1 and audit["symbols"] >= 5 and audit["violations"] >= 1
           and audit["corner_cases"].get("dataclass", 0) == 1
           and audit["corner_cases"].get("dynamic_call:getattr", 0) >= 1)

    if fails:
        print(f"FAIL - pyprefix: {len(fails)} failure(s)")
        return 1
    print("PASS - pyprefix: 8-kind convention (+ qualified_name: globally-unique file__scope__name, no hash), "
          "AST analyzer (defs/refs/imports/edges), conformance check, structural graph, operation graph, "
          "cross-file rename (compile-verified + reversible), safe-target finder; stdlib-only, deterministic.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Typed, greppable Python identifiers for deterministic code maps.")
    sub = ap.add_subparsers(dest="cmd")
    ap.add_argument("--self-test", action="store_true")
    for c in ("check", "map", "stats"):
        sp = sub.add_parser(c)
        sp.add_argument("path")
        if c == "map":
            sp.add_argument("--json")
    sp = sub.add_parser("find"); sp.add_argument("name"); sp.add_argument("path")
    ap_apply = sub.add_parser("apply"); ap_apply.add_argument("path"); ap_apply.add_argument("--exempt", default="")
    ap_graph = sub.add_parser("graph"); ap_graph.add_argument("path"); ap_graph.add_argument("--mermaid", action="store_true"); ap_graph.add_argument("--json")
    ap_opgraph = sub.add_parser("opgraph"); ap_opgraph.add_argument("path"); ap_opgraph.add_argument("--json")
    ap_audit = sub.add_parser("audit"); ap_audit.add_argument("path"); ap_audit.add_argument("--json")
    ap_safe = sub.add_parser("safe-targets"); ap_safe.add_argument("path")
    ap_mig = sub.add_parser("migrate-safe"); ap_mig.add_argument("path")
    ap_pkg = sub.add_parser("migrate-package"); ap_pkg.add_argument("path"); ap_pkg.add_argument("--apply", action="store_true")
    ap_modscope = sub.add_parser("migrate-module-scope"); ap_modscope.add_argument("path"); ap_modscope.add_argument("--apply", action="store_true")
    ap_arg = sub.add_parser("arg-report"); ap_arg.add_argument("path"); ap_arg.add_argument("--json")
    ap_safeargs = sub.add_parser("migrate-safe-args"); ap_safeargs.add_argument("path"); ap_safeargs.add_argument("--apply", action="store_true")
    ap_contract = sub.add_parser("contract-report"); ap_contract.add_argument("path"); ap_contract.add_argument("--json")
    ap_scoped = sub.add_parser("migrate-scoped")
    ap_scoped.add_argument("path")
    ap_scoped.add_argument("--kinds", default="local")
    ap_scoped.add_argument("--apply", action="store_true")
    sub.add_parser("standard")
    args = ap.parse_args(argv)

    if args.self_test or args.cmd is None:
        if args.cmd is None and not args.self_test:
            print(STANDARD_TEXT)
            return 0
        return _self_test()

    if args.cmd == "standard":
        print(STANDARD_TEXT)
        return 0
    if args.cmd == "check":
        v = check_path(Path(args.path))
        for x in v:
            print(f"  {x['path']}:{x['line']}  {x['kind']:8} {x['name']}  ->  {x['target']}")
        print(f"{len(v)} violation(s).")
        return 1 if v else 0
    if args.cmd == "apply":
        exempt = {x.strip() for x in args.exempt.split(",") if x.strip()}
        total = 0
        for f in _py_files(Path(args.path)):
            r = codemod_file(f, exempt=exempt)
            if r["renamed"]:
                total += r["renamed"]
                print(f"  {r['path']}: renamed {r['renamed']}")
            elif not r["ok"]:
                print(f"  {r['path']}: SKIPPED (rolled back) - {r['reason']}")
        print(f"renamed {total} definition(s) across {args.path}. RUN THE PROOF GATE NOW (it is the oracle).")
        return 0
    if args.cmd == "map":
        m = build_map(Path(args.path))
        if args.json:
            Path(args.json).write_text(json.dumps(m, indent=1), encoding="utf-8")
            print(f"wrote {args.json}: {len(m['symbols'])} symbols across {m['files']} files")
        else:
            for s in m["symbols"][:200]:
                print(f"  {s['kind']:8} {s['name']:32} {s['def']['path']}:{s['def']['line']}  refs={s['ref_count']}")
        return 0
    if args.cmd == "find":
        for s in find_symbol(args.name, Path(args.path)):
            print(f"{s['name']}  ({s['kind']})\n  def  {s['def']['path']}:{s['def']['line']}")
            for r in s["refs"][:50]:
                print(f"  ref  {r['path']}:{r['line']}")
        return 0
    if args.cmd == "stats":
        print(json.dumps(stats(Path(args.path)), indent=1))
        return 0
    if args.cmd == "graph":
        g = build_graph(Path(args.path))
        if args.mermaid:
            print(to_mermaid(g))
        elif args.json:
            Path(args.json).write_text(json.dumps(g, indent=1), encoding="utf-8")
            print(f"wrote {args.json}: {g['counts']}")
        else:
            print(json.dumps(g["counts"], indent=1))
        return 0
    if args.cmd == "opgraph":
        g = build_operation_graph(Path(args.path))
        if args.json:
            Path(args.json).write_text(json.dumps(g, indent=1), encoding="utf-8")
            print(f"wrote {args.json}: {g['counts']}")
        else:
            print(json.dumps(g["counts"], indent=1))
        return 0
    if args.cmd == "audit":
        res = migration_audit(Path(args.path))
        if args.json:
            Path(args.json).write_text(json.dumps(res, indent=1), encoding="utf-8")
            print(f"wrote {args.json}: files={res['files']} symbols={res['symbols']} violations={res['violations']}")
        else:
            print(json.dumps({
                "files": res["files"],
                "symbols": res["symbols"],
                "conforming": res["conforming"],
                "violations": res["violations"],
                "conformance_pct": res["conformance_pct"],
                "violations_by_kind": res["violations_by_kind"],
                "corner_cases": res["corner_cases"],
                "top_roots": res["roots"][:10],
            }, indent=1))
        return 0
    if args.cmd == "safe-targets":
        st = safe_targets(Path(args.path), REPO_ROOT)
        for t in st[:400]:
            print(f"  {t['path']}:{t['line']}  {t['kind']:8} {t['name']}  ->  {t['target']}")
        print(f"{len(st)} safe in-file rename target(s) in {args.path} (no cross-file references repo-wide).")
        return 0
    if args.cmd == "migrate-safe":
        res = migrate_safe(Path(args.path), REPO_ROOT)
        for r in res:
            if r["renamed"] or not r["ok"]:
                print(f"  {r['path']}: renamed {r['renamed']}  ({r['reason']})")
        print(f"renamed safe symbols in {sum(1 for r in res if r['renamed'])} file(s). RUN THE PROOF GATE; revert if red.")
        return 0
    if args.cmd == "migrate-package":
        res = migrate_package(Path(args.path), REPO_ROOT, dry_run=not args.apply)
        mode = "DRY RUN" if res["dry_run"] else "APPLIED"
        for t in res["targets"][:200]:
            print(f"  target {t['module']}:{t['name']} -> {t['target']}")
        if len(res["targets"]) > 200:
            print(f"  ... {len(res['targets']) - 200} more target(s)")
        for r in res["files_changed"][:200]:
            print(f"  file {r['path']}: {'would rename' if res['dry_run'] else 'renamed'} {r['renamed']} token(s)")
        if len(res["files_changed"]) > 200:
            print(f"  ... {len(res['files_changed']) - 200} more changed file(s)")
        for r in res["failures"]:
            print(f"  failure {r['path']}: {r.get('reason', 'unknown')}")
        print(f"{mode}: {len(res['targets'])} target symbol(s), {len(res['files_changed'])} file(s), {len(res['failures'])} compile failure(s).")
        if not res["dry_run"]:
            print("RUN THE FULL PROOF GATE NOW; it is the runtime oracle.")
        return 1 if res["failures"] else 0
    if args.cmd == "migrate-module-scope":
        res = migrate_module_scope(Path(args.path), REPO_ROOT, dry_run=not args.apply)
        mode = "DRY RUN" if res["dry_run"] else "APPLIED"
        for t in res["targets"][:200]:
            print(f"  target {t['module']}:{t['name']} -> {t['target']}")
        if len(res["targets"]) > 200:
            print(f"  ... {len(res['targets']) - 200} more target(s)")
        for r in res["files_changed"][:200]:
            print(f"  file {r['path']}: {'would rename' if res['dry_run'] else 'renamed'} {r['renamed']} token(s)")
        if len(res["files_changed"]) > 200:
            print(f"  ... {len(res['files_changed']) - 200} more changed file(s)")
        for r in res["failures"]:
            print(f"  failure {r['path']}: {r.get('reason', 'unknown')}")
        print(f"{mode}: {len(res['targets'])} module-scope target symbol(s), {len(res['files_changed'])} file(s), {len(res['failures'])} compile failure(s).")
        if not res["dry_run"]:
            print("RUN THE FULL PROOF GATE NOW; it is the runtime oracle.")
        return 1 if res["failures"] else 0
    if args.cmd == "migrate-scoped":
        kinds = {x.strip() for x in args.kinds.split(",") if x.strip()}
        bad = kinds - set(PREFIX)
        if bad:
            print(f"unknown kind(s): {sorted(bad)}")
            return 2
        res = migrate_scoped(Path(args.path), kinds=kinds, dry_run=not args.apply)
        mode = "DRY RUN" if res["dry_run"] else "APPLIED"
        for r in res["files_changed"][:200]:
            print(f"  file {r['path']}: {'would rename' if res['dry_run'] else 'renamed'} {r['renamed']} scoped name(s), {r['tokens']} token(s)")
        if len(res["files_changed"]) > 200:
            print(f"  ... {len(res['files_changed']) - 200} more changed file(s)")
        for r in res["failures"]:
            print(f"  failure {r['path']}: {r.get('reason', 'unknown')}")
        print(f"{mode}: kinds={','.join(res['kinds'])}, {len(res['files_changed'])} file(s), {len(res['failures'])} compile failure(s).")
        if not res["dry_run"]:
            print("RUN THE FULL PROOF GATE NOW; it is the runtime oracle.")
        return 1 if res["failures"] else 0
    if args.cmd == "arg-report":
        res = arg_safety_report(Path(args.path), REPO_ROOT)
        if args.json:
            Path(args.json).write_text(json.dumps(res, indent=1), encoding="utf-8")
            print(f"wrote {args.json}: {res['counts']}")
        else:
            print(json.dumps(res["counts"], indent=1))
            for row in [r for r in res["args"] if not r["conforms"] and not r["keyword_safe"]][:80]:
                reserved = " reserved_runtime_keyword=1" if row.get("reserved_runtime_keyword") else ""
                print(f"  risky {row['path']}:{row['line']} {row['scope']}({row['name']}) "
                      f"keyword_refs={row['keyword_refs']} dynamic_kwargs_refs={row['dynamic_kwargs_refs']}{reserved}")
        return 0
    if args.cmd == "migrate-safe-args":
        res = migrate_safe_args(Path(args.path), REPO_ROOT, dry_run=not args.apply)
        mode = "DRY RUN" if res["dry_run"] else "APPLIED"
        for r in res["files_changed"][:200]:
            print(f"  file {r['path']}: {'would rename' if res['dry_run'] else 'renamed'} {r['renamed']} safe arg(s), {r['tokens']} token(s)")
        if len(res["files_changed"]) > 200:
            print(f"  ... {len(res['files_changed']) - 200} more changed file(s)")
        for r in res["failures"]:
            print(f"  failure {r['path']}: {r.get('reason', 'unknown')}")
        print(f"{mode}: {res['candidate_args']} keyword-safe arg(s), {len(res['files_changed'])} file(s), {len(res['failures'])} compile failure(s).")
        if not res["dry_run"]:
            print("RUN THE FULL PROOF GATE NOW; it is the runtime oracle.")
        return 1 if res["failures"] else 0
    if args.cmd == "contract-report":
        res = contract_risk_report(Path(args.path), REPO_ROOT)
        if args.json:
            Path(args.json).write_text(json.dumps(res, indent=1), encoding="utf-8")
            print(f"wrote {args.json}: {res['counts']}")
        else:
            print(json.dumps(res["counts"], indent=1))
            for row in [r for r in res["methods"] if not r["candidate_safe"]][:60]:
                print(f"  method-risk {row['path']}:{row['line']} {row['scope']}.{row['name']} "
                      f"reasons={','.join(row['reasons']) or 'none'}")
            for row in [r for r in res["class_vars"] if not r["candidate_safe"]][:60]:
                print(f"  field-risk  {row['path']}:{row['line']} {row['scope']}.{row['name']} "
                      f"reasons={','.join(row['reasons']) or 'none'}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
