#!/usr/bin/env python3
"""Backs `processor/memory-reflect` (process_kind ``memory.reflect``).

Hindsight-style ``reflect()``: take the memories recalled for a turn and
produce a **coherent synthesis** for the prompt — themed paragraphs, facts
separated from opinions, conflicts surfaced — instead of a ranked list of
fragments. The synthesis is built deterministically (theme grouping by
shared salient terms, stable ordering, template prose), so the same memories
always reflect to the same text; the manifest marks the process_kind
non-deterministic because deployments may swap in an LLM synthesizer behind
the same contract, and this implementation is strictly stricter.

Honesty rules carried from the repo's laws (tested):

  * **serves_truth is pinned False** — a reflection is DERIVED content; it
    feeds a prompt, it never becomes a verified fact without the gate.
  * **Lossless** — every input memory id is accounted for: used ids appear in
    ``supporting_memory_ids``, off-query ids land in ``held_out`` with the
    reason. Nothing is silently dropped.
  * **Fact ≠ opinion** — ``kind: opinion/preference`` memories synthesize
    into the opinion sentence, never the "Known:" sentence.
  * **Conflicts surface** — two memories that disagree (negation or different
    numbers/values over the same salient terms) become an "Unresolved:"
    sentence naming both ids; the synthesis never silently picks a winner.

Runtime contract (matches the manifest): ``process_kind = memory.reflect``;
**idempotent**; **side_effects = read**; **on_error = raise**.

Public API:
    from scripts.processors.memory.memory_reflect import run
    out = run(query="deploy region?", memories=[{"id": ..., "text": ...}, ...])
    # -> {"synthesis": {"text": ..., "themes": [...], "serves_truth": False}}

CLI / self-test:
    python3 scripts/processors/memory/memory_reflect.py
    python3 -m scripts.processors.memory.memory_reflect
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Two memories sharing at least this many salient (non-stopword) terms are
#: grouped into one theme. 2 keeps "deploy region us-east-1" and "deploy
#: region eu-west-1" together without merging everything that shares one word.
THEME_OVERLAP_MIN = 2

#: Conflict detection needs at least this much shared vocabulary before a
#: negation/value disagreement counts as a conflict (one shared word is topic
#: drift, not disagreement).
CONFLICT_TERM_OVERLAP = 2

#: A memory must share at least this many salient terms with the query to be
#: woven into the synthesis; below it the memory is HELD OUT (returned, never
#: silently dropped — the lossless law).
MIN_RELEVANCE_TO_QUERY = 1

#: Memory kinds synthesized as opinion/preference rather than knowledge.
OPINION_KINDS = frozenset({"opinion", "preference"})

#: Negation tokens for the conflict heuristic.
NEGATION_TOKENS = frozenset({"not", "no", "never", "n't", "cannot", "isnt", "dont"})

#: Reason strings used in held_out entries (single definition, tests read them).
HELD_OUT_OFF_QUERY = "below MIN_RELEVANCE_TO_QUERY overlap with the query"

STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was",
    "what", "when", "where", "which", "who", "why", "will", "with", "our",
    "we", "i", "my", "us",
})

_TOKEN_RE = re.compile(r"[a-z0-9'-]+")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

#: Plural-stem floor: tokens longer than this lose a trailing "s" ("deploys"
#: → "deploy") so trivial inflection never splits a theme. Tokens ending in
#: "ss" ("press") are left alone.
PLURAL_STEM_MIN_LEN = 4


def _stem(token: str) -> str:
    if len(token) >= PLURAL_STEM_MIN_LEN and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _salient(text: str) -> set[str]:
    """Salient term set: lowercased, plural-stemmed word tokens minus stopwords."""
    return {_stem(t) for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}


def _conflict(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Deterministic disagreement heuristic over two same-theme memories."""
    ta, tb = _salient(a["text"]), _salient(b["text"])
    shared = ta & tb
    if len(shared) < CONFLICT_TERM_OVERLAP:
        return False
    neg_a = bool(ta & NEGATION_TOKENS)
    neg_b = bool(tb & NEGATION_TOKENS)
    if neg_a != neg_b:
        return True
    # Different numeric values over the same vocabulary disagree ("9am" vs "10am").
    nums_a = set(_NUMBER_RE.findall(a["text"]))
    nums_b = set(_NUMBER_RE.findall(b["text"]))
    if nums_a and nums_b and nums_a != nums_b:
        return True
    # Same leading terms but disjoint trailing VALUE words ("region is
    # us-east-1" vs "region is eu-west-1"): each side has a small remainder —
    # no larger than the shared core, so two genuinely different sentences
    # that merely overlap don't read as a disagreement.
    only_a, only_b = ta - shared - NEGATION_TOKENS, tb - shared - NEGATION_TOKENS
    return (bool(only_a) and bool(only_b)
            and len(only_a) <= len(shared) and len(only_b) <= len(shared))


