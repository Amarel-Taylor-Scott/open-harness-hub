# VCS platform PATs (GitHub, GitLab, Bitbucket, Atlassian)

*rule-pack* · `rule-pack/grep-vcs-platform-pats` · v0.1.0 · beta

Detection patterns for Personal Access Tokens issued by code-hosting
platforms. Each vendor uses a stable prefix (`ghp_`, `gho_`, `ghu_`,
`ghs_`, `ghr_` for GitHub; `glpat-` for GitLab; `ATATT3` for
Atlassian/Jira; `BBDC-` for Bitbucket Cloud).

| axis | value |
|---|---|
| industry | security, software |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `github_pat_classic` | critical | secret.github | `\bghp_[A-Za-z0-9]{36,}\b` |
| `github_pat_finegrained` | critical | secret.github | `\bgithub_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}\b` |
| `github_oauth_token` | critical | secret.github | `\bgho_[A-Za-z0-9]{36,}\b` |
| `github_user_to_server` | critical | secret.github | `\bghu_[A-Za-z0-9]{36,}\b` |
| `github_server_to_server` | critical | secret.github | `\bghs_[A-Za-z0-9]{36,}\b` |
| `github_refresh` | high | secret.github | `\bghr_[A-Za-z0-9]{76}\b` |
| `gitlab_pat` | critical | secret.gitlab | `\bglpat-[A-Za-z0-9_\-]{20}\b` |
| `atlassian_token` | critical | secret.atlassian | `\bATATT3[A-Za-z0-9_=\-]{180,}\b` |
| `bitbucket_app_password` | high | secret.bitbucket | `\bBBDC-[A-Za-z0-9+/=]{40,}\b` |
| `npm_token` | critical | secret.npm | `\bnpm_[A-Za-z0-9]{36}\b` |
| `pypi_token` | critical | secret.pypi | `\bpypi-AgEIcHlwaS5vcmcC[A-Za-z0-9_\-]+\b` |

