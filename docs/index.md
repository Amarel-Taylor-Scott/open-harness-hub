# Open Harness Hub - single-page catalog index

Auto-generated from `scripts/build_index_page.py` against 505 live artifacts. Run that script to refresh after any catalog change.

Use `python scripts/oh_hub.py describe <id>` for the full manifest + dependency tree of any entry below.

## Stats

- **Total artifacts:** 505
- **Artifact types:** 12
- **Industries:** 142

## Table of contents

- [harness (13)](#harness)
- [pipeline (108)](#pipeline)
- [benchmark (1)](#benchmark)
- [rule-pack (55)](#rule-pack)
- [knowledge-pack (56)](#knowledge-pack)
- [tool (14)](#tool)
- [persona (51)](#persona)
- [adapter (17)](#adapter)
- [rubric (45)](#rubric)
- [dataset (36)](#dataset)
- [processor (60)](#processor)
- [pattern (49)](#pattern)

## harness

- **`harness/aml-investigation`** - AML Investigation  
  _finance, finance.aml_ • Harness for AML suspicious-transaction review. Composes the AML-analyst persona, sanctions-screening heuristic, FATF-typology classifier, financial-PII privacy gate, FATF-typology …
- **`harness/appsec-code-audit`** - AppSec Code Audit harness  
  _security, security.appsec, software_ • CWE-cite-first AppSec audit harness for source-code review. Detects secrets-in-code + injection + crypto/auth weaknesses + describes attack vectors + proposes fixes.
- **`harness/chat-with-memory`** - Persistent chat with memory (multi-turn, preference-aware)  
  _personal_productivity, cross_industry_ • Multi-turn chat harness with persistent memory across sessions. Loads user preferences, recalls prior conversation context, and honors the user's stated rules (don't reveal X, alwa…
- **`harness/clinical-decision-support`** - Clinical Decision Support  
  _healthcare, healthcare.clinical_ • Healthcare-specific harness for differential-diagnosis reasoning. Composes the clinical-reasoner persona, red-flag classifier rules, HIPAA PHI privacy gate, clinical-guideline RAG,…
- **`harness/code-act-jupyter`** - Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)  
  _ai, scientific_research, education_ • Harness that wraps a model call with a Python execution loop. The model emits `<code>...</code>` blocks; the harness runs them in a sandboxed Jupyter kernel; stdout / stderr / repr…
- **`harness/contract-redline`** - Contract Clause Redlining harness  
  _legal, legal.contract, legal.compliance_ • Playbook-cite-first harness for commercial contract review. Surfaces red-flag clauses + proposes concrete redline language + cites the playbook clause family for every finding.
- **`harness/data-cleaning-and-enrichment`** - Data cleaning + entity enrichment harness  
  _cross_industry, retail, finance, healthcare_ • Cross-vertical harness that normalizes a raw customer / vendor / applicant record: addresses → USPS standardized + geocoded; phones → E.164; names → canonical with given/family spl…
- **`harness/email-triage-and-draft`** - Email Triage + Draft harness (preference-aware, tone-matched)  
  _personal_productivity, cross_industry_ • Email-handling harness: loads user preferences + recipient tone history, triages each thread (do-now/delegate/defer/drop), drafts reply candidates matching the recipient's tone, an…
- **`harness/esg-disclosure-grading`** - ESG Disclosure Grading harness  
  _esg, supply_chain, compliance_ • Wraps the ESG supplier-policy-grading flow as a reusable harness with persona + GREP + RAG + tools layers. Targets local-Ollama or Anthropic/OpenAI for the judge model arm; emits c…
- **`harness/personal-corpus-search`** - Personal corpus search (RAG over user's own files / notes / docs)  
  _personal_productivity, cross_industry_ • Search the user's personal corpus — their own files, notes, emails, calendar, contacts — and return answer + citations scoped to ONLY the user's data. Authorization-gated; refuses …
- **`harness/radiology-report-review`** - Radiology Report Review harness  
  _healthcare, healthcare.radiology_ • RADS-aware + Fleischner-aware harness for grading radiology reports with HIPAA-safe PHI redaction. Wraps `pipeline/radiology-report- grading` with reusable layers.
- **`harness/redact-pii-text`** - Redact PII (text)  
  _cross_industry_ • Deterministic text PII redactor. Regex + NER patterns + a per-pattern replacement contract; emits an audit log of (sha256(original), action). No model call by default.
- **`harness/text-safety-review`** - Text Safety Review  
  _cross_industry_ • A general-purpose text harness that composes persona + GREP + RAG + tools + (optional) online grounding around a model call. Designed to produce cited, bounded, citation-first resp…

## pipeline

- **`pipeline/academic-integrity-review`** - Academic integrity review (plagiarism / AI / citation fabrication)  
  _education, education.higher, compliance_ • Ninth vertical. Same chain — only persona / GREP / KB / rubric change.
- **`pipeline/agriculture-compliance-review`** - Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)  
  _agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic, compliance_ • Vertical 28 — farm + packing-house compliance: FSMA water, pesticide REI/PHI/MRL, organic, child labor.
- **`pipeline/ai-governance-audit`** - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)  
  _ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001_ • Vertical 33 — AI conformity assessment for Annex III high-risk + GPAI + ISO 42001 AIMS.
- **`pipeline/anonymized-illicit-recruitment-pattern-sharing`** - Anonymized cross-org pattern sharing for illicit recruitment corridors  
  _esg, supply_chain, compliance_ • Mechanism for cross-industry knowledge sharing of systemic bad actors (rogue labor brokers, repeat-offender contractors, illicit recruitment corridors) WITHOUT leaking corporate-co…
- **`pipeline/aorn-surgical-count-gate`** - AORN Surgical Count GO/NO-GO gate  
  _healthcare, compliance_ • Apply AORN Sponge/Sharp/Instrument count gate before patient leaves OR — discrepancy requires intra-op imaging.
- **`pipeline/audio-mel-spec-cnn-classifier`** - Audio classification via mel-spectrogram + CNN (KerasCV / EfficientNet)  
  _ai, scientific_research, scientific_research.bio_ • Convert audio to mel-spectrograms (librosa or torchaudio), treat as images, train a CNN backbone (EfficientNet / ResNet via KerasCV or timm). Standard Kaggle approach for bird-call…
- **`pipeline/aviation-safety-review`** - Aviation safety incident review  
  _aviation, aviation.safety_ • Sixteenth vertical.
- **`pipeline/awq-quantized-inference`** - AWQ-quantized LLM inference (alternative to bitsandbytes nf4)  
  _ai_ • Serve a 4-bit AWQ (Activation-aware Weight Quantization) checkpoint for inference. AWQ preserves activation statistics, generally delivering lower perplexity drop than naive nf4. T…
- **`pipeline/benefits-adjudication-review`** - Government benefits adjudication review (SNAP / Medicaid / UI / SSI)  
  _government, government.benefits, compliance_ • Tenth vertical. Same 6-step chain — persona / GREP / KB / rubric swap for benefits-eligibility adjudication.
- **`pipeline/bidirectional-lstm-sequence-prediction`** - Bidirectional LSTM for sequence prediction (time-series / text)  
  _ai, healthcare_ • Stacked Bidirectional LSTM for sequence-to-sequence or sequence- to-label prediction. Standard Kaggle approach for: ventilator pressure prediction, classic NLP toxic comment classi…
- **`pipeline/bill-info-extract-fraud-detect-recommend`** - Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection  
  _bureaucracy_translation, bureaucracy_translation.payment_letters, bureaucracy_translation.fraud_screening, humanitarian_ • Photograph → structured-field extraction (Gemma 4 26B vision) → deterministic business-rule validation → Gemma 4 26B fraud-detect call against Verbraucherzentrale 10-indicator taxo…
- **`pipeline/biosecurity-review`** - Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)  
  _biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc_ • Vertical 32 — registered select-agent entity + BSL-3/4 lab compliance + DURC.
- **`pipeline/blip-clip-image-to-prompt`** - BLIP + CLIP Interrogator image-to-prompt  
  _ai, creative, creative.image_ • Generate a prompt that would re-create a given image. Combines: (1) BLIP captioning model for high-level description, (2) CLIP Interrogator for matching against curated artist / st…
- **`pipeline/brand-safe-product-photo`** - Brand-Safe Product Photo  
  _creative, retail_ • Image-generation pipeline that composes a cinematic-photography persona, style-reference RAG, lens-physics RAG, GREP guard rules, a tool call to a text-to-image model, and an outpu…
- **`pipeline/cannabis-compliance-review`** - Cannabis compliance review (state + §280E + METRC + FinCEN)  
  _cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing_ • Vertical 31 — licensed cannabis operator compliance.
- **`pipeline/chat-with-pdf-citations`** - Chat with PDF (with citations)  
  _cross_industry_ • The canonical "upload a PDF, ask questions, get cited answers" pipeline used by vercel/ai-chatbot, lobe-chat, codertom/chat-with-pdf, etc. Full layered chain:   pdf-to-text →   rec…
- **`pipeline/citemind-pdf-to-research-wiki`** - Local PDF → research wiki + concept graph (CiteMind shape)  
  _education, compliance, privacy_ • Local-first pipeline that turns a single PDF (paper / textbook chapter / report) into a persistent study workspace: OCR-aware indexing, hybrid retrieval, RAG chat with citations, g…
- **`pipeline/climate-disclosure-review`** - Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)  
  _climate, esg, finance, compliance_ • Grade a corporate climate disclosure against the rubric. Sixth vertical proving the architecture's industry-agnosticism. Same 6-step chain: prose → PII redact → GREP → RAG → judge …
- **`pipeline/code-act-jupyter-loop`** - Code-act Jupyter loop  
  _ai, software_ • The OpenInterpreter pattern: model emits Python code in fenced blocks, runtime renders the message + executes the code in a Jupyter kernel, streams the observation back into the mo…
- **`pipeline/code-review-with-risk-score`** - Code review with risk score  
  _software, software.codereview, security_ • Full layered code-review pipeline. Composes:   persona (senior engineer) →   grep (secret-leak guards on the diff) →   classifier (clinical-style red-flag screen for OWASP categori…
- **`pipeline/code-security-review`** - Code security review (CWE-cite-first AppSec audit)  
  _security, security.appsec, software, software.codereview_ • Review source code against `rubric/code-security-review-v1`. Uses the SAME chain shape as ESG / radiology / contract review: structured-to-prose → secrets-redact → GREP (vuln + sec…
- **`pipeline/construction-safety-review`** - Construction safety review (OSHA 1926 / Focus Four)  
  _construction, construction.safety_ • Vertical 18.
- **`pipeline/contract-clause-review`** - Commercial contract clause review (cite-first redlining)  
  _legal, legal.contract, legal.compliance_ • Review a commercial contract against `rubric/contract-review-quality- v1`. Reuses the SAME primitives as the ESG + radiology grading pipelines: structured-to-prose → PII redact → G…
- **`pipeline/customer-record-enrichment`** - Customer record enrichment (deterministic, cross-vertical)  
  _cross_industry, retail, finance, compliance_ • Normalize + enrich a raw customer / vendor record. Chains the format-convert processors (address / phone / name / country / date) followed by deduplication via entity-resolution-li…
- **`pipeline/customs-broker-review`** - Customs entry review (US CBP + UFLPA + USMCA + WCO)  
  _customs, customs.entry, customs.tariff, customs.fta_ • Vertical 29 — customs-entry compliance: ISF 10+2, HTS classification, FTA origin, UFLPA, AD/CVD.
- **`pipeline/deberta-lgbm-hybrid-scorer`** - DeBERTa-v3 + LightGBM hybrid scorer (with spell autocorrect)  
  _ai, education_ • Hybrid two-stage pipeline: (1) DeBERTa-v3 to embed text, (2) LightGBM head trained on (DeBERTa embedding + hand-crafted text features + autocorrected text). Spell autocorrect (SymS…
- **`pipeline/deep-research-supervisor-workers`** - Deep research: supervisor + parallel workers  
  _ai, media, cross_industry_ • LangChain's open_deep_research pattern. A supervisor LLM decomposes the user query into research briefs and dispatches N parallel researcher subagents (each gets its own context + …
- **`pipeline/deep-research-with-citations`** - Deep research with citations  
  _cross_industry, media_ • The "deep research" pattern popularized by Perplexity and the Anthropic orchestrator-workers cookbook. Fully layered:   redact (PII out before external search) →   persona (researc…
- **`pipeline/deep-tier-supplier-audit`** - Deep-tier (T1→T4+) supplier audit with traceability  
  _esg, supply_chain, compliance_ • Multi-step audit pipeline that walks a supplier graph from tier-1 (direct supplier) down to tier-3 and tier-4+ (raw-material origin / sub-sub-contractors). At each tier:  1. Resolv…
- **`pipeline/deepseek-r1-code-interpreter-math`** - DeepSeek-R1 / QwQ + Python code-interpreter for math reasoning  
  _ai, scientific_research, education_ • The winning AIMO-2 shape: a reasoning-distilled LLM (DeepSeek-R1- Distill-Qwen-7B / QwQ-32B) generates Python code that solves a math problem, the code runs in a Jupyter / sandbox …
- **`pipeline/dfars-cmmc-compliance-review`** - DoD DFARS / CMMC compliance review  
  _defense, defense.dfars, defense.cmmc, defense.counterfeit_parts_ • Vertical 22 — defense acquisition compliance.
- **`pipeline/dicom-medical-image-preprocessing`** - DICOM medical image preprocessing (CT / MRI / X-ray)  
  _healthcare, healthcare.radiology, ai_ • Parse DICOM headers (pydicom), normalize Hounsfield units (HU), window/level adjustment, resample to consistent voxel spacing, optional lung-segmentation crop, convert to PNG / Num…
- **`pipeline/differential-diagnosis`** - Differential Diagnosis  
  _healthcare, healthcare.clinical_ • Educational decision-support pipeline. Given (presentation, history, exam) text, returns a ranked differential diagnosis with cited guideline sections, ICD-10 code candidates, and …
- **`pipeline/document-to-knowledge-graph`** - Document to knowledge graph (nodes + edges with source anchors)  
  _legal, compliance, supply_chain, research_ • Take any source document (contract, SOP, regulatory framework, supply-chain disclosure) and produce a typed knowledge graph with source-anchored nodes + edges. Implements the conce…
- **`pipeline/dot-pretrip-gate`** - DOT pre-trip inspection gate (DVIR / 49 CFR 396)  
  _transportation, compliance_ • Apply driver vehicle inspection report gate — out-of-service criteria block dispatch.
- **`pipeline/efficientnet-medical-imaging`** - EfficientNet for medical imaging classification + segmentation  
  _healthcare, healthcare.radiology, ai_ • EfficientNet-B0 / B3 backbone + custom head for medical-imaging competitions: skin lesion (ISIC), brain activity (EEG-as-image), histopathology (HuBMAP), spine MRI (RSNA Lumbar). U…
- **`pipeline/election-misinformation-review`** - Election misinformation / disinformation / synthetic-media review  
  _election_integrity, media, media.factcheck_ • Vertical 23 — election integrity. Same 6-step chain.
- **`pipeline/email-triage-and-draft`** - Email triage + reply draft  
  _retail, retail.support, cross_industry_ • Customer-support email workflow. Layered chain:   redact PII →   grep (prompt-injection guard on email body — emails often carry attack     content from untrusted senders) →   clas…
- **`pipeline/email-triage-pipeline`** - Email triage pipeline (preference-loaded, tone-matched, leakage-checked)  
  _personal_productivity, cross_industry_ • Concrete pipeline wrapping `harness/email-triage-and-draft`. Loads user prefs + recipient tone → triages each thread → drafts replies → leakage-checks each draft → returns thread d…
- **`pipeline/esi-triage-gate`** - ESI 5-Level Triage gate (ER)  
  _healthcare, compliance_ • Apply AHRQ ESI v4 triage algorithm — danger-zone vitals at ESI 3 require upgrade to ESI 2.
- **`pipeline/everything-research-pipeline`** - Everything research pipeline (kitchen-sink, 22 passes)  
  _cross_industry_ • A comprehensive research pipeline that demonstrates every layer the hub supports — 22 distinct passes from raw input through model call through iterative refinement to delivery.
- **`pipeline/faa-preflight-gate`** - FAA Part 91 Before-Takeoff gate  
  _aviation, compliance_ • Apply the FAA before-takeoff checklist as a deterministic GO/NO-GO gate.
- **`pipeline/food-safety-review`** - Food safety review (FDA FSMA + HACCP + GFSI)  
  _food_safety, food_safety.fsma, food_safety.haccp_ • Seventeenth vertical.
- **`pipeline/full-vendor-due-diligence`** - Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)  
  _cross_industry, compliance, supply_chain, security_ • Cross-vertical kitchen-sink pipeline. Accepts a vendor onboarding packet containing (a) ESG/supply-chain disclosure, (b) representative code bundle, (c) draft MSA, and runs each th…
- **`pipeline/gaming-integrity-review`** - Gaming integrity review (BSA AML + responsible-gambling + match-fixing)  
  _gaming, gaming.aml, gaming.responsible, compliance_ • Vertical 26 — gaming-operator review: AML/CTR/SAR, self-exclusion, source-of-funds, match-fixing.
- **`pipeline/gdpr-dsar-review`** - GDPR DSAR fulfillment review (CCPA-compatible)  
  _privacy, privacy.gdpr, privacy.dsar, compliance_ • Eleventh vertical.
- **`pipeline/gxp-validation-review`** - GxP validation review (21-CFR-11 + Annex 11 + ALCOA+)  
  _pharma, pharma.gxp, compliance_ • Review a GxP-validated electronic-records system against the rubric. Same 6-step chain as ESG / radiology / legal / AppSec — fifth vertical proving the architecture's industry-agno…
- **`pipeline/haccp-ccp-gate`** - HACCP CCP monitoring gate  
  _food, compliance_ • Apply Codex HACCP CCP gate — critical limit exceeded = HOLD product.
- **`pipeline/hr-hiring-compliance-review`** - HR hiring compliance review (EEOC / Title VII / ADA / ADEA)  
  _hr, hr.hiring, compliance_ • Twelfth vertical.
- **`pipeline/insurance-claim-review`** - Insurance claim review (NAIC fraud-aware)  
  _insurance, insurance.claims, insurance.fraud, finance_ • Eighth vertical proving the architecture's industry-agnosticism. Same 6-step chain — only persona/rule-pack/knowledge-pack/rubric change.
- **`pipeline/itil-change-gate`** - ITIL Change Enablement gate  
  _it, compliance_ • Apply ITIL 4 change-enablement runbook as deterministic gate — CAB approval + backout plan + validation criteria are GO requirements.
- **`pipeline/knowledge-graph-from-corpus`** - GraphRAG: knowledge-graph from corpus + global/local query  
  _ai, cross_industry_ • Microsoft GraphRAG pattern. Extract entities + relationships from documents into a graph; build community summaries via Leiden clustering; query via local (ego-network), global (ma…
- **`pipeline/kyc-cip-gate`** - KYC/CIP onboarding gate (BSA + USA PATRIOT §326)  
  _finance, compliance_ • Apply CIP 4-element + OFAC + PEP + beneficial-ownership gate before account opening. OFAC hit + cannot-verify-identity = NO-GO.
- **`pipeline/large-model-faiss-rag`** - Large-model FAISS RAG (Platypus2-70b style)  
  _ai, scientific_research, education_ • Use a large (70B-class) instruction-tuned model with FAISS-indexed Wikipedia retrieval. The "go big or go home" Kaggle pattern that wins multi-choice-with-context competitions.
- **`pipeline/lgb-xgb-catboost-ensemble`** - LightGBM + XGBoost + CatBoost ensemble (tabular ML)  
  _ai, finance, finance.lending, finance.fraud_ • The dominant Kaggle tabular-ML shape: train LightGBM + XGBoost + CatBoost separately on the same features, blend predictions (weighted-mean / rank-mean / stacking). K-fold CV (typi…
- **`pipeline/llm-judge-essay-grading`** - LLM-judge essay grading (with adversarial prompt prefix)  
  _ai, education_ • Run a frontier LLM as judge on candidate essays, using a few-shot prompt with adversarial prefix patterns to discourage gaming. The "you can't please them all" pattern: grade stric…
- **`pipeline/longformer-bigbird-ner`** - Long-document NER with LongFormer / BigBird  
  _ai, education, media_ • Token-classification NER on documents longer than the 512-token BERT limit. Uses LongFormer (sliding-window attention) or BigBird (sparse attention) to handle 4096-16384 token inpu…
- **`pipeline/ma-dd-review`** - M&A due-diligence review (6-stream)  
  _m_and_a, m_and_a.due_diligence, legal, finance_ • Fifteenth vertical.
- **`pipeline/maritime-safety-review`** - Maritime safety review (IMO SOLAS / MARPOL / ISM / STCW)  
  _maritime, maritime.safety_ • Vertical 20.
- **`pipeline/mask-rcnn-coco-transfer`** - Mask-RCNN with COCO transfer learning (instance segmentation + detection)  
  _healthcare, healthcare.radiology, ai_ • Mask-RCNN with ResNet-50-FPN backbone, COCO-pretrained weights as starting checkpoint, fine-tuned on domain-specific instance segmentation / detection task. Classic transfer-learni…
- **`pipeline/medlabel-photo-to-warning`** - MedLabel — photo-to-warning medicine safety pipeline  
  _healthcare, healthcare.pharmacy, humanitarian, bureaucracy_translation_ • Photograph of a medicine label → Gemma 4 vision extract (active ingredients + dosage + strength + warnings) → drug-interaction check against the user's current medication list → mu…
- **`pipeline/mixed-criteria-demo`** - Mixed success-criteria demo (regex + semantic + deterministic + LLM + composite)  
  _cross_industry, compliance, legal_ • Demonstrates `pattern/composable-success-criteria`. The pipeline runs the contract-clause-review chain, then evaluates its output against EVERY criterion kind:
- **`pipeline/msha-preshift-exam`** - MSHA pre-shift exam GO/NO-GO gate  
  _mining, compliance_ • Apply 30 CFR 75.360 pre-shift exam as a deterministic GO/NO-GO gate — methane / O2 / ventilation / roof-rib-face hazards block miner entry.
- **`pipeline/multi-agent-debate-with-judge`** - Multi-agent debate with judge  
  _ai_ • Two or more debater personas argue different sides of a question across N rounds. A judge persona scores the final positions. Used for hard reasoning tasks where stress-testing imp…
- **`pipeline/multi-doc-qa-subquestion`** - Multi-document QA with sub-question decomposition  
  _cross_industry_ • LlamaIndex's SubQuestionQueryEngine pattern in pipeline form. The user asks a compound question; an LLM decomposes it into sub-questions; each sub-question runs its own retrieval; …
- **`pipeline/multi-model-judging-ensemble`** - Multi-model judging ensemble  
  _ai_ • Run inference across N different LLMs (e.g. Mixtral / Mistral-7B / Gemma-7B / Llama-3-8B), score each model's prediction with a perplexity baseline, then majority-vote or weighted-…
- **`pipeline/nerc-cip-compliance-review`** - NERC CIP compliance review (Bulk Electric System cyber)  
  _energy, energy.grid, security_ • Vertical 19.
- **`pipeline/nfpa-70e-loto-gate`** - NFPA 70E Lockout/Tagout gate  
  _energy, compliance_ • Apply NFPA 70E + OSHA 1910.147 LOTO gate — voltage detected after isolation = re-isolate.
- **`pipeline/nist-800-61-ir-gate`** - NIST 800-61 Incident Response gate  
  _cyber, compliance_ • Apply NIST SP 800-61 IR playbook — confirmed data exfil escalates to IC + legal.
- **`pipeline/nuclear-safety-review`** - Nuclear safety review (NRC 10 CFR + IAEA + INPO)  
  _nuclear, nuclear.power, nuclear.security, compliance_ • Vertical 27 — nuclear-plant compliance: LCO/LER, scram, physical security, SNM accounting.
- **`pipeline/optuna-tabular-tuning`** - Optuna hyperparameter tuning for tabular models  
  _ai, finance, scientific_research_ • Optuna-driven hyperparameter optimization for LGB / XGB / CatBoost. TPESampler over typical search space (lr, num_leaves/max_depth, n_estimators, subsample, colsample, reg_alpha, r…
- **`pipeline/perplexity-baseline-scoring`** - Perplexity-baseline scoring  
  _ai_ • Score candidate answers by their perplexity under a reference LLM. Lower perplexity = better fit. Used as a baseline for prompt-recovery, AI-text-detection, and any task where "flu…
- **`pipeline/personal-chat-pipeline`** - Personal chat pipeline (preference + memory + tool-aware)  
  _personal_productivity, cross_industry_ • Wraps `harness/chat-with-memory` in a concrete pipeline that loads user preferences, resolves any tool calls, and persists the turn to the memory backend.
- **`pipeline/personal-code-review-with-preferences`** - Personal code review with preference layer  
  _cross_industry_ • Review a code diff through the user's personal-preference layer. Loads the user's preferences pack, runs the personal-coding-reviewer persona, gates output against the personal-sty…
- **`pipeline/personal-search-pipeline`** - Personal corpus search pipeline (RAG over user's own data)  
  _personal_productivity, cross_industry_ • Concrete pipeline wrapping `harness/personal-corpus-search` for answering user queries from their own files / notes / emails / calendar / contacts. Local-first; opt-in for hosted m…
- **`pipeline/plan-execute-critic-loop`** - Plan / execute / critic loop  
  _cross_industry_ • The classic agentic pattern: planner LLM drafts a step list, executor runs the steps (with tool calls), critic LLM reviews the trace + re-plans on failure. Iterates until either th…
- **`pipeline/platform-content-triage`** - Platform content triage (Trust + Safety)  
  _compliance, media, privacy_ • Review user-generated content against a documented platform policy. Detects illicit + harmful patterns, routes CSAM suspicion to the human queue + NCMEC referral packet without mod…
- **`pipeline/pssr-startup-gate`** - PSM Pre-Startup Safety Review (PSSR) gate  
  _energy, compliance_ • Apply 29 CFR 1910.119(i) PSSR as a deterministic gate before unit start-up after maintenance — open Cat-A items / unresolved PHA / training gaps block hydrocarbon introduction.
- **`pipeline/quantized-llm-inference`** - Quantized LLM inference (4-bit BitsAndBytes)  
  _ai, cross_industry_ • Inference-only path: load a 7-70B LLM with 4-bit BitsAndBytes quantization, run generation with controlled sampling kwargs and a chat template. The lightest production shape — no L…
- **`pipeline/qwen-vllm-rerank-eedi`** - Qwen-32B vLLM retrieval-rerank with logits-processor constraints  
  _ai, education_ • Two-stage retrieval pipeline that won EEDI Mining Misconceptions: 1. Embedding-based retrieve top-K candidate misconceptions 2. Constrain a Qwen-32B-AWQ vLLM call to emit ONLY one …
- **`pipeline/radiology-report-grading`** - Radiology report grading (RADS-aware, Fleischner-aware)  
  _healthcare, healthcare.radiology_ • Grade a radiology report against `rubric/radiology-report-quality- v1`. The pipeline reuses the SAME primitives as the ESG grading pipeline:  1. `processor/structured-to-prose` — f…
- **`pipeline/rcra-waste-review`** - RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)  
  _waste, waste.rcra_tsdf, waste.generator, waste.universal_ • Vertical 34 — LQG/SQG/TSDF + Universal Waste compliance.
- **`pipeline/real-estate-dd-review`** - Real estate due-diligence review  
  _real_estate, real_estate.due_diligence_ • Fourteenth vertical.
- **`pipeline/research-entity`** - Research Entity  
  _cross_industry_ • Given an entity name + entity kind (company / person / place / product), produce a sourced one-page profile. Verifiable, cited, redacted.
- **`pipeline/sd-prompt-embedding-cosine`** - Stable-Diffusion prompt embedding + cosine evaluation  
  _ai, creative, creative.image_ • Embed Stable-Diffusion prompts using sentence-transformers, compare candidate prompts against gold prompts via cosine similarity. The standard scoring approach for prompt-recovery …
- **`pipeline/security-incident-grading`** - Security incident write-up grading (CTI + AppSec chained)  
  _security, threat_intelligence, security.appsec_ • Chains threat-intel IOC review + AppSec code review on incident write-ups: extracts IOCs/TTPs from the report AND grades any attached code-of-concern for known vulnerabilities.
- **`pipeline/self-rag-grade-and-revise`** - Self-RAG: grade-and-revise (concrete implementation)  
  _ai, cross_industry_ • Concrete pipeline implementing `pattern/self-rag`. Retrieve → per-doc relevance grader → rewrite-query loop on irrelevant retrieval → generate with grounding → answer-support grade…
- **`pipeline/sensor-fusion-imu-blending`** - Multi-sensor fusion (IMU + thermal + ToF) with model blending  
  _healthcare, ai, manufacturing_ • Multi-modal sensor-fusion pipeline for behavior / activity classification: IMU (inertial measurement unit — accelerometer + gyroscope), THM (thermal), ToF (time-of-flight depth). T…
- **`pipeline/sentence-transformer-finetune-retrieval`** - Sentence-transformer fine-tune for retrieval / ranking  
  _ai, education, scientific_research_ • Fine-tune a sentence-transformer (Sentence-BERT family) on (query, positive, negative) triplets using MultipleNegativesRankingLoss or CosineSimilarityLoss. Embeds documents into a …
- **`pipeline/space-launch-review`** - Space launch + range safety review (FAA Part 450 / NASA / ITAR)  
  _space, space.launch, space.export_control, space.orbital_ • Vertical 30 — commercial space launch compliance: FSA / Ec / FTS / ITAR / 25-yr disposal / MPL.
- **`pipeline/storm-persona-curation-article`** - STORM: persona-curation + outline-fanout article  
  _ai, media, education_ • Stanford OVAL's STORM pattern. Generate N personas with different perspectives → run simulated dialogue per persona to curate knowledge → outline → parallel-expand each outline sec…
- **`pipeline/supplier-policy-grading`** - Supplier policy & disclosure grading (CSDDD-aligned)  
  _esg, supply_chain, compliance_ • End-to-end pipeline for grading supplier-submitted policy texts and self-assessments against the EU CSDDD, ILO forced-labor indicators, and the lead company's code of conduct. The …
- **`pipeline/suspicious-transaction-review`** - Suspicious Transaction Review  
  _finance, finance.aml_ • Given a transaction bundle (account, recent transactions, related entities), produce a sanctions-first risk review, FATF typology scoring, and a SAR-style narrative DRAFT (never a …
- **`pipeline/sustainability-report-full-review`** - Sustainability report full review (Climate + ESG-S + ESG-G chained)  
  _climate, esg, compliance, finance_ • Chains 3 sub-pipelines for a comprehensive sustainability-report audit: climate-disclosure-review + (a subset of) supplier-policy- grading focused on social + (a subset of) governa…
- **`pipeline/swe-patch-sample-and-review`** - SWE-agent: sample N patches + reviewer judges  
  _ai, software, software.codereview_ • The princeton-nlp/SWE-agent pattern. Given a bug report + repo: sample N action-rollouts (each producing a candidate patch via file-edit + run- test loop), then a reviewer model ju…
- **`pipeline/synthetic-data-gen-with-teacher-llm`** - Synthetic-data generation with teacher LLM  
  _ai_ • Use a teacher LLM to generate (input, output) training pairs for a downstream student fine-tune. Includes filtering for diversity + difficulty + safety. The pattern that won the pr…
- **`pipeline/telco-compliance-review`** - Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)  
  _telecommunications, telecommunications.fcc, telecommunications.cpni, compliance_ • Vertical 25 — telecom-carrier compliance: CPNI breach, NORS outages, STIR/SHAKEN, CALEA, E911.
- **`pipeline/threat-intel-ioc-review`** - Threat-intel IOC + TTP review (MITRE ATT&CK aligned)  
  _security, threat_intelligence_ • Ingest a CTI report or incident write-up, extract IOCs + TTPs, validate against MITRE ATT&CK, rate confidence, surface attribution risk. Seventh vertical proving industry-agnostici…
- **`pipeline/trade-compliance-review`** - Trade compliance review (HTS / EAR / ITAR / OFAC)  
  _trade, trade.eccn, trade.itar, trade.sanctions_ • Thirteenth vertical.
- **`pipeline/transfer-pricing-review`** - Transfer pricing review (OECD TPG / BEPS / §482 / Pillar Two)  
  _tax, tax.transfer_pricing, finance_ • Vertical 21.
- **`pipeline/trid-loan-gate`** - TRID Loan Estimate + Closing Disclosure gate  
  _finance, compliance_ • Apply Reg Z TRID timing + tolerance gate before mortgage consummation — CD timing miss = NO-GO + re-issue.
- **`pipeline/twenty-questions-agent`** - 20-questions agent (Akinator-style)  
  _ai, education_ • An agent that plays 20 Questions — asks yes/no questions to narrow down a hidden concept. Uses a candidate set + binary-search-style question generation. The classic agent-game pat…
- **`pipeline/two-time-retrieve-rerank`** - Two-time retrieval + cross-encoder rerank  
  _ai, education, scientific_research_ • Generic two-pass retrieval pipeline distilled from the EEDI-AWQ shape. First-pass: retrieve top-K with the raw query. Refine the query using LLM summary of pass-1. Second-pass: ret…
- **`pipeline/unet-segmentation-tta`** - U-Net medical segmentation with albumentations + TTA  
  _healthcare, healthcare.radiology, ai_ • U-Net (often with EfficientNet/ResNet/SEResNeXt encoder via segmentation_ models_pytorch) for medical image segmentation. Standard Kaggle shape: 5-fold CV + albumentations augmenta…
- **`pipeline/verify-claim-against-corpus`** - Verify Claim Against Corpus  
  _cross_industry, media_ • Given a claim and a corpus, return supports / contradicts / no-evidence with cited passages and a confidence score.
- **`pipeline/vllm-batch-llm-inference`** - vLLM batch LLM inference (with logits-processor-zoo)  
  _ai, education_ • Serve many prompts through a single vLLM engine with shared KV cache + prefix caching. Optional logits-processor-zoo entries (SuppressTokens / AllowedTokens / FixedTokenBias) const…
- **`pipeline/water-utility-compliance-review`** - Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)  
  _water_utility, water_utility.sdwa, water_utility.lcr, water_utility.scada_ • Vertical 24 — drinking-water utility compliance + cyber.
- **`pipeline/who-surgical-safety-gate`** - WHO Surgical Safety Checklist gate (Sign In before induction)  
  _healthcare, compliance_ • Apply the WHO SSC Sign In gate to a pre-induction packet. If any required item is unverified OR any NO-GO is triggered, halt and emit NO-GO.

## benchmark

- **`benchmark/esg-supplier-grading-bench`** - ESG supplier-grading benchmark v1  
  _esg, supply_chain, compliance_ • Runs `pipeline/supplier-policy-grading` against the synthetic supplier disclosure pack test set (3 representative cases: a well- disclosed T1 tech supplier; a T3 textile supplier i…

## rule-pack

- **`rule-pack/aml-typologies-fatf`** - FATF AML typologies (sampled)  
  _finance, finance.aml_ • Classifier rules for common FATF-aligned AML typologies. Each rule is a labeled-example bundle the AML harness uses to score a transaction sequence against known patterns (structur…
- **`rule-pack/clinical-red-flags`** - Clinical red flags  
  _healthcare, healthcare.clinical_ • A classifier rule pack of presenting-symptom patterns that require immediate clinical evaluation. Fires inside the clinical-decision- support harness BEFORE differential reasoning,…
- **`rule-pack/financial-pii-en`** - Financial PII (English)  
  _finance_ • Detection patterns for common financial PII in English transaction narratives and KYC documents — account numbers, IBANs, SWIFT/BIC, card PANs (Luhn-likely), SSN/TIN. Designed to g…
- **`rule-pack/grep-academic-integrity-flags`** - Academic integrity red-flag detectors (plagiarism / AI / fabricated citations)  
  _education, education.higher, compliance_ • Heuristic detectors for academic integrity violations. Designed to TRIGGER deep review (similarity check + AI detector + citation DB lookup) — not to determine guilt directly.
- **`rule-pack/grep-agriculture-compliance-flags`** - Agriculture compliance flags (USDA / GAP / NOP organic)  
  _agriculture_compliance, agriculture_compliance.usda, agriculture_compliance.organic, agriculture_compliance.gap_ • Detectors for ag-supply-chain compliance gaps.
- **`rule-pack/grep-ai-governance-flags`** - AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)  
  _ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001_ • Detectors for AI governance + conformity assessment gaps.
- **`rule-pack/grep-ai-vendor-keys`** - AI vendor API key detectors  
  _security, ai_ • Detection patterns for API keys issued by major LLM / AI vendors — Anthropic, OpenAI, Hugging Face, Cohere, Replicate, Mistral, Groq, Together, fal, Perplexity, Voyage, NVIDIA NIM.…
- **`rule-pack/grep-aviation-safety-flags`** - Aviation safety incident flags (NTSB / FAA / HFACS)  
  _aviation, aviation.safety_ • Detectors for aviation-incident-report red flags.
- **`rule-pack/grep-benefits-eligibility-flags`** - Benefits-eligibility red-flag detectors (SNAP / Medicaid / UI)  
  _government, government.benefits, compliance_ • GREP detectors for the highest-leverage benefits-eligibility signals: countable-income markers above thresholds, asset deemers, undisclosed household members, immigration-status qu…
- **`rule-pack/grep-biosecurity-flags`** - Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags  
  _biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc_ • Detectors for 42 CFR 73 / BMBL / WHO LBM4 / DURC compliance gaps.
- **`rule-pack/grep-cannabis-compliance-flags`** - Cannabis compliance flags (METRC + §280E + FinCEN + COA)  
  _cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing_ • Detectors for cannabis-industry compliance gaps.
- **`rule-pack/grep-climate-disclosure-gaps`** - Climate disclosure gap detectors (TCFD / ISSB / ESRS E1)  
  _climate, esg, finance, compliance_ • GREP detectors for the highest-leverage climate-disclosure gaps: missing Scope-3 categories, missing transition plan, board- oversight silence, no 2C scenario analysis, no SBTi com…
- **`rule-pack/grep-cloud-secrets`** - Cloud provider secret detectors  
  _security, cross_industry, ai_ • Detection patterns for cloud-provider access keys and service-account credentials — AWS, GCP, Azure, DigitalOcean, OCI. Converged from gitleaks (`config/gitleaks.toml`), trufflehog…
- **`rule-pack/grep-code-vulnerabilities`** - Code vulnerability + secret-detection GREP pack  
  _security, security.appsec, software_ • GREP detectors for the highest-leverage source-code vulnerabilities + hardcoded secrets + dangerous-function calls. Pair with `pipeline/code-security-review`. Cite each rule with i…
- **`rule-pack/grep-construction-safety-flags`** - Construction safety red-flag detectors (OSHA 1926)  
  _construction, construction.safety_ • Detectors for OSHA Focus Four + scaffolding + excavation + PPE.
- **`rule-pack/grep-contract-red-flags`** - Commercial contract red-flag detectors  
  _legal, legal.contract, legal.compliance_ • GREP detectors for the 10 highest-leverage contract red-flag patterns: uncapped indemnity, unlimited liability, pre-existing IP assignment, unilateral termination, asymmetric caps,…
- **`rule-pack/grep-customs-broker-flags`** - Customs entry / FTA / forced-labor flags (US CBP)  
  _customs, customs.entry, customs.tariff, customs.fta_ • Detectors for customs-entry compliance gaps.
- **`rule-pack/grep-defense-dfars-flags`** - Defense DFARS + CMMC + counterfeit-parts red-flag detectors  
  _defense, defense.dfars, defense.counterfeit_parts, defense.cmmc_ • GREP detectors for DFARS / CMMC / SAE AS5553 / Section 889 / SAM exclusion.
- **`rule-pack/grep-election-misinformation-flags`** - Election misinformation / disinformation / deepfake detectors  
  _election_integrity, media, media.factcheck_ • Heuristic GREP detectors for common election-misinformation patterns.
- **`rule-pack/grep-esg-environmental-red-flags`** - ESG environmental red-flag detectors (the 'E' of ESG)  
  _esg, supply_chain, compliance, climate_ • GREP detectors for the environmental dimension of supplier disclosures: deforestation, water pollution, hazardous-waste mismanagement, GHG underreporting, biodiversity harm, illega…
- **`rule-pack/grep-esg-forced-labor-red-flags`** - ESG / forced-labor red-flag detectors (the 'S' of ESG)  
  _esg, supply_chain, compliance_ • Heuristic regex detectors for the 11 ILO forced-labor indicators + child labor + recruitment-fee abuse + tier-3/4 supply-chain transparency gaps + 12 high-risk corridors. Designed …
- **`rule-pack/grep-esg-governance-red-flags`** - ESG governance red-flag detectors (the 'G' of ESG)  
  _esg, compliance, finance_ • GREP detectors for the governance dimension: beneficial-ownership opacity, anti-bribery / corruption signals, whistleblower-channel weaknesses, conflict-of-interest, board-independ…
- **`rule-pack/grep-fake-inkasso-fraud-flags`** - Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)  
  _bureaucracy_translation, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee_ • GREP detectors for the 10 Verbraucherzentrale Fake-Inkasso indicators. Used by `pipeline/bill-info-extract-fraud-detect-recommend` as a deterministic FIRST PASS before the LLM-base…
- **`rule-pack/grep-food-safety-flags`** - Food safety / FSMA / HACCP red-flag detectors  
  _food_safety, food_safety.fsma, food_safety.haccp, compliance_ • Detectors for FSMA + HACCP non-compliance.
- **`rule-pack/grep-gaming-integrity-flags`** - Gaming integrity / AML / responsible-gambling flags  
  _gaming, gaming.aml, gaming.responsible_gambling_ • Detectors for gaming compliance gaps.
- **`rule-pack/grep-gdpr-dsar-red-flags`** - GDPR DSAR red-flag detectors  
  _privacy, privacy.gdpr, privacy.dsar, compliance_ • GREP detectors for GDPR Data Subject Access Request handling red flags: missing identity verification, missing-lawful-basis, unlawful erasure refusal, missing transfer safeguards, …
- **`rule-pack/grep-gxp-data-integrity-red-flags`** - GxP data-integrity red-flag detectors (21-CFR-11 / ALCOA+)  
  _pharma, pharma.gxp, compliance_ • GREP detectors for the highest-leverage 21-CFR-11 + ALCOA+ data- integrity violations: missing audit trails, shared accounts, post- hoc record alteration, validation gaps, missing …
- **`rule-pack/grep-hr-hiring-bias-flags`** - HR hiring bias detectors (Title VII / ADA / ADEA / EEOC)  
  _hr, hr.hiring, compliance_ • GREP detectors for biased language in job postings + screening questions. Each rule cites the protected-class statute. TRIGGER review — never autoreject; recommend neutral language…
- **`rule-pack/grep-insurance-fraud-red-flags`** - Insurance claim fraud red-flag detectors (NAIC + CAIF)  
  _insurance, insurance.claims, insurance.fraud, finance_ • GREP detectors for the highest-leverage insurance-claim fraud red flags drawn from NAIC fraud-fighter handbook + Coalition Against Insurance Fraud indicators. Pair with `pipeline/i…
- **`rule-pack/grep-ioc-extraction`** - IOC extraction GREP pack (file hashes / domains / IPs / URLs)  
  _security, threat_intelligence_ • Extracts indicators-of-compromise from threat-intel reports, incident write-ups, sandbox outputs. Output IOCs feed into `pipeline/threat-intel-ioc-review` for verification + ATT&CK…
- **`rule-pack/grep-ma-dd-red-flags`** - M&A DD red-flag detectors (6 streams)  
  _m_and_a, m_and_a.due_diligence, legal, finance_ • GREP detectors for financial/legal/IP/customer/HR/tax DD.
- **`rule-pack/grep-maritime-safety-flags`** - Maritime safety red-flag detectors (SOLAS / MARPOL / ISM)  
  _maritime, maritime.safety_ • Detectors for vessel + crew + management deficiencies.
- **`rule-pack/grep-nerc-cip-flags`** - NERC CIP compliance red-flag detectors  
  _energy, energy.grid, security, compliance_ • Detectors for NERC CIP gaps.
- **`rule-pack/grep-nuclear-safety-flags`** - Nuclear safety / NRC / IAEA flags  
  _nuclear, nuclear.nrc, nuclear.iaea_ • Detectors for nuclear-safety findings.
- **`rule-pack/grep-output-safety-image`** - Image-output safety checks  
  _creative, media_ • Post-generation safety check pack for image outputs. Pairs of (detector-call, threshold) plus a watermark presence check. Designed to be called by an image-gen pipeline AFTER the t…
- **`rule-pack/grep-personal-info-leakage`** - Personal-info leakage detectors (assistant drafts → wrong audience)  
  _personal_productivity, cross_industry_ • GREP detectors that fire when a personal-assistant DRAFT is about to be sent to a recipient and contains content the user has marked private (salary / health / family conflict / me…
- **`rule-pack/grep-personal-style-flags`** - Personal style flags (catches disallowed idioms)  
  _cross_industry_ • GREP-family detectors that flag content the user has disallowed. Out-of-the-box catches: em dashes, marketing-speak verbs (delve, leverage), hedging adjectives (robust, seamless), …
- **`rule-pack/grep-platform-moderation-flags`** - Platform moderation flags (text-only triage)  
  _compliance, media, privacy_ • GREP detectors for text-only moderation triage. Catches obvious-language signals that warrant policy review. CSAM-suspicion routing is keyword-free + relies on multimodal classifie…
- **`rule-pack/grep-private-key-blocks`** - Private key block detectors  
  _security, cross_industry_ • Detection patterns for PEM-encoded private keys (RSA, EC, DSA, OpenSSH, PGP) and modern formats (Age, Sigstore). Any match is a critical-severity hit — full revocation + key rotati…
- **`rule-pack/grep-prohibited-terms`** - Prohibited Terms (image-gen guard rails)  
  _creative, media_ • GREP guard rail for image-generation pipelines. Blocks prompts that reference real celebrities by name, real trademarks, hate slurs, or explicit sexual content. Severity drives the…
- **`rule-pack/grep-prompt-injection-heuristics`** - Prompt-injection heuristic detectors  
  _security, ai, cross_industry_ • Heuristic regex patterns that flag likely prompt-injection attempts in input, retrieved documents, or tool results. Inspired by garak probe families (`promptinject`, `latentinjecti…
- **`rule-pack/grep-radiology-report-red-flags`** - Radiology report quality + incidental-findings red flags  
  _healthcare, healthcare.radiology_ • GREP detectors for radiology-report quality and incidental-finding follow-up gaps. Designed to be run AFTER `rule-pack/privacy-phi- hipaa-en` redaction. Pair with `pipeline/radiolo…
- **`rule-pack/grep-rcra-waste-flags`** - RCRA hazardous waste + e-Manifest + DOT HMR flags  
  _waste, waste.rcra_tsdf, waste.generator, waste.universal_ • Detectors for 40 CFR 260-279 + e-Manifest + DOT 49 CFR 172 compliance gaps.
- **`rule-pack/grep-real-estate-dd-red-flags`** - Real estate DD red-flag detectors  
  _real_estate, real_estate.due_diligence_ • GREP detectors for title/ESA/structural/zoning issues.
- **`rule-pack/grep-space-launch-flags`** - Space launch + range safety + ITAR/EAR flags  
  _space, space.launch, space.export_control, space.orbital_ • Detectors for FAA Part 450 / range-safety / ITAR compliance gaps.
- **`rule-pack/grep-telco-compliance-flags`** - Telco compliance red-flag detectors (FCC / CPNI / CALEA)  
  _telecommunications, telecommunications.fcc, telecommunications.cpni_ • Detectors for telco regulatory gaps.
- **`rule-pack/grep-trade-compliance-flags`** - Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)  
  _trade, trade.eccn, trade.itar, trade.sanctions_ • GREP detectors for export-control red flags: dual-use technology to embargoed destinations, missing end-user diligence, ITAR technical data outside licensed scope, deemed-export si…
- **`rule-pack/grep-transfer-pricing-flags`** - Transfer-pricing red-flag detectors (OECD / §482 / BEPS)  
  _tax, tax.transfer_pricing, finance_ • Detectors for transfer-pricing risk.
- **`rule-pack/grep-vcs-platform-pats`** - VCS platform PATs (GitHub, GitLab, Bitbucket, Atlassian)  
  _security, software_ • Detection patterns for Personal Access Tokens issued by code-hosting platforms. Each vendor uses a stable prefix (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` for GitHub; `glpat-` for Gi…
- **`rule-pack/grep-water-utility-flags`** - Water utility SDWA / LCRR / AWIA red-flag detectors  
  _water_utility, water_utility.lcr, water_utility.sdwa_ • GREP detectors for SDWA compliance gaps + acute risks.
- **`rule-pack/hybrid-retrieval-policy`** - Hybrid retrieval policy (BM25 + dense + RRF)  
  _cross_industry_ • A RAG retrieval policy pack: BM25 sparse + dense vector + Reciprocal Rank Fusion + optional cross-encoder reranking + 1-hop citation graph expansion. Pipelines and harnesses refere…
- **`rule-pack/phi-hipaa-en`** - PHI (HIPAA 18-identifier) — English text  
  _healthcare_ • Detection patterns for the 18 HIPAA "Safe Harbor" PHI identifiers in English text. Designed to feed `harness/redact-pii-text` and any downstream healthcare pipeline that needs a ha…
- **`rule-pack/privacy-pii-text-en`** - Privacy PII (English text)  
  _cross_industry_ • Baseline GREP rule pack for detecting common PII in English text. Emails, phone numbers, US SSN, passport numbers, IBANs, IPv4. Designed to feed `harness/redact-pii-text` and any d…
- **`rule-pack/sanctions-screening`** - Sanctions screening (deterministic)  
  _finance, finance.aml, finance.kyc_ • Heuristic rule pack for sanctions screening. Each rule is a condition that pairs a normalized entity name (or fuzzy match) with a sanctions list and a fuzz threshold. The harness p…
- **`rule-pack/web-search-allowlist-default`** - Web search allowlist (default)  
  _cross_industry_ • Default online-search rule pack. Allowlist of trusted public-source domains, per-source freshness windows, query sanitization rules, and a small blocklist of dangerous source patte…

## knowledge-pack

- **`knowledge-pack/academic-honor-codes`** - Academic honor codes + AI-policy frameworks  
  _education, education.higher, compliance_ • Composite educational reference of academic honor codes, AI-use policies, plagiarism definitions, and citation standards (APA / MLA / Chicago).
- **`knowledge-pack/agriculture-compliance-frameworks`** - Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)  
  _agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic_ • FSMA Produce Safety Rule + NOP organic + GlobalGAP + EPA pesticide labeling.
- **`knowledge-pack/ai-governance-frameworks`** - AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)  
  _ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001_ • Regulation (EU) 2024/1689 + NIST AI RMF 1.0 + ISO/IEC 42001:2023 + GDPR Art 22 + serious incident reporting.
- **`knowledge-pack/aml-red-flags-extended`** - AML red flags (extended)  
  _finance, finance.aml, finance.kyc_ • Extended catalog of anti-money-laundering red flags drawn from FATF guidance, FinCEN advisories, and Wolfsberg principles. Complements `knowledge-pack/fatf-typologies-sample` with …
- **`knowledge-pack/aviation-safety-frameworks`** - Aviation safety frameworks (NTSB / FAA / ICAO / HFACS / ASAP)  
  _aviation, aviation.safety_ • Composite — NTSB cause taxonomy + FAA AC 120-92 SMS + ICAO Annex 13 + HFACS framework + ASAP MOU principles.
- **`knowledge-pack/biosecurity-frameworks`** - Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)  
  _biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc_ • HHS/CDC/APHIS select agent + BMBL 6th + WHO Lab Biosafety Manual 4th + DURC + P3CO.
- **`knowledge-pack/cannabis-frameworks`** - Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)  
  _cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing_ • State licensing + §280E + METRC + FinCEN 2014 + 21 USC 812 + COA panels + ASTM D3475.
- **`knowledge-pack/citemind-architecture-reference`** - CiteMind architecture reference (local-first PDF → research wiki + concept graph)  
  _education, privacy, compliance_ • Architectural shape extracted from the CiteMind hackathon submission: Tauri 2 desktop + React 19/TypeScript + Rust backend + SQLite, OCR-aware page-chunked indexing, hybrid retriev…
- **`knowledge-pack/climate-disclosure-frameworks`** - Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)  
  _climate, esg, finance_ • Composite educational extracts of the major climate-disclosure frameworks:  - TCFD (Task Force on Climate-related Financial Disclosures)    recommendations across 4 pillars (Govern…
- **`knowledge-pack/clinical-guidelines-sample`** - Clinical guidelines (sample chunks)  
  _healthcare, healthcare.clinical_ • Sample chunks of clinical-guideline language for catalog-demo purposes. Each chunk has a stable section reference so a citation-first persona can cite by section. Use authoritative…
- **`knowledge-pack/common-abbreviations`** - Common abbreviations (cross-industry sample)  
  _cross_industry_ • Sampled abbreviations and acronyms across healthcare, finance, legal, security, and technology, with expansions and a context tag. Designed for the `expand.abbreviation` processor …
- **`knowledge-pack/common-personas-library`** - Common personas / system-prompt library  
  _cross_industry_ • Reusable persona / system-prompt fragments for common roles — research analyst, code reviewer, customer-support agent, technical writer, translator, tutor, summarizer, fact-checker…
- **`knowledge-pack/contract-law-clauses`** - Commercial contract clause library (composite educational)  
  _legal, legal.contract, legal.compliance_ • Composite, educational reference of common commercial contract clauses with: standard market language, common red-flag variants, why each red flag matters, and a suggested redline.…
- **`knowledge-pack/csddd-and-forced-labor-indicators`** - Global supply-chain due-diligence regulatory pack  
  _esg, supply_chain, compliance, cross_industry_ • Reference pack of (composite, educational) extracts from 12 jurisdictions + 4 international frameworks:
- **`knowledge-pack/customs-cbp-wco-frameworks`** - Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)  
  _customs, customs.entry, customs.tariff, customs.fta_ • 19 CFR Parts 142/149/152/174 + 19 USC §1484/1592/1307 + UFLPA + USMCA + WCO SAFE.
- **`knowledge-pack/defense-dfars-frameworks`** - Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)  
  _defense, defense.dfars, defense.cmmc, defense.counterfeit_parts_ • Composite of US DoD acquisition + cyber + counterfeit-parts compliance.
- **`knowledge-pack/drug-interaction-references`** - Drug-drug interaction references (DrugBank / RxNorm / FDA Orange Book / DailyMed)  
  _healthcare, healthcare.pharmacy_ • Composite educational reference of drug-drug interaction sources for use by `pipeline/medlabel-photo-to-warning` and similar medicine-safety AI pipelines.
- **`knowledge-pack/drug-interactions-sample`** - Drug-drug interactions (sample, educational)  
  _healthcare, healthcare.pharmacy, healthcare.clinical_ • Composite paraphrases of well-known drug-drug interaction patterns for educational reference. NOT a substitute for an authoritative database (e.g. RxNorm + Lexicomp + Micromedex). …
- **`knowledge-pack/eeoc-hiring-statutes`** - EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)  
  _hr, hr.hiring, compliance_ • Composite educational reference of the federal anti-discrimination hiring statutes administered by the EEOC + OFCCP.
- **`knowledge-pack/election-integrity-frameworks`** - Election integrity frameworks (EAC / CISA / DHS / C2PA)  
  _election_integrity, media, media.factcheck_ • Composite — EAC election standards + CISA election infrastructure + DHS election cyber + C2PA Content Credentials + ACT methodology.
- **`knowledge-pack/fatf-typologies-sample`** - FATF typologies (sample chunks)  
  _finance, finance.aml_ • Sample paraphrased typology chunks for catalog-demo purposes. Real deployments should ingest the latest FATF and FinCEN typology reports; this pack anchors the data shape and citat…
- **`knowledge-pack/food-safety-fsma-haccp`** - FSMA + HACCP + GFSI food safety frameworks  
  _food_safety, food_safety.fsma, food_safety.haccp_ • Composite — FDA FSMA rules (21 CFR 117 / FSVP / 112 / 121) + HACCP 7 principles + GFSI-recognized schemes (SQF / BRCGS / FSSC 22000) + FDA recall classes + FSMA-204 traceability.
- **`knowledge-pack/gaming-aml-rg-frameworks`** - Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state RG)  
  _gaming, gaming.aml, gaming.responsible_ • BSA gaming-industry obligations + state responsible-gambling + UKGC LCCP + match-fixing integrity.
- **`knowledge-pack/gdpr-articles-and-ccpa`** - GDPR articles + CCPA/CPRA + e-Privacy  
  _privacy, privacy.gdpr, privacy.ccpa, privacy.dsar_ • Composite educational extracts of:  - EU GDPR (Regulation 2016/679) — Articles 5 / 6 / 7 / 9 /    12-22 (data subject rights) / 25 (privacy by design) / 30    (records of processin…
- **`knowledge-pack/gov-benefits-rules`** - Government benefits program rules (SNAP / Medicaid / UI / SSI)  
  _government, government.benefits, compliance_ • Composite educational reference of the major US federal benefits programs' eligibility rules: SNAP (7 CFR 273), Medicaid (42 CFR + state plan), Unemployment Insurance (state UI man…
- **`knowledge-pack/gxp-21-cfr-11-guidelines`** - 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack  
  _pharma, pharma.gxp, healthcare.pharmacy, compliance_ • Composite educational extracts of GxP electronic-records / electronic-signatures / data-integrity guidance:  - US FDA 21 CFR Part 11 (Subpart B — Electronic Records;    Subpart C —…
- **`knowledge-pack/high-risk-corridors-and-sectors`** - High-risk corridors & sector-specific labor / environmental risks  
  _esg, supply_chain, compliance, humanitarian_ • Composite reference of high-risk geographic corridors and product sectors with documented patterns of forced labor, child labor, environmental harm, or governance opacity. Used by …
- **`knowledge-pack/icd10-sample`** - ICD-10 sample  
  _healthcare, healthcare.clinical_ • Sampled subset of ICD-10 diagnosis codes for catalog-demo purposes. Use the public, full ICD-10 release for any production deployment; this pack exists to anchor the data shape, no…
- **`knowledge-pack/imo-conventions`** - IMO conventions (SOLAS / MARPOL / ISM / STCW / ISPS / MLC)  
  _maritime, maritime.safety_ • Composite of IMO maritime safety + pollution + crew conventions.
- **`knowledge-pack/insurance-fraud-typologies`** - Insurance fraud typologies (NAIC + CAIF + ABI)  
  _insurance, insurance.claims, insurance.fraud, finance_ • Composite reference of insurance-fraud typologies and red-flag indicators across personal auto, property, workers-comp, and health insurance. Sourced from NAIC Fraud Section + Coal…
- **`knowledge-pack/iso-country-codes`** - ISO 3166 country codes (sample)  
  _cross_industry, finance, humanitarian_ • ISO 3166-1 alpha-2, alpha-3, numeric codes plus region and a coarse FATF risk hint. Useful for KYC, transaction-graph queries, and cross-border-flow analysis. Sample subset; full l…
- **`knowledge-pack/iso-currency-codes`** - ISO 4217 currency codes  
  _finance, cross_industry_ • ISO 4217 three-letter currency codes with name, numeric code, and minor-unit precision. Useful for finance pipelines that need to validate currency strings or normalize amounts. Sa…
- **`knowledge-pack/lead-company-code-stub`** - Lead-company code-of-conduct stub (placeholder)  
  _cross_industry, esg, supply_chain, compliance_ • Placeholder reference that ESG / vendor pipelines accept as the lead-company-specific code of conduct. Real instances would replace this with the deploying organization's actual co…
- **`knowledge-pack/lens-physics-primers`** - Lens physics primers  
  _creative_ • Short physical-prior descriptors for camera lens behavior. Used by image-gen prompt-shapers so prompts request physically plausible combinations of focal length, aperture, distance…
- **`knowledge-pack/ma-dd-frameworks`** - M&A DD frameworks (legal / financial / IP / customer / HR / tax)  
  _m_and_a, m_and_a.due_diligence, legal, finance_ • Composite educational reference: standard M&A DD checklist + R&W insurance scope + IRC §382 NOL limits + WARN Act + standard IP-assignment + open-source license compatibility matri…
- **`knowledge-pack/mitre-attack-sample`** - MITRE ATT&CK techniques (sample)  
  _security_ • Sample of MITRE ATT&CK Enterprise tactics + techniques. Each row carries the technique ID, name, tactic, and a one-paragraph description. Use the canonical MITRE source at attack.m…
- **`knowledge-pack/nerc-cip-standards`** - NERC CIP standards (CIP-002 to CIP-014)  
  _energy, energy.grid, security_ • Composite of NERC CIP standards for Bulk Electric System cyber compliance.
- **`knowledge-pack/nuclear-nrc-iaea-frameworks`** - Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)  
  _nuclear, nuclear.power, nuclear.security_ • 10 CFR 20/50/73 + IAEA INFCIRC + INPO + ROP significance determination.
- **`knowledge-pack/oecd-tp-and-beps`** - OECD TP Guidelines + BEPS + Pillar Two + §482  
  _tax, tax.transfer_pricing, finance_ • Composite of OECD TP Guidelines + BEPS actions + GloBE rules + US §482.
- **`knowledge-pack/osha-construction-1926`** - OSHA 29 CFR 1926 (Construction) + ANSI Z10 + Focus Four  
  _construction, construction.safety_ • Composite extracts of OSHA 1926 subparts + Focus Four + competent-person + ANSI Z10.
- **`knowledge-pack/owasp-top-10-llm`** - OWASP Top 10 for LLM Applications (2025)  
  _security, ai_ • OWASP Top 10 risks for LLM-based applications — prompt injection, insecure output handling, training-data poisoning, model DoS, supply chain, sensitive disclosure, plugin design, e…
- **`knowledge-pack/personal-preferences-template`** - Personal preferences template (fork + edit)  
  _cross_industry_ • A template knowledge pack that holds a single user's preferences for working with an LLM. Fork this file to your own repo and edit the entries. Loaded by persona/personal-coding-re…
- **`knowledge-pack/platform-content-policy-frameworks`** - Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)  
  _compliance, media, privacy_ • Composite reference for platform-side moderation policy: EU Digital Services Act, UK Online Safety Act 2023, US COPPA, US Section 230 limits, German NetzDG, NCMEC CyberTipline obli…
- **`knowledge-pack/radiology-acrac-fleischner`** - ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics  
  _healthcare, healthcare.radiology, healthcare.clinical_ • Composite, educational extracts of radiology citation backbone:
- **`knowledge-pack/rcra-waste-frameworks`** - RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)  
  _waste, waste.rcra_tsdf, waste.generator, waste.universal_ • RCRA Subtitle C identification + generator + transporter + TSDF + LDR + Universal Waste + Used Oil + DOT HMR.
- **`knowledge-pack/real-estate-dd-standards`** - Real estate DD standards (ALTA / ASTM ESA / Bldg Code / Zoning)  
  _real_estate, real_estate.due_diligence_ • Composite educational reference: ALTA title insurance forms + ASTM E1527-21 Phase I ESA standard + ASTM E1903-19 Phase II + IBC structural code summary + common zoning code structu…
- **`knowledge-pack/sanctions-list-shape`** - Sanctions list (shape, with placeholder entries)  
  _finance, finance.aml, finance.kyc_ • Reference SHAPE for sanctions list integration. Real data must be pulled from OFAC, UN, EU, HMT, or the institution's licensed provider; this pack illustrates the row schema, not t…
- **`knowledge-pack/space-launch-frameworks`** - Space launch + range safety + ITAR/EAR frameworks  
  _space, space.launch, space.export_control, space.orbital_ • 14 CFR Part 450 + NASA-STD-8719.25 + RCC 319 + 22 CFR ITAR + 15 CFR EAR + 25-year LEO.
- **`knowledge-pack/spdx-licenses-summary`** - SPDX licenses (summary)  
  _cross_industry, legal, software_ • Sampled summary of common SPDX licenses — permissive, copyleft, non-commercial, public-domain. For each: license_id, category, one-paragraph summary, redistribution-compatible flag…
- **`knowledge-pack/style-references-cinematic`** - Cinematic style references  
  _creative_ • Curated style descriptors for cinematic product / scene photography. Each entry is a textual descriptor of a style — lighting, color palette, composition, atmosphere — with attribu…
- **`knowledge-pack/technician-checklists`** - Technician checklists — 50 industry procedural artifacts  
  _compliance, healthcare, aviation, construction_ • Canonical written checklists / standard work that real practitioners use: WHO Surgical Safety, FAA preflight, OSHA JHA, AORN counts, HACCP CCP, NFPA 70E LOTO, MSHA pre-shift, ITIL …
- **`knowledge-pack/telco-fcc-cpni-frameworks`** - Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)  
  _telecommunications, telecommunications.fcc, telecommunications.cpni_ • Composite 47 CFR Part 4 (NORS) / Part 9 (911) / Part 64 (CPNI + STIR/SHAKEN) / CALEA + 47 USC §222.
- **`knowledge-pack/trade-export-control-frameworks`** - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)  
  _trade, trade.hts, trade.eccn, trade.itar_ • Composite educational reference: HTSUS chapters/headings, EAR Commerce Control List (Cat 0-9), ITAR USML (Categories I-XXI), OFAC sanctions programs, BIS Entity List + Unverified L…
- **`knowledge-pack/user-preference-schema`** - User preference schema (canonical shape for personal assistants)  
  _personal_productivity, cross_industry_ • Canonical schema for storing user preferences that personal- assistant harnesses load before taking action. Covers:  - Communication tone preferences (formal / casual / terse / war…
- **`knowledge-pack/verbraucherzentrale-fake-inkasso-indicators`** - Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)  
  _bureaucracy_translation, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee_ • Composite educational reference of the Verbraucherzentrale's published Fake-Inkasso indicators. Used by Sviatoslav Grabovsky's Bill_info AI to classify German payment demands as le…
- **`knowledge-pack/water-sdwa-lcrr-awia`** - Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)  
  _water_utility, water_utility.lcr, water_utility.sdwa_ • Composite of EPA drinking water regulations + critical-infrastructure cyber.

## tool

- **`tool/cbp-wro-lookup`** - US CBP Withhold Release Order + UFLPA Entity List lookup  
  _esg, supply_chain, compliance_ • Check a supplier name + geography against:  - US CBP Withhold Release Orders (active)  - US CBP Findings list (escalated WROs that became confirmed    forced-labor determinations) …
- **`tool/google-geocode`** - Google Maps Geocoding (address → lat/lng)  
  _cross_industry, retail, real_estate, transportation_ • Forward and reverse geocoding via Google Maps Geocoding API. Returns lat/lng + place_id + formatted_address + address_components (street_number / route / locality / admin_area_leve…
- **`tool/json-schema-validator`** - JSON Schema 2020-12 validator  
  _cross_industry_ • Validates a candidate JSON object against a JSON Schema 2020-12 document. Used by `processor/verify-tool-validate-criterion` to enforce structural acceptance bars on pipeline outpu…
- **`tool/lookup-icd10`** - ICD-10 lookup  
  _healthcare, healthcare.clinical_ • Lookup an ICD-10 diagnosis code by code or label substring. Returns code + label + category. Backend-agnostic; intended to bind to a local copy of the WHO ICD-10 release or to an i…
- **`tool/mitre-attack-mapper`** - MITRE ATT&CK technique mapper  
  _security, threat_intelligence, threat_intelligence.ttp_ • Map free-text TTPs to MITRE ATT&CK technique IDs (T1234.xxx). Returns the matched technique + tactic + sub-techniques + KEV status if any associated CVE is on the CISA Known Exploi…
- **`tool/opencorporates-lookup`** - OpenCorporates company lookup  
  _finance, finance.kyc, compliance, esg_ • Look up a company in the OpenCorporates global registry (220M+ legal entities). Returns: jurisdiction code, incorporation date, company status, registered address, officers, benefi…
- **`tool/presidio-pii-detect`** - Microsoft Presidio PII detection proxy  
  _cross_industry, healthcare, finance, insurance_ • Proxy to Microsoft Presidio Analyzer for PII detection. Substantially more thorough than `processor/redact-pii-text` regex baseline — supports 30+ entity types across multiple lang…
- **`tool/sanctions-check`** - Sanctions list check  
  _finance, finance.aml, finance.kyc_ • Check a normalized entity name against one or more sanctions lists (OFAC SDN, UN Consolidated, EU Consolidated, HMT, or institutional PEP). Returns matches above the configured fuz…
- **`tool/semgrep-sast-proxy`** - Semgrep SAST proxy (CWE-tagged code findings)  
  _security, security.appsec, software_ • Proxy to Semgrep CLI for static-analysis code scanning. Used by `pipeline/code-security-review` to corroborate GREP findings with a real SAST tool that has community-maintained rul…
- **`tool/swift-bic-validator`** - SWIFT BIC validator + BIC → bank metadata  
  _finance, finance.kyc, finance.aml_ • Validate an 8 or 11-character SWIFT BIC (Bank Identifier Code) and resolve it to the bank's name + country + city. Used by payment- processing + KYC + AML pipelines for counterpart…
- **`tool/transaction-graph-query`** - Transaction graph query  
  _finance, finance.aml_ • Query a transaction-graph store for one-hop or multi-hop paths between accounts / entities. Used by AML harnesses to find shell layering, circular flows, and rapid-in-rapid-out pat…
- **`tool/txt2img-sdxl`** - Text-to-Image (SDXL)  
  _creative_ • Generic SDXL text-to-image tool. Backend-agnostic — implementations include local Diffusers, Replicate, Hugging Face Inference, fal.ai, Together, or a custom OpenAPI endpoint.
- **`tool/usps-address-validator`** - USPS address validation  
  _cross_industry, retail, finance, government_ • Proxy to the USPS Address Information API. Given a US address, returns: standardized form, ZIP+4, deliverability, DPV (Delivery Point Validation) status, RDI (Residential Delivery …
- **`tool/web-search`** - Web Search  
  _cross_industry_ • Generic web search tool. Backend-agnostic — implementations include Brave, Serper, DuckDuckGo, or a self-hosted SearXNG.

## persona

- **`persona/academic-integrity-officer`** - Academic Integrity Officer (plagiarism / AI-generated / citation fabrication)  
  _education, education.higher, compliance_ • Higher-ed academic integrity persona reviewing student submissions for plagiarism, AI-generated content, fabricated citations, and honor-code violations. Cite-first — every flagged…
- **`persona/agriculture-compliance-officer`** - Agriculture Compliance Officer (USDA / GAP / GlobalGAP / NOP organic)  
  _agriculture_compliance, agriculture_compliance.gap, agriculture_compliance.usda, agriculture_compliance.organic_ • Ag-supply-chain compliance persona for farm + processor records: USDA inspection / labeling (PACA + AMS), Good Agricultural Practices (USDA GAP + GlobalGAP IFA), Organic certificat…
- **`persona/ai-governance-auditor`** - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)  
  _ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001_ • Persona for AI conformity assessment — EU AI Act high-risk + GPAI + NIST AI RMF + ISO 42001 AIMS + GDPR Art 22 automated decisions.
- **`persona/aml-analyst`** - AML Analyst  
  _finance, finance.aml_ • Anti-money-laundering analyst persona. Reasons about transaction patterns, FATF typologies, sanctions hits, and behavioral signals. Produces SAR-style narratives with cited typolog…
- **`persona/aviation-safety-investigator`** - Aviation Safety Investigator (NTSB / FAA / ICAO / SMS / ASAP)  
  _aviation, aviation.safety, compliance_ • Aviation-safety persona reviewing incident / accident reports against ICAO SMS (Safety Management System) framework, NTSB accident-investigation taxonomy, FAA AC 120-92 (SMS for Pa…
- **`persona/benefits-adjudicator`** - Government Benefits Adjudicator (SNAP / Medicaid / UI / SSI)  
  _government, government.benefits, compliance_ • Government benefits eligibility adjudicator. Applies the programmatic rules (SNAP / Medicaid / Unemployment Insurance / SSI / SSDI / TANF) to a beneficiary application, decides eli…
- **`persona/biosecurity-officer`** - Responsible Official / Biosecurity Officer (42 CFR Part 73 + BMBL 6th + WHO LBM4 + DURC/P3CO)  
  _biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc_ • Persona for select-agent registered entity Responsible Official + biosafety officer — HHS/CDC + APHIS + DURC.
- **`persona/bureaucracy-translator-cite-first`** - Bureaucracy Translator (cite-first, action-oriented, vulnerable-user safe)  
  _bureaucracy_translation, bureaucracy_translation.payment_letters, bureaucracy_translation.fraud_screening, humanitarian_ • Persona for translating bureaucratic documents (payment demands, benefits letters, court notices, immigration forms) for users with language barriers + time pressure + stress. Opti…
- **`persona/cannabis-compliance-officer`** - Cannabis Compliance Officer (State + IRS §280E + METRC + FinCEN)  
  _cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing_ • Persona for licensed cannabis cultivation / manufacturing / dispensary / testing — state regulator + §280E + METRC + FinCEN 2014 guidance.
- **`persona/cinematic-product-photographer`** - Cinematic Product Photographer  
  _creative, retail_ • A persona for image-gen prompt-shaping. Writes prompts in the voice of a working commercial photographer: specific lens, lighting, aperture, color palette, composition. Refuses cel…
- **`persona/climate-risk-analyst`** - Climate Risk Analyst (TCFD / ISSB IFRS S2 / CDP)  
  _climate, esg, esg.csrd, finance_ • Climate-risk analyst persona for reviewing corporate climate disclosures under TCFD recommendations, ISSB IFRS S2 standard, CDP questionnaires, and the EU CSRD ESRS E1 standard. Ci…
- **`persona/clinical-reasoner`** - Clinical Reasoner  
  _healthcare, healthcare.clinical_ • A clinical-reasoning persona for decision-support assistants. Cites guideline sections, flags red-flag symptoms, distinguishes differential diagnoses, and refuses to give definitiv…
- **`persona/code-consultant`** - Code consultant  
  _software, software.codereview_ • Senior-engineer persona for code review and architecture discussion. Converged from the Anthropic prompt library "Code Consultant", awesome-chatgpt-prompts "Cyber Security Speciali…
- **`persona/construction-safety-officer`** - Construction Safety Officer (OSHA 1926 / ANSI Z10 / Focus Four)  
  _construction, construction.safety, compliance_ • Construction-site safety persona reviewing daily JHA / pre-task plans, toolbox talks, near-miss reports, and OSHA 1926 compliance against the Focus Four hazards (falls, struck-by, …
- **`persona/contract-reviewer-cite-first`** - Contract Reviewer (citation-first, senior in-house counsel)  
  _legal, legal.contract, legal.compliance_ • Senior in-house counsel persona for reviewing commercial contracts: NDAs, MSAs, SOWs, vendor agreements, employment contracts, license agreements. Citation-first: every red-flag re…
- **`persona/customs-broker`** - Licensed Customs Broker (US CBP / EU UCC / WCO)  
  _customs, customs.entry, customs.tariff, customs.fta_ • Licensed customs broker persona for reviewing import entries against CBP entry filing requirements (19 CFR Part 142), classification per HTSUS, valuation per 19 CFR 152, FTA utilis…
- **`persona/defense-acquisition-officer`** - Defense Acquisition Officer (DFARS / FAR / CMMC / counterfeit parts)  
  _defense, defense.dfars, defense.counterfeit_parts, defense.cmmc_ • US DoD acquisition compliance persona for reviewing defense contracts + supplier flow-downs. Cite-first per DFARS clause / FAR section / CMMC level / NIST SP 800-171 control / SAE …
- **`persona/eeoc-hiring-officer`** - EEOC Hiring Officer (Title VII / ADA / ADEA / OFCCP)  
  _hr, hr.hiring, compliance_ • Hiring-compliance persona reviewing job postings, screening questions, interview rubrics, and hiring decisions for protected-class bias and disparate impact. Aligned to: Title VII …
- **`persona/election-integrity-analyst`** - Election Integrity Analyst (misinformation / deepfake / voter-roll)  
  _election_integrity, election_integrity.misinformation, election_integrity.deepfake, media_ • Election-integrity analyst persona for reviewing election-related content for misinformation, AI-generated synthetic media (deepfakes), coordinated inauthentic behavior, and voter-…
- **`persona/esg-auditor`** - ESG / Supply Chain Due Diligence Auditor (E + S + G)  
  _esg, esg.csddd, esg.modern_slavery, esg.csrd_ • ESG auditor persona covering the full E + S + G dimensions of supply-chain due diligence. Aligned to:
- **`persona/fact-checker`** - Fact Checker  
  _cross_industry, media_ • A careful fact-checker persona. Reasons about claims, evidence, and the gap between them. Prefers primary sources and refuses to confirm controversial claims without independent co…
- **`persona/food-safety-officer`** - Food Safety Officer (FDA FSMA / HACCP / GFSI)  
  _food_safety, food_safety.fsma, food_safety.haccp, compliance_ • Food-safety persona reviewing supplier verification, HACCP plans, recall traceability, and food-defense programs against FDA FSMA rules (PCHF / FSVP / Produce Safety / Sanitary Tra…
- **`persona/gaming-integrity-officer`** - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)  
  _gaming, gaming.aml, gaming.responsible_gambling, gaming.licensing_ • Casino + sportsbook compliance persona for reviewing player records for suspicious activity (BSA/AML for gaming under 31 CFR §1021), responsible-gambling indicators (self-exclusion…
- **`persona/gxp-auditor`** - GxP Auditor (21-CFR-11 / EU GMP Annex 11 / ICH / ALCOA+)  
  _pharma, pharma.gxp, healthcare.pharmacy, compliance_ • Pharmaceutical/biotech GxP auditor reviewing electronic records, audit trails, and validated systems against 21-CFR-11, EU GMP Annex 11, ICH Q9/Q10, ALCOA+ data-integrity principle…
- **`persona/inbox-zero-coach`** - Inbox Zero Coach (triage + reply-draft + delegation)  
  _personal_productivity_ • Email triage assistant that classifies each thread (do-now / delegate / defer / drop) and drafts reply candidates using the user's prior tone with each correspondent.
- **`persona/insurance-claims-adjuster`** - Insurance Claims Adjuster (fraud-aware, NAIC-aligned)  
  _insurance, insurance.claims, insurance.fraud, finance_ • Insurance claims adjuster persona reviewing first-notice-of-loss reports, repair invoices, medical bills, and supporting documentation for legitimacy + fraud indicators. Aligned to…
- **`persona/linux-terminal`** - Linux terminal  
  _cross_industry, software_ • The single most-cloned community persona — model behaves like a Linux terminal, returning only the would-be terminal output. Doubles as a deterministic-IO eval (the same command sh…
- **`persona/local-first-research-tutor`** - Local-first research tutor (CiteMind-style)  
  _education, privacy, compliance_ • Persona for a privacy-preserving, source-grounded study assistant that answers strictly from the provided PDF + retrieved chunks + concept graph. Never invents facts beyond the doc…
- **`persona/ma-dd-counsel`** - M&A Due Diligence Counsel (financial / legal / IP / customer / HR / tax)  
  _m_and_a, m_and_a.due_diligence, legal, finance_ • Senior M&A counsel persona reviewing target company DD across 6 classic streams: financial (audited financials, working capital, EBITDA adjustments), legal (litigation, regulatory,…
- **`persona/maritime-safety-officer`** - Maritime Safety Officer (IMO SOLAS / MARPOL / ISM / STCW)  
  _maritime, maritime.safety, compliance_ • Maritime-safety persona reviewing vessel inspection reports, port- state control records, ISM Code SMS audits, MARPOL compliance, ISPS port security, and STCW crew certifications. …
- **`persona/math-tutor`** - Math tutor  
  _education, education.tutoring_ • Patient math-tutor persona that uses Socratic prompts and step-by-step reasoning. Diagnoses what the student understands before introducing new material. Useful baseline for `pipel…
- **`persona/nerc-cip-analyst`** - NERC CIP Compliance Analyst (Bulk Electric System cyber)  
  _energy, energy.grid, compliance, security_ • Critical-infrastructure cybersecurity persona reviewing Bulk Electric System (BES) cyber assets against NERC CIP-002 through CIP-014 standards: asset categorization, security manag…
- **`persona/nuclear-safety-inspector`** - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)  
  _nuclear, nuclear.nrc, nuclear.iaea, nuclear.security_ • US NRC + IAEA nuclear-safety inspection persona for power-reactor + fuel-cycle + medical-isotope facility records. Cite-first per 10 CFR (NRC) / IAEA INFCIRC + Safety Series / INPO…
- **`persona/personal-assistant`** - Personal Assistant (preference-aware, privacy-first)  
  _personal_productivity, cross_industry_ • Personal AI assistant persona that reads user preferences BEFORE taking action, never reveals private info to wrong audiences, cites the user's stated rule when declining a request…
- **`persona/personal-coding-reviewer`** - Personal code reviewer (loads user preferences)  
  _cross_industry_ • A code reviewer persona that loads the user's personal preferences before commenting. Encodes the reviewer's own style discipline (concise, no marketing-speak, no em dashes, prefer…
- **`persona/personal-writing-companion`** - Personal writing companion (loads user preferences)  
  _cross_industry_ • A writing assistant persona that loads the user's personal style preferences before drafting. Strips disallowed idioms (em dashes, hedging adjectives, marketing-speak), enforces th…
- **`persona/privacy-officer-gdpr`** - Privacy Officer (GDPR / CCPA / DSAR fulfillment)  
  _privacy, privacy.gdpr, privacy.dsar, compliance_ • Privacy officer / DPO persona reviewing Data Subject Access Requests (Art. 15), Right-to-Erasure (Art. 17), Right-to- Rectification (Art. 16), Right-to-Portability (Art. 20), Right…
- **`persona/radiologist-cite-first`** - Radiologist (citation-first, specialty radiology)  
  _healthcare, healthcare.radiology_ • Specialization of `persona/clinical-reasoner` for radiology report generation and review. Citation-first: every BI-RADS / Fleischner / ACR Appropriateness Criteria assertion is gro…
- **`persona/rcra-waste-manager`** - RCRA Hazardous Waste Manager (40 CFR Parts 260-279 + e-Manifest + DOT HMR)  
  _waste, waste.rcra_tsdf, waste.generator, waste.universal_ • Persona for RCRA TSDF + LQG / SQG / VSQG generator + Universal Waste handler + DOT hazmat.
- **`persona/real-estate-dd-analyst`** - Real Estate Due Diligence Analyst (title / environmental / structural / zoning)  
  _real_estate, real_estate.due_diligence_ • Commercial real-estate due-diligence persona reviewing property acquisition packets: title search + chain of title + ALTA survey, Phase I/II environmental site assessment (ESA), st…
- **`persona/research-analyst`** - Research Analyst  
  _cross_industry_ • A careful research analyst persona. Cites every claim, prefers primary sources, and refuses to fabricate when evidence is thin.
- **`persona/security-engineer-cite-first`** - Security Engineer (CWE-cite-first AppSec reviewer)  
  _security, security.appsec, software, software.codereview_ • AppSec reviewer persona for source-code review. Citation-first: every red-flag refers to a CWE (Common Weakness Enumeration) entry, OWASP Top 10 category, or the specific MITRE ATT…
- **`persona/space-launch-safety-officer`** - Commercial Space Launch Safety Officer (FAA Part 450 / NASA Range Safety)  
  _space, space.launch, space.export_control, space.orbital_ • Persona for licensed commercial space launch / reentry — FAA Part 450 + NASA-STD-8719.25 + ITAR/EAR USML XV / ECCN 9A515.
- **`persona/support-agent`** - Customer support agent  
  _retail, retail.support, cross_industry_ • Customer-support agent persona. Acknowledges the user's situation, confirms the goal, proposes the next concrete step. Escalates to a human if the issue cannot be solved in two mes…
- **`persona/telco-compliance-officer`** - Telco Compliance Officer (FCC Part 47 / CPNI / CALEA / TRAI)  
  _telecommunications, telecommunications.fcc, telecommunications.cpni, compliance_ • Telco compliance persona for reviewing carrier records for FCC Part 47 regulatory obligations (Universal Service Fund, robocall mitigation STIR/SHAKEN, network outage reporting), C…
- **`persona/threat-intel-analyst`** - Threat Intelligence Analyst (MITRE ATT&CK + STIX/TAXII + IOC)  
  _security, threat_intelligence, threat_intelligence.ioc, threat_intelligence.ttp_ • CTI analyst persona for IOC verification, TTP mapping to MITRE ATT&CK techniques, and threat-actor attribution analysis. Citation-first: every assertion cites the ATT&CK technique …
- **`persona/trade-compliance-officer`** - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)  
  _trade, trade.hts, trade.eccn, trade.itar_ • International-trade compliance persona reviewing product / technology exports for: HTS classification (Harmonized Tariff Schedule), ECCN classification (Export Control Classificati…
- **`persona/transfer-pricing-counsel`** - Transfer Pricing Counsel (OECD BEPS / IRC §482 / Pillar Two)  
  _tax, tax.transfer_pricing, finance, compliance_ • International tax / transfer-pricing persona reviewing intercompany transactions for arm's-length compliance against OECD Transfer Pricing Guidelines, IRC §482, BEPS Action items (…
- **`persona/translator-improver`** - Translator + improver  
  _cross_industry, creative_ • The second-most-cloned community persona. Translates input into fluent English (or any target language) AND improves the original for clarity, idiom, and register. Pairs naturally …
- **`persona/trust-and-safety-reviewer`** - Trust + Safety reviewer (platform moderation)  
  _compliance, media, privacy_ • Persona for a platform Trust + Safety reviewer applying a documented content policy to user-generated content. Handles the standard T+S categories (CSAM, NCII, terrorist content, i…
- **`persona/water-utility-compliance-officer`** - Water Utility Compliance Officer (SDWA / LCRR / AWIA)  
  _water_utility, water_utility.lcr, water_utility.sdwa, water_utility.scada_ • Drinking-water-utility compliance persona reviewing public-water- system records against EPA Safe Drinking Water Act (SDWA), Lead and Copper Rule Revisions (LCRR), Surface Water Tr…

## adapter

- **`adapter/anthropic-claude-opus`** - Anthropic Claude Opus (deep-reasoning frontier-class)  
  _ai, cross_industry_ • Anthropic Claude Opus 4.x — deeper reasoning + 1M-context variant for tasks where Sonnet is bottlenecked by reasoning depth (long legal briefs, deep-tier supplier chain traversal, …
- **`adapter/anthropic-claude-sonnet`** - Anthropic Claude Sonnet (frontier-class chat + tool-use)  
  _ai, cross_industry_ • Frontier-class generation + tool-use adapter using Anthropic's Claude Sonnet (4.x family) via the official Anthropic API. Use as the strongest generation arm in benchmarks, the "fr…
- **`adapter/bge-embeddings-local`** - BGE embeddings (local)  
  _cross_industry, ai_ • Local BGE (BAAI General Embeddings) via sentence-transformers. The small variant is 384-dim and runs on CPU; the large variant is 1024-dim and benefits from GPU. Strong English + m…
- **`adapter/deepseek-r1-distill`** - DeepSeek R1 Distill (open-weights reasoning)  
  _cross_industry_ • DeepSeek R1 distilled into Qwen/Llama bases (1.5B / 7B / 14B / 32B / 70B). Open-weights reasoning model with explicit `<think>...</think>` chain-of- thought. MIT-licensed weights. …
- **`adapter/flux-1-schnell-local`** - FLUX.1 Schnell (open-weights image generation)  
  _cross_industry, media_ • Black Forest Labs FLUX.1 Schnell — 12B parameter rectified-flow transformer for text-to-image. Apache 2.0 / FLUX.1 [dev] non-commercial license depending on variant. State-of-the-a…
- **`adapter/gemma-4-26b-vision`** - Google Gemma 4 26B-A4B-IT (multimodal vision + native multilingual)  
  _ai, cross_industry, bureaucracy_translation, humanitarian_ • Adapter for Google Gemma 4 26B Instruction-Tuned — multimodal vision (256K context), native multilingual (Ukrainian + German + many others without dedicated fine-tune), structured …
- **`adapter/google-gemini`** - Google Gemini (multimodal frontier)  
  _ai, cross_industry_ • Google Gemini frontier-class adapter — strongest of the three big-three frontier vendors on multimodal (vision + audio + video) tasks. Use when the pipeline needs to process images…
- **`adapter/llama-3-3-70b-instruct`** - Meta Llama 3.3 70B Instruct (open-weights)  
  _cross_industry_ • Meta Llama 3.3 70B Instruct — open-weights, 128k context, multilingual, function-calling. Apache-style llama 3.3 community license. Runs via Ollama (`ollama:llama3.3:70b`), vLLM, l…
- **`adapter/mistral-8x22b-instruct`** - Mistral 8x22B Instruct (Mixtral, open-weights)  
  _cross_industry_ • Mistral AI Mixtral 8x22B Instruct — sparse Mixture-of-Experts (8x22B / 39B active), Apache 2.0 license, 64k context. Runs via Ollama (`ollama:mixtral:8x22b`), vLLM, llama.cpp. Stro…
- **`adapter/nomic-embed-text-v15`** - Nomic Embed Text v1.5 (open-weights embeddings)  
  _cross_industry_ • Nomic AI nomic-embed-text-v1.5 — open-weights text embedding model, 768 dim, 8k context, outperforms ada-002 on MTEB. Apache 2.0. Runs via Ollama (`ollama:nomic-embed-text`), sente…
- **`adapter/ollama-default`** - Ollama (local default)  
  _cross_industry_ • Default local-Ollama transport. Configured for `llama3.1:8b` at `http://localhost:11434`. Override by setting `OLLAMA_HOST` and `OLLAMA_MODEL` env vars at runtime.
- **`adapter/openai-embeddings`** - OpenAI embeddings (text-embedding-3-small/large)  
  _cross_industry, ai_ • OpenAI-compatible embeddings adapter. Defaults to text-embedding-3-small (1536-dim, $0.02 / 1M tokens). Set OPENAI_API_KEY at runtime. Works against the OpenAI API directly, Azure …
- **`adapter/openai-gpt-frontier`** - OpenAI frontier-class chat + tool-use  
  _ai, cross_industry_ • OpenAI's frontier-class chat + tool-use adapter, configured for the latest GPT model at instantiation time. Use as one of the frontier arms in cross-vendor benchmarks; useful when …
- **`adapter/phi-4-instruct`** - Microsoft Phi-4 Instruct (open-weights)  
  _cross_industry_ • Microsoft Phi-4 14B Instruct — small-model, strong reasoning + code. MIT-licensed weights. Designed for on-device + edge deployments where 70B models won't fit. Runs via Ollama (`o…
- **`adapter/qwen-2-5-72b-instruct`** - Qwen 2.5 72B Instruct (Alibaba, open-weights)  
  _cross_industry_ • Alibaba Qwen 2.5 72B Instruct — multilingual (29+ languages), 128k context, strong code + math + tool use. Apache 2.0 (7B/72B) / Qwen license. Runs via Ollama (`ollama:qwen2.5:72b`…
- **`adapter/sdxl-local`** - SDXL (local Diffusers)  
  _creative_ • Local SDXL via Hugging Face Diffusers. CUDA preferred; CPU falls back to long inference times. Used by `tool/txt2img-sdxl`.
- **`adapter/vllm-awq-local`** - Local vLLM engine with AWQ-quantized weights  
  _ai_ • Adapter for serving a local LLM via vLLM with AWQ (Activation-aware Weight Quantization) weights. Used in the Kaggle "EEDI" and "AIMO 2" competitions to fit Qwen-32B / DeepSeek-R1-…

## rubric

- **`rubric/academic-integrity-quality-v1`** - Academic integrity review quality v1  
  _education, education.higher, compliance_ • Six-dimension rubric for grading an academic-integrity review.
- **`rubric/agriculture-quality-v1`** - Agriculture compliance review quality v1  
  _agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic_ • 7-dim rubric for FSMA + USDA NOP + GlobalGAP review
- **`rubric/ai-governance-quality-v1`** - AI governance audit review quality v1  
  _ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001_ • 7-dim rubric for EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22 review
- **`rubric/aml-investigation-v1`** - AML investigation v1  
  _finance, finance.aml_ • Six-dimension rubric for AML-investigation outputs. Used by `pipeline/suspicious-transaction-review`.
- **`rubric/aviation-safety-quality-v1`** - Aviation safety report quality v1  
  _aviation, aviation.safety_ • 6-dim rubric (HFACS-anchored, blame-free)
- **`rubric/benefits-adjudication-quality-v1`** - Benefits adjudication quality v1  
  _government, government.benefits, compliance_ • Eight-dimension rubric for grading a benefits-eligibility adjudication.
- **`rubric/biosecurity-quality-v1`** - Biosecurity / select agent review quality v1  
  _biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc_ • 7-dim rubric for 42 CFR 73 + BMBL 6e + DURC/P3CO review
- **`rubric/brand-safe-image-v1`** - Brand-safe image v1  
  _creative, retail_ • Five-dimension rubric for brand-safe image generation. Used by `pipeline/brand-safe-product-photo`.
- **`rubric/bureaucracy-translation-quality-v1`** - Bureaucracy translation + fraud-screen quality v1  
  _bureaucracy_translation, humanitarian, compliance_ • Ten-dimension rubric for grading a bureaucracy-translation pipeline output (e.g. Bill_info AI). Anchored in the Bill_info AI eval set (28 documents, 96% extraction, 100% redacted-f…
- **`rubric/cannabis-quality-v1`** - Cannabis compliance review quality v1  
  _cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing_ • 7-dim rubric for state cannabis + §280E + METRC + FinCEN review
- **`rubric/citemind-citation-fidelity-v1`** - CiteMind citation-fidelity rubric v1  
  _education, research, compliance_ • 7-dim rubric for evaluating source-grounded answers from a research-wiki pipeline (CiteMind shape).
- **`rubric/climate-disclosure-quality-v1`** - Climate disclosure quality v1 (TCFD/ISSB/ESRS aligned)  
  _climate, esg, finance, compliance_ • Ten-dimension rubric for grading a corporate climate disclosure against TCFD recommendations, ISSB IFRS S2 paragraphs, and ESRS E1 disclosure requirements.
- **`rubric/clinical-grounded-response-v1`** - Clinical grounded response v1  
  _healthcare, healthcare.clinical_ • Six-dimension rubric for clinical-decision-support outputs. Used by `pipeline/differential-diagnosis`.
- **`rubric/code-security-review-v1`** - Code security review v1  
  _security, security.appsec, software_ • Seven-dimension rubric for grading an AppSec code review.
- **`rubric/construction-safety-quality-v1`** - Construction safety review quality v1  
  _construction, construction.safety_ • 7-dim rubric — Focus Four + competent-person + corrective action
- **`rubric/contract-review-quality-v1`** - Contract review quality v1  
  _legal, legal.contract, legal.compliance_ • Eight-dimension rubric for grading a commercial-contract review. Used by `pipeline/contract-clause-review`.
- **`rubric/customs-quality-v1`** - Customs entry review quality v1  
  _customs, customs.entry, customs.tariff, customs.fta_ • 7-dim rubric for US CBP + UFLPA + USMCA + WCO review
- **`rubric/defense-dfars-quality-v1`** - Defense DFARS/CMMC review quality v1  
  _defense, defense.dfars, defense.cmmc_ • 7-dim rubric
- **`rubric/election-integrity-quality-v1`** - Election integrity review quality v1  
  _election_integrity, media_ • 7-dim rubric
- **`rubric/esg-env-v1`** - ESG environmental (E) sub-rubric v1  
  _esg, supply_chain, compliance, climate_ • Five-dimension rubric for grading ONLY the environmental dimension of a supplier disclosure. Aligned to CSRD ESRS E1-E5, EUDR, and CSDDD Art. 13 (climate transition plan).
- **`rubric/esg-gov-v1`** - ESG governance (G) sub-rubric v1  
  _esg, compliance, finance_ • Six-dimension rubric for grading ONLY the governance dimension of a supplier disclosure. Aligned to OECD MNE Guidelines (Chapter II general policies + Chapter VII anti-bribery), UK…
- **`rubric/esg-social-v1`** - ESG social (S) sub-rubric v1  
  _esg, supply_chain, compliance, humanitarian_ • Six-dimension rubric for grading ONLY the social dimension of a supplier disclosure. Aligned to ILO 11 forced-labor indicators, CSRD ESRS S1 (own workforce) + S2 (value-chain worke…
- **`rubric/esg-supplier-compliance-v1`** - ESG supplier compliance v1 (full E + S + G)  
  _esg, supply_chain, compliance_ • Twelve-dimension rubric for grading supplier-submitted policy texts, self-assessments, and grievance transcripts against the CSDDD, the ILO forced-labor indicators, the major natio…
- **`rubric/food-safety-quality-v1`** - Food safety review quality v1  
  _food_safety, food_safety.fsma, food_safety.haccp_ • 7-dim rubric
- **`rubric/gaming-quality-v1`** - Gaming AML + responsible-gambling review quality v1  
  _gaming, gaming.aml, gaming.responsible_ • 7-dim rubric for gaming compliance review
- **`rubric/gdpr-dsar-quality-v1`** - GDPR DSAR fulfillment quality v1  
  _privacy, privacy.gdpr, privacy.dsar, compliance_ • Eight-dimension rubric for grading a GDPR DSAR fulfillment.
- **`rubric/gxp-validation-quality-v1`** - GxP validation review quality v1  
  _pharma, pharma.gxp, compliance_ • Eight-dimension rubric for grading a GxP system validation review. Used by `pipeline/gxp-validation-review`.
- **`rubric/hr-hiring-compliance-v1`** - HR hiring compliance review quality v1  
  _hr, hr.hiring, compliance_ • Seven-dimension rubric for grading a hiring-compliance review.
- **`rubric/insurance-claim-quality-v1`** - Insurance claim review quality v1  
  _insurance, insurance.claims, insurance.fraud, finance_ • Seven-dimension rubric for grading an insurance claim review.
- **`rubric/ma-dd-quality-v1`** - M&A DD review quality v1  
  _m_and_a, m_and_a.due_diligence, legal, finance_ • 8-dim rubric across the 6 DD streams + materiality + disposition
- **`rubric/maritime-safety-quality-v1`** - Maritime safety review quality v1  
  _maritime, maritime.safety_ • 7-dim rubric
- **`rubric/nerc-cip-quality-v1`** - NERC CIP compliance review quality v1  
  _energy, energy.grid, security_ • 7-dim rubric
- **`rubric/nuclear-quality-v1`** - Nuclear safety review quality v1  
  _nuclear, nuclear.power, nuclear.security_ • 7-dim rubric for NRC 10 CFR + INPO review
- **`rubric/platform-moderation-quality-v1`** - Platform moderation review quality v1  
  _compliance, media, privacy_ • 7-dim rubric for Trust + Safety triage quality.
- **`rubric/radiology-report-quality-v1`** - Radiology report quality v1  
  _healthcare, healthcare.radiology_ • Seven-dimension rubric for grading a radiology report. Used by `pipeline/radiology-report-grading`.
- **`rubric/rcra-waste-quality-v1`** - RCRA hazardous waste review quality v1  
  _waste, waste.rcra_tsdf, waste.generator, waste.universal_ • 7-dim rubric for 40 CFR 260-279 + e-Manifest + DOT HMR review
- **`rubric/real-estate-dd-quality-v1`** - Real-estate DD review quality v1  
  _real_estate, real_estate.due_diligence_ • 7-dim rubric
- **`rubric/research-entity-v1`** - Research Entity v1  
  _cross_industry_ • Six-dimension rubric for entity research outputs. Used by `pipeline/research-entity` as its success criterion.
- **`rubric/space-launch-quality-v1`** - Space launch + range safety review quality v1  
  _space, space.launch, space.export_control, space.orbital_ • 7-dim rubric for FAA Part 450 / range safety / ITAR / orbital review
- **`rubric/telco-quality-v1`** - Telco compliance review quality v1  
  _telecommunications, telecommunications.fcc, telecommunications.cpni_ • 7-dim rubric for FCC + CPNI + CALEA + STIR/SHAKEN review
- **`rubric/threat-intel-quality-v1`** - Threat intelligence report quality v1  
  _security, threat_intelligence_ • Six-dimension rubric for grading a CTI report against the diamond-model + ATT&CK navigator + Admiralty-confidence scheme.
- **`rubric/trade-compliance-quality-v1`** - Trade compliance review quality v1  
  _trade, trade.eccn, trade.itar, trade.sanctions_ • 8-dim rubric for grading export-control reviews.
- **`rubric/transfer-pricing-quality-v1`** - Transfer-pricing review quality v1  
  _tax, tax.transfer_pricing, finance_ • 8-dim rubric
- **`rubric/verification-v1`** - Verification v1  
  _cross_industry, media_ • Four-dimension rubric for fact-verification outputs. Used by `pipeline/verify-claim-against-corpus`.
- **`rubric/water-utility-quality-v1`** - Water utility compliance review quality v1  
  _water_utility, water_utility.sdwa, water_utility.lcr_ • 7-dim rubric

## dataset

- **`dataset/academic-essay-samples`** - Synthetic academic essay samples (integrity-review test set)  
  _education, education.higher, compliance_ • Two synthetic student-essay submissions:  - sample-essay-clean.json — proper Aristotle / Kant / Mill /    Hursthouse citations, no AI artefacts, AI-disclosure present.  - sample-es…
- **`dataset/agriculture-samples`** - Agriculture compliance samples  
  _agriculture_compliance, agriculture_compliance.fsma, agriculture_compliance.organic_ • 2 synthetic farm + packing-house compliance packets
- **`dataset/ai-governance-samples`** - AI governance audit samples  
  _ai_governance, ai_governance.eu_act, ai_governance.nist_rmf, ai_governance.iso_42001_ • 2 synthetic AI system conformity packets
- **`dataset/aviation-safety-samples`** - Aviation safety samples  
  _aviation, aviation.safety_ • 2 synthetic incident reports
- **`dataset/bill-info-test-documents`** - Bill_info AI evaluation set (28 documents)  
  _bureaucracy_translation, humanitarian, humanitarian.refugee_ • The 28-document evaluation set used in Sviatoslav Grabovsky's Bill_info AI (Gemma 4 Good Hackathon — Impact Track). Mixes:  - Reddit-sourced real German Inkasso / Mahnung letters (…
- **`dataset/biosecurity-samples`** - Biosecurity / select-agent samples  
  _biosecurity, biosecurity.select_agent, biosecurity.bsl, biosecurity.durc_ • 2 synthetic select-agent registered entity packets
- **`dataset/cannabis-samples`** - Cannabis compliance samples  
  _cannabis, cannabis.cultivation, cannabis.retail, cannabis.testing_ • 2 synthetic cannabis operator packets
- **`dataset/citemind-pdf-samples`** - CiteMind PDF samples (educational, open-license)  
  _education, research_ • Educational reference PDFs (open-license) suitable for benchmarking the CiteMind pipeline: OCR fallback behavior, page-aware chunking, citation accuracy, concept-graph extraction.
- **`dataset/climate-disclosure-samples`** - Synthetic climate disclosure samples (2 cases)  
  _climate, esg, finance_ • Two synthetic corporate climate disclosures for testing `pipeline/climate-disclosure-review`:  - sample-disclosure-good.json — Acme Corp, manufacturing, board    oversight quarterl…
- **`dataset/code-review-samples`** - Synthetic code-review samples (3 cases)  
  _security, security.appsec, software_ • Three synthetic code bundles for testing `pipeline/code-security-review`. Fully synthetic — values that look like AWS keys / JWT / Slack tokens follow the format documented in AWS …
- **`dataset/construction-safety-samples`** - Construction safety samples  
  _construction, construction.safety_ • 2 synthetic site packets
- **`dataset/contract-samples`** - Synthetic commercial contract samples (3 cases)  
  _legal, legal.contract, legal.compliance_ • Three synthetic commercial contracts for testing `pipeline/contract-clause-review`. Fully synthetic — no real contract data.
- **`dataset/customs-samples`** - Customs entry samples  
  _customs, customs.entry, customs.tariff, customs.fta_ • 2 synthetic CBP entry compliance packets
- **`dataset/defense-dfars-samples`** - Defense DFARS / CMMC samples  
  _defense, defense.dfars, defense.cmmc_ • 2 synthetic DoD contract packets
- **`dataset/election-integrity-samples`** - Election integrity samples  
  _election_integrity, media_ • 2 synthetic election-content packets
- **`dataset/foodsafety-samples`** - Food safety samples  
  _food_safety, food_safety.fsma, food_safety.haccp_ • 2 synthetic facility packets
- **`dataset/gaming-samples`** - Gaming integrity samples  
  _gaming, gaming.aml, gaming.responsible_ • 2 synthetic gaming-operator compliance packets
- **`dataset/gdpr-dsar-samples`** - Synthetic GDPR DSAR samples  
  _privacy, privacy.gdpr, privacy.dsar, compliance_ • Two synthetic DSARs:  - clean: identity verified, 14-day response, all Art. 15 fields,    no-transfer, free of charge. Expected 0 hits.  - flagged: 2.5 months past deadline, no ide…
- **`dataset/gov-benefits-samples`** - Synthetic SNAP application samples  
  _government, government.benefits_ • Two synthetic SNAP applications:  - sample-snap-app-clean.json — 3-person household with minor    children, $1850 gross income (below 130% poverty for HH of 3),    ID + paystub + r…
- **`dataset/gxp-validation-samples`** - Synthetic GxP validation samples (3 cases)  
  _pharma, pharma.gxp, healthcare.pharmacy, compliance_ • Three synthetic GxP-validated-system packets for testing `pipeline/gxp-validation-review`. Fully synthetic.
- **`dataset/hr-posting-samples`** - Synthetic HR job-posting samples  
  _hr, hr.hiring, compliance_ • Two synthetic job postings:  - clean: senior backend engineer, EEO statement, ADA contact,    fluency or equivalent. Expected 0 hits.  - flagged: 'rockstar' / 'ninja' / 'young dyna…
- **`dataset/insurance-claim-samples`** - Synthetic insurance claim samples  
  _insurance, insurance.claims, insurance.fraud, finance_ • Two synthetic insurance claims:  - sample-claim-clean.json — straightforward rear-end auto claim    with police report, witness, repair estimate. Expected ~0 hits.  - sample-claim-…
- **`dataset/ma-dd-samples`** - M&A DD samples  
  _m_and_a, m_and_a.due_diligence, legal, finance_ • 2 synthetic M&A target DD packets
- **`dataset/maritime-safety-samples`** - Maritime safety samples  
  _maritime, maritime.safety_ • 2 synthetic vessel packets
- **`dataset/nerc-cip-samples`** - NERC CIP BES samples  
  _energy, energy.grid, security_ • 2 synthetic BES Cyber System packets
- **`dataset/nuclear-samples`** - Nuclear safety samples  
  _nuclear, nuclear.power, nuclear.security_ • 2 synthetic nuclear-plant compliance packets
- **`dataset/radiology-report-samples`** - Synthetic radiology report samples (3 cases, fully synthetic)  
  _healthcare, healthcare.radiology_ • Three synthetic radiology reports for testing `pipeline/radiology-report-grading`. Fully synthetic — no real patient data.
- **`dataset/rcra-waste-samples`** - RCRA hazardous waste samples  
  _waste, waste.rcra_tsdf, waste.generator, waste.universal_ • 2 synthetic generator / TSDF packets
- **`dataset/realestate-dd-samples`** - Real-estate DD samples  
  _real_estate, real_estate.due_diligence_ • 2 synthetic real-estate DD packets
- **`dataset/space-launch-samples`** - Space launch readiness samples  
  _space, space.launch, space.export_control, space.orbital_ • 2 synthetic launch readiness packets
- **`dataset/supplier-disclosure-pack-schema`** - Supplier disclosure pack schema (canonical input shape)  
  _esg, supply_chain, compliance_ • Canonical input shape that `pipeline/supplier-policy-grading` and `pipeline/deep-tier-supplier-audit` accept as the supplier disclosure pack. Records the JSON Schema of the supplie…
- **`dataset/telco-samples`** - Telco compliance samples  
  _telecommunications, telecommunications.fcc, telecommunications.cpni_ • 2 synthetic carrier compliance packets
- **`dataset/threat-intel-samples`** - Synthetic threat-intelligence report samples  
  _security, threat_intelligence_ • Synthetic CTI report samples for testing `pipeline/threat-intel-ioc-review`. Includes IOCs (file hashes, IPs, domains, URLs, mutexes, CVEs, ATT&CK technique IDs, BTC addresses) dra…
- **`dataset/trade-export-samples`** - Synthetic trade-export transaction samples  
  _trade, trade.eccn, trade.itar, trade.sanctions_ • Two synthetic exports:  - clean: standard laptops to Singapore, EAR99, B-list destination,    no Entity-list hits, no license required. Expected 0 hits.  - flagged: Iran destinatio…
- **`dataset/transfer-pricing-samples`** - Transfer pricing samples  
  _tax, tax.transfer_pricing, finance_ • 2 synthetic MNE TP packets
- **`dataset/water-utility-samples`** - Water utility compliance samples  
  _water_utility, water_utility.sdwa, water_utility.lcr_ • 2 synthetic Public Water System packets

## processor

- **`processor/action-sampler-multi-rollout`** - Action sampler — N parallel rollouts  
  _ai, software_ • Sample N independent action trajectories for an agent task; return the trajectories + final-state candidates for downstream judging. The N candidates can be reviewed by a separate …
- **`processor/address-parse-standardize`** - Address parse + standardize (USPS Pub 28 / libpostal)  
  _cross_industry_ • Parse a free-form postal address into components (street_number, street_name, suite, city, state, postal_code, country) and standardize them to USPS Pub 28 + libpostal conventions.…
- **`processor/audio-to-text-whisper`** - Audio to text (Whisper)  
  _cross_industry_ • Speech-to-text via a Whisper-family model. Returns transcript + per-segment timestamps + detected language. Wraps `openai-whisper`, `faster-whisper`, or `distil-whisper` based on t…
- **`processor/audit-trace-emitter`** - Audit trace emitter  
  _cross_industry_ • Emit a per-step audit trace including hashed input/output, model version, adapter, applied layers, latency, and cost. Writes to a configured sink (local JSONL, Loki, OpenTelemetry,…
- **`processor/calendar-slot-finder`** - Calendar slot finder (preference-aware)  
  _personal_productivity_ • Given the user's calendar + their preferences (no-meeting hours, focus blocks, preferred meeting hours), find N candidate slots for a new meeting. Honors duration, time-zone, atten…
- **`processor/checklist-evaluator`** - Checklist evaluator (GO/NO-GO)  
  _compliance, healthcare, aviation, energy_ • Reads a named procedural checklist (knowledge-pack/technician-checklists record) plus a candidate input, returns per-item disposition (verified|unverified|nogo) + overall verdict (…
- **`processor/citation-coverage`** - Citation coverage verifier  
  _cross_industry_ • Verify that every factual sentence in a response carries at least one citation marker (e.g. `[1]`, `[smith-2026]`). Returns coverage ratio and a list of uncited sentences for re-pr…
- **`processor/community-summary-mapreduce`** - Community-summary map-reduce (GraphRAG global)  
  _ai, cross_industry_ • Per-community map step (LLM summarizes each Leiden community), then reduce step combines partial answers across communities. The core primitive of GraphRAG's global-search mode.
- **`processor/concept-graph-extractor`** - Concept graph extractor  
  _education, research, esg, compliance_ • Extract typed concept-graph nodes + edges from chunked text. Node types: concept, term, person, dataset, method, equation. Edge types: depends_on, cited_by, sub_concept, contradict…
- **`processor/context-window-packer`** - Context-window packer (Lost-in-the-middle aware)  
  _cross_industry_ • Reorganize retrieved chunks into the model's context window so the most important content lands at the BEGINNING and END of the window (Liu et al. 2023 "Lost in the Middle"). Also …
- **`processor/cost-ceiling-gate`** - Cost ceiling gate  
  _cross_industry_ • Reject a pipeline run if the predicted USD cost exceeds the budget configured for the calling pipeline / user. Uses token-count estimates + adapter pricing to predict cost.
- **`processor/cost-meter`** - Cost meter  
  _cross_industry_ • Emit per-call USD cost accounting given (adapter_ref, input_tokens, output_tokens, cached_tokens). Resolves the adapter's pricing card, multiplies, and writes a metering row to the…
- **`processor/cross-encoder-reranker`** - Cross-encoder reranker  
  _cross_industry, ai_ • Re-rank a list of retrieved candidates with a cross-encoder model (BAAI/bge-reranker-base, Cohere rerank-v3, or similar). Takes top-N candidates from a hybrid retriever and returns…
- **`processor/date-parse-multiformat`** - Date parse multi-format → ISO 8601  
  _cross_industry_ • Parse any date string in 50+ common formats (MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD, Mar 5 2025, 5-Mar-25, 1709589600 epoch, ISO 8601 fragments, RFC 2822) into a normalized ISO 8601 da…
- **`processor/document-grader`** - Per-document relevance grader (Self-RAG)  
  _ai, cross_industry_ • Score each retrieved document for relevance to the user query. Emits per-doc grade ∈ {relevant, irrelevant, ambiguous} with a confidence score. Used by Self-RAG and CRAG to filter …
- **`processor/embedder-minilm`** - Text embedder (MiniLM-L6-v2)  
  _cross_industry_ • Generate 384-dimensional text embeddings using `sentence-transformers/all-MiniLM-L6-v2`. Suitable for catalog semantic search, RAG retrieval, and de-duplication. Replace with a hig…
- **`processor/entity-resolution-link`** - Entity resolution: cluster records into entities  
  _cross_industry, finance, healthcare, government_ • Given N records, cluster those that refer to the same real-world entity (person, organization, address). Combines:  1. Blocking on canonical fields (zip, last name initial, alpha-2…
- **`processor/escalate-human-review`** - Escalate to human reviewer  
  _cross_industry_ • Route an output (and its full trace + context) to a human reviewer queue. Used when a safety gate fires, a confidence threshold is not met, or a red-flag classifier triggers. Plugg…
- **`processor/hallucination-scorer`** - Hallucination scorer (SelfCheckGPT-style)  
  _cross_industry_ • Score per-sentence hallucination probability by sampling N alternative generations from the same model, then measuring semantic agreement between them. Sentences that vary widely a…
- **`processor/hybrid-bm25-vector-retrieve`** - Hybrid BM25 + vector retrieve  
  _education, research, compliance_ • Combine BM25 lexical scoring with vector cosine similarity (reciprocal rank fusion) for retrieval. Returns top-k chunks with merged ranking, preserving page anchors for citation.
- **`processor/hyde-query-expander`** - HyDE query expander  
  _cross_industry_ • Hypothetical Document Embeddings (HyDE): generate a hypothetical *answer* to the user's query, then embed that hypothetical answer for retrieval instead of (or in addition to) the …
- **`processor/inject-datetime-locale`** - Inject datetime + locale into prompt  
  _cross_industry_ • Replace placeholders like `{{now}}`, `{{today}}`, `{{user_timezone}}`, `{{user_locale}}`, `{{user_currency}}` in the prompt template with the actual values at request time. Fixes t…
- **`processor/inject-output-schema`** - Inject output schema directive  
  _cross_industry, ai_ • Render a target JSON Schema (or Pydantic model) into the prompt as an instruction the model is asked to follow. Pairs with `processor/json-schema-repair` on the response side: if t…
- **`processor/intent-dispatcher`** - Intent dispatcher  
  _cross_industry_ • Classify an incoming message into one of N intents and route to the appropriate downstream pipeline. Backend can be a classifier rule pack, a small local model, or a keyword router…
- **`processor/iso-country-normalize`** - ISO country code normalize (alpha-2 / alpha-3 / numeric / name)  
  _cross_industry_ • Resolve any country reference — alpha-2, alpha-3, numeric, English name, French name, common alias — to canonical ISO 3166-1 codes. Returns alpha-2, alpha-3, numeric, English short…
- **`processor/iterative-revise-loop`** - Iterative revise loop  
  _cross_industry_ • The "send the response back to the LLM with accumulating context" primitive. Loops:   1. Run an inner harness call.   2. Run one or more verification processors on the response.   …
- **`processor/json-schema-repair`** - JSON Schema repair + validate  
  _cross_industry_ • Parse and repair JSON inside a model response, then validate against a JSON Schema. On failure, returns `valid: false` plus the schema errors so the upstream harness can re-prompt …
- **`processor/llm-judge`** - LLM-as-judge  
  _cross_industry_ • Generic LLM-as-judge wrapper. Given (candidate response, rubric, context), returns a per-dimension score with rationale and a weighted-sum overall score. Independent of the model u…
- **`processor/llmlingua-context-compressor`** - LLMLingua context compressor  
  _cross_industry_ • Compress long context (retrieved RAG chunks or prior conversation turns) by selectively pruning low-information tokens before the model sees them. Implementations include LLMLingua…
- **`processor/local-embedder`** - Local embedder (Ollama / nomic / mxbai)  
  _education, research, compliance, privacy_ • Embed text chunks via a local embedding model (Ollama nomic-embed-text / mxbai-embed-large / etc.). No network round-trip; embeddings stored locally.
- **`processor/memory-conversational-store`** - Conversational memory store  
  _cross_industry_ • Read / write conversational memory keyed by (user_id, session_id). Stores the last N turns plus a compressed summary for older turns. Pluggable backend: SQLite (default), Redis, Po…
- **`processor/multi-vector-fusion`** - Multi-vector / multi-query fusion (RRF + weighted)  
  _ai, cross_industry_ • Fuse N ranked candidate lists from independent retrievers (sparse + dense + graph + cross-encoder reranker output) via Reciprocal Rank Fusion or weighted score blending. Returns a …
- **`processor/name-canonicalize`** - Person-name canonicalize (Western + East-Asian)  
  _cross_industry_ • Canonicalize a person name string into structured components: given_name, family_name, middle_names, suffix, honorific. Handles the East-Asian convention where family name comes fi…
- **`processor/nsfw-image-classifier`** - NSFW image classifier  
  _creative, media_ • Lightweight NSFW image classifier (CLIP-based zero-shot or a fine-tuned head). Returns probability of NSFW content; pipelines bind to a threshold via the calling rule pack.
- **`processor/official-sources-checker`** - Official-sources analyzer  
  _cross_industry, media, government, healthcare_ • Verify retrieved candidates against an allowlist of authoritative sources (gov, intergovernmental, academic, standards bodies). Returns per-candidate flags:   - is_official: bool  …
- **`processor/page-aware-chunker`** - Page-aware chunker  
  _education, research, compliance_ • Split page-extracted text into ~800-token chunks with 120-token overlap; preserve the (page, span) coordinates on every chunk so downstream answers can cite back to the page + span…
- **`processor/pdf-extract-with-ocr-fallback`** - PDF extract with OCR fallback (CiteMind shape)  
  _education, compliance, legal, research_ • Extract embedded PDF text page by page; fall back to OCR (Tesseract / PaddleOCR / similar) for pages whose embedded-text yield is below threshold (scanned pages, image-heavy figure…
- **`processor/pdf-to-text`** - PDF to text  
  _cross_industry_ • Convert a PDF (extractable layer + optional OCR fallback) into plain text with page breaks preserved. Returns text plus per-page byte offsets so downstream chunkers can attribute c…
- **`processor/persona-set-generator`** - Persona-set generator (STORM)  
  _ai, media, education_ • Spawn N personas with distinct perspectives on a topic. Used by STORM's multi-perspective curation and by multi-agent debate pipelines. Each persona carries a role, an angle, prior…
- **`processor/phone-normalize-e164`** - Phone number normalize → E.164 (Google libphonenumber)  
  _cross_industry_ • Parse free-form phone numbers into E.164 international format (+CCNNNNNNNNNNNN) using Google libphonenumber conventions. Returns the E.164 string + country code + number type (mobi…
- **`processor/preference-loader`** - User preference loader  
  _personal_productivity, cross_industry_ • Load the user's preference file from `knowledge-pack/user-preference-schema` (or per-user overrides), resolve any inheritance from defaults, and emit a structured preference object…
- **`processor/prompt-injection-detector`** - Prompt-injection detector  
  _cross_industry, security_ • Detect prompt-injection / jailbreak attempts in user input, retrieved documents, or tool results. Two-tier: a fast regex / classifier first pass plus an optional small-model classi…
- **`processor/reasoning-framework-selector`** - Reasoning framework selector  
  _cross_industry, ai_ • Pick a reasoning framework (CoT / ReAct / Tree-of-Thoughts / Skeleton-of-Thought / Program-of-Thought / Self-Consistency / none) based on the task profile. Cheap heuristic up front…
- **`processor/recipient-tone-history`** - Recipient tone-history loader  
  _personal_productivity_ • Load the user's prior N email / chat exchanges with a specific recipient, summarize the tone signals (formality, length, warmth, sign-off style), and emit a tone-profile that downs…
- **`processor/recursive-character-chunker`** - Recursive character chunker  
  _cross_industry_ • Split text into chunks using a recursive character splitter (LangChain-style) that prefers paragraph → sentence → word boundaries. Returns chunks with overlap + per-chunk byte offs…
- **`processor/redact-pii-text`** - Redact PII from text (English-centric, MS Presidio-compatible)  
  _cross_industry, healthcare, finance, esg_ • Strip PII from free-form text before downstream LLM calls or hub sharing. Detects: email, phone, IBAN, SSN, passport, national-ID, full names (NER), street addresses, dates of birt…
- **`processor/runtime-tool-selector`** - Runtime tool selector (Toolformer / pydantic-ai)  
  _ai, cross_industry_ • Given a user query + a large registry of tools, semantically select the top-K most likely-relevant tools to expose to the model. Avoids overflowing the context window with every to…
- **`processor/self-consistency-sampler`** - Self-consistency sampler  
  _cross_industry_ • Run N parallel samples of a chain-of-thought reasoning prompt, then majority-vote on the final answer (Wang et al. 2023). Robust to arithmetic and reasoning errors that a single sa…
- **`processor/self-refine-critique`** - Self-Refine critique loop  
  _cross_industry_ • Critique-and-revise loop (Madaan et al. 2023). The same model first drafts an answer, then critiques its own draft against a rubric, then revises. Iterates up to `max_iterations`. …
- **`processor/skeleton-outliner`** - Skeleton outliner (Skeleton-of-Thought)  
  _ai, media, education_ • Generate a skeleton (bullet outline) for a long-form output, then return the outline so parallel sub-expansion can fan out per bullet. Used by Skeleton-of-Thought, STORM, and any p…
- **`processor/structured-to-prose`** - Structured JSON → prose normalizer (for GREP-style rule packs)  
  _esg, supply_chain, compliance, cross_industry_ • Walk a JSON object and emit one prose-like line per leaf value, flattening dict keys into space-separated labels. The output shape is what GREP-family rule packs (regex on natural-…
- **`processor/sub-question-decomposer`** - Sub-question decomposer  
  _cross_industry_ • Break a compound question into N atomic sub-questions, each independently answerable. Used by `pipeline/multi-doc-qa-subquestion` and similar LlamaIndex SubQuestionQueryEngine flow…
- **`processor/two-time-retrieval`** - Two-time retrieval (refine query, re-retrieve)  
  _ai, education_ • Retrieve top-K with the raw query, ask an LLM to compose a refined query incorporating what was found, then re-retrieve. Final retrieval set is the second pass (or union of both, d…
- **`processor/verify-composite-criterion`** - Composite (AND/OR/NOT) success-criterion evaluator  
  _cross_industry_ • Evaluates one `kind: composite` success criterion. Combines child criteria with AND / OR / NOT semantics. Children may themselves be composite — arbitrarily deep nesting allowed. S…
- **`processor/verify-deterministic-criterion`** - Deterministic comparison success-criterion evaluator  
  _cross_industry_ • Evaluates one `kind: deterministic` success criterion. Resolves a target value from the pipeline trace and applies a comparison operator (>, >=, <, <=, ==, !=, in, not_in, is_truth…
- **`processor/verify-llm-judge-criterion`** - LLM-as-judge success-criterion evaluator  
  _cross_industry_ • Evaluates one `kind: llm_judge` success criterion. Wraps `processor/llm-judge` but with an explicit pass/fail threshold and a clear criterion label. The judge adapter is configurab…
- **`processor/verify-regex-criterion`** - Regex success-criterion evaluator  
  _cross_industry_ • Evaluates one `kind: regex` success criterion. Given a target path (resolved from the pipeline trace) + a pattern + a `must_match` flag, returns a pass/fail record with the matched…
- **`processor/verify-semantic-criterion`** - Semantic-similarity success-criterion evaluator  
  _cross_industry_ • Evaluates one `kind: semantic` success criterion. Computes embedding similarity between the target text and each reference topic in `must_cover`; passes if EVERY topic clears `simi…
- **`processor/verify-tool-validate-criterion`** - Tool-validation success-criterion evaluator  
  _cross_industry_ • Evaluates one `kind: tool_validate` success criterion. Invokes an external tool (e.g. `tool/json-schema-validator`, `tool/run-unit-tests`, `tool/iban-checker`) against the target. …
- **`processor/vllm-batched-sampling`** - vLLM batched sampling (SamplingParams + logits processors)  
  _ai_ • Issue an LLM batch through vLLM's `LLM.generate` (or `llm.chat`) with `SamplingParams`. Optional `logits_processors` (e.g. logits-processor-zoo: SuppressTokens, FixedTokenBias, All…

## pattern

- **`pattern/anti-eval-leak-into-train`** - Anti-pattern: Evaluation set leaked into training data  
  _cross_industry_ • Benchmark records (or close paraphrases) end up in training corpus — fine-tune, RAG index, exemplar set. Reported scores inflate; downstream consumer cannot trust the benchmark; ev…
- **`pattern/anti-grep-as-classifier`** - Anti-pattern: GREP regex as a classifier  
  _cross_industry_ • Stretching pattern-match rules to classify intent / sentiment / risk / topic when the signal is semantic, not lexical. Regex catches the surface form ('passport held') but misses s…
- **`pattern/anti-llm-as-judge-without-rubric`** - Anti-pattern: LLM-as-judge without rubric  
  _cross_industry_ • Asking an LLM 'is this output good?' with no rubric, no scoring dimensions, no calibration set. Scores drift by model version, sampling temperature, even prompt order. The judge be…
- **`pattern/anti-missing-determinism-seed`** - Anti-pattern: Missing determinism / seed control  
  _cross_industry_ • Pipeline reports a finding 'pesticide REI violation' on Tuesday + clean on Wednesday for the same input. Temperature > 0, no seed, no run-id, no model-version pin. Disagreements be…
- **`pattern/anti-no-audit-trace`** - Anti-pattern: No audit trace  
  _cross_industry, compliance_ • Pipeline returns a verdict (approved / denied / NO-GO / critical-finding) without logging which step produced it, which model arm answered, which evidence was retrieved, what promp…
- **`pattern/anti-no-pii-redact-before-model`** - Anti-pattern: PII reaches the model without redaction  
  _cross_industry, healthcare, finance, privacy_ • Sending PHI / SSN / financial PII / credentials directly into a hosted LLM call. Even when the model 'doesn't store data,' the data is on the wire + in the provider's transient log…
- **`pattern/anti-over-prompting-as-crutch`** - Anti-pattern: 5,000-token system prompt as a crutch  
  _cross_industry_ • Workarounds for missing structured infrastructure get stuffed into the system prompt: 'always cite sources,' 'never invent data,' 'use these 47 industry terms,' 'follow this 12-ste…
- **`pattern/anti-silent-tool-failure`** - Anti-pattern: Silent tool failure (empty result == success)  
  _cross_industry, compliance_ • Tool returns an empty list or null on error; the calling agent treats empty as 'nothing found' and continues. Sanctions lookup that times out returns []; agent reports 'no matches'…
- **`pattern/anti-single-model-no-fallback`** - Anti-pattern: Single-model dependency with no fallback  
  _cross_industry_ • Pipeline hard-codes one model adapter. Production fails entirely when the model has an outage, rate-limit, region-block, deprecation, or quality regression. No graceful degradation…
- **`pattern/anti-un-cited-extraction`** - Anti-pattern: Un-cited extraction  
  _cross_industry, compliance, legal, healthcare_ • Pipeline extracts fields from a document but the output does not include a (page, span) pointer back to the source. Downstream consumers cannot verify; mistakes propagate silently;…
- **`pattern/chain-of-density`** - Chain-of-Density (iterative dense summarization)  
  _ai, media, cross_industry_ • Iteratively compress a summary by N rounds: each round the model identifies a missing entity / fact from the source and rewrites the summary to include it WHILE keeping length cons…
- **`pattern/chain-of-verification`** - Chain-of-Verification (CoVe)  
  _ai, cross_industry_ • Generate a draft response, decompose it into atomic verifiable claims, execute independent verification queries per claim, and emit a final response that drops or revises unverifia…
- **`pattern/composable-success-criteria`** - Composable success criteria (regex + semantic + LLM-judge + deterministic + tool + composite)  
  _cross_industry, ai, compliance_ • Treat success criteria as first-class composable artifacts rather than a single rubric+threshold check. Six concrete criterion kinds combine via AND / OR / NOT into arbitrary boole…
- **`pattern/concept-graph-from-text`** - Concept graph from text  
  _education, esg, supply_chain, compliance_ • Promote relationships between entities mentioned in source text to first-class graph nodes + edges. Each node + edge is source-anchored (page, span). Generalizes from CiteMind's Bo…
- **`pattern/corrective-rag`** - Corrective RAG (CRAG)  
  _ai, cross_industry_ • RAG with a three-state retrieval evaluator. After initial retrieval, an evaluator classifies the retrieval as {correct, incorrect, ambiguous}. Correct → strip-and-recompose; incorr…
- **`pattern/critical-tier-output-override`** - Critical-tier output override (one dominant message on critical finding)  
  _ai, cross_industry, bureaucracy_translation, humanitarian_ • When a classifier / judge step finds a critical-tier issue, every user-facing output component is FORCED into one consistent message rather than mixing the issue with the original …
- **`pattern/diamond-model-attribution`** - Diamond Model attribution (CTI threat-actor analysis)  
  _security, threat_intelligence_ • Classical CTI threat-actor attribution framework. An incident is analyzed across 4 vertices: Adversary (who) + Capability (how) + Infrastructure (with what) + Victim (against whom)…
- **`pattern/dpo-from-pairwise`** - Direct Preference Optimization (DPO) from pairwise preferences  
  _cross_industry_ • Skip explicit reward modeling + PPO; directly optimize policy against pairwise (chosen, rejected) preferences via a closed-form log-likelihood loss. Trains with the same compute as…
- **`pattern/evaluator-optimizer`** - Evaluator-Optimizer  
  _ai, cross_industry_ • One LLM call generates a candidate output; a second LLM (or processor) evaluates against a rubric and provides specific feedback; the generator revises. Loops until the evaluator p…
- **`pattern/go-nogo-checklist-gate`** - GO/NO-GO checklist gate  
  _compliance, healthcare, aviation, energy_ • Wrap a candidate action with an explicit checklist whose unmet items hard-gate the action. Models the human-performance discipline that real-world surgical teams, flight crews, min…
- **`pattern/hyde`** - HyDE (Hypothetical Document Embeddings)  
  _ai, cross_industry_ • Generate a hypothetical answer to the query (allowing hallucination), then embed THAT answer instead of (or alongside) the query, and retrieve against the embedding. Reduces query-…
- **`pattern/k-anonymity-aggregation`** - K-anonymity + HMACed-key cross-organization aggregation  
  _security, esg, compliance, finance_ • Share *aggregated* signal across organizations without revealing per-org provenance. Each org HMACs the key (broker ID, supplier hash, address) with a hub-published salt so the sam…
- **`pattern/local-first-with-cited-answers`** - Local-first with cited answers  
  _education, privacy, compliance, healthcare_ • Privacy-preserving RAG pattern: all PDF content + chunks + embeddings + chat history live on the user's machine; model inference goes through a local provider (e.g. Ollama) by defa…
- **`pattern/lora-merge-and-deploy`** - LoRA merge + deploy (or hot-swap)  
  _cross_industry_ • Two production deployment shapes for LoRA-trained models: (a) merge the LoRA delta into base weights once + serve as a single monolithic model — zero adapter overhead per request, …
- **`pattern/multi-agent-debate`** - Multi-Agent Debate  
  _ai_ • Two or more LLM instances argue different sides of a question, with a judge LLM scoring the arguments. Used for hard reasoning problems where stress-testing a position improves acc…
- **`pattern/naive-rag`** - Naive RAG  
  _ai, cross_industry_ • Single-shot retrieval-augmented generation: embed query, retrieve top-k chunks, concatenate into the prompt, generate. The baseline every other RAG variant compares against.
- **`pattern/orchestrator-workers`** - Orchestrator-Workers  
  _ai, cross_industry_ • A central orchestrator decomposes the task and delegates parallel subtasks to worker agents (sometimes with different personas / tools per worker). Workers return structured result…
- **`pattern/peft-lora-adapter-insertion`** - PEFT LoRA adapter insertion  
  _cross_industry_ • Train tiny low-rank decomposition matrices A∈R^(d×r), B∈R^(r×d) inserted alongside frozen base weights W. Forward pass becomes W·x + B·A·x. Only A + B are trained; base stays froze…
- **`pattern/personal-preference-layer`** - Personal preference layer  
  _cross_industry_ • Treat individual user preferences as a first-class layer on top of any pipeline. The layer loads a preference knowledge pack at run-start, applies it to the persona system prompt, …
- **`pattern/plan-and-execute`** - Plan-and-Execute  
  _ai, cross_industry_ • Separate planning from execution. A planner LLM produces an explicit step list; an executor (often a different / cheaper model) runs each step. After execution, a re-planner can up…
- **`pattern/prompt-chaining`** - Prompt Chaining  
  _ai, cross_industry_ • Break a task into a SEQUENCE of LLM calls where each call's output is the next call's input. The simplest agent pattern — no tools, no loops, no routing — just a linear chain. Usef…
- **`pattern/qlora-4bit-finetune`** - QLoRA 4-bit fine-tune  
  _cross_industry_ • Load base model in 4-bit NF4 quantization + freeze + insert LoRA adapters that train in BF16/FP16. Enables fine-tuning a 70B model on a single 48GB GPU (or 24GB with aggressive off…
- **`pattern/raft-retrieval-aug-finetune`** - RAFT (Retrieval-Augmented Fine-Tuning)  
  _ai, cross_industry_ • Fine-tune an LLM on (question, retrieved_docs_including_distractors, reasoning_chain, gold_answer) tuples so the model learns to USE the retrieved docs at inference time AND ignore…
- **`pattern/rag-fusion`** - RAG-Fusion  
  _ai, cross_industry_ • Generate N rewrites of the user query, run retrieval for each, and fuse the ranked lists via Reciprocal Rank Fusion. Outperforms single- query retrieval when the user's wording dif…
- **`pattern/react`** - ReAct (Reason + Act)  
  _ai, cross_industry_ • Interleave reasoning steps with tool calls. At each step the model emits one of: Thought (free-form reasoning), Action (tool call), Observation (tool result fed back). Loop until t…
- **`pattern/reflexion`** - Reflexion  
  _ai_ • Add a verbal self-reflection step after each failed attempt. The reflection is appended to memory and shown to the model on the next attempt. Bounded by `max_iters`. Captures the "…
- **`pattern/refuse-on-redacted`** - Refuse-on-redacted (null over hallucination on missing fields)  
  _ai, cross_industry, bureaucracy_translation, healthcare_ • When an input field is missing, redacted, or unreadable, return `null` (or its user-language equivalent — 'unknown' / 'невідомо' / 'unbekannt') rather than hallucinating a plausibl…
- **`pattern/routing`** - Routing  
  _ai, cross_industry_ • Classify the input and dispatch to the appropriate specialized sub-pipeline. A classifier (LLM, embedder + threshold, or rule pack) picks a route; the chosen sub-pipeline handles t…
- **`pattern/self-rag`** - Self-RAG  
  _ai, cross_industry_ • Reflection-token retrieval-augmented generation. The model first decides whether to retrieve at all, then grades each retrieved document for relevance, generates an answer grounded…
- **`pattern/self-refine`** - Self-Refine  
  _ai, cross_industry_ • Single critique-and-revise pair. The model drafts an answer, then critiques its own draft against a rubric, then revises. One iteration by default; can be looped. Simpler than Refl…
- **`pattern/skeleton-of-thought`** - Skeleton of Thought (SoT)  
  _ai_ • First generate a SKELETON (bullet outline) of the answer, then expand each bullet IN PARALLEL via separate LLM calls. Stitch the expansions into the final answer. Often used for ta…
- **`pattern/source-document-to-persistent-knowledge-layer`** - Source document → persistent knowledge layer  
  _education, compliance, esg, research_ • Architectural pattern: instead of treating each chat turn as ephemeral, encode the source document as a long-lived knowledge layer (wiki pages + concept graph + study guide + bookm…
- **`pattern/step-back-prompting`** - Step-Back Prompting  
  _ai_ • Before answering, the model is prompted to derive a MORE ABSTRACT question that captures the essence of the user's question. Retrieval and reasoning then happen against the abstrac…
- **`pattern/tree-of-thoughts`** - Tree of Thoughts (ToT)  
  _ai_ • At each reasoning step, propose N candidate "thoughts", value/vote each, and expand the best ones via BFS or DFS. Backtrack on dead-ends. Generalizes chain-of-thought from a single…
- **`pattern/two-stage-extract-then-judge`** - Two-stage extract-then-judge (separate calls for extraction + classification)  
  _ai, cross_industry, bureaucracy_translation, humanitarian_ • Use two separate LLM calls instead of one combined call: the first extracts every relevant structured field, the second classifies / judges given the extracted context. Costs more …
- **`pattern/two-stage-retrieve-rerank`** - Two-stage retrieve + constrained rerank  
  _ai, education, scientific_research_ • Retrieve K candidates with a cheap embedder (BM25 / dense), then rerank with a stronger but slower model. The reranker can be: a cross-encoder, or an LLM CONSTRAINED to emit only o…
- **`pipeline/deberta-finetune-classification`** - DeBERTa-v3-large fine-tune for closed-set classification  
  _ai, cross_industry_ • DeBERTa-v3-large fine-tuning shape used as the heavy half of nearly every top Kaggle LLM-classification submission since 2023. Combined with `pipeline/tfidf-lightgbm-text-classific…
- **`pipeline/lora-qlora-pairwise-pref-finetune`** - LoRA + QLoRA pairwise-preference fine-tune (Gemma-2-9b 4-bit)  
  _ai, cross_industry_ • Production-verified fine-tune shape for the LMSYS / WSDM Chatbot Arena class of pairwise-preference competitions. Load Gemma-2-9b with 4-bit BitsAndBytes quantization, attach a PEF…
- **`pipeline/tfidf-lightgbm-text-classification`** - TF-IDF + LightGBM text classification  
  _ai, cross_industry, media_ • The non-LLM baseline that consistently wins or co-wins Kaggle text- classification competitions. Char- and word-ngram TF-IDF feature extraction → LightGBM (often stacked with SGDCl…

## Index by industry vertical

### agriculture_compliance

- `dataset/agriculture-samples` - Agriculture compliance samples
- `knowledge-pack/agriculture-compliance-frameworks` - Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)
- `persona/agriculture-compliance-officer` - Agriculture Compliance Officer (USDA / GAP / GlobalGAP / NOP organic)
- `pipeline/agriculture-compliance-review` - Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)
- `rubric/agriculture-quality-v1` - Agriculture compliance review quality v1
- `rule-pack/grep-agriculture-compliance-flags` - Agriculture compliance flags (USDA / GAP / NOP organic)

### agriculture_compliance.fsma

- `dataset/agriculture-samples` - Agriculture compliance samples
- `knowledge-pack/agriculture-compliance-frameworks` - Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)
- `pipeline/agriculture-compliance-review` - Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)
- `rubric/agriculture-quality-v1` - Agriculture compliance review quality v1

### agriculture_compliance.gap

- `persona/agriculture-compliance-officer` - Agriculture Compliance Officer (USDA / GAP / GlobalGAP / NOP organic)
- `rule-pack/grep-agriculture-compliance-flags` - Agriculture compliance flags (USDA / GAP / NOP organic)

### agriculture_compliance.organic

- `dataset/agriculture-samples` - Agriculture compliance samples
- `knowledge-pack/agriculture-compliance-frameworks` - Agriculture compliance frameworks (FSMA + USDA NOP + GAP + GlobalGAP)
- `persona/agriculture-compliance-officer` - Agriculture Compliance Officer (USDA / GAP / GlobalGAP / NOP organic)
- `pipeline/agriculture-compliance-review` - Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)
- `rubric/agriculture-quality-v1` - Agriculture compliance review quality v1
- `rule-pack/grep-agriculture-compliance-flags` - Agriculture compliance flags (USDA / GAP / NOP organic)

### agriculture_compliance.usda

- `persona/agriculture-compliance-officer` - Agriculture Compliance Officer (USDA / GAP / GlobalGAP / NOP organic)
- `rule-pack/grep-agriculture-compliance-flags` - Agriculture compliance flags (USDA / GAP / NOP organic)

### ai

- `adapter/anthropic-claude-opus` - Anthropic Claude Opus (deep-reasoning frontier-class)
- `adapter/anthropic-claude-sonnet` - Anthropic Claude Sonnet (frontier-class chat + tool-use)
- `adapter/bge-embeddings-local` - BGE embeddings (local)
- `adapter/gemma-4-26b-vision` - Google Gemma 4 26B-A4B-IT (multimodal vision + native multilingual)
- `adapter/google-gemini` - Google Gemini (multimodal frontier)
- `adapter/openai-embeddings` - OpenAI embeddings (text-embedding-3-small/large)
- `adapter/openai-gpt-frontier` - OpenAI frontier-class chat + tool-use
- `adapter/vllm-awq-local` - Local vLLM engine with AWQ-quantized weights
- `harness/code-act-jupyter` - Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)
- `knowledge-pack/owasp-top-10-llm` - OWASP Top 10 for LLM Applications (2025)
- `pattern/chain-of-density` - Chain-of-Density (iterative dense summarization)
- `pattern/chain-of-verification` - Chain-of-Verification (CoVe)
- `pattern/composable-success-criteria` - Composable success criteria (regex + semantic + LLM-judge + deterministic + tool + composite)
- `pattern/corrective-rag` - Corrective RAG (CRAG)
- `pattern/critical-tier-output-override` - Critical-tier output override (one dominant message on critical finding)
- `pattern/evaluator-optimizer` - Evaluator-Optimizer
- `pattern/hyde` - HyDE (Hypothetical Document Embeddings)
- `pattern/multi-agent-debate` - Multi-Agent Debate
- `pattern/naive-rag` - Naive RAG
- `pattern/orchestrator-workers` - Orchestrator-Workers
- `pattern/plan-and-execute` - Plan-and-Execute
- `pattern/prompt-chaining` - Prompt Chaining
- `pattern/raft-retrieval-aug-finetune` - RAFT (Retrieval-Augmented Fine-Tuning)
- `pattern/rag-fusion` - RAG-Fusion
- `pattern/react` - ReAct (Reason + Act)
- `pattern/reflexion` - Reflexion
- `pattern/refuse-on-redacted` - Refuse-on-redacted (null over hallucination on missing fields)
- `pattern/routing` - Routing
- `pattern/self-rag` - Self-RAG
- `pattern/self-refine` - Self-Refine
- `pattern/skeleton-of-thought` - Skeleton of Thought (SoT)
- `pattern/step-back-prompting` - Step-Back Prompting
- `pattern/tree-of-thoughts` - Tree of Thoughts (ToT)
- `pattern/two-stage-extract-then-judge` - Two-stage extract-then-judge (separate calls for extraction + classification)
- `pattern/two-stage-retrieve-rerank` - Two-stage retrieve + constrained rerank
- `pipeline/deberta-finetune-classification` - DeBERTa-v3-large fine-tune for closed-set classification
- `pipeline/lora-qlora-pairwise-pref-finetune` - LoRA + QLoRA pairwise-preference fine-tune (Gemma-2-9b 4-bit)
- `pipeline/tfidf-lightgbm-text-classification` - TF-IDF + LightGBM text classification
- `pipeline/audio-mel-spec-cnn-classifier` - Audio classification via mel-spectrogram + CNN (KerasCV / EfficientNet)
- `pipeline/awq-quantized-inference` - AWQ-quantized LLM inference (alternative to bitsandbytes nf4)
- `pipeline/bidirectional-lstm-sequence-prediction` - Bidirectional LSTM for sequence prediction (time-series / text)
- `pipeline/blip-clip-image-to-prompt` - BLIP + CLIP Interrogator image-to-prompt
- `pipeline/code-act-jupyter-loop` - Code-act Jupyter loop
- `pipeline/deberta-lgbm-hybrid-scorer` - DeBERTa-v3 + LightGBM hybrid scorer (with spell autocorrect)
- `pipeline/deep-research-supervisor-workers` - Deep research: supervisor + parallel workers
- `pipeline/deepseek-r1-code-interpreter-math` - DeepSeek-R1 / QwQ + Python code-interpreter for math reasoning
- `pipeline/dicom-medical-image-preprocessing` - DICOM medical image preprocessing (CT / MRI / X-ray)
- `pipeline/efficientnet-medical-imaging` - EfficientNet for medical imaging classification + segmentation
- `pipeline/knowledge-graph-from-corpus` - GraphRAG: knowledge-graph from corpus + global/local query
- `pipeline/large-model-faiss-rag` - Large-model FAISS RAG (Platypus2-70b style)
- `pipeline/lgb-xgb-catboost-ensemble` - LightGBM + XGBoost + CatBoost ensemble (tabular ML)
- `pipeline/llm-judge-essay-grading` - LLM-judge essay grading (with adversarial prompt prefix)
- `pipeline/longformer-bigbird-ner` - Long-document NER with LongFormer / BigBird
- `pipeline/mask-rcnn-coco-transfer` - Mask-RCNN with COCO transfer learning (instance segmentation + detection)
- `pipeline/multi-agent-debate-with-judge` - Multi-agent debate with judge
- `pipeline/multi-model-judging-ensemble` - Multi-model judging ensemble
- `pipeline/optuna-tabular-tuning` - Optuna hyperparameter tuning for tabular models
- `pipeline/perplexity-baseline-scoring` - Perplexity-baseline scoring
- `pipeline/quantized-llm-inference` - Quantized LLM inference (4-bit BitsAndBytes)
- `pipeline/qwen-vllm-rerank-eedi` - Qwen-32B vLLM retrieval-rerank with logits-processor constraints
- `pipeline/sd-prompt-embedding-cosine` - Stable-Diffusion prompt embedding + cosine evaluation
- `pipeline/self-rag-grade-and-revise` - Self-RAG: grade-and-revise (concrete implementation)
- `pipeline/sensor-fusion-imu-blending` - Multi-sensor fusion (IMU + thermal + ToF) with model blending
- `pipeline/sentence-transformer-finetune-retrieval` - Sentence-transformer fine-tune for retrieval / ranking
- `pipeline/storm-persona-curation-article` - STORM: persona-curation + outline-fanout article
- `pipeline/swe-patch-sample-and-review` - SWE-agent: sample N patches + reviewer judges
- `pipeline/synthetic-data-gen-with-teacher-llm` - Synthetic-data generation with teacher LLM
- `pipeline/twenty-questions-agent` - 20-questions agent (Akinator-style)
- `pipeline/two-time-retrieve-rerank` - Two-time retrieval + cross-encoder rerank
- `pipeline/unet-segmentation-tta` - U-Net medical segmentation with albumentations + TTA
- `pipeline/vllm-batch-llm-inference` - vLLM batch LLM inference (with logits-processor-zoo)
- `processor/action-sampler-multi-rollout` - Action sampler — N parallel rollouts
- `processor/community-summary-mapreduce` - Community-summary map-reduce (GraphRAG global)
- `processor/cross-encoder-reranker` - Cross-encoder reranker
- `processor/document-grader` - Per-document relevance grader (Self-RAG)
- `processor/inject-output-schema` - Inject output schema directive
- `processor/multi-vector-fusion` - Multi-vector / multi-query fusion (RRF + weighted)
- `processor/persona-set-generator` - Persona-set generator (STORM)
- `processor/reasoning-framework-selector` - Reasoning framework selector
- `processor/runtime-tool-selector` - Runtime tool selector (Toolformer / pydantic-ai)
- `processor/skeleton-outliner` - Skeleton outliner (Skeleton-of-Thought)
- `processor/two-time-retrieval` - Two-time retrieval (refine query, re-retrieve)
- `processor/vllm-batched-sampling` - vLLM batched sampling (SamplingParams + logits processors)
- `rule-pack/grep-ai-vendor-keys` - AI vendor API key detectors
- `rule-pack/grep-cloud-secrets` - Cloud provider secret detectors
- `rule-pack/grep-prompt-injection-heuristics` - Prompt-injection heuristic detectors

### ai_governance

- `dataset/ai-governance-samples` - AI governance audit samples
- `knowledge-pack/ai-governance-frameworks` - AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `persona/ai-governance-auditor` - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)
- `pipeline/ai-governance-audit` - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `rubric/ai-governance-quality-v1` - AI governance audit review quality v1
- `rule-pack/grep-ai-governance-flags` - AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

### ai_governance.eu_act

- `dataset/ai-governance-samples` - AI governance audit samples
- `knowledge-pack/ai-governance-frameworks` - AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `persona/ai-governance-auditor` - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)
- `pipeline/ai-governance-audit` - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `rubric/ai-governance-quality-v1` - AI governance audit review quality v1
- `rule-pack/grep-ai-governance-flags` - AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

### ai_governance.iso_42001

- `dataset/ai-governance-samples` - AI governance audit samples
- `knowledge-pack/ai-governance-frameworks` - AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `persona/ai-governance-auditor` - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)
- `pipeline/ai-governance-audit` - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `rubric/ai-governance-quality-v1` - AI governance audit review quality v1
- `rule-pack/grep-ai-governance-flags` - AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

### ai_governance.nist_rmf

- `dataset/ai-governance-samples` - AI governance audit samples
- `knowledge-pack/ai-governance-frameworks` - AI governance frameworks (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `persona/ai-governance-auditor` - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)
- `pipeline/ai-governance-audit` - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `rubric/ai-governance-quality-v1` - AI governance audit review quality v1
- `rule-pack/grep-ai-governance-flags` - AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)

### aviation

- `dataset/aviation-safety-samples` - Aviation safety samples
- `knowledge-pack/aviation-safety-frameworks` - Aviation safety frameworks (NTSB / FAA / ICAO / HFACS / ASAP)
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pattern/go-nogo-checklist-gate` - GO/NO-GO checklist gate
- `persona/aviation-safety-investigator` - Aviation Safety Investigator (NTSB / FAA / ICAO / SMS / ASAP)
- `pipeline/aviation-safety-review` - Aviation safety incident review
- `pipeline/faa-preflight-gate` - FAA Part 91 Before-Takeoff gate
- `processor/checklist-evaluator` - Checklist evaluator (GO/NO-GO)
- `rubric/aviation-safety-quality-v1` - Aviation safety report quality v1
- `rule-pack/grep-aviation-safety-flags` - Aviation safety incident flags (NTSB / FAA / HFACS)

### aviation.safety

- `dataset/aviation-safety-samples` - Aviation safety samples
- `knowledge-pack/aviation-safety-frameworks` - Aviation safety frameworks (NTSB / FAA / ICAO / HFACS / ASAP)
- `persona/aviation-safety-investigator` - Aviation Safety Investigator (NTSB / FAA / ICAO / SMS / ASAP)
- `pipeline/aviation-safety-review` - Aviation safety incident review
- `rubric/aviation-safety-quality-v1` - Aviation safety report quality v1
- `rule-pack/grep-aviation-safety-flags` - Aviation safety incident flags (NTSB / FAA / HFACS)

### biosecurity

- `dataset/biosecurity-samples` - Biosecurity / select-agent samples
- `knowledge-pack/biosecurity-frameworks` - Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)
- `persona/biosecurity-officer` - Responsible Official / Biosecurity Officer (42 CFR Part 73 + BMBL 6th + WHO LBM4 + DURC/P3CO)
- `pipeline/biosecurity-review` - Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)
- `rubric/biosecurity-quality-v1` - Biosecurity / select agent review quality v1
- `rule-pack/grep-biosecurity-flags` - Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags

### biosecurity.bsl

- `dataset/biosecurity-samples` - Biosecurity / select-agent samples
- `knowledge-pack/biosecurity-frameworks` - Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)
- `persona/biosecurity-officer` - Responsible Official / Biosecurity Officer (42 CFR Part 73 + BMBL 6th + WHO LBM4 + DURC/P3CO)
- `pipeline/biosecurity-review` - Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)
- `rubric/biosecurity-quality-v1` - Biosecurity / select agent review quality v1
- `rule-pack/grep-biosecurity-flags` - Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags

### biosecurity.durc

- `dataset/biosecurity-samples` - Biosecurity / select-agent samples
- `knowledge-pack/biosecurity-frameworks` - Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)
- `persona/biosecurity-officer` - Responsible Official / Biosecurity Officer (42 CFR Part 73 + BMBL 6th + WHO LBM4 + DURC/P3CO)
- `pipeline/biosecurity-review` - Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)
- `rubric/biosecurity-quality-v1` - Biosecurity / select agent review quality v1
- `rule-pack/grep-biosecurity-flags` - Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags

### biosecurity.select_agent

- `dataset/biosecurity-samples` - Biosecurity / select-agent samples
- `knowledge-pack/biosecurity-frameworks` - Biosecurity frameworks (42 CFR 73 + BMBL 6e + WHO LBM4 + DURC/P3CO)
- `persona/biosecurity-officer` - Responsible Official / Biosecurity Officer (42 CFR Part 73 + BMBL 6th + WHO LBM4 + DURC/P3CO)
- `pipeline/biosecurity-review` - Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)
- `rubric/biosecurity-quality-v1` - Biosecurity / select agent review quality v1
- `rule-pack/grep-biosecurity-flags` - Biosecurity / select-agent / BSL-3 BSL-4 / DURC flags

### bureaucracy_translation

- `adapter/gemma-4-26b-vision` - Google Gemma 4 26B-A4B-IT (multimodal vision + native multilingual)
- `dataset/bill-info-test-documents` - Bill_info AI evaluation set (28 documents)
- `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` - Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)
- `pattern/critical-tier-output-override` - Critical-tier output override (one dominant message on critical finding)
- `pattern/refuse-on-redacted` - Refuse-on-redacted (null over hallucination on missing fields)
- `pattern/two-stage-extract-then-judge` - Two-stage extract-then-judge (separate calls for extraction + classification)
- `persona/bureaucracy-translator-cite-first` - Bureaucracy Translator (cite-first, action-oriented, vulnerable-user safe)
- `pipeline/bill-info-extract-fraud-detect-recommend` - Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection
- `pipeline/medlabel-photo-to-warning` - MedLabel — photo-to-warning medicine safety pipeline
- `rubric/bureaucracy-translation-quality-v1` - Bureaucracy translation + fraud-screen quality v1
- `rule-pack/grep-fake-inkasso-fraud-flags` - Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)

### bureaucracy_translation.fraud_screening

- `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` - Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)
- `persona/bureaucracy-translator-cite-first` - Bureaucracy Translator (cite-first, action-oriented, vulnerable-user safe)
- `pipeline/bill-info-extract-fraud-detect-recommend` - Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection
- `rule-pack/grep-fake-inkasso-fraud-flags` - Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)

### bureaucracy_translation.payment_letters

- `persona/bureaucracy-translator-cite-first` - Bureaucracy Translator (cite-first, action-oriented, vulnerable-user safe)
- `pipeline/bill-info-extract-fraud-detect-recommend` - Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection

### cannabis

- `dataset/cannabis-samples` - Cannabis compliance samples
- `knowledge-pack/cannabis-frameworks` - Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)
- `persona/cannabis-compliance-officer` - Cannabis Compliance Officer (State + IRS §280E + METRC + FinCEN)
- `pipeline/cannabis-compliance-review` - Cannabis compliance review (state + §280E + METRC + FinCEN)
- `rubric/cannabis-quality-v1` - Cannabis compliance review quality v1
- `rule-pack/grep-cannabis-compliance-flags` - Cannabis compliance flags (METRC + §280E + FinCEN + COA)

### cannabis.cultivation

- `dataset/cannabis-samples` - Cannabis compliance samples
- `knowledge-pack/cannabis-frameworks` - Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)
- `persona/cannabis-compliance-officer` - Cannabis Compliance Officer (State + IRS §280E + METRC + FinCEN)
- `pipeline/cannabis-compliance-review` - Cannabis compliance review (state + §280E + METRC + FinCEN)
- `rubric/cannabis-quality-v1` - Cannabis compliance review quality v1
- `rule-pack/grep-cannabis-compliance-flags` - Cannabis compliance flags (METRC + §280E + FinCEN + COA)

### cannabis.retail

- `dataset/cannabis-samples` - Cannabis compliance samples
- `knowledge-pack/cannabis-frameworks` - Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)
- `persona/cannabis-compliance-officer` - Cannabis Compliance Officer (State + IRS §280E + METRC + FinCEN)
- `pipeline/cannabis-compliance-review` - Cannabis compliance review (state + §280E + METRC + FinCEN)
- `rubric/cannabis-quality-v1` - Cannabis compliance review quality v1
- `rule-pack/grep-cannabis-compliance-flags` - Cannabis compliance flags (METRC + §280E + FinCEN + COA)

### cannabis.testing

- `dataset/cannabis-samples` - Cannabis compliance samples
- `knowledge-pack/cannabis-frameworks` - Cannabis regulatory frameworks (state + IRS §280E + METRC + FinCEN)
- `persona/cannabis-compliance-officer` - Cannabis Compliance Officer (State + IRS §280E + METRC + FinCEN)
- `pipeline/cannabis-compliance-review` - Cannabis compliance review (state + §280E + METRC + FinCEN)
- `rubric/cannabis-quality-v1` - Cannabis compliance review quality v1
- `rule-pack/grep-cannabis-compliance-flags` - Cannabis compliance flags (METRC + §280E + FinCEN + COA)

### climate

- `dataset/climate-disclosure-samples` - Synthetic climate disclosure samples (2 cases)
- `knowledge-pack/climate-disclosure-frameworks` - Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)
- `persona/climate-risk-analyst` - Climate Risk Analyst (TCFD / ISSB IFRS S2 / CDP)
- `pipeline/climate-disclosure-review` - Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)
- `pipeline/sustainability-report-full-review` - Sustainability report full review (Climate + ESG-S + ESG-G chained)
- `rubric/climate-disclosure-quality-v1` - Climate disclosure quality v1 (TCFD/ISSB/ESRS aligned)
- `rubric/esg-env-v1` - ESG environmental (E) sub-rubric v1
- `rule-pack/grep-climate-disclosure-gaps` - Climate disclosure gap detectors (TCFD / ISSB / ESRS E1)
- `rule-pack/grep-esg-environmental-red-flags` - ESG environmental red-flag detectors (the 'E' of ESG)

### compliance

- `benchmark/esg-supplier-grading-bench` - ESG supplier-grading benchmark v1
- `dataset/academic-essay-samples` - Synthetic academic essay samples (integrity-review test set)
- `dataset/gdpr-dsar-samples` - Synthetic GDPR DSAR samples
- `dataset/gxp-validation-samples` - Synthetic GxP validation samples (3 cases)
- `dataset/hr-posting-samples` - Synthetic HR job-posting samples
- `dataset/supplier-disclosure-pack-schema` - Supplier disclosure pack schema (canonical input shape)
- `dataset/trade-export-samples` - Synthetic trade-export transaction samples
- `harness/esg-disclosure-grading` - ESG Disclosure Grading harness
- `knowledge-pack/academic-honor-codes` - Academic honor codes + AI-policy frameworks
- `knowledge-pack/citemind-architecture-reference` - CiteMind architecture reference (local-first PDF → research wiki + concept graph)
- `knowledge-pack/csddd-and-forced-labor-indicators` - Global supply-chain due-diligence regulatory pack
- `knowledge-pack/eeoc-hiring-statutes` - EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)
- `knowledge-pack/gdpr-articles-and-ccpa` - GDPR articles + CCPA/CPRA + e-Privacy
- `knowledge-pack/gov-benefits-rules` - Government benefits program rules (SNAP / Medicaid / UI / SSI)
- `knowledge-pack/gxp-21-cfr-11-guidelines` - 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack
- `knowledge-pack/high-risk-corridors-and-sectors` - High-risk corridors & sector-specific labor / environmental risks
- `knowledge-pack/lead-company-code-stub` - Lead-company code-of-conduct stub (placeholder)
- `knowledge-pack/platform-content-policy-frameworks` - Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `knowledge-pack/trade-export-control-frameworks` - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
- `pattern/anti-no-audit-trace` - Anti-pattern: No audit trace
- `pattern/anti-no-pii-redact-before-model` - Anti-pattern: PII reaches the model without redaction
- `pattern/anti-silent-tool-failure` - Anti-pattern: Silent tool failure (empty result == success)
- `pattern/anti-un-cited-extraction` - Anti-pattern: Un-cited extraction
- `pattern/composable-success-criteria` - Composable success criteria (regex + semantic + LLM-judge + deterministic + tool + composite)
- `pattern/concept-graph-from-text` - Concept graph from text
- `pattern/critical-tier-output-override` - Critical-tier output override (one dominant message on critical finding)
- `pattern/go-nogo-checklist-gate` - GO/NO-GO checklist gate
- `pattern/k-anonymity-aggregation` - K-anonymity + HMACed-key cross-organization aggregation
- `pattern/local-first-with-cited-answers` - Local-first with cited answers
- `pattern/source-document-to-persistent-knowledge-layer` - Source document → persistent knowledge layer
- `persona/academic-integrity-officer` - Academic Integrity Officer (plagiarism / AI-generated / citation fabrication)
- `persona/agriculture-compliance-officer` - Agriculture Compliance Officer (USDA / GAP / GlobalGAP / NOP organic)
- `persona/ai-governance-auditor` - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)
- `persona/aviation-safety-investigator` - Aviation Safety Investigator (NTSB / FAA / ICAO / SMS / ASAP)
- `persona/benefits-adjudicator` - Government Benefits Adjudicator (SNAP / Medicaid / UI / SSI)
- `persona/biosecurity-officer` - Responsible Official / Biosecurity Officer (42 CFR Part 73 + BMBL 6th + WHO LBM4 + DURC/P3CO)
- `persona/cannabis-compliance-officer` - Cannabis Compliance Officer (State + IRS §280E + METRC + FinCEN)
- `persona/climate-risk-analyst` - Climate Risk Analyst (TCFD / ISSB IFRS S2 / CDP)
- `persona/construction-safety-officer` - Construction Safety Officer (OSHA 1926 / ANSI Z10 / Focus Four)
- `persona/customs-broker` - Licensed Customs Broker (US CBP / EU UCC / WCO)
- `persona/defense-acquisition-officer` - Defense Acquisition Officer (DFARS / FAR / CMMC / counterfeit parts)
- `persona/eeoc-hiring-officer` - EEOC Hiring Officer (Title VII / ADA / ADEA / OFCCP)
- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)
- `persona/food-safety-officer` - Food Safety Officer (FDA FSMA / HACCP / GFSI)
- `persona/gaming-integrity-officer` - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)
- `persona/gxp-auditor` - GxP Auditor (21-CFR-11 / EU GMP Annex 11 / ICH / ALCOA+)
- `persona/local-first-research-tutor` - Local-first research tutor (CiteMind-style)
- `persona/maritime-safety-officer` - Maritime Safety Officer (IMO SOLAS / MARPOL / ISM / STCW)
- `persona/nerc-cip-analyst` - NERC CIP Compliance Analyst (Bulk Electric System cyber)
- `persona/nuclear-safety-inspector` - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)
- `persona/privacy-officer-gdpr` - Privacy Officer (GDPR / CCPA / DSAR fulfillment)
- `persona/rcra-waste-manager` - RCRA Hazardous Waste Manager (40 CFR Parts 260-279 + e-Manifest + DOT HMR)
- `persona/telco-compliance-officer` - Telco Compliance Officer (FCC Part 47 / CPNI / CALEA / TRAI)
- `persona/trade-compliance-officer` - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)
- `persona/transfer-pricing-counsel` - Transfer Pricing Counsel (OECD BEPS / IRC §482 / Pillar Two)
- `persona/trust-and-safety-reviewer` - Trust + Safety reviewer (platform moderation)
- `persona/water-utility-compliance-officer` - Water Utility Compliance Officer (SDWA / LCRR / AWIA)
- `pipeline/academic-integrity-review` - Academic integrity review (plagiarism / AI / citation fabrication)
- `pipeline/agriculture-compliance-review` - Agriculture compliance review (FSMA + USDA NOP + GlobalGAP)
- `pipeline/ai-governance-audit` - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `pipeline/anonymized-illicit-recruitment-pattern-sharing` - Anonymized cross-org pattern sharing for illicit recruitment corridors
- `pipeline/aorn-surgical-count-gate` - AORN Surgical Count GO/NO-GO gate
- `pipeline/benefits-adjudication-review` - Government benefits adjudication review (SNAP / Medicaid / UI / SSI)
- `pipeline/biosecurity-review` - Biosecurity / select agent review (42 CFR 73 + BMBL 6e + DURC/P3CO)
- `pipeline/cannabis-compliance-review` - Cannabis compliance review (state + §280E + METRC + FinCEN)
- `pipeline/citemind-pdf-to-research-wiki` - Local PDF → research wiki + concept graph (CiteMind shape)
- `pipeline/climate-disclosure-review` - Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)
- `pipeline/customer-record-enrichment` - Customer record enrichment (deterministic, cross-vertical)
- `pipeline/customs-broker-review` - Customs entry review (US CBP + UFLPA + USMCA + WCO)
- `pipeline/deep-tier-supplier-audit` - Deep-tier (T1→T4+) supplier audit with traceability
- `pipeline/dfars-cmmc-compliance-review` - DoD DFARS / CMMC compliance review
- `pipeline/document-to-knowledge-graph` - Document to knowledge graph (nodes + edges with source anchors)
- `pipeline/dot-pretrip-gate` - DOT pre-trip inspection gate (DVIR / 49 CFR 396)
- `pipeline/esi-triage-gate` - ESI 5-Level Triage gate (ER)
- `pipeline/faa-preflight-gate` - FAA Part 91 Before-Takeoff gate
- `pipeline/full-vendor-due-diligence` - Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)
- `pipeline/gaming-integrity-review` - Gaming integrity review (BSA AML + responsible-gambling + match-fixing)
- `pipeline/gdpr-dsar-review` - GDPR DSAR fulfillment review (CCPA-compatible)
- `pipeline/gxp-validation-review` - GxP validation review (21-CFR-11 + Annex 11 + ALCOA+)
- `pipeline/haccp-ccp-gate` - HACCP CCP monitoring gate
- `pipeline/hr-hiring-compliance-review` - HR hiring compliance review (EEOC / Title VII / ADA / ADEA)
- `pipeline/itil-change-gate` - ITIL Change Enablement gate
- `pipeline/kyc-cip-gate` - KYC/CIP onboarding gate (BSA + USA PATRIOT §326)
- `pipeline/mixed-criteria-demo` - Mixed success-criteria demo (regex + semantic + deterministic + LLM + composite)
- `pipeline/msha-preshift-exam` - MSHA pre-shift exam GO/NO-GO gate
- `pipeline/nfpa-70e-loto-gate` - NFPA 70E Lockout/Tagout gate
- `pipeline/nist-800-61-ir-gate` - NIST 800-61 Incident Response gate
- `pipeline/nuclear-safety-review` - Nuclear safety review (NRC 10 CFR + IAEA + INPO)
- `pipeline/platform-content-triage` - Platform content triage (Trust + Safety)
- `pipeline/pssr-startup-gate` - PSM Pre-Startup Safety Review (PSSR) gate
- `pipeline/rcra-waste-review` - RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)
- `pipeline/space-launch-review` - Space launch + range safety review (FAA Part 450 / NASA / ITAR)
- `pipeline/supplier-policy-grading` - Supplier policy & disclosure grading (CSDDD-aligned)
- `pipeline/sustainability-report-full-review` - Sustainability report full review (Climate + ESG-S + ESG-G chained)
- `pipeline/telco-compliance-review` - Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)
- `pipeline/trade-compliance-review` - Trade compliance review (HTS / EAR / ITAR / OFAC)
- `pipeline/trid-loan-gate` - TRID Loan Estimate + Closing Disclosure gate
- `pipeline/water-utility-compliance-review` - Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)
- `pipeline/who-surgical-safety-gate` - WHO Surgical Safety Checklist gate (Sign In before induction)
- `processor/checklist-evaluator` - Checklist evaluator (GO/NO-GO)
- `processor/concept-graph-extractor` - Concept graph extractor
- `processor/entity-resolution-link` - Entity resolution: cluster records into entities
- `processor/hybrid-bm25-vector-retrieve` - Hybrid BM25 + vector retrieve
- `processor/local-embedder` - Local embedder (Ollama / nomic / mxbai)
- `processor/page-aware-chunker` - Page-aware chunker
- `processor/pdf-extract-with-ocr-fallback` - PDF extract with OCR fallback (CiteMind shape)
- `processor/structured-to-prose` - Structured JSON → prose normalizer (for GREP-style rule packs)
- `rubric/academic-integrity-quality-v1` - Academic integrity review quality v1
- `rubric/benefits-adjudication-quality-v1` - Benefits adjudication quality v1
- `rubric/bureaucracy-translation-quality-v1` - Bureaucracy translation + fraud-screen quality v1
- `rubric/citemind-citation-fidelity-v1` - CiteMind citation-fidelity rubric v1
- `rubric/climate-disclosure-quality-v1` - Climate disclosure quality v1 (TCFD/ISSB/ESRS aligned)
- `rubric/esg-env-v1` - ESG environmental (E) sub-rubric v1
- `rubric/esg-gov-v1` - ESG governance (G) sub-rubric v1
- `rubric/esg-social-v1` - ESG social (S) sub-rubric v1
- `rubric/esg-supplier-compliance-v1` - ESG supplier compliance v1 (full E + S + G)
- `rubric/gdpr-dsar-quality-v1` - GDPR DSAR fulfillment quality v1
- `rubric/gxp-validation-quality-v1` - GxP validation review quality v1
- `rubric/hr-hiring-compliance-v1` - HR hiring compliance review quality v1
- `rubric/platform-moderation-quality-v1` - Platform moderation review quality v1
- `rubric/trade-compliance-quality-v1` - Trade compliance review quality v1
- `rule-pack/grep-academic-integrity-flags` - Academic integrity red-flag detectors (plagiarism / AI / fabricated citations)
- `rule-pack/grep-benefits-eligibility-flags` - Benefits-eligibility red-flag detectors (SNAP / Medicaid / UI)
- `rule-pack/grep-climate-disclosure-gaps` - Climate disclosure gap detectors (TCFD / ISSB / ESRS E1)
- `rule-pack/grep-esg-environmental-red-flags` - ESG environmental red-flag detectors (the 'E' of ESG)
- `rule-pack/grep-esg-forced-labor-red-flags` - ESG / forced-labor red-flag detectors (the 'S' of ESG)
- `rule-pack/grep-esg-governance-red-flags` - ESG governance red-flag detectors (the 'G' of ESG)
- `rule-pack/grep-food-safety-flags` - Food safety / FSMA / HACCP red-flag detectors
- `rule-pack/grep-gdpr-dsar-red-flags` - GDPR DSAR red-flag detectors
- `rule-pack/grep-gxp-data-integrity-red-flags` - GxP data-integrity red-flag detectors (21-CFR-11 / ALCOA+)
- `rule-pack/grep-hr-hiring-bias-flags` - HR hiring bias detectors (Title VII / ADA / ADEA / EEOC)
- `rule-pack/grep-nerc-cip-flags` - NERC CIP compliance red-flag detectors
- `rule-pack/grep-platform-moderation-flags` - Platform moderation flags (text-only triage)
- `rule-pack/grep-trade-compliance-flags` - Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)
- `tool/cbp-wro-lookup` - US CBP Withhold Release Order + UFLPA Entity List lookup
- `tool/opencorporates-lookup` - OpenCorporates company lookup

### construction

- `dataset/construction-safety-samples` - Construction safety samples
- `knowledge-pack/osha-construction-1926` - OSHA 29 CFR 1926 (Construction) + ANSI Z10 + Focus Four
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pattern/go-nogo-checklist-gate` - GO/NO-GO checklist gate
- `persona/construction-safety-officer` - Construction Safety Officer (OSHA 1926 / ANSI Z10 / Focus Four)
- `pipeline/construction-safety-review` - Construction safety review (OSHA 1926 / Focus Four)
- `processor/checklist-evaluator` - Checklist evaluator (GO/NO-GO)
- `rubric/construction-safety-quality-v1` - Construction safety review quality v1
- `rule-pack/grep-construction-safety-flags` - Construction safety red-flag detectors (OSHA 1926)

### construction.safety

- `dataset/construction-safety-samples` - Construction safety samples
- `knowledge-pack/osha-construction-1926` - OSHA 29 CFR 1926 (Construction) + ANSI Z10 + Focus Four
- `persona/construction-safety-officer` - Construction Safety Officer (OSHA 1926 / ANSI Z10 / Focus Four)
- `pipeline/construction-safety-review` - Construction safety review (OSHA 1926 / Focus Four)
- `rubric/construction-safety-quality-v1` - Construction safety review quality v1
- `rule-pack/grep-construction-safety-flags` - Construction safety red-flag detectors (OSHA 1926)

### creative

- `adapter/sdxl-local` - SDXL (local Diffusers)
- `knowledge-pack/lens-physics-primers` - Lens physics primers
- `knowledge-pack/style-references-cinematic` - Cinematic style references
- `persona/cinematic-product-photographer` - Cinematic Product Photographer
- `persona/translator-improver` - Translator + improver
- `pipeline/blip-clip-image-to-prompt` - BLIP + CLIP Interrogator image-to-prompt
- `pipeline/brand-safe-product-photo` - Brand-Safe Product Photo
- `pipeline/sd-prompt-embedding-cosine` - Stable-Diffusion prompt embedding + cosine evaluation
- `processor/nsfw-image-classifier` - NSFW image classifier
- `rubric/brand-safe-image-v1` - Brand-safe image v1
- `rule-pack/grep-output-safety-image` - Image-output safety checks
- `rule-pack/grep-prohibited-terms` - Prohibited Terms (image-gen guard rails)
- `tool/txt2img-sdxl` - Text-to-Image (SDXL)

### creative.image

- `pipeline/blip-clip-image-to-prompt` - BLIP + CLIP Interrogator image-to-prompt
- `pipeline/sd-prompt-embedding-cosine` - Stable-Diffusion prompt embedding + cosine evaluation

### cross_industry

- `adapter/anthropic-claude-opus` - Anthropic Claude Opus (deep-reasoning frontier-class)
- `adapter/anthropic-claude-sonnet` - Anthropic Claude Sonnet (frontier-class chat + tool-use)
- `adapter/bge-embeddings-local` - BGE embeddings (local)
- `adapter/deepseek-r1-distill` - DeepSeek R1 Distill (open-weights reasoning)
- `adapter/flux-1-schnell-local` - FLUX.1 Schnell (open-weights image generation)
- `adapter/gemma-4-26b-vision` - Google Gemma 4 26B-A4B-IT (multimodal vision + native multilingual)
- `adapter/google-gemini` - Google Gemini (multimodal frontier)
- `adapter/llama-3-3-70b-instruct` - Meta Llama 3.3 70B Instruct (open-weights)
- `adapter/mistral-8x22b-instruct` - Mistral 8x22B Instruct (Mixtral, open-weights)
- `adapter/nomic-embed-text-v15` - Nomic Embed Text v1.5 (open-weights embeddings)
- `adapter/ollama-default` - Ollama (local default)
- `adapter/openai-embeddings` - OpenAI embeddings (text-embedding-3-small/large)
- `adapter/openai-gpt-frontier` - OpenAI frontier-class chat + tool-use
- `adapter/phi-4-instruct` - Microsoft Phi-4 Instruct (open-weights)
- `adapter/qwen-2-5-72b-instruct` - Qwen 2.5 72B Instruct (Alibaba, open-weights)
- `harness/chat-with-memory` - Persistent chat with memory (multi-turn, preference-aware)
- `harness/data-cleaning-and-enrichment` - Data cleaning + entity enrichment harness
- `harness/email-triage-and-draft` - Email Triage + Draft harness (preference-aware, tone-matched)
- `harness/personal-corpus-search` - Personal corpus search (RAG over user's own files / notes / docs)
- `harness/redact-pii-text` - Redact PII (text)
- `harness/text-safety-review` - Text Safety Review
- `knowledge-pack/common-abbreviations` - Common abbreviations (cross-industry sample)
- `knowledge-pack/common-personas-library` - Common personas / system-prompt library
- `knowledge-pack/csddd-and-forced-labor-indicators` - Global supply-chain due-diligence regulatory pack
- `knowledge-pack/iso-country-codes` - ISO 3166 country codes (sample)
- `knowledge-pack/iso-currency-codes` - ISO 4217 currency codes
- `knowledge-pack/lead-company-code-stub` - Lead-company code-of-conduct stub (placeholder)
- `knowledge-pack/personal-preferences-template` - Personal preferences template (fork + edit)
- `knowledge-pack/spdx-licenses-summary` - SPDX licenses (summary)
- `knowledge-pack/user-preference-schema` - User preference schema (canonical shape for personal assistants)
- `pattern/anti-eval-leak-into-train` - Anti-pattern: Evaluation set leaked into training data
- `pattern/anti-grep-as-classifier` - Anti-pattern: GREP regex as a classifier
- `pattern/anti-llm-as-judge-without-rubric` - Anti-pattern: LLM-as-judge without rubric
- `pattern/anti-missing-determinism-seed` - Anti-pattern: Missing determinism / seed control
- `pattern/anti-no-audit-trace` - Anti-pattern: No audit trace
- `pattern/anti-no-pii-redact-before-model` - Anti-pattern: PII reaches the model without redaction
- `pattern/anti-over-prompting-as-crutch` - Anti-pattern: 5,000-token system prompt as a crutch
- `pattern/anti-silent-tool-failure` - Anti-pattern: Silent tool failure (empty result == success)
- `pattern/anti-single-model-no-fallback` - Anti-pattern: Single-model dependency with no fallback
- `pattern/anti-un-cited-extraction` - Anti-pattern: Un-cited extraction
- `pattern/chain-of-density` - Chain-of-Density (iterative dense summarization)
- `pattern/chain-of-verification` - Chain-of-Verification (CoVe)
- `pattern/composable-success-criteria` - Composable success criteria (regex + semantic + LLM-judge + deterministic + tool + composite)
- `pattern/corrective-rag` - Corrective RAG (CRAG)
- `pattern/critical-tier-output-override` - Critical-tier output override (one dominant message on critical finding)
- `pattern/dpo-from-pairwise` - Direct Preference Optimization (DPO) from pairwise preferences
- `pattern/evaluator-optimizer` - Evaluator-Optimizer
- `pattern/hyde` - HyDE (Hypothetical Document Embeddings)
- `pattern/k-anonymity-aggregation` - K-anonymity + HMACed-key cross-organization aggregation
- `pattern/lora-merge-and-deploy` - LoRA merge + deploy (or hot-swap)
- `pattern/naive-rag` - Naive RAG
- `pattern/orchestrator-workers` - Orchestrator-Workers
- `pattern/peft-lora-adapter-insertion` - PEFT LoRA adapter insertion
- `pattern/personal-preference-layer` - Personal preference layer
- `pattern/plan-and-execute` - Plan-and-Execute
- `pattern/prompt-chaining` - Prompt Chaining
- `pattern/qlora-4bit-finetune` - QLoRA 4-bit fine-tune
- `pattern/raft-retrieval-aug-finetune` - RAFT (Retrieval-Augmented Fine-Tuning)
- `pattern/rag-fusion` - RAG-Fusion
- `pattern/react` - ReAct (Reason + Act)
- `pattern/refuse-on-redacted` - Refuse-on-redacted (null over hallucination on missing fields)
- `pattern/routing` - Routing
- `pattern/self-rag` - Self-RAG
- `pattern/self-refine` - Self-Refine
- `pattern/two-stage-extract-then-judge` - Two-stage extract-then-judge (separate calls for extraction + classification)
- `pipeline/deberta-finetune-classification` - DeBERTa-v3-large fine-tune for closed-set classification
- `pipeline/lora-qlora-pairwise-pref-finetune` - LoRA + QLoRA pairwise-preference fine-tune (Gemma-2-9b 4-bit)
- `pipeline/tfidf-lightgbm-text-classification` - TF-IDF + LightGBM text classification
- `persona/fact-checker` - Fact Checker
- `persona/linux-terminal` - Linux terminal
- `persona/personal-assistant` - Personal Assistant (preference-aware, privacy-first)
- `persona/personal-coding-reviewer` - Personal code reviewer (loads user preferences)
- `persona/personal-writing-companion` - Personal writing companion (loads user preferences)
- `persona/research-analyst` - Research Analyst
- `persona/support-agent` - Customer support agent
- `persona/translator-improver` - Translator + improver
- `pipeline/chat-with-pdf-citations` - Chat with PDF (with citations)
- `pipeline/customer-record-enrichment` - Customer record enrichment (deterministic, cross-vertical)
- `pipeline/deep-research-supervisor-workers` - Deep research: supervisor + parallel workers
- `pipeline/deep-research-with-citations` - Deep research with citations
- `pipeline/email-triage-and-draft` - Email triage + reply draft
- `pipeline/email-triage-pipeline` - Email triage pipeline (preference-loaded, tone-matched, leakage-checked)
- `pipeline/everything-research-pipeline` - Everything research pipeline (kitchen-sink, 22 passes)
- `pipeline/full-vendor-due-diligence` - Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)
- `pipeline/knowledge-graph-from-corpus` - GraphRAG: knowledge-graph from corpus + global/local query
- `pipeline/mixed-criteria-demo` - Mixed success-criteria demo (regex + semantic + deterministic + LLM + composite)
- `pipeline/multi-doc-qa-subquestion` - Multi-document QA with sub-question decomposition
- `pipeline/personal-chat-pipeline` - Personal chat pipeline (preference + memory + tool-aware)
- `pipeline/personal-code-review-with-preferences` - Personal code review with preference layer
- `pipeline/personal-search-pipeline` - Personal corpus search pipeline (RAG over user's own data)
- `pipeline/plan-execute-critic-loop` - Plan / execute / critic loop
- `pipeline/quantized-llm-inference` - Quantized LLM inference (4-bit BitsAndBytes)
- `pipeline/research-entity` - Research Entity
- `pipeline/self-rag-grade-and-revise` - Self-RAG: grade-and-revise (concrete implementation)
- `pipeline/verify-claim-against-corpus` - Verify Claim Against Corpus
- `processor/address-parse-standardize` - Address parse + standardize (USPS Pub 28 / libpostal)
- `processor/audio-to-text-whisper` - Audio to text (Whisper)
- `processor/audit-trace-emitter` - Audit trace emitter
- `processor/citation-coverage` - Citation coverage verifier
- `processor/community-summary-mapreduce` - Community-summary map-reduce (GraphRAG global)
- `processor/context-window-packer` - Context-window packer (Lost-in-the-middle aware)
- `processor/cost-ceiling-gate` - Cost ceiling gate
- `processor/cost-meter` - Cost meter
- `processor/cross-encoder-reranker` - Cross-encoder reranker
- `processor/date-parse-multiformat` - Date parse multi-format → ISO 8601
- `processor/document-grader` - Per-document relevance grader (Self-RAG)
- `processor/embedder-minilm` - Text embedder (MiniLM-L6-v2)
- `processor/entity-resolution-link` - Entity resolution: cluster records into entities
- `processor/escalate-human-review` - Escalate to human reviewer
- `processor/hallucination-scorer` - Hallucination scorer (SelfCheckGPT-style)
- `processor/hyde-query-expander` - HyDE query expander
- `processor/inject-datetime-locale` - Inject datetime + locale into prompt
- `processor/inject-output-schema` - Inject output schema directive
- `processor/intent-dispatcher` - Intent dispatcher
- `processor/iso-country-normalize` - ISO country code normalize (alpha-2 / alpha-3 / numeric / name)
- `processor/iterative-revise-loop` - Iterative revise loop
- `processor/json-schema-repair` - JSON Schema repair + validate
- `processor/llm-judge` - LLM-as-judge
- `processor/llmlingua-context-compressor` - LLMLingua context compressor
- `processor/memory-conversational-store` - Conversational memory store
- `processor/multi-vector-fusion` - Multi-vector / multi-query fusion (RRF + weighted)
- `processor/name-canonicalize` - Person-name canonicalize (Western + East-Asian)
- `processor/official-sources-checker` - Official-sources analyzer
- `processor/pdf-to-text` - PDF to text
- `processor/phone-normalize-e164` - Phone number normalize → E.164 (Google libphonenumber)
- `processor/preference-loader` - User preference loader
- `processor/prompt-injection-detector` - Prompt-injection detector
- `processor/reasoning-framework-selector` - Reasoning framework selector
- `processor/recursive-character-chunker` - Recursive character chunker
- `processor/redact-pii-text` - Redact PII from text (English-centric, MS Presidio-compatible)
- `processor/runtime-tool-selector` - Runtime tool selector (Toolformer / pydantic-ai)
- `processor/self-consistency-sampler` - Self-consistency sampler
- `processor/self-refine-critique` - Self-Refine critique loop
- `processor/structured-to-prose` - Structured JSON → prose normalizer (for GREP-style rule packs)
- `processor/sub-question-decomposer` - Sub-question decomposer
- `processor/verify-composite-criterion` - Composite (AND/OR/NOT) success-criterion evaluator
- `processor/verify-deterministic-criterion` - Deterministic comparison success-criterion evaluator
- `processor/verify-llm-judge-criterion` - LLM-as-judge success-criterion evaluator
- `processor/verify-regex-criterion` - Regex success-criterion evaluator
- `processor/verify-semantic-criterion` - Semantic-similarity success-criterion evaluator
- `processor/verify-tool-validate-criterion` - Tool-validation success-criterion evaluator
- `rubric/research-entity-v1` - Research Entity v1
- `rubric/verification-v1` - Verification v1
- `rule-pack/grep-cloud-secrets` - Cloud provider secret detectors
- `rule-pack/grep-personal-info-leakage` - Personal-info leakage detectors (assistant drafts → wrong audience)
- `rule-pack/grep-personal-style-flags` - Personal style flags (catches disallowed idioms)
- `rule-pack/grep-private-key-blocks` - Private key block detectors
- `rule-pack/grep-prompt-injection-heuristics` - Prompt-injection heuristic detectors
- `rule-pack/hybrid-retrieval-policy` - Hybrid retrieval policy (BM25 + dense + RRF)
- `rule-pack/privacy-pii-text-en` - Privacy PII (English text)
- `rule-pack/web-search-allowlist-default` - Web search allowlist (default)
- `tool/google-geocode` - Google Maps Geocoding (address → lat/lng)
- `tool/json-schema-validator` - JSON Schema 2020-12 validator
- `tool/presidio-pii-detect` - Microsoft Presidio PII detection proxy
- `tool/usps-address-validator` - USPS address validation
- `tool/web-search` - Web Search

### customs

- `dataset/customs-samples` - Customs entry samples
- `knowledge-pack/customs-cbp-wco-frameworks` - Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)
- `persona/customs-broker` - Licensed Customs Broker (US CBP / EU UCC / WCO)
- `pipeline/customs-broker-review` - Customs entry review (US CBP + UFLPA + USMCA + WCO)
- `rubric/customs-quality-v1` - Customs entry review quality v1
- `rule-pack/grep-customs-broker-flags` - Customs entry / FTA / forced-labor flags (US CBP)

### customs.entry

- `dataset/customs-samples` - Customs entry samples
- `knowledge-pack/customs-cbp-wco-frameworks` - Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)
- `persona/customs-broker` - Licensed Customs Broker (US CBP / EU UCC / WCO)
- `pipeline/customs-broker-review` - Customs entry review (US CBP + UFLPA + USMCA + WCO)
- `rubric/customs-quality-v1` - Customs entry review quality v1
- `rule-pack/grep-customs-broker-flags` - Customs entry / FTA / forced-labor flags (US CBP)

### customs.fta

- `dataset/customs-samples` - Customs entry samples
- `knowledge-pack/customs-cbp-wco-frameworks` - Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)
- `persona/customs-broker` - Licensed Customs Broker (US CBP / EU UCC / WCO)
- `pipeline/customs-broker-review` - Customs entry review (US CBP + UFLPA + USMCA + WCO)
- `rubric/customs-quality-v1` - Customs entry review quality v1
- `rule-pack/grep-customs-broker-flags` - Customs entry / FTA / forced-labor flags (US CBP)

### customs.tariff

- `dataset/customs-samples` - Customs entry samples
- `knowledge-pack/customs-cbp-wco-frameworks` - Customs frameworks (US CBP 19 CFR + WCO + UFLPA + USMCA)
- `persona/customs-broker` - Licensed Customs Broker (US CBP / EU UCC / WCO)
- `pipeline/customs-broker-review` - Customs entry review (US CBP + UFLPA + USMCA + WCO)
- `rubric/customs-quality-v1` - Customs entry review quality v1
- `rule-pack/grep-customs-broker-flags` - Customs entry / FTA / forced-labor flags (US CBP)

### cyber

- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pipeline/nist-800-61-ir-gate` - NIST 800-61 Incident Response gate

### defense

- `dataset/defense-dfars-samples` - Defense DFARS / CMMC samples
- `knowledge-pack/defense-dfars-frameworks` - Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)
- `pattern/local-first-with-cited-answers` - Local-first with cited answers
- `persona/defense-acquisition-officer` - Defense Acquisition Officer (DFARS / FAR / CMMC / counterfeit parts)
- `pipeline/dfars-cmmc-compliance-review` - DoD DFARS / CMMC compliance review
- `rubric/defense-dfars-quality-v1` - Defense DFARS/CMMC review quality v1
- `rule-pack/grep-defense-dfars-flags` - Defense DFARS + CMMC + counterfeit-parts red-flag detectors

### defense.cmmc

- `dataset/defense-dfars-samples` - Defense DFARS / CMMC samples
- `knowledge-pack/defense-dfars-frameworks` - Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)
- `persona/defense-acquisition-officer` - Defense Acquisition Officer (DFARS / FAR / CMMC / counterfeit parts)
- `pipeline/dfars-cmmc-compliance-review` - DoD DFARS / CMMC compliance review
- `rubric/defense-dfars-quality-v1` - Defense DFARS/CMMC review quality v1
- `rule-pack/grep-defense-dfars-flags` - Defense DFARS + CMMC + counterfeit-parts red-flag detectors

### defense.counterfeit_parts

- `knowledge-pack/defense-dfars-frameworks` - Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)
- `persona/defense-acquisition-officer` - Defense Acquisition Officer (DFARS / FAR / CMMC / counterfeit parts)
- `pipeline/dfars-cmmc-compliance-review` - DoD DFARS / CMMC compliance review
- `rule-pack/grep-defense-dfars-flags` - Defense DFARS + CMMC + counterfeit-parts red-flag detectors

### defense.dfars

- `dataset/defense-dfars-samples` - Defense DFARS / CMMC samples
- `knowledge-pack/defense-dfars-frameworks` - Defense compliance frameworks (DFARS / FAR / CMMC / NIST 800-171 / SAE AS5553 / Section 889)
- `persona/defense-acquisition-officer` - Defense Acquisition Officer (DFARS / FAR / CMMC / counterfeit parts)
- `pipeline/dfars-cmmc-compliance-review` - DoD DFARS / CMMC compliance review
- `rubric/defense-dfars-quality-v1` - Defense DFARS/CMMC review quality v1
- `rule-pack/grep-defense-dfars-flags` - Defense DFARS + CMMC + counterfeit-parts red-flag detectors

### education

- `dataset/academic-essay-samples` - Synthetic academic essay samples (integrity-review test set)
- `dataset/citemind-pdf-samples` - CiteMind PDF samples (educational, open-license)
- `harness/code-act-jupyter` - Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)
- `knowledge-pack/academic-honor-codes` - Academic honor codes + AI-policy frameworks
- `knowledge-pack/citemind-architecture-reference` - CiteMind architecture reference (local-first PDF → research wiki + concept graph)
- `pattern/concept-graph-from-text` - Concept graph from text
- `pattern/local-first-with-cited-answers` - Local-first with cited answers
- `pattern/source-document-to-persistent-knowledge-layer` - Source document → persistent knowledge layer
- `pattern/two-stage-retrieve-rerank` - Two-stage retrieve + constrained rerank
- `persona/academic-integrity-officer` - Academic Integrity Officer (plagiarism / AI-generated / citation fabrication)
- `persona/local-first-research-tutor` - Local-first research tutor (CiteMind-style)
- `persona/math-tutor` - Math tutor
- `pipeline/academic-integrity-review` - Academic integrity review (plagiarism / AI / citation fabrication)
- `pipeline/citemind-pdf-to-research-wiki` - Local PDF → research wiki + concept graph (CiteMind shape)
- `pipeline/deberta-lgbm-hybrid-scorer` - DeBERTa-v3 + LightGBM hybrid scorer (with spell autocorrect)
- `pipeline/deepseek-r1-code-interpreter-math` - DeepSeek-R1 / QwQ + Python code-interpreter for math reasoning
- `pipeline/large-model-faiss-rag` - Large-model FAISS RAG (Platypus2-70b style)
- `pipeline/llm-judge-essay-grading` - LLM-judge essay grading (with adversarial prompt prefix)
- `pipeline/longformer-bigbird-ner` - Long-document NER with LongFormer / BigBird
- `pipeline/qwen-vllm-rerank-eedi` - Qwen-32B vLLM retrieval-rerank with logits-processor constraints
- `pipeline/sentence-transformer-finetune-retrieval` - Sentence-transformer fine-tune for retrieval / ranking
- `pipeline/storm-persona-curation-article` - STORM: persona-curation + outline-fanout article
- `pipeline/twenty-questions-agent` - 20-questions agent (Akinator-style)
- `pipeline/two-time-retrieve-rerank` - Two-time retrieval + cross-encoder rerank
- `pipeline/vllm-batch-llm-inference` - vLLM batch LLM inference (with logits-processor-zoo)
- `processor/concept-graph-extractor` - Concept graph extractor
- `processor/hybrid-bm25-vector-retrieve` - Hybrid BM25 + vector retrieve
- `processor/local-embedder` - Local embedder (Ollama / nomic / mxbai)
- `processor/page-aware-chunker` - Page-aware chunker
- `processor/pdf-extract-with-ocr-fallback` - PDF extract with OCR fallback (CiteMind shape)
- `processor/persona-set-generator` - Persona-set generator (STORM)
- `processor/skeleton-outliner` - Skeleton outliner (Skeleton-of-Thought)
- `processor/two-time-retrieval` - Two-time retrieval (refine query, re-retrieve)
- `rubric/academic-integrity-quality-v1` - Academic integrity review quality v1
- `rubric/citemind-citation-fidelity-v1` - CiteMind citation-fidelity rubric v1
- `rule-pack/grep-academic-integrity-flags` - Academic integrity red-flag detectors (plagiarism / AI / fabricated citations)

### education.higher

- `dataset/academic-essay-samples` - Synthetic academic essay samples (integrity-review test set)
- `knowledge-pack/academic-honor-codes` - Academic honor codes + AI-policy frameworks
- `persona/academic-integrity-officer` - Academic Integrity Officer (plagiarism / AI-generated / citation fabrication)
- `pipeline/academic-integrity-review` - Academic integrity review (plagiarism / AI / citation fabrication)
- `rubric/academic-integrity-quality-v1` - Academic integrity review quality v1
- `rule-pack/grep-academic-integrity-flags` - Academic integrity red-flag detectors (plagiarism / AI / fabricated citations)

### education.tutoring

- `persona/math-tutor` - Math tutor

### election_integrity

- `dataset/election-integrity-samples` - Election integrity samples
- `knowledge-pack/election-integrity-frameworks` - Election integrity frameworks (EAC / CISA / DHS / C2PA)
- `persona/election-integrity-analyst` - Election Integrity Analyst (misinformation / deepfake / voter-roll)
- `pipeline/election-misinformation-review` - Election misinformation / disinformation / synthetic-media review
- `rubric/election-integrity-quality-v1` - Election integrity review quality v1
- `rule-pack/grep-election-misinformation-flags` - Election misinformation / disinformation / deepfake detectors

### election_integrity.deepfake

- `persona/election-integrity-analyst` - Election Integrity Analyst (misinformation / deepfake / voter-roll)

### election_integrity.misinformation

- `persona/election-integrity-analyst` - Election Integrity Analyst (misinformation / deepfake / voter-roll)

### energy

- `dataset/nerc-cip-samples` - NERC CIP BES samples
- `knowledge-pack/nerc-cip-standards` - NERC CIP standards (CIP-002 to CIP-014)
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pattern/go-nogo-checklist-gate` - GO/NO-GO checklist gate
- `persona/nerc-cip-analyst` - NERC CIP Compliance Analyst (Bulk Electric System cyber)
- `persona/nuclear-safety-inspector` - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)
- `pipeline/nerc-cip-compliance-review` - NERC CIP compliance review (Bulk Electric System cyber)
- `pipeline/nfpa-70e-loto-gate` - NFPA 70E Lockout/Tagout gate
- `pipeline/pssr-startup-gate` - PSM Pre-Startup Safety Review (PSSR) gate
- `processor/checklist-evaluator` - Checklist evaluator (GO/NO-GO)
- `rubric/nerc-cip-quality-v1` - NERC CIP compliance review quality v1
- `rule-pack/grep-nerc-cip-flags` - NERC CIP compliance red-flag detectors

### energy.grid

- `dataset/nerc-cip-samples` - NERC CIP BES samples
- `knowledge-pack/nerc-cip-standards` - NERC CIP standards (CIP-002 to CIP-014)
- `persona/nerc-cip-analyst` - NERC CIP Compliance Analyst (Bulk Electric System cyber)
- `pipeline/nerc-cip-compliance-review` - NERC CIP compliance review (Bulk Electric System cyber)
- `rubric/nerc-cip-quality-v1` - NERC CIP compliance review quality v1
- `rule-pack/grep-nerc-cip-flags` - NERC CIP compliance red-flag detectors

### esg

- `benchmark/esg-supplier-grading-bench` - ESG supplier-grading benchmark v1
- `dataset/climate-disclosure-samples` - Synthetic climate disclosure samples (2 cases)
- `dataset/supplier-disclosure-pack-schema` - Supplier disclosure pack schema (canonical input shape)
- `harness/esg-disclosure-grading` - ESG Disclosure Grading harness
- `knowledge-pack/climate-disclosure-frameworks` - Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)
- `knowledge-pack/csddd-and-forced-labor-indicators` - Global supply-chain due-diligence regulatory pack
- `knowledge-pack/high-risk-corridors-and-sectors` - High-risk corridors & sector-specific labor / environmental risks
- `knowledge-pack/lead-company-code-stub` - Lead-company code-of-conduct stub (placeholder)
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pattern/concept-graph-from-text` - Concept graph from text
- `pattern/k-anonymity-aggregation` - K-anonymity + HMACed-key cross-organization aggregation
- `pattern/source-document-to-persistent-knowledge-layer` - Source document → persistent knowledge layer
- `persona/climate-risk-analyst` - Climate Risk Analyst (TCFD / ISSB IFRS S2 / CDP)
- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)
- `pipeline/anonymized-illicit-recruitment-pattern-sharing` - Anonymized cross-org pattern sharing for illicit recruitment corridors
- `pipeline/climate-disclosure-review` - Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)
- `pipeline/deep-tier-supplier-audit` - Deep-tier (T1→T4+) supplier audit with traceability
- `pipeline/supplier-policy-grading` - Supplier policy & disclosure grading (CSDDD-aligned)
- `pipeline/sustainability-report-full-review` - Sustainability report full review (Climate + ESG-S + ESG-G chained)
- `processor/concept-graph-extractor` - Concept graph extractor
- `processor/redact-pii-text` - Redact PII from text (English-centric, MS Presidio-compatible)
- `processor/structured-to-prose` - Structured JSON → prose normalizer (for GREP-style rule packs)
- `rubric/climate-disclosure-quality-v1` - Climate disclosure quality v1 (TCFD/ISSB/ESRS aligned)
- `rubric/esg-env-v1` - ESG environmental (E) sub-rubric v1
- `rubric/esg-gov-v1` - ESG governance (G) sub-rubric v1
- `rubric/esg-social-v1` - ESG social (S) sub-rubric v1
- `rubric/esg-supplier-compliance-v1` - ESG supplier compliance v1 (full E + S + G)
- `rule-pack/grep-climate-disclosure-gaps` - Climate disclosure gap detectors (TCFD / ISSB / ESRS E1)
- `rule-pack/grep-esg-environmental-red-flags` - ESG environmental red-flag detectors (the 'E' of ESG)
- `rule-pack/grep-esg-forced-labor-red-flags` - ESG / forced-labor red-flag detectors (the 'S' of ESG)
- `rule-pack/grep-esg-governance-red-flags` - ESG governance red-flag detectors (the 'G' of ESG)
- `tool/cbp-wro-lookup` - US CBP Withhold Release Order + UFLPA Entity List lookup
- `tool/opencorporates-lookup` - OpenCorporates company lookup

### esg.csddd

- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)

### esg.csrd

- `persona/climate-risk-analyst` - Climate Risk Analyst (TCFD / ISSB IFRS S2 / CDP)
- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)

### esg.modern_slavery

- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)

### finance

- `dataset/climate-disclosure-samples` - Synthetic climate disclosure samples (2 cases)
- `dataset/insurance-claim-samples` - Synthetic insurance claim samples
- `dataset/ma-dd-samples` - M&A DD samples
- `dataset/transfer-pricing-samples` - Transfer pricing samples
- `harness/aml-investigation` - AML Investigation
- `harness/data-cleaning-and-enrichment` - Data cleaning + entity enrichment harness
- `knowledge-pack/aml-red-flags-extended` - AML red flags (extended)
- `knowledge-pack/climate-disclosure-frameworks` - Climate disclosure frameworks (TCFD + ISSB IFRS S2 + CDP + ESRS E1)
- `knowledge-pack/fatf-typologies-sample` - FATF typologies (sample chunks)
- `knowledge-pack/insurance-fraud-typologies` - Insurance fraud typologies (NAIC + CAIF + ABI)
- `knowledge-pack/iso-country-codes` - ISO 3166 country codes (sample)
- `knowledge-pack/iso-currency-codes` - ISO 4217 currency codes
- `knowledge-pack/ma-dd-frameworks` - M&A DD frameworks (legal / financial / IP / customer / HR / tax)
- `knowledge-pack/oecd-tp-and-beps` - OECD TP Guidelines + BEPS + Pillar Two + §482
- `knowledge-pack/sanctions-list-shape` - Sanctions list (shape, with placeholder entries)
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pattern/anti-no-pii-redact-before-model` - Anti-pattern: PII reaches the model without redaction
- `pattern/go-nogo-checklist-gate` - GO/NO-GO checklist gate
- `pattern/k-anonymity-aggregation` - K-anonymity + HMACed-key cross-organization aggregation
- `pattern/refuse-on-redacted` - Refuse-on-redacted (null over hallucination on missing fields)
- `persona/aml-analyst` - AML Analyst
- `persona/climate-risk-analyst` - Climate Risk Analyst (TCFD / ISSB IFRS S2 / CDP)
- `persona/gaming-integrity-officer` - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)
- `persona/insurance-claims-adjuster` - Insurance Claims Adjuster (fraud-aware, NAIC-aligned)
- `persona/ma-dd-counsel` - M&A Due Diligence Counsel (financial / legal / IP / customer / HR / tax)
- `persona/transfer-pricing-counsel` - Transfer Pricing Counsel (OECD BEPS / IRC §482 / Pillar Two)
- `pipeline/climate-disclosure-review` - Climate disclosure review (TCFD + ISSB IFRS S2 + ESRS E1)
- `pipeline/customer-record-enrichment` - Customer record enrichment (deterministic, cross-vertical)
- `pipeline/insurance-claim-review` - Insurance claim review (NAIC fraud-aware)
- `pipeline/kyc-cip-gate` - KYC/CIP onboarding gate (BSA + USA PATRIOT §326)
- `pipeline/lgb-xgb-catboost-ensemble` - LightGBM + XGBoost + CatBoost ensemble (tabular ML)
- `pipeline/ma-dd-review` - M&A due-diligence review (6-stream)
- `pipeline/optuna-tabular-tuning` - Optuna hyperparameter tuning for tabular models
- `pipeline/suspicious-transaction-review` - Suspicious Transaction Review
- `pipeline/sustainability-report-full-review` - Sustainability report full review (Climate + ESG-S + ESG-G chained)
- `pipeline/transfer-pricing-review` - Transfer pricing review (OECD TPG / BEPS / §482 / Pillar Two)
- `pipeline/trid-loan-gate` - TRID Loan Estimate + Closing Disclosure gate
- `processor/entity-resolution-link` - Entity resolution: cluster records into entities
- `processor/official-sources-checker` - Official-sources analyzer
- `processor/redact-pii-text` - Redact PII from text (English-centric, MS Presidio-compatible)
- `rubric/aml-investigation-v1` - AML investigation v1
- `rubric/climate-disclosure-quality-v1` - Climate disclosure quality v1 (TCFD/ISSB/ESRS aligned)
- `rubric/esg-gov-v1` - ESG governance (G) sub-rubric v1
- `rubric/insurance-claim-quality-v1` - Insurance claim review quality v1
- `rubric/ma-dd-quality-v1` - M&A DD review quality v1
- `rubric/transfer-pricing-quality-v1` - Transfer-pricing review quality v1
- `rule-pack/aml-typologies-fatf` - FATF AML typologies (sampled)
- `rule-pack/financial-pii-en` - Financial PII (English)
- `rule-pack/grep-climate-disclosure-gaps` - Climate disclosure gap detectors (TCFD / ISSB / ESRS E1)
- `rule-pack/grep-esg-governance-red-flags` - ESG governance red-flag detectors (the 'G' of ESG)
- `rule-pack/grep-insurance-fraud-red-flags` - Insurance claim fraud red-flag detectors (NAIC + CAIF)
- `rule-pack/grep-ma-dd-red-flags` - M&A DD red-flag detectors (6 streams)
- `rule-pack/grep-transfer-pricing-flags` - Transfer-pricing red-flag detectors (OECD / §482 / BEPS)
- `rule-pack/sanctions-screening` - Sanctions screening (deterministic)
- `tool/opencorporates-lookup` - OpenCorporates company lookup
- `tool/presidio-pii-detect` - Microsoft Presidio PII detection proxy
- `tool/sanctions-check` - Sanctions list check
- `tool/swift-bic-validator` - SWIFT BIC validator + BIC → bank metadata
- `tool/transaction-graph-query` - Transaction graph query
- `tool/usps-address-validator` - USPS address validation

### finance.aml

- `harness/aml-investigation` - AML Investigation
- `knowledge-pack/aml-red-flags-extended` - AML red flags (extended)
- `knowledge-pack/fatf-typologies-sample` - FATF typologies (sample chunks)
- `knowledge-pack/sanctions-list-shape` - Sanctions list (shape, with placeholder entries)
- `persona/aml-analyst` - AML Analyst
- `pipeline/suspicious-transaction-review` - Suspicious Transaction Review
- `rubric/aml-investigation-v1` - AML investigation v1
- `rule-pack/aml-typologies-fatf` - FATF AML typologies (sampled)
- `rule-pack/sanctions-screening` - Sanctions screening (deterministic)
- `tool/sanctions-check` - Sanctions list check
- `tool/swift-bic-validator` - SWIFT BIC validator + BIC → bank metadata
- `tool/transaction-graph-query` - Transaction graph query

### finance.fraud

- `pipeline/lgb-xgb-catboost-ensemble` - LightGBM + XGBoost + CatBoost ensemble (tabular ML)

### finance.kyc

- `knowledge-pack/aml-red-flags-extended` - AML red flags (extended)
- `knowledge-pack/sanctions-list-shape` - Sanctions list (shape, with placeholder entries)
- `rule-pack/sanctions-screening` - Sanctions screening (deterministic)
- `tool/opencorporates-lookup` - OpenCorporates company lookup
- `tool/sanctions-check` - Sanctions list check
- `tool/swift-bic-validator` - SWIFT BIC validator + BIC → bank metadata

### finance.lending

- `pipeline/lgb-xgb-catboost-ensemble` - LightGBM + XGBoost + CatBoost ensemble (tabular ML)

### food

- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pipeline/haccp-ccp-gate` - HACCP CCP monitoring gate

### food_safety

- `dataset/foodsafety-samples` - Food safety samples
- `knowledge-pack/food-safety-fsma-haccp` - FSMA + HACCP + GFSI food safety frameworks
- `persona/food-safety-officer` - Food Safety Officer (FDA FSMA / HACCP / GFSI)
- `pipeline/food-safety-review` - Food safety review (FDA FSMA + HACCP + GFSI)
- `rubric/food-safety-quality-v1` - Food safety review quality v1
- `rule-pack/grep-food-safety-flags` - Food safety / FSMA / HACCP red-flag detectors

### food_safety.fsma

- `dataset/foodsafety-samples` - Food safety samples
- `knowledge-pack/food-safety-fsma-haccp` - FSMA + HACCP + GFSI food safety frameworks
- `persona/food-safety-officer` - Food Safety Officer (FDA FSMA / HACCP / GFSI)
- `pipeline/food-safety-review` - Food safety review (FDA FSMA + HACCP + GFSI)
- `rubric/food-safety-quality-v1` - Food safety review quality v1
- `rule-pack/grep-food-safety-flags` - Food safety / FSMA / HACCP red-flag detectors

### food_safety.haccp

- `dataset/foodsafety-samples` - Food safety samples
- `knowledge-pack/food-safety-fsma-haccp` - FSMA + HACCP + GFSI food safety frameworks
- `persona/food-safety-officer` - Food Safety Officer (FDA FSMA / HACCP / GFSI)
- `pipeline/food-safety-review` - Food safety review (FDA FSMA + HACCP + GFSI)
- `rubric/food-safety-quality-v1` - Food safety review quality v1
- `rule-pack/grep-food-safety-flags` - Food safety / FSMA / HACCP red-flag detectors

### gaming

- `dataset/gaming-samples` - Gaming integrity samples
- `knowledge-pack/gaming-aml-rg-frameworks` - Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state RG)
- `persona/gaming-integrity-officer` - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)
- `pipeline/gaming-integrity-review` - Gaming integrity review (BSA AML + responsible-gambling + match-fixing)
- `rubric/gaming-quality-v1` - Gaming AML + responsible-gambling review quality v1
- `rule-pack/grep-gaming-integrity-flags` - Gaming integrity / AML / responsible-gambling flags

### gaming.aml

- `dataset/gaming-samples` - Gaming integrity samples
- `knowledge-pack/gaming-aml-rg-frameworks` - Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state RG)
- `persona/gaming-integrity-officer` - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)
- `pipeline/gaming-integrity-review` - Gaming integrity review (BSA AML + responsible-gambling + match-fixing)
- `rubric/gaming-quality-v1` - Gaming AML + responsible-gambling review quality v1
- `rule-pack/grep-gaming-integrity-flags` - Gaming integrity / AML / responsible-gambling flags

### gaming.licensing

- `persona/gaming-integrity-officer` - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)

### gaming.responsible

- `dataset/gaming-samples` - Gaming integrity samples
- `knowledge-pack/gaming-aml-rg-frameworks` - Gaming AML + responsible-gambling frameworks (BSA 31 CFR §1021 + state RG)
- `pipeline/gaming-integrity-review` - Gaming integrity review (BSA AML + responsible-gambling + match-fixing)
- `rubric/gaming-quality-v1` - Gaming AML + responsible-gambling review quality v1

### gaming.responsible_gambling

- `persona/gaming-integrity-officer` - Gaming Integrity Officer (gambling AML / responsible gambling / licensing)
- `rule-pack/grep-gaming-integrity-flags` - Gaming integrity / AML / responsible-gambling flags

### government

- `dataset/gov-benefits-samples` - Synthetic SNAP application samples
- `harness/data-cleaning-and-enrichment` - Data cleaning + entity enrichment harness
- `knowledge-pack/gov-benefits-rules` - Government benefits program rules (SNAP / Medicaid / UI / SSI)
- `persona/benefits-adjudicator` - Government Benefits Adjudicator (SNAP / Medicaid / UI / SSI)
- `pipeline/benefits-adjudication-review` - Government benefits adjudication review (SNAP / Medicaid / UI / SSI)
- `processor/entity-resolution-link` - Entity resolution: cluster records into entities
- `processor/official-sources-checker` - Official-sources analyzer
- `rubric/benefits-adjudication-quality-v1` - Benefits adjudication quality v1
- `rule-pack/grep-benefits-eligibility-flags` - Benefits-eligibility red-flag detectors (SNAP / Medicaid / UI)
- `tool/presidio-pii-detect` - Microsoft Presidio PII detection proxy
- `tool/usps-address-validator` - USPS address validation

### government.benefits

- `dataset/gov-benefits-samples` - Synthetic SNAP application samples
- `knowledge-pack/gov-benefits-rules` - Government benefits program rules (SNAP / Medicaid / UI / SSI)
- `persona/benefits-adjudicator` - Government Benefits Adjudicator (SNAP / Medicaid / UI / SSI)
- `pipeline/benefits-adjudication-review` - Government benefits adjudication review (SNAP / Medicaid / UI / SSI)
- `rubric/benefits-adjudication-quality-v1` - Benefits adjudication quality v1
- `rule-pack/grep-benefits-eligibility-flags` - Benefits-eligibility red-flag detectors (SNAP / Medicaid / UI)

### healthcare

- `dataset/radiology-report-samples` - Synthetic radiology report samples (3 cases, fully synthetic)
- `harness/clinical-decision-support` - Clinical Decision Support
- `harness/data-cleaning-and-enrichment` - Data cleaning + entity enrichment harness
- `harness/radiology-report-review` - Radiology Report Review harness
- `knowledge-pack/clinical-guidelines-sample` - Clinical guidelines (sample chunks)
- `knowledge-pack/drug-interaction-references` - Drug-drug interaction references (DrugBank / RxNorm / FDA Orange Book / DailyMed)
- `knowledge-pack/drug-interactions-sample` - Drug-drug interactions (sample, educational)
- `knowledge-pack/icd10-sample` - ICD-10 sample
- `knowledge-pack/radiology-acrac-fleischner` - ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pattern/anti-no-pii-redact-before-model` - Anti-pattern: PII reaches the model without redaction
- `pattern/anti-un-cited-extraction` - Anti-pattern: Un-cited extraction
- `pattern/concept-graph-from-text` - Concept graph from text
- `pattern/go-nogo-checklist-gate` - GO/NO-GO checklist gate
- `pattern/local-first-with-cited-answers` - Local-first with cited answers
- `pattern/refuse-on-redacted` - Refuse-on-redacted (null over hallucination on missing fields)
- `persona/clinical-reasoner` - Clinical Reasoner
- `persona/radiologist-cite-first` - Radiologist (citation-first, specialty radiology)
- `pipeline/aorn-surgical-count-gate` - AORN Surgical Count GO/NO-GO gate
- `pipeline/bidirectional-lstm-sequence-prediction` - Bidirectional LSTM for sequence prediction (time-series / text)
- `pipeline/dicom-medical-image-preprocessing` - DICOM medical image preprocessing (CT / MRI / X-ray)
- `pipeline/differential-diagnosis` - Differential Diagnosis
- `pipeline/efficientnet-medical-imaging` - EfficientNet for medical imaging classification + segmentation
- `pipeline/esi-triage-gate` - ESI 5-Level Triage gate (ER)
- `pipeline/mask-rcnn-coco-transfer` - Mask-RCNN with COCO transfer learning (instance segmentation + detection)
- `pipeline/medlabel-photo-to-warning` - MedLabel — photo-to-warning medicine safety pipeline
- `pipeline/radiology-report-grading` - Radiology report grading (RADS-aware, Fleischner-aware)
- `pipeline/sensor-fusion-imu-blending` - Multi-sensor fusion (IMU + thermal + ToF) with model blending
- `pipeline/unet-segmentation-tta` - U-Net medical segmentation with albumentations + TTA
- `pipeline/who-surgical-safety-gate` - WHO Surgical Safety Checklist gate (Sign In before induction)
- `processor/checklist-evaluator` - Checklist evaluator (GO/NO-GO)
- `processor/concept-graph-extractor` - Concept graph extractor
- `processor/entity-resolution-link` - Entity resolution: cluster records into entities
- `processor/official-sources-checker` - Official-sources analyzer
- `processor/redact-pii-text` - Redact PII from text (English-centric, MS Presidio-compatible)
- `rubric/clinical-grounded-response-v1` - Clinical grounded response v1
- `rubric/radiology-report-quality-v1` - Radiology report quality v1
- `rule-pack/clinical-red-flags` - Clinical red flags
- `rule-pack/grep-radiology-report-red-flags` - Radiology report quality + incidental-findings red flags
- `rule-pack/phi-hipaa-en` - PHI (HIPAA 18-identifier) — English text
- `tool/lookup-icd10` - ICD-10 lookup
- `tool/presidio-pii-detect` - Microsoft Presidio PII detection proxy

### healthcare.clinical

- `harness/clinical-decision-support` - Clinical Decision Support
- `knowledge-pack/clinical-guidelines-sample` - Clinical guidelines (sample chunks)
- `knowledge-pack/drug-interactions-sample` - Drug-drug interactions (sample, educational)
- `knowledge-pack/icd10-sample` - ICD-10 sample
- `knowledge-pack/radiology-acrac-fleischner` - ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics
- `persona/clinical-reasoner` - Clinical Reasoner
- `pipeline/differential-diagnosis` - Differential Diagnosis
- `rubric/clinical-grounded-response-v1` - Clinical grounded response v1
- `rule-pack/clinical-red-flags` - Clinical red flags
- `tool/lookup-icd10` - ICD-10 lookup

### healthcare.pharmacy

- `dataset/gxp-validation-samples` - Synthetic GxP validation samples (3 cases)
- `knowledge-pack/drug-interaction-references` - Drug-drug interaction references (DrugBank / RxNorm / FDA Orange Book / DailyMed)
- `knowledge-pack/drug-interactions-sample` - Drug-drug interactions (sample, educational)
- `knowledge-pack/gxp-21-cfr-11-guidelines` - 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack
- `persona/gxp-auditor` - GxP Auditor (21-CFR-11 / EU GMP Annex 11 / ICH / ALCOA+)
- `pipeline/medlabel-photo-to-warning` - MedLabel — photo-to-warning medicine safety pipeline

### healthcare.radiology

- `dataset/radiology-report-samples` - Synthetic radiology report samples (3 cases, fully synthetic)
- `harness/radiology-report-review` - Radiology Report Review harness
- `knowledge-pack/radiology-acrac-fleischner` - ACR Appropriateness Criteria + Fleischner + ACR RADS rubrics
- `persona/radiologist-cite-first` - Radiologist (citation-first, specialty radiology)
- `pipeline/dicom-medical-image-preprocessing` - DICOM medical image preprocessing (CT / MRI / X-ray)
- `pipeline/efficientnet-medical-imaging` - EfficientNet for medical imaging classification + segmentation
- `pipeline/mask-rcnn-coco-transfer` - Mask-RCNN with COCO transfer learning (instance segmentation + detection)
- `pipeline/radiology-report-grading` - Radiology report grading (RADS-aware, Fleischner-aware)
- `pipeline/unet-segmentation-tta` - U-Net medical segmentation with albumentations + TTA
- `rubric/radiology-report-quality-v1` - Radiology report quality v1
- `rule-pack/grep-radiology-report-red-flags` - Radiology report quality + incidental-findings red flags

### hr

- `dataset/hr-posting-samples` - Synthetic HR job-posting samples
- `knowledge-pack/eeoc-hiring-statutes` - EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)
- `persona/eeoc-hiring-officer` - EEOC Hiring Officer (Title VII / ADA / ADEA / OFCCP)
- `pipeline/hr-hiring-compliance-review` - HR hiring compliance review (EEOC / Title VII / ADA / ADEA)
- `rubric/hr-hiring-compliance-v1` - HR hiring compliance review quality v1
- `rule-pack/grep-hr-hiring-bias-flags` - HR hiring bias detectors (Title VII / ADA / ADEA / EEOC)

### hr.hiring

- `dataset/hr-posting-samples` - Synthetic HR job-posting samples
- `knowledge-pack/eeoc-hiring-statutes` - EEOC hiring statutes pack (Title VII / ADA / ADEA / GINA / PWFA)
- `persona/eeoc-hiring-officer` - EEOC Hiring Officer (Title VII / ADA / ADEA / OFCCP)
- `pipeline/hr-hiring-compliance-review` - HR hiring compliance review (EEOC / Title VII / ADA / ADEA)
- `rubric/hr-hiring-compliance-v1` - HR hiring compliance review quality v1
- `rule-pack/grep-hr-hiring-bias-flags` - HR hiring bias detectors (Title VII / ADA / ADEA / EEOC)

### humanitarian

- `adapter/gemma-4-26b-vision` - Google Gemma 4 26B-A4B-IT (multimodal vision + native multilingual)
- `dataset/bill-info-test-documents` - Bill_info AI evaluation set (28 documents)
- `knowledge-pack/high-risk-corridors-and-sectors` - High-risk corridors & sector-specific labor / environmental risks
- `knowledge-pack/iso-country-codes` - ISO 3166 country codes (sample)
- `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` - Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)
- `pattern/critical-tier-output-override` - Critical-tier output override (one dominant message on critical finding)
- `pattern/two-stage-extract-then-judge` - Two-stage extract-then-judge (separate calls for extraction + classification)
- `persona/bureaucracy-translator-cite-first` - Bureaucracy Translator (cite-first, action-oriented, vulnerable-user safe)
- `pipeline/bill-info-extract-fraud-detect-recommend` - Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection
- `pipeline/medlabel-photo-to-warning` - MedLabel — photo-to-warning medicine safety pipeline
- `rubric/bureaucracy-translation-quality-v1` - Bureaucracy translation + fraud-screen quality v1
- `rubric/esg-social-v1` - ESG social (S) sub-rubric v1
- `rule-pack/grep-fake-inkasso-fraud-flags` - Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)

### humanitarian.refugee

- `dataset/bill-info-test-documents` - Bill_info AI evaluation set (28 documents)
- `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` - Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)
- `persona/bureaucracy-translator-cite-first` - Bureaucracy Translator (cite-first, action-oriented, vulnerable-user safe)
- `pipeline/bill-info-extract-fraud-detect-recommend` - Bill_info AI — photo-to-action bureaucracy translator with Verbraucherzentrale-grounded fraud detection
- `rule-pack/grep-fake-inkasso-fraud-flags` - Fake-Inkasso fraud-detection GREP pack (Verbraucherzentrale 10-indicator taxonomy)

