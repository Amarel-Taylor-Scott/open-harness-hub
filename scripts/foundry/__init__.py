"""The Evidence-Driven Component Factory ("foundry").

A modular, no-filler pipeline that mints reusable AI-pipeline components ONLY
from evidence: a measured capability gap, a real licensed source, and a measured
lift over a bare model. See `docs/architecture/evidence-driven-component-factory.md`.

Eight stages, each a `Stage` over a shared `Candidate` (see `contracts`):

    0 gaps        — where does the bare model measurably fail?
    1 sources     — search for the licensed source that fixes it
    2 construction— agent + tools mine the source into typed components
    3 standardize — canonical body, schema-valid, ID + content/version hash
    4 novelty     — SimHash + LSH + source-url dedup
    5 measure     — bare vs pipeline on held-out tasks -> measured delta
    6 gate        — admit iff delta>0 AND durable AND sourced AND novel
    7 stage_load  — row families + embeddings + JSONL + partitioned load

The orchestrator (`pipeline`) threads a `Candidate` batch through the stages,
partitioned for a worker fleet, and reports a funnel ledger — never
"generated", always "promoted".
"""
from __future__ import annotations

__all__ = ["contracts", "novelty"]
