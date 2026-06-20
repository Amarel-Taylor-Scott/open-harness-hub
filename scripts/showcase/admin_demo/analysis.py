"""Deterministic context analysis for the Baltor admin demo."""
from __future__ import annotations

import datetime as _dt
import hashlib
import re

from scripts.context_workers.priority import make_research_task
from scripts.model_gateway import ModelRouteCandidate, resolve_model_route

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_ENTITY_RE = re.compile(
    r"\b(?:[A-Z][a-z0-9]+|[A-Z]{2,})(?:[\s/&-]+(?:[A-Z][a-z0-9]+|[A-Z]{2,})){0,5}\b"
)
_DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|20\d{2})\b",
    re.I,
)
_NUMBER_RE = re.compile(r"\b(?:\$\s?\d[\d,]*(?:\.\d+)?|\d+(?:\.\d+)?\s?(?:%|percent|bps|days|months|years|hours))\b", re.I)
_URL_RE = re.compile(r"https?://[^\s)>\"]+")
_CLAIM_SIGNAL_RE = re.compile(
    r"\b(is|are|was|were|must|shall|should|required|requires|prohibited|allowed|deadline|effective|expires|updated|current|latest|policy|rule|threshold|limit)\b",
    re.I,
)
_VOLATILE_RE = re.compile(r"\b(current|currently|latest|recent|recently|today|now|as of|deadline|expires|price|rate|threshold|limit|policy|regulation)\b", re.I)
_AMBIGUOUS_RE = re.compile(r"\b(may|might|could|usually|generally|soon|recently|approximately|about|expected|planned|likely)\b", re.I)
_NEGATIVE_RE = re.compile(r"\b(not|no longer|prohibited|forbidden|cannot|must not|invalid|expired|revoked)\b", re.I)
_POSITIVE_RE = re.compile(r"\b(required|must|shall|allowed|valid|approved|effective|active|enabled)\b", re.I)

_BUDGET_ACTION_LABELS = {
    "allow": "Queued",
    "batch": "Batch when efficient",
    "require_approval": "Needs approval",
    "block": "Blocked",
}


def _demo_model_candidates() -> list[ModelRouteCandidate]:
    return [
        ModelRouteCandidate(
            adapter="local-gemma-efficient",
            lane="local_efficient",
            model="gemma-class-local",
            provider="ollama",
            trust_boundary="local",
            quality_tier="local_efficient",
            capabilities=("summary", "claim.extract", "classify", "vision.caption"),
            modalities=("text", "image"),
            data_retention="local",
            estimated_cost_usd=0.0,
            latency_ms=900,
        ),
        ModelRouteCandidate(
            adapter="self-hosted-qwen-medium",
            lane="open_weight_medium",
            model="qwen-medium-self-hosted",
            provider="vllm",
            trust_boundary="tenant",
            quality_tier="open_weight_medium",
            capabilities=("claim.normalize", "evidence.match", "edge.propose", "summary.reduce"),
            modalities=("text",),
            data_retention="local",
            estimated_cost_usd=0.006,
            latency_ms=2200,
        ),
        ModelRouteCandidate(
            adapter="hosted-free-credit-open-weight",
            lane="open_weight_medium",
            model="open-weight-medium-free-credit",
            provider="openrouter",
            trust_boundary="hosted",
            quality_tier="open_weight_medium",
            capabilities=("source.verify", "web.summarize", "claim.extract"),
            modalities=("text",),
            data_retention="zero",
            free_credit=True,
            estimated_cost_usd=0.012,
            latency_ms=3000,
        ),
        ModelRouteCandidate(
            adapter="large-open-weight-audit",
            lane="open_weight_large",
            model="kimi-qwen-glm-large-audit",
            provider="self-hosted-gpu",
            trust_boundary="tenant",
            quality_tier="open_weight_large",
            capabilities=("audit", "reconcile", "procedure.discover"),
            modalities=("text",),
            data_retention="local",
            estimated_cost_usd=0.08,
            latency_ms=8500,
        ),
        ModelRouteCandidate(
            adapter="frontier-controlled-review",
            lane="frontier_controlled",
            model="frontier-reviewer",
            provider="frontier-api",
            trust_boundary="frontier",
            quality_tier="frontier_controlled",
            capabilities=("adjudicate", "hard.research"),
            modalities=("text", "image"),
            data_retention="zero",
            estimated_cost_usd=0.75,
            latency_ms=11000,
        ),
    ]


