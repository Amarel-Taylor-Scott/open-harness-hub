#!/usr/bin/env python3
"""Generate marketplace and registry source-surface primitive factory seeds."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/marketplace-primitive-source-surfaces")
SOURCE_STATUS = "marketplace_seed_needs_source_ref_resolution"
COMMON_ROW = {"candidate": True, "serves_truth": False, "source_refs": [], "source_evidence_status": SOURCE_STATUS}

SURFACES: list[dict[str, Any]] = [
    {
        "source_surface_id": "market:mcp_registry",
        "rank": 1,
        "title": "MCP registry and MCP server catalogs",
        "marketplace_kind": "agent_tool_registry",
        "input_edge": "McpServerMetadata+ToolSchema+AuthPolicy",
        "output_edge": "ToolPrimitiveCard+ConnectionReceipt",
        "runtime_targets": ["mcp.client", "agent_tool_runtime"],
        "effects": ["artifact_write", "tool_connection_optional"],
        "candidate_outputs": ["ToolPrimitiveCard", "EffectSet", "ConnectionReceipt", "ProofObligationSet"],
        "proof_requirements": ["server_source_ref", "tool_schema_validation", "sandboxed_call_test", "effect_classification"],
    },
    {
        "source_surface_id": "market:apis_guru_openapi",
        "rank": 2,
        "title": "APIs.guru and OpenAPI directories",
        "marketplace_kind": "api_spec_registry",
        "input_edge": "OpenApiOperationObject+AuthPolicy+RuntimePolicy",
        "output_edge": "ApiEndpointPrimitiveCard+ToolSchema+ProofPlan",
        "runtime_targets": ["api.client", "mcp.tool", "serverless_function_optional"],
        "effects": ["artifact_write"],
        "candidate_outputs": ["EndpointPrimitiveCard", "ToolSchema", "RuntimeWrapperCandidate", "ProofObligationSet"],
        "proof_requirements": ["schema_validation", "auth_scope_review", "rate_limit_review", "error_model_check"],
    },
    {
        "source_surface_id": "market:postman_api_network",
        "rank": 3,
        "title": "Postman API Network and public collections",
        "marketplace_kind": "api_collection_registry",
        "input_edge": "ApiCollection+EnvironmentPolicy+AuthPolicy",
        "output_edge": "ApiWorkflowPrimitiveCandidateSet+CollectionReceipt",
        "runtime_targets": ["api.client", "test_runner", "mcp.tool"],
        "effects": ["artifact_write", "network_call_optional"],
        "candidate_outputs": ["ApiCallPrimitive", "ContractTestArtifact", "ExampleSet", "ProofObligationSet"],
        "proof_requirements": ["collection_source_ref", "request_schema_check", "example_request_test_optional", "secret_placeholder_check"],
    },
    {
        "source_surface_id": "market:terraform_registry",
        "rank": 4,
        "title": "Terraform Registry",
        "marketplace_kind": "iac_module_registry",
        "input_edge": "TerraformModuleRef+VariableMap+WorkspacePolicy",
        "output_edge": "TerraformPlanOrApplyReceipt+CloudResourceRefs",
        "runtime_targets": ["terraform", "ci_cd", "container"],
        "effects": ["cloud_resource_create_optional", "state_write", "network_call"],
        "candidate_outputs": ["IaCModulePrimitive", "DeploymentRecipe", "PolicyObligation", "DriftCheckPlan"],
        "proof_requirements": ["terraform_validate", "terraform_plan", "variable_schema_check", "policy_check"],
    },
    {
        "source_surface_id": "market:pulumi_registry",
        "rank": 5,
        "title": "Pulumi Registry",
        "marketplace_kind": "iac_component_registry",
        "input_edge": "PulumiPackageOrComponent+Config+StackPolicy",
        "output_edge": "CloudArchitectureDeploymentReceipt+ResourceRefs",
        "runtime_targets": ["pulumi", "ci_cd", "container"],
        "effects": ["cloud_resource_create_optional", "state_write", "network_call"],
        "candidate_outputs": ["IaCComponentPrimitive", "RuntimeWrapperCandidate", "PolicyObligation", "DeploymentRecipe"],
        "proof_requirements": ["package_source_ref", "config_schema_check", "preview_receipt", "policy_check"],
    },
    {
        "source_surface_id": "market:cdk_construct_hub",
        "rank": 6,
        "title": "CDK Construct Hub",
        "marketplace_kind": "cloud_construct_registry",
        "input_edge": "ConstructRef+Props+SynthesisPolicy",
        "output_edge": "SynthesizedInfrastructureTemplate+ConstructReceipt",
        "runtime_targets": ["cdk", "cdktf", "cdk8s", "ci_cd"],
        "effects": ["artifact_write", "cloud_resource_create_optional"],
        "candidate_outputs": ["ConstructPrimitiveCard", "SynthesisRecipe", "ProofObligationSet", "SecurityReview"],
        "proof_requirements": ["construct_source_ref", "props_schema_check", "synth_test", "security_review"],
    },
    {
        "source_surface_id": "market:cloudformation_registry",
        "rank": 7,
        "title": "CloudFormation Registry",
        "marketplace_kind": "cloud_resource_and_hook_registry",
        "input_edge": "CloudFormationTemplate+HookPolicy",
        "output_edge": "ProvisionDecision+HookReceipt",
        "runtime_targets": ["cloudformation", "ci_cd", "policy_hook"],
        "effects": ["cloud_resource_create_optional", "policy_decision"],
        "candidate_outputs": ["ResourcePrimitiveCard", "HookPrimitiveCard", "PolicyObligation", "ProvisionReceiptSchema"],
        "proof_requirements": ["template_validate", "hook_policy_test", "iam_review", "stack_output_check"],
    },
    {
        "source_surface_id": "market:aws_serverless_application_repository",
        "rank": 8,
        "title": "AWS Serverless Application Repository",
        "marketplace_kind": "serverless_application_registry",
        "input_edge": "ServerlessApplicationRef+ParameterMap+DeploymentPolicy",
        "output_edge": "ServerlessStackReceipt+EndpointSet",
        "runtime_targets": ["serverless_function", "api_gateway", "cloudformation"],
        "effects": ["cloud_resource_create", "iam_permission_use", "artifact_write"],
        "candidate_outputs": ["ServerlessAppPrimitive", "DeploymentRecipe", "PermissionReview", "StackOutputReceipt"],
        "proof_requirements": ["template_source_ref", "parameter_schema_check", "iam_policy_review", "deployment_smoke_test"],
    },
    {
        "source_surface_id": "market:github_actions",
        "rank": 9,
        "title": "GitHub Actions Marketplace",
        "marketplace_kind": "ci_cd_action_registry",
        "input_edge": "RepositoryEvent+ActionInputs+RepoContext",
        "output_edge": "WorkflowStepResult+ActionReceipt",
        "runtime_targets": ["github_actions"],
        "effects": ["repo_read", "repo_write_optional", "network_call_optional", "secret_use_optional"],
        "candidate_outputs": ["CiCdActionPrimitive", "WorkflowRecipe", "PermissionReview", "SecretUseReview"],
        "proof_requirements": ["action_version_pin", "permissions_review", "secret_usage_review", "test_workflow_run"],
    },
    {
        "source_surface_id": "market:n8n_zapier_make_pipedream",
        "rank": 10,
        "title": "n8n Zapier Make and Pipedream workflow marketplaces",
        "marketplace_kind": "automation_workflow_template_registry",
        "input_edge": "TriggerEvent+WorkflowConfig+ManagedAuthPolicy",
        "output_edge": "WorkflowRunReceipt+ActionResultSet",
        "runtime_targets": ["workflow_worker", "serverless_function", "container"],
        "effects": ["network_read_optional", "network_write_optional", "external_system_mutation_optional"],
        "candidate_outputs": ["PrimitiveGroupCandidate", "WorkflowRoutePlan", "AuthObligation", "ReceiptSchema"],
        "proof_requirements": ["field_mapping_test", "sandbox_workflow_test_optional", "idempotency_test", "notification_test"],
    },
    {
        "source_surface_id": "market:artifacthub_helm",
        "rank": 11,
        "title": "Artifact Hub and Helm charts",
        "marketplace_kind": "kubernetes_package_registry",
        "input_edge": "HelmChartRef+ValuesYaml+ClusterPolicy",
        "output_edge": "KubernetesReleaseReceipt+ManagedResourceRefs",
        "runtime_targets": ["helm", "kubernetes", "ci_cd"],
        "effects": ["kubernetes_resource_create", "kubernetes_resource_update"],
        "candidate_outputs": ["KubernetesDeploymentPrimitive", "HelmWrapper", "RbacReview", "InstallSmokePlan"],
        "proof_requirements": ["chart_source_ref", "values_schema_check", "rbac_review", "install_smoke_test"],
    },
    {
        "source_surface_id": "market:operatorhub",
        "rank": 12,
        "title": "OperatorHub and Kubernetes Operators",
        "marketplace_kind": "kubernetes_operator_registry",
        "input_edge": "CustomResourceSpec+ClusterPolicy",
        "output_edge": "ReconciledStateReceipt+ManagedResourceRefs",
        "runtime_targets": ["kubernetes.operator", "olm", "helm_optional"],
        "effects": ["kubernetes_resource_create", "kubernetes_resource_update", "controller_loop"],
        "candidate_outputs": ["OperatorPrimitiveCard", "ReconcileRoutePlan", "RbacReview", "UninstallCleanupPlan"],
        "proof_requirements": ["crd_schema_check", "rbac_review", "install_smoke_test", "reconcile_status_check"],
    },
    {
        "source_surface_id": "market:docker_hub_container_registries",
        "rank": 13,
        "title": "Docker Hub and public container registries",
        "marketplace_kind": "container_image_registry",
        "input_edge": "ContainerImageRef+RuntimeConfig+SecretRefs",
        "output_edge": "ServiceEndpoint+ContainerRunReceipt",
        "runtime_targets": ["docker", "kubernetes", "ecs", "cloud_run", "azure_container_apps"],
        "effects": ["container_start", "network_bind_optional", "volume_mount_optional"],
        "candidate_outputs": ["ContainerRuntimePrimitive", "HealthcheckPlan", "ImageSecurityObligation", "LicenseReview"],
        "proof_requirements": ["image_digest_pin", "license_review", "healthcheck_test", "secret_mount_policy_check"],
    },
    {
        "source_surface_id": "market:huggingface_replicate_model_hubs",
        "rank": 14,
        "title": "Hugging Face Replicate and model hubs",
        "marketplace_kind": "model_and_dataset_registry",
        "input_edge": "InputArtifact+ModelRef+InferencePolicy",
        "output_edge": "PredictionArtifact+InferenceReceipt",
        "runtime_targets": ["huggingface_endpoint", "replicate_api", "local_model_optional"],
        "effects": ["model_call", "network_call", "cost_incurring", "artifact_write_optional"],
        "candidate_outputs": ["ModelCallPrimitive", "DatasetPrimitive", "EvalPlan", "CostProfile"],
        "proof_requirements": ["model_version_pin", "provider_policy_review", "input_schema_check", "output_schema_check"],
    },
    {
        "source_surface_id": "market:data_marketplaces",
        "rank": 15,
        "title": "AWS Data Exchange Snowflake Databricks and BigQuery data marketplaces",
        "marketplace_kind": "data_product_marketplace",
        "input_edge": "DataProductListing+SubscriberContext+UsagePolicy",
        "output_edge": "DatasetAccessRef+EntitlementReceipt",
        "runtime_targets": ["aws_data_exchange", "snowflake", "databricks", "bigquery"],
        "effects": ["data_access_grant", "billing_optional", "audit_log_write"],
        "candidate_outputs": ["DataProductPrimitive", "EntitlementRecipe", "DataQualityPlan", "PrivacyReview"],
        "proof_requirements": ["license_terms_review", "data_dictionary_check", "freshness_check", "schema_profile"],
    },
    {
        "source_surface_id": "market:pypi_npm_dbt_airflow",
        "rank": 16,
        "title": "PyPI npm dbt Hub and Airflow providers",
        "marketplace_kind": "package_registry",
        "input_edge": "PackageRef+VersionPolicy+LanguageRuntime",
        "output_edge": "PackageApiSurfaceCard+PrimitiveCandidateSet",
        "runtime_targets": ["python", "node", "dbt", "airflow"],
        "effects": ["package_install_optional", "artifact_write"],
        "candidate_outputs": ["PackageSurfaceCard", "FunctionPrimitiveCandidate", "OperatorPrimitiveCandidate", "LicenseReview"],
        "proof_requirements": ["package_version_pin", "license_review", "api_surface_extract", "import_smoke_test"],
    },
    {
        "source_surface_id": "market:enterprise_app_marketplaces",
        "rank": 17,
        "title": "Salesforce Atlassian Slack Shopify HubSpot ServiceNow and app marketplaces",
        "marketplace_kind": "business_app_marketplace",
        "input_edge": "BusinessAppListing+ObjectModel+WorkflowIntent",
        "output_edge": "IndustryWorkflowPrimitiveCandidateSet+ProofObligationSet",
        "runtime_targets": ["saas.integration", "api.client", "workflow_worker"],
        "effects": ["source_ref_read", "artifact_write", "network_write_optional"],
        "candidate_outputs": ["BusinessWorkflowPrimitive", "ObjectModelOverlay", "AuthScopeReview", "SandboxWorkflowTestPlan"],
        "proof_requirements": ["listing_source_ref", "supported_object_check", "auth_scope_review", "sandbox_workflow_test_optional"],
    },
    {
        "source_surface_id": "market:cloud_marketplaces",
        "rank": 18,
        "title": "AWS Google Cloud and Microsoft cloud marketplaces",
        "marketplace_kind": "cloud_solution_marketplace",
        "input_edge": "MarketplaceListing+DeploymentPolicy+TenantContext",
        "output_edge": "DeployableCapabilityCard+ProcurementReceipt",
        "runtime_targets": ["cloud_marketplace", "saas", "container", "vm_image"],
        "effects": ["marketplace_procurement_optional", "cloud_deploy_optional", "billing_optional"],
        "candidate_outputs": ["MarketplaceProductPrimitive", "ProcurementRecipe", "SecurityReview", "DeploymentRecipe"],
        "proof_requirements": ["listing_source_ref", "license_terms_review", "deployment_smoke_test", "security_review"],
    },
    {
        "source_surface_id": "market:mulesoft_anypoint_exchange",
        "rank": 19,
        "title": "MuleSoft Anypoint Exchange and connector catalogs",
        "marketplace_kind": "integration_connector_exchange",
        "input_edge": "ConnectorOperation+ConnectionConfig+PayloadPolicy",
        "output_edge": "IntegrationActionReceipt+ConnectorPrimitiveCard",
        "runtime_targets": ["integration_platform", "api.client", "workflow_worker"],
        "effects": ["network_read_optional", "network_write_optional", "external_system_mutation_optional"],
        "candidate_outputs": ["ConnectorPrimitive", "IntegrationTemplate", "AuthRequirement", "ProofObligationSet"],
        "proof_requirements": ["connector_source_ref", "auth_requirement_review", "payload_schema_test", "sandbox_call_test_optional"],
    },
    {
        "source_surface_id": "market:browser_extension_plugin_stores",
        "rank": 20,
        "title": "Browser extension plugin and design-tool community stores",
        "marketplace_kind": "client_plugin_marketplace",
        "input_edge": "PluginListing+PermissionManifest+UseCasePolicy",
        "output_edge": "ClientPluginPrimitiveCandidate+PermissionReview",
        "runtime_targets": ["browser_extension", "desktop_plugin", "design_tool_plugin"],
        "effects": ["browser_permission_use", "file_read_optional", "network_call_optional"],
        "candidate_outputs": ["PluginPrimitiveCard", "PermissionReview", "UiActionPrimitive", "SecurityObligation"],
        "proof_requirements": ["listing_source_ref", "permission_manifest_review", "sandbox_test_optional", "privacy_review"],
    },
]

FACTORY_PATTERNS = [
    {"pattern_id": "factory:marketplace_listing_to_source_surface_card", "input_edge": "MarketplaceListing+SourcePolicy", "output_edge": "SourceSurfaceCard+SourceReceipt"},
    {"pattern_id": "factory:openapi_operation_to_endpoint_primitive", "input_edge": "OpenApiOperation+AuthPolicy", "output_edge": "ApiEndpointPrimitiveCard+ToolSchema+ProofPlan"},
    {"pattern_id": "factory:workflow_template_to_group_candidate", "input_edge": "WorkflowTemplate+ConnectionPolicy", "output_edge": "PrimitiveGroupCandidate+WorkflowReceipt"},
    {"pattern_id": "factory:iac_module_to_deployment_wrapper", "input_edge": "IaCModuleRef+VariableMap", "output_edge": "DeploymentWrapperCandidate+PlanReceipt"},
    {"pattern_id": "factory:mcp_tool_to_action_primitive", "input_edge": "McpToolSchema+AuthPolicy", "output_edge": "ToolPrimitiveCard+ConnectionReceipt"},
    {"pattern_id": "factory:package_to_api_surface_cards", "input_edge": "PackageRef+VersionPolicy", "output_edge": "ApiSurfaceCardSet+LicenseReviewObligation"},
    {"pattern_id": "factory:data_product_to_dataset_primitive", "input_edge": "DataProductListing+UsagePolicy", "output_edge": "DatasetAccessPrimitive+EntitlementReceipt"},
    {"pattern_id": "factory:container_image_to_runtime_primitive", "input_edge": "ContainerImageRef+RuntimeConfig", "output_edge": "ServiceRuntimePrimitive+HealthcheckPlan"},
]

EXAMPLE_CARDS = [
    {
        "primitive_id": "market:github_action.publish_docker_image",
        "source_surface_id": "market:github_actions",
        "kind": "ci_cd.action",
        "input_edge": "RepoCommit+DockerBuildPolicy+RegistryCredentials",
        "output_edge": "PublishedContainerImageRef+WorkflowReceipt",
        "effects": ["repo_read", "container_build", "registry_write", "secret_use"],
        "runtime_targets": ["github_actions"],
        "proof_requirements": ["action_version_pin", "permissions_review", "secret_usage_review", "test_workflow_run", "image_digest_check"],
    },
    {
        "primitive_id": "market:n8n.lead_capture_to_crm_notification",
        "source_surface_id": "market:n8n_zapier_make_pipedream",
        "kind": "workflow.template_group",
        "input_edge": "LeadCaptureEvent+CrmTarget+NotificationPolicy",
        "output_edge": "CrmLeadCreated+NotificationReceipt",
        "effects": ["network_read", "network_write", "external_system_mutation"],
        "runtime_targets": ["n8n", "workflow_worker", "container"],
        "proof_requirements": ["field_mapping_test", "crm_sandbox_test", "notification_test", "idempotency_test"],
    },
    {
        "primitive_id": "market:mcp.filesystem.read_file",
        "source_surface_id": "market:mcp_registry",
        "kind": "mcp.tool",
        "input_edge": "ToolCall[ReadFile]+FilesystemPolicy",
        "output_edge": "FileContentArtifact+ToolCallReceipt",
        "effects": ["file_read"],
        "runtime_targets": ["mcp_server", "local_agent_runtime"],
        "proof_requirements": ["tool_schema_validation", "path_boundary_test", "permission_test", "receipt_test"],
    },
    {
        "primitive_id": "market:terraform.vpc_module",
        "source_surface_id": "market:terraform_registry",
        "kind": "iac.module",
        "input_edge": "VpcConfig+RegionAccountPolicy",
        "output_edge": "VpcResourceRefs+TerraformReceipt",
        "effects": ["cloud_resource_create", "terraform_state_write"],
        "runtime_targets": ["terraform", "ci_cd", "container"],
        "proof_requirements": ["terraform_validate", "terraform_plan", "policy_check", "cost_estimate_optional", "drift_detection_optional"],
    },
    {
        "primitive_id": "market:openapi.operation_to_tool_card",
        "source_surface_id": "market:apis_guru_openapi",
        "kind": "api.endpoint_primitive_factory",
        "input_edge": "OpenApiOperationObject+AuthPolicy+RuntimePolicy",
        "output_edge": "ApiEndpointPrimitiveCard+ToolSchema+ProofPlan",
        "effects": ["artifact_write"],
        "runtime_targets": ["api.client", "mcp.tool", "llm.tool"],
        "proof_requirements": ["schema_validation", "auth_scope_review", "rate_limit_review", "error_model_check"],
    },
    {
        "primitive_id": "market:data.dataset_entitlement",
        "source_surface_id": "market:data_marketplaces",
        "kind": "data.product",
        "input_edge": "DataProductListing+SubscriberContext+UsagePolicy",
        "output_edge": "DatasetAccessRef+EntitlementReceipt",
        "effects": ["data_access_grant", "billing_optional", "audit_log_write"],
        "runtime_targets": ["aws_data_exchange", "snowflake", "databricks", "bigquery"],
        "proof_requirements": ["license_terms_review", "data_dictionary_check", "freshness_check", "schema_profile", "privacy_policy_review"],
    },
]


def _with_common(row: dict[str, Any], record_type: str) -> dict[str, Any]:
    return {"record_type": record_type, **row, **COMMON_ROW}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    surface_rows = [_with_common(row, "marketplace_primitive_source_surface") for row in SURFACES]
    pattern_rows = [_with_common(row, "marketplace_primitive_factory_pattern") for row in FACTORY_PATTERNS]
    example_rows = [_with_common(row, "marketplace_example_primitive_card") for row in EXAMPLE_CARDS]
    extraction_policy = {
        "record_type": "marketplace_primitive_extraction_policy",
        "copy_code": False,
        "extract_contracts": True,
        "extract_effects": True,
        "extract_runtime_targets": True,
        "extract_proof_requirements": True,
        "candidate": True,
        "serves_truth": False,
        "source_status": SOURCE_STATUS,
    }
    manifest = {
        "record_type": "marketplace_primitive_source_surface_pack_manifest",
        "pack_id": "marketplace-primitive-source-surfaces",
        "version": "0.1.0",
        "candidate": True,
        "serves_truth": False,
        "source_status": SOURCE_STATUS,
        "description": "Marketplace, registry, package, workflow, model, data, and cloud catalogs as primitive factory source surfaces.",
        "files": {
            "source_surfaces": "marketplace_source_surfaces.jsonl",
            "factory_patterns": "marketplace_factory_patterns.jsonl",
            "example_primitive_cards": "example_marketplace_primitive_cards.jsonl",
            "extraction_policy": "extraction_policy.json",
        },
        "source_surface_count": len(surface_rows),
        "factory_pattern_count": len(pattern_rows),
        "example_primitive_card_count": len(example_rows),
        "top_sources": [row["source_surface_id"] for row in SURFACES[:10]],
    }
    _write_jsonl(PACK_DIR / "marketplace_source_surfaces.jsonl", surface_rows)
    _write_jsonl(PACK_DIR / "marketplace_factory_patterns.jsonl", pattern_rows)
    _write_jsonl(PACK_DIR / "example_marketplace_primitive_cards.jsonl", example_rows)
    (PACK_DIR / "extraction_policy.json").write_text(json.dumps(extraction_policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"source_surface_count": len(surface_rows), "factory_pattern_count": len(pattern_rows), "example_primitive_card_count": len(example_rows)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
