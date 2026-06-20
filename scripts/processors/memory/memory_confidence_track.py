#!/usr/bin/env python3
"""Backs `processor/memory-confidence-track` (process_kind ``memory.belief``).

Hindsight-style **belief tracking**: every claim in governed memory carries a
confidence that moves as evidence arrives — and fact is structurally
separated from opinion. Belief is a log-odds accumulator: each evidence item
contributes its source-kind weight, positive when it supports, negative when
it contradicts, and the sigmoid of the total is the belief.

Two laws are wired into the weights (both tested):

  * **LLM output is never truth** — ``model_interpretation`` and ``opinion``
    carry the smallest weights, AND a claim supported ONLY by them is capped
    at ``OPINION_BELIEF_CEILING``, strictly below the SUPPORTED threshold: no
    pile of opinions can make a fact.
  * **Lossless** — every evidence item is echoed in ``evidence_log`` with the
    weight applied to it; contested evidence is preserved, never resolved by
    deletion.

Runtime contract (matches the manifest): ``process_kind = memory.belief``;
**deterministic** / **idempotent** (same claim + evidence → byte-identical
belief); **side_effects = write** — but ONLY via the explicitly injected
``ledger`` dict (appends under the claim id; reported, never implicit);
**on_error = raise** (unknown source kinds are an error, not a guess).

Public API:
    from scripts.processors.memory.memory_confidence_track import run
    out = run(claim={"text": "Reg E requires provisional credit in 10 business days"},
              evidence=[{"source_kind": "source_of_law", "stance": "supports",
                         "source_id": "12 CFR 1005.11"}])
    # -> {"belief": {"belief": 0.88, "state": "SUPPORTED", ...}}

CLI / self-test:
    python3 scripts/processors/memory/memory_confidence_track.py
    python3 -m scripts.processors.memory.memory_confidence_track
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Log-odds contribution per evidence item, by source kind. The ordering IS
#: the authority model: law > primary document > gate-verified fact >
#: secondary report > model interpretation > bare opinion. Model/opinion
#: weights are small BY LAW (LLM output never truth).
EVIDENCE_WEIGHTS: dict[str, float] = {
    "source_of_law": 2.0,
    "primary_document": 1.5,
    "verified_fact": 1.2,
    "secondary_report": 0.6,
    "model_interpretation": 0.3,
    "opinion": 0.15,
}

#: Evidence kinds that can never, alone, establish a fact.
SOFT_KINDS = frozenset({"model_interpretation", "opinion"})

#: Prior log-odds for a fresh claim: 0.0 — belief 0.5, maximally uncertain.
PRIOR_LOG_ODDS = 0.0

#: State thresholds on the belief (sigmoid) scale.
SUPPORTED_THRESHOLD = 0.8
REFUTED_THRESHOLD = 0.2

#: Ceiling applied when ALL evidence is soft (opinion/model): strictly below
#: SUPPORTED_THRESHOLD so opinions alone can never promote.
OPINION_BELIEF_CEILING = 0.65

#: With both stances present and |net log-odds| inside this band, the claim
#: is CONTESTED — close calls with live disagreement must read as disputed,
#: not weakly-supported.
CONTESTED_BAND = 1.0

#: State names (single definition; tests and dashboards read these).
STATE_SUPPORTED = "SUPPORTED"
STATE_REFUTED = "REFUTED"
STATE_CONTESTED = "CONTESTED"
STATE_UNCERTAIN = "UNCERTAIN"

#: Belief rounding (decimal places) for stable envelopes.
BELIEF_DECIMALS = 6

#: Stances (single definition).
STANCE_SUPPORTS = "supports"
STANCE_CONTRADICTS = "contradicts"

#: Hash algorithm + prefix for content-addressed claim ids.
HASH_ALGORITHM = "sha256"
CLAIM_ID_PREFIX = "claim:"
CLAIM_ID_HEX_LEN = 24


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def claim_id_for(claim: dict[str, Any]) -> str:
    if "id" in claim:
        return str(claim["id"])
    digest = hashlib.new(HASH_ALGORITHM,
                         claim["text"].strip().lower().encode("utf-8")).hexdigest()
    return CLAIM_ID_PREFIX + digest[:CLAIM_ID_HEX_LEN]


def run(
    *,
    claim: dict[str, Any],
    evidence: list[dict[str, Any]],
    ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fold ``evidence`` into a belief about ``claim``; append to ``ledger`` if given.

    Returns ``{"belief": {...}}`` per the manifest's single output.
    """
    if not isinstance(claim, dict) or not (claim.get("text") or claim.get("id")):
        raise TypeError("claim must be a dict with text (or a pre-minted id)")
    if not isinstance(evidence, list):
        raise TypeError(f"evidence must be a list of dicts, got {type(evidence).__name__}")

    log_odds = PRIOR_LOG_ODDS
    supporting = contradicting = 0
    evidence_log: list[dict[str, Any]] = []
    all_soft = True
    for idx, ev in enumerate(evidence):
        if not isinstance(ev, dict):
            raise TypeError(f"evidence[{idx}] must be a dict")
        kind = ev.get("source_kind")
        if kind not in EVIDENCE_WEIGHTS:
            raise ValueError(
                f"evidence[{idx}] has unknown source_kind {kind!r}; "
                f"known: {sorted(EVIDENCE_WEIGHTS)}")
        stance = ev.get("stance")
        if stance not in (STANCE_SUPPORTS, STANCE_CONTRADICTS):
            raise ValueError(f"evidence[{idx}] stance must be "
                             f"{STANCE_SUPPORTS!r} or {STANCE_CONTRADICTS!r}, got {stance!r}")
        weight = EVIDENCE_WEIGHTS[kind]
        signed = weight if stance == STANCE_SUPPORTS else -weight
        log_odds += signed
        if stance == STANCE_SUPPORTS:
            supporting += 1
        else:
            contradicting += 1
        if kind not in SOFT_KINDS:
            all_soft = False
        # Lossless: every item echoed with the weight applied to it.
        evidence_log.append({**ev, "applied_log_odds": signed})

    belief = _sigmoid(log_odds)
    capped = False
    if evidence and all_soft and belief > OPINION_BELIEF_CEILING:
        belief = OPINION_BELIEF_CEILING  # opinions alone never make a fact
        capped = True

    if supporting >= 1 and contradicting >= 1 and abs(log_odds) < CONTESTED_BAND:
        state = STATE_CONTESTED
    elif belief >= SUPPORTED_THRESHOLD:
        state = STATE_SUPPORTED
    elif belief <= REFUTED_THRESHOLD:
        state = STATE_REFUTED
    else:
        state = STATE_UNCERTAIN

    cid = claim_id_for(claim)
    result = {
        "claim_id": cid,
        "belief": round(belief, BELIEF_DECIMALS),
        "state": state,
        "supporting": supporting,
        "contradicting": contradicting,
        "evidence_log": evidence_log,
        "soft_capped": capped,
        "is_fact_eligible": state == STATE_SUPPORTED,
        "serves_truth": False,
    }
    ledger_appended = False
    if ledger is not None:
        if not isinstance(ledger, dict):
            raise TypeError(f"ledger must be a dict or None, got {type(ledger).__name__}")
        ledger.setdefault(cid, {"history": []})["history"].append(result)
        ledger_appended = True
    return {"belief": {**result, "ledger_appended": ledger_appended}}


