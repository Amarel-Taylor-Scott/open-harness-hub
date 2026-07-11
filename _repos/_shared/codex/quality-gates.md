# Quality Gates

Scaling to a million objects is only useful if objects are trustworthy, searchable, and deployable.

## Required Gates

- **Schema validity**: component definitions pass JSON Schema validation.
- **Reference validity**: component references resolve.
- **Vocabulary validity**: industries, capabilities, and modalities use controlled vocabularies unless intentionally extended.
- **Provenance**: source, collection date, publisher, license, and trust boundary are recorded.
- **Privacy**: no real PII, PHI, secrets, credentials, or employer-confidential content in repo data.
- **Reproducibility**: benchmarks declare commit SHA, dataset version, and run date.
- **Freshness**: volatile facts have refresh, archive, or revocation strategy.
- **Deduplication**: near-duplicates are linked or merged.
- **Evaluation**: high-impact primitives have rubrics, test cases, or benchmark plans.
- **Deployment clarity**: tools and pipelines declare local, external, containerized, MCP, cloud-function, or hosted runtime assumptions.
- **Daily throughput evidence**: daily factory runs report generated candidate rows, staged unique rows, review-ticket counts, and showcase pipeline counts separately.
- **Proof boundary**: generated rows, staged load-ready rows, and committed Postgres rows are separate metrics. A staged audit is not proof of database load.
- **Showcase usefulness**: daily showcase pipelines should map real user problem sentences to pre-LLM, LLM, post-LLM, review, cost, and deployment components.
- **Speed discipline**: daily generation should use database-backed JSONL partitions, load plans, and index deltas. Full static-site rebuilds are release gates, not a prerequisite for each high-volume batch.

## Warning-First Drift Gates

These checks are surfaced by `scripts/validate.py` during release-scope
validation, but they are advisory before they become hard gates.

- **Database-backed migration drift**: catalog YAML manifests are seed/export
  artifacts. Validation warns when manifest import records are missing or stale
  relative to current catalog manifests.
- **Hard-coded setting drift**: model IDs, backend names, vector dimensions,
  route names, thresholds, and cloud settings should move into `scripts._config`
  registries or `setting_profile` / `setting_value` rows. Validation warns on
  repeated unregistered literals found by the context-storage audit.
- **Object governance package gaps**: account management, billing, context,
  flow, connection, process, database, identity, policy, integration, and
  analytics objects need governance packages: rubrics, contracts, schemas,
  layouts, diagrams, context rules, lifecycle, events, policy, and storage
  mapping. Validation warns when the schema/rubric exists but operational
  seed/export row artifacts are not present.

Promotion path:

1. Warn in full validation.
2. Create or refresh database seed/import artifacts.
3. Baseline intentional exceptions with owners and review dates.
4. Promote stable checks to fatal release gates.

## Human Review Queues

Objects should be routed for review when they are:

- legal, medical, financial, public safety, or child-safety relevant;
- extracted from volatile public facts;
- signed by external publishers;
- generated from job descriptions or SOPs;
- candidates for automated deployment;
- high cost, high risk, or high usage.

Daily batches must not bypass review queues to hit volume targets. If a high-risk source or generated candidate is uncertain, count it as staged or review-pending, not approved.

## Anti-Patterns

- Huge untyped dumps with no extraction schema.
- Prompt-only pipelines where tools, RAG, or verification are needed.
- Unversioned live facts.
- Undifferentiated workflow imports with no safety scan.
- Model recommendations without current pricing and hosting assumptions.
- Human-review domains without procedure questions or evidence requirements.
- Reporting raw generated JSONL lines as active components.
- Treating public component definition count as the only progress metric.
- Blocking daily component generation on full catalog page rebuilds when focused validation, selected page rendering, and database load audits are sufficient for the current change.
- Shipping daily generated candidates without at least one path to showcase pipelines.
- Stopping daily progress because one source surface is unavailable when other matrices, pipeline templates, rubrics, audits, or promotion planners can still move forward.
