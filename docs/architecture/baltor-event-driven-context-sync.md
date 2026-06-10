# Baltor Event-Driven Context Sync

Updated: 2026-06-01

Baltor should treat context synchronization as an event-driven control loop, not
as a periodic full re-index. Commits, pushes, merge requests, pipeline
artifacts, source edits, and scheduled refreshes all create typed sync events.
Workers then decide whether to pull exact source objects, ingest generated
artifacts, regenerate derived context, refresh stale facts, or only record a
heartbeat/check result.

## Source Patterns

Common trigger sources:

| Source | Events | Best use |
| --- | --- | --- |
| GitHub webhooks/actions | `push`, `pull_request`, `workflow_run`, `check_run`, `repository_dispatch`, `workflow_dispatch` | Repo-wiki generation, MR context packs, artifact ingestion, manual refresh. |
| GitLab webhooks | push, merge request, pipeline, job, comment/edit events | GitLab-first repo and MR context sync. |
| GitLab APIs | MR pipelines and job artifacts | Pull exact pipeline status and generated wiki/context artifacts. |
| Tekton Triggers | EventListener, Trigger, Interceptor, TriggerBinding, TriggerTemplate | Kubernetes-native event filtering and deterministic PipelineRun creation. |
| Argo Events | EventSource, Sensor, Trigger | Event-to-workflow orchestration for webhook, S3/object events, cron, queues, and workflow fan-out. |
| Local hooks/watchers | post-commit hook, file watcher | Developer-local wiki/context drafts before push. |
| Schedules/pollers | cron, scheduled workflow, repository polling | Backstop for missed webhooks and stale facts. |

## Push, Pull, And Hybrid Sync

Use three sync modes.

### Push Sync

The source system sends an event.

```text
push / MR / pipeline event
-> webhook receiver
-> signature and replay check
-> normalize to baltor.context-sync-event.v1
-> dedupe by source/ref/sha/event kind
-> enqueue lane-specific work
```

Best for:

- commits and pushes;
- MR/PR updates;
- pipeline completion;
- artifact availability;
- edited comments or docs.

Risk:

- payloads are untrusted source data;
- webhooks can be duplicated, delayed, or delivered out of order;
- a webhook does not prove the generated artifact is available yet.

### Pull Sync

Baltor asks the source for current state or exact artifacts.

```text
scheduled poll / exact handle fetch
-> source API metadata request
-> compare etag, sha, updated_at, pipeline id, artifact hash
-> pull only changed or exact objects
```

Best for:

- backfilling after downtime;
- validating freshness;
- fetching GitLab job artifacts by job ID;
- refreshing high-risk volatile facts;
- reconciling missed webhook events.

Risk:

- source API search can be broad and noisy;
- polling too often creates cost and rate-limit pressure.

### Hybrid Sync

Use push to schedule, pull to verify.

```text
webhook says "pipeline finished"
-> Baltor verifies pipeline/job status by API
-> fetches only declared artifact paths
-> validates manifest, commit SHA, content hash
-> imports generated context
```

This is the preferred production pattern.

## Event Envelope

Normalize every trigger into a compact event before queueing work:

```json
{
  "kind": "baltor.context-sync-event.v1",
  "event_id": "evt_...",
  "source_system": "gitlab",
  "connector_id": "connector:repo-wiki",
  "event_type": "pipeline_artifact",
  "delivery": {
    "mode": "push_then_pull",
    "received_at": "2026-06-01T00:00:00Z",
    "signature_verified": true,
    "replay_window_ok": true
  },
  "repo": {
    "host": "gitlab.example.com",
    "project": "group/service",
    "ref": "main",
    "commit_sha": "abc123",
    "merge_request": "42"
  },
  "artifact": {
    "kind": "repo_wiki_manifest",
    "pipeline_id": "991",
    "job_id": "12345",
    "path": "baltor/repo-wiki-manifest.json",
    "content_sha256": "..."
  },
  "dedupe_key": "gitlab:group/service:abc123:pipeline_artifact:repo_wiki_manifest",
  "queue_policy": {
    "lane": "sync",
    "priority": "normal",
    "max_attempts": 5,
    "backoff": "exponential"
  }
}
```

## Check Gates

Every sync event should pass checks before content reaches a model:

