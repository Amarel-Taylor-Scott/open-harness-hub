# GitHub Signal intake — 2026-06-20

> Owner-shared repo list, reviewed live (WebFetch/WebSearch) as **governed candidates**. The GitHub Signal
> Flywheel turns shared repos into hub CANDIDATES — **discovery is not trust; intake is never auto-active.**
> Single source of truth: `scripts/ingest_github_signal_intake.py` (→ `data/capability-candidates/discovered-feed-github-signal-2026-06-20.json`),
> proof-gated. `adoptable` is cross-checked against the org-guardrail denied-licenses (copyleft / unstated /
> proprietary can never be adoptable). serves_truth=false for everything.

## Dispositions

| Repo / target | License | Disposition | Why | Candidate slots |
|---|---|---|---|---|
| **LeoYeAI/openclaw-marketing-skills** (1.1k★) | MIT | **ADOPT-CANDIDATE** | 37 marketing-domain skills; clean license, low-risk non-regulated domain | `marketing-copy-skill`, `seo-brief-skill` |
| **konbakuyomu/smartsearch** (589★) | MIT | **CONSIDER** | CLI web-research tool; gate behind a tool-adapter port — fetches are untrusted candidates, never facts | `web-source-discovery-tool`, `page-fetch-adapter` |
| **agentic-in/inferoa** (207★) | Apache-2.0 | **WATCH** (foil) | Another agent harness (our explicit non-goal); borrow prefix-cache/token-routing techniques behind OIPS only | `inference.prefix_cache_routing_policy` |
| **webfuse-com/awesome-autoresearch** (2.2k★) | CC0-1.0 | **CONSIDER** (scout) | Index of self-improving loops → mine via gap_screen; **owner corrected** (not `alvinreal`) | `autoloop_system_candidate_feed`, `eval_benchmark_adapter` |
| **RoggeOhta/awesome-codex-cli** (318★) | CC0-1.0 | **WATCH** (scout) | 280+ Codex-CLI tools; mixed downstream licenses incl. GPL → per-item intake only | `codex-cli-wrapper` |
| **discover-legal/BigLaw** (68★) | **AGPL-3.0** | **WATCH** (intel) | Self-hosted legal-AI platform; AGPL → clean-room ideas only; its 32-connector legal-source list is intel; lacks our verification/source-authority layer (sharpens the wedge) | `legal_source_connector_catalog`, `court_deadline_rule_calculator` |
| **jaytel0/taste** (245★) | **unstated** | **WATCH** | image-refs → SKILL.md; unstated license blocks adoption; output is a candidate skill | `skill_synthesis.image_reference_to_skill_md` |
| **tantara/openbrief** (463★) | **AGPL-3.0** | **AVOID** | off-thesis consumer media app + AGPL; ASR is commodity, no durable gap | — |
| **engineering-management/awesome-engineering-management** (2.7k★) | CC0-1.0 | **AVOID** | out of scope (no AI capability/data); name shared by 6+ owners | — |
| **deeprepo.ai** | n/a (SaaS) | **WATCH** | repo-architecture analysis SaaS; **`.ai` domain is dead** — real product at `deeprepo.dev`; comprehension aid, output never trusted | `repo_intake.architecture_extraction` |

## Provenance corrections (honest, not fabricated)

- **`alvinreal/awesome-autoresearch` → `webfuse-com/awesome-autoresearch`** — the shared owner is not the live owner (cross-host redirect, not a fork). Canonical owner recorded.
- **`deeprepo.ai` is a dead link** — refused connection (×2). The live product "DeepRepo" is at **`deeprepo.dev`** (AI repo-architecture analysis). This is a *comprehension* SaaS, not the prior Facebook DeepRepo *feed* (see [[deeprepo-intake-2026-06-18]]); confirm the intended target.
- **`enginee.../awesome-engineering-management`** — source URL was truncated; resolved to the 2.7k★ `engineering-management/` org repo, but the name is shared by ≥6 owners. Re-confirm intent if it matters (it's AVOID either way).
- **Flows Agent (`facebook.com/share/r/17qA2JQ68b`)** — **not scrapeable** (FB share link), consistent with the prior DeepRepo FB-feed intake. Cannot review; the owner would need to paste the underlying repo URL. Recorded under `unfetchable` in the feed.

## Net

Two clean MIT, on-thesis adopt/consider candidates (`openclaw-marketing-skills`, `smartsearch`); two CC0 scout
feeds to mine (`awesome-autoresearch`, `awesome-codex-cli`); one AGPL legal platform worth watching as intel for
the legal beachhead (BigLaw); the rest WATCH/AVOID on license or off-thesis grounds. Nothing is promoted — each
adopt-candidate must still pass the gap/lift screen + human/eval gates. Relates to [[github-signal-flywheel]],
[[deeprepo-intake-2026-06-18]].
