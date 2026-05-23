# Use case: Refugee bureaucracy translation (Bill_info AI integration)

## What this answers

> "A Ukrainian refugee in Germany photographs a German payment letter
> demanding €299 in 48 hours. They have ≈10 seconds of attention
> before they decide to pay, ignore, or panic. They don't need a
> translation - they need to know whether this is real and what to
> do."

This use case is anchored in Sviatoslav Grabovsky's **Bill_info AI**
(Gemma 4 Good Hackathon - Impact Track: Digital Equity & Inclusivity)
running live at https://huggingface.co/spaces/Svityk/bill-info-ai.

## Why this matters

By March 2026, Germany hosted 1.274M people from Ukraine under
temporary protection. Their permits are extended automatically until
March 2027. Four barriers hit when they receive a German payment
letter:

1. **Language**: legal German (Verzug, Mahnbescheid, Aufsichtsbehörde)
2. **Bureaucracy**: unfamiliar processes (Schufa, Inkasso law, Verbraucherzentrale)
3. **Time pressure**: 14-day deadline; missing adds ~€100 in fees + court escalation
4. **Fraud**: fake-Inkasso letters specifically target refugees. Verbraucherzentrale Brandenburg's Schwarzliste Inkasso recorded ~191,000 page views in a single year + 400 reported fake letters in 2022. Foreign IBANs make the money unrecoverable.

Google Translate translates *words*. A general chatbot mixes
"pay if the amount is correct" with "this might be a scam" in the
same response - and a stressed reader picks the more action-oriented
advice.

Bill_info AI's architectural answer is **two-stage extract-then-judge
+ critical-tier output override + refuse-on-redacted**.

## Catalog ingredients (16 artifacts)

| Layer | Artifact | Role |
|---|---|---|
| Persona | `persona/bureaucracy-translator-cite-first` | Action-first, ≤10-second attention budget; cite Verbraucherzentrale; never hallucinate |
| Adapter | `adapter/gemma-4-26b-vision` | Gemma 4 26B-A4B-IT (256K context, vision, native multilingual, Apache 2.0 weights for NGO self-hosting) |
| Knowledge pack | `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` | 10-criterion fraud taxonomy (4 critical + 6 supporting) + 3-level classification rule |
| GREP rule pack | `rule-pack/grep-fake-inkasso-fraud-flags` | First-pass deterministic detectors for the 10 indicators (foreign IBAN, private recipient, legal threats sans Mahnung, extreme deadline, missing Handelsregister, etc.) |
| Rubric | `rubric/bureaucracy-translation-quality-v1` | 9-dim grading (next-24h action present, field accuracy ≥ 95%, redacted refusal, fraud-tier classification, critical override enforced, authority cited, ...) |
| Pipeline | `pipeline/bill-info-extract-fraud-detect-recommend` | Two-stage Gemma 4 vision: extract → validate deterministically → GREP fraud-pass → focused fraud-detect LLM → RAG against Verbraucherzentrale → assemble with critical override |
| Dataset | `dataset/bill-info-test-documents` | 28-doc eval set (real redacted + synthetic clear + adversarial); reproducible via `python -m eval.run_eval` |
| Pattern (new) | `pattern/two-stage-extract-then-judge` | Separate extraction + judgment calls - focused criteria don't compete with extraction for model attention |
| Pattern (new) | `pattern/critical-tier-output-override` | Critical finding forces every UI component into ONE consistent message; prevents mixed "pay if correct + might be a scam" |
| Pattern (new) | `pattern/refuse-on-redacted` | Null over hallucination on missing/redacted fields; UI renders as user-language "unknown" |

## Live evidence (from Bill_info AI's published eval)

| Metric | Result |
|---|---|
| Documents tested | 28 |
| Extraction success rate | **96%** (27/28) |
| Overall field accuracy | **95.8%** |
| Refusal accuracy on redacted documents | **100%** (7/7) |
| Average latency (local) | 8.5s |
| Concrete fraud true-positive (synthetic Polish-IBAN scam) | 3 indicators detected with quoted German evidence - `likely_scam` classification |
| Concrete fraud true-negative (real r/germany Inkasso) | `legitimate` classification - **zero false-positive indicators** |

