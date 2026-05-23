# HR hiring bias detectors (Title VII / ADA / ADEA / EEOC)

*rule-pack* · `rule-pack/grep-hr-hiring-bias-flags` · v0.1.0 · beta

GREP detectors for biased language in job postings + screening
questions. Each rule cites the protected-class statute. TRIGGER
review — never autoreject; recommend neutral language.

| axis | value |
|---|---|
| industry | hr, hr.hiring, compliance |
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
| `gendered_terms` | high | hr.bias.gendered_language | `(?i)\b(rockstar|ninja|guru|wizard|chairman|chairwoman|salesman|saleswoman|ste...` |
| `age_proxies` | high | hr.bias.age_proxy.adea | `(?i)\b(digital native|recent grad(?:uate)?|young dynamic team|fresh|energetic...` |
| `ableist_must_be_able` | medium | hr.bias.ableist.ada | `(?i)must\s+be\s+able\s+to\s+(?:lift|stand|walk|see|hear|speak|drive)(?!.{0,20...` |
| `discriminate_explicit_class` | critical | hr.bias.explicit_class_preference | `(?i)(?:looking\s+for|seeking|prefer)\s+(?:a\s+)?(?:woman|man|female|male|youn...` |
| `national_origin_proxy` | high | hr.bias.national_origin | `(?i)\bnative\s+(?:english\s+)?speaker(?!.{0,80}fluent|.{0,80}c[12])|us[- ]?ba...` |
| `pregnancy_proxy` | critical | hr.bias.pregnancy.pwfa | `(?i)(?:no\s+plans?\s+for\s+children|family\s+commitments\s+(?:must\s+not|won'...` |
| `salary_history_question` | medium | hr.bias.salary_history.equal_pay_act | `(?i)(?:what\s+(?:was|is)\s+your\s+(?:current|prior|previous|last)\s+(?:salary...` |
| `genetic_question` | critical | hr.bias.genetic.gina | `(?i)(?:family\s+(?:medical|health)\s+history|genetic\s+(?:condition|disease|d...` |
| `criminal_history_blanket` | medium | hr.bias.criminal_history.blanket | `(?i)(?:must\s+have|require)\s+(?:no|clean)\s+criminal\s+(?:history|record)(?!...` |
| `no_eeo_statement` | high | hr.bias.no_eeo_statement | `(?i)\b(?:no|absent)\s+(?:eeo|equal\s+(?:opportunity|employment))\s+statement\...` |
| `degree_required_unjustified` | low | hr.bias.degree_unjustified | `(?i)(?:bachelor'?s|master'?s|degree)\s+required(?!.{0,400}(?:equivalent\s+exp...` |

