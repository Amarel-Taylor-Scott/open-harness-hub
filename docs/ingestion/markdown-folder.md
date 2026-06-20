# Markdown Folder Ingestion (Obsidian-style vaults, behind SourceAdapterPort)

**Purpose.** Ingest a folder of markdown notes (an Obsidian-style vault) as a SOURCE — not as truth. Each
note flows through the SAME governed path as every other source type: source artifacts → `source_record` →
`source_field` → `atomic_fact` / `narrative_allegation` → (existing) ledger → vector → graph → conflict →
reconcile → verify → optimize → consumption. A note's prose is held out; only its structured frontmatter can
be promotion-eligible, and only when the note marks itself structured.

**Owner.** `src/baltor/adapters/source/markdown_folder.py` (`MarkdownFolderAdapter`, satisfies the existing
`scripts.ingest.source_adapters.SourceAdapter` Protocol; reuses `_artifact` / `_base_handle` / `_sentences`).
**Registry.** `architecture/contract_registry.json#source_types` (`markdown`). **Parser provider.**
`markdown_vault` (local, stdlib line-parse — no yaml dependency).

## Input

Either an in-memory dict `{relpath: text}` (offline fixture) or a filesystem path to a vault folder (real
connector behind the same port). A `.obsidian/` (and `.git/`, `.trash/`) config dir is **ignored** — including
any `.md` file inside it.

## What each note becomes

| Markdown element | Governed artifact | Promotion-eligible? |
|---|---|---|
| the note itself | `source_record` (handle `…#note.<relpath>`) | n/a |
| frontmatter scalar (`key: value`) | `source_field` + `atomic_fact` | **only if** frontmatter marks the note structured (`structured`/`promote`/`promotion_eligible`/`verified` truthy) |
| frontmatter list (`key: [a, b]`) | `source_field` + one `atomic_fact` per item | same rule as scalars |
| note prose (paragraphs → sentences) | `narrative_allegation` (`claim_status=unverified_allegation`) | **never** (a note's claims are not facts) |
| `[[wikilink]]` | `note_links_to` **edge candidate** (in `link_edges` + on the note's `source_record` metadata) | n/a (candidate, not a served edge) |
| `#tag` | recorded on the note's `source_record` metadata (`note_tags`) | n/a |

**Source handle:** `ctx://tenant/<tid>/source/<sid>#note.<relpath>.<field-or-sN>` (public root when the note
is `global_public`).

## Governance (enforced)

- **Note prose is held out.** Every prose sentence is a `narrative_allegation`, `promotion_eligible=false`. A
  note never becomes truth by being written down.
- **Frontmatter is only promotion-eligible when the note says so.** A note without a `structured`/`promote`
  flag produces `atomic_fact`s that are `promotion_eligible=false`.
- **Private vault stays private.** The vault default scope is `tenant_private`. A note is only `global_public`
  when its frontmatter explicitly sets `source_scope: global_public`. A private note never produces a
  `global_public` artifact — no leak.
- Frontmatter `source_authority` is honored per-note (e.g. `official`).
- Every artifact carries a **source handle + content hash + tenant scope + parent lineage**.
- **Deterministic.** Same vault + same injected ingest time → identical artifacts; changing one frontmatter
  field changes only that field's artifact hash. Time is injected (`now=`), not read from the wall clock.
- Produced frontmatter facts are **gate-compatible** (pass the `VerificationGate`); note allegations are held
  out by the gate.

## Commands

```
PYTHONPATH=. python3 scripts/check_ingest_markdown_folder.py --self-test
PYTHONPATH=. python3 -c "from src.baltor.adapters.source.markdown_folder import MarkdownFolderAdapter as A; \
  import json; print(json.dumps(A().ingest('demo-data/markdown-vault', tenant_id='acme', source_id='vault1', now=0)['notes'], indent=2, default=str))"
```

## Fixture

`demo-data/markdown-vault/` — `reg-e-error-resolution.md` (`global_public`, `structured: true`, a wikilink,
Reg-E-style structured fields), `dispute-intake.md` (`tenant_private` prose + wikilink + tags), and a
`.obsidian/` config dir (a JSON config **and** a `.md` cache note) to prove the config dir is ignored.

## Boundaries

This adapter is INGESTION ONLY. It writes governed source artifacts to the existing ledger path; it does not
write served facts, does not introduce a second runtime/bus/parser-framework, and does not edit
`scripts/ingest/source_adapters.py`. Registration of the `markdown` source type (adapter wiring +
`contract_registry.json#source_types`) is applied by the integrating agent.
