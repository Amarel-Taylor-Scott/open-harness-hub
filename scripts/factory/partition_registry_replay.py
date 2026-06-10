#!/usr/bin/env python3
"""Build a partition registry and verify replayable index deltas.

This is a local, stdlib-only audit primitive for the million-object path. It
checks that partition manifests and append-only index delta files can be
discovered, summarized, and replayed without doing a full catalog rebuild.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.factory.index_delta_emitter import emit_index_delta


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_hash_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _stable_hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return _stable_hash_bytes(raw)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        records.append(value)
    return records


def _resolve_path(raw_path: str, manifest_path: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    candidates = [
        (manifest_path.parent / path).resolve(),
        Path(raw_path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _discover_manifest_paths(paths: list[str], dirs: list[str]) -> list[Path]:
    discovered: list[Path] = []
    for raw in paths:
        discovered.append(Path(raw).resolve())
    for raw_dir in dirs:
        base = Path(raw_dir).resolve()
        discovered.extend(base.rglob("partition-manifest.json"))
        discovered.extend(base.rglob("partition-manifest.yaml"))
    unique: dict[str, Path] = {}
    for path in discovered:
        unique[str(path)] = path
    return sorted(unique.values(), key=lambda p: str(p))


def _partition_entry(manifest_path: Path, manifest: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    partition_id = str(manifest.get("partition_id") or "")
    if not partition_id:
        raise ValueError(f"{manifest_path}: missing partition_id")
    delta_paths = [
        str(_resolve_path(str(raw), manifest_path))
        for raw in manifest.get("index_delta_paths", [])
    ]
    return partition_id, {
        "partition_id": partition_id,
        "manifest_path": str(manifest_path),
        "manifest_hash": _stable_hash_bytes(manifest_path.read_bytes()),
        "partition_kind": manifest.get("partition_kind"),
        "run_id": manifest.get("run_id"),
        "source_surface_id": manifest.get("source_surface_id", ""),
        "tenant_id": manifest.get("tenant_id", ""),
        "object_count": manifest.get("object_count", 0),
        "shard_paths": manifest.get("shard_paths", []),
        "index_delta_paths": delta_paths,
        "content_hash": manifest.get("content_hash", ""),
        "privacy_summary": manifest.get("privacy_summary", {}),
        "quality_summary": manifest.get("quality_summary", {}),
        "created": manifest.get("created", ""),
        "updated": manifest.get("updated", ""),
    }


def build_partition_registry(
    *,
    manifest_paths: list[str] | None = None,
    manifest_dirs: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Build a compact registry from partition manifest files."""
    paths = _discover_manifest_paths(manifest_paths or [], manifest_dirs or [])
    partitions: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    total_objects = 0
    for path in paths:
        manifest = _read_json(path)
        partition_id, entry = _partition_entry(path, manifest)
        if partition_id in partitions:
            duplicates.append(partition_id)
        partitions[partition_id] = entry
        if isinstance(entry.get("object_count"), int):
            total_objects += entry["object_count"]

    registry = {
        "version": "0.1.0",
        "generated_at": _utc_now(),
        "partition_count": len(partitions),
        "total_objects": total_objects,
        "duplicates": duplicates,
        "partitions": partitions,
    }
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return registry


def verify_replay(
    *,
    registry_path: str | None = None,
    registry: dict[str, Any] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Replay index deltas from a registry and report idempotency issues."""
    if registry is None:
        if registry_path is None:
            raise ValueError("registry_path or registry is required")
        registry = _read_json(Path(registry_path))

    partitions = registry.get("partitions", {})
    if not isinstance(partitions, dict):
        raise ValueError("registry missing partitions map")

    errors: list[str] = []
    warnings: list[str] = []
    seen_delta_ids: set[str] = set()
    replay_state: dict[str, dict[str, Any]] = {}
    index_kind_counts: dict[str, int] = {}
    operation_counts: dict[str, int] = {}

    for partition_id, entry in sorted(partitions.items()):
        if not isinstance(entry, dict):
            errors.append(f"{partition_id}: registry entry must be object")
            continue
        delta_paths = entry.get("index_delta_paths", [])
        if not delta_paths:
            warnings.append(f"{partition_id}: no index_delta_paths")
            continue
        for raw_path in delta_paths:
            delta_path = Path(str(raw_path))
            if not delta_path.exists():
                errors.append(f"{partition_id}: missing delta file {delta_path}")
                continue
            try:
                deltas = _read_jsonl(delta_path)
            except (json.JSONDecodeError, ValueError) as exc:
                errors.append(str(exc))
                continue
            for i, delta in enumerate(deltas, 1):
                delta_id = str(delta.get("delta_id") or "")
                if not delta_id:
                    errors.append(f"{delta_path}:{i}: missing delta_id")
                    continue
                if delta_id in seen_delta_ids:
                    errors.append(f"{delta_path}:{i}: duplicate delta_id {delta_id}")
                seen_delta_ids.add(delta_id)

                actual_partition = delta.get("partition_id")
                if actual_partition != partition_id:
                    errors.append(f"{delta_path}:{i}: partition_id {actual_partition!r} does not match registry {partition_id!r}")

                operation = str(delta.get("operation") or "")
                operation_counts[operation] = operation_counts.get(operation, 0) + 1
                index_record = delta.get("index_record")
                if not isinstance(index_record, dict):
                    errors.append(f"{delta_path}:{i}: missing index_record object")
                    continue
                index_record_id = str(index_record.get("index_record_id") or "")
                if not index_record_id:
                    errors.append(f"{delta_path}:{i}: missing index_record.index_record_id")
                    continue
                content_hash = delta.get("content_hash")
                if isinstance(content_hash, str) and content_hash:
                    actual_hash = _stable_hash_json(index_record)
                    if actual_hash != content_hash:
                        errors.append(f"{delta_path}:{i}: content_hash mismatch for {delta_id}")

                key = str((delta.get("replay_policy") or {}).get("idempotency_key") or index_record_id)
                if operation in {"upsert", "replace"}:
                    replay_state[key] = index_record
                elif operation == "delete":
                    replay_state.pop(key, None)
                else:
                    errors.append(f"{delta_path}:{i}: unsupported operation {operation!r}")

                kind = str(index_record.get("index_kind") or "unknown")
                index_kind_counts[kind] = index_kind_counts.get(kind, 0) + 1

    report = {
        "version": "0.1.0",
        "generated_at": _utc_now(),
        "ok": not errors,
        "partition_count": len(partitions),
        "delta_count": len(seen_delta_ids),
        "replayed_record_count": len(replay_state),
        "index_kind_counts": index_kind_counts,
        "operation_counts": operation_counts,
        "errors": errors,
        "warnings": warnings,
    }
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        shard = base / "objects.jsonl"
        shard.write_text(
            "\n".join([
                json.dumps({
                    "object_id": "procedure/demo/source-governance",
                    "object_type": "checklist_item",
                    "text": "Route the source through governance checks before indexing.",
                    "labels": ["governance.source"],
                }),
                json.dumps({
                    "object_id": "procedure/demo/replay-audit",
                    "object_type": "checklist_item",
                    "text": "Replay emitted deltas and compare idempotent index state.",
                    "labels": ["index.replay"],
                }),
            ]) + "\n",
            encoding="utf-8",
        )
        emit_index_delta(
            input_path=str(shard),
            partition_id="demo/replay/000001",
            output_dir=str(base / "out"),
            emit=["keyword", "facet"],
        )
        registry_path = base / "registry.json"
        report_path = base / "replay-report.json"
        registry = build_partition_registry(
            manifest_dirs=[str(base / "out")],
            output_path=str(registry_path),
        )
        report = verify_replay(registry=registry, output_path=str(report_path))
        assert registry["partition_count"] == 1
        assert report["ok"] is True
        assert report["delta_count"] == 4
        print(json.dumps({
            "ok": True,
            "partition_count": registry["partition_count"],
            "delta_count": report["delta_count"],
            "replayed_record_count": report["replayed_record_count"],
        }, indent=2))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build partition registries and verify index delta replay.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest", action="append", default=[])
    parser.add_argument("--manifest-dir", action="append", default=[])
    parser.add_argument("--registry-output")
    parser.add_argument("--registry-input")
    parser.add_argument("--replay-report-output")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.verify_only:
        if not args.registry_input:
            parser.error("--verify-only requires --registry-input")
        report = verify_replay(
            registry_path=args.registry_input,
            output_path=args.replay_report_output,
        )
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if report["ok"] else 1

    registry = build_partition_registry(
        manifest_paths=args.manifest,
        manifest_dirs=args.manifest_dir,
        output_path=args.registry_output,
    )
    report = verify_replay(
        registry=registry,
        output_path=args.replay_report_output,
    )
    print(json.dumps({
        "ok": report["ok"],
        "partition_count": registry["partition_count"],
        "delta_count": report["delta_count"],
        "replayed_record_count": report["replayed_record_count"],
        "errors": report["errors"],
        "warnings": report["warnings"],
    }, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
