"""src.teleon.seeds.api_and_feed_seeds — governed seeds distilled from the 2026-06-20 repo batch + the owner's
API-hub / feed-intake asks. Learn-from-them, clean-room: drop-in only for clean permissive licenses; technique-only
otherwise. Two are first-class new capabilities:

  * api-hub-intake — catalog + use API-HUB endpoints (RapidAPI, Nokia Network-as-Code / CAMARA, other hubs) per
    capability need, governed: each endpoint is a CANDIDATE with auth + cost + a port; the actual call happens
    behind the inference/egress ports, never here. The "constant stream of new tools/APIs" rail, governed.
  * governed-feed-intake — ingest a social/repo FEED (e.g. a DeepRepo page) via LEGITIMATE paths only (official
    API, owner-pasted export, RSS). It REFUSES ToS-violating scraping + PII harvesting by policy, and LOGS an
    inaccessible source honestly (the established `unfetchable` pattern) rather than evading anti-bot protections.

Every runner is real; serves_truth is forced False by the framework; nothing here is promoted.
"""
from __future__ import annotations

from src.teleon.seeds.capability_seed import CapabilitySeed, SeedResult, register

_DUE = "github-signal repo batch 2026-06-20"

#: feed access methods the governed intake ALLOWS (legitimate) vs REFUSES (ToS-violating / PII-harvesting).
_ALLOWED_ACCESS = ("official_api", "owner_paste", "rss", "public_export")
_REFUSED_ACCESS = ("scrape_tos_protected", "anti_bot_evasion", "bulk_pii_harvest")


# ── 1. cc-desktop-switch (MIT, drop-in) → provider-allowlist inference gateway ───────────────────────────────
def _provider_allowlist(p: dict | None) -> SeedResult:
    p = p or {}
    allow = {str(k): str(v) for k, v in (p.get("mapping") or {}).items()}
    req = str(p.get("requested", ""))
    routed = allow.get(req)
    return SeedResult(output={"requested": req, "routed_to": routed, "allowed": routed is not None,
                              "note": "explicit mapping only; an unmapped route is REJECTED (no implicit egress)"},
                      provenance="clean-room provider-allowlist gateway (technique from cc-desktop-switch)")


register(CapabilitySeed(
    slot="provider-allowlist-gateway", intent="Route an inference request only to an explicitly mapped provider; reject unmapped.",
    learned_from="lonr-6/cc-desktop-switch", source_license="MIT", category="other",
    determinism_ceiling=1.0, adoptable=True,
    lesson="an allow-list gateway (explicit route mapping, reject-unmapped) is the right default for multi-provider routing — it mirrors our OIPS plane + the jurisdiction guard for non-US lanes.",
    runner=_provider_allowlist))


# ── 2. arcane (BSD-3, drop-in) → container-lifecycle control behind the ExecutionProviderPort ────────────────
def _container_lifecycle(p: dict | None) -> SeedResult:
    p = p or {}
    action = str(p.get("action", "list"))
    valid = action in ("list", "start", "stop", "logs", "compose_up", "compose_down")
    return SeedResult(output={"action": action, "valid": valid, "target": p.get("target"),
                              "note": "bounded container ops behind ExecutionProviderPort; receipts record the actual backend"},
                      provenance="clean-room container-lifecycle control (UX technique from arcane)")


register(CapabilitySeed(
    slot="container-lifecycle-panel", intent="Bounded container lifecycle ops (list/start/stop/logs/compose) behind a port.",
    learned_from="getarcaneapp/arcane", source_license="BSD-3-Clause", category="other",
    determinism_ceiling=1.0, adoptable=True,
    lesson="container-control UX maps onto our ExecutionProviderPort + Control Tower; study the UX, keep ops bounded + receipted (don't fork the app).",
    runner=_container_lifecycle))


# ── 3. google-maps-scraper (MIT, learn) → API-FIRST geo-business intake (NOT scraping) ───────────────────────
def _places_api_intake(p: dict | None) -> SeedResult:
    p = p or {}
    return SeedResult(output={"query": p.get("query", ""), "access": "official_places_api",
                              "pii_policy": "public business metadata only; no personal contact harvesting",
                              "note": "use the official Places API; the scraping path is REFUSED (Google ToS + PII)"},
                      provenance="clean-room geo-business intake — API-first, PII-gated (scraping path declined)")


register(CapabilitySeed(
    slot="places-api-intake", intent="Look up public business listings via the official Places API (not by scraping Maps).",
    learned_from="omkarcloud/google-maps-scraper", source_license="MIT", category="identity-compliance",
    determinism_ceiling=0.9, adoptable=True, drop_in=False,
    lesson="the scraper's VALUE is the data shape, not the method — adopt the official Places API + a PII gate; scraping a ToS-protected platform + harvesting contact PII is declined by policy.",
    runner=_places_api_intake))