def _selftest() -> None:
    claim = {"text": "Reg E requires provisional credit within 10 business days"}

    # Two strong agreeing sources → SUPPORTED and fact-eligible.
    strong = run(claim=claim, evidence=[
        {"source_kind": "source_of_law", "stance": "supports", "source_id": "12 CFR 1005.11"},
        {"source_kind": "primary_document", "stance": "supports", "source_id": "cfpb-faq-30"},
    ])["belief"]
    assert strong["state"] == STATE_SUPPORTED and strong["is_fact_eligible"] is True
    assert strong["belief"] >= SUPPORTED_THRESHOLD and strong["supporting"] == 2

    # Similar-weight support vs contradiction → CONTESTED, not weakly supported.
    contested = run(claim=claim, evidence=[
        {"source_kind": "primary_document", "stance": "supports", "source_id": "doc-a"},
        {"source_kind": "verified_fact", "stance": "contradicts", "source_id": "fact-b"},
    ])["belief"]
    assert contested["state"] == STATE_CONTESTED and contested["is_fact_eligible"] is False

    # Strong contradiction → REFUTED.
    refuted = run(claim=claim, evidence=[
        {"source_kind": "source_of_law", "stance": "contradicts", "source_id": "12 CFR 1005.11"},
    ])["belief"]
    assert refuted["state"] == STATE_REFUTED and refuted["belief"] <= REFUTED_THRESHOLD

    # TEN unanimous opinions still cap below SUPPORTED — opinions never promote.
    opinions = [{"source_kind": "opinion", "stance": "supports", "source_id": f"op-{i}"}
                for i in range(10)]
    soft = run(claim=claim, evidence=opinions)["belief"]
    assert soft["soft_capped"] is True and soft["belief"] == OPINION_BELIEF_CEILING
    assert soft["state"] != STATE_SUPPORTED and soft["is_fact_eligible"] is False
    # Model interpretations are soft too.
    model_only = run(claim=claim, evidence=[
        {"source_kind": "model_interpretation", "stance": "supports", "source_id": "llm-1"}
        for _ in range(8)])["belief"]
    assert model_only["state"] != STATE_SUPPORTED
    # One hard source lifts the cap.
    mixed = run(claim=claim, evidence=opinions + [
        {"source_kind": "source_of_law", "stance": "supports", "source_id": "law-1"}])["belief"]
    assert mixed["soft_capped"] is False and mixed["state"] == STATE_SUPPORTED

    # Lossless: every evidence item echoed with its applied weight.
    assert len(soft["evidence_log"]) == 10
    assert all(e["applied_log_odds"] == EVIDENCE_WEIGHTS["opinion"] for e in soft["evidence_log"])
    assert len(contested["evidence_log"]) == 2

    # No evidence → maximally uncertain, honest.
    fresh = run(claim=claim, evidence=[])["belief"]
    assert fresh["state"] == STATE_UNCERTAIN and fresh["belief"] == 0.5

    # Ledger append happens only via the injected dict and is reported.
    ledger: dict[str, Any] = {}
    first = run(claim=claim, evidence=opinions, ledger=ledger)["belief"]
    assert first["ledger_appended"] is True
    assert len(ledger[first["claim_id"]]["history"]) == 1
    run(claim=claim, evidence=opinions + [{"source_kind": "secondary_report",
                                           "stance": "supports", "source_id": "s-1"}],
        ledger=ledger)
    assert len(ledger[first["claim_id"]]["history"]) == 2  # history grows, never replaced

    # Derived-content honesty + deterministic byte-identical repeats.
    assert strong["serves_truth"] is False
    a = json.dumps(run(claim=claim, evidence=opinions), sort_keys=True)
    b = json.dumps(run(claim=claim, evidence=opinions), sort_keys=True)
    assert a == b

    # on_error=raise: unknown kinds and bad stances are errors, never guesses.
    raised = False
    try:
        run(claim=claim, evidence=[{"source_kind": "blog_vibes", "stance": "supports"}])
    except ValueError:
        raised = True
    assert raised, "unknown source_kind must raise ValueError"
    raised = False
    try:
        run(claim=claim, evidence=[{"source_kind": "opinion", "stance": "maybe"}])
    except ValueError:
        raised = True
    assert raised, "bad stance must raise ValueError"

    print(
        "PASS — memory_confidence_track: log-odds belief with authority-ordered "
        "weights, SUPPORTED/REFUTED/CONTESTED/UNCERTAIN states, soft-evidence "
        f"ceiling {OPINION_BELIEF_CEILING} (10 opinions never promote, one law "
        "does), lossless evidence_log, append-only ledger, serves_truth pinned "
        "False verified"
    )


if __name__ == "__main__":
    _selftest()
