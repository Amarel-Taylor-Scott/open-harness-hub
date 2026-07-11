"""src.teleon.lift.connectors — inventory connectors behind a port (offline canned + labelled live SEAMS).

InventoryConnectorPort.scan() returns provider-native resource dicts (the shape normalize.py accepts). The
offline CANNED connectors return realistic fixtures (env vars carry VALUES on purpose, so the redaction proof has
something to strip). The LIVE connectors are labelled seams — they document the real provider API to call and
raise until creds/network exist (mirrors _repos/shared-backend-components/scripts/ingest/sanctions_feed_live.py's --live discipline). No network,
no SDK import here.
"""
from __future__ import annotations

from typing import Any, Protocol


class InventoryConnectorPort(Protocol):
    """Discover existing workloads. `scan()` returns a list of provider-native resource dicts. READ-ONLY."""
    source: str

    def scan(self) -> list[dict]: ...


# ── offline canned fixtures (realistic shapes; env values present so redaction can be proven to drop them) ──
_CANNED_K8S: list[dict] = [
    {
        "kind": "Job", "name": "invoice-extraction", "namespace": "production", "cluster": "prod-us-east",
        "labels": {"team": "finance-ops", "service": "invoice-processing"},
        "image": "registry/invoice-extractor:1.4", "command": ["python", "extract.py"],
        "env": [{"name": "DATABASE_URL", "value": "postgres://user:SECRET@db/invoices"},
                {"name": "S3_BUCKET", "value": "acme-invoices"}, {"name": "OPENAI_API_KEY", "value": "sk-REDACTME"}],
        "service_account": "invoice-job-sa", "queue": "invoice-uploaded-prod",
        "resources": {"cpu": "1", "memory": "2Gi"}, "repo": "github.com/acme/invoice-processing",
        "logs_ref": "loki://prod/invoice-extraction", "metrics_ref": "prom://prod/invoice-extraction",
    },
    {
        "kind": "CronJob", "name": "nightly-fact-refresh", "namespace": "production", "cluster": "prod-us-east",
        "labels": {"team": "data-platform", "service": "fact-freshness"}, "schedule": "0 2 * * *",
        "image": "registry/fact-refresh:2.0",
        "env": [{"name": "DB_DSN", "value": "postgres://x"}, {"name": "REDIS_URL", "value": "redis://y"}],
        "service_account": "fact-refresh-sa", "repo": "github.com/acme/fact-freshness",
        "metrics_ref": "prom://prod/nightly-fact-refresh",
    },
    {
        "kind": "Deployment", "name": "risk-summary-api", "namespace": "production", "cluster": "prod-us-east",
        "labels": {"team": "risk", "service": "risk-summary"}, "image": "registry/risk-summary:3.1", "replicas": 4,
        "env": [{"name": "POSTGRES_HOST", "value": "h"}, {"name": "ANTHROPIC_API_KEY", "value": "sk-ant-REDACTME"}],
        "exposed_by": ["Service:risk-summary-svc", "Ingress:risk.acme.internal"],
        "service_account": "risk-summary-sa", "repo": "github.com/acme/risk-summary",
        "logs_ref": "loki://prod/risk-summary-api",
    },
]

_CANNED_LAMBDA: list[dict] = [
    {
        "source": "aws", "name": "process-invoice-prod", "account": "123456789012", "region": "us-east-1",
        "runtime": "python3.12", "handler": "app.handler", "memory_mb": 1024, "timeout_s": 60,
        "role": "arn:aws:iam::123456789012:role/process-invoice",
        "env": {"DATABASE_URL": "postgres://SECRET", "QUEUE_URL": "https://sqs/...", "OPENAI_API_KEY": "sk-REDACTME"},
        "event_source_mappings": [{"type": "sqs", "ref": "invoice-uploaded-prod"}], "function_url": False,
        "tags": {"team": "finance-ops", "service": "invoice-processing"}, "repo": "github.com/acme/invoice-fn",
        "logs_ref": "cloudwatch://process-invoice-prod", "metrics_ref": "cloudwatch://process-invoice-prod",
    },
]


class CannedK8sConnector:
    """Offline K8s inventory (the offline default). The live adapter would use the K8s API list/watch."""
    source = "k8s"

    def scan(self) -> list[dict]:
        return [dict(r) for r in _CANNED_K8S]


class CannedLambdaConnector:
    """Offline AWS Lambda inventory (the offline default). The live adapter would call ListFunctions/GetFunction."""
    source = "aws"

    def scan(self) -> list[dict]:
        return [dict(r) for r in _CANNED_LAMBDA]


# ── live SEAMS (labelled; not exercised offline — they document the exact provider API) ──
_LIVE_API_NOTES = {
    "aws": "AWS Lambda ListFunctions/GetFunction + event-source-mappings + EventBridge rules + IAM role summary "
           "+ CloudWatch log/metric refs (env VALUE never read — key names only).",
    "gcp": "GCP Cloud Asset Inventory searchAllResources + Cloud Functions/Run v2 list (location '-') + Pub/Sub "
           "+ Cloud Scheduler + IAM service-account summary.",
    "azure": "Azure Resource Graph + Function Apps + App Insights refs + Event Grid/Service Bus + managed identity.",
    "k8s": "Kubernetes API list/watch (resourceVersion + bookmarks; relist on 410 Gone) + kube-state-metrics.",
    "iac": "Terraform/CloudFormation/Helm/Kustomize/GitHub Actions parse (Terraformer is DEPRECATED 2026-03-16 — "
           "do NOT build on it).",
}


class LiveConnectorSeam:
    """A labelled live connector that is NOT implemented offline. Documents the real provider API to call."""

    def __init__(self, source: str):
        self.source = source
        self.api_note = _LIVE_API_NOTES.get(source, "unknown provider")

    def scan(self) -> list[dict]:
        raise NotImplementedError(
            f"live {self.source} connector is a SEAM (needs creds + network). Real API: {self.api_note}")


def offline_connectors() -> list[InventoryConnectorPort]:
    """The offline default connector set (canned K8s + Lambda) — the whole pipeline runs from these with no cloud."""
    return [CannedK8sConnector(), CannedLambdaConnector()]


__all__ = ["InventoryConnectorPort", "CannedK8sConnector", "CannedLambdaConnector", "LiveConnectorSeam",
           "offline_connectors", "_LIVE_API_NOTES"]
