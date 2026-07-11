# Enterprise operating-system primitive atlas

> GENERATED from `catalog/knowledge-packs/data/enterprise-operating-system-primitive-atlas/atlas_source.yaml`.
> Public examples establish workflow breadth; primitive decompositions are independent candidate inferences.

## Honest boundary

This atlas does **not** claim access to every project performed by Palantir or any other company, and it does not
copy vendor code, UI, schemas, or proprietary implementation details. It normalizes publicly documented patterns
into generic system families, workflows, canonical primitive templates, specialization edges, proof plans, and
project benchmark seeds. All generated rows are `candidate=true` and `serves_truth=false`.

A benchmark binding is only a seed. It becomes a real result only after the starter repo, runtime, hidden oracle,
known-good/known-bad mutation checks, cleanup, and `project_run_receipt` actually execute.

## Generated surface

- system families: 30
- business workflows: 120
- canonical primitive templates: 83
- system-adapter candidates: 210
- workflow-specific primitive candidates: 5201
- source records: 39
- project benchmark seeds: 120

## Normalization model

```text
canonical operation + typed contract + invariants + side effects + error semantics
  + system adapter + industry/standard overlay + workflow composition + executable oracle
```

Company and product names are provenance, not primitive identity. A hospital bed, transformer, aircraft, railcar,
factory machine, and vehicle can all specialize the same governed `asset` operations. A quality investigation,
AML case, public-sector case, and incident can all specialize the same evidence-linked case/work-queue machinery.

## System families and workflows

| System family | Industries | Workflows | Public evidence refs |
|---|---|---:|---|
| `automotive-mobility` | automotive, manufacturing | 4 | palantir-automotive |
| `aviation-operations` | aviation, transportation | 4 | palantir-airbus |
| `construction-operations` | construction, real_estate | 4 | palantir-construction |
| `defense-readiness-logistics` | defense | 4 | palantir-gotham, palantir-defense-navy, palantir-readiness |
| `energy-utility-operations` | energy, energy.grid, climate | 4 | palantir-energy |
| `financial-services-aml` | finance, finance.aml, finance.kyc | 4 | palantir-financial-services, palantir-aml |
| `food-agriculture-operations` | food, agriculture, food_safety | 4 | palantir-food-beverage, palantir-consumer-goods |
| `government-financial-readiness` | government, defense | 4 | army-financial-management, palantir-readiness |
| `hospital-operations` | healthcare | 4 | palantir-hospitals |
| `humanitarian-operations` | humanitarian, nonprofit, logistics | 4 | wfp-palantir |
| `life-sciences-operations` | pharma, biotech, scientific_research | 4 | palantir-health |
| `manufacturing-operations` | manufacturing | 4 | palantir-manufacturing |
| `platform-ai-agents` | ai, cross_industry | 4 | palantir-aip-logic, palantir-aip-retrieval, palantir-aip-evals |
| `platform-data-integration` | cross_industry, data_governance | 4 | palantir-data-integration, palantir-platform-architecture, sec-palantir-form-10k |
| `platform-deployment-runtime` | software, it, sre | 4 | palantir-apollo-environments, palantir-platform-architecture |
| `platform-model-operations` | ai, software | 4 | palantir-model-integration, palantir-aip-evals |
| `platform-observability` | it, sre, software, ai | 4 | palantir-observability |
| `platform-ontology-digital-twin` | cross_industry, data_governance | 4 | palantir-ontology-system, palantir-platform-architecture |
| `platform-operational-workflows` | cross_industry | 4 | palantir-action-types, palantir-automate |
| `platform-process-mining` | cross_industry, data_governance | 4 | palantir-process-mining |
| `platform-security-governance` | security, privacy, compliance, ai_governance | 4 | palantir-security, palantir-platform-architecture |
| `procurement-contract-operations` | procurement, supply_chain | 4 | palantir-procurement |
| `public-health-research` | healthcare.public_health, scientific_research, data_governance | 4 | palantir-health, nih-n3c |
| `public-sector-case-management` | government, humanitarian | 4 | palantir-uk-government |
| `rail-transportation-operations` | transportation, transportation.rail | 4 | palantir-rail |
| `retail-consumer-goods` | retail, manufacturing, supply_chain | 4 | palantir-retail, palantir-consumer-goods |
| `semiconductor-operations` | semiconductors, manufacturing | 4 | palantir-semiconductors, palantir-manufacturing |
| `space-edge-operations` | space | 4 | palantir-metaconstellation, palantir-apollo-environments |
| `supply-chain-logistics` | supply_chain, logistics | 4 | palantir-consumer-goods, palantir-retail |
| `telecommunications-operations` | telecommunications, telecom | 4 | palantir-telecommunications |

