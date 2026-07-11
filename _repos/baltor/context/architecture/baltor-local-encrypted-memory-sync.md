# Baltor Local Encrypted Memory Sync

Baltor needs a split-brain memory design.

```text
Local encrypted memory:
  works offline
  user/device can search and update it
  cloud stores encrypted sync blobs
  cloud may not be able to search it

Company cloud context:
  centrally indexed
  governed and permission-aware
  searchable by approved company services
  usually not true zero-knowledge from the company

Hybrid local MCP:
  Claude Code reads both through one local interface
```

The central rule:

```text
If the cloud cannot decrypt a memory item, the cloud cannot normally embed,
semantic-search, rerank, summarize, or compress that item.
```

Those operations either happen locally, or the item enters a separate
company-readable context tier.

## Memory Classes

```text
private_local
  personal/device memory
  E2EE or local-only
  local search only

team_encrypted
  team key can decrypt
  cloud relay stores ciphertext
  local devices build indexes

repo_encrypted
  repo maintainers can decrypt
  useful for repo gotchas and local context packs

org_approved_cache
  cached company context packs
  encrypted locally with TTL and freshness labels

company_context
  company-readable governed context
  central indexing, embeddings, reranking, compression
```

Private memory stores compact claims, local workflow notes, failed approaches,
and source handles. It should not store raw Jira, Confluence, GitLab, customer
data, or secrets.

Company context stores approved source-derived context and can be centrally
searched because the company context service is allowed to read it.

## Local MCP Contract

The local agent should expose:

```text
remember()
search_memory()
context_for_ticket()
context_for_repo()
context_fetch()
sync_status()
sync_now()
validate_sources_when_online()
```

Offline behavior:

```text
local memory read/write allowed
local search allowed
local cached context packs allowed
source freshness marked as stale or last-validated
source-system writes disabled
encrypted sync queued
```

Online behavior:

```text
encrypted memory events sync
company context gateway can be queried
cached context packs can be refreshed
source handles can be validated
stale local claims can be flagged
```

## Storage Options

Fastest proof:

```text
Markdown or Obsidian vault
+ encrypted sync
+ Claude Code skill/hooks
```

Developer-friendly proof:

```text
Git-backed memory repo
+ git-crypt, SOPS, or age
+ Gitleaks
+ Markdown context packs
```

Productized proof:

```text
local-contextd
+ SQLCipher
+ local vector index
+ encrypted append-only event log
+ company cloud relay
+ MCP facade
```

Local-first app proof:

```text
PowerSync / Replicache / Automerge / cr-sqlite
+ encrypted local store
+ local MCP facade
```

## Product Invariants

```text
private_e2ee_memory_is_not_cloud_searchable
plaintext_embeddings_are_sensitive
local_embeddings_stay_local_by_default
company_context_index_is_separate_from_private_memory
cached_company_context_has_ttl_and_freshness
source_handles_required_for_durable_claims
raw_source_dumps_blocked_from_memory
secrets_and_customer_data_blocked_from_memory
```

This keeps offline progress useful without pretending encrypted cloud blobs are
a normal central RAG index.
