# Research-swarm intake queue

**This is where you manually feed areas of improvement for the agent swarm to
research, scrape, conform, and spider.** Append one JSON object per line to
`areas.jsonl`, then run:

```bash
python3 -m scripts.acquisition.research_queue          # ranked queue (human-readable)
python3 -m scripts.acquisition.research_queue --json   # machine-readable
```

The loader turns each area into a grid **cell**, runs the Stage-1 **gap screen**
(estimates how badly base models fail there *without collecting anything*), feeds
that into the **value function**, and prints a ranked queue. The swarm collects
`confirm` cells top-down; `skip` cells stay *named but not collected* — that is the
negative-space discipline ("collect the negative space, not the head").

Pipeline: `areas.jsonl` → `research_queue` → `gap_screen` (Stage 1) → `cell_priority`
→ queue → [swarm: Source-Discoverer → Harvester → Normalizer → Verifier →
CDC-Monitor] (see `docs/strategy/corpus-acquisition-grid-spec.md`).

## Minimum row

```json
{"area": "Short name", "jurisdiction": "PH", "industry": "financial-crime"}
```

## Full row (all fields optional except `area`)

| Field | Meaning |
|---|---|
| `area` | human label (required) |
| `jurisdiction` | ISO 3166 (PH, ID, NG, …) |
| `industry` | labor, financial-crime, customs, GxP, … |
| `use_case` | screening, eligibility, classification, due-diligence, reporting |
| `source_type` / `publisher_type` | primary_regulator / gazette / court / aggregator / social ; government_primary / government_social / law_firm / ngo / expert |
| `time_window` | issuance bucket, e.g. `2026` (enables CDC + recency targeting) |
| `tier` | retrievability tier key: `clean_api`, `structured_no_api`, `unstructured_addressable`, `unaddressable_ephemeral`, `human_only` |
| `corpus_density_gap` | 0–1, **model-independent**: how sparse/non-English/PDF-only/login-walled the indexed text is (high = gap) |
| `regulatory_velocity` | 0–1, **model-independent**: how fast the cell changes |
| `query_misses` | int, **model-independent**: registry questions you couldn't answer here (purest gap signal) |
| `confident_hallucination` | 0–1, **bridge**: model confidently fabricates a verifiable artifact (a circular number, a date) |
| `cross_model_disagreement`, `hedge_rate`, `recency_gap` | 0–1, **model-dependent** (discounted — known unknowns only; probe the *frontier* model) |
| `pays` | 0–1: buyer budget / legal mandate |
| `current_coverage` | 0–1: how much we already hold (SUBTRACTS — pushes us to empty cells) |
| `acquisition_cost` | 0–1: crawl/parse/maintain effort |
| `why`, `source_hints` | free notes + candidate publisher domains |

**Discipline:** lean on the model-independent signals + `query_misses`. The model
can tell you where it *knows* it's weak; only the external world tells you where
it's *confidently blind* (the highest-value tier-4 gaps). Re-score each model
generation — a spike is model- and time-relative.

Lines starting with `#` are ignored. Source ToS: respect robots.txt, never breach
login-walled platforms; prefer official feeds/APIs.
