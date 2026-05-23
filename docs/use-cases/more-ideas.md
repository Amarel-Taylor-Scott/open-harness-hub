# More use cases - ideation roundup

> Grounded in production-repo ports + landscape research, plus
> brainstorm from the broader landscape. Each row is a future
> `docs/use-cases/<slug>.md` recipe.

The original 8 (in this directory):
**qa-on-documents** · **code-review** · **deep-research** · **customer-support** · **clinical-decision-support** · **aml-screening** · **image-gen** · **llm-red-team**

Below: **30 additional** use cases organized by category. Each has:
the proposed slug, the primary pipeline shape (existing or planned),
and evidence from real-world sources.

## A. AI-system-engineering (fine-tune / eval / data)

| # | Slug | What | Evidence |
|---|---|---|---|
| 1 | `lora-qlora-pairwise-pref-finetune` | Fine-tune Gemma-2-9b-4bit with QLoRA on pairwise-preference triples. Outputs a LoRA adapter. | **Verified Kaggle pattern** - 3 of 9 top WSDM-Cup Multilingual Chatbot Arena kernels |
| 2 | `tfidf-lightgbm-text-classification` | Char-ngram TF-IDF → SGD+LightGBM stack → calibrated probability. The non-LLM baseline that wins many Kaggle text comps. | **Verified** - top kernels of LLM-Detect-AI-Generated-Text |
| 3 | `deberta-finetune-classification` | DeBERTa-v3-large fine-tune for closed-set classification. Often layered on TF-IDF baseline. | **Verified** - top kernels across LLM classification comps |
| 4 | `model-arm-benchmark` | Run baseline / harnessed / fine-tuned / fine-tuned+harnessed arms; combined rule+LLM grading; comparison report. | _reference/gemma4_comp A-00 |
| 5 | `synthetic-sft-dpo-gen` | Use a teacher LLM to synthesize (input, output) training rows; rubric-polish for the response contract. | DSPy + DueCare A-00 + RLAIF |
| 6 | `rubric-driven-llm-judge` | Score outputs against a multi-dimension rubric with a frontier judge model. | Anthropic + DeepEval + Ragas |
| 7 | `regression-test-eval-suite` | Run a fixed test set against new model version; fail if regression > threshold on any rubric dim. | Promptfoo + LangSmith |

## B. Document understanding (extract / classify / summarize)

| # | Slug | What | Evidence |
|---|---|---|---|
| 8 | `long-doc-map-reduce-summary` | Chunk → per-chunk summary → reduce → critic-refine. The canonical long-doc summarization shape. | LangChain MapReduceDocumentsChain |
| 9 | `contract-clause-extract-and-flag` | Pull standard clauses (force majeure, IP, termination) from a contract; flag missing or unusual ones. | Legal-tech industry standard |
| 10 | `meeting-transcript-actions-decisions` | Whisper STT → diarize → map-reduce summarize → extract decisions + action items + owners. | Anthropic cookbook + dozens of OSS impls |
| 11 | `pdf-table-and-figure-qa` | OCR/layout → table extract → image caption → multimodal QA over text+tables+figures. | RAGFlow + Unstructured |
| 12 | `knowledge-graph-from-corpus` | Extract entities + relationships from documents into a graph; query via Cypher/SPARQL. | microsoft/graphrag (cloned + verified) |
| 13 | `voice-of-customer-themes` | Cluster reviews into themes with sentiment, aspect, and representative quotes per theme. | Standard retail / B2B-product pattern |
| 14 | `news-event-extraction` | From news streams: extract events with (who, what, where, when, why) + dedupe across sources. | OEEC + NewsHunt |
| 15 | `scientific-literature-survey` | Given a research question, build a literature survey across N papers with citation graph + accept/reject per paper. | STORM + Elicit |

## C. Agentic / multi-step

| # | Slug | What | Evidence |
|---|---|---|---|
| 16 | `code-act-jupyter-loop` | LLM emits code → exec in sandbox → observe → iterate until done. | OpenInterpreter (cloned + verified) |
| 17 | `swe-patch-sample-and-review` | Sample N action-rollouts → compile+test → reviewer judges → emit best patch. | princeton-nlp/SWE-agent (cloned + verified) |
| 18 | `plan-and-execute-with-critic` | Planner LLM drafts steps → executor model + tools → critic re-plans on failure. | langgraph examples (cloned + verified) |
| 19 | `multi-agent-debate-with-judge` | 2-3 persona agents argue; judge LLM scores final positions; verdict + transcripts. | microsoft/autogen (cloned + verified) |
| 20 | `storm-persona-curation-article` | Generate personas → simulated dialogue curation → outline → section-fanout → polish. | stanford-oval/storm |
| 21 | `web-action-observe-act-verify` | Browser automation: observe DOM → propose action → act → verify; loop. | browserbase/stagehand + OpenHands |
| 22 | `deep-research-supervisor-workers` | Clarify → brief → supervisor fans out N parallel researchers → compress → write report. | langchain-ai/open_deep_research (cloned) |
| 23 | `self-rag-grade-and-revise` | Retrieve → grade docs → rewrite query → retry; generate → grade answer support → revise. | AkariAsai/self-rag (cloned + verified) |
| 24 | `corrective-rag-tri-state-with-web-fallback` | Retrieve → evaluator (correct/incorrect/ambiguous) → refine or web-fallback → answer. | CRAG paper + Ollama impl (cloned) |

