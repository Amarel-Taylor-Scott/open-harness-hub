# AIDevObserver Long Session Sources And Ingestion Plan

Date: 2026-06-28

## Short Answer

Yes. We should build AIDevObserver around both public long-session sources and controlled synthetic long-session generation.

The best strategy is tiered:

1. Ingest published AI coding sessions and agent trajectories where license, provenance, and redaction are acceptable.
2. Use SWE-bench-style tasks and agent harnesses to generate our own reproducible long sessions.
3. Create large synthetic application sessions for product demos and benchmark fixtures.
4. Normalize everything into AIDevObserver session records, then route them through registry search, reinvention detection, token accounting, and proof/promotion review.

The important framing:

```text
Public does not automatically mean ingestable.
Every source needs license, provenance, redaction, and serves_truth=false until reviewed.
```

## Why Long Sessions Matter

Short sessions prove the UI. Long sessions prove the product.

Large application sessions expose the patterns AIDevObserver is supposed to catch:

- agents recreating helpers that already exist somewhere in the primitive database;
- repeated code search through model context instead of deterministic search;
- loops where an agent keeps testing or patching the same failure;
- framework boilerplate generated from scratch instead of retrieved from templates;
- duplicate API clients, validators, retry wrappers, CSV parsers, auth helpers, CI jobs, and ETL steps;
- high-token context dumps that could have been compacted into a registry route;
- local work that should become a reusable primitive, template, or composite route.

For demos, a long synthetic session should feel like a real multi-file build:

```text
user asks for a large app capability
agent reads many files
agent creates duplicate code
agent loops on tests
observer finds existing primitive/template/workflow route
human accepts or dismisses
registry memory improves
```

## Source Classes

### 0. Curated Public Codegen Use-Case Seeds

This is the first active ingestion lane.

It is not a live download connector. It is a normalized seed pack for likely
LLM coding use cases, shaped exactly like the output we want future GitHub,
Kaggle, package-registry, n8n, and benchmark connectors to produce.

Seed file:

```text
catalog/knowledge-packs/data/aidevobserver-public-codegen-use-cases/use-cases.jsonl
```

Each seed records:

```text
task family
industry
intent
observed reinvention patterns
expected template
expected primitives
artifact policy
effects
source status
license status
serves_truth=false
```

The foundry loop converts each seed into:

```text
source_candidate
synthetic_session_spec
primitive_draft records
candidate_ranking row
```

This gives us immediate realistic primitive/session generation while preserving
the hard truth boundary:

```text
curated seed != live public evidence
generated primitive draft != registry truth
synthetic session != real transcript
serves_truth=false until proof/promotion
```

### 0b. Product Microsurface Atlas

This is the second active seed lane.

Seed file:

```text
catalog/knowledge-packs/data/aidevobserver-microsurface-atlas/microsurfaces.jsonl
```

The microsurface atlas decomposes common website/app/platform surfaces into:

```text
surface family
platform examples
common objects
common actions
reinvention patterns
candidate templates
candidate primitives
industries
modalities
effects
artifact policy
serves_truth=false
```

This is how AIDevObserver can move beyond GitHub/Kaggle and model what agents
commonly rebuild inside product work:

```text
login/session/MFA
checkout/subscription/billing
admin table/CRUD/import/export
search/filter/sort/recommend
notifications/preferences/delivery
file upload/scan/preview/convert
review/approval/escalation
maps/geocoding/routing
media generation/QC/publish
analytics dashboards/metric cards
marketplace listing/cart/order/return
support chat/ticket/CRM/SLA
```

The next expansion target is hundreds to thousands of these microsurfaces,
covering the repeated objects and flows used by the top websites, SaaS apps,
marketplaces, developer tools, media tools, data platforms, and enterprise
systems. Each row should generate candidate source records, realistic demo
session specs, primitive drafts, and benchmark ideas without claiming live
source truth.

### 1. Real Published Sessions

