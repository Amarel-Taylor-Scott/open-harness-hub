#!/usr/bin/env python3
"""Extract candidate primitive JSONL from primitive factory model receipts.

The model receipts are not truth. This script only normalizes model text into
candidate JSONL and keeps rows blocked from promotion until downstream review.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

DAILY_SHARDS_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "daily_shards_20k"

REQUIRED_FIELDS = (
    "primitive_id",
    "kind",
    "title",
    "input_edge",
    "output_edge",
    "source_refs",
    "proof_requirements",
    "promotion_blockers",
    "dedupe_key",
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _sha(value: Any, *, n: int = 20) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _append_note(row: dict[str, Any], note: str) -> None:
    notes = row.get("normalization_notes")
    if not isinstance(notes, list):
        notes = []
    if note not in notes:
        notes.append(note)
    row["normalization_notes"] = notes


def _append_blocker(row: dict[str, Any], blocker: str) -> None:
    blockers = row.get("promotion_blockers")
    if isinstance(blockers, str) and blockers.strip():
        blockers = [blockers.strip()]
    if not isinstance(blockers, list):
        blockers = []
    if blocker not in blockers:
        blockers.append(blocker)
    row["promotion_blockers"] = blockers


def _source_refs_have_url(source_refs: Any) -> bool:
    for ref in _as_list(source_refs):
        if isinstance(ref, str) and _valid_url(ref):
            return True
        if isinstance(ref, dict):
            value = ref.get("url") or ref.get("href") or ref.get("source_url") or ref.get("uri")
            if isinstance(value, str) and _valid_url(value):
                return True
    return False


def _shard_source_refs(run_dates: set[str]) -> dict[str, list[dict[str, Any]]]:
    refs_by_shard: dict[str, list[dict[str, Any]]] = {}
    for run_date in sorted(run_dates):
        shard_path = _resource(run_date) / "shards.jsonl"
        if not shard_path.exists():
            continue
        for row in _read_jsonl(shard_path):
            shard_id = row.get("shard_id")
            if not isinstance(shard_id, str) or not shard_id:
                continue
            refs: list[dict[str, Any]] = []
            for ref in _as_list(row.get("source_refs")):
                if not isinstance(ref, dict):
                    continue
                url = ref.get("url")
                if not isinstance(url, str) or not _valid_url(url):
                    continue
                refs.append(
                    {
                        "label": str(ref.get("id") or ref.get("label") or ref.get("title") or url),
                        "url": url,
                    }
                )
            if refs:
                refs_by_shard[shard_id] = refs
    return refs_by_shard


def _skip_ws(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _wrap_adjacent_object_values(text: str, field: str) -> tuple[str, bool]:
    marker = f'"{field}"'
    decoder = json.JSONDecoder()
    search_from = 0
    changed = False
    while True:
        field_index = text.find(marker, search_from)
        if field_index < 0:
            return text, changed
        colon = text.find(":", field_index + len(marker))
        if colon < 0:
            return text, changed
        start = _skip_ws(text, colon + 1)
        if start >= len(text) or text[start] != "{":
            search_from = start
            continue
        object_spans: list[tuple[int, int]] = []
        pos = start
        while pos < len(text) and text[pos] == "{":
            try:
                _obj, relative_end = decoder.raw_decode(text[pos:])
            except json.JSONDecodeError:
                break
            end = pos + relative_end
            object_spans.append((pos, end))
            comma = _skip_ws(text, end)
            if comma >= len(text) or text[comma] != ",":
                pos = end
                break
            next_pos = _skip_ws(text, comma + 1)
            if next_pos >= len(text) or text[next_pos] != "{":
                pos = end
                break
            pos = next_pos
        if len(object_spans) < 2:
            search_from = object_spans[-1][1] if object_spans else start + 1
            continue
        replacement = "[" + ",".join(text[a:b] for a, b in object_spans) + "]"
        replace_end = object_spans[-1][1]
        text = text[:start] + replacement + text[replace_end:]
        changed = True
        search_from = start + len(replacement)


def _parse_candidate_line(line: str) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    try:
        parsed = json.loads(line)
        return parsed if isinstance(parsed, dict) else None, None if isinstance(parsed, dict) else "not_json_object", []
    except json.JSONDecodeError as first_exc:
        repaired = line
        notes: list[str] = []
        for field in ("input_edge", "output_edge"):
            repaired, changed = _wrap_adjacent_object_values(repaired, field)
            if changed:
                notes.append(f"{field}_adjacent_objects_wrapped")
        if repaired != line:
            try:
                parsed = json.loads(repaired)
            except json.JSONDecodeError:
                return None, f"json_decode_error:{first_exc.msg}", []
            if isinstance(parsed, dict):
                return parsed, None, notes
            return None, "not_json_object", []
        return None, f"json_decode_error:{first_exc.msg}", []


def _repair_candidate_from_receipt(row: dict[str, Any], receipt: dict[str, Any], refs_by_shard: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    repaired = dict(row)
    if not _source_refs_have_url(repaired.get("source_refs")):
        shard_refs = refs_by_shard.get(str(receipt.get("shard_id") or ""))
        if shard_refs:
            repaired["source_refs"] = shard_refs
            _append_note(repaired, "source_refs_repaired_from_source_shard")
            _append_blocker(repaired, "repaired_source_refs_need_review")
    return repaired


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _content_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        lines.append(line)
    return lines


def _candidate_error(row: dict[str, Any]) -> str | None:
    if row.get("candidate") is not True:
        return "candidate_not_true"
    if row.get("serves_truth") is not False:
        return "serves_truth_not_false"
    missing = [field for field in REQUIRED_FIELDS if field not in row or row.get(field) in ("", [], None)]
    if missing:
        return "missing_required_fields:" + ",".join(missing)
    return None


def extract_candidates(outputs_path: Path, out_dir: Path) -> dict[str, Any]:
    receipts = _read_jsonl(outputs_path)
    run_dates = {str(receipt.get("run_date")) for receipt in receipts if receipt.get("run_date")}
    refs_by_shard = _shard_source_refs(run_dates)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    extracted_at = _now()

    for receipt in receipts:
        output_id = receipt.get("output_id")
        shard_id = receipt.get("shard_id")
        content = str(receipt.get("assistant_content") or "")
        for line_index, line in enumerate(_content_lines(content), start=1):
            parsed, parse_error, repair_notes = _parse_candidate_line(line)
            if parse_error:
                rejected.append(
                    {
                        "record_type": "primitive_model_candidate_rejection",
                        "reason": parse_error,
                        "source_output_id": output_id,
                        "source_shard_id": shard_id,
                        "line_index": line_index,
                        "line_sample": line[:500],
                        "candidate": True,
                        "serves_truth": False,
                    }
                )
                continue
            assert parsed is not None
            parsed = _repair_candidate_from_receipt(parsed, receipt, refs_by_shard)
            for note in repair_notes:
                _append_note(parsed, note)
            error = _candidate_error(parsed)
            if error:
                rejected.append(
                    {
                        "record_type": "primitive_model_candidate_rejection",
                        "reason": error,
                        "source_output_id": output_id,
                        "source_shard_id": shard_id,
                        "line_index": line_index,
                        "candidate_row": parsed,
                        "candidate": True,
                        "serves_truth": False,
                    }
                )
                continue
            parsed = dict(parsed)
            parsed.setdefault("record_type", "primitive_model_extracted_candidate")
            parsed["extracted_candidate_id"] = f"pmc:{_sha({'output': output_id, 'line': line_index, 'row': parsed})}"
            parsed["source_output_id"] = output_id
            parsed["source_shard_id"] = shard_id
            parsed["source_model"] = receipt.get("model")
            parsed["source_provider"] = receipt.get("provider")
            parsed["extracted_at"] = extracted_at
            parsed["promotion_status"] = "candidate_extracted_needs_review"
            parsed["serves_truth"] = False
            accepted.append(parsed)

    out_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = out_dir / "extracted_candidates.jsonl"
    rejected_path = out_dir / "rejected_candidates.jsonl"
    manifest_path = out_dir / "manifest.json"
    _write_jsonl(candidates_path, accepted)
    _write_jsonl(rejected_path, rejected)
    manifest = {
        "record_type": "primitive_model_candidate_extraction_manifest",
        "outputs_path": str(outputs_path.relative_to(REPO_ROOT) if outputs_path.is_relative_to(REPO_ROOT) else outputs_path),
        "out_dir": str(out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir),
        "candidates_path": str(candidates_path.relative_to(REPO_ROOT) if candidates_path.is_relative_to(REPO_ROOT) else candidates_path),
        "rejected_path": str(rejected_path.relative_to(REPO_ROOT) if rejected_path.is_relative_to(REPO_ROOT) else rejected_path),
        "receipt_count": len(receipts),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "source_ref_shard_count": len(refs_by_shard),
        "candidate": True,
        "serves_truth": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        outputs = root / "model_outputs.jsonl"
        repaired_line = (
            '{"primitive_id":"prim:edge.repair","kind":"primitive","title":"Edge Repair",'
            '"input_edge":{"name":"a","type":"A"},{"name":"b","type":"B"},'
            '"output_edge":{"name":"c","type":"C"},"source_refs":[{"url":"https://example.invalid"}],'
            '"proof_requirements":["schema_validation"],"promotion_blockers":["review_required"],'
            '"dedupe_key":"edge-repair","candidate":true,"serves_truth":false}'
        )
        receipt = {
            "output_id": "pfmo:test",
            "shard_id": "pfs:test",
            "model": "gemma-4-coding",
            "provider": "openwebui",
            "run_date": "2099-01-01",
            "assistant_content": json.dumps(
                {
                    "primitive_id": "prim:test",
                    "kind": "primitive",
                    "title": "Test",
                    "input_edge": "A",
                    "output_edge": "B",
                    "source_refs": ["https://example.invalid"],
                    "proof_requirements": ["schema_validation"],
                    "promotion_blockers": ["review_required"],
                    "dedupe_key": "test",
                    "candidate": True,
                    "serves_truth": False,
                },
                sort_keys=True,
            ),
            "candidate": True,
            "serves_truth": False,
        }
        repair_receipt = dict(receipt)
        repair_receipt["output_id"] = "pfmo:repair"
        repair_receipt["assistant_content"] = repaired_line
        _write_jsonl(outputs, [receipt, repair_receipt])
        manifest = extract_candidates(outputs, root / "out")
        ok = manifest["accepted_count"] == 2 and manifest["rejected_count"] == 0
    print("PASS - extracted primitive model candidates remain candidate-only." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", required=False, default="")
    parser.add_argument("--out-dir", required=False, default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.outputs or not args.out_dir:
        print("FAIL: --outputs and --out-dir are required", file=sys.stderr)
        return 1
    outputs = Path(args.outputs)
    out_dir = Path(args.out_dir)
    if not outputs.is_absolute():
        outputs = _resource(outputs)
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    try:
        manifest = extract_candidates(outputs, out_dir)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
