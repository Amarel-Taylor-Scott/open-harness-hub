# Real estate DD red-flag detectors

*rule-pack* · `rule-pack/grep-real-estate-dd-red-flags` · v0.1.0 · beta

GREP detectors for title/ESA/structural/zoning issues.

| axis | value |
|---|---|
| industry | real_estate, real_estate.due_diligence |
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
| `open_permit` | critical | real_estate.title.open_permit | `(?i)(?:open|expired|unresolved)\s+(?:building\s+)?permit` |
| `unrecorded_transfer` | critical | real_estate.title.unrecorded | `(?i)unrecorded\s+(?:transfer|deed|conveyance|mortgage)` |
| `mechanics_lien` | high | real_estate.title.mechanics_lien | `(?i)mechanic[''']?s?\s+lien|materialmen[''']?s\s+lien|construction\s+lien` |
| `environmental_rec` | critical | real_estate.environmental.rec | `(?i)(?<!no\s)(?<!no\sknown\s)(?<!no\sidentified\s)\b(?:recognized\s+environme...` |
| `vapor_intrusion` | high | real_estate.environmental.vapor_intrusion | `(?i)vapor\s+intrusion(?:\s+(?:concern|pathway))?` |
| `asbestos_lead_paint` | high | real_estate.environmental.acm_lbp | `(?i)\b(asbestos|lead[- ]?based\s+paint|acm|lbp)\s+(?:present|detected|suspect)` |
| `underground_storage_tank` | high | real_estate.environmental.ust | `(?i)\bust\b|underground\s+storage\s+tank|leaking\s+ust` |
| `unpermitted_alteration` | high | real_estate.zoning.unpermitted_alteration | `(?i)unpermitted\s+(?:alteration|addition|conversion|change\s+of\s+use)` |
| `co_expired` | critical | real_estate.zoning.no_co | `(?i)(?:certificate\s+of\s+occupancy|\bco\b)\s+(?:expired|revoked|not\s+issued)` |
| `pending_litigation` | high | real_estate.title.pending_litigation | `(?i)pending\s+(?:litigation|lawsuit|action|condemnation|eminent\s+domain)` |
| `foundation_issue` | high | real_estate.structural.foundation | `(?i)(?:foundation\s+(?:settlement|crack|movement|failure)|structural\s+integr...` |
| `roof_eol` | medium | real_estate.structural.roof | `(?i)roof\s+(?:end[- ]?of[- ]?life|past\s+useful\s+life|active\s+leaks?|deferr...` |
| `ada_noncompliance` | medium | real_estate.accessibility.ada | `(?i)ada\s+(?:noncompliance|violations?|barriers?)|not\s+ada[- ]?compliant` |
| `zoning_variance_lapsed` | high | real_estate.zoning.variance_lapsed | `(?i)variance\s+(?:lapsed|expired|conditions\s+not\s+met)|special\s+(?:use\s+)...` |
| `flood_zone_no_insurance` | medium | real_estate.environmental.flood_zone | `(?i)flood\s+zone\s+[A-Z]\d?(?!.{0,200}(?:flood\s+insurance|nfip))` |
| `scale_expansion_v1_critical_signal_01` | high | grep-real-estate-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red....` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-real-estate-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,24}...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-real-estate-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-real-estate-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-real-estate-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-real-estate-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-real-estate-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}re...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-real-estate-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-real-estate-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red....` |
| `scale_expansion_v1_owner_gap_10` | high | grep-real-estate-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,24}...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-real-estate-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-real-estate-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-real-estate-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-real-estate-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-real-estate-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}re...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-real-estate-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-real-estate-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red....` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-real-estate-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,24}...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-real-estate-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-real-estate-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-real-estate-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-real-estate-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-real-estate-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}re...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-real-estate-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-real-estate-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red....` |
| `scale_expansion_v1_owner_gap_26` | high | grep-real-estate-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,24}...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-real-estate-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-real-estate-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-real-estate-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-real-estate-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-real-estate-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}re...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-real-estate-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-real-estate-dd-red-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red....` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-real-estate-dd-red-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,24}...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-real-estate-dd-red-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-real-estate-dd-red-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-real-estate-dd-red-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-real-estate-dd-red-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red.{0,...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-real-estate-dd-red-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}re...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-real-estate-dd-red-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}real.{0,24}estate.{0,24}dd.{0,24}red...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-real-estate-dd-red-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-real-estate-dd-red-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-real-estate-dd-red-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

