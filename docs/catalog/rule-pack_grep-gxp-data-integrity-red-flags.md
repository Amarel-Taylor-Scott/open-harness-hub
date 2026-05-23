# GxP data-integrity red-flag detectors (21-CFR-11 / ALCOA+)

*rule-pack* · `rule-pack/grep-gxp-data-integrity-red-flags` · v0.1.0 · beta

GREP detectors for the highest-leverage 21-CFR-11 + ALCOA+ data-
integrity violations: missing audit trails, shared accounts, post-
hoc record alteration, validation gaps, missing electronic-
signature meaning, missing reason-for-change, manual data
transcription without verification. Pair with
`pipeline/gxp-validation-review`.

| axis | value |
|---|---|
| industry | pharma, pharma.gxp, compliance |
| capability | safety_gating, classification, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `audit_trail_disabled` | critical | gxp.audit_trail.disabled | `(?i)audit[- ]?trail\s+(?:disabled|turned\s+off|switched\s+off|not\s+(?:enable...` |
| `shared_account` | critical | gxp.shared_account | `(?i)(?:(?<!no\s)(?<!none\s)(?<!zero\s)(shared|generic|group|admin)\s+(?:accou...` |
| `post_hoc_alteration` | critical | gxp.post_hoc_alteration | `(?i)(modify|update|alter|edit|correct).*(?:past|prior|previous|already[- ]?(?...` |
| `validation_missing` | high | gxp.validation.missing | `(?i)(not[- ]?validated|validation\s+(?:not\s+(?:performed|complete)|pending|o...` |
| `missing_reason_for_change` | high | gxp.reason_for_change.missing | `(?i)(change|modification|edit|amendment)\s+without\s+(?:reason|justification|...` |
| `missing_signature_meaning` | high | gxp.signature.no_meaning | `(?i)e[- ]?signature.{0,80}without\s+(?:meaning|purpose|review|approval|author...` |
| `single_factor_signature` | high | gxp.signature.single_factor | `(?i)e[- ]?signature\s+via\s+password\s+only|single[- ]?factor\s+signature|pas...` |
| `manual_transcription_unverified` | medium | gxp.manual_transcription.unverified | `(?i)(manual|hand)\s+(?:transcription|entry|re[- ]?keying)\s+(?:from|of)\s+(?:...` |
| `backup_treated_as_archive` | medium | gxp.backup_not_archive | `(?i)backup\s+(?:is|serves\s+as|acts\s+as|replaces)\s+archive|no\s+separate\s+...` |
| `dynamic_record_static_export` | high | gxp.dynamic_record_flattened | `(?i)dynamic\s+record\s+(?:exported|archived)\s+as\s+(?:pdf|static|image)(?!.{...` |
| `test_data_in_production` | medium | gxp.test_data_in_prod | `(?i)test\s+data\s+in\s+(?:production|live|prod)|prod.*populated\s+with\s+test` |
| `unrestricted_blank_template` | medium | gxp.uncontrolled_template | `(?i)blank\s+(?:record|template|form)\s+(?:not\s+(?:numbered|controlled)|freel...` |
| `missing_audit_trail_review` | high | gxp.audit_trail.unreviewed | `(?i)audit[- ]?trail\s+(?:not\s+reviewed|review\s+(?:not\s+performed|skipped|d...` |