# ── 4. awesome-legal-skills (CC-BY-NC-ND, learn) → clean-room legal capability taxonomy (gap signal only) ─────
def _legal_gap_taxonomy(p: dict | None) -> SeedResult:
    cats = ["contract-review", "privacy-gdpr", "compliance", "employment", "corporate", "legal-methodology"]
    return SeedResult(output={"legal_capability_categories": cats,
                              "note": "TAXONOMY/gap signal only; NC-ND blocks reuse of their content — clean-room each "
                              "capability from PRIMARY legal sources (statutes/regs + signed publishers), never their text"},
                      provenance="clean-room legal gap taxonomy (intel only; no content reuse)")


register(CapabilitySeed(
    slot="legal-gap-taxonomy", intent="A clean-room map of legal capability categories to seed from PRIMARY sources.",
    learned_from="lawve-ai/awesome-legal-skills", source_license="CC-BY-NC-ND-4.0", category="identity-compliance",
    determinism_ceiling=1.0, adoptable=False, drop_in=False,
    lesson="NC-ND forbids commercial use + derivatives → use it ONLY as a gap/taxonomy signal for the legal beachhead; build each capability clean-room from statutes/regs + signed publishers, governed (not 'ask the model').",
    runner=_legal_gap_taxonomy))


# ── 5. NEW: api-hub-intake — catalog + use API-hub endpoints per capability need (governed) ──────────────────
def _api_hub_intake(p: dict | None) -> SeedResult:
    p = p or {}
    need = str(p.get("capability_need", ""))
    # representative governed endpoint candidates per need (the actual call is behind the inference/egress port).
    hub_map = {
        "whois": [{"endpoint": "rdap.org", "hub": "direct", "auth": False, "cost": "free"}],
        "telecom-location": [{"endpoint": "Nokia Network-as-Code / CAMARA location-verification", "hub": "rapidapi/nokia", "auth": True, "cost": "per_call"}],
        "sim-swap": [{"endpoint": "CAMARA sim-swap", "hub": "rapidapi/nokia", "auth": True, "cost": "per_call"}],
        "places": [{"endpoint": "Google Places API", "hub": "google", "auth": True, "cost": "per_call"}],
    }
    candidates = hub_map.get(need, [])
    return SeedResult(output={"capability_need": need,
                              "endpoint_candidates": [dict(c, governed="candidate", serves_truth=False) for c in candidates],
                              "note": "API-hub endpoints are CANDIDATES; the call happens behind the inference/egress "
                              "port with auth + cost governed; track fastest/cheapest/most-reliable per need"},
                      provenance="governed API-hub endpoint catalog (RapidAPI / Nokia CAMARA / direct)")


register(CapabilitySeed(
    slot="api-hub-intake", intent="Catalog + govern API-hub endpoints (RapidAPI/Nokia CAMARA/etc.) per capability need.",
    learned_from="owner ask: RapidAPI + Nokia API-hub usage", source_license="n/a (capability)", category="other",
    determinism_ceiling=0.95, adoptable=True, drop_in=False,
    lesson="an API hub is a constant stream of new tools — govern it: each endpoint is a candidate with auth+cost+a port, tracked for fastest/cheapest/most-reliable, the call never made here. Extends the provider-endpoint registry.",
    runner=_api_hub_intake))


# ── 6. NEW: governed-feed-intake — ingest a feed via LEGITIMATE paths; refuse ToS-violating scraping ─────────
def _governed_feed_intake(p: dict | None) -> SeedResult:
    p = p or {}
    source = str(p.get("source", ""))
    method = str(p.get("access_method", ""))
    if method in _REFUSED_ACCESS:
        return SeedResult(output={"source": source, "access_method": method, "refused": True,
                                  "reason": "ToS-violating scraping / anti-bot evasion / bulk PII harvest is declined "
                                  "by policy; use official_api / owner_paste / rss / public_export instead",
                                  "unfetchable_logged": True},
                          provenance="policy gate: refused ToS-violating intake (logged honestly, not evaded)")
    if method not in _ALLOWED_ACCESS:
        return SeedResult(output={"source": source, "access_method": method or "(none)", "fetched": False,
                                  "unfetchable_logged": True,
                                  "note": "no legitimate access method given; recorded as unfetchable (e.g. a Facebook "
                                  "page with no API access) — the owner pastes the content or provides API creds"},
                          provenance="honest unfetchable log (no legitimate path) — never fabricated")
    items = [{"text": str(it), "trusted": False} for it in (p.get("items") or [])][:50]
    return SeedResult(output={"source": source, "access_method": method, "fetched": True,
                              "candidate_items": items, "n": len(items),
                              "note": "ingested via a legitimate path; items are UNTRUSTED candidates (discovery!=trust) "
                              "that feed the governed intake, never served as truth"},
                      provenance="governed feed intake via a legitimate path")


register(CapabilitySeed(
    slot="governed-feed-intake", intent="Ingest a social/repo feed via legitimate paths only; refuse ToS-violating scraping.",
    learned_from="owner ask: feed intake from pages like facebook.com/DeepRepo", source_license="n/a (capability)",
    category="research", determinism_ceiling=0.9, adoptable=True, drop_in=False,
    lesson="the goal (a constant stream of new capabilities from feeds) is served by LEGITIMATE access (official API / owner-paste / RSS) + an honest unfetchable log — NOT by evading a platform's anti-scraping or harvesting others' PII (declined by policy).",
    runner=_governed_feed_intake))