def _compact_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _stable_id(prefix: str, text: str, n: int) -> str:
    digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"{prefix}-{n:03d}-{digest}"


def _split_chunks(text: str, target_chars: int = 900) -> list[dict]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [_compact_space(text)] if text.strip() else []
    chunks: list[dict] = []
    buf: list[str] = []
    size = 0
    for p in paragraphs:
        if buf and size + len(p) > target_chars:
            body = "\n\n".join(buf)
            chunks.append({"id": _stable_id("chunk", body, len(chunks) + 1), "text": body, "char_count": len(body)})
            buf, size = [], 0
        if len(p) > target_chars * 1.4:
            sentences = _SENTENCE_RE.split(p)
            for s in sentences:
                if buf and size + len(s) > target_chars:
                    body = " ".join(buf)
                    chunks.append({"id": _stable_id("chunk", body, len(chunks) + 1), "text": body, "char_count": len(body)})
                    buf, size = [], 0
                buf.append(s)
                size += len(s) + 1
            continue
        buf.append(p)
        size += len(p) + 2
    if buf:
        body = "\n\n".join(buf)
        chunks.append({"id": _stable_id("chunk", body, len(chunks) + 1), "text": body, "char_count": len(body)})
    return chunks


def _sentences(text: str) -> list[str]:
    raw = []
    for paragraph in re.split(r"\n\s*\n", text):
        raw.extend(_SENTENCE_RE.split(paragraph.strip()))
    return [_compact_space(s) for s in raw if len(_compact_space(s)) >= 20]


def _extract_entities(text: str) -> list[str]:
    stop = {
        "The", "This", "That", "These", "Those", "We", "Our", "It", "If", "When", "Then",
        "As", "According", "A", "An", "Later", "Current", "Latest", "Recruitment",
    }
    found = []
    for m in _ENTITY_RE.finditer(text):
        ent = _compact_space(m.group(0).strip(" .,:;()[]{}"))
        if ent and ent not in stop and len(ent) > 2 and not ent.lower().startswith(("according ", "as of ")):
            found.append(ent)
    return sorted(set(found), key=lambda s: (-len(s.split()), s.lower()))[:80]


def _claim_subject(sentence: str, entities: list[str]) -> str:
    lowered = sentence.lower()
    for ent in entities:
        if ent.lower() in lowered:
            return ent
    words = re.findall(r"[A-Za-z0-9-]+", sentence)
    return " ".join(words[:5]).lower() if words else "claim"


def _priority_signals(fact: dict) -> dict:
    signals = set(fact.get("signals") or [])
    risk = 0.35
    impact = 0.35
    if "numeric" in signals:
        risk += 0.16
    if "volatile" in signals or "dated" in signals:
        risk += 0.18
    if "needs-reconciliation" in signals:
        risk += 0.25
        impact += 0.18
    if "ambiguous" in signals:
        risk += 0.12
    return {
        "risk": round(min(risk, 1.0), 3),
        "customer_impact": round(min(impact, 1.0), 3),
        "agent_usage": 35 if fact.get("confidence") == "low" else 15,
        "freshness_age_hours": 96 if "dated" in signals else 36,
        "injection_risk": 0.12 if "source-linked" in signals else 0.04,
        "failed_attempts": 3 if "ambiguous" in signals and "dated" in signals else 0,
    }


def _fact_state(fact: dict, reasons: list[str]) -> str:
    signals = set(fact.get("signals") or [])
    if "needs-reconciliation" in signals:
        return "needs_reconciliation"
    if any("needs a citable external source" in reason for reason in reasons):
        return "needs_official_or_primary_source"
    if any("ambiguous wording" in reason for reason in reasons):
        return "needs_second_source"
    if "source-linked" in signals:
        return "one_source_found"
    return "candidate_detected"


