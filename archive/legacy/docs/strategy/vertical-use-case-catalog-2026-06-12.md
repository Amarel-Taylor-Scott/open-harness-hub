# Vertical use-case catalog — capability-gap negative space (2026-06-12)

Twenty-nine vertical use cases across three domain clusters, each built for the **negative
space** (where a bare frontier model fails STRUCTURALLY — freshness, aggregation,
jurisdiction, precedence, provability, coded vocabularies, low-resource languages, offline
constraints — not transient gaps the next model closes). Every pipeline composes only the
**real** processor method-components (`scripts/processors/**`); four are proven runnable
end-to-end in `scripts/showcase_pipelines/` and cross-linked below. Durability labels map to
`scripts/eval/reason_codes.py` (the single source of the lift taxonomy).

**The shared law:** every pipeline ends at a gate that **proposes, never disposes** — it
serves an answer only when each fact carries a live source handle within its effective
window, and otherwise abstains or escalates. Clinical/edge pipelines additionally pin
`serves_truth=False` and are decision-SUPPORT only (never autonomous).

---

## Cluster A — Regulated / Compliance (durability: jurisdiction x4, aggregation x3, precedence x2, freshness x2, provability x2)

| # | Use case / Who | Negative-space gap (why STRUCTURAL) | Pipeline (real processor ids) | Durability |
|---|---|---|---|---|
| A1 | **Sanctions/AML ownership screening** / KYC ops | OFAC 50% Rule = aggregate ownership of *unlisted* entities; daily delta lists | exact-id-lookup -> fuzzy-trigram-retrieve -> simhash-dedupe -> graphrag-retrieve -> cross-encoder-reranker -> source-precedence-select -> escalate-human -> deliver-report | aggregation |
| A2 | **State usury / rate caps** / lending legal | cap varies by state x loan-type x band, changes by statute | bm25 -> dense -> rrf-fusion -> page-aware-chunker -> extractive-span-selector -> source-precedence-select -> deliver-report | jurisdiction -> **`regulated_fact_qa.py`** |
| A3 | **Tax threshold / nexus** / tax ops | economic-nexus thresholds revised yearly, jurisdiction-specific | exact-id-lookup -> hybrid-retrieve-fuse -> cross-encoder-reranker -> extractive-span-selector -> memory-confidence-track -> deliver-report | freshness |
| A4 | **Securities filings monitoring** / IR | 5% disclosure crossings via aggregation across serial filings | bm25 -> dense -> hybrid-retrieve-fuse -> recursive-character-chunker -> cross-encoder-reranker -> memory-temporal-graph -> deliver-webhook | aggregation |
| A5 | **EU AI Act / GDPR obligations** / AI governance | obligation = risk-tier x role x Article, phased dates, Recital interplay | dense -> graphrag-retrieve -> mmr-diversity-select -> source-precedence-select -> extractive-span-selector -> deliver-report | precedence |
| A6 | **Gov procurement eligibility** / capture | FAR + agency supplements + flow-downs, hierarchical + amended | exact-id-lookup -> bm25 -> rrf-fusion -> page-aware-chunker -> source-precedence-select -> extractive-span-selector -> escalate-human | precedence |
| A7 | **Export controls (ECCN)** / trade compliance | CCL x Country Chart x Entity List combine multiplicatively | dense -> hybrid-retrieve-fuse -> cross-encoder-reranker -> exact-id-lookup -> source-precedence-select -> escalate-human -> deliver-report | jurisdiction |
| A8 | **Employment law by jurisdiction** / HR ops | min-wage/overtime/leave differ by locality; locality preempts state | bm25 -> dense -> rrf-fusion -> extractive-span-selector -> source-precedence-select -> deliver-report | jurisdiction |
| A9 | **Beneficial ownership (CTA/UBO)** / AML onboarding | 25% control via indirect holdings across entity layers | exact-id-lookup -> graphrag-retrieve -> simhash-dedupe -> cross-encoder-reranker -> memory-distilled-write -> escalate-human | provability |

