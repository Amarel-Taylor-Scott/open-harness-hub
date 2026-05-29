#!/usr/bin/env python3
"""Seed the two outbound/platform ACTION buckets as real components (the recipe's Deliver/emit +
Platform-actions phases): outbound delivery vs on-platform persistence. Uses the shared
standardized builder (scripts.seed.component_seed) so attribution is consistent.

    python3 -m scripts.seed.action_bucket_components
    python3 scripts/validate.py catalog/processors/deliver/*.yaml catalog/processors/platform/*.yaml
"""
from __future__ import annotations

from scripts.seed.component_seed import processor, write_batch

DOC = "docs/concepts/component-taxonomy-and-stages.md"
LABEL = "Open Harness Hub action-bucket taxonomy"

# DELIVER / EMIT — all OUTBOUND actions (the result leaves the platform). (slug, name, process_kind,
# capability, deterministic, side_effects, inputs, outputs, description)
DELIVER = [
    ("deliver-return", "Return to caller", "deliver.return_response", ["routing"], True, "none",
     ["result"], ["response"],
     "Return the validated result to the caller as the synchronous API/function response. The default "
     "outbound: no external system, just the result handed back. Deliver / emit (outbound) bucket."),
    ("deliver-webhook", "Webhook deliver", "deliver.webhook", ["routing"], False, "external_call",
     ["result", "endpoint", "signing_key"], ["delivery_receipt"],
     "POST the result to a configured webhook endpoint with a signed payload + retries/backoff. "
     "Outbound to an external system. Deliver / emit (outbound) bucket."),
    ("deliver-email", "Email deliver", "deliver.email", ["routing"], False, "external_call",
     ["result", "recipients", "template"], ["message_id"],
     "Render the result into an email template and send to recipients. Outbound. Deliver / emit bucket."),
    ("deliver-report", "Report deliver (md / pdf)", "report.pdf", ["routing", "format_conversion"], True, "external_call",
     ["result", "format"], ["document_uri"],
     "Render the result into a shareable report (Markdown / PDF, with citations) and deliver it. The "
     "render is deterministic; the delivery is outbound. Deliver / emit (outbound) bucket."),
    ("deliver-notify", "Notify / alert", "deliver.notify", ["routing"], False, "external_call",
     ["result", "channel"], ["ack"],
     "Post a notification / alert summarizing the result to a channel (Slack / Teams / SMS). Outbound. "
     "Deliver / emit (outbound) bucket."),
    ("escalate-human", "Escalate to human", "escalate.human", ["routing", "governance"], True, "external_call",
     ["result", "reason"], ["ticket"],
     "Route the result + the reason (a fired gate, low confidence, an abstention) to a human review "
     "queue / on-call. The governed escalation path. Deliver / emit (outbound) bucket."),
]

# PLATFORM ACTIONS — persist / register / surface ON the platform (no external send).
PLATFORM = [
    ("persist-run-store", "Persist run to store", "audit.trace", ["memory", "governance"], True, "write",
     ["run"], ["run_id"],
     "Persist the full run object (steps, cost, citations) to the platform run store as a replayable, "
     "auditable trace. The default platform action. Platform-actions (on-platform) bucket."),
    ("persist-object-store", "Persist artifact to object store", "platform.object_store", ["serving"], True, "write",
     ["artifact"], ["uri"],
     "Store result artifacts (export bundles, reports) in platform object storage (S3 / R2) under a "
     "content-addressed URI. Platform-actions (on-platform) bucket."),
    ("persist-pgvector", "Upsert to pgvector index", "index.update_vector", ["embedding", "serving"], False, "write",
     ["records", "embedder"], ["upserted"],
     "Embed result records and upsert them into the platform pgvector index so they become "
     "semantically searchable. Platform-actions (on-platform) bucket."),
    ("persist-postgres", "Upsert to postgres table", "platform.postgres_upsert", ["serving"], True, "write",
     ["rows", "table"], ["upserted"],
     "Upsert structured result rows into a governed postgres table, idempotent by content hash, for "
     "query + reporting. Platform-actions (on-platform) bucket."),
    ("register-component", "Register as component", "platform.register_component", ["governance"], False, "write",
     ["result", "manifest"], ["component_id"],
     "Register a validated result (a fact, list, sub-flow) as a reusable, versioned component / Knowledge "
     "Corpus entry in the platform registry, with provenance — a run's output becomes a building block. "
     "Platform-actions (on-platform) bucket."),
    ("create-data-store-view", "Create data store + view", "platform.create_data_store", ["serving"], True, "write",
     ["rows", "schema"], ["store_id", "view"],
     "Materialize a queryable data store + view from accumulated results — the component-generated stores "
     "the dashboards bind to. Platform-actions (on-platform) bucket."),
    ("update-dashboard-widget", "Update dashboard widget", "platform.dashboard_widget", ["serving"], True, "write",
     ["metric", "store"], ["widget_id"],
     "Feed a metric from the result into a monitoring dashboard widget (cost, lift-over-time decay, "
     "freshness). Platform-actions (on-platform) bucket."),
    ("cache-write", "Cache response", "cache.write_response", ["memory"], True, "write",
     ["key", "result", "ttl"], ["cached"],
     "Cache the result keyed by the (task, components, inputs) hash so identical runs return instantly "
     "and at near-zero cost. Platform-actions (on-platform) bucket."),
    ("memory-write", "Write to memory", "memory.write_conversational", ["memory"], True, "write",
     ["turn", "session"], ["written"],
     "Write the result to conversational / agent memory for multi-turn continuity. Platform-actions bucket."),
]


def main() -> int:
    deliver = [processor(*c, tags=("action-bucket", "deliver", "outbound"), source_doc=DOC,
                         source_label=LABEL, impl_prefix="scripts.processors.deliver") for c in DELIVER]
    platform = [processor(*c, tags=("action-bucket", "platform", "on-platform"), source_doc=DOC,
                          source_label=LABEL, impl_prefix="scripts.processors.platform") for c in PLATFORM]
    wd = write_batch("catalog/processors/deliver", deliver)
    wp = write_batch("catalog/processors/platform", platform)
    print(f"wrote {len(wd)} deliver + {len(wp)} platform components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
