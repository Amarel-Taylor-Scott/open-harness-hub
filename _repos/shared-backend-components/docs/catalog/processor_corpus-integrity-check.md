# Corpus integrity check (detect an internal doc that contradicts or claims to supersede the authoritative source)

*processor* · `processor/corpus-integrity-check` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. Detects an internal corpus document that
CONTRADICTS the registered authoritative source, or that asserts authority it
does not have ("this policy supersedes …", "effective immediately, overrides
…"). This is the adversarial-integrity axis of context assurance.

THREAT MODEL (the 8-of-12 fake-policy attack): published corpus-poisoning
research (BadRAG / TrojanRAG) demonstrates that a planted document can be
cited by a majority of RAG systems as authoritative even though no
authoritative publisher ever issued it. Faithfulness-only evaluation does not
catch this: the answer faithfully reflects the corpus; the corpus is the
attack. This processor checks the document AGAINST the authoritative
source_record rather than trusting the corpus as ground truth.

Checks performed (deterministic over governed inputs):
  1. Provenance binding — does the candidate document trace to a registered
     authoritative source_record (publisher, content_hash, effective_date)?
     An unbound document claiming authority is the primary red flag.
  2. Supersession assertion — does the document text claim to supersede /
     override / replace policy without a binding to an authoritative
     publisher record that grants that authority?
  3. Contradiction detection — does the document state a fact that directly
     conflicts with the current authoritative source on the same field?
  4. Verdict — pass | contradiction | unauthorized_supersession |
     unverified_provenance, each carrying the deterministic warrant (which
     source_record, which field, what conflict) plus a review_ticket when the
     finding warrants human adjudication.

GOVERNANCE (honest framing): this is a governed DEFINITION of an integrity
check, not a measured-lift claim. It describes the threat (poisoned /
authority-spoofing corpus documents) and the deterministic checks against
governed provenance that flag it. It does NOT assert a populated detection
rate. The implementation is built by the code lane at the path below.

| axis | value |
|---|---|
| industry | cross_industry, ai, government.regulatory, finance |
| capability | verification, safety, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | hub |
| freshness | volatile |
| license | Apache-2.0 |



