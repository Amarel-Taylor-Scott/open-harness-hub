# Text-transformation systems map — indexed for Baltor (2026-06-05)

Owner-provided catalog (a deep pass on text-transformation tooling) turned into a **stage-mapped index
of systems, repos, layers, and use cases** — not a flat list. This is directly on Baltor's deepest
north star: *a registry of reusable AI pipeline components.* Text transformation **is** Baltor's
Enhancement→Optimization→Verification arc.

## Provenance & verify status (read first)
- **Owner-curated**, with the owner's own citations. Per **verify-first / never-trust-a-list**, repos are
  NOT treated as verified-for-runtime just because they're listed here.
- **VERIFIED ✓** = web-confirmed (owner/name, what it is) on 2026-06-05 (the priority subset below).
- **(listed)** = owner-provided, plausible, **pending verification** — verify before any enters the
  runtime. Corrections already found: `ragas` → `vibrantlabsai/ragas` (renamed); NeMo →
  `NVIDIA-NeMo/Guardrails`; **SemanticDiff is commercial, not OSS**; `princeton-nlp/AutoCompressors`
  needs fine-tuning → **breaks Baltor's frozen-model rule**.
- Adoption of any item is gated by Baltor's rules: OSS/self-hostable preferred, **frozen-model +
  governed-data**, behind a capability **Provider port (primary + fallback)**, real-or-labeled-SEAM.

## The pipeline ↔ Baltor's six stages
The owner's transformation pipeline maps almost 1:1 onto Baltor's macro stages:

| Owner's pipeline step | Baltor stage | Baltor module today |
|---|---|---|
| extraction + cleanup | **Source Systems** | connectors, `parser_router`, `source_handle_resolver` |
| linguistic analysis | **Reconciliation** | (gap — analysis layer is thin) |
| transformation engine | **Enhancement** | (LLM rewrite path) |
| constraint + style control | **Optimization** | `context_compress` (deterministic ladder) |
| semantic / factual QA | **Verification rail** | `context_lift_matrix`, `context_swarm`, `verified_context_flow` |
| diff / provenance | **Verification rail / Consumption** | receipts, lineage, `context_memory_block` |
| final rewritten text | **Consumption** | `serve`, llms.txt + MCP descriptor |

## Layered catalog (by function → Baltor stage)

### L1 · Extraction & document→text  → Source Systems
`microsoft/markitdown`✓ · `docling-project/docling`✓ · `Unstructured-IO/unstructured`✓ ·
`datalab-to/marker`(listed) · `allenai/olmocr`(listed) · `adbar/trafilatura`(listed) ·
`jgm/pandoc`(listed) · `matthewwithanm/python-markdownify`(listed) · `kreuzberg-dev/html-to-markdown`(listed)
→ **Adopt-candidate:** docling (primary, MIT/LF, layout+tables+OCR+lineage) + markitdown (lightweight fallback).

### L2 · Cleaning / normalization / Unicode repair  → Source Systems
`rspeer/python-ftfy`(listed) · `jfilter/clean-text`(listed) · `trinker/textclean`(listed) ·
`hplt-project/sacremoses`(listed) · `adbar/simplemma`(listed)
→ boring-but-essential intake hygiene; cheap deterministic, fits before normalization.

### L3 · Linguistic analysis  → Reconciliation (Baltor gap)
`explosion/spaCy`(listed) · `stanfordnlp/stanza`(listed) · `chartbeat-labs/textacy`(listed) ·
`bjascob/LemmInflect`(listed) · `jaraco/inflect`(listed) · `rspeer/wordfreq`(listed) ·
`keredson/wordninja`(listed) · `globalwordnet/english-wordnet`(listed) · `goodmami/wn`(listed)
→ substrate for **entity-safe rewriting** (protect names/numbers/dates/citations before transform).

### L4 · Deterministic NLG / templating  → Enhancement (deterministic path)
`simplenlg/simplenlg`(listed) · `RosaeNLG/rosaenlg`(listed) · `rali-udem/jsRealB`(listed) ·
`lapalme/pyrealb`(listed) · `amazon-science/datatuner`(listed) · `kasnerz/tabgenie`(listed)
→ on-thesis: deterministic surface realization before reaching for an LLM (repeatability/compliance).

