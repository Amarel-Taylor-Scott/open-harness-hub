#!/usr/bin/env python3
"""Verify generated primitive candidates deterministically.

This stage turns extracted model rows into verified candidate rows. It does
not promote truth: verified here means the row is well-shaped, source-backed
by URL syntax, deduped, and has explicit proof obligations.
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

from scripts._config import PRIMITIVE_FACTORY_BATCH_RUNS_DIR, REPO_ROOT  # noqa: E402

REQUIRED_FIELDS = (
    "primitive_id",
    "kind",
    "title",
    "input_edge",
    "output_edge",
    "contract",
    "blackbox",
    "effects",
    "source_refs",
    "mutators",
    "proof_requirements",
    "promotion_blockers",
    "dedupe_key",
    "candidate",
    "serves_truth",
)

ALLOWED_KINDS = {"primitive", "primitive_group"}
GROUP_MIN_HIDDEN_EDGES = 3
DAILY_SHARDS_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "daily_shards_20k"
PLACEHOLDER_SOURCE_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "example.invalid",
    "internal.docs",
}
LOCAL_SOURCE_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
}
PRIVATE_SOURCE_SUFFIXES = (
    ".local",
    ".localhost",
    ".internal",
    ".test",
    ".invalid",
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


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
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _source_urls(source_refs: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(source_refs, str):
        source_refs = [source_refs]
    if not isinstance(source_refs, list):
        return urls
    for ref in source_refs:
        if isinstance(ref, str):
            urls.append(_extract_url_from_source_ref_string(ref))
        elif isinstance(ref, dict):
            value = (
                ref.get("url")
                or ref.get("ref")
                or ref.get("href")
                or ref.get("source_url")
                or ref.get("uri")
            )
            if isinstance(value, str):
                urls.append(value)
    return urls


def _extract_url_from_source_ref_string(value: str) -> str:
    text = value.strip()
    if "=" in text:
        label, possible_url = text.split("=", 1)
        if label.strip() and possible_url.strip():
            return possible_url.strip()
    return text


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _valid_public_source_url(value: str) -> bool:
    if not _valid_url(value):
        return False
    parsed = urlparse(value)
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        return False
    if host in PLACEHOLDER_SOURCE_HOSTS or host in LOCAL_SOURCE_HOSTS:
        return False
    if host.startswith("internal.") or any(host.endswith(suffix) for suffix in PRIVATE_SOURCE_SUFFIXES):
        return False
    if host.startswith("10.") or host.startswith("192.168."):
        return False
    if host.startswith("172."):
        parts = host.split(".")
        if len(parts) > 1 and parts[1].isdigit() and 16 <= int(parts[1]) <= 31:
            return False
    return True


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _field_missing(row: dict[str, Any], field: str) -> bool:
    value = row.get(field)
    return value is None or value == "" or value == [] or value == {}


def _edge_key(row: dict[str, Any]) -> str:
    return "::".join(
        str(row.get(field) or "").strip().lower()
        for field in ("kind", "input_edge", "output_edge", "dedupe_key")
    )


def _normalize_kind(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value.strip().replace("-", "_")


def _normalize_contract(row: dict[str, Any]) -> None:
    contract = row.get("contract")
    if isinstance(contract, str) and contract.strip():
        row["contract"] = {"summary": contract.strip()}


def _normalize_source_refs(row: dict[str, Any], source_ref_aliases: dict[str, str]) -> None:
    source_refs = row.get("source_refs")
    if isinstance(source_refs, str):
        source_refs = [source_refs]
    if not isinstance(source_refs, list):
        return
    normalized: list[Any] = []
    changed = False
    for ref in source_refs:
        if not isinstance(ref, str):
            normalized.append(ref)
            continue
        text = ref.strip()
        if text in source_ref_aliases:
            normalized.append({"label": text, "url": source_ref_aliases[text]})
            changed = True
            continue
        if "=" not in text:
            normalized.append(ref)
            continue
        label, url = text.split("=", 1)
        label = label.strip()
        url = url.strip()
        if label and _valid_url(url):
            normalized.append({"label": label, "url": url})
            changed = True
        else:
            normalized.append(ref)
    if changed:
        row["source_refs"] = normalized
        _append_normalization_note(row, "source_refs_label_equals_url_normalized")


def _normalize_proof_requirements(row: dict[str, Any]) -> None:
    proofs = row.get("proof_requirements")
    if isinstance(proofs, str) and proofs.strip():
        proofs = [proofs.strip()]
    if not isinstance(proofs, list):
        return
    normalized = [proof for proof in proofs if proof]
    if len(normalized) >= 2:
        if normalized != proofs:
            row["proof_requirements"] = normalized
        return
    text = _text_blob(row)
    if any(term in text for term in ("source", "api", "http", "url", "endpoint")):
        normalized.append("source_ref_resolution")
    if any(term in text for term in ("schema", "parse", "json", "record", "batch")):
        normalized.append("contract_fixture_validation")
    normalized.append("candidate_boundary_gate")
    deduped: list[Any] = []
    for proof in normalized:
        if proof not in deduped:
            deduped.append(proof)
    row["proof_requirements"] = deduped
    _append_normalization_note(row, "proof_requirements_completed_from_candidate_shape")
    _append_promotion_blocker(row, "inferred_proof_requirements_need_test_review")


def _normalize_effects(row: dict[str, Any]) -> None:
    effects = row.get("effects")
    if not isinstance(effects, list):
        return
    normalized: list[Any] = []
    changed = False
    for effect in effects:
        if isinstance(effect, str) and effect.strip():
            normalized.append({"effect": effect.strip(), "target": row.get("output_edge") or "unknown"})
            changed = True
        else:
            normalized.append(effect)
    if changed:
        row["effects"] = normalized
        _append_normalization_note(row, "string_effects_wrapped")


def _append_normalization_note(row: dict[str, Any], note: str) -> None:
    notes = row.get("normalization_notes")
    if not isinstance(notes, list):
        notes = []
    if note not in notes:
        notes.append(note)
    row["normalization_notes"] = notes


def _append_promotion_blocker(row: dict[str, Any], blocker: str) -> None:
    blockers = row.get("promotion_blockers")
    if isinstance(blockers, str) and blockers.strip():
        blockers = [blockers.strip()]
    if not isinstance(blockers, list):
        blockers = []
    if blocker not in blockers:
        blockers.append(blocker)
    row["promotion_blockers"] = blockers


def _text_blob(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("primitive_id") or ""),
        str(row.get("title") or ""),
        str(row.get("input_edge") or ""),
        str(row.get("output_edge") or ""),
        str(row.get("blackbox") or ""),
        json.dumps(row.get("effects") or [], sort_keys=True),
    ]
    return " ".join(parts).lower()


def _infer_mutators(row: dict[str, Any]) -> list[str]:
    text = _text_blob(row)
    mutators: list[str] = ["input_envelope_wrapper", "output_wrapper", "schema_validator_inserter"]
    if any(term in text for term in ("http", "api", "request", "endpoint")):
        mutators.append("api_endpoint_wrapper")
    if any(term in text for term in ("json", "deserialize", "parse")):
        mutators.append("json_to_dataclass")
    if any(term in text for term in ("filter", "field", "map", "param")):
        mutators.append("field_project")
    if any(term in text for term in ("page", "pagination", "cursor")):
        mutators.append("pagination_expander")
    if any(term in text for term in ("receipt", "artifact", "manifest", "emit")):
        mutators.append("artifact_reference")
    deduped: list[str] = []
    for mutator in mutators:
        if mutator not in deduped:
            deduped.append(mutator)
    return deduped


def _normalize_mutators(row: dict[str, Any]) -> None:
    mutators = row.get("mutators")
    if isinstance(mutators, str) and mutators.strip():
        row["mutators"] = [part.strip() for part in mutators.replace(";", ",").split(",") if part.strip()]
        _append_normalization_note(row, "string_mutators_split")
        return
    if isinstance(mutators, list) and mutators:
        return
    row["mutators"] = _infer_mutators(row)
    _append_normalization_note(row, "mutators_inferred_from_candidate_shape")
    _append_promotion_blocker(row, "inferred_mutators_need_human_or_test_review")


def _normalize_group_contract(row: dict[str, Any]) -> None:
    if row.get("kind") != "primitive_group":
        return
    group_contract = row.get("group_contract")
    top_level_hidden_edges = _as_list(row.get("hidden_member_edges"))
    if isinstance(group_contract, dict):
        if len(_as_list(group_contract.get("hidden_member_edges"))) < GROUP_MIN_HIDDEN_EDGES and len(top_level_hidden_edges) >= GROUP_MIN_HIDDEN_EDGES:
            group_contract["hidden_member_edges"] = top_level_hidden_edges
            _append_normalization_note(row, "group_hidden_edges_moved_from_top_level")
        return
    if not isinstance(group_contract, str) or not group_contract.strip():
        if len(top_level_hidden_edges) >= GROUP_MIN_HIDDEN_EDGES:
            row["group_contract"] = {
                "visible_input": row.get("input_edge") or "",
                "visible_output": row.get("output_edge") or "",
                "hidden_member_edges": top_level_hidden_edges,
                "summary": "Group contract repaired from top-level hidden_member_edges.",
            }
            _append_normalization_note(row, "group_contract_repaired_from_top_level_hidden_edges")
        return
    text = group_contract.strip()
    hidden_edges: list[str] = []
    marker = "members:"
    lower = text.lower()
    if marker in lower:
        members = text[lower.index(marker) + len(marker):]
        if "." in members:
            members = members.split(".", 1)[0]
        hidden_edges = [
            part.strip().replace(" ", "_")
            for part in members.replace(" and ", ",").split(",")
            if part.strip()
        ]
    if len(hidden_edges) < GROUP_MIN_HIDDEN_EDGES and len(top_level_hidden_edges) >= GROUP_MIN_HIDDEN_EDGES:
        hidden_edges = [str(edge) for edge in top_level_hidden_edges]
    row["group_contract"] = {
        "visible_input": row.get("input_edge") or "",
        "visible_output": row.get("output_edge") or "",
        "hidden_member_edges": hidden_edges,
        "summary": text,
    }
    _append_normalization_note(row, "group_contract_string_normalized")


def _normalize_candidate_row(row: dict[str, Any], source_ref_aliases: dict[str, str]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["kind"] = _normalize_kind(normalized.get("kind"))
    _normalize_contract(normalized)
    _normalize_source_refs(normalized, source_ref_aliases)
    _normalize_effects(normalized)
    _normalize_mutators(normalized)
    _normalize_proof_requirements(normalized)
    _normalize_group_contract(normalized)
    return normalized


def _build_source_ref_aliases(run_date: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    shard_path = _resource(run_date) / "shards.jsonl"
    if not shard_path.exists():
        return aliases
    for row in _read_jsonl(shard_path):
        for ref in _as_list(row.get("source_refs")):
            if not isinstance(ref, dict):
                continue
            url = ref.get("url")
            if not isinstance(url, str) or not _valid_url(url):
                continue
            for key in ("id", "label", "source_id", "title"):
                value = ref.get(key)
                if isinstance(value, str) and value.strip():
                    aliases.setdefault(value.strip(), url)
    return aliases


def _candidate_errors(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if _field_missing(row, field)]
    if missing:
        errors.append("missing_required_fields:" + ",".join(missing))
    if row.get("candidate") is not True:
        errors.append("candidate_not_true")
    if row.get("serves_truth") is not False:
        errors.append("serves_truth_not_false")
    if str(row.get("kind") or "") not in ALLOWED_KINDS:
        errors.append("unsupported_kind")
    if str(row.get("input_edge") or "").strip() == str(row.get("output_edge") or "").strip():
        errors.append("input_output_edge_same")
    urls = _source_urls(row.get("source_refs"))
    if not urls:
        errors.append("missing_source_ref_url")
    elif not any(_valid_url(url) for url in urls):
        errors.append("no_valid_source_ref_url")
    elif not any(_valid_public_source_url(url) for url in urls):
        errors.append("no_public_source_ref_url")
    if len(_as_list(row.get("proof_requirements"))) < 2:
        errors.append("weak_proof_requirements")
    if len(_as_list(row.get("mutators"))) < 1:
        errors.append("missing_mutators")
    if len(_as_list(row.get("effects"))) < 1:
        errors.append("missing_effects")
    contract = row.get("contract")
    if not isinstance(contract, dict):
        errors.append("contract_not_object")
    elif not contract:
        errors.append("contract_empty")
    if str(row.get("kind") or "") == "primitive_group":
        group_contract = row.get("group_contract")
        if not isinstance(group_contract, dict):
            errors.append("group_contract_missing")
        else:
            hidden_edges = _as_list(group_contract.get("hidden_member_edges"))
            if len(hidden_edges) < GROUP_MIN_HIDDEN_EDGES:
                errors.append("group_contract_hidden_edges_lt_3")
            visible_input = str(group_contract.get("visible_input") or "")
            visible_output = str(group_contract.get("visible_output") or "")
            if visible_input and visible_input != str(row.get("input_edge") or ""):
                errors.append("group_visible_input_mismatch")
            if visible_output and visible_output != str(row.get("output_edge") or ""):
                errors.append("group_visible_output_mismatch")
    return errors


def verify_candidates(*, run_date: str, out_dir: Path, source_root: Path, limit: int = 0) -> dict[str, Any]:
    source_files = sorted(source_root.glob("**/extracted/extracted_candidates.jsonl"))
    seen_edges: dict[str, str] = {}
    verified: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    verification_started = _now()
    source_row_count = 0
    source_ref_aliases = _build_source_ref_aliases(run_date)

    for path in source_files:
        for row in _read_jsonl(path):
            source_row_count += 1
            if limit and source_row_count > limit:
                break
            row = _normalize_candidate_row(row, source_ref_aliases)
            edge_key = _edge_key(row)
            errors = _candidate_errors(row)
            verification_id = f"pcv:{_sha({'row': row, 'edge_key': edge_key})}"
            base = {
                "record_type": "primitive_candidate_verification_receipt",
                "verification_id": verification_id,
                "run_date": run_date,
                "source_candidate_id": row.get("extracted_candidate_id") or "",
                "source_candidate_path": _rel(path),
                "primitive_id": row.get("primitive_id") or "",
                "dedupe_key": row.get("dedupe_key") or "",
                "edge_key": edge_key,
                "source_model": row.get("source_model") or "",
                "source_provider": row.get("source_provider") or "",
                "verified_at": verification_started,
                "candidate": True,
                "serves_truth": False,
            }
            if errors:
                rejected.append({**base, "status": "rejected", "errors": errors, "candidate_row": row})
                continue
            if edge_key in seen_edges:
                duplicates.append(
                    {
                        **base,
                        "status": "duplicate",
                        "duplicate_of": seen_edges[edge_key],
                        "candidate_row": row,
                    }
                )
                continue
            seen_edges[edge_key] = verification_id
            verified.append(
                {
                    **row,
                    "record_type": "primitive_verified_candidate",
                    "verification_id": verification_id,
                    "verification_status": "verified_candidate",
                    "verification_level": "L3_shape_source_proof_deduped",
                    "verified_at": verification_started,
                    "source_candidate_path": _rel(path),
                    "candidate": True,
                    "serves_truth": False,
                }
            )
        if limit and source_row_count >= limit:
            break

    out_dir.mkdir(parents=True, exist_ok=True)
    verified_path = out_dir / "verified_candidates.jsonl"
    duplicates_path = out_dir / "duplicate_candidates.jsonl"
    rejected_path = out_dir / "rejected_candidates.jsonl"
    manifest_path = out_dir / "manifest.json"
    _write_jsonl(verified_path, verified)
    _write_jsonl(duplicates_path, duplicates)
    _write_jsonl(rejected_path, rejected)
    manifest = {
        "record_type": "primitive_candidate_verification_manifest",
        "run_date": run_date,
        "source_root": _rel(source_root),
        "out_dir": _rel(out_dir),
        "source_files": len(source_files),
        "source_row_count": source_row_count,
        "verified_count": len(verified),
        "duplicate_count": len(duplicates),
        "rejected_count": len(rejected),
        "verified_path": _rel(verified_path),
        "duplicates_path": _rel(duplicates_path),
        "rejected_path": _rel(rejected_path),
        "verified_candidate_level": "L3_shape_public_source_proof_deduped",
        "source_ref_policy": "public_http_url_required",
        "source_ref_rejection_hosts": sorted(PLACEHOLDER_SOURCE_HOSTS | LOCAL_SOURCE_HOSTS),
        "source_ref_rejection_suffixes": list(PRIVATE_SOURCE_SUFFIXES),
        "source_ref_alias_count": len(source_ref_aliases),
        "promotion_note": "Verified candidates are still candidate-only and do not serve truth.",
        "candidate": True,
        "serves_truth": False,
        "created_at": _now(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "batch" / "extracted"
        good = {
            "primitive_id": "grp:test@candidate",
            "kind": "primitive_group",
            "title": "Test Group",
            "input_edge": "A",
            "output_edge": "B",
            "contract": {"fields": ["a"], "produces": ["b"]},
            "group_contract": {
                "visible_input": "A",
                "visible_output": "B",
                "hidden_member_edges": ["A->X", "X->Y", "Y->B"],
            },
            "blackbox": "Turns A into B.",
            "effects": [{"type": "artifact_write"}],
            "source_refs": [{"url": "https://docs.python.org/3/library/json.html"}],
            "mutators": ["schema_validator_inserter"],
            "proof_requirements": ["schema_validation", "golden_fixture"],
            "promotion_blockers": ["review_required"],
            "dedupe_key": "test",
            "candidate": True,
            "serves_truth": False,
        }
        repaired = {
            "primitive_id": "prim:test.repaired",
            "kind": "primitive",
            "title": "Repairable primitive",
            "input_edge": "RawApiResponse",
            "output_edge": "ParsedRecordBatch",
            "contract": "Parse raw API JSON into records.",
            "blackbox": "Parses JSON and emits a typed batch.",
            "effects": ["parse_json"],
            "source_refs": ["docs=https://docs.python.org/3/library/urllib.request.html"],
            "mutators": [],
            "proof_requirements": ["json_schema_conformance", "golden_fixture"],
            "promotion_blockers": ["review_required"],
            "dedupe_key": "repaired",
            "candidate": True,
            "serves_truth": False,
        }
        group_repaired = {
            "primitive_id": "grp:test.repaired",
            "kind": "primitive-group",
            "title": "Repairable group",
            "input_edge": "A",
            "output_edge": "Z",
            "contract": {"summary": "Collapse a route."},
            "group_contract": "Repairable group route.",
            "hidden_member_edges": ["A->B", "B->C", "C->Z"],
            "blackbox": "Collapses a route.",
            "effects": ["route_emit"],
            "source_refs": [{"url": "https://docs.python.org/3/library/pathlib.html"}],
            "mutators": [],
            "proof_requirements": ["route_fixture"],
            "promotion_blockers": ["review_required"],
            "dedupe_key": "group_repaired",
            "candidate": True,
            "serves_truth": False,
        }
        _write_jsonl(source / "extracted_candidates.jsonl", [good, good, repaired, group_repaired])
        manifest = verify_candidates(run_date="2099-01-01", out_dir=root / "verified", source_root=root)
        ok = manifest["verified_count"] == 3 and manifest["duplicate_count"] == 1 and manifest["rejected_count"] == 0
    print("PASS - primitive candidate verification keeps rows candidate-only." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--source-root", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    source_root = Path(args.source_root) if args.source_root else _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / args.date
    out_dir = Path(args.out_dir) if args.out_dir else _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates" / args.date
    if not source_root.is_absolute():
        source_root = _resource(source_root)
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    try:
        manifest = verify_candidates(run_date=args.date, out_dir=out_dir, source_root=source_root, limit=args.limit)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
