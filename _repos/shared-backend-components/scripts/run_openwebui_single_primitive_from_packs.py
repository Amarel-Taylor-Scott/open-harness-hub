#!/usr/bin/env python3
"""Expand generated_primitive_packs rows with one model call per primitive.

This runner is intentionally not a batch-row prompt. It reads Markdown table
rows from generated_primitive_packs, sends exactly one source row per model
call, asks for exactly one candidate primitive JSON object, and checkpoints
after every row.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import OPENWEBUI_DEFAULT_BASE_URL, OPENWEBUI_DEFAULT_MODEL, REPO_ROOT  # noqa: E402
from scripts.extract_primitive_model_candidates import extract_candidates  # noqa: E402
from scripts._llm_client import chat, resolve_provider  # noqa: E402
from scripts.openwebui_cdp_client import cdp_chat  # noqa: E402

PACK_DIR = _resource("generated_primitive_packs")
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "single_primitive_openwebui"

SYSTEM_PROMPT = (
    "You convert exactly one primitive seed row into exactly one candidate primitive JSON object. "
    "Return one JSON object only. No markdown, no prose, no code fences, no arrays, no second object. "
    "Keep candidate=true and serves_truth=false. Do not claim implementation exists. "
    "Prefer compact, testable contracts and honest promotion blockers."
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _sha(value: Any, *, n: int = 20) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise AssertionError(f"{path}:{line_number}: expected object")
        rows.append(row)
    return rows


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
        handle.flush()


def _write_json(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _split_md_row(line: str) -> list[str]:
    text = line.strip()
    if not text.startswith("|") or not text.endswith("|"):
        return []
    text = text.strip("|")
    return [cell.strip().strip("`") for cell in text.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(cell.replace(":", "").replace("-", "").strip()) <= set() for cell in cells)


def iter_pack_rows(pack_dir: Path, *, pack_file: str = "") -> list[dict[str, Any]]:
    files = [pack_dir / pack_file] if pack_file else sorted(path for path in pack_dir.glob("*.md") if path.name != "primitive_generated_pack_index.md")
    rows: list[dict[str, Any]] = []
    for path in files:
        if not path.exists():
            raise AssertionError(f"missing pack file: {path}")
        header: list[str] | None = None
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            cells = _split_md_row(line)
            if not cells:
                continue
            if header is None:
                if "row_id" in cells and "record_id" in cells:
                    header = cells
                continue
            if _is_separator(cells):
                continue
            if len(cells) != len(header):
                continue
            row = dict(zip(header, cells))
            row["source_pack_file"] = path.name
            row["source_line_number"] = line_number
            row["source_row_digest"] = _sha({"file": path.name, "line": line_number, "row": row}, n=16)
            rows.append(row)
    return rows


def build_prompt(seed_row: dict[str, Any]) -> str:
    seed_json = json.dumps(seed_row, sort_keys=True, ensure_ascii=False)
    return f"""Convert this one generated primitive-pack row into one candidate primitive JSON object.

Required output fields:
- primitive_id: stable candidate id derived from record_id, without adding version suffixes
- kind: primitive or primitive_group
- title
- input_edge
- output_edge
- source_refs: at least one object with label and url or source path
- proof_requirements
- promotion_blockers
- dedupe_key
- contract: object with summary, input, output, errors
- edge_contract: object with input_edge_description, output_edge_description, preconditions, postconditions, failure_modes, composition_notes
- blackbox: concise string
- effects: non-empty list
- runtime_targets: list
- candidate: true
- serves_truth: false

Rules:
- Return exactly one JSON object.
- No markdown, no prose, no array wrapper.
- Do not claim the primitive is implemented.
- Add blockers for missing source review, unimplemented adapter, and missing proof receipts.
- Keep descriptions compact enough to avoid timeout.

