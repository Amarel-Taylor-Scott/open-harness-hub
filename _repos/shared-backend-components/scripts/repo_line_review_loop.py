#!/usr/bin/env python3
"""Resumable repo line-review loop.

This command reviews owned repository files file-by-file and line-by-line in bounded batches. It is not
an LLM. It creates deterministic review artifacts that an agent can consume and act on repeatedly:

  .agent/repo-line-review/state.json
  .agent/repo-line-review/findings.jsonl
  .agent/repo-line-review/reviewed-lines.jsonl   (only with --emit-line-records)
  .agent/repo-line-review/summary.md

The loop is deliberately restartable. It records file hashes, line counts, findings, and progress, so a
multi-day agent goal can sweep the entire owned source surface without trying to fit the repo into one
context window.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import ast
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource   # resolves a relocated resource dir to its _repos home (no root symlink needed)
DEFAULT_OUT = (REPO / ".agent") / "repo-line-review"

EXCLUDE_PARTS = {
    ".agent",
    ".agents",
    ".claude",
    ".codex",
    ".git",
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

DEFAULT_ROOTS = (
    "scripts",
    "src",
    "hf-space",
    "templates",
    "code-templates",
    "catalog",
    "schemas",
    "vocabularies",
    "docs",
    "taxonomy",
    "architecture",
    ".github",
    "db",
)

TEXT_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".md", ".rst", ".txt", ".html", ".css", ".sql", ".sh",
    ".dockerfile", ".env.example",
}

SECRET_PATTERNS = [
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai_like_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("live_secret_like", re.compile(r"\b(?:sk|pk)_live_[A-Za-z0-9_-]{8,}\b")),
    ("token_assignment", re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
]

TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b", re.IGNORECASE)
CONFLICT_RE = re.compile(r"^(<{7}|={7}|>{7})")
DYNAMIC_CALL_RE = re.compile(r"\b(getattr|setattr|hasattr|globals|locals|eval|exec|__import__)\s*\(")
IMPORTLIB_RE = re.compile(r"\bimportlib\.import_module\s*\(")
PY_ENTRYPOINT_RE = re.compile(r"^\s*def\s+(run|main|serve|handle)\s*\(")


@dataclass(frozen=True)
class FileRecord:
    path: Path
    rel: str
    size: int
    sha256: str
    line_count: int


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _excluded(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.parts)


def _is_text_candidate(path: Path) -> bool:
    if _excluded(path):
        return False
    if path.name in {"Dockerfile", "Makefile", "AGENTS.md", "README.md"}:
        return True
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if path.name.endswith(".env.example"):
        return True
    return False


def _roots(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    try:
        if root.resolve() == REPO.resolve():
            return [resource(name) for name in DEFAULT_ROOTS if resource(name).exists()]
    except FileNotFoundError:
        pass
    return [root]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_text(path: Path) -> tuple[str | None, bytes, str | None]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, b"", f"read_error:{exc}"
    if b"\x00" in raw:
        return None, raw, "binary_nul"
    for enc in ("utf-8", "utf-8-sig"):
        try:
            return raw.decode(enc), raw, None
        except UnicodeDecodeError:
            continue
    return None, raw, "decode_error"


def discover_files(root: Path = REPO) -> list[FileRecord]:
    records: list[FileRecord] = []
    for base in _roots(root):
        if not base.exists() or _excluded(base):
            continue
        paths = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in paths:
            if not path.is_file() or not _is_text_candidate(path):
                continue
            text, raw, err = _read_text(path)
            if err:
                line_count = 0
            else:
                line_count = len((text or "").splitlines())
            try:
                rel = str(path.resolve().relative_to(REPO.resolve()))
            except ValueError:
                rel = str(path)
            records.append(FileRecord(path=path, rel=rel, size=len(raw), sha256=_sha256_bytes(raw), line_count=line_count))
    return sorted(records, key=lambda r: r.rel)


def _jsonl_append(path: Path, rows: Iterable[dict]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def _finding(path: str, line: int, kind: str, severity: str, message: str, text: str = "", **extra: object) -> dict:
    row = {
        "ts": _now(),
        "path": path,
        "line": line,
        "kind": kind,
        "severity": severity,
        "message": message,
    }
    if text:
        row["excerpt"] = text.strip()[:220]
    row.update(extra)
    return row


def _python_ast_findings(rel: str, text: str) -> list[dict]:
    findings: list[dict] = []
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        return [_finding(rel, exc.lineno or 0, "python_syntax", "error", str(exc))]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = ""
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
            if any(kw.arg is None for kw in node.keywords):
                findings.append(_finding(rel, node.lineno, "dynamic_kwargs", "medium", "Call uses **kwargs; signature renames need contract review"))
            if callee in {"getattr", "setattr", "hasattr", "eval", "exec", "__import__"}:
                findings.append(_finding(rel, node.lineno, "dynamic_python_call", "high", f"Dynamic call `{callee}` requires unresolved-reference handling"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and getattr(node, "decorator_list", None):
            findings.append(_finding(rel, node.lineno, "decorated_definition", "low", "Decorated definition; renames may affect framework/reflection behavior"))
        elif isinstance(node, ast.JoinedStr):
            findings.append(_finding(rel, node.lineno, "f_string", "info", "F-string line; token positions can be approximate for codemods"))
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            findings.append(_finding(rel, node.lineno, "comprehension", "info", "Comprehension introduces local binding scope"))
    return findings


def _pyprefix_findings(rel: str, path: Path) -> list[dict]:
    if path.suffix != ".py":
        return []
    try:
        import pyprefix  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive in alternate runners
        return [_finding(rel, 0, "pyprefix_unavailable", "low", f"Could not import pyprefix: {exc}")]
    violations = pyprefix.check_path(path)
    if not violations:
        return []
    rows = [_finding(rel, 0, "pyprefix_file", "medium", f"{len(violations)} pyprefix violation(s)")]
    for v in violations[:20]:
        rows.append(_finding(rel, v["line"], "pyprefix_symbol", "medium",
                             f"{v['kind']} `{v['name']}` should be `{v['target']}`"))
    if len(violations) > 20:
        rows.append(_finding(rel, 0, "pyprefix_symbol_overflow", "info",
                             f"{len(violations) - 20} additional pyprefix violation(s) omitted for this file"))
    return rows


def review_file(record: FileRecord, emit_line_records: bool = False) -> tuple[list[dict], list[dict]]:
    text, raw, err = _read_text(record.path)
    if err:
        return [_finding(record.rel, 0, "file_read", "warning", err, size=record.size)], []
    assert text is not None
    findings: list[dict] = []
    line_rows: list[dict] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        if emit_line_records:
            line_rows.append({
                "ts": _now(),
                "path": record.rel,
                "line": idx,
                "sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                "length": len(line),
            })
        if line.rstrip("\n\r") != line.rstrip():
            findings.append(_finding(record.rel, idx, "trailing_whitespace", "low", "Trailing whitespace", line))
        if "\t" in line and record.path.suffix in {".py", ".js", ".jsx", ".ts", ".tsx"}:
            findings.append(_finding(record.rel, idx, "tab_in_code", "low", "Tab character in code file", line))
        if len(line) > 180:
            findings.append(_finding(record.rel, idx, "long_line", "low", f"Line length {len(line)} > 180", line))
        if CONFLICT_RE.search(line):
            findings.append(_finding(record.rel, idx, "merge_conflict_marker", "error", "Merge conflict marker found", line))
        if TODO_RE.search(line):
            findings.append(_finding(record.rel, idx, "todo_marker", "info", "TODO/FIXME/HACK marker", line))
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(_finding(record.rel, idx, f"secret_pattern:{name}", "high", f"Secret-like pattern `{name}`", line))
        if DYNAMIC_CALL_RE.search(line) or IMPORTLIB_RE.search(line):
            findings.append(_finding(record.rel, idx, "dynamic_reference_text", "medium", "Dynamic reference/import text", line))
        if record.path.suffix == ".py" and PY_ENTRYPOINT_RE.search(line):
            findings.append(_finding(record.rel, idx, "external_entrypoint_candidate", "info",
                                     "Potential external entrypoint; use shim/exemption policy before renaming", line))
    if record.path.suffix == ".py":
        findings.extend(_python_ast_findings(record.rel, text))
        findings.extend(_pyprefix_findings(record.rel, record.path))
    return findings, line_rows


def _load_state(out_dir: Path, records: list[FileRecord], reset: bool = False) -> dict:
    state_path = out_dir / "state.json"
    manifest = [{"path": r.rel, "sha256": r.sha256, "size": r.size, "line_count": r.line_count} for r in records]
    if reset or not state_path.exists():
        return {
            "version": 1,
            "created_at": _now(),
            "updated_at": _now(),
            "repo": str(REPO),
            "cursor": 0,
            "completed_files": 0,
            "reviewed_lines": 0,
            "findings": 0,
            "manifest_hash": _sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8")),
            "manifest": manifest,
        }
    state = json.loads(state_path.read_text(encoding="utf-8"))
    current_hash = _sha256_bytes(json.dumps(manifest, sort_keys=True).encode("utf-8"))
    if state.get("manifest_hash") != current_hash:
        # Preserve progress by path where possible, but recompute the manifest for changed trees.
        done = {row["path"] for row in state.get("manifest", [])[:int(state.get("cursor", 0))]}
        cursor = 0
        for idx, row in enumerate(manifest):
            if row["path"] not in done:
                cursor = idx
                break
        else:
            cursor = len(manifest)
        state.update({"manifest_hash": current_hash, "manifest": manifest, "cursor": cursor})
    return state


def _write_state(out_dir: Path, state: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = _now()
    (out_dir / "state.json").write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _write_summary(out_dir: Path, state: dict, batch: dict) -> None:
    lines = [
        "# Repo Line Review Loop",
        "",
        f"- Updated: `{state['updated_at']}`",
        f"- Cursor: `{state['cursor']}` / `{len(state.get('manifest', []))}`",
        f"- Completed files: `{state.get('completed_files', 0)}`",
        f"- Reviewed lines: `{state.get('reviewed_lines', 0)}`",
        f"- Findings: `{state.get('findings', 0)}`",
        "",
        "## Last Batch",
        "",
        f"- Files reviewed: `{batch.get('files', 0)}`",
        f"- Lines reviewed: `{batch.get('lines', 0)}`",
        f"- Findings emitted: `{batch.get('findings', 0)}`",
        f"- Done: `{batch.get('done', False)}`",
        "",
        "Artifacts:",
        "",
        "- `state.json`",
        "- `findings.jsonl`",
        "- `reviewed-lines.jsonl` when `--emit-line-records` is used",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_once(root: Path, out_dir: Path, max_files: int, max_lines: int,
             emit_line_records: bool = False, reset: bool = False) -> dict:
    records = discover_files(root)
    if reset:
        for name in ("findings.jsonl", "reviewed-lines.jsonl", "summary.md"):
            artifact = out_dir / name
            if artifact.exists():
                artifact.unlink()
    state = _load_state(out_dir, records, reset=reset)
    cursor = int(state.get("cursor", 0))
    reviewed_files = 0
    reviewed_lines = 0
    finding_count = 0
    while cursor < len(records) and reviewed_files < max_files and reviewed_lines < max_lines:
        rec = records[cursor]
        findings, line_rows = review_file(rec, emit_line_records=emit_line_records)
        finding_count += _jsonl_append(out_dir / "findings.jsonl", findings)
        if emit_line_records:
            _jsonl_append(out_dir / "reviewed-lines.jsonl", line_rows)
        reviewed_files += 1
        reviewed_lines += rec.line_count
        cursor += 1
    state["cursor"] = cursor
    state["completed_files"] = cursor
    state["reviewed_lines"] = int(state.get("reviewed_lines", 0)) + reviewed_lines
    state["findings"] = int(state.get("findings", 0)) + finding_count
    batch = {"files": reviewed_files, "lines": reviewed_lines, "findings": finding_count, "done": cursor >= len(records)}
    _write_state(out_dir, state)
    _write_summary(out_dir, state, batch)
    return {"state": state, "batch": batch}


def _self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "src").mkdir()
        py = root / "src" / "sample.py"
        py.write_text(
            "SECRET = 'not-real'\n\n"
            "def run(inputs):\n"
            "    value = inputs.get('value')\n"
            "    return getattr(inputs, 'items')()\n",
            encoding="utf-8",
        )
        (root / ".venv").mkdir()
        (root / ".venv" / "ignored.py").write_text("def ignored():\n    pass\n", encoding="utf-8")
        out = root / ".agent" / "review"
        res = run_once(root, out, max_files=10, max_lines=1000, emit_line_records=True, reset=True)
        state = json.loads((out / "state.json").read_text(encoding="utf-8"))
        findings = [json.loads(line) for line in (out / "findings.jsonl").read_text(encoding="utf-8").splitlines()]
        ok = (
            res["batch"]["files"] == 1
            and state["completed_files"] == 1
            and any(f["kind"] == "external_entrypoint_candidate" for f in findings)
            and any(f["kind"] in {"dynamic_reference_text", "dynamic_python_call"} for f in findings)
            and "ignored.py" not in (out / "summary.md").read_text(encoding="utf-8")
            and (out / "reviewed-lines.jsonl").exists()
        )
        if not ok:
            print("FAIL - repo_line_review_loop self-test")
            return 1
    print("PASS - repo_line_review_loop: discovers owned text files, reviews line-by-line, emits findings, checkpoints state")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resumable line-by-line review loop for owned repo files.")
    parser.add_argument("root", nargs="?", default=".", help="Root/file to review; default is repo root owned-source sweep.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Artifact directory.")
    parser.add_argument("--max-files", type=int, default=25)
    parser.add_argument("--max-lines", type=int, default=8000)
    parser.add_argument("--emit-line-records", action="store_true", help="Append a hash record for every reviewed line.")
    parser.add_argument("--reset", action="store_true", help="Start a new sweep state in --out.")
    parser.add_argument("--loop", action="store_true", help="Run continuously until the sweep completes.")
    parser.add_argument("--sleep", type=float, default=5.0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    root = Path(args.root)
    if not root.is_absolute():
        root = resource(root).resolve()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = (REPO / out_dir).resolve()  # REPO is override-able (tests point it at a temp tree); absolute out_dir passes through

    while True:
        result = run_once(root, out_dir, args.max_files, args.max_lines,
                          emit_line_records=args.emit_line_records, reset=args.reset)
        batch = result["batch"]
        print(json.dumps({
            "files": batch["files"],
            "lines": batch["lines"],
            "findings": batch["findings"],
            "done": batch["done"],
            "state": str(out_dir / "state.json"),
            "findings_path": str(out_dir / "findings.jsonl"),
        }, indent=2))
        args.reset = False
        if not args.loop or batch["done"]:
            return 0
        time.sleep(args.sleep)


if __name__ == "__main__":
    raise SystemExit(main())