### L5 · Spinning / spintax (HANDLE WITH CARE — owned-content variation ONLY)
`m1/gospin`(listed) · `vkosuri/Spinner`(listed) · others(listed)
→ **OUT-OF-SCOPE for product**; keep only as a cautionary baseline (synonym-substitution ≠ quality).
   Not for plagiarism/spam/disguising copied text.

### L6 · Translation / backtranslation (paraphrase via round-trip)  → Enhancement
`argosopentech/argos-translate`(listed) · `LibreTranslate/LibreTranslate`(listed) ·
`OpenNMT/OpenNMT-py`(listed) · `facebookresearch/fairseq`(listed) · `marian-nmt/marian`(listed)
→ self-hostable backtranslation = privacy-preserving paraphrase; heavier ones need training (caution).

### L7 · Paraphrase / rewrite generators  → Enhancement
`PrithivirajDamodaran/Parrot_Paraphraser`(listed) · `Vamsi995/Paraphrase-Generator`(listed) · others(listed)
→ use **candidate-and-filter** (generate N → reject entity/number/date drift → score → pick), never first-candidate.

### L8 · Simplification / lexical simplification  → Enhancement
`facebookresearch/muss`(listed) · `feralvam/easse`(listed) · `koc-lab/lex-simple`(listed, **legal**) ·
`salesforce/simplification`(listed) · others(listed)
→ `koc-lab/lex-simple` flagged for our compliance domain: simplification can change LEGAL meaning → route to review.

### L9 · Grammar / spelling / GEC  → Optimization (polish)
`grammarly/gector`(listed) · `chrisjbryant/errant`(listed) · `neuspell/neuspell`(listed) ·
`bakwc/JamSpell`(listed) · `wolfgarbe/SymSpell`(listed) · `languagetool-org/languagetool`(listed) ·
`jxmorris12/language_tool_python`(listed) · others(listed)
→ post-transform repair layer; deterministic-ish, self-hostable.

### L10 · Editorial linting / brand voice  → Optimization (style control)
`vale-cli/vale`(listed) · `textlint/textlint`(listed) · `retextjs/retext`(listed) ·
`amperser/proselint`(listed) · `get-alex/alex`(listed) · `btford/write-good`(listed)
→ turns "make it sound better" into **enforceable rules**; Vale = strongest for brand/style governance.

### L11 · Style transfer / tone control  → Enhancement
`PrithivirajDamodaran/Styleformer`(listed) · `martiansideofthemoon/style-transfer-paraphrase`(listed) ·
`SALT-NLP/FormalityStyleTransfer`(listed) · survey repos(listed)
→ treat style change as a *meaning-preserving paraphrase with a target attribute*.

### L12 · Prompt / context compression  → Optimization  ★ HIGHEST-LEVERAGE
`microsoft/LLMLingua`✓ · `liyucheng09/Selective_Context`✓ · `princeton-nlp/AutoCompressors`✓(but fine-tune→**excluded**) ·
`3DAgentWorld/Toolkit-for-Prompt-Compression`(listed) · `HuangOwen/Awesome-LLM-Compression`(listed)
→ **LLMLingua-2** (small distilled token-classifier, frozen, self-hostable) = the top adoption (see below).

### L13 · Elongation / length control  → Enhancement
`QwenLM/Self-Lengthen`(listed) · `salesforce/ctrl-sum`(listed) · `IAAR-Shanghai/CTGSurvey`(listed)
→ expansion = structure+examples+caveats, not "add words"; extract-claims→outline→expand→prune→enforce-length.

### L14 · Structured / constrained generation  → Verification rail  ★ HIGH-LEVERAGE
`dottxt-ai/outlines`✓ · `guidance-ai/guidance`✓ · `mlc-ai/xgrammar`✓ · `noamgat/lm-format-enforcer`✓ ·
`eth-sri/lmql`(listed) · `ggml-org/llama.cpp` GBNF(listed)
→ forces valid JSON/schema output (e.g. `{rewrite, preserved_entities, changed_terms, score}`) — see adoption #2.

