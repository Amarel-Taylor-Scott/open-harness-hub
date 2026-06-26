# Prompt-Tooling Source Surface

How to turn thousands of public prompt-tool repositories into reusable Open Harness Hub components through controlled source governance.

## The Problem

GitHub hosts tens of thousands of prompt-engineering repositories — collections of system prompts, template libraries, one-liner generators, PromptFlow pipelines, and LangChain notebooks. Bulk importing them produces noise: duplicate strings, incompatible licenses, stale examples, and no provenance. This document describes the controlled intake pipeline that converts that surface into attributable, deduplicated, embeddable components.

## Intake Pipeline Overview

```
license-filter (permissive only)
        │
        ▼
metadata fetch (repo-level, not bulk text)
        │
        ▼
normalize → source_record + normalized_object
        │
        ▼
fuzzy dedupe → dedupe_cluster
        │
        ▼
attribute → canonical_entity + object_entity_ref
        │
        ▼
embed → object_embedding + index_record
        │
        ▼
risk gate → review_ticket (uncertain) or promotion_candidate
```

Each stage emits one or more standard row families into the staging layer. No component skips the license filter or bypasses the risk gate.

---

## Stage 1: License Filter (Permissive Only)

**Scope**: Only ingest repositories that carry an OSI-approved permissive license (MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, CC-BY-4.0, CC-BY-SA-4.0, CC0-1.0, Unlicense). Copyleft (GPL, AGPL, LGPL) and proprietary licenses are excluded from automated intake.

**Mechanism**:
1. Query GitHub Search API for repos tagged `prompt-engineering`, `llm-prompts`, `prompt-template`, `system-prompt`, or `chatgpt-prompts`.
2. Fetch `LICENSE` file content for each repo (single API call per repo — no bulk text clone).
3. Parse license SPDX identifier from the file header or from `repo.license.spdx_id` in the API response.
4. Reject any repo where the identifier is absent, ambiguous, or not in the permissive allowlist.
5. Emit a `source_record` with `license`, `spdx_id`, `repo_url`, `repo_stars`, `last_pushed_at`, `content_hash` of the LICENSE file, and `trust_tier: community_registry`.

**Row emitted**: `source_record`

---

## Stage 2: Metadata Fetch (Not Bulk Text)

Do not clone repositories. Fetch only:
- `README.md` (first 8,000 characters) for description and usage examples.
- Top-level directory listing to identify template formats (`.yaml`, `.json`, `.txt`, `.md`, `.prompt`).
- `package.json` / `pyproject.toml` / `requirements.txt` if present, for dependency signals.
- GitHub Topics and Description fields from the API.

This keeps storage costs low, avoids ingesting binary or executable content, and limits exposure to embedded secrets or PII in full repository clones.

**Row emitted**: `normalized_object` with `source_kind: github`, `content_type: prompt_template_collection` or `prompt_template`, `extraction_method: metadata_only`.

---

## Stage 3: Normalize

Map each fetched metadata object to the catalog's standard object shape:

| Field | Source |
|---|---|
| `name` | Repository name or README h1 |
| `description` | GitHub description or README first paragraph |
| `capability` | Inferred from topics + README keywords |
| `modality` | Inferred from file formats present |
| `template_slots` | Extracted from README usage examples |
| `license` | From Stage 1 license record |
| `content_hash` | SHA-256 of the normalized description string |
| `source_url` | Canonical GitHub repo URL |

Normalization runs deterministically: same input always produces the same `content_hash`. Formatting changes do not create false versions.

**Row emitted**: `normalized_object`

---

## Stage 4: Fuzzy Dedupe

Many prompt repos are forks, mirrors, or paraphrases of each other. Layered dedupe:

1. **Exact**: match on `content_hash` or canonical `source_url`.
2. **Near-exact**: trigram + token sort ratio ≥ 0.92 on normalized `description`.
3. **Semantic**: cosine similarity ≥ 0.88 on 512-dim embedding of the description.
4. **Cluster**: group into `dedupe_cluster` with a canonical representative. Preserve all source provenance links — dedupe does not erase history.

High-uncertainty pairs (0.75–0.88 cosine, or conflicting licenses) go to `review_ticket` rather than auto-merge.

**Row emitted**: `dedupe_cluster`

---

## Stage 5: Attribute

For each canonical representative surviving dedupe:

- Create a `canonical_entity` linking the component to its upstream author (`author: nidhinjs`, `source_kind: github`, `license: MIT`).
- Create an `object_entity_ref` linking the `normalized_object` to the `canonical_entity`.
- Populate the catalog manifest's `attribution` block: `source_url`, `source_kind`, `author`, `license`.

Attribution must appear in every manifest derived from an external source. It is not optional. Removing it makes the component non-promotable.

**Rows emitted**: `canonical_entity`, `object_entity_ref`

---

## Stage 6: Embed

Generate vector embeddings for each attributed `normalized_object`:

