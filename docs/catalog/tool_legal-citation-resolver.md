# Legal citation resolver (statute / case / regulation)

*tool* · `tool/legal-citation-resolver` · v0.1.0 · experimental

Resolve a legal citation string to its canonical metadata + best-
effort source URL. Handles:

 - US federal statutes: "42 U.S.C. § 1983"
 - US federal regulations: "29 C.F.R. § 1910.132"
 - US Supreme Court: "Loper Bright Enterprises v. Raimondo, 603 U.S. ___ (2024)"
 - US Circuit / District: "Smith v. Jones, 999 F.3d 1234 (5th Cir. 2024)"
 - State statutes: "Cal. Penal Code § 187"
 - UK statutes: "Human Rights Act 1998, s 3"
 - UK cases (neutral citation): "Pepper v Hart [1993] AC 593"
 - EU directives: "Directive 2024/1760"
 - EU regulations: "Regulation (EU) 2023/1115"
 - Bluebook short forms: "id.", "supra note 4"

Returns structured metadata: jurisdiction, source type, identifier
parts, canonical URL (when known), and a confidence score for the
parse. Does NOT verify that the cited authority says what the
citing source claims it says — that requires the
`processor/llm-judge` step against the actual text.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government |
| capability | extraction, verification |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