### infrastructure

- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts

### insurance

- `dataset/insurance-claim-samples` - Synthetic insurance claim samples
- `harness/data-cleaning-and-enrichment` - Data cleaning + entity enrichment harness
- `knowledge-pack/insurance-fraud-typologies` - Insurance fraud typologies (NAIC + CAIF + ABI)
- `persona/insurance-claims-adjuster` - Insurance Claims Adjuster (fraud-aware, NAIC-aligned)
- `pipeline/insurance-claim-review` - Insurance claim review (NAIC fraud-aware)
- `rubric/insurance-claim-quality-v1` - Insurance claim review quality v1
- `rule-pack/grep-insurance-fraud-red-flags` - Insurance claim fraud red-flag detectors (NAIC + CAIF)
- `tool/presidio-pii-detect` - Microsoft Presidio PII detection proxy

### insurance.claims

- `dataset/insurance-claim-samples` - Synthetic insurance claim samples
- `knowledge-pack/insurance-fraud-typologies` - Insurance fraud typologies (NAIC + CAIF + ABI)
- `persona/insurance-claims-adjuster` - Insurance Claims Adjuster (fraud-aware, NAIC-aligned)
- `pipeline/insurance-claim-review` - Insurance claim review (NAIC fraud-aware)
- `rubric/insurance-claim-quality-v1` - Insurance claim review quality v1
- `rule-pack/grep-insurance-fraud-red-flags` - Insurance claim fraud red-flag detectors (NAIC + CAIF)

