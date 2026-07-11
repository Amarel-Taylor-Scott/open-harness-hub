#!/usr/bin/env python3
"""Backs `processor/context-placer-edge` (process_kind ``assemble.context_placement``).

Edge placement (taxonomy step R6): put the MOST relevant evidence at the
edges — first AND last — of the context block, weaker evidence in the
middle, task instructions after the evidence. This directly counters the
"lost in the middle" attention drop, and every block is source-tagged and
delimited so the model can cite per claim.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs chunks({"id","text","score"}), query, instructions → assembled_prompt.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/retrieval/context_placer_edge.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Delimiters for evidence blocks — stable, greppable, and unlikely to occur
#: in source text. The id inside the tag is what per-claim citations cite.
BLOCK_OPEN = "<evidence id={id} rank={rank}>"
BLOCK_CLOSE = "</evidence>"

#: Section headers (single definition; tests read them).
EVIDENCE_HEADER = "## Evidence (cite by id)"
QUESTION_HEADER = "## Question"
INSTRUCTIONS_HEADER = "## Instructions"


def _interleave_edges(ordered: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Best-first list → edge placement: ranks 1,3,5,… forward; 2,4,6,… reversed
    at the tail, so #1 opens the block and #2 closes it."""
    front = ordered[0::2]
    back = ordered[1::2]
    return front + back[::-1]


def run(*, chunks: list[dict[str, Any]], query: str,
        instructions: str = "Answer from the evidence blocks only; cite ids; "
                            "if the evidence does not support an answer, say so.") -> dict[str, Any]:
    """Assemble the evidence + question + instructions prompt with edge placement."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(instructions, str):
        raise TypeError("instructions must be str")
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list of id/text dicts")
    rows: list[dict[str, Any]] = []
    for i, c in enumerate(chunks):
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            raise ValueError(f"chunks[{i}] needs id and text")
        rows.append({"id": str(c["id"]), "text": str(c["text"]),
                     "score": float(c.get("score", 0.0))})
    rows.sort(key=lambda r: (-r["score"], r["id"]))  # best-first, deterministic
    placed = _interleave_edges(rows)

    blocks = []
    placement = []
    for pos, r in enumerate(placed):
        rank = rows.index(r) + 1
        blocks.append(BLOCK_OPEN.format(id=r["id"], rank=rank) + "\n" + r["text"] + "\n" + BLOCK_CLOSE)
        placement.append({"position": pos, "id": r["id"], "rank": rank})
    prompt = "\n".join([
        EVIDENCE_HEADER, *blocks, "",
        QUESTION_HEADER, query, "",
        INSTRUCTIONS_HEADER, instructions,
    ])
    return {"assembled_prompt": {"prompt": prompt, "placement": placement,
                                 "strategy": "edge_first_and_last (lost-in-the-middle mitigation)",
                                 "instructions_last": True}}


def _selftest() -> None:
    chunks = [
        {"id": "best", "text": "the cap is 8% per the statute", "score": 0.95},
        {"id": "second", "text": "the cap was amended in 2024", "score": 0.90},
        {"id": "third", "text": "context about lending generally", "score": 0.60},
        {"id": "fourth", "text": "weak background detail", "score": 0.30},
    ]
    out = run(chunks=chunks, query="what is the usury cap?")["assembled_prompt"]
    order = [p["id"] for p in out["placement"]]
    # Edges hold the strongest evidence: #1 first, #2 LAST; weakest mid-block.
    assert order[0] == "best" and order[-1] == "second"
    assert "fourth" in order[1:-1]
    # Instructions come after the evidence and the question.
    p = out["prompt"]
    assert p.index(EVIDENCE_HEADER) < p.index(QUESTION_HEADER) < p.index(INSTRUCTIONS_HEADER)
    assert out["instructions_last"] is True
    # Source-tagged delimited blocks with rank lineage.
    assert "<evidence id=best rank=1>" in p and "</evidence>" in p
    assert "<evidence id=second rank=2>" in p
    # Default instructions carry the cite-or-abstain contract.
    assert "cite ids" in p and "say so" in p
    # Deterministic; inputs untouched; honest empty assembly.
    snap = json.dumps(chunks, sort_keys=True)
    assert json.dumps(run(chunks=chunks, query="q"), sort_keys=True) == \
           json.dumps(run(chunks=chunks, query="q"), sort_keys=True)
    assert json.dumps(chunks, sort_keys=True) == snap
    empty = run(chunks=[], query="q")["assembled_prompt"]
    assert empty["placement"] == [] and QUESTION_HEADER in empty["prompt"]
    # on_error=raise.
    raised = False
    try:
        run(chunks=[{"text": "no id"}], query="q")
    except ValueError:
        raised = True
    assert raised
    print("PASS — context_placer_edge: best evidence at BOTH edges (#1 opens, #2 closes), "
          "weak in the middle, source-tagged delimited blocks, instructions last, "
          "deterministic verified")


if __name__ == "__main__":
    _selftest()