These are the most persuasive for product positioning, because they show actual human/agent behavior.

Candidate sources:

- SWE-chat: real coding agent sessions from public repositories.
- Programming by Chat: real IDE-native AI-assisted sessions from public repositories.
- Public chat/session files committed to GitHub, such as exported assistant logs, JSONL transcripts, or Aider-style history files.

Use these for:

- benchmark realism;
- examples of progressive specification;
- measuring actual reinvention and context waste;
- building finder precision tests.

Do not use them blindly. Run license, privacy, secret, PII, and source-attribution gates.

Current implementation status:

```text
_repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --live-github
_repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py --live-kaggle
```

This connector performs live GitHub Code Search metadata discovery behind an
explicit opt-in flag. It stores candidate metadata only: URL, repository
identifier, file path/name, source SHA, query digest, and status fields. It
does not fetch raw transcript/source content.

The connector emits:

```text
source_kind=public_github_session_candidate
source_status=metadata_discovered_not_downloaded
license_status=needs_review
redaction_status=not_fetched
serves_truth=false
```

Next connector stage:

```text
public metadata candidate
  -> license allowlist
  -> raw fetch into artifact
  -> secret/PII scan
  -> source attribution capture
  -> synthetic derivative generation
  -> benchmark fixture review
```

The Kaggle connector is metadata-only today. It lists competitions, datasets,
and kernels by topic through the Kaggle CLI, tolerates older CLI option support,
and stores no notebooks or datasets until a later license/redaction/artifact
fetch gate.

### 2. Synthetic Agent Trajectories

These are useful because they can be long, diverse, and reproducible.

Candidate sources:

- Open-SWE-Traces: a large synthetic trajectory dataset generated through OpenHands and SWE-agent harnesses.
- SWE-Synth-style generated bug-fix traces.
- Our own generated traces from OpenHands, SWE-agent, or similar agents over benchmark tasks.

Use these for:

- long-horizon agent behavior;
- failure-loop fixtures;
- replayable deterministic tests;
- generating many examples without exposing private user logs.

### 3. PR-Level Agent Datasets

These are not always full chat sessions, but they are valuable for reconstructing AI-agent work products and task families.

Candidate sources:

- AIDev / Agentic-PR datasets.
- Agent-authored GitHub PRs with commits, issue links, reviews, and comments.

Use these for:

- identifying common AI-generated capabilities;
- mining repeated task families;
- building primitive candidates from agent-produced code;
- comparing final code against known registry routes.

### 4. Benchmark Tasks That Generate Sessions

SWE-bench is not primarily a session transcript corpus, but it is a strong source of real issue/repo tasks. We can run agents against those tasks and capture the resulting sessions.

Use these for:

- reproducible task setup;
- large-repo debugging sessions;
- before/after comparisons;
- evaluating whether AIDevObserver catches reinvention before an agent wastes context.

### 5. Local Capture Tools

Tools like Entire CLI are useful for collecting first-party sessions with consent. They are not a public dataset by themselves, but they suggest an ingestion model: capture prompts, responses, tool calls, files touched, and token usage alongside Git commits.

Use these for:

- internal dogfooding;
- opt-in user imports;
- traceability around accepted/reused findings.

### 6. Kaggle Projects, Competitions, And Notebooks

Kaggle is not usually a raw AI-session source. It is better treated as a large source of finished public data-science work that can be converted into synthetic sessions and primitive candidates.

Kaggle can give us:

- competition task descriptions;
- datasets and schemas;
- public notebooks/kernels;
- notebook outputs;
- model artifacts and variations;
- discussion threads;
- evaluation metrics and leaderboard context.

That is enough to synthesize realistic long sessions:

```text
competition brief
  -> dataset inspection
  -> baseline notebook reconstruction
  -> feature engineering path
  -> model training path
  -> validation/metric path
  -> submission/output path
  -> primitive extraction
```

