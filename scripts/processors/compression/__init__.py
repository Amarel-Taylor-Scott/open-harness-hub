"""OpenHubForAI — context-compression processors (Baltor enrichment tier).

This package holds the deterministic implementations behind the
`catalog/processors/compression/` manifests — the *Compressed* tier of the
Baltor service (see `docs/strategy/context-enrichment-service.md`).

Each manifest's `implementations[].path` resolves to a `run(...)` callable here.

Modules:
  structural_compress  — backs processor/structural-compress
                         (process_kind compress.structural): strip code bodies,
                         keep signatures + structure (Repomix-style), for
                         Python and JS/TS, degrading gracefully on other text.
  usage_gated_compress — backs processor/usage-gated-compress
                         (process_kind compress.usage_gated): prediction-error-
                         gated retention (the Friston move) — a usage prior
                         learned from past turns decides per-item FULL/SUMMARY/
                         HANDLE_ONLY fidelity under a budget; cross-turn,
                         model-external, lossless (paged-out items rehydrate on
                         a prediction miss). See
                         docs/concepts/prediction-error-gated-context.md.
"""
