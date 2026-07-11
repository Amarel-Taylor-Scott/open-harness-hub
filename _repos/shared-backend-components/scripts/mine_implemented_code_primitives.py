#!/usr/bin/env python3
"""Mine real Python functions/classes into source-backed primitive records.

This is the non-LLM fallback lane for growing useful primitive code objects.
It extracts implemented code from real modules, records signatures/source spans,
validates AST + snippet compilation, and emits candidate primitive records.

Generated rows are implementation-backed candidates, not promoted truth:
  candidate=true, serves_truth=false
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
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "implemented_code_primitives"
DEFAULT_PROGRESS_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "progress"
DEFAULT_RUN_ID = "implemented_code_primitives_daily"
DEFAULT_LIMIT = 1_000
SOURCE_HASH_CHARS = 20


SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "_reference",
    "node_modules",
    "site-packages",
}

LOW_VALUE_PREFIXES = (
    "data/dev-intel/primitive_codeblocks/",
    "data/dev-intel/primitive_factory/million_seed_compiler_runs/",
)

HIGH_VALUE_PATH_HINTS = (
    "/src/teleon/primitives/",
    "/src/teleon/registry/",
    "/src/teleon/runtime/",
    "/src/teleon/retrieval/",
    "/src/teleon/resolution/",
    "/src/teleon/synthesis/",
    "/src/teleon/context/",
    "/src/teleon/observer/",
    "/scripts/context_workers/",
    "/scripts/db/",
    "/scripts/run_",
    "/scripts/check_",
    "/scripts/build_",
    "/primitives/",
    "/tests/",
)


@dataclass(frozen=True, slots=True)
class CodeObjectCandidate:
    root: Path
    path: Path
    kind: str
    qualname: str
    name: str
    lineno: int
    end_lineno: int
    source_code: str
    signature: str
    docstring: str
    decorators: tuple[str, ...]
    parameters: tuple[str, ...]
    return_annotation: str
    is_public: bool
    score: int


def _utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _json(row: Any) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any, chars: int = SOURCE_HASH_CHARS) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()[:chars]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _module_id(root: Path, path: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    if rel.name == "__init__.py":
        rel = rel.parent
    else:
        rel = rel.with_suffix("")
    return ".".join(part for part in rel.parts if part)


def _safe_id_part(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "_", text).strip("_")
    return value[:140] or "code_object"


def _skip_path(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_PARTS:
        return True
    rel = _rel(path)
    return rel.startswith(LOW_VALUE_PREFIXES)


def _annotation_text(node: ast.AST | None) -> str:
    if node is None:
        return "Any"
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return "Any"


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> tuple[str, tuple[str, ...], str]:
    if isinstance(node, ast.ClassDef):
        return f"class {node.name}", (), node.name
    args = []
    params = []
    all_args = list(node.args.posonlyargs) + list(node.args.args)
    defaults = [None] * (len(all_args) - len(node.args.defaults)) + list(node.args.defaults)
    for arg, default in zip(all_args, defaults):
        text = arg.arg
        params.append(arg.arg)
        ann = _annotation_text(arg.annotation) if arg.annotation else ""
        if ann:
            text += f": {ann}"
        if default is not None:
            try:
                text += f" = {ast.unparse(default)}"
            except Exception:  # noqa: BLE001
                text += " = ..."
        args.append(text)
    if node.args.vararg:
        params.append(node.args.vararg.arg)
        args.append("*" + node.args.vararg.arg)
    for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        text = arg.arg
        params.append(arg.arg)
        ann = _annotation_text(arg.annotation) if arg.annotation else ""
        if ann:
            text += f": {ann}"
        if default is not None:
            try:
                text += f" = {ast.unparse(default)}"
            except Exception:  # noqa: BLE001
                text += " = ..."
        args.append(text)
    if node.args.kwarg:
        params.append(node.args.kwarg.arg)
        args.append("**" + node.args.kwarg.arg)
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    ret = _annotation_text(node.returns)
    return f"{prefix} {node.name}({', '.join(args)}) -> {ret}", tuple(params), ret


def _decorators(node: ast.AST) -> tuple[str, ...]:
    out = []
    for dec in getattr(node, "decorator_list", []):
        try:
            out.append(ast.unparse(dec))
        except Exception:  # noqa: BLE001
            out.append("<decorator>")
    return tuple(out)


def _compile_ok(source: str, *, kind: str) -> tuple[bool, str]:
    try:
        compile(source, f"<{kind}_primitive_snippet>", "exec")
    except SyntaxError as exc:
        return False, f"{exc.msg} (line {exc.lineno})"
    return True, ""


def _score(path: Path, node: ast.AST, doc: str, kind: str) -> int:
    rel = "/" + _rel(path)
    score = 0
    score += 40 if any(hint in rel for hint in HIGH_VALUE_PATH_HINTS) else 0
    score += 20 if "/primitives/" in rel else 0
    score += 12 if "/tests/" in rel else 0
    score += 8 if doc else 0
    score += 8 if not getattr(node, "name", "").startswith("_") else -10
    score += 6 if kind in {"function", "class"} else 3
    score += 5 if "receipt" in rel.lower() or "primitive" in rel.lower() else 0
    score -= 10 if "/archive/" in rel else 0
    return score


def iter_python_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".py":
            files = [root]
        else:
            files = sorted(root.rglob("*.py"))
        for path in files:
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen or _skip_path(path):
                continue
            seen.add(resolved)
            yield path


def _source_segment(source: str, node: ast.AST) -> str:
    text = ast.get_source_segment(source, node)
    if text:
        return text
    lines = source.splitlines()
    start = max(getattr(node, "lineno", 1) - 1, 0)
    end = getattr(node, "end_lineno", start + 1)
    return "\n".join(lines[start:end])


def _walk_top_level(path: Path, root: Path) -> Iterable[CodeObjectCandidate]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception:
        return
    module = _module_id(root, path)
    parent_stack: list[str] = []

    def visit_body(body: list[ast.stmt]) -> Iterable[CodeObjectCandidate]:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else ("async_function" if isinstance(node, ast.AsyncFunctionDef) else "function")
                qual = ".".join([*parent_stack, node.name])
                sig, params, ret = _signature(node)
                doc = ast.get_docstring(node) or ""
                snippet = _source_segment(source, node)
                is_public = not node.name.startswith("_")
                yield CodeObjectCandidate(
                    root=root,
                    path=path,
                    kind=kind,
                    qualname=qual,
                    name=node.name,
                    lineno=int(getattr(node, "lineno", 1)),
                    end_lineno=int(getattr(node, "end_lineno", getattr(node, "lineno", 1))),
                    source_code=snippet,
                    signature=sig,
                    docstring=doc,
                    decorators=_decorators(node),
                    parameters=params,
                    return_annotation=ret,
                    is_public=is_public,
                    score=_score(path, node, doc, kind),
                )
                if isinstance(node, ast.ClassDef):
                    parent_stack.append(node.name)
                    yield from visit_body(node.body)
                    parent_stack.pop()

    yield from visit_body(tree.body)


def collect_candidates(roots: list[Path]) -> list[CodeObjectCandidate]:
    all_candidates: list[CodeObjectCandidate] = []
    for path in iter_python_files(roots):
        root = next((r for r in roots if str(path.resolve()).startswith(str(r.resolve()))), path.parent)
        all_candidates.extend(_walk_top_level(path, root) or [])
    all_candidates.sort(key=lambda c: (-c.score, _rel(c.path), c.lineno, c.qualname))
    return all_candidates


def _record(candidate: CodeObjectCandidate) -> dict[str, Any]:
    module = _module_id(candidate.root, candidate.path)
    object_id = f"{module}.{candidate.qualname}" if module else candidate.qualname
    code_hash = _sha({"source": candidate.source_code, "object": object_id}, chars=24)
    source_locator = f"line{candidate.lineno}-{code_hash[-8:]}"
    compile_ok, compile_error = _compile_ok(candidate.source_code, kind=candidate.kind)
    action = "instantiate" if candidate.kind == "class" else "call"
    input_edge = f"Python{candidate.kind.title().replace('_', '')}[{object_id}]+InvocationPolicy+SourceContext"
    output_edge = f"Python{candidate.kind.title().replace('_', '')}Receipt+{_safe_id_part(candidate.return_annotation)}"
    return {
        "record_type": "implemented_code_primitive_candidate",
        "primitive_id": f"impl:python.{_safe_id_part(object_id)}.{source_locator}@source",
        "code_object_id": object_id,
        "title": f"{action} {candidate.name}",
        "kind": "implemented_code_primitive",
        "code_kind": candidate.kind,
        "language": "python",
        "source_path": _rel(candidate.path),
        "source_root": _rel(candidate.root),
        "source_span": {"start_line": candidate.lineno, "end_line": candidate.end_lineno},
        "module": module,
        "qualname": candidate.qualname,
        "signature": candidate.signature,
        "parameters": list(candidate.parameters),
        "return_annotation": candidate.return_annotation,
        "decorators": list(candidate.decorators),
        "docstring": candidate.docstring,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "blackbox": candidate.docstring.splitlines()[0] if candidate.docstring else f"Source-backed Python {candidate.kind} `{object_id}`.",
        "contract": {
            "problem": f"Reuse source-backed Python {candidate.kind} `{object_id}` without asking a model to recreate it.",
            "summary": candidate.docstring.splitlines()[0] if candidate.docstring else f"Wraps implemented Python {candidate.kind} `{object_id}` as a candidate primitive.",
            "input": input_edge,
            "output": output_edge,
            "errors": "import_side_effect; missing_dependency; behavior_not_fixture_verified; unsafe_runtime_effect",
        },
        "edge_contract": {
            "input_edge_description": f"Call-site payload for `{candidate.signature}` plus execution policy and source context.",
            "output_edge_description": f"Receipt and return value for `{object_id}`.",
            "preconditions": "Module source parses and snippet compiles; runtime dependencies and safe import behavior still require proof.",
            "postconditions": "Source span, code hash, signature, and promotion blockers are recorded.",
            "failure_modes": "signature_mismatch; import_error; runtime_exception; missing_fixture; side_effect_not_declared",
            "composition_notes": "Generated by deterministic AST source mining from an implemented Python module.",
        },
        "runtime_targets": ["python_import", "python_function" if candidate.kind != "class" else "python_class"],
        "effects": ["unknown_runtime_effects_need_audit"],
        "proof_requirements": [
            "module_ast_parse",
            "snippet_compile",
            "import_smoke_test",
            "fixture_behavior_test",
            "effect_audit",
            "dependency_review",
        ],
        "promotion_blockers": [
            "import_smoke_not_run",
            "behavior_fixture_missing",
            "effects_not_audited",
            "source_license_review_needed",
        ],
        "validation": {
            "module_ast_parse_ok": True,
            "snippet_compile_ok": compile_ok,
            "snippet_compile_error": compile_error,
            "source_span_present": candidate.lineno > 0 and candidate.end_lineno >= candidate.lineno,
            "signature_extracted": bool(candidate.signature),
            "implementation_backed": True,
        },
        "code": candidate.source_code,
        "code_sha256": "sha256:" + hashlib.sha256(candidate.source_code.encode("utf-8")).hexdigest(),
        "dedupe_key": code_hash,
        "rank_features": {
            "source_priority_score": candidate.score,
            "has_docstring": bool(candidate.docstring),
            "is_public": candidate.is_public,
            "parameter_count": len(candidate.parameters),
        },
        "generation_path": "deterministic_ast_source_mining",
        "verification_level": "L4_source_ast_snippet_compiled" if compile_ok else "L3_source_ast_parse_only",
        "candidate": True,
        "serves_truth": False,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    roots = [Path(p) for p in args.source_root]
    run_id = args.run_id or f"{DEFAULT_RUN_ID}_{_utc_stamp()}"
    out_dir = Path(args.out_dir) if args.out_dir else _resource(run_id)
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = collect_candidates(roots)
    selected = candidates[max(args.offset, 0):]
    if args.limit:
        selected = selected[: args.limit]

    records_path = out_dir / "implemented_code_primitives.jsonl"
    records = [_record(c) for c in selected]
    with records_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(_json(record) + "\n")

    duration = max(time.perf_counter() - started, 0.000001)
    compile_pass = sum(1 for r in records if r["validation"]["snippet_compile_ok"])
    manifest = {
        "record_type": "implemented_code_primitive_mining_manifest",
        "run_id": run_id,
        "source_roots": [_rel(p) for p in roots],
        "out_dir": _rel(out_dir),
        "records_path": _rel(records_path),
        "available_code_objects": len(candidates),
        "selected": len(records),
        "included": len(records),
        "snippet_compile_pass": compile_pass,
        "snippet_compile_fail": len(records) - compile_pass,
        "duration_seconds": round(duration, 3),
        "included_per_hour": round(len(records) / duration * 3600, 2),
        "candidate": True,
        "serves_truth": False,
        "created_at": _utc_stamp(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    DEFAULT_PROGRESS_ROOT.mkdir(parents=True, exist_ok=True)
    progress_path = _resource(f"{run_id}_progress.md")
    progress_path.write_text(
        "# Implemented Code Primitive Mining Progress\n\n"
        f"- run_id: `{run_id}`\n"
        f"- available_code_objects: `{len(candidates):,}`\n"
        f"- included: `{len(records):,}`\n"
        f"- snippet_compile_pass: `{compile_pass:,}`\n"
        f"- snippet_compile_fail: `{len(records) - compile_pass:,}`\n"
        f"- included_per_hour: `{manifest['included_per_hour']:,}`\n"
        f"- records_path: `{manifest['records_path']}`\n\n"
        "These rows are source-backed implemented code primitive candidates. "
        "They are not promoted truth until import smoke, fixtures, dependency review, and effect audit pass.\n",
        encoding="utf-8",
    )
    manifest["progress_path"] = _rel(progress_path)
    return manifest


def self_test() -> int:
    sample = "def add(a: int, b: int) -> int:\n    \"\"\"Add two integers.\"\"\"\n    return a + b\n"
    tree = ast.parse(sample)
    node = tree.body[0]
    assert isinstance(node, ast.FunctionDef)
    sig, params, ret = _signature(node)
    assert sig == "def add(a: int, b: int) -> int"
    assert params == ("a", "b")
    assert ret == "int"
    ok, err = _compile_ok(sample, kind="function")
    assert ok and not err
    print("mine_implemented_code_primitives self-test: OK")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", action="append", default=[], help="Source root to mine. Can be repeated.")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if not args.source_root:
        args.source_root = [str(REPO), "/tmp/claude-code-online-repo"]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.self_test:
        return self_test()
    manifest = run(args)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
