from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FILE_NAMES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "label_assignment": "label-assignments.jsonl",
    "dimension_value": "dimension-values.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "review_ticket": "review-tickets.jsonl",
    "index_record": "index-records.jsonl",
}


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-")[:72] or "unknown"


def _slug_with_hash(value: str, *, max_slug_len: int = 56, hash_len: int = 12) -> str:
    slug = _safe_slug(value)[:max_slug_len].strip("-") or "unknown"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:hash_len]
    return f"{slug}-{digest}"


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _label(
    *,
    subject_id: str,
    label_set: str,
    label: str,
    path: str = "",
    confidence: float = 0.9,
    review_status: str = "generated_candidate",
) -> dict[str, Any]:
    key = f"{subject_id}:{label_set}:{path or label}"
    return {
        "label_id": f"label/{hashlib.sha256(key.encode('utf-8')).hexdigest()[:20]}",
        "label_set": label_set,
        "label": label,
        "path": path,
        "subject_id": subject_id,
        "subject_type": "normalized_object",
        "confidence": confidence,
        "assigned_by": "use-case-seed-row-exporter",
        "assignment_method": "deterministic",
        "model_route_id": "",
        "provenance": {"source": "cross-domain-use-case-seed"},
        "review_status": review_status,
    }


def _dimension(
    *,
    subject_id: str,
    name: str,
    value: Any,
    value_type: str,
    scale: str = "",
    confidence: float = 0.8,
    review_status: str = "generated_candidate",
) -> dict[str, Any]:
    key = f"{subject_id}:{name}:{json.dumps(value, sort_keys=True, ensure_ascii=False)}"
    return {
        "dimension_id": f"dimension/{hashlib.sha256(key.encode('utf-8')).hexdigest()[:20]}",
        "name": name,
        "subject_id": subject_id,
        "subject_type": "normalized_object",
        "value": value,
        "value_type": value_type,
        "scale": scale,
        "confidence": confidence,
        "assigned_by": "use-case-seed-row-exporter",
        "assignment_method": "deterministic",
        "model_route_id": "",
        "provenance": {"source": "cross-domain-use-case-seed"},
        "review_status": review_status,
    }


def _entity(entity_type: str, canonical_name: str, description: str = "") -> dict[str, Any]:
    key = f"{entity_type}:{canonical_name}"
    slug = _safe_slug(canonical_name.replace(".", " "))
    return {
        "entity_id": f"entity/use-case-seed/{entity_type}/{slug}",
        "entity_type": entity_type,
        "canonical_name": canonical_name,
        "aliases": sorted({canonical_name, canonical_name.replace("_", " "), canonical_name.replace(".", " ")}),
        "identifiers": {
            "namespace": "open-harness.use-case-seed",
            "stable_key": hashlib.sha256(key.encode("utf-8")).hexdigest()[:20],
        },
        "description": description,
        "confidence": 0.88,
        "review_status": "generated_candidate",
    }


def _ref(object_id: str, entity_id: str, role: str, confidence: float = 0.86) -> dict[str, Any]:
    return {
        "object_id": object_id,
        "entity_id": entity_id,
        "role": role,
        "confidence": confidence,
    }


def _entity_type_for_label_path(path: str) -> str:
    head = path.split(".")[0] if path else "label"
    return {
        "domain": "domain",
        "industry": "vertical",
        "jurisdiction": "jurisdiction",
        "law": "law",
        "output": "output_type",
        "risk": "risk_tier",
        "scope": "scope",
        "stage": "pipeline_stage",
        "vertical": "vertical",
        "workflow": "workflow",
    }.get(head, "label_path")


def _add_entity_ref(
    *,
    entities: dict[str, dict[str, Any]],
    refs: dict[tuple[str, str, str], dict[str, Any]],
    object_id: str,
    entity_type: str,
    canonical_name: str,
    role: str,
    description: str = "",
    confidence: float = 0.86,
) -> str:
    entity = _entity(entity_type, canonical_name, description=description)
    entities.setdefault(entity["entity_id"], entity)
    refs.setdefault((object_id, entity["entity_id"], role), _ref(object_id, entity["entity_id"], role, confidence=confidence))
    return entity["entity_id"]


