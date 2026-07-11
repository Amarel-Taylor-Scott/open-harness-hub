"""src.teleon.stateful_swarms.cfpb_evidence_demo — the Baltor GOVERNED-BLACKBOARD demo (``blackboard.baltor.cfpb_evidence@v1``).

Runs the deterministic OFFLINE :class:`~src.teleon.stateful_swarms.local_swarm.LocalStatefulSwarm` over the
synthetic CFPB Reg E fixture (``demo-data/cfpb-sample`` / the planted Reg E facts) and shows the full motion:

    signals -> observations (with source handles) -> gaps -> held-out allegations (kept SEPARATE) ->
    verified facts -> synthesis (reads the BOARD) -> governed answer -> receipts.

The planted facts (shared with ``src.teleon.environments.baltor_cfpb_context_governance``): the authoritative Reg E
§1005.11 answer is **"10 business days"** (extendable to 45 calendar days with provisional credit); a stale
internal FAQ says **"30 days"** — the HELD-OUT CONTRADICTION that must NEVER be served. The served answer here is
"10 business days" + a source handle; the stale "30 days" stays in ``held_out`` as a WARNING, never a substring of
the served answer.

THE GOVERNANCE BOUNDARY: ``serves_truth`` is False everywhere — the swarm produced analytical state, and the
governed projection returns a CANDIDATE + evidence (``promotion_eligible`` false). Teleon RETURNS evidence; Baltor
GOVERNS served truth. This module is Teleon infra modeling a Baltor-style task — it does **NOT import src.baltor**
(it reuses the planted facts via ``baltor_cfpb_context_governance``, itself Teleon infra). Stdlib only;
deterministic when ``now`` is injected; offline; no live LLM / install / network / cloud / secrets.
"""
from __future__ import annotations

from src.teleon.blackboard.local_sqlite_blackboard import py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard
from src.teleon.environments.baltor_cfpb_context_governance import (
    AUTHORITATIVE_ANSWER,
    AUTHORITATIVE_SOURCE_HANDLE,
    HELD_OUT_CONTRADICTION,
    load_fixture as load_cfpb_fixture,
)
from src.teleon.ports.blackboard_provider import (
    KIND_ANALYSIS,
    KIND_GAP,
    KIND_OBSERVATION,
    KIND_SIGNAL,
    KIND_SYNTHESIS,
)
from src.teleon.ports.stateful_swarm_provider import SWARM_SERVES_TRUTH
from src.teleon.stateful_swarms.local_swarm import DEFAULT_TENANT_SCOPE, LocalStatefulSwarm

#: the id of this Baltor-style governed-blackboard demo run (local-first; serves_truth False).
DEMO_ID = "blackboard.baltor.cfpb_evidence@v1"
#: the tenant scope for the CFPB demo (synthetic; tenant-isolated working state).
CFPB_TENANT_SCOPE = "tenant.cfpb-demo"
#: a stale FAQ source handle for the held-out "30 days" (from the cfpb-sample seed graph).
STALE_FAQ_HANDLE = "ctx://cfpb-sample/docs/disputes-faq.md#timeline"
#: a second corroborating handle (the SOP code that implements Reg E) — strengthens the served answer's lineage.
SOP_CODE_HANDLE = "ctx://cfpb-sample/sop/dispute_sla.py#L5-L7"


def build_cfpb_swarm_fixture(*, cfpb_fixture: dict | None = None) -> dict:
    """Build the swarm fixture from the planted CFPB Reg E facts.

    Two source-backed observations (the Reg E decision + the SOP code) both state the authoritative
    "10 business days"; the stale "30 days" FAQ is carried ONLY in ``held_out`` (a warning, never extracted as an
    observation, never folded into the answer). Reuses ``baltor_cfpb_context_governance.load_fixture`` (Teleon
    infra) so the planted facts are single-sourced; never imports src.baltor.
    """
    fx = cfpb_fixture if cfpb_fixture is not None else load_cfpb_fixture()
    authoritative = fx["authoritative_answer"]   # "10 business days"
    auth_handle = fx["source_handle"]            # ctx://cfpb-sample/regs/RegE-error-resolution.md#decision
    held_out_value = fx["held_out_contradiction"]  # "30 days"
    question = fx["question"]

    return {
        "task": question,
        "tenant_scope": CFPB_TENANT_SCOPE,
        "signals": [
            {"question": question, "priority": 10},
        ],
        "documents": [
            {
                "source_id": "src.cfpb.rege-decision",
                "handle": auth_handle,
                "authority_rank": 95,  # the regulation: highest authority
                "statement": f"Under Reg E §1005.11 the institution must resolve the error within {authoritative}.",
                "confidence": 0.98,
                "entity": "reg_e_error_resolution_deadline",
            },
            {
                "source_id": "src.cfpb.sop-code",
                "handle": SOP_CODE_HANDLE,
                "authority_rank": 85,  # the implementing code: corroborates the regulation
                "statement": f"The dispute SLA implements Reg E: error resolution within {authoritative}.",
                "confidence": 0.9,
                "entity": "reg_e_error_resolution_deadline",
            },
        ],
        # the stale FAQ "30 days" — preserved as a WARNING in held_out, NEVER extracted/served.
        "held_out": [
            {
                "source_id": "src.cfpb.stale-faq",
                "handle": STALE_FAQ_HANDLE,
                "statement": f"A pre-Reg-E-refresh FAQ still says we have {held_out_value} to resolve a dispute.",
                "reason": "stale: superseded by Reg E §1005.11; a contradiction held out as a warning, never served",
                "confidence": 0.4,
            },
        ],
        # the consolidated, source-backed candidate answer (NOT truth — Baltor governs promotion).
        "answer": (
            f"Under Reg E §1005.11 the institution must investigate and resolve the error within {authoritative} "
            f"(extendable to 45 calendar days with provisional credit). [source: {auth_handle}]"
        ),
    }


