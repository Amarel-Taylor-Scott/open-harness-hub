# Multi-source corroborate (a claim is corroborated only when >= N independent sources agree)

*processor* · `processor/multi-source-corroborate` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. Decides whether a claim is CORROBORATED by
requiring that at least N INDEPENDENT sources agree on it. A claim supported by
one source — or supported by several sources that share a single origin — is
NOT corroborated; a claim that any source contradicts is flagged. This is the
runtime form of the change-verification contract (docs/codex/
change-verification-contract.md): >= 2 independent agreeing sources, where one
source — or one agent's assertion — is not corroboration.

WHY THIS IS THE MOAT, NOT FAITHFULNESS: faithfulness-only RAG evaluation asks
"did the answer match the retrieved context". That passes even when the context
itself is a single unverified document (or a planted one — see
processor/corpus-integrity-check). This processor instead asks "do enough
INDEPENDENT sources agree that this claim is TRUE", which is the job a
faithfulness check structurally cannot do.

Procedure (deterministic over governed inputs):
  1. Group the supporting and contradicting evidence by the claim each piece
     asserts, every piece carrying its source_record (publisher, origin,
     content_hash — see schemas/source-record.schema.json).
  2. Collapse non-independence — evidence that traces to the SAME origin
     (same publisher, syndication root, or mirror) counts once, so a single
     story republished N times cannot manufacture corroboration. Independence
     is judged from governed provenance, not from text similarity.
  3. Count independent agreement against the declared threshold N (a governed
     parameter, default >= 2; a domain may raise it). Emit a corroboration
     verdict: corroborated | single_source | insufficient_independent |
     contradicted, each carrying the warrant (which independent sources agreed
     or disagreed, and on which field).
  4. Open a review_ticket when the verdict is single_source, contradicted, or
     insufficient_independent on a field declared must-verify.

This processor does NOT itself fetch the web; it adjudicates evidence already
gathered (e.g. by processor/web-search-verify and processor/authority-fetch-diff,
which run under their own external trust boundary). It is therefore a local
read-only decision over governed inputs.

GOVERNANCE (honest framing): this is a governed DEFINITION of an independent-
corroboration rule, not a measured-lift claim. It describes the independence
test, the threshold N, and the deterministic verdicts and warrants. It does NOT
assert a populated agreement rate or detection number. The implementation is
built by the code lane at the path below.

| axis | value |
|---|---|
| industry | cross_industry, ai, media.factcheck, government.regulatory |
| capability | verification, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | hub |
| freshness | volatile |
| license | Apache-2.0 |