| Check | Required behavior |
| --- | --- |
| Signature | Verify GitHub/GitLab webhook signature or trusted internal source. |
| Replay | Reject stale delivery IDs or timestamps outside the replay window. |
| Scope | Ensure repo/project/ref is allowed for the connector. |
| ACL | Apply source/project ACL before derived context is exposed. |
| Event filter | Ignore events outside configured branches, paths, or event kinds. |
| Artifact manifest | Require declared artifact type, commit SHA, content hash, and schema version. |
| Generated content policy | Treat generated docs as derived context, not source truth. |
| Prompt-injection scan | Treat webhook payloads, comments, docs, and generated pages as untrusted data. |
| Idempotency | Reprocessing the same event must not duplicate graph facts or cache entries. |
| Staleness | Do not serve repo-wiki pages after the repo ref advances unless policy allows stale context. |

## Worker Routing

Recommended worker lanes:

| Event | Queue task | Lane |
| --- | --- | --- |
| `push_webhook` | `repo.diff.plan` | `sync` |
| `merge_request_webhook` | `repo.mr_context.plan` | `sync` |
| `pipeline_artifact` | `repo_wiki.artifact.import` | `ingest` |
| `post_commit_hook` | `repo_wiki.local_draft.import` | `ingest` |
| `file_watcher` | `repo_wiki.local_draft.refresh` | `refresh` |
| `scheduled_poll` | `repo.sync.poll` | `refresh` |
| `release_tag` | `repo_wiki.versioned.promote` | `promote` |

For repo-wiki artifacts, the pipeline should be:

```text
event normalize
-> verify signature/scope/dedupe
-> fetch artifact manifest
-> validate manifest schema and content hashes
-> import pages as baltor.repo-wiki-page.v1
-> generate source handles pinned to commit SHA
-> update context gateway search index
-> emit heartbeat/audit event
```

## Artifact Manifest

CI-generated repo context should include a manifest:

```json
{
  "kind": "baltor.repo-wiki-artifact-manifest.v1",
  "provider": "repowiki",
  "repo": "group/service",
  "ref": "main",
  "commit_sha": "abc123",
  "pipeline": {
    "system": "gitlab",
    "pipeline_id": "991",
    "job_id": "12345",
    "trigger": "merge_request_event"
  },
  "generated_at": "2026-06-01T00:00:00Z",
  "pages": [
    {
      "path": "wiki/request-pipeline.md",
      "kind": "baltor.repo-wiki-page.v1",
      "title": "Request Pipeline",
      "content_sha256": "...",
      "source_handles": [
        "ctx://repo/group/service/commit/abc123/path/src/request.py#L20-L80"
      ]
    }
  ],
  "policy": {
    "generated_docs_are_derived_context": true,
    "raw_repo_scan_allowed": false,
    "commit_scoped_outputs_required": true
  }
}
```

## Orchestration Options

| Orchestrator | Fit |
| --- | --- |
| Local hooks + Baltor cache scripts | Fastest local PoC, good for Obsidian/Markdown memory. |
| GitHub Actions / GitLab CI | Best initial enterprise artifact producer. |
| Tekton Triggers | Kubernetes-native event filtering and pipeline creation. |
| Argo Events + Argo Workflows | Good for event-to-DAG workflows and object-store/cron/queue triggers. |
| Temporal | Best for long-running syncs, retries, and customer-visible workflow state. |
| Redis/SQS/PubSub queues | Good for lane workers and bursty event fan-out. |

## Recommended MVP

1. Add a governed `repo_wiki` connector envelope with sync triggers.
2. Generate a mock `baltor.repo-wiki-artifact-manifest.v1`.
3. Import mock pages as derived context with commit-scoped handles.
4. Add a CI example that uploads the manifest as an artifact.
5. Add a `context_repo_wiki` or `context_search(source=repo_wiki)` proof.
6. Add webhook receiver later; start with artifact import to avoid opening a
   broad raw repo read path.

## Sources

- GitHub Actions events: <https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows>
- GitLab webhooks: <https://docs.gitlab.com/ee/user/project/integrations/webhooks.html>
- GitLab webhook events: <https://docs.gitlab.com/user/project/integrations/webhook_events/>
- GitLab project webhooks API: <https://docs.gitlab.com/api/project_webhooks/>
- GitLab merge request pipelines API: <https://docs.gitlab.com/api/merge_requests/>
- GitLab job artifacts API: <https://docs.gitlab.com/api/job_artifacts/>
- Tekton Triggers: <https://tekton.dev/docs/triggers/>
- Tekton Interceptors: <https://tekton.dev/docs/triggers/interceptors/>
- Argo Events: <https://github.com/argoproj/argo-events>
- Argo Events workflow trigger: <https://argoproj.github.io/argo-events/sensors/triggers/argo-workflow/>