- Embed the concatenation of `name`, `description`, and up to 3 `template_slots` descriptions.
- Use the standard embedding model specified in the pipeline manifest (e.g. `sentence-transformers/all-MiniLM-L6-v2` or equivalent).
- Store as `object_embedding` with `model_id`, `vector_dims`, `content_hash` of the embedded string, and `placeholder: false`.

Components with `placeholder: true` embeddings are not eligible for promotion.

**Rows emitted**: `object_embedding`, `index_record`

---

## Stage 7: Risk Gate → Review Ticket or Promotion Candidate

Before a component can become tenant-visible, it must pass:

| Check | Pass condition |
|---|---|
| License verified | SPDX ID in permissive allowlist |
| Attribution present | `attribution.source_url` + `attribution.license` set |
| Content hash stable | Hash matches stored `normalized_object` |
| Embedding not placeholder | `placeholder: false` |
| No open review ticket | All prior tickets resolved |
| No volatile public facts | Static text only; no live data claims |

Components failing any check emit a `review_ticket` with `reason`, `risk_level`, and `blocking: true`. Only components with all checks passing advance to `promotion_candidate`.

**Row emitted**: `review_ticket` (on failure) or `promotion_candidate` (on pass)

---

## Worked Example: prompt-master (nidhinjs)

**Repository**: `https://github.com/nidhinjs/prompt-master`
**License**: MIT (SPDX `MIT`) — permissive, passes Stage 1.

### Stage 1 output

```json
{
  "type": "source_record",
  "source_url": "https://github.com/nidhinjs/prompt-master",
  "spdx_id": "MIT",
  "trust_tier": "community_registry",
  "repo_stars": 47,
  "last_pushed_at": "2024-11-01",
  "content_hash": "sha256:e3b0c44298fc1c149afb..."
}
```

### Stage 2–3 output (normalized_object excerpt)

```json
{
  "type": "normalized_object",
  "name": "prompt-master template library",
  "description": "Curated collection of reusable prompt templates covering task-brief, visual-descriptor, and few-shot patterns with anti-pattern guidance.",
  "capability": ["generation"],
  "modality": ["text"],
  "content_hash": "sha256:a7f3b2...",
  "source_url": "https://github.com/nidhinjs/prompt-master",
  "source_kind": "github",
  "content_type": "prompt_template_collection"
}
```

### Stage 4 output

The repo is unique in the dedupe cluster (no exact or near-exact duplicates found). A new `dedupe_cluster` is created with this object as the canonical representative.

### Stage 5 output (attribution in manifest)

```yaml
attribution:
  source_url: "https://github.com/nidhinjs/prompt-master"
  source_kind: github
  author: "nidhinjs"
  license: "MIT"
```

This attribution block appears in every derived manifest:
- `catalog/patterns/prompt/anti-vague-task-prompt.yaml`
- `catalog/patterns/prompt/anti-unbounded-context-prompt.yaml`
- `catalog/patterns/prompt/anti-missing-success-criteria-prompt.yaml`
- `catalog/logic-packs/prompt/prompt-template-library.yaml`

### Stage 6–7 outcome

All checks pass. Components advance to `promotion_candidate`. No `review_ticket` is emitted.

---

## Scaling to Thousands of Repos

This pipeline is designed for batch operation:

- **Source surface scan**: a single GitHub Search API session yields 1,000 repos per query (paginated). Ten topic queries = 10,000 candidates before deduplication.
- **License filter**: eliminates ~40–60% of repos. Expect ~5,000 permissive candidates from 10,000 raw.
- **Metadata fetch**: each repo requires 2–3 API calls. At GitHub's 5,000 requests/hour authenticated rate: ~1,600 repos/hour.
- **Normalize + dedupe**: CPU-bound Python, deterministic, parallelizable across workers.
- **Embed**: GPU-bound if using local models; batch with the embedding worker fleet.
- **Daily target**: 1,000–5,000 new `promotion_candidate` rows/day after dedupe collapse.

All rows land in JSONL staging first. Postgres/pgvector load is a separate step (see `docs/architecture/postgres-pgvector-bootstrap.md`).

---

## What Is NOT Ingested

- Bulk text of prompt files (only metadata and descriptions).
- Any repo without a parseable permissive license.
- Repos with `_secret`, `private`, `internal`, or `confidential` in the description.
- Content that references real personal data, credentials, or API keys.
- Insurance-specific pipelines or examples (per project safety scope).

---

## Related Architecture Docs

- `docs/architecture/source-governance-and-entity-resolution.md` — full source tier classification and dedupe strategy.
- `docs/architecture/database-backed-component-store.md` — Postgres schema for staging rows.
- `docs/architecture/daily-promotion-readiness.md` — promotion gate and CDC plan.

## Related Catalog Components

- `catalog/patterns/prompt/anti-vague-task-prompt.yaml`
- `catalog/patterns/prompt/anti-unbounded-context-prompt.yaml`
- `catalog/patterns/prompt/anti-missing-success-criteria-prompt.yaml`
- `catalog/logic-packs/prompt/prompt-template-library.yaml`
