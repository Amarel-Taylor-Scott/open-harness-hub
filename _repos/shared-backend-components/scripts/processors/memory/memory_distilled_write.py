#!/usr/bin/env python3
"""Backs `processor/memory-distilled-write` (process_kind ``memory.write_kb``).

Mem0-style **selective extraction**: distill a conversation into the durable
facts it taught us — identities, preferences, stable settings — and write
those to the memory store instead of hoarding raw history. Extraction is
deterministic (sentence-pattern rules, no model), so the same conversation
always yields the same facts with the same content-addressed ids; the
manifest marks the process_kind non-deterministic because deployments may
swap in an LLM extractor behind the same contract, and this implementation
is strictly stricter.

The LOSSLESS LAW (_repos/shared-backend-components/docs/codex/lossless-distillation.md) shapes every field:

  * every fact carries LINEAGE — the verbatim source ``quote``, ``turn_index``
    and ``role`` it came from; distillation never replaces raw.
  * non-durable sentences (questions, greetings, deictic "right now" chatter)
    are HELD OUT with a reason — returned, never silently dropped.
  * a within-run duplicate folds into the kept fact's ``also_seen`` list —
    the duplicate's lineage survives the dedupe.
  * facts are CANDIDATES: ``serves_truth`` is pinned False; the verification
    gate, not the extractor, promotes.

Runtime contract (matches the manifest): ``process_kind = memory.write_kb``;
**idempotent** (same turns → same fact_ids; a keyed store absorbs replays);
**side_effects = write** — but ONLY via the explicitly injected store, and
the write count is reported; **on_error = raise**.

Public API:
    from scripts.processors.memory.memory_distilled_write import run
    out = run(turns=[{"role": "user", "content": "My favorite database is Postgres."}],
              store=kb, now=t)
    # -> {"facts": {"extracted": [...], "held_out": [...], "written": 1}}

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/processors/memory/memory_distilled_write.py
    python3 -m scripts.processors.memory.memory_distilled_write
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Durable-fact patterns, tried in order; first match wins and names the
#: fact kind. Each is anchored to a whole sentence (after splitting) so one
#: sentence yields at most one fact.
#:   identity   — "my X is Y" / "I am Y" / "I'm Y"
#:   preference — "I prefer/like/love/hate/always/never ..."
#:   setting    — "we use X for Y" / "our X is Y" / "X is hosted/deployed on Y"
FACT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("identity", re.compile(r"^my\s+.{2,80}?\s+is\s+.{1,120}$", re.IGNORECASE)),
    ("identity", re.compile(r"^i\s*(?:am|'m)\s+(?!sure|not\s+sure|asking|wondering).{2,120}$", re.IGNORECASE)),
    ("preference", re.compile(r"^i\s+(?:prefer|like|love|hate|always|never)\s+.{2,120}$", re.IGNORECASE)),
    ("setting", re.compile(r"^(?:we|our team)\s+(?:use|run|deploy(?: on| to)?)\s+.{2,120}$", re.IGNORECASE)),
    ("setting", re.compile(r"^our\s+.{2,80}?\s+is\s+.{1,120}$", re.IGNORECASE)),
]

#: Sentences excluded from distillation, each with the reason recorded in the
#: held_out entry. Order matters: the first matching reason is reported.
EPHEMERA_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("question", re.compile(r"\?\s*$")),
    ("greeting", re.compile(r"^(?:hi|hello|hey|thanks|thank you|good (?:morning|afternoon|evening))\b", re.IGNORECASE)),
    ("deictic/ephemeral", re.compile(r"\b(?:right now|at the moment|currently|today|this minute)\b", re.IGNORECASE)),
]

#: Catch-all held-out reason for sentences matching no durable pattern.
HELD_OUT_NO_PATTERN = "no durable-fact pattern matched"

#: Sentence boundary: ., !, ? followed by whitespace. A period INSIDE a token
#: ("Fly.io", "v1.2") is not followed by whitespace, so it never splits.
#: Deterministic and deliberately simple — abbreviation handling is not worth
#: nondeterminism.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

#: Hash algorithm + prefix for content-addressed fact ids (stable across runs
#: so replays dedupe instead of duplicating — the ID discipline in CLAUDE.md).
HASH_ALGORITHM = "sha256"
FACT_ID_PREFIX = "fact:"
#: Hex chars kept from the digest — enough to never collide at memory-store
#: scale while staying readable in logs.
FACT_ID_HEX_LEN = 24


def _normalize(text: str) -> str:
    """Case/whitespace-insensitive normal form used for ids and dedupe."""
    return re.sub(r"\s+", " ", text.strip().rstrip(".!").lower())


def fact_id(text: str, tenant_id: str | None) -> str:
    payload = json.dumps({"fact": _normalize(text), "tenant_id": tenant_id},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.new(HASH_ALGORITHM, payload.encode("utf-8")).hexdigest()
    return FACT_ID_PREFIX + digest[:FACT_ID_HEX_LEN]


def _sentences(content: str) -> list[str]:
    out: list[str] = []
    for line in content.splitlines():
        out.extend(p.strip() for p in _SENTENCE_SPLIT_RE.split(line) if p.strip())
    return out


def run(
    *,
    turns: list[dict[str, Any]],
    store: dict[str, dict[str, Any]] | list[dict[str, Any]] | None = None,
    now: float = 0.0,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Distill ``turns`` into durable fact candidates; write them ONLY via ``store``.

    Returns ``{"facts": {...}}`` per the manifest's single output. With
    ``store=None`` the call is a pure preview (``written: 0``) and the result
    is still complete.
    """
    if not isinstance(turns, list):
        raise TypeError(f"turns must be a list of role/content dicts, got {type(turns).__name__}")
    extracted: list[dict[str, Any]] = []
    by_norm: dict[str, dict[str, Any]] = {}
    held_out: list[dict[str, Any]] = []
    for idx, turn in enumerate(turns):
        if not isinstance(turn, dict) or "content" not in turn:
            raise ValueError(f"turn {idx} must be a dict with content")
        role = turn.get("role", "user")
        for sentence in _sentences(str(turn["content"])):
            reason = next((r for r, pat in EPHEMERA_RULES if pat.search(sentence)), None)
            if reason is not None:
                held_out.append({"quote": sentence, "turn_index": idx, "reason": reason})
                continue
            kind = next((k for k, pat in FACT_PATTERNS if pat.match(sentence)), None)
            if kind is None:
                held_out.append({"quote": sentence, "turn_index": idx,
                                 "reason": HELD_OUT_NO_PATTERN})
                continue
            norm = _normalize(sentence)
            if norm in by_norm:
                # Lossless dedupe: the duplicate's lineage folds into the kept fact.
                by_norm[norm]["also_seen"].append({"quote": sentence, "turn_index": idx, "role": role})
                continue
            fact = {
                "fact_id": fact_id(sentence, tenant_id),
                "text": norm,
                "quote": sentence,
                "turn_index": idx,
                "role": role,
                "kind": kind,
                "tenant_id": tenant_id,
                "extracted_at": float(now),
                "also_seen": [],
                "serves_truth": False,
            }
            by_norm[norm] = fact
            extracted.append(fact)

    written = 0
    if store is not None:
        if isinstance(store, dict):
            for fact in extracted:
                if fact["fact_id"] not in store:  # replay-safe: keyed store absorbs reruns
                    store[fact["fact_id"]] = fact
                    written += 1
        elif isinstance(store, list):
            store.extend(extracted)
            written = len(extracted)
        else:
            raise TypeError(f"store must be dict, list or None, got {type(store).__name__}")

    return {"facts": {
        "extracted": extracted,
        "held_out": held_out,
        "written": written,
        "considered_turns": len(turns),
    }}


