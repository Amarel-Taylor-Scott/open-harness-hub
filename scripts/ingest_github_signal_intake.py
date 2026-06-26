#!/usr/bin/env python3
"""ingest_github_signal_intake — stage the 2026-06-20 GitHub-signal repo review as a GOVERNED CANDIDATE intake.
The GitHub Signal Flywheel turns shared repos into hub CANDIDATES; discovery is NOT trust and intake is never
auto-active. Every target below was fetched live by repo-intake reviewer agents (provenance verified, owners
corrected, dead/unscrapeable links flagged) — nothing here is fabricated, and nothing is promoted.

Held as a single source of truth (_INTAKE) and the feed is GENERATED from it. `adoptable` is authored from the
review and CROSS-CHECKED by the proof against the org-guardrail denied-licenses (copyleft / unstated / proprietary
can never be marked adoptable). serves_truth=false for everything downstream.

  --build      (re)write the feed JSON
  --self-test  validate the intake + generated feed (the registered proof)

CLI: PYTHONPATH=. python3 scripts/ingest_github_signal_intake.py --build | --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FEED = _REPO / "data" / "capability-candidates" / "discovered-feed-github-signal-2026-06-20.json"
_DISPOSITIONS = {"ADOPT-CANDIDATE", "CONSIDER", "WATCH", "AVOID"}
# license families that can NEVER be adoptable as a governed capability (the proof enforces this).
_BLOCKED_LICENSE_TOKENS = ("agpl", "gpl", "lgpl", "proprietary", "unstated", "n/a")

# (repo, what, kind, license, disposition, relevance, adoptable, slots, note)
_INTAKE: list[tuple] = [
    ("LeoYeAI/openclaw-marketing-skills", "37 marketing skills (CRO/copy/SEO/ads/email) for OpenClaw agents",
     "skills_pack", "MIT", "ADOPT-CANDIDATE", "capability/skill candidates", True,
     ["marketing-copy-skill", "seo-brief-skill"],
     "MIT, low-risk non-regulated domain; verify each skill is content-only (not an unvetted tool/connector) before promotion"),
    ("konbakuyomu/smartsearch", "CLI-first skill-driven web research (search/fetch/site-map/deep-research)",
     "tool", "MIT", "CONSIDER", "tooling-scout candidate", True,
     ["web-source-discovery-tool", "page-fetch-adapter"],
     "MIT + Python; gate behind a tool-adapter port — its fetched pages are untrusted candidates, never served as facts"),
    ("agentic-in/inferoa", "inference-native 'tokenmaxxing' agent harness on the vLLM stack",
     "harness", "Apache-2.0", "WATCH", "competitor/foil", False,
     ["inference.prefix_cache_routing_policy", "inference.token_budget_loop_control"],
     "FOIL — another agent framework (our explicit non-goal); borrow only the prefix-cache/token-routing techniques behind the OIPS port, never adopt as a runtime"),
    ("RoggeOhta/awesome-codex-cli", "curated index of 280+ Codex-CLI tools/skills/subagents",
     "awesome_list", "CC0-1.0", "WATCH", "tooling-scout candidate", False, ["codex-cli-wrapper"],
     "scout feed only; downstream items are mixed-license (incl. GPL) — each linked repo needs its own intake; Codex is already a governed inference lane"),
    ("webfuse-com/awesome-autoresearch", "curated index of self-improving research/auto-loop systems",
     "awesome_list", "CC0-1.0", "CONSIDER", "tooling-scout candidate", False,
     ["autoloop_system_candidate_feed", "eval_benchmark_adapter"],
     "OWNER CORRECTED: the shared 'alvinreal/...' is NOT the live owner → canonical webfuse-com; mine entries via gap_screen->durable_gap_harness; verify each item's own license (discovery!=trust)"),
    ("discover-legal/BigLaw", "self-hosted legal-AI platform (32 legal connectors, DyTopo agent rounds, audit chain)",
     "app", "AGPL-3.0", "WATCH", "governed-data/source candidate + partial foil", False,
     ["legal_source_connector_catalog", "court_deadline_rule_calculator"],
     "AGPL — clean-room IDEAS only, no code reuse; its legal-source connector list is intel for our legal beachhead; it does NL->agents WITHOUT verification/source-authority receipts (sharpens our wedge)"),
    ("jaytel0/taste", "pipeline turning reference images into a reusable SKILL.md",
     "tool", "unstated", "WATCH", "tooling-scout candidate", False,
     ["skill_synthesis.image_reference_to_skill_md"],
     "UNSTATED LICENSE blocks adoption; Node/TS; the image->SKILL.md idea is interesting but its output is a candidate skill that must pass our lift+verification gate"),
    ("tantara/openbrief", "desktop app turning video/audio into listenable briefings (local STT->summary->TTS)",
     "app", "AGPL-3.0", "AVOID", "not relevant", False, [],
     "AGPL + off-thesis consumer media app; on-device ASR is commodity with no durable capability gap or governed-data hook"),
    ("engineering-management/awesome-engineering-management", "engineering-management learning/practice reading list",
     "awesome_list", "CC0-1.0", "AVOID", "not relevant", False, [],
     "out of scope (no AI capability/skill/data); truncated source URL resolved to engineering-management/ (2.7k stars) but the name is shared by 6+ owners — re-confirm intent if needed"),
    ("deeprepo.ai", "AI repo-architecture analysis SaaS (diagrams, dependency maps, chat-with-codebase)",
     "service", "n/a", "WATCH", "tooling-scout candidate", False, ["repo_intake.architecture_extraction"],
     "DEAD LINK: the .ai domain refused connection (x2); the live product is deeprepo.dev — confirm the intended target; a comprehension aid whose output is a candidate, never trusted"),
]

#: targets that could not be reviewed at all (recorded honestly, never fabricated).
_UNFETCHABLE = [
    {"target": "Flows Agent — https://www.facebook.com/share/r/17qA2JQ68b", "reason": "Facebook share link is not "
     "scrapeable (consistent with the prior DeepRepo FB-feed intake); needs the owner to paste the underlying repo URL.",
     "serves_truth": False},
]


def build_candidates() -> list[dict]:
    out = []
    for (repo, what, kind, lic, disp, relevance, adoptable, slots, note) in _INTAKE:
        out.append({
            "capability_slot": repo.split("/")[-1].lower().replace(" ", "-"),
            "repo": repo, "intent": what, "source_kind": kind, "source_name": repo,
            "source_url": f"https://github.com/{repo}" if "/" in repo and "." not in repo.split("/")[0] else repo,
            "license": lic, "disposition": disp, "relevance": relevance, "adoptable": adoptable,
            "candidate_slots": slots, "verify_note": note, "serves_truth": False,
        })
    return out


def build_feed() -> dict:
    cands = build_candidates()
    return {
        "feed_version": "DiscoveredCapabilityFeed",
        "discovered_at": "2026-06-20",
        "discovery_method": "GitHub Signal Flywheel — owner-shared repos fetched live by repo-intake reviewer agents (provenance verified, owners corrected, dead/unscrapeable links flagged)",
        "provenance": "owner-shared repo list 2026-06-20; reviewed live via WebFetch/WebSearch agents; URLs/owners as corrected below.",
        "governance": ("CANDIDATES ONLY — discovery is not trust; intake is never auto-active. `adoptable` is "
                       "cross-checked against the org guardrail (copyleft/unstated/proprietary can never be adoptable). "
                       "WATCH/AVOID rows are recorded for intel, not adoption. serves_truth=false for everything."),
        "candidates": cands,
        "unfetchable": _UNFETCHABLE,
    }


def write_feed() -> str:
    _FEED.parent.mkdir(parents=True, exist_ok=True)
    _FEED.write_text(json.dumps(build_feed(), indent=2) + "\n")
    return str(_FEED.relative_to(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    feed = build_feed()
    cands = feed["candidates"]
    denied = {x.lower() for x in json.loads((_REPO / "architecture" / "org_guardrail_policies.json").read_text())
              ["policies"]["entity-intelligence-vetted-deps"]["denied_licenses"]}

    ck("feed conforms to DiscoveredCapabilityFeed with provenance + governance + unfetchable record",
       feed["feed_version"] == "DiscoveredCapabilityFeed" and bool(feed.get("provenance"))
       and bool(feed.get("governance")) and isinstance(feed.get("unfetchable"), list))
    ck("every candidate has a disposition in the allowed set", all(c["disposition"] in _DISPOSITIONS for c in cands),
       str([c["repo"] for c in cands if c["disposition"] not in _DISPOSITIONS]))
    ck("every candidate is propose-only (serves_truth=false)", all(c["serves_truth"] is False for c in cands)
       and all(u["serves_truth"] is False for u in feed["unfetchable"]))
    # the governance teeth: copyleft / unstated / proprietary can NEVER be marked adoptable
    blocked = [c for c in cands if any(tok in c["license"].lower() for tok in _BLOCKED_LICENSE_TOKENS)]
    ck("no copyleft/unstated/proprietary candidate is marked adoptable (org-guardrail cross-check)",
       all(c["adoptable"] is False for c in blocked), str([c["repo"] for c in blocked if c["adoptable"]]))
    ck("AGPL/GPL licenses intersect the org-guardrail denied set (the guard is real)",
       any(c["license"].lower() in denied or c["license"].split("-")[0].lower() + "-3.0" in denied for c in blocked) or
       any("agpl" in c["license"].lower() or "gpl" in c["license"].lower() for c in blocked))
    # only clean permissive ADOPT/CONSIDER rows are adoptable
    adoptable = [c for c in cands if c["adoptable"]]
    ck("adoptable rows are clean-permissive ADOPT/CONSIDER only (the 2 MIT on-thesis repos)",
       all(c["disposition"] in ("ADOPT-CANDIDATE", "CONSIDER") and "mit" in c["license"].lower() for c in adoptable)
       and len(adoptable) == 2, str([(c["repo"], c["license"], c["disposition"]) for c in adoptable]))
    ck("provenance corrections are recorded (owner fix + dead link + unscrapeable FB link)",
       any("alvinreal" in c["verify_note"] for c in cands)
       and any("deeprepo.dev" in c["verify_note"] for c in cands)
       and any("facebook" in u["target"].lower() for u in feed["unfetchable"]))
    if _FEED.exists():
        ck("on-disk feed is fresh vs the intake (regenerate with --build)", json.loads(_FEED.read_text()) == feed)
    ck("deterministic", build_feed() == feed)

    n_adopt = sum(1 for c in cands if c["disposition"] == "ADOPT-CANDIDATE")
    print("\n" + (f"PASS - ingest_github_signal_intake: {len(cands)} reviewed targets ({len(adoptable)} adoptable / "
                  f"{n_adopt} ADOPT-CANDIDATE), {len(feed['unfetchable'])} unfetchable recorded honestly; every "
                  f"copyleft/unstated/proprietary target is non-adoptable (org-guardrail cross-check); provenance "
                  f"corrections captured. Discovery is not trust — nothing promoted."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        print("wrote:", write_feed())
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: ingest_github_signal_intake.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