def _theme_label(members: list[dict[str, Any]]) -> str:
    """Most frequent salient term across members; alphabetical tie-break."""
    freq: dict[str, int] = {}
    for m in members:
        for t in _salient(m["text"]):
            freq[t] = freq.get(t, 0) + 1
    return sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def run(*, query: str, memories: list[dict[str, Any]]) -> dict[str, Any]:
    """Reflect ``memories`` against ``query`` into one coherent synthesis (read-only).

    Returns ``{"synthesis": {...}}`` per the manifest's single output.
    """
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(memories, list):
        raise TypeError(f"memories must be a list of dicts, got {type(memories).__name__}")
    for m in memories:
        if not isinstance(m, dict) or "id" not in m or "text" not in m:
            raise ValueError("every memory needs at least id and text")

    qterms = _salient(query)
    relevant: list[dict[str, Any]] = []
    held_out: list[dict[str, Any]] = []
    for m in memories:
        if len(_salient(m["text"]) & qterms) >= MIN_RELEVANCE_TO_QUERY:
            relevant.append(m)
        else:
            held_out.append({"id": m["id"], "reason": HELD_OUT_OFF_QUERY})

    # Greedy deterministic theme grouping over input order (stable: input
    # order, then id, decides membership when overlaps tie).
    themes: list[list[dict[str, Any]]] = []
    for m in sorted(relevant, key=lambda x: (x.get("created_at", 0.0), str(x["id"]))):
        terms = _salient(m["text"])
        placed = False
        for group in themes:
            if any(len(terms & _salient(g["text"])) >= THEME_OVERLAP_MIN for g in group):
                group.append(m)
                placed = True
                break
        if not placed:
            themes.append([m])
    themes.sort(key=lambda g: _theme_label(g))  # deterministic theme order

    theme_rows: list[dict[str, Any]] = []
    paragraphs: list[str] = []
    supporting: list[str] = []
    for group in themes:
        label = _theme_label(group)
        ids = [str(g["id"]) for g in group]
        supporting.extend(ids)
        conflicts: list[list[str]] = []
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if _conflict(group[i], group[j]):
                    conflicts.append(sorted([str(group[i]["id"]), str(group[j]["id"])]))
        conflicted_ids = {cid for pair in conflicts for cid in pair}
        known = [g for g in group
                 if g.get("kind", "fact") not in OPINION_KINDS and str(g["id"]) not in conflicted_ids]
        opinions = [g for g in group if g.get("kind") in OPINION_KINDS]
        sentences: list[str] = []
        if known:
            sentences.append("Known: " + "; ".join(g["text"].rstrip(". ") for g in known) + ".")
        if opinions:
            sentences.append("Opinions/preferences: "
                             + "; ".join(g["text"].rstrip(". ") for g in opinions) + ".")
        for pair in sorted(conflicts):
            a = next(g for g in group if str(g["id"]) == pair[0])
            b = next(g for g in group if str(g["id"]) == pair[1])
            sentences.append(f"Unresolved ({pair[0]} vs {pair[1]}): "
                             f"\"{a['text'].rstrip('. ')}\" conflicts with \"{b['text'].rstrip('. ')}\".")
        paragraphs.append(f"[{label}] " + " ".join(sentences))
        theme_rows.append({"label": label, "memory_ids": ids, "conflicts": sorted(conflicts)})

    return {"synthesis": {
        "text": "\n".join(paragraphs),
        "themes": theme_rows,
        "supporting_memory_ids": supporting,
        "held_out": held_out,
        "is_derived": True,
        "serves_truth": False,
    }}