## D. Creative / content gen

| # | Slug | What | Evidence |
|---|---|---|---|
| 25 | `cinematic-storyboard-generation` | Outline → per-scene description → image gen per scene with consistent style → stitch. | Hollywood / agency workflow |
| 26 | `brand-voice-marketing-copy` | Brief + brand guidelines → draft variants → A/B with style metrics → top-N. | Marketing-tech |
| 27 | `educational-curriculum-builder` | Subject + age + duration → lesson plan with objectives, activities, assessments, references. | EdTech pattern |
| 28 | `voice-narration-with-tts` | Markdown script → SSML → TTS → audio file with timing markers. | Anthropic / OpenAI patterns |
| 29 | `data-story-from-spreadsheet` | CSV/Parquet → schema inference → narrative summary + 3 key visualizations → markdown report. | Code-act + Snowflake Cortex Code |

## E. Operations / business intelligence

| # | Slug | What | Evidence |
|---|---|---|---|
| 30 | `sales-outreach-personalization` | Lead record + company news → tailored opener + CTA + 3 talking points; output schema verified. | Industry standard |
| 31 | `competitive-intel-watch` | Daily: search → official-source verify → diff vs yesterday → email digest of changes. | Crayon / Klue pattern |
| 32 | `incident-postmortem-drafter` | Logs + chat transcripts → root cause hypothesis + timeline + action items + lessons. | Anthropic + DevOps standard |
| 33 | `vendor-due-diligence` | Company name → public-records + sanctions + news + financial signals → risk score + flags. | AML-adjacent |
| 34 | `compliance-policy-mapper` | Internal policies → mapping to GDPR / HIPAA / SOC-2 / ISO-42001 / EU AI Act articles. | Vanta / Drata pattern |

## F. Specialized verticals

| # | Slug | What | Evidence |
|---|---|---|---|
| 35 | `radiology-report-draft` | Image + history → structured findings + impression + recommendations (cited). PHI-safe. | Healthcare AI standard |
| 36 | `code-security-scan-with-fix` | Diff → 4 secret-grep packs + Semgrep + OWASP RAG → findings with risk score + fix PR. | Snyk / Socket pattern |
| 37 | `prior-art-patent-search` | Invention disclosure → semantic search USPTO + PCT → ranked prior art + claim-overlap analysis. | LegalTech |
| 38 | `clinical-trial-eligibility-match` | Patient record → trial inclusion/exclusion criteria → match probability + missing-data flags. | Healthcare AI / pharma |

---

## Priority sequencing (next batches)

**Highest value (real-evidence-backed)**:
1. `pipeline/lora-qlora-pairwise-pref-finetune` (verified WSDM-Cup)
2. `pipeline/tfidf-lightgbm-text-classification` (verified Kaggle pattern)
3. `pipeline/deberta-finetune-classification` (verified)
4. `pipeline/model-arm-benchmark` (verified in _reference)
5. `pipeline/swe-patch-sample-and-review` (verified clone)
6. `pipeline/self-rag-grade-and-revise` (verified clone)
7. `pipeline/code-act-jupyter-loop` (verified clone)
8. `pipeline/storm-persona-curation-article` (verified)
9. `pipeline/deep-research-supervisor-workers` (verified clone)
10. `pipeline/knowledge-graph-from-corpus` (verified clone - graphrag)

**Strong-signal (next candidates)**:
11. `pipeline/long-doc-map-reduce-summary`
12. `pipeline/meeting-transcript-actions-decisions`
13. `pipeline/synthetic-sft-dpo-gen`
14. `pipeline/rubric-driven-llm-judge`
15. `pipeline/multi-agent-debate-with-judge`

**Verticalize after the 15 above** (radiology, contract-clause, etc.).

## Going broader - methodology

For each future use case, the recipe should answer:

1. **Goal** (one sentence)
2. **Inputs** + **outputs** (typed)
3. **Primary pipeline** (existing or planned slug)
4. **Primitives used** (table mapping each layer to an artifact in the catalog)
5. **Composition diagram** (the persona → grep → rag → tool → harness chain)
6. **Sample inputs / outputs**
7. **Install path** (Claude Code marketplace command, direct skill drop, or run-pipeline command)
8. **Customization knobs**
9. **Verifier / rubric** (which `rubric/*` to use as success criterion)
10. **Known risks / gotchas**

When all 38+ recipes are written, the use-cases section becomes the
"recipes" answer to "what can I build with this hub?"
