# Supermemory — Candidate Provider (what we borrow, what we refuse)

Supermemory (github.com/supermemoryai/supermemory, MIT, #1 on LongMemEval/LoCoMo/ConvoMem) is "the memory
and context layer for AI." Baltor adopts its **shape** as a **candidate provider behind ports** — and
explicitly **refuses** the parts that break governance. Full positioning: `docs/research/supermemory.md`.
Reference clone: `_reference/supermemory` (read-only; **never** import, execute, npm/pip-install, or call out).

## Purpose

Make Supermemory's strong context primitives available to Baltor **without making Supermemory the source of
truth.** It is cataloged `status=candidate`, sits behind `MemoryProviderPort`/`MemoryMCPProviderPort`, and is
fronted by a deterministic offline emulator so the correctness invariant runs with **no credentials**.

## Owner

- Candidate stubs: `src/baltor/adapters/memory/supermemory_api.py` (developer API),
  `src/baltor/adapters/memory/supermemory_mcp.py` (the `memory`/`recall`/`context` MCP tools).
- Offline stand-in: `src/baltor/adapters/memory/supermemory_emulator.py`.
- Catalog entries (added by MAIN during integration): `memory.supermemory_api@candidate` +
  `mcp.supermemory@candidate` in `architecture/external_capability_catalog.json`, mirrored in
  `architecture/repo_replacement_matrix.json`.

## What we borrow (behind ports, verify-first, NEVER as runtime)

1. **Governed User-Profile projection** — `profile.static` (long-term) + `profile.dynamic` (recent) as a
   **candidate** projection (one call). Highest-value borrow; modeled in `MemoryProfile.v1`. In Baltor,
   `static` is *candidate* long-lived memory — **not** a promoted fact; promotion happens only downstream.
2. **Hybrid recall shape** — `searchMode: hybrid|memories|documents` surfaced on `MemorySearchRequest`.
3. **The Documents-vs-Memories framing** — reused as Baltor's "governed-context (provable) vs RAG
   (stateless recall)" narrative; the assurance axis, not the recall axis.
4. **Connector breadth** — GDrive/Gmail/Notion/OneDrive/GitHub/Web Crawler validate + extend the
   `SourceAdapterPort` ingestion roadmap; each cataloged as a **candidate** connector behind the port.
5. **MCP + plugin distribution** — expose governed-context tools where Supermemory is consumable (we already
   have `catalog/adapters/gateway/mcp-server-bridge`).

## What we refuse (the governance lines)

- **"Intelligent forgetting" / auto-forget** — a *liability* in compliance. Baltor's **lossless-distillation
  law** (`docs/codex/lossless-distillation.md`): omitted/held-out `!=` deleted; raw + lineage + held-out +
  rejected + `rollback_target` are always preserved. Every `MemoryArtifact` and `MemoryTrace` carries them.
- **Recency-only contradiction resolution (`isLatest`)** — replaced by Baltor's deterministic reconciliation
  by **authority + receipt** (Reg E's 10 days beats a newer FAQ's 30 days; the loser is *held out*, not
  forgotten). Recency `!=` correctness.
- **"Derives" served as fact** — an inference without a source handle is exactly what Baltor **holds out**.
  If the Updates/Extends/Derives vocabulary is ever adopted, **Derives maps to `held_out`/`candidate`,
  never a served fact**.
- **Storing facts without source handles** — every artifact requires `external_source_handle` + `lineage`.
- **The TS/Cloudflare runtime** — Baltor is a stdlib-Python governed runtime; the candidate is `_reference/`
  + a cataloged candidate only.

## Contracts

- Implements `MemoryProviderPort` (api) / `MemoryMCPProviderPort` (mcp). Outputs MUST be candidate
  `MemoryArtifact`s (`claim_status="candidate"` + `external_source_handle` + `lineage`).
- With **no credentials** (the correctness invariant), every operation raises `UnavailableProvider` naming
  `env://SUPERMEMORY_API_KEY` (a ref, never a value). `status()` reports `unavailable` without raising.
- Cataloged `status=candidate` with a declared fallback/stub and a `contract_tests` list a replacement must
  keep green — asserted by `scripts/check_supermemory_candidate_catalog.py`.

## Inputs / Outputs

Same as the port (see `docs/memory/overview.md`): write/search/profile requests in; candidate
`MemoryArtifact`s out — or `UnavailableProvider` when no creds. No network I/O in any tracked build.

## Proofs

- `scripts/check_supermemory_emulator.py` — the offline emulator honors the contract with no creds.
- `scripts/check_supermemory_candidate_catalog.py` — cataloged candidate (+ fallback + contract_tests),
  never active.
- `scripts/check_no_direct_supermemory_imports.py` — nothing imports the supermemory SDK/package.
- `scripts/check_supermemory_no_truth_bypass.py` — no path lets a Supermemory recall serve as canonical truth.
- `scripts/check_memory_provider_full_stack.py` — the candidate stubs fail closed in the full motion.

## Commands

```bash
python3 scripts/check_supermemory_candidate_catalog.py --self-test
python3 scripts/check_supermemory_emulator.py --self-test
python3 scripts/check_no_direct_supermemory_imports.py --self-test
python3 scripts/check_supermemory_no_truth_bypass.py --self-test
```

## Limitations

- The candidate stubs never reach network — even with a key set, they raise a clear not-implemented
  `UnavailableProvider` so no one believes a live call happened.
- We do not (and will not) out-distribute or out-recall Supermemory; Baltor competes on the **assurance**
  axis (provable, governed, auditable context), not frictionless personal recall.

## Next

- Wire a real impl behind the candidate surface only if/when warranted — output contract is unchanged.
- Catalog the connectors as `SourceAdapterPort` candidates; stand up `GovernedContextBench` (assurance, not
  recall) as the credibility flywheel on Baltor's axis.

One-liner: **Supermemory remembers you; Baltor can prove what it served, why, from where, and how to roll it
back.**
