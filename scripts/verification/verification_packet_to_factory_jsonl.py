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
    return "".join(cleaned).strip("-")[:64] or "unknown"


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _entity(entity_type: str, name: str, confidence: float = 0.8) -> dict[str, Any]:
    slug = _safe_slug(f"{entity_type}-{name}")
    return {
        "entity_id": f"entity/{slug}",
        "entity_type": entity_type,
        "canonical_name": name,
        "aliases": [],
        "identifiers": {},
        "description": f"Verification packet entity: {name}",
        "confidence": confidence,
        "review_status": "generated_candidate",
    }


def _public_reviewer(review: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(review)
    for key in ["email", "name", "raw_body", "message_body", "signature", "quoted_text"]:
        cleaned.pop(key, None)
    reviewer_id = cleaned.pop("reviewer_id", None) or cleaned.pop("sender", None)
    if reviewer_id:
        cleaned["reviewer_hash"] = hashlib.sha256(str(reviewer_id).encode("utf-8")).hexdigest()
    return cleaned


def _public_packet(packet: dict[str, Any], include_raw_messages: bool) -> dict[str, Any]:
    cleaned = dict(packet)
    if not include_raw_messages:
        cleaned.pop("raw_messages", None)
        cleaned.pop("raw_email", None)
        cleaned.pop("raw_search_results", None)
    cleaned["expert_reviews"] = [_public_reviewer(item) for item in cleaned.get("expert_reviews", [])]
    return cleaned


def _add_object(
    rows: dict[str, list[dict[str, Any]]],
    *,
    object_id: str,
    object_type: str,
    source_record_id: str,
    title: str,
    body: dict[str, Any],
    trust_tier: str,
    privacy_boundary: str,
    review_status: str,
    now: str,
) -> None:
    content_hash = _hash_json(body)
    dedupe_cluster_id = f"dedupe/verification/{object_type}/{content_hash[:16]}"
    rows["normalized_object"].append(
        {
            "object_id": object_id,
            "object_type": object_type,
            "source_record_id": source_record_id,
            "title": title,
            "body": body,
            "trust_tier": trust_tier,
            "privacy_boundary": privacy_boundary,
            "quality_status": "generated_candidate",
            "review_status": review_status,
            "content_hash": content_hash,
            "dedupe_cluster_id": dedupe_cluster_id,
        }
    )
    rows["dedupe_cluster"].append(
        {
            "dedupe_cluster_id": dedupe_cluster_id,
            "canonical_object_id": object_id,
            "method": "verification_object_type_content_hash",
            "threshold": {"exact_hash": True},
            "status": "generated_candidate",
            "created_at": now,
        }
    )


def _index_object(
    rows: dict[str, list[dict[str, Any]]],
    *,
    object_id: str,
    object_type: str,
    title: str,
    text: str,
    metadata: dict[str, Any],
) -> None:
    for kind in ["keyword", "vector", "facet", "graph", "quality", "freshness"]:
        rows["index_record"].append(
            {
                "index_record_id": f"index/{kind}/{_safe_slug(object_id)}",
                "index_kind": kind,
                "subject_id": object_id,
                "subject_type": object_type,
                "text": text or title,
                "metadata": metadata,
                "embedding_model": "",
                "embedding_ref": "",
                "graph_edges": [],
            }
        )


def build_row_families(
    verification_packet: dict[str, Any],
    inbound_digest: dict[str, Any] | None = None,
    include_raw_messages: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    now = datetime.now(timezone.utc).isoformat()
    public_packet = _public_packet(verification_packet, include_raw_messages)
    packet_hash = _hash_json(public_packet)
    source_record_id = f"source/verification-packet/{packet_hash[:16]}"
    knowledge_object_id = str(public_packet.get("knowledge_object_id") or public_packet.get("object_id") or "knowledge-object")
    risk_tier = str(public_packet.get("risk_tier", "unknown"))
    decision = str(public_packet.get("decision", "pending_review"))
    privacy_boundary = str(public_packet.get("privacy_boundary", "tenant_private_by_default"))

    rows: dict[str, list[dict[str, Any]]] = {key: [] for key in FILE_NAMES}
    rows["source_record"].append(
        {
            "source_record_id": source_record_id,
            "source_url": public_packet.get("source_url", ""),
            "archive_url": public_packet.get("archive_url", ""),
            "publisher": public_packet.get("publisher", "verification packet exporter"),
            "license": public_packet.get("license", "tenant-private"),
            "trust_tier": public_packet.get("trust_tier", "generated_candidate"),
            "privacy_boundary": privacy_boundary,
            "freshness": public_packet.get("freshness", "volatile"),
            "retrieved_at": now,
            "effective_date": public_packet.get("effective_date", ""),
            "content_hash": packet_hash,
            "body": {
                "knowledge_object_id": knowledge_object_id,
                "risk_tier": risk_tier,
                "decision": decision,
                "verification_channels": public_packet.get("verification_channels", []),
                "grounded_source_count": len(public_packet.get("grounded_sources", [])),
                "model_review_count": len(public_packet.get("model_reviews", [])),
                "expert_review_count": len(public_packet.get("expert_reviews", [])),
                "raw_messages_exported": include_raw_messages,
            },
        }
    )

    entities: dict[str, dict[str, Any]] = {}
    for entity in [
        _entity("risk_tier", risk_tier, 0.9),
        _entity("verification_decision", decision, 0.9),
    ]:
        entities[entity["entity_id"]] = entity
    for name in public_packet.get("jurisdictions", []):
        entity = _entity("jurisdiction", str(name), 0.85)
        entities[entity["entity_id"]] = entity
    for channel in public_packet.get("verification_channels", []):
        entity = _entity("verification_channel", str(channel), 0.9)
        entities[entity["entity_id"]] = entity

    claim_title = str(public_packet.get("claim") or public_packet.get("title") or knowledge_object_id)
    fact_object_id = f"object/verification/versioned-fact/{_safe_slug(knowledge_object_id)}"
    _add_object(
        rows,
        object_id=fact_object_id,
        object_type="versioned_fact",
        source_record_id=source_record_id,
        title=claim_title,
        body={
            "knowledge_object_id": knowledge_object_id,
            "claim": public_packet.get("claim", ""),
            "jurisdictions": public_packet.get("jurisdictions", []),
            "effective_date": public_packet.get("effective_date", ""),
            "source_url": public_packet.get("source_url", ""),
        },
        trust_tier=str(public_packet.get("trust_tier", "generated_candidate")),
        privacy_boundary=privacy_boundary,
        review_status="pending" if risk_tier in {"high", "critical", "regulated"} else "generated_candidate",
        now=now,
    )
    _index_object(
        rows,
        object_id=fact_object_id,
        object_type="versioned_fact",
        title=claim_title,
        text=" ".join([claim_title, risk_tier, decision]),
        metadata={"risk_tier": risk_tier, "decision": decision, "knowledge_object_id": knowledge_object_id},
    )

    decision_object_id = f"object/verification/decision-gate/{packet_hash[:16]}"
    _add_object(
        rows,
        object_id=decision_object_id,
        object_type="decision_gate",
        source_record_id=source_record_id,
        title=f"Verification decision for {knowledge_object_id}",
        body={
            "decision": decision,
            "confidence": public_packet.get("confidence"),
            "conflicts": public_packet.get("conflicts", []),
            "required_evidence_channels": public_packet.get("required_evidence_channels", []),
            "promotion_hold": bool(public_packet.get("promotion_hold", decision not in {"promote", "approved"})),
        },
        trust_tier="generated_candidate",
        privacy_boundary=privacy_boundary,
        review_status="pending" if decision not in {"promote", "approved"} else "reviewed",
        now=now,
    )
    _index_object(
        rows,
        object_id=decision_object_id,
        object_type="decision_gate",
        title=f"Verification decision for {knowledge_object_id}",
        text=f"{knowledge_object_id} {decision} {risk_tier}",
        metadata={"risk_tier": risk_tier, "decision": decision},
    )

    evidence_items: list[tuple[str, dict[str, Any]]] = []
    evidence_items.extend(("grounded_source", item) for item in public_packet.get("grounded_sources", []))
    evidence_items.extend(("model_review", item) for item in public_packet.get("model_reviews", []))
    evidence_items.extend(("expert_review", item) for item in public_packet.get("expert_reviews", []))
    if inbound_digest:
        evidence_items.extend(("inbound_digest", item) for item in inbound_digest.get("normalized_objects", []))

    for index, (channel, item) in enumerate(evidence_items, 1):
        body = {"channel": channel, "knowledge_object_id": knowledge_object_id, "evidence": item}
        object_id = f"object/verification/evidence/{packet_hash[:12]}-{index:03d}"
        _add_object(
            rows,
            object_id=object_id,
            object_type="evidence_requirement",
            source_record_id=source_record_id,
            title=f"{channel.replace('_', ' ').title()} evidence for {knowledge_object_id}",
            body=body,
            trust_tier="generated_candidate",
            privacy_boundary=privacy_boundary,
            review_status="pending" if channel in {"expert_review", "inbound_digest"} else "generated_candidate",
            now=now,
        )
        _index_object(
            rows,
            object_id=object_id,
            object_type="evidence_requirement",
            title=f"{channel} evidence",
            text=f"{channel} {knowledge_object_id} {json.dumps(item, sort_keys=True, ensure_ascii=False)}",
            metadata={"risk_tier": risk_tier, "decision": decision, "channel": channel},
        )
        entity = _entity("verification_channel", channel, 0.9)
        entities[entity["entity_id"]] = entity

    rows["canonical_entity"] = sorted(entities.values(), key=lambda item: item["entity_id"])
    for record in rows["normalized_object"]:
        for entity_id in entities:
            rows["object_entity_ref"].append(
                {
                    "object_id": record["object_id"],
                    "entity_id": entity_id,
                    "role": "verification_context",
                    "confidence": 0.72,
                }
            )

    if public_packet.get("conflicts") or decision not in {"promote", "approved"} or risk_tier in {"high", "critical", "regulated"}:
        rows["review_ticket"].append(
            {
                "review_ticket_id": f"review/verification/{packet_hash[:16]}",
                "object_id": decision_object_id,
                "source_record_id": source_record_id,
                "review_type": "verification_packet_review",
                "reason": "Verification packet requires human review because of risk tier, unresolved conflicts, or non-promote decision.",
                "status": "open",
                "created_at": now,
            }
        )
    return rows


def export_verification_packet(
    verification_packet: dict[str, Any],
    inbound_digest: dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
    include_raw_messages: bool = False,
) -> dict[str, Any]:
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-verification-records-"))
    rows = build_row_families(
        verification_packet,
        inbound_digest=inbound_digest,
        include_raw_messages=include_raw_messages,
    )
    files = []
    row_family_paths = {}
    counts = {}
    for family, filename in FILE_NAMES.items():
        family_rows = rows.get(family, [])
        path = out_dir / filename
        _write_jsonl(path, family_rows)
        files.append(filename)
        row_family_paths[family] = str(path)
        counts[family] = len(family_rows)
    warnings = []
    if not include_raw_messages:
        warnings.append("Raw messages and personal reviewer identifiers were not exported.")
    return {
        "output_dir": str(out_dir),
        "row_counts": counts,
        "files": files,
        "row_family_paths": row_family_paths,
        "warnings": warnings,
    }


def _sample_packet() -> dict[str, Any]:
    return {
        "knowledge_object_id": "knowledge-object/ph-ofw-placement-fee-rule",
        "claim": "Placement fee limits for overseas worker recruitment should be checked against current official rules before pipeline deployment.",
        "risk_tier": "high",
        "decision": "hold_for_review",
        "confidence": 0.72,
        "privacy_boundary": "tenant_private_by_default",
        "verification_channels": ["grounded_search", "model_review", "expert_review"],
        "jurisdictions": ["Philippines"],
        "grounded_sources": [{"source_url": "https://example.gov/rules", "assessment": "needs-current-source"}],
        "model_reviews": [{"model": "local-small-reviewer", "assessment": "needs-human-verification"}],
        "expert_reviews": [{"reviewer_id": "reviewer@example.org", "role": "civil_society", "assessment": "agree_with_caveat"}],
        "conflicts": [{"type": "freshness", "note": "Official source should be refreshed before promotion."}],
    }


def _self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = export_verification_packet(_sample_packet(), output_dir=tmp)
        assert result["row_counts"]["source_record"] == 1
        assert result["row_counts"]["normalized_object"] >= 4
        assert result["row_counts"]["canonical_entity"] >= 3
        assert result["row_counts"]["object_entity_ref"] >= result["row_counts"]["normalized_object"]
        assert result["row_counts"]["review_ticket"] >= 1
        assert (Path(tmp) / "normalized-objects.jsonl").exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export verification packets to canonical JSONL row families.")
    parser.add_argument("--packet-json", help="Inline verification packet JSON object.")
    parser.add_argument("--packet-file", help="Path to a verification packet JSON file.")
    parser.add_argument("--output-dir")
    parser.add_argument("--include-raw-messages", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if args.packet_file:
        packet = json.loads(Path(args.packet_file).read_text(encoding="utf-8"))
    elif args.packet_json:
        packet = json.loads(args.packet_json)
    else:
        parser.error("--packet-json or --packet-file is required unless --self-test is used")
    print(
        json.dumps(
            export_verification_packet(
                packet,
                output_dir=args.output_dir,
                include_raw_messages=args.include_raw_messages,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