## Canonical primitive templates

| Template | Layer | Operation | Contract | Determinism | Oracle |
|---|---|---|---|---|---|
| `agent-action-policy` | ai | authorize | `ToolIntentActorScopeAndPolicy -> ToolDecision` | deterministic | security |
| `allocation-engine` | analytics | allocate | `SupplyDemandAndConstraints -> AllocationPlan` | deterministic_or_seeded | optimization |
| `anomaly-signal-builder` | analytics | detect | `ObservationsAndThresholdPolicy -> AnomalySignals` | deterministic_or_model_wrapped | held-out |
| `approval-gate` | workflow | approve | `ActionIntentActorAndPolicy -> ApprovalDecision` | deterministic | security |
| `attribute-policy-gate` | governance | authorize | `ActorResourceAttributesAndPolicy -> AccessDecision` | deterministic | security |
| `audit-event-emitter` | governance | record | `ActionTrace -> AuditEvent` | deterministic | receipt |
| `bottleneck-ranker` | process | rank | `ProcessGraphAndDurations -> RankedBottlenecks` | deterministic | property |
| `canary-health-gate` | runtime | gate | `CanaryMetricsAndPolicy -> PromoteHoldOrRecall` | deterministic | fault-injection |
| `case-state-machine` | workflow | transition | `CaseStateEventAndPolicy -> NewCaseStateReceipt` | deterministic | stateful |
| `cdc-watermark` | data | checkpoint | `ChangeBatch -> WatermarkReceipt` | deterministic | stateful |
| `citation-span-verifier` | ai | verify | `ClaimCitationAndSourceSpan -> CitationVerdict` | deterministic_or_model_wrapped | held-out |
| `config-drift-detector` | runtime | detect | `ExpectedAndObservedConfig -> ConfigDriftReport` | deterministic | mutation |
| `conformance-checker` | process | compare | `ObservedAndExpectedProcess -> ConformanceReport` | deterministic | mutation |
| `connector-probe` | data | probe | `ConnectorConfig -> ConnectorCapabilityReceipt` | deterministic | contract |
| `constraint-feasibility-checker` | analytics | validate | `CandidatePlanAndConstraints -> FeasibilityReport` | deterministic | optimization |
| `context-budgeter` | ai | select | `EvidenceSetAndBudget -> BoundedContextPack` | deterministic_or_scored | property |
| `cost-per-pass-calculator` | runtime | calculate | `UsageCostsAndOracleResults -> CostPerPassReceipt` | deterministic | property |
| `credential-scope-check` | data | authorize | `CredentialIntent -> CredentialScopeDecision` | deterministic | security |
| `decision-receipt` | workflow | record | `DecisionActorEvidenceAndPolicy -> ImmutableDecisionReceipt` | deterministic | receipt |
| `desired-state-diff` | runtime | compare | `DesiredAndReportedState -> DeploymentDiff` | deterministic | mutation |
| `digital-twin-snapshot` | ontology | snapshot | `ObjectGraph -> VersionedTwinSnapshot` | deterministic | replay |
| `digital-twin-state-reducer` | ontology | reduce | `OrderedEvents -> ObjectState` | deterministic | stateful |
| `disconnected-edge-sync` | runtime | synchronize | `LocalRemoteStateAndConflictPolicy -> ReconciledStateReceipt` | deterministic | fault-injection |
| `entity-identity-resolver` | identity | resolve | `EntityCandidates -> IdentityResolution` | deterministic_or_scored | held-out |
| `environment-selector` | runtime | select | `TaskPolicyAndAvailableBackends -> EnvironmentDecision` | deterministic | truth-table |
| `eval-case-runner` | ai | evaluate | `CandidateAndHeldOutCases -> EvalReceipt` | deterministic_or_model_wrapped | mutation |
| `event-deduplicator` | data | deduplicate | `EventBatch -> UniqueEventBatch` | deterministic | property |
| `event-log-normalizer` | process | normalize | `HeterogeneousEventLogs -> CanonicalProcessEvents` | deterministic | contract |
| `evidence-gap-router` | ai | route | `ClaimAndEvidenceVerdict -> RefusalReviewOrSearchAction` | deterministic | truth-table |
| `exception-escalator` | workflow | escalate | `FailureAndEscalationPolicy -> EscalationReceipt` | deterministic | stateful |
| `feedback-capture` | ai | capture | `DecisionOutcomeAndCorrection -> VersionedFeedbackReceipt` | deterministic | receipt |
| `field-mapper` | quality | map | `SourceRecordAndMapping -> CanonicalRecord` | deterministic | contract |
| `forecast-wrapper` | analytics | forecast | `FeaturesModelAndHorizon -> ForecastWithIntervals` | model_wrapped | ml |
| `freshness-gate` | governance | verify | `FactDatesAndFreshnessPolicy -> FreshStaleOrReviewDecision` | deterministic | boundary |
| `governed-retriever` | ai | retrieve | `QueryScopeAndPermissions -> RankedEvidenceSet` | deterministic_or_scored | held-out |
| `graph-reachability` | ontology | traverse | `GraphAndTraversalPolicy -> ReachableObjectSet` | deterministic | graph |
| `human-review-packet` | workflow | assemble | `EvidenceDecisionOptionsAndGaps -> ReviewPacket` | deterministic | receipt |
| `idempotency-gate` | workflow | deduplicate | `ActionIntentAndKey -> NewOrReplayDecision` | deterministic | stateful |
| `incremental-sync` | data | synchronize | `SourceDelta -> CanonicalDelta` | deterministic | integration |
| `lineage-propagator` | identity | trace | `TransformReceiptSet -> LineageGraph` | deterministic | graph |
| `link-type-validator` | ontology | validate | `TypedObjectGraph -> LinkValidationReport` | deterministic | graph |
| `metric-calculator` | analytics | calculate | `TypedFactsAndMetricSpec -> MetricValueReceipt` | deterministic | property |
| `model-route-policy` | ai | route | `TaskRiskCostAndCapability -> ModelRouteDecision` | deterministic | truth-table |
| `notification-router` | workflow | notify | `EventRecipientsAndPolicy -> NotificationIntent` | deterministic | integration |
| `object-change-event` | ontology | emit | `ObjectStateDiff -> ChangeEvent` | deterministic | receipt |
| `object-mapper` | ontology | materialize | `CanonicalRecord -> ObjectProjection` | deterministic | contract |
| `optimizer-adapter` | analytics | optimize | `DecisionVariablesConstraintsObjective -> CandidatePlan` | deterministic_or_seeded | optimization |
| `prioritization-ranker` | analytics | rank | `WorkItemsAndPolicy -> RankedWorkItems` | deterministic_or_model_wrapped | held-out |
| `process-graph-miner` | process | mine | `CanonicalProcessEvents -> ProcessGraph` | deterministic | graph |
| `process-simulator` | process | simulate | `ProcessGraphResourcesAndScenario -> ProcessScenarioReceipt` | deterministic_or_seeded | replay |
| `purpose-limit-gate` | governance | authorize | `PurposeDataAndPolicy -> PurposeDecision` | deterministic | security |
| `quarantine-router` | quality | route | `ValidationResult -> AcceptedAndQuarantinedRows` | deterministic | stateful |
| `raw-landing-receipt` | data | preserve | `RawArtifact -> RawArtifactReceipt` | deterministic | receipt |
| `rbac-gate` | governance | authorize | `ActorRoleResourceAndAction -> AccessDecision` | deterministic | security |
| `reconciliation-engine` | analytics | reconcile | `LeftRightAndMatchPolicy -> MatchedAndUnmatchedSets` | deterministic | property |
| `record-linker` | identity | link | `CanonicalRecords -> RecordLinks` | deterministic_or_scored | held-out |
| `reference-integrity-checker` | quality | validate | `RecordGraph -> IntegrityReport` | deterministic | mutation |
| `regression-gate` | ai | gate | `BaselineCandidateAndMetrics -> PromotionOrHoldDecision` | deterministic | mutation |
| `release-channel-resolver` | runtime | route | `ArtifactEnvironmentAndChannelPolicy -> ReleaseDecision` | deterministic | truth-table |
| `retention-enforcer` | governance | retain-or-expire | `RecordDatesAndPolicy -> RetentionActionReceipt` | deterministic | boundary |
| `rollback-controller` | runtime | rollback | `FailedReleaseAndPriorState -> RollbackReceipt` | deterministic | integration |
| `root-cause-traversal` | analytics | explain | `SignalAndDependencyGraph -> RankedCausePaths` | deterministic_or_scored | graph |
| `route-cost-evaluator` | analytics | route | `NetworkDemandAndConstraints -> RoutePlanAndCost` | deterministic_or_seeded | optimization |
| `row-column-policy-filter` | governance | filter | `QueryActorAndPolicy -> AuthorizedProjection` | deterministic | security |
| `scenario-runner` | analytics | simulate | `BaselineAndScenarioInputs -> ScenarioComparison` | deterministic_or_seeded | replay |
| `schedule-feasibility` | analytics | schedule | `ResourcesTasksAndConstraints -> FeasibleScheduleOrConflict` | deterministic_or_seeded | optimization |
| `schema-drift-detector` | data | compare | `SchemaPair -> SchemaDriftReport` | deterministic | mutation |
| `schema-snapshot` | data | snapshot | `SourceSchema -> VersionedSchemaSnapshot` | deterministic | contract |
| `schema-validator` | quality | validate | `RecordAndSchema -> ValidationResult` | deterministic | mutation |
| `sensitive-data-redactor` | governance | redact | `RecordAndPrivacyPolicy -> RedactedRecordAndReceipt` | deterministic_or_model_wrapped | security |
| `separation-of-duties-gate` | workflow | authorize | `ActorHistoryAndPolicy -> AuthorizationDecision` | deterministic | security |
| `sla-deadline-monitor` | workflow | monitor | `DatedWorkItemsAndClock -> DeadlineSignals` | deterministic | boundary |
| `source-authority-gate` | governance | verify | `SourceIdentityScopeAndEvidence -> AuthorityDecision` | deterministic | truth-table |
| `source-health-check` | data | inspect | `SourceEndpoint -> SourceHealthReceipt` | deterministic | integration |
| `structured-output-validator` | ai | validate | `ModelOutputAndSchema -> ValidatedOutputOrErrors` | deterministic | mutation |
| `temporal-validity-resolver` | identity | resolve | `DatedFacts -> PointInTimeFacts` | deterministic | boundary |
| `token-meter` | runtime | meter | `ProviderUsageReceipt -> NormalizedUsageReceipt` | deterministic | receipt |
| `trace-context-propagator` | runtime | propagate | `ParentTraceAndOperation -> ChildTraceContext` | deterministic | receipt |
| `transactional-outbox` | workflow | dispatch | `CommittedChange -> DeliveryIntentReceipt` | deterministic | fault-injection |
| `transactional-writeback` | workflow | write | `AuthorizedObjectChanges -> TransactionReceipt` | deterministic | integration |
| `type-coercer` | quality | coerce | `TypedValueIntent -> TypedValueOrError` | deterministic | property |
| `unit-normalizer` | quality | normalize | `Measurement -> CanonicalMeasurement` | deterministic | property |
| `work-queue-router` | workflow | route | `WorkItemAndRoutingPolicy -> QueueAssignmentReceipt` | deterministic_or_scored | stateful |

