# Screens — visual reference

One captured image per surface (desktop, default light theme) plus a few key sub-states.
These are **reference captures** of the HTML prototypes — recreate the look in your codebase;
don't trace pixels from the PNGs (open the live HTML for exact spacing/interaction).

## Surfaces
| # | Image | Surface | Entry HTML |
|---|---|---|---|
| 01 | `01-parent-ai-done-right.png` | Parent portfolio (AI Done Right) | `context-is-everything/Context is Everything.html` |
| 02 | `02-demo-control-tower.png` | Demo Control Tower (operator index) | `context-is-everything/Demo Control Tower.html` |
| 03 | `03-baltor.png` | Baltor.ai (context assurance) | `context-enrichment/Context Enrichment Prototype.html` |
| 04 | `04-teleon.png` | Teleon.dev (runtime · reference kit site) | `teleon/Teleon Prototype.html` |
| 05 | `05-opencontexthub.png` | OpenContextHub (live) | `opencontexthub/OpenContextHub Prototype.html` |
| 06 | `06-openskillshub.png` | OpenSkillsHub (live) | `openskillshub/OpenSkillsHub Prototype.html` |
| 07 | `07-opentoolshub.png` | OpenToolsHub (live) | `opentoolshub/OpenToolsHub Prototype.html` |
| 08 | `08-openskilltotool.png` | OpenSkillToTool (live) | `openskilltotool/OpenSkillToTool Prototype.html` |
| 09 | `09-openmcphub.png` | OpenMCPHub (live) | `openmcphub/OpenMCPHub Prototype.html` |
| 10 | `10-opencompressionhub.png` | OpenCompressionHub (live) | `opencompressionhub/OpenCompressionHub Prototype.html` |
| 11 | `11-openbenchmarkhub.png` | OpenBenchmarkHub (live) | `openbenchmarkhub/OpenBenchmarkHub Prototype.html` |
| 12 | `12-openreviewhub.png` | OpenReviewHub (live) | `openreviewhub/OpenReviewHub Prototype.html` |
| 13 | `13-openharnesshub.png` | OpenHarnessHub (live · bespoke pt-*) | `openharnesshub/OpenHarnessHub Prototype.html` |
| 14 | `14-opentemplateshub-private.png` | OpenTemplatesHub (**private bench**) | `opentemplateshub/OpenTemplatesHub Prototype.html` |
| 15 | `15-openendpointhub-private.png` | OpenEndpointHub (**private bench**) | `openendpointhub/OpenEndpointHub Prototype.html` |
| 16 | `16-openenvhub-private.png` | OpenEnvHub (**private bench**) | `openenvhub/OpenEnvHub Prototype.html` |
| 17 | `17-opensandboxhub-private.png` | OpenSandboxHub (**private bench**) | `opensandboxhub/OpenSandboxHub Prototype.html` |
| 18 | `18-openagenthub-private.png` | OpenAgentHub (**private bench**) | `openagenthub/OpenAgentHub Prototype.html` |
| 19 | `19-openreceipthub-private.png` | OpenReceiptHub (**private bench**) | `openreceipthub/OpenReceiptHub Prototype.html` |
| 20 | `20-openstatehub-private.png` | OpenStateHub (**private bench**) | `openstatehub/OpenStateHub Prototype.html` |

## Key sub-states (bespoke depth + shared patterns)
| # | Image | What it shows | Route |
|---|---|---|---|
| 21 | `21-os2t-architecture.png` | OpenSkillToTool backend pipeline (`extraRoutes` hook) | `…/OpenSkillToTool Prototype.html#/architecture` |
| 22 | `22-os2t-convert-wizard.png` | OpenSkillToTool multi-step convert wizard (`convert.render`) | `…#/convert` |
| 23 | `23-orh-review-report.png` | OpenReviewHub review report on an entry (`entryExtra` hook) | `…/OpenReviewHub Prototype.html#/e/agent-runtime-repo` |
| 24 | `24-hub-browse-grid.png` | The shared `makeHub` browse graph (facets + cards) | `…/OpenContextHub Prototype.html#/browse` |

## Context-governance method hubs (private bench · Baltor engine stages)
| # | Image | Surface | Entry HTML |
|---|---|---|---|
| 25 | `25-openreconciliationhub-private.png` | OpenReconciliationHub (Reconcile) | `openreconciliationhub/OpenReconciliationHub Prototype.html` |
| 26 | `26-openhardeninghub-private.png` | OpenHardeningHub (Harden) | `openhardeninghub/OpenHardeningHub Prototype.html` |
| 27 | `27-openenrichmenthub-private.png` | OpenEnrichmentHub (Enhance) | `openenrichmenthub/OpenEnrichmentHub Prototype.html` |
| 28 | `28-openoptimizationhub-private.png` | OpenOptimizationHub (Optimize) | `openoptimizationhub/OpenOptimizationHub Prototype.html` |
| 29 | `29-openverificationhub-private.png` | OpenVerificationHub (Verify) | `openverificationhub/OpenVerificationHub Prototype.html` |

## Notes for the implementer
- **Private-bench hubs (14–20)** all show the muted accent + the **"Private preview" banner** —
  that's the `access:'private'` treatment. Live hubs show a saturated accent and no banner.
- The **only visual difference between hubs** is the accent color — same layout, chrome, and
  components throughout (branded house). Don't build them as separate designs.
- Captures are **light theme, desktop**. Every surface also has a **dark theme** (☾/☀ toggle)
  and reflows to a single column on mobile — verify against the live HTML.
- For exact tokens (color/space/type), read `shared/oh-tokens.css` + `oh-components.css`, not
  the PNGs.
