# Vendor Onboarding Risk RAG retrieval policy

*rule-pack* · `rule-pack/rag-vendor-onboarding-risk-retrieval-policy` · v0.1.0 · experimental

Citation and retrieval policy for grounding vendor onboarding risk reviews.

| axis | value |
|---|---|
| industry | procurement.vendor_risk, compliance |
| capability | retrieval, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `rag`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `cite_operational_control` | high | - | `finding mentions policy, control, exception, incident, approval, or missing e...` |
| `surface_evidence_gap` | medium | - | `required packet component is missing or ambiguous` |
| `avoid_unverified_determination` | high | - | `classification would require facts not present in packet or retrieved context` |
| `scale_expansion_v1_evidence_matrix_01` | medium | - | `evidence matrix is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_escalation_path_02` | medium | - | `escalation path is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_benchmark_trace_03` | medium | - | `benchmark trace is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_packet_policy_04` | high | - | `packet policy is needed to support a finding, recommendation, citation, or be...` |
| `scale_expansion_v1_gap_split_05` | medium | - | `gap split is needed to support a finding, recommendation, citation, or benchm...` |
| `scale_expansion_v1_material_claim_06` | medium | - | `material claim is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_redaction_gate_07` | medium | - | `redaction gate is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_control_context_08` | high | - | `control context is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_evidence_matrix_09` | medium | - | `evidence matrix is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_escalation_path_10` | medium | - | `escalation path is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_benchmark_trace_11` | medium | - | `benchmark trace is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_packet_policy_12` | high | - | `packet policy is needed to support a finding, recommendation, citation, or be...` |
| `scale_expansion_v1_gap_split_13` | medium | - | `gap split is needed to support a finding, recommendation, citation, or benchm...` |
| `scale_expansion_v1_material_claim_14` | medium | - | `material claim is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_redaction_gate_15` | medium | - | `redaction gate is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_control_context_16` | high | - | `control context is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_evidence_matrix_17` | medium | - | `evidence matrix is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_escalation_path_18` | medium | - | `escalation path is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_benchmark_trace_19` | medium | - | `benchmark trace is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_packet_policy_20` | high | - | `packet policy is needed to support a finding, recommendation, citation, or be...` |
| `scale_expansion_v1_gap_split_21` | medium | - | `gap split is needed to support a finding, recommendation, citation, or benchm...` |
| `scale_expansion_v1_material_claim_22` | medium | - | `material claim is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_redaction_gate_23` | medium | - | `redaction gate is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_control_context_24` | high | - | `control context is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_evidence_matrix_25` | medium | - | `evidence matrix is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_escalation_path_26` | medium | - | `escalation path is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_benchmark_trace_27` | medium | - | `benchmark trace is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_packet_policy_28` | high | - | `packet policy is needed to support a finding, recommendation, citation, or be...` |
| `scale_expansion_v1_gap_split_29` | medium | - | `gap split is needed to support a finding, recommendation, citation, or benchm...` |
| `scale_expansion_v1_material_claim_30` | medium | - | `material claim is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_redaction_gate_31` | medium | - | `redaction gate is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_control_context_32` | high | - | `control context is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_evidence_matrix_33` | medium | - | `evidence matrix is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_escalation_path_34` | medium | - | `escalation path is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_benchmark_trace_35` | medium | - | `benchmark trace is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v1_packet_policy_36` | high | - | `packet policy is needed to support a finding, recommendation, citation, or be...` |
| `scale_expansion_v1_gap_split_37` | medium | - | `gap split is needed to support a finding, recommendation, citation, or benchm...` |
| `scale_expansion_v1_material_claim_38` | medium | - | `material claim is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_redaction_gate_39` | medium | - | `redaction gate is needed to support a finding, recommendation, citation, or b...` |
| `scale_expansion_v1_control_context_40` | high | - | `control context is needed to support a finding, recommendation, citation, or ...` |
| `scale_expansion_v2_evidence_matrix_001` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_002` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_003` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_004` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_005` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_006` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_007` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_008` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_009` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_010` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_011` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_012` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_013` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_014` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_015` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_016` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_017` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_018` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_019` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_020` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_evidence_matrix_021` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_022` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_023` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_024` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_025` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_026` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_027` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_028` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_029` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_030` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_031` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_032` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_033` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_034` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_035` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_036` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_037` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_038` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_039` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_040` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_evidence_matrix_041` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_042` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_043` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_044` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_045` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_046` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_047` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_048` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_049` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_050` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_051` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_052` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_053` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_054` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_055` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_056` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_057` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_058` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_059` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_060` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_evidence_matrix_061` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_062` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_063` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_064` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_065` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_066` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_067` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_068` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_069` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_070` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_071` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_072` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_073` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_074` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_075` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_076` | low | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_077` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_078` | medium | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_079` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_080` | high | rag-vendor-onboarding-risk-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |

