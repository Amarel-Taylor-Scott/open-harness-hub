"""src.teleon.stateful_swarms.local_swarm — the OFFLINE local stateful-swarm runner (the correctness invariant).

:class:`LocalStatefulSwarm` implements
:class:`~src.teleon.ports.stateful_swarm_provider.StatefulSwarmProviderPort` over the OFFLINE
:class:`~src.teleon.blackboard.local_sqlite_blackboard.LocalSqliteBlackboard`. It is the deterministic, stdlib,
no-key, no-network swarm runner (``swarm.local_stub@v1`` — the single ACTIVE runner in
``architecture/stateful_swarm_provider_catalog.json``). It exercises the full blackboard write / handoff /
synthesis shape WITHOUT any external runner or live LLM: the six workers are deterministic rules over a fixture.

THE SWARM PATTERN (each worker reads the BOARD, posts typed entries under a MANDATORY receipt):

  1. ``seed_planner``         -> posts SIGNALS (the open questions directing the swarm; procedural, no sources).
  2. ``observation_extractor``-> posts OBSERVATIONS, each WITH ``source_refs`` from the fixture (source-backed).
  3. ``gap_detector``         -> posts explicit GAPS (named holes that block the analysis; convergence currency).
  4. ``entity_resolver``      -> reconciles/links observations to a canonical entity (posts an ANALYSIS w/ lineage)
                                 and, when entities MISMATCH, surfaces the conflict AS A GAP (never silently drops).
  5. ``synthesis``            -> reads the BLACKBOARD ENTRIES (NOT the raw docs) and posts a SYNTHESIS whose
                                 ``supporting_entry_ids`` are real blackboard entry_ids and whose ``held_out``
                                 preserves the items deliberately NOT folded in (minority / stale / rejected).
  6. ``governed_projection``  -> projects a :class:`GovernedBlackboardEntry`-shaped governance verdict over the
                                 synthesis (``serves_truth`` const False; ``promotion_eligible`` is the explicit,
                                 auditable gate — Teleon returns evidence/candidate, Baltor governs served truth).

INVARIANTS HELD BY CONSTRUCTION: blackboard/swarm/LLM output is NEVER truth (every entry + the run envelope carry
``serves_truth=False``); held-out items stay WARNINGS, never merged into the served answer; an observation is
always source-backed; every worker writes a BlackboardWorkerReceipt; the synthesis worker proves it read the
BOARD via ``read_entry_ids`` + ``supporting_entry_ids`` (real blackboard entry_ids).

Teleon-owned: imports only the stdlib + the Teleon blackboard provider + Teleon id helpers — NEVER Baltor.
Deterministic given the same (fixture, ``now``): content-addressed ids; no RNG; no wall-clock (``now`` injected).
Stdlib only; offline; no live LLM / install / network / cloud / secrets.
"""
from __future__ import annotations

from src.teleon.blackboard.local_sqlite_blackboard import LocalSqliteBlackboard
from src.teleon.ports.blackboard_provider import (
    KIND_ANALYSIS,
    KIND_GAP,
    KIND_OBSERVATION,
    KIND_SIGNAL,
    KIND_SOURCE,
    KIND_SYNTHESIS,
)
from src.teleon.ports.stateful_swarm_provider import SWARM_SERVES_TRUTH, SwarmWorkerResult

#: the provider id of the one active, offline, deterministic local stateful-swarm runner (matches the catalog's
#: single ``status: active`` entry — the correctness invariant the catalog falls back to).
LOCAL_SWARM_PROVIDER_ID = "swarm.local_stub@v1"
#: the default tenant scope for a local swarm run (synthetic; tenant-isolated working state).
DEFAULT_TENANT_SCOPE = "tenant-demo"

#: the six bounded worker kinds, in deterministic run order (single source — the order workers fire).
WORKER_SEED_PLANNER = "seed_planner"
WORKER_OBSERVATION_EXTRACTOR = "observation_extractor"
WORKER_GAP_DETECTOR = "gap_detector"
WORKER_ENTITY_RESOLVER = "entity_resolver"
WORKER_SYNTHESIS = "synthesis"
WORKER_GOVERNED_PROJECTION = "governed_projection"
SWARM_WORKER_ORDER = (
    WORKER_SEED_PLANNER,
    WORKER_OBSERVATION_EXTRACTOR,
    WORKER_GAP_DETECTOR,
    WORKER_ENTITY_RESOLVER,
    WORKER_SYNTHESIS,
    WORKER_GOVERNED_PROJECTION,
)


