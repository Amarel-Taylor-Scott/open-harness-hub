# Cross-source reconcile (conflicting authorities — reconcile, then escalate to a human)

*processor* · `processor/cross-source-reconcile` · v0.1.0 · experimental

CONTEXT-ASSURANCE component. When two or more REGISTERED authoritative
sources disagree on the same fact, this processor reconciles them by governed
precedence rules and, when reconciliation is not deterministic, escalates to a
human adjudicator rather than silently picking one. This is the
conflicting-authority axis of context assurance.

WORKED PROBLEM (agri-food double-submission): the same consignment / record is
submitted to two authoritative systems and the two systems hold conflicting
values for the same field (quantity, grade, certificate status). A naive RAG
pipeline retrieves whichever source ranks higher and serves a confidently
wrong answer. This processor surfaces the conflict explicitly and routes it.

Reconciliation procedure (deterministic over governed inputs):
  1. Align — group competing claims by the field they assert, each claim
     carrying its source_record (publisher, trust_tier, effective_date,
     content_hash — see schemas/source-record.schema.json).
  2. Apply precedence — governed, declared precedence rules only:
     higher trust_tier wins; on equal tier, the later effective_date wins;
     precedence is data, not an LLM guess.
  3. Resolve or escalate — if precedence yields a single winner, emit a
     reconciled value WITH its warrant (which source won and why). If
     precedence is ambiguous (equal tier and equal/unknown effective_date, or
     a declared must-escalate field), emit no winner and open a review_ticket
     routing the conflict to a human adjudicator (escalate.human path).

GOVERNANCE (honest framing): this is a governed DEFINITION of a reconciliation
+ escalation policy, not a measured-lift claim. It describes the conflict
object, the deterministic precedence rules, and the human-escalation boundary.
It does NOT assert a populated accuracy number. The differentiator versus
faithfulness-only retrieval is that the conflict between authorities is made
explicit and adjudicated under governance rather than hidden by ranking.

| axis | value |
|---|---|
| industry | cross_industry, agriculture, government.regulatory, supply_chain |
| capability | verification, governance, routing |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | hub |
| freshness | volatile |
| license | Apache-2.0 |