### insurance.fraud

- `dataset/insurance-claim-samples` - Synthetic insurance claim samples
- `knowledge-pack/insurance-fraud-typologies` - Insurance fraud typologies (NAIC + CAIF + ABI)
- `persona/insurance-claims-adjuster` - Insurance Claims Adjuster (fraud-aware, NAIC-aligned)
- `pipeline/insurance-claim-review` - Insurance claim review (NAIC fraud-aware)
- `rubric/insurance-claim-quality-v1` - Insurance claim review quality v1
- `rule-pack/grep-insurance-fraud-red-flags` - Insurance claim fraud red-flag detectors (NAIC + CAIF)

### it

- `pipeline/itil-change-gate` - ITIL Change Enablement gate

### legal

- `dataset/contract-samples` - Synthetic commercial contract samples (3 cases)
- `dataset/ma-dd-samples` - M&A DD samples
- `harness/contract-redline` - Contract Clause Redlining harness
- `knowledge-pack/contract-law-clauses` - Commercial contract clause library (composite educational)
- `knowledge-pack/ma-dd-frameworks` - M&A DD frameworks (legal / financial / IP / customer / HR / tax)
- `knowledge-pack/spdx-licenses-summary` - SPDX licenses (summary)
- `pattern/anti-un-cited-extraction` - Anti-pattern: Un-cited extraction
- `pattern/local-first-with-cited-answers` - Local-first with cited answers
- `pattern/source-document-to-persistent-knowledge-layer` - Source document → persistent knowledge layer
- `persona/contract-reviewer-cite-first` - Contract Reviewer (citation-first, senior in-house counsel)
- `persona/ma-dd-counsel` - M&A Due Diligence Counsel (financial / legal / IP / customer / HR / tax)
- `pipeline/contract-clause-review` - Commercial contract clause review (cite-first redlining)
- `pipeline/document-to-knowledge-graph` - Document to knowledge graph (nodes + edges with source anchors)
- `pipeline/full-vendor-due-diligence` - Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)
- `pipeline/ma-dd-review` - M&A due-diligence review (6-stream)
- `pipeline/mixed-criteria-demo` - Mixed success-criteria demo (regex + semantic + deterministic + LLM + composite)
- `processor/pdf-extract-with-ocr-fallback` - PDF extract with OCR fallback (CiteMind shape)
- `rubric/contract-review-quality-v1` - Contract review quality v1
- `rubric/ma-dd-quality-v1` - M&A DD review quality v1
- `rule-pack/grep-contract-red-flags` - Commercial contract red-flag detectors
- `rule-pack/grep-ma-dd-red-flags` - M&A DD red-flag detectors (6 streams)

