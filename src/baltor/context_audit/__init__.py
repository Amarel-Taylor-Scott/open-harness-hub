"""src.baltor.context_audit — the Context Auditor (pre-LLM-call context-governance manifest).

Baltor governs CONTEXT; before context is handed to Teleon's inference gateway for routing, this auditor
normalizes every context source (system prompt, CLAUDE.md / AGENTS.md, MCP tool schemas, retrieved docs,
memories, tool outputs, code comments), assigns authority + recency, and emits a deterministic, auditable
optimization manifest (the ContextAuditReport) flagging redundant / conflicting / bloated / stale context.

It is the UNIFYING orchestrator that the per-source engines already shipped don't provide on their own
(context_graph.find_contradictions, context_compress, context_rot). It PROPOSES — it never disposes
(agents propose, Baltor disposes); dedupe/supersession are LOSSLESS proposals (raw is never mutated or
deleted, conflicts SURFACE both sides); its output is evidence, not truth. Baltor → Teleon only; this module
imports neither Teleon nor a model.
"""
from __future__ import annotations

from .audit_bridge import audit_and_emit, audited_pre_call, optimize_pre_call
from .context_auditor import (
    AUTHORITY_RANK,
    ISSUE_TYPES,
    SOURCE_KINDS,
    audit,
)
from .context_object_adapter import audit_context_graph, from_context_objects
from .optimizer import apply_manifest, rehydrate

__all__ = ["audit", "audit_and_emit", "audited_pre_call", "optimize_pre_call", "apply_manifest", "rehydrate",
           "from_context_objects", "audit_context_graph", "AUTHORITY_RANK", "SOURCE_KINDS", "ISSUE_TYPES"]
