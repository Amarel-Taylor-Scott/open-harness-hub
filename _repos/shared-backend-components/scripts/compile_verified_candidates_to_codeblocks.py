#!/usr/bin/env python3
"""Compile verified primitive candidate rows into reusable candidate codeblocks.

One verified candidate row becomes one codeblock record. Each generated block
is a tiny Python callable that imports the shared candidate runtime and emits a
receipt; the domain contract, effects, proof requirements, and problem/solution
core travel in the embedded spec.

Generated codeblocks remain candidates:
  candidate=true, serves_truth=false

They are syntax-checked and smoke-run, but they are not promoted production
implementations until adapter code, source review, side-effect proof, and
domain-specific tests exist.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.primitives.codeblock_runtime import execute_primitive_codeblock, spec_from_candidate  # noqa: E402


DEFAULT_SOURCE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "million_seed_compiler_runs"
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "primitive_codeblocks"
DEFAULT_PROGRESS_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "progress"
DEFAULT_SHARD_SIZE = 10_000
REPORT_HASH_CHARS = 16


def _utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", (value or "primitive").lower()).strip("_")
    if not slug or slug[0].isdigit():
        slug = f"primitive_{slug}"
    return slug[:64]


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _full_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2)


def _source_files(source_roots: list[Path], source_files: list[Path]) -> list[Path]:
    if source_files:
        return sorted(p for p in source_files if p.exists())
    found: list[Path] = []
    for root in source_roots:
        if root.is_file():
            found.append(root)
        elif root.exists():
            found.extend(root.rglob("verified_candidates.jsonl"))
    return sorted(dict.fromkeys(found))


def _iter_rows(files: Iterable[Path], offset: int, limit: int) -> Iterable[tuple[Path, int, dict[str, Any]]]:
    seen = 0
    yielded = 0
    for path in files:
        with path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                if seen < offset:
                    seen += 1
                    continue
                if limit and yielded >= limit:
                    return
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    seen += 1
                    continue
                yielded += 1
                seen += 1
                yield path, line_no, row


def _compact_spec(row: Mapping[str, Any]) -> dict[str, Any]:
    spec = asdict(spec_from_candidate(row))
    spec["source_candidate"] = {
        "verification_id": row.get("verification_id"),
        "verification_level": row.get("verification_level"),
        "verification_status": row.get("verification_status"),
        "dedupe_key": row.get("dedupe_key"),
        "seed_id": row.get("seed_id"),
        "source_provider": row.get("source_provider"),
        "source_model": row.get("source_model"),
    }
    return spec


def _render_code(spec: Mapping[str, Any]) -> str:
    function_name = f"run_{_slug(str(spec.get('primitive_id', 'primitive')))}"
    spec_json_literal = repr(_json(spec))
    return (
        "from __future__ import annotations\n\n"
        "import json\n"
        "from typing import Any, Mapping\n\n"
        "from src.teleon.primitives.codeblock_runtime import execute_primitive_codeblock\n\n"
        f"PRIMITIVE_SPEC: dict[str, Any] = json.loads({spec_json_literal})\n\n\n"
        "def run(payload: Mapping[str, Any] | None, policy: Mapping[str, Any] | None = None, "
        "context: Mapping[str, Any] | None = None) -> dict[str, Any]:\n"
        "    return execute_primitive_codeblock(PRIMITIVE_SPEC, payload, policy=policy, context=context)\n\n\n"
        f"def {function_name}(payload: Mapping[str, Any] | None, policy: Mapping[str, Any] | None = None, "
        "context: Mapping[str, Any] | None = None) -> dict[str, Any]:\n"
        "    return run(payload, policy=policy, context=context)\n"
    )


def _validate_code(code: str) -> tuple[bool, bool, dict[str, Any]]:
    syntax_ok = False
    smoke_ok = False
    details: dict[str, Any] = {}
    try:
        compiled = compile(code, "<primitive_codeblock>", "exec")
        syntax_ok = True
    except SyntaxError as exc:
        details["syntax_error"] = f"{exc.msg} (line {exc.lineno})"
        return syntax_ok, smoke_ok, details
    namespace: dict[str, Any] = {}
    try:
        exec(compiled, namespace)
        result = namespace["run"]({"sample": True}, policy={"mode": "smoke"}, context={"compiler": "codeblock"})
        smoke_ok = bool(result.get("candidate") is True and result.get("serves_truth") is False and result.get("receipt_hash"))
        details["receipt_hash"] = result.get("receipt_hash")
        details["status"] = result.get("status")
    except Exception as exc:  # noqa: BLE001
        details["smoke_error"] = f"{type(exc).__name__}: {exc}"
    return syntax_ok, smoke_ok, details


def _codeblock_record(
    row: Mapping[str, Any],
    spec: Mapping[str, Any],
    code: str,
    source_path: Path,
    line_no: int,
    syntax_ok: bool,
    smoke_ok: bool,
    validation_details: Mapping[str, Any],
) -> dict[str, Any]:
    primitive_id = str(spec.get("primitive_id"))
    return {
        "record_type": "primitive_codeblock_candidate",
        "codeblock_id": f"codeblock:{primitive_id}",
        "primitive_id": primitive_id,
        "title": spec.get("title"),
        "language": "python",
        "runtime_framework": "src.teleon.primitives.codeblock_runtime",
        "entrypoint": "run(payload, policy=None, context=None)",
        "input_edge": spec.get("input_edge"),
        "output_edge": spec.get("output_edge"),
        "family": spec.get("family"),
        "industry": spec.get("industry"),
        "region": spec.get("region"),
        "runtime_targets": spec.get("runtime_targets", []),
        "effects": spec.get("effects", []),
        "proof_requirements": spec.get("proof_requirements", []),
        "promotion_blockers": spec.get("promotion_blockers", []),
        "problem_solution_core": spec.get("problem_solution_core", {}),
        "source_refs": spec.get("source_refs", []),
        "source_candidate_path": str(source_path.relative_to(REPO)) if source_path.is_relative_to(REPO) else str(source_path),
        "source_line": line_no,
        "source_verification_id": row.get("verification_id"),
        "source_verification_level": row.get("verification_level"),
        "code": code,
        "validation": {
            "syntax_ok": syntax_ok,
            "smoke_ok": smoke_ok,
            "details": dict(validation_details),
        },
        "candidate": True,
        "serves_truth": False,
    }


def compile_rows(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    run_id = args.run_id or f"codeblock_compile_{_utc_stamp()}"
    out_dir = args.out_dir or (_resource(run_id))
    out_dir.mkdir(parents=True, exist_ok=True)
    source_files = _source_files(args.source_root, args.source_file)

    generated = 0
    syntax_pass = 0
    smoke_pass = 0
    included = 0
    rejected = 0
    current_shard_index = -1
    shard_fh = None
    shard_paths: list[Path] = []

    try:
        for source_path, line_no, row in _iter_rows(source_files, args.offset, args.limit):
            if generated % args.shard_size == 0:
                if shard_fh:
                    shard_fh.close()
                current_shard_index += 1
                shard_path = out_dir / f"primitive_codeblocks_{current_shard_index:06d}.jsonl"
                shard_paths.append(shard_path)
                shard_fh = shard_path.open("w", encoding="utf-8")

            spec = _compact_spec(row)
            code = _render_code(spec)
            syntax_ok, smoke_ok, validation_details = _validate_code(code)
            generated += 1
            syntax_pass += int(syntax_ok)
            smoke_pass += int(smoke_ok)
            if syntax_ok and smoke_ok:
                included += 1
            else:
                rejected += 1

            record = _codeblock_record(row, spec, code, source_path, line_no, syntax_ok, smoke_ok, validation_details)
            assert shard_fh is not None
            shard_fh.write(_json(record) + "\n")
    finally:
        if shard_fh:
            shard_fh.close()

    duration = max(time.perf_counter() - started, 0.000001)
    manifest = {
        "run_id": run_id,
        "record_type": "primitive_codeblock_compile_manifest",
        "source_files": [str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p) for p in source_files],
        "out_dir": str(out_dir.relative_to(REPO)) if out_dir.is_relative_to(REPO) else str(out_dir),
        "shard_count": len(shard_paths),
        "generated": generated,
        "syntax_pass": syntax_pass,
        "smoke_pass": smoke_pass,
        "included": included,
        "rejected": rejected,
        "candidate": True,
        "serves_truth": False,
        "duration_seconds": round(duration, 3),
        "generated_per_hour": round(generated / duration * 3600, 2),
        "included_per_hour": round(included / duration * 3600, 2),
        "created_at": _utc_stamp(),
        "notes": [
            "One verified candidate row compiled to one executable candidate codeblock record.",
            "Smoke validation proves syntax and receipt-level invocation only; domain side effects are not executed.",
            "Generated codeblocks remain candidate=true and serves_truth=false.",
        ],
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    progress = (
        f"# Primitive Codeblock Compiler Progress\n\n"
        f"- run_id: `{run_id}`\n"
        f"- source_files: `{len(source_files)}`\n"
        f"- output: `{manifest['out_dir']}`\n"
        f"- generated: `{generated:,}`\n"
        f"- syntax_pass: `{syntax_pass:,}`\n"
        f"- smoke_pass: `{smoke_pass:,}`\n"
        f"- included: `{included:,}`\n"
        f"- rejected: `{rejected:,}`\n"
        f"- duration_seconds: `{manifest['duration_seconds']}`\n"
        f"- included_per_hour: `{manifest['included_per_hour']:,}`\n\n"
        "## Interpretation\n\n"
        "These are executable candidate codeblocks backed by the shared primitive runtime. "
        "They are reusable scaffolds and receipt emitters, not promoted production implementations. "
        "Promotion still requires source review, adapter implementation, effect proof, domain fixtures, "
        "and benchmark receipts.\n"
    )
    DEFAULT_PROGRESS_ROOT.mkdir(parents=True, exist_ok=True)
    progress_path = _resource(f"{run_id}_progress.md")
    progress_json_path = _resource(f"{run_id}_progress.json")
    progress_path.write_text(progress, encoding="utf-8")
    progress_json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path.relative_to(REPO)) if manifest_path.is_relative_to(REPO) else str(manifest_path)
    manifest["progress_path"] = str(progress_path.relative_to(REPO))
    manifest["progress_json_path"] = str(progress_json_path.relative_to(REPO))
    return manifest


def self_test() -> int:
    sample = {
        "primitive_id": "prim:test.customer_tracker",
        "title": "customer tracker smoke",
        "input_edge": "CustomerEvent+Policy",
        "output_edge": "CustomerReceipt",
        "contract": {
            "problem": "teams need repeatable customer-event tracking",
            "summary": "emit a candidate receipt for a customer tracker primitive",
            "fit_when": "tracking event-shaped input",
            "avoid_when": "promotion has no source proof",
        },
        "edge_contract": {
            "preconditions": "payload is mapping",
            "postconditions": "receipt emitted",
            "failure_modes": "payload_must_be_mapping",
        },
        "effects": [{"effect": "audit_log_write", "target": "CustomerReceipt"}],
        "proof_requirements": ["schema_contract_test"],
        "promotion_blockers": ["proof_receipts_missing"],
        "runtime_targets": ["python_function"],
        "candidate": True,
        "serves_truth": False,
    }
    spec = _compact_spec(sample)
    code = _render_code(spec)
    syntax_ok, smoke_ok, details = _validate_code(code)
    assert syntax_ok, details
    assert smoke_ok, details
    receipt = execute_primitive_codeblock(spec, {"customer_id": "demo"})
    assert receipt["candidate"] is True and receipt["serves_truth"] is False and receipt["receipt_hash"]
    print("compile_verified_candidates_to_codeblocks self-test: OK")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", action="append", type=Path, default=[], help="Root containing verified_candidates.jsonl files.")
    parser.add_argument("--source-file", action="append", type=Path, default=[], help="Specific verified_candidates.jsonl file to compile.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory for sharded codeblock JSONL records.")
    parser.add_argument("--run-id", default="", help="Stable run id for output/progress names.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum rows to compile. 0 means no limit.")
    parser.add_argument("--offset", type=int, default=0, help="Rows to skip before compiling.")
    parser.add_argument("--shard-size", type=int, default=DEFAULT_SHARD_SIZE, help="Records per output JSONL shard.")
    parser.add_argument("--self-test", action="store_true", help="Run offline self-test.")
    args = parser.parse_args(argv)
    if not args.source_root:
        args.source_root = [DEFAULT_SOURCE_ROOT]
    if args.shard_size <= 0:
        parser.error("--shard-size must be positive")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.self_test:
        return self_test()
    manifest = compile_rows(args)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
