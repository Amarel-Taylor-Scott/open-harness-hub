#!/usr/bin/env python3
"""Run realistic multi-prompt primitive reuse benchmarks.

This complements ``run_token_savings_experiments.py``. The older harness tests
single capability retrieval. This harness tests full prompt sessions: multi-
surface app builds, data warehouse builds, compliance systems, RAG agents,
DevOps migrations, and other long developer workflows.

Every row is candidate-only evidence. Token counts use a deterministic chars/4
proxy plus explicit workload-size estimates so the same scenario can be rerun
against a base registry and an expanded primitive corpus.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install  # noqa: E402

_install()

from scripts._jsonl import read_jsonl_tolerant  # noqa: E402
from scripts._repo_paths import repo_root as _repo_root  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402
from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: E402


RECORD_TYPE = "realistic_session_primitive_benchmark"
OUT_DIR = _resource("data") / "dev-intel" / "realistic_session_benchmarks"
TOKENS_BASIS = "deterministic_proxy_chars/4+scenario_workload_estimates"
CHARS_PER_TOKEN = 4
DEFAULT_SESSIONS = 12
DEFAULT_K = 8
DEFAULT_COMPONENTS_PER_TURN = 4
DEFAULT_CONTEXT_WINDOW = 262_144
SCORE_FLOOR = 1.0
BASE_CARD_SOURCES = (
    "data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",
    "data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl",
    "catalog/knowledge-packs/data/primitive-search-index/search_docs.jsonl",
)
SUPERVISED_CYCLE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal" / "supervised_cycles"
SPECIALIZED_PACK_DIR = _resource("data") / "dev-intel" / "primitive_factory" / "specialized_packs"
ML_LIFECYCLE_PACK_PATH = SPECIALIZED_PACK_DIR / "ml_lifecycle_primitive_cards.jsonl"
ML_LIFECYCLE_MANIFEST_PATH = SPECIALIZED_PACK_DIR / "ml_lifecycle_manifest.json"
ML_LIFECYCLE_SOURCE_REF = "conversation:production_ml_role_matrix:2026-07-07"
ML_LIFECYCLE_PACKAGED_AT = "2026-07-07T00:00:00Z"
ORG_SCALE_PACK_PATH = SPECIALIZED_PACK_DIR / "large_org_primitive_cards.jsonl"
ORG_SCALE_MANIFEST_PATH = SPECIALIZED_PACK_DIR / "large_org_manifest.json"
ORG_SCALE_SOURCE_REF = "conversation:google_scale_org_model:2026-07-07"
ORG_SCALE_PACKAGED_AT = "2026-07-07T00:00:00Z"
ML_LIFECYCLE_ROLE_BY_STAGE = {
    "product": "ml_product_owner",
    "architecture": "technical_lead_solution_architect",
    "governance": "data_steward_governance_lead",
    "data_engineering": "data_engineer",
    "analytics": "analytics_engineer",
    "science": "data_scientist",
    "labeling": "annotation_specialist",
    "ml_engineering": "ml_engineer",
    "mlops": "mlops_platform_engineer",
    "backend": "backend_api_engineer",
    "frontend": "frontend_mobile_engineer",
    "infrastructure": "devops_cloud_engineer",
    "sre": "site_reliability_engineer",
    "qa": "qa_test_automation_engineer",
    "security": "security_devsecops_engineer",
    "privacy": "privacy_legal_compliance_lead",
    "responsible_ai": "responsible_ai_risk_lead",
    "support": "support_operations_human_review",
    "documentation": "technical_writer_documentation_owner",
    "program": "engineering_manager_delivery_lead",
    "data": "data_engineer_analytics_engineer_steward",
    "ml": "data_ml_lead",
    "platform": "platform_devops_engineer",
    "application": "full_stack_engineer",
    "reliability": "platform_sre_engineer",
    "operations": "qa_support_feedback_owner",
}
ML_LIFECYCLE_CARD_ACTIONS = (
    ("plan", "requirements contracts architecture acceptance criteria rollout gates"),
    ("build", "implementation templates pipelines schemas services dashboards workflows"),
    ("verify", "tests validation evaluation security privacy risk release readiness"),
    ("operate", "monitoring runbooks feedback retraining incident response ownership"),
)
ML_ROLE_DETAIL_PLANES = (
    ("actions", "action checklist workflow execution collaboration decision ownership"),
    ("deliverables", "deliverables artifacts documents reports manifests records"),
    ("tools", "tools platforms services libraries systems integration"),
    ("concepts", "concepts methods patterns controls technical vocabulary"),
    ("launch_gate", "launch readiness acceptance signoff rollback production gate"),
    ("handoff", "handoff runbook ownership escalation feedback operations"),
)
ML_ROLE_DETAIL_ROWS: tuple[dict[str, str], ...] = (
    {
        "role_id": "product_manager",
        "title": "Product Manager / ML Product Owner",
        "stage": "product",
        "actions": "business objective ML use cases success metrics prioritization user stories acceptance criteria rollout strategy A/B test go no-go launch decisions business impact retraining retirement",
        "deliverables": "product requirements document ML use-case definition success metrics launch criteria experiment plan A/B testing plan rollout plan feedback-loop requirements risk impact summary",
        "tools": "Jira Linear Asana Azure DevOps Confluence Notion Figma Miro Amplitude Mixpanel Looker Tableau LaunchDarkly Statsig Optimizely Slack Teams",
        "concepts": "KPI design A/B testing feature flags product analytics experimentation user segmentation funnel analysis model success metrics human-in-the-loop workflows rollout rollback",
    },
    {
        "role_id": "technical_lead_solution_architect",
        "title": "Technical Lead / Solution Architect",
        "stage": "architecture",
        "actions": "end-to-end architecture online batch streaming edge prediction data flow service boundaries cloud storage serving monitoring integration points failure points rollback disaster recovery",
        "deliverables": "system architecture data flow diagram model serving architecture security architecture deployment architecture integration design ADRs non-functional requirements production readiness checklist",
        "tools": "Lucidchart Miro Draw.io C4 OpenAPI Swagger Postman Terraform Kubernetes Helm GitHub GitLab Confluence Notion",
        "concepts": "microservices event-driven architecture REST gRPC queues streaming batch feature stores model registries container orchestration IaC observability SLOs security boundaries lineage",
    },
    {
        "role_id": "domain_expert",
        "title": "Domain Expert / Subject Matter Expert",
        "stage": "domain",
        "actions": "target label definition edge cases labeling guidelines ambiguous example review model prediction validation business rules human review high-risk cases error analysis escalation",
        "deliverables": "domain rules labeling guidelines edge-case catalog gold-standard test set business-rule document error review notes human review guidelines",
        "tools": "Label Studio Labelbox Prodigy CVAT spreadsheets internal business systems case management annotation dashboards Notion Confluence Slack Teams",
        "concepts": "label taxonomy business ontology decision rules human review workflows error cost analysis ground truth expert adjudication operational constraints",
    },
    {
        "role_id": "data_steward",
        "title": "Data Owner / Data Steward / Governance Lead",
        "stage": "governance",
        "actions": "approved data sources ownership approvals sensitive data classification retention catalog access controls lineage schema changes data contracts consent rights auditability",
        "deliverables": "data inventory data classification data access policy data retention policy data lineage documentation dataset approval record data contract data governance checklist",
        "tools": "DataHub Collibra Alation Atlan BigQuery Snowflake Redshift Databricks Unity Catalog IAM DLP GX dbt docs OpenLineage Marquez cloud audit logs",
        "concepts": "data cataloging metadata management lineage PII classification data contracts RBAC ABAC encryption audit logging consent management retention governance",
    },
    {
        "role_id": "data_engineer",
        "title": "Data Engineer",
        "stage": "data_engineering",
        "actions": "source connectors ingestion pipelines APIs databases logs object stores event streams raw cleaned curated layers batch streaming schema validation dedupe late data backfills partitions feature computation snapshots retries",
        "deliverables": "ingestion pipelines ETL ELT jobs data validation rules cleaned datasets curated training tables feature source tables pipeline DAGs quality reports backfill scripts data contracts",
        "tools": "Python SQL Scala Java Airflow Dagster Prefect Spark PySpark Flink Beam Kafka Kinesis PubSub RabbitMQ dbt GX Fivetran Airbyte Snowflake BigQuery Redshift Databricks S3 GCS Delta Iceberg Hudi Terraform Docker GitHub Actions",
        "concepts": "ETL ELT batch stream lake warehouse lakehouse partitioning schema evolution data contracts incremental loading CDC idempotent pipelines feature generation quality lineage orchestration",
    },
    {
        "role_id": "analytics_engineer",
        "title": "Analytics Engineer / BI Engineer",
        "stage": "analytics",
        "actions": "curated analytics tables business metrics dashboard-ready models metric consistency model performance dashboards business KPIs A/B reporting SQL tests transformation docs semantic layer stakeholder interpretation",
        "deliverables": "analytics marts KPI definitions metric dictionary dashboards A/B test reports model impact reports dbt models dbt tests semantic layer definitions",
        "tools": "SQL dbt Looker Tableau Power BI Mode Hex Observable Jupyter Snowflake BigQuery Redshift Databricks GitHub GitLab MetricFlow Cube LookML Airflow Dagster GX",
        "concepts": "dimensional modeling star schema semantic layer metric governance data marts BI dashboards cohort analysis funnel analysis experiment analysis SQL testing analytics CI/CD",
    },
    {
        "role_id": "data_analyst",
        "title": "Data Analyst / Decision Scientist",
        "stage": "analysis",
        "actions": "historical exploration problem validation opportunity sizing baseline measurement segment analysis adoption tracking business impact post-launch analysis metric regression investigation executive communication",
        "deliverables": "exploratory analysis baseline reports business impact analysis segment-level performance reports A/B test analysis monitoring dashboards executive summaries",
        "tools": "SQL Python R Jupyter Hex Mode Looker Tableau Power BI Excel Google Sheets Amplitude Mixpanel Snowflake BigQuery Redshift stats packages",
        "concepts": "hypothesis testing causal inference cohort analysis confidence intervals experiment design KPI tracking funnel analysis segmentation statistical significance power analysis",
    },
    {
        "role_id": "data_scientist",
        "title": "Data Scientist / ML Scientist",
        "stage": "science",
        "actions": "ML task definition EDA labels evaluation metrics baselines features training hyperparameters offline evaluation model comparison cross-validation error analysis leakage fairness robustness explainability retraining triggers",
        "deliverables": "EDA notebook baseline model feature analysis training notebook experiment results evaluation report error analysis report model selection recommendation model card fairness robustness analysis retraining recommendation",
        "tools": "Python R Jupyter VS Code pandas NumPy SciPy scikit-learn XGBoost LightGBM CatBoost PyTorch TensorFlow Hugging Face MLflow Weights Biases Neptune Comet Optuna Ray Tune SHAP LIME SQL Spark Databricks",
        "concepts": "supervised unsupervised regression classification ranking forecasting anomaly detection deep learning embeddings evaluation hyperparameter tuning feature engineering cross-validation calibration explainability leakage detection fairness",
    },
    {
        "role_id": "labeling_specialist",
        "title": "Labeling / Annotation Specialist",
        "stage": "labeling",
        "actions": "label examples guidelines ambiguous flags model-suggested labels active learning disagreements gold sets consistency escalation guideline updates label audits human feedback",
        "deliverables": "labeled dataset annotation guideline feedback gold-standard examples adjudicated labels label quality report inter-annotator agreement report human feedback records",
        "tools": "Label Studio Labelbox Prodigy CVAT Scale AI Snorkel spreadsheets custom review tools moderation tools annotation QA dashboards",
        "concepts": "ground truth label taxonomy inter-annotator agreement active learning weak supervision human-in-the-loop learning label noise adjudication gold set creation",
    },
    {
        "role_id": "ml_engineer",
        "title": "ML Engineer",
        "stage": "ml_engineering",
        "actions": "notebook productionization reproducible training pipelines feature pipelines feature store integration model packaging inference optimization registry versions tests batch scoring online serving validation artifacts retraining monitoring",
        "deliverables": "production training pipeline feature pipeline model artifact model registry entry inference container batch scoring job online inference service model tests retraining workflow deployment manifest monitoring hooks",
        "tools": "Python PyTorch TensorFlow scikit-learn MLflow Weights Biases Feast DVC Kubeflow Metaflow Airflow Dagster Prefect Docker Kubernetes KServe Seldon BentoML Ray Serve Triton TorchServe TensorFlow Serving ONNX TorchScript Spark Ray SageMaker Azure ML Vertex AI GitHub Actions Terraform Helm",
        "concepts": "reproducible training packaging versioning feature stores registry online inference batch inference serving optimization quantization distillation containers GPU autoscaling CI/CD CT drift",
    },
    {
        "role_id": "mlops_engineer",
        "title": "MLOps Engineer / ML Platform Engineer",
        "stage": "mlops",
        "actions": "pipeline templates registry infrastructure feature store training infrastructure GPU CPU environments CI/CD promotion deployment templates monitoring integration retraining automation artifact storage governance gates self-service docs",
        "deliverables": "ML platform pipeline templates CI/CD workflows training infrastructure model registry feature store artifact repository deployment templates monitoring templates retraining automation governance gates platform documentation",
        "tools": "MLflow Kubeflow Airflow Dagster Prefect Argo Workflows Kubernetes Docker Helm Terraform Pulumi GitHub Actions GitLab CI Jenkins CircleCI Argo CD Flux Feast DVC S3 GCS ADLS SageMaker Azure ML Google Cloud Prometheus Grafana Evidently WhyLabs Arize Fiddler Vault secret managers",
        "concepts": "MLOps CI/CD CT orchestration registry feature store artifacts containers IaC GitOps promotion governance reproducibility automated retraining deployment automation",
    },
    {
        "role_id": "backend_engineer",
        "title": "Backend Engineer / API Engineer",
        "stage": "backend",
        "actions": "inference APIs request schemas response schemas validation model endpoint calls real-time features business rules auth authorization rate limits caching timeouts retries fallbacks prediction logs workflow integration async flows API tests contract tests",
        "deliverables": "prediction API service integration request response schema OpenAPI spec API tests integration tests fallback logic logging tracing authentication authorization production service code",
        "tools": "Python Java Go Node.js C# FastAPI Flask Django Spring Boot Express NestJS REST GraphQL gRPC OpenAPI Swagger Postman Redis PostgreSQL MySQL MongoDB Kafka RabbitMQ PubSub Docker Kubernetes API Gateway Kong Apigee Envoy NGINX GitHub Actions Datadog Prometheus Grafana OpenTelemetry",
        "concepts": "API design services microservices auth caching queues rate limiting circuit breakers retries idempotency schema validation contract testing distributed tracing logging feature retrieval online inference",
    },
    {
        "role_id": "frontend_engineer",
        "title": "Frontend Engineer / Mobile Engineer",
        "stage": "frontend",
        "actions": "model output UI recommendations classifications scores generated responses feedback capture confidence warnings explanations loading fallback feature flags A/B variants telemetry accessibility graceful errors user adoption",
        "deliverables": "model-powered UI feedback capture flow experiment variants telemetry events error states accessibility-compliant UI frontend integration tests user behavior tracking",
        "tools": "React Next.js Vue Angular TypeScript JavaScript Swift Kotlin React Native Flutter GraphQL REST clients Figma Storybook LaunchDarkly Statsig Optimizely Segment Amplitude Mixpanel Sentry Cypress Playwright Jest",
        "concepts": "human-AI interaction feedback loops feature flags experimentation telemetry API integration accessibility progressive rollout explainable UI error boundaries UX uncertainty",
    },
    {
        "role_id": "devops_cloud_engineer",
        "title": "DevOps / Cloud Infrastructure Engineer",
        "stage": "infrastructure",
        "actions": "cloud infrastructure environments CI/CD container registries Kubernetes networking IAM service accounts secrets encryption databases object storage queues compute GPU nodes autoscaling resource limits costs disaster recovery rollback",
        "deliverables": "cloud infrastructure Kubernetes clusters CI/CD pipelines infrastructure-as-code modules container registry setup secrets management environment configuration autoscaling policies deployment automation cost monitoring backup recovery",
        "tools": "AWS Azure Google Cloud Terraform Pulumi CloudFormation Bicep Docker Kubernetes EKS AKS GKE Helm Kustomize GitHub Actions GitLab CI Jenkins CircleCI Argo CD Flux Vault AWS Secrets Manager Azure Key Vault Google Secret Manager CloudWatch Azure Monitor Google Cloud Monitoring Prometheus Grafana NGINX Envoy Istio Linkerd",
        "concepts": "IaC containers Kubernetes GitOps CI/CD cloud networking IAM secrets autoscaling load balancing blue-green canary disaster recovery cost optimization environment isolation",
    },
    {
        "role_id": "sre",
        "title": "Site Reliability Engineer / Production Operations Engineer",
        "stage": "sre",
        "actions": "SLIs SLOs dashboards alerts on-call runbooks uptime latency throughput errors resources incidents RCA rollbacks load testing capacity failure scenarios dependencies logs metrics traces model alerts",
        "deliverables": "SLOs SLIs alert rules dashboards runbooks incident response process postmortems capacity plans reliability reports rollback procedures",
        "tools": "Prometheus Grafana Datadog New Relic OpenTelemetry CloudWatch Azure Monitor Google Cloud Monitoring PagerDuty Opsgenie ELK OpenSearch Loki Jaeger Tempo Sentry k6 Locust JMeter Kubernetes dashboards service mesh observability",
        "concepts": "observability metrics logs traces alerting SLOs SLIs error budgets incident response postmortems runbooks capacity planning autoscaling high availability disaster recovery rollbacks",
    },
    {
        "role_id": "qa_engineer",
        "title": "QA Engineer / Test Automation Engineer",
        "stage": "qa",
        "actions": "test strategy data pipeline tests model schema tests API tests frontend tests batch scoring tests edge cases failure modes regression performance rollback monitoring alerts staging validation release gates",
        "deliverables": "test plan automated test suite data validation tests model behavior tests API tests UI tests load test report regression test report release validation report",
        "tools": "pytest unittest Great Expectations dbt tests Postman Newman Pact Selenium Cypress Playwright k6 Locust JMeter Tox GitHub Actions GitLab CI TestRail Allure Docker Kubernetes test environments",
        "concepts": "unit integration e2e contract data validation schema validation regression load chaos model behavior golden datasets canary validation release gates",
    },
    {
        "role_id": "security_engineer",
        "title": "Security Engineer / DevSecOps Engineer",
        "stage": "security",
        "actions": "threat modeling API security IAM data access secrets vulnerability scanning dependency scanning container scanning CI/CD permissions model artifact security training data inference data audit logging endpoint security prompt injection abuse cases incident response",
        "deliverables": "threat model security architecture review IAM review vulnerability scan results container scan results secrets management plan API security review supply chain controls security sign-off abuse-case analysis incident response plan",
        "tools": "Snyk Dependabot Renovate Trivy Grype Clair Semgrep CodeQL SonarQube OWASP ZAP Burp Suite Vault secret managers IAM WAF SIEM CloudTrail audit logs Sigstore Cosign SBOM GitHub Advanced Security OPA Gatekeeper",
        "concepts": "secure SDLC threat modeling IAM least privilege secrets encryption API security container security supply chain SBOM SAST DAST dependency scanning model endpoint security prompt injection defense data exfiltration audit logging",
    },
    {
        "role_id": "privacy_legal_compliance",
        "title": "Privacy / Legal / Compliance Lead",
        "stage": "privacy",
        "actions": "data use review consent retention third-party licenses PII sensitive data cross-border transfer regulated decisions human review explanations notices audit documentation vendor risk model risk internal AI policies",
        "deliverables": "privacy review DPIA legal approval data usage approval vendor risk assessment compliance checklist model risk documentation user notice language audit package retention policy",
        "tools": "OneTrust TrustArc GRC platforms data catalogs DLP IAM contract management model inventory audit logging privacy templates NIST AI RMF documentation",
        "concepts": "PII PHI PCI consent data minimization purpose limitation retention data residency auditability model risk human oversight explainability regulatory compliance",
    },
    {
        "role_id": "responsible_ai_lead",
        "title": "Responsible AI / AI Risk / Fairness Lead",
        "stage": "responsible_ai",
        "actions": "responsible AI requirements intended uses unintended uses impacted groups segment performance fairness metrics harmful failure modes red teaming robustness explainability safety filters escalation thresholds hallucination toxicity prompt injection data leakage model cards risk acceptance monitoring",
        "deliverables": "responsible AI review fairness analysis bias analysis robustness report red-team report safety evaluation model card risk register mitigation plan human oversight plan",
        "tools": "Fairlearn IBM AI Fairness 360 SHAP LIME What-If Tool Evidently Arize Fiddler WhyLabs Ragas DeepEval TruLens Promptfoo Guardrails content safety APIs human evaluation platforms NIST AI RMF OWASP LLM Top 10",
        "concepts": "fairness metrics bias testing explainability transparency robustness red teaming model cards data cards human-in-the-loop safety filters toxicity hallucination prompt injection model abuse trustworthy AI governance",
    },
    {
        "role_id": "ux_designer",
        "title": "UX Designer / UX Researcher",
        "stage": "ux",
        "actions": "user research workflows model-powered experiences confidence indicators explanations human override feedback capture user trust fallback states review queues implementation collaboration usability metrics misuse evaluation",
        "deliverables": "user journey maps wireframes prototypes AI interaction design feedback flow human review flow usability test report UX acceptance criteria",
        "tools": "Figma FigJam Miro Maze UserTesting Dovetail Storybook Amplitude Mixpanel Hotjar FullStory design systems",
        "concepts": "human-AI interaction trust calibration explainable UX feedback loops accessibility error recovery human review confidence communication design systems usability testing",
    },
    {
        "role_id": "technical_writer",
        "title": "Technical Writer / Documentation Owner",
        "stage": "documentation",
        "actions": "model documentation API documentation runbooks onboarding guides model cards data cards deployment procedures rollback procedures monitoring docs alerts release notes limitations intended use unintended use audit materials",
        "deliverables": "model card data card API docs runbooks deployment guide monitoring guide troubleshooting guide release notes architecture docs user-facing documentation",
        "tools": "Markdown MkDocs Sphinx Docusaurus OpenAPI Swagger Confluence Notion GitHub GitLab Mermaid Lucidchart ReadMe Stoplight Datadog Grafana dashboard links",
        "concepts": "API documentation model cards data cards runbooks architecture docs release management knowledge management operational documentation audit documentation",
    },
    {
        "role_id": "support_ops",
        "title": "Customer Support / Operations Analyst / Human Review Team",
        "stage": "support",
        "actions": "uncertain output review high-risk output review user complaints false positives false negatives recurring issues feedback labels safety escalation review queues operational impact manual workload retraining feedback",
        "deliverables": "escalation reports human review decisions feedback labels support issue summaries model issue tickets operational impact reports review queue metrics",
        "tools": "Zendesk Intercom Salesforce Service Cloud internal review tools annotation tools Jira Linear BI dashboards Slack Teams CRM case management model monitoring dashboards",
        "concepts": "human-in-the-loop review escalation workflows feedback loops ground truth collection manual review queues operational metrics false positive review false negative review",
    },
    {
        "role_id": "delivery_lead",
        "title": "Engineering Manager / Delivery Lead / Technical Program Manager",
        "stage": "program",
        "actions": "milestone planning cross-functional coordination dependencies delivery risks ceremonies ownership production readiness launch approvals documentation post-launch issues on-call support resourcing",
        "deliverables": "project plan milestone plan risk register dependency tracker launch checklist stakeholder updates production readiness review post-launch review",
        "tools": "Jira Linear Asana Azure DevOps Confluence Notion Slack Teams Miro Google Sheets Excel roadmap tools incident review tools",
        "concepts": "agile delivery risk management dependency management production readiness release management stakeholder communication RACI ownership delivery governance",
    },
)
ORG_SCALE_CARD_ACTIONS = (
    ("structure", "org chart hierarchy operating model centralized embedded ownership"),
    ("responsibilities", "mission responsibilities interfaces decision rights escalation"),
    ("technologies", "technologies platforms systems tools infrastructure integrations"),
    ("governance", "review forums policies launch gates risk compliance reliability"),
)
ORG_SCALE_STAGE_OWNER = {
    "corporate": "executive_leadership",
    "search": "search_knowledge_product_org",
    "ads": "ads_commerce_product_org",
    "media": "youtube_media_platform_org",
    "cloud": "cloud_enterprise_platform_org",
    "platforms": "android_chrome_play_platform_org",
    "hardware": "devices_hardware_silicon_supply_chain_org",
    "ai": "ai_research_frontier_models_org",
    "moonshots": "other_bets_moonshot_org",
    "infrastructure": "technical_infrastructure_org",
    "devinfra": "developer_infrastructure_productivity_org",
    "sre": "site_reliability_org",
    "data": "data_platform_analytics_org",
    "mlops": "ml_platform_mLOps_org",
    "security": "security_privacy_trust_org",
    "trust": "trust_safety_integrity_org",
    "gtm": "go_to_market_org",
    "legal": "legal_regulatory_public_policy_org",
    "finance": "finance_procurement_business_ops_org",
    "people": "people_operations_org",
    "governance": "governance_forum_review_board",
    "workflow": "global_delivery_operating_cadence",
    "engineering": "engineering_ladder_and_execution_org",
}


SCENARIO_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "template_id": "multi_surface_saas_control_plane",
        "category": "massive_multi_surface_app",
        "title": "Build a multi-tenant SaaS control plane with web app, admin app, API, workers, billing, and observability.",
        "surfaces": ["react_app", "admin_dashboard", "fastapi_api", "postgres", "queue_worker", "terraform"],
        "turns": [
            ("product", "requirements", "Turn the product brief into an implementation plan for tenant onboarding, project scaffold, workspace settings, roles, billing, audit trail, and support tooling.", 7600),
            ("backend", "auth", "Implement login session management with password reset, MFA hooks, RBAC authorization, tenant isolation, secret handling, and API receipts.", 9200),
            ("database", "schema", "Create Postgres schemas, migrations, seed data, audit log tables, account limits, subscription tracker tables, and tenant-scoped indexes.", 10800),
            ("api", "routes", "Build API gateway routes, FastAPI endpoints, webhook handlers, pagination, idempotency wrappers, retry wrappers, and error receipts.", 12400),
            ("frontend", "surfaces", "Build the React user app, admin dashboard, tables, filters, settings pages, empty states, export actions, and accessibility states.", 14200),
            ("workers", "async", "Add queue workers, email service flows, cache layer, scheduled jobs, notifications, and failure recovery paths.", 11800),
            ("quality", "tests", "Write schema contract tests, route fixture tests, Playwright flows, privacy boundary checks, and candidate boundary gates.", 9000),
            ("ops", "deploy", "Ship Terraform, Kubernetes jobs, Cloud Run service definitions, log metric trace dashboards, SLO alerts, and runbooks.", 11200),
        ],
    },
    {
        "template_id": "retail_data_warehouse",
        "category": "data_warehouse_build",
        "title": "Build a retail analytics warehouse from raw app, order, inventory, and marketing sources.",
        "surfaces": ["bigquery", "dbt", "airflow", "dagster", "dashboard", "data_quality"],
        "turns": [
            ("architecture", "warehouse", "Design the raw, staging, intermediate, and mart layers for a retail data warehouse with orders, inventory, customers, sessions, and ad spend.", 11800),
            ("ingestion", "connectors", "Build source adapters for CSV drops, webhook events, app analytics, Shopify-like order data, inventory snapshots, and late arriving records.", 12600),
            ("modeling", "schema", "Create BigQuery SQL and dbt models for star schemas, slowly changing dimensions, fact tables, bridge tables, and semantic metrics.", 15200),
            ("orchestration", "pipelines", "Implement Airflow tasks or Dagster assets with idempotent loads, partitioning, retries, freshness checks, and backfill controls.", 13800),
            ("quality", "validation", "Add data quality tests for uniqueness, referential integrity, accepted values, null thresholds, row count drift, and anomaly receipts.", 10400),
            ("governance", "privacy", "Add PII redaction, column classification, access policies, lineage, data contracts, and reproducibility metadata.", 9800),
            ("analytics", "dashboards", "Build executive dashboards, cohort tables, retention metrics, funnel views, inventory alerts, and metric documentation.", 13200),
            ("ops", "monitoring", "Create warehouse monitoring, cost controls, run status reports, incident playbooks, and owner-facing release notes.", 9200),
        ],
    },
    {
        "template_id": "rag_agent_knowledge_platform",
        "category": "ai_agent_app",
        "title": "Build an internal RAG and agent knowledge platform with ingestion, retrieval, evaluation, and admin surfaces.",
        "surfaces": ["crawler", "embedding", "reranker", "chat_ui", "eval_harness", "admin"],
        "turns": [
            ("ingestion", "sources", "Build document ingestion for PDFs, markdown docs, web pages, repo files, issue threads, source refs, and refresh ledgers.", 11800),
            ("retrieval", "index", "Implement chunking, embeddings, vector search, reranking, metadata filters, query rewrite, and source-backed citations.", 13600),
            ("agent", "planner", "Add an agent planner with tool routing, prompt session memory, context budget controls, and compact primitive cards.", 12600),
            ("frontend", "chat", "Build chat, search, review, source inspection, feedback, and admin moderation surfaces with accessible states.", 11600),
            ("evaluation", "benchmarks", "Create an eval harness with golden tasks, trace pairs, coverage gaps, precision checks, token accounting, and failure memory.", 12400),
            ("security", "policy", "Add privacy boundaries, tenant permissions, prompt injection checks, redaction, audit receipts, and source trust labels.", 10800),
            ("ops", "observability", "Add dashboards for latency, retrieval quality, hallucination reports, usage, costs, and incident runbooks.", 9400),
            ("packaging", "handoff", "Create deployment manifests, operator docs, SDK examples, and migration guides for existing teams.", 8600),
        ],
    },
    {
        "template_id": "compliance_case_management",
        "category": "regulated_workflow_app",
        "title": "Build KYC, AML, sanctions, and case-management operations software for a regulated team.",
        "surfaces": ["case_app", "screening_api", "workflow_engine", "warehouse", "reports", "audit"],
        "turns": [
            ("intake", "forms", "Build customer and business intake forms, evidence upload, identity normalization, beneficial owner capture, and consent receipts.", 10600),
            ("screening", "risk", "Implement sanctions screening, watchlist matching, entity resolution, adverse media triage, risk scoring, and manual review queues.", 14600),
            ("workflow", "cases", "Build case assignment, SLA timers, escalation rules, analyst notes, status transitions, and audit-safe comment histories.", 12200),
            ("integration", "apis", "Create provider adapters, webhook handlers, retry logic, API gateway routes, idempotency keys, and reconciliation jobs.", 11200),
            ("warehouse", "reporting", "Build compliance reporting marts, evidence lineage, examiner exports, SAR-like report drafts, and quality checks.", 13200),
            ("policy", "governance", "Add approval gates, role-based permissions, privacy boundaries, retention policies, and model-output disclaimers.", 9800),
            ("frontend", "review", "Build analyst review surfaces, match explanations, side-by-side evidence, batch actions, and accessibility states.", 11600),
            ("ops", "proof", "Add contract tests, synthetic fixtures, monitoring, incident playbooks, and reproducibility receipts.", 9200),
        ],
    },
    {
        "template_id": "ecommerce_marketplace_platform",
        "category": "massive_multi_surface_app",
        "title": "Build a marketplace platform with storefront, seller portal, admin tools, inventory, payments, and fulfillment.",
        "surfaces": ["storefront", "seller_portal", "admin", "payments", "inventory", "warehouse"],
        "turns": [
            ("catalog", "product", "Build product catalog, category taxonomy, search filters, media handling, pricing rules, and import/export tools.", 11800),
            ("accounts", "seller", "Implement seller onboarding, login sessions, verification, payout settings, RBAC authorization, and support workflows.", 10400),
            ("checkout", "payments", "Build cart, checkout, payment intents, webhook handlers, tax calculation, fraud checks, and refund flows.", 14600),
            ("inventory", "ops", "Add inventory reservations, warehouse locations, stock reconciliation, shipping label generation, and fulfillment state machines.", 13200),
            ("frontend", "surfaces", "Build storefront, seller portal, admin dashboard, order views, dispute pages, and mobile-responsive states.", 15000),
            ("data", "analytics", "Create order, seller, customer, inventory, and marketing marts with cohort and margin dashboards.", 12800),
            ("quality", "tests", "Add unit, contract, Playwright, payment fixture, privacy, and accessibility tests across all checkout paths.", 9800),
            ("ops", "deploy", "Deploy services, workers, queues, cache, observability dashboards, feature flags, and rollback runbooks.", 10800),
        ],
    },
    {
        "template_id": "healthcare_intake_and_claims",
        "category": "regulated_workflow_app",
        "title": "Build a healthcare intake, scheduling, referral, and claims analytics system.",
        "surfaces": ["patient_portal", "provider_admin", "claims_warehouse", "scheduler", "audit", "reports"],
        "turns": [
            ("intake", "forms", "Build patient intake forms, referral capture, document upload, consent receipts, eligibility fields, and validation.", 10600),
            ("auth", "privacy", "Implement login sessions, role boundaries, PHI redaction, audit logs, data retention, and access-review reports.", 11200),
            ("scheduler", "workflow", "Create appointment scheduling, referral queues, provider availability, reminders, no-show workflows, and escalation rules.", 12600),
            ("integration", "claims", "Add claims file ingestion, payer adapters, normalized schemas, denial categories, and reconciliation jobs.", 13200),
            ("warehouse", "analytics", "Build claims and operations marts, quality measures, cycle-time dashboards, and reproducibility metadata.", 14600),
            ("frontend", "surfaces", "Build patient portal, provider admin, case review, document viewer, task queues, and accessibility states.", 13400),
            ("quality", "tests", "Add synthetic data fixtures, privacy boundary checks, schema contract tests, e2e flows, and audit receipts.", 9800),
            ("ops", "deploy", "Deploy services with monitoring, incident playbooks, backup checks, data quality alerts, and operator docs.", 9400),
        ],
    },
    {
        "template_id": "platform_devops_migration",
        "category": "platform_migration",
        "title": "Migrate a monolith into a governed platform with services, infrastructure, CI, observability, and runbooks.",
        "surfaces": ["services", "kubernetes", "terraform", "ci_cd", "observability", "security"],
        "turns": [
            ("discovery", "inventory", "Inventory modules, APIs, database tables, background jobs, secrets, external dependencies, and migration risks.", 8800),
            ("architecture", "services", "Design service boundaries, API gateway routes, queue workers, cache layers, database ownership, and rollout phases.", 12200),
            ("infra", "terraform", "Create Terraform modules, Kubernetes jobs, Cloud Run services, secrets management, network policies, and environments.", 13600),
            ("delivery", "ci", "Build CI pipelines, contract tests, image builds, migration checks, deployment approvals, and rollback automation.", 11200),
            ("data", "migration", "Implement data migration scripts, backfills, dual-write checks, reconciliation dashboards, and cutover receipts.", 11800),
            ("observability", "sre", "Add log metric trace pipelines, service dashboards, SLO alerts, incident runbooks, and capacity reports.", 10600),
            ("security", "governance", "Add RBAC, key management, secret detection, compliance reports, audit trails, and policy gates.", 9800),
            ("handoff", "docs", "Write operator docs, service catalogs, onboarding guides, architecture diagrams, and post-migration review checks.", 7600),
        ],
    },
    {
        "template_id": "iot_monitoring_and_warehouse",
        "category": "data_warehouse_build",
        "title": "Build an IoT monitoring platform with streaming ingestion, device dashboards, anomaly detection, and warehouse marts.",
        "surfaces": ["streaming", "device_api", "warehouse", "dashboard", "alerts", "ml_eval"],
        "turns": [
            ("ingestion", "stream", "Build streaming ingestion for device telemetry, schema validation, deduplication, late data handling, and partitioning.", 12800),
            ("api", "devices", "Create device registration APIs, auth tokens, status endpoints, firmware metadata, and webhook handlers.", 10400),
            ("warehouse", "models", "Build time-series warehouse tables, rollups, device dimensions, anomaly features, and cost-aware retention.", 13600),
            ("ml", "anomaly", "Add anomaly scoring, threshold calibration, feedback capture, evaluation fixtures, and model monitoring.", 11800),
            ("frontend", "dashboards", "Build fleet dashboard, device detail pages, alert inbox, map views, and operator actions.", 13200),
            ("workflow", "alerts", "Implement escalation policies, incident states, notifications, suppressions, and audit-safe comments.", 9800),
            ("quality", "tests", "Add simulator fixtures, contract tests, load tests, data quality checks, and replayable benchmark traces.", 10200),
            ("ops", "deploy", "Ship infrastructure, stream monitoring, dashboards, on-call runbooks, and failure recovery plans.", 9400),
        ],
    },
    {
        "template_id": "production_ml_model_lifecycle",
        "category": "ml_lifecycle_system",
        "title": "Build, deploy, monitor, govern, and maintain a production ML model across the full technical team lifecycle.",
        "surfaces": [
            "product_requirements",
            "data_platform",
            "feature_store",
            "training_pipeline",
            "model_registry",
            "serving_api",
            "monitoring",
            "governance",
        ],
        "turns": [
            ("product", "requirements", "Create the ML product requirements document, business objective, success metrics, user stories, launch criteria, A/B test plan, rollout plan, feedback-loop requirements, and risk summary.", 9800),
            ("architecture", "system_design", "Design the end-to-end ML architecture across data sources, training, feature store, model registry, inference API, frontend integration, monitoring, rollback, and disaster recovery.", 13200),
            ("governance", "data_stewardship", "Create data inventory, approved source list, data classification, access policies, retention rules, lineage records, data contracts, consent checks, and auditability controls.", 11800),
            ("data_engineering", "pipelines", "Build ingestion, CDC, batch and streaming pipelines, raw and curated layers, schema validation, deduplication, late data handling, backfills, partitions, and data quality checks.", 14800),
            ("analytics", "metrics", "Build analytics marts, KPI definitions, semantic layer, model impact dashboards, A/B test reporting, cohort analysis, funnel analysis, dbt models, and SQL tests.", 12200),
            ("science", "experiments", "Convert the ML task into baselines, feature exploration, model training, cross-validation, leakage checks, error analysis, calibration, explainability, and model-card evidence.", 15600),
            ("labeling", "gold_set", "Create labeling guidelines, annotation workflow, gold-standard test set, active learning loop, adjudication process, label quality report, and human feedback records.", 9600),
            ("ml_engineering", "training", "Productionize notebooks into reproducible training code, feature pipelines, MLflow experiment tracking, model artifact packaging, registry versioning, retraining workflows, and model tests.", 16400),
            ("mlops", "platform", "Build reusable ML pipeline templates, CI/CD and CT, model registry infrastructure, feature store infrastructure, artifact storage, deployment templates, promotion gates, and platform docs.", 15200),
            ("backend", "serving_api", "Build prediction APIs with request and response schemas, real-time feature retrieval, business rules, auth, rate limiting, caching, retries, fallbacks, logging, tracing, and contract tests.", 14800),
            ("frontend", "human_ai_ui", "Build user-facing model output surfaces, confidence indicators, explanations, feedback capture, feature flag variants, frontend telemetry, fallback states, and accessibility checks.", 12600),
            ("infrastructure", "deploy", "Provision Docker, Kubernetes, Terraform, environments, secrets, IAM, GPU or CPU serving nodes, autoscaling, networking, CI/CD, backup, rollback, and cost controls.", 14200),
            ("sre", "observability", "Create SLIs, SLOs, dashboards, alerts, runbooks, on-call process, capacity plans, load tests, dependency health checks, model latency and error monitoring, and postmortem templates.", 12600),
            ("qa", "release_gates", "Create data, model, API, UI, performance, regression, load, canary, rollback, and monitoring tests with release validation reports and staging sign-off.", 11400),
            ("security", "devsecops", "Threat model the ML system, review IAM, API security, secrets, dependency scanning, container scanning, CI/CD permissions, model artifact security, prompt-injection risks, and audit logs.", 11800),
            ("privacy", "compliance", "Create privacy review, data protection impact assessment, legal approval, retention policy, vendor risk assessment, model risk documentation, user notices, and audit package.", 10800),
            ("responsible_ai", "risk", "Build fairness, bias, robustness, red-team, explainability, model card, risk register, human oversight, hallucination, toxicity, prompt injection, and data leakage evaluations.", 12600),
            ("support", "operations", "Create human review queues, escalation workflows, support issue summaries, false positive and false negative review loops, feedback labels, operational metrics, and retraining tickets.", 10200),
            ("documentation", "handoff", "Write API docs, runbooks, deployment guide, rollback guide, monitoring guide, model card, data card, release notes, limitations, intended use, and audit documentation.", 9200),
            ("program", "delivery", "Create RACI ownership, dependency tracker, milestone plan, risk register, production readiness review, launch checklist, stakeholder updates, and post-launch review process.", 8800),
        ],
    },
    {
        "template_id": "lean_ml_team_platform",
        "category": "ml_lifecycle_system",
        "title": "Build a lean startup ML platform where six people cover product, data, ML, full-stack, platform, QA, and support responsibilities.",
        "surfaces": ["lean_roles", "training", "warehouse", "api", "ui", "ops", "governance"],
        "turns": [
            ("product", "lean_roles", "Map founder, data/ML lead, data engineer, full-stack engineer, platform engineer, and QA/support hybrid responsibilities into clear ownership, launch gates, and escalation paths.", 8600),
            ("data", "warehouse", "Build the minimum reliable data warehouse with ingestion, dbt transformations, Great Expectations checks, reproducible training tables, and business impact marts.", 12400),
            ("ml", "training", "Build baseline model training, feature engineering, experiment tracking, model selection, error analysis, model card, and retraining trigger definitions.", 13600),
            ("platform", "mlops", "Create a lean MLOps stack with Docker, GitHub Actions, Terraform, MLflow registry, feature store definitions, deployment templates, and promotion gates.", 13200),
            ("application", "api_ui", "Build the prediction API, frontend model output experience, feedback capture, feature flags, fallback behavior, and human review queue.", 12600),
            ("reliability", "monitoring", "Add Prometheus, Grafana, OpenTelemetry, Evidently-style drift checks, business KPI dashboards, runbooks, SLOs, alerts, and incident response.", 11600),
            ("security", "governance", "Add IAM, secrets, data minimization, audit logs, privacy review, responsible AI checks, dependency scanning, and launch sign-off docs.", 10400),
            ("operations", "feedback", "Create support workflows, false positive and false negative review, labeling feedback, issue triage, retraining backlog, release notes, and post-launch review.", 9800),
        ],
    },
    {
        "template_id": "google_scale_operating_model",
        "category": "large_org_operating_model",
        "title": "Design a Google-scale technology organization with vertical product areas, horizontal platforms, control functions, go-to-market, and governance forums.",
        "surfaces": ["org_chart", "business_units", "platform_orgs", "trust", "gtm", "governance", "delivery"],
        "turns": [
            ("corporate", "executive_layer", "Create the corporate and executive operating layer with CEO, board, finance, legal, people, security, privacy, AI leadership, strategy, capital allocation, risk governance, and executive dashboards.", 11800),
            ("search", "search_knowledge", "Design the search, knowledge, and assistant product organization with crawling, indexing, ranking, query understanding, knowledge graph, search UX, ads integration, and trust and safety.", 16400),
            ("ads", "ads_commerce", "Design the ads and commerce business unit with auction systems, advertiser tools, measurement, attribution, ad quality, anti-fraud, publisher monetization, and privacy-safe ads.", 15600),
            ("media", "youtube_media", "Design the media platform organization with video ingestion, transcoding, storage, CDN delivery, recommendations, creator tools, ads, subscriptions, trust and safety, and live streaming.", 15800),
            ("cloud", "cloud_enterprise", "Design the cloud and enterprise business unit with compute, storage, databases, data analytics, AI platform, workspace, security products, customer engineering, support, and customer success.", 16800),
            ("platforms", "android_chrome_play", "Design the platform ecosystem organization for operating systems, browser engines, app marketplace, developer tools, ecosystem partnerships, and platform security.", 14200),
            ("hardware", "devices_silicon_supply_chain", "Design devices, data-center hardware, custom silicon, supply chain, hardware reliability, manufacturing engineering, firmware, accelerators, and field quality operations.", 14600),
            ("ai", "research_frontier_models", "Design the AI research and frontier-model organization with pretraining, post-training, multimodal models, applied AI, data and labeling, model evaluation, responsible AI, AI security, and AI infrastructure.", 17200),
            ("moonshots", "other_bets", "Design the moonshot and other-bets operating model with venture-style leadership, R&D teams, commercialization, regulatory teams, and shared corporate services.", 10400),
            ("infrastructure", "technical_infrastructure", "Design the technical infrastructure organization with data centers, fleet management, compute scheduling, storage, databases, network engineering, edge CDN, and capacity planning.", 17400),
            ("devinfra", "developer_productivity", "Design developer infrastructure with source control, code review, build systems, CI, release tooling, static analysis, large-scale changes, developer environments, and documentation systems.", 15200),
            ("sre", "production_reliability", "Design the SRE organization with product SRE, infrastructure SRE, incident management, global traffic, observability, disaster recovery, production readiness, SLOs, and error budgets.", 14600),
            ("data", "data_platform_analytics", "Design the data platform and analytics organization with ingestion, warehouse, lake, governance, metrics platform, experimentation, feature platform, BI, and reporting.", 14800),
            ("mlops", "ml_ai_platform", "Design the ML platform and MLOps organization with distributed training, accelerator scheduling, model registry, feature store, serving, evaluation, monitoring, governance, prompt and agent platforms, and vector search.", 16400),
            ("security", "security_privacy", "Design the security and privacy organization with corporate security, product security, infrastructure security, detection and response, red team, supply chain security, AI security, privacy engineering, data-use governance, and user controls.", 16800),
            ("trust", "trust_safety_integrity", "Design trust and safety with abuse detection, content moderation, ads policy, platform integrity, civic integrity, child safety, human review operations, appeals, and escalation workflows.", 14200),
            ("gtm", "go_to_market", "Design go-to-market with enterprise sales, customer engineering, customer success, marketing, partnerships, developer relations, support, CRM, forecasting, and partner portals.", 12800),
            ("legal", "legal_policy_compliance", "Design legal, regulatory, public policy, IP, litigation, compliance, audit, contract, e-discovery, GRC, and product counsel workflows.", 11800),
            ("finance", "finance_people_ops", "Design finance, procurement, business operations, real estate, investor relations, recruiting, HRBPs, compensation, learning, DEI, and employee relations.", 12600),
            ("governance", "review_boards", "Create repeatable executive operating reviews, product-area reviews, architecture boards, production readiness reviews, security reviews, privacy reviews, responsible AI reviews, launch reviews, incident reviews, and portfolio reviews.", 13800),
            ("workflow", "idea_to_global_production", "Map the work flow from strategy to discovery, product and technical design, build, test, launch readiness, progressive rollout, production operations, and continuous improvement.", 13200),
            ("engineering", "ladders", "Define engineering management and individual-contributor ladders, responsibilities from engineer to fellow, staff-level design ownership, directors, VPs, and cross-organization technical leadership.", 10200),
        ],
    },
    {
        "template_id": "hyperscale_platform_stack",
        "category": "large_org_operating_model",
        "title": "Build the full technology stack for a hyperscale organization from physical infrastructure through applications, developer workflow, observability, and governance.",
        "surfaces": ["physical_infra", "compute", "storage", "data", "ml", "apps", "dev_workflow", "ops"],
        "turns": [
            ("infrastructure", "physical", "Design data centers, power, cooling, racks, facility telemetry, custom servers, accelerators, fiber backbone, SDN, edge POPs, supply chain, and sustainability controls.", 14800),
            ("infrastructure", "compute", "Design cluster management, containers, batch jobs, serverless, autoscaling, quotas, priorities, reservations, workload isolation, and resource governance.", 14600),
            ("infrastructure", "storage_databases", "Design distributed file and object storage, globally distributed SQL, wide-column NoSQL, analytical warehouse, caches, search indexes, metadata stores, backup, and archive.", 15200),
            ("data", "events_analytics", "Design event collection, streaming, batch processing, data transformation, data quality, lineage, governance, experimentation, feature platform, and BI reporting.", 14600),
            ("mlops", "ai_infra", "Design ML development, distributed training, experiment tracking, feature stores, model registry, model serving, evaluation, monitoring, agent platforms, and vector search.", 15800),
            ("engineering", "application_engineering", "Design backend, frontend, mobile, APIs, auth, authorization, payments, localization, accessibility, product frameworks, and service integration patterns.", 13800),
            ("devinfra", "developer_workflow", "Design source control, code review, Bazel-like builds, unit integration E2E fuzz load golden tests, CI, CD, artifact signing, docs-as-code, and launch automation.", 14200),
            ("sre", "observability_operations", "Design metrics, logs, traces, SLO alerts, incident response, capacity planning, release safety, chaos testing, cost observability, and automated rollback.", 13600),
        ],
    },
    {
        "template_id": "kaggle_tabular_competition",
        "category": "kaggle_project",
        "title": "Take a Kaggle-style tabular competition from raw CSVs to a leaderboard submission with a reproducible pipeline.",
        "surfaces": ["notebook", "pandas", "feature_pipeline", "gbdt", "cv_harness", "submission"],
        "turns": [
            ("data", "eda", "Profile the train and test CSVs: dtypes, missingness, target distribution, leakage suspects, adversarial validation between train and test, and a data dictionary.", 8200),
            ("features", "engineering", "Build the feature pipeline: imputation, categorical encodings, target encoding with fold safety, aggregations, interactions, datetime decomposition, and frequency features.", 10800),
            ("modeling", "baselines", "Train baseline models: regularized linear, random forest, then tuned XGBoost and LightGBM with early stopping and a stratified cross-validation harness.", 11400),
            ("modeling", "tuning", "Run hyperparameter search over depth, learning rate, subsampling, and regularization; track every run with parameters, metrics, and fold scores.", 9600),
            ("ensembling", "blend", "Build out-of-fold stacking and weighted blending, calibrate probabilities, and verify the blend beats every single model on the CV harness.", 8800),
            ("quality", "leakage_checks", "Audit for leakage: fold contamination, target leakage in encodings, test-set fitting, and train/test distribution drift; document the reproducibility seed policy.", 7400),
            ("packaging", "submission", "Produce the inference script, submission file, environment lockfile, and a run report with CV-vs-leaderboard deltas.", 6800),
        ],
    },
    {
        "template_id": "kaggle_vision_competition",
        "category": "kaggle_project",
        "title": "Build a Kaggle-style computer-vision competition pipeline with augmentation, transfer learning, and TTA.",
        "surfaces": ["notebook", "pytorch", "augmentation", "cnn_transformer", "cv_harness", "submission"],
        "turns": [
            ("data", "loaders", "Build dataset loaders for the image corpus: decoding, resizing, normalization, class-balance analysis, corrupt-file handling, and a fold split that respects groups.", 8600),
            ("features", "augmentation", "Implement the augmentation stack: flips, crops, color jitter, cutmix/mixup, and test-time augmentation variants with deterministic seeds.", 9400),
            ("modeling", "transfer", "Fine-tune pretrained backbones (ResNet/EfficientNet/ViT): staged unfreezing, discriminative learning rates, mixed precision, and checkpointing.", 12200),
            ("modeling", "training_loop", "Build the training loop with early stopping, LR scheduling, gradient clipping, per-fold checkpoints, and run tracking of parameters and metrics.", 10400),
            ("ensembling", "tta_blend", "Combine fold checkpoints with test-time augmentation and weighted averaging; verify gains on the validation harness.", 8200),
            ("quality", "error_analysis", "Cluster misclassifications, inspect hard examples, check label noise, and produce a per-class performance report.", 7600),
            ("packaging", "submission", "Produce the inference notebook within compute limits, the submission file, and a reproducibility report.", 6600),
        ],
    },
    {
        "template_id": "kaggle_timeseries_nlp_competition",
        "category": "kaggle_project",
        "title": "Build a Kaggle-style forecasting or NLP competition pipeline with temporal validation or transformer fine-tuning.",
        "surfaces": ["notebook", "pandas", "temporal_cv", "transformers", "eval_harness", "submission"],
        "turns": [
            ("data", "temporal_eda", "Profile the series or corpus: trend, seasonality, gaps, hierarchy, or for NLP the length distribution, vocabulary, label balance, and duplicates.", 8400),
            ("features", "windows_or_tokens", "Build lag/rolling/holiday features with leak-safe windows, or the tokenization pipeline with truncation strategy and fold-safe text cleaning.", 10200),
            ("modeling", "primary", "Train the primary models: gradient boosting on windowed features or fine-tuned transformer with scheduled LR, early stopping, and fold checkpoints.", 12000),
            ("modeling", "validation", "Build the temporal or grouped cross-validation harness that mirrors the leaderboard split; verify no future leakage crosses fold boundaries.", 9200),
            ("ensembling", "hierarchy_blend", "Reconcile hierarchical forecasts or blend seeds/checkpoints; compare against naive and seasonal baselines honestly.", 8400),
            ("quality", "drift_checks", "Stress-test on the last known period, check residual autocorrelation or per-slice NLP performance, and document failure segments.", 7200),
            ("packaging", "submission", "Produce the inference script, submission file, and a run report with validation-vs-leaderboard deltas and seeds.", 6400),
        ],
    },
)

STACK_VARIANTS = (
    "React, FastAPI, Postgres, Redis, queue workers, Terraform",
    "Next.js, Python services, BigQuery, dbt, Dagster, Cloud Run",
    "Flutter web, Go APIs, Postgres, Kafka, Kubernetes, OpenTelemetry",
    "React Native, serverless functions, object storage, warehouse marts, Grafana",
    "Python, scikit-learn, MLflow, Feast, Airflow, Kubernetes, Prometheus, Grafana",
    "PyTorch, Hugging Face, dbt, Great Expectations, KServe, Terraform, OpenTelemetry",
)
SCALE_VARIANTS = (
    ("department", 0.78),
    ("growth", 1.0),
    ("enterprise", 1.35),
    ("regulated enterprise", 1.55),
)
#: CODE-STATE axis (owner-directed 2026-07-07): projects are NOT all ground-up — sessions cycle the starting
#: code state. (label, prompt context injected into every turn, output-token multiplier: brownfield turns
#: write less new code but must respect what exists.)
CODE_STATE_VARIANTS: tuple[tuple[str, str, float], ...] = (
    ("greenfield", "Starting from an empty repo.", 1.0),
    ("partial_scaffold", "The repo already has scaffolding: models, route stubs, and CI exist; extend "
                         "without duplicating what exists.", 0.86),
    ("mid_build", "About half the features are implemented and tests pass; continue from the existing "
                  "code state and keep its conventions.", 0.74),
    ("legacy_refactor", "A working legacy implementation exists; modernize incrementally, preserving "
                        "behavior and adding tests first.", 0.92),
    ("brownfield_integration", "Integrate the new capability into an existing production codebase with "
                               "established conventions, migrations, and review gates.", 0.81),
)


def _utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, n: int = 12) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:n]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def _slug(text: str) -> str:
    chars: list[str] = []
    previous_dash = False
    for char in str(text).lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "".join(chars).strip("-")[:64] or "item"


def _pascal(text: str) -> str:
    return "".join(part.capitalize() for part in _slug(text).split("-") if part)


def _ml_lifecycle_templates() -> list[dict[str, Any]]:
    return [template for template in SCENARIO_TEMPLATES if template["category"] == "ml_lifecycle_system"]


def _ml_lifecycle_card(
    *,
    template_id: str,
    stage: str,
    surface: str,
    prompt: str,
    base_output_tokens: int,
    action: str,
    action_terms: str,
) -> dict[str, Any]:
    role = ML_LIFECYCLE_ROLE_BY_STAGE.get(stage, stage)
    slug = _slug(f"{template_id}-{stage}-{surface}-{action}")
    input_edge = f"ProductionML{_pascal(stage)}{_pascal(surface)}Intent+{_pascal(role)}Context"
    output_edge = f"ProductionML{_pascal(stage)}{_pascal(surface)}{_pascal(action)}Artifacts+Receipt"
    compact_title = f"Production ML {stage} {surface} {action} primitive group"
    blackbox = (
        f"{role} reusable lifecycle primitive for {stage}/{surface}. "
        f"{prompt} Action lens: {action_terms}. "
        "Produces implementation-ready artifacts, ownership boundaries, acceptance checks, "
        "risk gates, monitoring hooks, and candidate receipts for production ML systems."
    )
    mutators = ["role_owner_bind", "artifact_template_fill", "risk_gate_attach", "receipt_emit"]
    hidden_member_edges = [
        f"{surface}_{action}_requirements",
        f"{surface}_{action}_artifact",
        f"{surface}_{action}_validation",
        f"{surface}_{action}_handoff",
    ]
    saved_tokens = max(1800, int(base_output_tokens * 0.62))
    return {
        "record_type": "linkable_primitive_card",
        "primitive_id": f"grp:ml-lifecycle.{slug}",
        "card_id": f"lpc:ml-lifecycle:{_sha({'slug': slug, 'action': action}, n=16)}",
        "title": compact_title,
        "blackbox": blackbox,
        "kind": "primitive_group",
        "source_family": "ml_lifecycle_specialized_pack",
        "source_refs": [ML_LIFECYCLE_SOURCE_REF],
        "source_verification_id": f"candidate:{_sha({'template_id': template_id, 'stage': stage, 'surface': surface, 'action': action}, n=16)}",
        "source_verified_at": ML_LIFECYCLE_PACKAGED_AT,
        "run_date": "2026-07-07",
        "packaged_at": ML_LIFECYCLE_PACKAGED_AT,
        "domains": ["ml_lifecycle", "mlops", role, stage, surface],
        "mutators": mutators,
        "blocking_keys": [
            "production ml",
            "model lifecycle",
            role,
            stage,
            surface,
            action,
            *action_terms.split(),
        ],
        "visible_edge": {
            "input": input_edge,
            "output": output_edge,
            "signature": f"{input_edge} -> {output_edge}",
            "description": f"{role} {stage} {surface} {action} lifecycle artifacts and receipt",
        },
        "composition_hints": {
            "candidate_only": True,
            "serves_truth": False,
            "consumes_edge": input_edge,
            "produces_edge": output_edge,
            "route_signature": f"{input_edge} -> {output_edge}",
            "adapter_mutators": mutators,
            "group_expansion_policy": "show_visible_edge_first_expand_hidden_edges_only_for_debug",
            "proofs_to_run_before_linking": [
                "candidate_boundary_gate",
                "artifact_schema_check",
                "role_owner_mapping_check",
                "release_or_governance_gate_check",
            ],
        },
        "edge_contract": {
            "candidate": True,
            "serves_truth": False,
            "input_edge": input_edge,
            "output_edge": output_edge,
            "input_contract": {
                "TaskBrief": "production ML lifecycle request, role context, and system constraints",
                "RoleContext": role,
                "Stage": stage,
                "Surface": surface,
            },
            "output_contract": {
                "Artifacts": f"{stage}/{surface} {action} deliverables",
                "Receipt": "candidate-only trace with assumptions, owners, and validation gates",
            },
            "preconditions": ["input matches input_contract", "candidate boundary remains visible"],
            "postconditions": ["output matches output_contract", "receipt records validation gates"],
        },
        "group_contract": {
            "visible_input": input_edge,
            "visible_output": output_edge,
            "hidden_member_edges": hidden_member_edges,
            "summary": f"Reusable {role} {action} primitive group for production ML lifecycle work.",
        },
        "hidden_member_edges": hidden_member_edges,
        "leverage_profile": {
            "candidate": True,
            "serves_truth": False,
            "reuse_class": "ml_lifecycle_multistep_group",
            "leverage_tier": "high",
            "estimated_saved_output_tokens": saved_tokens,
            "estimated_retrieval_context_tokens": 420,
            "hidden_member_edge_count": len(hidden_member_edges),
            "mutator_count": len(mutators),
            "proof_requirement_count": 4,
            "coding_surface_terms": [stage, surface, role, action, "mlops", "production"],
            "score": 1000,
        },
        "token_saving_usage": {
            "candidate_only": True,
            "serves_truth": False,
            "retrieval_unit": "card_id_plus_visible_edge_plus_compact_role_contract",
            "context_policy": "include hidden member edges only for lifecycle route validation",
            "leverage_tier": "high",
            "reuse_class": "ml_lifecycle_multistep_group",
            "estimated_saved_output_tokens": saved_tokens,
            "builder_instruction": "Link this lifecycle primitive before asking an LLM to recreate role-specific production ML deliverables.",
        },
        "candidate": True,
        "serves_truth": False,
    }


def _build_ml_lifecycle_specialized_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for template in _ml_lifecycle_templates():
        for stage, surface, prompt, base_output_tokens in template["turns"]:
            for action, action_terms in ML_LIFECYCLE_CARD_ACTIONS:
                cards.append(
                    _ml_lifecycle_card(
                        template_id=template["template_id"],
                        stage=stage,
                        surface=surface,
                        prompt=prompt,
                        base_output_tokens=int(base_output_tokens),
                        action=action,
                        action_terms=action_terms,
                    )
                )
    for role in ML_ROLE_DETAIL_ROWS:
        for plane, plane_terms in ML_ROLE_DETAIL_PLANES:
            role_terms = str(role.get(plane) or role.get("actions") or "")
            role_prompt = (
                f"{role['title']} production ML role plane. "
                f"Actions: {role['actions']}. Deliverables: {role['deliverables']}. "
                f"Tools: {role['tools']}. Concepts: {role['concepts']}."
            )
            cards.append(
                _ml_lifecycle_card(
                    template_id="production_ml_role_plane",
                    stage=str(role["stage"]),
                    surface=str(role["role_id"]),
                    prompt=role_prompt,
                    base_output_tokens=10_800,
                    action=plane,
                    action_terms=f"{plane_terms} {role_terms}",
                )
            )
    return cards


def _org_scale_templates() -> list[dict[str, Any]]:
    return [template for template in SCENARIO_TEMPLATES if template["category"] == "large_org_operating_model"]


def _org_scale_card(
    *,
    template_id: str,
    stage: str,
    surface: str,
    prompt: str,
    base_output_tokens: int,
    action: str,
    action_terms: str,
) -> dict[str, Any]:
    owner = ORG_SCALE_STAGE_OWNER.get(stage, f"{stage}_owner")
    slug = _slug(f"{template_id}-{stage}-{surface}-{action}")
    input_edge = f"HyperscaleOrg{_pascal(stage)}{_pascal(surface)}Intent+{_pascal(owner)}Context"
    output_edge = f"HyperscaleOrg{_pascal(stage)}{_pascal(surface)}{_pascal(action)}Artifacts+Receipt"
    title = f"Hyperscale org {stage} {surface} {action} primitive group"
    blackbox = (
        f"{owner} reusable large-organization primitive for {stage}/{surface}. "
        f"{prompt} Action lens: {action_terms}. "
        "Produces org structure, responsibility maps, technology stack slices, review forums, operating cadence, "
        "ownership boundaries, escalation paths, and candidate receipts for hyperscale technology organizations."
    )
    mutators = ["org_owner_bind", "platform_boundary_map", "governance_gate_attach", "receipt_emit"]
    hidden_member_edges = [
        f"{surface}_{action}_org_map",
        f"{surface}_{action}_responsibility_matrix",
        f"{surface}_{action}_technology_stack",
        f"{surface}_{action}_governance_gate",
    ]
    saved_tokens = max(2400, int(base_output_tokens * 0.66))
    return {
        "record_type": "linkable_primitive_card",
        "primitive_id": f"grp:large-org.{slug}",
        "card_id": f"lpc:large-org:{_sha({'slug': slug, 'action': action}, n=16)}",
        "title": title,
        "blackbox": blackbox,
        "kind": "primitive_group",
        "source_family": "large_org_specialized_pack",
        "source_refs": [ORG_SCALE_SOURCE_REF],
        "source_verification_id": f"candidate:{_sha({'template_id': template_id, 'stage': stage, 'surface': surface, 'action': action}, n=16)}",
        "source_verified_at": ORG_SCALE_PACKAGED_AT,
        "run_date": "2026-07-07",
        "packaged_at": ORG_SCALE_PACKAGED_AT,
        "domains": ["large_org", "hyperscale", owner, stage, surface],
        "mutators": mutators,
        "blocking_keys": [
            "large organization",
            "google scale",
            "hyperscale",
            owner,
            stage,
            surface,
            action,
            *action_terms.split(),
        ],
        "visible_edge": {
            "input": input_edge,
            "output": output_edge,
            "signature": f"{input_edge} -> {output_edge}",
            "description": f"{owner} {stage} {surface} {action} organization artifacts and receipt",
        },
        "composition_hints": {
            "candidate_only": True,
            "serves_truth": False,
            "consumes_edge": input_edge,
            "produces_edge": output_edge,
            "route_signature": f"{input_edge} -> {output_edge}",
            "adapter_mutators": mutators,
            "group_expansion_policy": "show_visible_edge_first_expand_hidden_edges_only_for_debug",
            "proofs_to_run_before_linking": [
                "candidate_boundary_gate",
                "org_boundary_consistency_check",
                "technology_stack_mapping_check",
                "governance_forum_coverage_check",
            ],
        },
        "edge_contract": {
            "candidate": True,
            "serves_truth": False,
            "input_edge": input_edge,
            "output_edge": output_edge,
            "input_contract": {
                "OrgBrief": "hyperscale organization request, business-unit context, platform constraints, and governance needs",
                "OwnerContext": owner,
                "Stage": stage,
                "Surface": surface,
            },
            "output_contract": {
                "Artifacts": f"{stage}/{surface} {action} organization deliverables",
                "Receipt": "candidate-only trace with assumptions, owners, governance gates, and technology mappings",
            },
            "preconditions": ["input matches input_contract", "candidate boundary remains visible"],
            "postconditions": ["output matches output_contract", "receipt records org and governance gates"],
        },
        "group_contract": {
            "visible_input": input_edge,
            "visible_output": output_edge,
            "hidden_member_edges": hidden_member_edges,
            "summary": f"Reusable {owner} {action} primitive group for hyperscale organization design.",
        },
        "hidden_member_edges": hidden_member_edges,
        "leverage_profile": {
            "candidate": True,
            "serves_truth": False,
            "reuse_class": "large_org_multistep_group",
            "leverage_tier": "high",
            "estimated_saved_output_tokens": saved_tokens,
            "estimated_retrieval_context_tokens": 460,
            "hidden_member_edge_count": len(hidden_member_edges),
            "mutator_count": len(mutators),
            "proof_requirement_count": 4,
            "coding_surface_terms": [stage, surface, owner, action, "hyperscale", "organization"],
            "score": 1000,
        },
        "token_saving_usage": {
            "candidate_only": True,
            "serves_truth": False,
            "retrieval_unit": "card_id_plus_visible_edge_plus_compact_org_contract",
            "context_policy": "include hidden member edges only for org route validation",
            "leverage_tier": "high",
            "reuse_class": "large_org_multistep_group",
            "estimated_saved_output_tokens": saved_tokens,
            "builder_instruction": "Link this large-org primitive before asking an LLM to recreate hyperscale team structures, responsibilities, technologies, and governance.",
        },
        "candidate": True,
        "serves_truth": False,
    }


def _build_org_scale_specialized_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for template in _org_scale_templates():
        for stage, surface, prompt, base_output_tokens in template["turns"]:
            for action, action_terms in ORG_SCALE_CARD_ACTIONS:
                cards.append(
                    _org_scale_card(
                        template_id=template["template_id"],
                        stage=stage,
                        surface=surface,
                        prompt=prompt,
                        base_output_tokens=int(base_output_tokens),
                        action=action,
                        action_terms=action_terms,
                    )
                )
    return cards


def _ensure_ml_lifecycle_pack() -> list[dict[str, Any]]:
    cards = _build_ml_lifecycle_specialized_cards()
    _write_jsonl(ML_LIFECYCLE_PACK_PATH, cards)
    _write_json(
        ML_LIFECYCLE_MANIFEST_PATH,
        {
            "record_type": "ml_lifecycle_specialized_pack_manifest",
            "generated_at": now_iso(),
            "cards_path": _rel(ML_LIFECYCLE_PACK_PATH),
            "card_count": len(cards),
            "source_ref": ML_LIFECYCLE_SOURCE_REF,
            "candidate": True,
            "serves_truth": False,
        },
    )
    return cards


def _ensure_org_scale_pack() -> list[dict[str, Any]]:
    cards = _build_org_scale_specialized_cards()
    _write_jsonl(ORG_SCALE_PACK_PATH, cards)
    _write_json(
        ORG_SCALE_MANIFEST_PATH,
        {
            "record_type": "large_org_specialized_pack_manifest",
            "generated_at": now_iso(),
            "cards_path": _rel(ORG_SCALE_PACK_PATH),
            "card_count": len(cards),
            "source_ref": ORG_SCALE_SOURCE_REF,
            "candidate": True,
            "serves_truth": False,
        },
    )
    return cards


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _rel(path: Path) -> str:
    root = _repo_root()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _tokens(text: Any) -> int:
    return max(1, len(str(text)) // CHARS_PER_TOKEN)


def _primitive_id(card: dict[str, Any]) -> str:
    return str(card.get("primitive_id") or card.get("card_id") or "").strip()


def _input_edge(card: dict[str, Any]) -> str:
    visible = card.get("visible_edge") if isinstance(card.get("visible_edge"), dict) else {}
    hints = card.get("composition_hints") if isinstance(card.get("composition_hints"), dict) else {}
    return str(card.get("input_edge") or visible.get("input") or hints.get("consumes_edge") or "").strip()


def _output_edge(card: dict[str, Any]) -> str:
    visible = card.get("visible_edge") if isinstance(card.get("visible_edge"), dict) else {}
    hints = card.get("composition_hints") if isinstance(card.get("composition_hints"), dict) else {}
    return str(card.get("output_edge") or visible.get("output") or hints.get("produces_edge") or "").strip()


def _normalize_card(card: dict[str, Any], *, source_label: str) -> dict[str, Any] | None:
    pid = _primitive_id(card)
    if not pid:
        return None
    hints = card.get("composition_hints") if isinstance(card.get("composition_hints"), dict) else {}
    leverage = card.get("leverage_profile") if isinstance(card.get("leverage_profile"), dict) else {}
    title = str(card.get("title") or hints.get("route_signature") or pid)
    normalized = dict(card)
    normalized.update({
        "primitive_id": pid,
        "title": title,
        "input_edge": _input_edge(card),
        "output_edge": _output_edge(card),
        "kind": card.get("kind") or "primitive",
        "source_family": card.get("source_family") or leverage.get("reuse_class") or "unknown",
        "domains": card.get("domains") or [str(leverage.get("reuse_class") or source_label)],
        "candidate": True,
        "serves_truth": False,
        "_benchmark_source": source_label,
    })
    return normalized


def _edge_text(card: dict[str, Any]) -> str:
    return json.dumps(
        {
            "primitive_id": card.get("primitive_id"),
            "title": card.get("title"),
            "input_edge": card.get("input_edge"),
            "output_edge": card.get("output_edge"),
            "kind": card.get("kind"),
            "source_family": card.get("source_family"),
        },
        sort_keys=True,
    )


def _load_base_cards(limit: int = 0) -> list[dict[str, Any]]:
    for rel in BASE_CARD_SOURCES:
        path = _resource(rel)
        if path.exists():
            rows = read_jsonl_tolerant(path)
            cards: list[dict[str, Any]] = []
            for row in rows:
                card = _normalize_card(row, source_label="base_registry")
                if card:
                    cards.append(card)
                if limit and len(cards) >= limit:
                    break
            return cards
    return []


def _supervised_cycle_manifests(max_cycles: int) -> list[dict[str, Any]]:
    paths = sorted(
        SUPERVISED_CYCLE_ROOT.glob("*/cycle_manifest.json"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    manifests: list[dict[str, Any]] = []
    for path in paths[:max(0, max_cycles)]:
        manifest = _read_json(path)
        if manifest.get("record_type") == "twenty_million_supervised_cycle_manifest":
            manifests.append(manifest)
    return manifests


def _load_supervised_cards(limit: int = 0, max_cycles: int = 5) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for manifest in _supervised_cycle_manifests(max_cycles):
        for package in manifest.get("package_manifests") or []:
            cards_path = package.get("cards_path") if isinstance(package, dict) else None
            if not isinstance(cards_path, str):
                continue
            path = _repo_root() / cards_path
            if not path.exists():
                path = _resource(cards_path)
            for row in read_jsonl_tolerant(path):
                card = _normalize_card(row, source_label="twenty_million_supervised")
                if card:
                    cards.append(card)
                if limit and len(cards) >= limit:
                    return cards
    return cards


def _load_ml_lifecycle_specialized_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in _ensure_ml_lifecycle_pack():
        card = _normalize_card(row, source_label="ml_lifecycle_specialized")
        if card:
            cards.append(card)
    return cards


def _load_org_scale_specialized_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in _ensure_org_scale_pack():
        card = _normalize_card(row, source_label="large_org_specialized")
        if card:
            cards.append(card)
    return cards


def load_cards(*, base_limit: int, supervised_limit: int, max_cycles: int, include_supervised: bool) -> dict[str, list[dict[str, Any]]]:
    base = _load_base_cards(base_limit)
    if not include_supervised:
        return {"base": base, "expanded": base}
    supervised = _load_supervised_cards(supervised_limit, max_cycles=max_cycles)
    lifecycle = _load_ml_lifecycle_specialized_cards()
    large_org = _load_org_scale_specialized_cards()
    by_id: dict[str, dict[str, Any]] = {}
    for card in [*base, *supervised, *lifecycle, *large_org]:
        by_id[_primitive_id(card)] = card
    return {"base": base, "expanded": list(by_id.values())}


def _template_filter(mode: str) -> list[dict[str, Any]]:
    if mode == "mixed":
        return list(SCENARIO_TEMPLATES)
    if mode == "warehouse":
        return [s for s in SCENARIO_TEMPLATES if s["category"] == "data_warehouse_build"]
    if mode == "app":
        return [s for s in SCENARIO_TEMPLATES if "app" in s["category"] or s["category"] == "ai_agent_app"]
    if mode == "regulated":
        return [s for s in SCENARIO_TEMPLATES if s["category"] == "regulated_workflow_app"]
    if mode == "platform":
        return [s for s in SCENARIO_TEMPLATES if s["category"] == "platform_migration"]
    if mode == "ml_lifecycle":
        return [s for s in SCENARIO_TEMPLATES if s["category"] == "ml_lifecycle_system"]
    if mode == "large_org":
        return [s for s in SCENARIO_TEMPLATES if s["category"] == "large_org_operating_model"]
    if mode == "kaggle":
        return [s for s in SCENARIO_TEMPLATES if s["category"] == "kaggle_project"]
    return list(SCENARIO_TEMPLATES)


def build_sessions(*, session_count: int, turns_per_session: int, seed: int, scenario_mode: str) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    templates = _template_filter(scenario_mode)
    if not templates:
        templates = list(SCENARIO_TEMPLATES)
    sessions: list[dict[str, Any]] = []
    for index in range(session_count):
        template = templates[index % len(templates)]
        stack = STACK_VARIANTS[(index + seed) % len(STACK_VARIANTS)]
        scale_label, scale_multiplier = SCALE_VARIANTS[(index + seed // 3) % len(SCALE_VARIANTS)]
        code_state, code_context, code_multiplier = CODE_STATE_VARIANTS[(index + seed // 5) % len(CODE_STATE_VARIANTS)]
        variant = f"{scale_label} scale using {stack}; {code_state.replace('_', ' ')} code state"
        turns = []
        selected_turns = template["turns"][:turns_per_session or None]
        for turn_index, (stage, surface, prompt, base_output_tokens) in enumerate(selected_turns, start=1):
            jitter = 1.0 + rng.uniform(-0.06, 0.08)
            turns.append({
                "turn_index": turn_index,
                "stage": stage,
                "surface": surface,
                "prompt": (
                    f"{template['title']} Context: {variant}. {code_context} "
                    f"Prompt {turn_index}: {prompt}"
                ),
                "base_output_tokens": int(base_output_tokens * scale_multiplier * code_multiplier * jitter),
            })
        sessions.append({
            "session_id": f"sess:{template['template_id']}:{index:04d}:{_sha({'seed': seed, 'index': index}, n=8)}",
            "template_id": template["template_id"],
            "category": template["category"],
            "title": template["title"],
            "variant": variant,
            "code_state": code_state,
            "surfaces": template["surfaces"],
            "turns": turns,
            "candidate": True,
            "serves_truth": False,
        })
    return sessions


def _select_matches(results: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], components_per_turn: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in results:
        if float(row.get("score") or 0) < SCORE_FLOOR:
            continue
        pid = str(row.get("primitive_id") or "")
        if not pid or pid in seen:
            continue
        card = by_id.get(pid)
        if card:
            matches.append(card)
            seen.add(pid)
        if len(matches) >= components_per_turn:
            break
    return matches


def _covered_fraction(matches: list[dict[str, Any]]) -> float:
    if not matches:
        return 0.0
    high = sum(1 for card in matches if str(card.get("leverage_tier") or "").lower() == "high")
    group = sum(1 for card in matches if str(card.get("kind") or "") == "primitive_group")
    return min(0.86, 0.32 + len(matches) * 0.105 + high * 0.035 + group * 0.025)


def run_sessions(
    cards: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
    *,
    corpus_label: str,
    k: int,
    components_per_turn: int,
    context_window: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not cards:
        return [], [], {
            "record_type": "realistic_session_benchmark_summary",
            "corpus_label": corpus_label,
            "sessions": 0,
            "turns": 0,
            "net_positive": False,
            "candidate": True,
            "serves_truth": False,
        }
    index = build_index(cards)
    by_id = {card["primitive_id"]: card for card in cards if card.get("primitive_id")}
    turn_rows: list[dict[str, Any]] = []
    session_rows: list[dict[str, Any]] = []

    for session in sessions:
        baseline_context = 0
        primitive_context = 0
        used_primitives: set[str] = set()
        repeated_reuses = 0
        session_totals = Counter()
        surface_counts: Counter[str] = Counter()
        stage_counts: Counter[str] = Counter()
        for turn in session["turns"]:
            query = turn["prompt"]
            results, stats = search_with_stats(query, k, index)
            matches = _select_matches(results, by_id, components_per_turn)
            match_ids = [_primitive_id(card) for card in matches]
            reused_this_turn = sum(1 for pid in match_ids if pid in used_primitives)
            repeated_reuses += reused_this_turn
            for pid in match_ids:
                used_primitives.add(pid)
            top_score = float(results[0].get("score") or 0) if results else 0.0
            covered_fraction = _covered_fraction(matches)
            coverage = bool(matches)
            prompt_tokens = _tokens(query)
            scan_tokens = 0
            for row in results[:k]:
                pid = str(row.get("primitive_id") or "")
                if pid in used_primitives:
                    scan_tokens += 8
                else:
                    scan_tokens += _tokens(_edge_text(by_id.get(pid) or row))
            baseline_input = min(context_window, prompt_tokens + baseline_context)
            baseline_output = int(turn["base_output_tokens"])
            baseline_total = baseline_input + baseline_output

            if coverage:
                primitive_input = min(context_window, prompt_tokens + primitive_context + scan_tokens)
                primitive_output = max(220, int(baseline_output * (1.0 - covered_fraction)) + 140 * len(matches))
                primitive_total = primitive_input + primitive_output
                baseline_context = min(context_window, baseline_context + int(baseline_output * 0.18) + prompt_tokens // 3)
                primitive_context = min(context_window, primitive_context + 48 * len(matches) + 72)
            else:
                primitive_input = min(context_window, baseline_input + scan_tokens)
                primitive_output = baseline_output
                primitive_total = primitive_input + primitive_output
                baseline_context = min(context_window, baseline_context + int(baseline_output * 0.18) + prompt_tokens // 3)
                primitive_context = min(context_window, primitive_context + int(primitive_output * 0.16) + prompt_tokens // 4)

            net_saved = baseline_total - primitive_total
            row = {
                "record_type": "realistic_session_turn_benchmark",
                "corpus_label": corpus_label,
                "session_id": session["session_id"],
                "template_id": session["template_id"],
                "category": session["category"],
                "variant": session["variant"],
                "turn_index": turn["turn_index"],
                "stage": turn["stage"],
                "surface": turn["surface"],
                "prompt_tokens": prompt_tokens,
                "baseline_input_tokens": baseline_input,
                "baseline_output_tokens": baseline_output,
                "baseline_total_tokens": baseline_total,
                "primitive_input_tokens": primitive_input,
                "primitive_output_tokens": primitive_output,
                "primitive_total_tokens": primitive_total,
                "net_saved_tokens": net_saved,
                "reduction_ratio": round(baseline_total / primitive_total, 3) if primitive_total else None,
                "coverage": coverage,
                "covered_fraction_estimate": round(covered_fraction, 3),
                "top_score": round(top_score, 4),
                "match_count": len(matches),
                "reused_match_count": reused_this_turn,
                "matched_primitive_ids": match_ids,
                "candidates_scored": stats.get("candidates_scored") or stats.get("candidate_count"),
                "tokens_basis": TOKENS_BASIS,
                "candidate": True,
                "serves_truth": False,
            }
            turn_rows.append(row)
            surface_counts[turn["surface"]] += 1
            stage_counts[turn["stage"]] += 1
            for key in ("baseline_total_tokens", "primitive_total_tokens", "net_saved_tokens", "match_count"):
                session_totals[key] += int(row[key])
            session_totals["covered_turns"] += int(coverage)
            session_totals["turns"] += 1

        turns = int(session_totals["turns"])
        baseline = int(session_totals["baseline_total_tokens"])
        primitive = int(session_totals["primitive_total_tokens"])
        session_rows.append({
            "record_type": "realistic_session_benchmark_session_summary",
            "corpus_label": corpus_label,
            "session_id": session["session_id"],
            "template_id": session["template_id"],
            "category": session["category"],
            "variant": session["variant"],
            "surfaces": session["surfaces"],
            "turns": turns,
            "covered_turns": int(session_totals["covered_turns"]),
            "coverage_rate": round(session_totals["covered_turns"] / turns, 3) if turns else 0,
            "baseline_total_tokens": baseline,
            "primitive_total_tokens": primitive,
            "net_saved_tokens": baseline - primitive,
            "reduction_ratio": round(baseline / primitive, 3) if primitive else None,
            "unique_primitives_used": len(used_primitives),
            "repeated_reuses": repeated_reuses,
            "surface_counts": dict(surface_counts),
            "stage_counts": dict(stage_counts),
            "tokens_basis": TOKENS_BASIS,
            "candidate": True,
            "serves_truth": False,
        })

    summary = aggregate(turn_rows, session_rows, corpus_label=corpus_label, card_count=len(cards))
    return turn_rows, session_rows, summary


def aggregate(turn_rows: list[dict[str, Any]], session_rows: list[dict[str, Any]], *, corpus_label: str, card_count: int) -> dict[str, Any]:
    turns = len(turn_rows)
    sessions = len(session_rows)
    if not turns:
        return {
            "record_type": "realistic_session_benchmark_summary",
            "corpus_label": corpus_label,
            "card_count": card_count,
            "sessions": sessions,
            "turns": 0,
            "net_positive": False,
            "candidate": True,
            "serves_truth": False,
        }
    total_baseline = sum(int(row["baseline_total_tokens"]) for row in turn_rows)
    total_primitive = sum(int(row["primitive_total_tokens"]) for row in turn_rows)
    total_saved = total_baseline - total_primitive
    coverage_rate = sum(1 for row in turn_rows if row["coverage"]) / turns
    positive_sessions = sum(1 for row in session_rows if int(row["net_saved_tokens"]) > 0)
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in turn_rows:
        by_stage[str(row["stage"])].append(row)
        by_surface[str(row["surface"])].append(row)

    def rollup(rows: list[dict[str, Any]], key_name: str, name: str) -> dict[str, Any]:
        count = len(rows)
        saved = sum(int(row["net_saved_tokens"]) for row in rows)
        return {
            key_name: name,
            "turns": count,
            "coverage_rate": round(sum(1 for row in rows if row["coverage"]) / count, 3) if count else 0,
            "avg_net_saved_tokens": round(saved / count, 1) if count else 0,
            "gap_count": sum(1 for row in rows if not row["coverage"]),
        }

    stage_rollups = sorted((rollup(rows, "stage", stage) for stage, rows in by_stage.items()), key=lambda row: row["avg_net_saved_tokens"])
    surface_rollups = sorted((rollup(rows, "surface", surface) for surface, rows in by_surface.items()), key=lambda row: row["avg_net_saved_tokens"])
    gap_turns = [
        {
            "session_id": row["session_id"],
            "template_id": row["template_id"],
            "stage": row["stage"],
            "surface": row["surface"],
            "top_score": row["top_score"],
            "baseline_output_tokens": row["baseline_output_tokens"],
        }
        for row in turn_rows
        if not row["coverage"]
    ][:50]
    return {
        "record_type": "realistic_session_benchmark_summary",
        "generated_at": now_iso(),
        "corpus_label": corpus_label,
        "card_count": card_count,
        "sessions": sessions,
        "turns": turns,
        "coverage_rate": round(coverage_rate, 3),
        "positive_session_rate": round(positive_sessions / sessions, 3) if sessions else 0,
        "baseline_total_tokens": total_baseline,
        "primitive_total_tokens": total_primitive,
        "total_net_saved_tokens": total_saved,
        "avg_net_saved_tokens_per_turn": round(total_saved / turns, 1),
        "avg_net_saved_tokens_per_session": round(total_saved / sessions, 1) if sessions else 0,
        "reduction_ratio": round(total_baseline / total_primitive, 3) if total_primitive else None,
        "net_positive": total_saved > 0,
        "unique_primitives_used": len({pid for row in turn_rows for pid in row.get("matched_primitive_ids", [])}),
        "repeated_reuses": sum(int(row.get("reused_match_count") or 0) for row in turn_rows),
        "stage_rollups_worst_first": stage_rollups,
        "surface_rollups_worst_first": surface_rollups,
        "coverage_gap_turns": gap_turns,
        "tokens_basis": TOKENS_BASIS,
        "candidate": True,
        "serves_truth": False,
    }


def _comparison(base: dict[str, Any], expanded: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "realistic_session_corpus_comparison",
        "base_corpus_label": base.get("corpus_label"),
        "expanded_corpus_label": expanded.get("corpus_label"),
        "base_card_count": base.get("card_count", 0),
        "expanded_card_count": expanded.get("card_count", 0),
        "card_count_delta": int(expanded.get("card_count") or 0) - int(base.get("card_count") or 0),
        "coverage_rate_delta": round(float(expanded.get("coverage_rate") or 0) - float(base.get("coverage_rate") or 0), 3),
        "total_net_saved_tokens_delta": int(expanded.get("total_net_saved_tokens") or 0) - int(base.get("total_net_saved_tokens") or 0),
        "avg_session_net_saved_delta": round(
            float(expanded.get("avg_net_saved_tokens_per_session") or 0)
            - float(base.get("avg_net_saved_tokens_per_session") or 0),
            1,
        ),
        "expanded_net_positive": bool(expanded.get("net_positive")),
        "positive_improvement": (
            bool(expanded.get("net_positive"))
            and int(expanded.get("total_net_saved_tokens") or 0) >= int(base.get("total_net_saved_tokens") or 0)
        ),
        "candidate": True,
        "serves_truth": False,
    }


def _emit(
    *,
    out_dir: Path,
    sessions: list[dict[str, Any]],
    base_turns: list[dict[str, Any]],
    base_sessions: list[dict[str, Any]],
    base_summary: dict[str, Any] | None,
    expanded_turns: list[dict[str, Any]],
    expanded_sessions: list[dict[str, Any]],
    expanded_summary: dict[str, Any],
    comparison: dict[str, Any] | None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "scenario_catalog": out_dir / "scenario_catalog.jsonl",
        "expanded_turns": out_dir / "expanded_session_turns.jsonl",
        "expanded_sessions": out_dir / "expanded_session_summaries.jsonl",
        "expanded_summary": out_dir / "expanded_summary.json",
        "latest_status": OUT_DIR / "latest_status.json",
    }
    _write_jsonl(paths["scenario_catalog"], sessions)
    _write_jsonl(paths["expanded_turns"], expanded_turns)
    _write_jsonl(paths["expanded_sessions"], expanded_sessions)
    _write_json(paths["expanded_summary"], expanded_summary)
    if base_summary is not None:
        paths["base_turns"] = out_dir / "base_session_turns.jsonl"
        paths["base_sessions"] = out_dir / "base_session_summaries.jsonl"
        paths["base_summary"] = out_dir / "base_summary.json"
        _write_jsonl(paths["base_turns"], base_turns)
        _write_jsonl(paths["base_sessions"], base_sessions)
        _write_json(paths["base_summary"], base_summary)
    if comparison is not None:
        paths["comparison"] = out_dir / "corpus_comparison.json"
        _write_json(paths["comparison"], comparison)
    status = {
        "record_type": RECORD_TYPE,
        "generated_at": now_iso(),
        "run_dir": _rel(out_dir),
        "expanded_summary": expanded_summary,
        "base_summary": base_summary,
        "comparison": comparison,
        "paths": {key: _rel(path) for key, path in paths.items()},
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(paths["latest_status"], status)
    _write_json(out_dir / "run_manifest.json", status)
    return status


def run(
    *,
    sessions_n: int,
    turns_per_session: int,
    k: int,
    components_per_turn: int,
    seed: int,
    base_limit: int,
    supervised_limit: int,
    max_cycles: int,
    scenario_mode: str,
    include_supervised: bool,
    compare_base: bool,
    context_window: int,
) -> dict[str, Any]:
    sessions = build_sessions(
        session_count=sessions_n,
        turns_per_session=turns_per_session,
        seed=seed,
        scenario_mode=scenario_mode,
    )
    corpora = load_cards(
        base_limit=base_limit,
        supervised_limit=supervised_limit,
        max_cycles=max_cycles,
        include_supervised=include_supervised,
    )
    expanded_cards = corpora["expanded"]
    if not expanded_cards:
        raise RuntimeError("no primitive cards found for realistic session benchmark")
    expanded_turns, expanded_session_rows, expanded_summary = run_sessions(
        expanded_cards,
        sessions,
        corpus_label="base_plus_20m_supervised_lifecycle_and_large_org_packs" if include_supervised else "base_registry",
        k=k,
        components_per_turn=components_per_turn,
        context_window=context_window,
    )
    base_turns: list[dict[str, Any]] = []
    base_session_rows: list[dict[str, Any]] = []
    base_summary: dict[str, Any] | None = None
    comparison: dict[str, Any] | None = None
    if compare_base and include_supervised and corpora["base"]:
        base_turns, base_session_rows, base_summary = run_sessions(
            corpora["base"],
            sessions,
            corpus_label="base_registry",
            k=k,
            components_per_turn=components_per_turn,
            context_window=context_window,
        )
        comparison = _comparison(base_summary, expanded_summary)

    run_id = f"realistic-session-bench-{_utc_stamp()}-{_sha({'seed': seed, 'sessions': sessions_n})}"
    return _emit(
        out_dir=OUT_DIR / "runs" / run_id,
        sessions=sessions,
        base_turns=base_turns,
        base_sessions=base_session_rows,
        base_summary=base_summary,
        expanded_turns=expanded_turns,
        expanded_sessions=expanded_session_rows,
        expanded_summary=expanded_summary,
        comparison=comparison,
    )


def _self_test() -> int:
    synthetic_cards = [
        {
            "primitive_id": "prim:project-scaffold",
            "title": "project scaffold react fastapi postgres tenant workspace",
            "input_edge": "ProductBrief",
            "output_edge": "ProjectScaffold",
            "kind": "primitive_group",
            "source_family": "multistep_coding_group",
            "leverage_tier": "high",
        },
        {
            "primitive_id": "prim:login-rbac",
            "title": "login session rbac authorization password reset mfa",
            "input_edge": "AuthIntent",
            "output_edge": "AuthRoutes",
            "kind": "primitive_group",
            "source_family": "adapter_mutator_chain",
            "leverage_tier": "high",
        },
        {
            "primitive_id": "prim:warehouse-dbt",
            "title": "bigquery dbt data warehouse star schema airflow dagster",
            "input_edge": "WarehouseIntent",
            "output_edge": "WarehouseModels",
            "kind": "primitive_group",
            "source_family": "multistep_coding_group",
            "leverage_tier": "high",
        },
        {
            "primitive_id": "prim:dashboard",
            "title": "react admin dashboard filters tables export accessibility",
            "input_edge": "DashboardIntent",
            "output_edge": "DashboardSurface",
            "kind": "primitive",
            "source_family": "adapter_mutator_chain",
            "leverage_tier": "high",
        },
    ]
    sessions = build_sessions(session_count=2, turns_per_session=3, seed=3, scenario_mode="mixed")
    turns, session_rows, summary = run_sessions(
        synthetic_cards,
        sessions,
        corpus_label="synthetic",
        k=3,
        components_per_turn=2,
        context_window=65_536,
    )
    miss_turns, miss_sessions, miss_summary = run_sessions(
        [
            {
                "primitive_id": "prim:unrelated",
                "title": "video transcoding codec waveform audio sprite sheet",
                "input_edge": "MediaIntent",
                "output_edge": "VideoArtifact",
                "kind": "primitive",
                "source_family": "synthetic",
            }
        ],
        sessions,
        corpus_label="synthetic_miss",
        k=1,
        components_per_turn=1,
        context_window=65_536,
    )
    checks = [
        ("turn rows emitted", len(turns) == 6),
        ("session rows emitted", len(session_rows) == 2),
        ("rows are candidate-only", all(row["candidate"] and row["serves_truth"] is False for row in [*turns, *session_rows])),
        ("summary has required session metrics", all(key in summary for key in ("coverage_rate", "total_net_saved_tokens", "reduction_ratio", "stage_rollups_worst_first"))),
        ("matching corpus is net positive", summary["net_positive"] is True and summary["total_net_saved_tokens"] > 0),
        ("miss corpus is not forced positive", miss_summary["total_net_saved_tokens"] < summary["total_net_saved_tokens"]),
        ("miss rows emitted", bool(miss_turns) and bool(miss_sessions)),
        ("sessions carry the CODE-STATE axis (brownfield/legacy variants, not only greenfield)",
         all(s.get("code_state") in {c[0] for c in CODE_STATE_VARIANTS} for s in sessions)
         and len({s["code_state"] for s in build_sessions(session_count=5, turns_per_session=2,
                                                          seed=3, scenario_mode="mixed")}) == 5),
        ("kaggle scenario mode filters to kaggle_project templates",
         all(s["category"] == "kaggle_project"
             for s in build_sessions(session_count=3, turns_per_session=2, seed=1, scenario_mode="kaggle"))
         and len(_template_filter("kaggle")) == 3),
    ]
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - realistic session benchmarks cover multi-prompt app and warehouse sessions; candidate-only.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--sessions", type=int, default=DEFAULT_SESSIONS)
    parser.add_argument("--turns-per-session", type=int, default=0, help="0 = all turns in each template")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--components-per-turn", type=int, default=DEFAULT_COMPONENTS_PER_TURN)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--base-limit", type=int, default=30_000)
    parser.add_argument("--supervised-limit", type=int, default=80_000)
    parser.add_argument("--max-cycles", type=int, default=5)
    parser.add_argument(
        "--scenario-mode",
        choices=["mixed", "warehouse", "app", "regulated", "platform", "ml_lifecycle", "large_org", "kaggle"],
        default="mixed",
    )
    parser.add_argument("--context-window", type=int, default=DEFAULT_CONTEXT_WINDOW)
    parser.add_argument("--include-supervised", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--compare-base", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.run:
        parser.error("--run is required unless --self-test is used")
    status = run(
        sessions_n=max(1, args.sessions),
        turns_per_session=max(0, args.turns_per_session),
        k=max(1, args.k),
        components_per_turn=max(1, args.components_per_turn),
        seed=max(0, args.seed),
        base_limit=max(0, args.base_limit),
        supervised_limit=max(0, args.supervised_limit),
        max_cycles=max(0, args.max_cycles),
        scenario_mode=args.scenario_mode,
        include_supervised=args.include_supervised,
        compare_base=args.compare_base,
        context_window=max(4_096, args.context_window),
    )
    print(json.dumps(status, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
