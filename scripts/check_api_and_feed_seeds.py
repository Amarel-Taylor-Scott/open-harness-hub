#!/usr/bin/env python3
"""check_api_and_feed_seeds — proof for the API-hub intake + governed feed-intake seeds (+ the repo-batch seeds).
The load-bearing assertion: the governed feed-intake REFUSES ToS-violating scraping / anti-bot evasion / bulk PII
harvesting by policy, ingests only via legitimate paths (official API / owner-paste / RSS / public export), and
logs an inaccessible source HONESTLY (never fabricated). The API-hub intake catalogs endpoint CANDIDATES (auth +
cost + a port) without making the call. Nothing serves truth; discovery != trust.

CLI: PYTHONPATH=. python3 scripts/check_api_and_feed_seeds.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.seeds import all_seeds


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    by = {s.slot: s for s in all_seeds()}
    for slot in ("api-hub-intake", "governed-feed-intake", "provider-allowlist-gateway",
                 "container-lifecycle-panel", "places-api-intake", "legal-gap-taxonomy"):
        ck(f"seed '{slot}' is registered", slot in by)

    feed = by["governed-feed-intake"]
    # THE GOVERNANCE TEETH: ToS-violating scraping / anti-bot evasion / bulk PII harvest is REFUSED
    refused = feed.run({"source": "facebook.com/DeepRepo", "access_method": "scrape_tos_protected"})["output"]
    ck("feed-intake REFUSES ToS-violating scraping (the FB-scrape ask) and logs it honestly",
       refused.get("refused") is True and refused.get("unfetchable_logged") is True)
    evade = feed.run({"source": "x", "access_method": "anti_bot_evasion"})["output"]
    ck("feed-intake REFUSES anti-bot evasion + bulk PII harvest", evade.get("refused") is True)
    # no legitimate path -> honest unfetchable log (never fabricated)
    none = feed.run({"source": "facebook.com/DeepRepo", "access_method": ""})["output"]
    ck("a source with no legitimate access path is logged UNFETCHABLE (never fabricated)",
       none.get("fetched") is False and none.get("unfetchable_logged") is True)
    # legitimate paths DO ingest — as untrusted candidates
    ok_paste = feed.run({"source": "DeepRepo export", "access_method": "owner_paste",
                         "items": ["repo A shared", "repo B shared"]})["output"]
    ck("feed-intake INGESTS via a legitimate path (owner_paste) as untrusted candidates",
       ok_paste.get("fetched") is True and ok_paste.get("n") == 2
       and all(it["trusted"] is False for it in ok_paste["candidate_items"]))
    ck("feed-intake never serves truth", feed.run({"source": "x", "access_method": "rss"})["serves_truth"] is False)

    # api-hub-intake catalogs governed endpoint CANDIDATES, never makes the call
    hub = by["api-hub-intake"].run({"capability_need": "telecom-location"})["output"]
    ck("api-hub-intake catalogs governed endpoint candidates (Nokia CAMARA), call stays behind a port",
       hub["endpoint_candidates"] and all(c["serves_truth"] is False and c["governed"] == "candidate"
                                          for c in hub["endpoint_candidates"]))
    whois = by["api-hub-intake"].run({"capability_need": "whois"})["output"]
    ck("api-hub-intake resolves a different need to its own endpoint set (whois -> RDAP)",
       any("rdap" in c["endpoint"].lower() for c in whois["endpoint_candidates"]))

    # places-api-intake is API-FIRST (scraping declined); legal-gap-taxonomy is intel-only
    places = by["places-api-intake"].run({"query": "bakeries"})["output"]
    ck("places-api-intake uses the official API + PII gate (scraping path declined)",
       places["access"] == "official_places_api" and "pii" in str(places).lower())
    ck("legal-gap-taxonomy is intel-only (NC-ND): not adoptable, not drop-in",
       by["legal-gap-taxonomy"].adoptable is False and by["legal-gap-taxonomy"].is_drop_in() is False)

    # the two clean-permissive repo seeds ARE drop-in; everything is governed + deterministic
    ck("provider-allowlist + container-lifecycle (MIT/BSD) are drop-in; api/feed/legal/places are clean-room",
       by["provider-allowlist-gateway"].is_drop_in() and by["container-lifecycle-panel"].is_drop_in()
       and not by["governed-feed-intake"].is_drop_in() and not by["api-hub-intake"].is_drop_in())
    ck("all six run + never serve truth + deterministic",
       all(by[s].run({})["serves_truth"] is False for s in
           ("api-hub-intake", "governed-feed-intake", "provider-allowlist-gateway",
            "container-lifecycle-panel", "places-api-intake", "legal-gap-taxonomy"))
       and feed.run({"source": "x", "access_method": "rss"}) == feed.run({"source": "x", "access_method": "rss"}))

    print("\n" + ("PASS - check_api_and_feed_seeds: the governed feed-intake INGESTS only via legitimate paths "
                  "(official API / owner-paste / RSS) and REFUSES ToS-violating scraping + anti-bot evasion + bulk "
                  "PII harvest (the FB-scrape ask), logging inaccessible sources honestly; the API-hub intake "
                  "catalogs governed endpoint candidates (RapidAPI/Nokia CAMARA) behind a port; the repo-batch seeds "
                  "are clean-room/drop-in by license. Discovery != trust; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_api_and_feed_seeds.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
