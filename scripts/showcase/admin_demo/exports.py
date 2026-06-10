"""Serving package exports for the Baltor admin demo."""
from __future__ import annotations

import io
import json
import zipfile
from typing import Any
from xml.sax.saxutils import escape

from scripts.showcase.admin_demo.runs import admin_run_payload


def _result_for_run(run_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    run = admin_run_payload(run_id)
    if run is None:
        return None, None
    result = run.get("result") if isinstance(run.get("result"), dict) else {}
    return run, result


def _lineage(run: dict[str, Any]) -> dict[str, Any]:
    result = run.get("result") if isinstance(run.get("result"), dict) else {}
    return {
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "created_at": run.get("created_at"),
        "updated_at": run.get("updated_at"),
        "summary": run.get("summary") or result.get("summary") or {},
        "sources": result.get("sources") or run.get("sources") or [],
        "worker_plan": result.get("worker_plan") or run.get("worker_plan") or [],
        "cost_estimate": result.get("cost_estimate") or {},
        "queue_plan": result.get("queue_plan") or {},
    }


def _serving_manifest(run: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    summary = run.get("summary") or result.get("summary") or {}
    run_id = str(run.get("run_id") or "")
    base_path = f"/api/admin-demo/runs/{run_id}/exports"
    return {
        "package_type": "baltor.serving_manifest.v1",
        "run_id": run_id,
        "status": run.get("status"),
        "summary": {
            "sources": summary.get("sources", 0),
            "chunks": summary.get("chunks", 0),
            "claims": summary.get("claims", 0),
            "entities": summary.get("entities", 0),
            "verification_queue": summary.get("fragile_facts", 0),
            "refresh_jobs": summary.get("worker_updates", 0),
        },
        "contracts": [
            {
                "kind": "text",
                "content_type": "application/json",
                "path": f"{base_path}/text",
                "purpose": "Prompt/tool context with fact state, confidence, and provenance history.",
            },
            {
                "kind": "rag",
                "content_type": "application/x-ndjson",
                "path": f"{base_path}/rag",
                "purpose": "Chunk records with claims, source metadata, and freshness fields.",
            },
            {
                "kind": "graph",
                "content_type": "application/graphml+xml",
                "path": f"{base_path}/graph",
                "purpose": "Entity, claim, chunk, source-link, and support edges for hybrid retrieval.",
            },
            {
                "kind": "audit",
                "content_type": "application/zip",
                "path": f"{base_path}/audit",
                "purpose": "Review packet with sources, worker trace, costs, queue plan, and approvals.",
            },
        ],
        "governance": {
            "promotion_policy": "facts with unresolved evidence remain queued, blocked, or approval-gated before serving",
            "state_history_included": True,
            "cost_estimate_included": True,
            "source_versions_included": True,
        },
    }


def _text_pack(run: dict[str, Any], result: dict[str, Any]) -> bytes:
    facts = []
    fragile_by_id = {item.get("fact_id"): item for item in result.get("fragile_facts", [])}
    for fact in result.get("facts", []):
        facts.append({
            "id": fact.get("id"),
            "claim": fact.get("claim"),
            "subject": fact.get("subject"),
            "state": fact.get("state") or ("needs_verification" if fact.get("id") in fragile_by_id else "candidate_detected"),
            "confidence": fact.get("confidence"),
            "source_chunk": fact.get("source_chunk"),
            "independent_source_count": fact.get("independent_source_count", 0),
            "authoritative_source_count": fact.get("authoritative_source_count", 0),
            "signals": fact.get("signals", []),
            "provenance": {
                "run_id": run.get("run_id"),
                "original_source_fact": fact.get("claim"),
                "history": (fact.get("state_history") or []) + ([fragile_by_id[fact.get("id")]] if fact.get("id") in fragile_by_id else []),
            },
        })
    payload = {
        "package_type": "baltor.text_pack.v1",
        "serving_manifest": _serving_manifest(run, result),
        "run": _lineage(run),
        "facts": facts,
    }
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _rag_records(result: dict[str, Any]) -> bytes:
    facts_by_chunk: dict[str, list[dict[str, Any]]] = {}
    for fact in result.get("facts", []):
        facts_by_chunk.setdefault(str(fact.get("source_chunk") or ""), []).append(fact)
    sources = result.get("sources", [])
    rows = []
    for chunk in result.get("chunks", []):
        rows.append(json.dumps({
            "id": chunk.get("id"),
            "text": chunk.get("text"),
            "metadata": {
                "char_count": chunk.get("char_count"),
                "claims": facts_by_chunk.get(str(chunk.get("id") or ""), []),
                "sources": sources,
                "freshness": "refresh_planned" if facts_by_chunk.get(str(chunk.get("id") or "")) else "candidate",
            },
        }, sort_keys=True))
    return ("\n".join(rows) + ("\n" if rows else "")).encode("utf-8")


def _graphml(result: dict[str, Any]) -> bytes:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<graph edgedefault="directed">',
    ]
    for node in result.get("nodes", []):
        lines.append(f'<node id="{escape(str(node.get("id", "")))}">')
        lines.append(f'<data key="label">{escape(str(node.get("label", "")))}</data>')
        lines.append(f'<data key="type">{escape(str(node.get("type", "")))}</data>')
        lines.append("</node>")
    for idx, edge in enumerate(result.get("edges", []), 1):
        lines.append(
            f'<edge id="e{idx}" source="{escape(str(edge.get("from", "")))}" target="{escape(str(edge.get("to", "")))}">'
            f'<data key="type">{escape(str(edge.get("type", "")))}</data></edge>'
        )
    lines.extend(["</graph>", "</graphml>"])
    return ("\n".join(lines) + "\n").encode("utf-8")


def _audit_zip(run: dict[str, Any], result: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest = _serving_manifest(run, result)
        manifest["package_type"] = "baltor.audit_packet.v1"
        manifest["run"] = _lineage(run)
        manifest["files"] = [
            "manifest.json",
            "sources.json",
            "worker-plan.json",
            "cost-estimate.json",
            "queue-plan.json",
            "claims.json",
            "verification-queue.json",
            "refresh-jobs.json",
        ]
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        zf.writestr("sources.json", json.dumps(result.get("sources") or run.get("sources") or [], indent=2, sort_keys=True))
        zf.writestr("worker-plan.json", json.dumps(result.get("worker_plan") or run.get("worker_plan") or [], indent=2, sort_keys=True))
        zf.writestr("cost-estimate.json", json.dumps(result.get("cost_estimate") or {}, indent=2, sort_keys=True))
        zf.writestr("queue-plan.json", json.dumps(result.get("queue_plan") or {}, indent=2, sort_keys=True))
        zf.writestr("claims.json", json.dumps(result.get("facts") or [], indent=2, sort_keys=True))
        zf.writestr("verification-queue.json", json.dumps(result.get("fragile_facts") or [], indent=2, sort_keys=True))
        zf.writestr("refresh-jobs.json", json.dumps(result.get("updates") or [], indent=2, sort_keys=True))
    return buf.getvalue()


def build_export(run_id: str, kind: str) -> tuple[bytes, str, str] | None:
    run, result = _result_for_run(run_id)
    if run is None or result is None:
        return None
    if not result:
        return None
    safe_run_id = str(run_id).replace("/", "-")
    if kind == "manifest":
        return (
            json.dumps(_serving_manifest(run, result), indent=2, sort_keys=True).encode("utf-8"),
            "application/json",
            f"{safe_run_id}-serving-manifest.json",
        )
    if kind == "text":
        return _text_pack(run, result), "application/json", f"{safe_run_id}-text-pack.json"
    if kind == "rag":
        return _rag_records(result), "application/x-ndjson", f"{safe_run_id}-rag-records.jsonl"
    if kind == "graph":
        return _graphml(result), "application/graphml+xml", f"{safe_run_id}-graph.graphml"
    if kind == "audit":
        return _audit_zip(run, result), "application/zip", f"{safe_run_id}-audit-packet.zip"
    return None
