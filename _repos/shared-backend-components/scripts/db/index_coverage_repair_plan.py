#!/usr/bin/env python3
"""Plan missing index records for staged component candidate rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


DEFAULT_INDEX_KINDS = ["keyword", "vector", "graph", "facet", "quality"]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_jsonl(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{p}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _safe_slug(value: str, max_len: int = 56) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:max_len].strip("-") or "object"


def _hash(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _body(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("body")
    return value if isinstance(value, dict) else {}


def _index_text(row: dict[str, Any]) -> str:
    body = _body(row)
    parts = [
        str(row.get("title") or ""),
        str(row.get("object_type") or ""),
        str(body.get("domain") or ""),
        str(body.get("risk_tier") or ""),
        str(body.get("task") or ""),
        "inputs " + " ".join(str(item) for item in body.get("inputs", []) or []),
        "outputs " + " ".join(str(item) for item in body.get("outputs", []) or []),
        "stages " + " ".join(str(item) for item in body.get("required_stages", []) or []),
        "labels " + " ".join(str(item) for item in body.get("label_paths", []) or []),
    ]
    return " ".join(part for part in parts if part).strip()


def _group_refs(ref_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in ref_rows:
        object_id = str(row.get("object_id") or "")
        if object_id:
            grouped.setdefault(object_id, []).append(row)
    return grouped


def _embedding_by_subject(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("subject_id")): row for row in rows if row.get("subject_id")}


def _existing_kind_map(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for row in rows:
        subject_id = str(row.get("subject_id") or "")
        index_kind = str(row.get("index_kind") or "")
        if subject_id and index_kind:
            out.setdefault(subject_id, set()).add(index_kind)
    return out


def _make_index_record(
    *,
    obj: dict[str, Any],
    kind: str,
    embedding: dict[str, Any] | None,
    refs: list[dict[str, Any]],
    run_id: str,
    generated_at: str,
) -> dict[str, Any]:
    object_id = str(obj.get("object_id") or "")
    body = _body(obj)
    entity_ids = sorted({str(row.get("entity_id")) for row in refs if row.get("entity_id")})
    key = f"{object_id}:{kind}:{obj.get('content_hash') or ''}:{run_id}"
    return {
        "index_record_id": f"index/{kind}/{_safe_slug(object_id)}-{_hash(key)}",
        "index_kind": kind,
        "subject_id": object_id,
        "subject_type": str(obj.get("object_type") or "candidate_component"),
        "text": _index_text(obj),
        "metadata": {
            "domain": body.get("domain", ""),
            "risk_tier": body.get("risk_tier", ""),
            "label_paths": body.get("label_paths", []),
            "entity_ids": entity_ids,
            "source_record_id": obj.get("source_record_id", ""),
            "dedupe_cluster_id": obj.get("dedupe_cluster_id", ""),
            "content_hash": obj.get("content_hash", ""),
            "repair_run_id": run_id,
            "repair_generated_at": generated_at,
        },
        "embedding_model": str(embedding.get("embedding_model") or "") if kind == "vector" and embedding else "",
        "embedding_ref": str(embedding.get("embedding_id") or "") if kind == "vector" and embedding else "",
        "graph_edges": [
            {"src_id": object_id, "dst_id": entity_id, "role": "linked_entity", "confidence": 0.82}
            for entity_id in entity_ids
        ] if kind == "graph" else [],
    }


def build_index_coverage_repair_plan(
    *,
    normalized_objects_jsonl: str | Path,
    existing_index_records_jsonl: str | Path,
    output_dir: str | Path,
    object_embeddings_jsonl: str | Path | None = None,
    object_entity_refs_jsonl: str | Path | None = None,
    run_id: str = "index-coverage-repair",
    required_kinds: list[str] | None = None,
) -> dict[str, Any]:
    objects = _read_jsonl(normalized_objects_jsonl)
    existing = _read_jsonl(existing_index_records_jsonl)
    embeddings = _embedding_by_subject(_read_jsonl(object_embeddings_jsonl))
    refs_by_object = _group_refs(_read_jsonl(object_entity_refs_jsonl))
    kinds = required_kinds or DEFAULT_INDEX_KINDS
    existing_by_subject = _existing_kind_map(existing)
    generated_at = _utc_now()

    missing_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    for obj in objects:
        object_id = str(obj.get("object_id") or "")
        present = existing_by_subject.get(object_id, set())
        missing = [kind for kind in kinds if kind not in present]
        for kind in missing:
            missing_rows.append(_make_index_record(
                obj=obj,
                kind=kind,
                embedding=embeddings.get(object_id),
                refs=refs_by_object.get(object_id, []),
                run_id=run_id,
                generated_at=generated_at,
            ))
        coverage_rows.append({
            "object_id": object_id,
            "present_index_kinds": sorted(present),
            "missing_index_kinds": missing,
            "required_index_kinds": kinds,
            "covered": not missing,
            "has_embedding_work_row": object_id in embeddings,
            "entity_ref_count": len(refs_by_object.get(object_id, [])),
        })

    out = Path(output_dir)
    repair_path = out / "missing-index-records.jsonl"
    coverage_path = out / "index-coverage.jsonl"
    summary_path = out / "index-coverage-repair-plan.json"
    _write_jsonl(repair_path, missing_rows)
    _write_jsonl(coverage_path, coverage_rows)
    counts_by_missing_kind = {kind: sum(1 for row in coverage_rows if kind in row["missing_index_kinds"]) for kind in kinds}
    fully_covered = sum(1 for row in coverage_rows if row["covered"])
    report = {
        "ok": True,
        "run_id": run_id,
        "generated_at": generated_at,
        "inputs": {
            "normalized_objects_jsonl": str(normalized_objects_jsonl),
            "existing_index_records_jsonl": str(existing_index_records_jsonl),
            "object_embeddings_jsonl": str(object_embeddings_jsonl) if object_embeddings_jsonl else "",
            "object_entity_refs_jsonl": str(object_entity_refs_jsonl) if object_entity_refs_jsonl else "",
        },
        "required_index_kinds": kinds,
        "counts": {
            "normalized_objects": len(objects),
            "existing_index_records": len(existing),
            "fully_covered_objects": fully_covered,
            "incomplete_objects": len(objects) - fully_covered,
            "missing_index_records_emitted": len(missing_rows),
            "missing_by_kind": counts_by_missing_kind,
        },
        "files": {
            "missing_index_records": str(repair_path),
            "index_coverage": str(coverage_path),
            "summary": str(summary_path),
        },
        "safety_notes": [
            "This planner writes repair JSONL only; it does not apply SQL or update an index.",
            "Generated repair records should pass load preflight before candidate-table load.",
            "Vector records reference embedding work rows when available but do not compute embeddings.",
        ],
    }
    _write_json(summary_path, report)
    return report


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        objects = base / "normalized-objects.jsonl"
        existing = base / "index-records.jsonl"
        embeddings = base / "object-embeddings.jsonl"
        refs = base / "object-entity-refs.jsonl"
        obj = {
            "object_id": "object/test/component-a",
            "object_type": "candidate_component",
            "title": "Component A",
            "body": {"domain": "test", "task": "Check index coverage", "risk_tier": "medium"},
            "source_record_id": "source/test",
            "dedupe_cluster_id": "dedupe/test",
            "content_hash": "abc",
        }
        objects.write_text(json.dumps(obj) + "\n", encoding="utf-8")
        existing.write_text(json.dumps({"subject_id": obj["object_id"], "index_kind": "keyword"}) + "\n", encoding="utf-8")
        embeddings.write_text(json.dumps({"subject_id": obj["object_id"], "embedding_id": "embedding/test", "embedding_model": "stub"}) + "\n", encoding="utf-8")
        refs.write_text(json.dumps({"object_id": obj["object_id"], "entity_id": "entity/test", "role": "domain"}) + "\n", encoding="utf-8")
        result = build_index_coverage_repair_plan(
            normalized_objects_jsonl=objects,
            existing_index_records_jsonl=existing,
            object_embeddings_jsonl=embeddings,
            object_entity_refs_jsonl=refs,
            output_dir=base / "out",
            run_id="self-test",
        )
        assert result["counts"]["normalized_objects"] == 1
        assert result["counts"]["fully_covered_objects"] == 0
        assert result["counts"]["missing_index_records_emitted"] == 4
    print(json.dumps({"ok": True}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--normalized-objects-jsonl")
    parser.add_argument("--existing-index-records-jsonl")
    parser.add_argument("--object-embeddings-jsonl")
    parser.add_argument("--object-entity-refs-jsonl")
    parser.add_argument("--output-dir", default="dist/index-coverage-repair")
    parser.add_argument("--run-id", default="index-coverage-repair")
    parser.add_argument("--required-kind", action="append")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.normalized_objects_jsonl or not args.existing_index_records_jsonl:
        parser.error("--normalized-objects-jsonl and --existing-index-records-jsonl are required unless --self-test is used")
    result = build_index_coverage_repair_plan(
        normalized_objects_jsonl=args.normalized_objects_jsonl,
        existing_index_records_jsonl=args.existing_index_records_jsonl,
        object_embeddings_jsonl=args.object_embeddings_jsonl,
        object_entity_refs_jsonl=args.object_entity_refs_jsonl,
        output_dir=args.output_dir,
        run_id=args.run_id,
        required_kinds=args.required_kind,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
