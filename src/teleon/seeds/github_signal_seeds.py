"""src.teleon.seeds.github_signal_seeds — one governed capability seed per repo from the 2026-06-20 GitHub-signal
review (docs/research/github-signal-intake-2026-06-20.md). Each is what we LEARNED from the repo, implemented
clean-room: drop-in where the license is permissive, technique-only where it is copyleft/unstated/proprietary.
Every runner is real (no placeholder) and serves_truth is forced False by the framework. Nothing here is promoted.
"""
from __future__ import annotations

from datetime import date, timedelta

from src.teleon.seeds.capability_seed import CapabilitySeed, SeedResult, register

_DUE = "github-signal-intake-2026-06-20"


# ── 1. openclaw-marketing-skills (MIT, drop-in) → a deterministic marketing-brief Action ─────────────────────
def _marketing_brief(p: dict | None) -> SeedResult:
    p = p or {}
    product, audience, goal = p.get("product", "the product"), p.get("audience", "buyers"), p.get("goal", "signups")
    brief = {
        "hook": f"Stop guessing — {product} gets {audience} to {goal}.",
        "value_prop": f"{product} removes the friction between {audience} and {goal}.",
        "cta": f"Start with {product} today.",
        "channels": ["email", "seo", "paid-social"],
    }
    return SeedResult(output=brief, provenance="clean-room marketing-skill template (content-only; no tool calls)")


register(CapabilitySeed(
    slot="marketing-copy-brief", intent="Generate a structured marketing brief (hook/value-prop/CTA/channels).",
    learned_from="LeoYeAI/openclaw-marketing-skills", source_license="MIT", category="productivity",
    determinism_ceiling=0.9, adoptable=True,
    lesson="battle-tested marketing-skill STRUCTURE (CRO/copy/SEO) encodes cleanly as a deterministic content Action — no tool calls, so it is safe to drop in for a non-regulated domain.",
    runner=_marketing_brief))


# ── 2. konbakuyomu/smartsearch (MIT, drop-in but gated) → a port-bounded source-discovery candidate ──────────
def _source_discovery(p: dict | None) -> SeedResult:
    p = p or {}
    query = p.get("query", "")
    terms = [t for t in query.replace(",", " ").split() if t]
    candidates = [{"query_intent": query, "search_term": t, "fetched": False, "trusted": False} for t in terms[:8]]
    return SeedResult(output={"candidate_sources": candidates, "note": "real fetch is behind a tool-adapter port; "
                              "any fetched page is an UNTRUSTED candidate that must pass the source-authority rail"},
                      provenance="clean-room source-discovery port (decomposes intent; never fetches truth)")


register(CapabilitySeed(
    slot="web-source-discovery", intent="Decompose a research query into candidate source-search intents (port-bounded).",
    learned_from="konbakuyomu/smartsearch", source_license="MIT", category="research",
    determinism_ceiling=0.4, adoptable=True,
    lesson="CLI source-discovery belongs BEHIND a tool-adapter port: results are untrusted candidates, never served as facts — the verification/source-authority rail is the difference.",
    runner=_source_discovery))


# ── 3. agentic-in/inferoa (Apache, FOIL) → a deterministic prefix-cache + token-budget routing policy ─────────
def _route_inference(p: dict | None) -> SeedResult:
    p = p or {}
    models = p.get("models", [])                      # [{id, cost, ctx, cache_hit(bool)}]
    need = int(p.get("prompt_tokens", 0))
    capable = [m for m in models if int(m.get("ctx", 0)) >= need]
    # cheapest capable; prefer a warm prefix-cache on ties (the borrowed inferoa technique)
    ranked = sorted(capable, key=lambda m: (round(float(m.get("cost", 1.0)), 6), not bool(m.get("cache_hit")), m.get("id", "")))
    pick = ranked[0]["id"] if ranked else None
    return SeedResult(output={"picked": pick, "reason": "cheapest capable model within the token budget, prefix-cache "
                              "preferred on ties", "considered": [m.get("id") for m in capable]},
                      provenance="clean-room routing policy (technique borrowed from inferoa; NOT its runtime)")


register(CapabilitySeed(
    slot="inference-prefix-cache-routing", intent="Pick the cheapest capable model within a token budget, cache-preferring.",
    learned_from="agentic-in/inferoa", source_license="Apache-2.0", category="other",
    determinism_ceiling=1.0, adoptable=False, drop_in=False,
    lesson="inferoa is a FOIL (another agent runtime = our non-goal); we take only the prefix-cache + token-budget ROUTING technique and fold it into OIPS as a policy — we govern+route, we don't run their loop.",
    runner=_route_inference))