Use Kaggle for:

- classification primitives;
- regression primitives;
- time-series forecasting primitives;
- tabular feature engineering primitives;
- computer vision preprocessing/training primitives;
- NLP/text classification primitives;
- geospatial/data-cleaning primitives;
- evaluation and submission templates.

Do not present Kaggle-derived synthetic sessions as real AI-agent transcripts. Label them as `synthetic_from_public_project` and preserve attribution to the competition, dataset, and notebook sources.

## Public Sources To Track

| Source | What it gives us | Use in AIDevObserver |
| --- | --- | --- |
| Curated public codegen seeds | Normalized likely LLM coding tasks and expected primitive families | Immediate realistic demo/session/primitive generation while live connectors mature |
| SWE-chat | Real coding agent sessions with prompts/tool calls | Real-world benchmark fixtures and behavior taxonomy |
| Programming by Chat | IDE-native sessions across public repos | Long conversational programming patterns |
| Open-SWE-Traces | Synthetic multi-turn SWE trajectories | Large-scale long-session training/eval data |
| AIDev / Agentic-PRs | AI-agent PR metadata and changes | Common task families and generated-code mining |
| SWE-bench | Real GitHub issue/repo tasks | Generate our own reproducible long sessions |
| Entire CLI | Git-native session capture model | Opt-in ingestion pattern for user/team sessions |
| GitHub Code Search | Discovery of public session artifacts | Candidate source discovery, license-gated |
| Kaggle competitions/datasets/notebooks | Public ML/data-science tasks, notebooks, outputs, discussions | Synthetic session generation and primitive mining |

## GitHub Search Strategy

Use GitHub Code Search to discover public session-like artifacts. GitHub supports qualifiers such as `repo:`, `org:`, `user:`, `language:`, `license:`, `path:`, `symbol:`, `content:`, `is:`, boolean operators, and regular expressions.

Candidate searches:

```text
path:*.jsonl "role" "assistant" "tool_calls"
path:*.jsonl "\"role\":\"assistant\"" "tool_call"
path:*.json "messages" "tool_calls" "assistant"
path:*.md "assistant:" "tool:" "user:"
path:.aider.chat.history.md
"swe-agent" "trajectory" "patch"
"OpenHands" "trajectory" "SWE-bench"
"Claude Code" "transcript" "tool_calls"
"Codex" "session" "tool_calls"
"Cursor" "chat" "repository"
"GitHub Copilot" "chat" "messages"
```

Add filters when possible:

```text
license:MIT
license:Apache-2.0
NOT is:fork
NOT is:archived
path:/examples/
path:/logs/
path:/traces/
path:/trajectories/
```

These searches should feed a candidate-source queue, not automatic ingestion.

## Kaggle Mining Strategy

Kaggle should feed two outputs:

1. synthetic long sessions for AIDevObserver examples and benchmarks;
2. primitive/template candidates for Teleon/OpenHubForAI registries.

### Discover

Use the Kaggle API/CLI to search:

```text
kaggle competitions list
kaggle competitions files <competition>
kaggle datasets list --search <topic>
kaggle datasets files <owner/dataset>
kaggle kernels list --search <topic>
kaggle kernels pull <owner/kernel>
kaggle kernels output <owner/kernel>
```

Initial topics:

```text
classification
regression
forecasting
tabular
computer vision
nlp
recommendation
fraud detection
churn
house prices
titanic
credit risk
medical imaging
sentiment analysis
time series
```

### Distill

For each selected competition or notebook:

```text
competition overview
dataset contract
target variable
metric
baseline notebook steps
feature transforms
model family
validation method
submission/output format
known pitfalls
```

Normalize into:

