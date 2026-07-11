# Stream 1 — schema.org / W3C / JSON-LD (research notes)

> Source: parallel research agent, returned 2026-05-19. Web tools were
> denied; relied on training-data knowledge. Verify URLs & adoption
> claims before publishing.

## Headline recommendations
1. Ship JSON-LD `@context` at a stable hub URL; embed it in every
   manifest. Maps custom hub terms to schema.org core (`SoftwareApplication`,
   `Dataset`, `HowTo`, `CreativeWork`) + a custom `ai:` namespace.
2. Adopt **SKOS + DCAT** together — hub root = `dcat:Catalog`, each
   open vocabulary (industries, capabilities, leaf-types,
   process_kinds) = `skos:ConceptScheme`.
3. Layer **PROV-O** on reproducibility/attribution + **ODRL** on
   license/trust_boundary.

## Standard-by-standard

| Standard | Status | Hub mapping | Decision |
|---|---|---|---|
| schema.org core | de facto | harness→SoftwareApplication; pipeline→HowTo; tool→SoftwareApplication/Action; dataset→Dataset; rubric→Rating/DefinedTermSet | @context only; subclass via `additionalType` |
| schema.org AI/ML | sparse — no first-class `MLModel`/`AIAgent` | Bioschemas `ComputationalWorkflow`/`ComputationalTool` closest community ext | Reuse Dataset props; emit own `ai:Harness`/`ai:Pipeline` IRIs |
| JSON-LD 1.1 | W3C Rec (2020) | embed `@context`; YAML-LD draft lets it live in YAML | full adopt |
| DCAT-3 | W3C Rec (Aug 2024) | dataset, knowledge-pack, catalog root | full adopt |
| PROV-O | W3C Rec (2013) | reproducibility, attribution, provenance | full adopt |
| SKOS | W3C Rec (2009) | open vocabularies | full adopt |
| ODRL 2.2 | W3C Rec (2018) | license, trust_boundary | adopt for non-trivial policies |
| LDP | W3C Rec (2015), niche | n/a | ignore for v1 |

## Concrete YAML-LD example (proposed pattern)

```yaml
"@context":
  - "https://schema.org"
  - vocab: "https://open-harness-hub.dev/ns/"
    Harness: "vocab:Harness"
    capability: "vocab:capability"
    lifecycle_position: "vocab:lifecyclePosition"
"@type": ["SoftwareApplication", "vocab:Harness"]
```

## Open questions for the synthesis
- Where to host the `@context` JSON file? Suggest `docs/ns/context.jsonld`
  served by the static site at `/ns/context.jsonld`.
- Should the hub publish a `sitemap.xml` of all manifests for Google
  Dataset Search to crawl?
- ActivityPub / Solid relevance for write-back federation later?

## Word count
~720 (within cap).
