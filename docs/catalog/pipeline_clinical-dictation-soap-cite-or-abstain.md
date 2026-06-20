# Clinical dictation -> SOAP note (cite-or-abstain)

*pipeline* · `pipeline/clinical-dictation-soap-cite-or-abstain` · v0.1.0 · experimental

Turn a clinician's free-text dictation into a structured SOAP note
(Subjective / Objective / Assessment / Plan) in which every
Assessment and Plan claim is grounded in a cited guideline span or
in the dictation itself — otherwise abstain on that claim. This is
the High-precision clinical RAG bundle (Bundle B) wired as a
governed gate:

 - PHI redaction (HIPAA) on the raw dictation before anything else;
 - clinical acronym-sense disambiguation corpus resolves ambiguous
   dictated abbreviations ("MS" = mitral stenosis vs multiple
   sclerosis) against context BEFORE retrieval, the dominant error
   source in dictation;
 - hybrid retrieval over the clinical guidelines corpus, fused +
   cross-encoder reranked;
 - clinical-reasoner persona + clinical decision-support harness
   drafts the SOAP note with a citation on each A/P claim;
 - DETERMINISTIC cite-or-abstain gate: an Assessment/Plan line with
   no citation fails citation-coverage and blocks publication —
   the model may NOT invent a guideline-backed recommendation.

Negative-space task: dictation transcription tools paraphrase a
recommendation into the note that the clinician never said and no
guideline supports. Here unsupported A/P content is structurally
barred; clinical red-flags also gate for escalation.

Decision-support DRAFT for clinician review; NOT autonomous medical
advice. Synthetic dictation only.

| axis | value |
|---|---|
| industry | healthcare, healthcare.clinical |
| capability | extraction, retrieval, verification, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



## Task

Given a clinician's free-text dictation, produce a structured SOAP
note where every Assessment and Plan claim cites the guideline span
or dictated finding that grounds it, with ambiguous acronyms
disambiguated against context, or abstain on that claim. Publication
is blocked unless citation coverage and the hallucination score
clear threshold.

**pipeline_kind:** `extract`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 2 | `redact_phi` | processor | `processor/redact-pii-text` | - |
| 3 | `disambiguate_acronyms` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 4 | `red_flags` | rule_pack | `rule-pack/clinical-red-flags` | - |
| 5 | `retrieve_guidelines` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 6 | `rerank` | processor | `processor/cross-encoder-reranker` | - |
| 7 | `draft_soap` | harness | `harness/clinical-decision-support` | - |
| 8 | `citation_coverage` | processor | `processor/citation-coverage` | - |
| 9 | `hallucination_check` | processor | `processor/hallucination-scorer` | - |
| 10 | `grade` | processor | `processor/llm-judge` | - |
| 11 | `redaction_audit` | processor | `processor/packet-redaction-audit` | - |
| 12 | `audit` | processor | `processor/audit-trace-emitter` | - |

