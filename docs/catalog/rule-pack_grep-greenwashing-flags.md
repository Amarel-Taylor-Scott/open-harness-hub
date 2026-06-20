# Greenwashing & vague-sustainability claim detectors

*rule-pack* · `rule-pack/grep-greenwashing-flags` · v0.1.0 · experimental

Regex heuristics flagging common greenwashing patterns in
sustainability disclosures, marketing materials, and product
claims. Aligned to:

 - UK CMA Green Claims Code (2021)
 - EU Empowering Consumers for the Green Transition Directive
   (2024/825)
 - EU Green Claims Directive (proposal 2023/0085)
 - FTC Green Guides (16 CFR Part 260)
 - Competition Bureau Canada Environmental Claims Guidance
 - SBTi Net-Zero Standard

Catches: vague aspirational language without methodology, "net-
zero" claims without scope/baseline/offset disclosure, comparative
claims without benchmark, future-tense commitments without interim
milestone, cherry-picked baselines, outdated assurance, hidden
trade-offs, irrelevant claims (e.g. "CFC-free" for a product class
where CFCs were banned 30 years ago).

FAST first-pass heuristics. Pair with
`persona/esg-pillar-analyst` for framework-aligned interpretation.

| axis | value |
|---|---|
| industry | esg, esg.csrd, sustainability, climate, media, media.factcheck |
| capability | safety_gating, classification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `grep`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `net_zero_no_scope` | critical | greenwashing.net_zero_unsubstantiated | `(?i)\b(net[- ]?zero|carbon[- ]?neutral|climate[- ]?neutral|carbon[- ]?negativ...` |
| `net_zero_no_target_year` | high | greenwashing.net_zero_no_target_year | `(?i)\b(net[- ]?zero|carbon[- ]?neutral)\b(?!.{0,200}\b(20[2-7]\d|by 20[2-7]\d...` |
| `offset_no_disclosure` | high | greenwashing.offset_unsubstantiated | `(?i)\b(offset|carbon credit|VCM|voluntary carbon market|nature-based solution...` |
| `vague_eco_friendly` | high | greenwashing.vague_aspirational | `(?i)\b(eco[- ]?friendly|environmentally[- ]friendly|green|sustainable|natural...` |
| `future_commit_no_milestone` | high | greenwashing.distant_target_no_interim | `(?i)\bby 20(4|5|6)\d\b(?!.{0,300}\b(interim|milestone|20[23]\d (target|goal)|...` |
| `best_in_class_no_benchmark` | high | greenwashing.comparative_no_benchmark | `(?i)\b(best[- ]in[- ]class|industry[- ]leading|world[- ]leading|category[- ]l...` |
| `cherry_picked_baseline` | medium | greenwashing.no_baseline | `(?i)\b(reduced?|cut|lowered)\b.{0,80}\bby \d{1,3}%\b(?!.{0,200}\b(baseline|si...` |
| `outdated_assurance` | high | greenwashing.outdated_assurance | `(?i)\b(audited|assured|verified|certified) (?:by [A-Z][a-zA-Z& ]+ )?(in |as o...` |
| `no_assurance_marker` | medium | esg.no_third_party_assurance | `(?i)\b(self[- ]reported|self[- ]declared|company-reported|management estimate...` |
| `scope3_excluded` | high | esg.scope3_exclusion_check_materiality | `(?i)\bscope\s*3\b.{0,200}\b(excluded|not included|out of scope|de minimis|imm...` |
| `irrelevant_claim_cfc` | medium | greenwashing.irrelevant_claim | `(?i)\b(CFC[- ]?free|chlorofluorocarbon[- ]?free|ozone[- ]friendly)\b` |
| `hidden_tradeoff_palm_oil` | high | greenwashing.hidden_tradeoff_palm_oil | `(?i)\b(palm oil|palm kernel oil|elaeis)\b(?!.{0,300}\b(RSPO|certified sustain...` |
| `renewable_no_RECs` | high | greenwashing.renewable_no_provenance | `(?i)\b(100%|fully|completely) renewable\b(?!.{0,200}\b(REC|guarantee of origi...` |
| `biodegradable_no_standard` | medium | greenwashing.recyclability_no_standard | `(?i)\b(biodegradable|compostable|recyclable|reusable)\b(?!.{0,200}\b(ASTM|D64...` |
| `diverse_no_metric` | medium | greenwashing.vague_DEI_claim | `(?i)\b(diverse|inclusive|equitable|representative) (workforce|leadership|boar...` |
| `human_rights_no_framework` | medium | greenwashing.vague_human_rights | `(?i)\b(respect (for )?human rights|human rights (policy|commitment|programme)...` |
| `sbti_no_validation` | high | greenwashing.sbti_unvalidated | `(?i)\b(science[- ]based target|SBTi[- ]aligned|1\.5°C aligned|Paris[- ]aligne...` |
| `scale_expansion_v1_critical_signal_01` | high | grep-greenwashing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_owner_gap_02` | medium | grep-greenwashing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evidenc...` |
| `scale_expansion_v1_deadline_risk_03` | medium | grep-greenwashing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_redaction_risk_04` | medium | grep-greenwashing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_benchmark_gap_05` | high | grep-greenwashing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_citation_gap_06` | high | grep-greenwashing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_severity_mismatch_07` | medium | grep-greenwashing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_missing_evidence_08` | medium | grep-greenwashing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_critical_signal_09` | medium | grep-greenwashing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_owner_gap_10` | high | grep-greenwashing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evidenc...` |
| `scale_expansion_v1_deadline_risk_11` | high | grep-greenwashing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_redaction_risk_12` | medium | grep-greenwashing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_benchmark_gap_13` | medium | grep-greenwashing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_citation_gap_14` | medium | grep-greenwashing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_severity_mismatch_15` | high | grep-greenwashing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_missing_evidence_16` | high | grep-greenwashing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_critical_signal_17` | medium | grep-greenwashing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_owner_gap_18` | medium | grep-greenwashing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evidenc...` |
| `scale_expansion_v1_deadline_risk_19` | medium | grep-greenwashing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_redaction_risk_20` | high | grep-greenwashing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_benchmark_gap_21` | high | grep-greenwashing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_citation_gap_22` | medium | grep-greenwashing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_severity_mismatch_23` | medium | grep-greenwashing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_missing_evidence_24` | medium | grep-greenwashing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_critical_signal_25` | high | grep-greenwashing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_owner_gap_26` | high | grep-greenwashing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evidenc...` |
| `scale_expansion_v1_deadline_risk_27` | medium | grep-greenwashing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_redaction_risk_28` | medium | grep-greenwashing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_benchmark_gap_29` | medium | grep-greenwashing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_citation_gap_30` | high | grep-greenwashing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_severity_mismatch_31` | high | grep-greenwashing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_missing_evidence_32` | medium | grep-greenwashing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v1_critical_signal_33` | medium | grep-greenwashing-flags.scale_expansion.critical_signal | `(?i)(?:critical.{0,24}signal|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:e...` |
| `scale_expansion_v1_owner_gap_34` | medium | grep-greenwashing-flags.scale_expansion.owner_gap | `(?i)(?:owner.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evidenc...` |
| `scale_expansion_v1_deadline_risk_35` | high | grep-greenwashing-flags.scale_expansion.deadline_risk | `(?i)(?:deadline.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_redaction_risk_36` | high | grep-greenwashing-flags.scale_expansion.redaction_risk | `(?i)(?:redaction.{0,24}risk|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:ev...` |
| `scale_expansion_v1_benchmark_gap_37` | medium | grep-greenwashing-flags.scale_expansion.benchmark_gap | `(?i)(?:benchmark.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evi...` |
| `scale_expansion_v1_citation_gap_38` | medium | grep-greenwashing-flags.scale_expansion.citation_gap | `(?i)(?:citation.{0,24}gap|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:evid...` |
| `scale_expansion_v1_severity_mismatch_39` | medium | grep-greenwashing-flags.scale_expansion.severity_mismatch | `(?i)(?:severity.{0,24}mismatch|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?...` |
| `scale_expansion_v1_missing_evidence_40` | high | grep-greenwashing-flags.scale_expansion.missing_evidence | `(?i)(?:missing.{0,24}evidence|grep.{0,24}greenwashing.{0,24}flags).{0,160}(?:...` |
| `scale_expansion_v2_unsupported_material_claim_001` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_002` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_003` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_004` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_005` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_006` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_007` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_008` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_009` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_010` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_011` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_012` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_013` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_014` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_015` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_016` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_017` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_018` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_019` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_020` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_021` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_022` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_023` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_024` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_025` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_026` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_027` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_028` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_029` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_030` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_031` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_032` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_033` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_034` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_035` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_036` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_037` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_038` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_039` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_040` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_041` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_042` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_043` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_044` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_045` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_046` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_047` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_048` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_049` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_050` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_051` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_052` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_053` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_054` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_055` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_056` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_057` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_058` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_059` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_060` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_061` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_062` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_063` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_064` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_065` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_066` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_067` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_068` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_069` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_070` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |
| `scale_expansion_v2_unsupported_material_claim_071` | low | grep-greenwashing-flags.scale_expansion_v2.unsupported_material_claim | `(?i)(?:unsupported.{0,32}material.{0,32}claim|material.{0,32}claim.{0,32}with...` |
| `scale_expansion_v2_missing_owner_072` | medium | grep-greenwashing-flags.scale_expansion_v2.missing_owner | `(?i)(?:missing.{0,32}owner|owner.{0,32}(?:not assigned|unknown|tbd)).{0,180}(...` |
| `scale_expansion_v2_stale_evidence_073` | medium | grep-greenwashing-flags.scale_expansion_v2.stale_evidence | `(?i)(?:stale.{0,32}evidence|evidence.{0,32}(?:expired|outdated|older than)).{...` |
| `scale_expansion_v2_redaction_leak_074` | high | grep-greenwashing-flags.scale_expansion_v2.redaction_leak | `(?i)(?:redaction.{0,32}(?:leak|failure)|(?:ssn|dob|patient|account).{0,32}vis...` |
| `scale_expansion_v2_citation_mismatch_075` | high | grep-greenwashing-flags.scale_expansion_v2.citation_mismatch | `(?i)(?:citation.{0,32}(?:mismatch|does not support|unsupported)|source.{0,32}...` |
| `scale_expansion_v2_benchmark_regression_076` | low | grep-greenwashing-flags.scale_expansion_v2.benchmark_regression | `(?i)(?:benchmark.{0,32}(?:regression|failure|delta)|score.{0,32}(?:dropped|de...` |
| `scale_expansion_v2_policy_exception_077` | medium | grep-greenwashing-flags.scale_expansion_v2.policy_exception | `(?i)(?:policy.{0,32}exception|exception.{0,32}(?:approved|pending|missing)).{...` |
| `scale_expansion_v2_escalation_overdue_078` | medium | grep-greenwashing-flags.scale_expansion_v2.escalation_overdue | `(?i)(?:escalation.{0,32}(?:overdue|missed|late)|sla.{0,32}(?:breach|missed))....` |
| `scale_expansion_v2_tool_side_effect_079` | high | grep-greenwashing-flags.scale_expansion_v2.tool_side_effect | `(?i)(?:tool.{0,32}(?:write|external_call|side effect)|side.{0,32}effect.{0,32...` |
| `scale_expansion_v2_context_poisoning_080` | high | grep-greenwashing-flags.scale_expansion_v2.context_poisoning | `(?i)(?:context.{0,32}(?:poison|injection|override)|retrieved.{0,32}doc.{0,32}...` |