### legal.compliance

- `dataset/contract-samples` - Synthetic commercial contract samples (3 cases)
- `harness/contract-redline` - Contract Clause Redlining harness
- `knowledge-pack/contract-law-clauses` - Commercial contract clause library (composite educational)
- `persona/contract-reviewer-cite-first` - Contract Reviewer (citation-first, senior in-house counsel)
- `pipeline/contract-clause-review` - Commercial contract clause review (cite-first redlining)
- `rubric/contract-review-quality-v1` - Contract review quality v1
- `rule-pack/grep-contract-red-flags` - Commercial contract red-flag detectors

### legal.contract

- `dataset/contract-samples` - Synthetic commercial contract samples (3 cases)
- `harness/contract-redline` - Contract Clause Redlining harness
- `knowledge-pack/contract-law-clauses` - Commercial contract clause library (composite educational)
- `persona/contract-reviewer-cite-first` - Contract Reviewer (citation-first, senior in-house counsel)
- `pipeline/contract-clause-review` - Commercial contract clause review (cite-first redlining)
- `rubric/contract-review-quality-v1` - Contract review quality v1
- `rule-pack/grep-contract-red-flags` - Commercial contract red-flag detectors

### m_and_a

- `dataset/ma-dd-samples` - M&A DD samples
- `knowledge-pack/ma-dd-frameworks` - M&A DD frameworks (legal / financial / IP / customer / HR / tax)
- `persona/ma-dd-counsel` - M&A Due Diligence Counsel (financial / legal / IP / customer / HR / tax)
- `pipeline/ma-dd-review` - M&A due-diligence review (6-stream)
- `rubric/ma-dd-quality-v1` - M&A DD review quality v1
- `rule-pack/grep-ma-dd-red-flags` - M&A DD red-flag detectors (6 streams)

