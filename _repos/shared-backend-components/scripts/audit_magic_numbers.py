"""audit_magic_numbers — the no-magic-values AUDITOR (backs registry #41 magic_number_audit).

Scans Python for UNNAMED numeric literals: inline numbers used in expressions / calls / comparisons that are
NOT bound to a named constant and carry no provenance ("why 0.83?"). This gives the no-magic-values discipline
(_repos/shared-backend-components/docs/codex/no-magic-values.md) an actual SCANNER, not just a doc + ad-hoc per-check enforcement.

A literal is treated as OK when it is:
  - the RHS of a `NAME = <number>` / `NAME: T = <number>` assignment (it is *named* — the good pattern), or
  - a ubiquitous low-signal value (see _ALLOWED), or
  - inside a test file / this auditor itself.
Everything else inline (0.83 in `if conf > 0.83`, 1800 in `sleep(1800)`, 256 in `vector(256)`) is a CANDIDATE
magic number — flagged for a named constant + a unit/rationale comment.

Usage:
  python3 _repos/shared-backend-components/scripts/audit_magic_numbers.py [PATH] [--top N]   # report (default PATH = _repos/teleon/backend/src/teleon)
  python3 _repos/shared-backend-components/scripts/audit_magic_numbers.py --self-test         # embedded test; exit nonzero on failure

Heuristic (candidate flags, not all are real magic). Deterministic, offline, stdlib (ast) only.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import ast
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
# Ubiquitous, low-signal literals that are not worth flagging (identity/neutral elements, common small bumps).
_ALLOWED = {0, 1, 2, -1, 0.0, 1.0, 0.5, 100, 1000}
_SKIP_DIRS = {"__pycache__", ".git", "node_modules", "_reference", "archive", ".venv", "venv"}


def _named_literal_ids(tree: ast.AST) -> set[int]:
    """ids() of Constant nodes that ARE the value of a `NAME = <number>` binding — those literals are named, so OK."""
    ok: set[int] = set()
    for node in ast.walk(tree):
        val = None
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) for t in node.targets):
            val = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            val = node.value
        if isinstance(val, ast.Constant) and isinstance(val.value, (int, float)) and not isinstance(val.value, bool):
            ok.add(id(val))
        # unary minus on a literal (e.g. THRESHOLD = -0.5) — name the inner constant too
        if isinstance(val, ast.UnaryOp) and isinstance(val.operand, ast.Constant) and isinstance(val.operand.value, (int, float)):
            ok.add(id(val.operand))
    return ok


def scan_source(src: str) -> list[tuple[int, object]]:
    """Return [(lineno, value)] for each unnamed, non-allowed numeric literal."""
    tree = ast.parse(src)
    named = _named_literal_ids(tree)
    out: list[tuple[int, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if id(node) in named or node.value in _ALLOWED:
                continue
            out.append((getattr(node, "lineno", 0), node.value))
    return out


def _iter_py(path: Path):
    if path.is_file() and path.suffix == ".py":
        yield path
        return
    for p in path.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in p.parts) or p.name.startswith("test_") or p.name.endswith("_test.py"):
            continue
        yield p


_SAMPLE = (
    "MAX_RETRIES = 5\n"            # named constant -> OK
    "TIMEOUT_S: int = 1800\n"      # named (annotated) -> OK
    "def f(x):\n"
    "    if x > 0.83:\n"           # inline magic -> FLAG 0.83
    "        return g(256)\n"      # inline magic -> FLAG 256
    "    return x + 1\n"           # 1 is allowed -> OK
)


def _self_test() -> int:
    vals = {v for _, v in scan_source(_SAMPLE)}
    checks = [
        ("flags inline 0.83", 0.83 in vals),
        ("flags inline 256", 256 in vals),
        ("ignores named MAX_RETRIES=5", 5 not in vals),
        ("ignores named TIMEOUT_S=1800", 1800 not in vals),
        ("ignores allowed 1", 1 not in vals),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'XX'}] {n}")
    if bad:
        print(f"FAIL - audit_magic_numbers self-test: {len(bad)} failed; found={sorted(vals, key=str)}")
        return 1
    print(f"PASS - audit_magic_numbers: scanner flags unnamed literals, ignores named + allowed (found={sorted(vals, key=str)}).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default="_repos/teleon/backend/src/teleon", help="file or dir to audit (default: _repos/teleon/backend/src/teleon)")
    ap.add_argument("--top", type=int, default=15, help="show the N files with the most flags")
    ap.add_argument("--self-test", action="store_true", help="run the embedded test; exit nonzero on failure")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()

    target = (_resource(args.path)) if not Path(args.path).is_absolute() else Path(args.path)
    if not target.exists():
        print(f"audit_magic_numbers: path not found: {target}")
        return 0
    per_file: list[tuple[int, str]] = []
    total = 0
    for p in _iter_py(target):
        try:
            findings = scan_source(p.read_text())
        except SyntaxError:
            continue
        if findings:
            per_file.append((len(findings), str(p.relative_to(_REPO))))
            total += len(findings)
    per_file.sort(reverse=True)
    print(f"audit_magic_numbers: {total} candidate magic numbers across {len(per_file)} files under {args.path}")
    print("(candidates — give each a named constant + a unit/rationale comment, or add to _ALLOWED if truly neutral)")
    for n, f in per_file[: args.top]:
        print(f"  {n:5d}  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
