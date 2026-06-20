#!/usr/bin/env python3
"""Backs `processor/emit-claudemd-fragment` (process_kind ``deliver.claudemd``).

Emit the distilled, always-loaded tier as a CLAUDE.md fragment — the stable
knowledge that survives compaction (conventions, glossary, invariants) at
near-zero token cost. Input is the DISTILLED layer (already gated upstream);
this emitter only renders, it never invents: only ``stable: true`` items are
emitted, everything else is returned in ``held_out`` with the reason (the
lossless law at the consumption surface).

Contract: deterministic; side_effects=none; on_error=raise.
Input distilled → output claudemd.

CLI / self-test: python3 scripts/processors/deliver/emit_claudemd_fragment.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Sections rendered, in order. Item kind → section header.
SECTION_ORDER = ("convention", "glossary", "invariant")
SECTION_HEADERS = {"convention": "## Conventions", "glossary": "## Glossary",
                   "invariant": "## Invariants (do not violate)"}

#: Items longer than this are NOT silently truncated — they are held out as
#: too long for the always-loaded tier (CLAUDE.md is a token budget).
MAX_ITEM_CHARS = 300

HELD_OUT_NOT_STABLE = "not marked stable: true (only gated-stable knowledge ships)"
HELD_OUT_TOO_LONG = f"longer than {MAX_ITEM_CHARS} chars — too big for the always-loaded tier"
HELD_OUT_UNKNOWN_KIND = "unknown kind (not convention/glossary/invariant)"


def run(*, distilled: list[dict[str, Any]], title: str = "Distilled knowledge (auto-emitted)") -> dict[str, Any]:
    """Render stable distilled items into a CLAUDE.md fragment."""
    if not isinstance(distilled, list):
        raise TypeError("distilled must be a list of item dicts")
    by_kind: dict[str, list[dict[str, Any]]] = {k: [] for k in SECTION_ORDER}
    held_out: list[dict[str, Any]] = []
    for i, item in enumerate(distilled):
        if not isinstance(item, dict) or "text" not in item:
            raise ValueError(f"distilled[{i}] needs text")
        iid = item.get("id", f"item-{i}")
        if item.get("kind") not in SECTION_ORDER:
            held_out.append({"id": iid, "reason": HELD_OUT_UNKNOWN_KIND})
            continue
        if not item.get("stable"):
            held_out.append({"id": iid, "reason": HELD_OUT_NOT_STABLE})
            continue
        if len(str(item["text"])) > MAX_ITEM_CHARS:
            held_out.append({"id": iid, "reason": HELD_OUT_TOO_LONG})
            continue
        by_kind[item["kind"]].append(item)
    lines = [f"# {title}", ""]
    emitted = 0
    for kind in SECTION_ORDER:
        items = sorted(by_kind[kind], key=lambda x: str(x.get("id", x["text"])))
        if not items:
            continue
        lines += [SECTION_HEADERS[kind]]
        for item in items:
            term = f"**{item['term']}** — " if kind == "glossary" and item.get("term") else ""
            lines.append(f"- {term}{item['text']}")
            emitted += 1
        lines.append("")
    fragment = "\n".join(lines).rstrip() + "\n"
    return {"claudemd": {"fragment": fragment, "emitted": emitted,
                         "held_out": held_out, "tier": "always_loaded"}}


def _selftest() -> None:
    distilled = [
        {"id": "c1", "kind": "convention", "stable": True,
         "text": "Components and subcomponents, never artifacts/manifests, in new prose."},
        {"id": "g1", "kind": "glossary", "stable": True, "term": "Knowledge Corpus",
         "text": "the governed fact store a pipeline consumes (never 'knowledge pack')."},
        {"id": "i1", "kind": "invariant", "stable": True,
         "text": "Distillation is never replacement — raw + lineage always survive."},
        {"id": "u1", "kind": "convention", "stable": False, "text": "still churning"},
        {"id": "b1", "kind": "convention", "stable": True, "text": "x" * 400},
        {"id": "k1", "kind": "vibe", "stable": True, "text": "not a real kind"},
    ]
    out = run(distilled=distilled)["claudemd"]
    f = out["fragment"]
    # Stable items render under their sections, glossary terms bolded.
    assert SECTION_HEADERS["convention"] in f and SECTION_HEADERS["invariant"] in f
    assert "**Knowledge Corpus** — the governed" in f
    assert out["emitted"] == 3
    # Everything else is HELD OUT with the exact reason (lossless).
    reasons = {h["id"]: h["reason"] for h in out["held_out"]}
    assert reasons["u1"] == HELD_OUT_NOT_STABLE
    assert reasons["b1"] == HELD_OUT_TOO_LONG
    assert reasons["k1"] == HELD_OUT_UNKNOWN_KIND
    assert "still churning" not in f and "x" * 50 not in f
    # Deterministic; honest empty; on_error=raise.
    assert json.dumps(run(distilled=distilled), sort_keys=True) == \
           json.dumps(run(distilled=distilled), sort_keys=True)
    empty = run(distilled=[])["claudemd"]
    assert empty["emitted"] == 0 and empty["fragment"].startswith("# ")
    raised = False
    try:
        run(distilled=[{"kind": "convention"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — emit_claudemd_fragment: stable-only sections (conventions/glossary/"
          "invariants), held_out with exact reasons (unstable/too-long/unknown-kind), "
          "deterministic render verified")


if __name__ == "__main__":
    _selftest()