### m_and_a.due_diligence

- `dataset/ma-dd-samples` - M&A DD samples
- `knowledge-pack/ma-dd-frameworks` - M&A DD frameworks (legal / financial / IP / customer / HR / tax)
- `persona/ma-dd-counsel` - M&A Due Diligence Counsel (financial / legal / IP / customer / HR / tax)
- `pipeline/ma-dd-review` - M&A due-diligence review (6-stream)
- `rubric/ma-dd-quality-v1` - M&A DD review quality v1
- `rule-pack/grep-ma-dd-red-flags` - M&A DD red-flag detectors (6 streams)

### manufacturing

- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pipeline/sensor-fusion-imu-blending` - Multi-sensor fusion (IMU + thermal + ToF) with model blending

### maritime

- `dataset/maritime-safety-samples` - Maritime safety samples
- `knowledge-pack/imo-conventions` - IMO conventions (SOLAS / MARPOL / ISM / STCW / ISPS / MLC)
- `persona/maritime-safety-officer` - Maritime Safety Officer (IMO SOLAS / MARPOL / ISM / STCW)
- `pipeline/maritime-safety-review` - Maritime safety review (IMO SOLAS / MARPOL / ISM / STCW)
- `rubric/maritime-safety-quality-v1` - Maritime safety review quality v1
- `rule-pack/grep-maritime-safety-flags` - Maritime safety red-flag detectors (SOLAS / MARPOL / ISM)

### maritime.safety

- `dataset/maritime-safety-samples` - Maritime safety samples
- `knowledge-pack/imo-conventions` - IMO conventions (SOLAS / MARPOL / ISM / STCW / ISPS / MLC)
- `persona/maritime-safety-officer` - Maritime Safety Officer (IMO SOLAS / MARPOL / ISM / STCW)
- `pipeline/maritime-safety-review` - Maritime safety review (IMO SOLAS / MARPOL / ISM / STCW)
- `rubric/maritime-safety-quality-v1` - Maritime safety review quality v1
- `rule-pack/grep-maritime-safety-flags` - Maritime safety red-flag detectors (SOLAS / MARPOL / ISM)

### media

- `adapter/flux-1-schnell-local` - FLUX.1 Schnell (open-weights image generation)
- `dataset/election-integrity-samples` - Election integrity samples
- `knowledge-pack/election-integrity-frameworks` - Election integrity frameworks (EAC / CISA / DHS / C2PA)
- `knowledge-pack/platform-content-policy-frameworks` - Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)
- `pattern/chain-of-density` - Chain-of-Density (iterative dense summarization)
- `pipeline/tfidf-lightgbm-text-classification` - TF-IDF + LightGBM text classification
- `persona/election-integrity-analyst` - Election Integrity Analyst (misinformation / deepfake / voter-roll)
- `persona/fact-checker` - Fact Checker
- `persona/trust-and-safety-reviewer` - Trust + Safety reviewer (platform moderation)
- `pipeline/deep-research-supervisor-workers` - Deep research: supervisor + parallel workers
- `pipeline/deep-research-with-citations` - Deep research with citations
- `pipeline/election-misinformation-review` - Election misinformation / disinformation / synthetic-media review
- `pipeline/longformer-bigbird-ner` - Long-document NER with LongFormer / BigBird
- `pipeline/platform-content-triage` - Platform content triage (Trust + Safety)
- `pipeline/storm-persona-curation-article` - STORM: persona-curation + outline-fanout article
- `pipeline/verify-claim-against-corpus` - Verify Claim Against Corpus
- `processor/nsfw-image-classifier` - NSFW image classifier
- `processor/official-sources-checker` - Official-sources analyzer
- `processor/persona-set-generator` - Persona-set generator (STORM)
- `processor/skeleton-outliner` - Skeleton outliner (Skeleton-of-Thought)
- `rubric/election-integrity-quality-v1` - Election integrity review quality v1
- `rubric/platform-moderation-quality-v1` - Platform moderation review quality v1
- `rubric/verification-v1` - Verification v1
- `rule-pack/grep-election-misinformation-flags` - Election misinformation / disinformation / deepfake detectors
- `rule-pack/grep-output-safety-image` - Image-output safety checks
- `rule-pack/grep-platform-moderation-flags` - Platform moderation flags (text-only triage)
- `rule-pack/grep-prohibited-terms` - Prohibited Terms (image-gen guard rails)

### media.factcheck

- `knowledge-pack/election-integrity-frameworks` - Election integrity frameworks (EAC / CISA / DHS / C2PA)
- `persona/election-integrity-analyst` - Election Integrity Analyst (misinformation / deepfake / voter-roll)
- `pipeline/election-misinformation-review` - Election misinformation / disinformation / synthetic-media review
- `rule-pack/grep-election-misinformation-flags` - Election misinformation / disinformation / deepfake detectors

### mining

- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pipeline/msha-preshift-exam` - MSHA pre-shift exam GO/NO-GO gate