# ── 4 & 5. awesome-autoresearch / awesome-codex-cli (CC0 scout lists) → governed candidate-intake seeds ───────
def _scout_intake(p: dict | None) -> SeedResult:
    p = p or {}
    items = p.get("items", [])
    rows = [{"slot": str(i).strip().lower().replace(" ", "-"), "screen_status": "unscreened",
             "serves_truth": False} for i in items if str(i).strip()]
    return SeedResult(output={"candidate_intake": rows, "note": "a curated list is a SCOUT FEED; each item needs its "
                              "own license + gap/lift intake before it is anything but a candidate"},
                      provenance="clean-room scout-feed → governed candidate intake")


register(CapabilitySeed(
    slot="autoloop-scout-intake", intent="Turn a curated list of self-improving-loop systems into governed candidate-intake rows.",
    learned_from="webfuse-com/awesome-autoresearch", source_license="CC0-1.0", category="research",
    determinism_ceiling=1.0, adoptable=False, drop_in=False,
    lesson="the propose→evaluate→keep/revert pattern IS our 'agents propose, Baltor disposes'; a curated awesome-list is a discovery funnel → scout feed, never auto-trusted (owner corrected: webfuse-com, not alvinreal).",
    runner=_scout_intake))

register(CapabilitySeed(
    slot="codex-cli-scout-intake", intent="Turn the Codex-CLI tools index into governed candidate-intake rows.",
    learned_from="RoggeOhta/awesome-codex-cli", source_license="CC0-1.0", category="research",
    determinism_ceiling=1.0, adoptable=False, drop_in=False,
    lesson="an awesome-list is a per-item intake queue, not a bulk import — downstream items are mixed-license (incl. GPL); Codex is already a governed inference lane here.",
    runner=_scout_intake))


# ── 6 & 7. discover-legal/BigLaw (AGPL → clean-room) → a legal-source registry + a DETERMINISTIC deadline calc ─
def _legal_source_catalog(p: dict | None) -> SeedResult:
    catalog = [
        {"source": "CourtListener", "authority_tier": "official", "license": "US public domain"},
        {"source": "EUR-Lex / CELLAR", "authority_tier": "official", "license": "CC-BY"},
        {"source": "HUDOC (ECtHR)", "authority_tier": "official", "license": "open"},
        {"source": "UK Find Case Law", "authority_tier": "official", "license": "Open Justice Licence"},
    ]
    return SeedResult(output={"legal_sources": catalog, "note": "authority-tiered; we ADD the verification + "
                              "source-authority + freshness layer BigLaw lacks"},
                      provenance="clean-room legal-source registry (no AGPL code; sources are public/open)")


def _court_deadline(p: dict | None) -> SeedResult:
    """DETERMINISTIC court-deadline calc: filing_date + N days, rolled FORWARD off weekends (FRCP-style)."""
    p = p or {}
    try:
        d = date.fromisoformat(str(p.get("filing_date", "2026-06-19")))
    except ValueError:
        d = date(2026, 6, 19)
    n = int(p.get("rule_days", 0))
    due = d + timedelta(days=n)
    while due.weekday() >= 5:           # Sat(5)/Sun(6) → roll forward to the next business day
        due += timedelta(days=1)
    return SeedResult(output={"filing_date": d.isoformat(), "rule_days": n, "deadline": due.isoformat(),
                              "rolled_off_weekend": due != d + timedelta(days=n),
                              "note": "holidays not modeled in v1 (jurisdiction calendar is a follow-on)"},
                      provenance="deterministic If-Statement (weekend roll-forward); never model-guessed")


register(CapabilitySeed(
    slot="legal-source-registry", intent="A governed, authority-tiered registry of public legal-data sources.",
    learned_from="discover-legal/BigLaw", source_license="AGPL-3.0", category="identity-compliance",
    determinism_ceiling=1.0, adoptable=True, drop_in=False,
    lesson="BigLaw's 32 connectors → learn the SOURCE LIST, not the AGPL code; a governed legal-source registry with authority tiers is the clean-room takeaway for the legal beachhead.",
    runner=_legal_source_catalog))

register(CapabilitySeed(
    slot="court-deadline-calculator", intent="Compute a court deadline deterministically (date + rule-days, weekend roll).",
    learned_from="discover-legal/BigLaw", source_license="AGPL-3.0", category="identity-compliance",
    determinism_ceiling=1.0, adoptable=True, drop_in=False,
    lesson="a court-deadline calc MUST be a deterministic If-Statement (FRCP/CPR rules), never a model guess — BigLaw validates the need; this is exactly our determinism thesis (clean-room, no AGPL code).",
    runner=_court_deadline))