---

## Cluster B — Engineering / Security / Data (durability: codebase-specificity, freshness, exactness, provability)

| # | Use case / Who | Negative-space gap (why STRUCTURAL) | Pipeline (real processor ids) | Durability |
|---|---|---|---|---|
| B1 | **CVE / dependency triage** / AppSec | CVE/KEV feeds change daily; exact version-range match, not recall | mcp-gitlab-connector -> exact-id-lookup -> hybrid-retrieve-fuse -> rrf-fusion -> cross-encoder-reranker -> source-precedence-select -> deliver-report -> escalate-human | freshness + exactness |
| B2 | **Code review vs codebase conventions** / reviewers | THIS repo's rules live only in the code, never in pretraining | mcp-gitlab-connector -> grep-agentic-retrieve -> structural-compress -> cross-encoder-reranker -> system-prompt-builder -> emit-claudemd-fragment -> deliver-webhook | codebase-specificity |
| B3 | **API-migration assistant** / upgraders | post-cutoff API surfaces; models invent removed methods | exact-id-lookup -> page-aware-chunker -> dense -> rrf-fusion -> extractive-span-selector -> source-precedence-select -> deliver-report | freshness + exactness |
| B4 | **Incident runbook retrieval** / on-call SRE | runbooks private + change constantly; generic remediation dangerous | mcp-confluence-connector -> cache-semantic -> bm25 -> hybrid-retrieve-fuse -> cross-encoder-reranker -> deliver-webhook -> escalate-human | freshness + codebase-specificity |
| B5 | **Secure-code gen w/ injection screen** / developers | models follow injected instructions in retrieved snippets | dense -> prompt-injection-screen -> extractive-span-selector -> system-prompt-builder -> json-repair-coerce -> deliver-report | provability |
| B6 | **IaC policy compliance** / platform-gov | org-specific Terraform/K8s policy not pretrained | mcp-gitlab-connector -> exact-id-lookup -> graphrag-retrieve -> source-precedence-select -> deliver-report -> escalate-human | provability + codebase-specificity |
| B7 | **Internal-docs Q&A** / any engineer | closed-channel private knowledge (no addressable source) | mcp-confluence-connector + mcp-gitlab-connector -> recursive-character-chunker -> hybrid-retrieve-fuse -> rrf-fusion -> cross-encoder-reranker -> memory-confidence-track -> serve-mcp-corpus | codebase-specificity |
| B8 | **SQL over governed schema** / analysts | models invent table/column names; hallucinated SQL silently wrong | mcp-postgres-connector -> exact-id-lookup -> dense -> source-precedence-select -> system-prompt-builder -> json-repair-coerce -> deliver-report | exactness + provability |
| B9 | **License-compliance audit** / OSS-compliance | SPDX<->dependency mapping is exact + legally accountable | mcp-gitlab-connector -> exact-id-lookup -> simhash-dedupe -> source-precedence-select -> deliver-report -> escalate-human | exactness + provability |
| B10 | **Large-repo context compression** / any agent | stateless transformers re-pay full prefill for every file every turn | mcp-gitlab-connector -> grep-agentic-retrieve -> **structural-compress** -> **usage-gated-compress** -> cache-prompt-prefix + cache-kv-reuse -> system-prompt-builder -> emit-llms-txt | codebase-specificity + **efficiency moat** |

B10 is the through-line to the active context-efficiency thread
(`docs/concepts/prediction-error-gated-context.md`): structural-compress strips token-heavy
bodies (structure-lossless), then usage-gated-compress spends fidelity only where prediction
fails. The re-read cost never disappears as models improve — an efficiency moat, not a
knowledge gap.

---

## Cluster C — Healthcare / Public-sector / Multilingual-edge (DEFENSIVE: propose/escalate, serves_truth=False)

