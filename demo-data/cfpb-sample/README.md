# CFPB-sample — Baltor demo corpus (SYNTHETIC, public-safe)

A tiny, deterministic, **synthetic** corpus shaped like a consumer-finance disputes knowledge base
(in the spirit of CFPB complaint/regulation data). **No real PII, no real complaints, no scraped
data** — every file is invented for demonstration. The **live** CFPB connector
(`scripts/demo_cfpb_context_pack.py`) is a separate path that needs network; this bundled sample
lets the demo console animate a **real, offline, deterministic** run over a CFPB-shaped graph.

## Planted facts (on purpose)
1. **A contradiction.** `docs/disputes-faq.md` (stale) says EFT errors get **30 days** to resolve;
   `regs/RegE-error-resolution.md` (the authority) and `sop/dispute_sla.py` say **10 business days**
   (extendable to 45 under conditions). Graph interrogation must pick the regulation as the
   authority, flag the FAQ as stale/superseded, and cite source handles.
2. **Staleness.** The FAQ is `freshness.staleness = "stale"` and `SUPERSEDES`-d by the regulation.

Canonical seed (objects/relationships/assertions, same schemas as `demo-data/acme-billing`):
`seed-graph.json`. `ctx://cfpb-sample/...` handles resolve to the sibling files.
