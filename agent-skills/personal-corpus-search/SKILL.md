---
name: personal-corpus-search
description: Search the user's personal corpus — their own files, notes, emails, calendar,
  contacts — and return answer + citations scoped to ONLY the user's data. Authorization-gated;
  refuses to answer questions about a person from third-party data unless the user
  has explicitly authorized. Trust boundary is local — the user's data does not leave
  their device unless they choose a hosted model arm.
when_to_use: Use when the user needs retrieval. Use when the user needs reasoning.
  Use when the user needs memory. Particularly relevant for personal_productivity.
---

# Personal corpus search (RAG over user's own files / notes / docs)

Search the user's personal corpus — their own files, notes,
emails, calendar, contacts — and return answer + citations
scoped to ONLY the user's data. Authorization-gated; refuses
to answer questions about a person from third-party data
unless the user has explicitly authorized.

Trust boundary is local — the user's data does not leave their
device unless they choose a hosted model arm.

## Applied layers

- `persona`
- `privacy`
- `grep`
- `rag`
- `tools`

## query → personal corpus retrieve → cite-first answer

*model_call:* `required`

**Steps**

1. load user preferences (incl. privacy gates)
2. scope retrieval to user's own corpus (calendar / contacts / notes / docs / emails)
3. retrieve top-K from each source (hybrid BM25 + dense)
4. rerank with cross-encoder
5. compose persona + retrieved + tool registry
6. generate answer with citations to source URIs / file paths
7. redact any third-party PII before answer is returned

**Verification**

- every claim cites a personal corpus source URI
- no third-party PII in answer body
- no synthesis of information not actually in the corpus

## Privacy boundaries

- **raw_input**: the query stays on user's device
- **derived_output**: the answer stays with the user
- **external_calls**: only if model_target.trust_boundary == external AND user opted in via env

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_claude` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/personal-corpus-search` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
