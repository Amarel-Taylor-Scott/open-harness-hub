# OpenHarness Zip Integration Review

> Historical alignment note (2026-05-31), kept for lineage. The LIVE design system (5 surfaces, light theme,
> byte-identical CSS, Inter UI) is now canonical in **`docs/DESIGN-BIBLE.md`** + `scripts/surface_server.py` — read
> those for current truth; the three-site framing below is the 2026-05-31 record.

Date: 2026-05-31

This note records how the `OpenHarness.zip` / Claude Code design export maps
into the current three-site platform. It is a working alignment document, not a
new product strategy.

## Source Artifacts

The archive contains three usable design tracks:

- `openharness/shared/`: shared tokens, components, product registry, and
  primitive visual language.
- `openharness/context-is-everything/`: parent mission landing for the company
  story.
- `openharness/context-enrichment/`: the older Context Enrichment prototype,
  now interpreted as Baltor.
- `openharness/openharnesshub/`: Open Harness Hub prototype, route inventory,
  design canvas, and app shell.

The repo already carries the Open Harness Hub handoff under
`web/harness-hub/design/`. That handoff remains the design source of truth for
the open product surface.

## Adopted Decisions

- Use one shared design foundation across all three sites: common spacing,
  card primitives, typography scale, and status patterns.
- Keep brand roles distinct:
  - AI Done Right (founding thesis: Context is Everything): parent mission and platform story.
  - Baltor: paid context-control and context-assurance product.
  - Open Harness Hub: open catalog, builder, registry, and funnel.
- Treat the old `context-enrichment` prototype as Baltor source material, not
  as a fourth brand.
- Keep the Baltor admin demo operational and quiet: entry page is a launcher;
  processing, graph/RAG exploration, exports, and integration tests are routed
  to dedicated pages.

## Design Rules To Preserve

- Cards should resolve to shared card primitives or their site-specific aliases.
- Avoid one-off color declarations when an existing token can express the state.
- Prefer routed task surfaces over one crowded dashboard.
- Use calm product language: verified, current, reconciled, traceable,
  token-efficient, serving package, automated refresh job, verification queue.
- Do not describe customer data as broken. Show the next resolution path.

## Current Gaps

- Baltor and AI Done Right (founding thesis: Context is Everything) are visually related but still less aligned
  to the Open Harness Hub shared component system than the zip export intends.
- The Baltor admin demo has modular CSS, but its panels are still custom
  `ad-*` components rather than mapped aliases to the shared `oh-*` primitives.
- Some docs still mention old product states, including earlier admin-demo
  launcher language and generic context-enrichment naming.
- The three-site navigation story is not yet surfaced as a persistent
  cross-site product switcher.

## Next Implementation Targets

1. Continue reducing one-off Baltor admin CSS into smaller routed modules.
2. Add a simple cross-site product switcher pattern shared by all three sites.
3. Map Baltor status badges and cards to shared component tokens where possible.
4. Keep updating stale docs to point at the locked brand architecture and clean
   Baltor context instead of repeating old naming.
