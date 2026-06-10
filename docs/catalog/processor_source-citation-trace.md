# Source citation trace (trace every claim in an answer to a cited source; flag unsupported claims)

*processor* · `processor/source-citation-trace` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. Decomposes a generated answer into its individual
CLAIMS and traces each one to a CITED source, flagging any claim that no cited
source supports. It is the attribution-coverage axis: an answer can read fluent
and even cite documents while still containing sentences that the cited
documents never support (the dangling-citation / unsupported-claim failure).

WHY THIS AXIS: faithfulness scored at the whole-answer level can pass while a
minority of load-bearing sentences are uncited or mis-cited. Tracing at the
per-claim grain makes attribution auditable: every asserted fact must point at
a source span, and the gaps are named rather than averaged away.

Procedure (deterministic over governed inputs):
  1. Segment the answer into atomic claims (one assertion each), preserving the
     inline citation markers the answer attached to each claim.
  2. Resolve each cited marker to a governed source span — the cited
     source_record and the specific passage relied on (publisher, source_url,
     content_hash, span offsets — see schemas/source-record.schema.json).
  3. Score support per claim:
       - supported — a resolved cited span asserts the claim;
       - unsupported — the claim carries no citation, or its citation resolves
         to a span that does not assert it (mis-citation);
       - uncited — the claim has no citation marker at all.
  4. Emit per-claim trace rows (claim text -> source span -> support status),
     a citation-coverage summary (supported vs unsupported vs uncited counts),
     and a review_ticket when any claim on a declared must-cite field is
     unsupported or uncited.

This processor checks ATTRIBUTION — that each claim is tied to the source it
cites. It does not by itself establish that the cited source is TRUE or current;
truth/independence is the job of processor/multi-source-corroborate and
processor/claim-refute, and freshness/contradiction of the cited authority is
the job of processor/authority-fetch-diff. It is a local, read-only,
deterministic decision over the answer and its citations; it makes no external
calls.

GOVERNANCE (honest framing): this is a governed DEFINITION of a per-claim
citation-trace policy, not a measured-lift claim. It describes the claim
segmentation, the citation-to-source-span resolution, the support statuses, and
the deterministic warrant (which span did or did not support each claim). It
does NOT assert a populated coverage or hallucination-rate number.

| axis | value |
|---|---|
| industry | cross_industry, ai, media.factcheck, legal.compliance |
| capability | verification, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | hub |
| freshness | volatile |
| license | Apache-2.0 |



