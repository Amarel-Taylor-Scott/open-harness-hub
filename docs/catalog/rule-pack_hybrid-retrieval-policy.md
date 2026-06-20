# Hybrid retrieval policy (BM25 + dense + RRF)

*rule-pack* · `rule-pack/hybrid-retrieval-policy` · v0.1.0 · beta

A RAG retrieval policy pack: BM25 sparse + dense vector + Reciprocal
Rank Fusion + optional cross-encoder reranking + 1-hop citation
graph expansion. Pipelines and harnesses reference this pack to keep
retrieval behaviour consistent across the catalog.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | retrieval |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



**family:** `rag`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `bm25_default` | info | retrieval.sparse | `bm25(k1=1.2, b=0.75)` |
| `dense_optional` | info | retrieval.dense | `dense(embedder='processor/embedder-minilm', top_k=20)` |
| `rrf_merge` | info | retrieval.fusion | `rrf(k=60, top_k=10)` |
| `rerank_optional` | info | retrieval.rerank | `rerank(model='processor/cross-encoder-reranker', top_k=10, output_k=5)` |
| `citation_graph_expand` | info | retrieval.graph | `citation_graph(hops=1, max_expand=5)` |
| `redact_chunks_if_pii` | high | retrieval.safety | `redact(rule_pack='rule-pack/privacy-pii-text-en')` |
| `freshness_window_default` | info | retrieval.freshness | `freshness_days=180` |
| `top_k_default` | info | retrieval.budget | `top_k=10` |
| `max_chunk_tokens_default` | info | retrieval.budget | `max_chunk_tokens=512` |
| `min_score_threshold` | low | retrieval.quality | `min_score=0.30` |
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
| `scale_expansion_v2_evidence_matrix_001` | low | hybrid-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_002` | medium | hybrid-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_003` | medium | hybrid-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_004` | high | hybrid-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_005` | high | hybrid-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_006` | low | hybrid-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_007` | medium | hybrid-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_008` | medium | hybrid-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_009` | high | hybrid-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_010` | high | hybrid-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_011` | low | hybrid-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_012` | medium | hybrid-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_013` | medium | hybrid-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_014` | high | hybrid-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_015` | high | hybrid-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_016` | low | hybrid-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_017` | medium | hybrid-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_018` | medium | hybrid-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_019` | high | hybrid-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_020` | high | hybrid-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_evidence_matrix_021` | low | hybrid-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_022` | medium | hybrid-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_023` | medium | hybrid-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_024` | high | hybrid-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_025` | high | hybrid-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_026` | low | hybrid-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_027` | medium | hybrid-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_028` | medium | hybrid-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_029` | high | hybrid-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_030` | high | hybrid-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_031` | low | hybrid-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_032` | medium | hybrid-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_033` | medium | hybrid-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_034` | high | hybrid-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_035` | high | hybrid-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_036` | low | hybrid-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_037` | medium | hybrid-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_038` | medium | hybrid-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_039` | high | hybrid-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_040` | high | hybrid-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_evidence_matrix_041` | low | hybrid-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_042` | medium | hybrid-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_043` | medium | hybrid-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_044` | high | hybrid-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_045` | high | hybrid-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_046` | low | hybrid-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_047` | medium | hybrid-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_048` | medium | hybrid-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_049` | high | hybrid-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_050` | high | hybrid-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_051` | low | hybrid-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_052` | medium | hybrid-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_053` | medium | hybrid-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_054` | high | hybrid-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_055` | high | hybrid-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_056` | low | hybrid-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_057` | medium | hybrid-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_058` | medium | hybrid-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_059` | high | hybrid-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_060` | high | hybrid-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_evidence_matrix_061` | low | hybrid-retrieval-policy.scale_expansion_v2.evidence_matrix | `evidence matrix context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_source_freshness_062` | medium | hybrid-retrieval-policy.scale_expansion_v2.source_freshness | `source freshness context is required to support a material finding, remediati...` |
| `scale_expansion_v2_policy_exception_063` | medium | hybrid-retrieval-policy.scale_expansion_v2.policy_exception | `policy exception context is required to support a material finding, remediati...` |
| `scale_expansion_v2_owner_routing_064` | high | hybrid-retrieval-policy.scale_expansion_v2.owner_routing | `owner routing context is required to support a material finding, remediation,...` |
| `scale_expansion_v2_redaction_gate_065` | high | hybrid-retrieval-policy.scale_expansion_v2.redaction_gate | `redaction gate context is required to support a material finding, remediation...` |
| `scale_expansion_v2_citation_support_066` | low | hybrid-retrieval-policy.scale_expansion_v2.citation_support | `citation support context is required to support a material finding, remediati...` |
| `scale_expansion_v2_benchmark_trace_067` | medium | hybrid-retrieval-policy.scale_expansion_v2.benchmark_trace | `benchmark trace context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_control_crosswalk_068` | medium | hybrid-retrieval-policy.scale_expansion_v2.control_crosswalk | `control crosswalk context is required to support a material finding, remediat...` |
| `scale_expansion_v2_packet_completeness_069` | high | hybrid-retrieval-policy.scale_expansion_v2.packet_completeness | `packet completeness context is required to support a material finding, remedi...` |
| `scale_expansion_v2_human_escalation_070` | high | hybrid-retrieval-policy.scale_expansion_v2.human_escalation | `human escalation context is required to support a material finding, remediati...` |
| `scale_expansion_v2_tool_permission_071` | low | hybrid-retrieval-policy.scale_expansion_v2.tool_permission | `tool permission context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_data_lineage_072` | medium | hybrid-retrieval-policy.scale_expansion_v2.data_lineage | `data lineage context is required to support a material finding, remediation, ...` |
| `scale_expansion_v2_negative_fixture_073` | medium | hybrid-retrieval-policy.scale_expansion_v2.negative_fixture | `negative fixture context is required to support a material finding, remediati...` |
| `scale_expansion_v2_counter_evidence_074` | high | hybrid-retrieval-policy.scale_expansion_v2.counter_evidence | `counter evidence context is required to support a material finding, remediati...` |
| `scale_expansion_v2_deadline_obligation_075` | high | hybrid-retrieval-policy.scale_expansion_v2.deadline_obligation | `deadline obligation context is required to support a material finding, remedi...` |
| `scale_expansion_v2_risk_threshold_076` | low | hybrid-retrieval-policy.scale_expansion_v2.risk_threshold | `risk threshold context is required to support a material finding, remediation...` |
| `scale_expansion_v2_decision_record_077` | medium | hybrid-retrieval-policy.scale_expansion_v2.decision_record | `decision record context is required to support a material finding, remediatio...` |
| `scale_expansion_v2_appeal_path_078` | medium | hybrid-retrieval-policy.scale_expansion_v2.appeal_path | `appeal path context is required to support a material finding, remediation, c...` |
| `scale_expansion_v2_retrieval_boundary_079` | high | hybrid-retrieval-policy.scale_expansion_v2.retrieval_boundary | `retrieval boundary context is required to support a material finding, remedia...` |
| `scale_expansion_v2_gap_taxonomy_080` | high | hybrid-retrieval-policy.scale_expansion_v2.gap_taxonomy | `gap taxonomy context is required to support a material finding, remediation, ...` |

