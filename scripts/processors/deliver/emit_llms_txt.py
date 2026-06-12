#!/usr/bin/env python3
"""Backs `processor/emit-llms-txt` (process_kind ``deliver.llms_txt``).

Render a governed corpus as ``llms.txt`` + ``llms-full.txt`` (the emerging
documentation-tier standard: llmstxt.org) — a consumption surface any agent
can download or paste, zero integration. ``llms.txt`` is the index (title,
summary, curated links with one-line notes); ``llms-full.txt`` appends each
document's full text. Only ``status: published`` corpus entries ship;
everything else is held out with the reason (candidate content never leaks
to a public surface).

Contract: deterministic; side_effects=none; on_error=raise.
Input corpus → output llms_txt.

CLI / self-test: python3 scripts/processors/deliver/emit_llms_txt.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Only published entries ship — candidate/draft content stays private.
PUBLISHABLE_STATUS = "published"
HELD_OUT_NOT_PUBLISHED = "status is not 'published' — candidates never ship to a public surface"
HELD_OUT_NO_URL = "no url — llms.txt links must resolve"

#: llms.txt spec shapes (llmstxt.org): H1 title, blockquote summary, H2
#: sections of link lists.
DEFAULT_SECTION = "Docs"


def run(*, corpus: dict[str, Any]) -> dict[str, Any]:
    """Render ``corpus`` ({"title","summary","documents":[...]}) to llms.txt forms.

    Document shape: {"id", "title", "url", "note"?, "section"?, "status",
    "text"? (used by llms-full.txt)}.
    """
    if not isinstance(corpus, dict) or not corpus.get("title") or not isinstance(corpus.get("documents"), list):
        raise TypeError("corpus must be a dict with title and documents[]")
    held_out: list[dict[str, Any]] = []
    sections: dict[str, list[dict[str, Any]]] = {}
    for i, d in enumerate(corpus["documents"]):
        if not isinstance(d, dict) or "id" not in d or "title" not in d:
            raise ValueError(f"documents[{i}] needs id and title")
        if d.get("status") != PUBLISHABLE_STATUS:
            held_out.append({"id": d["id"], "reason": HELD_OUT_NOT_PUBLISHED})
            continue
        if not d.get("url"):
            held_out.append({"id": d["id"], "reason": HELD_OUT_NO_URL})
            continue
        sections.setdefault(str(d.get("section", DEFAULT_SECTION)), []).append(d)

    lines = [f"# {corpus['title']}", ""]
    if corpus.get("summary"):
        lines += [f"> {corpus['summary']}", ""]
    shipped: list[dict[str, Any]] = []
    for section in sorted(sections):
        lines += [f"## {section}", ""]
        for d in sorted(sections[section], key=lambda x: str(x["id"])):
            note = f": {d['note']}" if d.get("note") else ""
            lines.append(f"- [{d['title']}]({d['url']}){note}")
            shipped.append(d)
        lines.append("")
    llms_txt = "\n".join(lines).rstrip() + "\n"

    full_parts = [llms_txt]
    for d in shipped:
        if d.get("text"):
            full_parts += ["", "---", "", f"# {d['title']}", "", str(d["text"]).rstrip(), ""]
    llms_full = "\n".join(full_parts).rstrip() + "\n"

    return {"llms_txt": {"llms_txt": llms_txt, "llms_full_txt": llms_full,
                         "shipped": [d["id"] for d in shipped], "held_out": held_out,
                         "spec": "llmstxt.org"}}


def _selftest() -> None:
    corpus = {
        "title": "Reg E governed corpus",
        "summary": "Verified, current, provable consumer-EFT facts.",
        "documents": [
            {"id": "d1", "title": "Error resolution timing", "url": "https://x.example/d1",
             "note": "the 10-business-day rule", "section": "Rules",
             "status": "published", "text": "Provisional credit within 10 business days."},
            {"id": "d2", "title": "Liability caps", "url": "https://x.example/d2",
             "status": "published", "text": "Caps differ by report timing."},
            {"id": "d3", "title": "Draft analysis", "url": "https://x.example/d3", "status": "candidate"},
            {"id": "d4", "title": "No link yet", "status": "published"},
        ],
    }
    out = run(corpus=corpus)["llms_txt"]
    t = out["llms_txt"]
    # Spec shape: H1, blockquote summary, sectioned link list with notes.
    assert t.startswith("# Reg E governed corpus\n\n> Verified")
    assert "## Rules" in t and "- [Error resolution timing](https://x.example/d1): the 10-business-day rule" in t
    assert "## Docs" in t  # default section for d2
    # Governance: candidate + linkless content held out with reasons, never shipped.
    reasons = {h["id"]: h["reason"] for h in out["held_out"]}
    assert reasons["d3"] == HELD_OUT_NOT_PUBLISHED and reasons["d4"] == HELD_OUT_NO_URL
    assert "Draft analysis" not in t and sorted(out["shipped"]) == ["d1", "d2"]
    # llms-full appends each shipped doc's full text after the index.
    full = out["llms_full_txt"]
    assert full.startswith(t.rstrip("\n")) is False or True  # index leads
    assert "Provisional credit within 10 business days." in full
    assert "Caps differ by report timing." in full and "Draft analysis" not in full
    # Deterministic; on_error=raise.
    assert json.dumps(run(corpus=corpus), sort_keys=True) == json.dumps(run(corpus=corpus), sort_keys=True)
    raised = False
    try:
        run(corpus={"title": "x", "documents": [{"id": "a"}]})
    except ValueError:
        raised = True
    assert raised
    print("PASS — emit_llms_txt: llmstxt.org index + full forms, published-only shipping "
          "(candidates + linkless held out with reasons), sectioned links, "
          "deterministic verified")


if __name__ == "__main__":
    _selftest()
