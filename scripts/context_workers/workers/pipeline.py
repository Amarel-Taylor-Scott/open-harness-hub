"""Deterministic context pipeline worker."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.registry import TaskContext, TaskResult, registry
from scripts.context_workers.workers.chunk import chunk_context
from scripts.context_workers.workers.claim import claim_extract
from scripts.context_workers.workers.deterministic_graphs import (
    document_graph_build,
    nlp_signals,
    proper_noun_extract,
    regex_extract,
)
from scripts.context_workers.workers.document_tree import document_tree_normalize
from scripts.context_workers.workers.entity import entity_extract
from scripts.context_workers.workers.fragility import fragility_scan
from scripts.context_workers.workers.graph import graph_extract
from scripts.context_workers.workers.keyword import keyword_analysis
from scripts.context_workers.workers.llm_trust_layer import (
    ambiguity_scan,
    conflict_scan,
    fragile_fact_enrich,
    llm_trust_plan,
)
from scripts.context_workers.workers.node_research import node_research_plan
from scripts.context_workers.workers.pre_llm_hygiene import (
    dedupe_fingerprint,
    graph_metrics,
    pii_detect,
    text_normalize,
)
from scripts.context_workers.workers.refresh import refresh_plan


@registry.register(
    "context.pipeline.pass",
    lane="orchestrate",
    description="Run one deterministic first/second/N pass over inline context.",
    emits=(
        "normalized_document_tree",
        "normalized_documents",
        "page_components",
        "source_hierarchy_edges",
        "chunks",
        "normalized_text",
        "normalization_report",
        "fingerprints",
        "keywords",
        "nlp_signals",
        "proper_nouns",
        "regex_facts",
        "pii_findings",
        "entities",
        "claims",
        "document_nodes",
        "document_edges",
        "nodes",
        "edges",
        "graph_metrics",
        "fragile_facts",
        "ambiguous_claims",
        "context_concerns",
        "conflict_candidates",
        "claim_risk_records",
        "updates",
        "refresh_jobs",
        "node_research_tasks",
        "node_research_routes",
        "llm_review_tasks",
        "llm_review_plan",
    ),
    capabilities=("pipeline_orchestration", "deterministic_first_pass"),
    task_types=("context.pipeline.pass",),
    image="baltor-worker-orchestrator",
    output_contract="context_pass.v1",
)
def pipeline_pass(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    text = str(payload.get("text") or "")
    if not text.strip():
        return TaskResult.failure("text required")
    state: dict[str, Any] = {
        "text": text,
        "document_tree": payload.get("document_tree") if isinstance(payload.get("document_tree"), dict) else None,
        "source_name": payload.get("source_name"),
        "source_type": payload.get("source_type"),
        "path": payload.get("path"),
    }
    document_tree = document_tree_normalize(ctx, state)
    if not document_tree.ok:
        return document_tree
    state.update(document_tree.output)
    state["document_tree"] = document_tree.output.get("normalized_document_tree")
    normalized = text_normalize(ctx, state)
    if not normalized.ok:
        return normalized
    state.update(normalized.output)
    state["text"] = str(normalized.output.get("normalized_text") or text)
    for task in (
        chunk_context,
        dedupe_fingerprint,
        keyword_analysis,
        nlp_signals,
        proper_noun_extract,
        regex_extract,
        pii_detect,
        entity_extract,
        claim_extract,
        document_graph_build,
        graph_extract,
        graph_metrics,
        fragility_scan,
        ambiguity_scan,
        conflict_scan,
        fragile_fact_enrich,
        refresh_plan,
    ):
        result = task(ctx, state)
        if not result.ok:
            return result
        state.update(result.output)
    research_nodes = []
    for key in ("entities", "proper_nouns", "nodes"):
        values = state.get(key)
        if isinstance(values, list):
            research_nodes.extend(item for item in values if isinstance(item, dict))
    node_research = node_research_plan(ctx, {
        **state,
        "nodes": research_nodes,
        "max_nodes": int(payload.get("max_node_research_tasks") or 12),
        "authorized": bool(payload.get("authorized")),
        "active_recon_authorized": bool(payload.get("active_recon_authorized")),
        "enabled_node_research_tools": payload.get("enabled_node_research_tools"),
        "disabled_node_research_tools": payload.get("disabled_node_research_tools"),
    })
    if not node_research.ok:
        return node_research
    state.update(node_research.output)
    warnings = list(node_research.warnings)
    llm_plan = llm_trust_plan(ctx, {
        **state,
        "allow_cloud_llm": bool(payload.get("allow_cloud_llm")),
        "allow_frontier_llm": bool(payload.get("allow_frontier_llm")),
        "llm_review_approved": bool(payload.get("llm_review_approved")),
        "privacy_scope": payload.get("privacy_scope") or "tenant",
    })
    if not llm_plan.ok:
        return llm_plan
    state.update(llm_plan.output)
    warnings.extend(llm_plan.warnings)
    followups = []
    for task in state.get("refresh_jobs", []):
        if isinstance(task, dict):
            followups.append(task)
    for task in state.get("node_research_tasks", []):
        if isinstance(task, dict):
            followups.append(task)
    for task in state.get("llm_review_tasks", []):
        if isinstance(task, dict):
            followups.append(task)
    return TaskResult.success({
        "summary": {
            "pass_index": ctx.pass_index,
            "documents": len(state.get("normalized_documents", [])),
            "pages": (state.get("document_tree_summary") or {}).get("pages", 0),
            "page_components": len(state.get("page_components", [])),
            "chunks": len(state.get("chunks", [])),
            "keywords": len(state.get("keywords", [])),
            "pii_findings": len(state.get("pii_findings", [])),
            "entities": len(state.get("entities", [])),
            "proper_nouns": len(state.get("proper_nouns", [])),
            "regex_facts": len(state.get("regex_facts", [])),
            "fingerprints": len(state.get("fingerprints", [])),
            "claims": len(state.get("claims", [])),
            "document_nodes": len(state.get("document_nodes", [])),
            "fragile_facts": len(state.get("fragile_facts", [])),
            "ambiguous_claims": len(state.get("ambiguous_claims", [])),
            "conflict_candidates": len(state.get("conflict_candidates", [])),
            "claim_risk_records": len(state.get("claim_risk_records", [])),
            "refresh_jobs": len(state.get("refresh_jobs", [])),
            "node_research_tasks": len(state.get("node_research_tasks", [])),
            "llm_review_tasks": len(state.get("llm_review_tasks", [])),
        },
        **{k: v for k, v in state.items() if k != "text"},
    }, enqueue=followups, warnings=warnings)