def _embedding_text(normalized: dict[str, Any], seed: dict[str, Any]) -> str:
    body = normalized.get("body", {}) if isinstance(normalized.get("body"), dict) else {}
    parts = [
        str(normalized.get("title", "")),
        str(body.get("domain", "")),
        str(body.get("risk_tier", "")),
        str(body.get("task", "")),
        "inputs " + " ".join(str(item) for item in body.get("inputs", []) or []),
        "outputs " + " ".join(str(item) for item in body.get("outputs", []) or []),
        "stages " + " ".join(str(item) for item in body.get("required_stages", []) or []),
        "labels " + " ".join(str(item) for item in seed.get("label_paths", []) or []),
    ]
    return " ".join(part for part in parts if part).strip()


def _embedding_bucket(seed: dict[str, Any], risk_tier: str) -> str:
    domain = _safe_slug(str(seed.get("domain", "cross_domain")))
    stage_names = [str(item) for item in seed.get("required_stages", []) or []]
    stage_signature = hashlib.sha256("|".join(sorted(stage_names)).encode("utf-8")).hexdigest()[:8]
    output_names = [str(item) for item in seed.get("outputs", []) or []]
    output_signature = hashlib.sha256("|".join(sorted(output_names)).encode("utf-8")).hexdigest()[:8]
    return f"seed-bucket/{domain}/{risk_tier}/{stage_signature}/{output_signature}"


def _embedding_stub(*, object_id: str, text: str, bucket: str, entity_ids: list[str], now: str) -> dict[str, Any]:
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    model = "stub:deterministic-text-v1"
    return {
        "embedding_id": f"embedding/{hashlib.sha256(f'{object_id}:{model}:{text_hash}'.encode('utf-8')).hexdigest()[:20]}",
        "subject_id": object_id,
        "subject_type": "normalized_object",
        "embedding_model": model,
        "text_hash": text_hash,
        "text": text,
        "embedding": "",
        "metadata": {
            "bucket": bucket,
            "bucket_method": "domain+risk+stage_signature+output_signature",
            "entity_ids": sorted(set(entity_ids)),
            "actual_embedding_required": True,
        },
        "created_at": now,
    }


def _risk_score(risk_tier: str) -> int:
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
        "regulated": 4,
    }.get(risk_tier, 2)


def _object_id(seed: dict[str, Any]) -> str:
    key = str(seed.get("id") or seed.get("title") or _hash_json(seed))
    return f"object/use-case-seed/{_slug_with_hash(key)}"


def normalize_seed(seed: dict[str, Any], excluded_scopes: list[str] | None = None) -> dict[str, Any]:
    excluded_scopes = [scope.lower() for scope in (excluded_scopes or [])]
    seed_excluded = [str(scope).lower() for scope in seed.get("excluded_scope", [])]
    if any(scope in seed_excluded or scope in str(seed).lower() for scope in excluded_scopes):
        scope_status = "excluded_scope_declared"
    else:
        scope_status = "in_scope"
    return {
        "object_id": _object_id(seed),
        "object_type": "candidate_primitive",
        "title": str(seed.get("title") or seed.get("id") or "Use case seed"),
        "body": {
            "seed_id": seed.get("id"),
            "domain": seed.get("domain", "cross_domain"),
            "task": seed.get("task", ""),
            "inputs": seed.get("inputs", []),
            "outputs": seed.get("outputs", []),
            "required_stages": seed.get("required_stages", []),
            "label_paths": seed.get("label_paths", []),
            "risk_tier": seed.get("risk_tier", "medium"),
            "excluded_scope": sorted(set(seed_excluded + excluded_scopes)),
            "scope_status": scope_status,
        },
    }


