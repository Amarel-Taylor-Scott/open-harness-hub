# Cloud provider secret detectors

*rule-pack* · `rule-pack/grep-cloud-secrets` · v0.1.0 · beta

Detection patterns for cloud-provider access keys and service-account
credentials — AWS, GCP, Azure, DigitalOcean, OCI. Converged from
gitleaks (`config/gitleaks.toml`), trufflehog (`pkg/detectors/`), and
GitHub's native secret-scanning partner program.

Critical-severity by default — any match is a hard block on input or
output. Verify against a Luhn / mod-N / live-call validator before
alerting to reduce false positives in production.

| axis | value |
|---|---|
| industry | security, cross_industry, ai |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `aws_access_key` | critical | secret.aws | `\b(AKIA|ASIA)[0-9A-Z]{16}\b` |
| `aws_secret_key` | critical | secret.aws | `(?i)aws(.{0,20})?(secret|access)?[_\-]?key([_\-]?id)?["'\s:=]{0,5}[A-Za-z0-9/...` |
| `gcp_service_account_json` | critical | secret.gcp | `"type": "service_account"` |
| `gcp_api_key` | high | secret.gcp | `\bAIza[0-9A-Za-z\-_]{35}\b` |
| `azure_storage_connection` | critical | secret.azure | `DefaultEndpointsProtocol=https;AccountName=[A-Za-z0-9]+;AccountKey=[A-Za-z0-9...` |
| `azure_sas_token` | high | secret.azure | `sig=[A-Za-z0-9%]{40,}&sv=\d{4}-\d{2}-\d{2}` |
| `digitalocean_pat` | critical | secret.digitalocean | `\bdop_v1_[a-f0-9]{64}\b` |
| `oci_credentials_marker` | high | secret.oci | `(?i)\b(ocid1\.tenancy|ocid1\.user)\.oc1\.\.[a-z0-9]{60,}\b` |
| `cloudflare_api_token` | high | secret.cloudflare | `\bcf-[A-Za-z0-9_-]{40}\b|\bCFPAT-[A-Za-z0-9_-]{40,}\b` |
| `heroku_api_key` | high | secret.heroku | `(?i)heroku(.{0,20})?[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{...` |

