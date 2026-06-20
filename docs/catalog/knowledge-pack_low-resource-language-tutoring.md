# Low-resource-language tutoring scaffold (Marathi, Swahili, Twi — school subjects)

*knowledge-pack* · `knowledge-pack/low-resource-language-tutoring` · v0.1.0 · experimental

Knowledge Corpus scaffold for tutoring school subjects (mathematics,
science, basic literacy) in low-resource languages including Marathi,
Swahili, and Twi. Provides key concept glossaries, worked example
templates, and curriculum alignment notes for standard primary/secondary
curricula in Maharashtra (India), East Africa, and West Africa respectively.
Designed to run entirely on-device; no cloud dependency.

HONEST INGESTION CONTRACT:
- Coverage is partial and curriculum-approximate. This corpus MUST be
  presented to students as supplementary, not authoritative.
- Subject-matter experts for each language community should review and
  extend entries before production use.
- Entries that are uncertain are flagged with "coverage: partial".
- No proprietary curriculum content is included; all entries derive from
  public-domain syllabi and open educational resources.

CAPABILITY LIFT (structural): frontier models have sparse training data
for low-resource languages, especially in school-subject domains. Marathi
STEM vocabulary, Twi arithmetic terminology, and Swahili science glossaries
are not well represented in public LLM training corpora. This corpus
provides the vocabulary layer that a base model lacks — the gap is
structural because it cannot close by scaling the model without acquiring
the missing training data (sparse_data mechanism). The corpus is an
on-device retrieval source available when network is absent.
lift_reason: no_addressable_source (offline) + sparse_data mechanism.

| axis | value |
|---|---|
| industry | education, education.k12, education.tutoring |
| capability | retrieval, translation, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | CC-BY-4.0 |