| # | Use case / Who | Negative-space gap (why STRUCTURAL) | Pipeline (real processor ids) | Durability |
|---|---|---|---|---|
| C1 | **Drug-interaction & dosing co-pilot** / pharmacists | governed versioned interaction DB + ranges, not parametric recall | exact-id-lookup -> drug-interaction-checker -> dosage-range-validator -> allergy-contraindication-check -> clinical-abstention-gate -> escalate-human | governed-reference -> **`clinical_support.py`** |
| C2 | **Lab critical-value flag** / ED triage | numeric panic thresholds; deterministic escalation guarantee | faithful-extract-before-model -> lab-critical-value-flag -> dosage-range-validator -> clinical-redflag-screen -> escalate-human -> deliver-notify | governed-reference |
| C3 | **Red-flag symptom screen + abstain** / nurse-line | bare models over-reassure; value = deterministic abstain/escalate | clinical-redflag-screen -> clinical-abstention-gate -> source-precedence-select -> escalate-human -> deliver-report | abstention |
| C4 | **ICD-10 coding assistant** / coders | coded vocabulary — fluency gives zero signal; plausible wrong = liability | soap-note-structurer -> extractive-span-selector -> icd10-code-grounder -> exact-id-lookup -> clinical-abstention-gate -> escalate-human | governed-reference |
| C5 | **SOAP note structuring** / clinicians | faithful extraction into a rigid schema, no fabrication | faithful-extract-before-model -> soap-note-structurer -> template-field-gem -> structured-json-fence-guard -> clinical-abstention-gate -> escalate-human | provability |
| C6 | **Disaster-alert radio scripts (Waray/Ilocano)** / DRRM | low-resource language + volatile official advisories | source-precedence-select -> faithful-extract-before-model -> english-pivot-translation -> language-lock -> tts-preprocess-low-resource -> escalate-human -> deliver-notify | low-resource -> **`low_resource_alert.py`** |
| C7 | **Offline field health-worker assistant** / CHWs | no connectivity + deterministic safety gates | offline-fallback-gate -> on-device-smart-router -> clinical-redflag-screen -> dosage-range-validator -> clinical-abstention-gate -> offline-queue-sync-on-reconnect -> escalate-human | offline |
| C8 | **On-device form OCR (low-connectivity)** / enumerators | scanned forms = inaccessible channel; offline + faithful extract | on-device-ocr-prepass -> faithful-extract-before-model -> template-field-gem -> structured-json-fence-guard -> offline-queue-sync-on-reconnect -> escalate-human | offline |
| C9 | **Gov advisory translation (English-pivot)** / PIOs | direct low<->low translation degrades; advisories volatile | source-precedence-select -> faithful-extract-before-model -> english-pivot-translation -> language-lock -> prompt-injection-screen -> escalate-human -> deliver-report | low-resource |
| C10 | **On-device tutoring from curriculum PDFs** / students | offline + faithful grounding in governed curriculum | doc-to-markdown-rag-ingest -> curriculum-qa-dataset-builder -> offline-fallback-gate -> on-device-smart-router -> faithful-extract-before-model -> sm2-spaced-repetition-scheduler -> escalate-human | offline |

---

## How to read this catalog

- **It is a demand map, not a build list.** Each row is a real buyer with a structural gap;
  the pipeline is the governed answer composed from components that already exist.
- **Four rows are runnable today** (`scripts/showcase_pipelines/`): A2 (regulated_fact_qa),
  the governed-RAG default, C1 (clinical_support), C6 (low_resource_alert) — they prove the
  components compose end-to-end with the model as the only simulated seam.
- **Sequence behind the proof point.** The beachhead is regulated-fact context (Cluster A);
  Clusters B and C are the expansion once the proof lands. Avoid insurance (repo policy);
  store no real PII (synthetic/public only).
- **The gap is the moat.** Every durability class here is structural — it will not close
  when the next base model ships. That is the capability-gap framework's whole bet.
