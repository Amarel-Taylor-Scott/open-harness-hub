#!/usr/bin/env python3
"""src.baltor.contextops.research_stub — the DETERMINISTIC offline research agent + candidate catalog stubs.

``research.local_stub@v1`` is the working critical-path bounded research agent: given a ``ResearchTask`` it
returns a ``SourceDiscoveryReport`` (``serves_truth=False``) whose candidates each carry a ``source_handle``,
plus a replayable ``trace_ref``. It NEVER calls out (offline, stdlib), NEVER serves/promotes a fact, and stays
inside ``task.bounds``. It is the live half of THE INVARIANT: *agents DISCOVER and PROPOSE; Baltor STORES,
VERIFIES, RECONCILES, PROVES, CONSUMES.*

The candidate providers — ``research.hermes`` / ``research.openclaw`` / ``research.claude_code`` /
``research.openhands`` / ``research.open_swe`` — are CATALOG ENTRIES ONLY. They are NEVER imported or executed
in this repo: their stub ``research()`` raises :class:`ResearchAgentUnavailable` naming the ``env://…``
runtime/credential ref they would need, and ``status()`` reports ``unavailable`` with ``imported=False`` /
``executed=False``. A candidate provider can therefore never accidentally serve a fact or run an unbounded
agent in the lean core — the system stays green and the local stub does the work.

Determinism: ids are ``hashlib`` content hashes over identity fields; ``now`` is INJECTED; no RNG, no clock,
no network. Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from src.baltor.ports.research_agent_provider import (
    AGENT_SERVES_TRUTH,
    RESEARCH_PRODUCES,
    ResearchAgentProviderPort,
    ResearchAgentUnavailable,
)

#: the working local-stub provider id (single source — used in describe/status/report.discovered_by).
LOCAL_STUB_PROVIDER_ID = "research.local_stub@v1"

#: the SourceDiscoveryReport contract version this stub emits (single source).
DISCOVERY_REPORT_SCHEMA_VERSION = "SourceDiscoveryReport.v1"

#: id prefixes (content-addressed) — one definition each.
_REPORT_PREFIX = "sdr-"
_TRACE_PREFIX = "objref:sha256:"

#: the candidate research providers, as CATALOG ENTRIES ONLY. Each carries the env:// runtime/credential ref
#: it would require. None is imported or executed. Single source for the candidate-agent catalog (MAIN mirrors
#: this into external_capability_catalog.json + repo_replacement_matrix.json under the research_agent slot).
CANDIDATE_PROVIDERS: dict[str, dict[str, str]] = {
    "research.hermes@candidate": {
        "provider": "Hermes (bounded open-ended research agent)",
        "credential_ref": "env://HERMES_AGENT_ENDPOINT",
        "note": "candidate open-ended research agent; catalog entry only — never imported/executed in the lean core",
    },
    "research.openclaw@candidate": {
        "provider": "OpenClaw",
        "credential_ref": "env://OPENCLAW_AGENT_ENDPOINT",
        "note": "candidate research agent; catalog entry only — never imported/executed",
    },
    "research.claude_code@candidate": {
        "provider": "Claude Code (as a bounded research driver)",
        "credential_ref": "env://CLAUDE_CODE_AGENT_ENDPOINT",
        "note": "candidate research driver; catalog entry only — never imported/executed",
    },
    "research.openhands@candidate": {
        "provider": "OpenHands (as a bounded research agent)",
        "credential_ref": "env://OPENHANDS_AGENT_ENDPOINT",
        "note": "candidate research agent; catalog entry only — distinct from the agent_runtime FOIL; never imported/executed",
    },
    "research.open_swe@candidate": {
        "provider": "Open SWE (as a bounded research agent)",
        "credential_ref": "env://OPEN_SWE_AGENT_ENDPOINT",
        "note": "candidate research agent; catalog entry only — never imported/executed",
    },
}


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16]


class LocalResearchStub:
    """``research.local_stub@v1`` — the deterministic OFFLINE bounded research agent (a working stdlib stub).

    Implements :class:`ResearchAgentProviderPort`. ``research`` discovers candidate sources for a ResearchTask
    from a DETERMINISTIC offline knowledge of where authoritative sources live (no network), ranks nothing
    itself beyond carrying authority notes, and returns a SourceDiscoveryReport whose ``serves_truth`` is
    pinned False and whose every candidate carries a source_handle. It can never serve/promote a fact.
    """

    provider_id = LOCAL_STUB_PROVIDER_ID
    role = "stub"
    status_value = "active"

    def __init__(self, *, source_index: dict[str, list[dict[str, str]]] | None = None) -> None:
        # an OFFLINE, deterministic map: fact_key -> ordered candidate source descriptors. Defaults cover the
        # CFPB reference scenario; callers can inject their own offline index (still no network).
        self._index: dict[str, list[dict[str, str]]] = source_index or _DEFAULT_SOURCE_INDEX

    # ── capability card (no I/O, no import of any external runtime) ──────────────────────────────────
    def describe(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "role": self.role,
            "status": self.status_value,
            "supported_access": ["fixture", "local_file"],
            "offline": True,
            "imported": False,    # the stub IS this repo; it imports no external research runtime
            "executed": False,    # runs deterministic offline logic, not an external agent runtime
            "produces": RESEARCH_PRODUCES,
            "agent_may_serve_truth": AGENT_SERVES_TRUTH,
        }

    def status(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": "active",
            "imported": False,
            "executed": False,
            "detail": "deterministic offline local stub; no external runtime or credentials needed",
        }

    # ── the bounded discovery loop — DISCOVERS + PROPOSES, never serves a fact ───────────────────────
    def research(self, task: dict[str, Any], *, now: str) -> dict[str, Any]:
        """Run the bounded discovery loop for ``task`` and return a SourceDiscoveryReport.v1 dict.

        Stays inside ``task['bounds']``: never exceeds max_steps, never uses a non-allowlisted access method,
        never requests secrets. ``serves_truth`` is pinned False; every candidate carries a source_handle; the
        report names ``discovered_by`` = this provider; a ``trace_ref`` points at the (content-addressed) run
        trace. Deterministic over (task, now)."""
        bounds = dict(task.get("bounds") or {})
        if bounds.get("secrets_allowed"):
            raise ResearchAgentUnavailable(
                self.provider_id, "env://NONE",
                "task.bounds.secrets_allowed is true — the local stub never accepts a secrets-bearing task")
        max_steps = int(bounds.get("max_steps", 0) or 0)
        fact_key = task.get("fact_key", "")
        tenant_id = task.get("tenant_id", "")
        scope = task.get("source_scope", "global_public")
        task_id = task.get("task_id", "")

        # discover candidates from the OFFLINE index, one "search" step each, capped by the step budget.
        found = self._index.get(fact_key, [])
        steps_used = min(len(found), max_steps) if max_steps else len(found)
        candidates: list[dict[str, str]] = []
        for desc in found[:steps_used or len(found)]:
            cand_id = "scand-" + _hash({"h": desc["source_handle"], "scope": scope})
            entry = {"candidate_id": cand_id, "source_handle": desc["source_handle"]}
            if desc.get("authority_note"):
                entry["authority_note"] = desc["authority_note"]
            candidates.append(entry)

        trace_ref = f"{_TRACE_PREFIX}trace-{_hash({'task': task_id, 'fk': fact_key})}:{tenant_id}"
        report_id = _REPORT_PREFIX + _hash({"task": task_id, "handles": [c["source_handle"] for c in candidates]})

        report: dict[str, Any] = {
            "schema_version": DISCOVERY_REPORT_SCHEMA_VERSION,
            "report_id": report_id,
            "task_id": task_id,
            "tenant_id": tenant_id,
            "source_scope": scope,
            "discovered_by": self.provider_id,
            "candidates": candidates,
            "serves_truth": AGENT_SERVES_TRUTH,  # PINNED False — never a fact
            "trace_ref": trace_ref,
            "notes": (f"{len(candidates)} candidate source(s) discovered offline for {fact_key!r}; "
                      f"Baltor reconciliation/verification decide what (if anything) becomes a fact"),
            "discovered_at": now,
        }
        return report


class CandidateResearchStub:
    """A CATALOG-ONLY candidate research provider (Hermes/OpenClaw/Claude Code/OpenHands/Open SWE).

    It is NEVER imported or executed: ``research`` raises :class:`ResearchAgentUnavailable` naming its
    ``env://…`` runtime/credential ref, and ``status`` reports ``unavailable`` with ``imported=False`` /
    ``executed=False``. This makes the candidate-agent slot real (a typed provider behind the
    ResearchAgentProviderPort) WITHOUT pulling in an external runtime — the lean-core correctness invariant uses
    :class:`LocalResearchStub`. A candidate can therefore never serve a fact or run an unbounded agent here.
    """

    role = "candidate"
    status_value = "unavailable"

    def __init__(self, provider_id: str) -> None:
        if provider_id not in CANDIDATE_PROVIDERS:
            raise ValueError(f"unknown candidate research provider {provider_id!r}; "
                             f"known: {sorted(CANDIDATE_PROVIDERS)}")
        self.provider_id = provider_id
        self._card = CANDIDATE_PROVIDERS[provider_id]

    def describe(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider": self._card["provider"],
            "role": self.role,
            "status": self.status_value,
            "imported": False,
            "executed": False,
            "credential_ref": self._card["credential_ref"],
            "produces": RESEARCH_PRODUCES,
            "agent_may_serve_truth": AGENT_SERVES_TRUTH,
            "note": self._card["note"],
        }

    def status(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": "unavailable",
            "imported": False,
            "executed": False,
            "credential_ref": self._card["credential_ref"],
            "detail": "catalog candidate only; not imported/executed in the lean core",
        }

    def research(self, task: dict[str, Any], *, now: str) -> dict[str, Any]:
        raise ResearchAgentUnavailable(
            self.provider_id, self._card["credential_ref"],
            "candidate research agents are catalog entries only — use research.local_stub@v1 in the lean core")


#: an OFFLINE, deterministic default source index for the CFPB reference scenario. fact_key -> ordered candidates
#: (highest authority first). NO network — these are known source handles + authority notes only.
_DEFAULT_SOURCE_INDEX: dict[str, list[dict[str, str]]] = {
    "reg_e.error_resolution.deadline": [
        {"source_handle": "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i",
         "authority_note": "eCFR source-of-law; the binding Regulation E text (highest authority)"},
        {"source_handle": "ctx://public/source/cfpb-faq/error-resolution#q12",
         "authority_note": "agency FAQ restating the rule; LOWER authority than the regulation"},
    ],
    "cfpb.error_resolution.investigation_deadline": [
        {"source_handle": "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i",
         "authority_note": "eCFR source-of-law; the binding Regulation E text (highest authority)"},
        {"source_handle": "ctx://public/source/cfpb-faq/error-resolution#q12",
         "authority_note": "agency FAQ restating the rule; LOWER authority than the regulation"},
    ],
}


def make_provider(provider_id: str, **kwargs: Any) -> ResearchAgentProviderPort:
    """Return a research provider by id. ``research.local_stub@v1`` → the working :class:`LocalResearchStub`;
    any catalog candidate id → a :class:`CandidateResearchStub` (catalog entry only, raises on research())."""
    if provider_id == LOCAL_STUB_PROVIDER_ID:
        return LocalResearchStub(**kwargs)
    return CandidateResearchStub(provider_id)
