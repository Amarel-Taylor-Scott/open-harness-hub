"""OpenHubForAI — the verified-context PIPELINE package (the north-star payoff).

This package is the one place where the four shipped milestones of the
verified-context wave (``docs/codex/north-star.md``) are TIED TOGETHER into a
single runnable product flow, instead of four modules that each prove themselves
in isolation:

  * **M1 — assurance** (``scripts.processors.assurance``): is this internal claim
    *poisoned* (unsigned supersession / contradicts the authority) and is it
    *independently corroborated* (>= 2 distinct publishers)?
  * **M2 — sanctions freshness** (``scripts.sanctions.sanctions_freshness``): is
    this internal claim still in step with the CURRENT authoritative list, or has
    the list moved underneath it into a would-be VIOLATION?
  * **M3 — serve** (``scripts.enrichment.serve`` + ``scripts.enrichment.tier_pipeline``):
    render the governed corpus into the agent consumption surfaces (``llms.txt`` +
    MCP descriptor) at raw / compressed / hyper-efficient tiers, each carrying a
    MEASURED fidelity from a *separate* evaluator.

The thesis it demonstrates (``docs/codex/north-star.md``): **OHH is the open
funnel; verified context is the business; the wedge is "we verify your docs are
RIGHT, not just current."** A faithfulness-only RAG stack retrieves a stale
internal control faithfully and is exactly wrong; this flow catches the
lag/contradiction against the live source of truth, corroborates it, and only then
serves it — with every flag and its provenance attached.

Modules:
  verified_context_flow — ``run(source_records, internal_claims, peer_sources=None)``
                          composes M1-M4 into ONE governed bundle:
                          ``{served, verification_report, summary}``.

Honest scope (the seams are INHERITED, not introduced here): the live OFAC/BIS/EU
feed (M2's ``ingest.sanctions_feed`` connector), the live MCP wire + per-request
meter + CDC re-serve (M3's ``serve`` seams), the learned-compression / memory /
cache hyper-efficient mechanisms (M3's ``tier_pipeline`` seams), and the live
model route + CI publish gate (M4) are all SEAMS owned by the milestones this
package composes. This flow touches no network and invents no metric: it is a
pure, deterministic function of the records and claims it is HANDED.

Public entrypoint:
    from scripts.pipeline.verified_context_flow import run
"""