def _selftest() -> None:
    turns = [
        {"role": "user", "content": "Hey there. My favorite database is Postgres."},
        {"role": "user", "content": "What should we use for hosting?"},
        {"role": "assistant", "content": "We use Fly.io for hosting. The deploy is green right now."},
        {"role": "user", "content": "I prefer dark roast coffee. My favorite database is Postgres!"},
    ]
    snapshot = json.dumps(turns, sort_keys=True)

    out = run(turns=turns, now=1_000.0)["facts"]
    by_text = {f["text"]: f for f in out["extracted"]}

    # Durable facts extracted with kind + full lineage.
    fav = by_text["my favorite database is postgres"]
    assert fav["kind"] == "identity" and fav["turn_index"] == 0
    assert fav["quote"] == "My favorite database is Postgres."
    host = by_text["we use fly.io for hosting"]
    assert host["kind"] == "setting" and host["role"] == "assistant"
    pref = by_text["i prefer dark roast coffee"]
    assert pref["kind"] == "preference"

    # Ephemera held out WITH reasons (lossless — nothing silently dropped).
    reasons = {h["quote"]: h["reason"] for h in out["held_out"]}
    assert reasons["What should we use for hosting?"] == "question"
    assert reasons["Hey there."] == "greeting"
    assert reasons["The deploy is green right now."] == "deictic/ephemeral"

    # Within-run dedupe keeps ONE fact and folds the repeat's lineage in.
    assert len([f for f in out["extracted"] if f["text"] == "my favorite database is postgres"]) == 1
    assert fav["also_seen"] == [{"quote": "My favorite database is Postgres!",
                                 "turn_index": 3, "role": "user"}]

    # Candidates, never truth.
    assert all(f["serves_truth"] is False for f in out["extracted"])

    # Idempotent ids: a second run mints identical fact_ids; a keyed store
    # absorbs the replay with zero new writes.
    again = run(turns=turns, now=2_000.0)["facts"]
    assert [f["fact_id"] for f in again["extracted"]] == [f["fact_id"] for f in out["extracted"]]
    kb: dict[str, dict[str, Any]] = {}
    w1 = run(turns=turns, store=kb, now=1_000.0)["facts"]["written"]
    w2 = run(turns=turns, store=kb, now=2_000.0)["facts"]["written"]
    assert w1 == 3 and w2 == 0 and len(kb) == 3

    # Tenant scoping changes identity (acme's fact id ≠ global fact id).
    t = run(turns=turns, tenant_id="acme")["facts"]["extracted"][0]
    assert t["fact_id"] != fav["fact_id"] and t["tenant_id"] == "acme"

    # Preview mode (store=None) writes nothing; raw turns never mutated.
    assert out["written"] == 0
    assert json.dumps(turns, sort_keys=True) == snapshot

    # Deterministic byte-identical repeat.
    a = json.dumps(run(turns=turns, now=1_000.0), sort_keys=True)
    b = json.dumps(run(turns=turns, now=1_000.0), sort_keys=True)
    assert a == b

    # on_error=raise.
    raised = False
    try:
        run(turns="not a list")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-list turns must raise TypeError"
    raised = False
    try:
        run(turns=[{"role": "user"}])
    except ValueError:
        raised = True
    assert raised, "turn without content must raise ValueError"

    print(
        "PASS — memory_distilled_write: pattern-based selective extraction "
        "(identity/preference/setting) with verbatim-quote lineage, reasons on "
        "every held-out sentence, lossless also_seen dedupe, content-addressed "
        "replay-stable fact ids, store-only writes, serves_truth pinned False "
        "verified"
    )


if __name__ == "__main__":
    _selftest()