### nuclear

- `dataset/nuclear-samples` - Nuclear safety samples
- `knowledge-pack/nuclear-nrc-iaea-frameworks` - Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `persona/nuclear-safety-inspector` - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)
- `pipeline/nuclear-safety-review` - Nuclear safety review (NRC 10 CFR + IAEA + INPO)
- `rubric/nuclear-quality-v1` - Nuclear safety review quality v1
- `rule-pack/grep-nuclear-safety-flags` - Nuclear safety / NRC / IAEA flags

### nuclear.iaea

- `persona/nuclear-safety-inspector` - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)
- `rule-pack/grep-nuclear-safety-flags` - Nuclear safety / NRC / IAEA flags

### nuclear.nrc

- `persona/nuclear-safety-inspector` - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)
- `rule-pack/grep-nuclear-safety-flags` - Nuclear safety / NRC / IAEA flags

### nuclear.power

- `dataset/nuclear-samples` - Nuclear safety samples
- `knowledge-pack/nuclear-nrc-iaea-frameworks` - Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)
- `pipeline/nuclear-safety-review` - Nuclear safety review (NRC 10 CFR + IAEA + INPO)
- `rubric/nuclear-quality-v1` - Nuclear safety review quality v1

### nuclear.security

- `dataset/nuclear-samples` - Nuclear safety samples
- `knowledge-pack/nuclear-nrc-iaea-frameworks` - Nuclear safety frameworks (NRC 10 CFR + IAEA + INPO)
- `persona/nuclear-safety-inspector` - Nuclear Safety Inspector (NRC 10 CFR / IAEA / INPO)
- `pipeline/nuclear-safety-review` - Nuclear safety review (NRC 10 CFR + IAEA + INPO)
- `rubric/nuclear-quality-v1` - Nuclear safety review quality v1

