# Academic integrity red-flag detectors (plagiarism / AI / fabricated citations)

*rule-pack* · `rule-pack/grep-academic-integrity-flags` · v0.1.0 · beta

Heuristic detectors for academic integrity violations. Designed
to TRIGGER deep review (similarity check + AI detector + citation
DB lookup) — not to determine guilt directly.

| axis | value |
|---|---|
| industry | education, education.higher, compliance |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `as_an_ai_language_model` | critical | academic_integrity.ai_artefact_phrase | `(?i)\bas an ai (?:language )?model\b|\bas a large language model\b|i'm an ai\...` |
| `i_cannot_provide_personal_opinion` | high | academic_integrity.ai_canned_disclaimer | `(?i)i (?:cannot|do not have the ability to|am unable to) (?:provide|express|h...` |
| `ai_safe_response_disclaimer` | low | academic_integrity.ai_filler_phrase | `(?i)it'?s important to note that|please note that|it is worth (?:noting|menti...` |
| `future_knowledge_cutoff` | critical | academic_integrity.ai_self_reference | `(?i)(?:my|knowledge) (?:training|knowledge) cutoff (?:is|was)|as of (?:my|the...` |
| `fabricated_doi` | low | academic_integrity.candidate_doi | `(?i)10\.\d{4,9}/[-._;()/:A-Z0-9]+` |
| `fabricated_arxiv` | low | academic_integrity.candidate_arxiv | `(?i)arxiv:\s*\d{4}\.\d{4,5}(?:v\d+)?|arxiv\.org/abs/\d{4}\.\d{4,5}` |
| `block_quote_no_attribution` | medium | academic_integrity.block_quote_no_cite | `(?:^|\n)\s{4,}[A-Z][^\n]{200,}(?!.{0,80}(\(\w+,?\s*\d{4}\)|\bcited\b|\baccord...` |
| `repeated_filler_phrase` | low | academic_integrity.ai_filler_pattern | `(?i)(in conclusion|to summarize|in summary|moreover|furthermore|additionally|...` |
| `perfect_paragraph_lengths` | low | academic_integrity.suspicious_paragraph_uniformity | `(?:^|\n)([A-Z][^\n]{180,260}\.)\n([A-Z][^\n]{180,260}\.)\n([A-Z][^\n]{180,260...` |

