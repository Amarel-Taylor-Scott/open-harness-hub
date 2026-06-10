# Wikipedia article quality review harness

*harness* · `harness/wikipedia-quality-review` · v0.1.0 · experimental

Wraps the Wikipedia-quality review flow as a reusable harness with
persona + GREP + RAG + tools layers. Reviews an article (or draft)
against the four core content policies + style/structure rubric and
emits structured per-claim findings with WP-policy citation.

| axis | value |
|---|---|
| industry | media, media.editorial, media.factcheck, education |
| capability | evaluation, verification, retrieval, extraction |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**Contributes to:** `pipeline/wikipedia-page-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### article text → quality flags → policy RAG → grade + edit suggestions  
*model_call: `required`*

1. fetch article wikitext (or accept inline)
1. extract claims + sources
1. fire WP-quality GREP pack
1. RAG against WP-policy pack per flag category
1. verify a sample of citations against the cited text
1. judge per wikipedia-article-quality-v1 rubric
1. propose per-finding edits (tag / rewrite / remove)
1. emit audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**verification:** every finding cites a WP policy shortcut (WP:NPOV, WP:V, etc.) + URL anchor, every finding quotes the exact text from the article + section heading, BLP findings have explicit removal-vs-tag-vs-talk-page recommendation



## Privacy boundaries

- **raw_input**: stays local; article text is public
- **derived_output**: may sync to hub
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

