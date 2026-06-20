# Example: migrant-worker safety as a generic-catalog instance

This folder walks through how the DueCare safety ecosystem (the
reference repo at `_reference/gemma4_comp/`) maps onto the
industry-agnostic taxonomy in this hub.

## Mapping DueCare → hub artifacts

| DueCare concept | Hub artifact | Notes |
|---|---|---|
| Persona block (40-year anti-trafficking expert) | `persona/research-analyst` + a humanitarian-specific subclass (TBA) | Persona stays generic; trafficking specifics live in the knowledge pack. |
| GREP_RULES (100+ regex) | `rule-pack/grep/trafficking-recruitment-fraud` (TBA) | One rule pack per risk family. |
| RAG_CORPUS (50+ docs) | `knowledge-pack/ilo-statutes-and-typologies` (TBA) | Provenance: ILO, UNODC, FATF. |
| `_citations.json` | `knowledge-pack/...` with `content_types: [citation_edge]` | Citation graph as a typed leaf. |
| `_TOOL_DISPATCH` | One `tool/...` manifest per function-call | Each tool gets a JSON-schema parameters block. |
| `_contacts.json` | `knowledge-pack/...` with `content_types: [contact_directory]` | Volatile data — fetched at runtime. |
| `chat` harness module | `harness/text-safety-review` (this hub) + a humanitarian-specific harness that extends it | The generic safety review is reusable across industries. |
| `process` harness module | `harness/bulk-file-review` (TBA) | Bundle/document analyst pattern. |
| `extraction` harness | `harness/typed-envelope-drafter` (TBA) | Generic structured-output drafter. |
| `anonymization` harness | `harness/redact-pii-text` (this hub) | Pure deterministic gate. |
| Universal rubric | `rubric/humanitarian-grounded-response-v1` (TBA) | Rubric is the comparable unit. |

## Why the generic mapping works

The DueCare repo carefully separated three things:

1. **Generic primitives** — the harness/RAG/GREP/tool pattern.
2. **Volatile facts** — phone numbers, fee caps, current advisories
   (in tools or knowledge packs).
3. **Stable structure** — refusal style, evidence-first response shape,
   ILO indicator categories (in personas or rubrics).

This separation is exactly what the hub's taxonomy enforces. The
DueCare repo is a fully-worked migrant-safety instance of the generic
shapes in this hub.

## Building this instance

To rebuild the migrant-safety instance from this hub:

1. Add a humanitarian persona that extends `persona/research-analyst`
   (`persona/anti-trafficking-expert`).
2. Add a knowledge pack of ILO statutes and trafficking typologies
   (`knowledge-pack/ilo-statutes-and-typologies`).
3. Add GREP rule packs per risk family
   (`rule-pack/grep/recruitment-fraud`,
   `rule-pack/grep/passport-retention`, …).
4. Add tools for hotline/contact lookups
   (`tool/lookup-hotline-by-country`).
5. Compose them into a pipeline
   (`pipeline/migrant-worker-safety-review`).

This is left as an exercise; the hub provides the substrate.
