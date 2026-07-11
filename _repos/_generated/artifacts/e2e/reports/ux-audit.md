# UI/UX audit — 2026-06-10T13:21:47.393Z

Design system: **Hanken Grotesk** (display) + **IBM Plex Mono** (mono) · min text 12px · min tap 44px.
**9 surfaces · 17 findings** (high 0, medium 10, low 7)

## Findings to troubleshoot (ranked)
- **[medium] baltor** · tiny-text: 44 text elements < 12px (e.g. "Conflicts solved" 10px)
- **[medium] teleon** · off-system-font: off-design-system fonts: jetbrains mono
- **[medium] teleon** · tiny-text: 15 text elements < 12px (e.g. "▾" 9px)
- **[medium] harness-hub** · off-system-font: off-design-system fonts: space grotesk, times new roman
- **[medium] harness-hub** · tiny-text: 3 text elements < 12px (e.g. "▴Activity" 10px)
- **[medium] control-tower** · tiny-text: 20 text elements < 12px (e.g. "active" 11px)
- **[medium] hub:opencontexthub** · off-system-font: off-design-system fonts: times new roman
- **[medium] hub:openreviewhub** · off-system-font: off-design-system fonts: times new roman
- **[medium] hub:openroutinghub** · off-system-font: off-design-system fonts: times new roman
- **[medium] hub:openharnesshub** · off-system-font: off-design-system fonts: times new roman
- **[low] parent** · small-tap-target: 7 interactive elements < 44px (e.g. "AI Done Right" 16px)
- **[low] baltor** · small-tap-target: 13 interactive elements < 44px (e.g. "Baltor" 23px)
- **[low] teleon** · font-sprawl: 4 distinct font families (expect ≤3)
- **[low] teleon** · small-tap-target: 12 interactive elements < 44px (e.g. "⬢
▾" 32px)
- **[low] harness-hub** · font-sprawl: 4 distinct font families (expect ≤3)
- **[low] harness-hub** · small-tap-target: 25 interactive elements < 44px (e.g. "Explore" 32px)
- **[low] control-tower** · small-tap-target: 25 interactive elements < 44px (e.g. "local" 17px)

## Per-surface metrics
| surface | fonts | taps<44 | tiny text | overflow |
|---|---|---|---|---|
| parent | 2 | 7 | 0 | no |
| baltor | 3 | 13 | 44 | no |
| teleon | 4 | 12 | 15 | no |
| harness-hub | 4 | 25 | 3 | no |
| control-tower | 2 | 25 | 20 | no |
| hub:opencontexthub | 1 | 0 | 0 | no |
| hub:openreviewhub | 1 | 0 | 0 | no |
| hub:openroutinghub | 1 | 0 | 0 | no |
| hub:openharnesshub | 1 | 0 | 0 | no |

## UI/UX action graph (surface → nav targets)
```mermaid
graph LR
  parent --> r_portfolio
  parent --> r___aidoneright_index_html
  parent --> r___teleon_dev_index_html
  parent --> r___baltor_index_html
  parent --> r___opencontexthub_index_html
  parent --> r___openskillshub_index_html
  parent --> r___opentoolshub_index_html
  parent --> r___openharnesshub_index_html
  baltor --> r_
  baltor --> r_engine
  baltor --> r_pricing
  baltor --> r_trust
  baltor --> r_dashboard_html
  baltor --> r_demo_console_html
  baltor --> r_reviews_html
  baltor --> r_admin_demo_
  teleon --> r___context_is_everything_Conte
  teleon --> r___context_enrichment_Context_
  teleon --> r___openharnesshub_OpenHarnessH
  harness_hub --> r_
  harness_hub --> r_pipelines
  harness_hub --> r_compare
  harness_hub --> r_solutions
  harness_hub --> r_pricing
  harness_hub --> r_docs
  harness_hub --> r_trust
  harness_hub --> r_how_it_works_html
```