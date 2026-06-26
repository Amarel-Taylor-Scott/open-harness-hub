---
name: wikipedia-quality-review
description: Wraps the Wikipedia-quality review flow as a reusable harness with persona
  + GREP + RAG + tools layers. Reviews an article (or draft) against the four core
  content policies + style/structure rubric and emits structured per-claim findings
  with WP-policy citation.
when_to_use: Use when the user needs evaluation. Use when the user needs verification.
  Use when the user needs retrieval. Use when the user needs extraction. Particularly
  relevant for media. Particularly relevant for media.editorial. Particularly relevant
  for media.factcheck. Particularly relevant for education.
---

# Wikipedia article quality review harness

Wraps the Wikipedia-quality review flow as a reusable harness with
persona + GREP + RAG + tools layers. Reviews an article (or draft)
against the four core content policies + style/structure rubric and
emits structured per-claim findings with WP-policy citation.

## Applied layers

- `persona`
- `grep`
- `rag`
- `tools`

## article text → quality flags → policy RAG → grade + edit suggestions

*model_call:* `required`

**Steps**

1. fetch article wikitext (or accept inline)
2. extract claims + sources
3. fire WP-quality GREP pack
4. RAG against WP-policy pack per flag category
5. verify a sample of citations against the cited text
6. judge per wikipedia-article-quality-v1 rubric
7. propose per-finding edits (tag / rewrite / remove)
8. emit audit trace

**Verification**

- every finding cites a WP policy shortcut (WP:NPOV, WP:V, etc.) + URL anchor
- every finding quotes the exact text from the article + section heading
- BLP findings have explicit removal-vs-tag-vs-talk-page recommendation

## Privacy boundaries

- **raw_input**: stays local; article text is public
- **derived_output**: may sync to hub
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/wikipedia-quality-review` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
