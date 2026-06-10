# NIST CSRC publications walker

*processor* · `processor/nist-publications-walker` · v0.1.0 · experimental

Walks the NIST Computer Security Resource Center publication catalog
(csrc.nist.gov) and yields one structured knowledge node per
publication. Series supported:

 - SP 800-series  — Special Publications (FedRAMP, FISMA, AI RMF anchor)
 - SP 1800-series — NCCoE practice guides
 - SP 500-series  — Information technology
 - AI series      — NIST AI publications (AI 100, AI 200, AI RMF)
 - IR / NISTIR    — Internal reports
 - FIPS           — Federal Information Processing Standards

Each node carries: pub_id (e.g. "NIST SP 800-53 Rev. 5"), series, title,
summary, status (final/draft/withdrawn), issued_date, canonical_url,
pdf_url.

Default filters: status=final only.

Designed to feed `harness/draft-manifest-author` so each publication
becomes a candidate knowledge-pack entry (the publication's scope) +
candidate rubric (where the publication defines controls) + candidate
rule-pack (where the publication enumerates checks).

Source: NIST publications are public-domain.

| axis | value |
|---|---|
| industry | cyber, ai_governance, ai_governance.nist_rmf, compliance |
| capability | retrieval, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