def _selftest() -> None:
    memories = [
        {"id": "m1", "text": "the deploy region is us-east-1", "created_at": 1.0},
        {"id": "m2", "text": "the deploy region is eu-west-1", "created_at": 2.0},
        {"id": "m3", "text": "deploys are gated by the promotion readiness plan", "created_at": 3.0},
        {"id": "m4", "text": "I prefer deploys to happen on Tuesdays", "kind": "preference", "created_at": 4.0},
        {"id": "m5", "text": "the owner's favorite coffee is dark roast", "created_at": 5.0},
    ]
    out = run(query="how do we deploy and to which region?", memories=memories)["synthesis"]

    # Conflict surfaced, neither side silently chosen.
    all_conflicts = [pair for t in out["themes"] for pair in t["conflicts"]]
    assert ["m1", "m2"] in all_conflicts
    assert "Unresolved (m1 vs m2)" in out["text"]
    assert "us-east-1" in out["text"] and "eu-west-1" in out["text"]

    # Fact vs opinion separation: the preference shows up only as opinion.
    assert "Opinions/preferences: I prefer deploys to happen on Tuesdays." in out["text"]
    for line in out["text"].splitlines():
        if "Known:" in line:
            assert "I prefer" not in line.split("Opinions/preferences:")[0]

    # Lossless accounting: every input id is either supporting or held out.
    accounted = set(out["supporting_memory_ids"]) | {h["id"] for h in out["held_out"]}
    assert accounted == {"m1", "m2", "m3", "m4", "m5"}
    assert {"id": "m5", "reason": HELD_OUT_OFF_QUERY} in out["held_out"]

    # Derived-content honesty is pinned.
    assert out["is_derived"] is True and out["serves_truth"] is False

    # Themed grouping: the region memories share a theme.
    region_theme = next(t for t in out["themes"] if set(t["memory_ids"]) >= {"m1", "m2"})
    assert region_theme["label"]

    # Deterministic byte-identical repeat; inputs not mutated.
    snapshot = json.dumps(memories, sort_keys=True)
    a = json.dumps(run(query="how do we deploy and to which region?", memories=memories), sort_keys=True)
    b = json.dumps(run(query="how do we deploy and to which region?", memories=memories), sort_keys=True)
    assert a == b and json.dumps(memories, sort_keys=True) == snapshot

    # Honest empty synthesis.
    empty = run(query="anything", memories=[])["synthesis"]
    assert empty["text"] == "" and empty["themes"] == [] and empty["serves_truth"] is False

    # Numeric disagreement also conflicts ("9" vs "10").
    nums = [{"id": "a", "text": "standup starts at 9 every day"},
            {"id": "b", "text": "standup starts at 10 every day"}]
    n = run(query="when does standup start", memories=nums)["synthesis"]
    assert [["a", "b"]] == [p for t in n["themes"] for p in t["conflicts"]] or \
           ["a", "b"] in [p for t in n["themes"] for p in t["conflicts"]]

    # on_error=raise.
    raised = False
    try:
        run(query="x", memories=[{"text": "missing id"}])
    except ValueError:
        raised = True
    assert raised, "memory without id must raise ValueError"
    raised = False
    try:
        run(query=None, memories=[])  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str query must raise TypeError"

    print(
        "PASS — memory_reflect: themed deterministic synthesis (not a ranked "
        "list), fact/opinion separation, negation+numeric conflicts surfaced "
        "as Unresolved (never silently resolved), lossless held_out accounting, "
        "serves_truth pinned False, byte-identical repeats verified"
    )


if __name__ == "__main__":
    _selftest()