The single eval failure was a synthetic info-letter that triggered a
schema validation error rather than producing a wrong result. The
validation layer rejected malformed output - the safe failure mode.

## How the 3 new patterns generalize

These design patterns are NOT specific to Bill_info AI - they're
reusable across the catalog:

### `pattern/two-stage-extract-then-judge`
Already used (retroactively documented) in:
- `pipeline/supplier-policy-grading` (extract supplier disclosure → grade against rubric)
- `pipeline/radiology-report-grading` (extract findings → grade against RADS rubric)
- `pipeline/contract-clause-review` (extract clauses → grade against playbook)

### `pattern/critical-tier-output-override`
Generalizes to:
- ESG: CBP WRO / UFLPA hit → halt routine grading (persona/esg-auditor hard rule)
- Radiology: unredacted PHI in input → halt assessment (persona/radiologist-cite-first)
- Trade: ITAR technical data to foreign national → halt + cite §126
- Healthcare: drug interaction critical → override "may be appropriate" with "DO NOT prescribe"

### `pattern/refuse-on-redacted`
Generalizes to:
- Insurance claim review: redacted policy number → null + "request unredacted copy"
- Benefits adjudication: redacted SSN → null + "cure-period documentation request"
- M&A DD: redacted financials → null + "request unredacted disclosure schedules"
- Tax / transfer pricing: redacted CbCR → null + "missing-documentation finding"

## Path to NGO deployment

Bill_info AI's roadmap explicitly targets Caritas, Diakonie, and
Verbraucherzentrale for self-hosted deployments using the Apache 2.0
Gemma 4 weights. Self-hosting keeps refugee financial documents on
the organisation's own infrastructure - something closed APIs cannot
do.

The Open Harness Hub catalog complements this with:
- Standards-format publication (Croissant / MCP / Agent Skills emitters
  for the pipeline manifest)
- Vocabulary fork point for additional consumer-protection authorities
  (CFPB US, FCA UK, ACCC AU, ASIC NZ) - same pipeline shape, different
  knowledge pack
- Composable success criteria so individual NGOs can add their own
  acceptance bars (e.g. "must include hotline number for that
  city's Beratungsstelle")

## What's NOT in this catalog reference

- The original Gemma 4 26B model weights (Hugging Face hosts those)
- The Bill_info AI Hugging Face Space code (Svityk's repo is canonical)
- The real (non-synthetic) eval documents (those are private per the
  contributors' wishes)
- Production-scale fraud benchmark (Bill_info AI explicitly notes
  fraud detection has qualitative evidence on tested cases, not
  statistical evaluation against gold fraud labels - that's the
  next-step work)

The catalog reference is the **shape** of the pipeline + the
reusable design patterns + a port of the rule pack against the
published 10-indicator taxonomy.

## Co-authorship + attribution

This use-case integration credits Sviatoslav Grabovsky on:
- The pipeline manifest (`pipeline/bill-info-extract-fraud-detect-recommend`)
- All 3 design patterns (`pattern/two-stage-extract-then-judge`,
  `pattern/critical-tier-output-override`, `pattern/refuse-on-redacted`)
- The knowledge pack (`knowledge-pack/verbraucherzentrale-fake-inkasso-indicators`)
- The dataset reference (`dataset/bill-info-test-documents`)

All artifacts cite the HF Space URL + the Gemma 4 Good Hackathon
context + the Apache 2.0 Gemma license + Bill_info AI's MIT code
license.

## Try It

Live demo + code: https://huggingface.co/spaces/Svityk/bill-info-ai
Primary repo: https://github.com/Svityk/bill-info-ai

Run the catalog's port of the pipeline shape:

```bash
oh-hub describe pipeline/bill-info-extract-fraud-detect-recommend
oh-hub depends pipeline/bill-info-extract-fraud-detect-recommend
```