# ── 8. jaytel0/taste (unstated → clean-room) → a skill-synthesis template ────────────────────────────────────
def _skill_synthesis(p: dict | None) -> SeedResult:
    p = p or {}
    attrs = p.get("attributes", [])
    skill_md = {"name": p.get("name", "synthesized-skill"), "when_to_use": "matches the reference attributes",
                "attributes": list(attrs), "format": "SKILL.md"}
    return SeedResult(output={"skill": skill_md, "note": "structures PROVIDED attributes deterministically; the "
                              "vision-extraction stage is a separate candidate (its output is never truth)"},
                      provenance="clean-room skill-synthesis template (unstated upstream license → no code reuse)")


register(CapabilitySeed(
    slot="skill-synthesis-from-attributes", intent="Synthesize a SKILL.md from provided reference attributes.",
    learned_from="jaytel0/taste", source_license="unstated", category="productivity",
    determinism_ceiling=0.7, adoptable=False, drop_in=False,
    lesson="reference-refs → reusable SKILL.md is a real pattern, but an UNSTATED license forbids vendoring → clean-room only; split the vision-extraction (candidate) from the deterministic structuring.",
    runner=_skill_synthesis))


# ── 9. deeprepo (.ai dead → .dev) → a repo-architecture extraction candidate ─────────────────────────────────
def _repo_architecture(p: dict | None) -> SeedResult:
    p = p or {}
    files = [f for f in p.get("files", []) if isinstance(f, str)]
    modules: dict[str, int] = {}
    for f in files:
        top = f.split("/")[0] if "/" in f else "(root)"
        modules[top] = modules.get(top, 0) + 1
    summary = sorted(({"module": k, "files": v} for k, v in modules.items()), key=lambda m: (-m["files"], m["module"]))
    return SeedResult(output={"architecture": summary, "note": "a comprehension AID; the map is a candidate, "
                              "never trusted; deeprepo.ai is dead → product lives at deeprepo.dev"},
                      provenance="clean-room repo-architecture summary (deterministic dir grouping)")


register(CapabilitySeed(
    slot="repo-architecture-extraction", intent="Summarize a repo's module/dir architecture from a file list.",
    learned_from="deeprepo.dev", source_license="n/a", category="data-extraction",
    determinism_ceiling=1.0, adoptable=False, drop_in=False,
    lesson="repo-comprehension is a discovery aid; the architecture map is a candidate, not truth — and verify the live domain (the shared .ai is dead; product is .dev).",
    runner=_repo_architecture))


# ── 10. tantara/openbrief (AGPL, AVOID) → commodity ASR component, recorded honestly ─────────────────────────
def _local_asr(p: dict | None) -> SeedResult:
    return SeedResult(output={"capability": "local_asr_transcription", "status": "commodity",
                              "note": "declared as a pre-LLM component behind a provider port; AVOID the AGPL app, "
                              "no durable gap to differentiate on"},
                      provenance="port declaration only (commodity; not a differentiator)")


register(CapabilitySeed(
    slot="local-asr-transcription", intent="Declare local ASR as a commodity pre-LLM component behind a provider port.",
    learned_from="tantara/openbrief", source_license="AGPL-3.0", category="other",
    determinism_ceiling=0.0, adoptable=False, drop_in=False,
    lesson="openbrief is AVOID (AGPL + off-thesis consumer app); the only takeaway is that on-device ASR is COMMODITY with no durable capability gap — record it, don't build on it.",
    runner=_local_asr))


# ── 11. engineering-management/awesome-engineering-management (out of scope) → honest no-op ───────────────────
def _no_capability(p: dict | None) -> SeedResult:
    return SeedResult(output={"capability": None, "reason": "engineering-management reading list — no AI capability "
                              "to seed; recorded as catalogued-not-seeded"},
                      provenance="honest no-op (not every shared repo yields a capability)")


register(CapabilitySeed(
    slot="eng-management-out-of-scope", intent="Record an out-of-scope repo honestly (no capability seeded).",
    learned_from="engineering-management/awesome-engineering-management", source_license="CC0-1.0", category="other",
    determinism_ceiling=1.0, adoptable=False, drop_in=False,
    lesson="not every shared repo yields a capability — an honest no-op (catalogued, not fabricated) beats a hollow module; the name is shared by 6+ owners (ambiguous).",
    runner=_no_capability))