def _build_queue_plan(run_id: str, facts: list[dict], fragile: list[dict], updates: list[dict]) -> dict:
    fragile_by_id = {item.get("fact_id"): item for item in fragile}
    update_by_id = {item.get("fact_id"): item for item in updates}
    tasks = []
    for fact in facts:
        if fact.get("id") not in update_by_id and fact.get("id") not in fragile_by_id:
            continue
        reasons = fragile_by_id.get(fact.get("id"), {}).get("reasons", [])
        task_input = {
            "id": fact.get("id"),
            "fact_id": fact.get("id"),
            "subject": fact.get("subject"),
            "target": fact.get("subject"),
            "state": fact.get("state") or _fact_state(fact, reasons),
            "independent_source_count": 1 if "source-linked" in (fact.get("signals") or []) else 0,
            "authoritative_source_count": 0,
            "priority_signals": _priority_signals(fact),
            "task_budget_ceiling_usd": 0.10 if "ambiguous" in (fact.get("signals") or []) and "dated" in (fact.get("signals") or []) else 0.25,
        }
        task = make_research_task(run_id=run_id, tenant_id="demo-tenant", fact=task_input)
        budget = task.get("budget_policy") or {}
        cost = task.get("cost_estimate") or {}
        tasks.append({
            "fact_id": fact.get("id"),
            "claim": fact.get("claim"),
            "target": fact.get("subject"),
            "lane": task.get("lane"),
            "task_type": task.get("task_type"),
            "priority": task.get("priority"),
            "action": budget.get("action", "allow"),
            "action_label": _BUDGET_ACTION_LABELS.get(str(budget.get("action") or "allow"), "Queued"),
            "reason_codes": budget.get("reason_codes") or [],
            "estimated_total_usd": cost.get("estimated_total_usd", 0),
            "dedupe_key": (task.get("queue_policy") or {}).get("dedupe_key"),
            "state_history": [
                {"state": "candidate_detected", "actor": "extract-worker", "note": "Claim extracted from customer source"},
                {"state": task_input["state"], "actor": "priority-policy", "note": "Follow-up task selected from evidence and budget rules"},
            ],
        })
    actions = {}
    lanes = {}
    for task in tasks:
        actions[task["action"]] = actions.get(task["action"], 0) + 1
        lanes[task["lane"]] = lanes.get(task["lane"], 0) + 1
    return {
        "summary": {
            "total": len(tasks),
            "queued": actions.get("allow", 0),
            "batched": actions.get("batch", 0),
            "approval_required": actions.get("require_approval", 0),
            "blocked": actions.get("block", 0),
            "estimated_total_usd": round(sum(float(task.get("estimated_total_usd") or 0) for task in tasks), 4),
        },
        "lanes": lanes,
        "tasks": tasks[:80],
    }


def _route_status(record: dict) -> str:
    if record.get("selected_adapter") == "none":
        return "approval_required"
    trust = record.get("trust_boundary")
    if trust == "local":
        return "local"
    if trust == "tenant":
        return "self_hosted"
    if trust == "hosted":
        return "hosted"
    if trust == "frontier":
        return "frontier"
    return "selected"


def _build_model_routes(facts: list[dict], updates: list[dict]) -> list[dict]:
    candidates = _demo_model_candidates()
    route_tasks = [
        {
            "label": "Chunk summaries",
            "task": "context.chunk.summary",
            "model_policy": {"capability": "summary", "lane": "local_efficient"},
            "data_policy": {"privacy_scope": "tenant"},
        },
        {
            "label": "Claim extraction",
            "task": "context.claim.extract",
            "model_policy": {"capability": "claim.extract", "lane": "local_efficient"},
            "data_policy": {"privacy_scope": "tenant"},
        },
        {
            "label": "Claim normalization",
            "task": "context.claim.normalize",
            "model_policy": {"capability": "claim.normalize", "lane": "open_weight_medium"},
            "data_policy": {"privacy_scope": "tenant"},
            "budget_policy": {"max_model_cost_usd": 0.05},
        },
        {
            "label": "External source verification",
            "task": "context.source.verify",
            "model_policy": {"capability": "source.verify", "lane": "open_weight_medium", "allow_cloud": True},
            "data_policy": {"privacy_scope": "public", "require_zero_data_retention": True},
            "budget_policy": {"max_model_cost_usd": 0.05},
        },
        {
            "label": "OpenClaw audit",
            "task": "openclaw.adversarial.review",
            "model_policy": {"capability": "audit", "lane": "open_weight_large"},
            "data_policy": {"privacy_scope": "tenant"},
            "budget_policy": {"max_model_cost_usd": 0.12},
        },
        {
            "label": "Frontier adjudication",
            "task": "context.fact.adjudicate",
            "model_policy": {"capability": "adjudicate", "lane": "frontier_controlled", "allow_cloud": True},
            "data_policy": {"privacy_scope": "tenant", "require_zero_data_retention": True},
            "budget_policy": {"max_model_cost_usd": 0.25},
        },
    ]
    routes = []
    for index, task in enumerate(route_tasks, start=1):
        record = resolve_model_route(task, candidates=candidates, now=index)
        rejected = [item for item in record.get("fallbacks", []) if not item.get("accepted")]
        routes.append({
            "label": task["label"],
            "task_type": record.get("task_type"),
            "status": _route_status(record),
            "selected_adapter": record.get("selected_adapter"),
            "selected_model": record.get("selected_model"),
            "trust_boundary": record.get("trust_boundary"),
            "quality_tier": record.get("quality_tier"),
            "estimated_cost_usd": (record.get("cost_estimate") or {}).get("estimated_cost_usd"),
            "route_reason": record.get("route_reason"),
            "fallback_count": len(rejected),
            "fallback_reasons": sorted({reason for item in rejected for reason in item.get("reason_codes", [])})[:4],
        })
    return routes