```yaml
kaggle_case:
  id: kaggle_case_...
  source_kind: kaggle_competition | kaggle_dataset | kaggle_notebook
  source_url: https://...
  license: ...
  problem_type: classification | regression | forecast | cv | nlp | ranking | anomaly
  input_contract: DatasetArtifact
  output_contract: SubmissionArtifact | ModelArtifact | EvalReport
  metric: auc | rmse | accuracy | f1 | logloss | map_at_k | custom
  steps:
    - inspect_data
    - clean_data
    - feature_engineer
    - split_validate
    - train_model
    - evaluate
    - submit
```

### Synthesize A Session

Build a realistic AI coding session around the distilled case:

```text
user: build a baseline for this Kaggle competition
agent: inspects files and data dictionary
agent: writes loader
agent: writes feature engineering
agent: recreates common transform already in registry
agent: tries model
agent: loops on metric or shape mismatch
observer: finds existing feature, metric, split, or submission primitive
agent: switches to registry route
proof: metric run and output schema pass
```

This creates a long session without pretending Kaggle provided the chat transcript.

### Extract Primitives

Each recurring step becomes a candidate primitive:

```yaml
candidate_primitive:
  slug: kaggle.tabular.standardize_numeric_features
  source_case: kaggle_case_...
  contract_guess: TableArtifact>FeatureTableArtifact
  problem_types: [classification, regression]
  evidence:
    - notebook_cell_range: 12-18
    - competition_metric: rmse
  trust: candidate
  serves_truth: false
```

Each recurring workflow becomes a candidate template:

```yaml
candidate_template:
  slug: kaggle.tabular_baseline_train_submit
  route: load -> clean -> feature -> split -> train -> evaluate -> submit
  contracts:
    input: DatasetArtifact
    output: SubmissionArtifact
  proof_requirements:
    - schema_check
    - metric_recompute
    - deterministic_split
    - output_format_check
  trust: candidate
  serves_truth: false
```

### Primitive Families To Mine From Kaggle

Start with these:

```text
dataset.inspect_schema
dataset.infer_column_roles
table.fill_missing_values
table.encode_categoricals
table.scale_numeric_features
table.create_date_features
table.create_text_features
table.train_valid_split_seeded
metric.compute_rmse
metric.compute_auc
metric.compute_f1
model.train_logistic_regression
model.train_random_forest
model.train_xgboost
model.train_lightgbm
model.train_catboost
model.cross_validate
submission.validate_format
submission.write_csv
```

For image and media competitions:

```text
image.load_dataset
image.resize_normalize
image.augment_train
image.train_classifier
image.evaluate_topk
image.write_predictions
```

For NLP competitions:

```text
text.clean
text.tokenize
text.vectorize_tfidf
text.embed
text.train_classifier
text.evaluate_classification
```

### Kaggle Guardrails

- Respect competition rules and dataset licenses.
- Treat notebook code as source evidence, not automatically reusable code.
- Prefer extracting contracts, routes, and primitive shapes over copying implementation.
- Preserve attribution.
- Redact credentials, file paths, usernames, and private output paths.
- Mark Kaggle-derived primitives as candidate until proof/promotion.
- Do not submit to active competitions from automated pipelines unless explicitly authorized.

## Ingestion Contract

Every discovered or generated long session should become a normalized record.

```yaml
session_id: sess_...
source_kind: public_dataset | public_github | kaggle_project | generated_benchmark | first_party_opt_in | synthetic_demo | synthetic_from_public_project
source_url: https://...
source_commit: sha256_or_git_sha
license: MIT | Apache-2.0 | BSD | unknown | restricted
collected_at: 2026-06-28
serves_truth: false
redaction_status: pending | pass | fail
normalization_status: pending | pass | fail
messages:
  - role: user | assistant | tool | system
    content_ref: inline_or_artifact_ref
    timestamp: optional
    tool_name: optional
    file_refs: []
    token_estimate: optional
actions:
  - kind: file_read | file_write | command | search | tool_call | model_call | test_run
    target: optional
    digest: sha256:...
findings_expected:
  - type: reinvention | wasted_context | loop | missed_route | missing_proof | secret_risk
    source_ref: optional
```

