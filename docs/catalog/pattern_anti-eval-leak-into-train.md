# Anti-pattern: Evaluation set leaked into training data

*pattern* · `pattern/anti-eval-leak-into-train` · v0.1.0 · stable

Benchmark records (or close paraphrases) end up in training corpus — fine-tune, RAG index, exemplar set. Reported scores inflate; downstream consumer cannot trust the benchmark; eval becomes marketing instead of measurement.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | evaluation |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