def analyze_admin_context(text: str, filename: str = "", run_id: str = "admin-demo-preview") -> dict:
    """Run the local deterministic pass that mirrors the intended K8 worker stages."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return {"error": "context required"}

    chunks = _split_chunks(cleaned)
    all_entities = _extract_entities(cleaned)
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    facts: list[dict] = []
    fragile: list[dict] = []
    updates: list[dict] = []

    for ent in all_entities[:50]:
        nid = _stable_id("node", ent, len(nodes) + 1)
        nodes[ent] = {"id": nid, "label": ent, "type": "entity", "weight": cleaned.count(ent)}

    for chunk in chunks:
        cid = chunk["id"]
        for ent in all_entities:
            if ent in chunk["text"] and ent in nodes:
                edges.append({"from": nodes[ent]["id"], "to": cid, "type": "mentioned_in", "weight": chunk["text"].count(ent)})

    subject_groups: dict[str, list[dict]] = {}
    for chunk in chunks:
        chunk_entities = _extract_entities(chunk["text"])
        for sentence in _sentences(chunk["text"]):
            if not (_CLAIM_SIGNAL_RE.search(sentence) or _DATE_RE.search(sentence) or _NUMBER_RE.search(sentence)):
                continue
            n = len(facts) + 1
            subject = _claim_subject(sentence, chunk_entities or all_entities)
            signals = []
            if _VOLATILE_RE.search(sentence):
                signals.append("volatile")
            if _AMBIGUOUS_RE.search(sentence):
                signals.append("ambiguous")
            if _DATE_RE.search(sentence):
                signals.append("dated")
            if _NUMBER_RE.search(sentence):
                signals.append("numeric")
            if _URL_RE.search(sentence):
                signals.append("source-linked")
            if "according to" in sentence.lower() or "reportedly" in sentence.lower():
                signals.append("attributed")
            polarity = "negative" if _NEGATIVE_RE.search(sentence) else "positive" if _POSITIVE_RE.search(sentence) else "neutral"
            fact = {
                "id": _stable_id("fact", sentence, n),
                "claim": sentence,
                "subject": subject,
                "source_chunk": chunk["id"],
                "polarity": polarity,
                "signals": signals,
                "state": "candidate_detected",
                "independent_source_count": 1 if "source-linked" in signals else 0,
                "authoritative_source_count": 0,
                "state_history": [
                    {"state": "candidate_detected", "actor": "extract-worker", "note": "Claim extracted from uploaded context"}
                ],
                "confidence": "medium",
            }
            facts.append(fact)
            subject_groups.setdefault(subject.lower(), []).append(fact)
            edges.append({"from": fact["id"], "to": chunk["id"], "type": "supported_by", "weight": 1})
            for ent in chunk_entities[:4]:
                if ent in nodes:
                    edges.append({"from": fact["id"], "to": nodes[ent]["id"], "type": "mentions", "weight": 1})

    for group in subject_groups.values():
        polarities = {f["polarity"] for f in group}
        if len(group) > 1 and {"positive", "negative"}.issubset(polarities):
            for f in group:
                f["signals"] = sorted(set(f["signals"] + ["needs-reconciliation"]))

    today = _dt.date.today()
    for fact in facts:
        reasons = []
        if "needs-reconciliation" in fact["signals"]:
            reasons.append("reconcile with nearby claims before promotion")
        if "volatile" in fact["signals"] or "dated" in fact["signals"] or "numeric" in fact["signals"]:
            reasons.append("refreshable via search/tool worker")
        if "ambiguous" in fact["signals"]:
            reasons.append("ambiguous wording needs stronger source or narrower scope")
        if "source-linked" not in fact["signals"] and ("volatile" in fact["signals"] or "numeric" in fact["signals"]):
            reasons.append("needs a citable external source")
        if reasons:
            fact["state"] = _fact_state(fact, reasons)
            fact["state_history"].append({
                "state": fact["state"],
                "actor": "verification-policy",
                "note": "; ".join(reasons[:2]),
            })
            fact["confidence"] = "low" if len(reasons) >= 2 else "medium"
            fragile.append({"fact_id": fact["id"], "claim": fact["claim"], "reasons": reasons, "source_chunk": fact["source_chunk"]})
        if any(s in fact["signals"] for s in ("volatile", "dated", "numeric", "needs-reconciliation")):
            updates.append({
                "fact_id": fact["id"],
                "target": fact["subject"],
                "worker": "search-refresh" if "needs-reconciliation" not in fact["signals"] else "reconcile-and-verify",
                "query": f"{fact['subject']} {today.isoformat()} verification source",
                "priority": "high" if fact["confidence"] == "low" else "normal",
            })

    queue_plan = _build_queue_plan(run_id, facts, fragile, updates)
    model_routes = _build_model_routes(facts, updates)
    queue_by_fact = {task.get("fact_id"): task for task in queue_plan.get("tasks", [])}
    for update in updates:
        task = queue_by_fact.get(update.get("fact_id")) or {}
        if task:
            update["lane"] = task.get("lane")
            update["task_type"] = task.get("task_type")
            update["budget_action"] = task.get("action")
            update["estimated_total_usd"] = task.get("estimated_total_usd")

    chunk_nodes = [{"id": c["id"], "label": c["id"], "type": "chunk", "weight": c["char_count"]} for c in chunks]
    fact_nodes = [{"id": f["id"], "label": f["subject"], "type": "claim", "weight": 1} for f in facts[:80]]
    graph_nodes = list(nodes.values())[:50] + chunk_nodes + fact_nodes
    worker_plan = [
        {"stage": "ingest", "status": "ready", "output": f"{len(cleaned):,} characters from {filename or 'pasted context'}"},
        {"stage": "chunk", "status": "ready", "output": f"{len(chunks)} chunks with stable ids"},
        {"stage": "graph", "status": "ready", "output": f"{len(graph_nodes)} nodes and {len(edges)} edges"},
        {"stage": "extract", "status": "ready", "output": f"{len(facts)} candidate claims"},
        {"stage": "reconcile", "status": "ready", "output": f"{sum('needs-reconciliation' in f['signals'] for f in facts)} claims need reconciliation"},
        {"stage": "refresh", "status": "queued", "output": f"{len(updates)} search/tool worker candidates"},
        {"stage": "route", "status": "ready", "output": f"{len(model_routes)} model route policies resolved"},
        {"stage": "promote", "status": "blocked", "output": "Promotion requires verified sources and curator approval"},
    ]
    return {
        "summary": {
            "filename": filename or "pasted-context.txt",
            "characters": len(cleaned),
            "chunks": len(chunks),
            "entities": len(nodes),
            "claims": len(facts),
            "fragile_facts": len(fragile),
            "worker_updates": len(updates),
            "queue_approval_required": queue_plan["summary"]["approval_required"],
            "queue_blocked": queue_plan["summary"]["blocked"],
        },
        "chunks": chunks,
        "nodes": graph_nodes,
        "edges": edges[:300],
        "facts": facts[:120],
        "fragile_facts": fragile[:80],
        "updates": updates[:80],
        "queue_plan": queue_plan,
        "model_routes": model_routes,
        "worker_plan": worker_plan,
    }
