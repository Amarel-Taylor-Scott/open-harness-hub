#!/usr/bin/env python3
"""check_teleon_capability_network — proof for the cross-capability NETWORK graph + metadata enrichment.

Builds the relationships BETWEEN capabilities so distillation can be learned from STRUCTURE:
  * alternative_of — same need, different provider (same category + similar intent) clusters into ENDPOINT SETS
    (e.g. three WHOIS providers are detected as mutual alternatives; an unrelated capability is not).
  * composability — a capability's category exposes downstream categories it can feed (scraping -> data-extraction
    -> document), captured as a per-capability feature (no O(n^2) edge blow-up).
  * per-capability PROFILE = metadata + graph position; network_features EXTEND the skills-DB feature vector, so a
    trained policy can learn from alternative-count + composability, not just per-item features.
  * deterministic; never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_capability_network.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.training import CapabilityNetwork, enrich_features
from src.teleon.training.skills_db import FEATURE_KEYS


def _c(slot, category, intent, source_kind="mcp_server"):
    return {"capability_slot": slot, "category": category, "intent": intent,
            "determinism_ceiling": 0.95, "deterministic_coverage_estimate": 0.9, "source": {"kind": source_kind}}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    candidates = [
        _c("whois-rdap", "identity-compliance", "lookup domain whois registration record"),
        _c("whois-paid-api", "identity-compliance", "lookup domain whois registration ownership record"),
        _c("whois-library", "identity-compliance", "lookup domain whois registration record parser"),
        _c("sanctions-screen", "identity-compliance", "screen a name against OFAC sanctions lists"),
        _c("scrape-page", "scraping", "scrape a web page to markdown content"),
        _c("crawl-site", "scraping", "crawl a web site to markdown content pages"),
        _c("parse-pdf", "document", "parse a pdf document into text"),
    ]
    net = CapabilityNetwork().build(candidates)

    # alternative_of clusters the WHOIS providers (endpoint set); the sanctions cap is NOT an alternative of them.
    whois_alts = set(net.alternatives("whois-rdap"))
    ck("the three WHOIS providers are detected as mutual alternatives (an endpoint set)",
       {"whois-paid-api", "whois-library"} <= whois_alts, str(whois_alts))
    ck("an unrelated same-category capability is NOT an alternative (sanctions != whois)",
       "sanctions-screen" not in whois_alts and net.alternatives("sanctions-screen") == [])
    ck("the two scraping providers are alternatives of each other",
       net.alternatives("scrape-page") == ["crawl-site"])

    # per-capability profile (the metadata 'map').
    prof = net.profile("whois-rdap")
    ck("profile carries metadata + graph position (n_alternatives, category_size, downstream)",
       prof["n_alternatives"] == 2 and prof["category_size"] == 4
       and "regulation" in prof["downstream_categories"] and prof["serves_truth"] is False)

    # composability: a scraping capability has downstream data-extraction/document/research capabilities.
    sp = net.profile("scrape-page")
    ck("composability is captured: scraping -> downstream categories with available capabilities",
       "data-extraction" in sp["downstream_categories"] or "document" in sp["downstream_categories"]
       and sp["downstream_capability_count"] >= 1, str(sp["downstream_categories"]))

    # network features EXTEND the skills-DB feature vector (richer training signal).
    enriched = enrich_features(candidates[0], net)
    ck("enriched features add network signals on TOP of the base feature schema",
       set(FEATURE_KEYS) <= set(enriched) and {"n_alternatives", "has_alternatives", "is_composable",
       "downstream_capability_count"} <= set(enriched) and enriched["has_alternatives"] == 1)

    # summary + determinism + unknown slot fails loud.
    s = net.summary()
    ck("summary reports the network shape and never serves truth",
       s["capabilities"] == 7 and s["with_alternatives"] >= 5 and s["serves_truth"] is False)
    ck("the network build is deterministic", CapabilityNetwork().build(candidates).alternatives("whois-rdap") == net.alternatives("whois-rdap"))
    raised = False
    try:
        net.profile("no-such-cap")
    except KeyError:
        raised = True
    ck("an unknown capability fails loud", raised)

    print("\n" + ("PASS - check_teleon_capability_network: the cross-capability network detects alternative_of "
                  "endpoint sets (WHOIS providers cluster; unrelated caps don't), captures composability via "
                  "category adjacency, and exposes a per-capability profile + network features that extend the "
                  "skills-DB feature vector — so distillation can be learned from STRUCTURE. Deterministic, never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