def run_cfpb_evidence_demo(*, now: str, blackboard: py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard | None = None,
                           cfpb_fixture: dict | None = None) -> dict:
    """Run ``blackboard.baltor.cfpb_evidence@v1``: the swarm over the CFPB Reg E fixture on a governed blackboard.

    Returns an envelope::

        {
          "demo_id", "provider_id", "blackboard_id", "tenant_scope",
          "served_answer",        # the consolidated answer — contains "10 business days" + a source handle
          "served_source_handles",
          "held_out",             # the stale "30 days" warning (NOT a substring of served_answer)
          "held_out_values",      # ["30 days"] — preserved, never served
          "governed_entry",       # GovernedBlackboardEntry verdict (serves_truth False; promotion_eligible False)
          "serves_truth",         # False everywhere
          "worker_results", "receipts",
          "signals", "observations", "gaps", "synthesis",  # the typed entries, for inspection
        }

    Deterministic for a fixed ``now``. ``blackboard`` is injectable (tests pass a tempfile / ``:memory:`` so the
    real .agent db is never touched). Offline; never imports src.baltor.
    """
    bb = blackboard if blackboard is not None else py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard(db_path=":memory:")
    fixture = build_cfpb_swarm_fixture(cfpb_fixture=cfpb_fixture)

    board = bb.create_blackboard(task=fixture["task"], tenant_scope=fixture["tenant_scope"], now=now)
    blackboard_id = board["blackboard_id"]

    swarm = LocalStatefulSwarm(blackboard=bb, fixture=fixture)
    run = swarm.run(fixture["task"], blackboard_id=blackboard_id, now=now)

    # pull the synthesis entry off the BOARD (the swarm read the board to build it).
    synth_rows = bb.query(blackboard_id, kind=KIND_SYNTHESIS)
    synth_body = synth_rows[0]["body"] if synth_rows else {}
    served_answer = synth_body.get("answer", "")
    served_source_handles = list(synth_body.get("source_handles", []))
    held_out = list(synth_body.get("held_out", []))

    return {
        "demo_id": DEMO_ID,
        "provider_id": swarm.provider_id,
        "blackboard_id": blackboard_id,
        "tenant_scope": fixture["tenant_scope"],
        "served_answer": served_answer,
        "served_source_handles": served_source_handles,
        "held_out": held_out,
        # the held-out CONTRADICTING value(s) — preserved as warnings, never in the served answer.
        "held_out_values": [HELD_OUT_CONTRADICTION],
        "governed_entry": run["governed_entry"],
        "serves_truth": SWARM_SERVES_TRUTH,  # False everywhere — Teleon returns evidence; Baltor governs truth
        "worker_results": run["worker_results"],
        "receipts": bb.get_receipts(blackboard_id),
        "signals": bb.query(blackboard_id, kind=KIND_SIGNAL),
        "observations": bb.query(blackboard_id, kind=KIND_OBSERVATION),
        "gaps": bb.query(blackboard_id, kind=KIND_GAP),
        "analyses": bb.query(blackboard_id, kind=KIND_ANALYSIS),
        "synthesis": synth_rows,
    }


def describe() -> dict:
    """Card for the Baltor governed-blackboard demo (local-first; serves_truth False; Teleon infra, no src.baltor)."""
    return {
        "demo_id": DEMO_ID,
        "name": "baltor-cfpb governed-blackboard demo (local)",
        "status": "active",
        "requires_network": False,
        "requires_keys": False,
        "serves_truth": False,
        "authoritative_answer": AUTHORITATIVE_ANSWER,
        "held_out_contradiction": HELD_OUT_CONTRADICTION,
        "authoritative_source_handle": AUTHORITATIVE_SOURCE_HANDLE,
        "models": "a Baltor-style governed-blackboard demo as Teleon infra; does not import src.baltor",
    }


__all__ = [
    "DEMO_ID",
    "CFPB_TENANT_SCOPE",
    "STALE_FAQ_HANDLE",
    "SOP_CODE_HANDLE",
    "build_cfpb_swarm_fixture",
    "run_cfpb_evidence_demo",
    "describe",
]
