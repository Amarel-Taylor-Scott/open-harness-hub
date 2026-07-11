#!/usr/bin/env python3
"""check_input_acquire — proof that the cheapest-that-meets extraction cascade generalizes across INPUT TYPES:
PDF, Office doc, plain text, email + attachments, web page, RSS feed, social post, image, audio note. Each is
normalized by a cheapest-first acquire ladder (deterministic where possible; a model method only when the input
forces it; web/social via legitimate paths only — never scraping), then fed the SAME extraction cascade. A combined
receipt tracks acquire + extract cost/path. serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_input_acquire.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.extraction.input_acquire import ACQUIRE_LADDER, acquire, extract_from, supported_input_types


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    types = supported_input_types()
    ck("supports >= 9 input types incl. email/web/rss/text/social/image/audio",
       len(types) >= 9 and {"pdf", "email", "web_page", "rss_feed", "text", "social_post", "image", "audio_note"} <= set(types),
       str(types))
    ck("every input type has a cheapest-first acquire ladder",
       all(ACQUIRE_LADDER[t] and [m[1] for m in ACQUIRE_LADDER[t]] == sorted(m[1] for m in ACQUIRE_LADDER[t]) for t in types))

    # the deterministic-where-possible point: text/email/web/rss/office have a FREE/cheap deterministic acquire (no key)
    det_types = ["text", "email", "web_page", "rss_feed", "office_doc"]
    ck("text/email/web/rss/office acquire deterministically with NO LLM key",
       all(acquire(t, {"is_html": True}, available_keys=())["deterministic"] for t in det_types))

    # social uses the LEGITIMATE feed path (governed), not scraping
    soc = acquire("social_post", {"has_legitimate_api": True}, available_keys=())
    ck("social_post acquires via the legitimate-feed path (governed, not scraping)",
       soc["acquired"] and soc["method"] == "legitimate_feed_intake" and soc["deterministic"])

    # a model acquire (audio ASR) needs its key; without it, acquire honestly fails (not fabricated)
    ck("audio_note needs an LLM/ASR key; without it acquire fails honestly (not fabricated)",
       acquire("audio_note", {}, available_keys=())["acquired"] is False
       and acquire("audio_note", {}, available_keys=("LLM_API_KEY",))["acquired"] is True)

    # extract_from: web page + all-structured schema, no key → FULLY deterministic (html→text + regex), no LLM
    web = extract_from("web_page", {"is_html": True}, {"title": "structured", "price": "structured"}, available_keys=())
    ck("web_page + all-structured schema → fully deterministic end-to-end (acquire + extract, no LLM)",
       web["met_requirement"] and web["deterministic_only"] is True and "html_to_clean_text" in web["path"])

    # extract_from: email + a schema with an unstructured field + key → acquire deterministic, extract escalates to LLM
    em = extract_from("email", {}, {"sender": "structured", "intent": "unstructured"}, available_keys=("LLM_API_KEY",))
    ck("email + mixed schema → deterministic acquire (mime_parse) then LLM only for the unstructured field",
       em["met_requirement"] and em["acquire"]["method"] == "mime_parse" and em["extract"]["used_llm"] is True)

    # combined receipt: total cost = acquire + extract; path includes both stages
    ck("the combined receipt sums acquire + extract cost and lists the full path",
       abs(em["total_cost"] - round(em["acquire"]["cost"] + em["extract"]["total_cost"], 4)) < 1e-9
       and em["path"][0] == "mime_parse")

    ck("an unsupported input type is reported, not crashed", acquire("hologram", {})["acquired"] is False)
    ck("never serves truth", web["serves_truth"] is False and soc["serves_truth"] is False)
    ck("deterministic", extract_from("web_page", {"is_html": True}, {"title": "structured"}, available_keys=()) ==
       extract_from("web_page", {"is_html": True}, {"title": "structured"}, available_keys=()))

    print("\n" + (f"PASS - check_input_acquire: the extraction cascade generalizes across {len(types)} input types "
                  f"(pdf/office/text/email/web/rss/social/image/audio) — each normalized by a cheapest-first acquire "
                  f"ladder (deterministic where possible; model only when forced; social/web via legitimate paths), "
                  f"then the same cheapest-that-meets extraction. Combined acquire+extract receipt. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_input_acquire.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