def build_row_families(seeds: list[dict[str, Any]], excluded_scopes: list[str] | None = None) -> dict[str, list[dict[str, Any]]]:
    now = datetime.now(timezone.utc).isoformat()
    excluded_scopes = excluded_scopes or []
    body = {
        "seed_count": len(seeds),
        "excluded_scopes": excluded_scopes,
        "source": "cross-domain use-case seeds",
    }
    source_record_id = f"source/use-case-seeds/{_hash_json(body)[:16]}"
    rows: dict[str, list[dict[str, Any]]] = {key: [] for key in FILE_NAMES}
    rows["source_record"].append(
        {
            "source_record_id": source_record_id,
            "source_url": "",
            "archive_url": "",
            "publisher": "Open Harness Hub contributors",
            "license": "CC-BY-4.0",
            "trust_tier": "synthetic_seed",
            "privacy_boundary": "public",
            "freshness": "stable",
            "retrieved_at": now,
            "effective_date": "",
            "content_hash": _hash_json(body),
            "body": body,
        }
    )

    for seed in seeds:
        entities: dict[str, dict[str, Any]] = {row["entity_id"]: row for row in rows["canonical_entity"]}
        refs: dict[tuple[str, str, str], dict[str, Any]] = {
            (row["object_id"], row["entity_id"], row["role"]): row for row in rows["object_entity_ref"]
        }
        normalized = normalize_seed(seed, excluded_scopes=excluded_scopes)
        object_id = normalized["object_id"]
        risk_tier = str(normalized["body"].get("risk_tier", "medium"))
        content_hash = _hash_json(normalized["body"])
        dedupe_cluster_id = f"dedupe/use-case-seed/{content_hash[:16]}"
        rows["normalized_object"].append(
            {
                "object_id": object_id,
                "object_type": "candidate_primitive",
                "source_record_id": source_record_id,
                "title": normalized["title"],
                "body": normalized["body"],
                "trust_tier": "synthetic_seed",
                "privacy_boundary": "public",
                "quality_status": "generated_candidate",
                "review_status": "pending" if risk_tier in {"high", "critical", "regulated"} else "generated_candidate",
                "content_hash": content_hash,
                "dedupe_cluster_id": dedupe_cluster_id,
            }
        )
        rows["dedupe_cluster"].append(
            {
                "dedupe_cluster_id": dedupe_cluster_id,
                "canonical_object_id": object_id,
                "method": "use_case_seed_body_hash",
                "threshold": {"exact_hash": True},
                "status": "generated_candidate",
                "created_at": now,
            }
        )

        domain = str(seed.get("domain", "cross_domain"))
        linked_entity_ids = [
            _add_entity_ref(
                entities=entities,
                refs=refs,
                object_id=object_id,
                entity_type="domain",
                canonical_name=domain,
                role="domain",
                description="Use-case seed domain used for flexible hierarchy and graph faceting.",
                confidence=0.9,
            ),
            _add_entity_ref(
                entities=entities,
                refs=refs,
                object_id=object_id,
                entity_type="risk_tier",
                canonical_name=risk_tier,
                role="risk_tier",
                description="Generated risk tier used for review routing and promotion gating.",
                confidence=0.88,
            ),
        ]
        labels = [
            _label(subject_id=object_id, label_set="hierarchical", label=domain, path=f"domain.{domain}"),
            _label(subject_id=object_id, label_set="generated", label=f"risk:{risk_tier}", path=f"risk.{risk_tier}"),
            _label(subject_id=object_id, label_set="generated", label="scope:insurance_excluded", path="scope.excluded.insurance"),
        ]
        for path in seed.get("label_paths", []) or []:
            label_path = str(path)
            labels.append(
                _label(
                    subject_id=object_id,
                    label_set="hierarchical",
                    label=label_path.split(".")[-1],
                    path=label_path,
                    confidence=0.86,
                )
            )
            linked_entity_ids.append(
                _add_entity_ref(
                    entities=entities,
                    refs=refs,
                    object_id=object_id,
                    entity_type=_entity_type_for_label_path(label_path),
                    canonical_name=label_path,
                    role="label_path",
                    description="Hierarchical label path promoted to a graph-addressable canonical entity.",
                    confidence=0.86,
                )
            )
            parts = label_path.split(".")
            for depth in range(1, len(parts)):
                ancestor_path = ".".join(parts[:depth])
                linked_entity_ids.append(
                    _add_entity_ref(
                        entities=entities,
                        refs=refs,
                        object_id=object_id,
                        entity_type=_entity_type_for_label_path(ancestor_path),
                        canonical_name=ancestor_path,
                        role="label_ancestor",
                        description="Ancestor label node used for hierarchy rollups and broad facet search.",
                        confidence=0.82,
                    )
                )
        for output in seed.get("outputs", []) or []:
            output_name = str(output)
            labels.append(
                _label(
                    subject_id=object_id,
                    label_set="generated",
                    label=f"output:{output_name}",
                    path=f"output.{_safe_slug(output_name).replace('-', '_')}",
                    confidence=0.82,
                )
            )
            linked_entity_ids.append(
                _add_entity_ref(
                    entities=entities,
                    refs=refs,
                    object_id=object_id,
                    entity_type="output_type",
                    canonical_name=output_name,
                    role="emits",
                    description="Expected output object type for this candidate primitive.",
                    confidence=0.84,
                )
            )
        for input_name in seed.get("inputs", []) or []:
            linked_entity_ids.append(
                _add_entity_ref(
                    entities=entities,
                    refs=refs,
                    object_id=object_id,
                    entity_type="input_type",
                    canonical_name=str(input_name),
                    role="accepts",
                    description="Expected input type or source surface for this candidate primitive.",
                    confidence=0.8,
                )
            )
        rows["label_assignment"].extend(labels)

        required_stages = seed.get("required_stages", []) or []
        for stage in required_stages:
            linked_entity_ids.append(
                _add_entity_ref(
                    entities=entities,
                    refs=refs,
                    object_id=object_id,
                    entity_type="pipeline_stage",
                    canonical_name=str(stage),
                    role="requires_stage",
                    description="Pipeline stage needed before this seed can become a deployable primitive.",
                    confidence=0.86,
                )
            )
        rows["canonical_entity"] = sorted(entities.values(), key=lambda row: row["entity_id"])
        rows["object_entity_ref"] = sorted(refs.values(), key=lambda row: (row["object_id"], row["entity_id"], row["role"]))

        embedding_text = _embedding_text(normalized, seed)
        embedding_bucket = _embedding_bucket(seed, risk_tier)
        embedding = _embedding_stub(
            object_id=object_id,
            text=embedding_text,
            bucket=embedding_bucket,
            entity_ids=linked_entity_ids,
            now=now,
        )
        rows["object_embedding"].append(embedding)

        dimensions = [
            _dimension(subject_id=object_id, name="risk_score", value=_risk_score(risk_tier), value_type="integer", scale="1-4"),
            _dimension(subject_id=object_id, name="pipeline_stage_count", value=len(required_stages), value_type="integer"),
            _dimension(subject_id=object_id, name="input_count", value=len(seed.get("inputs", []) or []), value_type="integer"),
            _dimension(subject_id=object_id, name="output_count", value=len(seed.get("outputs", []) or []), value_type="integer"),
            _dimension(subject_id=object_id, name="requires_human_review", value=risk_tier in {"high", "critical", "regulated"}, value_type="boolean"),
            _dimension(subject_id=object_id, name="excluded_scopes", value=normalized["body"]["excluded_scope"], value_type="array"),
            _dimension(subject_id=object_id, name="embedding_bucket", value=embedding_bucket, value_type="string"),
        ]
        rows["dimension_value"].extend(dimensions)

        if risk_tier in {"high", "critical", "regulated"}:
            rows["review_ticket"].append(
                {
                    "review_ticket_id": f"review/{_slug_with_hash(object_id)}",
                    "object_id": object_id,
                    "source_record_id": source_record_id,
                    "review_type": "high_risk_use_case_seed_review",
                    "reason": "High-risk use-case seed requires curator review before promotion into deployable pipeline components.",
                    "status": "open",
                    "created_at": now,
                }
            )

        index_text = " ".join(
            [
                normalized["title"],
                domain,
                risk_tier,
                str(seed.get("task", "")),
                " ".join(str(item) for item in seed.get("label_paths", []) or []),
                " ".join(str(item) for item in seed.get("outputs", []) or []),
            ]
        )
        for kind in ["keyword", "vector", "graph", "facet", "quality"]:
            rows["index_record"].append(
                {
                    "index_record_id": f"index/{kind}/{_slug_with_hash(object_id)}",
                    "index_kind": kind,
                    "subject_id": object_id,
                    "subject_type": "candidate_primitive",
                    "text": index_text,
                    "metadata": {
                        "domain": domain,
                        "risk_tier": risk_tier,
                        "label_paths": seed.get("label_paths", []),
                        "entity_ids": sorted(set(linked_entity_ids)),
                        "embedding_bucket": embedding_bucket,
                        "excluded_scope": normalized["body"]["excluded_scope"],
                    },
                    "embedding_model": embedding["embedding_model"] if kind == "vector" else "",
                    "embedding_ref": embedding["embedding_id"] if kind == "vector" else "",
                    "graph_edges": [
                        {"src_id": object_id, "dst_id": entity_id, "role": "linked_entity", "confidence": 0.84}
                        for entity_id in sorted(set(linked_entity_ids))
                    ],
                }
            )
    return rows


