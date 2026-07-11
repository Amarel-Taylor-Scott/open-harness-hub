"""Baltor enrichment package — the content refinery that turns one governed
object into token-efficiency tiers.

This package composes the *real* shared-backend processors into the three Baltor
tiers described in ``_repos/baltor/context/strategy/context-enrichment-service.md``
(raw → compressed → hyper-efficient). It owns no compression logic of its own:
the tiers are assembled from ``scripts.processors.*`` so the same components the
build/monitor product (OHH) mints are the components the enrichment product
(Baltor) sells — "two services, one shared infra; the join = one governed object,
two doors."

Public entrypoint:
    from scripts.enrichment.tier_pipeline import run
"""