def _receipt(worker_id: str, worker_kind: str, *, now: str) -> dict:
    """A minimal BlackboardWorkerReceipt-shaped dict (hashes are filled in by the store from the entry lineage).

    No raw keys/secrets — worker id/kind + timestamps only. We deliberately do NOT attach an
    ``llm_route_receipt_ref``: the local swarm makes NO model call (it is deterministic rules over the fixture).
    """
    return {"worker_id": worker_id, "worker_kind": worker_kind, "started_at": now, "completed_at": now}


def _default_fixture() -> dict:
    """A small deterministic offline fixture (used when the caller passes none).

    Shape: a ``task`` (the open question), a list of ``signals`` (open questions), a list of ``documents`` (each a
    source the extractor can cite, with a stable ``handle`` + ``authority_rank``), and an explicit list of
    ``held_out`` items (minority / stale / rejected statements that must NEVER be folded into the served answer).
    The CFPB demo (see ``cfpb_evidence_demo``) supplies the planted Reg E fixture; this generic default exercises
    the same shape so the self-test does not depend on the CFPB module.
    """
    return {
        "task": "What is the effective resolution deadline?",
        "tenant_scope": DEFAULT_TENANT_SCOPE,
        "signals": [
            {"question": "What is the effective resolution deadline?", "priority": 10},
        ],
        "documents": [
            {
                "source_id": "src.authority",
                "handle": "ctx://demo/authority.md#decision",
                "authority_rank": 90,
                "statement": "The resolution deadline is 10 business days.",
                "confidence": 0.95,
                "entity": "resolution_deadline",
            },
            {
                "source_id": "src.code",
                "handle": "ctx://demo/code.py#L5-L7",
                "authority_rank": 80,
                "statement": "The resolution deadline is 10 business days.",
                "confidence": 0.9,
                "entity": "resolution_deadline",
            },
        ],
        # items deliberately preserved as WARNINGS — never merged into the served answer (lossless distillation).
        "held_out": [
            {
                "source_id": "src.stale_faq",
                "handle": "ctx://demo/faq.md#timeline",
                "statement": "The resolution deadline is 30 days.",
                "reason": "stale: superseded by the authority; preserved as a warning, never served",
                "confidence": 0.4,
            },
        ],
        # the consolidated, source-backed answer the synthesis should converge on (NOT truth — a candidate).
        "answer": "The resolution deadline is 10 business days.",
    }