### personal_productivity

- `harness/chat-with-memory` - Persistent chat with memory (multi-turn, preference-aware)
- `harness/email-triage-and-draft` - Email Triage + Draft harness (preference-aware, tone-matched)
- `harness/personal-corpus-search` - Personal corpus search (RAG over user's own files / notes / docs)
- `knowledge-pack/user-preference-schema` - User preference schema (canonical shape for personal assistants)
- `persona/inbox-zero-coach` - Inbox Zero Coach (triage + reply-draft + delegation)
- `persona/personal-assistant` - Personal Assistant (preference-aware, privacy-first)
- `pipeline/email-triage-pipeline` - Email triage pipeline (preference-loaded, tone-matched, leakage-checked)
- `pipeline/personal-chat-pipeline` - Personal chat pipeline (preference + memory + tool-aware)
- `pipeline/personal-search-pipeline` - Personal corpus search pipeline (RAG over user's own data)
- `processor/calendar-slot-finder` - Calendar slot finder (preference-aware)
- `processor/preference-loader` - User preference loader
- `processor/recipient-tone-history` - Recipient tone-history loader
- `rule-pack/grep-personal-info-leakage` - Personal-info leakage detectors (assistant drafts → wrong audience)

### pharma

- `dataset/gxp-validation-samples` - Synthetic GxP validation samples (3 cases)
- `knowledge-pack/gxp-21-cfr-11-guidelines` - 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `persona/gxp-auditor` - GxP Auditor (21-CFR-11 / EU GMP Annex 11 / ICH / ALCOA+)
- `pipeline/gxp-validation-review` - GxP validation review (21-CFR-11 + Annex 11 + ALCOA+)
- `rubric/gxp-validation-quality-v1` - GxP validation review quality v1
- `rule-pack/grep-gxp-data-integrity-red-flags` - GxP data-integrity red-flag detectors (21-CFR-11 / ALCOA+)

### pharma.gxp

- `dataset/gxp-validation-samples` - Synthetic GxP validation samples (3 cases)
- `knowledge-pack/gxp-21-cfr-11-guidelines` - 21-CFR-11 + EU GMP Annex 11 + ICH + ALCOA+ regulatory pack
- `persona/gxp-auditor` - GxP Auditor (21-CFR-11 / EU GMP Annex 11 / ICH / ALCOA+)
- `pipeline/gxp-validation-review` - GxP validation review (21-CFR-11 + Annex 11 + ALCOA+)
- `rubric/gxp-validation-quality-v1` - GxP validation review quality v1
- `rule-pack/grep-gxp-data-integrity-red-flags` - GxP data-integrity red-flag detectors (21-CFR-11 / ALCOA+)

### privacy

- `dataset/gdpr-dsar-samples` - Synthetic GDPR DSAR samples
- `knowledge-pack/citemind-architecture-reference` - CiteMind architecture reference (local-first PDF → research wiki + concept graph)
- `knowledge-pack/gdpr-articles-and-ccpa` - GDPR articles + CCPA/CPRA + e-Privacy
- `knowledge-pack/platform-content-policy-frameworks` - Platform content policy frameworks (DSA + UK OSA + COPPA + NetzDG)
- `pattern/anti-no-pii-redact-before-model` - Anti-pattern: PII reaches the model without redaction
- `pattern/local-first-with-cited-answers` - Local-first with cited answers
- `persona/ai-governance-auditor` - AI Governance Auditor (EU AI Act + NIST AI RMF + ISO/IEC 42001 + GDPR Art 22)
- `persona/local-first-research-tutor` - Local-first research tutor (CiteMind-style)
- `persona/privacy-officer-gdpr` - Privacy Officer (GDPR / CCPA / DSAR fulfillment)
- `persona/trust-and-safety-reviewer` - Trust + Safety reviewer (platform moderation)
- `pipeline/ai-governance-audit` - AI governance audit (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `pipeline/citemind-pdf-to-research-wiki` - Local PDF → research wiki + concept graph (CiteMind shape)
- `pipeline/gdpr-dsar-review` - GDPR DSAR fulfillment review (CCPA-compatible)
- `pipeline/platform-content-triage` - Platform content triage (Trust + Safety)
- `processor/local-embedder` - Local embedder (Ollama / nomic / mxbai)
- `rubric/gdpr-dsar-quality-v1` - GDPR DSAR fulfillment quality v1
- `rubric/platform-moderation-quality-v1` - Platform moderation review quality v1
- `rule-pack/grep-ai-governance-flags` - AI governance audit flags (EU AI Act + NIST AI RMF + ISO 42001 + GDPR Art 22)
- `rule-pack/grep-gdpr-dsar-red-flags` - GDPR DSAR red-flag detectors
- `rule-pack/grep-platform-moderation-flags` - Platform moderation flags (text-only triage)

### privacy.ccpa

- `knowledge-pack/gdpr-articles-and-ccpa` - GDPR articles + CCPA/CPRA + e-Privacy

### privacy.dsar

- `dataset/gdpr-dsar-samples` - Synthetic GDPR DSAR samples
- `knowledge-pack/gdpr-articles-and-ccpa` - GDPR articles + CCPA/CPRA + e-Privacy
- `persona/privacy-officer-gdpr` - Privacy Officer (GDPR / CCPA / DSAR fulfillment)
- `pipeline/gdpr-dsar-review` - GDPR DSAR fulfillment review (CCPA-compatible)
- `rubric/gdpr-dsar-quality-v1` - GDPR DSAR fulfillment quality v1
- `rule-pack/grep-gdpr-dsar-red-flags` - GDPR DSAR red-flag detectors

### privacy.gdpr

- `dataset/gdpr-dsar-samples` - Synthetic GDPR DSAR samples
- `knowledge-pack/gdpr-articles-and-ccpa` - GDPR articles + CCPA/CPRA + e-Privacy
- `persona/privacy-officer-gdpr` - Privacy Officer (GDPR / CCPA / DSAR fulfillment)
- `pipeline/gdpr-dsar-review` - GDPR DSAR fulfillment review (CCPA-compatible)
- `rubric/gdpr-dsar-quality-v1` - GDPR DSAR fulfillment quality v1
- `rule-pack/grep-gdpr-dsar-red-flags` - GDPR DSAR red-flag detectors

### real_estate

- `dataset/realestate-dd-samples` - Real-estate DD samples
- `knowledge-pack/real-estate-dd-standards` - Real estate DD standards (ALTA / ASTM ESA / Bldg Code / Zoning)
- `persona/real-estate-dd-analyst` - Real Estate Due Diligence Analyst (title / environmental / structural / zoning)
- `pipeline/real-estate-dd-review` - Real estate due-diligence review
- `rubric/real-estate-dd-quality-v1` - Real-estate DD review quality v1
- `rule-pack/grep-real-estate-dd-red-flags` - Real estate DD red-flag detectors
- `tool/google-geocode` - Google Maps Geocoding (address → lat/lng)

### real_estate.due_diligence

- `dataset/realestate-dd-samples` - Real-estate DD samples
- `knowledge-pack/real-estate-dd-standards` - Real estate DD standards (ALTA / ASTM ESA / Bldg Code / Zoning)
- `persona/real-estate-dd-analyst` - Real Estate Due Diligence Analyst (title / environmental / structural / zoning)
- `pipeline/real-estate-dd-review` - Real estate due-diligence review
- `rubric/real-estate-dd-quality-v1` - Real-estate DD review quality v1
- `rule-pack/grep-real-estate-dd-red-flags` - Real estate DD red-flag detectors

### research

- `dataset/citemind-pdf-samples` - CiteMind PDF samples (educational, open-license)
- `pattern/concept-graph-from-text` - Concept graph from text
- `pattern/source-document-to-persistent-knowledge-layer` - Source document → persistent knowledge layer
- `pipeline/document-to-knowledge-graph` - Document to knowledge graph (nodes + edges with source anchors)
- `processor/concept-graph-extractor` - Concept graph extractor
- `processor/hybrid-bm25-vector-retrieve` - Hybrid BM25 + vector retrieve
- `processor/local-embedder` - Local embedder (Ollama / nomic / mxbai)
- `processor/page-aware-chunker` - Page-aware chunker
- `processor/pdf-extract-with-ocr-fallback` - PDF extract with OCR fallback (CiteMind shape)
- `rubric/citemind-citation-fidelity-v1` - CiteMind citation-fidelity rubric v1

### retail

- `harness/data-cleaning-and-enrichment` - Data cleaning + entity enrichment harness
- `persona/cinematic-product-photographer` - Cinematic Product Photographer
- `persona/support-agent` - Customer support agent
- `pipeline/brand-safe-product-photo` - Brand-Safe Product Photo
- `pipeline/customer-record-enrichment` - Customer record enrichment (deterministic, cross-vertical)
- `pipeline/email-triage-and-draft` - Email triage + reply draft
- `rubric/brand-safe-image-v1` - Brand-safe image v1
- `tool/google-geocode` - Google Maps Geocoding (address → lat/lng)
- `tool/usps-address-validator` - USPS address validation

### retail.support

- `persona/support-agent` - Customer support agent
- `pipeline/email-triage-and-draft` - Email triage + reply draft

### scientific_research

- `harness/code-act-jupyter` - Code-Act Jupyter (tool-augmented reasoning via sandboxed Python)
- `pattern/two-stage-retrieve-rerank` - Two-stage retrieve + constrained rerank
- `pipeline/audio-mel-spec-cnn-classifier` - Audio classification via mel-spectrogram + CNN (KerasCV / EfficientNet)
- `pipeline/deepseek-r1-code-interpreter-math` - DeepSeek-R1 / QwQ + Python code-interpreter for math reasoning
- `pipeline/large-model-faiss-rag` - Large-model FAISS RAG (Platypus2-70b style)
- `pipeline/optuna-tabular-tuning` - Optuna hyperparameter tuning for tabular models
- `pipeline/sentence-transformer-finetune-retrieval` - Sentence-transformer fine-tune for retrieval / ranking
- `pipeline/two-time-retrieve-rerank` - Two-time retrieval + cross-encoder rerank

### scientific_research.bio

- `pipeline/audio-mel-spec-cnn-classifier` - Audio classification via mel-spectrogram + CNN (KerasCV / EfficientNet)

### security

- `dataset/code-review-samples` - Synthetic code-review samples (3 cases)
- `dataset/nerc-cip-samples` - NERC CIP BES samples
- `dataset/threat-intel-samples` - Synthetic threat-intelligence report samples
- `harness/appsec-code-audit` - AppSec Code Audit harness
- `knowledge-pack/mitre-attack-sample` - MITRE ATT&CK techniques (sample)
- `knowledge-pack/nerc-cip-standards` - NERC CIP standards (CIP-002 to CIP-014)
- `knowledge-pack/owasp-top-10-llm` - OWASP Top 10 for LLM Applications (2025)
- `pattern/diamond-model-attribution` - Diamond Model attribution (CTI threat-actor analysis)
- `pattern/k-anonymity-aggregation` - K-anonymity + HMACed-key cross-organization aggregation
- `persona/nerc-cip-analyst` - NERC CIP Compliance Analyst (Bulk Electric System cyber)
- `persona/security-engineer-cite-first` - Security Engineer (CWE-cite-first AppSec reviewer)
- `persona/threat-intel-analyst` - Threat Intelligence Analyst (MITRE ATT&CK + STIX/TAXII + IOC)
- `pipeline/code-review-with-risk-score` - Code review with risk score
- `pipeline/code-security-review` - Code security review (CWE-cite-first AppSec audit)
- `pipeline/full-vendor-due-diligence` - Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)
- `pipeline/nerc-cip-compliance-review` - NERC CIP compliance review (Bulk Electric System cyber)
- `pipeline/security-incident-grading` - Security incident write-up grading (CTI + AppSec chained)
- `pipeline/threat-intel-ioc-review` - Threat-intel IOC + TTP review (MITRE ATT&CK aligned)
- `processor/prompt-injection-detector` - Prompt-injection detector
- `rubric/code-security-review-v1` - Code security review v1
- `rubric/nerc-cip-quality-v1` - NERC CIP compliance review quality v1
- `rubric/threat-intel-quality-v1` - Threat intelligence report quality v1
- `rule-pack/grep-ai-vendor-keys` - AI vendor API key detectors
- `rule-pack/grep-cloud-secrets` - Cloud provider secret detectors
- `rule-pack/grep-code-vulnerabilities` - Code vulnerability + secret-detection GREP pack
- `rule-pack/grep-ioc-extraction` - IOC extraction GREP pack (file hashes / domains / IPs / URLs)
- `rule-pack/grep-nerc-cip-flags` - NERC CIP compliance red-flag detectors
- `rule-pack/grep-private-key-blocks` - Private key block detectors
- `rule-pack/grep-prompt-injection-heuristics` - Prompt-injection heuristic detectors
- `rule-pack/grep-vcs-platform-pats` - VCS platform PATs (GitHub, GitLab, Bitbucket, Atlassian)
- `tool/mitre-attack-mapper` - MITRE ATT&CK technique mapper
- `tool/semgrep-sast-proxy` - Semgrep SAST proxy (CWE-tagged code findings)

### security.appsec

- `dataset/code-review-samples` - Synthetic code-review samples (3 cases)
- `harness/appsec-code-audit` - AppSec Code Audit harness
- `persona/security-engineer-cite-first` - Security Engineer (CWE-cite-first AppSec reviewer)
- `pipeline/code-security-review` - Code security review (CWE-cite-first AppSec audit)
- `pipeline/security-incident-grading` - Security incident write-up grading (CTI + AppSec chained)
- `rubric/code-security-review-v1` - Code security review v1
- `rule-pack/grep-code-vulnerabilities` - Code vulnerability + secret-detection GREP pack
- `tool/semgrep-sast-proxy` - Semgrep SAST proxy (CWE-tagged code findings)

### software

- `dataset/code-review-samples` - Synthetic code-review samples (3 cases)
- `harness/appsec-code-audit` - AppSec Code Audit harness
- `knowledge-pack/spdx-licenses-summary` - SPDX licenses (summary)
- `persona/code-consultant` - Code consultant
- `persona/linux-terminal` - Linux terminal
- `persona/security-engineer-cite-first` - Security Engineer (CWE-cite-first AppSec reviewer)
- `pipeline/code-act-jupyter-loop` - Code-act Jupyter loop
- `pipeline/code-review-with-risk-score` - Code review with risk score
- `pipeline/code-security-review` - Code security review (CWE-cite-first AppSec audit)
- `pipeline/swe-patch-sample-and-review` - SWE-agent: sample N patches + reviewer judges
- `processor/action-sampler-multi-rollout` - Action sampler — N parallel rollouts
- `rubric/code-security-review-v1` - Code security review v1
- `rule-pack/grep-code-vulnerabilities` - Code vulnerability + secret-detection GREP pack
- `rule-pack/grep-vcs-platform-pats` - VCS platform PATs (GitHub, GitLab, Bitbucket, Atlassian)
- `tool/semgrep-sast-proxy` - Semgrep SAST proxy (CWE-tagged code findings)

### software.codereview

- `persona/code-consultant` - Code consultant
- `persona/security-engineer-cite-first` - Security Engineer (CWE-cite-first AppSec reviewer)
- `pipeline/code-review-with-risk-score` - Code review with risk score
- `pipeline/code-security-review` - Code security review (CWE-cite-first AppSec audit)
- `pipeline/swe-patch-sample-and-review` - SWE-agent: sample N patches + reviewer judges

### space

- `dataset/space-launch-samples` - Space launch readiness samples
- `knowledge-pack/space-launch-frameworks` - Space launch + range safety + ITAR/EAR frameworks
- `persona/space-launch-safety-officer` - Commercial Space Launch Safety Officer (FAA Part 450 / NASA Range Safety)
- `pipeline/space-launch-review` - Space launch + range safety review (FAA Part 450 / NASA / ITAR)
- `rubric/space-launch-quality-v1` - Space launch + range safety review quality v1
- `rule-pack/grep-space-launch-flags` - Space launch + range safety + ITAR/EAR flags

### space.export_control

- `dataset/space-launch-samples` - Space launch readiness samples
- `knowledge-pack/space-launch-frameworks` - Space launch + range safety + ITAR/EAR frameworks
- `persona/space-launch-safety-officer` - Commercial Space Launch Safety Officer (FAA Part 450 / NASA Range Safety)
- `pipeline/space-launch-review` - Space launch + range safety review (FAA Part 450 / NASA / ITAR)
- `rubric/space-launch-quality-v1` - Space launch + range safety review quality v1
- `rule-pack/grep-space-launch-flags` - Space launch + range safety + ITAR/EAR flags

### space.launch

- `dataset/space-launch-samples` - Space launch readiness samples
- `knowledge-pack/space-launch-frameworks` - Space launch + range safety + ITAR/EAR frameworks
- `persona/space-launch-safety-officer` - Commercial Space Launch Safety Officer (FAA Part 450 / NASA Range Safety)
- `pipeline/space-launch-review` - Space launch + range safety review (FAA Part 450 / NASA / ITAR)
- `rubric/space-launch-quality-v1` - Space launch + range safety review quality v1
- `rule-pack/grep-space-launch-flags` - Space launch + range safety + ITAR/EAR flags

### space.orbital

- `dataset/space-launch-samples` - Space launch readiness samples
- `knowledge-pack/space-launch-frameworks` - Space launch + range safety + ITAR/EAR frameworks
- `persona/space-launch-safety-officer` - Commercial Space Launch Safety Officer (FAA Part 450 / NASA Range Safety)
- `pipeline/space-launch-review` - Space launch + range safety review (FAA Part 450 / NASA / ITAR)
- `rubric/space-launch-quality-v1` - Space launch + range safety review quality v1
- `rule-pack/grep-space-launch-flags` - Space launch + range safety + ITAR/EAR flags

### supply_chain

- `benchmark/esg-supplier-grading-bench` - ESG supplier-grading benchmark v1
- `dataset/supplier-disclosure-pack-schema` - Supplier disclosure pack schema (canonical input shape)
- `harness/esg-disclosure-grading` - ESG Disclosure Grading harness
- `knowledge-pack/csddd-and-forced-labor-indicators` - Global supply-chain due-diligence regulatory pack
- `knowledge-pack/high-risk-corridors-and-sectors` - High-risk corridors & sector-specific labor / environmental risks
- `knowledge-pack/lead-company-code-stub` - Lead-company code-of-conduct stub (placeholder)
- `pattern/concept-graph-from-text` - Concept graph from text
- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)
- `pipeline/anonymized-illicit-recruitment-pattern-sharing` - Anonymized cross-org pattern sharing for illicit recruitment corridors
- `pipeline/deep-tier-supplier-audit` - Deep-tier (T1→T4+) supplier audit with traceability
- `pipeline/document-to-knowledge-graph` - Document to knowledge graph (nodes + edges with source anchors)
- `pipeline/full-vendor-due-diligence` - Full vendor due-diligence (ESG + AppSec + Legal — kitchen-sink)
- `pipeline/supplier-policy-grading` - Supplier policy & disclosure grading (CSDDD-aligned)
- `processor/structured-to-prose` - Structured JSON → prose normalizer (for GREP-style rule packs)
- `rubric/esg-env-v1` - ESG environmental (E) sub-rubric v1
- `rubric/esg-social-v1` - ESG social (S) sub-rubric v1
- `rubric/esg-supplier-compliance-v1` - ESG supplier compliance v1 (full E + S + G)
- `rule-pack/grep-esg-environmental-red-flags` - ESG environmental red-flag detectors (the 'E' of ESG)
- `rule-pack/grep-esg-forced-labor-red-flags` - ESG / forced-labor red-flag detectors (the 'S' of ESG)
- `tool/cbp-wro-lookup` - US CBP Withhold Release Order + UFLPA Entity List lookup
- `tool/opencorporates-lookup` - OpenCorporates company lookup

### sustainability

- `persona/esg-auditor` - ESG / Supply Chain Due Diligence Auditor (E + S + G)
- `rule-pack/grep-esg-environmental-red-flags` - ESG environmental red-flag detectors (the 'E' of ESG)

### tax

- `dataset/transfer-pricing-samples` - Transfer pricing samples
- `knowledge-pack/oecd-tp-and-beps` - OECD TP Guidelines + BEPS + Pillar Two + §482
- `persona/transfer-pricing-counsel` - Transfer Pricing Counsel (OECD BEPS / IRC §482 / Pillar Two)
- `pipeline/transfer-pricing-review` - Transfer pricing review (OECD TPG / BEPS / §482 / Pillar Two)
- `rubric/transfer-pricing-quality-v1` - Transfer-pricing review quality v1
- `rule-pack/grep-transfer-pricing-flags` - Transfer-pricing red-flag detectors (OECD / §482 / BEPS)

### tax.transfer_pricing

- `dataset/transfer-pricing-samples` - Transfer pricing samples
- `knowledge-pack/oecd-tp-and-beps` - OECD TP Guidelines + BEPS + Pillar Two + §482
- `persona/transfer-pricing-counsel` - Transfer Pricing Counsel (OECD BEPS / IRC §482 / Pillar Two)
- `pipeline/transfer-pricing-review` - Transfer pricing review (OECD TPG / BEPS / §482 / Pillar Two)
- `rubric/transfer-pricing-quality-v1` - Transfer-pricing review quality v1
- `rule-pack/grep-transfer-pricing-flags` - Transfer-pricing red-flag detectors (OECD / §482 / BEPS)

### telecommunications

- `dataset/telco-samples` - Telco compliance samples
- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `knowledge-pack/telco-fcc-cpni-frameworks` - Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)
- `persona/telco-compliance-officer` - Telco Compliance Officer (FCC Part 47 / CPNI / CALEA / TRAI)
- `pipeline/telco-compliance-review` - Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)
- `rubric/telco-quality-v1` - Telco compliance review quality v1
- `rule-pack/grep-telco-compliance-flags` - Telco compliance red-flag detectors (FCC / CPNI / CALEA)