## Project proof path

Each workflow maps to an O5-or-stronger project seed. The implementation path is:

```text
public source metadata
  -> generic workflow candidate
  -> canonical primitive composition
  -> starter repo + hidden oracle
  -> known-good / known-bad / mutation validation
  -> harness-alone vs primitive-assisted execution
  -> project_run_receipt
```

High-risk healthcare, government, finance, defense, energy, and space workflows require explicit human
authority. The source policy excludes insurance expansion and autonomous lethal targeting, unreviewed
clinical decisions, unreviewed public-benefit decisions, and covert-surveillance decisions.

## Source registry

- [Army financial-management use of Vantage](https://www.army.mil/article/254210/) — class A; government.
- [NIH N3C frequently asked questions](https://ncats.nih.gov/research/research-activities/n3c/faqs) — class A; government.
- [Action types overview](https://www.palantir.com/docs/foundry/action-types/overview) — class B; vendor_technical_docs.
- [AIP Evals](https://www.palantir.com/docs/foundry/aip-evals/overview) — class B; vendor_technical_docs.
- [AIP Logic](https://www.palantir.com/docs/foundry/logic) — class B; vendor_technical_docs.
- [AIP retrieval context](https://www.palantir.com/docs/foundry/chatbot-studio/retrieval-context) — class B; vendor_technical_docs.
- [Airbus and Skywise impact page](https://www.palantir.com/impact/airbus/) — class C; vendor_customer_page.
- [Anti-money laundering offering](https://www.palantir.com/offerings/anti-money-laundering/) — class C; vendor_offering_page.
- [Apollo environments](https://www.palantir.com/docs/apollo/core/environments) — class B; vendor_technical_docs.
- [Automate](https://www.palantir.com/docs/foundry/automate) — class B; vendor_technical_docs.
- [Automotive and mobility offering](https://www.palantir.com/offerings/automotive-mobility/) — class C; vendor_offering_page.
- [Construction offering](https://www.palantir.com/offerings/construction/) — class C; vendor_offering_page.
- [Consumer goods offering](https://www.palantir.com/offerings/consumer-goods) — class C; vendor_offering_page.
- [Data integration overview](https://www.palantir.com/docs/foundry/data-integration/overview) — class B; vendor_technical_docs.
- [Defense and Navy offering](https://www.palantir.com/offerings/defense/navy/) — class C; vendor_offering_page.
- [Energy offering](https://www.palantir.com/offerings/energy) — class C; vendor_offering_page.
- [Financial services offering](https://www.palantir.com/offerings/financial-services/) — class C; vendor_offering_page.
- [Food and beverage offering](https://www.palantir.com/offerings/food-and-beverage/) — class C; vendor_offering_page.
- [Gotham platform](https://www.palantir.com/platforms/gotham/) — class B; vendor_technical_docs.
- [Health and life sciences offering](https://www.palantir.com/offerings/health/) — class C; vendor_offering_page.
- [Hospitals offering](https://www.palantir.com/offerings/palantir-for-hospitals/) — class C; vendor_offering_page.
- [Manufacturing offering](https://www.palantir.com/explore/foundry-for-manufacturing/) — class C; vendor_offering_page.
- [MetaConstellation offering](https://www.palantir.com/offerings/metaconstellation) — class C; vendor_offering_page.
- [Model integration](https://www.palantir.com/docs/foundry/model-integration/overview/index.html) — class B; vendor_technical_docs.
- [Observability overview](https://www.palantir.com/docs/foundry/observability/overview) — class B; vendor_technical_docs.
- [Public offerings index](https://www.palantir.com/offerings/) — class C; vendor_offering_page.
- [Ontology system](https://www.palantir.com/docs/foundry/architecture-center/ontology-system) — class B; vendor_technical_docs.
- [AIP Foundry and Apollo architecture](https://www.palantir.com/docs/foundry/architecture-center/platforms) — class B; vendor_technical_docs.
- [Process mining and automation](https://www.palantir.com/platforms/foundry/process-mining/) — class B; vendor_technical_docs.
- [Procurement offering](https://www.palantir.com/offerings/procurement/) — class C; vendor_offering_page.
- [Rail offering](https://www.palantir.com/offerings/palantir-for-rail/) — class C; vendor_offering_page.
- [Readiness offering](https://www.palantir.com/offerings/readiness/) — class C; vendor_offering_page.
- [Retail offering](https://www.palantir.com/offerings/retail/) — class C; vendor_offering_page.
- [Security overview](https://www.palantir.com/docs/foundry/security/overview) — class B; vendor_technical_docs.
- [Semiconductor overview](https://www.palantir.com/offerings/semiconductors/) — class C; vendor_offering_page.
- [Telecommunications offering](https://www.palantir.com/offerings/telecommunications/) — class C; vendor_offering_page.
- [United Kingdom government page](https://www.palantir.com/uk/government/) — class C; vendor_customer_page.
- [Palantir 2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1321655/000132165526000011/pltr-20251231.htm) — class A; regulator_filing.
- [World Food Programme partnership](https://www.wfp.org/news/palantir-and-wfp-partner-help-transform-global-humanitarian-delivery) — class A; intergovernmental_organization.