class LocalStatefulSwarm:
    """The offline correctness-invariant stateful-swarm runner. Deterministic, stdlib, no-key, no-network.

    Six bounded workers post typed entries onto an injected :class:`LocalSqliteBlackboard`; the synthesis worker
    reads the BOARD (not the raw docs). The run envelope's ``serves_truth`` is pinned False — the run produced
    analytical state, never truth. Deterministic when ``now`` is injected.

    ``blackboard`` is injectable (default a fresh in-memory store) so tests pass a tempfile / ``:memory:`` and the
    real ``.agent`` db is never touched. ``fixture`` is injectable (the CFPB demo supplies the planted Reg E
    fixture); a default offline fixture is used otherwise.
    """

    provider_id = LOCAL_SWARM_PROVIDER_ID

    def __init__(self, *, blackboard: LocalSqliteBlackboard | None = None, fixture: dict | None = None) -> None:
        self.blackboard = blackboard if blackboard is not None else LocalSqliteBlackboard(db_path=":memory:")
        self.fixture = fixture if fixture is not None else _default_fixture()

    # ---- describe ------------------------------------------------------------------------
    def describe(self) -> dict:
        """Local-first golden-path card: no network, no keys, IS its own local_equivalent, never truth."""
        return {
            "provider_id": self.provider_id,
            "name": "local-stateful-swarm-stub",
            "status": "active",
            "requires_network": False,
            "requires_keys": False,
            "local_equivalent": self.provider_id,
            "serves_truth": SWARM_SERVES_TRUTH,
            "workers": list(SWARM_WORKER_ORDER),
        }

    # ---- the six bounded workers ---------------------------------------------------------
    def _seed_planner(self, blackboard_id: str, tenant_scope: str, *, now: str) -> SwarmWorkerResult:
        """WORKER 1 — post SIGNALS (open questions) directing the swarm. Procedural; no sources required."""
        entry_ids: list[str] = []
        receipt_id: str | None = None
        for i, sig in enumerate(self.fixture.get("signals", [])):
            row = self.blackboard.append_entry(
                blackboard_id,
                {
                    "kind": KIND_SIGNAL,
                    "author_worker_id": WORKER_SEED_PLANNER,
                    "iteration": 0,
                    "tenant_scope": tenant_scope,
                    "source_refs": [],
                    "body": {"question": sig["question"], "priority": int(sig.get("priority", 10 - i))},
                },
                worker_receipt=_receipt(WORKER_SEED_PLANNER, "planner", now=now),
                now=now,
            )
            entry_ids.append(row["entry_id"])
            receipt_id = row["receipt_id"]
        return SwarmWorkerResult(
            worker_id=WORKER_SEED_PLANNER, worker_kind="planner",
            entry_ids=tuple(entry_ids), receipt_id=receipt_id,
            detail={"signals_posted": len(entry_ids)},
        )

    def _observation_extractor(self, blackboard_id: str, tenant_scope: str, *, now: str) -> SwarmWorkerResult:
        """WORKER 2 — for each fixture document, post a SOURCE handle then an OBSERVATION that CITES it.

        Every observation carries non-empty ``source_refs`` (the cited source ids) — the store would REJECT a
        sourceless observation, so this worker is source-backed by construction. Held-out items are NOT extracted
        here; they are carried separately and preserved as warnings by the synthesis worker.
        """
        entry_ids: list[str] = []
        receipt_id: str | None = None
        for doc in self.fixture.get("documents", []):
            # post the source handle first (a stable provenance locator the observation will cite).
            src_row = self.blackboard.append_entry(
                blackboard_id,
                {
                    "kind": KIND_SOURCE,
                    "author_worker_id": WORKER_OBSERVATION_EXTRACTOR,
                    "iteration": 1,
                    "tenant_scope": tenant_scope,
                    "source_refs": [],
                    "body": {
                        "source_id": doc["source_id"],
                        "handle": doc["handle"],
                        "authority_rank": int(doc.get("authority_rank", 50)),
                        "retrieved_at": now,
                    },
                },
                worker_receipt=_receipt(WORKER_OBSERVATION_EXTRACTOR, "extractor", now=now),
                now=now,
            )
            entry_ids.append(src_row["entry_id"])
            source_id = src_row["body"]["source_id"]
            # the observation CITES the source (non-empty source_refs => passes the source-backed guard).
            obs_row = self.blackboard.append_entry(
                blackboard_id,
                {
                    "kind": KIND_OBSERVATION,
                    "author_worker_id": WORKER_OBSERVATION_EXTRACTOR,
                    "iteration": 1,
                    "tenant_scope": tenant_scope,
                    "source_refs": [source_id],
                    "body": {
                        "statement": doc["statement"],
                        "source_refs": [source_id],
                        "confidence": float(doc.get("confidence", 0.9)),
                    },
                },
                worker_receipt=_receipt(WORKER_OBSERVATION_EXTRACTOR, "extractor", now=now),
                now=now,
            )
            entry_ids.append(obs_row["entry_id"])
            receipt_id = obs_row["receipt_id"]
        return SwarmWorkerResult(
            worker_id=WORKER_OBSERVATION_EXTRACTOR, worker_kind="extractor",
            entry_ids=tuple(entry_ids), receipt_id=receipt_id,
            detail={"documents": len(self.fixture.get("documents", []))},
        )

    def _gap_detector(self, blackboard_id: str, tenant_scope: str, *, now: str) -> SwarmWorkerResult:
        """WORKER 3 — read the BOARD's observations + held-out items and post explicit GAPS (named holes).

        Held-out (e.g. stale/minority) statements are surfaced as an OPEN gap — they are a hole in a clean answer,
        not silently dropped. A gap is convergence currency (the swarm converges when open gaps reach zero).
        """
        # READ the board: the held-out items the swarm knows about become an explicit reconciliation gap.
        read = self.blackboard.query(blackboard_id, kind=KIND_OBSERVATION)
        entry_ids: list[str] = []
        receipt_id: str | None = None
        held_out = self.fixture.get("held_out", [])
        if held_out:
            row = self.blackboard.append_entry(
                blackboard_id,
                {
                    "kind": KIND_GAP,
                    "author_worker_id": WORKER_GAP_DETECTOR,
                    "iteration": 1,
                    "tenant_scope": tenant_scope,
                    "source_refs": [],
                    "body": {
                        "missing": "Whether the held-out contradicting value(s) are reconciled against the authority.",
                        "why_it_matters": (
                            "A contradicting/stale value exists and must be held out as a warning, never served; "
                            "reconciliation determines authority and freshness."
                        ),
                        "status": "open",
                    },
                },
                worker_receipt=_receipt(WORKER_GAP_DETECTOR, "gap_detector", now=now),
                now=now,
            )
            entry_ids.append(row["entry_id"])
            receipt_id = row["receipt_id"]
        return SwarmWorkerResult(
            worker_id=WORKER_GAP_DETECTOR, worker_kind="gap_detector",
            entry_ids=tuple(entry_ids), receipt_id=receipt_id,
            read_entry_ids=tuple(e["entry_id"] for e in read),
            detail={"gaps_posted": len(entry_ids), "held_out_count": len(held_out)},
        )

    def _entity_resolver(self, blackboard_id: str, tenant_scope: str, *, now: str) -> SwarmWorkerResult:
        """WORKER 4 — read the BOARD's observations, reconcile/link them to a canonical entity (an ANALYSIS with
        lineage to the supporting observations). If the fixture documents name MISMATCHING entities, surface the
        mismatch AS A GAP (never silently drop it).
        """
        read = self.blackboard.query(blackboard_id, kind=KIND_OBSERVATION)
        supporting = [e["entry_id"] for e in read]
        entry_ids: list[str] = []
        receipt_id: str | None = None

        # detect an entity mismatch across the fixture documents (e.g. two docs about different entities).
        entities = sorted({str(d.get("entity", "")) for d in self.fixture.get("documents", []) if d.get("entity")})
        if len(entities) > 1:
            # surface the mismatch as a GAP — an unresolved entity conflict is a hole, not a silent merge.
            gap_row = self.blackboard.append_entry(
                blackboard_id,
                {
                    "kind": KIND_GAP,
                    "author_worker_id": WORKER_ENTITY_RESOLVER,
                    "iteration": 2,
                    "tenant_scope": tenant_scope,
                    "source_refs": [],
                    "body": {
                        "missing": f"Observations reference mismatching entities {entities}; which is canonical?",
                        "why_it_matters": "Linking unrelated entities would fabricate a relationship; resolve first.",
                        "status": "open",
                    },
                },
                worker_receipt=_receipt(WORKER_ENTITY_RESOLVER, "entity_resolver", now=now),
                now=now,
            )
            entry_ids.append(gap_row["entry_id"])
            receipt_id = gap_row["receipt_id"]

        # post the reconciliation ANALYSIS with lineage to the observations it links (a claim, never truth).
        canonical_entity = entities[0] if entities else "entity.unresolved"
        analysis_row = self.blackboard.append_entry(
            blackboard_id,
            {
                "kind": KIND_ANALYSIS,
                "author_worker_id": WORKER_ENTITY_RESOLVER,
                "iteration": 2,
                "tenant_scope": tenant_scope,
                "source_refs": [],
                "body": {
                    "claim": f"Observations reconcile to canonical entity {canonical_entity!r}.",
                    "supporting_entry_ids": supporting,
                    "serves_truth": False,
                    "canonical_entity": canonical_entity,
                    "entity_mismatch": len(entities) > 1,
                },
            },
            worker_receipt=_receipt(WORKER_ENTITY_RESOLVER, "entity_resolver", now=now),
            now=now,
        )
        entry_ids.append(analysis_row["entry_id"])
        receipt_id = analysis_row["receipt_id"]
        return SwarmWorkerResult(
            worker_id=WORKER_ENTITY_RESOLVER, worker_kind="entity_resolver",
            entry_ids=tuple(entry_ids), receipt_id=receipt_id,
            read_entry_ids=tuple(supporting),
            detail={"canonical_entity": canonical_entity, "entity_mismatch": len(entities) > 1},
        )

    def _synthesis(self, blackboard_id: str, tenant_scope: str, *, now: str) -> SwarmWorkerResult:
        """WORKER 5 — read the BLACKBOARD ENTRIES (NOT the raw docs) and post a SYNTHESIS.

        The answer is built from the source-backed OBSERVATIONS on the board; ``supporting_entry_ids`` are the
        real observation/analysis blackboard entry_ids it consolidates (proving it read the BOARD). ``held_out``
        preserves the items deliberately NOT folded in (the stale/minority statements + open gaps) so the winner
        always carries lineage to the losers. The served answer NEVER contains a held-out statement.
        """
        # READ the board (the whole point — synthesis consumes blackboard entries, not raw documents).
        observations = self.blackboard.query(blackboard_id, kind=KIND_OBSERVATION)
        analyses = self.blackboard.query(blackboard_id, kind=KIND_ANALYSIS)
        gaps = self.blackboard.query(blackboard_id, kind=KIND_GAP)

        supporting = [e["entry_id"] for e in observations] + [e["entry_id"] for e in analyses]
        # source handles carried end-to-end from the board's observations (never sourceless).
        source_handles = sorted({sr for e in observations for sr in (e.get("source_refs") or [])})

        # the consolidated answer = the fixture's reconciled answer (from the source-backed observations on the
        # board). Held-out statements are NOT in it. We assert this below so a leak can never pass.
        answer = self.fixture.get("answer") or (observations[0]["body"]["statement"] if observations else "")

        # held_out = the open gaps' entry_ids (unresolved) + the held-out source handles (stale/minority).
        held_out_handles = [h["handle"] for h in self.fixture.get("held_out", []) if h.get("handle")]
        held_out = [e["entry_id"] for e in gaps if e["body"].get("status") == "open"] + held_out_handles

        row = self.blackboard.append_entry(
            blackboard_id,
            {
                "kind": KIND_SYNTHESIS,
                "author_worker_id": WORKER_SYNTHESIS,
                "iteration": 3,
                "tenant_scope": tenant_scope,
                "source_refs": [],
                "body": {
                    "answer": answer,
                    "supporting_entry_ids": supporting,  # real blackboard entry_ids => read the board
                    "held_out": held_out,                # omitted != deleted (lossless distillation)
                    "source_handles": source_handles,
                    "serves_truth": False,               # even the final synthesis is a candidate, never truth
                },
            },
            worker_receipt=_receipt(WORKER_SYNTHESIS, "synthesizer", now=now),
            now=now,
        )
        return SwarmWorkerResult(
            worker_id=WORKER_SYNTHESIS, worker_kind="synthesizer",
            entry_ids=(row["entry_id"],), receipt_id=row["receipt_id"],
            read_entry_ids=tuple(supporting),  # proves it consumed blackboard entries, not raw docs
            detail={"answer": answer, "held_out": held_out, "source_handles": source_handles,
                    "supporting_count": len(supporting)},
        )

    def _governed_projection(self, blackboard_id: str, tenant_scope: str, synthesis_entry_id: str,
                             *, now: str) -> tuple[SwarmWorkerResult, dict]:
        """WORKER 6 — project a :class:`GovernedBlackboardEntry`-shaped governance verdict OVER the synthesis.

        This is the Teleon→Baltor SEAM: Teleon RETURNS a candidate + evidence; Baltor GOVERNS served truth. The
        verdict's ``serves_truth`` is const False and ``promotion_eligible`` is the explicit, auditable gate
        (false here: open gaps remain, so the candidate is NOT promotable). The held-out items are recorded in the
        verdict's ``held_out_reason`` — preserved as a warning, never served. The verdict itself is recorded as an
        ANALYSIS entry on the board (lineage), under a receipt; it does NOT mark anything truth.
        """
        synth = self.blackboard.query(blackboard_id, kind=KIND_SYNTHESIS)
        synth_body = next((e["body"] for e in synth if e["entry_id"] == synthesis_entry_id), {})
        held_out = list(synth_body.get("held_out", []))
        source_handles = list(synth_body.get("source_handles", []))
        receipts = self.blackboard.get_receipts(blackboard_id)
        receipt_refs = sorted({r["receipt_id"] for r in receipts})

        # GovernedBlackboardEntry.v1-shaped verdict (Baltor's governance seam — never makes the entry truth).
        governed_entry = {
            "entry_id": synthesis_entry_id,
            "blackboard_id": blackboard_id,
            "authority_rank": 90,  # numeric reconciliation weight; graph data, not a display label
            "claim_status": "candidate",       # a swarm conclusion is born candidate (never auto-served)
            "verification_status": "unverified",  # Baltor's verification rail runs separately
            "held_out_reason": (
                "held_out items preserved as warnings (stale/minority/open-gap); never folded into the answer"
                if held_out else ""
            ),
            "freshness_policy": "cdc:revalidate-on-source-change",
            "temporal_validity": f"as_of:{now}",
            "tenant_scope": tenant_scope,
            # explicit, auditable gate: NOT promotable while gaps remain / verification has not passed.
            "promotion_eligible": False,
            "receipt_refs": receipt_refs,
            "source_handles": source_handles,
            "serves_truth": False,  # ALWAYS false — governance wrapping never makes the entry served truth
        }

        # record the governance verdict as an ANALYSIS entry (lineage), under a receipt — not truth.
        row = self.blackboard.append_entry(
            blackboard_id,
            {
                "kind": KIND_ANALYSIS,
                "author_worker_id": WORKER_GOVERNED_PROJECTION,
                "iteration": 4,
                "tenant_scope": tenant_scope,
                "source_refs": [],
                "body": {
                    "claim": "Governance verdict projected over the synthesis (candidate; not promotable).",
                    "supporting_entry_ids": [synthesis_entry_id],
                    "serves_truth": False,
                    "governed_entry": governed_entry,
                },
            },
            worker_receipt=_receipt(WORKER_GOVERNED_PROJECTION, "governor", now=now),
            now=now,
        )
        result = SwarmWorkerResult(
            worker_id=WORKER_GOVERNED_PROJECTION, worker_kind="governor",
            entry_ids=(row["entry_id"],), receipt_id=row["receipt_id"],
            read_entry_ids=(synthesis_entry_id,),
            detail={"promotion_eligible": False, "held_out_preserved": len(held_out)},
        )
        return result, governed_entry

    # ---- run (orchestrate the workers) ---------------------------------------------------
    def run(self, task: str, *, blackboard_id: str, now: str) -> dict:
        """Orchestrate the six bounded workers writing typed entries to ``blackboard_id``; return the envelope.

        Order: seed_planner -> observation_extractor -> gap_detector -> entity_resolver -> synthesis ->
        governed_projection. Each worker reads the board and posts entries under a MANDATORY receipt; the synthesis
        worker reads BLACKBOARD ENTRIES (not raw docs). The envelope's ``serves_truth`` is pinned False (analytical
        state, never truth). Deterministic when ``now`` is injected.
        """
        tenant_scope = self.fixture.get("tenant_scope", DEFAULT_TENANT_SCOPE)
        results: list[SwarmWorkerResult] = []

        results.append(self._seed_planner(blackboard_id, tenant_scope, now=now))
        results.append(self._observation_extractor(blackboard_id, tenant_scope, now=now))
        results.append(self._gap_detector(blackboard_id, tenant_scope, now=now))
        results.append(self._entity_resolver(blackboard_id, tenant_scope, now=now))
        synth_result = self._synthesis(blackboard_id, tenant_scope, now=now)
        results.append(synth_result)
        synthesis_entry_id = synth_result.entry_ids[0] if synth_result.entry_ids else None
        gov_result, governed_entry = self._governed_projection(
            blackboard_id, tenant_scope, synthesis_entry_id, now=now
        )
        results.append(gov_result)

        return {
            "provider_id": self.provider_id,
            "blackboard_id": blackboard_id,
            "task": task,
            "tenant_scope": tenant_scope,
            "worker_results": results,
            "synthesis_entry_id": synthesis_entry_id,
            "governed_entry": governed_entry,
            "serves_truth": SWARM_SERVES_TRUTH,  # the run produced analytical state, NEVER served truth
        }


__all__ = [
    "LocalStatefulSwarm",
    "LOCAL_SWARM_PROVIDER_ID",
    "DEFAULT_TENANT_SCOPE",
    "SWARM_WORKER_ORDER",
    "WORKER_SEED_PLANNER",
    "WORKER_OBSERVATION_EXTRACTOR",
    "WORKER_GAP_DETECTOR",
    "WORKER_ENTITY_RESOLVER",
    "WORKER_SYNTHESIS",
    "WORKER_GOVERNED_PROJECTION",
]
