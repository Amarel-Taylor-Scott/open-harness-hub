# Semgrep SAST proxy (CWE-tagged code findings)

*tool* · `tool/semgrep-sast-proxy` · v0.1.0 · stable

Proxy to Semgrep CLI for static-analysis code scanning. Used by
`pipeline/code-security-review` to corroborate GREP findings with
a real SAST tool that has community-maintained rules and proper
AST analysis. Returns CWE-tagged findings with file:line refs.

Implementation defers to local semgrep CLI; no network egress.

| axis | value |
|---|---|
| industry | security, security.appsec, software |
| capability | verification, classification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



