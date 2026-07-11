# Example: migrant-worker safety as a generic-catalog instance

This folder walks through how the DueCare safety ecosystem (the
reference repo at `_reference/gemma4_comp/`) maps onto the
industry-agnostic taxonomy in this hub.

## Mapping DueCare → hub components

| DueCare concept | Hub component | Notes |
|---|---|---|
| Expert-role block (40-year anti-trafficking expert) | `action/research-analyst` + a humanitarian-specific subclass (TBA) | The Action stays generic; trafficking specifics live in the Knowledge Corpus. |
| GREP_RULES (100+ regex) | `if-statement/grep/trafficking-recruitment-fraud` (TBA) | One If Statement per risk family. |
| RAG_CORPUS (50+ docs) | `knowledge-corpus/ilo-statutes-and-typologies` (TBA) | Provenance: ILO, UNODC, FATF. |
| `_citations.json` | `knowledge-corpus/...` with `content_types: [citation_edge]` | Citation graph as a typed leaf. |
| `_TOOL_DISPATCH` | One `tool/...` component per function-call | Each tool gets a JSON-schema parameters block. |
| `_contacts.json` | `knowledge-corpus/...` with `content_types: [contact_directory]` | Volatile data — fetched at runtime. |
| `chat` module | `action/text-safety-review` (this hub) + a humanitarian-specific Action that extends it | The generic safety review is reusable across industries. |
| `process` module | `action/bulk-file-review` (TBA) | Bundle/document analyst pattern. |
| `extraction` module | `action/typed-envelope-drafter` (TBA) | Generic structured-output drafter. |
| `anonymization` module | `action/redact-pii-text` (this hub) | Pure deterministic gate. |
| Universal scoring guide | `action/humanitarian-grounded-response` (TBA) | The scoring Action is the comparable unit. |

## Why the generic mapping works

The DueCare repo carefully separated three things:

1. **Generic primitives** — the Action / RAG / GREP / tool pattern.
2. **Volatile facts** — phone numbers, fee caps, current advisories
   (in tools or Knowledge Corpora).
3. **Stable structure** — refusal style, evidence-first response shape,
   ILO indicator categories (in Actions).

This separation is exactly what the hub's taxonomy enforces. The
DueCare repo is a fully-worked migrant-safety instance of the generic
shapes in this hub.

## Building this instance

To rebuild the migrant-safety instance from this hub:

1. Add a humanitarian expert-role Action that extends
   `action/research-analyst` (`action/anti-trafficking-expert`).
2. Add a Knowledge Corpus of ILO statutes and trafficking typologies
   (`knowledge-corpus/ilo-statutes-and-typologies`).
3. Add GREP If Statements per risk family
   (`if-statement/grep/recruitment-fraud`,
   `if-statement/grep/passport-retention`, …).
4. Add tools for hotline/contact lookups
   (`tool/lookup-hotline-by-country`).
5. Compose them into a pipeline
   (`pipeline/migrant-worker-safety-review`).

This is left as an exercise; the hub provides the substrate.
