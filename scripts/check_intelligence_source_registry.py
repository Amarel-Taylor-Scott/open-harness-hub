#!/usr/bin/env python3
"""check_intelligence_source_registry — proof for the FREE, LEGITIMATE intelligence-source registry + intake: a
constant stream (top repos / AI news / papers / newsletters / search) from RSS + official REST APIs only (keyless
or free-key, ToS-clean), with a news-sweep planner and a pull that routes through governed-feed-intake (legitimate
paths; refuses scraping). The rate-limit-proof alternative to ad-hoc web search. serves_truth=false.

CLI: PYTHONPATH=. python3 scripts/check_intelligence_source_registry.py --self-test
"""
from __future__ import annotations

import os
import re
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.intel.intelligence_intake import load_sources, needs, plan_news_sweep, pull, select_sources

_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    srcs = load_sources()
    ck("registry has >= 12 free sources across >= 5 needs (repos/news/papers/newsletters/search)",
       len(srcs) >= 12 and len(needs()) >= 5, f"{len(srcs)} sources / {len(needs())} needs")
    # every source is LEGITIMATE: rss or official rest_api, ToS-clean, keyless or free-key
    ck("every source is legitimate (rss/rest_api, ToS-clean)",
       all(s["access"] in ("rss", "rest_api") and s["tos_clean"] is True for s in srcs))
    bad_keys = [k for s in srcs for k in s["requires_keys"] if not _KEY_RE.match(k)]
    ck("any required key is an env-ref NAME, never a value (secret hygiene)", not bad_keys, str(bad_keys))
    ck("most sources are keyless (low setup friction)", sum(1 for s in srcs if s["keyless"] and not s["requires_keys"]) >= 9)
    ck("the named source kinds are present (GitHub trends, Hacker News, arXiv, a newsletter RSS)",
       {"github-search-api", "hackernews", "arxiv"} <= {s["id"] for s in srcs}
       and any(s["need"] == "newsletter" and s["access"] == "rss" for s in srcs))

    # selector: keyless preferred; a key-requiring source excluded with no key, included with the key
    code_nokey = select_sources("code_trends", available_keys=())
    ck("code_trends has keyless sources selectable with NO keys (trending RSS / OSS Insight)",
       code_nokey and all(s["keyless"] for s in code_nokey))
    search_nokey = {s["id"] for s in select_sources("search", available_keys=())}
    search_key = {s["id"] for s in select_sources("search", available_keys=("BRAVE_API_KEY",))}
    ck("brave-search is excluded with no key, included once BRAVE_API_KEY is provided",
       "brave-search" not in search_nokey and "brave-search" in search_key)

    # the news-sweep plan covers every need with >= 1 free source — the rate-limit-proof sweep
    sweep = plan_news_sweep(available_keys=())
    ck("the keyless news-sweep plan covers EVERY need with >= 1 free source",
       all(len(sweep["plan"][n]) >= 1 for n in needs()) and sweep["serves_truth"] is False, str(sweep["plan"]))

    # pull routes through governed-feed-intake (legitimate): rss ingests candidates; never scrapes
    p = pull("tldr-ai-rss", items=("New agent framework X released", "Model Y benchmarks"))
    ck("pull via an RSS source ingests items as UNTRUSTED candidates (governed-feed-intake, legitimate)",
       p["access_method"] == "rss" and p["intake"]["fetched"] is True
       and all(it["trusted"] is False for it in p["intake"]["candidate_items"]))
    # a key-requiring source with no key → unfetchable, logged honestly (not faked)
    pk = pull("brave-search", items=("q",), available_keys=())
    ck("a key-requiring source with no key is logged unfetchable (honest, not fabricated)",
       pk["fetched"] is False and pk["unfetchable_logged"] is True)
    ck("intake never serves truth", p["serves_truth"] is False)
    ck("deterministic", plan_news_sweep(available_keys=()) == sweep)

    print("\n" + (f"PASS - check_intelligence_source_registry: {len(srcs)} FREE legitimate sources across "
                  f"{len(needs())} needs (RSS + official APIs, keyless/free-key, ToS-clean); a keyless news-sweep "
                  f"plan covers every need; pull routes through governed-feed-intake (legitimate paths, refuses "
                  f"scraping); key-gated sources logged unfetchable honestly. The rate-limit-proof intelligence "
                  f"stream. Never serves truth." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_intelligence_source_registry.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
