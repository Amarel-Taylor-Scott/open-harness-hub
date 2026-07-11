"""OpenHubForAI — the SANCTIONS BEACHHEAD (the verified-context wedge, made real).

This package is the first concrete instance of the north-star wedge
(``_repos/_shared/codex/north-star.md``, ``_repos/_shared/strategy/positioning-v2.md``): *"we verify
your docs are RIGHT against the source of truth, not just current."* Sanctions
screening is the sharpest possible demo of it because the cost of being stale is
asymmetric and legal — an internal control that says an entity is **clear** while
the current OFAC SDN / BIS Entity List / EU consolidated list has just **added**
that entity is not a typo, it is a would-be sanctions violation. A
faithfulness-only RAG stack retrieves the internal doc faithfully and is exactly
wrong; the value is in catching the *lag/contradiction against the live list*,
which no amount of model scale fixes (the list changed yesterday — that is a
``channel_inaccessibility`` / volatile-source **structural** lift in the
``scripts.eval.reason_codes`` taxonomy, not a transient one).

Modules:
  sanctions_freshness — the beachhead end-to-end. A small **SYNTHETIC** fixture of
                        OFAC-SDN-like entries (clearly synthetic, NOT real
                        persons/entities) stands in offline for the real feeds,
                        plus the REAL deterministic logic:
                          * ``parse_list``         — records -> a normalized index
                            (provenance + version captured).
                          * ``freshness_diff``     — old vs new list ->
                            {added, removed, changed} with the version delta.
                          * ``flag_stale_context`` — verdict (current / stale /
                            contradicted) + provenance for an internal claim that
                            references an entity/threshold/list_version.

Honest scope (the seam): the records here are a synthetic stand-in. The **live**
OFAC SDN / BIS / EU consolidated feeds wire in through the connector/ingest layer
— that fetch is a SEPARATE component (``side_effects: external_call``,
``trust_boundary: external``); everything in this package is a pure, deterministic
function of the records it is HANDED, which is what keeps the freshness logic
auditable and reproducible. No network is touched here.
"""