The curated seed lane currently produces these records directly from likely
use cases. Live public connectors should produce the same shape after source
discovery, license review, attribution capture, and redaction.

Hard gates:

- Unknown license blocks publication.
- Secret or PII detection blocks publication until redacted.
- Public-source attribution is preserved.
- Long raw transcripts become artifacts, not inline state.
- Findings remain candidate advice.
- Nothing from a session becomes registry truth without proof/promotion.

## Normalization Pipeline

```text
discover_source
  -> license_gate
  -> fetch_source
  -> secret_pii_redaction
  -> project_or_transcript_distill
  -> transcript_normalize
  -> action_extract
  -> token_accounting
  -> session_segment
  -> registry_search
  -> expected_findings_attach
  -> benchmark_fixture_emit
```

A long session should be segmented into useful windows:

```text
session overview
goal/spec phase
repository exploration phase
implementation phase
test/failure loop phase
registry missed-route phase
final patch/proof phase
```

AIDevObserver should review both:

- the whole session summary;
- selected windows where reinvention or waste likely happened.

## Large Synthetic Application Sessions

We should generate long synthetic sessions for demos even if public data is available. Synthetic sessions let us control the lesson, the registry hits, and the expected findings.

Good app families:

- SaaS admin dashboard;
- CRM/company enrichment product;
- e-commerce storefront plus returns portal;
- RAG documentation search app;
- CSV/warehouse data platform;
- media generation workflow editor;
- DevOps deployment dashboard;
- auth/RBAC backend;
- healthcare prior-auth workflow;
- legal document extraction tool.

Each large synthetic session should include:

- 300 to 2,000 turns or events;
- multi-file edits;
- commands and test runs;
- realistic false starts;
- repeated context dumps;
- at least 5 duplicate-helper opportunities;
- at least 3 missed template/primitive routes;
- at least 1 loop or thrash pattern;
- a clean proof path after reuse;
- expected AIDevObserver findings.

## Long Session Demo Shapes

### Large SaaS App Build

```text
Build an admin dashboard with users, roles, audit logs, billing, CSV import, and exports.
```

Expected finds:

- duplicate CSV importer;
- duplicate retry wrapper;
- duplicate RBAC guard;
- missed admin-table component template;
- context waste from pasted schema;
- repeated test loop on role permissions.

### RAG Documentation App

```text
Build a docs search app with ingestion, chunking, embeddings, citations, and evals.
```

Expected finds:

- existing chunking primitive;
- existing embedding cache primitive;
- missed citation validator;
- recreated vector search wrapper;
- missing eval gate.

### Media Workflow App

```text
Build an image-to-video workflow editor with upload, safety gate, model route, QC, and encode.
```

Expected finds:

- existing media artifact schema;
- existing model route primitive;
- missed safety/QC gates;
- duplicate ffmpeg encode helper;
- large binary output incorrectly placed inline.

### Data Platform Ingestion App

```text
Build a vendor ingestion system with schema validation, type casting, parquet output, and catalog publishing.
```

Expected finds:

- existing CSV/table ingestion template;
- existing field rename remix;
- missed artifact materialization;
- side effect before validation;
- duplicate catalog publish helper.

### Kaggle Competition Baseline

```text
Build a baseline solution for a tabular Kaggle competition with feature engineering, model training, validation, and submission.
```

Expected finds:

- existing train/validation split primitive;
- existing categorical encoding primitive;
- existing metric primitive;
- existing submission format validator;
- repeated notebook-to-script conversion pattern;
- synthetic session route back to a tabular baseline template.

## What To Add To AIDevObserver

### Product

- Add a "Long Sessions" example category.
- Add a "Large application replay" modal group.
- Show token savings by phase, not only whole transcript.
- Show "registry hit found at turn N" so the demo makes missed reuse concrete.
- Add "source_kind" and "license_status" to example metadata.

### Benchmark

