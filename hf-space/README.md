---
title: Open Harness Hub Playground
emoji: 🧩
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.40.0
app_file: app.py
pinned: false
license: mit
short_description: Browse + run the 360+ catalog harnesses across 24 industry verticals.
---

# Open Harness Hub — Playground

Pick any pipeline from the [Open Harness Hub](https://github.com/Amarel-Taylor-Scott/open-harness-hub)
catalog (363 validated manifests, 24 industry verticals), plug in
sample data, and watch the DAG execute step-by-step. This Space
reads pipelines directly from the catalog at runtime.

## What's in the catalog (v0.5.0+)

**24 industry-grading verticals**, all running the same 6-step
chain (structured-to-prose → PII redact → GREP → RAG → judge → audit)
with only the persona / rule pack / knowledge pack / rubric changing:

1. ESG / Supply-Chain DD (CSDDD, 12 jurisdictions, 13 languages)
2. Healthcare radiology (RADS / Fleischner / HIPAA)
3. Legal contract review (10-clause playbook + redlines)
4. AppSec code review (CWE / OWASP / Semgrep / Presidio)
5. Pharma GxP validation (21-CFR-11 / Annex 11 / ALCOA+)
6. Climate finance disclosure (TCFD / ISSB / ESRS E1 / CDP)
7. Threat intelligence (MITRE ATT&CK / STIX / Admiralty)
8. Insurance claims fraud (NAIC / CAIF / ABI)
9. Academic integrity (plagiarism / AI / fabricated citations)
10. Gov benefits adjudication (SNAP / Medicaid / UI / SSI)
11. Privacy GDPR DSAR (GDPR + CCPA / CPRA)
12. HR EEOC hiring compliance (Title VII / ADA / ADEA / GINA / PWFA)
13. Trade compliance (HTS / EAR / ITAR / OFAC)
14. Real-estate due diligence (ALTA / ASTM ESA / IBC / zoning)
15. M&A due diligence (6-stream financial/legal/IP/customer/HR/tax)
16. Aviation safety (NTSB / FAA / ICAO / HFACS / ASAP)
17. Food safety (FDA FSMA / HACCP / GFSI)
18. Construction safety (OSHA 1926 / ANSI Z10 / Focus Four)
19. Energy grid (NERC CIP-002 → CIP-014)
20. Maritime safety (IMO SOLAS / MARPOL / ISM / STCW)
21. Transfer pricing (OECD TPG / BEPS / Pillar Two / US §482)
22. Refugee bureaucracy translation (Verbraucherzentrale / Bill_info AI)
23. Defense DFARS (coming next iteration)
24. Election integrity (coming next iteration)

**Plus cross-vertical primitives**:
- Data cleaning + entity enrichment (address / phone / name /
  country / dates / dedup / USPS / Google Geocode / OpenCorporates
  / SWIFT BIC)
- Personal-assistant harnesses (email triage + chat with memory +
  personal corpus search; preference-aware + tone-history-matched)
- Three kitchen-sink compound pipelines that chain sub-pipelines
  (vendor onboarding / sustainability full review / security
  incident grading)

**29 design patterns** including:
- Self-RAG, ReAct, Tree-of-Thoughts, Skeleton-of-Thought, Reflexion,
  Self-Refine, Plan-and-Execute, Orchestrator-Workers, Evaluator-
  Optimizer, Multi-Agent-Debate, Routing, Prompt-Chaining,
  Naive/Corrective/Fusion RAG, HyDE, Step-Back
- Two-Stage-Retrieve-Rerank, K-Anonymity-Aggregation,
  Composable-Success-Criteria
- Chain-of-Verification, RAFT, Chain-of-Density, Diamond-Model-
  Attribution
- **Two-Stage-Extract-Then-Judge** (from Bill_info AI)
- **Critical-Tier-Output-Override** (from Bill_info AI)
- **Refuse-on-Redacted** (from Bill_info AI)

**26 verified-evidence pipelines** mined from 96 top-voted Kaggle
kernels across 33 competition families (LMSYS / WSDM / EEDI / AIMO-2
/ LLM-Science-Exam / Feedback-Prize-2021 / LECR / SD-Image-to-Prompts
/ Optiver / Home-Credit / HMS / ISIC / HuBMAP / RSNA / BirdCLEF /
CommonLit / SIIM-Melanoma / OSIC / Jigsaw / M5 / CMI / Jane-Street /
AMEX / etc.) — every pipeline traceable to a named Kaggle kernel
with vote count.

**9 model adapters**: local Ollama, vLLM AWQ, Anthropic Claude
Sonnet, Anthropic Claude Opus, OpenAI GPT frontier, Google Gemini,
BGE embeddings, OpenAI embeddings, SDXL local, Gemma 4 26B vision.

**13 standards-format emitters** all verified working: Croissant,
MCP server, Agent Skills, HF model+dataset+space cards, lm-eval-
harness, promptfoo, CycloneDX-ML, OpenLineage, C2PA, EU AI Act
Annex IV, SPDX 3.0.

## Run locally

```bash
git clone https://github.com/Amarel-Taylor-Scott/open-harness-hub
cd open-harness-hub
pip install -r requirements.txt
python hf-space/app.py
# open http://127.0.0.1:7860

# OR use the CLI:
python scripts/oh_hub.py stats
python scripts/oh_hub.py search verbraucherzentrale
python scripts/oh_hub.py describe pipeline/bill-info-extract-fraud-detect-recommend
python scripts/oh_hub.py depends pipeline/supplier-policy-grading
```

## Live demo scripts

```bash
python scripts/demo_esg_pipeline.py          # CSDDD supplier grading
python scripts/demo_radiology_pipeline.py    # RADS/Fleischner report grading
python scripts/demo_contract_pipeline.py     # contract clause review
python scripts/demo_appsec_pipeline.py       # CWE secret + vuln detection
python scripts/demo_new_verticals.py         # GxP + climate + threat-intel
python scripts/demo_v3_verticals.py          # GDPR + HR + trade
python scripts/demo_v4_verticals.py          # real estate + M&A + aviation + food safety
python scripts/demo_v5_verticals.py          # construction + NERC CIP + maritime + tax
python scripts/demo_more_verticals.py        # insurance + academic + gov benefits
python scripts/demo_vendor_onboarding.py     # kitchen-sink: ESG + AppSec + Legal
```

## Switching the model

- `OH_JUDGE_ARM=ollama|anthropic|openai` (default: deterministic)
- `OLLAMA_HOST` / `OLLAMA_MODEL`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

Without a model configured, every pipeline still runs end-to-end —
the deterministic severity-weighted fallback for `processor/llm-judge`
produces real numeric grades from the GREP findings.

## Adding a new pipeline

Open a PR against the main repo with a new manifest under
`catalog/pipelines/...`. CI rebuilds this Space on merge.

## Notable verified-evidence integrations

- **Bill_info AI** (Sviatoslav Grabovsky, Gemma 4 Good Hackathon —
  Impact Track: Digital Equity & Inclusivity) — refugee bureaucracy
  translation with Verbraucherzentrale-grounded fraud detection.
  Live demo: https://huggingface.co/spaces/Svityk/bill-info-ai
- **Open Harness Hub Spec** (`docs/spec/HARNESS_HUB_SPEC.md`) —
  the portable Docker-Hub-for-harnesses standard Hassan Gasim
  proposed.
- **Peer-registry comparison** (`docs/comparison/peer-registries.md`)
  — what the hub adds vs HuggingFace / LangChain Hub / OpenAI Evals
  / lm-eval-harness / promptfoo / MCP marketplace.
