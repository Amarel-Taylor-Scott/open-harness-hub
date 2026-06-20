# Adapter contract (swappable backend infra)

Baltor domain code depends on a **capability** (a `*Provider` port), never on a vendor SDK. Each
capability has a **primary + fallback** (verified, OSS-first — `data/backend-tools.yaml`), and the
vendor lives behind an adapter that can be swapped without touching domain logic.

## The contract
A backend adapter declares its capability + how it runs, and is **real or a labeled SEAM**:
- **Real** behavior is proven by an offline, deterministic self-test against a `Canned*` fixture.
- The **live** path (network / heavy dependency / credentials) is reached via a `--live` flag or a
  lazy import; when the dependency/creds are absent it **raises a clear seam error** (naming the
  install / the boundary) — it never fakes a result.

## Shipped examples (the pattern to copy)
- **Fetcher** (`scripts/foundry/scrapers.py`): `HttpFetcher` (live) / `CannedFetcher` (offline).
  Used by `sanctions_feed_live`, `ecfr_feed`, `federal_register_feed` — each: fetch → parse →
  `content_hash` + lineage → `changed_since` CDC; offline self-test + `--live`.
- **ParserProvider** (`scripts/ingest/parser_provider.py`): `DoclingParser` (live, lazy-imports
  docling, labeled seam when absent) / `CannedParser` (offline default). Swap LiteParse/Unstructured
  behind the same `parse(raw) -> {"pages":[blocks]}` interface.

## Capability ports (target set)
`ParserProvider` · `RetrievalProvider` · `GraphProvider` · `WorkflowEngineProvider` ·
`PolicyProvider` · `ObservabilityProvider` · `SandboxProvider` · `ScrapingProvider` ·
`RepoDirectoryProvider` · `ApiCatalogProvider`. Primary/fallback per port: `data/backend-tools.yaml`.

## Rules
- A new adapter requires: the capability it satisfies, license/hosting, an offline self-test, and a
  declared fallback for its capability.
- Domain modules must not `import` a vendor SDK at top level — import lazily inside the adapter.
- Do not reintroduce flagged tools (Synapse AI, Microsoft Conductor as a durable engine, Kuzu) —
  see `research/backend-tool-verification.md` §2.