### telecommunications.cpni

- `dataset/telco-samples` - Telco compliance samples
- `knowledge-pack/telco-fcc-cpni-frameworks` - Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)
- `persona/telco-compliance-officer` - Telco Compliance Officer (FCC Part 47 / CPNI / CALEA / TRAI)
- `pipeline/telco-compliance-review` - Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)
- `rubric/telco-quality-v1` - Telco compliance review quality v1
- `rule-pack/grep-telco-compliance-flags` - Telco compliance red-flag detectors (FCC / CPNI / CALEA)

### telecommunications.fcc

- `dataset/telco-samples` - Telco compliance samples
- `knowledge-pack/telco-fcc-cpni-frameworks` - Telco regulatory frameworks (FCC 47 CFR + CPNI + CALEA + STIR/SHAKEN)
- `persona/telco-compliance-officer` - Telco Compliance Officer (FCC Part 47 / CPNI / CALEA / TRAI)
- `pipeline/telco-compliance-review` - Telco compliance review (FCC + CPNI + CALEA + STIR/SHAKEN)
- `rubric/telco-quality-v1` - Telco compliance review quality v1
- `rule-pack/grep-telco-compliance-flags` - Telco compliance red-flag detectors (FCC / CPNI / CALEA)

### threat_intelligence

- `dataset/threat-intel-samples` - Synthetic threat-intelligence report samples
- `pattern/diamond-model-attribution` - Diamond Model attribution (CTI threat-actor analysis)
- `persona/threat-intel-analyst` - Threat Intelligence Analyst (MITRE ATT&CK + STIX/TAXII + IOC)
- `pipeline/security-incident-grading` - Security incident write-up grading (CTI + AppSec chained)
- `pipeline/threat-intel-ioc-review` - Threat-intel IOC + TTP review (MITRE ATT&CK aligned)
- `rubric/threat-intel-quality-v1` - Threat intelligence report quality v1
- `rule-pack/grep-ioc-extraction` - IOC extraction GREP pack (file hashes / domains / IPs / URLs)
- `tool/mitre-attack-mapper` - MITRE ATT&CK technique mapper

### threat_intelligence.ioc

- `persona/threat-intel-analyst` - Threat Intelligence Analyst (MITRE ATT&CK + STIX/TAXII + IOC)

### threat_intelligence.ttp

- `persona/threat-intel-analyst` - Threat Intelligence Analyst (MITRE ATT&CK + STIX/TAXII + IOC)
- `tool/mitre-attack-mapper` - MITRE ATT&CK technique mapper

### trade

- `dataset/trade-export-samples` - Synthetic trade-export transaction samples
- `knowledge-pack/trade-export-control-frameworks` - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
- `persona/customs-broker` - Licensed Customs Broker (US CBP / EU UCC / WCO)
- `persona/space-launch-safety-officer` - Commercial Space Launch Safety Officer (FAA Part 450 / NASA Range Safety)
- `persona/trade-compliance-officer` - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)
- `pipeline/customs-broker-review` - Customs entry review (US CBP + UFLPA + USMCA + WCO)
- `pipeline/trade-compliance-review` - Trade compliance review (HTS / EAR / ITAR / OFAC)
- `rubric/trade-compliance-quality-v1` - Trade compliance review quality v1
- `rule-pack/grep-customs-broker-flags` - Customs entry / FTA / forced-labor flags (US CBP)
- `rule-pack/grep-trade-compliance-flags` - Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)

### trade.eccn

- `dataset/trade-export-samples` - Synthetic trade-export transaction samples
- `knowledge-pack/trade-export-control-frameworks` - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
- `persona/trade-compliance-officer` - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)
- `pipeline/trade-compliance-review` - Trade compliance review (HTS / EAR / ITAR / OFAC)
- `rubric/trade-compliance-quality-v1` - Trade compliance review quality v1
- `rule-pack/grep-trade-compliance-flags` - Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)

### trade.hts

- `knowledge-pack/trade-export-control-frameworks` - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
- `persona/trade-compliance-officer` - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)

### trade.itar

- `dataset/trade-export-samples` - Synthetic trade-export transaction samples
- `knowledge-pack/trade-export-control-frameworks` - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
- `persona/trade-compliance-officer` - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)
- `pipeline/trade-compliance-review` - Trade compliance review (HTS / EAR / ITAR / OFAC)
- `rubric/trade-compliance-quality-v1` - Trade compliance review quality v1
- `rule-pack/grep-trade-compliance-flags` - Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)

### trade.sanctions

- `dataset/trade-export-samples` - Synthetic trade-export transaction samples
- `knowledge-pack/trade-export-control-frameworks` - Trade & export control frameworks (HTS / EAR / ITAR / OFAC)
- `persona/trade-compliance-officer` - Trade Compliance Officer (HTS / ECCN / ITAR / OFAC)
- `pipeline/trade-compliance-review` - Trade compliance review (HTS / EAR / ITAR / OFAC)
- `rubric/trade-compliance-quality-v1` - Trade compliance review quality v1
- `rule-pack/grep-trade-compliance-flags` - Trade compliance red-flag detectors (HTS / ECCN / ITAR / OFAC)

### transportation

- `knowledge-pack/technician-checklists` - Technician checklists — 50 industry procedural artifacts
- `pipeline/dot-pretrip-gate` - DOT pre-trip inspection gate (DVIR / 49 CFR 396)
- `tool/google-geocode` - Google Maps Geocoding (address → lat/lng)

### waste

- `dataset/rcra-waste-samples` - RCRA hazardous waste samples
- `knowledge-pack/rcra-waste-frameworks` - RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)
- `persona/rcra-waste-manager` - RCRA Hazardous Waste Manager (40 CFR Parts 260-279 + e-Manifest + DOT HMR)
- `pipeline/rcra-waste-review` - RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)
- `rubric/rcra-waste-quality-v1` - RCRA hazardous waste review quality v1
- `rule-pack/grep-rcra-waste-flags` - RCRA hazardous waste + e-Manifest + DOT HMR flags

### waste.generator

- `dataset/rcra-waste-samples` - RCRA hazardous waste samples
- `knowledge-pack/rcra-waste-frameworks` - RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)
- `persona/rcra-waste-manager` - RCRA Hazardous Waste Manager (40 CFR Parts 260-279 + e-Manifest + DOT HMR)
- `pipeline/rcra-waste-review` - RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)
- `rubric/rcra-waste-quality-v1` - RCRA hazardous waste review quality v1
- `rule-pack/grep-rcra-waste-flags` - RCRA hazardous waste + e-Manifest + DOT HMR flags

### waste.rcra_tsdf

- `dataset/rcra-waste-samples` - RCRA hazardous waste samples
- `knowledge-pack/rcra-waste-frameworks` - RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)
- `persona/rcra-waste-manager` - RCRA Hazardous Waste Manager (40 CFR Parts 260-279 + e-Manifest + DOT HMR)
- `pipeline/rcra-waste-review` - RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)
- `rubric/rcra-waste-quality-v1` - RCRA hazardous waste review quality v1
- `rule-pack/grep-rcra-waste-flags` - RCRA hazardous waste + e-Manifest + DOT HMR flags

### waste.universal

- `dataset/rcra-waste-samples` - RCRA hazardous waste samples
- `knowledge-pack/rcra-waste-frameworks` - RCRA hazardous waste frameworks (40 CFR 260-279 + e-Manifest + DOT 49 CFR 172)
- `persona/rcra-waste-manager` - RCRA Hazardous Waste Manager (40 CFR Parts 260-279 + e-Manifest + DOT HMR)
- `pipeline/rcra-waste-review` - RCRA hazardous waste review (40 CFR 260-279 + e-Manifest + DOT HMR)
- `rubric/rcra-waste-quality-v1` - RCRA hazardous waste review quality v1
- `rule-pack/grep-rcra-waste-flags` - RCRA hazardous waste + e-Manifest + DOT HMR flags

### water_utility

- `dataset/water-utility-samples` - Water utility compliance samples
- `knowledge-pack/water-sdwa-lcrr-awia` - Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)
- `persona/water-utility-compliance-officer` - Water Utility Compliance Officer (SDWA / LCRR / AWIA)
- `pipeline/water-utility-compliance-review` - Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)
- `rubric/water-utility-quality-v1` - Water utility compliance review quality v1
- `rule-pack/grep-water-utility-flags` - Water utility SDWA / LCRR / AWIA red-flag detectors

### water_utility.lcr

- `dataset/water-utility-samples` - Water utility compliance samples
- `knowledge-pack/water-sdwa-lcrr-awia` - Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)
- `persona/water-utility-compliance-officer` - Water Utility Compliance Officer (SDWA / LCRR / AWIA)
- `pipeline/water-utility-compliance-review` - Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)
- `rubric/water-utility-quality-v1` - Water utility compliance review quality v1
- `rule-pack/grep-water-utility-flags` - Water utility SDWA / LCRR / AWIA red-flag detectors

### water_utility.scada

- `persona/water-utility-compliance-officer` - Water Utility Compliance Officer (SDWA / LCRR / AWIA)
- `pipeline/water-utility-compliance-review` - Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)

### water_utility.sdwa

- `dataset/water-utility-samples` - Water utility compliance samples
- `knowledge-pack/water-sdwa-lcrr-awia` - Water utility regulatory pack (SDWA / NPDWR / LCRR / DBPR / AWIA)
- `persona/water-utility-compliance-officer` - Water Utility Compliance Officer (SDWA / LCRR / AWIA)
- `pipeline/water-utility-compliance-review` - Water utility compliance review (SDWA / NPDWR / LCRR / AWIA)
- `rubric/water-utility-quality-v1` - Water utility compliance review quality v1
- `rule-pack/grep-water-utility-flags` - Water utility SDWA / LCRR / AWIA red-flag detectors
