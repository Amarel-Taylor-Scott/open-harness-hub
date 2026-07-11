# Anti-pattern: No audit trace

*pattern* · `pattern/anti-no-audit-trace` · v0.1.0 · stable

Pipeline returns a verdict (approved / denied / NO-GO / critical-finding) without logging which step produced it, which model arm answered, which evidence was retrieved, what prompts were used, which rubric version applied. Regulators ask 'how did you decide' and the answer is 'GPT said so.'

| axis | value |
|---|---|
| industry | cross_industry, compliance |
| capability | evaluation, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



