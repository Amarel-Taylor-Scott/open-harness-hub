"""Post-deterministic trust-layer workers.

The deterministic pipeline should produce evidence-bearing claims, entities,
chunks, and graph edges before any model sees the corpus. These workers prepare
the next layer: ambiguity/risk scans plus queueable LLM review tasks that add
nodes, edges, summaries, conflict reviews, and confidence judgments without
promoting weak facts directly into serving context.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from scripts.context_workers.common import compact, stable_hash
from scripts.context_workers.model_cascade import choose_cascade_tiers, load_cascade_policy
from scripts.context_workers.registry import TaskContext, TaskResult, registry
from scripts.model_gateway import resolve_model_route
from scripts.model_routes import ChatRoute

AMBIGUOUS_RE = re.compile(
    r"\b(it|they|this|that|these|those|former|latter|various|several|many|some|recent|soon|currently|"
    r"approximately|about|around|likely|may|might|could|should|generally|often|usually|significant|material)\b",
    re.I,
)
VOLATILE_RE = re.compile(
    r"\b(current|currently|latest|today|yesterday|tomorrow|as of|now|recent|new|planned|pending|"
    r"price|cost|rate|threshold|owner|officer|address|website|status|policy|version|deadline|schedule|available)\b",
    re.I,
)

ALLOWED_EDGE_TYPES = {
    "MENTIONS",
    "SUPPORTS",
    "CONTRADICTS",
    "SUPERSEDES",
    "QUALIFIES",
    "ALIAS_OF",
    "SAME_AS_CANDIDATE",
    "LOCATED_IN",
    "HEADQUARTERED_AT",
    "REGISTERED_IN",
    "HAS_IDENTIFIER",
    "HAS_ROLE",
    "HELD_ROLE",
    "WORKS_FOR",
    "OWNS",
    "CONTROLS",
    "PART_OF",
    "PARENT_OF",
    "SUBSIDIARY_OF",
    "CITES",
    "REFERENCES",
    "HAS_VALUE",
    "HAS_TEMPORAL_SCOPE",
    "REQUIRES_REVIEW",
}

EDGE_TYPE_ALIASES = {
    "IS_CEO_OF": "HELD_ROLE",
    "IS_CFO_OF": "HELD_ROLE",
    "IS_COO_OF": "HELD_ROLE",
    "IS_CCO_OF": "HELD_ROLE",
    "CEO_OF": "HELD_ROLE",
    "CFO_OF": "HELD_ROLE",
    "COO_OF": "HELD_ROLE",
    "CCO_OF": "HELD_ROLE",
    "WORKED_FOR": "WORKS_FOR",
    "EMPLOYED_BY": "WORKS_FOR",
    "EMPLOYEE_OF": "WORKS_FOR",
    "HAS_HEADQUARTERS_AT": "HEADQUARTERED_AT",
    "HEADQUARTERS_IN": "HEADQUARTERED_AT",
    "BASED_IN": "LOCATED_IN",
    "IS_LOCATED_IN": "LOCATED_IN",
    "REGISTERED_AT": "REGISTERED_IN",
    "IDENTIFIED_BY": "HAS_IDENTIFIER",
    "MENTIONED_IN": "MENTIONS",
    "SOURCE_SUPPORTS": "SUPPORTS",
    "CONFLICTS_WITH": "CONTRADICTS",
    "UPDATES": "SUPERSEDES",
}

LLM_REVIEW_TASKS = {
    "llm.claim.review": {
        "lane": "local_efficient",
        "capability": "claim_review",
        "purpose": "Rate claim clarity, evidence strength, freshness risk, and context-safety.",
    },
    "llm.conflict.review": {
        "lane": "open_weight_medium",
        "capability": "conflict_detection",
        "purpose": "Compare related claims and propose support/contradiction/needs-review edges.",
    },
    "llm.graph.enrich": {
        "lane": "open_weight_medium",
        "capability": "graph_extraction",
        "purpose": "Propose additional nodes, typed edges, aliases, and evidence links.",
    },
    "llm.context.summarize": {
        "lane": "local_efficient",
        "capability": "summarization",
        "purpose": "Create source, section, node, and corpus summaries with cited claim IDs.",
    },
    "llm.audit.review": {
        "lane": "open_weight_medium",
        "capability": "audit_review",
        "purpose": "Escalated local review for high-risk contradictions, ambiguous instructions, or fragile facts.",
    },
}


def _claims(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [claim for claim in payload.get("claims", []) if isinstance(claim, dict)]


def _claim_text(claim: dict[str, Any]) -> str:
    return str(claim.get("claim") or claim.get("text") or "")


@registry.register(
    "context.ambiguity.scan",
    lane="verify",
    description="Flag unclear sentences and claims that are risky to serve as LLM context without review.",
    emits=("ambiguous_claims", "context_concerns"),
    capabilities=("ambiguity_detection", "context_safety", "local_rules"),
    task_types=("context.ambiguity.scan", "claim.ambiguity.detect"),
    image="baltor-worker-audit",
    output_contract="context_ambiguity.v1",
)
def ambiguity_scan(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    concerns: list[dict[str, Any]] = []
    for claim in _claims(payload):
        text = _claim_text(claim)
        hits = sorted({match.group(0).lower() for match in AMBIGUOUS_RE.finditer(text)})
        if not hits:
            continue
        severity = "high" if any(hit in {"it", "they", "this", "that", "former", "latter"} for hit in hits) else "medium"
        concerns.append({
            "concern_id": stable_hash("ambiguity", f"{claim.get('id')}:{','.join(hits)}", len(concerns) + 1),
            "claim_id": claim.get("id"),
            "source_chunk": claim.get("source_chunk"),
            "type": "ambiguous_language",
            "severity": severity,
            "signals": hits,
            "evidence": text,
            "recommended_action": "llm_claim_review",
        })
    return TaskResult.success({"ambiguous_claims": concerns, "context_concerns": concerns})


@registry.register(
    "context.conflict.scan",
    lane="verify",
    description="Find deterministic contradiction/conflict candidates among claims before LLM review.",
    emits=("conflict_candidates",),
    capabilities=("conflict_detection", "claim_reconciliation", "local_rules"),
    task_types=("context.conflict.scan", "claim.conflict.detect"),
    image="baltor-worker-audit",
    output_contract="conflict_candidates.v1",
)
def conflict_scan(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    claims = _claims(payload)
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        subject = compact(str(claim.get("subject") or "claim")).lower()
        by_subject.setdefault(subject, []).append(claim)
    conflicts: list[dict[str, Any]] = []
    for subject, items in by_subject.items():
        positives = [item for item in items if item.get("polarity") == "positive"]
        negatives = [item for item in items if item.get("polarity") == "negative"]
        for left in positives:
            for right in negatives:
                conflicts.append({
                    "conflict_id": stable_hash("conflict", f"{left.get('id')}:{right.get('id')}", len(conflicts) + 1),
                    "subject": subject,
                    "left_claim_id": left.get("id"),
                    "right_claim_id": right.get("id"),
                    "left_evidence": _claim_text(left),
                    "right_evidence": _claim_text(right),
                    "state": "needs_llm_or_human_reconciliation",
                    "recommended_action": "llm_conflict_review",
                })
    return TaskResult.success({"conflict_candidates": conflicts})


@registry.register(
    "context.fragile_fact.enrich",
    lane="verify",
    description="Turn fragile facts into first-class risk records with freshness, authority, and context-serving guidance.",
    emits=("claim_risk_records",),
    capabilities=("fragile_fact_detection", "claim_records", "context_safety"),
    task_types=("context.fragile_fact.enrich", "claim.risk.enrich"),
    image="baltor-worker-audit",
    output_contract="claim_risk_records.v1",
)
def fragile_fact_enrich(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    records: list[dict[str, Any]] = []
    fragile_by_id = {item.get("fact_id"): item for item in payload.get("fragile_facts", []) if isinstance(item, dict)}
    ambiguous_by_id = {item.get("claim_id"): item for item in payload.get("ambiguous_claims", []) if isinstance(item, dict)}
    for index, claim in enumerate(_claims(payload), 1):
        claim_id = claim.get("id") or stable_hash("claim", _claim_text(claim), index)
        text = _claim_text(claim)
        volatile_hits = sorted({match.group(0).lower() for match in VOLATILE_RE.finditer(text)})
        risk_reasons = []
        if claim_id in fragile_by_id:
            risk_reasons.extend(fragile_by_id[claim_id].get("reasons") or ["needs_refresh"])
        if claim_id in ambiguous_by_id:
            risk_reasons.append("ambiguous_language")
        if volatile_hits:
            risk_reasons.append("volatile_fact")
        serving_state = "allow_with_citation"
        if risk_reasons:
            serving_state = "review_before_serving" if "ambiguous_language" in risk_reasons else "serve_with_freshness_warning"
        records.append({
            "claim_id": claim_id,
            "claim": text,
            "subject": claim.get("subject"),
            "source_chunk": claim.get("source_chunk"),
            "polarity": claim.get("polarity", "neutral"),
            "provenance": {
                "run_id": ctx.run_id,
                "source_chunk": claim.get("source_chunk"),
                "evidence_span": text[:800],
            },
            "freshness": {
                "volatile": bool(volatile_hits),
                "signals": volatile_hits,
                "retrieved_at": None,
                "valid_until": None,
            },
            "verification": {
                "state": "detected",
                "independent_source_count": 1,
                "authoritative_source_count": 0,
                "conflict_status": "unknown",
            },
            "context_serving": {
                "state": serving_state,
                "risk_reasons": sorted(set(risk_reasons)),
                "requires_citation": True,
            },
        })
    return TaskResult.success({"claim_risk_records": records})


def _review_task(ctx: TaskContext, name: str, payload: dict[str, Any], *, index: int) -> dict[str, Any]:
    spec = LLM_REVIEW_TASKS[name]
    cascade = choose_cascade_tiers(name, payload)
    selected_tier = (cascade.get("selected_tiers") or [{}])[-1] if cascade.get("selected_tiers") else {}
    tier_policy = selected_tier.get("model_policy") if isinstance(selected_tier, dict) else {}
    lane = str(tier_policy.get("lane") or spec["lane"])
    capability = str(tier_policy.get("capability") or spec["capability"])
    frontier_requested = lane in {"frontier_controlled", "human_review"}
    frontier_allowed = bool(payload.get("allow_frontier_llm") or payload.get("llm_review_approved"))
    if frontier_requested and not frontier_allowed:
        lane = "open_weight_medium"
        capability = spec["capability"]
    route = resolve_model_route({
        "task": name,
        "payload": {
            "model_policy": {
                "capability": capability,
                "lane": lane,
                "allow_cloud": bool(payload.get("allow_cloud_llm")),
                "allow_frontier": bool(payload.get("allow_frontier_llm")) or lane == "frontier_controlled",
            },
            "data_policy": {
                "privacy_scope": str(payload.get("privacy_scope") or "tenant"),
                "allow_cloud": bool(payload.get("allow_cloud_llm")),
            },
        },
    })
    requires_approval = frontier_requested and frontier_allowed and not payload.get("llm_review_approved")
    return {
        "task_id": stable_hash("llm-review", f"{ctx.run_id}:{name}:{index}", index),
        "task": name,
        "run_id": ctx.run_id,
        "tenant_id": ctx.tenant_id,
        "lane": "llm_review",
        "state": "queued",
        "payload": {
            "purpose": spec["purpose"],
            "cascade": cascade,
            "model_route": route,
            "claims": payload.get("claim_risk_records") or payload.get("claims") or [],
            "nodes": payload.get("nodes") or [],
            "edges": payload.get("edges") or [],
            "conflict_candidates": payload.get("conflict_candidates") or [],
            "context_concerns": payload.get("context_concerns") or [],
            "output_rules": {
                "must_return_evidence_ids": True,
                "may_propose_nodes_edges": name == "llm.graph.enrich",
                "may_change_verification_state": False,
                "human_review_required_for_promotion": True,
            },
        },
        "budget_policy": {
            "action": "require_approval" if requires_approval else "allow",
            "reason_codes": (
                ["frontier_or_human_review_requires_approval"] if requires_approval
                else ["frontier_downgraded_to_local_open_weight"] if frontier_requested and not frontier_allowed
                else ["within_policy"]
            ),
        },
    }


@registry.register(
    "model.cascade.catalog",
    lane="orchestrate",
    description="Report the configured cost/confidence model cascade policy and fine-tuning targets.",
    emits=("model_cascade_policy",),
    capabilities=("model_routing", "cost_control", "fine_tuning_feedback"),
    task_types=("model.cascade.catalog",),
    image="baltor-worker-orchestrator",
    output_contract="model_cascade_policy.v1",
)
def model_cascade_catalog(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    return TaskResult.success({"model_cascade_policy": load_cascade_policy(str(payload.get("policy_path") or "") or None)})


@registry.register(
    "llm.trust.plan",
    lane="orchestrate",
    description="Plan hierarchical LLM review tasks for claims, summaries, graph enrichment, ambiguity, conflicts, and fragile facts.",
    emits=("llm_review_tasks", "llm_review_plan"),
    capabilities=("llm_review_planning", "hierarchical_models", "graph_enrichment", "summarization", "conflict_review"),
    task_types=("llm.trust.plan", "context.llm_review.plan"),
    image="baltor-worker-orchestrator",
    output_contract="llm_trust_plan.v1",
)
def llm_trust_plan(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    tasks: list[dict[str, Any]] = []
    tasks.append(_review_task(ctx, "llm.claim.review", payload, index=1))
    tasks.append(_review_task(ctx, "llm.graph.enrich", payload, index=2))
    tasks.append(_review_task(ctx, "llm.context.summarize", payload, index=3))
    if payload.get("conflict_candidates"):
        tasks.append(_review_task(ctx, "llm.conflict.review", payload, index=4))
    high_risk = bool(payload.get("conflict_candidates")) or any(
        "review_before_serving" == ((record.get("context_serving") or {}).get("state"))
        for record in payload.get("claim_risk_records", [])
        if isinstance(record, dict)
    )
    if high_risk:
        tasks.append(_review_task(ctx, "llm.audit.review", payload, index=5))
    return TaskResult.success({
        "llm_review_plan": {
            "task_count": len(tasks),
            "hierarchy": [tier.get("id") for tier in load_cascade_policy().get("tiers", [])],
            "promotion_policy": "LLM tasks may propose nodes, edges, summaries, and ratings; promotion requires evidence IDs and review gates.",
        },
        "llm_review_tasks": tasks,
    }, enqueue=tasks)


def _training_example(ctx: TaskContext, task_name: str, payload: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    cascade = payload.get("cascade") if isinstance(payload.get("cascade"), dict) else {}
    return {
        "training_example_id": stable_hash("training-example", f"{ctx.run_id}:{ctx.job_id}:{task_name}", 1),
        "task": task_name,
        "training_task": cascade.get("training_task", task_name),
        "run_id": ctx.run_id,
        "input": {
            "claims": payload.get("claims", []),
            "nodes": payload.get("nodes", []),
            "edges": payload.get("edges", []),
            "conflict_candidates": payload.get("conflict_candidates", []),
            "context_concerns": payload.get("context_concerns", []),
        },
        "model_route": payload.get("model_route"),
        "cascade": cascade,
        "model_output": output,
        "reviewed_output": None,
        "accepted": None,
        "do_not_train_changing_facts_into_weights": True,
        "label_source": "pending_review",
    }


def _selected_chat_route(model_route: dict[str, Any] | None) -> ChatRoute | None:
    if not isinstance(model_route, dict):
        return None
    selected = model_route.get("selected_route")
    if not isinstance(selected, dict):
        return None
    base_url = str(selected.get("base_url") or "").strip()
    model = str(selected.get("model") or "").strip()
    if not base_url or not model or model == "none":
        return None
    api_key = None
    api_key_env = selected.get("api_key_env")
    if api_key_env:
        api_key = os.environ.get(str(api_key_env))
    return ChatRoute(str(selected.get("backend") or "http-openai"), model, base_url, api_key)


def _json_slice(text: str) -> str:
    body = compact(text)
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?\s*", "", body, flags=re.I).strip()
        body = re.sub(r"\s*```$", "", body).strip()
    start_candidates = [idx for idx in (body.find("{"), body.find("[")) if idx >= 0]
    if not start_candidates:
        return body
    start = min(start_candidates)
    end = max(body.rfind("}"), body.rfind("]"))
    return body[start:end + 1] if end >= start else body[start:]


def _normalize_edge_type(value: object) -> str:
    raw = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_").upper()
    if not raw:
        return "REQUIRES_REVIEW"
    raw = EDGE_TYPE_ALIASES.get(raw, raw)
    return raw if raw in ALLOWED_EDGE_TYPES else "REQUIRES_REVIEW"


def _normalize_proposed_edge(edge: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(edge)
    original_type = str(edge.get("type") or "")
    edge_type = _normalize_edge_type(original_type)
    normalized["type"] = edge_type
    normalized["controlled_edge_type"] = edge_type
    if original_type and original_type != edge_type:
        normalized["original_type"] = original_type
    if edge_type == "REQUIRES_REVIEW":
        normalized["schema_warning"] = "Edge type was outside the controlled vocabulary and must be reviewed before promotion."
    normalized["allowed_edge_types_version"] = "baltor-graph-edge-types-2026-06-01"
    normalized["promotion_allowed"] = False
    return normalized


def _llm_input(payload: dict[str, Any], *, max_chars: int = 10000) -> dict[str, Any]:
    data = {
        "purpose": payload.get("purpose"),
        "claims": payload.get("claims") or [],
        "nodes": payload.get("nodes") or [],
        "edges": payload.get("edges") or [],
        "conflict_candidates": payload.get("conflict_candidates") or [],
        "context_concerns": payload.get("context_concerns") or [],
        "output_rules": payload.get("output_rules") or {},
    }
    text = json.dumps(data, ensure_ascii=True, sort_keys=True)
    if len(text) <= max_chars:
        return data
    return {
        "purpose": payload.get("purpose"),
        "truncated": True,
        "claims": (payload.get("claims") or [])[:12],
        "nodes": (payload.get("nodes") or [])[:20],
        "edges": (payload.get("edges") or [])[:30],
        "conflict_candidates": (payload.get("conflict_candidates") or [])[:10],
        "context_concerns": (payload.get("context_concerns") or [])[:10],
        "output_rules": payload.get("output_rules") or {},
    }


def _run_llm_json(ctx: TaskContext, task_name: str, payload: dict[str, Any], *, output_key: str, schema_hint: dict[str, Any]) -> dict[str, Any]:
    model_route = payload.get("model_route") if isinstance(payload.get("model_route"), dict) else {}
    route = _selected_chat_route(model_route)
    if route is None:
        return {
            output_key: [],
            "adapter_status": "no_compliant_model_route",
            "model_route": model_route,
            "llm_error": "No selected local/allowed model route.",
        }

    system = (
        "You are a local evidence-review worker. Return only strict JSON. "
        "Do not promote claims to verified facts. Do not memorize or update facts. "
        "Every proposed claim, edge, or summary must refer to source claim IDs or evidence IDs when available."
    )
    user = json.dumps({
        "task": task_name,
        "run_id": ctx.run_id,
        "input": _llm_input(payload),
        "required_json_shape": schema_hint,
    }, ensure_ascii=True, sort_keys=True)
    raw = route.complete(system, user, max_tokens=1400, temperature=0.0)
    if not raw:
        return {
            output_key: [],
            "adapter_status": "model_unreachable_or_failed",
            "model_route": model_route,
            "llm_error": "Selected route did not return a response.",
        }
    try:
        parsed = json.loads(_json_slice(raw))
    except Exception as exc:
        return {
            output_key: [],
            "adapter_status": "invalid_model_json",
            "model_route": model_route,
            "llm_raw_preview": raw[:1000],
            "llm_error": str(exc),
        }
    records = parsed.get(output_key) if isinstance(parsed, dict) else parsed
    if records is None:
        records = []
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list):
        records = [{"value": records}]
    return {
        output_key: records,
        "adapter_status": "executed",
        "model_route": model_route,
        "llm_raw_preview": raw[:1000],
        "model": route.model_id,
    }


@registry.register(
    "llm.claim.review",
    lane="verify",
    description="Placeholder execution contract for small/local LLM claim clarity and evidence review.",
    emits=("llm_claim_reviews",),
    capabilities=("claim_review", "structured_json"),
    task_types=("llm.claim.review",),
    image="baltor-worker-gpu",
    output_contract="llm_claim_reviews.v1",
)
def llm_claim_review(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    output = _run_llm_json(ctx, "llm.claim.review", payload, output_key="llm_claim_reviews", schema_hint={
        "llm_claim_reviews": [{
            "claim_id": "string",
            "support_status": "directly_supported|partially_supported|ambiguous|unsupported",
            "evidence_directness": "number 0..1",
            "temporal_fragility": "stable|slow_changing|medium_changing|fast_changing|real_time|unknown",
            "safe_context_policy": "safe_context|safe_with_warning|unsafe_without_refresh|unsafe_due_to_conflict|unsafe_due_to_ambiguity",
            "reason": "short string",
        }]
    })
    return TaskResult.success({**output, "training_examples": [_training_example(ctx, "llm.claim.review", payload, output)]})


@registry.register(
    "llm.conflict.review",
    lane="verify",
    description="Placeholder execution contract for LLM contradiction/support review over related claims.",
    emits=("llm_conflict_reviews",),
    capabilities=("conflict_detection", "structured_json"),
    task_types=("llm.conflict.review",),
    image="baltor-worker-gpu",
    output_contract="llm_conflict_reviews.v1",
)
def llm_conflict_review(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    output = _run_llm_json(ctx, "llm.conflict.review", payload, output_key="llm_conflict_reviews", schema_hint={
        "llm_conflict_reviews": [{
            "claim_ids": ["string"],
            "conflict_status": "no_conflict|apparent_conflict|temporal_update|contradiction|not_enough_context",
            "preferred_claim_id": "string|null",
            "requires_human_review": "boolean",
            "reason": "short string",
        }]
    })
    return TaskResult.success({**output, "training_examples": [_training_example(ctx, "llm.conflict.review", payload, output)]})


@registry.register(
    "llm.graph.enrich",
    lane="graph",
    description="Placeholder execution contract for LLM-proposed nodes, edges, aliases, and evidence links.",
    emits=("llm_proposed_nodes", "llm_proposed_edges"),
    capabilities=("graph_extraction", "structured_json"),
    task_types=("llm.graph.enrich",),
    image="baltor-worker-gpu",
    output_contract="llm_graph_enrichment.v1",
)
def llm_graph_enrich(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    output = _run_llm_json(ctx, "llm.graph.enrich", payload, output_key="llm_graph_enrichment", schema_hint={
        "llm_graph_enrichment": [{
            "proposed_nodes": [{"label": "string", "type": "string", "evidence_ids": ["string"]}],
            "proposed_edges": [{"source": "string", "type": "string", "target": "string", "evidence_ids": ["string"], "confidence": "number 0..1"}],
            "promotion_allowed": False,
        }]
    })
    enrichments = output.pop("llm_graph_enrichment", [])
    proposed_nodes: list[dict[str, Any]] = []
    proposed_edges: list[dict[str, Any]] = []
    for item in enrichments:
        if isinstance(item, dict):
            proposed_nodes.extend([node for node in item.get("proposed_nodes", []) if isinstance(node, dict)])
            proposed_edges.extend([_normalize_proposed_edge(edge) for edge in item.get("proposed_edges", []) if isinstance(edge, dict)])
    output = {**output, "llm_proposed_nodes": proposed_nodes, "llm_proposed_edges": proposed_edges, "llm_graph_enrichment": enrichments}
    return TaskResult.success({**output, "training_examples": [_training_example(ctx, "llm.graph.enrich", payload, output)]})


@registry.register(
    "llm.context.summarize",
    lane="analyze",
    description="Placeholder execution contract for cited source/node/corpus summaries.",
    emits=("llm_summaries",),
    capabilities=("summarization", "structured_json"),
    task_types=("llm.context.summarize",),
    image="baltor-worker-gpu",
    output_contract="llm_summaries.v1",
)
def llm_context_summarize(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    output = _run_llm_json(ctx, "llm.context.summarize", payload, output_key="llm_summaries", schema_hint={
        "llm_summaries": [{
            "summary_type": "claim_set|entity|document|risk",
            "text": "short cited summary with caveats",
            "supported_claim_ids": ["string"],
            "freshness_warning": "string",
            "faithfulness_risk": "low|medium|high",
        }]
    })
    return TaskResult.success({**output, "training_examples": [_training_example(ctx, "llm.context.summarize", payload, output)]})


@registry.register(
    "llm.audit.review",
    lane="verify",
    description="Approval-gated frontier/human-audit contract for high-risk trust-layer findings.",
    emits=("llm_audit_reviews",),
    capabilities=("audit_review", "structured_json"),
    task_types=("llm.audit.review",),
    image="baltor-worker-audit",
    output_contract="llm_audit_reviews.v1",
)
def llm_audit_review(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    output = _run_llm_json(ctx, "llm.audit.review", payload, output_key="llm_audit_reviews", schema_hint={
        "llm_audit_reviews": [{
            "decision": "approve_with_warning|reject|requires_human_review|requires_refresh",
            "reason": "short string",
            "blocked_claim_ids": ["string"],
            "safe_context_instruction": "string",
        }]
    })
    if output.get("adapter_status") == "no_compliant_model_route":
        output["adapter_status"] = "approval_or_human_review_required"
    return TaskResult.success({**output, "training_examples": [_training_example(ctx, "llm.audit.review", payload, output)]})
