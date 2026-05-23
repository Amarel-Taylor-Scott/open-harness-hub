# Private key block detectors

*rule-pack* · `rule-pack/grep-private-key-blocks` · v0.1.0 · stable

Detection patterns for PEM-encoded private keys (RSA, EC, DSA,
OpenSSH, PGP) and modern formats (Age, Sigstore). Any match is a
critical-severity hit — full revocation + key rotation required.

| axis | value |
|---|---|
| industry | security, cross_industry |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `pem_rsa_private` | critical | secret.private_key | `-----BEGIN RSA PRIVATE KEY-----` |
| `pem_ec_private` | critical | secret.private_key | `-----BEGIN EC PRIVATE KEY-----` |
| `pem_dsa_private` | critical | secret.private_key | `-----BEGIN DSA PRIVATE KEY-----` |
| `pem_openssh_private` | critical | secret.private_key | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `pem_generic_private` | critical | secret.private_key | `-----BEGIN PRIVATE KEY-----` |
| `pgp_private_block` | critical | secret.private_key | `-----BEGIN PGP PRIVATE KEY BLOCK-----` |
| `age_secret_key` | critical | secret.age | `\bAGE-SECRET-KEY-1[QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7L]{58}\b` |
| `ssh_pem_encrypted` | critical | secret.private_key | `-----BEGIN ENCRYPTED PRIVATE KEY-----` |
| `jwt_signing_key_marker` | high | secret.signing | `(?i)(signing[_\-]?key|jwt[_\-]?secret)\s*[:=]\s*["'][A-Za-z0-9+/=]{32,}["']` |
| `id_rsa_filename_reference` | medium | secret.private_key | `\b(id_rsa|id_ed25519|id_ecdsa|id_dsa)(?:\.pub)?\b` |

