# Risks and Gaps

From `architecture/risk_register.json`.

| Risk | Severity | Likelihood | Owner | Detection | Status |
|---|---|---|---|---|---|
| RISK-data-correctness | high | medium | verification_gate | `scripts/check_verification_gate.py` | mitigated |
| RISK-stale-fragile-facts | high | medium | fragile_fact_watchtower | `scripts/check_watchtower_minimum_freshness.py` | mitigated |
| RISK-unresolved-conflicts | high | medium | reconciliation | `scripts/check_cfpb_reconciliation.py` | mitigated |
| RISK-unstructured-parser-quality | medium | medium | unstructured_document_decomposition | `scripts/check_pipeline_unstructured.py` | accepted |
| RISK-tenant-isolation | critical | low | security_tenant_isolation | `scripts/check_tenant_isolation_policy.py` | mitigated |
| RISK-provider-dependency-drift | medium | high | provider_catalog | `scripts/check_repo_health_policy.py` | mitigated |
| RISK-monolith-api-server | medium | high | api_runtime | `scripts/check_monolith_allowlist.py` | open |
| RISK-worker-throughput | low | medium | workers | `scripts/check_durable_worker_parallel.py` | mitigated |
| RISK-dashboard-truth-leakage | high | low | ui_pages | `scripts/check_architecture_dashboard_projection_only.py` | mitigated |
| RISK-direct-provider-bypass | high | low | architecture_guardrails | `scripts/check_no_direct_provider_bypass.py` | mitigated |
| RISK-unproven-external-tools | medium | medium | provider_catalog | `scripts/check_no_uncataloged_github_repos.py` | mitigated |
| RISK-documentation-drift | medium | low | docs | `scripts/check_documentation_coverage.py` | mitigated |
| RISK-secret-leakage | critical | low | llm_gateway | `scripts/check_llm_secret_hygiene.py` | mitigated |
| RISK-consumption-serves-unsafe | critical | low | consumption_service | `scripts/check_consumption_blocks_bad_artifacts.py` | mitigated |