Seed row JSON:
{seed_json}
"""


def _compact_one_json_object(text: str) -> tuple[str, bool]:
    stripped = text.strip()
    if not stripped:
        return text, False
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        stripped = "\n".join(lines).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return text, False
    if not isinstance(parsed, dict):
        return text, False
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True), True


def receipt_for_row(
    seed_row: dict[str, Any],
    *,
    text: str,
    usage: dict[str, Any],
    finish_reason: str | None,
    error: str | None,
    provider: str,
    model: str,
    started_at: float,
) -> dict[str, Any]:
    elapsed = round(time.time() - started_at, 3)
    completion_tokens = int((usage or {}).get("completion_tokens") or 0)
    total_tokens = int((usage or {}).get("total_tokens") or 0)
    return {
        "record_type": "primitive_factory_model_output",
        "output_id": f"pfmo:{_sha({'seed': seed_row.get('source_row_digest'), 'model': model, 'text': text, 'error': error})}",
        "shard_id": f"generated_pack:{seed_row.get('source_pack_file')}:{seed_row.get('row_id')}",
        "run_date": "generated_primitive_packs",
        "lane_id": str(seed_row.get("pack_id") or seed_row.get("source_pack_file") or "generated_primitive_pack"),
        "provider": provider,
        "model": model,
        "prompt_field": "single_primitive_seed_row",
        "prompt_sha256": _sha(build_prompt(seed_row), n=64),
        "raw_candidate_target": 1,
        "useful_candidate_target": 1,
        "assistant_content": text,
        "usage": usage or {},
        "finish_reason": finish_reason,
        "error": error,
        "status": "error" if error else "candidate_model_output",
        "duration_seconds": elapsed,
        "completion_tps": round(completion_tokens / elapsed, 3) if elapsed and completion_tokens else 0,
        "total_tps": round(total_tokens / elapsed, 3) if elapsed and total_tokens else 0,
        "source_seed_row": seed_row,
        "candidate": True,
        "serves_truth": False,
    }


def run(
    *,
    pack_dir: Path,
    out_dir: Path,
    pack_file: str,
    offset: int,
    limit: int,
    model: str,
    provider: str,
    base_url: str,
    cdp_url: str,
    max_tokens: int,
    timeout: int,
    dry_run: bool,
    extract: bool,
) -> dict[str, Any]:
    all_seed_rows = iter_pack_rows(pack_dir, pack_file=pack_file)
    selected = all_seed_rows[max(0, offset):]
    if limit > 0:
        selected = selected[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs_path = out_dir / "model_outputs.jsonl"
    failed_path = out_dir / "failed_model_outputs.jsonl"
    if outputs_path.exists():
        outputs_path.unlink()
    if failed_path.exists():
        failed_path.unlink()

    started = time.time()
    receipts: list[dict[str, Any]] = []
    for index, seed_row in enumerate(selected, start=1):
        call_started = time.time()
        if dry_run:
            receipt = receipt_for_row(
                seed_row,
                text="",
                usage={},
                finish_reason="dry_run",
                error=None,
                provider=provider,
                model=model,
                started_at=call_started,
            ) | {"status": "planned"}
        else:
            try:
                if provider == "openwebui":
                    normalized = cdp_chat(
                        build_prompt(seed_row),
                        system=SYSTEM_PROMPT,
                        model=model,
                        base_url=base_url,
                        cdp_url=cdp_url or None,
                        max_tokens=max_tokens,
                        timeout=timeout,
                    )
                    result_text = str(normalized.get("assistant_content") or "")
                    result_usage = normalized.get("usage") or {}
                    result_finish = normalized.get("finish_reason")
                    result_error = None
                else:
                    provider_config = resolve_provider(provider)
                    response = chat(
                        model,
                        SYSTEM_PROMPT,
                        build_prompt(seed_row),
                        provider_config,
                        max_tokens=max_tokens,
                        timeout=timeout,
                    )
                    result_text = str(response.get("text") or "")
                    result_usage = response.get("usage") or {}
                    result_finish = response.get("finish_reason")
                    result_error = response.get("error")
                    if result_error:
                        raise AssertionError(str(result_error))
                receipt = receipt_for_row(
                    seed_row,
                    text=_compact_one_json_object(result_text)[0],
                    usage=result_usage,
                    finish_reason=result_finish,
                    error=result_error,
                    provider=provider,
                    model=model,
                    started_at=call_started,
                )
            except Exception as exc:  # noqa: BLE001
                receipt = receipt_for_row(
                    seed_row,
                    text="",
                    usage={},
                    finish_reason=None,
                    error=f"{type(exc).__name__}: {exc}",
                    provider=provider,
                    model=model,
                    started_at=call_started,
                )
        _append_jsonl(outputs_path, receipt)
        if receipt.get("error"):
            _append_jsonl(failed_path, receipt)
        receipts.append(receipt)
        checkpoint = {
            "record_type": "single_primitive_openwebui_checkpoint",
            "processed": index,
            "selected": len(selected),
            "latest_output_id": receipt.get("output_id"),
            "latest_error": receipt.get("error") or "",
            "candidate": True,
            "serves_truth": False,
        }
        _write_json(out_dir / "checkpoint.json", checkpoint)

    extraction_manifest: dict[str, Any] = {}
    if extract and not dry_run:
        extraction_manifest = extract_candidates(outputs_path, out_dir / "extracted")

    usage = {
        "prompt_tokens": sum(int((row.get("usage") or {}).get("prompt_tokens") or 0) for row in receipts),
        "completion_tokens": sum(int((row.get("usage") or {}).get("completion_tokens") or 0) for row in receipts),
        "total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in receipts),
    }
    duration = round(time.time() - started, 3)
    manifest = {
        "record_type": "single_primitive_openwebui_run_manifest",
        "source": "generated_primitive_packs",
        "pack_dir": _rel(pack_dir),
        "pack_file": pack_file,
        "out_dir": _rel(out_dir),
        "outputs_path": _rel(outputs_path),
        "failed_outputs_path": _rel(failed_path),
        "offset": offset,
        "limit": limit,
        "selected_count": len(selected),
        "model": model,
        "provider": provider,
        "mode": "cdp" if provider == "openwebui" else "direct",
        "one_call_per_primitive": True,
        "raw_candidate_target": 1,
        "useful_candidate_target": 1,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "dry_run": dry_run,
        "error_count": sum(1 for row in receipts if row.get("error")),
        "usage": usage,
        "duration_seconds": duration,
        "accepted_count": extraction_manifest.get("accepted_count", 0) if extraction_manifest else 0,
        "rejected_count": extraction_manifest.get("rejected_count", 0) if extraction_manifest else 0,
        "extraction_manifest": extraction_manifest,
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(out_dir / "manifest.json", manifest)
    return manifest


def _self_test() -> int:
    rows = iter_pack_rows(PACK_DIR, pack_file="primitive_cloud_guardrail_runtime_pack.md")
    ok = bool(rows) and {"row_id", "record_id", "input_edge", "output_edge"}.issubset(rows[0])
    prompt = build_prompt(rows[0]) if rows else ""
    compacted, changed = _compact_one_json_object('{"candidate": true, "serves_truth": false}')
    ok = (
        ok
        and "Return exactly one JSON object" in prompt
        and "Seed row JSON" in prompt
        and changed
        and compacted == '{"candidate":true,"serves_truth":false}'
    )
    print("PASS - single primitive Open WebUI runner parses pack rows and builds one-row prompts." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", default=str(PACK_DIR))
    parser.add_argument("--pack-file", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--provider", choices=["openwebui", "ollama", "openrouter"], default="openwebui")
    parser.add_argument("--base-url", default=OPENWEBUI_DEFAULT_BASE_URL)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--max-tokens", type=int, default=1400)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-extract", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    out_dir = Path(args.out_dir) if args.out_dir else _resource(_now().replace(":", "-"))
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    try:
        manifest = run(
            pack_dir=Path(args.pack_dir),
            out_dir=out_dir,
            pack_file=args.pack_file,
            offset=args.offset,
            limit=args.limit,
            model=args.model,
            provider=args.provider,
            base_url=args.base_url,
            cdp_url=args.cdp_url,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            dry_run=args.dry_run,
            extract=not args.no_extract,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