def export_seed_rows(
    seeds: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-use-case-seeds-"))
    rows = build_row_families(seeds, excluded_scopes=excluded_scopes)
    files = []
    row_family_paths = {}
    counts = {}
    for family, filename in FILE_NAMES.items():
        path = out_dir / filename
        _write_jsonl(path, rows.get(family, []))
        files.append(filename)
        row_family_paths[family] = str(path)
        counts[family] = len(rows.get(family, []))
    return {
        "output_dir": str(out_dir),
        "row_counts": counts,
        "files": files,
        "row_family_paths": row_family_paths,
        "warnings": ["Insurance-related seeds are excluded by default."],
    }


def _sample_seeds() -> list[dict[str, Any]]:
    return [
        {
            "id": "animal-hospital-workflow-builder",
            "title": "Animal hospital workflow builder",
            "domain": "animal_hospital",
            "label_paths": ["vertical.veterinary.animal_hospital.triage"],
            "task": "Convert clinic procedures into checklist and RAG objects.",
            "inputs": ["procedure", "species"],
            "outputs": ["checklist_item", "procedure_object", "review_ticket"],
            "risk_tier": "high",
            "required_stages": ["source_governance", "entity_linking", "review_ticket_routing"],
            "excluded_scope": ["insurance"],
        },
        {
            "id": "creative-brief-to-asset-pipeline",
            "title": "Creative brief to asset pipeline",
            "domain": "creative_creation",
            "task": "Turn a brief into candidate concepts and brand-safe routes.",
            "inputs": ["brief"],
            "outputs": ["prompt_pack", "rubric"],
            "risk_tier": "medium",
            "required_stages": ["brief_normalization", "cost_estimation"],
            "excluded_scope": ["insurance"],
        },
    ]


def _self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = export_seed_rows(_sample_seeds(), output_dir=tmp, excluded_scopes=["insurance"])
        assert result["row_counts"]["source_record"] == 1
        assert result["row_counts"]["normalized_object"] == 2
        assert result["row_counts"]["canonical_entity"] >= 10
        assert result["row_counts"]["object_entity_ref"] >= 10
        assert result["row_counts"]["label_assignment"] >= 6
        assert result["row_counts"]["dimension_value"] >= 10
        assert result["row_counts"]["object_embedding"] == 2
        assert result["row_counts"]["review_ticket"] >= 1
        object_ids = [
            json.loads(line)["object_id"]
            for line in (Path(tmp) / "normalized-objects.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(object_ids) == len(set(object_ids))
        index_ids = [
            json.loads(line)["index_record_id"]
            for line in (Path(tmp) / "index-records.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(index_ids) == len(set(index_ids))
        review_ids = [
            json.loads(line)["review_ticket_id"]
            for line in (Path(tmp) / "review-tickets.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(review_ids) == len(set(review_ids))
        assert (Path(tmp) / "label-assignments.jsonl").exists()
        assert (Path(tmp) / "canonical-entities.jsonl").exists()
        assert (Path(tmp) / "object-entity-refs.jsonl").exists()
        assert (Path(tmp) / "object-embeddings.jsonl").exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export cross-domain use-case seeds to candidate primitive, label, dimension, and index JSONL rows.")
    parser.add_argument("--seeds-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.seeds_jsonl:
        parser.error("--seeds-jsonl is required unless --self-test is used")
    print(
        json.dumps(
            export_seed_rows(
                _read_jsonl(args.seeds_jsonl),
                output_dir=args.output_dir,
                excluded_scopes=args.excluded_scopes,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