Create `AIDevObserver Long Session Benchmark v0`:

```text
24 synthetic large-app sessions
24 public-dataset-derived sessions
24 generated SWE-bench/OpenHands/SWE-agent sessions
24 clean negative-control sessions
```

Metrics:

- reinvention recall;
- source_ref precision;
- missed route top-1 and top-3 accuracy;
- loop detection;
- token waste estimate accuracy;
- redaction correctness;
- license gate correctness;
- false positive rate on clean sessions.

### Registry

When a long session contains a reusable component, emit:

```yaml
candidate_primitive:
  slug: discovered.csv_import.read_rows
  source_session: sess_...
  source_turn_range: [144, 191]
  contract_guess: FileArtifact>TableArtifact
  trust: candidate
  serves_truth: false
```

When a long session shows a repeated route, emit:

```yaml
candidate_template:
  slug: app.admin_table_with_csv_import
  route: parse -> validate -> normalize -> table -> export
  evidence_sessions: [...]
  trust: candidate
  serves_truth: false
```

## First Implementation Slice

1. Add a `long_sessions` source registry JSONL.
2. Add 3 synthetic large-app session fixtures.
3. Add 3 Kaggle-derived synthetic data-science session fixtures. Initial demo-pack fixtures now exist for tabular, image-classification, and text-classification baselines.
4. Add an importer that normalizes TXT, JSON, and JSONL transcript formats.
5. Add a discovery script that stores GitHub and Kaggle search hits as candidate source records only.
6. Add a redaction/provenance report before any source becomes an example.
7. Add a benchmark runner that scores expected findings against AIDevObserver output. Initial verifier: `_repos/shared-backend-components/scripts/check_aidevobserver_session_benchmark.py`.

Initial benchmark fixture pack:

```text
fixtures/benchmarks/aidevobserver_session_review_v0/kaggle_public_project_cases.json
```

The first pack covers tabular, image-classification, and text-classification Kaggle-style synthetic public-project sessions. It records target expected findings, current reviewer expectations, false-positive traps, and proxy token-savings estimates.

Current proof status:

```text
_repos/shared-backend-components/scripts/check_aidevobserver_session_benchmark.py
  3 Kaggle synthetic public-project cases
  6 target expected findings
  current reviewer covers the target source-ref routes
```

The first version of this loop now lives in:

```text
_repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py
```

Operating notes:

```text
_repos/shared-backend-components/context/codex/aidevobserver-context-foundry-loop-runbook.md
```

## Recommended Default Policy

Use synthetic sessions for public demos.

Use public datasets for benchmark development after license/provenance review.

Use first-party opt-in captures for customer value.

Use GitHub search only to discover candidate sources, not to automatically republish transcripts.

Use Kaggle to synthesize realistic sessions and mine primitive contracts; copy no notebook implementation unless its license and attribution are explicitly compatible.

## Sources

- [SWE-chat: Coding Agent Interactions From Real Users in the Wild](https://arxiv.org/abs/2604.20779)
- [Programming by Chat: A Large-Scale Behavioral Analysis of 11,579 Real-World AI-Assisted IDE Sessions](https://arxiv.org/abs/2604.00436)
- [Open-SWE-Traces: Advancing Dual-Mode Multilingual Distillation for Software Engineering Agents](https://arxiv.org/abs/2606.16038)
- [AIDev: Studying AI Coding Agents on GitHub](https://arxiv.org/abs/2602.09185)
- [SWE-bench repository](https://github.com/SWE-bench/SWE-bench)
- [SWE-bench leaderboards and benchmark family](https://www.swebench.com/)
- [Entire CLI](https://github.com/entireio/cli)
- [GitHub Code Search syntax](https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax)
- [Kaggle API / CLI](https://github.com/Kaggle/kaggle-api)
- [Meta Kaggle dataset](https://www.kaggle.com/datasets/kaggle/meta-kaggle)
