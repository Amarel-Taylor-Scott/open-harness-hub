#!/usr/bin/env python3
"""Build the deployment packaging and container runtime surface pack.

Implements the owner directive of 2026-07-02: primitives and compiled routes
must be packageable as real deployables — terraform definitions, deployment
component sets, docker image build plans, cloud-marketplace deployables — and
the base images those deployables stand on (for example ``python:3.11-slim``)
must be tracked as MAINTAINED SURFACES with digest pinning, rebuild triggers,
end-of-life calendars, and software-bill-of-materials policy.

The pack under
``catalog/knowledge-packs/data/deployment-packaging-and-container-surfaces/``
holds four generated files:

* ``packaging_target_families.jsonl`` — one row per packaging target family
  (oci_image, terraform_module, helm_chart, marketplace_listing_bundle, …)
  with input/output edges, packaging conventions, a validation command
  pattern (dry-run / plan / lint — carried as DATA, never executed here),
  the five required proof receipts, known failure modes, and the marketplace
  targets it can be distributed through.
* ``base_image_runtime_surfaces.jsonl`` — one row per tracked base image
  family with digest pinning policy, rebuild trigger policy (base-digest
  drift, CVE severity threshold, end-of-life calendar reference), and
  maintenance receipts. These are TRACKING CONTRACTS (candidate rows), not
  claims that tracking runs today.
* ``packaging_mutator_catalog.jsonl`` — deterministic mutators that route a
  compiled capability into a packaging family (route_to_oci_image_build_plan,
  image_pin_digest, sbom_attach, signature_attach, …) with preconditions,
  postconditions, lossiness policy, proof obligations, and telemetry fields.
* ``cloud_marketplace_targets.jsonl`` — one row per distribution surface
  (AWS/Azure/GCP marketplaces, Terraform Registry, Artifact Hub, OperatorHub,
  Docker Hub, GitHub Container Registry, VS Code / JetBrains marketplaces,
  PyPI, npm registry, GitHub Marketplace) with a submission requirement
  checklist and validation receipts.

Every row is a CANDIDATE contract: ``candidate=true`` / ``serves_truth=false``.
Nothing here claims a build ran, a listing was submitted, or an image scan
happened — the paired checker
(``scripts/check_deployment_packaging_surface_pack.py``) keeps that boundary
and goes red on hand-edited pack files (this builder is the single source).

Offline-deterministic: no network calls, no wall-clock in row bodies; the
manifest date comes from ``--date`` (default 2026-07-02).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

DEPLOYMENT_PACKAGING_SURFACE_PACK_DIR = (
    "catalog/knowledge-packs/data/deployment-packaging-and-container-surfaces"
)
PACK_DIR = _resource(DEPLOYMENT_PACKAGING_SURFACE_PACK_DIR)
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

DEFAULT_GENERATED_DATE = "2026-07-02"  # owner directive date; manifest-only, override via --date
PACK_ID = "deployment-packaging-and-container-surfaces"
PACK_SOURCE_FAMILY = "deployment_packaging_and_container_surface_pack"
PACK_SOURCE_STATUS = "owner_directive_seed_needs_local_packaging_adapters"
PACK_EVIDENCE_STATUS = "tracking_contract_only_not_local_measured_evidence"

# Every base-image row must carry this status: the row is a contract for HOW
# the surface will be maintained, never a claim that maintenance runs today.
BASE_IMAGE_TRACKING_STATUS = "tracking_contract_only_not_yet_running"

# The five proof receipts every packaging target family must declare.
REQUIRED_PROOF_RECEIPTS: list[str] = [
    "dry_run_receipt",
    "sbom_receipt",
    "signature_receipt",
    "reproducible_build_receipt",
    "policy_scan_receipt",
]

# The three rebuild triggers every base-image tracking contract must declare.
REQUIRED_REBUILD_TRIGGERS: list[str] = [
    "base_digest_drift",
    "cve_severity_threshold",
    "eol_calendar_ref",
]

# Owner-directed packaging family set (checker enforces exact coverage).
REQUIRED_PACKAGING_FAMILY_KEYS: list[str] = [
    "oci_image",
    "terraform_module",
    "opentofu_module",
    "helm_chart",
    "kubernetes_manifest_set",
    "aws_sam_application",
    "aws_cdk_construct",
    "azure_bicep_template",
    "azure_arm_template",
    "gcp_cloud_run_service",
    "gcp_deployment_package",
    "cloudformation_template",
    "pulumi_component",
    "buildpack",
    "devcontainer",
    "mcp_server_package",
    "python_wheel",
    "npm_package",
    "github_action",
    "marketplace_listing_bundle",
]

# Owner-directed deterministic mutator set (checker enforces exact coverage).
REQUIRED_MUTATOR_KEYS: list[str] = [
    "route_to_oci_image_build_plan",
    "route_to_terraform_module",
    "route_to_helm_chart",
    "listing_spec_to_marketplace_manifest_set",
    "image_pin_digest",
    "sbom_attach",
    "signature_attach",
    "multiarch_matrix_expand",
]

# Ids stay version-free: version lives in metadata, never in an id.
FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)
# Key-name substrings that would smuggle a credential field into the pack.
FORBIDDEN_KEY_SUBSTRINGS: list[str] = [
    "password", "secret", "api_key", "apikey", "private_key",
    "access_key", "auth_token", "credential",
]
# Value patterns that look like real leaked tokens (never allowed in rows).
FORBIDDEN_VALUE_PATTERN = re.compile(
    r"(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[bp]-|-----BEGIN [A-Z ]*PRIVATE KEY)"
)

ID_FIELD_BY_FILE: dict[str, str] = {
    "packaging_target_families.jsonl": "family_id",
    "base_image_runtime_surfaces.jsonl": "image_family_id",
    "packaging_mutator_catalog.jsonl": "mutator_id",
    "cloud_marketplace_targets.jsonl": "market_id",
}


def _rows(record_type: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"record_type": record_type, **BOUNDARY, **row} for row in rows]


# ── cloud_marketplace_targets.jsonl ────────────────────────────────────────
def _market(key: str, title: str, operator: str, docs_url: str, kind: str,
            checklist: list[str], receipts: list[str]) -> dict[str, Any]:
    return {
        "market_id": f"market:{key}",
        "title": title,
        "operator": operator,
        "listing_docs_url": docs_url,
        "distribution_kind": kind,
        "submission_checklist": checklist,
        "validation_receipts": receipts,
        "submission_state": "no_listing_submitted",
    }


def _cloud_marketplace_targets() -> list[dict[str, Any]]:
    common_receipts = ["listing_metadata_validation_receipt", "policy_scan_receipt"]
    rows = [
        _market("aws_marketplace_container", "AWS Marketplace container-based product",
                "Amazon Web Services",
                "https://docs.aws.amazon.com/marketplace/latest/userguide/container-based-products.html",
                "container_product",
                ["product_title_and_description", "images_hosted_in_amazon_elastic_container_registry",
                 "helm_or_container_delivery_option_declared", "pricing_model_declared",
                 "vulnerability_scan_clean", "usage_instructions", "support_contact",
                 "architecture_diagram"],
                common_receipts + ["container_scan_receipt", "delivery_option_dry_run_receipt"]),
        _market("aws_marketplace_ami", "AWS Marketplace machine-image product",
                "Amazon Web Services",
                "https://docs.aws.amazon.com/marketplace/latest/userguide/ami-products.html",
                "machine_image_product",
                ["product_title_and_description", "machine_image_self_service_scan_passed",
                 "no_embedded_credentials_or_default_passwords_declared", "pricing_model_declared",
                 "region_availability_declared", "usage_instructions", "support_contact"],
                common_receipts + ["machine_image_scan_receipt"]),
        _market("aws_marketplace_saas", "AWS Marketplace software-as-a-service product",
                "Amazon Web Services",
                "https://docs.aws.amazon.com/marketplace/latest/userguide/saas-products.html",
                "saas_product",
                ["product_title_and_description", "registration_landing_page_declared",
                 "entitlement_and_metering_integration_declared", "pricing_model_declared",
                 "usage_instructions", "support_contact"],
                common_receipts + ["integration_test_receipt"]),
        _market("azure_marketplace_managed_application", "Azure Marketplace managed application",
                "Microsoft",
                "https://learn.microsoft.com/en-us/partner-center/marketplace-offers/plan-azure-app-managed-app",
                "managed_application",
                ["offer_listing_details", "managed_application_package_validated",
                 "plan_and_pricing_declared", "customer_usage_attribution_declared",
                 "support_contact", "preview_audience_declared"],
                common_receipts + ["deployment_package_validation_receipt"]),
        _market("azure_marketplace_solution_template", "Azure Marketplace solution template",
                "Microsoft",
                "https://learn.microsoft.com/en-us/partner-center/marketplace-offers/plan-azure-app-solution-template",
                "solution_template",
                ["offer_listing_details", "resource_template_validated",
                 "plan_and_pricing_declared", "support_contact", "preview_audience_declared"],
                common_receipts + ["template_validation_receipt"]),
        _market("gcp_marketplace", "Google Cloud Marketplace",
                "Google Cloud",
                "https://cloud.google.com/marketplace/docs/partners",
                "cloud_marketplace_product",
                ["partner_onboarding_complete", "product_listing_details",
                 "deployment_package_verified", "pricing_model_declared",
                 "vulnerability_scan_clean", "support_contact"],
                common_receipts + ["deployment_verification_receipt"]),
        _market("terraform_registry", "Terraform Registry module publication",
                "HashiCorp",
                "https://developer.hashicorp.com/terraform/registry/modules/publish",
                "infrastructure_module",
                ["repository_naming_convention_terraform_provider_name", "semantic_version_tag_present",
                 "module_structure_standard", "readme_with_usage", "license_declared"],
                common_receipts + ["module_validation_receipt"]),
        _market("artifact_hub", "Artifact Hub repository listing",
                "Cloud Native Computing Foundation",
                "https://artifacthub.io/docs/topics/repositories/",
                "cloud_native_package_index",
                ["repository_registered", "package_metadata_file_present",
                 "maintainer_contact_declared", "license_declared", "security_report_optional_declared"],
                common_receipts + ["repository_lint_receipt"]),
        _market("operatorhub", "OperatorHub community operator listing",
                "OperatorHub community",
                "https://operatorhub.io/contribute",
                "kubernetes_operator_index",
                ["operator_bundle_format_valid", "cluster_service_version_metadata_complete",
                 "upgrade_path_declared", "maintainer_contact_declared", "icon_and_description"],
                common_receipts + ["operator_bundle_validation_receipt"]),
        _market("docker_hub", "Docker Hub repository",
                "Docker",
                "https://docs.docker.com/docker-hub/",
                "container_registry",
                ["repository_name_and_description", "readme_overview_present",
                 "supported_tags_documented", "license_declared"],
                common_receipts + ["image_push_dry_run_receipt"]),
        _market("ghcr", "GitHub Container Registry package",
                "GitHub",
                "https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry",
                "container_registry",
                ["package_visibility_declared", "repository_link_declared",
                 "readme_overview_present", "license_declared"],
                common_receipts + ["image_push_dry_run_receipt"]),
        _market("vscode_marketplace", "Visual Studio Code Marketplace extension",
                "Microsoft",
                "https://code.visualstudio.com/api/working-with-extensions/publishing-extension",
                "editor_extension_marketplace",
                ["publisher_identity_declared", "extension_manifest_valid",
                 "readme_and_changelog_present", "license_declared", "icon_present"],
                common_receipts + ["extension_package_validation_receipt"]),
        _market("jetbrains_marketplace", "JetBrains Marketplace plugin",
                "JetBrains",
                "https://plugins.jetbrains.com/docs/marketplace/",
                "editor_extension_marketplace",
                ["vendor_profile_declared", "plugin_descriptor_valid",
                 "compatibility_range_declared", "readme_and_changelog_present", "license_declared"],
                common_receipts + ["plugin_verifier_receipt"]),
        _market("pypi", "Python Package Index distribution",
                "Python Software Foundation",
                "https://pypi.org/help/",
                "language_package_index",
                ["project_name_available", "distribution_metadata_valid",
                 "readme_rendering_valid", "license_declared", "trusted_publishing_declared"],
                common_receipts + ["distribution_check_receipt"]),
        _market("npm_registry", "npm public registry package",
                "npm (GitHub)",
                "https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry",
                "language_package_index",
                ["package_name_available", "package_json_metadata_valid",
                 "readme_present", "license_declared", "provenance_attestation_declared"],
                common_receipts + ["publish_dry_run_receipt"]),
        _market("github_marketplace", "GitHub Marketplace action listing",
                "GitHub",
                "https://docs.github.com/en/actions/sharing-automations/publishing-actions-in-github-marketplace",
                "workflow_action_marketplace",
                ["action_metadata_file_valid", "branding_icon_and_color_declared",
                 "readme_with_usage", "release_tag_present", "license_declared"],
                common_receipts + ["action_metadata_validation_receipt"]),
    ]
    return _rows("cloud_marketplace_distribution_target", rows)


MARKET_IDS: list[str] = [row["market_id"] for row in _cloud_marketplace_targets()]


# ── packaging_target_families.jsonl ────────────────────────────────────────
def _receipts(dry_run: str, sbom: str, signature: str, reproducible: str,
              policy: str) -> dict[str, str]:
    return {
        "dry_run_receipt": dry_run,
        "sbom_receipt": sbom,
        "signature_receipt": signature,
        "reproducible_build_receipt": reproducible,
        "policy_scan_receipt": policy,
    }


def _family(key: str, title: str, input_edge: str, output_edge: str,
            conventions: list[str], validation: str,
            receipts: dict[str, str], failures: list[str],
            markets: list[str]) -> dict[str, Any]:
    return {
        "family_id": f"packfamily:{key}",
        "title": title,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "packaging_conventions": conventions,
        "validation_command_pattern": validation,
        "validation_command_is_data_only": True,
        "proof_receipts": receipts,
        "known_failure_modes": failures,
        "marketplace_targets": [f"market:{m}" for m in markets],
    }


def _packaging_target_families() -> list[dict[str, Any]]:
    rows = [
        _family("oci_image", "OCI container image",
                "CompiledPrimitiveRoute+RuntimeDependencySet+BaseImageSelection",
                "OciImageDigest+BuildReceipt",
                ["single-process entrypoint wrapping the compiled route",
                 "base image referenced by pinned digest, never a floating tag",
                 "labels carry route id, lineage refs, and schema_version metadata",
                 "multi-stage build keeps toolchains out of the runtime layer"],
                "docker build --check . && docker buildx build --provenance=true --sbom=true --load .",
                _receipts("BuildKit lint / build --check output recorded before any push",
                          "SBOM attestation generated at build time and attached to the image",
                          "image signed (sigstore/cosign-style) and signature stored beside the digest",
                          "two clean-room builds from the same inputs produce the same layer digests",
                          "image scanned against the CVE severity policy before promotion"),
                ["floating base tag silently changes the runtime",
                 "build context leaks files that are not in the dependency set",
                 "image runs as root because no user was declared"],
                ["docker_hub", "ghcr", "aws_marketplace_container", "gcp_marketplace"]),
        _family("terraform_module", "Terraform module",
                "InfrastructureCapabilityContract+ProviderRequirementSet",
                "TerraformModulePackage+PlanReceipt",
                ["standard module structure (main/variables/outputs/versions)",
                 "provider version constraints pinned in required_providers",
                 "no provider credentials in module source — injected by the caller",
                 "examples/ directory carries a runnable minimal example"],
                "terraform init -backend=false && terraform validate && terraform plan -out=plan.tfplan",
                _receipts("terraform plan output recorded with zero unexplained destroys",
                          "provider + module dependency lock exported as an inventory",
                          "module release tag signed and checksum recorded",
                          "same inputs produce a byte-identical plan JSON",
                          "policy-as-code scan (deny-lists, tagging, encryption) over the plan"),
                ["unpinned provider version drifts under the module",
                 "plan clean but apply fails on quota or permissions",
                 "module hardcodes a region or account assumption"],
                ["terraform_registry"]),
        _family("opentofu_module", "OpenTofu module",
                "InfrastructureCapabilityContract+ProviderRequirementSet",
                "OpenTofuModulePackage+PlanReceipt",
                ["same standard module structure as terraform_module",
                 "state encryption options documented for the caller",
                 "provider version constraints pinned in required_providers"],
                "tofu init -backend=false && tofu validate && tofu plan -out=plan.tfplan",
                _receipts("tofu plan output recorded with zero unexplained destroys",
                          "provider + module dependency lock exported as an inventory",
                          "module release tag signed and checksum recorded",
                          "same inputs produce a byte-identical plan JSON",
                          "policy-as-code scan over the plan"),
                ["module written for terraform-only features fails under tofu",
                 "registry namespace confusion between terraform and opentofu mirrors"],
                ["terraform_registry"]),
        _family("helm_chart", "Helm chart",
                "KubernetesWorkloadShape+ValuesSchema",
                "PackagedHelmChart+LintReceipt",
                ["values.schema.json validates every exposed knob",
                 "image references templated to pinned digests",
                 "chart version and appVersion live in Chart.yaml metadata only",
                 "NOTES.txt explains the deployed capability and its seams"],
                "helm lint . && helm template . && helm install --dry-run --debug release-name .",
                _receipts("helm install --dry-run rendered manifests recorded",
                          "chart dependency inventory + subchart image list exported",
                          "chart provenance file signed and verified on pull",
                          "helm package from the same source tree produces the same chart digest",
                          "rendered manifests scanned against cluster policy (no privileged pods)"),
                ["values drift makes template output diverge from the tested render",
                 "subchart pulls an unpinned image",
                 "CRD ordering breaks first install"],
                ["artifact_hub"]),
        _family("kubernetes_manifest_set", "Kubernetes manifest set",
                "WorkloadSpec+ClusterPolicy",
                "KubernetesManifestSet+ServerDryRunReceipt",
                ["kustomize-style base + overlays, no environment forks of the base",
                 "resource requests/limits declared on every workload",
                 "images referenced by pinned digest",
                 "namespaces and network policies declared explicitly"],
                "kubectl apply --dry-run=server -f . && kubeconform -strict .",
                _receipts("server-side dry-run accepted every object",
                          "image list across the set exported as an inventory",
                          "manifest bundle checksum signed",
                          "same source produces byte-identical rendered manifests",
                          "manifests scanned against admission policy (no hostPath, no privileged)"),
                ["client-side dry-run passes but server-side admission rejects",
                 "implicit default namespace scatters objects",
                 "missing resource limits starve the node"],
                ["artifact_hub"]),
        _family("aws_sam_application", "AWS Serverless Application Model application",
                "ServerlessFunctionRouteSet+EventSourceBindings",
                "SamApplicationPackage+ChangeSetReceipt",
                ["template.yaml declares functions, events, and permissions minimally",
                 "runtime pinned to a supported language runtime identifier",
                 "least-privilege per-function policies, no wildcard resources"],
                "sam validate --lint && sam build && sam deploy --no-execute-changeset",
                _receipts("change set created and recorded without execution",
                          "function dependency inventory exported per artifact",
                          "packaged template checksum signed",
                          "sam build from the same source produces identical artifacts",
                          "template scanned for wildcard permissions and public buckets"),
                ["change set clean but execution hits service quotas",
                 "runtime identifier reaches end of support",
                 "event source mapping duplicates deliveries"],
                ["aws_marketplace_saas"]),
        _family("aws_cdk_construct", "AWS Cloud Development Kit construct",
                "InfrastructureCapabilityContract+ConstructPropsSchema",
                "CdkConstructPackage+SynthReceipt",
                ["construct props typed and validated at synth time",
                 "no account/region literals — resolved from the environment",
                 "published as a language package with pinned peer dependencies"],
                "cdk synth --strict && cdk diff",
                _receipts("cdk synth output recorded; cdk diff shows only intended changes",
                          "construct dependency inventory exported",
                          "package release signed with provenance attestation",
                          "synth from the same source produces identical templates",
                          "synthesized template scanned against policy rules"),
                ["construct upgrades change synthesized defaults silently",
                 "cross-stack references create hidden coupling"],
                ["npm_registry", "ghcr"]),
        _family("azure_bicep_template", "Azure Bicep template",
                "InfrastructureCapabilityContract+ParameterSchema",
                "BicepTemplatePackage+WhatIfReceipt",
                ["parameters carry types, allowed values, and descriptions",
                 "no plaintext sensitive parameters — references only",
                 "modules pinned to registry versions in metadata"],
                "az bicep build --file main.bicep && az deployment group what-if --template-file main.bicep",
                _receipts("what-if output recorded with zero unexplained deletes",
                          "module dependency inventory exported",
                          "compiled template checksum signed",
                          "bicep build from the same source produces identical ARM JSON",
                          "template scanned for open network rules and missing encryption"),
                ["what-if misses runtime-evaluated properties",
                 "API version drift changes resource defaults"],
                ["azure_marketplace_solution_template"]),
        _family("azure_arm_template", "Azure Resource Manager template",
                "InfrastructureCapabilityContract+ParameterSchema",
                "ArmTemplatePackage+ValidationReceipt",
                ["schema and contentVersion declared in metadata",
                 "parameters file separated from the template",
                 "nested templates referenced by checksum"],
                "az deployment group validate --template-file azuredeploy.json && az deployment group what-if --template-file azuredeploy.json",
                _receipts("validate + what-if output recorded",
                          "linked template inventory exported",
                          "template checksum signed",
                          "same source produces byte-identical template JSON",
                          "template scanned against Azure policy assignments"),
                ["copy loops hide per-instance failures",
                 "linked template URL becomes unreachable at deploy time"],
                ["azure_marketplace_solution_template", "azure_marketplace_managed_application"]),
        _family("gcp_cloud_run_service", "Google Cloud Run service definition",
                "OciImageDigest+ServiceContract",
                "CloudRunServiceSpec+ValidationReceipt",
                ["service YAML pins the image by digest",
                 "concurrency, CPU, memory, and timeout declared explicitly",
                 "least-privilege runtime service account named in the spec"],
                "gcloud run services replace service.yaml --dry-run",
                _receipts("dry-run replace accepted the service spec",
                          "image SBOM referenced from the pinned digest",
                          "image signature verified before deploy",
                          "same spec inputs produce identical rendered service YAML",
                          "spec scanned for public ingress and missing authentication"),
                ["unpinned image tag redeploys different code",
                 "cold-start latency violates the capability contract"],
                ["gcp_marketplace"]),
        _family("gcp_deployment_package", "Google Cloud deployment package",
                "InfrastructureCapabilityContract+DeploymentSchema",
                "GcpDeploymentPackage+PreviewReceipt",
                ["deployment config declares resources with explicit properties",
                 "images and machine types pinned in configuration",
                 "marketplace deployment package schema followed for listing use"],
                "gcloud deployment-manager deployments create preview-check --config config.yaml --preview",
                _receipts("preview deployment recorded and abandoned without execution",
                          "resource + image inventory exported",
                          "package checksum signed",
                          "same config produces identical expanded resource set",
                          "expanded resources scanned against organization policy"),
                ["preview succeeds but actual create hits IAM gaps",
                 "template expansion differs across API versions"],
                ["gcp_marketplace"]),
        _family("cloudformation_template", "AWS CloudFormation template",
                "InfrastructureCapabilityContract+ParameterSchema",
                "CloudFormationTemplatePackage+ChangeSetReceipt",
                ["parameters carry types, constraints, and descriptions",
                 "no hardcoded credentials or account ids",
                 "cfn-lint clean before any change set"],
                "cfn-lint template.yaml && aws cloudformation validate-template --template-body file://template.yaml && aws cloudformation create-change-set --change-set-name check --no-execute-changeset",
                _receipts("change set created and recorded without execution",
                          "resource inventory exported from the template",
                          "template checksum signed",
                          "same source produces byte-identical template",
                          "template scanned for wildcard IAM and open security groups"),
                ["stack rollback leaves orphaned resources",
                 "drift between template and live stack goes undetected"],
                ["aws_marketplace_ami", "aws_marketplace_container"]),
        _family("pulumi_component", "Pulumi component package",
                "InfrastructureCapabilityContract+ComponentArgsSchema",
                "PulumiComponentPackage+PreviewReceipt",
                ["component args typed and validated",
                 "provider versions pinned in package metadata",
                 "published as a language package with schema"],
                "pulumi preview --diff --non-interactive",
                _receipts("pulumi preview diff recorded with zero unexplained deletes",
                          "component dependency inventory exported",
                          "package release signed",
                          "same program + state produce the same preview plan",
                          "planned resources scanned against policy packs"),
                ["state drift makes preview lie about the real diff",
                 "dynamic providers hide untyped behavior"],
                ["npm_registry", "pypi", "ghcr"]),
        _family("buildpack", "Cloud Native Buildpack",
                "ApplicationSourceTree+RuntimeDependencySet",
                "BuildpackBuiltImage+BuildReceipt",
                ["buildpack.toml declares id, targets, and stack compatibility",
                 "detect phase must be side-effect free",
                 "builder image pinned by digest"],
                "pack buildpack package check --format image && pack build smoke-app --builder <pinned-builder-digest>",
                _receipts("pack build against a fixture app recorded",
                          "SBOM emitted by the buildpack lifecycle attached",
                          "built image signed",
                          "same source + builder digest produce the same image digest",
                          "built image scanned against the CVE severity policy"),
                ["detect matches applications it cannot actually build",
                 "builder stack update changes runtime behavior"],
                ["docker_hub", "ghcr"]),
        _family("devcontainer", "Development container definition",
                "ToolchainRequirementSet+EditorIntegrationContract",
                "DevcontainerDefinition+BuildReceipt",
                ["devcontainer.json references an image pinned by digest or a lockable feature set",
                 "features pinned to exact versions in metadata",
                 "postCreate commands idempotent and offline-tolerant"],
                "devcontainer build --workspace-folder .",
                _receipts("devcontainer build completed against the definition",
                          "feature + image inventory exported",
                          "published template/feature signed",
                          "same definition produces the same image digest",
                          "definition scanned for privileged mounts and docker-socket exposure"),
                ["feature auto-upgrade changes the toolchain under the team",
                 "definition depends on host state that CI lacks"],
                ["ghcr"]),
        _family("mcp_server_package", "Model Context Protocol server package",
                "ToolSurfaceContractSet+TransportPolicy",
                "McpServerPackage+HandshakeReceipt",
                ["tool names, schemas, and descriptions declared statically",
                 "transport (stdio/http) and auth expectations documented",
                 "distributed as a language package and/or pinned container image"],
                "mcp-inspector --cli --method tools/list against a locally started server (handshake smoke)",
                _receipts("handshake + tools/list smoke output recorded",
                          "package dependency inventory exported",
                          "package release signed with provenance",
                          "same source produces identical package contents",
                          "tool surface scanned for undeclared side effects and shell escapes"),
                ["tool schema drift breaks callers silently",
                 "server assumes a workspace layout the host does not have"],
                ["pypi", "npm_registry", "docker_hub", "ghcr"]),
        _family("python_wheel", "Python wheel distribution",
                "PythonPackageSourceTree+DependencyPinSet",
                "PythonWheel+DistributionCheckReceipt",
                ["pyproject.toml is the single build configuration",
                 "dependencies carry lower+upper bounds; extras documented",
                 "version lives in package metadata only"],
                "python -m build && twine check dist/*",
                _receipts("twine check accepted every distribution file",
                          "dependency inventory exported from the built wheel",
                          "release signed / attested via trusted publishing",
                          "same source tree produces byte-identical wheels",
                          "package scanned for bundled secrets and known-vulnerable pins"),
                ["missing upper bounds break under a future dependency",
                 "sdist and wheel diverge in included files"],
                ["pypi"]),
        _family("npm_package", "npm package distribution",
                "NodePackageSourceTree+DependencyPinSet",
                "NpmPackageTarball+PublishDryRunReceipt",
                ["package.json files field allow-lists published content",
                 "engines field declares supported node versions",
                 "version lives in package metadata only"],
                "npm pack --dry-run && npm publish --dry-run",
                _receipts("publish --dry-run file list recorded",
                          "dependency inventory exported from the lockfile",
                          "release published with provenance attestation",
                          "same source produces byte-identical tarballs",
                          "package scanned for install scripts and bundled secrets"),
                ["postinstall script runs unexpected code on consumers",
                 "unpinned transitive dependency introduces a breaking change"],
                ["npm_registry", "ghcr"]),
        _family("github_action", "GitHub Action",
                "WorkflowStepContract+RunnerPolicy",
                "GitHubActionPackage+MetadataValidationReceipt",
                ["action.yml declares inputs/outputs with descriptions and defaults",
                 "composite/docker/javascript flavor declared explicitly",
                 "referenced actions pinned by commit digest"],
                "actionlint && action.yml schema validation against the published metadata schema",
                _receipts("actionlint + metadata validation output recorded",
                          "bundled dependency inventory exported",
                          "release tag signed",
                          "same source produces identical packaged action",
                          "action scanned for credential echoing and untrusted input interpolation"),
                ["mutable tag reference lets the action change under consumers",
                 "untrusted input reaches a shell without quoting"],
                ["github_marketplace"]),
        _family("marketplace_listing_bundle", "Cloud marketplace listing bundle",
                "DeployableSet+ListingSpec",
                "MarketplaceListingBundle+SubmissionChecklistReceipt",
                ["one listing spec fans out to per-marketplace bundles",
                 "pricing, support, and legal fields sourced from the listing spec only",
                 "every referenced deployable carries its own proof receipts"],
                "per-marketplace validator over the generated bundle (metadata schema check + checklist completeness)",
                _receipts("per-marketplace metadata validation recorded",
                          "aggregate inventory across bundled deployables exported",
                          "bundle checksum signed",
                          "same listing spec produces byte-identical bundles",
                          "bundle scanned for placeholder text and missing legal fields"),
                ["marketplace schema change invalidates the generated bundle",
                 "listing copy drifts from the actual deployable behavior"],
                ["aws_marketplace_container", "aws_marketplace_ami", "aws_marketplace_saas",
                 "azure_marketplace_managed_application", "azure_marketplace_solution_template",
                 "gcp_marketplace", "operatorhub", "vscode_marketplace", "jetbrains_marketplace"]),
    ]
    return _rows("deployment_packaging_target_family", rows)


PACKAGING_FAMILY_IDS: list[str] = [f"packfamily:{key}" for key in REQUIRED_PACKAGING_FAMILY_KEYS]


# ── base_image_runtime_surfaces.jsonl ──────────────────────────────────────
def _base_image(key: str, family: str, tracked_tags: list[str], tag_pattern: str,
                pull_reference: str, registry_url: str, eol_url: str,
                maintainer: str) -> dict[str, Any]:
    return {
        "image_family_id": f"baseimage:{key}",
        "image_family": family,
        "tracked_tags": tracked_tags,
        "tag_pattern": tag_pattern,
        "pull_reference": pull_reference,
        "registry_url": registry_url,
        "maintainer": maintainer,
        "digest_pinning_policy": (
            "every build plan resolves the tracked tag to a sha256 digest at plan time, "
            "records the digest in the build receipt, and builds FROM the digest — "
            "never from the floating tag"
        ),
        "rebuild_trigger_policy": {
            "base_digest_drift": "rebuild dependents when a tracked tag resolves to a new digest",
            "cve_severity_threshold": "rebuild when the base layer scan reports a fixable HIGH or CRITICAL vulnerability",
            "eol_calendar_ref": eol_url,
        },
        "eol_policy_url": eol_url,
        "sbom_policy": (
            "a software bill of materials is generated for every image built on this base "
            "and stored beside the image digest; base-layer packages are attributed to this surface"
        ),
        "freshness_policy": (
            "tracked tags are re-resolved on a scheduled cadence; a digest observation older than "
            "the cadence window marks dependents stale-pending-review, never auto-promotes"
        ),
        "maintenance_receipts": [
            "digest_resolution_receipt",
            "cve_scan_receipt",
            "rebuild_receipt",
            "eol_calendar_check_receipt",
        ],
        "tracking_status": BASE_IMAGE_TRACKING_STATUS,
    }


def _base_image_runtime_surfaces() -> list[dict[str, Any]]:
    rows = [
        _base_image("python_slim", "python-slim",
                    ["3.11-slim", "3.12-slim", "3.13-slim"], "<major>.<minor>-slim",
                    "docker.io/library/python", "https://hub.docker.com/_/python",
                    "https://devguide.python.org/versions/", "Docker Official Images"),
        _base_image("node_alpine", "node-alpine",
                    ["20-alpine", "22-alpine", "24-alpine"], "<major>-alpine",
                    "docker.io/library/node", "https://hub.docker.com/_/node",
                    "https://github.com/nodejs/release", "Docker Official Images"),
        _base_image("golang_alpine", "golang-alpine",
                    ["1-alpine"], "<major>-alpine",
                    "docker.io/library/golang", "https://hub.docker.com/_/golang",
                    "https://go.dev/doc/devel/release", "Docker Official Images"),
        _base_image("distroless_python3", "distroless-python3",
                    ["python3-debian12", "python3-debian12:nonroot"], "python3-<debian-release>[:nonroot]",
                    "gcr.io/distroless/python3-debian12",
                    "https://github.com/GoogleContainerTools/distroless",
                    "https://github.com/GoogleContainerTools/distroless#debian-12", "Google Container Tools"),
        _base_image("distroless_static", "distroless-static",
                    ["static-debian12", "static-debian12:nonroot"], "static-<debian-release>[:nonroot]",
                    "gcr.io/distroless/static-debian12",
                    "https://github.com/GoogleContainerTools/distroless",
                    "https://github.com/GoogleContainerTools/distroless#debian-12", "Google Container Tools"),
        _base_image("ubi9_minimal", "ubi9-minimal",
                    ["9"], "<major>[.<minor>]",
                    "registry.access.redhat.com/ubi9-minimal",
                    "https://catalog.redhat.com/software/base-images",
                    "https://access.redhat.com/support/policy/updates/errata", "Red Hat"),
        _base_image("debian_slim", "debian-slim",
                    ["bookworm-slim", "trixie-slim"], "<release-codename>-slim",
                    "docker.io/library/debian", "https://hub.docker.com/_/debian",
                    "https://wiki.debian.org/DebianReleases", "Docker Official Images"),
        _base_image("eclipse_temurin", "eclipse-temurin",
                    ["17-jre", "21-jre"], "<major>-jre",
                    "docker.io/library/eclipse-temurin", "https://hub.docker.com/_/eclipse-temurin",
                    "https://adoptium.net/support/", "Eclipse Adoptium"),
        _base_image("ruby_slim", "ruby-slim",
                    ["3.3-slim", "3.4-slim"], "<major>.<minor>-slim",
                    "docker.io/library/ruby", "https://hub.docker.com/_/ruby",
                    "https://www.ruby-lang.org/en/downloads/branches/", "Docker Official Images"),
        _base_image("rust_slim", "rust-slim",
                    ["1-slim"], "<major>-slim",
                    "docker.io/library/rust", "https://hub.docker.com/_/rust",
                    "https://forge.rust-lang.org/", "Docker Official Images"),
        _base_image("dotnet_runtime_deps", "dotnet-runtime-deps",
                    ["8.0", "9.0"], "<major>.<minor>",
                    "mcr.microsoft.com/dotnet/runtime-deps",
                    "https://mcr.microsoft.com/en-us/artifact/mar/dotnet/runtime-deps/about",
                    "https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core", "Microsoft"),
        _base_image("alpine", "alpine",
                    ["3.20", "3.21", "3.22"], "<major>.<minor>",
                    "docker.io/library/alpine", "https://hub.docker.com/_/alpine",
                    "https://alpinelinux.org/releases/", "Docker Official Images"),
        _base_image("wolfi_base", "wolfi-base",
                    ["latest-rolling"], "rolling (distroless-style, apk-updatable)",
                    "cgr.dev/chainguard/wolfi-base", "https://github.com/wolfi-dev/os",
                    "https://github.com/wolfi-dev/os#readme", "Chainguard"),
    ]
    return _rows("base_image_runtime_surface", rows)


BASE_IMAGE_IDS: list[str] = [
    str(row["image_family_id"]) for row in _base_image_runtime_surfaces()
]


# ── packaging_mutator_catalog.jsonl ────────────────────────────────────────
def _mutator(key: str, input_edge: str, output_edge: str,
             target_family_keys: list[str], preconditions: list[str],
             postconditions: list[str], lossiness: str,
             proof_obligations: list[str], telemetry: list[str],
             base_image_refs: list[str] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "mutator_id": f"packmutator:{key}",
        "deterministic": True,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "target_family_refs": [f"packfamily:{k}" for k in target_family_keys],
        "preconditions": preconditions,
        "postconditions": postconditions,
        "lossiness_policy": lossiness,
        "proof_obligations": proof_obligations,
        "telemetry_fields": telemetry,
    }
    if base_image_refs is not None:
        row["base_image_refs"] = base_image_refs
    return row


LOSSLESS_CLAUSE = (
    "lossless: the source specification, intermediates, and rejected options are preserved "
    "with lineage back to the input; the emitted plan carries a rollback target"
)


def _packaging_mutator_catalog() -> list[dict[str, Any]]:
    rows = [
        _mutator("route_to_oci_image_build_plan",
                 "CompiledPrimitiveRoute+RuntimeDependencySet+BaseImageSelection",
                 "OciImageBuildPlan+PlanReceipt",
                 ["oci_image"],
                 ["route is compiled and proof-passed",
                  "runtime dependency set is fully pinned",
                  "selected base image family is a tracked surface"],
                 ["build plan references the base image by digest only",
                  "plan lists every file entering the build context",
                  "plan is byte-identical for identical inputs"],
                 LOSSLESS_CLAUSE,
                 ["dry_run_receipt", "sbom_receipt", "reproducible_build_receipt"],
                 ["plan_generation_duration_seconds", "dependency_count",
                  "base_image_digest", "estimated_image_layer_count"],
                 base_image_refs=list(BASE_IMAGE_IDS)),
        _mutator("route_to_terraform_module",
                 "InfrastructureCapabilityContract+ProviderRequirementSet",
                 "TerraformModulePackage+PlanReceipt",
                 ["terraform_module", "opentofu_module"],
                 ["capability contract declares every managed resource shape",
                  "provider requirements carry version constraints"],
                 ["module exposes only variables named in the contract",
                  "no credentials or account literals in emitted source",
                  "module source is byte-identical for identical inputs"],
                 LOSSLESS_CLAUSE,
                 ["dry_run_receipt", "policy_scan_receipt"],
                 ["plan_generation_duration_seconds", "resource_count",
                  "variable_count", "provider_constraint_count"]),
        _mutator("route_to_helm_chart",
                 "KubernetesWorkloadShape+ValuesSchema",
                 "PackagedHelmChart+LintReceipt",
                 ["helm_chart", "kubernetes_manifest_set"],
                 ["workload shape declares resources, probes, and image digests",
                  "values schema validates every exposed knob"],
                 ["rendered manifests match the workload shape exactly",
                  "chart lints clean and templates without cluster access",
                  "chart is byte-identical for identical inputs"],
                 LOSSLESS_CLAUSE,
                 ["dry_run_receipt", "policy_scan_receipt"],
                 ["render_duration_seconds", "manifest_object_count",
                  "values_knob_count"]),
        _mutator("listing_spec_to_marketplace_manifest_set",
                 "ListingSpec+DeployableSet",
                 "MarketplaceManifestSet+SubmissionChecklistReceipt",
                 ["marketplace_listing_bundle"],
                 ["listing spec carries pricing, support, and legal fields",
                  "every referenced deployable carries its own proof receipts"],
                 ["one bundle emitted per selected marketplace target",
                  "checklist completeness computed per target, never assumed",
                  "bundles are byte-identical for identical inputs"],
                 LOSSLESS_CLAUSE,
                 ["dry_run_receipt", "policy_scan_receipt"],
                 ["bundle_count", "checklist_completeness_ratio_per_target",
                  "missing_field_count"]),
        _mutator("image_pin_digest",
                 "ImageReferenceSet+DigestObservationSet",
                 "PinnedImageReferenceSet+PinReceipt",
                 ["oci_image", "helm_chart", "kubernetes_manifest_set",
                  "gcp_cloud_run_service", "devcontainer"],
                 ["every floating tag has a recorded digest observation",
                  "digest observations carry their resolution receipts"],
                 ["no floating tag survives in the output reference set",
                  "each pin records the tag it replaced and the observation it used"],
                 LOSSLESS_CLAUSE,
                 ["dry_run_receipt"],
                 ["references_pinned_count", "already_pinned_count",
                  "unresolvable_reference_count"],
                 base_image_refs=list(BASE_IMAGE_IDS)),
        _mutator("sbom_attach",
                 "BuiltDeployable+DependencyInventory",
                 "DeployableWithSbom+SbomReceipt",
                 ["oci_image", "helm_chart", "python_wheel", "npm_package",
                  "mcp_server_package", "buildpack"],
                 ["deployable identity is content-addressed (digest or checksum)",
                  "dependency inventory was produced by the build, not typed by hand"],
                 ["software bill of materials attached and referenced from the deployable identity",
                  "inventory row count recorded in the receipt"],
                 LOSSLESS_CLAUSE,
                 ["sbom_receipt"],
                 ["sbom_component_count", "sbom_format", "attachment_duration_seconds"]),
        _mutator("signature_attach",
                 "DeployableWithSbom+SigningPolicy",
                 "SignedDeployable+SignatureReceipt",
                 ["oci_image", "helm_chart", "python_wheel", "npm_package",
                  "github_action", "marketplace_listing_bundle"],
                 ["signing policy names the signing mechanism and key custody model",
                  "deployable carries an attached software bill of materials"],
                 ["signature stored beside the deployable identity",
                  "verification command pattern recorded as data in the receipt"],
                 LOSSLESS_CLAUSE,
                 ["signature_receipt"],
                 ["signature_mechanism", "verification_duration_seconds"]),
        _mutator("multiarch_matrix_expand",
                 "OciImageBuildPlan+PlatformMatrix",
                 "MultiArchBuildPlanSet+MatrixReceipt",
                 ["oci_image", "buildpack", "devcontainer"],
                 ["platform matrix lists explicit os/arch pairs",
                  "base image family publishes every requested platform"],
                 ["one build plan per platform plus a manifest-list plan",
                  "per-platform plans differ only in platform fields"],
                 LOSSLESS_CLAUSE,
                 ["dry_run_receipt", "reproducible_build_receipt"],
                 ["platform_count", "per_platform_plan_checksum_list"]),
    ]
    return _rows("deployment_packaging_mutator", rows)


# ── Pack assembly ──────────────────────────────────────────────────────────
JSONL_BUILDERS: dict[str, Any] = {
    "packaging_target_families.jsonl": _packaging_target_families,
    "base_image_runtime_surfaces.jsonl": _base_image_runtime_surfaces,
    "packaging_mutator_catalog.jsonl": _packaging_mutator_catalog,
    "cloud_marketplace_targets.jsonl": _cloud_marketplace_targets,
}


def build_pack() -> dict[str, list[dict[str, Any]]]:
    """Return {filename: rows} for every non-manifest pack file."""
    return {name: builder() for name, builder in JSONL_BUILDERS.items()}


def _canonical_bytes(pack: dict[str, list[dict[str, Any]]]) -> bytes:
    parts: list[str] = []
    for name in sorted(pack):
        parts.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in pack[name])
    return ("\n".join(parts) + "\n").encode("utf-8")


def build_manifest(pack: dict[str, list[dict[str, Any]]],
                   generated_date: str = DEFAULT_GENERATED_DATE) -> dict[str, Any]:
    row_counts = {name: len(rows) for name, rows in pack.items()}
    files = {name.rsplit(".", 1)[0]: name for name in sorted(pack)}
    return {
        "record_type": "deployment_packaging_and_container_surface_pack_manifest",
        "pack_id": PACK_ID,
        **BOUNDARY,
        "version": "0.1.0",
        "generator": "scripts/build_deployment_packaging_surface_pack.py",
        "generated_utc": generated_date,
        "source_family": PACK_SOURCE_FAMILY,
        "source_status": PACK_SOURCE_STATUS,
        "evidence_status": PACK_EVIDENCE_STATUS,
        "boundary": (
            "candidate=true; serves_truth=false; packaging families, base-image tracking rows, "
            "mutators, and marketplace targets are CONTRACTS — no build, scan, signature, "
            "submission, or tracking run is claimed; validation command patterns are data, "
            "never executed by this pack"
        ),
        "owner_directive": (
            "2026-07-02: package primitives as terraform definitions, deployment component sets, "
            "docker image builds, and cloud-marketplace deployables; track base images "
            "(for example python:3.11-slim) as maintained surfaces"
        ),
        "files": files,
        "file_count": len(files),
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "content_sha256": hashlib.sha256(_canonical_bytes(pack)).hexdigest(),
        "reuses": [
            "catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds",
            "catalog/knowledge-packs/data/marketplace-primitive-source-surfaces",
        ],
    }


def write_pack(generated_date: str = DEFAULT_GENERATED_DATE) -> dict[str, Any]:
    pack = build_pack()
    manifest = build_manifest(pack, generated_date)
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in pack.items():
        with (PACK_DIR / name).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return manifest


# ── Shared validation (used by the builder self-test AND the checker) ─────
def _walk_strings(value: Any, key_path: str = "") -> list[tuple[str, str]]:
    """Yield (key_path, string) pairs for every string in a nested structure."""
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(_walk_strings(child, f"{key_path}.{key}" if key_path else str(key)))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_strings(child, key_path))
    elif isinstance(value, str):
        found.append((key_path, value))
    return found


def validate_pack(pack: dict[str, list[dict[str, Any]]]) -> None:
    """Raise AssertionError on any invariant violation (shared single source)."""
    assert set(pack) == set(JSONL_BUILDERS), \
        f"pack files diverge from the builder registry: {sorted(set(pack) ^ set(JSONL_BUILDERS))}"

    # Boundary + unique version-free ids on every row.
    for name, rows in pack.items():
        assert rows, f"{name}: expected rows"
        id_field = ID_FIELD_BY_FILE[name]
        ids = [str(row.get(id_field) or "") for row in rows]
        assert "" not in ids and len(ids) == len(set(ids)), \
            f"{name}: {id_field} must be present and unique"
        for row, row_id in zip(rows, ids):
            assert row.get("candidate") is True and row.get("serves_truth") is False, \
                f"{name}/{row_id}: truth boundary violated"
            assert not FORBIDDEN_ID_PATTERN.search(row_id), \
                f"{name}: id must be version-free: {row_id!r}"

    families = pack["packaging_target_families.jsonl"]
    base_images = pack["base_image_runtime_surfaces.jsonl"]
    mutators = pack["packaging_mutator_catalog.jsonl"]
    markets = pack["cloud_marketplace_targets.jsonl"]
    family_ids = {str(row["family_id"]) for row in families}
    base_ids = {str(row["image_family_id"]) for row in base_images}
    market_ids = {str(row["market_id"]) for row in markets}

    # Owner-directed coverage: the exact family and mutator sets exist.
    assert family_ids == set(PACKAGING_FAMILY_IDS), \
        f"packaging families diverge from the owner-directed set: " \
        f"{sorted(family_ids ^ set(PACKAGING_FAMILY_IDS))}"
    expected_mutators = {f"packmutator:{key}" for key in REQUIRED_MUTATOR_KEYS}
    mutator_ids = {str(row["mutator_id"]) for row in mutators}
    assert mutator_ids == expected_mutators, \
        f"mutators diverge from the owner-directed set: {sorted(mutator_ids ^ expected_mutators)}"

    # Packaging families: edges, conventions, validation pattern, receipts,
    # failure modes, resolvable non-empty marketplace targets.
    referenced_markets: set[str] = set()
    for row in families:
        fid = row["family_id"]
        for field in ("input_edge", "output_edge"):
            edge = str(row.get(field) or "")
            assert edge and "->" not in edge, f"{fid}: {field} must be a single non-empty edge"
        assert row.get("packaging_conventions"), f"{fid}: needs packaging_conventions"
        assert str(row.get("validation_command_pattern") or "").strip(), \
            f"{fid}: needs a validation_command_pattern"
        assert row.get("validation_command_is_data_only") is True, \
            f"{fid}: validation command must be declared data-only"
        receipts = row.get("proof_receipts") or {}
        assert set(receipts) == set(REQUIRED_PROOF_RECEIPTS) and all(receipts.values()), \
            f"{fid}: proof_receipts must declare exactly {REQUIRED_PROOF_RECEIPTS}"
        assert row.get("known_failure_modes"), f"{fid}: needs known_failure_modes"
        targets = row.get("marketplace_targets") or []
        assert targets and set(targets) <= market_ids, \
            f"{fid}: marketplace_targets must be non-empty and resolve"
        referenced_markets.update(targets)
    assert referenced_markets == market_ids, \
        f"orphaned marketplace targets (referenced by no family): {sorted(market_ids - referenced_markets)}"

    # Base images: tracking contracts only, full trigger policy, receipts.
    for row in base_images:
        bid = row["image_family_id"]
        for field in ("image_family", "tag_pattern", "pull_reference", "registry_url",
                      "digest_pinning_policy", "eol_policy_url", "sbom_policy",
                      "freshness_policy", "maintainer"):
            assert str(row.get(field) or "").strip(), f"{bid}: missing {field}"
        assert row.get("tracked_tags"), f"{bid}: needs tracked_tags"
        triggers = row.get("rebuild_trigger_policy") or {}
        assert set(triggers) == set(REQUIRED_REBUILD_TRIGGERS) and all(triggers.values()), \
            f"{bid}: rebuild_trigger_policy must declare exactly {REQUIRED_REBUILD_TRIGGERS}"
        assert row.get("maintenance_receipts"), f"{bid}: needs maintenance_receipts"
        assert row.get("tracking_status") == BASE_IMAGE_TRACKING_STATUS, \
            f"{bid}: base-image rows are tracking contracts, not running trackers"

    # Mutators: deterministic, complete contracts, resolvable references.
    for row in mutators:
        mid = row["mutator_id"]
        assert row.get("deterministic") is True, f"{mid}: mutators must be deterministic"
        for field in ("input_edge", "output_edge"):
            edge = str(row.get(field) or "")
            assert edge and "->" not in edge, f"{mid}: {field} must be a single non-empty edge"
        for field in ("preconditions", "postconditions", "proof_obligations", "telemetry_fields"):
            assert row.get(field), f"{mid}: needs non-empty {field}"
        assert set(row["proof_obligations"]) <= set(REQUIRED_PROOF_RECEIPTS), \
            f"{mid}: proof_obligations must name known proof receipts"
        assert "lossless" in str(row.get("lossiness_policy") or "") \
            and "lineage" in str(row.get("lossiness_policy") or ""), \
            f"{mid}: lossiness_policy must declare lossless handling with lineage"
        refs = row.get("target_family_refs") or []
        assert refs and set(refs) <= family_ids, \
            f"{mid}: target_family_refs must be non-empty and resolve"
        if "base_image_refs" in row:
            assert row["base_image_refs"] and set(row["base_image_refs"]) <= base_ids, \
                f"{mid}: base_image_refs must resolve to tracked base images"

    # Marketplace targets: docs url, checklist, receipts, no submission claims.
    for row in markets:
        mid = row["market_id"]
        assert row.get("submission_checklist"), f"{mid}: needs a submission_checklist"
        assert row.get("validation_receipts"), f"{mid}: needs validation_receipts"
        assert row.get("submission_state") == "no_listing_submitted", \
            f"{mid}: no marketplace submission may be claimed in this pack"

    # URL hygiene + credential hygiene across every row.
    for name, rows in pack.items():
        for row in rows:
            for key_path, text in _walk_strings(row):
                leaf = key_path.rsplit(".", 1)[-1].lower()
                if leaf.endswith("_url") or leaf == "eol_calendar_ref":
                    assert text.startswith("https://") and "@" not in text and " " not in text, \
                        f"{name}/{key_path}: url must be official https without userinfo: {text!r}"
                assert not any(sub in leaf for sub in FORBIDDEN_KEY_SUBSTRINGS), \
                    f"{name}/{key_path}: credential-shaped field name is forbidden"
                assert not FORBIDDEN_VALUE_PATTERN.search(text), \
                    f"{name}/{key_path}: value matches a leaked-credential pattern"


def self_test() -> int:
    pack = build_pack()
    validate_pack(pack)
    manifest = build_manifest(pack)
    assert manifest.get("candidate") is True and manifest.get("serves_truth") is False
    assert manifest["total_rows"] == sum(len(rows) for rows in pack.values())
    assert manifest["file_count"] == len(pack)
    assert set(manifest["row_counts"]) == set(JSONL_BUILDERS)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="validate the generated pack without writing")
    parser.add_argument("--write", action="store_true",
                        help="write the pack + manifest to disk")
    parser.add_argument("--date", default=DEFAULT_GENERATED_DATE,
                        help="manifest generated_utc date (manifest-only, never in rows)")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(args.date)
    print(json.dumps({"pack_id": manifest["pack_id"], "files": manifest["file_count"],
                      "total_rows": manifest["total_rows"],
                      "content_sha256": manifest["content_sha256"]}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