### L15 · Guardrails / validation  → Verification rail / Consumption
`NVIDIA-NeMo/Guardrails`✓ · `guardrails-ai/guardrails`✓
→ preserve names/numbers/dates/citations; block unsupported additions; enforce length/reading-level.

### L16 · Synthetic data / repeatable pipelines  → (factory / corpus)
`argilla-io/distilabel`(listed) · `datadreamer-dev/DataDreamer`(listed) · `argilla-io/synthetic-data-generator`(listed)
→ for generating rewrite/style/compression variants at scale (corpus acquisition, not runtime).

### L17 · Evaluation / regression / QA  → Verification rail  ★ HIGH-LEVERAGE
`promptfoo/promptfoo`✓ · `confident-ai/deepeval`✓ · `stanfordnlp/dspy`✓ · `vibrantlabsai/ragas`✓ ·
`openai/evals`(listed) · `EleutherAI/lm-evaluation-harness`(listed) · `feralvam/easse`(listed)
→ where most rewrite systems fail (plausible but unmeasured). Feeds Baltor's `pipeline−bare` lift gate — adoption #3.

### L18 · Diff / provenance  → Verification rail / Consumption
`icflorescu/textdiff-create`✓ · `mmueller2012/awesome-diff-tools`(listed) · ~~SemanticDiff~~ (commercial, not OSS)
→ Baltor already emits receipts/lineage; a `{original, rewrite, changed_terms, preserved_entities,
   added_claims, removed_claims, risk_flags, readability_before/after}` change-report is the natural fit.

### L19 · Commercial APIs (benchmarks, not deps)
DeepL Write · Wordtune · QuillBot · Writer.com (brand-voice/terminology governance) · Grammarly (SDK deprecated 2024-01-10)
→ comparison points for user-facing quality; not adoptable infra.

## Top 3 highest-leverage adoptions for Baltor (verified, on-thesis)
1. **`microsoft/LLMLingua` (LLMLingua-2) behind `context_compress` as an OPTIONAL Provider.** Keep the
   deterministic token-budget ladder as the **primary**; LLMLingua-2 (small distilled classifier, frozen,
   self-hostable) as the higher-ratio **fallback rung** when a tighter budget is requested. Caveat: upstream
   quiet since Apr 2024 → pin a version + vendor the model. *(L12 → Optimization.)*
2. **`dottxt-ai/outlines` as the structured-output Provider on the Verification rail**, with
   `mlc-ai/xgrammar` / `noamgat/lm-format-enforcer` as engine-level fallback. 100%-valid JSON for rewrite
   verdicts/diffs instead of post-hoc parsing. *(L14 → Verification rail.)*
3. **`promptfoo/promptfoo` + `vibrantlabsai/ragas` as the measured-lift / faithfulness harness** feeding the
   `pipeline_score − bare_model_score` gate — turning the lift bar into an automated, CI-enforced gate.
   *(L17 → Verification rail.)*
4. *(if intake is near-term)* **`docling-project/docling`** primary + **`microsoft/markitdown`** fallback for
   Source-stage document→text. *(L1 → Source Systems.)*

## The architecture this implies (Baltor as a controlled text compiler)
`extract (L1) → clean (L2) → analyze (L3) → transform (L4/L6/L7/L8/L11) → constrain (L14/L15) →
polish (L9/L10) → evaluate (L17) → diff/audit (L18)` — a **candidate-and-filter loop**, not one model.
This is exactly Baltor's six stages + verification rail; the gap today is the **analysis (L3)** and a
first-class **diff/change-report (L18)** output.

## Parked / next
- Adoptions above are **queued** (need vendored deps; no-pip) — see `research/future-ideas.md`.
- The (listed) repos remain **pending verification**; verify a layer before adopting from it.
- Brand-voice (L10/Vale rules) touches **brand** → owner-decision before any rule pack ships.
