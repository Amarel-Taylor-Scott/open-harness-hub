"""Open Harness Hub — context-compression processors (Baltor enrichment tier).

This package holds the deterministic implementations behind the
`catalog/processors/compression/` manifests — the *Compressed* tier of the
Baltor service (see `docs/strategy/context-enrichment-service.md`).

Each manifest's `implementations[].path` resolves to a `run(...)` callable here.

Modules:
  structural_compress  — backs processor/structural-compress
                         (process_kind compress.structural): strip code bodies,
                         keep signatures + structure (Repomix-style), for
                         Python and JS/TS, degrading gracefully on other text.
"""
