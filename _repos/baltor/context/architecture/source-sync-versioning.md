# Source Sync And Versioning

Baltor context control needs a source ledger before it needs more model logic.
Every uploaded file, connector folder, repository path, and object-store prefix
should have a durable record of what was synced, when it changed, and which
worker jobs were created from that change.

## Core Records

`source_connection`

- `id`
- `kind`: `upload`, `drive`, `sharepoint`, `git`, `s3`, `web`, `api`
- `display_name`
- `scope`: `public`, `org`, `tenant`, `user`, `private`
- `sync_policy`: manual, interval, webhook, CDC feed
- `last_sync_at`
- `last_success_at`
- `last_error`
- `next_sync_at`
- `enabled`

`source_file`

- `id`
- `connection_id`
- `external_id`
- `path`
- `mime_type`
- `size_bytes`
- `modified_at`
- `current_version_id`
- `deleted_at`

`source_file_version`

- `id`
- `source_file_id`
- `content_hash`
- `metadata_hash`
- `version_label`
- `created_at`
- `extracted_text_uri`
- `raw_object_uri`
- `diff_uri`
- `status`: `new`, `unchanged`, `changed`, `deleted`, `failed`

`source_change_event`

- `id`
- `connection_id`
- `source_file_id`
- `from_version_id`
- `to_version_id`
- `change_type`: `new`, `changed`, `deleted`, `metadata_only`
- `detected_at`
- `enqueued_jobs`

## Processing Flow

1. Connector sync lists remote files and metadata.
2. The sync worker compares `external_id`, `modified_at`, `size_bytes`, and
   hashes against the latest `source_file_version`.
3. New or changed files create a version row and a `source_change_event`.
4. Extractor workers produce text, OCR output, tables, and document layout.
5. Context workers chunk, embed, extract entities, create graph edges, extract
   claims, scan fragile facts, and plan verification.
6. Reconciliation workers compare new claims against prior accepted context and
   source authority rules.
7. Promotion remains blocked until required sources and curator gates pass.

## Worker Cost Hierarchy

Processing should run cheapest-first and escalate only when narrower workers
cannot resolve the case:

- Deterministic workers: hashing, diffs, MIME routing, OCR routing, chunking,
  keyword extraction, date and number extraction, duplicate detection, citation
  parsing, schema validation, and source freshness checks.
- Small model workers: chunk summaries, entity extraction, claim extraction,
  table interpretation, topic classification, document type classification, and
  source type classification.
- Medium model workers: claim normalization, evidence matching, source
  precedence comparison, graph edge inference, reconciliation candidates, and
  provenance summaries.
- Hermes/OpenClaw workers: unresolved investigations, adversarial review,
  open-ended source search, procedure discovery, and deterministic rule
  generation.

Expensive workers should write artifacts that cheaper workers can replay later:
resolver rules, extraction templates, source precedence policies, search query
templates, validation checks, graph edge rules, and promotion gates.

## Serving Outputs

Verified context should be packaged for several serving paths instead of
remaining only as run output:

- Text context pack: current facts, concise source notes, optional provenance
  history, and prompt-ready policy/procedure text.
- RAG index: chunks, embeddings, keyword records, citations, freshness metadata,
  and source scopes.
- Graph or hybrid retrieval: entities, claims, source links, procedure edges,
  supersession links, and impact-analysis paths.
- Audit packet: original customer facts, reconciled facts, source diffs, worker
  traces, generated deterministic procedures, approvals, and timestamps.

The default serving mode should stay token-efficient. Agents can request
`current_only` or `current_with_sources`, while admin and audit views can request
`current_with_history`, `audit_packet`, or `diff_since_last_sync`.

## User-Facing Status

The admin surface should make sync state visible without exposing internal
queue details first:

- `Last sync: 2 hours ago`
- `Next sync: in 30 minutes`
- `Version: v-8ab13d4`
- `Change: 14 files changed, 2 deleted`
- `Running: OCR, graph extraction, verification`
- `Queued: 8 refresh jobs`
- `Blocked: waiting on source approval`

Copied run links should reopen the same run state. Local demo runs persist under
`dist/admin-demo-runs/`; production should store the same shape in Postgres and
use Redis, Celery, Temporal, or Argo only for execution state.

## Local And Cloud Parity

The local admin demo uses deterministic source metadata: source name, type,
size, modified time, content hash, version label, sync age, and next action.
That mirrors the production record model closely enough to keep the UI stable
when real connectors arrive.

Production connectors should emit the same event shape used by
`_repos/shared-backend-components/scripts/ingest/freshness.py`: `new`, `changed`, `unchanged`, and `error`.
Those events then enqueue `context.pipeline.pass` or narrower workers from the
context worker registry.

## Design Rule

The product language should emphasize that context is verified, current,
reconciled, modular, and token-efficient. Internally, the implementation can
talk about hashes, cache keys, CDC, and diff artifacts; externally, users need
clear freshness and readiness signals.
